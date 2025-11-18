# -*- coding: utf-8 -*-
"""
AWC游戏API控制器
为UniApp前端提供AWC游戏相关接口

@author: Arthur
@date: 2025-10-17
"""

from flask import Blueprint, request, jsonify

from app_server import auth
from app_server.controller.AppUserController import verify_token
from app_server.service.AWCApiService import get_awc_api_service
from app_server.utils.Kits import Kits
import logging
import json

logger = logging.getLogger(__name__)

# 创建蓝图
awc_game_bp = Blueprint('awc_game', __name__, url_prefix='/awc')


def get_request_data():
    """获取请求数据"""
    if request.method == 'POST':
        return request.form.to_dict() if request.form else request.get_json(force=True, silent=True) or {}
    return request.args.to_dict()


@awc_game_bp.route('/createMember', methods=['POST'])
def create_member():
    """
    创建AWC玩家账户

    请求参数:
        userId: 玩家ID (必填)
        currency: 货币类型 (必填)
        betLimit: 下注限红配置JSON (必填)
        language: 语言 (可选)
        userName: 显示名称 (可选)

    返回:
        {
            "success": true/false,
            "message": "消息",
            "data": {
                "status": "0000",
                "desc": "Success"
            }
        }
    """
    try:
        data = get_request_data()
        user_id = data.get('userId')
        currency = data.get('currency')
        bet_limit = data.get('betLimit')
        language = data.get('language')
        user_name = data.get('userName')

        if not user_id or not currency or not bet_limit:
            return Kits.rt_error('缺少必填参数: userId, currency, betLimit')

        awc_service = get_awc_api_service()
        result = awc_service.create_member(
            user_id=user_id,
            currency=currency,
            bet_limit=bet_limit,
            language=language,
            user_name=user_name
        )

        if result.get('status') == '0000':
            return Kits.rt_code(200, '创建玩家成功', result)
        else:
            return Kits.rt_error(result.get('desc', '创建玩家失败'))

    except Exception as e:
        logger.error(f"创建AWC玩家失败: {str(e)}", exc_info=True)
        return Kits.rt_error(f'创建玩家失败: {str(e)}')


@awc_game_bp.route('/login', methods=['POST'])
def login():
    """
    玩家登入AWC游戏大厅

    请求参数:
        userId: 玩家ID (必填)
        isMobileLogin: 是否移动端 true/false (可选)
        externalURL: 返回URL (可选)
        platform: 平台名称 (可选)
        gameType: 游戏类型 (可选)
        gameForbidden: 禁止游戏JSON (可选)
        language: 语言 (可选)
        betLimit: 下注限红JSON (可选)
        autoBetMode: 自动下注模式 (可选)
        oddsMode: 赔率模式 (可选)
        isEnableJackpot: 是否启用Jackpot (可选)
        landingSportId: 默认体育分类 (可选)

    返回:
        {
            "success": true/false,
            "message": "消息",
            "data": {
                "status": "0000",
                "url": "游戏登录URL",
                "extension": [...]
            }
        }
    """
    try:
        data = get_request_data()
        user_id = data.get('userId')

        if not user_id:
            return Kits.rt_error('缺少必填参数: userId')

        # 处理布尔值
        is_mobile_login = None
        if 'isMobileLogin' in data:
            is_mobile_login = data.get('isMobileLogin') in ['true', 'True', True, '1', 1]

        is_enable_jackpot = None
        if 'isEnableJackpot' in data:
            is_enable_jackpot = data.get('isEnableJackpot') in ['true', 'True', True, '1', 1]

        awc_service = get_awc_api_service()
        result = awc_service.login(
            user_id=user_id,
            is_mobile_login=is_mobile_login,
            external_url=data.get('externalURL'),
            platform=data.get('platform'),
            game_type=data.get('gameType'),
            game_forbidden=data.get('gameForbidden'),
            language=data.get('language'),
            bet_limit=data.get('betLimit'),
            autoBetMode=data.get('autoBetMode'),
            oddsMode=data.get('oddsMode'),
            isEnableJackpot=is_enable_jackpot,
            landingSportId=data.get('landingSportId')
        )

        if result.get('status') == '0000':
            return Kits.rt_code(200, '登录成功', result)
        else:
            return Kits.rt_error(result.get('desc', '登录失败'))

    except Exception as e:
        logger.error(f"AWC登录失败: {str(e)}", exc_info=True)
        return Kits.rt_error(f'登录失败: {str(e)}')


@awc_game_bp.route('/launchGame', methods=['POST'])
@auth.login_required
def launch_game():
    """
    玩家登入并进入指定游戏

    自动注册流程：
    1. 检查用户的awc字段，判断是否已注册
    2. 如果未注册(awc!='1')，先创建AWC会员，然后更新awc='1'
    3. 启动游戏并返回游戏URL

    请求参数:
        userId: 玩家ID/手机号 (可选，如果不传则从JWT token获取)
        platform: 平台名称 (必填)
        gameType: 游戏类型 (必填)
        gameCode: 游戏代码 (必填)
        isMobileLogin: 是否移动端 (可选，默认true)
        currency: 货币类型 (可选，默认MMK)
        language: 语言 (可选，默认en)
        externalURL: 返回URL (可选)
        hall: 大厅类型 (可选)
        betLimit: 下注限红JSON (可选)
        其他可选参数...

    返回:
        {
            "code": 200,
            "message": "Success",
            "ok": true,
            "data": {
                "status": "0000",
                "url": "游戏URL",
                "isNewMember": true/false,
                "extension": [...]
            }
        }
    """
    try:
        from app_server.model.AppMemberModel import AppMember
        from flask import g

        data = get_request_data()

        # 优先从前端获取userId，如果没有则从JWT token获取
        user_id = data.get('userId')
        if not user_id:
            user_id = g.user.phone

        platform = data.get('platform')
        game_type = data.get('gameType')
        game_code = data.get('gameCode')

        if not all([user_id, platform, game_type, game_code]):
            return Kits.rt_error('Missing required parameters: userId, platform, gameType, gameCode')

        # 获取默认配置
        awc_service = get_awc_api_service()
        currency = data.get('currency') or awc_service.default_currency
        language = data.get('language') or awc_service.default_language
        is_mobile = data.get('isMobileLogin', 'true') in ['true', 'True', True, '1', 1]

        is_new_member = False

        # 第一步：查询用户的awc字段，检查是否已注册
        member = AppMember.query.filter_by(phone=user_id).first()

        if not member:
            logger.error(f"User not found: {user_id}")
            return Kits.rt_error('User not found')

        # 检查用户是否已在AWC注册
        need_create = not hasattr(member, 'awc') or member.awc != '1'

        if need_create:
            # 第二步：创建AWC会员
            try:
                default_bet_limit = awc_service.default_bet_limit

                logger.info(f"Creating AWC member - userId: {user_id}, currency: {currency}, language: {language}, betLimit: {default_bet_limit}")

                create_result = awc_service.create_member(
                    user_id=user_id,
                    currency=currency,
                    bet_limit=default_bet_limit,
                    language=language
                )

                logger.info(f"AWC create member response: {create_result}")

                if create_result.get('status') == '0000':
                    # 创建成功，更新数据库awc字段为'1'
                    from datetime import datetime
                    from app_server import db
                    member.awc = '1'
                    member.awc_createtime = datetime.now()
                    db.session.commit()
                    is_new_member = True
                    logger.info(f"Successfully created AWC member and updated database: {user_id}")
                elif create_result.get('status') == '1017':
                    # 1017 = 会员已存在，更新数据库awc字段
                    from datetime import datetime
                    from app_server import db
                    member.awc = '1'
                    if not member.awc_createtime:
                        member.awc_createtime = datetime.now()
                    db.session.commit()
                    logger.info(f"AWC member already exists, updated database flag: {user_id}")
                else:
                    # 其他错误，返回错误信息
                    error_msg = create_result.get('desc', 'Failed to create AWC member')
                    logger.error(f"创建AWC会员失败: status={create_result.get('status')}, desc={error_msg}, user={user_id}")
                    return Kits.rt_error(f'Failed to create game account: {error_msg}')
            except Exception as create_error:
                # 创建异常，返回错误
                logger.error(f"创建AWC会员异常: {str(create_error)}, user={user_id}", exc_info=True)
                return Kits.rt_error(f'Failed to create game account: {str(create_error)}')
        else:
            logger.info(f"User already registered with AWC, launch game directly: {user_id}")

        # 第三步：启动游戏
        # 处理布尔值
        is_launch_game_table = None
        if 'isLaunchGameTable' in data:
            is_launch_game_table = data.get('isLaunchGameTable') in ['true', 'True', True, '1', 1]

        is_enable_jackpot = None
        if 'isEnableJackpot' in data:
            is_enable_jackpot = data.get('isEnableJackpot') in ['true', 'True', True, '1', 1]

        result = awc_service.do_login_and_launch_game(
            user_id=user_id,
            platform=platform,
            game_type=game_type,
            game_code=game_code,
            is_mobile_login=is_mobile,
            external_url=data.get('externalURL'),
            hall=data.get('hall'),
            language=language,
            bet_limit=data.get('betLimit'),
            autoBetMode=data.get('autoBetMode'),
            isLaunchGameTable=is_launch_game_table,
            gameTableId=data.get('gameTableId'),
            oddsMode=data.get('oddsMode'),
            isEnableJackpot=is_enable_jackpot,
            landingSportId=data.get('landingSportId')
        )

        if result.get('status') == '0000':
            # 添加新会员标记
            result['isNewMember'] = is_new_member
            return Kits.rt_code(200, 'Launch game successfully', result)
        else:
            return Kits.rt_error(result.get('desc', 'Failed to launch game'))

    except Exception as e:
        logger.error(f"AWC进入游戏失败: {str(e)}", exc_info=True)
        return Kits.rt_error(f'Failed to launch game: {str(e)}')


@awc_game_bp.route('/updateBetLimit', methods=['POST'])
def update_bet_limit():
    """
    更新玩家投注限红

    请求参数:
        userId: 玩家ID (必填)
        betLimit: 下注限红配置JSON (必填)

    返回:
        {
            "success": true/false,
            "message": "消息",
            "data": {"status": "0000", "desc": "Success"}
        }
    """
    try:
        data = get_request_data()
        user_id = data.get('userId')
        bet_limit = data.get('betLimit')

        if not user_id or not bet_limit:
            return Kits.rt_error('缺少必填参数: userId, betLimit')

        awc_service = get_awc_api_service()
        result = awc_service.update_bet_limit(user_id=user_id, bet_limit=bet_limit)

        if result.get('status') == '0000':
            return Kits.rt_code(200, '更新限红成功', result)
        else:
            return Kits.rt_error(result.get('desc', '更新限红失败'))

    except Exception as e:
        logger.error(f"更新AWC限红失败: {str(e)}", exc_info=True)
        return Kits.rt_error(f'更新限红失败: {str(e)}')


@awc_game_bp.route('/logout', methods=['POST'])
def logout():
    """
    强制玩家登出

    请求参数:
        userIds: 玩家ID列表，逗号分隔 (必填)

    返回:
        {
            "success": true/false,
            "message": "消息",
            "data": {
                "status": "0000",
                "logoutUsers": [...],
                "count": 2
            }
        }
    """
    try:
        data = get_request_data()
        user_ids = data.get('userIds')

        if not user_ids:
            return Kits.rt_error('缺少必填参数: userIds')

        awc_service = get_awc_api_service()
        result = awc_service.logout(user_ids=user_ids)

        if result.get('status') == '0000':
            return Kits.rt_code(200, '登出成功', result)
        else:
            return Kits.rt_error(result.get('desc', '登出失败'))

    except Exception as e:
        logger.error(f"AWC登出失败: {str(e)}", exc_info=True)
        return Kits.rt_error(f'登出失败: {str(e)}')


@awc_game_bp.route('/updatePlayerStatus', methods=['POST'])
def update_player_status():
    """
    更新玩家状态

    请求参数:
        userId: 玩家ID (必填)
        status: 状态 active/suspend/lock (必填)

    返回:
        {
            "success": true/false,
            "message": "消息",
            "data": {"status": "0000", "desc": "Success"}
        }
    """
    try:
        data = get_request_data()
        user_id = data.get('userId')
        status = data.get('status')

        if not user_id or not status:
            return Kits.rt_error('缺少必填参数: userId, status')

        if status not in ['active', 'suspend', 'lock']:
            return Kits.rt_error('status参数必须是: active, suspend, lock')

        awc_service = get_awc_api_service()
        result = awc_service.update_player_status(user_id=user_id, status=status)

        if result.get('status') == '0000':
            return Kits.rt_code(200, '更新状态成功', result)
        else:
            return Kits.rt_error(result.get('desc', '更新状态失败'))

    except Exception as e:
        logger.error(f"更新AWC玩家状态失败: {str(e)}", exc_info=True)
        return Kits.rt_error(f'更新状态失败: {str(e)}')


@awc_game_bp.route('/getTransactionHistory', methods=['GET', 'POST'])
def get_transaction_history():
    """
    获取交易历史记录

    请求参数:
        userId: 玩家ID (必填)
        platformTxId: 平台交易单号 (必填)
        platform: 平台名称 (必填)
        roundId: 回合识别码 (可选，SEXYBCRT需要)

    返回:
        {
            "success": true/false,
            "message": "消息",
            "data": {
                "status": "0000",
                "url": "回放URL",
                "txnUrl": "",
                "roundUrl": ""
            }
        }
    """
    try:
        data = get_request_data()
        user_id = data.get('userId')
        platform_tx_id = data.get('platformTxId')
        platform = data.get('platform')
        round_id = data.get('roundId')

        if not all([user_id, platform_tx_id, platform]):
            return Kits.rt_error('缺少必填参数: userId, platformTxId, platform')

        awc_service = get_awc_api_service()
        result = awc_service.get_transaction_history_result(
            user_id=user_id,
            platform_tx_id=platform_tx_id,
            platform=platform,
            round_id=round_id
        )

        if result.get('status') == '0000':
            return Kits.rt_code(200, '获取成功', result)
        else:
            return Kits.rt_error(result.get('desc', '获取失败'))

    except Exception as e:
        logger.error(f"获取AWC交易历史失败: {str(e)}", exc_info=True)
        return Kits.rt_error(f'获取失败: {str(e)}')


@awc_game_bp.route('/getSummary', methods=['GET', 'POST'])
def get_summary():
    """
    获取交易摘要

    请求参数:
        startTime: 开始时间 (必填, 格式: 2018-09-26T12+08:00)
        endTime: 结束时间 (必填)
        platform: 平台名称 (必填)
        gameType: 游戏类型 (可选)
        gameCode: 游戏代码 (可选)

    返回:
        {
            "success": true/false,
            "message": "消息",
            "data": {
                "status": "0000",
                "transactions": [...]
            }
        }
    """
    try:
        data = get_request_data()
        start_time = data.get('startTime')
        end_time = data.get('endTime')
        platform = data.get('platform')

        if not all([start_time, end_time, platform]):
            return Kits.rt_error('缺少必填参数: startTime, endTime, platform')

        awc_service = get_awc_api_service()
        result = awc_service.get_summary_by_bet_time_hour(
            start_time=start_time,
            end_time=end_time,
            platform=platform,
            game_type=data.get('gameType'),
            game_code=data.get('gameCode')
        )

        if result.get('status') == '0000':
            return Kits.rt_code(200, '获取成功', result)
        else:
            return Kits.rt_error(result.get('desc', '获取失败'))

    except Exception as e:
        logger.error(f"获取AWC交易摘要失败: {str(e)}", exc_info=True)
        return Kits.rt_error(f'获取失败: {str(e)}')


@awc_game_bp.route('/checkStatus', methods=['GET', 'POST'])
def check_status():
    """
    检查系统状态

    请求参数:
        platform: 平台名称 (可选)
        gameType: 游戏类型 (可选)
        gameCode: 游戏代码 (可选)

    返回:
        {
            "success": true/false,
            "message": "消息",
            "data": {"status": "0000"}
        }
    """
    try:
        data = get_request_data()

        awc_service = get_awc_api_service()
        result = awc_service.check_status(
            platform=data.get('platform'),
            game_type=data.get('gameType'),
            game_code=data.get('gameCode')
        )

        if result.get('status') == '0000':
            return Kits.rt_code(200, '系统正常', result)
        else:
            return Kits.rt_error(result.get('desc', '系统异常'))

    except Exception as e:
        logger.error(f"检查AWC状态失败: {str(e)}", exc_info=True)
        return Kits.rt_error(f'检查失败: {str(e)}')


@awc_game_bp.route('/queryBetLimit', methods=['GET', 'POST'])
def query_bet_limit():
    """
    查询玩家下注限额

    请求参数:
        userId: 玩家ID (必填)
        platform: 平台名称 (必填)
        gameType: 游戏类型 (必填)

    返回:
        {
            "success": true/false,
            "message": "消息",
            "data": {
                "status": "0000",
                "betLimit": "{...}"
            }
        }
    """
    try:
        data = get_request_data()
        user_id = data.get('userId')
        platform = data.get('platform')
        game_type = data.get('gameType')

        if not all([user_id, platform, game_type]):
            return Kits.rt_error('缺少必填参数: userId, platform, gameType')

        awc_service = get_awc_api_service()
        result = awc_service.query_bet_limit(
            user_id=user_id,
            platform=platform,
            game_type=game_type
        )

        if result.get('status') == '0000':
            return Kits.rt_code(200, '查询成功', result)
        else:
            return Kits.rt_error(result.get('desc', '查询失败'))

    except Exception as e:
        logger.error(f"查询AWC限红失败: {str(e)}", exc_info=True)
        return Kits.rt_error(f'查询失败: {str(e)}')


@awc_game_bp.route('/getPlatformList', methods=['GET', 'POST'])
def get_platform_list():
    """
    获取平台列表

    返回:
        {
            "success": true/false,
            "message": "消息",
            "data": {
                "status": "0000",
                "agentId": "...",
                "platform": "SPADE,PP,..."
            }
        }
    """
    try:
        awc_service = get_awc_api_service()
        result = awc_service.get_platform_list_by_agent()

        if result.get('status') == '0000':
            # 将平台字符串转换为数组
            if 'platform' in result and isinstance(result['platform'], str):
                result['platformList'] = result['platform'].split(',')
            return Kits.rt_code(200, '获取成功', result)
        else:
            return Kits.rt_error(result.get('desc', '获取失败'))

    except Exception as e:
        logger.error(f"获取AWC平台列表失败: {str(e)}", exc_info=True)
        return Kits.rt_error(f'获取失败: {str(e)}')


@awc_game_bp.route('/getJackpotPool', methods=['GET', 'POST'])
def get_jackpot_pool():
    """
    查询Jackpot彩池金额

    请求参数:
        platform: 平台名称 (必填, JILI或FC)
        gameType: 游戏类型 (必填)
        currency: 货币类型 (必填)

    返回:
        {
            "success": true/false,
            "message": "消息",
            "data": {
                "status": "0000",
                "results": {...}
            }
        }
    """
    try:
        data = get_request_data()
        platform = data.get('platform')
        game_type = data.get('gameType')
        currency = data.get('currency')

        if not all([platform, game_type, currency]):
            return Kits.rt_error('缺少必填参数: platform, gameType, currency')

        awc_service = get_awc_api_service()
        result = awc_service.get_jackpot_pool(
            platform=platform,
            game_type=game_type,
            currency=currency
        )

        if result.get('status') == '0000':
            return Kits.rt_code(200, '查询成功', result)
        else:
            return Kits.rt_error(result.get('desc', '查询失败'))

    except Exception as e:
        logger.error(f"查询AWC Jackpot失败: {str(e)}", exc_info=True)
        return Kits.rt_error(f'查询失败: {str(e)}')


@awc_game_bp.route('/getLobbyState', methods=['GET', 'POST'])
def get_lobby_state():
    """
    获取桌子维护状态

    请求参数:
        platform: 平台名称 (必填, SEXYBCRT或EVOLUTION)

    返回:
        {
            "success": true/false,
            "message": "消息",
            "data": {
                "status": "0000",
                "results": [...]
            }
        }
    """
    try:
        data = get_request_data()
        platform = data.get('platform')

        if not platform:
            return Kits.rt_error('缺少必填参数: platform')

        awc_service = get_awc_api_service()
        result = awc_service.get_lobby_state(platform=platform)

        if result.get('status') == '0000':
            return Kits.rt_code(200, '获取成功', result)
        else:
            return Kits.rt_error(result.get('desc', '获取失败'))

    except Exception as e:
        logger.error(f"获取AWC桌子状态失败: {str(e)}", exc_info=True)
        return Kits.rt_error(f'获取失败: {str(e)}')


@awc_game_bp.route('/enterGameLobby', methods=['POST'])
@auth.login_required
def enter_game_lobby():
    """
    Auto register and login to AWC game lobby

    Flow:
    1. Check user's awc field to determine if already registered
    2. If not registered (awc!='1'), create AWC member first, then update awc='1'
    3. Login to AWC game lobby
    4. Return game URL

    Request parameters:
        userId: Player ID (required)
        currency: Currency type (optional, default MMK)
        language: Language (optional, default en)
        isMobileLogin: Is mobile login (optional, default true)

    Response:
        {
            "code": 200,
            "message": "Success",
            "ok": true,
            "data": {
                "status": "0000",
                "url": "Game login URL",
                "isNewMember": true/false  // Whether newly created member
            }
        }
    """
    try:
        from app_server.model.AppMemberModel import AppMember

        data = get_request_data()
        user_id = data.get('userId')

        if not user_id:
            return Kits.rt_error('Missing required parameter: userId')

        # Get default values from config
        awc_service = get_awc_api_service()
        currency = data.get('currency') or awc_service.default_currency
        language = data.get('language') or awc_service.default_language
        is_mobile = data.get('isMobileLogin', 'true') in ['true', 'True', True, '1', 1]

        is_new_member = False

        # Step 1: Query user's awc field to check if already registered
        member = AppMember.query.filter_by(phone=user_id).first()

        if not member:
            logger.error(f"User not found: {user_id}")
            return Kits.rt_error('User not found')

        # Check if user is already registered with AWC
        need_create = not hasattr(member, 'awc') or member.awc != '1'

        if need_create:
            # Step 2: Create AWC member
            try:
                # Use default betLimit from configuration
                # betLimit is required for LIVE games - format: {"SEXYBCRT":{"LIVE":{"limitId":[280301]}}}
                # Contact AWC to get your agent's limitId
                default_bet_limit = awc_service.default_bet_limit

                logger.info(f"Creating AWC member - userId: {user_id}, currency: {currency}, language: {language}, betLimit: {default_bet_limit}")

                create_result = awc_service.create_member(
                    user_id=user_id,
                    currency=currency,
                    bet_limit=default_bet_limit,
                    language=language
                )

                logger.info(f"AWC create member response: {create_result}")

                if create_result.get('status') == '0000':
                    # Created successfully, update database awc field to '1'
                    from datetime import datetime
                    from app_server import db
                    member.awc = '1'
                    member.awc_createtime = datetime.now()
                    db.session.commit()
                    is_new_member = True
                    logger.info(f"Successfully created AWC member and updated database: {user_id}")
                elif create_result.get('status') == '1017':
                    # 1017 = Member already exists, update database awc field
                    from datetime import datetime
                    from app_server import db
                    member.awc = '1'
                    if not member.awc_createtime:
                        member.awc_createtime = datetime.now()
                    db.session.commit()
                    logger.info(f"AWC member already exists, updated database flag: {user_id}")
                else:
                    # Other errors, return error message to frontend
                    error_msg = create_result.get('desc', 'Failed to create AWC member')
                    logger.error(f"Failed to create AWC member: status={create_result.get('status')}, desc={error_msg}, user={user_id}")
                    return Kits.rt_error(f'{error_msg}')
            except Exception as create_error:
                # Creation exception, return error
                logger.error(f"Exception creating AWC member: {str(create_error)}, user={user_id}", exc_info=True)
                return Kits.rt_error(f'Failed to create AWC member: {str(create_error)}')
        else:
            logger.info(f"User already registered with AWC, login directly: {user_id}")

        # Step 3: Login to game lobby
        login_result = awc_service.login(
            user_id=user_id,
            is_mobile_login=is_mobile,
            language=language
        )

        if login_result.get('status') == '0000':
            # Add new member flag
            login_result['isNewMember'] = is_new_member
            return Kits.rt_code(200, 'Successfully entered game lobby', login_result)
        else:
            return Kits.rt_error(login_result.get('desc', 'Failed to login to game lobby'))

    except Exception as e:
        logger.error(f"Failed to enter AWC game lobby: {str(e)}", exc_info=True)
        return Kits.rt_error(f'Failed to enter game lobby: {str(e)}')


@awc_game_bp.route('/getAwcGameList', methods=['GET', 'POST'])
def get_awcGame_list():
    """
    获取游戏大厅列表（移动端）

    根据分类（Hot/New/All）、游戏类型（Casino/Sport等）返回游戏列表

    请求参数:
        filter: 筛选条件 hot/new/all/favourite (可选，默认all)
        gameType: 游戏类型 LIVE/SLOT/EGAME/FISH 等 (可选)
        platform: 平台名称 (可选)
        pageNo: 页码 (可选，默认1)
        pageSize: 每页数量 (可选，默认20)

    返回:
        {
            "code": 200,
            "message": "Success",
            "ok": true,
            "data": {
                "records": [
                    {
                        "id": "游戏ID",
                        "platform": "CRASH88",
                        "gameType": "EGAME",
                        "gameCode": "CRASH88-EGAME-001",
                        "nameEn": "AVIATORX",
                        "nameZh": "AVIATORX",
                        "iconUrl": "游戏图标URL",
                        "thumbnailUrl": "缩略图URL",
                        "rtp": 95.00,
                        "isHot": 1,
                        "isNew": 0,
                        "sortOrder": 100,
                        "status": 1,
                        "isFavourite": 0
                    }
                ],
                "total": 17,
                "pageNo": 1,
                "pageSize": 20
            }
        }
    """
    try:
        from app_server.model.AwcGameModel import AwcGame
        from app_server.model.AwcGameFavouriteModel import AwcGameFavourite
        from flask import g

        data = get_request_data()
        filter_type = data.get('filter', 'all').lower()  # hot/new/all/favourite
        game_type = data.get('gameType')
        platform = data.get('platform')
        page_no = int(data.get('pageNo', 1))
        page_size = int(data.get('pageSize', 20))

        # 获取当前登录用户的ID（如果已登录）
        mb_id = None
        _auth = auth.get_auth()
        if _auth and verify_token(_auth.get('token')):
            mb_id = g.user.id

        # 如果筛选类型是favourite，只返回收藏的游戏
        if filter_type == 'favourite':
            if not mb_id:
                return Kits.rt_error('查看收藏需要登录')

            # 获取用户收藏的游戏代码列表
            favourite_codes = AwcGameFavourite.get_user_favourites(mb_id)

            if not favourite_codes:
                # 没有收藏，返回空列表
                return Kits.rt_code(200, '获取成功', {
                    'records': [],
                    'total': 0,
                    'pageNo': page_no,
                    'pageSize': page_size
                })

            # 查询收藏的游戏
            query = AwcGame.query.filter(
                AwcGame.game_code.in_(favourite_codes),
                AwcGame.status == 1,
                AwcGame.del_flag == 0
            )

            # 按游戏类型筛选
            if game_type:
                query = query.filter_by(game_type=game_type)

            # 按平台筛选
            if platform:
                query = query.filter_by(platform=platform)

            # 获取总数
            total = query.count()

            # 分页查询（按收藏时间排序，收藏越晚越靠前）
            # 这里简化处理，直接按sort_order排序
            games = query.order_by(
                AwcGame.sort_order.desc(),
                AwcGame.id.desc()
            ).paginate(page=page_no, per_page=page_size, error_out=False).items

        else:
            # 使用Model的静态方法获取游戏列表
            games, total = AwcGame.get_game_list(
                filter_type=filter_type,
                game_type=game_type,
                platform=platform,
                page_no=page_no,
                page_size=page_size
            )

        # 转换为移动端格式
        game_list = [game.to_mobile_dict() for game in games]

        # 如果用户已登录，添加isFavourite字段标记是否已收藏
        if mb_id:
            favourite_codes = AwcGameFavourite.get_user_favourites(mb_id)
            for game in game_list:
                game['isFavourite'] = 1 if game['gameCode'] in favourite_codes else 0
        else:
            # 未登录用户，全部标记为未收藏
            for game in game_list:
                game['isFavourite'] = 0

        logger.info(f"获取AWC游戏列表成功: filter={filter_type}, gameType={game_type}, platform={platform}, mbId={mb_id}, total={total}")

        return Kits.rt_code(200, '获取成功', {
            'records': game_list,
            'total': total,
            'pageNo': page_no,
            'pageSize': page_size
        })

    except Exception as e:
        logger.error(f"获取游戏大厅列表失败: {str(e)}", exc_info=True)
        return Kits.rt_error(f'获取游戏列表失败: {str(e)}')


@awc_game_bp.route('/getGameDetail', methods=['GET', 'POST'])
def get_game_detail():
    """
    获取游戏详情

    请求参数:
        gameCode: 游戏代码 (必填)

    返回:
        {
            "code": 200,
            "message": "Success",
            "ok": true,
            "data": {
                "id": "游戏ID",
                "platform": "CRASH88",
                "gameType": "EGAME",
                "gameCode": "CRASH88-EGAME-001",
                "nameEn": "AVIATORX",
                "nameZh": "AVIATORX",
                "iconUrl": "游戏图标URL",
                "rtp": 95.00,
                ...
            }
        }
    """
    try:
        from app_server.model.AwcGameModel import AwcGame

        data = get_request_data()
        game_code = data.get('gameCode')

        if not game_code:
            return Kits.rt_error('缺少必填参数: gameCode')

        # 根据游戏代码获取游戏
        game = AwcGame.get_by_game_code(game_code)

        if not game:
            return Kits.rt_error('游戏不存在或已下架')

        logger.info(f"获取游戏详情成功: gameCode={game_code}")

        return Kits.rt_code(200, '获取成功', game.to_dict())

    except Exception as e:
        logger.error(f"获取游戏详情失败: {str(e)}", exc_info=True)
        return Kits.rt_error(f'获取游戏详情失败: {str(e)}')


@awc_game_bp.route('/getGamePlatforms', methods=['GET', 'POST'])
def get_game_platforms():
    """
    获取游戏平台列表

    返回:
        {
            "code": 200,
            "message": "Success",
            "ok": true,
            "data": {
                "platforms": ["CRASH88", "PP", "JILI", ...]
            }
        }
    """
    try:
        from app_server.model.AwcGameModel import AwcGame

        platforms = AwcGame.get_platforms()

        logger.info(f"获取平台列表成功: count={len(platforms)}")

        return Kits.rt_code(200, '获取成功', {
            'platforms': platforms
        })

    except Exception as e:
        logger.error(f"获取平台列表失败: {str(e)}", exc_info=True)
        return Kits.rt_error(f'获取平台列表失败: {str(e)}')


@awc_game_bp.route('/addGameFavourite', methods=['POST'])
@auth.login_required
def add_game_favourite():
    """
    添加游戏收藏

    请求参数:
        gameCode: 游戏代码 (必填)

    返回:
        {
            "code": 200,
            "message": "收藏成功",
            "data": null
        }
    """
    try:
        from app_server.model.AwcGameModel import AwcGame
        from app_server.model.AwcGameFavouriteModel import AwcGameFavourite
        from flask import g

        data = get_request_data()
        game_code = data.get('gameCode')

        if not game_code:
            return Kits.rt_error('缺少必填参数: gameCode')

        # 从JWT token中获取当前登录用户的ID
        mb_id = g.user.id

        # 检查游戏是否存在
        game = AwcGame.get_by_game_code(game_code)
        if not game:
            return Kits.rt_error('游戏不存在')

        # 添加收藏
        success = AwcGameFavourite.add_favourite(mb_id, game.id, game_code)

        if success:
            logger.info(f"用户 {mb_id} 收藏游戏 {game_code} 成功")
            return Kits.rt_code(200, '收藏成功', None)
        else:
            return Kits.rt_error('游戏已在收藏列表中')

    except Exception as e:
        logger.error(f"添加游戏收藏失败: {str(e)}", exc_info=True)
        return Kits.rt_error(f'添加收藏失败: {str(e)}')


@awc_game_bp.route('/removeGameFavourite', methods=['POST'])
@auth.login_required
def remove_game_favourite():
    """
    取消游戏收藏

    请求参数:
        gameCode: 游戏代码 (必填)

    返回:
        {
            "code": 200,
            "message": "取消收藏成功",
            "data": null
        }
    """
    try:
        from app_server.model.AwcGameFavouriteModel import AwcGameFavourite
        from flask import g

        data = get_request_data()
        game_code = data.get('gameCode')

        if not game_code:
            return Kits.rt_error('缺少必填参数: gameCode')

        # 从JWT token中获取当前登录用户的ID
        mb_id = g.user.id

        # 取消收藏
        success = AwcGameFavourite.remove_favourite(mb_id, game_code)

        if success:
            logger.info(f"用户 {mb_id} 取消收藏游戏 {game_code} 成功")
            return Kits.rt_code(200, '取消收藏成功', None)
        else:
            return Kits.rt_error('游戏不在收藏列表中')

    except Exception as e:
        logger.error(f"取消游戏收藏失败: {str(e)}", exc_info=True)
        return Kits.rt_error(f'取消收藏失败: {str(e)}')


@awc_game_bp.route('/getGameTypes', methods=['GET', 'POST'])
def get_game_types():
    """
    获取游戏类型列表

    返回:
        {
            "code": 200,
            "message": "Success",
            "ok": true,
            "data": {
                "gameTypes": ["LIVE", "SLOT", "EGAME", "FISH", ...]
            }
        }
    """
    try:
        from app_server.model.AwcGameModel import AwcGame

        game_types = AwcGame.get_game_types()

        logger.info(f"获取游戏类型列表成功: count={len(game_types)}")

        return Kits.rt_code(200, '获取成功', {
            'gameTypes': game_types
        })

    except Exception as e:
        logger.error(f"获取游戏类型列表失败: {str(e)}", exc_info=True)
        return Kits.rt_error(f'获取游戏类型列表失败: {str(e)}')
