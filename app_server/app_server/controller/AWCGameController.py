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


def validate_promotion_wallet_for_awc(user_id, game_platform=None):
    """
    验证玩家是否有支持AWC/Egame的活动，从而允许使用促销钱包

    Args:
        user_id: 玩家ID/手机号
        game_platform: 具体的游戏平台名称（如 'JILI', 'PG', 'PRAGMATIC' 等），用于精确匹配

    Returns:
        dict: {
            'valid': bool,  # 是否验证通过
            'message': str,  # 错误消息（如果验证失败）
            'activity_info': dict  # 活动信息（如果验证通过）
        }
    """
    try:
        from app_server.model.AppPlayerActivityRecordModel import AppPlayerActivityRecord
        from app_server.model.MAppCouponModel import MAppCoupon
        from app_server.model.AppMemberModel import AppMember
        from app_server import db

        # 1. 获取玩家ID
        member = AppMember.query.filter_by(phone=user_id).first()
        if not member:
            return {
                'valid': False,
                'message': 'Player not found'
            }

        # 2. 查询玩家正在参与的活动（status='ACTIVE'或'Active'）
        active_records = AppPlayerActivityRecord.query.filter(
            AppPlayerActivityRecord.mb_id == member.id,
            AppPlayerActivityRecord.status.in_(['ACTIVE', 'Active']),
            AppPlayerActivityRecord.del_flag == 0
        ).all()

        if not active_records:
            logger.info(f"Player {user_id} has no active activities, cannot use promotion wallet for AWC")
            return {
                'valid': False,
                'message': 'No active activity found. You must participate in an activity that supports AWC/Egame to use promotion wallet.'
            }

        # 3. 遍历活动记录，检查是否有支持AWC/Egame的活动
        for record in active_records:
            activity_type = record.activity_type
            activity_id = record.activity_id

            logger.info(f"Checking activity: type={activity_type}, id={activity_id}, name={record.activity_name}")

            # 根据活动类型查询对应的活动配置
            if activity_type == 'COUPON':
                # 优惠券：检查 usage_scenario_config
                coupon = MAppCoupon.query.filter_by(id=activity_id, del_flag=0).first()
                if coupon and coupon.usage_scenario_config:
                    try:
                        scenario_config = json.loads(coupon.usage_scenario_config)

                        # 新格式：{"scenarios": [{"type": "Egame", "enabled": true, "config": {...}}, ...]}
                        scenarios = scenario_config.get('scenarios', [])

                        if scenarios:
                            # 遍历所有场景，查找启用的Egame场景
                            for scenario in scenarios:
                                scenario_type = scenario.get('type', '')
                                enabled = scenario.get('enabled', False)
                                config = scenario.get('config', {})

                                # 检查是否是启用的Egame场景
                                if scenario_type == 'Egame' and enabled:
                                    # 如果配置了platforms，需要检查具体的游戏平台是否在列表中
                                    platforms = config.get('platforms', [])

                                    if platforms:
                                        # 如果提供了具体的游戏平台，检查是否在允许列表中
                                        if game_platform:
                                            # 不区分大小写比较
                                            allowed_platforms_upper = [p.upper() for p in platforms]
                                            game_platform_upper = game_platform.upper()

                                            if game_platform_upper in allowed_platforms_upper:
                                                logger.info(f"Player {user_id} has active COUPON activity '{record.activity_name}' supporting platform '{game_platform}', promotion wallet allowed")
                                                return {
                                                    'valid': True,
                                                    'message': 'Validation passed',
                                                    'activity_info': {
                                                        'type': activity_type,
                                                        'name': record.activity_name,
                                                        'scenario': 'Egame',
                                                        'platforms': platforms,
                                                        'matched_platform': game_platform
                                                    }
                                                }
                                            else:
                                                logger.info(f"Player {user_id} has Egame scenario but platform '{game_platform}' not in allowed list {platforms}")
                                                continue
                                        else:
                                            # 没有提供游戏平台（向后兼容），使用旧逻辑检查是否有AWC平台
                                            from app_server.model.AwcGameModel import AwcGame
                                            awc_platforms = [p.upper() for p in AwcGame.get_platforms()]
                                            has_awc = any(platform.upper() in awc_platforms for platform in platforms)

                                            if has_awc:
                                                logger.info(f"Player {user_id} has active COUPON activity '{record.activity_name}' supporting Egame with AWC platforms: {platforms}, promotion wallet allowed (no platform specified)")
                                                return {
                                                    'valid': True,
                                                    'message': 'Validation passed',
                                                    'activity_info': {
                                                        'type': activity_type,
                                                        'name': record.activity_name,
                                                        'scenario': 'Egame',
                                                        'platforms': platforms
                                                    }
                                                }
                                            else:
                                                logger.info(f"Player {user_id} has Egame scenario but platforms {platforms} don't include AWC")
                                                continue
                                    else:
                                        # 没有配置platforms，表示支持所有Egame平台
                                        logger.info(f"Player {user_id} has active COUPON activity '{record.activity_name}' supporting all Egame platforms, promotion wallet allowed")
                                        return {
                                            'valid': True,
                                            'message': 'Validation passed',
                                            'activity_info': {
                                                'type': activity_type,
                                                'name': record.activity_name,
                                                'scenario': 'Egame',
                                                'platforms': 'all'
                                            }
                                        }
                        else:
                            # 旧格式兼容：{"type": "Egame", "config": {...}} 或 {"type": "All"}
                            scenario_type = scenario_config.get('type', '')
                            if scenario_type in ['Egame', 'All']:
                                logger.info(f"Player {user_id} has active COUPON activity '{record.activity_name}' supporting {scenario_type} (legacy format), promotion wallet allowed")
                                return {
                                    'valid': True,
                                    'message': 'Validation passed',
                                    'activity_info': {
                                        'type': activity_type,
                                        'name': record.activity_name,
                                        'scenario': scenario_type
                                    }
                                }

                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to parse usage_scenario_config for coupon {activity_id}: {str(e)}")
                        continue
                    except Exception as e:
                        logger.error(f"Error processing usage_scenario_config for coupon {activity_id}: {str(e)}", exc_info=True)
                        continue

            elif activity_type == 'PROMOTION':
                # 促销活动：检查 egamesConfig
                # 查询 m_app_promotion 表
                promotion_result = db.session.execute(
                    db.text("SELECT egames_config FROM m_app_promotion WHERE id = :id AND del_flag = 0"),
                    {'id': activity_id}
                ).fetchone()

                if promotion_result and promotion_result[0]:
                    # egamesConfig 不为空，表示支持Egame
                    logger.info(f"Player {user_id} has active PROMOTION activity '{record.activity_name}' with egamesConfig, promotion wallet allowed")
                    return {
                        'valid': True,
                        'message': 'Validation passed',
                        'activity_info': {
                            'type': activity_type,
                            'name': record.activity_name,
                            'scenario': 'Egame'
                        }
                    }

            elif activity_type == 'INVITATION':
                # 邀请活动：默认允许（或根据业务需求调整）
                logger.info(f"Player {user_id} has active INVITATION activity '{record.activity_name}', promotion wallet allowed")
                return {
                    'valid': True,
                    'message': 'Validation passed',
                    'activity_info': {
                        'type': activity_type,
                        'name': record.activity_name,
                        'scenario': 'All'
                    }
                }

        # 4. 没有找到支持AWC/Egame的活动
        logger.info(f"Player {user_id} has {len(active_records)} active activity(ies), but none support AWC/Egame")
        return {
            'valid': False,
            'message': 'Your current activity does not support AWC/Egame games. Please use main wallet or join an activity that supports Egame.'
        }

    except Exception as e:
        logger.error(f"Error validating promotion wallet for AWC: {str(e)}", exc_info=True)
        return {
            'valid': False,
            'message': f'Validation error: {str(e)}'
        }


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
        walletType: 钱包类型 Money/Promotion (可选，默认Money)
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

        username = g.user.username
        platform = data.get('platform')
        game_type = data.get('gameType')
        game_code = data.get('gameCode')
        wallet_type = data.get('walletType', 'Money')  # 默认使用主钱包

        if not all([username, platform, game_type, game_code]):
            return Kits.rt_error('Missing required parameters: userId, platform, gameType, gameCode')

        # 验证钱包类型
        if wallet_type not in ['Money', 'Promotion']:
            return Kits.rt_error('Invalid walletType, must be Money or Promotion')

        # 如果选择促销钱包，需要验证玩家是否有支持AWC/Egame的活动
        if wallet_type == 'Promotion':
            validation_result = validate_promotion_wallet_for_awc(username, platform)
            if not validation_result['valid']:
                return Kits.rt_error(validation_result['message'])

        # 获取默认配置
        awc_service = get_awc_api_service()
        currency = data.get('currency') or awc_service.default_currency
        language = data.get('language') or awc_service.default_language
        is_mobile = data.get('isMobileLogin', 'true') in ['true', 'True', True, '1', 1]

        is_new_member = False

        # 第一步：查询用户的awc字段，检查是否已注册
        member = AppMember.query.filter_by(username=username).first()

        if not member:
            logger.error(f"User not found: {username}")
            return Kits.rt_error('User not found')

        # 更新玩家当前选择的钱包类型
        try:
            from app_server import db
            from datetime import datetime

            # 只有在钱包类型发生变化时才更新
            if member.current_wallet_type != wallet_type:
                member.current_wallet_type = wallet_type
                member.wallet_type_update_time = datetime.now()
                db.session.commit()
                logger.info(f"Updated wallet selection for user {username}: {wallet_type} at {member.wallet_type_update_time}")
            else:
                logger.info(f"Wallet type unchanged for user {username}: {wallet_type}")
        except Exception as wallet_update_error:
            logger.error(f"Failed to update wallet type: {str(wallet_update_error)}", exc_info=True)
            # 不影响游戏启动，继续执行

        # 检查用户是否已在AWC注册
        need_create = not hasattr(member, 'awc') or member.awc != '1'

        if need_create:
            # 第二步：创建AWC会员
            try:
                default_bet_limit = awc_service.default_bet_limit

                logger.info(f"Creating AWC member - userId: {username}, currency: {currency}, language: {language}, betLimit: {default_bet_limit}")

                create_result = awc_service.create_member(
                    user_id=username,
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
                    logger.info(f"Successfully created AWC member and updated database: {username}")
                elif create_result.get('status') == '1017':
                    # 1017 = 会员已存在，更新数据库awc字段
                    from datetime import datetime
                    from app_server import db
                    member.awc = '1'
                    if not member.awc_createtime:
                        member.awc_createtime = datetime.now()
                    db.session.commit()
                    logger.info(f"AWC member already exists, updated database flag: {username}")
                else:
                    # 其他错误，返回错误信息
                    error_msg = create_result.get('desc', 'Failed to create AWC member')
                    logger.error(f"创建AWC会员失败: status={create_result.get('status')}, desc={error_msg}, user={username}")
                    return Kits.rt_error(f'Failed to create game account: {error_msg}')
            except Exception as create_error:
                # 创建异常，返回错误
                logger.error(f"创建AWC会员异常: {str(create_error)}, user={username}", exc_info=True)
                return Kits.rt_error(f'Failed to create game account: {str(create_error)}')
        else:
            logger.info(f"User already registered with AWC, launch game directly: {username}")

        # 第三步：启动游戏
        # 处理布尔值
        is_launch_game_table = None
        if 'isLaunchGameTable' in data:
            is_launch_game_table = data.get('isLaunchGameTable') in ['true', 'True', True, '1', 1]

        is_enable_jackpot = None
        if 'isEnableJackpot' in data:
            is_enable_jackpot = data.get('isEnableJackpot') in ['true', 'True', True, '1', 1]

        result = awc_service.do_login_and_launch_game(
            user_id=username,
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

            # 创建游戏会话记录
            try:
                from app_server.model.GameSessionModel import GameSession
                from app_server.model.AwcGameModel import AwcGame
                from app_server import db

                # 获取游戏名称
                game = AwcGame.get_by_game_code(game_code)
                game_name = game.name_en if game else game_code

                # 创建会话记录
                session = GameSession.create_session(
                    mb_id=member.id,
                    mb_username=member.username or member.phone,
                    game_code=game_code,
                    game_name=game_name,
                    platform=platform,
                    game_type=game_type,
                    main_wallet=member.money or 0,
                    promo_wallet=member.money_promotion or 0,
                    game_url=result.get('url'),
                    aid=member.aid
                )

                db.session.add(session)
                db.session.commit()

                # 返回sessionId给前端
                result['sessionId'] = session.id

                logger.info(f"Created game session: {session.id} for user {member.username}, game {game_name}")

            except Exception as session_error:
                # 会话创建失败不影响游戏启动，只记录日志
                logger.error(f"Failed to create game session: {str(session_error)}", exc_info=True)

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

        # 默认排序
        print("game_types", game_types)
        # 优化排序逻辑：优先按 leagues_sort 顺序排列，其余按名称排序
        type_sort = ["EGAME", "SLOT", "LIVE"]
        if type_sort:
            def sort_key(name):
                if name in type_sort:
                    return (0, type_sort.index(name))  # 在优先列表中，按索引排序
                else:
                    return (1, name)  # 不在优先列表中，按名称排序

            game_types.sort(key=sort_key)
        else:
            game_types.sort()  # 如果没有配置排序，按名称排序

        logger.info(f"获取游戏类型列表成功: {game_types}")

        return Kits.rt_code(200, '获取成功', {
            'gameTypes': game_types
        })

    except Exception as e:
        logger.error(f"获取游戏类型列表失败: {str(e)}", exc_info=True)
        return Kits.rt_error(f'获取游戏类型列表失败: {str(e)}')


@awc_game_bp.route('/getHotGames', methods=['GET', 'POST'])
def get_hot_games():
    """
    获取热门游戏列表

    请求参数:
        gameType: 游戏类型 (可选)，如果不传则返回所有类型的热门游戏
        pageNo: 页码 (可选，默认1)
        pageSize: 每页数量 (可选，默认20)

    返回:
        {
            "code": 200,
            "message": "Success",
            "data": {
                "records": [游戏列表],
                "total": 总数,
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
        game_type = data.get('gameType')
        page_no = int(data.get('pageNo', 1))
        page_size = int(data.get('pageSize', 20))

        # 获取当前登录用户的ID（如果已登录）
        mb_id = None
        _auth = auth.get_auth()
        if _auth and verify_token(_auth.get('token')):
            mb_id = g.user.id

        # 获取热门游戏
        games, total = AwcGame.get_game_list(
            filter_type='hot',
            game_type=game_type,
            platform=None,
            page_no=page_no,
            page_size=page_size
        )

        # 转换为移动端格式
        game_list = [game.to_mobile_dict() for game in games]

        # 如果用户已登录，添加isFavourite字段
        if mb_id:
            favourite_codes = AwcGameFavourite.get_user_favourites(mb_id)
            for game in game_list:
                game['isFavourite'] = 1 if game['gameCode'] in favourite_codes else 0
        else:
            for game in game_list:
                game['isFavourite'] = 0

        logger.info(f"获取热门游戏成功: gameType={game_type}, total={total}")

        return Kits.rt_code(200, '获取成功', {
            'records': game_list,
            'total': total,
            'pageNo': page_no,
            'pageSize': page_size
        })

    except Exception as e:
        logger.error(f"获取热门游戏失败: {str(e)}", exc_info=True)
        return Kits.rt_error(f'获取热门游戏失败: {str(e)}')


@awc_game_bp.route('/getAllVendors', methods=['GET', 'POST'])
def get_all_vendors():
    """
    获取所有厂商列表（按游戏类型分组）

    请求参数:
        gameType: 游戏类型 (可选)，如果不传则返回所有类型的厂商

    返回:
        {
            "code": 200,
            "message": "Success",
            "data": {
                "vendors": [
                    {
                        "platform": "JILI",
                        "gameCount": 150,
                        "sampleGame": {
                            "iconUrl": "...",
                            "thumbnailUrl": "..."
                        },
                        "platform_image": "/image/platform/JILI/JILI.png"
                    },
                    ...
                ]
            }
        }
    """
    try:
        from app_server.model.AwcGameModel import AwcGame
        from app_server import db

        data = get_request_data()
        game_type = data.get('gameType')

        # 构建查询
        query = db.session.query(
            AwcGame.platform,
            db.func.count(AwcGame.id).label('game_count')
        ).filter(
            AwcGame.status == 1,
            AwcGame.del_flag == 0
        )

        # 如果指定了游戏类型，添加过滤
        if game_type and game_type != 'All':
            query = query.filter(AwcGame.game_type == game_type)

        # 按平台分组并计数
        vendors_data = query.group_by(AwcGame.platform).all()

        # 为每个厂商获取一个示例游戏图片
        vendors = []
        for platform, game_count in vendors_data:
            # 获取该平台的第一个游戏作为示例
            sample_query = AwcGame.query.filter(
                AwcGame.platform == platform,
                AwcGame.status == 1,
                AwcGame.del_flag == 0
            )

            if game_type and game_type != 'All':
                sample_query = sample_query.filter(AwcGame.game_type == game_type)

            sample_game = sample_query.order_by(AwcGame.sort_order.desc()).first()

            vendor_info = {
                'platform': platform,
                'gameCount': game_count,
                'platform_image': f'/image/platform/{platform}/{platform}.png'
            }

            # 添加示例游戏图片
            if sample_game:
                vendor_info['sampleGame'] = {
                    'iconUrl': sample_game.icon_url,
                    'thumbnailUrl': sample_game.thumbnail_url
                }

            vendors.append(vendor_info)

        # 按游戏数量降序排列
        vendors.sort(key=lambda x: x['gameCount'], reverse=True)

        logger.info(f"获取厂商列表成功: gameType={game_type}, vendorCount={len(vendors)}")

        return Kits.rt_code(200, '获取成功', {
            'vendors': vendors
        })

    except Exception as e:
        logger.error(f"获取厂商列表失败: {str(e)}", exc_info=True)
        return Kits.rt_error(f'获取厂商列表失败: {str(e)}')


@awc_game_bp.route('/closeGameSession', methods=['POST'])
@auth.login_required
def close_game_session():
    """
    关闭游戏会话

    当用户退出游戏时调用，计算余额变化和盈亏

    请求参数:
        sessionId: 会话ID (必填)

    返回:
        {
            "code": 200,
            "message": "Session closed successfully",
            "ok": true,
            "data": {
                "sessionId": "会话ID",
                "netTotal": 净变化金额,
                "resultStatus": "Win/Loss/Draw",
                "sessionDuration": 会话时长(秒)
            }
        }
    """
    try:
        from flask import g
        from app_server.model.GameSessionModel import GameSession, SessionStatus
        from app_server.model.AppMemberModel import AppMember
        from datetime import datetime
        from app_server import db

        data = get_request_data()
        session_id = data.get('sessionId')

        if not session_id:
            return Kits.rt_error('Missing required parameter: sessionId')

        # 查找会话
        session = GameSession.query.filter_by(id=session_id, del_flag=0).first()
        if not session:
            return Kits.rt_error('Session not found')

        # 验证会话所属用户
        if session.mb_id != g.user.id:
            return Kits.rt_error('Session does not belong to current user')

        # 检查会话是否已关闭
        if session.session_status == SessionStatus.Completed:
            logger.info(f"Session {session_id} already closed")
            return Kits.rt_code(200, 'Session already closed', {
                'sessionId': session.id,
                'netTotal': float(session.net_total) if session.net_total else 0,
                'resultStatus': session.result_status,
                'sessionDuration': session.session_duration
            })

        # 获取当前余额
        member = AppMember.query.filter_by(id=session.mb_id).first()
        if not member:
            return Kits.rt_error('Member not found')

        # 更新退出时间和余额
        session.exit_time = datetime.now()

        # 计算余额变化和结果
        session.calculate_results(
            exit_main_wallet=member.money or 0,
            exit_promo_wallet=member.money_promotion or 0
        )

        # 更新会话状态为已完成
        session.session_status = SessionStatus.Completed

        db.session.commit()

        logger.info(f"Closed game session: {session.id}, user: {member.username}, "
                   f"net_total: {session.net_total}, result: {session.result_status}")

        return Kits.rt_code(200, 'Session closed successfully', {
            'sessionId': session.id,
            'netTotal': float(session.net_total) if session.net_total else 0,
            'resultStatus': session.result_status,
            'sessionDuration': session.session_duration,
            'entryMainWallet': float(session.entry_main_wallet),
            'entryPromoWallet': float(session.entry_promo_wallet),
            'exitMainWallet': float(session.exit_main_wallet) if session.exit_main_wallet else 0,
            'exitPromoWallet': float(session.exit_promo_wallet) if session.exit_promo_wallet else 0
        })

    except Exception as e:
        logger.error(f"Close session failed: {str(e)}", exc_info=True)
        return Kits.rt_error(f'Failed to close session: {str(e)}')


@awc_game_bp.route('/sessionHeartbeat', methods=['POST'])
@auth.login_required
def session_heartbeat():
    """
    游戏会话心跳

    前端定期调用以更新会话状态，防止会话超时

    请求参数:
        sessionId: 会话ID (必填)

    返回:
        {
            "code": 200,
            "message": "Heartbeat updated",
            "ok": true,
            "data": {
                "sessionId": "会话ID",
                "lastHeartbeatTime": "最后心跳时间"
            }
        }
    """
    try:
        from flask import g
        from app_server.model.GameSessionModel import GameSession, SessionStatus
        from datetime import datetime
        from app_server import db

        data = get_request_data()
        session_id = data.get('sessionId')

        if not session_id:
            return Kits.rt_error('Missing required parameter: sessionId')

        # 查找会话
        session = GameSession.query.filter_by(id=session_id, del_flag=0).first()
        if not session:
            return Kits.rt_error('Session not found')

        # 验证会话所属用户
        if session.mb_id != g.user.id:
            return Kits.rt_error('Session does not belong to current user')

        # 只更新进行中的会话
        if session.session_status == SessionStatus.InProgress:
            session.last_heartbeat_time = datetime.now()
            db.session.commit()

            return Kits.rt_code(200, 'Heartbeat updated', {
                'sessionId': session.id,
                'lastHeartbeatTime': session.last_heartbeat_time.isoformat()
            })
        else:
            return Kits.rt_code(200, 'Session already completed', {
                'sessionId': session.id,
                'sessionStatus': session.session_status
            })

    except Exception as e:
        logger.error(f"Session heartbeat failed: {str(e)}", exc_info=True)
        return Kits.rt_error(f'Failed to update heartbeat: {str(e)}')


@awc_game_bp.route('/getGameSessionHistory', methods=['GET', 'POST'])
@auth.login_required
def get_game_session_history():
    """
    获取用户的游戏会话历史

    请求参数:
        pageNo: 页码 (可选，默认1)
        pageSize: 每页数量 (可选，默认20)
        sessionStatus: 会话状态过滤 (可选: InProgress, Completed, Timeout)
        resultStatus: 结果状态过滤 (可选: Win, Loss, Draw)

    返回:
        {
            "code": 200,
            "message": "Success",
            "ok": true,
            "data": {
                "records": [...],
                "total": 100,
                "pageNo": 1,
                "pageSize": 20
            }
        }
    """
    try:
        from flask import g
        from app_server.model.GameSessionModel import GameSession

        data = get_request_data()
        page_no = int(data.get('pageNo', 1))
        page_size = int(data.get('pageSize', 20))
        session_status_filter = data.get('sessionStatus')
        result_status_filter = data.get('resultStatus')

        # 构建查询
        query = GameSession.query.filter_by(
            mb_id=g.user.id,
            del_flag=0
        )

        # 状态过滤
        if session_status_filter:
            query = query.filter_by(session_status=session_status_filter)

        if result_status_filter:
            query = query.filter_by(result_status=result_status_filter)

        # 排序
        query = query.order_by(GameSession.entry_time.desc())

        # 获取总数
        total = query.count()

        # 分页
        sessions = query.paginate(
            page=page_no,
            per_page=page_size,
            error_out=False
        )

        # 转换为字典
        session_list = [session.to_dict() for session in sessions.items]

        logger.info(f"Get game session history: user={g.user.username}, total={total}")

        return Kits.rt_code(200, 'Get session history successfully', {
            'records': session_list,
            'total': total,
            'pageNo': page_no,
            'pageSize': page_size
        })

    except Exception as e:
        logger.error(f"Get game session history failed: {str(e)}", exc_info=True)
        return Kits.rt_error(f'Failed to get session history: {str(e)}')


@awc_game_bp.route('/getGameConfig', methods=['GET'])
@auth.login_required
def get_game_config():
    """
    获取游戏配置（包括闲置超时等设置）

    返回:
        {
            "code": 200,
            "message": "Success",
            "data": {
                "enabled": true,
                "timeoutMinutes": 15,
                "warningMinutes": 2,
                "awcAutoLogout": true,
                "sessionHeartbeatInterval": 30,
                "sessionMaxDuration": 120
            }
        }
    """
    try:
        from flask import current_app

        # 从Flask配置读取游戏设置
        config = {
            'enabled': current_app.config.get('AWC_GAME_IDLE_TIMEOUT_ENABLED', True),
            'timeoutMinutes': current_app.config.get('AWC_GAME_IDLE_TIMEOUT_MINUTES', 15),
            'warningMinutes': current_app.config.get('AWC_GAME_IDLE_WARNING_MINUTES', 2),
            'awcAutoLogout': current_app.config.get('AWC_GAME_AUTO_LOGOUT', True),
            'sessionHeartbeatInterval': current_app.config.get('AWC_GAME_SESSION_HEARTBEAT_INTERVAL', 30),
            'sessionMaxDuration': current_app.config.get('AWC_GAME_SESSION_MAX_DURATION', 120)
        }

        return Kits.rt_code(200, 'Success', config)

    except Exception as e:
        logger.error(f"Get game config failed: {str(e)}", exc_info=True)
        # 返回默认配置
        return Kits.rt_code(200, 'Success', {
            'enabled': True,
            'timeoutMinutes': 15,
            'warningMinutes': 2,
            'awcAutoLogout': True,
            'sessionHeartbeatInterval': 30,
            'sessionMaxDuration': 120
        })
