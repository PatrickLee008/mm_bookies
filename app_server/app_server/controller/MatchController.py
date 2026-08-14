import pytz

from app_server import app, db, auth, app_opt
from app_server.controller.AppUserController import verify_token
from app_server.model.AppFavouriteModel import AppFavourite
from app_server.model.AppLeagueTeamScraperModel import LeagueTeamScraperModel
from app_server.model.MAppLeagueModel import MAppLeague
from app_server.model.MatchModel import Match, MatchAttr, VipMatchAttr
from app_server.model.MatchResultModel import Result
from flask import g, request, jsonify, Blueprint
from app_server.utils import OrmUttil
from sqlalchemy import or_, func, and_, not_
import json
from datetime import datetime, timezone, timedelta
from app_server.model import Redis

match = Blueprint('match', __name__)
key_prefix = 'live_matches'


def get_league_logo_map(league_names):
    """Build a league-name-to-logo map for the match list response."""
    names = {
        name.strip()
        for name in league_names
        if isinstance(name, str) and name.strip()
    }
    if not names:
        return {}

    leagues = MAppLeague.query.filter(
        MAppLeague.del_flag == 0,
        MAppLeague.status == 1,
        or_(
            MAppLeague.name.in_(names),
            MAppLeague.scraper_name.in_(names),
        ),
    ).all()

    logo_map = {}
    for league in leagues:
        logo = (league.logo2 or league.logo or '').strip()
        if not logo:
            continue

        for name in (league.name, league.scraper_name):
            if isinstance(name, str) and name.strip():
                normalized_name = name.strip()
                logo_map[normalized_name] = logo
                logo_map[normalized_name.casefold()] = logo

    return logo_map


# 获取比赛列表
@match.route('/get', methods=['GET'])
# @auth.login_required
def get_match_list():
    """ get_match_list API Endpoint
            ---
            tags:
              - match
            parameters:
               - name: page
                 in: query
                 type: string
                 required: true
                 description: page of match
               - name: limit
                 in: query
                 type: integer
                 description: limit of match
               - name: odds_type
                 in: query
                 type: string
                 description: odds_type of match ('single', 'mix', 'old_mix')
               - name: sub_leagues
                 in: query
                 type: string
                 description: sub_leagues of match ['Spain Primera Division', 'Italy Serie A',]
            responses:
              200:
                description: { 'items': [...], 'total': 100 }
            """
    # 参数获取
    current_page = request.args.get('page', type=int, default=1)
    limit = request.args.get('limit', type=int, default=20)
    odds_type = request.args.get('odds_type')
    sub_leagues = request.args.get('sub_leagues')
    time_zone_hours = request.args.get('time_zone_hours', type=float, default=6.5)

    # 缓存处理
    cache_key = f"{key_prefix}|{odds_type}"
    match_caches = Redis.read(cache_key)

    if not match_caches:
        return jsonify({
            'items': [],
            'total': 0,
            'allPage': 0,
            'leagues': [],
            'favor_leagues': [],
        })

    items = json.loads(match_caches)

    # 时间处理
    custom_tz = timezone(timedelta(hours=time_zone_hours))
    server_now = datetime.now(pytz.timezone('Asia/Shanghai'))
    user_start = server_now.astimezone(custom_tz)
    user_date = user_start.date()
    user_start = datetime(user_date.year, user_date.month, user_date.day, tzinfo=custom_tz)
    user_end = user_start + timedelta(days=2, hours=10, minutes=30, seconds=59)

    # 日期边界计算
    today_date = user_start.date()
    tomorrow_date = today_date + timedelta(days=1)
    today_start = datetime(today_date.year, today_date.month, today_date.day, 0, 0, tzinfo=custom_tz)
    today_end = datetime(tomorrow_date.year, tomorrow_date.month, tomorrow_date.day, 10, 30, 59, tzinfo=custom_tz)
    tomorrow_start = datetime(tomorrow_date.year, tomorrow_date.month, tomorrow_date.day, 10, 30, tzinfo=custom_tz)
    day_after_tomorrow = tomorrow_date + timedelta(days=1)
    tomorrow_end = datetime(day_after_tomorrow.year, day_after_tomorrow.month, day_after_tomorrow.day, 10, 30, 59, tzinfo=custom_tz)
    # print(f"用户时间: {user_start} ~ {user_end}")
    # print(f"今天时间: {today_start} ~ {today_end}")
    # print(f"明天时间: {tomorrow_start} ~ {tomorrow_end}")
    # 过滤和标记有效比赛
    valid_items = []
    for item in items:
        # 时间转换
        source_match_time = datetime.strptime(item['MATCH_TIME'], "%Y-%m-%d %H:%M:%S").astimezone(timezone(timedelta(hours=8)))
        target_match_time = source_match_time.astimezone(custom_tz)
        
        # 时间范围过滤
        if not (user_start <= target_match_time < user_end):
            continue
        
        # 添加本地时间和比赛日期标记
        item['LOCAL_MATCH_TIME'] = target_match_time.strftime("%Y-%m-%d %H:%M:%S")
        if today_start <= target_match_time < today_end:
            item['MATCH_DAY'] = 'today'
        elif tomorrow_start <= target_match_time < tomorrow_end:
            item['MATCH_DAY'] = 'tomorrow'
        else:
            item['MATCH_DAY'] = 'other'
        
        valid_items.append(item)

    items = valid_items

    league_logo_map = get_league_logo_map(
        item.get('LEAGUE') for item in items
    )
    for item in items:
        league_name = item.get('LEAGUE')
        item['league_logo'] = league_logo_map.get(
            league_name,
            league_logo_map.get(league_name.casefold()) if isinstance(league_name, str) else None,
        )

    # 获取联赛排序和过滤
    leagues_sort = MAppLeague.get_scraper_leagues(True)
    leagues = list({u['LEAGUE'] for u in items})
    
    # 联赛排序
    if leagues_sort:
        leagues.sort(key=lambda l: (0, leagues_sort.index(l)) if l in leagues_sort else (1, l))
    else:
        leagues.sort()

    # 获取用户收藏联赛
    favor_leagues = []
    _auth = auth.get_auth()
    if _auth and verify_token(_auth.get('token')):
        mbid = g.user.id
        favor_leagues = [row[0] for row in AppFavourite.query.filter_by(mb_id=mbid).with_entities(AppFavourite.league).all()]

    # 联赛过滤
    if sub_leagues:
        sub_leagues = set(sub_leagues.split(","))
        items = [i for i in items if i['LEAGUE'] in sub_leagues]

    # 分页处理
    total = len(items)
    page_num = (total + limit - 1) // limit  # 更标准的分页计算
    start_idx = (current_page - 1) * limit
    end_idx = start_idx + limit
    paged_items = items[start_idx:end_idx]

    return jsonify({
        'items': paged_items,
        'total': total,
        'allPage': page_num,
        'leagues': leagues,
        'favor_leagues': favor_leagues,
    })


# 获取订单列表
@match.route('/get_result', methods=['GET'])
# @auth.login_required
def get_match_result():
    """ get_match_list API Endpoint
            ---
            tags:
              - match
            parameters:
               - name: page
                 in: query
                 type: string
                 required: true
                 description: page of match
               - name: limit
                 in: query
                 type: integer
                 description: limit of match
               - name: odds_type
                 in: query
                 type: string
                 description: odds_type of match ('single'/'mix')
            responses:
              200:
                description: { 'items': [...], 'total': 100 }
            """
    current_page = request.args.get('page', type=int, default=1)
    limit = request.args.get('limit', type=int, default=20)

    match_id = request.args.get('matchId')

    key_word = request.args.get('key_word')
    start_time = request.args.get('start_time')
    end_time = request.args.get('end_time')
    odds_type = request.args.get('odds_type')

    result_list = Result.query
    # print(result_list.all())
    if match_id:
        result_list = result_list.filter(Result.MATCH_ID == match_id)

    if key_word:
        result_list = result_list.filter(
            or_(Result.LEAGUE_NAME.like('%{}%'.format(key_word)), Result.HOST_TEAM.like('%{}%'.format(key_word)),
                Result.GUEST_TEAM.like('%{}%'.format(key_word))))
    if start_time:
        result_list = result_list.filter(Result.MATCH_TIME >= start_time)

    if end_time:
        end_time += ' 23:59:59'
        result_list = result_list.filter(Result.MATCH_TIME <= end_time)

    total = result_list.count()
    print(result_list.all())

    result_list = result_list.offset((current_page - 1) * limit).limit(limit).all()

    return jsonify({
        'items': [u.to_dict() for u in result_list],
        'total': total
    })


# 获取Odds
@match.route('/get_odds', methods=['GET'])
# @auth.login_required
def get_odds():
    """ get_odds API Endpoint
        ---
        tags:
          - match
        responses:
          200:
            description: { 'items': [...], 'total': 100 }
        """
    match_list = Match.query.filter(Match.MATCH_TIME > datetime.now(), Match.hide == "0")
    matches = {u.MATCH_ID for u in match_list}
    attrs = MatchAttr.query.filter(and_(MatchAttr.MATCH_ID.in_(matches),
                                        MatchAttr.MATCH_ATTR_TYPE.in_({'1', '2', '4', '5', '8', '9', '10'}))).all()

    return jsonify({
        'items': [u.to_dict() for u in attrs],
        'total': len(attrs)
    })


# 获取Odds
@match.route('/get_odd_detail', methods=['POST'])
@auth.login_required
def get_odd_detail():
    """ get_odd_detail API Endpoint
        ---
        tags:
          - match
        responses:
          200:
            description: { 'items': [...], 'total': 100 }
        """
    details = request.get_json().get("details")
    print(">>>>>>>>>>>dt", request.args, request.get_json())
    if details:
        result = []
        for det in details:
            attr = None
            if g.user.IS_VIP:
                attr = VipMatchAttr.query.filter(and_(VipMatchAttr.MATCH_ID == det['matchId'],
                                                      VipMatchAttr.MATCH_ATTR_TYPE == det['attrType'])).one_or_none()
            if not attr:
                attr = MatchAttr.query.filter(and_(MatchAttr.MATCH_ID == det['matchId'],
                                                   MatchAttr.MATCH_ATTR_TYPE == det['attrType'])).one_or_none()
            temp = attr.to_dict()
            temp.update(det)
            temp.pop('CREATE_TIME')
            result.append(temp)

        return jsonify({
            'items': result,
            'total': len(result)
        })
    response = jsonify({'message': "System or Technical Error"})
    response.status_code = 400
    return response


# 获取比赛列表
@match.route('/get_favor', methods=['GET'])
@auth.login_required
def get_favor_list():
    """ get_favor_list API Endpoint
            ---
            tags:
              - match
            parameters:
               - name: page
                 in: query
                 type: string
                 required: true
                 description: page of match
               - name: limit
                 in: query
                 type: integer
                 description: limit of match
               - name: odds_type
                 in: query
                 type: string
                 description: odds_type of match ('single'/'mix')
               - name: sub_leagues
                 in: query
                 type: string
                 description: sub_leagues of match ['Spain Primera Division', 'Italy Serie A', ...]
            responses:
              200:
                description: { 'items': [...], 'total': 100 }
            """
    current_page = request.args.get('page', type=int, default=1)
    limit = request.args.get('limit', type=int, default=20)

    odds_type = request.args.get('odds_type')

    cache_key = f"{key_prefix}|%s" % odds_type

    match_caches = Redis.read(cache_key)

    items = []
    if match_caches:
        items = json.loads(match_caches)

    mbid = g.user.id
    favor_leagues = [row[0] for row in
                     AppFavourite.query.filter_by(mb_id=mbid).with_entities(AppFavourite.league).all()]

    valid_items = []
    for item in items:
        if item['LEAGUE'] not in favor_leagues:
            continue
        valid_items.append(item)

    # 联赛排序：优先按 leagues_sort 顺序排列，其余按名称排序
    leagues_sort = MAppLeague.get_scraper_leagues(True)
    leagues = list({u['LEAGUE'] for u in valid_items})

    if leagues_sort:
        def sort_key(league_name):
            if league_name in leagues_sort:
                return (0, leagues_sort.index(league_name))  # 在优先列表中，按索引排序
            else:
                return (1, league_name)  # 不在优先列表中，按名称排序

        leagues.sort(key=sort_key)
    else:
        leagues.sort()  # 如果没有配置排序，按名称排序
    # 分页操作
    total = len(valid_items)
    page_num = int(total / limit) + 1
    right_bound = current_page * limit
    paged_items = valid_items[
                  (current_page - 1) * limit: right_bound if right_bound < len(valid_items) else len(valid_items)]

    return jsonify({
        'items': paged_items,
        'total': total,
        'leagues': leagues,
        'favor_leagues': favor_leagues,
    })


# 获取比赛结果列表
@match.route('/get_results', methods=['GET'])
@auth.login_required
def get_match_results():
    """ get_match_results API Endpoint
            ---
            tags:
              - match
            parameters:
               - name: page
                 in: query
                 type: string
                 required: true
                 description: page of results
               - name: limit
                 in: query
                 type: integer
                 description: limit of results
               - name: days
                 in: query
                 type: integer
                 description: number of days to look back (default: 3)
               - name: language_type
                 in: query
                 type: string
                 description: language type (mm for Myanmar, others for standard time)
            responses:
              200:
                description: { 'items': [...], 'total': 100, 'leagues': [...] }
            """
    current_page = request.args.get('page', type=int, default=1)
    limit = request.args.get('limit', type=int, default=200)
    days = request.args.get('days', type=int, default=3)  # 修改为近3天

    # 计算时间范围（默认查询最近3天的比赛结果）
    now = datetime.now()
    start_time = now - timedelta(days=days)

    # 从 Match 表查询已完成的比赛结果
    # 注意：表中没有 EXCEPTION 字段，如需添加该过滤条件，请先在数据库中添加该字段
    matches = Match.query.filter(
        Match.MATCH_TIME >= start_time,
        or_(
            Match.HOST_TEAM_RESULT.isnot(None),  # 有主队得分
            Match.GUEST_TEAM_RESULT.isnot(None),  # 有客队得分
        ),
        # 重复隐藏
        not_(
            and_(
                Match.hide == 1,
                Match.hide_reason.isnot(None)
            )
        ),
        Match.HOST_TEAM_RESULT != 100,  # 非隐藏比赛
    ).order_by(Match.MATCH_TIME.desc()).all()

    # 转换为字典列表并调整字段名以匹配前端
    items = []
    for match in matches:
        match_dict = match.to_dict()
        # 将字段名映射为前端期望的格式
        match_dict['LEAGUE_NAME'] = match_dict.get('LEAGUE')
        match_dict['FULL_HOST_SCORE'] = match_dict.get('HOST_TEAM_RESULT')
        match_dict['FULL_GUEST_SCORE'] = match_dict.get('GUEST_TEAM_RESULT')

        # 通过球队名称模糊匹配获取队徽
        host_team_name = match_dict.get('HOST_TEAM')
        guest_team_name = match_dict.get('GUEST_TEAM')
        league_name = match_dict.get('LEAGUE')

        # 查询主队队徽（通过联赛名称+球队名称匹配）
        if host_team_name and league_name:
            host_team = LeagueTeamScraperModel.query.filter(
                LeagueTeamScraperModel.league_name == league_name,
                LeagueTeamScraperModel.status == 1,
                or_(
                    LeagueTeamScraperModel.name == host_team_name,
                    LeagueTeamScraperModel.team_name == host_team_name
                )
            ).first()
            match_dict['home_logo'] = host_team.logo if host_team and host_team.logo else None
        else:
            match_dict['home_logo'] = None

        # 查询客队队徽（通过联赛名称+球队名称匹配）
        if guest_team_name and league_name:
            guest_team = LeagueTeamScraperModel.query.filter(
                LeagueTeamScraperModel.league_name == league_name,
                LeagueTeamScraperModel.status == 1,
                or_(
                    LeagueTeamScraperModel.name == guest_team_name,
                    LeagueTeamScraperModel.team_name == guest_team_name
                )
            ).first()
            match_dict['away_logo'] = guest_team.logo if guest_team and guest_team.logo else None
        else:
            match_dict['away_logo'] = None

        items.append(match_dict)

    # # 联赛排序
    leagues_sort = MAppLeague.get_scraper_leagues(True)
    print("leagues_sort:", leagues_sort)

    leagues = list({u['LEAGUE'] for u in items})

    # 优化排序逻辑：优先按 leagues_sort 顺序排列，其余按名称排序
    if leagues_sort:
        def sort_key(league_name):
            if league_name in leagues_sort:
                return (0, leagues_sort.index(league_name))  # 在优先列表中，按索引排序
            else:
                return (1, league_name)  # 不在优先列表中，按名称排序

        leagues.sort(key=sort_key)
    else:
        leagues.sort()  # 如果没有配置排序，按名称排序

    # 判断用户是否登录，获取收藏的联赛列表
    # _auth = auth.get_auth()
    # favor_leagues = []
    # if _auth and verify_token(_auth.get('token')):
    #     mbid = g.user.id
    #     favor_leagues = [row[0] for row in
    #                      AppFavourite.query.filter_by(mb_id=mbid).with_entities(AppFavourite.league).all()]
    favor_leagues = [row[0] for row in
                     AppFavourite.query.filter_by(mb_id=g.user.id).with_entities(AppFavourite.league).all()]

    # 分页操作
    total = len(items)
    page_num = int(total / limit) + 1
    right_bound = current_page * limit
    paged_items = items[(current_page - 1) * limit: right_bound if right_bound < len(items) else len(items)]

    return jsonify({
        'items': paged_items,
        'total': total,
        'leagues': leagues,
        'favor_leagues': favor_leagues,
    })
