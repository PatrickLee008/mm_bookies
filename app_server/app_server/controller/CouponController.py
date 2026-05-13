from datetime import datetime, timedelta
from decimal import Decimal
import json
import uuid
from uuid import uuid4

from sqlalchemy import func, and_, or_, case
from flask import g, request, jsonify, Blueprint

from app_server import app, db, auth
from app_server.model.AppMemberModel import AppMember
from app_server.model.MAppCouponModel import MAppCoupon
from app_server.model.MAppMemberCouponModel import MAppMemberCoupon
from app_server.model.AppMemberBalanceLogModel import AppMemberBalanceLog, TransactionType, TransactionMap
from app_server.model.AppPlayerActivityRecordModel import AppPlayerActivityRecord

from app_server.model.AppBetOrderModel import AppBetOrder, BetStatus
from app_server.service.NetWinService import NetWinService
from app_server.service.RiskManagementService import RiskManagementService
from app_server.utils.Kits import Kits

# 常量定义
SUCCESS_CODE = 200
SYSTEM_ERROR_CODE = 501
PARAM_ERROR_CODE = 401
COUPON_NOT_FOUND_CODE = 402
COUPON_NOT_VALID_CODE = 403
COUPON_ALREADY_CLAIMED_CODE = 404
INSUFFICIENT_BALANCE_CODE = 405
NET_WIN_NOT_MET_CODE = 406
RISK_CHECK_FAILED_CODE = 407

# 创建蓝图
coupon = Blueprint('coupon', __name__)


# 辅助函数：检查优惠券是否有效
def is_coupon_valid(coupon):
    """检查优惠券是否在有效期内且已激活

    优惠券状态说明：
    - Active: 活跃状态，可以被用户领取
    - Finished: 已结束状态，不可领取但已领取的仍可使用
    - Expired: 已过期状态，已领取的优惠券也已过期

    托管状态说明：
    - 0: 未托管
    - 1: 已托管（正常状态）
    - 2: 已退款（钱已退还给代理，不可再领取）

    用户端只能领取 Active 状态且未退款的优惠券
    """
    if not coupon or coupon.del_flag != 0 or coupon.p_status not in ['Active']:
        return False

    now = datetime.now()

    # 检查领取时间范围 (p_start 和 p_end 是优惠券可领取的时间范围)
    if coupon.p_start and now < coupon.p_start:
        return False
    if coupon.p_end and now > coupon.p_end:
        return False

    # 注意：这里不检查 p_expire，因为 p_expire 是优惠券的最终过期时间
    # 即使超过 p_end，只要状态是 Active，仍可领取
    # p_expire 由后台定时任务处理，前端只需检查状态即可

    # 检查托管状态：已退款的优惠券不可领取
    if coupon.escrow_status == 2:
        return False

    # 统一检查托管余额是否充足（代理和House优惠券都需要）
    if not coupon.remaining_amount or coupon.remaining_amount <= 0:
        return False

    return True


# 辅助函数：检查净赢条件
def check_net_win_condition(user_id, coupon):
    """
    检查用户是否满足优惠券的净赢条件
    ✅ 与Java端保持一致：只统计该优惠券活动的订单
    """
    # 使用 NetWinService 检查净赢条件
    result = NetWinService.check_net_win_eligibility(
        user_id=user_id,
        net_win_enabled=coupon.net_win_enabled,
        condition_type=coupon.net_win_condition_type,
        required_amount=coupon.net_win_amount,
        coupon_id=coupon.id,  # ⭐ 传入优惠券ID，只统计该活动的订单
        start_date=coupon.p_start,
        end_date=coupon.p_end
    )

    return result['eligible'], result['message']


# 辅助函数：检查用户领取限制
def check_user_claim_limits(user_id, coupon_id, coupon, member_locked=None):
    """检查用户是否超过领取限制

    ⚠️ 重要：此函数必须在锁定用户记录后调用，以防止并发插入导致超出限制

    Args:
        user_id: 用户ID
        coupon_id: 优惠券ID
        coupon: 优惠券对象
        member_locked: 已加锁的会员对象（可选），如果提供则跳过用户查询
    """
    # 检查资金来源权限
    if coupon.fund_source_type == 'AGENT':
        # 使用已加锁的member对象，避免重复查询
        member = member_locked if member_locked else AppMember.query.filter_by(id=user_id, del_flag=0).first()
        if not member:
            return False, "Member not found"

        # AGENT类型的优惠券需要会员的aid与优惠券的aid匹配
        if member.aid != coupon.aid:
            return False, "You are not authorized to redeem this agent coupon"
    # HOUSE类型的优惠券所有人都可以领取，无需额外检查

    # 检查用户总领取次数
    # ⚠️ 不再使用 with_for_update()，因为它只能锁定已存在的行，无法防止并发插入（幻读）
    # 必须依赖外层的用户记录锁来确保操作串行化
    if coupon.plmu_jtt and coupon.plmu_jtt > 0:
        total_claims = MAppMemberCoupon.query.filter_by(
            mb_id=user_id,
            p_id=coupon_id,
            del_flag=0
        ).count()  # 移除 with_for_update()，依赖外层用户锁

        if total_claims >= coupon.plmu_jtt:
            return False, f"Total claim limit reached: {coupon.plmu_jtt}"

    # 检查用户每日领取次数
    if coupon.plmu_jpd and coupon.plmu_jpd > 0:
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)

        daily_claims = MAppMemberCoupon.query.filter(
            MAppMemberCoupon.mb_id == user_id,
            MAppMemberCoupon.p_id == coupon_id,
            MAppMemberCoupon.create_time >= today_start,
            MAppMemberCoupon.create_time < today_end,
            MAppMemberCoupon.del_flag == 0
        ).count()  # 移除 with_for_update()，依赖外层用户锁

        if daily_claims >= coupon.plmu_jpd:
            return False, f"Daily claim limit reached: {coupon.plmu_jpd}"

    # 检查玩家下次参与时间间隔（时间窗口限制）
    if coupon.next_participate_hours and coupon.next_participate_hours > 0:
        # 查询用户最后一次领取该优惠券的时间
        last_claim = MAppMemberCoupon.query.filter(
            MAppMemberCoupon.mb_id == user_id,
            MAppMemberCoupon.p_id == coupon_id,
            MAppMemberCoupon.del_flag == 0
        ).order_by(MAppMemberCoupon.create_time.desc()).first()

        if last_claim and last_claim.create_time:
            # 计算距离上次领取的时间（小时）
            time_since_last_claim = datetime.now() - last_claim.create_time
            hours_since_last_claim = time_since_last_claim.total_seconds() / 3600

            # 如果距离上次领取的时间小于设定的时间间隔，则不允许领取
            if hours_since_last_claim < coupon.next_participate_hours:
                remaining_hours = coupon.next_participate_hours - hours_since_last_claim
                return False, f"You can claim this coupon again in {remaining_hours:.1f} hours (Next participate interval: {coupon.next_participate_hours} hours)"

    return True, "Within claim limits"


# 辅助函数：风险检查
def perform_risk_check(user_id, coupon_id, coupon_obj, ip_address=None, device_id=None, user_agent=None):
    """使用RiskManagementService进行风险检查

    Args:
        user_id: 用户ID
        coupon_id: 优惠券ID
        coupon_obj: 优惠券对象（用于获取风险配置）
        ip_address: IP地址
        device_id: 设备唯一标识 (IMEI/UUID/Device ID)
        user_agent: User Agent
    """
    try:
        # 首先检查用户状态
        member = AppMember.query.filter_by(id=user_id, del_flag=0).first()
        if not member:
            return False, "User not found"

        if member.status != 1:  # 假设1是正常状态
            return False, "User account is not active"

        # ✅ 从优惠券配置中读取风险控制参数（简化版：只包含核心配置）
        coupon_config = {
            'ip_limit_count': coupon_obj.ip_limit_count if coupon_obj.ip_limit_count is not None else 10,
            'ip_time_window_hours': coupon_obj.ip_time_window_hours if coupon_obj.ip_time_window_hours is not None else 1,
            'imei_limit_count': coupon_obj.imei_limit_count if coupon_obj.imei_limit_count is not None else 5
        }

        # 使用RiskManagementService进行综合风险评估
        risk_result = RiskManagementService.assess_redemption_risk(
            user_id=user_id,
            coupon_id=coupon_id,
            ip=ip_address or '0.0.0.0',
            imei=device_id,  # 传递设备唯一标识
            user_agent=user_agent,
            location=None,  # 可以从请求中获取位置信息
            coupon_config=coupon_config,
            username=member.username  # 传递用户名用于黑名单检查
        )

        if not risk_result['allowed']:
            return False, risk_result['reason']

        return True, "Risk check passed"

    except Exception as e:
        print(f"Risk check error: {str(e)}")
        return False, "Risk check failed"


# 辅助函数：检查注册时间限制
def check_registration_restriction(user_id, coupon):
    """
    检查玩家是否满足注册时间限制

    Args:
        user_id: 玩家ID
        coupon: 优惠券对象

    Returns:
        tuple: (是否通过, 消息)
    """
    # 如果未勾选"Use for registering"，直接通过
    if not coupon.p_register_display or coupon.p_register_display == '0':
        return True, "No registration restriction"

    # 获取玩家注册时间
    member = AppMember.query.filter_by(id=user_id, del_flag=0).first()
    if not member or not member.create_time:
        return False, "Player registration time not found"

    player_register_time = member.create_time

    # 检查是否在注册时间范围内
    if coupon.p_register_start and player_register_time < coupon.p_register_start:
        return False, f"This coupon is only for players registered after {coupon.p_register_start.strftime('%Y-%m-%d %H:%M:%S')}"

    if coupon.p_register_end and player_register_time > coupon.p_register_end:
        return False, f"This coupon is only for players registered before {coupon.p_register_end.strftime('%Y-%m-%d %H:%M:%S')}"

    # 如果设置了充值金额要求
    if coupon.p_min_deposit and coupon.p_min_deposit > 0:
        # 查询玩家在活动时间内的最后一次充值金额
        from app_server.model.ChargeModel import Charge

        # 构建查询条件
        query = db.session.query(Charge).filter(
            Charge.mb_id == user_id,
            Charge.status == 'Success',  # 只统计成功的充值
            Charge.del_flag == 0
        )

        # 如果有活动开始时间，只统计活动期间的充值
        if coupon.p_start:
            query = query.filter(Charge.create_time >= coupon.p_start)

        # 如果有活动结束时间
        if coupon.p_end:
            query = query.filter(Charge.create_time <= coupon.p_end)

        # 获取活动期间的最后一次充值
        last_deposit = query.order_by(Charge.create_time.desc()).first()
        last_deposit_amount = last_deposit.amount if last_deposit else Decimal('0')

        min_deposit_require = '%.1f' % coupon.p_min_deposit
        if last_deposit_amount < Decimal(min_deposit_require):
            return False, f"Deposit requirement not met. Required: {min_deposit_require}, Current: {float(last_deposit_amount)}"

    return True, "Registration restriction passed"


def check_invitation_activity_completed(activity_record):
    """
    检查邀请活动是否已完成流水/净赢条件

    Args:
        activity_record: 邀请活动记录（AppPlayerActivityRecord）

    Returns:
        bool: True = 已完成条件, False = 未完成条件
    """
    # 直接检查达标标记
    return activity_record.is_requirement_met == 1


# 辅助函数：计算自动派发奖金金额
def calculate_auto_distribution_bonus(user_id, coupon):
    """
    根据优惠券的自动派发配置计算实际奖金金额

    Args:
        user_id: 玩家ID
        coupon: 优惠券对象

    Returns:
        tuple: (奖金金额, 消息, 数据详情)
    """
    # 如果未启用自动派发，返回原始奖金金额
    if not coupon.p_at_ep or coupon.p_at_ep == '0':
        return coupon.bonus_amount, "Auto distribution not enabled", None

    # 检查必需字段
    if not coupon.p_at_ep_cond or not coupon.p_at_ep_type or not coupon.p_at_ep_amt:
        return coupon.bonus_amount, "Auto distribution config incomplete", None

    condition_type = coupon.p_at_ep_cond  # Deposit, Bet, First_Deposit, First_Bet
    amount_type = coupon.p_at_ep_type  # Amount, Percent
    amount_value = Decimal(str(coupon.p_at_ep_amt))
    min_amount = Decimal(str(coupon.p_at_ep_min_amt)) if coupon.p_at_ep_min_amt else Decimal('0')
    max_amount = Decimal(str(coupon.p_at_ep_max_amt)) if coupon.p_at_ep_max_amt else None

    # 无论是固定金额还是百分比模式，都需要根据条件类型验证玩家是否满足要求
    reference_amount = Decimal('0')
    data_details = {}
    condition_met = False  # 是否满足条件

    if condition_type == 'Deposit':
        # 验证当天最后一笔充值（且在活动期间内）
        from app_server.model.ChargeModel import Charge
        import pytz

        # 获取当前用户的时区（从 g.user 直接获取）
        user_timezone = g.user.timezone if hasattr(g.user, 'timezone') and g.user.timezone else 'Asia/Yangon'

        # 获取用户时区的当天00:00:00时间
        user_tz = pytz.timezone(user_timezone)
        user_now = datetime.now(user_tz)
        user_today_start_str = user_now.replace(hour=0, minute=0, second=0, microsecond=0).strftime('%Y-%m-%d %H:%M:%S')
        user_today_end_str = (user_now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)).strftime(
            '%Y-%m-%d %H:%M:%S')

        # 转换为系统时区（Asia/Shanghai UTC+8）
        system_today_start_str = Kits.user_time_to_system_time(user_timezone, user_today_start_str)
        system_today_end_str = Kits.user_time_to_system_time(user_timezone, user_today_end_str)

        # 转换为datetime对象用于数据库查询
        today_start = datetime.strptime(system_today_start_str, '%Y-%m-%d %H:%M:%S')
        today_end = datetime.strptime(system_today_end_str, '%Y-%m-%d %H:%M:%S')

        # 构建查询：当天的充值 + 活动期间限制
        query = db.session.query(Charge).filter(
            Charge.mb_id == user_id,
            Charge.status == 'Success',
            Charge.del_flag == 0,
            Charge.create_time >= today_start,
            Charge.create_time < today_end
        )

        # 限制在活动期间内
        if coupon.p_start:
            query = query.filter(Charge.create_time >= coupon.p_start)
        if coupon.p_end:
            query = query.filter(Charge.create_time <= coupon.p_end)

        # 查询符合条件的最后一笔充值（最新的充值）
        last_deposit_today = query.order_by(Charge.create_time.desc()).first()

        if last_deposit_today:
            reference_amount = last_deposit_today.amount or Decimal('0')

            # 检查充值金额是否达到最低要求
            if reference_amount < min_amount:
                return Decimal('0'), f"Deposit amount does not meet minimum requirement", {
                    'condition': 'Deposit',
                    'last_deposit_today': float(reference_amount),
                    'min_required': float(min_amount),
                    'message': f'Deposit amount {float(reference_amount)} is less than minimum required {float(min_amount)}'
                }

            condition_met = True
        else:
            # 当天没有充值记录
            return Decimal('0'), f"No deposit found today", {
                'condition': 'Deposit',
                'last_deposit_today': 0,
                'min_required': float(min_amount),
                'message': 'No deposit found today'
            }

        data_details = {
            'condition': 'Deposit',
            'last_deposit_today': float(reference_amount),
            'min_required': float(min_amount)
        }

    elif condition_type == 'First_Deposit':
        # 获取玩家在活动期间的首次充值金额
        from app_server.model.ChargeModel import Charge

        # 构建查询：先筛选活动期间，再按时间排序取第一条
        query = db.session.query(Charge).filter(
            Charge.mb_id == user_id,
            Charge.status == 'Success',
            Charge.del_flag == 0
        )

        # 限制在活动期间内
        if coupon.p_start:
            query = query.filter(Charge.create_time >= coupon.p_start)
        if coupon.p_end:
            query = query.filter(Charge.create_time <= coupon.p_end)

        # 获取活动期间的首次充值
        first_deposit = query.order_by(Charge.create_time.asc()).first()

        if first_deposit:
            reference_amount = first_deposit.amount or Decimal('0')
            # 检查首充金额是否达到最低要求
            condition_met = reference_amount >= min_amount

        data_details = {
            'condition': 'First_Deposit',
            'first_deposit_amount': float(reference_amount),
            'min_required': float(min_amount),
            'condition_met': condition_met
        }

    elif condition_type == 'Bet':
        # 获取玩家在活动期间的总下注金额
        query = db.session.query(func.sum(AppBetOrder.bet_amount)).filter(
            AppBetOrder.mb_id == user_id,
            AppBetOrder.game_status == 'Finished',  # 已结算的订单
            AppBetOrder.del_flag == 0
        )

        if coupon.p_start:
            query = query.filter(AppBetOrder.create_time >= coupon.p_start)
        if coupon.p_end:
            query = query.filter(AppBetOrder.create_time <= coupon.p_end)

        reference_amount = query.scalar() or Decimal('0')
        # 检查是否达到最低下注要求
        condition_met = reference_amount >= min_amount
        data_details = {
            'condition': 'Bet',
            'total_bet': float(reference_amount),
            'min_required': float(min_amount)
        }

    elif condition_type == 'First_Bet':
        # 获取玩家在活动期间的首次下注金额
        # 构建查询：先筛选活动期间，再按时间排序取第一条
        query = db.session.query(AppBetOrder).filter(
            AppBetOrder.mb_id == user_id,
            AppBetOrder.game_status == 'Finished',
            AppBetOrder.del_flag == 0
        )

        # 限制在活动期间内
        if coupon.p_start:
            query = query.filter(AppBetOrder.create_time >= coupon.p_start)
        if coupon.p_end:
            query = query.filter(AppBetOrder.create_time <= coupon.p_end)

        # 获取活动期间的首次下注
        first_bet = query.order_by(AppBetOrder.create_time.asc()).first()

        if first_bet:
            reference_amount = first_bet.bet_amount or Decimal('0')
            # 检查首注金额是否达到最低要求
            condition_met = reference_amount >= min_amount

        data_details = {
            'condition': 'First_Bet',
            'first_bet_amount': float(reference_amount),
            'min_required': float(min_amount),
            'condition_met': condition_met
        }
    else:
        return Decimal('0'), f"Invalid condition type: {condition_type}", None

    # 检查是否满足条件
    if not condition_met:
        if min_amount > 0:
            return Decimal(
                '0'), f"Minimum {condition_type} requirement not met. Required: {float(min_amount)}, Current: {float(reference_amount)}", data_details
        else:
            return Decimal('0'), f"Condition not met: No {condition_type} record found in activity period", data_details

    # 根据金额类型计算奖金
    if amount_type == 'Amount':
        # 固定金额模式：满足条件后直接返回固定金额
        bonus = amount_value
        data_details['type'] = 'Amount'
        data_details['fixed_amount'] = float(amount_value)
        data_details['final_bonus'] = float(bonus)
        return bonus, f"Fixed amount (condition met): {float(bonus)}", data_details

    elif amount_type == 'Percent':
        # 百分比模式：根据参考金额计算百分比
        if reference_amount <= 0:
            return Decimal('0'), f"No {condition_type} amount found for percentage calculation", data_details

        # 计算百分比奖金：参考金额 * 百分比
        bonus = reference_amount * (amount_value / Decimal('100'))

        # 应用最大金额限制
        if max_amount and bonus > max_amount:
            original_bonus = bonus
            bonus = max_amount
            data_details['capped'] = True
            data_details['original_bonus'] = float(original_bonus)
            data_details['max_amount'] = float(max_amount)

        data_details['type'] = 'Percent'
        data_details['percent'] = float(amount_value)
        data_details['reference_amount'] = float(reference_amount)
        data_details['final_bonus'] = float(bonus)

        return bonus, f"Calculated {float(amount_value)}% of {condition_type}: {float(bonus)}", data_details

    else:
        return Decimal('0'), f"Invalid amount type: {amount_type}", None


@coupon.route('/list', methods=['GET'])
@auth.login_required
def get_available_coupons():
    """获取可用的优惠券列表"""
    try:
        user_id = g.user.id
        page = int(request.args.get('page', 1))
        page_size = min(int(request.args.get('page_size', 20)), 100)

        # 查询所有有效的优惠券
        # 条件：状态为Active + 在领取时间范围内
        now = datetime.now()
        query = MAppCoupon.query.filter(
            MAppCoupon.del_flag == 0,
            MAppCoupon.p_status == 'Active',  # 只有Active状态才可领取
            MAppCoupon.tenant_id == '10000',
            or_(
                MAppCoupon.p_start.is_(None),
                MAppCoupon.p_start <= now  # 领取开始时间检查
            ),
            or_(
                MAppCoupon.p_end.is_(None),
                MAppCoupon.p_end >= now  # 领取结束时间检查
            )
            # 注意：不检查p_expire，p_expire由后台定时任务处理状态变更
        )

        # 获取总数
        total_count = query.count()

        # 分页
        offset = (page - 1) * page_size
        coupons = query.order_by(MAppCoupon.create_time.desc()).offset(offset).limit(page_size).all()

        # 格式化返回数据
        coupon_list = []
        for c in coupons:
            # 检查用户是否已领取
            user_claims = MAppMemberCoupon.query.filter_by(
                mb_id=user_id,
                p_id=c.id,
                del_flag=0
            ).count()

            # 检查是否可以领取
            can_claim = True
            claim_message = "Available"

            # 检查领取限制
            limit_check, limit_msg = check_user_claim_limits(user_id, c.id, c)
            if not limit_check:
                can_claim = False
                claim_message = limit_msg

            coupon_info = {
                'id': c.id,
                'name': c.pname,
                'code': c.pcode,
                'description': c.p_des,
                'bonus_amount': float(c.bonus_amount) if c.bonus_amount else 0,
                'bonus_type': c.bonus_type,
                'turnover_rate': float(c.turnover_rate) if c.turnover_rate else 0,
                'start_date': c.p_start.strftime('%Y-%m-%d %H:%M:%S') if c.p_start else None,
                'end_date': c.p_end.strftime('%Y-%m-%d %H:%M:%S') if c.p_end else None,
                'user_claimed_count': user_claims,
                'can_claim': can_claim,
                'claim_message': claim_message,
                'fund_source_type': c.fund_source_type,
                'remaining_amount': float(c.remaining_amount) if c.remaining_amount else 0
            }
            coupon_list.append(coupon_info)

        return jsonify({
            'code': SUCCESS_CODE,
            'data': {
                'coupons': coupon_list,
                'pagination': {
                    'current_page': page,
                    'page_size': page_size,
                    'total_count': total_count,
                    'total_pages': (total_count + page_size - 1) // page_size
                }
            },
            'message': 'success'
        }), 200

    except Exception as e:
        return jsonify({
            'code': SYSTEM_ERROR_CODE,
            'data': None,
            'message': str(e)
        }), 500


@coupon.route('/validate', methods=['POST'])
@auth.login_required
def validate_coupon():
    """验证优惠券是否可以使用"""
    try:
        user_id = g.user.id
        data = request.json
        coupon_id = data.get('coupon_id')

        if not coupon_id:
            return jsonify({
                'code': PARAM_ERROR_CODE,
                'data': None,
                'message': 'Coupon ID is required'
            }), 400

        # 获取优惠券信息
        coupon_obj = MAppCoupon.query.filter_by(
            id=coupon_id,
            del_flag=0,
            tenant_id='10000'
        ).first()

        if not coupon_obj:
            return jsonify({
                'code': COUPON_NOT_FOUND_CODE,
                'data': None,
                'message': 'Coupon does not exist'
            }), 404

        # 先检查活动余额是否充足
        if not coupon_obj.remaining_amount or coupon_obj.remaining_amount <= 0:
            return jsonify({
                'code': COUPON_NOT_VALID_CODE,
                'data': None,
                'message': 'Activity balance insufficient. Please participate in other activities.'
            }), 400

        # 检查优惠券是否有效
        if not is_coupon_valid(coupon_obj):
            return jsonify({
                'code': COUPON_NOT_VALID_CODE,
                'data': None,
                'message': 'Coupon is not valid or has expired'
            }), 400

        # 检查领取限制
        limit_check, limit_msg = check_user_claim_limits(user_id, coupon_id, coupon_obj)
        if not limit_check:
            return jsonify({
                'code': COUPON_ALREADY_CLAIMED_CODE,
                'data': None,
                'message': limit_msg
            }), 400

        # 检查主钱包最低余额限制（新增）
        if coupon_obj.min_main_wallet_balance and coupon_obj.min_main_wallet_balance > 0:
            # 获取用户信息
            member = AppMember.query.filter_by(id=user_id, del_flag=0).first()
            if not member:
                return jsonify({
                    'code': PARAM_ERROR_CODE,
                    'data': None,
                    'message': 'Member not found'
                }), 400

            # 检查用户主钱包余额
            if not member.money or member.money < coupon_obj.min_main_wallet_balance:
                return jsonify({
                    'code': COUPON_NOT_VALID_CODE,
                    'data': {
                        'required_balance': float(coupon_obj.min_main_wallet_balance),
                        'current_balance': float(member.money) if member.money else 0
                    },
                    'message': f"Main wallet balance insufficient. Required: {float(coupon_obj.min_main_wallet_balance)}, Current: {float(member.money) if member.money else 0}"
                }), 400

        # ✅ 净赢条件已移除 - 净赢检查应该在结算时进行，而不是领取时
        # 原因：用户领取前还没有使用促销钱包下注，查询不到 pro_id 相关的订单

        # 风险检查
        ip_address = request.remote_addr
        user_agent = request.headers.get('User-Agent')
        # 获取设备唯一标识（支持多种header格式）
        device_id = (request.headers.get('X-Device-ID') or
                     request.headers.get('Device-ID') or
                     request.headers.get('X-Device-IMEI') or
                     request.headers.get('IMEI'))
        risk_check, risk_msg = perform_risk_check(user_id, coupon_id, coupon_obj, ip_address, device_id=device_id,
                                                  user_agent=user_agent)
        if not risk_check:
            return jsonify({
                'code': RISK_CHECK_FAILED_CODE,
                'data': None,
                'message': risk_msg
            }), 400

        return jsonify({
            'code': SUCCESS_CODE,
            'data': {
                'can_use': True,
                'coupon_id': coupon_id,
                'bonus_amount': float(coupon_obj.bonus_amount) if coupon_obj.bonus_amount else 0,
                'turnover_requirement': float(
                    coupon_obj.bonus_amount * coupon_obj.turnover_rate) if coupon_obj.bonus_amount and coupon_obj.turnover_rate else 0
            },
            'message': 'Coupon is valid and can be used'
        }), 200

    except Exception as e:
        return jsonify({
            'code': SYSTEM_ERROR_CODE,
            'data': None,
            'message': str(e)
        }), 500


@coupon.route('/redeem', methods=['POST'])
@auth.login_required
def redeem_coupon():
    """兑换优惠券 - 支持通过优惠券ID或兑换码"""
    try:
        user_id = g.user.id
        data = request.json
        coupon_id = data.get('coupon_id')
        coupon_code = data.get('coupon_code')

        # 验证参数：必须提供其中一个
        if not coupon_id and not coupon_code:
            return jsonify({
                'code': PARAM_ERROR_CODE,
                'data': None,
                'message': 'Either coupon_id or coupon_code is required'
            }), 400

        if coupon_id and coupon_code:
            return jsonify({
                'code': PARAM_ERROR_CODE,
                'data': None,
                'message': 'Please provide either coupon_id or coupon_code, not both'
            }), 400

        # 根据参数类型查找优惠券
        if coupon_id:
            # 通过ID查找
            coupon_obj = db.session.query(MAppCoupon).filter(
                MAppCoupon.id == coupon_id,
                MAppCoupon.del_flag == 0,
                MAppCoupon.tenant_id == '10000',
                # MAppCoupon.p_app_hidden == 1,
            ).with_for_update().first()
            redeem_type = 'id'
        else:
            # 通过兑换码查找
            coupon_obj = db.session.query(MAppCoupon).filter(
                MAppCoupon.p_code == coupon_code.strip(),
                MAppCoupon.del_flag == 0,
                MAppCoupon.tenant_id == '10000'
            ).with_for_update().first()
            redeem_type = 'code'

        if not coupon_obj:
            error_message = 'Coupon does not exist' if coupon_id else 'Invalid coupon code'
            return jsonify({
                'code': COUPON_NOT_FOUND_CODE,
                'data': None,
                'message': error_message
            }), 404

        # 先检查活动余额是否充足
        if not coupon_obj.remaining_amount or coupon_obj.remaining_amount <= 0:
            return jsonify({
                'code': COUPON_NOT_VALID_CODE,
                'data': None,
                'message': 'Activity balance insufficient. Please participate in other activities.'
            }), 400

        # 验证优惠券
        if not is_coupon_valid(coupon_obj):
            return jsonify({
                'code': COUPON_NOT_VALID_CODE,
                'data': None,
                'message': 'Coupon is not valid or has expired'
            }), 400

        # ⚠️ 关键修复：提前锁定用户记录，防止并发插入导致超出限制（幻读问题）
        # 锁定用户记录可以确保同一用户的领取操作串行化
        member_locked = db.session.query(AppMember).filter(
            AppMember.id == user_id,
            AppMember.del_flag == 0
        ).with_for_update().first()

        if not member_locked:
            return jsonify({
                'code': PARAM_ERROR_CODE,
                'data': None,
                'message': 'Member not found'
            }), 400

        # 检查优惠券总领取次数限制（所有玩家总共能领取的次数）
        if coupon_obj.p_lm_j_pc and coupon_obj.p_lm_j_pc > 0:
            current_total_claims = coupon_obj.p_tt_jc or 0
            if current_total_claims >= coupon_obj.p_lm_j_pc:
                return jsonify({
                    'code': COUPON_NOT_VALID_CODE,
                    'data': None,
                    'message': f'Coupon claim limit reached. Total available: {coupon_obj.p_lm_j_pc}, already claimed: {current_total_claims}'
                }), 400

        # 检查单个玩家领取限制（传入已加锁的member对象）
        limit_check, limit_msg = check_user_claim_limits(user_id, coupon_obj.id, coupon_obj, member_locked)
        if not limit_check:
            return jsonify({
                'code': COUPON_ALREADY_CLAIMED_CODE,
                'data': None,
                'message': limit_msg
            }), 400

        # 检查主钱包最低余额限制（使用已加锁的member对象）
        if coupon_obj.min_main_wallet_balance and coupon_obj.min_main_wallet_balance > 0:
            if not member_locked.money or member_locked.money < coupon_obj.min_main_wallet_balance:
                return jsonify({
                    'code': COUPON_NOT_VALID_CODE,
                    'data': {
                        'required_balance': float(coupon_obj.min_main_wallet_balance),
                        'current_balance': float(member_locked.money) if member_locked.money else 0
                    },
                    'message': f"Main wallet balance insufficient. Required: {float(coupon_obj.min_main_wallet_balance)}, Current: {float(member_locked.money) if member_locked.money else 0}"
                }), 400

        # 检查是否有正在参加的优惠券/促销活动（INVITATION活动单独检查）
        existing_active_activity = db.session.query(AppPlayerActivityRecord).filter(
            AppPlayerActivityRecord.mb_id == user_id,
            AppPlayerActivityRecord.status == 'Active',
            AppPlayerActivityRecord.del_flag == 0,
            AppPlayerActivityRecord.activity_type != 'INVITATION'
        ).first()

        if existing_active_activity:
            return jsonify({
                'code': COUPON_ALREADY_CLAIMED_CODE,
                'data': None,
                'message': 'You have an active coupon activity. Please complete or cancel it before claiming another coupon.'
            }), 400

        # 检查是否有未结算且促销钱包>0的邀请活动（互斥检查）
        active_invitation_activity = db.session.query(AppPlayerActivityRecord).filter(
            AppPlayerActivityRecord.mb_id == user_id,
            AppPlayerActivityRecord.activity_type == 'INVITATION',
            AppPlayerActivityRecord.status == 'Active',
            AppPlayerActivityRecord.is_requirement_met == 0,
            AppPlayerActivityRecord.del_flag == 0
        ).first()

        if active_invitation_activity:
            # 检查促销钱包余额：余额>0才阻止；余额=0允许参与
            promotion_balance = member_locked.money_promotion or Decimal('0')
            if promotion_balance > Decimal('0'):
                return jsonify({
                    'code': COUPON_ALREADY_CLAIMED_CODE,
                    'data': None,
                    'message': 'You have an active invitation activity with unmet requirements and remaining promotion balance. Please complete it before claiming a coupon.'
                }), 400

        # 检查注册时间限制（新增）
        reg_check, reg_msg = check_registration_restriction(user_id, coupon_obj)
        if not reg_check:
            return jsonify({
                'code': COUPON_NOT_VALID_CODE,
                'data': None,
                'message': reg_msg
            }), 400

        # 风险检查
        ip_address = request.remote_addr
        user_agent = request.headers.get('User-Agent')
        # 获取设备唯一标识（支持多种header格式）
        device_id = (request.headers.get('X-Device-ID') or
                     request.headers.get('Device-ID') or
                     request.headers.get('X-Device-IMEI') or
                     request.headers.get('IMEI'))
        risk_check, risk_msg = perform_risk_check(user_id, coupon_obj.id, coupon_obj, ip_address, device_id=device_id,
                                                  user_agent=user_agent)
        if not risk_check:
            return jsonify({
                'code': RISK_CHECK_FAILED_CODE,
                'data': None,
                'message': risk_msg
            }), 400

        # 计算自动派发奖金金额（新增）
        bonus_amount, bonus_msg, bonus_details = calculate_auto_distribution_bonus(user_id, coupon_obj)

        # 如果计算出的奖金为0，不允许领取
        if bonus_amount <= 0:
            return jsonify({
                'code': COUPON_NOT_VALID_CODE,
                'data': bonus_details,
                'message': f"Cannot claim coupon: {bonus_msg}"
            }), 400

        # 统一检查和扣除托管余额（代理和House优惠券都需要）
        if not coupon_obj.remaining_amount or coupon_obj.remaining_amount < bonus_amount:
            return jsonify({
                'code': INSUFFICIENT_BALANCE_CODE,
                'data': None,
                'message': 'Insufficient coupon balance'
            }), 400

        # 统一扣除优惠券托管余额
        coupon_obj.used_amount = (coupon_obj.used_amount or Decimal('0')) + bonus_amount
        coupon_obj.remaining_amount = coupon_obj.remaining_amount - bonus_amount

        # 更新总领取次数统计（与Java自动派发保持一致）
        current_total_claims = coupon_obj.p_tt_jc or 0
        coupon_obj.p_tt_jc = current_total_claims + 1

        # 直接使用前面已加锁的 member_locked 对象，避免重复查询
        member = member_locked

        # 计算过期时间（如果优惠券有过期时间设置）
        now = datetime.now()
        expire_time = None
        if coupon_obj.p_expire:
            expire_time = coupon_obj.p_expire
        elif coupon_obj.p_end:
            expire_time = coupon_obj.p_end
        else:
            # 默认30天后过期
            expire_time = now + timedelta(days=30)

        # 计算流水/净赢要求（根据 p_ep_cond 字段判断）
        req_turnover_value = Decimal('0')
        req_netwin_value = Decimal('0')
        condition_type = "None"
        if coupon_obj.p_tray == 1:
            # 获取条件类型（Turnover 或 Net Win）
            p_ep_cond = coupon_obj.p_ep_cond if hasattr(coupon_obj,
                                                        'p_ep_cond') and coupon_obj.p_ep_cond else 'Turnover'
            if p_ep_cond == 'Net Win':
                # 净赢条件：直接使用 p_ep_amtrq，不使用倍数计算
                # p_ep_amtrq 是管理员在创建优惠券时直接输入的净赢要求金额
                req_netwin_value = Decimal(str(coupon_obj.p_ep_amtrq)) if coupon_obj.p_ep_amtrq else Decimal('0')
                condition_type = "Net Win"
            else:
                # 流水条件：要求流水 = 奖金金额 × 倍率
                # 使用 p_lm_j_wt 作为倍率
                multiplier = Decimal(str(coupon_obj.p_lm_j_wt)) if coupon_obj.p_lm_j_wt else Decimal('1')
                req_turnover_value = bonus_amount * multiplier
                condition_type = "Turnover"
        # 创建领取记录
        activity_record_id = Kits.generate_uuid(),
        member_coupon = MAppMemberCoupon(
            id=Kits.generate_uuid(),
            mb_id=user_id,
            player_activity_record_id=activity_record_id,
            p_id=coupon_obj.id,
            p_name=coupon_obj.pname,
            mb_username=member.username if hasattr(member, 'username') else None,
            money=bonus_amount,
            req_turnover=req_turnover_value,
            req_netwin=req_netwin_value,
            cur_turnover=Decimal('0'),
            cur_netwin=Decimal('0'),
            status='Used',
            mb_ip=ip_address,
            device_id=device_id,  # 设备唯一标识
            claim_time=now,  # 领取时间
            create_time=now,  # 创建时间与领取时间一致
            use_time=None,  # 使用时间，初始为空
            expire_time=expire_time,  # 过期时间
            start_time=coupon_obj.p_start,  # 活动开始时间
            end_time=coupon_obj.p_end,  # 活动结束时间
            game_hall=coupon_obj.p_lm_game_hall,  # 游戏平台限制
            game_type=coupon_obj.p_lm_game_type,  # 游戏类型限制
            # 根据优惠券类型设置奖金派发渠道和活动参与渠道
            jp_channel="Platform Coupon" if coupon_obj.fund_source_type == 'HOUSE' else "Agent Coupon",  # 奖金派发渠道
            ep_channel="Platform Redemption" if coupon_obj.fund_source_type == 'HOUSE' else "Agent Redemption",
            # 活动参与渠道
            create_by_id=user_id,  # 创建人ID (移动端兑换时设为用户自己)
            del_flag=0,
            tenant_id='10000'
        )

        # 更新会员促销活动金额 (money_promotion)
        old_balance = member.money_promotion if member.money_promotion else Decimal('0')
        new_balance = bonus_amount
        member.money_promotion = bonus_amount

        # 记录会员促销活动金额流水
        balance_log = AppMemberBalanceLog(
            id=Kits.generate_uuid(),
            sn=f"COUPON_{member_coupon.id}",
            type=TransactionType.Activity,
            type_sub=TransactionType.CouponRedemption,
            type_sub_data_id=member_coupon.id,
            mb_id=user_id,
            mb_username=member.username if hasattr(member, 'username') else (
                member.name if hasattr(member, 'name') else None),
            money=bonus_amount,
            start_balance=old_balance,
            end_balance=new_balance,
            create_by_id=user_id,
            update_by_id=user_id,
            aid=g.user.aid,
            source="System",
            target=TransactionMap.ProWallet,
            pay_wallet="Promotion",
            status=1,
            source_status=0
        )

        # 创建活动参与记录
        # 根据条件类型动态设置完成条件描述
        if condition_type == "Net Win":
            completion_condition_text = f'Net Win: {float(req_netwin_value)}'
            completion_detail_data = {
                'member_coupon_id': member_coupon.id,
                'bonus_amount': float(bonus_amount),
                'condition_type': 'Net Win',
                'netwin_required': float(req_netwin_value)
            }
        elif condition_type == "Turnover":
            completion_condition_text = f'Turnover: {float(req_turnover_value)}'
            completion_detail_data = {
                'member_coupon_id': member_coupon.id,
                'bonus_amount': float(bonus_amount),
                'condition_type': 'Turnover',
                'turnover_required': float(req_turnover_value)
            }
        else:
            completion_condition_text = 'No requirement'
            completion_detail_data = {
                'member_coupon_id': member_coupon.id,
                'bonus_amount': float(bonus_amount),
                'condition_type': 'None'
            }

        activity_record = AppPlayerActivityRecord(
            id=activity_record_id,
            mb_id=user_id,
            aid=coupon_obj.aid,  # 从优惠券获取代理ID
            username=member.username if hasattr(member, 'username') else (
                member.name if hasattr(member, 'name') else None),
            activity_type='COUPON',
            activity_id=coupon_obj.id,
            member_coupon_id=member_coupon.id,
            activity_name=coupon_obj.pname,
            status='Active',
            start_time=now,
            completion_condition=completion_condition_text,
            completion_detail=json.dumps(completion_detail_data),
            req_turnover=req_turnover_value,
            req_netwin=req_netwin_value,
            is_requirement_met=0,
            create_time=now,
            create_by_id=user_id,
            del_flag=0,
            tenant_id='10000'
        )

        # 保存所有更改
        db.session.add(member_coupon)
        db.session.add(coupon_obj)  # 保存优惠券变更（更新托管余额）
        db.session.add(member)  # 保存会员余额更新
        db.session.add(balance_log)  # 保存流水记录
        db.session.add(activity_record)  # 保存活动参与记录

        db.session.commit()

        # 记录成功的兑换尝试
        RiskManagementService.record_redemption_attempt(
            user_id=user_id,
            coupon_id=coupon_id,
            ip=ip_address,
            imei=device_id,  # 记录设备唯一标识
            successful=True
        )

        # 构建响应数据
        response_data = {
            'redemption_id': member_coupon.id,
            'coupon_name': coupon_obj.pname,
            'coupon_code': coupon_obj.pcode,
            'bonus_amount': float(bonus_amount),
            'condition_type': condition_type,
            'turnover_requirement': float(member_coupon.req_turnover) if member_coupon.req_turnover else 0,
            'netwin_requirement': float(member_coupon.req_netwin) if member_coupon.req_netwin else 0,
            'claim_time': member_coupon.claim_time.strftime(
                '%Y-%m-%d %H:%M:%S') if member_coupon.claim_time else None,
            'expire_time': member_coupon.expire_time.strftime(
                '%Y-%m-%d %H:%M:%S') if member_coupon.expire_time else None,
            'redeem_method': redeem_type
        }

        # 如果有奖金计算详情，添加到响应中
        if bonus_details:
            response_data['bonus_calculation'] = bonus_details

        return jsonify({
            'code': SUCCESS_CODE,
            'data': response_data,
            'message': f'Coupon redeemed successfully by {redeem_type}. {bonus_msg}'
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': SYSTEM_ERROR_CODE,
            'data': None,
            'message': str(e)
        }), 500


@coupon.route('/history', methods=['GET'])
@auth.login_required
def get_redemption_history():
    """获取用户的优惠券领取历史

    Unused状态：返回可领取的优惠券（MAppCoupon，p_app_hidden=0）
    Used/Expired状态：返回已领取的优惠券历史（MAppMemberCoupon）
    """
    try:
        user_id = g.user.id
        user = g.user
        page = int(request.args.get('page', 1))
        page_size = min(int(request.args.get('page_size', 20)), 100)
        status = request.args.get('status')  # 'Unused', 'Used', 'Expired'
        activity_status = request.args.get('activity_status')  # 活动状态筛选（仅用于Used状态）：Active, Completed, Cancelled, Expired
        start_time = request.args.get('start_time')  # 开始时间
        end_time = request.args.get('end_time')  # 结束时间
        time_type = request.args.get('time_type')  # 时间类型：'use_time' 或 'expire_time'

        # 如果status为'Unused'，查询可领取的优惠券（MAppCoupon）
        if status == 'Unused':
            now = datetime.now()

            # 查询用户正在参与的优惠券活动（同时只能参与一个）
            active_coupon_activity = db.session.query(AppPlayerActivityRecord).filter(
                AppPlayerActivityRecord.mb_id == user_id,
                AppPlayerActivityRecord.activity_type == 'COUPON',
                AppPlayerActivityRecord.status == 'Active',
                AppPlayerActivityRecord.del_flag == 0,
            ).first()

            query = MAppCoupon.query.filter(
                MAppCoupon.del_flag == 0,
                MAppCoupon.p_status == 'Active',
                MAppCoupon.p_app_hidden == 0,  # 只显示app可见的优惠券
                MAppCoupon.tenant_id == '10000',
                MAppCoupon.p_expire >= now,
                or_(MAppCoupon.aid == user.aid,
                    MAppCoupon.fund_source_type == 'HOUSE'),
                or_(
                    MAppCoupon.p_start.is_(None),
                    MAppCoupon.p_start <= now
                ),
                or_(
                    MAppCoupon.p_end.is_(None),
                    MAppCoupon.p_end >= now
                )
            )

            # 排除正在参与活动的优惠券
            if active_coupon_activity:
                query = query.filter(MAppCoupon.id != active_coupon_activity.activity_id)

            # 获取总数
            total_count = query.count()

            # 分页
            offset = (page - 1) * page_size
            coupons = query.order_by(MAppCoupon.create_time.desc()).offset(offset).limit(page_size).all()

            # 格式化返回数据 - 使用MAppCoupon的结构
            history_list = []
            for coupon in coupons:
                # 检查用户已领取次数
                user_claimed_count = MAppMemberCoupon.query.filter(
                    MAppMemberCoupon.mb_id == user_id,
                    MAppMemberCoupon.p_id == coupon.id,
                    MAppMemberCoupon.del_flag == 0
                ).count()
                # 检查是否达到领取上限，如果达到则跳过该优惠券
                usage_limit = coupon.p_lmu_j_tt
                if usage_limit is not None and user_claimed_count >= usage_limit:
                    continue  # 已达到领取上限，不显示该优惠券

                # 检查用户已使用次数
                used_count = MAppMemberCoupon.query.filter(
                    MAppMemberCoupon.mb_id == user_id,
                    MAppMemberCoupon.p_id == coupon.id,
                    # MAppMemberCoupon.status == 'Used',
                    MAppMemberCoupon.del_flag == 0
                ).count()
                # 获取最低投注金额
                min_bet_required = float(
                    coupon.min_bet_amount_required) if coupon and coupon.min_bet_amount_required else None

                history_info = {
                    'id': coupon.id,
                    'coupon_id': coupon.id,
                    'coupon_name': coupon.pname,
                    'min_bet_required': min_bet_required,
                    'bonus_amount': float(coupon.bonus_amount) if coupon.bonus_amount else 0,
                    'turnover_requirement': 0,  # Unused状态不显示流水
                    'turnover_progress': 0,
                    'status': 'Unused',
                    'claim_time': None,
                    'use_time': None,
                    'game_status': None,
                    'start_time': coupon.p_start.strftime('%Y-%m-%d %H:%M:%S') if coupon.p_start else None,
                    'end_time': coupon.p_end.strftime('%Y-%m-%d %H:%M:%S') if coupon.p_end else None,
                    'expire_time': coupon.p_expire.strftime('%Y-%m-%d %H:%M:%S') if coupon.p_expire else None,
                    'used_count': used_count,
                    'usage_limit': usage_limit,
                    'p_code': coupon.p_code,
                    'p_img_mb': coupon.p_img_mb,
                    'p_content': coupon.p_content,
                    'usage_scenario_config': coupon.usage_scenario_config,
                }
                history_list.append(history_info)

            return jsonify({
                'code': SUCCESS_CODE,
                'data': {
                    'history': history_list,
                    'pagination': {
                        'current_page': page,
                        'page_size': page_size,
                        'total_count': total_count,
                        'total_pages': (total_count + page_size - 1) // page_size
                    },
                    'statistics': {
                        'total_redeemed': 0,
                        'total_used': 0,
                        'total_unused': total_count,
                        'total_bonus_amount': 0
                    }
                },
                'message': 'success'
            }), 200

        # 如果status为'Used'或'Expired'，继续使用原来的逻辑查询MAppMemberCoupon
        # 构建查询
        query = MAppMemberCoupon.query.filter(
            MAppMemberCoupon.mb_id == user_id,
            MAppMemberCoupon.del_flag == 0
        )

        # if status is not None:
        #     query = query.filter(MAppMemberCoupon.status == status)

        # Used状态下的筛选：通过AppPlayerActivityRecord进行筛选
        if status == 'Used':
            query = query.filter(MAppMemberCoupon.status != 'Expired')
            # 先构建AppPlayerActivityRecord的查询条件
            activity_query = db.session.query(AppPlayerActivityRecord).filter(
                AppPlayerActivityRecord.mb_id == user_id,
                AppPlayerActivityRecord.activity_type == 'COUPON',
                AppPlayerActivityRecord.del_flag == 0
            )

            # 活动状态筛选
            if activity_status:
                activity_query = activity_query.filter(AppPlayerActivityRecord.status == activity_status)

            # 日期筛选 - 筛选活动开始时间
            if start_time:
                try:
                    start_date = datetime.strptime(start_time, '%Y-%m-%d')
                    activity_query = activity_query.filter(AppPlayerActivityRecord.start_time >= start_date)
                except ValueError:
                    pass

            if end_time:
                try:
                    end_date = datetime.strptime(end_time, '%Y-%m-%d')
                    # 结束日期包含整天，所以加一天
                    end_date = end_date + timedelta(days=1)
                    activity_query = activity_query.filter(AppPlayerActivityRecord.start_time < end_date)
                except ValueError:
                    pass

            # 获取符合条件的活动记录，并提取member_coupon_id
            activities = activity_query.all()
            # member_coupon_ids = []
            # for activity in activities:
            #     if activity.completion_detail:
            #         try:
            #             detail = json.loads(activity.completion_detail)
            #             if 'member_coupon_id' in detail:
            #                 member_coupon_ids.append(detail['member_coupon_id'])
            #         except:
            #             pass
            # 修改为根据AppPlayerActivityRecord的activity_id
            coupon_ids = list({activity.activity_id for activity in activities})

            # 用这些member_coupon_id筛选MAppMemberCoupon
            if coupon_ids:
                query = query.filter(MAppMemberCoupon.p_id.in_(coupon_ids))
            else:
                # 如果没有符合条件的活动，返回空结果
                query = query.filter(MAppMemberCoupon.id == None)

            # 获取总数
            total_count = query.count()

            # 分页
            offset = (page - 1) * page_size
            history = query.order_by(MAppMemberCoupon.claim_time.desc()).offset(offset).limit(page_size).all()

            # 格式化返回数据
            history_list = []
            for h in history:
                # 获取优惠券信息
                coupon_obj = MAppCoupon.query.filter_by(id=h.p_id, del_flag=0).first()

                # 查询使用日期（通过AppBetOrder）
                game_status = None
                bet_order = AppBetOrder.query.filter_by(pro_id=h.id, del_flag=0).order_by(
                    AppBetOrder.create_time.asc()).first()
                if bet_order:
                    game_status = bet_order.game_status if bet_order.game_status else None

                # 统计该优惠券的已使用次数（该用户使用该优惠券类型的次数）
                used_count = MAppMemberCoupon.query.filter(
                    MAppMemberCoupon.mb_id == user_id,
                    MAppMemberCoupon.p_id == h.p_id,
                    MAppMemberCoupon.del_flag == 0
                ).count()

                # 获取总次数限制 p_lmu_j_tt
                usage_limit = coupon_obj.p_lmu_j_tt if coupon_obj and coupon_obj.p_lmu_j_tt else None

                # 获取最低投注金额
                min_bet_required = float(
                    coupon_obj.min_bet_amount_required) if coupon_obj and coupon_obj.min_bet_amount_required else None

                history_info = {
                    'id': h.id,
                    'coupon_id': h.p_id,
                    'coupon_name': h.p_name or (coupon_obj.pname if coupon_obj else 'Unknown'),
                    'bonus_amount': float(h.money) if h.money else 0,
                    'turnover_requirement': float(h.req_turnover) if h.req_turnover else 0,
                    'turnover_progress': float(h.cur_turnover) if h.cur_turnover else 0,
                    'status': h.status,
                    'claim_time': h.claim_time.strftime('%Y-%m-%d %H:%M:%S') if h.claim_time else None,
                    'use_time': h.use_time.strftime('%Y-%m-%d %H:%M:%S') if h.use_time else None,
                    'game_status': game_status,  # 通过投注记录获取的比赛状态
                    'start_time': h.start_time.strftime('%Y-%m-%d %H:%M:%S') if h.start_time else None,
                    'end_time': h.end_time.strftime('%Y-%m-%d %H:%M:%S') if h.end_time else None,
                    'expire_time': h.expire_time.strftime('%Y-%m-%d %H:%M:%S') if h.expire_time else None,
                    'used_count': used_count,  # 该用户已使用该优惠券的次数
                    'usage_limit': usage_limit,  # 总次数限制 p_lmu_j_pd
                    'min_bet_required': min_bet_required,  # 最低投注金额
                    'p_code': coupon_obj.p_code if coupon_obj else None,
                    'p_img_mb': coupon_obj.p_img_mb if coupon_obj else None,
                    'p_content': coupon_obj.p_content if coupon_obj else None,
                    'usage_scenario_config': coupon_obj.usage_scenario_config if coupon_obj else None,
                }
                history_list.append(history_info)
        else:
            # Expired 状态：返回 过期未使用的优惠券(MAppCoupon) + 过期的已领取优惠券(MAppMemberCoupon)
            now = datetime.now()

            # 1. 查询已领取但已过期的 MAppMemberCoupon
            # 条件：过期时间 < 当前时间
            query_claimed = MAppMemberCoupon.query.filter(
                MAppMemberCoupon.mb_id == user_id,
                MAppMemberCoupon.del_flag == 0,
                MAppMemberCoupon.expire_time < now,
                MAppMemberCoupon.status != 'Used'  # 确保未使用的
            )

            if start_time and time_type == 'expire_time':
                try:
                    start_date = datetime.strptime(start_time, '%Y-%m-%d')
                    query_claimed = query_claimed.filter(MAppMemberCoupon.expire_time >= start_date)
                except ValueError:
                    pass

            if end_time and time_type == 'expire_time':
                try:
                    end_date = datetime.strptime(end_time, '%Y-%m-%d')
                    end_date = end_date + timedelta(days=1)
                    query_claimed = query_claimed.filter(MAppMemberCoupon.expire_time < end_date)
                except ValueError:
                    pass

            claimed_list = query_claimed.all()

            # 2. 查询未领取但已过期的 MAppCoupon
            # 先查询用户已领取的优惠券ID集合
            claimed_p_ids = db.session.query(MAppMemberCoupon.p_id).filter(
                MAppMemberCoupon.mb_id == user_id,
                MAppMemberCoupon.del_flag == 0
            ).distinct().all()
            claimed_p_ids = [row[0] for row in claimed_p_ids]

            # 查询过期的优惠券（p_end < now）
            query_unclaimed = MAppCoupon.query.filter(
                MAppCoupon.del_flag == 0,
                MAppCoupon.p_app_hidden == 0,
                MAppCoupon.tenant_id == '10000',
                MAppCoupon.p_end < now,
                MAppCoupon.p_expire < now,
                or_(
                    MAppCoupon.p_end.is_(None),
                    MAppCoupon.p_end < now
                ),
                or_(MAppCoupon.aid == user.aid,
                    MAppCoupon.fund_source_type == 'HOUSE')
            )

            # 排除已领取的
            if claimed_p_ids:
                query_unclaimed = query_unclaimed.filter(MAppCoupon.id.notin_(claimed_p_ids))

            # 时间筛选 (使用 p_end 作为过期时间)
            if start_time and time_type == 'expire_time':
                try:
                    start_date = datetime.strptime(start_time, '%Y-%m-%d')
                    query_unclaimed = query_unclaimed.filter(MAppCoupon.p_end >= start_date)
                except ValueError:
                    pass
            if end_time and time_type == 'expire_time':
                try:
                    end_date = datetime.strptime(end_time, '%Y-%m-%d')
                    end_date = end_date + timedelta(days=1)
                    query_unclaimed = query_unclaimed.filter(MAppCoupon.p_end < end_date)
                except ValueError:
                    pass

            unclaimed_list = query_unclaimed.all()

            # 合并数据
            all_items = []

            # 处理已领取过期的
            for h in claimed_list:
                coupon_obj = MAppCoupon.query.filter_by(id=h.p_id).first()
                usage_limit = coupon_obj.p_lmu_j_tt if coupon_obj and coupon_obj.p_lmu_j_tt else None
                min_bet_required = float(
                    coupon_obj.min_bet_amount_required) if coupon_obj and coupon_obj.min_bet_amount_required else None
                # 检查用户已使用次数

                used_count = MAppMemberCoupon.query.filter(MAppMemberCoupon.p_id == h.p_id,
                                                           MAppMemberCoupon.mb_id == user_id, ).count()
                info = {
                    'id': h.id,
                    'coupon_id': h.p_id,
                    'coupon_name': h.p_name or (coupon_obj.pname if coupon_obj else 'Unknown'),
                    'bonus_amount': float(h.money) if h.money else 0,
                    'turnover_requirement': float(h.req_turnover) if h.req_turnover else 0,
                    'turnover_progress': float(h.cur_turnover) if h.cur_turnover else 0,
                    'status': 'Expired',
                    'claim_time': h.claim_time.strftime('%Y-%m-%d %H:%M:%S') if h.claim_time else None,
                    'use_time': None,
                    'game_status': None,
                    'start_time': h.start_time.strftime('%Y-%m-%d %H:%M:%S') if h.start_time else None,
                    'end_time': h.end_time.strftime('%Y-%m-%d %H:%M:%S') if h.end_time else None,
                    'expire_time': h.expire_time.strftime('%Y-%m-%d %H:%M:%S') if h.expire_time else None,
                    'used_count': used_count,  # 这里不重要
                    'usage_limit': usage_limit,
                    'min_bet_required': min_bet_required,
                    'p_code': coupon_obj.p_code if coupon_obj else None,
                    'p_img_mb': coupon_obj.p_img_mb if coupon_obj else None,
                    'p_content': coupon_obj.p_content if coupon_obj else None,
                    'usage_scenario_config': coupon_obj.usage_scenario_config if coupon_obj else None,
                }
                all_items.append({'time': h.expire_time, 'data': info})

            # 处理未领取过期的
            for c in unclaimed_list:
                min_bet_required = float(c.min_bet_amount_required) if c.min_bet_amount_required else None
                info = {
                    'id': None,  # 未领取，没有member_coupon_id
                    'coupon_id': c.id,
                    'coupon_name': c.pname,
                    'bonus_amount': float(c.bonus_amount) if c.bonus_amount else 0,
                    'turnover_requirement': 0,
                    'turnover_progress': 0,
                    'status': 'Expired',
                    'claim_time': None,
                    'use_time': None,
                    'game_status': None,
                    'start_time': c.p_start.strftime('%Y-%m-%d %H:%M:%S') if c.p_start else None,
                    'end_time': c.p_end.strftime('%Y-%m-%d %H:%M:%S') if c.p_end else None,
                    'expire_time': c.p_end.strftime('%Y-%m-%d %H:%M:%S') if c.p_end else None,  # 使用结束时间作为过期时间
                    'used_count': 0,
                    'usage_limit': c.p_lmu_j_tt,
                    'min_bet_required': min_bet_required,
                    'p_code': c.p_code,
                    'p_img_mb': c.p_img_mb,
                    'p_content': c.p_content,
                    'usage_scenario_config': c.usage_scenario_config,
                }
                all_items.append({'time': c.p_end, 'data': info})

            # 排序：按时间倒序
            all_items.sort(key=lambda x: x['time'] if x['time'] else datetime.min, reverse=True)

            # 分页
            total_count = len(all_items)
            offset = (page - 1) * page_size
            page_items = all_items[offset:offset + page_size]
            history_list = [item['data'] for item in page_items]

        # 统计信息 (保持原逻辑)
        total_redeemed = MAppMemberCoupon.query.filter(
            MAppMemberCoupon.mb_id == user_id,
            MAppMemberCoupon.del_flag == 0
        ).count()

        total_used = MAppMemberCoupon.query.filter(
            MAppMemberCoupon.mb_id == user_id,
            MAppMemberCoupon.status == 1,
            MAppMemberCoupon.del_flag == 0
        ).count()

        total_bonus = db.session.query(func.sum(MAppMemberCoupon.money)).filter(
            MAppMemberCoupon.mb_id == user_id,
            MAppMemberCoupon.del_flag == 0
        ).scalar() or Decimal('0')

        return jsonify({
            'code': SUCCESS_CODE,
            'data': {
                'history': history_list,
                'pagination': {
                    'current_page': page,
                    'page_size': page_size,
                    'total_count': total_count,
                    'total_pages': (total_count + page_size - 1) // page_size if page_size > 0 else 0
                },
                'statistics': {
                    'total_redeemed': total_redeemed,
                    'total_used': total_used,
                    'total_unused': total_redeemed - total_used,
                    'total_bonus_amount': float(total_bonus)
                }
            },
            'message': 'success'
        }), 200

    except Exception as e:
        return jsonify({
            'code': SYSTEM_ERROR_CODE,
            'data': None,
            'message': str(e)
        }), 500


@coupon.route('/progress/<string:coupon_id>', methods=['GET'])
@auth.login_required
def get_coupon_progress(coupon_id):
    """获取用户在特定优惠券的使用进度"""
    try:
        user_id = g.user.id

        # 获取用户的优惠券领取记录
        member_coupon = MAppMemberCoupon.query.filter_by(
            mb_id=user_id,
            p_id=coupon_id,
            del_flag=0
        ).order_by(MAppMemberCoupon.claim_time.desc()).first()

        if not member_coupon:
            return jsonify({
                'code': SUCCESS_CODE,
                'data': {
                    'has_claimed': False,
                    'message': 'Coupon not claimed yet'
                },
                'message': 'success'
            }), 200

        # 获取优惠券信息
        coupon_obj = MAppCoupon.query.filter_by(
            id=coupon_id,
            del_flag=0
        ).first()

        if not coupon_obj:
            return jsonify({
                'code': COUPON_NOT_FOUND_CODE,
                'data': None,
                'message': 'Coupon does not exist'
            }), 404

        # 实时查询流水进度（从 AppBetOrder 统计，使用 claim_time 作为时间下限）
        settled_statuses = [BetStatus.Win, BetStatus.Lose, BetStatus.Draw, BetStatus.HalfWin, BetStatus.HalfLose]
        cur_turnover = Decimal('0')
        cur_netwin = Decimal('0')

        if member_coupon.claim_time:
            cur_turnover = Decimal(str(db.session.query(
                func.coalesce(func.sum(AppBetOrder.stake), 0)
            ).filter(
                AppBetOrder.mb_id == user_id,
                AppBetOrder.pro_id == coupon_id,
                AppBetOrder.create_time >= member_coupon.claim_time,
                AppBetOrder.bet_status.in_(settled_statuses)
            ).scalar()))

            # net_win: 统一使用 netwin_actual
            cur_netwin = Decimal(str(db.session.query(
                func.coalesce(func.sum(AppBetOrder.netwin_actual), 0)
            ).filter(
                AppBetOrder.mb_id == user_id,
                AppBetOrder.pro_id == coupon_id,
                AppBetOrder.create_time >= member_coupon.claim_time,
                AppBetOrder.bet_status.in_(settled_statuses)
            ).scalar()))

        # 计算流水进度百分比
        progress_percentage = 0
        if member_coupon.req_turnover and member_coupon.req_turnover > 0:
            progress_percentage = float(
                (cur_turnover / member_coupon.req_turnover) * 100
            )
            progress_percentage = min(100, progress_percentage)

        # 检查是否已过期
        is_expired = False
        if member_coupon.expire_time:
            is_expired = member_coupon.expire_time < datetime.now()

        return jsonify({
            'code': SUCCESS_CODE,
            'data': {
                'has_claimed': True,
                'coupon_name': member_coupon.p_name or coupon_obj.pname,
                'bonus_amount': float(member_coupon.money) if member_coupon.money else 0,
                'turnover_requirement': float(member_coupon.req_turnover) if member_coupon.req_turnover else 0,
                'turnover_progress': float(cur_turnover),
                'netwin_progress': float(cur_netwin),
                'progress_percentage': progress_percentage,
                'status': member_coupon.status,
                'status_text': 'Used' if member_coupon.status == 1 else 'Unused',
                'can_use': member_coupon.status == 0 and progress_percentage >= 100 and not is_expired,
                'claim_time': member_coupon.claim_time.strftime(
                    '%Y-%m-%d %H:%M:%S') if member_coupon.claim_time else None,
                'use_time': member_coupon.use_time.strftime('%Y-%m-%d %H:%M:%S') if member_coupon.use_time else None,
                'expire_time': member_coupon.expire_time.strftime(
                    '%Y-%m-%d %H:%M:%S') if member_coupon.expire_time else None,
                'is_expired': is_expired
            },
            'message': 'success'
        }), 200

    except Exception as e:
        return jsonify({
            'code': SYSTEM_ERROR_CODE,
            'data': None,
            'message': str(e)
        }), 500


@coupon.route('/available_for_bet', methods=['POST'])
@auth.login_required
def get_available_coupons_for_bet():
    """获取用户可用于下注的优惠券列表

    筛选条件：
    1. status为Unused（未使用）
    2. expire_time未超过当前时间
    3. 根据p_id在m_app_coupon表查询优惠券要求
    4. 满足用户使用次数上限p_lmu_j_pd（每日使用次数）
    5. 满足最低投注金额要求min_bet_amount_required
    """
    try:
        user_id = g.user.id
        data = request.json
        bet_amount = data.get('bet_amount', 0)

        # 将投注金额转换为Decimal以便比较
        bet_amount_decimal = Decimal(str(bet_amount)) if bet_amount else Decimal('0')

        now = datetime.now()

        # 查询用户未使用且未过期的优惠券
        member_coupons = MAppMemberCoupon.query.filter(
            MAppMemberCoupon.mb_id == user_id,
            MAppMemberCoupon.status == 'Unused',
            MAppMemberCoupon.del_flag == 0,
            or_(
                MAppMemberCoupon.expire_time.is_(None),
                MAppMemberCoupon.expire_time > now
            )
        ).all()

        available_coupons = []

        for mc in member_coupons:
            # 获取对应的优惠券配置
            coupon_config = MAppCoupon.query.filter_by(
                id=mc.p_id,
                del_flag=0
            ).first()

            if not coupon_config:
                continue

            # 检查优惠券配置的最低投注金额要求
            # 使用 min_bet_amount_required 字段（使用优惠券所需的最低投注金额）
            min_bet_required = Decimal('0')
            if hasattr(coupon_config, 'min_bet_amount_required') and coupon_config.min_bet_amount_required:
                min_bet_required = Decimal(str(coupon_config.min_bet_amount_required))

            # 检查投注金额是否满足最低要求
            # 如果优惠券要求最低投注金额，但用户投注金额不足，则跳过该优惠券
            if min_bet_required > 0 and bet_amount_decimal < min_bet_required:
                continue

            # 检查总使用次数限制（p_lmu_j_pd）
            if coupon_config.p_lmu_j_pd and coupon_config.p_lmu_j_pd > 0:
                # 统计该用户使用该优惠券的总次数
                total_usage_count = MAppMemberCoupon.query.filter(
                    MAppMemberCoupon.mb_id == user_id,
                    MAppMemberCoupon.p_id == mc.p_id,
                    MAppMemberCoupon.status == 'Used',
                    MAppMemberCoupon.del_flag == 0
                ).count()

                # 如果已经达到使用次数上限，则跳过
                if total_usage_count >= coupon_config.p_lmu_j_pd:
                    continue

            # 构建返回数据
            coupon_info = {
                'member_coupon_id': mc.id,  # 用户优惠券记录ID
                'coupon_id': mc.p_id,  # 优惠券配置ID
                'coupon_name': mc.p_name or (coupon_config.p_name if coupon_config else 'Unknown'),
                'bonus_amount': float(mc.money) if mc.money else 0,
                'min_bet_required': float(min_bet_required),
                'claim_time': mc.claim_time.strftime('%Y-%m-%d %H:%M:%S') if mc.claim_time else None,
                'expire_time': mc.expire_time.strftime('%Y-%m-%d %H:%M:%S') if mc.expire_time else None,
                'turnover_requirement': float(mc.req_turnover) if mc.req_turnover else 0,
                'turnover_progress': float(mc.cur_turnover) if mc.cur_turnover else 0
            }

            available_coupons.append(coupon_info)

        return jsonify({
            'code': SUCCESS_CODE,
            'data': {
                'coupons': available_coupons,
                'total_count': len(available_coupons)
            },
            'message': 'success'
        }), 200

    except Exception as e:
        return jsonify({
            'code': SYSTEM_ERROR_CODE,
            'data': None,
            'message': str(e)
        }), 500


@coupon.route('/current_activity', methods=['GET'])
@auth.login_required
def get_current_coupon_activity():
    """获取用户当前最新的优惠券活动信息"""
    try:
        user_id = g.user.id

        # 获取用户信息
        user = AppMember.query.filter_by(id=user_id, del_flag=0).first()
        if not user:
            return jsonify({
                'code': PARAM_ERROR_CODE,
                'data': None,
                'message': 'User not found'
            }), 404

        # 查询用户最新的一条 COUPON 活动
        activity = AppPlayerActivityRecord.query.filter(
            AppPlayerActivityRecord.mb_id == user_id,
            AppPlayerActivityRecord.activity_type == 'COUPON',
            AppPlayerActivityRecord.del_flag == 0
        ).order_by(AppPlayerActivityRecord.create_time.desc()).first()

        if not activity:
            return jsonify({
                'code': SUCCESS_CODE,
                'data': {
                    'has_activity': False
                },
                'message': 'No coupon activity found'
            }), 200

        # 获取优惠券配置信息
        coupon = MAppCoupon.query.filter_by(
            id=activity.activity_id,
            del_flag=0
        ).first()

        if not coupon:
            return jsonify({
                'code': SUCCESS_CODE,
                'data': {
                    'has_activity': False
                },
                'message': 'Coupon not found'
            }), 200

        # 统计所有已结算的有效投注（Win, Lose, Draw, HalfWin, HalfLose）
        # 排除：Pending（未结算）、Cancel（取消）、Rejected（拒绝）、Refund（退款）
        # 使用 start_time 作为时间下限，确保同一优惠券多次领取时只统计本次领取后的投注
        valid_statuses = [BetStatus.Win, BetStatus.Lose, BetStatus.Draw,
                          BetStatus.HalfWin, BetStatus.HalfLose]
        total_stake = db.session.query(func.sum(AppBetOrder.stake)).filter(
            AppBetOrder.mb_id == user_id,
            AppBetOrder.bet_status.in_(valid_statuses),
            AppBetOrder.pro_id == activity.activity_id,
            AppBetOrder.pay_wallet == 'Promotion',
            AppBetOrder.create_time >= activity.start_time,
        ).scalar() or 0
        # 获取用户领取的优惠券信息（从 completion_detail 中获取 member_coupon_id）
        member_coupon_id = None
        if activity.completion_detail:
            try:
                import json
                detail = json.loads(activity.completion_detail)
                member_coupon_id = detail.get('member_coupon_id')
                # print(member_coupon_id)
                # 统计所有已结算的有效投注（Win, Lose, Draw, HalfWin, HalfLose）
                # 排除：Pending（未结算）、Cancel（取消）、Rejected（拒绝）、Refund（退款）
                # valid_statuses = [BetStatus.Win, BetStatus.Lose, BetStatus.Draw,
                #                   BetStatus.HalfWin, BetStatus.HalfLose]
                # total_stake = db.session.query(func.sum(AppBetOrder.stake)).filter(
                #     AppBetOrder.mb_id == user_id,
                #     AppBetOrder.bet_status.in_(valid_statuses),
                #     AppBetOrder.pro_id == member_coupon_id,
                #     AppBetOrder.pay_wallet == 'Promotion',
                # ).scalar() or 0
            except:
                pass

        # 准备返回数据
        result = {
            'has_activity': True,
            'activity_name': activity.activity_name or coupon.pname,
            'bonus_amount': float(coupon.bonus_amount) if coupon.bonus_amount else 0,
            'deposit_condition': coupon.p_at_ep_cond,  # 参与条件类型
            'deposit_amount': float(coupon.p_min_deposit) if coupon.p_min_deposit else 0,  # 参与条件金额
            'status': activity.status,  # Active, Completed, Cancelled, Expired
            'money_promotion': float(user.money_promotion) if user.money_promotion else 0,
            'total_stake': float(total_stake),
            'activity_id': activity.id,
            'coupon_id': coupon.id,
            'member_coupon_id': member_coupon_id,
            'start_time': activity.start_time.strftime('%Y-%m-%d %H:%M:%S') if activity.start_time else None,
            'end_time': activity.end_time.strftime('%Y-%m-%d %H:%M:%S') if activity.end_time else None,
        }

        return jsonify({
            'code': SUCCESS_CODE,
            'data': result,
            'message': 'success'
        }), 200

    except Exception as e:
        return jsonify({
            'code': SYSTEM_ERROR_CODE,
            'data': None,
            'message': str(e)
        }), 500
