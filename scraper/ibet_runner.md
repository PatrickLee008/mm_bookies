# ibet_runner.py 开发文档

## 一、系统概述

### 1.1 系统功能
ibet_runner.py 是一个足球比赛数据爬虫系统，主要功能包括：
- 从 ibet789.com 网站爬取足球比赛数据
- 处理和存储比赛赔率信息（让球盘、大小球盘、胜平负盘）
- 检测赔率变盘异常并自动隐藏异常比赛
- 获取比赛结果并更新到数据库
- 将比赛数据缓存到 Redis 供前端调用

### 1.2 技术栈
- **HTTP请求**: requests
- **数据库**: SQLAlchemy ORM (MySQL)
- **缓存**: Redis
- **HTML解析**: lxml
- **代理**: 支持HTTP/HTTPS代理

---

## 二、核心数据模型

### 2.1 Match (比赛表)
| 字段 | 类型 | 说明 |
|------|------|------|
| MATCH_ID | String(40) | 比赛唯一ID（时间戳生成） |
| MATCH_WEB_ID | String(20) | 爬虫网页比赛ID |
| MATCH_DESC | String(127) | 比赛描述（主队 vs 客队） |
| MATCH_TIME | TIMESTAMP | 比赛时间 |
| CLOSING_TIME | TIMESTAMP | 封盘时间 |
| LEAGUE | String(64) | 联赛名称 |
| HOST_TEAM | String(64) | 主队名称 |
| GUEST_TEAM | String(64) | 客队名称 |
| HOST_TEAM_WEBID | String(32) | 主队网页ID |
| GUEST_TEAM_WEBID | String(32) | 客队网页ID |
| HOST_TEAM_RESULT | String(4) | 主队得分 |
| GUEST_TEAM_RESULT | String(4) | 客队得分 |
| hide | String(2) | 是否隐藏（0:否，1:是） |
| exception | TINYINT(3) | 异常状态（0:正常，1:异常） |
| MANUAL_ON | String(64) | 是否人工配置（0:否，1:是） |
| IS_GAME_OVER | String(2) | 比赛是否结束（0:否，1:是） |
| status | String(10) | 比赛状态（1:未开始，2:进行中，3:已结束） |

### 2.2 MatchAttr (赔率表)
| 字段 | 类型 | 说明                                                                   |
|------|------|----------------------------------------------------------------------|
| MATCH_ATTR_ID | String(40) | 赔率ID（格式：{MATCH_WEB_ID}_{赔率类型}）                                       |
| MATCH_ID | String(20) | 关联比赛ID                                                               |
| MATCH_ATTR_TYPE | String(2) | 赔率类型（1:让球，2:大小球，3:波胆，4:混合让球，5:混合大小球，6:单双，18:Both/One/Neither，10:胜平负） |
| ODDS | String(6) | 主队/大球/单数赔率                                                           |
| ODDS_GUEST | String(6) | 客队/小球/双数赔率                                                           |
| LOSE_TEAM | String(16) | 让球方（1:主队，2:客队）                                                       |
| LOSE_BALL_NUM | String(32) | 让球数/大小球数                                                             |
| DRAW_BUNKO | String(4) | 平局胜负（0:+，1:-）                                                        |
| DRAW_ODDS | String(6) | 平局赔率（%）/ Both/One/Neither中的Neither赔率                                 |
| CS_SCORE | String(10) | 波胆比分（如"1-0", "2-1", "AOS"等）                                          |
| CS_INDEX | Integer | 波胆比分索引（0-25）                                                         |
| MATCH_WEB_ID | String(20) | 关联网页比赛ID                                                             |

### 2.3 Config (配置表)
系统通过以下方式读取配置：
- **爬虫配置**: 通过 `SysBisDict.get_scraper_config()` 获取，返回 ScraperCfgVo 对象，包含：
  - `scraperEnabled`: 总开关（爬虫是否启用）
  - `singleSpiderEnabled`: 单式赔率开关
  - `mixParlaySpiderEnabled`: 混合盘开关
  - `minOddWinLose`: 单式-胜负盘HDP最小赔率（对应 odds_cond_1）
  - `minOddBallNum`: 单式-大小盘O/U最小球数（对应 odds_cond_2）
  - `minOddCond4`: 混合-胜负盘最小赔率（对应 odds_cond_4）
  - `minOddCond5`: 混合-大小盘最小球数（对应 odds_cond_5）
  - `pickAccount`: 当前使用的账号标识
- **联赛配置**: 通过 `MAppLeague.get_scraper_leagues()` 获取可爬取的联赛白名单（Set集合）

---

## 三、核心算法详解

### 3.1 登录和Cookie管理

#### 3.1.1 登录流程
```
login() 函数流程：
1. GET请求主页获取页面验证参数
   - __VIEWSTATE
   - __VIEWSTATEGENERATOR
   - __EVENTVALIDATION
2. 构造登录表单（包含用户名、密码、验证参数）
3. POST提交登录表单
4. 返回session cookies
```

#### 3.1.2 Cookie管理策略
```
get_cookies() 函数流程：
1. 尝试从本地文件 "cookies" 读取已保存的cookie
2. 调用 check_cookie() 验证cookie有效性
   - 访问 AccInfo.aspx 页面
   - 检查是否重定向到该页面且返回内容非空
3. 若cookie无效，调用 login() 重新登录
4. 验证新cookie，保存到本地文件
5. 返回有效cookie
```

**关键点**：
- Cookie持久化存储避免频繁登录
- 双重验证确保cookie可用性

---

### 3.2 比赛数据爬取算法 (get_matches)

这是系统的核心函数，包含多个复杂算法。

#### 3.2.1 预处理阶段

```
流程：
1. 读取配置参数（全局加载）
   - scraper_cfg = SysBisDict.get_scraper_config()  # 爬虫配置
   - scraper_leagues = MAppLeague.get_scraper_leagues()  # 联赛白名单
   - 总开关检查（scraperEnabled）
   - 单式/混合盘开关（singleSpiderEnabled/mixParlaySpiderEnabled）
   - 各类型赔率阈值（minOddWinLose/minOddBallNum/minOddCond4/minOddCond5）

2. 构建旧数据缓存
   - 查询近24小时内比赛（MATCH_TIME > datetime.now() - 1天）
   - 建立三个集合：
     * old_matches: {web_id: Match对象}
     * live_matches: 进行中比赛web_id集合
     * abort_matches: 已结束/手动禁用比赛web_id集合
     * hided_matches: 已隐藏比赛web_id集合

3. 查询旧赔率数据
   - old_odds_dict: {MATCH_ID: MatchAttr}
   - old_let_teams: {MATCH_ID: LOSE_TEAM} # 用于变盘检测
```

**关键数据结构**：
```python
old_matches = {}        # 存储所有旧比赛
live_matches = set()    # 当前活跃比赛（未隐藏且未封盘）
abort_matches = set()   # 禁止更新的比赛
hided_matches = set()   # 已隐藏比赛
```

#### 3.2.2 数据爬取阶段

**爬取三个主要接口**：

1. **胜平负盘接口** (OddsOE1X2_G.ashx)
```python
params = {
    "ot": "t",
    "gType": "S",    # 单式
    "gType2": "S",
    "sk": "",
    "r": "",
    "LID": "",
    "_": timestamp
}
```
返回数据结构：
```
[meta, info, leagues]
leagues = [
    [league_title, matches],
    ...
]
league_title = [id, league_name, ...]
match = [
    match_web_id,     # [0]
    ...,
    home_team,        # [19]
    away_team,        # [20]
    ...,
    win_odds,         # [28]
    lose_odds,        # [29]
    draw_odds,        # [30]
    ...
]
```

2. **让球/大小球盘接口** (MOdds_G.ashx)
```python
# 今日比赛
params = {
    "ot": "t",
    "tf": "2",       # 筛选未开始的比赛
    "mt": "0",
    "tv": "2",
    "ov": "0",
    "sk": "",
    "isWC": "0",
    "r": "",
    "LID": "",
    "_": timestamp
}

# 明日比赛（额外爬取）
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
    "_": timestamp
}
# 两次请求结果合并处理
```

返回数据关键字段索引：
```
match[9]  - is_first (是否首发)
match[19] - 主队名称
match[20] - 客队名称
match[60] - 主队web_id
match[61] - 客队web_id
match[63] - 比赛时间字符串
match[68] - 让球方标识（True:主队让球）
match[70] - 让球数
match[71] - 让球盘赔率
match[72] - 让球盘标识（-1表示不可用）
match[73] - 大小球数
match[74] - 大小球盘赔率
match[75] - 大小球盘标识（-1表示不可用）
match[76] - 滚球标识1
match[77] - 滚球标识2
```

#### 3.2.3 比赛筛选算法

```python
# Myanmar盘判定
_is_mian = (not match[76] or not match[77]) and (match[72] != -1 or match[75] != -1)

# 筛选条件：
1. 必须是Myanmar盘（_is_mian）
2. 必须是首发（is_first）
3. 联赛必须在白名单中
4. 不在abort_matches中（未被禁用）
```

#### 3.2.4 比赛创建与去重算法

**核心逻辑**：
```
IF match_web_id in old_matches:
    # 已存在比赛，更新时间
    更新 MATCH_TIME, CLOSING_TIME, MATCH_MD_TIME
    从 live_matches 移除（表示该比赛已处理）
ELSE:
    # 新比赛，检查是否重复
    FOR each old_match in old_matches:
        IF (相同联赛 AND 相同队伍名称):
            IF old_match 在 live_matches 中:
                # 重复比赛处理
                1. 更新旧比赛的web_id为新web_id
                2. 更新时间
                3. 删除旧赔率数据
                4. 标记为重复（match_repeated = True）
                break

    IF not match_repeated:
        # 真正的新比赛
        1. 生成新match_id（时间戳）
        2. 创建Match对象
        3. 调用 same_match_hide() 检查重复比赛并隐藏
        4. 添加到数据库
```

**比赛描述匹配算法**：
```python
# 忽略大小写和空格的比较
old_match.MATCH_DESC.replace(" ", "").lower() == new_match_desc.replace(" ", "").lower()

# 同时匹配联赛名称
old_match.LEAGUE == new_league_name
```

#### 3.2.5 赔率格式化算法 (odds_format)

**功能**：将赔率数值转换为标准格式（0、5、10的倍数）

```python
def odds_format(d_odds):
    """
    输入示例：
    - 123 -> "120"
    - 127 -> "130"
    - 12  -> "10"
    - 2   -> "0"
    - 8   -> "10"

    算法逻辑：
    1. 分离十位数和个位数
       tens = d_odds // 10
       ones = d_odds % 10

    2. 根据个位数归类：
       - 0-2: 向下取整到十位 (返回 tens*10)
       - 3-7: 四舍五入到 +5 (返回 tens*10+5)
       - 8-9: 向上取整到 +10 (返回 tens*10+10)
    """
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
```

#### 3.2.6 让球盘处理算法

**核心数据提取**：
```python
wl_mak = match[72]           # 让球盘标识（包含平局赔率信息）
wl_odds = match[71]          # 让球赔率
wl_ball = match[70]          # 让球数
lose_team_flag = match[68]   # 让球方标识

# 让球方判定
lose_team = "1" if match[68] else "2"  # True=主队让球，False=客队让球
```

**平局赔率计算**：
```python
wl_draw = int(wl_mak / 100)             # 除以100得到平局赔率原始值
wl_draw_bunko = "0" if wl_draw >= 0 else "1"  # 正数为+，负数为-
wl_draw_odds = odds_format(abs(wl_draw))      # 格式化绝对值
```

**特殊情况处理 - 0球让球修正**：
```python
# 当让球数为0时的特殊逻辑
if wl_ball == '0' and lose_team == '1' and wl_draw_bunko == '0':
    # 场景：0球让球，主队为让球方，平局赔率为正
    # 修正：交换让球方，反转平局胜负
    lose_team = "2"           # 改为客队让球
    wl_draw_bunko = "1"       # 改为负数
```

**赔率转换**：
```python
wl_host_odds = wl_guest_odds = match[71]  # 初始赔率相同
if wl_host_odds > 0:
    wl_host_odds /= 10    # 转换为小数形式
if wl_guest_odds > 0:
    wl_guest_odds /= 10
```

**存储逻辑**：
```python
# 条件判定
cond_odds = wl_odds * 10  # 用于阈值比较

# 单式让球盘（类型1）
if single_odds_on and cond_odds >= odds_cond_1:
    create MatchAttr(
        MATCH_ATTR_ID = "{match_web_id}_1",
        MATCH_ATTR_TYPE = "1",
        ODDS = wl_host_odds,
        ODDS_GUEST = wl_guest_odds,
        LOSE_TEAM = lose_team,
        LOSE_BALL_NUM = wl_ball,
        DRAW_BUNKO = wl_draw_bunko,
        DRAW_ODDS = wl_draw_odds
    )

# 混合让球盘（类型4）
if multi_odds_on and with_mix and cond_odds >= odds_cond_4:
    create MatchAttr(
        MATCH_ATTR_ID = "{match_web_id}_4",
        MATCH_ATTR_TYPE = "4",
        ODDS = "2",           # 固定赔率
        ODDS_GUEST = "2",     # 固定赔率
        其他字段同上
    )
```

#### 3.2.7 大小球盘处理算法

**算法与让球盘类似，关键差异**：
```python
bs_mak = match[75]      # 大小球盘标识
bs_odds = match[74]     # 大小球赔率
bs_ball = match[73]     # 大小球数

# 平局赔率计算（同让球盘）
bs_draw = int(bs_mak / 100)
bs_draw_bunko = "0" if bs_draw >= 0 else "1"
bs_draw_odds = odds_format(abs(bs_draw))

# 赔率类型
MATCH_ATTR_TYPE = "2"   # 单式大小球
MATCH_ATTR_TYPE = "5"   # 混合大小球

# 注意：大小球盘没有0球特殊处理逻辑
```

#### 3.2.8 MoreBets接口处理算法

**接口说明**：针对每场比赛单独请求，获取额外赔率信息

```python
# 请求参数
params = {
    "ot": "t",
    "oId": match_web_id,
    "update": "false",
    "r": "",
    "_": str(round(time.time()))
}
```

##### 3.2.8.1 Odd/Even（单双）处理

**数据位置**：`moreBets_G[1]`

```python
if len(moreBets_G)>1 and len(moreBets_G[1])>1 and moreBets_G[1][1]==match_web_id:
    oe1x2 = moreBets_G[1]
    oe_odds = round(oe1x2[5]/10, 2)        # 单数赔率
    oe_even_odds = round(oe1x2[6]/10, 2)   # 双数赔率

    create MatchAttr(
        MATCH_ATTR_ID = "{match_web_id}_6",
        MATCH_ATTR_TYPE = "6",
        ODDS = oe_odds,
        ODDS_GUEST = oe_even_odds,
        DRAW_BUNKO = "",
        DRAW_ODDS = "",
        LOSE_TEAM = lose_team,
        LOSE_BALL_NUM = ""
    )
```

##### 3.2.8.2 1X2（胜平负）处理（新方法）

**数据位置**：`moreBets_G[1]`（与Odd/Even在同一数据包）

```python
wdl_odds = round(oe1x2[8], 2)        # 主队胜赔率
wdl_draw_odds = round(oe1x2[9], 2)   # 平局赔率
wdl_guest_odds = round(oe1x2[10], 2) # 客队胜赔率

if wdl_odds > 0:  # 有效数据判断
    create MatchAttr(
        MATCH_ATTR_ID = "{match_web_id}_10",
        MATCH_ATTR_TYPE = "10",
        ODDS = wdl_odds,
        ODDS_GUEST = wdl_guest_odds,
        DRAW_BUNKO = "",
        DRAW_ODDS = wdl_draw_odds,
        LOSE_TEAM = lose_team
    )
    is_save1x2 = True  # 标记已保存
```

**双重来源策略**：
1. 优先使用 MoreBets_G 接口的1X2数据（更准确）
2. 如果 MoreBets_G 无数据（`is_save1x2 = False`），则使用 OddsOE1X2_G 接口的数据作为备份

##### 3.2.8.3 Both/One/Neither Team To Score 处理

**数据位置**：`moreBets_G[12]`

```python
if len(moreBets_G) > 12 and len(moreBets_G[12]) > 1 and moreBets_G[12][1] == match_web_id:
    bon = moreBets_G[12]
    bon_both_odds = round(bon[3], 2)   # 双方进球赔率
    bon_one_odds = round(bon[4], 2)    # 单方进球赔率
    bon_no_odds = round(bon[5], 2)     # 双方不进球赔率

    create MatchAttr(
        MATCH_ATTR_ID = "{match_web_id}_8",
        MATCH_ATTR_TYPE = "8",
        ODDS = bon_both_odds,
        ODDS_GUEST = bon_one_odds,
        DRAW_BUNKO = "",
        DRAW_ODDS = bon_no_odds,  # 使用DRAW_ODDS存储Neither赔率
        LOSE_TEAM = lose_team
    )
```

##### 3.2.8.4 Correct Score（波胆）处理

**数据位置**：`moreBets_G[3]`

**比分常量定义**：
```python
cs_const = ["1-0", "2-0", "2-1", "3-0", "3-1", "3-2", "4-0", "4-1", "4-2", "4-3",
            "0-1", "0-2", "1-2", "0-3", "1-3", "2-3", "0-4", "1-4", "2-4", "3-4",
            "0-0", "1-1", "2-2", "3-3", "4-4", "AOS"]
# 共26种比分结果，AOS表示Any Other Score（其他比分）
```

**处理逻辑**：
```python
if len(moreBets_G) > 3 and len(moreBets_G[3]) > 1 and moreBets_G[3][1] == match_web_id:
    cs_odds = moreBets_G[3]
    cs_odds_index = 3  # 赔率从索引3开始

    for cs_index in range(len(cs_const)):
        match_attr_id = f"{match_web_id}_{30 + cs_index}"  # ID从30-55
        odds = round(cs_odds[cs_odds_index + cs_index], 2)

        if odds <= 0:  # 无效赔率跳过
            continue
        if odds > 100:  # 赔率上限
            odds = 100

        score = cs_const[cs_index]
        create MatchAttr(
            MATCH_ATTR_ID = match_attr_id,
            MATCH_ATTR_TYPE = "3",
            ODDS = odds,
            ODDS_GUEST = "0",
            CS_SCORE = score,     # 比分字符串
            CS_INDEX = cs_index   # 比分索引
        )
```

**波胆MATCH_ATTR_ID规则**：
- {match_web_id}_30: 主队1-0
- {match_web_id}_31: 主队2-0
- ...
- {match_web_id}_40: 客队0-1
- ...
- {match_web_id}_50: 平局0-0
- ...
- {match_web_id}_55: AOS（其他比分）

#### 3.2.9 胜平负盘处理算法（备份方法）

**数据来源**：从 wld_odds_dict 获取（由OddsOE1X2_G接口提供）

```python
wld_odds = wld_odds_dict.get(match_web_id)
if wld_odds and not is_save1x2:  # 仅在MoreBets未保存1X2时使用
    wdl_odds, wdl_guest_odds, wdl_draw_odds = wld_odds

    create MatchAttr(
        MATCH_ATTR_ID = "{match_web_id}_10",
        MATCH_ATTR_TYPE = "10",
        ODDS = wdl_odds,              # 主队胜赔率
        ODDS_GUEST = wdl_guest_odds,  # 客队胜赔率
        DRAW_BUNKO = "",
        DRAW_ODDS = wdl_draw_odds,    # 平局赔率
        LOSE_TEAM = lose_team         # 继承让球方（用于标识）
    )
```

**特点**：
- 作为备份数据源
- 无需阈值判断
- 不区分单式/混合

#### 3.2.10 变盘检测算法

这是系统的核心风控算法，用于检测异常赔率变化。

**触发条件**：
```python
IF old_attr exists AND old_match exists:
    IF 让球数不变 AND 赔率不变:
        # 条件1：赔率>15 且 平局胜负变化（+/-号变化）
        IF wl_draw_odds > 15 AND old_DRAW_BUNKO != new_DRAW_BUNKO AND old_LOSE_TEAM == new_LOSE_TEAM:
            标记异常并隐藏

        # 条件2：平局胜负不变 但 让球方变化
        IF old_DRAW_BUNKO == new_DRAW_BUNKO AND old_LOSE_TEAM != new_LOSE_TEAM:
            标记异常并隐藏
```

**异常处理动作**：
```python
old_match.exception = 1      # 标记为异常
old_match.hide = '1'         # 隐藏比赛

# 记录变盘日志
change_log = "赛事变盘信息: {match_id}|{match_desc} 旧盘口: {old_info}, 新盘口: {new_info}  时间: {now}"
写入 "变盘日志.txt"
```

**算法意义**：
- 让球数和赔率都不变，理论上盘口应该完全一致
- 如果只有平局胜负或让球方变化，说明数据源可能异常
- 高赔率（>15）情况下更敏感，因为影响更大

**实际案例**：
```
旧盘口: 主队|0.5+15
新盘口: 主队|0.5-15    # 平局胜负变化，触发异常
```

#### 3.2.11 比赛隐藏/显示逻辑

**隐藏逻辑**：
```python
# 1. 变盘异常隐藏（见3.2.10）

# 2. 重复比赛隐藏
same_match_hide(db_session, new_match, old_match_queries)
# 在ibet_match.py中实现，检测同联赛同队伍名称的重复比赛

# 3. 比赛已开始隐藏
# 在最后处理阶段
live_matches中剩余的比赛（未被新数据更新）
    AND 比赛时间 <= 当前时间+1分钟
    => 设置 hide = "1"
```

**显示逻辑**：
```python
# 确保新爬取的比赛不被隐藏（除非异常）
if match_web_id in hided_matches:
    old_match = old_matches[match_web_id]
    if old_match.exception != 1:  # 非异常比赛
        old_match.hide = "0"      # 恢复显示
```

**live_matches 集合的妙用**：
```python
# 初始状态：包含所有活跃比赛
# 处理过程：每处理一个比赛，从集合移除
# 处理结束：集合中剩余的是"网站上已消失的比赛"
# 最终动作：将这些比赛隐藏（可能已开始或被取消）
```

#### 3.2.12 数据提交优化算法

```python
# 批量合并赔率数据
attrs = []  # 收集所有赔率对象

# 在循环中只添加到列表
attrs.append(new_attr)

# 循环结束后批量merge
for attr in attrs:
    db_session.merge(attr)

# 批量更新隐藏状态
db_session.query(Match).filter(
    Match.MATCH_WEB_ID.in_(live_matches),
    datetime.now() + timedelta(minutes=1) >= Match.MATCH_TIME
).update({"hide": "1"}, synchronize_session=False)

# 统一提交
db_session.commit()
```

**性能优化点**：
- 延迟写入：先收集后批量操作
- 批量更新：使用 update() 代替逐个修改
- 单次提交：减少数据库事务次数

---

### 3.3 比赛结果获取算法 (get_result)

**函数结构**：
- `get_result()`: 主函数，调用 get_result_by_day 获取今日和昨日结果
- `get_result_by_day(target_date)`: 获取指定日期的比赛结果

#### 3.3.1 数据爬取流程

```
1. get_result() 调用两次 get_result_by_day：
   - get_result_by_day(today)      # 今日比赛结果
   - get_result_by_day(yesterday)  # 昨日比赛结果

2. get_result_by_day(target_date) 流程：
   - 访问 Result.aspx 页面
   - 提取页面验证参数（同登录流程）
   - 构造POST请求获取指定日期比赛结果
   - 使用 lxml 解析 HTML 表格
```

#### 3.3.2 POST请求参数

```python
data = {
    "__EVENTTARGET": "btnTodayLink",
    "__EVENTARGUMENT": "",
    "__LASTFOCUS": "",
    "__VIEWSTATE": view_state,
    "__VIEWSTATEGENERATOR": view_state_generator,
    "__VIEWSTATEENCRYPTED": "",
    "__EVENTVALIDATION": event_validation,
    "lstDates": target_date,      # 目标日期（如"2025-12-21"）
    "lstGameType": "S,S,p1,g1",
    "lstEvent": "-1",
    "btnSubmit": "Submit",
    "lstSortBy": "0",
}
```

#### 3.3.3 HTML解析算法

**表格结构**：
```html
<table id="g1">
    <tr style="...">              <!-- 联赛标题行 -->
        <td><span>联赛名称</span></td>
    </tr>
    <tr>                          <!-- 比赛数据行 -->
        <td>比赛时间</td>
        <td>主队</td>
        <td>
            <div>
                <div>半场比分</div>
                <div>全场比分</div>  <!-- 或 <font>Refund</font> -->
            </div>
        </td>
        <td>客队</td>
    </tr>
    ...
</table>
```

**解析逻辑**：
```python
rows = html.xpath('//*[@id="g1"]/tr')[1:]  # 跳过表头

league_name = ""
for row in rows:
    styles = row.xpath('@style')

    if len(styles) == 1:
        # 有style属性 -> 联赛标题行
        league_name = row.xpath('./td/span')[0].text.strip()
    else:
        # 无style属性 -> 比赛数据行
        process_match(row, league_name)
```

#### 3.3.4 比赛匹配算法

**提取比赛信息**：
```python
row_ele = row.xpath('./td')
team1 = row_ele[1].text.strip()      # 主队
team2 = row_ele[3].text.strip()      # 客队
time_str = row_ele[0].text.strip()   # 时间（格式：HH:MM AM/PM）
```

**比分提取**：
```python
full_score_ele = row_ele[2].xpath('./div/div')

# 情况1：正常比分
if full_score_ele[1].text:
    full_score = full_score_ele[1].text.strip().replace(" ", "")
    # 格式："3 - 1" -> "3-1"

# 情况2：退款（比赛取消/异常）
else:
    refund_text = full_score_ele[1].xpath('./font/text()')[0]
    if refund_text == 'Refund':
        full_score = "100-100"  # 特殊标识
```

**时间转换算法**：
```python
match_time = datetime.strptime(f"{day} {time_str}", "%Y-%m-%d %I:%M%p")

# AM时段特殊处理（跨日问题）
if "AM" in time_str:
    the_day_10_am = datetime.strptime(f"{day} 10:00AM", "%Y-%m-%d %I:%M%p")
    if match_time < the_day_10_am:
        # 早于10AM视为次日凌晨
        match_time += timedelta(days=1)

# 示例：
# 日期：2024-12-10
# 时间：02:30AM
# 判断：02:30 < 10:00 -> 实际为 2024-12-11 02:30
```

**队伍名称模糊匹配**：
```python
# 处理中立场标识 (n) 或 (N)
host_prob_names = {
    f"{team1} (n)",
    f"{team1} (N)",
    team1
}
guest_prob_names = {
    f"{team2} (n)",
    f"{team2} (N)",
    team2
}

# 数据库匹配
exist_matches = db_session.query(Match).filter(
    Match.LEAGUE == league_name,
    Match.HOST_TEAM.in_(host_prob_names),
    Match.GUEST_TEAM.in_(guest_prob_names),
    Match.MATCH_TIME == match_time
).all()
```

#### 3.3.5 结果更新逻辑

```python
for exist_match in exist_matches:
    # 防重复更新
    if exist_match.HOST_TEAM_RESULT:
        return  # 已有结果，跳过

    # 更新比分
    exist_match.HOST_TEAM_RESULT = host_result
    exist_match.GUEST_TEAM_RESULT = guest_result

    # 更新状态
    exist_match.status = "3"  # 已结束（比赛结算，后台可直接操作结算或者取消）
```

**状态流转**：
```
status = "1" (未开始)
    -> "2" (进行中，在handle_match_status中自动更新)
    -> "3" (已结束，等待结算)
    -> "4" (已结算，后台操作)
```

---

### 3.4 Redis缓存算法 (cache_to_redis)

#### 3.4.1 缓存分类策略

**六种缓存类型**：
```python
cache_keys = ['single', 'mix', 'old_mix', '1', '2', 'wdl']

cache_dicts = {
    'single':  {'1', '2', '6', '8', '10', '3'},  # 单式（让球、大小球、单双、Both/One/Neither、胜平负、波胆）
    'mix':     {'4', '5', '7', '9', '11'},       # 混合盘（让球、大小球、单双、Both/One/Neither、胜平负）
    'old_mix': {'4', '5'},                       # 混合盘（旧版，仅让球和大小球）
    '1':       {'1'},                            # 纯让球盘
    '2':       {'2'},                            # 纯大小球盘
}
```

**注意**：
- wdl key 在 cache_keys 中定义但 cache_dicts 中未使用
- 波胆（类型3）仅包含在 single 中
- Both/One/Neither（类型8）仅包含在 single 中

**缓存键设计**：
```
Redis Key格式：live_matches|{cache_type}
- live_matches|single
- live_matches|mix
- live_matches|old_mix
- live_matches|1
- live_matches|2
- live_odds（存储所有赔率详情）
```

#### 3.4.2 数据查询优化

**时间范围计算**：
```python
now = datetime.now()
now_utc = now.astimezone(timezone.utc)
day_after_tomorrow_end_utc = now_utc + timedelta(days=2, hours=12, minutes=00, seconds=59)

# 查询范围：当前时间 到 后天12:00:59（UTC）
# 缓存到第三天的10点30分之前的比赛（服务器时间12点）
```

**查询条件**：
```sql
SELECT * FROM m_app_match
WHERE MATCH_TIME >= :start_time
  AND MATCH_TIME <= :end_time
  AND CLOSING_TIME <= :end_time
  AND (hide IS NULL OR hide != '1')    -- 未隐藏
  AND IS_GAME_OVER = '0'               -- 未结束
  AND CLOSING_STATE = '0'              -- 未封盘
ORDER BY LEAGUE IN (五大联赛) DESC     -- 五大联赛优先
```

**五大联赛优先级**：
```python
priority_leagues = {
    'Spain Primera Division',
    'Italy Serie A',
    'Germany Bundesliga 1',
    'France Ligue 1',
    'English Premier League',
    'English League Championship'
}
```

#### 3.4.3 赔率格式化算法

**REAL_ODDS 生成逻辑**：
```python
attr_type = attr['MATCH_ATTR_TYPE']

if attr_type in {'6', '7'}:  # 波胆类型
    # 格式：主队赔率/客队赔率
    attr['REAL_ODDS'] = f"{attr['ODDS']}/{attr['ODDS_GUEST']}"
    # 示例："2.5/3.0"

else:  # 让球、大小球类型
    # 格式：球数+/-平局赔率
    sign = "-" if attr['DRAW_BUNKO'] == "1" else "+"
    attr['REAL_ODDS'] = f"{attr['LOSE_BALL_NUM']}{sign}{attr['DRAW_ODDS']}"
    # 示例："0.5+15"、"2.5-20"
```

#### 3.4.4 单双赔率配对算法

**配对规则**：
```python
single_mix_pair = {
    '1': '4',  # 单式让球 <-> 混合让球
    '2': '5',  # 单式大小球 <-> 混合大小球
    '4': '1',
    '5': '2',
}

# 检查配对是否存在
pair_attr_id = f'{match_web_id}_{single_mix_pair.get(attr_type)}'
if attr_type in single_mix_pair and pair_attr_id not in attrs_dict:
    continue  # 配对不存在，跳过该赔率
```

**意义**：确保混合盘和单式盘同时存在才展示，避免数据不完整。

#### 3.4.5 数据组装算法

**构建比赛-赔率树形结构**：
```python
# 步骤1：初始化比赛容器
for k, v in cache_dicts.items():
    if attr_type not in v:
        continue

    if match_id not in cache_list[k]:
        # 首次遇到该比赛，创建结构
        cache_list[k][match_id] = matches_dict[match_id].copy()
        cache_list[k][match_id]['ATTR'] = []

        # 获取主队图片和名称（优先使用Team Mapping配置）
        home_team = LeagueTteamScraper.get_match_team(HOST_TEAM_WEBID, session=db_session)
        if home_team and home_team.logo:
            cache_list[k][match_id]['home_logo'] = home_team.logo
        if home_team and home_team.show_name:
            cache_list[k][match_id]['HOST_TEAM'] = home_team.show_name

        # 获取客队图片和名称（优先使用Team Mapping配置）
        guest_team = LeagueTteamScraper.get_match_team(GUEST_TEAM_WEBID, session=db_session)
        if guest_team and guest_team.logo:
            cache_list[k][match_id]['away_logo'] = guest_team.logo
        if guest_team and guest_team.show_name:
            cache_list[k][match_id]['GUEST_TEAM'] = guest_team.show_name

    # 步骤2：添加赔率到比赛
    cache_list[k][match_id]['ATTR'].append(attr)
```

**球队信息优先级**：
1. 优先使用 LeagueTteamScraper（Team Mapping表）中配置的 show_name 和 logo
2. 如果未配置，则使用爬虫获取的原始球队名称
3. 这样可以统一球队名称显示（如"曼联"代替"Manchester United"）

**数据结构示例**：
```json
{
  "MATCH_ID": "1702345678000",
  "MATCH_DESC": "Manchester United vs Liverpool",
  "MATCH_TIME": "2024-12-10 20:00:00",
  "LEAGUE": "English Premier League",
  "HOST_TEAM": "Manchester United",
  "GUEST_TEAM": "Liverpool",
  "home_logo": "https://...",
  "away_logo": "https://...",
  "ATTR": [
    {
      "MATCH_ATTR_TYPE": "1",
      "REAL_ODDS": "0.5+15",
      "ODDS": "1.95",
      "ODDS_GUEST": "1.95",
      "LOSE_TEAM": "1"
    },
    {
      "MATCH_ATTR_TYPE": "2",
      "REAL_ODDS": "2.5-10",
      ...
    }
  ]
}
```

#### 3.4.6 比赛状态自动更新

```python
now = datetime.now()
for match in match_list:
    # 检测比赛是否已开始
    if match.status == "1" and match.MATCH_TIME <= now:
        # 状态转换：未开始 -> 进行中
        match.status = "2"
        match.CLOSING_STATE = "1"  # 自动封盘

        # 批量更新
        db_session.query(Match).filter(
            Match.MATCH_ID == match_id
        ).update({
            "status": "2",
            "CLOSING_STATE": "1"
        })
```

#### 3.4.7 Redis存储策略

```python
# 存储各类型比赛列表
for k, v in items.items():
    Redis.set(
        f"live_matches|{k}",
        json.dumps(v),
        Config.CACHE_EXPIRE_TIME  # 从配置文件读取过期时间
    )

# 存储所有赔率详情
Redis.set(
    "live_odds",
    json.dumps(cache_attrs),
    Config.CACHE_EXPIRE_TIME
)
```

**过期时间设计**：
- 从 Config.CACHE_EXPIRE_TIME 读取（灵活配置）
- 每次运行刷新：保持持续可用
- 异常容错：即使更新失败，旧数据仍可用一段时间

---

## 四、关键配置说明

### 4.1 代理配置
```python
# 从配置文件读取代理
proxy = Config.PROXY

# 从配置文件读取headers
headers = Config.HEADERS
```

### 4.2 账号配置
```python
# 从配置文件读取账号信息
username = Config.SCRAPER_USERNAME
password = Config.SCRAPER_PASSWORD
```

### 4.3 数据字典映射
```python
# 平局胜负符号
draw_bunko_dict = {'0': '+', '1': '-'}

# 让球方名称
lose_team_dict = {'1': '主队', '2': '客队'}

# 单双赔率配对
single_mix_pair = {'1': '4', '2': '5', '4': '1', '5': '2'}
```

---

## 五、执行流程总览

### 5.1 主流程 (main)
```python
if __name__ == '__main__':
    print("爬虫配置，账号:", scraper_cfg.pickAccount)
    cache_time = time.time()  # 记录总耗时

    try:
        get_matches(with_mix=True)   # 爬取比赛（包含混合盘）
    except Exception as e:
        traceback.print_exc()
        print("get_matches run error:", e)

    try:
        handle_match_status()         # 处理比赛状态（自动锁定已开始的比赛）
    except Exception as e:
        traceback.print_exc()
        print("handle_match_status run error:", e)

    try:
        cache_to_redis()              # 缓存到Redis
    except Exception as e:
        traceback.print_exc()
        print("cache_to_redis run error:", e)

    try:
        get_result()                  # 获取比赛结果
    except Exception as e:
        traceback.print_exc()
        print("get_result run error:", e)

    print(datetime.now(), " 总耗时:", time.time() - cache_time)
```

### 5.2 handle_match_status 函数详解

**功能**：自动锁定已开始的比赛，更新比赛状态

```python
def handle_match_status():
    db_session = DBSession()
    now = datetime.now()

    # 查询状态为"1"（未开始）且比赛时间已到的比赛
    matchs = db_session.query(Match).filter(
        Match.status == "1",
        Match.MATCH_TIME <= now
    ).all()

    n = 0
    for match in matchs:
        n += 1
        update_info = {"status": "2"}  # 更新为进行中

        # 同时检查封盘时间
        if match.CLOSING_STATE == "0" and match.CLOSING_TIME <= now:
            update_info["CLOSING_STATE"] = "1"  # 封盘

        db_session.query(Match).filter(Match.ID == match.ID).update(update_info)

    db_session.commit()
    db_session.close()
    print("自动锁定比赛数量:", n)
```

**状态转换**：
- status: "1" (未开始) → "2" (进行中)
- CLOSING_STATE: "0" (未封盘) → "1" (已封盘)

**意义**：确保比赛状态与实际时间同步，防止用户对已开始的比赛下注

### 5.3 典型调度方案

**建议定时任务**：
```
*/5 * * * * python ibet_runner.py  # 每5分钟执行一次
```

**执行时间分析**：
- get_matches: 10-30秒（取决于比赛数量）
- handle_match_status: 1-2秒
- cache_to_redis: 2-5秒
- get_result: 3-8秒
- 总计：16-45秒

---

## 六、异常处理机制

### 6.1 网络异常
- 所有HTTP请求设置 timeout=7秒
- 代理失败自动记录但不中断

### 6.2 数据异常
- 变盘检测：自动隐藏异常比赛
- 重复比赛：自动更新web_id并删除旧赔率
- 比分缺失：跳过更新

### 6.3 数据库异常
- 事务机制：commit失败自动回滚
- Session管理：使用 try-finally 确保close

---

## 七、性能优化建议

### 7.1 已实现优化
✅ 批量merge赔率数据
✅ 批量update隐藏状态
✅ 字典缓存旧数据（减少重复查询）
✅ Redis缓存结果（减轻数据库压力）

### 7.2 可优化点
⚠️ 可使用多线程爬取两个接口
⚠️ 可增加数据库连接池配置
⚠️ 可添加本地缓存减少重复计算

---

## 八、数据流图

```
┌─────────────┐
│  ibet789    │
│  网站接口    │
└──────┬──────┘
       │ 爬取
       ▼
┌─────────────┐     ┌──────────────┐
│ get_matches │────▶│   MySQL      │
│  比赛数据    │     │ Match表      │
└─────────────┘     │ MatchAttr表  │
                    └──────┬───────┘
                           │ 查询
                           ▼
                    ┌──────────────┐
                    │cache_to_redis│
                    │  缓存构建    │
                    └──────┬───────┘
                           │ 存储
                           ▼
                    ┌──────────────┐
                    │    Redis     │
                    │  前端缓存    │
                    └──────────────┘

┌─────────────┐
│  Result页面 │
│  比赛结果    │
└──────┬──────┘
       │ 爬取
       ▼
┌─────────────┐
│ get_result  │
│  结果更新    │
└──────┬──────┘
       │ 更新
       ▼
┌──────────────┐
│   MySQL      │
│ Match.status │
│ 比分结果     │
└──────────────┘
```

---

## 九、常见问题

### Q1: 为什么需要变盘检测？
**A**: 赔率变化通常涉及让球数、赔率、平局胜负、让球方四个要素。正常情况下，如果让球数和赔率都不变，其他两项也不应变化。如果出现不一致，可能是数据源异常或人为操作错误，需要隐藏避免用户下注到错误盘口。

### Q2: 0球让球为什么需要特殊处理？
**A**: 0球让球时，主队让球且平局赔率为正数的情况在业务逻辑上不成立（0球让球理论上应该是客队让球或平局赔率为负），因此需要自动修正为客队让球并反转平局胜负。

### Q3: 为什么要区分Myanmar盘？
**A**: 不同地区的盘口规则不同，Myanmar盘是特定市场的盘口类型，通过 match[76]、match[77] 和 match[72]、match[75] 的组合判断。只处理Myanmar盘确保数据一致性。

### Q4: live_matches集合的作用是什么？
**A**: 它使用了"排除法"思想：
1. 初始包含所有活跃比赛
2. 每处理一个新数据就移除
3. 最后剩余的是"网站上消失的比赛"
4. 这些比赛可能已开始或被取消，需要隐藏

### Q5: 为什么混合盘赔率固定为2？
**A**: 混合盘是组合投注，其ODDS字段只用于标识，实际赔率由前端根据DRAW_ODDS、LOSE_BALL_NUM等计算。固定为2是业务规则，表示这是混合盘类型。

---

## 十、维护建议

### 10.1 日志监控
- 定期检查 "变盘日志.txt" 发现异常模式
- 监控 "check_result.html" 确保登录正常
- 记录执行时间发现性能退化

### 10.2 数据校验
- 定期比对网站数据与数据库数据
- 检查是否有比赛长期处于 hide='1' 状态
- 验证比分更新及时性

### 10.3 配置调整
- 根据服务器性能调整爬取频率
- 根据业务需求调整赔率阈值（odds_cond_*）
- 定期更新联赛白名单

---

## 十一、技术债务

### 11.1 硬编码问题
- ✅ 账号密码已改为从配置文件读取（Config.SCRAPER_USERNAME/PASSWORD）
- ✅ 代理地址已改为从配置文件读取（Config.PROXY）
- ✅ Headers已改为从配置文件读取（Config.HEADERS）
- 联赛优先级硬编码（建议改为数据库配置）

### 11.2 代码重复
- 让球盘和大小球盘处理逻辑高度相似
- 建议提取公共函数

### 11.3 异常处理
- 部分异常直接 print，未记录到日志系统
- 建议集成专业日志框架（如 logging）

---

## 十二、版本历史

**当前版本特性**：
- ✅ 支持让球盘、大小球盘、胜平负盘（1X2）
- ✅ 支持波胆盘（Correct Score，类型3）
- ✅ 支持单双盘（Odd/Even，类型6）
- ✅ 支持Both/One/Neither Team To Score（类型8）
- ✅ 变盘异常检测
- ✅ 比赛去重机制
- ✅ Redis缓存优化
- ✅ 自动结果更新（支持今日和昨日）
- ✅ 五大联赛优先排序
- ✅ 配置文件化（账号、代理、缓存过期时间等）
- ✅ 球队名称和图片优化（支持Team Mapping配置）
- ✅ 自动比赛状态管理（handle_match_status）
- ✅ 支持爬取今日和明日比赛
- ✅ 双重1X2数据源（MoreBets优先，OddsOE1X2备份）

**版本改进**：
- 从硬编码改为配置文件读取（账号、代理、headers）
- 从固定过期时间改为配置化（Config.CACHE_EXPIRE_TIME）
- 增强错误处理（traceback.print_exc()）
- 优化球队显示（优先使用show_name）

**未来规划**：
- [ ] 增加实时推送机制
- [ ] 优化并发爬取性能（多线程）
- [ ] 增加数据分析报表
- [ ] 支持更多赔率类型（如混合单双、混合Both/One/Neither）

---

**文档编写日期**: 2025-12-23（最后更新）
**适用代码版本**: ibet_runner.py (当前版本)
**维护者**: 技术团队

**文档修订记录**：
- 2025-12-23: 根据实际代码更新文档，补充新增赔率类型、配置读取方式、handle_match_status等内容
