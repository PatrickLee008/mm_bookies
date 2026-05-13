# Arthur 比赛数据处理

import re
from difflib import SequenceMatcher
from typing import Tuple
from datetime import datetime, time
from Orm import Match, DBSession, LeagueTteamScraper


def normalize_team_name(name: str) -> str:
    """
    标准化队名：
    - 转换为小写
    - 移除常见缩写和符号（如FC、.等）
    - 移除多余空格
    """
    # 定义需要移除的常见词（可根据需求扩展）
    stop_words ={'fk','baku','fc', 'club', 'cf', 'team', 'ac', 'sc', '&', '.', 'n', 'ksa', 'sd', 'cd', 'rc', 'as', 'us', 'rs', 'ts', 'fcw', 'fco', 'rsc', 'cfr', 'ksc', 'msc'}
    # 移除特殊符号并转换为小写
    name = re.sub(r'[^\w\s]', '', name.lower())
    # 按空格分割并过滤停用词
    words = [word for word in name.split() if word not in stop_words]
    return ' '.join(words).strip()


def calculate_similarity(str1: str, str2: str) -> float:
    """计算两个字符串的相似度（基于Jaro-Winkler改进的SequenceMatcher）"""
    return SequenceMatcher(None, str1, str2).ratio()


def is_same_match(match1: str, match2: str, threshold: float = 0.90) -> Tuple[bool, float, str]:
    """
    判断两场比赛是否队名相同：
    1. 分割主队和客队
    2. 标准化名称
    3. 计算主队和客队的相似度
    4. 综合判断是否超过阈值
    """
    # 分割主队和客队
    home1, away1 = map(normalize_team_name, match1.split(' vs '))
    home2, away2 = map(normalize_team_name, match2.split(' vs '))
    #print(f"对比{home1} vs {away1}，{home2} vs {away2}")
    # 计算主队和客队的相似度
    #home_sim = calculate_similarity(home1, home2)
    #away_sim = calculate_similarity(away1, away2)
    # 综合相似度（取最小值确保双方都匹配）
    #similarity = min(home_sim, away_sim)

    # 计算最优匹配相似度（考虑顺序可能互换）
    similarityHom1AndHome2 = calculate_similarity(home1, home2)
    similarityAway1AndAway2 = calculate_similarity(away1, away2)
    similarityHom1AndAway2 = calculate_similarity(home1, away2)
    similarityAway1AndHome2 = calculate_similarity(away1, home2)
    # 如果有1个相似度=1的则认为是同一场比赛
    same_team = ''
    if similarityHom1AndHome2 == 1:
        same_team = home1
    elif similarityAway1AndAway2 == 1:
        same_team = away1
    elif similarityHom1AndAway2 == 1:
        same_team = home1
    elif similarityAway1AndHome2 == 1:
        same_team = away1
    # 综合判断是否超过阈值
    if same_team != '':
        similarity = 1
    else:
        similarity = max(
            calculate_similarity(home1, home2) + calculate_similarity(away1, away2),
            calculate_similarity(home1, away2) + calculate_similarity(away1, home2)
        ) / 2
    # if similarity >= threshold:
    #     print(f"对比{home1}和{home2}，相似度为{calculate_similarity(home1, home2)}")
    #     print(f"对比{away1}和{away2}，相似度为{calculate_similarity(away1, away2)}")
    return similarity >= threshold, similarity, same_team


def add_team_map(db_session, new_match):
    """
    新增队伍映射
    """
    # 查找是否一键存在，存在则更新，不存在则新增
    # 主队
    league_name = new_match.LEAGUE
    web_id = new_match.HOST_TEAM_WEBID
    team = db_session.query(LeagueTteamScraper).filter(LeagueTteamScraper.league_name == league_name, LeagueTteamScraper.web_id == web_id, LeagueTteamScraper.del_flag == 0).first()
    if team:
        team.name = new_match.HOST_TEAM
        team.update_time = datetime.now()
    else:
        # 加001-100随机数，防止重复
        team = LeagueTteamScraper(id=new_match.MATCH_ID+str(1), name=new_match.HOST_TEAM, web_id=web_id, league_name=league_name)
        db_session.add(team)

    # 客队
    web_id = new_match.GUEST_TEAM_WEBID
    team = db_session.query(LeagueTteamScraper).filter(LeagueTteamScraper.league_name == league_name, LeagueTteamScraper.web_id == web_id, LeagueTteamScraper.del_flag == 0).first()
    if team:
        team.name = new_match.GUEST_TEAM
        team.update_time = datetime.now()
    else:
        team = LeagueTteamScraper(id=new_match.MATCH_ID+str(2), name=new_match.GUEST_TEAM, web_id=web_id, league_name=league_name)
        db_session.add(team)

# Arthur 判断两场比赛是否队名相同
def same_match_hide(db_session, new_match, live_matches, hide=True, onlyShowSame=False):
    # 新的比赛添加，先加入到Map表
    add_team_map(db_session, new_match)
    #print("开始比赛相似度判断")
    match_new = new_match.MATCH_DESC
    for liveMatch in live_matches:
        match_name = liveMatch.MATCH_DESC
        # 球队完全相同，时间不同,已经隐藏比赛，不进行比赛相似度判断
        # 计算两个比赛时间是否超过1个小时（绝对值）,日期是字符串
        diff_time = abs((new_match.MATCH_TIME - liveMatch.MATCH_TIME).total_seconds())
        if new_match.MATCH_ID == liveMatch.MATCH_ID or diff_time >= 3600 or liveMatch.hide == '1' or new_match.LEAGUE != liveMatch.LEAGUE :
            continue
        # 计算两个比赛队名是否相同
        same = False
        similarity = 0
        if (new_match.HOST_TEAM == liveMatch.HOST_TEAM or new_match.HOST_TEAM == liveMatch.GUEST_TEAM
                or new_match.GUEST_TEAM == liveMatch.HOST_TEAM or new_match.GUEST_TEAM == liveMatch.GUEST_TEAM):
            similarity = 1
            same = True
        else:
            same, similarity, same_team = is_same_match(match_new, match_name, threshold=0.8)
        if not hide and (onlyShowSame and same) or (not onlyShowSame):
            print(f"对比{new_match.MATCH_ID} {new_match.MATCH_TIME} 和 {liveMatch.MATCH_ID} {liveMatch.MATCH_TIME} --- {match_new}和{match_name}，相似度为{similarity}，相同为{same}")
        if same and new_match.MATCH_TIME == liveMatch.MATCH_TIME and hide:  # 如果队名相同(且比赛时间相同)，则隐藏
            print(f"对比{new_match.MATCH_ID} {new_match.MATCH_TIME} 和 {liveMatch.MATCH_ID} {liveMatch.MATCH_TIME} ---{match_new}和{match_name}，相似度为{similarity}，相同为{same},隐藏比赛")
            db_session.query(Match).filter(Match.MATCH_ID == liveMatch.MATCH_ID).update(
                {'hide': '1', 'UPDATE_TIME': datetime.now(), 'CLOSING_STATE': '1', 'HIDE_REASON': f"same match with：{new_match.MATCH_ID} {new_match.MATCH_DESC}",'HIDE_CONFIRM': '0'})
