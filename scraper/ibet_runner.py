import traceback

from Orm import DBSession, Match, MatchAttr, Redis, LeagueTteamScraper
from sqlalchemy import and_, or_, func
from datetime import datetime, timedelta, date, timezone
import requests
import json
import time
import os
import re
from ibet_match import same_match_hide
from model.MAppLeagueModel import MAppLeague
from model.SysBisDictModel import SysBisDict
from utils.DataVo import ScraperCfgVo
from env_config import Config

# 获取爬虫配置（全局）
scraper_cfg = SysBisDict.get_scraper_config()
scraper_leagues = MAppLeague.get_scraper_leagues()

# 从配置中读取账号信息
username = Config.SCRAPER_USERNAME
password = Config.SCRAPER_PASSWORD

# 从配置中读取代理
proxy = Config.PROXY

# 从配置中读取headers
headers = Config.HEADERS

draw_bunko_dict = {
    '0': '+', '1': '-', 0: '+', 1: '-',
}

lose_team_dict = {
    '1': '主队', '2': '客队', 1: '主队', 2: '客队',
}
# 单笔混合odds对照
single_mix_pair = {
    '1': '4', '2': '5',
    '4': '1', '5': '2',

}


class HomeAway:
    home = '1'
    away = '2'


def get_page_validate(page):
    # 获取页面验证参数
    view_state = re.findall(r'VIEWSTATE\".*value=\"(.*)\"', page)[0]
    view_state_generator = re.findall(r'__VIEWSTATEGENERATOR\".*value=\"(.*)\"', page)[0]
    event_validation = re.findall(r'EVENTVALIDATION\".*value=\"(.*)\"', page)[0]
    return view_state, view_state_generator, event_validation


def check_cookie(cookies):
    try:
        resp = requests.get("https://www.ibet789.com/_View/AccInfo.aspx", cookies=cookies, proxies=proxy, headers=headers, timeout=7)
    except Exception as e:
        return False
    # print("the check page:", resp.text)
    with open("check_result.html", "w", encoding="utf-8") as f:
        f.write(resp.text)
    print("check result:", resp.url, resp.text != "")
    return "_View/AccInfo.aspx" in resp.url and resp.text != ""


def login():
    session = requests.session()
    resp = session.get("https://ibet789.com/", proxies=proxy, headers=headers)
    # print("login resp:", resp.status_code, resp.text)
    if not resp.text:
        print("get page fail")
        return None
    # 获取页面验证参数
    view_state, view_state_generator, event_validation = get_page_validate(resp.text)
    # 构造登录表单
    login_form = {
        "__EVENTTARGET": "",
        "__EVENTARGUMENT": "",
        "__VIEWSTATE": view_state,
        "__VIEWSTATEGENERATOR": view_state_generator,
        "__VIEWSTATEENCRYPTED": "",
        "__EVENTVALIDATION": event_validation,
        "txtUserName": username,
        "password": password,
        "btnSignIn": "Login"
    }

    # 提交登录表单
    session.post("https://www.ibet789.com/Default1_0.aspx", login_form, proxies=proxy, headers=headers)
    cookies = requests.utils.dict_from_cookiejar(session.cookies)
    return cookies


def get_cookies():
    cookie_path = "cookies"

    cookies = {}
    try:
        if os.path.isfile(cookie_path):
            with open(cookie_path, 'r', encoding='utf-8') as f:
                cookies = json.loads(f.read())
    except Exception as e:
        print("cookie check error", e)

    cookie_valid = check_cookie(cookies)
    # print("cookie valid?", cookie_valid)
    if not cookie_valid:
        cookies = login()
        cookie_valid = check_cookie(cookies)

    if cookie_valid:
        with open(cookie_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(cookies))
        return cookies

    return None


def get_matches(with_mix=False):
    # 预处理
    start_time = time.time()
    exe_on = scraper_cfg.scraperEnabled
    if not exe_on:
        return
    db_session = DBSession()

    single_odds_on = scraper_cfg.singleSpiderEnabled # 单式（开启）
    multi_odds_on = scraper_cfg.mixParlaySpiderEnabled # 混合（开启）
    print("mix en?", multi_odds_on, with_mix)

    odds_cond_1 = scraper_cfg.minOddWinLose # 单式-胜负盘HDP（最小赔率）
    odds_cond_2 = scraper_cfg.minOddBallNum # 单式-大小盘O/U（最小球数）
    odds_cond_4 = scraper_cfg.minOddCond4 # 混合-胜负盘（最小赔率）
    odds_cond_5 = scraper_cfg.minOddCond5 # 混合-大小盘（最小球数）
    odds_cond_6 = scraper_cfg.minOddOddEven  # 单式-单双最小赔率
    print("odds cond:", odds_cond_1, odds_cond_2, odds_cond_4, odds_cond_5, odds_cond_6)

    # 爬取的联赛
    include_leagues = scraper_leagues; # 联赛过滤
    # include_leagues = set(include_leagues.split(","))

    # 查询已有比赛
    old_match_queries = db_session.query(Match).filter(Match.MATCH_TIME > (datetime.now() - timedelta(days=1))).all()
    old_matches = {}
    live_matches = set()
    hided_matches = set()
    abort_matches = set()
    live_match_ids = set()
    current_crawled_web_ids = set()  # 记录本次爬取到的所有web_id
    for match in old_match_queries:
        web_id = int(match.MATCH_WEB_ID or 0)
        if match.MANUAL_ON == "1" or match.IS_GAME_OVER == "1":
            abort_matches.add(web_id)
            continue
        old_matches[web_id] = match

        if match.hide and match.hide == "1":
            hided_matches.add(web_id)

        if match.CLOSING_TIME > datetime.now() and match.hide == "0":
            live_matches.add(web_id)
            live_match_ids.add(match.MATCH_ID)

    # 查询已有赔率
    old_odds_dict = {}
    old_let_teams = {}
    old_odds_queries = db_session.query(MatchAttr).filter(MatchAttr.MATCH_ID.in_(live_match_ids)).all()
    for row in old_odds_queries:
        old_odds_dict[row.MATCH_ID] = row
        if row.LOSE_TEAM:
            old_let_teams[row.MATCH_ID] = row.LOSE_TEAM

    _cookies = get_cookies()
    if not _cookies:
        db_session.close()
        return
    ts = round(time.time())
    request_session = requests.Session()
    request_session.get("https://www.ibet789.com/Main.aspx?lang=EN-US", cookies=_cookies, proxies=proxy, headers=headers)
    # 先行处理1x2
    params = {
        "ot": "t",
        "gType": "S",
        "gType2": "S",
        "sk": "",
        "r": "",
        "LID": "",
        "_": str(ts)
    }
    resp = request_session.get("https://www.ibet789.com/_View/OddsOE1X2_G.ashx", params=params, cookies=_cookies, proxies=proxy, headers=headers)
    # 写入到本地缓存
    #with open("OddsOE1X2_G.txt", "w", encoding="utf-8") as file:
    #    file.write(resp.text)
    wld_list = eval(resp.text)[2]
    # 读取本地爬虫数据
    # with open("OddsOE1X2_G.txt", "r", encoding="utf-8") as file:
    #    content = file.read()
    # wld_list = eval(content)[2]
    wld_odds_dict = {}
    for league in wld_list:
        title = league[0]
        matches = league[1]
        league_name = title[1]

        # 过滤未录入联赛
        if league_name.upper() not in include_leagues:
            continue
        for match in matches:
            match_web_id = match[0]
            if match[28] <= 0:
                continue
            w, l, d = "%.2f" % match[28], "%.2f" % match[29], "%.2f" % match[30]
            wld_odds_dict[match_web_id] = [w, l, d]

    # tf为 "r" 时表示已经开始
    params = {
        "ot": "t",
        "tf": "2",
        "mt": "0",
        "tv": "2",
        "ov": "0",
        "sk": "",
        "isWC": "0",
        "r": "",
        "LID": "",
        "_": str(ts)
    }

    resp = request_session.get("https://www.ibet789.com/_View/MOdds_G.ashx", params=params, cookies=_cookies, proxies=proxy, headers=headers)
    # 写入到本地缓存
    #with open("MOdds_G.txt", "w", encoding="utf-8") as file:
    #    file.write(resp.text)

    info_list = eval(resp.text)
    # 读取本地爬虫数据
    # with open("MOdds_G.txt", "r", encoding="utf-8") as file:
    #     content = file.read()
    # info_list = eval(content)
    all_leagues = info_list[2]

    # print("the now matches:", all_leagues)
    # Arthur 获取明日的比赛
    #ot=e&tf=2&mt=0&tv=2&ov=0&wd=2025-12-11&oview=0&sk=&isWC=0&r=1282479850&LID=&_=1765352068777
    params = {
        "ot": "e",
        "tf": "2",
        "mt": "0",
        "tv": "2",
        "ov": "0",
        "wd": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"),
        "sk": "",
        "isWC": "0",
        "r": "",
        "LID": "",
        "_": str(ts)
    }
    resp = request_session.get("https://www.ibet789.com/_View/MOdds_G.ashx", params=params, cookies=_cookies, proxies=proxy, headers=headers)
    all_leagues2 = eval(resp.text)[2]
    # 合并
    all_leagues.extend(all_leagues2)

    match_count = 0
    attrs = []

    def odds_format(d_odds):
        d_odds = str(d_odds)
        tens = 0
        if len(d_odds) > 1:
            tens = int(d_odds[:-1])
        ones = int(d_odds[-1])
        if ones < 3:
            return str(tens * 10)
        if ones < 8:
            return str(tens * 10 + 5)
        return str(tens * 10 + 10)
    # 特殊词过滤替换
    stop_words = ['(IN MOROCCO)']
    test_league_name = Config.TEST_LEAGUE_NAME
    for league in all_leagues:
        title = league[0]
        matches = league[1]
        league_name = title[1]
        if league_name == "FIFA WORLD CUP 2022 (IN QATAR)":
            print("?????", league_name.upper() not in include_leagues, include_leagues)
        # 把league_name中包含stop_words数组中的特殊词替换空
        for word in stop_words:
            league_name = league_name.replace(word, '')
        league_name = league_name.strip()  # 去除首尾空格
        # 过滤未录入联赛
        if league_name.upper() not in include_leagues:
            # print("not included league_name:", league_name)
            continue
        print("the now matches:", league_name)
        is_test_league = False
        if league_name.upper() in test_league_name:
            is_test_league =  True
            print("test_league_name:", matches)
        test_check_match_list = Config.TEST_CHECK_MATCH_LIST
        for match in matches:
            time.sleep(0.01)
            match_web_id = match[0]
            # 记录本次爬取到的所有web_id（无论是否符合条件）
            current_crawled_web_ids.add(match_web_id)
            host_match_name = match[19]
            is_test_match = False
            if match_web_id == 45401985 or host_match_name in test_check_match_list:
                is_test_match = True
                print("is_test_match:", match)
            match_time = datetime.strptime(match[63], "%Y-%m-%d %H:%M:%S")  # 筛选myan盘

            _is_mian = (not match[76] or not match[77]) and (match[72] != -1 or match[75] != -1)

            is_first = match[9]
            is_first = True
            if not _is_mian or not is_first:
                if is_test_match or is_test_league:
                    print("not _is_mian or not is_first:", match_web_id, host_match_name, match_time)
                # 判断是否旧的比赛，如果是则隐藏（比赛状态变化，不再符合条件）
                if match_web_id in old_matches:
                    live_matches.add(match_web_id)
                continue

            # 让球方判断更改
            lose_team = HomeAway.home if match[68] else HomeAway.away
            if match[19] == "France" and match[20] == "Denmark":
                # and league_name == "FIFA WORLD CUP 2022 (IN QATAR)"
                print("?????", match[68], match[24], lose_team)

            wl_mak = match[72]
            bs_mak = match[75]
            # 单笔HDP（胜负盘）
            match_web_id_wl = "%s_%s" % (match_web_id, "1")
            # 单笔O/U大小盘
            match_web_id_bs = "%s_%s" % (match_web_id, "2")
            # 单笔Correct Score波胆 （订单类型3，match_attr_id从30开始编）
            match_web_id_3 = "%s_%s" % (match_web_id, "3")
            # 混合HDP（胜负盘）
            match_web_id_4 = "%s_%s" % (match_web_id, "4")
            # 混合O/U大小盘
            match_web_id_5 = "%s_%s" % (match_web_id, "5")
            # 单笔 Odd/Even 单双
            match_web_id_6 = "%s_%s" % (match_web_id, "6")
            # 混合 Odd/Even 单双
            match_web_id_7 = "%s_%s" % (match_web_id, "7")
            # 单笔 1x2
            match_web_id_10 = "%s_%s" % (match_web_id, "10")
            # 混合  1x2
            match_web_id_11 = "%s_%s" % (match_web_id, "11")
            # 8数字 9数字3D
            # 单笔 Both/One/Neither Team To Score （BTTS进球数方）
            match_web_id_18 = "%s_%s" % (match_web_id, "18")
            # 混合 Both/One/Neither Team To Score （BTTS进球数方）
            match_web_id_19 = "%s_%s" % (match_web_id, "19")
            # 21 拳击比赛
            match_web_id_21 = "%s_%s" % (match_web_id, "21")

            # 去除已禁用或者已结束的比赛
            if match_web_id in abort_matches:
                print("*--match which is abort--*:", match_web_id)
                continue

            match_count += 1

            match_md_time = match_time - timedelta(hours=1.5)
            match_desc = ""

            if match_web_id in live_matches:
                live_matches.remove(match_web_id)

            if match_web_id in old_matches:
                old_match = old_matches[match_web_id]
                match_id = old_matches[match_web_id].MATCH_ID
                old_match.MATCH_TIME = match_time
                old_match.CLOSING_TIME = match_time
                old_match.MATCH_MD_TIME = match_md_time
                match_desc = old_match.MATCH_DESC
                old_match.hide = "0"
                # UPDATE_TIME 交给模型 onupdate 自动处理：仅当主表字段真实变化时才刷新，
                # 避免仅赔率变动就刷新 m_app_match 更新时间，利于第三方增量同步
                # 更新比赛时间
                # db_session.query(Match).filter(Match.MATCH_ID == match_id).update({"MATCH_TIME": match_time, "MATCH_MD_TIME": match_md_time})
                # 先删除旧的赔率
                db_session.query(MatchAttr).filter(MatchAttr.MATCH_ID == match_id).delete()
                if is_test_match:
                    print("*--test match old --*:", old_match)
            else:
                # 比赛未录入时 创建比赛
                host_name = match[19]
                guest_name = match[20]
                # Arthur 获取主客队ID
                host_team_id = match[60]
                guest_team_id = match[61]
                match_desc = "%s vs %s" % (host_name, guest_name)

                match_repeated = False
                for old_match in old_matches.values():
                    # for match_ in old_matches:
                    #     _match_ = old_matches[match_]
                    if old_match.LEAGUE == league_name and old_match.MATCH_DESC.replace(" ", "").lower() == match_desc.replace(" ", "").lower():
                        print("--------", old_match.MATCH_WEB_ID, old_match.MATCH_WEB_ID in live_matches)

                        old_match_id = int(old_match.MATCH_WEB_ID)
                        print("++++++++", old_match.MATCH_WEB_ID, old_match_id in live_matches)
                        if old_match_id in live_matches:
                            live_matches.remove(int(old_match.MATCH_WEB_ID))
                            old_match.MATCH_TIME = match_time
                            old_match.CLOSING_TIME = match_time
                            old_match.MATCH_MD_TIME = match_md_time
                            old_web_id = old_match.MATCH_WEB_ID
                            old_match.MATCH_WEB_ID = match_web_id
                            match_id = old_match.MATCH_ID
                            match_repeated = True

                            # 重复比赛的时候赔率给他删了
                            db_session.query(MatchAttr).filter(MatchAttr.MATCH_ID == match_id).delete()
                            print("something enter")
                            break

                if not match_repeated:
                    match_id = str(round(time.time() * 1000))
                    new_match = Match(ID=match_id, MATCH_ID=match_id, MATCH_DESC=match_desc, MATCH_TIME=match_time, CLOSING_TIME=match_time, MATCH_MD_TIME=match_md_time, HOST_TEAM=host_name, LEAGUE=league_name,
                                      GUEST_TEAM=guest_name, MATCH_WEB_ID=match_web_id, IS_GAME_OVER="0", HOST_TEAM_WEBID=host_team_id, GUEST_TEAM_WEBID=guest_team_id)
                    db_session.add(new_match)
                    # Arthur 检查是否存在重复比赛
                    same_match_hide(db_session, new_match, old_match_queries)
                # db_session.add(new_match)

            # 更新赔率
            # 处理让球盘
            wl_odds = match[71]
            if is_test_match:
                print("*--wl_odds--*:", wl_mak,wl_odds,match[70])
            # if wl_mak and wl_mak != -1 and wl_odds:
            # LRC 0129 只要存在赔率，显示让球盘
            if wl_odds:
                wl_ball = str(match[70])
                wl_draw = int(wl_mak / 100)
                # lose_team = "1" if match[68] else "2"
                wl_draw_bunko = "0" if wl_draw >= 0 else "1"
                wl_draw_odds = str(odds_format(abs(wl_draw)))
                if match_web_id == 45117870:
                    print(f"----- {match_web_id} {wl_mak} {wl_draw}")
                # 当赢球数等于0时候,主队赢球且赔率为+的时候，设置客队为赢球方，反转平局胜负
                if wl_ball == '0' and lose_team == '1' and wl_draw_bunko == '0':
                    lose_team = "2"
                    wl_draw_bunko = "1"
                old_attr = db_session.query(MatchAttr).filter_by(MATCH_ATTR_ID=match_web_id_wl).one_or_none()
                old_match = old_matches.get(match_web_id)
                if old_attr and old_match:
                    # 让球数不变，赔率不变，(赔率大于15且让球方（LOSE_TEAM）变化或-+号（DRAW_BUNKO）平局胜负变化)
                    if old_attr.LOSE_BALL_NUM == wl_ball and old_attr.DRAW_ODDS == wl_draw_odds:
                        if int(wl_draw_odds) > 15 and ((old_attr.DRAW_BUNKO != wl_draw_bunko) and (old_attr.LOSE_TEAM == lose_team)):
                            old_match.exception = 1
                            old_match.hide = '1'
                            print('确认比赛异常，进行隐藏')
                            # print('让球方或平局胜负变化,让球方是否变化：', old_attr.LOSE_TEAM != lose_team, old_match.to_dict())
                            change_log = "赛事变盘信息(平局胜负): %s|%s 旧盘口: %s|%s%s%s, 新盘口: %s|%s%s%s  时间: %s\n" % (
                                old_match.MATCH_ID, match_desc, lose_team_dict.get(old_attr.LOSE_TEAM), wl_ball, draw_bunko_dict.get(old_attr.DRAW_BUNKO), old_attr.DRAW_ODDS,
                                lose_team_dict.get(lose_team), wl_ball, draw_bunko_dict.get(wl_draw_bunko), wl_draw_odds, datetime.now())
                            print(change_log)
                            with open("变盘日志.txt", mode='a', encoding='utf-8') as f:
                                f.write(change_log)
                        if old_attr.DRAW_BUNKO == wl_draw_bunko and old_attr.LOSE_TEAM != lose_team:
                            old_match.exception = 1
                            old_match.hide = '1'
                            print('确认比赛异常，进行隐藏')
                            # print('让球方或平局胜负变化,让球方是否变化：', old_attr.LOSE_TEAM != lose_team, old_match.to_dict())
                            change_log = "赛事变盘信息(让球方): %s|%s 旧盘口: %s|%s%s%s, 新盘口: %s|%s%s%s  时间: %s\n" % (
                                old_match.MATCH_ID, match_desc, lose_team_dict.get(old_attr.LOSE_TEAM), wl_ball, draw_bunko_dict.get(old_attr.DRAW_BUNKO), old_attr.DRAW_ODDS,
                                lose_team_dict.get(lose_team), wl_ball, draw_bunko_dict.get(wl_draw_bunko), wl_draw_odds, datetime.now())
                            print(change_log)
                            with open("变盘日志.txt", mode='a', encoding='utf-8') as f:
                                f.write(change_log)

                match_attr_desc = "胜负让球盘赔率"
                wl_host_odds = wl_guest_odds = match[71]
                # print("------ i got hdp odds:", wl_host_odds, wl_guest_odds)
                # if wl_host_odds == 0:
                #     print("---zero hdp match", match[19], match[20], match[81], match[84], match[71], match[74])
                if wl_host_odds > 0:
                    wl_host_odds /= 10
                if wl_guest_odds > 0:
                    wl_guest_odds /= 10

                # 用于判断是否显示的赔率
                cond_odds = wl_odds * 10
                if single_odds_on and cond_odds >= odds_cond_1:
                    new_attr = MatchAttr(ID=match_web_id_wl, MATCH_ATTR_ID=match_web_id_wl, MATCH_ID=match_id, MATCH_ATTR_DESC=match_attr_desc, MATCH_ATTR_TYPE="1", ODDS=wl_host_odds, ODDS_GUEST=wl_guest_odds,
                                         DRAW_BUNKO=wl_draw_bunko, DRAW_ODDS=wl_draw_odds, LOSE_TEAM=lose_team, LOSE_BALL_NUM=wl_ball, MATCH_WEB_ID=match_web_id)
                    # db_session.add(new_attr)
                    attrs.append(new_attr)
                # 混合盘 如果已存在旧赔率则不进行更新 -> 1小时更新一次
                if multi_odds_on and with_mix and cond_odds >= odds_cond_4:
                    new_attr = MatchAttr(ID=match_web_id_4, MATCH_ATTR_ID=match_web_id_4, MATCH_ID=match_id, MATCH_ATTR_DESC=match_attr_desc, MATCH_ATTR_TYPE="4", ODDS="2", ODDS_GUEST="2",
                                         DRAW_BUNKO=wl_draw_bunko, DRAW_ODDS=wl_draw_odds, LOSE_TEAM=lose_team, LOSE_BALL_NUM=wl_ball, MATCH_WEB_ID=match_web_id)
                    # db_session.add(new_attr)
                    attrs.append(new_attr)

            # 处理大小盘
            bs_odds = match[74]
            if is_test_match:
                print("---zero ov match", match[19], match[20], match[81], match[84], match[71], match[74])
            # if bs_mak and bs_mak != -1 and bs_odds:
            # LRC 0129 只要存在赔率，则显示
            if bs_odds:
                bs_draw = int(bs_mak / 100)
                bs_draw_bunko = "0" if bs_draw >= 0 else "1"
                bs_draw_odds = odds_format(abs(bs_draw))
                bs_ball = match[73]
                match_attr_desc = "大小球赔率"
                # 用于判断是否显示的赔率
                cond_odds = bs_odds * 10
                bs_host_odds = bs_guest_odds = match[74]
                # print("------ i got over under host odds:", bs_host_odds, bs_guest_odds)
                # if bs_host_odds == 0:
                #     print("---zero ov match", match[19], match[20], match[81], match[84], match[71], match[74])
                if bs_host_odds > 0:
                    bs_host_odds /= 10
                if bs_guest_odds > 0:
                    bs_guest_odds /= 10
                # print("大小盘赔率",cond_odds, match_attr_desc, bs_host_odds, bs_guest_odds)
                if single_odds_on and cond_odds >= odds_cond_2:
                    new_attr = MatchAttr(ID=match_web_id_bs, MATCH_ATTR_ID=match_web_id_bs, MATCH_ID=match_id, MATCH_ATTR_DESC=match_attr_desc, MATCH_ATTR_TYPE="2", ODDS=bs_host_odds, ODDS_GUEST=bs_guest_odds,
                                         DRAW_BUNKO=bs_draw_bunko, DRAW_ODDS=bs_draw_odds, LOSE_TEAM=lose_team, LOSE_BALL_NUM=bs_ball, MATCH_WEB_ID=match_web_id)
                    # db_session.add(new_attr)
                    attrs.append(new_attr)
                    if is_test_match:
                        print("*--test match 处理大小盘 单 --*:", json.dumps(new_attr.to_dict()))
                # 混合盘 如果已存在旧赔率则不进行更新 -> 1小时更新一次
                if multi_odds_on and match_web_id_5 and with_mix and cond_odds >= odds_cond_5:
                    new_attr = MatchAttr(ID=match_web_id_5, MATCH_ATTR_ID=match_web_id_5, MATCH_ID=match_id, MATCH_ATTR_DESC=match_attr_desc, MATCH_ATTR_TYPE="5", ODDS="2", ODDS_GUEST="2",
                                         DRAW_BUNKO=bs_draw_bunko, DRAW_ODDS=bs_draw_odds, LOSE_TEAM=lose_team, LOSE_BALL_NUM=bs_ball, MATCH_WEB_ID=match_web_id)
                    # db_session.add(new_attr)
                    attrs.append(new_attr)
                    if is_test_match:
                        print("*--test match 处理大小盘 双 --*:", json.dumps(new_attr.to_dict()))

            # Arthur 调用新接口获取每场比赛的赔率
            params = {
                "ot": "t",
                "oId": match_web_id,
                "update": "false",
                "r": "",
                "_": str(round(time.time()))
            }
            resp = request_session.get("https://www.ibet789.com/_View/MoreBets_G.ashx", params=params, cookies=_cookies,proxies=proxy, headers=headers)
            # print(f"获取【{match_web_id}】赔率结果:", resp.text)
            moreBets_G = eval(resp.text)
            is_save1x2 = False # 记录是否保存过1X2，如果没有保存则使用之前的方法处理
            # 1、获取Odd/Even & 1X2
            if len(moreBets_G)>1 and len(moreBets_G[1])>1 and moreBets_G[1][1]==match_web_id:
                oe1x2 = moreBets_G[1]
                #保留两位小数
                oe_odds = round(oe1x2[5]/10,2)
                oe_even_odds = round(oe1x2[6]/10,2)
                # 添加赔率过滤：Odd/Even 赔率必须都 > 1
                if single_odds_on and oe_odds*100 > odds_cond_6 and oe_even_odds*100 > odds_cond_6:
                    match_attr_desc = "Odd/Even赔率"
                    new_attr = MatchAttr(ID=match_web_id_6, MATCH_ATTR_ID=match_web_id_6, MATCH_ID=match_id,
                                         MATCH_ATTR_DESC=match_attr_desc, MATCH_ATTR_TYPE="6", ODDS=oe_odds,
                                             ODDS_GUEST=oe_even_odds, LOSE_TEAM=lose_team, LOSE_BALL_NUM="",
                                         MATCH_WEB_ID=match_web_id)
                    attrs.append(new_attr)

                wdl_odds = round(oe1x2[8],2)
                wdl_draw_odds = round(oe1x2[9], 2)
                wdl_guest_odds = round(oe1x2[10],2)
                # 添加赔率过滤：1X2 赔率必须都 > 1
                if single_odds_on and wdl_odds > 1 and wdl_draw_odds > 1 and wdl_guest_odds > 1:
                    match_attr_desc = "1X2赔率"
                    new_attr = MatchAttr(ID=match_web_id_10, MATCH_ATTR_ID=match_web_id_10, MATCH_ID=match_id,
                                         MATCH_ATTR_DESC=match_attr_desc, MATCH_ATTR_TYPE="10", ODDS=wdl_odds,
                                         ODDS_GUEST=wdl_guest_odds,
                                         DRAW_BUNKO="", DRAW_ODDS=wdl_draw_odds, LOSE_TEAM=lose_team, LOSE_BALL_NUM="",
                                         MATCH_WEB_ID=match_web_id)
                    attrs.append(new_attr)
                    is_save1x2 =  True


            # 2、获取Both/One/Neither Team To Score （单笔）
            if len(moreBets_G) > 12 and len(moreBets_G[12]) > 1 and moreBets_G[12][1] == match_web_id:
                bon = moreBets_G[12]
                bon_both_odds = round(bon[3],2)
                bon_one_odds = round(bon[4],2)
                bon_no_odds = round(bon[5],2)
                # 添加赔率过滤：Both/One/Neither 赔率必须都 > 1
                if single_odds_on and bon_both_odds > 1 and bon_one_odds > 1 and bon_no_odds > 1:
                    match_attr_desc = "Both/One/Neither赔率"
                    new_attr = MatchAttr(ID=match_web_id_18, MATCH_ATTR_ID=match_web_id_18, MATCH_ID=match_id,
                                         MATCH_ATTR_DESC=match_attr_desc, MATCH_ATTR_TYPE="18", ODDS=bon_both_odds,
                                         ODDS_GUEST=bon_one_odds,
                                         DRAW_BUNKO="", DRAW_ODDS=bon_no_odds, LOSE_TEAM=lose_team, LOSE_BALL_NUM="",
                                         MATCH_WEB_ID=match_web_id)
                    attrs.append(new_attr)

            # 处理胜平负盘
            wld_odds = wld_odds_dict.get(match_web_id)
            if wld_odds and not is_save1x2:
                match_attr_desc = "胜平负盘赔率"
                wdl_odds, wdl_guest_odds, wdl_draw_odds = wld_odds
                # 添加赔率过滤：1X2 赔率必须都 > 1
                if single_odds_on and float(wdl_odds) > 1 and float(wdl_guest_odds) > 1 and float(wdl_draw_odds) > 1:
                    new_attr = MatchAttr(ID=match_web_id_10, MATCH_ATTR_ID=match_web_id_10, MATCH_ID=match_id, MATCH_ATTR_DESC=match_attr_desc, MATCH_ATTR_TYPE="10", ODDS=wdl_odds, ODDS_GUEST=wdl_guest_odds,
                                         DRAW_BUNKO="", DRAW_ODDS=wdl_draw_odds, LOSE_TEAM=lose_team, LOSE_BALL_NUM="", MATCH_WEB_ID=match_web_id)
                    attrs.append(new_attr)

            # 处理波胆 Correct Score
            cs_const = ["1-0", "2-0", "2-1", "3-0", "3-1", "3-2", "4-0", "4-1", "4-2", "4-3",
                        "0-1", "0-2", "1-2", "0-3", "1-3", "2-3", "0-4", "1-4", "2-4", "3-4",
                        "0-0", "1-1", "2-2", "3-3", "4-4", "AOS"]
            if len(moreBets_G) > 3 and len(moreBets_G[3]) > 1 and moreBets_G[3][1] == match_web_id:
                # 处理波胆
                cs_odds = moreBets_G[3]
                cs_odds_index = 3 # 波胆盘赔率，从索引3开始，对应cs_const
                # 便利数组，从索引0开始
                for cs_index in range(len(cs_const)):
                    match_attr_id = "%s_%s" % (match_web_id, 30 + cs_index)
                    # if match_attr_id in old_odds_dict:
                    #     continue
                    odds = round(cs_odds[cs_odds_index+cs_index],2)
                    if odds <= 0:
                        continue
                    if odds > 100:
                        odds = 100

                    match_attr_desc = "波胆盘赔率"
                    score = cs_const[cs_index]

                    new_attr = MatchAttr(ID=match_attr_id,MATCH_ATTR_ID=match_attr_id, MATCH_ID=match_id,
                                         MATCH_ATTR_DESC=match_attr_desc,
                                         MATCH_ATTR_TYPE="3", ODDS="%0.2f" % odds, ODDS_GUEST="0",
                                         MATCH_WEB_ID=match_web_id, CS_SCORE=score, CS_INDEX=cs_index)
                    attrs.append(new_attr)

            # 确保比赛不被隐藏（被自定隐藏，然后再显示出来）
            if match_web_id in hided_matches:
                old_match = old_matches[match_web_id]
                if old_match.exception != 1:
                    old_match.hide = "0"
                    print("show hide match:", old_match.MATCH_ID, old_match.MATCH_TIME, old_match.MATCH_NAME, old_match.MATCH_WEB_ID)
                    db_session.query(Match).filter(Match.MATCH_ID == old_match.MATCH_ID).update({"hide": "0"})

    t1 = time.time()
    for attr in attrs:
        db_session.merge(attr)
    print("merge cost:", time.time() - t1)
    print("what's left:", len(live_matches), live_matches)

    if len(live_matches):
        print("hide matches:", live_matches)
        # print(db_session.query(Match).filter(Match.MATCH_WEB_ID.in_(live_matches), datetime.now() + timedelta(minutes=1) >= Match.MATCH_TIME).all())
        db_session.query(Match).filter(Match.MATCH_WEB_ID.in_(live_matches)).update({"hide": "1"}, synchronize_session=False)

    # 隐藏本次爬取中未出现的旧比赛（排除已手动设置和已结束的比赛）
    missing_web_ids = set()
    for web_id, match in old_matches.items():
        # 如果旧比赛不在本次爬取中，且未被手动设置，且未结束
        if web_id not in current_crawled_web_ids and web_id not in live_matches and web_id not in hided_matches and match.hide == "0":
            missing_web_ids.add(web_id)

    if len(missing_web_ids):
        print("hide missing matches:", missing_web_ids)
        db_session.query(Match).filter(Match.MATCH_WEB_ID.in_(missing_web_ids)).update({"hide": "1"}, synchronize_session=False)

    print("提交前耗时:", time.time() - start_time)
    db_session.commit()
    db_session.close()
    print(datetime.now(), "成功处理", match_count, "场比赛", "耗时:", time.time() - start_time)

def get_result_by_day(target_date):
    """
    获取指定日期的比赛结果并更新数据库
    :param target_date: 目标日期，可以是字符串(如'2025-12-21')或datetime对象
    :return: None
    """
    t1 = time.time()
    from lxml import etree
    _cookies = get_cookies()
    if not _cookies:
        print("获取cookies失败")
        return
    # 处理日期参数
    if isinstance(target_date, str):
        day_str = target_date
    elif isinstance(target_date, (datetime, date)):
        day_str = str(target_date.date()) if isinstance(target_date, datetime) else str(target_date)
    else:
        print("Invalid date format")
        return

    db_session = DBSession()
    import requests
    url = "https://www.ibet789.com/_View/Result.aspx"

    req_session = requests.session()
    resp = req_session.get(url,cookies=_cookies, proxies=proxy, headers=headers)

    view_state, view_state_generator, event_validation = get_page_validate(resp.text)
    data = {
        "__EVENTTARGET": "btnTodayLink",
        "__EVENTARGUMENT": "",
        "__LASTFOCUS": "",
        "__VIEWSTATE": view_state,
        "__VIEWSTATEGENERATOR": view_state_generator,
        "__VIEWSTATEENCRYPTED": "",
        "__EVENTVALIDATION": event_validation,
        "lstDates": day_str,
        "lstGameType": "S,S,p1,g1",
        "lstEvent": "-1",
        "btnSubmit": "Submit",
        "lstSortBy": "0",
    }
    # print("the request data:", data)
    resp = req_session.post(url, data,cookies=_cookies, proxies=proxy, headers=headers)
    html = etree.HTML(resp.text)
    # print("the resp:", resp.text)
    rows = html.xpath('//*[@id="g1"]/tr')[1:]

    def deal_day_match(day, row, league_name):
        row_ele = row.xpath('./td')
        team1 = row_ele[1].text.strip()
        team2 = row_ele[3].text.strip()
        time_str = row_ele[0].text.strip()
        full_score_ele = row_ele[2].xpath('./div/div')
        full_score = None
        try:
            if len(full_score_ele) > 1:
                if full_score_ele[1].text:
                    full_score = full_score_ele[1].text.strip().replace(" ", "")
                else:
                    # maybe the match refund
                    refund_text = full_score_ele[1].xpath('./font/text()')[0]
                    if refund_text == 'Refund':
                        full_score = "100-100"
        except Exception as e:
            print("get full score error:", e)
        if not full_score:
            return

        host_result, guest_result = full_score.split("-")
        if not host_result or not guest_result:
            return  # 比分不完整
        match_time = datetime.strptime("%s %s" % (day, time_str), "%Y-%m-%d %I:%M%p")
        if "AM" in time_str:
            # 以早上十点分割, 早于当天早上十点比赛视作第二天
            the_day_10_am = datetime.strptime("%s 10:40AM" % day, "%Y-%m-%d %I:%M%p")
            if match_time < the_day_10_am:
                match_time += timedelta(days=1)

        host_prob_names = {"%s (n)" % team1, "%s (N)" % team1, team1}
        guest_prob_names = {"%s (n)" % team2, "%s (N)" % team2, team2}
        # 判断球队名称是否包含某个字符则输出日志
        if "Bournemouth" in team1 or "Bournemouth" in team2:
            print("处理比赛:",league_name, team1, team2, match_time)
        exist_matches = db_session.query(Match).filter(Match.LEAGUE == league_name, Match.HOST_TEAM.in_(host_prob_names),
                                                       Match.GUEST_TEAM.in_(guest_prob_names), 
                                                       Match.MATCH_TIME.between(match_time - timedelta(minutes=30), match_time + timedelta(minutes=30))).all()

        # 比赛不存在
        if not (exist_matches and len(exist_matches)):
            return
        for exist_match in exist_matches:
            # 如果已经有结果了就不再更新
            if exist_match.HOST_TEAM_RESULT is not None:
                continue

            print("需要更新比赛比分:", exist_match.MATCH_DESC, exist_match.MATCH_TIME, exist_match.MATCH_ID,
                  exist_match.MATCH_WEB_ID,exist_match.HOST_TEAM_RESULT,exist_match.GUEST_TEAM_RESULT, host_result, guest_result)
            exist_match.HOST_TEAM_RESULT = host_result
            exist_match.GUEST_TEAM_RESULT = guest_result
            exist_match.status = "3"  # 比赛结算，后台可直接操作结算或者取消

    _league_name = ""
    for _row in rows:
        styles = _row.xpath('@style')
        if len(styles) == 1:
            _league_name = _row.xpath('./td/span')[0].text.strip()
        else:
            deal_day_match(day_str, _row, _league_name)

    db_session.commit()
    db_session.close()
    t2 = time.time()
    print(f"处理日期 {day_str} 的比赛结果耗时: {t2 - t1:.2f}秒")


def get_result():
    """
    获取今天和昨天的比赛结果
    """
    t1 = time.time()
    from datetime import datetime
    today = str(datetime.today().date())
    yesterday = str((datetime.today() - timedelta(days=1)).date())

    print("开始获取今天和昨天的比赛结果")
    get_result_by_day(today)
    get_result_by_day(yesterday)

    t2 = time.time()
    print(f"处理比赛结果总耗时: {t2 - t1:.2f}秒")


def cache_to_redis_by_time(start_time, end_time=None):
    print("开始缓存到redis")
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

    # for match in match_list.all():
    #     print(match.MATCH_TIME)

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
    print("排序的联赛:", sorts_leagues)
    match_list = match_list.filter(and_(Match.IS_GAME_OVER == "0", Match.CLOSING_STATE == "0")).order_by(Match.LEAGUE.in_(sorts_leagues).desc()).all()
    print(f"缓存的比赛数量:{len(match_list)}")

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

    print(f"今天比赛数量: {today_count}")
    print(f"明天比赛数量: {tomorrow_count}")
    print(f"后天比赛数量: {day_after_tomorrow_count}")

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
            # if attr['COND_ODDS'] < cond_dict[attr_type]:
            #     continue
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
            # if attr_type in single_mix_pair and pair_attr_id not in attrs_dict:
            #     # 混合单笔赔率不是同时存在跳过
            #     continue
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
    print("缓存完毕,耗时:", time.time() - cache_time)


def cache_to_redis():
    # 缓存无关时区, 只需缓存到第三天的10点30分之前的比赛（服务器时间12点）
    now = datetime.now()
    now_utc = now.astimezone(timezone.utc)
    day_after_tomorrow_end_utc = now_utc + timedelta(days=2, hours=12, minutes=00, seconds=59)
    cache_to_redis_by_time(now, day_after_tomorrow_end_utc)


# 处理比赛状态
def handle_match_status():
    # 先自动锁定比赛
    print("自动锁定比赛")
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
    print("自动锁定比赛数量:", n)


# 运行任务
def run_task():
    try:
        get_matches(with_mix=True)
    except Exception as e:
        # 打印具体报错
        traceback.print_exc()
        print("get_matches run error:", e)
    # 处理比赛状态
    try:
        handle_match_status()
    except Exception as e:
        # 打印具体报错
        traceback.print_exc()
        print("handle_match_status run error:", e)

    try:
        cache_to_redis()
    except Exception as e:
        # 打印具体报错
        traceback.print_exc()
        print("cache_to_redis run error:", e)

    try:
        # 获取比分结果
        get_result()
    except Exception as e:
        # 打印具体报错
        traceback.print_exc()
        print("get_result run error:", e)

if __name__ == '__main__':
    print("爬虫配置，账号:", scraper_cfg.pickAccount)
    # 记录总耗时
    cache_time = time.time()
    # 调试，获取1月10日的比赛结果
    # get_result_by_day(target_date="2026-01-10")
    # 运行任务
    run_task()
    
    print(datetime.now()," 总耗时:", time.time() - cache_time)