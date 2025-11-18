import pytz

from app_server import app, db, auth, app_opt
from app_server.controller.AppUserController import verify_token
from app_server.model.AppFavouriteModel import AppFavourite
from app_server.model.AppLeagueTeamScraperModel import LeagueTeamScraperModel
from app_server.model.MatchModel import Match, MatchAttr, VipMatchAttr
from app_server.model.MatchResultModel import Result
from flask import g, request, jsonify, Blueprint
from app_server.utils import OrmUttil
from sqlalchemy import or_, func, and_
import json
from datetime import datetime, timezone, timedelta
from app_server.model import Redis

match = Blueprint('match', __name__)
key_prefix = 'live_matches'

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
    ot_dict = {
        'single': {'1', '2', '6', '8', '10'},
        'mix': {'4', '5', '7', '9'},
        'old_mix': {'4', '5'}
    }
    current_page = request.args.get('page', type=int, default=1)
    limit = request.args.get('limit', type=int, default=20)

    match_id = request.args.get('matchId')

    # key_word = request.args.get('key_word')
    odds_type = request.args.get('odds_type')
    sub_leagues = request.args.get('sub_leagues')
    match_date = request.args.get('match_date', default='today')
    time_zone_hours = request.args.get('time_zone_hours', type=float, default=6.5)
    if odds_type:
        print('dict:%s' % ot_dict[odds_type])
    print(">>>>>", request.args)

    cache_key = f"{key_prefix}|%s" % odds_type

    # if g.user.IS_VIP:
    #     print("match vip requesting...")
    #     cache_key = "live_matchs|%s_vip" % odds_type
    #     if odds_type_ex:
    #         cache_key = "live_matchs|%s_vip" % odds_type_ex

    match_caches = Redis.read(cache_key)
    # match_caches = None

    if not match_caches:
        return jsonify({
            'items': [],
            'total': 0,
            'allPage': 0,
            'leagues': [],
            'favor_leagues': [],
        })

    items = json.loads(match_caches)

    # start_time = datetime.now().astimezone(timezone(timedelta(hours=8)))
    # target_now = datetime.now(timezone(timedelta(hours=time_zone_hours)))
    # target_now_date = target_now.date()
    # # start_time = now_utc = now.astimezone(timezone(timedelta(hours=time_zone_hours)))
    #
    # end_time = datetime.strptime("%s 23:59:59" % target_now_date, "%Y-%m-%d %H:%M:%S").astimezone(timezone(timedelta(hours=time_zone_hours)))
    # print("start_time:", start_time, "end_time:", end_time)
    #
    # if match_date == 'tomorrow':
    #     start_time = datetime.strptime("%s 00:00:00" % (target_now_date + timedelta(days=1)), "%Y-%m-%d %H:%M:%S").astimezone(timezone(timedelta(hours=time_zone_hours)))
    #     end_time = start_time + timedelta(days=1, hours=24)

    server_now = datetime.now(pytz.timezone('Asia/Shanghai'))
    user_timezone = pytz.FixedOffset(time_zone_hours * 60)
    user_start = server_now.astimezone(user_timezone)
    user_date = user_start.date()

    # Always return both today and tomorrow data
    # Set start time to today 00:00:00 and end time to tomorrow 23:59:59
    custom_tz = timezone(timedelta(hours=time_zone_hours))
    user_start = datetime(user_date.year, user_date.month, user_date.day, tzinfo=custom_tz)
    user_end = user_start + timedelta(days=2)  # Include both today and tomorrow
    print('user_start:', user_start, 'user_end:', user_end)

    valid_items = []
    today_date = user_start.date()
    tomorrow_date = today_date + timedelta(days=1)
    
    for item in items:
        source_match_time = datetime.strptime(item['MATCH_TIME'], "%Y-%m-%d %H:%M:%S").astimezone(timezone(timedelta(hours=8)))
        target_match_time = source_match_time.astimezone(timezone(timedelta(hours=time_zone_hours)))
        print("source_match_time:", source_match_time, "target_match_time:", target_match_time)
        if not (user_start <= target_match_time < user_end):
            continue
        item['LOCAL_MATCH_TIME'] = target_match_time.strftime("%Y-%m-%d %H:%M:%S")

        match_date = target_match_time.date()
        if match_date == today_date:
            item['MATCH_DAY'] = 'today'
        elif match_date == tomorrow_date:
            item['MATCH_DAY'] = 'tomorrow'
        else:
            item['MATCH_DAY'] = 'other'
            
        valid_items.append(item)

    items = valid_items

    # 联赛排序
    top_leagues = {'Spain Primera Division',
                   'Italy Serie A',
                   'Germany Bundesliga 1',
                   'France Ligue 1',
                   'English Premier League',
                   'English League Championship'}
    leagues = list({u['LEAGUE'] for u in items})
    leagues.sort()
    leagues.sort(key=lambda x: x in top_leagues, reverse=True)
    # 判断用户是否登录
    _auth = auth.get_auth()
    favor_leagues = []
    if _auth and verify_token(_auth.get('token')):
        mbid = g.user.id
        favor_leagues = [row[0] for row in AppFavourite.query.filter_by(mb_id=mbid).with_entities(AppFavourite.league).all()]
    # 联赛过滤
    if sub_leagues:
        sub_leagues = set(sub_leagues.split(","))
        print(sub_leagues)
        items = [i for i in items if i['LEAGUE'] in sub_leagues]

    # print("got the sub leagues", items)
    # 分页操作
    total = len(items)
    page_num = int(total / limit) + 1
    right_bound = current_page * limit
    paged_items = items[(current_page - 1) * limit: right_bound if right_bound < len(items) else len(items)]

    # 获取比赛图标，改为更新redis时缓存
    # for item in paged_items:
    #     item['home_logo'] = LeagueTeamScraperModel.get_match_icon(item['HOST_TEAM_WEBID'])
    #     item['away_logo'] = LeagueTeamScraperModel.get_match_icon(item['GUEST_TEAM_WEBID'])

    return jsonify({
        'items': paged_items,
        'total': len(items),
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
    attrs = MatchAttr.query.filter(and_(MatchAttr.MATCH_ID.in_(matches), MatchAttr.MATCH_ATTR_TYPE.in_({'1', '2', '4', '5', '8', '9', '10'}))).all()

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
                attr = VipMatchAttr.query.filter(and_(VipMatchAttr.MATCH_ID == det['matchId'], VipMatchAttr.MATCH_ATTR_TYPE == det['attrType'])).one_or_none()
            if not attr:
                attr = MatchAttr.query.filter(and_(MatchAttr.MATCH_ID == det['matchId'], MatchAttr.MATCH_ATTR_TYPE == det['attrType'])).one_or_none()
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
    top_leagues = {'Spain Primera Division',
                   'Italy Serie A',
                   'Germany Bundesliga 1',
                   'France Ligue 1',
                   'English Premier League',
                   'English League Championship'}

    items = []
    if match_caches:
        items = json.loads(match_caches)
    # 联赛排序

    mbid = g.user.id
    favor_leagues = [row[0] for row in AppFavourite.query.filter_by(mb_id=mbid).with_entities(AppFavourite.league).all()]

    valid_items = []
    for item in items:
        if item['LEAGUE'] not in favor_leagues:
            continue
        valid_items.append(item)

    leagues = list({u['LEAGUE'] for u in valid_items})
    leagues.sort()
    leagues.sort(key=lambda x: x in top_leagues, reverse=True)
    # 分页操作
    total = len(valid_items)
    page_num = int(total / limit) + 1
    right_bound = current_page * limit
    paged_items = valid_items[(current_page - 1) * limit: right_bound if right_bound < len(valid_items) else len(valid_items)]

    return jsonify({
        'items': paged_items,
        'total': total,
        'leagues': leagues,
        'favor_leagues': favor_leagues,
    })
