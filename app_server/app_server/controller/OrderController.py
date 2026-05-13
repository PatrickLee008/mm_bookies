import traceback
import json

from app_server import db, auth, app_opt, Redis
from app_server.logger import get_logger
from flask import g, request, jsonify, Blueprint

from app_server.model.AppMemberBalanceLogModel import TransactionType
from app_server.model.AppSettingBet1x2Model import AppSettingBet1x2Model
from app_server.model.GameSessionModel import GameSession, ResultStatus
from app_server.model.MAppInvitationRewardModel import MAppInvitationReward
from app_server.model.MatchModel import Match, MatchAttr, VipMatchAttr
from app_server.model import GameType
from app_server.model.OrderModel import Order, OrderType, BetType
from app_server.model.OrderHistoryModel import OrderHistory
from app_server.model.AppBetOrderModel import AppBetOrder, BetStatus, PayWallet
from app_server.model.AppPlayerActivityRecordModel import AppPlayerActivityRecord
from app_server.model.MAppCouponModel import MAppCoupon
from app_server.model.MAppInvitationActivityModel import MAppInvitationActivity
from app_server.model.MAppPromotionModel import MAppPromotion
from app_server.utils.Kits import Kits
from app_server.utils.MemberMessageService import MemberMessageService
from sqlalchemy import or_, func, and_
from app_server.utils.sphinxapi import *
import ipaddress
import datetime
import time
import uuid

order = Blueprint('order', __name__)
logger = get_logger()


def convert_myanmar_to_china_time(date_str, is_end_time=False):
    """
    将缅甸时间转换为中国时间（加上1.5小时）

    系统设计说明：
    - 数据库存储服务器本地时间（中国时间），使用 datetime.now
    - 前端发送的是用户本地日期（缅甸日期）
    - 需要将缅甸日期转换为对应的中国时间范围进行数据库查询

    时区关系：
    - 缅甸时区：UTC+6:30
    - 中国时区：UTC+8:00
    - 转换公式：中国时间 = 缅甸时间 + 1.5小时

    Args:
        date_str: 日期字符串，格式为 'YYYY-MM-DD'（缅甸本地日期）
        is_end_time: 是否为结束时间（True则使用23:59:59，False则使用00:00:00）

    Returns:
        转换后的中国时间字符串，格式为 'YYYY-MM-DD HH:MM:SS'

    示例：
        缅甸 2024-01-28 00:00 -> 中国 2024-01-28 01:30
        缅甸 2024-01-28 23:59 -> 中国 2024-01-29 01:29
    """
    if not date_str:
        return None

    try:
        # 添加时间部分
        time_suffix = " 23:59:59" if is_end_time else " 00:00:00"
        full_time_str = date_str + time_suffix

        # 解析为datetime对象
        dt = datetime.datetime.strptime(full_time_str, "%Y-%m-%d %H:%M:%S")

        # 加上1.5小时（缅甸时间转中国时间）
        # 时区关系：中国UTC+8:00，缅甸UTC+6:30，中国比缅甸慢1.5小时
        dt = dt + datetime.timedelta(hours=1, minutes=30)

        # 返回格式化的时间字符串
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception as e:
        logger.error(f"Time conversion error: {e}, input: {date_str}")
        return None


def validate_promotion_activity(user_id, bet_amount, bet_type):
    """
    验证使用优惠钱包时的活动限制

    Args:
        user_id: 用户ID
        bet_amount: 下注金额
        bet_type: 下注类型 ('Single' 或 'Mixparlay')

    Returns:
        tuple: (success, error_response)
               success为True时error_response为None
               success为False时error_response为jsonify响应
    """
    # 检查是否有正在参加的活动（只查询未达标的活动）
    existing_active_activity = db.session.query(AppPlayerActivityRecord).filter(
        AppPlayerActivityRecord.mb_id == user_id,
        AppPlayerActivityRecord.status == 'Active',
        AppPlayerActivityRecord.is_requirement_met == 0,  # 只查询未达标的活动
        AppPlayerActivityRecord.del_flag == 0
    ).first()

    if not existing_active_activity:
        # 使用优惠钱包但没有活动记录，不允许下注
        response = jsonify({'message': 'No active promotion activity found'})
        response.status_code = 400
        return False, response

    activity_type = existing_active_activity.activity_type
    activity_id = existing_active_activity.activity_id

    # 根据活动类型查询对应的活动配置
    activity_config = None

    if activity_type == 'COUPON':
        activity_config = MAppCoupon.query.filter_by(
            id=activity_id,
            del_flag=0
        ).first()
    elif activity_type == 'INVITATION':
        # 邀请活动没有限制
        return True, None
        # response = jsonify({
        #     'message': 'Currently only coupons are supported. Other types will be available soon.'
        # })
        # response.status_code = 400
        # return False, response
        # activity_config = MAppInvitationActivity.query.filter_by(
        #     id=activity_id,
        #     del_flag=0
        # ).first()
    elif activity_type == 'PROMOTION':
        activity_config = MAppPromotion.query.filter_by(
            id=activity_id,
            del_flag=0
        ).first()
    else:
        # 未知活动类型
        response = jsonify({'message': 'Unknown activity type'})
        response.status_code = 400
        return False, response

    if not activity_config:
        response = jsonify({'message': 'Activity not found'})
        response.status_code = 400
        return False, response

    # 格式化活动类型（首字母大写，其余小写）
    activity_type_formatted = activity_type.capitalize()

    # 统一校验使用场景限制
    if hasattr(activity_config, 'usage_scenario_config') and activity_config.usage_scenario_config:
        try:
            # print(f"[DEBUG] usage_scenario_config raw: {activity_config.usage_scenario_config}")
            # print(f"[DEBUG] usage_scenario_config type: {type(activity_config.usage_scenario_config)}")
            usage_config = json.loads(activity_config.usage_scenario_config)
            # print(f"[DEBUG] usage_config parsed: {usage_config}")

            # 检查是否有 "All" 类型（无限制）
            if usage_config.get('type') == 'All':
                return True, None

            # 检查 scenarios 配置
            scenarios = usage_config.get('scenarios', [])

            # 查找 1x2 场景配置
            x2_scenario = None
            for scenario in scenarios:
                if scenario.get('type') == '1x2':
                    x2_scenario = scenario
                    break

            if x2_scenario:
                # 检查是否启用
                if not x2_scenario.get('enabled', False):
                    response = jsonify({
                        'message': f'{activity_type_formatted}: 1x2 betting is not enabled for this activity'
                    })
                    response.status_code = 400
                    return False, response

                # 检查 bet_types 配置
                config = x2_scenario.get('config', {})
                if config:
                    bet_types = config.get('bet_types', [])
                    if bet_type not in bet_types:
                        response = jsonify({
                            'message': f'{activity_type_formatted}: {bet_type} betting is not allowed for this activity'
                        })
                        response.status_code = 400
                        return False, response
            else:
                # 没有找到 1x2 场景配置，不允许 1x2 下注
                response = jsonify({
                    'message': f'{activity_type_formatted}: 1x2 betting is not supported for this activity'
                })
                response.status_code = 400
                return False, response

        except json.JSONDecodeError as e:
            # JSON 解析失败，返回错误
            # print(f"[ERROR] JSON decode error: {str(e)}")
            # print(f"[ERROR] Raw JSON: {activity_config.usage_scenario_config}")
            response = jsonify({'message': f'{activity_type_formatted}: Invalid activity configuration'})
            response.status_code = 400
            return False, response

    # 统一校验最小下注金额
    if hasattr(activity_config, 'min_bet_amount_required') and activity_config.min_bet_amount_required:
        if bet_amount < float(activity_config.min_bet_amount_required):
            response = jsonify({
                'message': f'{activity_type_formatted}: Minimum bet amount is {activity_config.min_bet_amount_required}'
            })
            response.status_code = 400
            return False, response

    return True, None


def validate_and_process_coupon(coupon_id, user_id, total_amount):
    """
    验证并处理优惠券逻辑（single和mix共用）

    Args:
        coupon_id: 优惠券ID
        user_id: 用户ID
        total_amount: 下注总金额

    Returns:
        tuple: (member_coupon对象, coupon_discount金额) 或 (None, error_response)
    """
    from app_server.model.MAppMemberCouponModel import MAppMemberCoupon
    from app_server.model.MAppCouponModel import MAppCoupon

    if not coupon_id:
        return None, 0

    # 1. 查询会员优惠券记录
    member_coupon = MAppMemberCoupon.query.filter_by(
        id=coupon_id,
        mb_id=user_id,
        del_flag=0
    ).with_for_update().first()

    if not member_coupon:
        db.session.rollback()
        response = jsonify({'message': "Coupon not found or does not belong to you"})
        response.status_code = 400
        return None, response

    # 2. 检查优惠券是否已使用
    if member_coupon.status != 'Unused':
        db.session.rollback()
        response = jsonify({'message': "Coupon has already been used or expired"})
        response.status_code = 400
        return None, response

    # 3. 检查优惠券是否过期
    if member_coupon.expire_time and member_coupon.expire_time < datetime.datetime.now():
        db.session.rollback()
        response = jsonify({'message': "Coupon has expired"})
        response.status_code = 400
        return None, response

    # 4. 查询优惠券主表信息
    coupon_master = MAppCoupon.query.filter_by(
        id=member_coupon.p_id,
        del_flag=0
    ).first()

    if not coupon_master:
        db.session.rollback()
        response = jsonify({'message': "Coupon configuration not found"})
        response.status_code = 400
        return None, response

    # 5. 检查是否达到最低投注要求
    if coupon_master.min_bet_amount_required and total_amount < float(coupon_master.min_bet_amount_required):
        db.session.rollback()
        response = jsonify({
            'message': f"Minimum bet amount required: {coupon_master.min_bet_amount_required}"
        })
        response.status_code = 400
        return None, response

    # 6. 检查总使用次数限制（p_lmu_j_pd）
    if coupon_master.p_lmu_j_pd and coupon_master.p_lmu_j_pd > 0:
        total_used_count = MAppMemberCoupon.query.filter(
            MAppMemberCoupon.mb_id == user_id,
            MAppMemberCoupon.p_id == coupon_master.id,
            MAppMemberCoupon.status == 'Used',
            MAppMemberCoupon.del_flag == 0
        ).count()

        if total_used_count >= coupon_master.p_lmu_j_pd:
            db.session.rollback()
            response = jsonify({
                'message': f"Coupon usage limit reached: {coupon_master.p_lmu_j_pd}"
            })
            response.status_code = 400
            return None, response

    # 7. 计算优惠金额
    coupon_discount = 0
    if member_coupon.money and float(member_coupon.money) > 0:
        coupon_discount = float(member_coupon.money)
        # 优惠金额不能超过下注金额
        if coupon_discount > total_amount:
            coupon_discount = total_amount

    return member_coupon, coupon_discount


def check_balance_and_deduct(user, total_amount, coupon_discount, use_promotion_wallet):
    """
    检查余额并计算实际扣除金额（single和mix共用）

    Args:
        user: 用户对象
        total_amount: 下注总金额
        coupon_discount: 优惠券折扣金额
        use_promotion_wallet: 是否使用优惠钱包

    Returns:
        tuple: (actual_deduction, pay_wallet_type, before_amount, after_amount) 或 (None, error_response, None, None)
    """
    # 计算实际需要扣除的金额
    actual_deduction = total_amount - coupon_discount

    # 检查余额是否足够
    if use_promotion_wallet:
        # 使用优惠钱包
        promotion_balance = float(user.money_promotion) if user.money_promotion else 0
        if promotion_balance < actual_deduction:
            response = jsonify({'message': "Sorry, your promotion wallet balance is not enough for this bet"})
            response.status_code = 400
            return None, response, None, None

        before_amount = promotion_balance
        user.money_promotion = before_amount - actual_deduction
        after_amount = before_amount - actual_deduction
        pay_wallet_type = PayWallet.Promotion
    else:
        # 使用主钱包
        current_money = float(user.money)
        current_withdrawable = float(user.money_promotion_withdrawable) if user.money_promotion_withdrawable else 0

        if current_money < actual_deduction:
            response = jsonify({'message': "Sorry, your current balance is not enough for this bet"})
            response.status_code = 400
            return None, response, None, None

        before_amount = current_money
        after_amount = current_money - actual_deduction
        user.money = after_amount

        # 扣款逻辑：优先扣除不可提现部分，如果剩余余额小于可提现部分则调整
        if after_amount < current_withdrawable:
            user.money_promotion_withdrawable = after_amount

        pay_wallet_type = PayWallet.Money

    return actual_deduction, pay_wallet_type, before_amount, after_amount


def mark_coupon_as_used(member_coupon, bet_order_id):
    """
    标记优惠券为已使用（single和mix共用）

    Args:
        member_coupon: 会员优惠券对象
        bet_order_id: 订单ID
    """
    if member_coupon:
        member_coupon.status = 'Used'
        member_coupon.use_time = datetime.datetime.now()
        member_coupon.link_id = bet_order_id
        db.session.add(member_coupon)


def build_remark(coupon_discount):
    """
    构建交易类型描述（single和mix共用）

    Args:
        use_promotion_wallet: 是否使用优惠钱包
        coupon_discount: 优惠券折扣金额

    Returns:
        str: 交易类型描述
    """
    type_sub_parts = []
    if coupon_discount > 0:
        type_sub_parts.append(f"coupon_{coupon_discount}")

    return ",".join(type_sub_parts)


def get_user_active_promotion_id(user_id):
    """
    获取用户当前活动优惠券的ID（优惠券模板ID）
    ✅ 专门用于保存到 m_app_bet_order.pro_id 字段

    ⚠️ 重要逻辑：
    - 只查询 is_requirement_met=0 的活动（还需要累计流水的活动）
    - 如果存在多个Active活动，说明邀请活动已达标(is_requirement_met=1)，
      此时应返回未达标的优惠券/促销活动ID

    Args:
        user_id: 用户ID

    Returns:
        str: 优惠券模板ID（p_id），如果没有活动优惠券则返回None
    """
    try:
        from app_server.model.AppPlayerActivityRecordModel import AppPlayerActivityRecord
        from app_server.model.MAppMemberCouponModel import MAppMemberCoupon

        # 查询状态为Active且未达标的活动记录（需要累计流水）
        active_record = db.session.query(AppPlayerActivityRecord).filter(
            AppPlayerActivityRecord.mb_id == user_id,
            AppPlayerActivityRecord.status == 'Active',
            AppPlayerActivityRecord.is_requirement_met == 0,  # 只查询未达标的活动
            AppPlayerActivityRecord.del_flag == 0
        ).first()

        if not active_record:
            return None

        if active_record.activity_type == 'COUPON':
            member_coupon = MAppMemberCoupon.query.filter_by(
                p_id=active_record.activity_id,
                mb_id=user_id,
                del_flag=0
            ).first()

            if member_coupon:
                return member_coupon.p_id
            return None

        elif active_record.activity_type == 'INVITATION':
            member_invitation = MAppInvitationReward.query.filter_by(
                activity_id=active_record.activity_id,
                mb_id=user_id,
                del_flag=0
            ).first()

            if member_invitation:
                return member_invitation.activity_id
            return None

        elif active_record.activity_type == 'PROMOTION':
            return active_record.activity_id

        return None

    except Exception as e:
        logger.error(f"获取活动优惠券ID失败 - 用户ID: {user_id}, 错误: {e}", exc_info=True)
        return None


def get_user_active_activity_record_id(user_id):
    """
    获取用户当前活动记录ID
    ✅ 专门用于保存到 m_app_bet_order.activity_record_id 字段

    ⚠️ 重要逻辑：
    - 只查询 is_requirement_met=0 的活动（还需要累计流水的活动）
    - 返回活动记录ID，用于精确关联订单到具体活动记录

    Args:
        user_id: 用户ID

    Returns:
        tuple: (activity_id, activity_record_id) 或 (None, None)
               activity_id: 活动模板ID（优惠券ID/PromotionID等）
               activity_record_id: 活动记录ID（m_app_player_activity_record.id）
    """
    try:
        from app_server.model.AppPlayerActivityRecordModel import AppPlayerActivityRecord
        from app_server.model.MAppMemberCouponModel import MAppMemberCoupon

        # 查询状态为Active且未达标的活动记录（需要累计流水）
        active_record = db.session.query(AppPlayerActivityRecord).filter(
            AppPlayerActivityRecord.mb_id == user_id,
            AppPlayerActivityRecord.status == 'Active',
            AppPlayerActivityRecord.is_requirement_met == 0,  # 只查询未达标的活动
            AppPlayerActivityRecord.del_flag == 0
        ).first()

        if not active_record:
            return None, None

        if active_record.activity_type == 'COUPON':
            member_coupon = MAppMemberCoupon.query.filter_by(
                p_id=active_record.activity_id,
                mb_id=user_id,
                del_flag=0
            ).first()

            if member_coupon:
                return member_coupon.p_id, active_record.id
            return None, None

        elif active_record.activity_type == 'INVITATION':
            member_invitation = MAppInvitationReward.query.filter_by(
                activity_id=active_record.activity_id,
                mb_id=user_id,
                del_flag=0
            ).first()

            if member_invitation:
                return member_invitation.activity_id, active_record.id
            return None, None

        elif active_record.activity_type == 'PROMOTION':
            return active_record.activity_id, active_record.id

        return None, None

    except Exception as e:
        logger.error(f"获取活动记录ID失败 - 用户ID: {user_id}, 错误: {e}", exc_info=True)
        return None, None


def update_activity_turnover(user_id, bet_amount, net_win_amount):
    """
    ❌ 已废弃：此方法不再使用
    流水和净赢校验改为直接从 m_app_bet_order 表统计

    @deprecated 请使用 get_user_active_promotion_id(user_id) 获取优惠券ID
    """
    logger.warning("update_activity_turnover 方法已废弃，请使用 get_user_active_promotion_id()")
    return None


@order.route('/check_odds', methods=['POST'])
@auth.login_required
def check_odds():
    """
        @@@
        #### Args:
                attrs: {attr_id:{"bet_type": 1, "DRAW_ODDS": 2.3, ...}, ...}
        #### Returns::
                {'code': 200, 'message': "check success!", items: {attr_id:odds, ...}}
                {'code': 500, 'message': "System or Technical Error"}
    """
    args = request.get_json()
    attrs = args.get('attrs')
    logger.info(f"检查赔率 - 属性: {attrs}")
    try:
        all_attr = MatchAttr.query.filter(MatchAttr.MATCH_ATTR_ID.in_(attrs)).all()
        change_list = []
        for attr in all_attr:
            remote_attr = attrs[attr.MATCH_ATTR_ID]
            if attr.DRAW_BUNKO != remote_attr['DRAW_BUNKO'] or attr.DRAW_ODDS != remote_attr[
                'DRAW_ODDS'] or attr.LOSE_BALL_NUM != remote_attr['LOSE_BALL_NUM']:
                change_list.append(attr)

        return jsonify({'message': "check success!", 'items': [u.to_dict() for u in change_list]})

    except Exception as e:
        logger.error(f"检查赔率失败: {e}", exc_info=True)
        response = jsonify({'message': "odds_change"})
        response.status_code = 400
        return response


@order.route('/single_bet', methods=['POST'])
@auth.login_required
def single_bet():
    """ single_bet API Endpoint
        ---
        tags:
          - order
        parameters:
          - in: body
            name: body
            required: true
            description: single_bet to add
            schema:
              type: object
              required:
                - bets
                - match_id
              properties:
                bets:
                  type: object
                  properties:
                    amount:
                        type: integer
                        description: the amount of the bet
                        example: 100
                    betType:
                        type: integer
                        description: the bet type of the bet
                        example: 1 # 1.host/over 2.guest/under 3.draw
                    attrType:
                        type: integer
                        description: the attr_type of the bet
                        example: 1 # 1.single hdp 2.single o/u 3.correct score 4.mix hdp 5.mix o/u 6.single even/odd 7.mix even/odd 8.digital 9.digital_3d 10.single win/lose 11. mix win/lose
                  description: the bets of the order
                match_id:
                  type: string
                  description: the match_id of the order
                  example: ""
                coupon_id:
                  type: string
                  description: the member coupon id if using coupon
                  example: ""
        responses:
          500:
            description: Bet failed, no order.
          500:
            description: Bet failed.
          500:
            description: Bet failed.
          500:
            description: Bet failed.
          200:
            description: bet success!
        """
    args = request.get_json()
    bets = args.get('bets')
    # coupon_id = args.get('coupon_id')  # 获取优惠券ID
    use_promotion_wallet = args.get('use_promotion_wallet', False)  # 是否使用优惠钱包

    getter_key = "order_bet_%s_%s" % (g.user.id, str(args))
    if not Redis.exists(getter_key):
        Redis.set(getter_key, 0, ex=2)
    else:
        response = jsonify({'message': "same bet request in very short time"})
        response.status_code = 429
        return response
    # 记录用户下注参数
    logger.info(f"用户single_bet - 用户ID: {g.user.id}, 下注参数: {args}")
    try:
        total_amount = 0

        user = g.user
        main_id = user.id
        del user
        from app_server.model.AppMemberModel import AppMember
        db.session.commit()
        user = AppMember.query.filter_by(id=main_id).with_for_update(of=AppMember).first()

        # 先行统计总下注额
        for bet in bets:
            total_amount += float(bet['amount'])

        # 如果使用优惠钱包，验证活动限制
        if use_promotion_wallet:
            success, error_response = validate_promotion_activity(user.id, total_amount, 'Single')
            if not success:
                db.session.rollback()
                return error_response

        # # 验证并处理优惠券（使用共用方法）
        # member_coupon, coupon_discount = validate_and_process_coupon(coupon_id, user.id, total_amount)
        # if isinstance(coupon_discount, tuple):  # 返回的是错误响应
        #     return coupon_discount
        member_coupon = None
        coupon_discount = 0

        # 检查余额并扣款（使用共用方法）
        result = check_balance_and_deduct(user, total_amount, coupon_discount, use_promotion_wallet)
        if result[0] is None:  # 返回的是错误响应
            return result[1]
        actual_deduction, pay_wallet_type, before_amount, after_amount = result
        # LRC 获取用户所属代理的下注配置（分1x2 hdp o/u）
        betting_config = AppSettingBet1x2Model.get_agent_config(user.aid)
        # 获取默认的下注配置（混合下注单场最大和订单数最大限制）
        betting_default_config = AppSettingBet1x2Model.get_agent_config()
        for bet in bets:
            order_type = bet['attrType']
            # 订单类型:1单笔胜负(让球)2单笔大小球3波胆4混合胜负5混合大小6单笔单双7混合单双8数字盘 9数字盘3d 10胜负平单笔 11胜负平混合
            min_max = betting_config.get_min_max_by_order_type(order_type)
            single_min = min_max['min_bet']
            single_max = min_max['max_bet']
            logger.info(f"下注限制检查 - 订单类型: {order_type}, 最小额: {single_min}, 最大额: {single_max}")
            if float(bet['amount']) < float(single_min):
                response = jsonify({'message': "single_min"})
                response.status_code = 400
                return response
            if float(bet['amount']) > float(single_max):
                response = jsonify({'message': "single_max"})
                response.status_code = 400
                return response
            match = Match.query.filter_by(MATCH_ID=bet['matchId']).one_or_none()
            if not match:
                db.session.rollback()
                response = jsonify({'message': "Bet failed: match not exist."})
                response.status_code = 400
                return response
            if match.CLOSING_STATE == "1":
                db.session.rollback()
                response = jsonify({'message': "Events already started or closed"})
                response.status_code = 400
                return response
            if match.CLOSING_TIME <= datetime.datetime.now():
                db.session.rollback()
                response = jsonify({'message': "Events already started or closed"})
                response.status_code = 400
                return response

            # attrs = MatchAttr.query.filter_by(MATCH_ID=bet['matchId']).all()
            # vip_attrs = VipMatchAttr.query.filter_by(MATCH_ID=bet['matchId']).all()
            # vip_attr_dict = {attr.MATCH_ATTR_TYPE: attr for attr in vip_attrs}
            # attr_dict = {attr.MATCH_ATTR_TYPE: attr for attr in attrs}
            #
            # attr = None
            # if order_type in attr_dict:
            #     attr = attr_dict[order_type]
            # if user.IS_VIP and order_type in vip_attr_dict:
            #     attr = vip_attr_dict[order_type]
            # 获取玩法并设置下注
            match_attr = MatchAttr.get_match_attr(match_id=bet['matchId'], attr_type=order_type,
                                                  bet_type=bet['betType'])
            if not match_attr:
                db.session.rollback()
                response = jsonify({'message': "Invalid Bet Type"})
                response.status_code = 400
                return response

            logger.info(f"匹配下注 - 比赛属性: {match_attr.to_dict()}")
            #   总限额
            single_order_total_limit = betting_default_config.sb_sg_max_per_match  # 单场比赛下注总限额
            match_total_unsettled = Order.query.filter(
                and_(Order.USER_ID == user.id, Order.ORDER_TYPE == order_type, Order.STATUS == "1",
                     Order.MATCH_ID == bet['matchId'])).with_entities(func.sum(Order.BET_MONEY)).scalar() or 0
            logger.info(
                f"单场限额检查 - 订单类型: {order_type}, 已下注: {match_total_unsettled}, 单场限额: {single_order_total_limit}")
            if float(match_total_unsettled) + total_amount > int(single_order_total_limit):
                db.session.rollback()
                response = jsonify({'message': "Bet failed: this match has reached the order limit."})
                response.status_code = 400
                return response

            order_id = "%s-%s" % (user.username, round(time.time() * 1000))
            new_order = Order(ID=str(uuid.uuid4()).replace("-", ""), ORDER_ID=order_id, USER_ID=user.id,
                              USER_NAME=user.username,
                              MATCH_ID=bet['matchId'], ORDER_TYPE=order_type, BET_TYPE=bet['betType'],
                              ORDER_DESC="%s || %s" % (match.HOST_TEAM, match.GUEST_TEAM),
                              BET_MONEY=bet['amount'], order_type_desc="暂无", STATUS="1", IS_MIX="0", IS_WIN="2",
                              BONUS="0", LOSE_TEAM=match_attr.LOSE_TEAM,
                              BET_ODDS=match_attr.ODDS, LEAGUE=match.LEAGUE,
                              DRAW_BUNKO=0 if match_attr.DRAW_BUNKO == '' else match_attr.DRAW_BUNKO,
                              DRAW_ODDS=match_attr.DRAW_ODDS,
                              LOSE_BALL_NUM=0 if match_attr.LOSE_BALL_NUM == '' else match_attr.LOSE_BALL_NUM,
                              MATCH_TIME=match.MATCH_MD_TIME, IP=int(ipaddress.IPv4Address(request.remote_addr)))
            # 设置下注信息
            match_attr.set_bet_info(new_order)
            # 设置代理ID
            if user.aid:
                new_order.AGENT_CODE = user.aid

            # 复制订单到主订单表
            new_order.bet_status = BetStatus.Pending
            new_order.pay_wallet = pay_wallet_type
            bet_order = AppBetOrder.create_from_order(new_order, match)

            # ✅ 如果使用促销钱包，获取并保存优惠券ID到 pro_id 和活动记录ID到 activity_record_id
            if use_promotion_wallet:
                pro_id, activity_record_id = get_user_active_activity_record_id(user.id)
                if pro_id:
                    bet_order.in_promotion = 1
                    bet_order.pro_id = pro_id
                    bet_order.activity_record_id = activity_record_id
                    logger.info(f"使用优惠钱包下注 - 保存优惠券ID: {pro_id}, 活动记录ID: {activity_record_id}")

            db.session.add(bet_order)
            new_order.main_order_id = bet_order.id

            db.session.add(new_order)

            db.session.commit()
            logger.info(
                f"单笔下注提交成功 - 用户ID: {user.id}, 订单ID: {order_id}, 比赛ID: {bet['matchId']}, 金额: {bet['amount']}, 订单类型: {order_type}, 下注ID: {bet_order.id}")

            # 构建交易类型描述（使用共用方法）
            # remark = build_remark(coupon_discount)

            app_opt.send({
                "user_account": user.id,
                "user_name": user.username,
                "type": TransactionType.Order,
                "type_sub": "Football",
                "before_amount": float(before_amount),
                "after_amount": float(after_amount),
                "amount": f"-{float(actual_deduction)}",
                "source_id": order_id,
                "bet_id": order_id,
                "aid": g.user.aid,
                "match_id": bet['matchId'],
                "pro_id": bet_order.pro_id,
                "pay_wallet": "Promotion" if use_promotion_wallet else "Money",
                # "remark": remark,
            })

            # 记录单笔下注行为日志
            try:
                from app_server.service.AppBehaviorLogService import AppBehaviorLogService
                from app_server import app

                AppBehaviorLogService.add_behavior_log(
                    request=request,
                    event_type='bet',
                    member_id=user.id,
                    event_params={
                        'bet_type': 'Single',
                        'order_id': order_id,
                        'bet_order_id': bet_order.id,
                        'match_id': bet['matchId'],
                        'amount': float(bet['amount']),
                        'order_type': order_type,
                        'odds': float(match_attr.ODDS) if match_attr.ODDS else 0,
                        'pay_wallet': 'Promotion' if use_promotion_wallet else 'Money',
                        'pro_id': bet_order.pro_id
                    },
                    remark='User single bet placed'
                )
            except Exception as e:
                app.logger.warning(f"Failed to add single bet behavior log: {str(e)}")

        # 创建佣金记录
        try:
            from app_server.service.CommissionRecordService import CommissionRecordService
            CommissionRecordService.create_commission_on_bet(
                bet_order=bet_order.id,
                member_id=user.id,
                bet_amount=float(bet['amount']),
                tenant_id=user.tenant_id
            )
        except Exception as e:
            app.logger.error(f"创建佣金记录失败: {str(e)}")
            # 不影响下注流程

        # P3: 发送站内通知给会员 — 单笔下注成功
        try:
            MemberMessageService.send_order_placed(
                member_id=user.id,
                order_id=order_id,
                amount=float(bet['amount']),
                aid=user.aid
            )
        except Exception as e:
            app.logger.warning(f"Failed to send single bet notification to member: {str(e)}")

        return jsonify({'message': "Bet success!"})

    except Exception as e:
        logger.error(f"单笔下注失败 - 用户ID: {g.user.id}, 错误: {e}", exc_info=True)
        db.session.rollback()
        response = jsonify({'message': "System or Technical Error"})
        response.status_code = 400
        return response


@order.route('/mix_bet', methods=['POST'])
@auth.login_required
def mix_bet():
    """ mix_bet API Endpoint
        ---
        tags:
          - order
        parameters:
          - in: body
            name: body
            required: true
            description: single_bet to add
            schema:
              type: object
              required:
                - bets
                - match_id
              properties:
                bets:
                  type: object
                  properties:
                    amount:
                        type: integer
                        description: the amount of the bet
                        example: 100
                    betType:
                        type: integer
                        description: the bet type of the bet
                        example: 1 # 1.host/over 2.guest/under 3.draw
                    attrType:
                        type: integer
                        description: the attr_type of the bet
                        example: 1 # 1.single hdp 2.single o/u 3.correct score 4.mix hdp 5.mix o/u 6.single even/odd 7.mix even/odd 8.digital 9.digital_3d 10.single win/lose 11. mix win/lose
                  description: the bets of the order
                match_id:
                  type: string
                  description: the match_id of the order
                  example: ""
        responses:
          500:
            description: Bet failed, no order.
          500:
            description: Bet failed.
          500:
            description: Bet failed.
          500:
            description: Bet failed.
          200:
            description: bet success!
        """
    args = request.get_json()
    bets = args.get('bets')
    # coupon_id = args.get('coupon_id')  # 获取优惠券ID
    use_promotion_wallet = args.get('use_promotion_wallet', False)  # 是否使用优惠钱包
    # getter_key = "order_bet_%s_%s" % (g.user.id, str(args))

    getter_key = "order_bet_%s" % (g.user.id)
    success = Redis.setnx(getter_key, 1)  # SETNX命令
    if not success:
        response = jsonify({'message': "same bet request in very short time"})
        response.status_code = 429
        return response

    # 设置键的过期时间
    Redis.expire(getter_key, 2)

    # if not Redis.exists(getter_key):
    #     Redis.set(getter_key, 0, ex=2)
    # else:
    #     return jsonify({'code': 50003, "message": "same bet request in very short time"})

    order_id = int(round(time.time() * 1000))
    # 直接给出总金额
    total_amount = float(args.get('totalAmount'))
    logger.info(f"用户mix_bet - 用户ID: {g.user.id}, 订单ID: {order_id}, 下注数: {len(bets)}, 总金额: {total_amount}")

    try:
        user = g.user
        # LRC 获取用户所属代理的下注配置（分1x2 hdp o/u）
        betting_config = AppSettingBet1x2Model.get_agent_config(user.aid)
        mix_min = betting_config.sb_mix_min_bet
        mix_max = betting_config.sb_mix_max_bet
        min_bet_count = betting_config.sb_mix_min_matches_amt
        max_bet_count = betting_config.sb_mix_max_matches_amt
        order_id = "%s-%s" % (g.user.username, round(time.time() * 1000))
        # 获取默认的下注配置（混合下注单场最大和订单数最大限制）
        betting_default_config = AppSettingBet1x2Model.get_agent_config()
        main_id = user.id
        del user
        from app_server.model.AppMemberModel import AppMember
        db.session.commit()
        user = AppMember.query.filter_by(id=main_id).with_for_update(of=AppMember).first()

        # 如果使用优惠钱包，验证活动限制
        if use_promotion_wallet:
            success, error_response = validate_promotion_activity(user.id, total_amount, 'Mixparlay')
            if not success:
                db.session.rollback()
                return error_response

        # # 验证并处理优惠券（使用共用方法）
        # member_coupon, coupon_discount = validate_and_process_coupon(coupon_id, user.id, total_amount)
        # if isinstance(coupon_discount, tuple):  # 返回的是错误响应
        #     return coupon_discount
        member_coupon = None
        coupon_discount = 0

        if total_amount < float(mix_min):
            response = jsonify({'message': "mix_min"
                                })
            response.status_code = 400
            return response
        if total_amount > float(mix_max):
            response = jsonify({'message': "mix_max"
                                })
            response.status_code = 400
            return response
        # match_ids = {bet['matchId'] for bet in bets}

        # 单场比赛混合下注判断
        # mix_orders = Order.query.with_entities(Order., Order.ORDER_ID).filter(Order.IS_MIX == "1", Order.STATUS == "1", Order.MATCH_ID.in_(match_ids), Order.USER_ID == user.id)

        match_to_orders = {}
        new_orders = []

        if len(bets) < int(min_bet_count):
            response = jsonify({
                'message': "at_least_2_game",
                'limit': min_bet_count,
            })
            response.status_code = 400
            return response
        if len(bets) > int(max_bet_count):
            response = jsonify({
                'message': "at_most_12_game",
                'limit': max_bet_count,
            })
            response.status_code = 400
            return response

        if len(set([bet['matchId'] for bet in bets])) < len(bets):
            response = jsonify({'message': "Duplicate Bet detected"})
            response.status_code = 400
            return response

        mix_type_dict = {}

        for bet in bets:
            match_id = bet['matchId']
            order_type = bet['attrType']

            already_bet = mix_type_dict.get(match_id)
            if not already_bet:
                mix_type_dict[match_id] = already_bet = set()

            if order_type in already_bet:
                logger.warning(
                    f"检测到非法下注 - 用户ID: {g.user.id}, 时间: {datetime.datetime.now()}, 参数: {args}, IP: {request.remote_addr}")
                response = jsonify({'message': "Bet failed: bet data illegal."})
                response.status_code = 400
                return response

            mix_type_dict[match_id].add(order_type)

            match = Match.query.filter_by(MATCH_ID=bet['matchId']).one_or_none()
            if not match:
                db.session.rollback()
                response = jsonify({'message': "Bet failed: match not exist."})
                response.status_code = 400
                return response
            if match.CLOSING_STATE == "1":
                db.session.rollback()
                response = jsonify({'message': "Events already started or closed"})
                response.status_code = 400
                return response
            if match.CLOSING_TIME <= datetime.datetime.now():
                db.session.rollback()
                response = jsonify({'message': "Events already started or closed"})
                response.status_code = 400
                return response

            # 混合单31限制
            # if user.HIGHER_LIMIT:
            #     mix_total_match_limit = MDict.query.filter_by(MDICT_ID="33").one()
            # else:
            #     mix_total_match_limit = MDict.query.filter_by(MDICT_ID="31").one()
            mix_total_match_limit = betting_default_config.mix_total_match_limit

            link_orders = Order.query.filter(Order.MATCH_ID == bet['matchId'], Order.USER_ID == user.id,
                                             Order.STATUS == 1, Order.IS_MIX == "1").group_by(Order.ORDER_ID).all()
            match_already_bet = 0
            for link_order in link_orders:
                match_already_bet += int(link_order.BET_MONEY)

            if match_already_bet + total_amount > float(mix_total_match_limit):
                response = jsonify({'message': "Bet failed: this match has reached the order limit."})
                response.status_code = 400
                return response

            attrs = MatchAttr.query.filter_by(MATCH_ID=bet['matchId']).all()
            vip_attrs = VipMatchAttr.query.filter_by(MATCH_ID=bet['matchId']).all()
            vip_attr_dict = {attr.MATCH_ATTR_TYPE: attr for attr in vip_attrs}
            attr_dict = {attr.MATCH_ATTR_TYPE: attr for attr in attrs}

            attr = None
            if order_type in attr_dict:
                attr = attr_dict[order_type]
            # if user.IS_VIP and order_type in vip_attr_dict:
            #     attr = vip_attr_dict[order_type]

            if not attr:
                db.session.rollback()
                response = jsonify({'message': "Invalid Bet Type"})
                response.status_code = 400
                return response

            new_order = Order(ID=str(uuid.uuid4()).replace("-", ""), ORDER_ID=order_id, USER_ID=user.id,
                              USER_NAME=user.username, BET_TYPE=bet['betType'],
                              MATCH_ID=bet['matchId'], ORDER_TYPE=order_type,
                              ORDER_DESC="%s || %s" % (match.HOST_TEAM, match.GUEST_TEAM),
                              BET_MONEY=total_amount, order_type_desc="%s串1" % len(bets), STATUS="1", IS_MIX="1",
                              IS_WIN="2", LOSE_TEAM=attr.LOSE_TEAM,
                              BONUS="0", MATCH_TIME=match.MATCH_MD_TIME, LEAGUE=match.LEAGUE,
                              BET_ODDS=attr.ODDS, DRAW_BUNKO=attr.DRAW_BUNKO, DRAW_ODDS=attr.DRAW_ODDS,
                              LOSE_BALL_NUM=attr.LOSE_BALL_NUM, IP=int(ipaddress.IPv4Address(request.remote_addr)))
            logger.info(f"混合下注订单 - 订单类型: {order_type}, 下注类型: {bet['betType']}")
            new_order.BET_TYPE = bet['betType']
            if user.aid:
                new_order.AGENT_CODE = user.aid
            if order_type == "5":
                new_order.BALL_TYPE = bet['betType']
            if g.user.aid:
                new_order.AGENT_CODE = g.user.aid

            # 单双赔率另外赋值
            if order_type == '7':
                new_order.BET_ODDS = attr.ODDS if bet['betType'] == '1' else attr.ODDS_GUEST

            new_orders.append(new_order)
            match_to_orders[bet['matchId']] = new_order

        # 检查余额并扣款（使用共用方法）
        result = check_balance_and_deduct(user, total_amount, coupon_discount, use_promotion_wallet)
        if result[0] is None:  # 返回的是错误响应
            return result[1]
        actual_deduction, pay_wallet_type, before_amount, after_amount = result

        # 统计同类混合单的注额 进行限制
        # if user.HIGHER_LIMIT:
        #     mix_order_total_limit = MDict.query.filter_by(MDICT_ID="32").one()
        # else:
        #     mix_order_total_limit = MDict.query.filter_by(MDICT_ID="30").one()

        mix_order_total_limit = betting_default_config.mix_order_total_limit
        mix_already = Order.query.with_entities(func.count(Order.ID), Order.ORDER_ID).filter(
            Order.USER_ID == user.id, Order.STATUS == 1, Order.IS_MIX == "1").group_by(Order.ORDER_ID).all()
        same_order_ids = []
        for length, o_id in mix_already:
            if length != len(bets):
                continue
            same_order_ids.append(o_id)

        logger.info(f"相同订单ID列表: {same_order_ids}")
        count_amount = 0
        for o_id in same_order_ids:
            orders = Order.query.filter_by(ORDER_ID=o_id).all()
            is_same = True
            for o in orders:
                if o.MATCH_ID not in match_to_orders:
                    is_same = False
                    break
                s = match_to_orders[o.MATCH_ID]

                is_same = compare(s.BET_TYPE, o.BET_TYPE) and compare(s.ORDER_TYPE, o.ORDER_TYPE) and compare(
                    s.BALL_TYPE, o.BALL_TYPE)
                if not is_same:
                    break
            logger.info(f"订单比较结果 - 订单ID: {o_id}, 是否相同: {is_same}")
            if is_same:
                count_amount += float(orders[0].BET_MONEY)

        logger.info(f"相同订单统计 - 订单ID: {order_id}, 已下注总额: {count_amount}, 相同订单列表: {same_order_ids}")

        if count_amount + total_amount > float(mix_order_total_limit):
            logger.warning(f"达到混合下注限额 - 当前总额: {count_amount + total_amount}, 限额: {mix_order_total_limit}")
            db.session.rollback()
            response = jsonify({'message': "mix_order_total"
                                })
            response.status_code = 400
            return response

        # 复制订单到主订单表
        new_order = new_orders[0]
        new_order.bet_status = BetStatus.Pending
        new_order.pay_wallet = pay_wallet_type
        bet_order = AppBetOrder.create_from_order(new_order, Match(), order_count=len(bets), )

        # ✅ 如果使用促销钱包，获取并保存优惠券ID到 pro_id 和活动记录ID到 activity_record_id
        pro_id = None
        if use_promotion_wallet:
            pro_id, activity_record_id = get_user_active_activity_record_id(user.id)
            if pro_id:
                bet_order.in_promotion = 1
                bet_order.pro_id = pro_id  # ✅ 保存优惠券模板ID
                bet_order.activity_record_id = activity_record_id  # ✅ 保存活动记录ID
                logger.info(f"使用优惠钱包混合下注 - 保存优惠券ID: {pro_id}, 活动记录ID: {activity_record_id}")

        db.session.add(bet_order)

        for o in new_orders:
            o.bet_status = bet_order.bet_status
            o.pay_wallet = bet_order.pay_wallet
            o.main_order_id = bet_order.id
            db.session.add(o)

        db.session.commit()
        logger.info(
            f"混合下注提交成功 - 用户ID: {user.id}, 订单ID: {order_id}, 比赛数: {len(bets)}, 总金额: {total_amount}, 下注ID: {bet_order.id}")

        # 构建交易类型描述（使用共用方法）
        # remark = build_remark(coupon_discount)

        app_opt.send({
            "user_account": user.id,
            "user_name": user.username,
            "type": TransactionType.Order,
            "type_sub": "Football",
            "before_amount": float(before_amount),
            "after_amount": float(after_amount),
            "amount": f"-{float(actual_deduction)}",
            "source_id": order_id,
            "aid": g.user.aid,
            "bet_id": order_id,
            "pro_id": bet_order.pro_id,
            "pay_wallet": "Promotion" if use_promotion_wallet else "Money",
            # "remark": remark,
        })

        # 记录混合下注行为日志
        try:
            from app_server.service.AppBehaviorLogService import AppBehaviorLogService
            from app_server import app
            match_ids = [bet['matchId'] for bet in bets]

            AppBehaviorLogService.add_behavior_log(
                request=request,
                event_type='bet',
                member_id=user.id,
                event_params={
                    'bet_type': 'Mixparlay',
                    'order_id': order_id,
                    'bet_order_id': bet_order.id,
                    'match_ids': match_ids,
                    'match_count': len(bets),
                    'total_amount': float(total_amount),
                    'pay_wallet': 'Promotion' if use_promotion_wallet else 'Money',
                    'pro_id': bet_order.pro_id
                },
                remark=f'User mix bet placed ({len(bets)} matches)'
            )
        except Exception as e:
            app.logger.warning(f"Failed to add mix bet behavior log: {str(e)}")

        # 创建佣金记录
        try:
            from app_server.service.CommissionRecordService import CommissionRecordService
            CommissionRecordService.create_commission_on_bet(
                bet_order=bet_order.id,
                member_id=user.id,
                bet_amount=float(total_amount),
                tenant_id=user.tenant_id
            )
        except Exception as e:
            app.logger.error(f"创建佣金记录失败: {str(e)}")
            # 不影响下注流程

        # P3: 发送站内通知给会员 — 混合下注成功
        try:
            MemberMessageService.send_order_placed(
                member_id=user.id,
                order_id=order_id,
                amount=float(total_amount),
                aid=user.aid
            )
        except Exception as e:
            app.logger.warning(f"Failed to send mix bet notification to member: {str(e)}")

        return jsonify({'message': "bet success!"})
    except Exception as e:
        logger.error(f"混合下注失败 - 用户ID: {g.user.id}, 错误: {e}", exc_info=True)
        response = jsonify({'message': "System or Technical Error"})
        response.status_code = 400
        return response


def compare(a, b):
    if a and b:
        return str(a) == str(b)
    return a == b


# 获取订单列表
@order.route('/get', methods=['GET'])
@auth.login_required
def get_order_list():
    """ get_order_list API Endpoint
        ---
        tags:
          - order
        parameters:
           - name: current_page
             in: query
             type: string
             required: true
             description: current_page of order_history
           - name: limit
             in: query
             type: integer
             description: limit of order_history
           - name: order_id
             in: query
             type: string
             description: order_id of order_history
           - name: key_word
             in: query
             type: string
             description: key_word of order_history
           - name: start_time
             in: query
             type: string
             description: start_time of order_history
           - name: end_time
             in: query
             type: string
             description: end_time of order_history
           - name: order_type
             in: query
             type: string
             description: status of order_history
             example: 1 # 1.single hdp 2.single o/u 3.correct score 4.mix hdp 5.mix o/u 6.single even/odd 7.mix even/odd 8.digital 9.digital_3d 10.single win/lose 11. mix win/lose
           - name: order_types
             in: query
             type: string
             description: order_types of order_history
             example: [1, 2, 3]
           - name: bet_type
             in: query
             type: string
             description: bet_type of order_history
             example: 1 # 1.host/over 2.guest/under 3.draw
           - name: status
             in: query
             type: string
             description: status of order_history   1 valid   0 invalid
           - name: is_mix
             in: query
             type: string
             description: is_mix of order_history 0 not mix   1 mix
           - name: is_win
             in: query
             type: string
             description: is_win of order_history  0 lose  1 win
        responses:
          200:
            description: { 'items': [...], 'total': 100, 'total_bet': 10000, 'total_bonus': 5000 }
        """

    current_page = request.args.get('page', type=int, default=1)
    limit = request.args.get('limit', type=int, default=20)
    order_id = request.args.get('order_id')

    match_id = request.args.get('match_id')
    is_detail = request.args.get('is_detail')

    key_word = request.args.get('key_word')
    start_time = request.args.get('start_time')
    end_time = request.args.get('end_time')

    order_type = request.args.get('order_type')
    order_types = request.args.get('order_types')
    bet_type = request.args.get('bet_type')
    status = request.args.get('status')
    pay_wallet = request.args.get('pay_wallet')
    bet_status = request.args.get('bet_status')

    if is_detail:
        detail_order_list = Order.query.filter(Order.USER_ID == g.user.id, Order.ORDER_ID == order_id,
                                               Order.STATUS == "1")
        detail_order_list = detail_order_list.all()
        detail_result = []
        for order in detail_order_list:
            detail_result.append(order.to_dict())

        return jsonify({
            'items': detail_result,
            'total': len(detail_result)
        })

    order_list = AppBetOrder.query.filter(AppBetOrder.mb_id == g.user.id, AppBetOrder.del_flag == 0,
                                          AppBetOrder.game_status == 'Pending')

    # if g.user.AGENT_CODE:
    #     users_under = AppUser.query.filter_by(aid=g.user.AGENT_CODE).all()
    #     users_under = set([u.USER_ID for u in users_under])
    #     order_list = order_list.filter(AppBetOrder.mb_id.in_(users_under))

    if order_id:
        order_list = order_list.filter(AppBetOrder.bet_group == order_id)
    if key_word:
        order_list = order_list.filter(
            or_(AppBetOrder.bet_group.like('%{}%'.format(key_word)), AppBetOrder.mb_id.like('%{}%'.format(key_word)),
                AppBetOrder.mb_username.like('%{}%'.format(key_word)),
                AppBetOrder.game_id.like('%{}%'.format(key_word)),
                AppBetOrder.remarks.like('%{}%'.format(key_word))))

    if match_id:
        order_list = order_list.filter(AppBetOrder.game_id == match_id)
    if order_type:
        order_list = order_list.filter(AppBetOrder.bet_type_sub.like('%{}:%'.format(order_type)))
    if order_types:
        bet_type_patterns = ['%{}:%'.format(ot) for ot in order_types.split(",")]
        order_list = order_list.filter(or_(*[AppBetOrder.bet_type_sub.like(pattern) for pattern in bet_type_patterns]))
    if status and int(status) > 0:
        order_list = order_list.filter(
            AppBetOrder.bet_status == BetStatus.Pending if status == "1" else AppBetOrder.bet_status != BetStatus.Pending)
    if pay_wallet:
        order_list = order_list.filter(AppBetOrder.pay_wallet == pay_wallet)
    if bet_status:
        order_list = order_list.filter(AppBetOrder.bet_status == bet_status)
    if bet_type:
        order_list = order_list.filter(AppBetOrder.bet_type == bet_type)

    if start_time:
        # 将缅甸时间转换为中国时间（加上1.5小时）
        start_time = convert_myanmar_to_china_time(start_time, is_end_time=False)
        order_list = order_list.filter(AppBetOrder.create_time >= start_time)

    if end_time:
        # 将缅甸时间转换为中国时间（加上1.5小时）
        end_time = convert_myanmar_to_china_time(end_time, is_end_time=True)
        order_list = order_list.filter(AppBetOrder.create_time <= end_time)

    order_list = order_list.group_by(AppBetOrder.bet_group)
    order_list = order_list.offset((current_page - 1) * limit).limit(limit).all()
    result = []
    from app_server.model.MatchModel import Match
    for u in order_list:
        temp = u.to_dict()
        # 如果game_id存在，查找Match并加上MATCH_TIME
        if u.game_id:
            match = Match.query.filter_by(ID=u.game_id).first()
            if match:
                temp['MATCH_TIME'] = str(match.MATCH_TIME)
        result.append(temp)

    return jsonify({
        'items': result,
        'total': len(result)})


# 获取订单列表（读历史表）
@order.route('/get_history', methods=['GET'])
@auth.login_required
def get_history_list():
    """
                @@@
                #### Args:
                        current_page = request.args.get('page', type=int, default=1)
                        limit = request.args.get('limit', type=int, default=20)
                        date_filtered = request.args.get('date_filtered', type=int, default=0)
                        order_id = request.args.get('order_id')

                        key_word = request.args.get('key_word')
                        start_time = request.args.get('start_time')
                        end_time = request.args.get('end_time')

                        order_type = request.args.get('order_type')    订单类型:1胜负(让球)2大小球3波胆 无参表示全部
                        order_types = request.args.get('order_types')  订单类型多选
                        bet_type = request.args.get('bet_type')        下注类型:1主胜,2客胜   无参表示全部
                        status = request.args.get('status')            订单状态:0无效,1有效   无参表示全部
                        is_mix = request.args.get('is_mix')            是否混合过关:0否，1是  无参表示全部
                        is_win = request.args.get('is_win')            订单结果:0、输，1、赢,  2未出结果    无参表示全部
                #### Returns::
                        {
                                            'items': [u.to_dict() for u in order_list],
                            'total': total,
                            'total_bet': total_bet,       下注总金额
                            'total_bonus': total_bonus    总奖金
                        }
            """

    current_page = request.args.get('page', type=int, default=1)
    limit = request.args.get('limit', type=int, default=20)
    date_filtered = request.args.get('date_filtered', type=int, default=0)
    order_id = request.args.get('order_id')

    match_id = request.args.get('match_id')
    is_detail = request.args.get('is_detail')

    key_word = request.args.get('key_word')
    start_time = request.args.get('start_time')
    end_time = request.args.get('end_time')

    order_type = request.args.get('order_type')
    order_types = request.args.get('order_types')
    bet_type = request.args.get('bet_type')
    status = request.args.get('status')
    pay_wallet = request.args.get('pay_wallet')
    bet_status = request.args.get('bet_status')

    if is_detail:
        order_list = OrderHistory.query.filter(OrderHistory.USER_ID == g.user.id, OrderHistory.ORDER_ID == order_id)
        order_list = order_list.all()
        return jsonify({
            'items': [u.to_dict() for u in order_list],
        })

    order_list = AppBetOrder.query.filter(AppBetOrder.mb_id == g.user.id, AppBetOrder.del_flag == 0,
                                          AppBetOrder.bet_type != 'AWC',
                                          or_(AppBetOrder.game_status == 'Finished',
                                              AppBetOrder.game_status == 'Cancelled'))

    # Query AWC game sessions (only completed sessions)
    session_query = GameSession.query.filter(
        GameSession.mb_id == g.user.id,
        GameSession.del_flag == 0,
        GameSession.result_status != 'InProgress',
    )

    # if g.user.AGENT_CODE:
    #     users_under = AppUser.query.filter_by(aid=g.user.AGENT_CODE).all()
    #     users_under = set([u.USER_ID for u in users_under])
    #     order_list = order_list.filter(OrderHistory.USER_ID.in_(users_under))

    if order_id:
        order_list = order_list.filter(AppBetOrder.bet_group == order_id)
    if key_word:
        order_list = order_list.filter(
            or_(AppBetOrder.bet_group.like('%{}%'.format(key_word)), AppBetOrder.mb_id.like('%{}%'.format(key_word)),
                AppBetOrder.mb_username.like('%{}%'.format(key_word)),
                AppBetOrder.game_id.like('%{}%'.format(key_word)),
                AppBetOrder.remarks.like('%{}%'.format(key_word))))

    if match_id:
        order_list = order_list.filter(AppBetOrder.game_id == match_id)
    if order_type:
        order_list = order_list.filter(AppBetOrder.bet_type_sub.like('%{}:%'.format(order_type)))
    if order_types:
        bet_type_patterns = ['%{}:%'.format(ot) for ot in order_types.split(",")]
        order_list = order_list.filter(or_(*[AppBetOrder.bet_type_sub.like(pattern) for pattern in bet_type_patterns]))
    if status and int(status) > 0:
        order_list = order_list.filter(
            AppBetOrder.bet_status == BetStatus.Pending if status == "1" else AppBetOrder.bet_status != BetStatus.Pending)
    if pay_wallet:
        order_list = order_list.filter(AppBetOrder.pay_wallet == pay_wallet)
    if bet_status:
        order_list = order_list.filter(AppBetOrder.bet_status == bet_status)

    if bet_type:
        order_list = order_list.filter(AppBetOrder.bet_type == bet_type)

    # AWC筛选
    if pay_wallet:
        if pay_wallet == "Promotion":  # Promotion
            session_query = session_query.filter(
                GameSession.entry_promo_wallet > 0,
                GameSession.net_promo != 0
            )
        else:  # Money
            session_query = session_query.filter(
                or_(
                    GameSession.net_main != 0,
                )
            )

    if bet_status:
        status_map = {
            "Win": ResultStatus.Win,
            "Lose": ResultStatus.Loss,
            "Loss": ResultStatus.Loss,
            "Draw": ResultStatus.Draw
        }
        if bet_status in status_map:
            session_query = session_query.filter(GameSession.result_status == status_map[bet_status])
        else:
            # bet_status 不在映射中（如 Pending），GameSession 无对应状态，返回空结果
            session_query = session_query.filter(False)

    # 保存无日期过滤的查询快照，用于结果不足5条时的回退查询
    order_list_no_date = order_list
    session_query_no_date = session_query

    if start_time:
        # 将缅甸时间转换为中国时间（加上1.5小时）
        start_time_china = convert_myanmar_to_china_time(start_time, is_end_time=False)
        order_list = order_list.filter(AppBetOrder.create_time >= start_time_china)
        session_query = session_query.filter(GameSession.entry_time >= start_time_china)

    if end_time:
        # 将缅甸时间转换为中国时间（加上1.5小时）
        end_time_china = convert_myanmar_to_china_time(end_time, is_end_time=True)
        order_list = order_list.filter(AppBetOrder.create_time <= end_time_china)
        session_query = session_query.filter(GameSession.entry_time <= end_time_china)

    # Execute AppBetOrder query
    order_query = order_list.group_by(AppBetOrder.bet_group)
    total_orders = order_query.count()
    app_bet_orders = order_query.offset((current_page - 1) * limit).limit(limit).all()

    # Execute GameSession query
    total_sessions = session_query.count()
    game_sessions = session_query.offset((current_page - 1) * limit).limit(limit).all()

    # Transform and merge results
    from app_server.model.MatchModel import Match

    def _build_result(bet_orders, sess_list):
        """将 AppBetOrder 和 GameSession 转换为统一的字典列表，按时间倒序"""
        merged = []
        for order in bet_orders:
            order_dict = order.to_dict()
            if order.game_id:
                m = Match.query.filter_by(ID=order.game_id).first()
                if m:
                    order_dict['MATCH_TIME'] = str(m.MATCH_TIME)
            order_dict['_sort_time'] = order.create_time
            merged.append(order_dict)
        for session in sess_list:
            merged.append(_transform_game_session_to_order_dict(session))
        merged.sort(key=lambda x: x.get('_sort_time') or x.get('_create_time'), reverse=True)
        return merged

    result = _build_result(app_bet_orders, game_sessions)

    # Apply pagination limit
    result = result[:limit]

    # 如果结果少于5条，取消日期过滤，保留其他筛选条件，取最新5条
    # 用户主动筛选日期时（date_filtered=1），不做回退，保留筛选结果
    min_display = 5
    if len(result) < min_display and (start_time or end_time) and not date_filtered:
        fallback_order_query = order_list_no_date.group_by(AppBetOrder.bet_group)
        fallback_orders = fallback_order_query.order_by(AppBetOrder.create_time.desc()).limit(min_display).all()
        fallback_sessions = session_query_no_date.order_by(GameSession.entry_time.desc()).limit(min_display).all()
        result = _build_result(fallback_orders, fallback_sessions)[:min_display]

    # Clean up internal sorting keys
    for item in result:
        item.pop('_sort_time', None)

    # Calculate total count
    total = total_orders + total_sessions

    return jsonify({
        'items': result,
        'total': total})


# 获取订单列表
@order.route('/get_history_old', methods=['GET'])
@auth.login_required
def get_order_history_old():
    """ get_order_history API Endpoint
        ---
        tags:
          - order
        parameters:
           - name: current_page
             in: query
             type: string
             required: true
             description: current_page of order_history
           - name: limit
             in: query
             type: integer
             description: limit of order_history
           - name: order_id
             in: query
             type: string
             description: order_id of order_history
           - name: key_word
             in: query
             type: string
             description: key_word of order_history
           - name: start_time
             in: query
             type: string
             description: start_time of order_history
           - name: end_time
             in: query
             type: string
             description: end_time of order_history
           - name: order_type
             in: query
             type: string
             description: status of order_history
             example: 1 # 1.single hdp 2.single o/u 3.correct score 4.mix hdp 5.mix o/u 6.single even/odd 7.mix even/odd 8.digital 9.digital_3d 10.single win/lose 11. mix win/lose
           - name: order_types
             in: query
             type: string
             description: order_types of order_history
             example: [1, 2, 3]
           - name: bet_type
             in: query
             type: string
             description: bet_type of order_history
             example: 1 # 1.host/over 2.guest/under 3.draw
           - name: status
             in: query
             type: string
             description: status of order_history   1 valid   0 invalid
           - name: is_mix
             in: query
             type: string
             description: is_mix of order_history 0 not mix   1 mix
           - name: is_win
             in: query
             type: string
             description: is_win of order_history  0 lose  1 win
        responses:
          200:
            description: { 'items': [...], 'total': 100, 'total_bet': 10000, 'total_bonus': 5000 }
        """
    # response = jsonify({'code': 50001, "message": "under maintence"})
    repeat_key = 'query_history_%s' % g.user.id
    Redis.get(repeat_key)
    is_detail = request.args.get('is_detail', type=bool, default=False)
    if Redis.get(repeat_key) and not is_detail:
        response = jsonify({'message': "Please wait for 60 second"})
        response.status_code = 429
        return response
    else:
        Redis.set(repeat_key, 1, ex=3)
    current_page = request.args.get('page', type=int, default=1)
    limit = request.args.get('limit', type=int, default=20)
    order_id = request.args.get('order_id')

    match_id = request.args.get('match_id')

    key_word = request.args.get('key_word')
    start_time = request.args.get('start_time')
    end_time = request.args.get('end_time')

    order_type = request.args.get('order_type')
    order_types = request.args.get('order_types')
    # 游戏类型 0:所有 1:比赛 2:数字
    game_type = request.args.get('game_type', type=int, default=1)
    bet_type = request.args.get('bet_type')
    is_mix = request.args.get('is_mix')
    is_win = request.args.get('is_win')

    if is_detail:
        order_list = OrderHistory.query.filter(OrderHistory.USER_ID == g.user.id, OrderHistory.ORDER_ID == order_id)
        order_list = order_list.all()
        return jsonify({
            'items': [u.to_dict() for u in order_list],
        })

    cl = SphinxClient()
    cl.SetServer('localhost', 9312)
    cl.SetLimits((current_page - 1) * limit, limit)
    print("????", (current_page - 1) * limit)
    cl.SetSortMode(SPH_SORT_ATTR_DESC, "id")
    print("getting order_history with:", request.args)

    total = 0

    query_str = "@USER_ID %s" % g.user.id

    if key_word:
        query_str += key_word

    if order_id:
        query_str += "@ORDER_ID %s" % order_id
    if match_id:
        query_str += "@MATCH_ID %s" % match_id
    if order_type:
        cl.SetFilter('ORDER_TYPE', [int(order_type)])
    if bet_type:
        cl.SetFilter('BET_TYPE', [bet_type])
    if is_mix:
        cl.SetFilter('IS_MIX', [int(is_mix)])
    if is_win:
        cl.SetFilter('IS_WIN', [int(is_win)])
    if not is_detail:
        cl.SetGroupBy('ORDER_GROUP', SPH_GROUPBY_ATTR, 'id desc')
    if game_type:
        if game_type == GameType.Match:
            cl.SetFilter('ORDER_TYPE', [1, 2, 3, 4, 5, 6, 7, 10])
        if game_type == GameType.Digit:
            cl.SetFilter('ORDER_TYPE', [8])

    # if start_time:
    #     start_time += " 00:00:00"
    #     time_array = time.strptime(start_time, "%Y-%m-%d %H:%M:%S")
    #     now_ts = int(time.time())
    #     start_time = int(time.mktime(time_array))
    #     cl.SetFilterRange('CREATE_TIME', start_time, now_ts)
    #
    # if end_time:
    #     end_time += " 23:59:59"
    #     time_array = time.strptime(end_time, "%Y-%m-%d %H:%M:%S")
    #     ts = int(time.mktime(time_array))
    #     cl.SetFilterRange('CREATE_TIME', start_time or 0, ts)

    print("filter str:", query_str)

    res = cl.Query(query_str, 'order_history;order_history_add')

    whole = {}
    order_ids = {}
    if res:
        whole = {w['id'] for w in res['matches']}
        order_ids = {w["attrs"]['order_group'] for w in res['matches']}
        total = res['total_found']
        print("order_history:", (current_page - 1) * limit, res['total_found'], res['total'])

    print("got result:", len(whole))
    order_list = OrderHistory.query.filter(OrderHistory.ID.in_(whole))

    if not is_detail:
        order_list = order_list.group_by(OrderHistory.ORDER_ID)
        result = []
        # order_list = order_list.with_entities(OrderHistory, func.count(OrderHistory.ORDER_ID))
        order_list = order_list.offset((current_page - 1) * limit).limit(limit).all()
        for u in order_list:
            # temp = u[0].to_dict()
            # temp['ORDER_COUNT'] = u[1]
            temp = u.to_dict()
            result.append(temp)
        return jsonify({
            'items': result,
            'total': len(result)})
        # order_list = order_list.group_by(OrderHistory.ORDER_ID).all()
        # _sum = OrderHistory.query.filter(OrderHistory.ORDER_TYPE == '8',
        #                                  OrderHistory.ORDER_ID.in_(order_ids)).with_entities(func.sum(OrderHistory.BONUS),
        #                                                                                      func.sum(OrderHistory.BET_MONEY), OrderHistory.ORDER_ID,
        #                                                                                      func.sum(OrderHistory.IS_WIN)).group_by(OrderHistory.ORDER_ID).all()
        # sum_dict = {}
        # for bonus, bet_money, order_id, id_win in _sum:
        #     # print("---", type(bonus), type(bet_money), type(id_win))
        #     # print("---", bonus, bet_money, id_win, order_ids)
        #     sum_dict[order_id] = {
        #         "BONUS": str(bonus),
        #         "BET_MONEY": str(bet_money),
        #         "IS_WIN": int(id_win),
        #     }
        # for u in order_list:
        #     temp = u.to_dict()
        #     # if u.ORDER_ID in sum_dict:
        #     #     temp.update(sum_dict[u.ORDER_ID])
        #     result.append(temp)
        # return jsonify({
        #     'items': result,
        #     'total': total
        # })

    order_list = order_list.all()
    return jsonify({
        'items': [u.to_dict() for u in order_list],
        'total': total

    })


def _transform_game_session_to_order_dict(session):
    """
    Transform GameSession to frontend-compatible dict with snake_case keys.

    Args:
        session: GameSession model instance

    Returns:
        dict: Transformed dictionary matching frontend expectations
    """
    # Determine pay_wallet: "Promotion" if promo wallet used, else "Money"
    pay_wallet = "Promotion" if (session.entry_promo_wallet and
                                 session.entry_promo_wallet > 0 and
                                 session.net_promo and
                                 session.net_promo != 0) else "Money"

    # Map result_status to bet_status
    bet_status_map = {
        ResultStatus.Win: "Win",
        ResultStatus.Loss: "Lose",
        ResultStatus.Draw: "Draw"
    }
    bet_status = bet_status_map.get(session.result_status)
    # bet_status = bet_status_map.get(session.result_status, "Pending")

    # Generate status icon path
    status_img = f"/static/image/order/{bet_status.lower()}.svg"

    # Format datetime helper
    def format_datetime(dt):
        if dt:
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        # if dt:
        #     return dt.strftime('%d/%m/%Y %I:%M:%S %p')
        return ""

    # Format net values with +/- prefix
    def format_net_value(value):
        if value is None:
            return "0"
        num = float(value)
        if num > 0:
            return f"+{int(num)}"
        elif num < 0:
            return str(int(num))
        else:
            return "0"

    return {
        'id': session.id,
        'platform_source': 'AWC',  # Trigger AWC display
        'platform': session.platform,
        'game_name': session.game_name,
        'pay_wallet': pay_wallet,
        'bet_status': bet_status,
        'status_img': status_img,
        'entry_time': format_datetime(session.entry_time),
        'exit_time': format_datetime(session.exit_time),
        # 'entry_time': session.entry_time,
        # 'exit_time': session.exit_time,
        'entry_main_wallet': float(session.entry_main_wallet) if session.entry_main_wallet else 0,
        'entry_promo_wallet': float(session.entry_promo_wallet) if session.entry_promo_wallet else 0,
        'net_main': format_net_value(session.net_main),
        'net_promo': format_net_value(session.net_promo),
        '_sort_time': session.entry_time,  # For sorting
    }
