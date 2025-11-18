from Orm import DBSession, Match, MatchAttr, Config, Redis, LeagueTteamScraper
from sqlalchemy import and_, or_, func
from datetime import datetime, timedelta, date, timezone
import requests
import json
import time
import os
import re
from ibet_match import same_match_hide

# 测试账号
username = 'y7yjk1'
password = 'Abcd1234'

# proxy = {'https': "127.0.0.1:10877"}
# proxy = {'https': "127.0.0.1:10120"}
# proxy = {'https': '127.0.0.1:11451'}
proxy = {'https': '127.0.0.1:10809'}
# proxy = None
headers = {'x-forwarded-for': '37.111.7.124',
           "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.74 Safari/537.36 Edg/99.0.1150.55"}
# headers = {"User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.74 Safari/537.36 Edg/99.0.1150.55"}

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
    db_session = DBSession()
    exe_on = db_session.query(Config).filter_by(MDICT_ID="20").one().CONTENT == '1'
    if not exe_on:
        db_session.close()
        return

    single_odds_on = db_session.query(Config).filter_by(MDICT_ID="21").one().CONTENT == '1'
    multi_odds_on = db_session.query(Config).filter_by(MDICT_ID="22").one().CONTENT == '1'
    print("mix en?", multi_odds_on, with_mix)

    odds_cond_1 = int(db_session.query(Config).filter_by(MDICT_ID="16").one().CONTENT)
    odds_cond_2 = int(db_session.query(Config).filter_by(MDICT_ID="17").one().CONTENT)
    odds_cond_4 = int(db_session.query(Config).filter_by(MDICT_ID="18").one().CONTENT)
    odds_cond_5 = int(db_session.query(Config).filter_by(MDICT_ID="19").one().CONTENT)

    # 爬取的联赛
    include_leagues = db_session.query(Config).filter_by(MDICT_ID="41").one().CONTENT.upper()
    include_leagues = set(include_leagues.split(","))

    # 查询已有比赛
    old_match_queries = db_session.query(Match).filter(Match.MATCH_TIME > (datetime.now() - timedelta(days=1))).all()
    old_matches = {}
    live_matches = set()
    hided_matches = set()
    abort_matches = set()
    live_match_ids = set()
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
    wld_list = eval(resp.text)[2]
    # 读取本地爬虫数据
    # with open("D:/tmp/爬虫/wld_odds_dict.txt", "r", encoding="utf-8") as file:
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
        "r": "",
        "LID": "",
        "_": str(ts)
    }

    resp = request_session.get("https://www.ibet789.com/_View/MOdds_G.ashx", params=params, cookies=_cookies, proxies=proxy, headers=headers)

    info_list = eval(resp.text)
    # 读取本地爬虫数据
    # with open("D:/tmp/爬虫/info_list.txt", "r", encoding="utf-8") as file:
    #     content = file.read()
    # info_list = eval(content)
    all_leagues = info_list[2]

    # print("the now matches:", all_leagues)

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

    for league in all_leagues:
        title = league[0]
        matches = league[1]
        league_name = title[1]
        if league_name == "FIFA WORLD CUP 2022 (IN QATAR)":
            print("?????", league_name.upper() not in include_leagues, include_leagues)

        # 过滤未录入联赛
        if league_name.upper() not in include_leagues:
            # print("not included league_name:", league_name)
            continue
        for match in matches:
            time.sleep(0.001)
            match_web_id = match[0]
            match_time = datetime.strptime(match[63], "%Y-%m-%d %H:%M:%S")  # 筛选myan盘

            _is_mian = (not match[76] or not match[77]) and (match[72] != -1 or match[75] != -1)

            is_first = match[9]
            is_first = True
            if not _is_mian or not is_first:
                continue

            # 让球方判断更改
            lose_team = HomeAway.home if match[68] else HomeAway.away
            if match[19] == "France" and match[20] == "Denmark":
                # and league_name == "FIFA WORLD CUP 2022 (IN QATAR)"
                print("?????", match[68], match[24], lose_team)

            wl_mak = match[72]
            bs_mak = match[75]

            match_web_id_wl = "%s_%s" % (match_web_id, "1")
            match_web_id_bs = "%s_%s" % (match_web_id, "2")
            match_web_id_4 = "%s_%s" % (match_web_id, "4")
            match_web_id_5 = "%s_%s" % (match_web_id, "5")
            match_web_id_10 = "%s_%s" % (match_web_id, "10")

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
                # 更新比赛时间
                # db_session.query(Match).filter(Match.MATCH_ID == match_id).update({"MATCH_TIME": match_time, "MATCH_MD_TIME": match_md_time})
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
                            db_session.query(MatchAttr).filter(MatchAttr.MATCH_WEB_ID == old_web_id).delete()
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
            if wl_mak and wl_mak != -1 and wl_odds:
                wl_ball = str(match[70])
                wl_draw = int(wl_mak / 100)
                # lose_team = "1" if match[68] else "2"
                wl_draw_bunko = "0" if wl_draw >= 0 else "1"
                wl_draw_odds = str(odds_format(abs(wl_draw)))
                if match_web_id == 42094306:
                    print("-----")
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
            if bs_mak and bs_mak != -1 and bs_odds:
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
                if single_odds_on and cond_odds >= odds_cond_2:
                    new_attr = MatchAttr(ID=match_web_id_bs, MATCH_ATTR_ID=match_web_id_bs, MATCH_ID=match_id, MATCH_ATTR_DESC=match_attr_desc, MATCH_ATTR_TYPE="2", ODDS=bs_host_odds, ODDS_GUEST=bs_guest_odds,
                                         DRAW_BUNKO=bs_draw_bunko, DRAW_ODDS=bs_draw_odds, LOSE_TEAM=lose_team, LOSE_BALL_NUM=bs_ball, MATCH_WEB_ID=match_web_id)
                    # db_session.add(new_attr)
                    attrs.append(new_attr)
                # 混合盘 如果已存在旧赔率则不进行更新 -> 1小时更新一次
                if multi_odds_on and match_web_id_5 and with_mix and cond_odds >= odds_cond_5:
                    new_attr = MatchAttr(ID=match_web_id_5, MATCH_ATTR_ID=match_web_id_5, MATCH_ID=match_id, MATCH_ATTR_DESC=match_attr_desc, MATCH_ATTR_TYPE="5", ODDS="2", ODDS_GUEST="2",
                                         DRAW_BUNKO=bs_draw_bunko, DRAW_ODDS=bs_draw_odds, LOSE_TEAM=lose_team, LOSE_BALL_NUM=bs_ball, MATCH_WEB_ID=match_web_id)
                    # db_session.add(new_attr)
                    attrs.append(new_attr)

            # 处理胜平负盘
            wld_odds = wld_odds_dict.get(match_web_id)
            if wld_odds:
                match_attr_desc = "胜平负盘赔率"
                wdl_odds, wdl_guest_odds, wdl_draw_odds = wld_odds
                if single_odds_on:
                    new_attr = MatchAttr(ID=match_web_id_10, MATCH_ATTR_ID=match_web_id_10, MATCH_ID=match_id, MATCH_ATTR_DESC=match_attr_desc, MATCH_ATTR_TYPE="10", ODDS=wdl_odds, ODDS_GUEST=wdl_guest_odds,
                                         DRAW_BUNKO="", DRAW_ODDS=wdl_draw_odds, LOSE_TEAM=lose_team, LOSE_BALL_NUM="", MATCH_WEB_ID=match_web_id)
                    attrs.append(new_attr)

            # 确保比赛不被隐藏
            if match_web_id in hided_matches:
                old_match = old_matches[match_web_id]
                if old_match.exception != 1:
                    old_match.hide = "0"
                # db_session.query(Match).filter(Match.MATCH_ID == match_id).update({"hide": "0"})

    t1 = time.time()
    for attr in attrs:
        db_session.merge(attr)

    print("merge cost:", time.time() - t1)
    print("what's left:", len(live_matches), live_matches)

    if len(live_matches):
        # print(db_session.query(Match).filter(Match.MATCH_WEB_ID.in_(live_matches), datetime.now() + timedelta(minutes=1) >= Match.MATCH_TIME).all())
        db_session.query(Match).filter(Match.MATCH_WEB_ID.in_(live_matches), datetime.now() + timedelta(minutes=1) >= Match.MATCH_TIME).update({"hide": "1"}, synchronize_session=False)

    print("提交前耗时:", time.time() - start_time)
    db_session.commit()
    db_session.close()
    print(datetime.now(), "成功处理", match_count, "场比赛", "耗时:", time.time() - start_time)


def get_result():
    t1 = time.time()
    from lxml import etree
    from datetime import datetime
    today = str(datetime.today().date())
    yesterday = str((datetime.today() - timedelta(days=1)).date())
    # get_result_by_day(today)
    # get_result_by_day(yesterday)

    db_session = DBSession()
    import requests
    url = "https://www.ibet789.com/_View/Result.aspx"

    req_session = requests.session()
    resp = req_session.get(url, proxies=proxy, headers=headers)
    html = etree.HTML(resp.text)
    today_rows = html.xpath('//*[@id="g1"]/tr')[1:]

    view_state, view_state_generator, event_validation = get_page_validate(resp.text)
    data = {
        "__EVENTTARGET": "",
        "__EVENTARGUMENT": "",
        "__VIEWSTATE": view_state,
        "__VIEWSTATEGENERATOR": view_state_generator,
        "__EVENTVALIDATION": event_validation,
        "lstDates": yesterday,
        "lstGameType": "S,S,p1,g1",
        "lstEvent": "-1",
        "btnSubmit": "Submit",
        "lstSortBy": "0",
    }

    import json
    resp = req_session.post(url, data, proxies=proxy, headers=headers)
    # print("got the resp:", resp.status_code, resp.text)
    html = etree.HTML(resp.text)
    # print("xxx", resp.text)
    yesterday_rows = html.xpath('//*[@id="g1"]/tr')[1:]

    def deal_day_match(day, row, league_name):
        row_ele = row.xpath('./td')
        team1 = row_ele[1].text.strip()
        team2 = row_ele[3].text.strip()
        time_str = row_ele[0].text.strip()
        # full_score = row_ele[2].xpath('./div/div')[1].text.strip().replace(" ", "")
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
                    #print("------", refund_text)
        except Exception as e:
            print("get full score error:", e)
        if not full_score:
            return
        if league_name == "SCOTLAND LEAGUE CUP":
            print("???")
        if league_name == "SCOTLAND LEAGUE CUP" and team1 == "Forfar Athletic" and team2 == "Saint Mirren":
            print("?????")
        host_result, guest_result = full_score.split("-")
        if not host_result or not guest_result:
            return # 比分不完整
        match_time = datetime.strptime("%s %s" % (day, time_str), "%Y-%m-%d %I:%M%p")
        if "AM" in time_str:
            # 以早上十点分割, 早于当天早上十点比赛视作第二天
            the_day_10_am = datetime.strptime("%s 10:00AM" % day, "%Y-%m-%d %I:%M%p")
            if match_time < the_day_10_am:
                match_time += timedelta(days=1)

        host_prob_names = {"%s (n)" % team1, "%s (N)" % team1, team1}
        guest_prob_names = {"%s (n)" % team2, "%s (N)" % team2, team2}
        exist_matches = db_session.query(Match).filter(Match.LEAGUE == league_name, Match.HOST_TEAM.in_(host_prob_names), Match.GUEST_TEAM.in_(guest_prob_names), Match.MATCH_TIME == match_time).all()

        # 比赛不存在
        if not (exist_matches and len(exist_matches)):
            return
        for exist_match in exist_matches:

            # 如果已经有结果了就不再更新
            if exist_match.HOST_TEAM_RESULT:
                return

            print("需要更新比赛比分:", exist_match.MATCH_DESC, exist_match.MATCH_TIME, exist_match.MATCH_ID, exist_match.MATCH_WEB_ID, host_result, guest_result)
            exist_match.HOST_TEAM_RESULT = host_result
            exist_match.GUEST_TEAM_RESULT = guest_result
            exist_match.CLOSING_STATE = "1"  # 标记比赛已结束, 实现自动结算
            exist_match.status = "3"  # 比赛结算，后台可直接操作结算或者取消

    _league_name = ""
    for _row in today_rows:
        styles = _row.xpath('@style')
        tds = _row.xpath('./td')
        if len(styles) == 1:
            _league_name = _row.xpath('./td/span')[0].text.strip()
            # print("got league name:", _league_name)
        else:
            deal_day_match(today, _row, _league_name)

    for _row in yesterday_rows:
        styles = _row.xpath('@style')
        tds = _row.xpath('./td')
        if len(styles) == 1:
            _league_name = _row.xpath('./td/span')[0].text.strip()
            # print("got league name:", _league_name)
        else:
            deal_day_match(yesterday, _row, _league_name)
    db_session.commit()
    db_session.close()
    t2 = time.time()
    print("处理比赛结果耗时:", t2 - t1)


def cache_to_redis_by_time(start_time, end_time=None):
    print("开始缓存到redis")
    cache_time = time.time()
    db_session = DBSession()

    cache_keys = ['single', 'mix', 'old_mix', '1', '2', 'wdl']
    cache_dicts = {
        'single': {'1', '2', '6', '10'},
        'mix': {'4', '5', '7', '11'},
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

    match_list = match_list.filter(and_(Match.IS_GAME_OVER == "0", Match.CLOSING_STATE == "0")).order_by(Match.LEAGUE.in_({'Spain Primera Division',
                                                                                                                           'Italy Serie A',
                                                                                                                           'Germany Bundesliga 1',
                                                                                                                           'France Ligue 1',
                                                                                                                           'English Premier League',
                                                                                                                           'English League Championship'}).desc()).all()
    matches_dict = {m.MATCH_ID: m.to_dict() for m in match_list}
    all_attrs = db_session.query(MatchAttr).filter(MatchAttr.MATCH_ID.in_(matches_dict)).all()
    attrs_dict = {a.MATCH_ATTR_ID: a.to_dict() for a in all_attrs}

    cache_attrs = []
    for attr in all_attrs:
        attr = attr.to_dict()
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
                cache_list[k][match_id]['home_logo'] = LeagueTteamScraper.get_match_icon(cache_list[k][match_id]['HOST_TEAM_WEBID'])
                cache_list[k][match_id]['away_logo'] = LeagueTteamScraper.get_match_icon(cache_list[k][match_id]['GUEST_TEAM_WEBID'])
            pair_attr_id = f'{match_web_id}_{single_mix_pair.get(attr_type)}'
            if attr_type in single_mix_pair and pair_attr_id not in attrs_dict:
                # 混合单笔赔率不是同时存在跳过
                continue
            cache_list[k][match_id]['ATTR'].append(attr)

    # 最终结果
    items = {k: [] for k in cache_keys}

    now = datetime.now()
    for match in match_list:
        match_id = match.MATCH_ID
        # 判断比赛是否已开始，如已开始则更新状态为2
        if match.status == "1" and match.MATCH_TIME <= now:
            match.status = "2"
            match.CLOSING_STATE = "1"
            db_session.query(Match).filter(Match.MATCH_ID == match_id).update({"status": "2", "CLOSING_STATE": "1"})

        for k, v in cache_list.items():
            if match_id in v:
                items[k].append(v[match_id])
    for k, v in items.items():
        Redis.set("live_matches|%s" % k, json.dumps(v), 12 * 3600)
    Redis.set("live_odds", json.dumps(cache_attrs), 12 * 3600)

    db_session.commit()
    db_session.close()
    print("缓存完毕,耗时:", time.time() - cache_time)


def cache_to_redis():
    # 缓存无关时区, 只需缓存两天内的比赛
    now = datetime.now()
    now_utc = now.astimezone(timezone.utc)
    day_after_tomorrow_end_utc = now_utc + timedelta(days=1, hours=23, minutes=59, seconds=59)
    cache_to_redis_by_time(now, day_after_tomorrow_end_utc)


if __name__ == '__main__':
    # get_matches(with_mix=True)
    # cache_to_redis()
    # get_result()

    cnt = 0
    while True:
        try:
            # if cnt % 60 == 0:
            #     # get_matches(with_mix=True)
            #     cnt = 0
            # else:
            #     pass
            # get_matches()
            get_matches(with_mix=True)
            cache_to_redis()
            get_result()
            # cnt += 1
        except Exception as e:
            print("cycle run error:", e)
            # traceback.print_stack()
        time.sleep(60)
