from re import A
import traceback
import requests
import json
import time
import os
import logging
from datetime import datetime, timedelta, timezone
from sqlalchemy import and_, or_, func

from Orm import DBSession, Match, MatchAttr, Redis, LeagueTteamScraper
from model.MAppLeagueModel import MAppLeague
from model.SysBisDictModel import SysBisDict
from ibet_match import same_match_hide
from env_config import Config

# 从配置文件读取配置
API_URL = Config.API_URL
API_TOKEN = Config.API_TOKEN
SYNC_STATUS_FILE = Config.SYNC_STATUS_FILE
LOG_DIR = Config.LOG_DIR

# 确保日志目录存在
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# 设置日志记录器，按天存储
def setup_logger():
    """设置日志记录器"""
    today = datetime.now().strftime("%Y-%m-%d")
    log_file = os.path.join(LOG_DIR, f"ibet_runner2_{today}.log")
    
    logger = logging.getLogger('ibet_runner2')
    logger.setLevel(logging.INFO)
    
    # 避免重复添加handler
    if not logger.handlers:
        # 文件handler
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        
        # 控制台handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # 格式化器
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # 添加handler
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
    
    return logger

# 初始化日志记录器
logger = setup_logger()

# 获取爬虫配置（全局）
scraper_cfg = SysBisDict.get_scraper_config()

# 混合单笔赔率对
single_mix_pair = {
    '1': '4', '2': '5',
    '4': '1', '5': '2',
}

# 爬取的联赛
scraper_leagues = MAppLeague.get_scraper_leagues()

class HomeAway:
    home = '1'
    away = '2'

def load_sync_status():
    """
    加载同步状态
    :return: 同步状态字典
    """
    if os.path.exists(SYNC_STATUS_FILE):
        try:
            with open(SYNC_STATUS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载同步状态失败: {e}")
    
    # 返回默认状态
    return {
        "last_sync_time": None,
        "last_update_time": None,
        "api_match_id_mapping": {}
    }

def save_sync_status(status):
    """
    保存同步状态
    :param status: 同步状态字典
    """
    try:
        with open(SYNC_STATUS_FILE, 'w', encoding='utf-8') as f:
            json.dump(status, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"保存同步状态失败: {e}")

def fetch_match_data(api_time):
    """
    从API获取比赛数据
    :param api_time: API请求的时间参数
    :return: API响应数据
    """
    headers = {
        'Content-Type': 'application/json'
    }
    
    payload = {
        "token": API_TOKEN,
        "time": api_time
    }
    
    try:
        logger.info(f"请求API数据，时间参数: {api_time}")
        response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"获取API数据失败: {e}")
        return None

def cache_to_redis_by_time(start_time, end_time=None):
    """
    将比赛数据缓存到Redis
    :param start_time: 开始时间
    :param end_time: 结束时间（可选）
    """
    logger.info("开始缓存到Redis")
    cache_time = time.time()
    db_session = DBSession()

    cache_keys = ['single', 'mix', 'old_mix', '1', '2', 'wdl']
    cache_dicts = {
        'single': {'1', '2','6','18', '10','3'},
        'mix': {'4', '5', '7','19', '11'},
        'old_mix': {'4', '5'},
        '1': {"1"},
        '2': {"2"}
    }
    # 存放各类型的 比赛: 赔率
    cache_list = {k: {} for k in cache_keys}
    match_list = db_session.query(Match).filter(and_(Match.MATCH_TIME >= start_time, Match.MATCH_TIME >= start_time)).filter(or_(Match.hide.is_(None), Match.hide != "1"))
    if end_time:
        match_list = match_list.filter(Match.MATCH_TIME <= end_time, Match.CLOSING_TIME <= end_time)

    # 获取排序值大于0的联赛进行排序
    leagues_sorts = MAppLeague.get_scraper_leagues(db_session, True)
    sorts_leagues = {'Spain Primera Division',
     'Italy Serie A',
     'Germany Bundesliga 1',
     'France Ligue 1',
     'English Premier League',
     'English League Championship'}
    if leagues_sorts:
        sorts_leagues = leagues_sorts
    logger.info(f"排序的联赛: {sorts_leagues}")
    match_list = match_list.filter(and_(Match.IS_GAME_OVER == "0", Match.CLOSING_STATE == "0")).order_by(Match.LEAGUE.in_(sorts_leagues).desc()).all()
    logger.info(f"缓存的比赛数量: {len(match_list)}")

    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow_start = today_start + timedelta(days=1)
    day_after_tomorrow_start = today_start + timedelta(days=2)
    day_after_tomorrow_end = day_after_tomorrow_start + timedelta(days=1)

    today_count = 0
    tomorrow_count = 0
    day_after_tomorrow_count = 0

    for match in match_list:
        match_time = match.MATCH_TIME
        if today_start <= match_time < tomorrow_start:
            today_count += 1
        elif tomorrow_start <= match_time < day_after_tomorrow_start:
            tomorrow_count += 1
        elif day_after_tomorrow_start <= match_time < day_after_tomorrow_end:
            day_after_tomorrow_count += 1

    logger.info(f"今天比赛数量: {today_count}")
    logger.info(f"明天比赛数量: {tomorrow_count}")
    logger.info(f"后天比赛数量: {day_after_tomorrow_count}")

    matches_dict = {m.MATCH_ID: m.to_cache_dict() for m in match_list}
    all_attrs = db_session.query(MatchAttr).filter(MatchAttr.MATCH_ID.in_(matches_dict)).all()
    attrs_dict = {a.MATCH_ATTR_ID: a.to_cache_dict() for a in all_attrs}

    cache_attrs = []
    for attr in all_attrs:
        attr = attr.to_cache_dict()
        match_id = attr["MATCH_ID"]
        match_web_id = attr["MATCH_WEB_ID"]
        attr_type = attr['MATCH_ATTR_TYPE']
        if attr_type in {'6', '7'}:
            attr['REAL_ODDS'] = "%s/%s" % (attr['ODDS'], attr['ODDS_GUEST'])
        else:
            sign = "-" if attr['DRAW_BUNKO'] == "1" else "+"
            attr['REAL_ODDS'] = "%s%s%s" % (attr['LOSE_BALL_NUM'], sign, attr['DRAW_ODDS'])
        cache_attrs.append(attr)

        for k, v in cache_dicts.items():
            if attr_type not in v:
                continue
            if match_id not in cache_list[k]:
                cache_list[k][match_id] = matches_dict[match_id].copy()
                cache_list[k][match_id]['ATTR'] = []
                # 修正球队图标和球队名称
                home_team = LeagueTteamScraper.get_match_team(cache_list[k][match_id]['HOST_TEAM_WEBID'], session=db_session)
                if home_team and home_team.logo:
                    cache_list[k][match_id]['home_logo'] = home_team.logo
                if home_team and home_team.show_name:
                    cache_list[k][match_id]['HOST_TEAM'] = home_team.show_name
                guest_team = LeagueTteamScraper.get_match_team(cache_list[k][match_id]['GUEST_TEAM_WEBID'], session=db_session)
                if guest_team and guest_team.logo:
                    cache_list[k][match_id]['away_logo'] = guest_team.logo
                if guest_team and guest_team.show_name:
                    cache_list[k][match_id]['GUEST_TEAM'] = guest_team.show_name

                # 删除WEBID字段以减少缓存大小（logo已添加，不再需要）
                cache_list[k][match_id].pop('HOST_TEAM_WEBID', None)
                cache_list[k][match_id].pop('GUEST_TEAM_WEBID', None)

            pair_attr_id = f'{match_web_id}_{single_mix_pair.get(attr_type)}'
            if attr_type in single_mix_pair and pair_attr_id not in attrs_dict:
                # 混合单笔赔率不是同时存在跳过
                continue
            cache_list[k][match_id]['ATTR'].append(attr)

    # 最终结果
    items = {k: [] for k in cache_keys}

    # 爬取的联赛（过滤仅显示目标联赛）
    include_leagues = scraper_leagues;  # 联赛过滤

    for match in match_list:
        match_id = match.MATCH_ID
        league_name = match.LEAGUE
        # 过滤未录入联赛
        if league_name.upper() not in include_leagues:
            continue
        for k, v in cache_list.items():
            if match_id in v:
                items[k].append(v[match_id])
    for k, v in items.items():
        Redis.set("live_matches|%s" % k, json.dumps(v), Config.CACHE_EXPIRE_TIME)
    # 缓存时间由配置文件控制
    Redis.set("live_odds", json.dumps(cache_attrs), Config.CACHE_EXPIRE_TIME)

    db_session.commit()
    db_session.close()
    logger.info(f"缓存完毕，耗时: {time.time() - cache_time:.2f}秒")


def cache_to_redis():
    """
    缓存比赛数据到Redis
    """
    # 缓存无关时区, 只需缓存到第三天的10点30分之前的比赛（服务器时间12点）
    now = datetime.now()
    now_utc = now.astimezone(timezone.utc)
    day_after_tomorrow_end_utc = now_utc + timedelta(days=2, hours=12, minutes=00, seconds=59)
    cache_to_redis_by_time(now, day_after_tomorrow_end_utc)


def sync_matches():
    """
    同步比赛数据主函数
    """
    # 预处理
    start_time = time.time()
    logger.info("开始同步比赛数据")
    
    exe_on = scraper_cfg.scraperEnabled
    if not exe_on:
        logger.warning("爬虫功能未启用")
        return
    
    # 获取赔率配置
    single_odds_on = scraper_cfg.singleSpiderEnabled # 单式（开启）
    multi_odds_on = scraper_cfg.mixParlaySpiderEnabled # 混合（开启）
    odds_cond_1 = scraper_cfg.minOddWinLose # 单式-胜负盘HDP（最小赔率）
    odds_cond_2 = scraper_cfg.minOddBallNum # 单式-大小盘O/U（最小球数）
    odds_cond_4 = scraper_cfg.minOddCond4 # 混合-胜负盘（最小赔率）
    odds_cond_5 = scraper_cfg.minOddCond5 # 混合-大小盘（最小球数）
    odds_cond_6 = scraper_cfg.minOddOddEven  # 单式-单双最小赔率
    logger.info(f"赔率配置: 单式胜负盘={odds_cond_1}, 单式大小盘={odds_cond_2}, 混合胜负盘={odds_cond_4}, 混合大小盘={odds_cond_5}, 单双={odds_cond_6}")
    
    # 调试配置
    test_check_match_list = getattr(Config, 'TEST_CHECK_MATCH_LIST', [])
    logger.info(f"调试比赛列表: {test_check_match_list}")
    
    # 加载同步状态
    sync_status = load_sync_status()
    last_update_time = sync_status.get("last_update_time")
    
    # 确定API请求时间参数
    if last_update_time:
        # 使用上次同步的最大updateTime作为起始点
        api_time = last_update_time
        logger.info(f"增量同步，从 {api_time} 开始")
    else:
        # 首次同步，使用当前时间
        api_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logger.info(f"全量同步，从 {api_time} 开始")
    
    db_session = DBSession()
    
    try:
        # 获取API数据
        api_data = fetch_match_data(api_time)
        if not api_data or 'data' not in api_data:
            logger.error("API返回数据无效")
            return
        
        # 检查API返回状态
        if api_data.get('code') != 0:
            logger.error(f"API返回错误: {api_data.get('msg', '未知错误')}")
            return
        
        # 比赛数据在data.matchList中
        if 'matchList' not in api_data['data']:
            logger.error("API返回数据中缺少matchList")
            return
            
        matches_data = api_data['data']['matchList']
        if not matches_data:
            logger.info("API返回的比赛数据为空")
            # 即使没有数据，也要更新同步状态
            sync_status["last_sync_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            sync_status["last_update_time"] = api_time  # 使用请求时间作为updateTime
            save_sync_status(sync_status)
            return
        
        logger.info(f"获取到 {len(matches_data)} 条比赛数据")
        
        # 查询已有比赛
        old_match_queries = db_session.query(Match).filter(
            Match.MATCH_TIME > (datetime.now() - timedelta(days=1))
        ).all()
        
        old_matches = {}
        live_matches = set()
        abort_matches = set()
        live_match_ids = set()
        
        for match in old_match_queries:
            web_id = int(match.MATCH_WEB_ID or 0)
            if match.MANUAL_ON == "1" or match.IS_GAME_OVER == "1":
                abort_matches.add(web_id)
                continue
            old_matches[web_id] = match
            
            if match.CLOSING_TIME > datetime.now() and match.hide == "0":
                live_matches.add(web_id)
                live_match_ids.add(match.MATCH_ID)
        
        # 查询已有赔率
        old_odds_dict = {}
        old_let_teams = {}
        old_odds_queries = db_session.query(MatchAttr).filter(
            MatchAttr.MATCH_ID.in_(live_match_ids)
        ).all()
        
        for row in old_odds_queries:
            old_odds_dict[row.MATCH_ID] = row
            if row.LOSE_TEAM:
                old_let_teams[row.MATCH_ID] = row.LOSE_TEAM
        
        # 处理API返回的比赛数据
        match_count = 0
        max_update_time = last_update_time  # 记录本次同步的最大updateTime
        
        for match_data in matches_data:
            try:
                # 获取比赛的updateTime
                update_time = match_data.get('updateTime')
                if update_time and (max_update_time is None or update_time > max_update_time):
                    max_update_time = update_time
                
                # 检查联赛范围
                league_name = match_data.get('league', '')
                if league_name.upper() not in scraper_leagues:
                    logger.debug(f"跳过不在配置范围内的联赛: {league_name}")
                    continue
                
                process_match_data(match_data, db_session, old_matches, live_matches, abort_matches, {
                    'single_odds_on': single_odds_on,
                    'multi_odds_on': multi_odds_on,
                    'odds_cond_1': odds_cond_1,
                    'odds_cond_2': odds_cond_2,
                    'odds_cond_4': odds_cond_4,
                    'odds_cond_5': odds_cond_5,
                    'odds_cond_6': odds_cond_6
                })
                match_count += 1
            except Exception as e:
                logger.error(f"处理比赛数据时出错: {e}")
                traceback.print_exc()
                continue
        
        # 隐藏不再活跃的比赛
        hidden_count = 0
        for web_id in live_matches:
            if web_id in old_matches:
                old_match = old_matches[web_id]
                old_match.hide = "1"
                old_match.HIDE_REASON = "比赛不再活跃"
                hidden_count += 1
                logger.debug(f"隐藏比赛: {old_match.MATCH_DESC} (ID: {old_match.MATCH_ID})")
        
        if hidden_count > 0:
            logger.info(f"隐藏了 {hidden_count} 场不再活跃的比赛")
        
        # 提交事务
        db_session.commit()
        
        # 更新同步状态
        sync_status["last_sync_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sync_status["last_update_time"] = max_update_time
        save_sync_status(sync_status)
        
        sync_time = time.time() - start_time
        logger.info(f"同步完成，处理了 {match_count} 场比赛，耗时 {sync_time:.2f} 秒")
        logger.info(f"下次同步将从 {max_update_time} 开始")
        
    except Exception as e:
        logger.error(f"同步比赛数据时出错: {e}")
        traceback.print_exc()
        db_session.rollback()
    finally:
        db_session.close()
        logger.info("同步任务结束")

def process_match_data(match_data, db_session, old_matches, live_matches, abort_matches, odds_config=None):
    """
    处理单场比赛数据
    :param match_data: API返回的单场比赛数据
    :param db_session: 数据库会话
    :param old_matches: 已有比赛字典
    :param live_matches: 活跃比赛集合
    :param abort_matches: 已中止比赛集合
    :param odds_config: 赔率配置字典
    """
    # 解析比赛基本信息
    api_match_id = match_data.get('id')  # API返回的比赛ID，直接作为系统ID
    match_web_id = match_data.get('matchWebId')
    if not match_web_id:
        logger.warning("比赛数据缺少matchWebId")
        return
    
    match_web_id = int(match_web_id)
    
    # 去除已禁用或者已结束的比赛
    if match_web_id in abort_matches:
        logger.debug(f"比赛已中止或结束: {match_web_id}")
        return
    
    # 解析比赛时间
    match_time_str = match_data.get('matchTime')
    if not match_time_str:
        logger.warning(f"比赛数据缺少matchTime: {match_web_id}")
        return
    
    try:
        match_time = datetime.strptime(match_time_str, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        try:
            # 尝试其他可能的时间格式
            match_time = datetime.fromisoformat(match_time_str.replace('Z', '+00:00'))
            # 转换为本地时间
            if match_time.tzinfo:
                match_time = match_time.astimezone().replace(tzinfo=None)
        except ValueError:
            logger.error(f"无法解析比赛时间: {match_time_str}")
            return
    
    # 获取matchMdTime，如果没有则使用matchTime减去1.5小时
    match_md_time_str = match_data.get('matchMdTime')
    if match_md_time_str:
        try:
            match_md_time = datetime.strptime(match_md_time_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            try:
                match_md_time = datetime.fromisoformat(match_md_time_str.replace('Z', '+00:00'))
                if match_md_time.tzinfo:
                    match_md_time = match_md_time.astimezone().replace(tzinfo=None)
            except ValueError:
                logger.warning(f"无法解析matchMdTime: {match_md_time_str}，使用默认计算")
                match_md_time = match_time - timedelta(hours=1.5)
    else:
        match_md_time = match_time - timedelta(hours=1.5)
    
    match_desc = match_data.get('matchDesc', '')
    league_name = match_data.get('league', '')
    host_team = match_data.get('hostTeam', '')
    guest_team = match_data.get('guestTeam', '')
    
    # 解析比赛比分
    host_team_result = match_data.get('hostTeamResult', '') or ''
    guest_team_result = match_data.get('guestTeamResult', '') or ''
    is_game_over = str(match_data.get('isGameOver', 0))
    
    # 解析接口返回的hide字段
    api_hide = match_data.get('hide', 0)
    api_hide = str(api_hide) if api_hide is not None else "0"
    
    # 调试逻辑
    test_check_match_list = getattr(Config, 'TEST_CHECK_MATCH_LIST', [])
    is_test_match = False
    if host_team in test_check_match_list or guest_team in test_check_match_list:
        is_test_match = True
        logger.info(f"调试比赛: {match_desc}")
        logger.info(f"比赛信息: WebID={match_web_id}, 联赛={league_name}, 时间={match_time}")
        logger.info(f"比赛数据: {json.dumps(match_data, ensure_ascii=False, indent=2)}")
    
    # 从live_matches中移除当前比赛（表示比赛仍然活跃）
    if match_web_id in live_matches:
        live_matches.remove(match_web_id)
    
    # 检查比赛是否已存在
    if match_web_id in old_matches:
        # 更新现有比赛
        old_match = old_matches[match_web_id]
        match_id = old_match.MATCH_ID
        
        # 更新比赛基本信息
        old_match.MATCH_TIME = match_time
        old_match.CLOSING_TIME = match_time
        old_match.MATCH_MD_TIME = match_md_time
        old_match.MATCH_DESC = match_desc
        old_match.LEAGUE = league_name
        old_match.HOST_TEAM = host_team
        old_match.GUEST_TEAM = guest_team
        old_match.hide = api_hide
        old_match.UPDATE_TIME = datetime.now()
        # 如果接口要求隐藏，设置隐藏原因
        if api_hide == "1":
            hide_reason = match_data.get('hideReason') or ''
            old_match.HIDE_REASON = "API_HIDE：" + hide_reason
        # 清除因无赔率而隐藏的标志
        elif old_match.HIDE_REASON == "NO_ODDS":
            old_match.HIDE_REASON = None
            logger.debug(f"恢复因无赔率而隐藏的比赛: {match_desc}")
        
        # 只有当系统没有比分时，才更新比分
        # 这样可以避免覆盖已有的比分数据
        if not old_match.HOST_TEAM_RESULT and host_team_result and not old_match.GUEST_TEAM_RESULT and guest_team_result:
            old_match.HOST_TEAM_RESULT = host_team_result
            old_match.GUEST_TEAM_RESULT = guest_team_result
            #修正比赛状态为结束
            old_match.status = "3"
        
        # 只有当系统比赛未结束时，才更新比赛状态
        if old_match.IS_GAME_OVER == "0" and is_game_over == "1":
            old_match.IS_GAME_OVER = is_game_over
        
        logger.debug(f"更新比赛: {match_desc} (ID: {match_id})")
    else:
        # 检查是否存在重复比赛
        match_repeated = False
        for old_match in old_matches.values():
            if old_match.LEAGUE == league_name and old_match.MATCH_DESC.replace(" ", "").lower() == match_desc.replace(" ", "").lower():
                old_match_id = int(old_match.MATCH_WEB_ID)
                if old_match_id in live_matches:
                    live_matches.remove(old_match_id)
                old_match.MATCH_TIME = match_time
                old_match.CLOSING_TIME = match_time
                old_match.MATCH_MD_TIME = match_md_time
                old_match.MATCH_WEB_ID = match_web_id
                match_id = old_match.MATCH_ID
                match_repeated = True
                
                # 重复比赛的时候赔率给他删了
                db_session.query(MatchAttr).filter(MatchAttr.MATCH_ID == match_id).delete()
                logger.debug(f"发现重复比赛，更新WebID: {old_match.MATCH_DESC} -> {match_web_id}")
                break
        
        if not match_repeated:
            # 在新增前，检查是否存在相同ID的比赛
            # 这是为了处理match_web_id变化但api_match_id不变的情况
            existing_match = db_session.query(Match).filter(
                Match.MATCH_ID == api_match_id
            ).first()

            if existing_match:
                # 如果ID已存在，则按ID更新比赛信息
                match_id = existing_match.MATCH_ID
                existing_match.MATCH_TIME = match_time
                existing_match.CLOSING_TIME = match_time
                existing_match.MATCH_MD_TIME = match_md_time
                existing_match.MATCH_DESC = match_desc
                existing_match.LEAGUE = league_name
                existing_match.HOST_TEAM = host_team
                existing_match.GUEST_TEAM = guest_team
                existing_match.MATCH_WEB_ID = match_web_id  # 更新match_web_id
                existing_match.HOST_TEAM_WEBID = match_data.get('hostTeamWebid', '')
                existing_match.GUEST_TEAM_WEBID = match_data.get('guestTeamWebid', '')
                existing_match.hide = api_hide
                existing_match.UPDATE_TIME = datetime.now()

                # 如果接口要求隐藏，设置隐藏原因
                if api_hide == "1":
                    hide_reason = match_data.get('hideReason') or ''
                    existing_match.HIDE_REASON = "API_HIDE：" + hide_reason
                # 清除因无赔率而隐藏的标志
                elif existing_match.HIDE_REASON == "NO_ODDS":
                    existing_match.HIDE_REASON = None

                # 只有当系统没有比分时，才更新比分
                if not existing_match.HOST_TEAM_RESULT and host_team_result and not existing_match.GUEST_TEAM_RESULT and guest_team_result:
                    existing_match.HOST_TEAM_RESULT = host_team_result
                    existing_match.GUEST_TEAM_RESULT = guest_team_result
                    # 修正比赛状态为结束
                    existing_match.status = "3"

                # 只有当系统比赛未结束时，才更新比赛状态
                if existing_match.IS_GAME_OVER == "0" and is_game_over == "1":
                    existing_match.IS_GAME_OVER = is_game_over

                old_matches[match_web_id] = existing_match
                # 删除旧的赔率数据
                db_session.query(MatchAttr).filter(MatchAttr.MATCH_ID == match_id).delete()
                logger.info(f"ID已存在，按ID更新比赛: {match_desc} (ID: {match_id}, WebID: {match_web_id})")
            else:
                # 创建新比赛，直接使用API返回的比赛ID
                match_id = api_match_id
                new_match = Match(
                    ID=match_id,
                    MATCH_ID=match_id,
                    MATCH_DESC=match_desc,
                    MATCH_TIME=match_time,
                    CLOSING_TIME=match_time,
                    MATCH_MD_TIME=match_md_time,
                    HOST_TEAM=host_team,
                    LEAGUE=league_name,
                    GUEST_TEAM=guest_team,
                    MATCH_WEB_ID=match_web_id,
                    IS_GAME_OVER=is_game_over,
                    HOST_TEAM_WEBID=match_data.get('hostTeamWebid', ''),
                    GUEST_TEAM_WEBID=match_data.get('guestTeamWebid', ''),
                    hide=api_hide,
                    UPDATE_TIME=datetime.now()
                )
                # 如果接口要求隐藏，设置隐藏原因
                if api_hide == "1":
                    hide_reason = match_data.get('hideReason') or ''
                    new_match.HIDE_REASON = "API_HIDE：" + hide_reason

                # 设置比分
                if host_team_result and guest_team_result:
                    new_match.HOST_TEAM_RESULT = host_team_result
                    new_match.GUEST_TEAM_RESULT = guest_team_result
                    # 修正比赛状态为结束
                    new_match.status = "3"

                db_session.add(new_match)
                old_matches[match_web_id] = new_match
                # 检查是否存在重复比赛
                same_match_hide(db_session, new_match, [])
                logger.debug(f"创建新比赛: {match_desc} (ID: {match_id})")
    
    # 处理赔率数据
    has_valid_odds = process_match_odds(match_data, db_session, match_id, match_web_id, odds_config)
    
    # 如果没有有效的赔率，隐藏比赛
    if not has_valid_odds:
        if match_web_id in old_matches:
            old_match = old_matches[match_web_id]
            old_match.hide = "1"
            old_match.HIDE_REASON = "NO_ODDS"
            logger.debug(f"隐藏没有有效赔率的比赛: {match_desc}")
        else:
            # 如果是新比赛且没有有效赔率，删除比赛
            db_session.query(Match).filter(Match.MATCH_ID == match_id).delete()
            logger.debug(f"删除没有有效赔率的新比赛: {match_desc}")

def process_match_odds(match_data, db_session, match_id, match_web_id, odds_config=None):
    """
    处理比赛赔率数据
    :param match_data: API返回的比赛数据
    :param db_session: 数据库会话
    :param match_id: 比赛ID
    :param match_web_id: 比赛网页ID
    :param odds_config: 赔率配置字典
    :return: 是否有符合条件的赔率被添加
    """
    # 先删除该比赛的所有赔率数据，避免重复
    db_session.query(MatchAttr).filter(
        MatchAttr.MATCH_ID == match_id
    ).delete()
    
    # 获取赔率数据，API返回的是attrList
    odds_data = match_data.get('attrList', [])
    
    has_valid_odds = False
    
    # 调试逻辑
    test_check_match_list = getattr(Config, 'TEST_CHECK_MATCH_LIST', [])
    host_team = match_data.get('hostTeam', '')
    guest_team = match_data.get('guestTeam', '')
    is_test_match = host_team in test_check_match_list or guest_team in test_check_match_list
    
    if is_test_match:
        logger.info(f"调试比赛赔率: {match_data.get('matchDesc', '')}")
        logger.info(f"赔率数据: {json.dumps(odds_data, ensure_ascii=False, indent=2)}")
    
    for odd_item in odds_data:
        try:
            # 直接使用API返回的ID
            api_attr_id = odd_item.get('id')
            match_attr_id = odd_item.get('matchAttrId')
            match_attr_type = odd_item.get('matchAttrType', '1')
            
            # 赔率范围控制
            if odds_config:
                # 获取赔率值（API返回的已经是除以10后的值）
                odds = float(odd_item.get('odds', '0'))
                odds_guest = float(odd_item.get('oddsGuest', '0'))
                
                # 根据不同玩法类型检查赔率范围
                if match_attr_type == '1':  # 单式-胜负盘
                    if not odds_config.get('single_odds_on') or odds * 100 < odds_config.get('odds_cond_1', 0):
                        logger.debug(f"跳过单式胜负盘赔率: {odds*100} < {odds_config.get('odds_cond_1')}")
                        continue
                elif match_attr_type == '2':  # 单式-大小盘
                    if not odds_config.get('single_odds_on') or odds * 100 < odds_config.get('odds_cond_2', 0):
                        logger.debug(f"跳过大小盘赔率: {odds*100} < {odds_config.get('odds_cond_2')}")
                        continue
                elif match_attr_type == '4':  # 混合-胜负盘
                    if not odds_config.get('multi_odds_on') or odds * 100 < odds_config.get('odds_cond_4', 0):
                        logger.debug(f"跳过混合胜负盘赔率: {odds*100} < {odds_config.get('odds_cond_4')}")
                        continue
                elif match_attr_type == '5':  # 混合-大小盘
                    if not odds_config.get('multi_odds_on') or odds * 100 < odds_config.get('odds_cond_5', 0):
                        logger.debug(f"跳过混合大小盘赔率: {odds*100} < {odds_config.get('odds_cond_5')}")
                        continue
                elif match_attr_type == '6':  # 单式-单双
                    if not odds_config.get('single_odds_on') or (odds * 100 < odds_config.get('odds_cond_6', 0) or odds_guest * 100 < odds_config.get('odds_cond_6', 0)):
                        logger.debug(f"跳过单双赔率: {odds*100}/{odds_guest*100} < {odds_config.get('odds_cond_6')}")
                        continue
            
            # 创建赔率记录，直接使用API返回的ID
            match_attr = MatchAttr(
                ID=api_attr_id,
                MATCH_ATTR_ID=match_attr_id,
                MATCH_ATTR_DESC=odd_item.get('matchAttrDesc', ''),
                MATCH_ATTR_TYPE=match_attr_type,
                ODDS=odd_item.get('odds', '0'),
                ODDS_GUEST=odd_item.get('oddsGuest', '0'),
                DRAW_BUNKO=odd_item.get('drawBunko', '0'),
                DRAW_ODDS=odd_item.get('drawOdds', '0'),
                MATCH_ID=match_id,
                LOSE_TEAM=odd_item.get('loseTeam', '1'),
                LOSE_BALL_NUM=odd_item.get('loseBallNum', '0'),
                MATCH_WEB_ID=str(match_web_id),
                UPDATE_TIME=datetime.now()
            )
            
            # 处理特殊字段
            if 'csScore' in odd_item:
                match_attr.CS_SCORE = odd_item['csScore']
            if 'csIndex' in odd_item:
                match_attr.CS_INDEX = odd_item['csIndex']
            if 'remark' in odd_item:
                match_attr.REMARK = odd_item['remark']
            
            db_session.add(match_attr)
            has_valid_odds = True
            
        except Exception as e:
            logger.error(f"处理赔率数据时出错: {e}")
            traceback.print_exc()
            continue
    
    return has_valid_odds

def handle_match_status():
    """
    处理比赛状态
    1. 自动锁定比赛
    2. 将已开始的比赛状态更新为2
    3. 如果比赛的CLOSING_STATE为0且CLOSING_TIME已过，则更新CLOSING_STATE为1
    """
    # 先自动锁定比赛
    logger.info("自动锁定比赛")
    db_session = DBSession()
    now = datetime.now()
    matchs = db_session.query(Match).filter(Match.status == "1", Match.MATCH_TIME <= now).all()
    # 判断比赛是否已开始，如已开始则更新状态为2
    n = 0
    for match in matchs:
        n = n + 1
        update_info = {
            "status": "2",
        }
        if match.CLOSING_STATE == "0" and match.CLOSING_TIME <= now:
            update_info["CLOSING_STATE"] = "1"
        db_session.query(Match).filter(Match.ID == match.ID).update(update_info)

    db_session.commit()
    db_session.close()
    logger.info(f"自动锁定比赛数量: {n}")


def main():
    """
    主函数
    """
    # 打印配置信息
    Config.print_config()
    
    # 开始时间
    start_time = time.time()
    logger.info("开始同步比赛数据...")
    sync_matches()
    logger.info("比赛数据同步完成")
    
    # 处理比赛状态
    logger.info("开始处理比赛状态")
    try:
        handle_match_status()
        logger.info("比赛状态处理完成")
    except Exception as e:
        logger.error(f"处理比赛状态失败: {e}")
        traceback.print_exc()
    
    # 无论同步成功或失败，都缓存数据到Redis
    logger.info("开始缓存数据到Redis")
    try:
        cache_to_redis()
        logger.info("Redis缓存完成")
    except Exception as e:
        logger.error(f"Redis缓存失败: {e}")
        traceback.print_exc()
    
    # 结束时间
    end_time = time.time()
    logger.info(f"同步耗时: {end_time - start_time} 秒")

if __name__ == "__main__":
    main()