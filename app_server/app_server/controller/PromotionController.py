"""
促销活动 API Controller
提供给 UniApp 移动端使用的促销活动接口

参考 CouponController.py 和 InvitationActivityV2Controller.py 风格
"""

from datetime import datetime, timedelta
from decimal import Decimal
import json

from sqlalchemy import func, and_, or_, case
from flask import g, request, jsonify, Blueprint

from app_server import app, db, auth

# 导入模型
from app_server.model.AppMemberModel import AppMember
from app_server.model.MAppPromotionModel import MAppPromotion
from app_server.model.MAppPromotionParticipationModel import MAppPromotionParticipation
from app_server.model.AppMemberBalanceLogModel import AppMemberBalanceLog, TransactionType, TransactionMap
from app_server.model.AppPlayerActivityRecordModel import AppPlayerActivityRecord
from app_server.model.ChargeModel import Charge
from app_server.model.AppBetOrderModel import AppBetOrder, BetStatus
from app_server.model.AppAgentModel import AppAgent
from app_server.model.AppAgentBalancelogModel import AppAgentBalancelog

from app_server.service.RiskManagementService import RiskManagementService
from app_server.utils.Kits import Kits

# 常量定义
SUCCESS_CODE = 200
SYSTEM_ERROR_CODE = 501
PARAM_ERROR_CODE = 401
PROMOTION_NOT_FOUND_CODE = 402
PROMOTION_NOT_VALID_CODE = 403
ALREADY_PARTICIPATED_CODE = 404
INSUFFICIENT_BALANCE_CODE = 405
CONDITION_NOT_MET_CODE = 406
RISK_CHECK_FAILED_CODE = 407

# 促销活动状态常量
PROMOTION_STATUS_INACTIVE = 'Inactive'  # 未激活
PROMOTION_STATUS_ACTIVE = 'Active'  # 激活
PROMOTION_STATUS_SCHEDULED = 'Scheduled'  # 计划中

# 创建蓝图
promotion = Blueprint('promotion', __name__)


# ==================== 辅助函数 ====================

def is_promotion_valid(promotion):
    """检查促销活动是否有效"""
    if not promotion or promotion.del_flag != 0:
        return False

    # 检查状态是否为激活
    if promotion.status != PROMOTION_STATUS_ACTIVE:
        return False

    # 检查奖金池是否耗尽
    if promotion.is_pool_exhausted == 1:
        return False

    # 检查奖金池余额
    if not promotion.bonus_pool_remaining or promotion.bonus_pool_remaining <= 0:
        return False

    # 检查时间范围
    now = datetime.now()
    if promotion.start_date and now < promotion.start_date:
        return False
    if promotion.end_date and now > promotion.end_date:
        return False

    return True


def check_user_eligibility(user, promotion):
    """检查用户是否符合参与条件"""
    # 检查资金来源权限
    if promotion.fund_source_type == 'AGENT':
        # AGENT类型的促销活动需要会员的aid与促销活动的agent_id匹配
        if not hasattr(user, 'aid') or str(user.aid) != str(promotion.agent_id):
            return False, "You are not authorized to participate in this agent promotion"
    # HOUSE类型的促销活动所有人都可以参与，无需额外检查

    # 检查代理权限（如果有agent_id，则只有该代理下的会员可以参与）
    if promotion.agent_id and promotion.fund_source_type == 'AGENT':
        if not hasattr(user, 'aid') or str(user.aid) != str(promotion.agent_id):
            return False, "You are not authorized to participate in this promotion"

    # 检查注册条件
    if promotion.registration_criteria == 'NEW_USERS':
        # 检查用户是否为新用户（例如：注册7天内）
        if not user.create_time:
            return False, "This promotion is only for new users (registered within 7 days)"
        days_since_registration = (datetime.now() - user.create_time).days
        if days_since_registration > 7:
            return False, "This promotion is only for new users (registered within 7 days)"

    elif promotion.registration_criteria == 'TIME_PERIOD':
        # registration_start_date / registration_end_date 已在后端管理保存时转为系统时间
        # user.create_time 也是系统时间，可直接比较
        if not user.create_time:
            return False, "Registration date is required for this promotion"
        if promotion.registration_start_date and user.create_time < promotion.registration_start_date:
            return False, f"This promotion is only for users registered after {promotion.registration_start_date.strftime('%Y-%m-%d %H:%M:%S')}"
        if promotion.registration_end_date and user.create_time > promotion.registration_end_date:
            return False, f"This promotion is only for users registered before {promotion.registration_end_date.strftime('%Y-%m-%d %H:%M:%S')}"

    return True, "Eligible"


def perform_risk_check(user_id, promotion_id, ip_address=None, device_id=None, user_agent=None):
    """风险检查"""
    try:
        member = AppMember.query.filter_by(id=user_id, del_flag=0).first()
        if not member:
            return False, "User not found"

        if member.status != 1:
            return False, "User account is not active"

        # 使用默认风险配置
        risk_config = {
            'ip_limit_count': 10,
            'ip_time_window_hours': 1,
            'imei_limit_count': 5
        }

        risk_result = RiskManagementService.assess_redemption_risk(
            user_id=user_id,
            coupon_id=promotion_id,  # 复用coupon_id参数
            ip=ip_address or '0.0.0.0',
            imei=device_id,
            user_agent=user_agent,
            location=None,
            coupon_config=risk_config,
            username=member.username
        )

        if not risk_result['allowed']:
            return False, risk_result['reason']

        return True, "Risk check passed"

    except Exception as e:
        print(f"Risk check error: {str(e)}")
        return False, "Risk check failed"


def refund_remaining_to_agent(member, remaining_amount, current_promo_balance, activity_record):
    """
    将促销结算剩余金额退回到代理/平台余额
    参考 Java CouponAutoSettlementService.refundRemainingToAgent()
    
    Args:
        member: 会员对象
        remaining_amount: 需要退回的剩余金额
        current_promo_balance: 当前促销钱包余额（用于流水记录）
        activity_record: 活动记录对象（AppPlayerActivityRecord）
    
    Raises:
        Exception: 如果代理账户不存在或更新失败
    """
    if remaining_amount <= 0:
        return

    # 1. 通过 aid 查询目标账户（代理或 HOUSE）
    agent = AppAgent.query.filter_by(id=member.aid, del_flag=0).first()
    if not agent:
        raise Exception(f"Agent/House account not found with aid: {member.aid}")

    agent_level = agent.agent_lvl if hasattr(agent, 'agent_lvl') else 'AGENT'

    # 2. 更新代理/平台余额
    agent_old_balance = agent.balance if agent.balance else Decimal('0')
    agent_new_balance = agent_old_balance + remaining_amount
    agent.balance = agent_new_balance

    # 3. 生成代理/平台流水记录
    timestamp = int(datetime.now().timestamp() * 1000)
    agent_description = "Promotion settlement remaining amount refund to " + \
                        ("House" if agent_level == "HOUSE" else "Agent")

    agent_balance_log = AppAgentBalancelog(
        id=Kits.generate_uuid(),
        trx_datetime=datetime.now(),
        trx_type="Refund",
        trx_amount=remaining_amount,
        trx_before=agent_old_balance,
        trx_after=agent_new_balance,
        trx_ref_id=activity_record.id,
        trx_note=agent_description,
        trx_status="Success",
        agent_id=agent.id,
        upline_id=agent.upline_id if hasattr(agent, 'upline_id') else None,
        player_id=member.id,
        submit_by="SYSTEM",
        confirm_by="SYSTEM",
        trx_type_sub="PromotionSettlementRefund",
        status=1,
        create_by_id="SYSTEM",
        update_by_id="SYSTEM",
        del_flag=0
    )

    # 4. 生成玩家促销钱包退款流水
    refund_sn = f"PROMO_END_REFUND_{activity_record.id}_{timestamp}"
    player_description = f"Promotion settlement: remaining amount {float(remaining_amount)} refunded to System"

    balance_log_refund = AppMemberBalanceLog(
        id=Kits.generate_uuid(),
        sn=refund_sn,
        type=TransactionType.Activity,
        type_sub="PromotionRefund",
        type_sub_data_id=activity_record.id,
        mb_id=member.id,
        mb_username=member.username if hasattr(member, 'username') else None,
        money=-remaining_amount,  # 负数表示扣除
        start_balance=current_promo_balance,
        end_balance=Decimal('0'),
        create_by_id=member.id,
        update_by_id=member.id,
        aid=member.aid if hasattr(member, 'aid') else None,
        source="ProWallet",
        target="System",
        pay_wallet="Promotion",
        status=1,
        source_status=0,
        remarks=player_description
    )

    # 5. 保存到数据库
    db.session.add(agent)
    db.session.add(agent_balance_log)
    db.session.add(balance_log_refund)

    print(f"Refunded remaining amount {float(remaining_amount)} to {agent_level} account {agent.id}")


def calculate_turnover_requirement(promotion, reward_amount):
    """计算流水要求"""
    if not promotion.turnover_multiplier or promotion.turnover_multiplier <= 0:
        return Decimal('0')

    return reward_amount * Decimal(str(promotion.turnover_multiplier))


def should_use_main_wallet(promotion):
    """判断奖励是否直接转入主钱包"""
    # 如果没有流水倍数或流水倍数为0，直接转主钱包
    turnover_multiplier = float(promotion.turnover_multiplier) if promotion.turnover_multiplier else 0
    net_win_amount = float(promotion.net_win_amount) if promotion.net_win_amount else 0

    return turnover_multiplier == 0 and net_win_amount == 0


# ==================== API 接口 ====================

@promotion.route('/test_list', methods=['GET'])
def test_promotion_list():
    """【测试专用】获取促销活动列表（无需认证）"""
    try:
        page = int(request.args.get('page', 1))
        page_size = min(int(request.args.get('page_size', 20)), 100)

        # 查询所有激活的促销活动
        now = datetime.now()
        query = MAppPromotion.query.filter(
            MAppPromotion.del_flag == 0,
            MAppPromotion.status == PROMOTION_STATUS_ACTIVE,
            MAppPromotion.tenant_id == '10000',
            or_(
                MAppPromotion.start_date.is_(None),
                MAppPromotion.start_date <= now
            ),
            or_(
                MAppPromotion.end_date.is_(None),
                MAppPromotion.end_date >= now
            )
        )

        # 获取总数
        total_count = query.count()

        # 分页
        offset = (page - 1) * page_size
        promotions = query.order_by(MAppPromotion.sort.asc(), MAppPromotion.create_time.desc()).offset(offset).limit(
            page_size).all()

        # 格式化返回数据（简化版，不包含用户相关信息）
        promotion_list = []
        for promo in promotions:
            promo_info = {
                'id': promo.id,
                'title': promo.title,
                'slogan': promo.slogan,
                'description': promo.description,
                'image_url': promo.image_url,
                'reward_amount': float(promo.reward_amount) if promo.reward_amount else 0,
                'start_date': promo.start_date.strftime('%Y-%m-%d %H:%M:%S') if promo.start_date else None,
                'end_date': promo.end_date.strftime('%Y-%m-%d %H:%M:%S') if promo.end_date else None,
                'status': promo.status if promo.status else 'Unknown',
                'turnover_multiplier': float(promo.turnover_multiplier) if promo.turnover_multiplier else 0,
                'net_win_amount': float(promo.net_win_amount) if promo.net_win_amount else 0,
                'bonus_pool_remaining': float(promo.bonus_pool_remaining) if promo.bonus_pool_remaining else 0,
                'fund_source_type': promo.fund_source_type if promo.fund_source_type else 'AGENT'
            }
            promotion_list.append(promo_info)

        return jsonify({
            'code': SUCCESS_CODE,
            'data': {
                'promotions': promotion_list,
                'pagination': {
                    'current_page': page,
                    'page_size': page_size,
                    'total_count': total_count,
                    'total_pages': (total_count + page_size - 1) // page_size
                }
            },
            'message': 'success (test mode - no authentication)'
        }), 200

    except Exception as e:
        return jsonify({
            'code': SYSTEM_ERROR_CODE,
            'data': None,
            'message': str(e)
        }), 500


@promotion.route('/list', methods=['GET'])
@auth.login_required
def get_promotion_list():
    """获取可参与的促销活动列表"""
    try:
        user_id = g.user.id
        user = g.user
        page = int(request.args.get('page', 1))
        page_size = min(int(request.args.get('page_size', 20)), 100)

        # 查询所有激活的促销活动
        now = datetime.now()
        query = MAppPromotion.query.filter(
            MAppPromotion.del_flag == 0,
            MAppPromotion.status == PROMOTION_STATUS_ACTIVE,
            MAppPromotion.tenant_id == '10000',
            or_(
                MAppPromotion.start_date.is_(None),
                MAppPromotion.start_date <= now
            ),
            or_(
                MAppPromotion.end_date.is_(None),
                MAppPromotion.end_date >= now
            )
        )

        # 根据资金来源过滤：显示该代理的活动或HOUSE资金来源的活动
        if hasattr(user, 'aid') and user.aid:
            query = query.filter(
                or_(
                    MAppPromotion.agent_id == user.aid,
                    MAppPromotion.fund_source_type == 'HOUSE'
                )
            )

        # 获取总数
        total_count = query.count()

        # 分页
        offset = (page - 1) * page_size
        promotions = query.order_by(MAppPromotion.sort.asc(), MAppPromotion.create_time.desc()).offset(offset).limit(
            page_size).all()

        # 检查用户是否有任何正在参加的活动（不限类型）
        # INVITATION活动如果已完成流水/净赢要求（is_requirement_met=1）则不阻止参与
        _raw_active = AppPlayerActivityRecord.query.filter(
            AppPlayerActivityRecord.mb_id == user_id,
            AppPlayerActivityRecord.del_flag == 0,
            AppPlayerActivityRecord.status == 'Active'
        ).all()
        has_any_active = next(
            (_act for _act in _raw_active
             if not (_act.activity_type == 'INVITATION' and _act.is_requirement_met == 1)),
            None
        )

        # 格式化返回数据
        promotion_list = []
        for promo in promotions:
            # 复用 has_any_active：如果正是当前活动则作为 existing_activity
            if has_any_active and has_any_active.activity_type == 'PROMOTION' and has_any_active.activity_id == promo.id:
                existing_activity = has_any_active
            else:
                existing_activity = None

            # 检查参与次数限制
            participation_limit_reached = False
            participation_frequency = promo.participation_frequency if promo.participation_frequency else 'Daily'
            max_per_user = promo.max_participations_per_user if promo.max_participations_per_user else 0
            
            if max_per_user > 0 or participation_frequency == 'Once':
                # 计算时间范围
                if participation_frequency == 'Daily':
                    period_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
                    period_end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
                    limit_value = max_per_user
                elif participation_frequency == 'Weekly':
                    weekday = now.weekday()
                    period_start = (now - timedelta(days=weekday)).replace(hour=0, minute=0, second=0, microsecond=0)
                    period_end = (period_start + timedelta(days=6)).replace(hour=23, minute=59, second=59, microsecond=999999)
                    limit_value = max_per_user
                elif participation_frequency == 'Monthly':
                    period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                    if now.month == 12:
                        next_month = now.replace(year=now.year + 1, month=1, day=1)
                    else:
                        next_month = now.replace(month=now.month + 1, day=1)
                    period_end = (next_month - timedelta(seconds=1))
                    limit_value = max_per_user
                elif participation_frequency == 'Once':
                    period_start = None
                    period_end = None
                    limit_value = 1
                else:
                    period_start = None
                    period_end = None
                    limit_value = max_per_user
                
                # 统计该时间段内的参与次数
                participation_query = AppPlayerActivityRecord.query.filter(
                    AppPlayerActivityRecord.mb_id == user_id,
                    AppPlayerActivityRecord.activity_type == 'PROMOTION',
                    AppPlayerActivityRecord.activity_id == promo.id,
                    AppPlayerActivityRecord.del_flag == 0
                )
                
                if period_start and period_end:
                    participation_query = participation_query.filter(
                        AppPlayerActivityRecord.create_time >= period_start,
                        AppPlayerActivityRecord.create_time <= period_end
                    )
                
                participation_count = participation_query.count()
                
                # 判断是否达到限制
                if participation_count >= limit_value:
                    participation_limit_reached = True

            # 检查资格
            eligible, eligible_msg = check_user_eligibility(user, promo)

            # 参与金额相关字段 - 根据模式返回正确的值
            if promo.participation_amount_type == 'Fixed':
                # Fixed 模式：min_amount 和 max_amount 都使用 participation_amount
                participation_amt = float(promo.participation_amount) if promo.participation_amount else 0
                min_amt = participation_amt
                max_amt = float(promo.reward_amount) if promo.reward_amount else 0  # max 显示奖励金额（PA → PDA）
            else:
                # Range 模式：使用 min 和 max 字段
                min_amt = float(promo.min_participation_amount) if promo.min_participation_amount else 0
                max_amt = float(promo.max_participation_amount) if promo.max_participation_amount else 0

            # 根据参与次数限制调整状态显示
            # 若用户当前正在参与该活动，即使达到次数上限也不显示 Completed
            display_status = 'Completed' if (participation_limit_reached and not existing_activity) else (promo.status if promo.status else 'Unknown')
            
            promo_info = {
                'id': promo.id,
                'title': promo.title,
                'slogan': promo.slogan,
                'description': promo.description,
                'image_url': promo.image_url,
                'reward_amount': float(promo.reward_amount) if promo.reward_amount else 0,
                'start_date': promo.start_date.strftime('%Y-%m-%d %H:%M:%S') if promo.start_date else None,
                'end_date': promo.end_date.strftime('%Y-%m-%d %H:%M:%S') if promo.end_date else None,
                'status': display_status,
                'turnover_multiplier': float(promo.turnover_multiplier) if promo.turnover_multiplier else 0,
                'net_win_amount': float(promo.net_win_amount) if promo.net_win_amount else 0,
                'bonus_pool_remaining': float(promo.bonus_pool_remaining) if promo.bonus_pool_remaining else 0,
                'fund_source_type': promo.fund_source_type if promo.fund_source_type else 'AGENT',
                'is_participated': existing_activity is not None,
                'participation_status': existing_activity.status if existing_activity else None,
                'can_participate': eligible and not existing_activity and not has_any_active and not participation_limit_reached,
                'message': eligible_msg if not eligible else (
                    'Participation limit reached' if participation_limit_reached else (
                        'Already participated' if existing_activity else (
                            'You already have an active activity' if has_any_active else 'Available'))),
                # 参与金额相关字段
                'participation_amount_type': promo.participation_amount_type if promo.participation_amount_type else 'Fixed',
                'min_amount': min_amt,
                'max_amount': max_amt,
                'participation_amount': float(promo.participation_amount) if promo.participation_amount else 0,
                'reward_mode': promo.reward_amount_type if promo.reward_amount_type else 'Fixed',
                'reward_percentage': 0,  # 目前模型中没有这个字段，暂时设为0
                # 使用场景配置
                'usage_scenario_config': promo.usage_scenario_config if promo.usage_scenario_config else None,
                # 最大提现限额
                'max_withdrawal_limit': float(promo.max_withdrawal_amount) if promo.max_withdrawal_amount else 0,
                # 手动结束相关
                'manual_end_enabled': promo.manual_end_enabled or 0,
                'manual_end_min_amount': float(promo.manual_end_min_amount) if promo.manual_end_min_amount else 0
            }

            # 如果已参与，增加进度信息
            if existing_activity:
                # 计算流水进度百分比
                turnover_percentage = 0
                if existing_activity.req_turnover and existing_activity.req_turnover > 0:
                    turnover_percentage = min(100, float(
                        (existing_activity.cur_turnover / existing_activity.req_turnover) * 100))

                # 计算净赢进度百分比
                netwin_percentage = 0
                if existing_activity.req_netwin and existing_activity.req_netwin > 0:
                    netwin_percentage = min(100,
                                            float((existing_activity.cur_netwin / existing_activity.req_netwin) * 100))

                # 检查是否过期
                is_expired = False
                if existing_activity.end_time:
                    is_expired = existing_activity.end_time < datetime.now()

                # 检查是否完成
                is_completed = existing_activity.status == 'Completed'
                if not is_completed and not is_expired:
                    # 检查是否满足条件
                    if existing_activity.req_turnover > 0:
                        is_completed = existing_activity.cur_turnover >= existing_activity.req_turnover
                    elif existing_activity.req_netwin > 0:
                        is_completed = existing_activity.cur_netwin >= existing_activity.req_netwin

                # 判断是否可以结束促销：默认不可结束
                can_end = False
                if promo.manual_end_enabled:
                    promo_balance = float(user.money_promotion) if user.money_promotion else 0
                    min_end_amt = float(promo.manual_end_min_amount) if promo.manual_end_min_amount else 0

                    # 条件1：余额低于阈值
                    balance_condition_met = promo_balance <= min_end_amt

                    # 条件2：流水和净赢达标
                    turnover_met = turnover_percentage >= 100 or not (
                            existing_activity.req_turnover and existing_activity.req_turnover > 0)
                    netwin_met = netwin_percentage >= 100 or not (
                            existing_activity.req_netwin and existing_activity.req_netwin > 0)
                    requirements_met = turnover_met and netwin_met

                    # 只要满足其中一个条件即可
                    can_end = balance_condition_met or requirements_met

                # 添加进度信息
                promo_info['progress'] = {
                    'target_wallet': 'Promotion',
                    'turnover_requirement': float(
                        existing_activity.req_turnover) if existing_activity.req_turnover else 0,
                    'turnover_progress': float(existing_activity.cur_turnover) if existing_activity.cur_turnover else 0,
                    'turnover_percentage': turnover_percentage,
                    'netwin_requirement': float(existing_activity.req_netwin) if existing_activity.req_netwin else 0,
                    'netwin_progress': float(existing_activity.cur_netwin) if existing_activity.cur_netwin else 0,
                    'netwin_percentage': netwin_percentage,
                    'is_completed': is_completed,
                    'is_expired': is_expired,
                    'can_end': can_end,
                    'participation_time': existing_activity.start_time.strftime(
                        '%Y-%m-%d %H:%M:%S') if existing_activity.start_time else None,
                    'completion_time': existing_activity.end_time.strftime(
                        '%Y-%m-%d %H:%M:%S') if existing_activity.end_time else None,
                    'expire_time': existing_activity.end_time.strftime(
                        '%Y-%m-%d %H:%M:%S') if existing_activity.end_time else None
                }
            else:
                promo_info['progress'] = None

            promotion_list.append(promo_info)

        return jsonify({
            'code': SUCCESS_CODE,
            'data': {
                'promotions': promotion_list,
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


@promotion.route('/detail/<string:promotion_id>', methods=['GET'])
@auth.login_required
def get_promotion_detail(promotion_id):
    """获取促销活动详情"""
    try:
        user_id = g.user.id
        user = g.user

        # 获取促销活动
        promotion_obj = MAppPromotion.query.filter_by(
            id=promotion_id,
            del_flag=0,
            tenant_id='10000'
        ).first()

        if not promotion_obj:
            return jsonify({
                'code': PROMOTION_NOT_FOUND_CODE,
                'data': None,
                'message': 'Promotion does not exist'
            }), 404

        # 检查用户参与记录（使用AppPlayerActivityRecord表）
        existing_activity = AppPlayerActivityRecord.query.filter(
            AppPlayerActivityRecord.mb_id == user_id,
            AppPlayerActivityRecord.activity_type == 'PROMOTION',
            AppPlayerActivityRecord.activity_id == promotion_id,
            AppPlayerActivityRecord.del_flag == 0
        ).first()

        # 检查资格
        eligible, eligible_msg = check_user_eligibility(user, promotion_obj)

        # 状态映射
        status_map = {
            PROMOTION_STATUS_INACTIVE: 'INACTIVE',
            PROMOTION_STATUS_ACTIVE: 'ACTIVE',
            PROMOTION_STATUS_SCHEDULED: 'SCHEDULED'
        }

        detail = {
            'id': promotion_obj.id,
            'title': promotion_obj.title,
            'slogan': promotion_obj.slogan,
            'description': promotion_obj.description,
            'image_url': promotion_obj.image_url,
            'reward_amount': float(promotion_obj.reward_amount) if promotion_obj.reward_amount else 0,
            'start_date': promotion_obj.start_date.strftime('%Y-%m-%d %H:%M:%S') if promotion_obj.start_date else None,
            'end_date': promotion_obj.end_date.strftime('%Y-%m-%d %H:%M:%S') if promotion_obj.end_date else None,
            'status': status_map.get(promotion_obj.status, 'UNKNOWN'),
            'turnover_multiplier': float(promotion_obj.turnover_multiplier) if promotion_obj.turnover_multiplier else 0,
            'net_win_amount': float(promotion_obj.net_win_amount) if promotion_obj.net_win_amount else 0,
            'payout_limit': float(promotion_obj.payout_limit) if promotion_obj.payout_limit else 0,
            'bonus_pool_remaining': float(
                promotion_obj.bonus_pool_remaining) if promotion_obj.bonus_pool_remaining else 0,
            'fund_source_type': promotion_obj.fund_source_type if promotion_obj.fund_source_type else 'AGENT',
            'is_participated': existing_activity is not None,
            'can_participate': eligible and not existing_activity and is_promotion_valid(promotion_obj),
            'eligibility_message': eligible_msg
        }

        return jsonify({
            'code': SUCCESS_CODE,
            'data': detail,
            'message': 'success'
        }), 200

    except Exception as e:
        return jsonify({
            'code': SYSTEM_ERROR_CODE,
            'data': None,
            'message': str(e)
        }), 500


@promotion.route('/participate', methods=['POST'])
@auth.login_required
def participate_promotion():
    """参与促销活动"""
    try:
        user_id = g.user.id
        user = g.user
        data = request.json
        promotion_id = data.get('promotion_id')

        if not promotion_id:
            return jsonify({
                'code': PARAM_ERROR_CODE,
                'data': None,
                'message': 'Promotion ID is required'
            }), 400

        # 获取促销活动（加锁）
        promotion_obj = db.session.query(MAppPromotion).filter(
            MAppPromotion.id == promotion_id,
            MAppPromotion.del_flag == 0,
            MAppPromotion.tenant_id == '10000'
        ).with_for_update().first()

        if not promotion_obj:
            return jsonify({
                'code': PROMOTION_NOT_FOUND_CODE,
                'data': None,
                'message': 'Promotion does not exist'
            }), 404

        # 验证活动是否有效
        if not is_promotion_valid(promotion_obj):
            return jsonify({
                'code': PROMOTION_NOT_VALID_CODE,
                'data': None,
                'message': 'Promotion is not valid or has ended'
            }), 400

        # ==================== 互斥检查：检查是否有进行中的活动 ====================
        # 一次性查询所有活跃活动
        active_activities = AppPlayerActivityRecord.query.filter(
            AppPlayerActivityRecord.mb_id == user_id,
            AppPlayerActivityRecord.status == 'Active',
            AppPlayerActivityRecord.del_flag == 0
        ).all()

        for activity in active_activities:
            if activity.activity_type == 'PROMOTION':
                return jsonify({
                    'code': ALREADY_PARTICIPATED_CODE,
                    'data': None,
                    'message': 'You have an active promotion activity. Please complete or cancel it before joining another promotion.'
                }), 400
            elif activity.activity_type == 'COUPON':
                return jsonify({
                    'code': ALREADY_PARTICIPATED_CODE,
                    'data': None,
                    'message': 'You have an active coupon activity. Please complete or cancel it before joining a promotion.'
                }), 400
            elif activity.activity_type == 'INVITATION':
                # 邀请活动：未达标 + 促销钱包>0 才阻止；促销钱包=0 放行
                if activity.is_requirement_met != 1:
                    promotion_balance = Decimal(str(user.money_promotion or 0))
                    if promotion_balance > Decimal('0'):
                        return jsonify({
                            'code': ALREADY_PARTICIPATED_CODE,
                            'data': None,
                            'message': 'You have an active invitation activity with unmet requirements and remaining promotion balance. Please complete it before joining a promotion.'
                        }), 400

        # 检查用户资格（包括资金来源权限）
        eligible, eligible_msg = check_user_eligibility(user, promotion_obj)
        if not eligible:
            return jsonify({
                'code': CONDITION_NOT_MET_CODE,
                'data': None,
                'message': eligible_msg
            }), 400

        # 风险检查
        ip_address = request.remote_addr
        user_agent = request.headers.get('User-Agent')
        device_id = (request.headers.get('X-Device-ID') or
                     request.headers.get('Device-ID') or
                     request.headers.get('X-Device-IMEI') or
                     request.headers.get('IMEI'))

        risk_check, risk_msg = perform_risk_check(user_id, promotion_id, ip_address, device_id, user_agent)
        if not risk_check:
            return jsonify({
                'code': RISK_CHECK_FAILED_CODE,
                'data': None,
                'message': risk_msg
            }), 400

        # ==================== 检查参与次数限制 ====================
        # 1. 检查活动总参与次数限制
        max_total = promotion_obj.max_total_participations if promotion_obj.max_total_participations else 0
        current_total = promotion_obj.current_total_participations if promotion_obj.current_total_participations else 0

        if max_total > 0 and current_total >= max_total:
            return jsonify({
                'code': CONDITION_NOT_MET_CODE,
                'data': None,
                'message': f'Promotion has reached maximum total participations ({max_total})'
            }), 400

        # 2. 检查用户参与频率限制
        participation_frequency = promotion_obj.participation_frequency if promotion_obj.participation_frequency else 'Daily'
        max_per_user = promotion_obj.max_participations_per_user if promotion_obj.max_participations_per_user else 0

        if max_per_user > 0 or participation_frequency == 'Once':
            # 计算时间范围
            now = datetime.now()
            if participation_frequency == 'Daily':
                # 每天：从今天 00:00:00 到 23:59:59
                period_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
                period_end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
                limit_value = max_per_user
                period_name = 'daily'
            elif participation_frequency == 'Weekly':
                # 每周：从本周一到本周日
                weekday = now.weekday()  # 0=Monday, 6=Sunday
                period_start = (now - timedelta(days=weekday)).replace(hour=0, minute=0, second=0, microsecond=0)
                period_end = (period_start + timedelta(days=6)).replace(hour=23, minute=59, second=59, microsecond=999999)
                limit_value = max_per_user
                period_name = 'weekly'
            elif participation_frequency == 'Monthly':
                # 每月：从本月1号到本月最后一天
                period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                # 下月第一天减1秒
                if now.month == 12:
                    next_month = now.replace(year=now.year + 1, month=1, day=1)
                else:
                    next_month = now.replace(month=now.month + 1, day=1)
                period_end = (next_month - timedelta(seconds=1))
                limit_value = max_per_user
                period_name = 'monthly'
            else:  # Once
                # 仅一次：检查所有时间
                period_start = None
                period_end = None
                limit_value = 1
                period_name = 'all time'

            # 查询用户在周期内的参与次数
            query = MAppPromotionParticipation.query.filter(
                MAppPromotionParticipation.mb_id == user_id,
                MAppPromotionParticipation.promotion_id == promotion_id,
                MAppPromotionParticipation.del_flag == 0
            )

            if period_start and period_end:
                query = query.filter(
                    MAppPromotionParticipation.participation_time >= period_start,
                    MAppPromotionParticipation.participation_time <= period_end
                )

            user_period_count = query.count()

            if user_period_count >= limit_value:
                return jsonify({
                    'code': CONDITION_NOT_MET_CODE,
                    'data': None,
                    'message': f'You have reached the {period_name} participation limit ({limit_value} times)'
                }), 400

        # ==================== 1. 处理参与金额 ====================
        participation_amount_type = promotion_obj.participation_amount_type or 'Fixed'
        user_participation_amount = Decimal('0')

        if participation_amount_type == 'Fixed':
            # 固定金额模式：直接使用配置的参与金额
            user_participation_amount = promotion_obj.participation_amount if promotion_obj.participation_amount else Decimal(
                '0')
        elif participation_amount_type == 'Range':
            # 范围金额模式：用户需要输入金额
            input_amount = data.get('participation_amount')
            if not input_amount:
                return jsonify({
                    'code': PARAM_ERROR_CODE,
                    'data': None,
                    'message': 'Participation amount is required for Range type promotion'
                }), 400

            try:
                user_participation_amount = Decimal(str(input_amount))
            except:
                return jsonify({
                    'code': PARAM_ERROR_CODE,
                    'data': None,
                    'message': 'Invalid participation amount'
                }), 400

            # 验证金额是否在范围内
            min_amount = promotion_obj.min_participation_amount if promotion_obj.min_participation_amount else Decimal(
                '0')
            max_amount = promotion_obj.max_participation_amount if promotion_obj.max_participation_amount else Decimal(
                '999999')

            if user_participation_amount < min_amount or user_participation_amount > max_amount:
                return jsonify({
                    'code': PARAM_ERROR_CODE,
                    'data': None,
                    'message': f'Participation amount must be between {float(min_amount)} and {float(max_amount)}'
                }), 400

        # ==================== 2. 计算奖励金额 ====================
        reward_amount_type = promotion_obj.reward_amount_type or 'Fixed'
        reward_amount = Decimal('0')

        if reward_amount_type == 'Fixed':
            # 固定金额奖励
            reward_amount = promotion_obj.reward_amount if promotion_obj.reward_amount else Decimal('0')
        elif reward_amount_type == 'Percent':
            # 百分比奖励：按参与金额的百分比计算
            reward_percentage = promotion_obj.reward_amount if promotion_obj.reward_amount else Decimal('0')
            reward_amount = user_participation_amount * (reward_percentage / Decimal('100'))

        # ==================== 3. 检查奖金池余额 ====================
        if promotion_obj.bonus_pool_remaining < reward_amount:
            return jsonify({
                'code': INSUFFICIENT_BALANCE_CODE,
                'data': None,
                'message': 'Insufficient bonus pool balance'
            }), 400

        # 扣除奖金池余额
        promotion_obj.bonus_pool_remaining -= reward_amount

        # 更新已使用金额
        current_used_amount = promotion_obj.used_amount if promotion_obj.used_amount else Decimal('0')
        promotion_obj.used_amount = current_used_amount + reward_amount

        # 更新总参与次数
        current_participations = promotion_obj.current_total_participations if promotion_obj.current_total_participations else 0
        promotion_obj.current_total_participations = current_participations + 1

        # 检查活动是否需要结束（奖金池耗尽或达到总参与次数上限）
        max_total = promotion_obj.max_total_participations if promotion_obj.max_total_participations else 0
        if promotion_obj.bonus_pool_remaining <= 0:
            promotion_obj.is_pool_exhausted = 1
            promotion_obj.status = PROMOTION_STATUS_INACTIVE
        elif max_total > 0 and promotion_obj.current_total_participations >= max_total:
            promotion_obj.status = PROMOTION_STATUS_INACTIVE

        # 获取会员信息（加锁）
        member = db.session.query(AppMember).filter(
            AppMember.id == user_id
        ).with_for_update().first()

        if not member:
            return jsonify({
                'code': PARAM_ERROR_CODE,
                'data': None,
                'message': 'Member not found'
            }), 400

        # ==================== 4. 检查主钱包余额 ====================
        main_wallet_balance = member.money if member.money else Decimal('0')
        if main_wallet_balance < user_participation_amount:
            return jsonify({
                'code': INSUFFICIENT_BALANCE_CODE,
                'data': None,
                'message': f'Insufficient main wallet balance. Required: {float(user_participation_amount)}, Available: {float(main_wallet_balance)}'
            }), 400

        # ==================== 5. 计算流水/净赢要求 ====================
        # 流水要求基于 PA + PDA（本金 + 奖励金额）
        req_turnover = calculate_turnover_requirement(promotion_obj, user_participation_amount + reward_amount)
        req_netwin = Decimal(str(promotion_obj.net_win_amount)) if promotion_obj.net_win_amount else Decimal('0')

        # ==================== 6. 更新会员余额 ====================
        now = datetime.now()

        # 从主钱包扣除参与金额（PA）
        old_main_balance = member.money if member.money else Decimal('0')
        new_main_balance = old_main_balance - user_participation_amount
        member.money = new_main_balance

        # 计算促销钱包入账金额：PA + PDA（新需求算法1）
        total_promo_amount = user_participation_amount + reward_amount

        # 将总金额（PA + PDA）加到促销钱包
        old_promo_balance = member.money_promotion if member.money_promotion else Decimal('0')
        new_promo_balance = old_promo_balance + total_promo_amount
        member.money_promotion = new_promo_balance

        # Add principal to member's accumulated current turnover
        # 参与promotion的时候把本金加到member的累积当前流水里
        if user_participation_amount > 0:
            member.current_turnover_accumulated = (member.current_turnover_accumulated or Decimal(
                '0')) + user_participation_amount

        target_wallet = "Promotion"

        # 创建参与记录
        participation_id = Kits.generate_uuid()
        participation = MAppPromotionParticipation(
            id=participation_id,
            promotion_id=promotion_id,
            mb_id=user_id,
            mb_username=member.username if hasattr(member, 'username') else None,
            agent_id=user.aid if hasattr(user, 'aid') else None,
            reward_amount=reward_amount,
            bonus_type='PROMOTION',
            req_turnover=req_turnover,
            req_netwin=req_netwin,
            cur_turnover=Decimal('0'),
            cur_netwin=Decimal('0'),
            status='Active',
            participation_time=now,
            expire_time=promotion_obj.end_date,
            mb_ip=ip_address,
            device_id=device_id,
            target_wallet=target_wallet,
            create_time=now,
            create_by_id=user_id,
            del_flag=0,
            tenant_id='10000'
        )

        # ==================== 7. 记录余额流水 ====================
        # 流水1：从主钱包扣除参与金额（PA）
        balance_log_deduct = AppMemberBalanceLog(
            id=Kits.generate_uuid(),
            sn=f"PROMO_DEDUCT_{participation_id}",
            type=TransactionType.Activity,
            type_sub=TransactionType.PromotionParticipation,
            type_sub_data_id=participation_id,
            mb_id=user_id,
            mb_username=member.username if hasattr(member, 'username') else None,
            money=-user_participation_amount,  # 负数表示扣除（PA）
            start_balance=old_main_balance,
            end_balance=new_main_balance,
            create_by_id=user_id,
            update_by_id=user_id,
            aid=user.aid if hasattr(user, 'aid') else None,
            source="MainWallet",
            target=TransactionMap.ProWallet,
            pay_wallet="Money",
            status=1,
            source_status=0
        )

        # 流水2：向促销钱包加入总金额（PA + PDA）
        balance_log_add = AppMemberBalanceLog(
            id=Kits.generate_uuid(),
            sn=f"PROMO_ADD_{participation_id}",
            type=TransactionType.Activity,
            type_sub=TransactionType.PromotionReward,
            type_sub_data_id=participation_id,
            mb_id=user_id,
            mb_username=member.username if hasattr(member, 'username') else None,
            money=total_promo_amount,  # PA + PDA（新需求算法1）
            start_balance=old_promo_balance,
            end_balance=new_promo_balance,
            create_by_id=user_id,
            update_by_id=user_id,
            aid=user.aid if hasattr(user, 'aid') else None,
            source="System",
            target=TransactionMap.ProWallet,
            pay_wallet="Promotion",
            status=1,
            source_status=0,
            remarks=f"Participation amount: {float(user_participation_amount)}, Reward amount: {float(reward_amount)}"
        )

        # ==================== 8. 创建活动参与记录 ====================
        condition_text = f'Turnover: {float(req_turnover)}' if req_turnover > 0 else (
            f'Net Win: {float(req_netwin)}' if req_netwin > 0 else 'No requirement')
        condition_detail = {
            'participation_id': participation_id,
            'participation_amount': float(user_participation_amount),
            'reward_amount': float(reward_amount),
            'total_promo_amount': float(total_promo_amount),  # PA + PDA
            'condition_type': 'Turnover' if req_turnover > 0 else ('Net Win' if req_netwin > 0 else 'None'),
            'turnover_required': float(req_turnover),
            'netwin_required': float(req_netwin)
        }

        # 判断是否有流水要求
        has_requirement = req_turnover > 0 or req_netwin > 0

        activity_record = AppPlayerActivityRecord(
            id=Kits.generate_uuid(),
            mb_id=user_id,
            aid=promotion_obj.agent_id,
            username=member.username if hasattr(member, 'username') else None,
            activity_type='PROMOTION',
            activity_id=promotion_id,
            activity_name=promotion_obj.title,
            status='Active' if has_requirement else 'Completed',
            start_time=now,
            completion_condition=condition_text,
            completion_detail=json.dumps(condition_detail),
            req_turnover=req_turnover,
            req_netwin=req_netwin,
            bonus_amount=reward_amount,  # ⚠️ 关键：设置奖励金额（用于取消时的退款分配）
            is_requirement_met=0 if has_requirement else 1,
            create_time=now,
            create_by_id=user_id,
            del_flag=0,
            tenant_id='10000'
        )

        # ==================== 9. 保存所有更改 ====================
        db.session.add(participation)
        db.session.add(promotion_obj)
        db.session.add(member)
        db.session.add(balance_log_deduct)  # 扣除主钱包流水
        db.session.add(balance_log_add)  # 增加促销钱包流水
        db.session.add(activity_record)
        db.session.commit()

        # 记录成功的参与尝试
        RiskManagementService.record_redemption_attempt(
            user_id=user_id,
            coupon_id=promotion_id,
            ip=ip_address,
            imei=device_id,
            successful=True
        )

        response_data = {
            'participation_id': participation_id,
            'promotion_title': promotion_obj.title,
            'participation_amount': float(user_participation_amount),
            'reward_amount': float(reward_amount),
            'total_promo_amount': float(total_promo_amount),  # PA + PDA
            'target_wallet': target_wallet,
            'turnover_requirement': float(req_turnover),
            'netwin_requirement': float(req_netwin),
            'participation_time': participation.participation_time.strftime('%Y-%m-%d %H:%M:%S'),
            'expire_time': participation.expire_time.strftime(
                '%Y-%m-%d %H:%M:%S') if participation.expire_time else None,
            'main_wallet_balance': float(new_main_balance),
            'promo_wallet_balance': float(new_promo_balance)
        }

        return jsonify({
            'code': SUCCESS_CODE,
            'data': response_data,
            'message': f'Successfully participated! Deducted {float(user_participation_amount)} (PA) from Main Wallet, Added {float(total_promo_amount)} (PA+PDA) to Promotion Wallet.'
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': SYSTEM_ERROR_CODE,
            'data': None,
            'message': str(e)
        }), 500


@promotion.route('/progress/<string:promotion_id>', methods=['GET'])
@auth.login_required
def get_promotion_progress(promotion_id):
    """获取用户在促销活动中的进度"""
    try:
        user_id = g.user.id
        user = g.user

        # 获取参与记录（使用AppPlayerActivityRecord表）
        activity_record = AppPlayerActivityRecord.query.filter(
            AppPlayerActivityRecord.mb_id == user_id,
            AppPlayerActivityRecord.activity_type == 'PROMOTION',
            AppPlayerActivityRecord.activity_id == promotion_id,
            AppPlayerActivityRecord.del_flag == 0,
            AppPlayerActivityRecord.status == 'Active',
        ).first()

        if not activity_record:
            return jsonify({
                'code': SUCCESS_CODE,
                'data': {
                    'has_participated': False,
                    'message': 'You have not participated in this promotion yet'
                },
                'message': 'success'
            }), 200

        # 获取促销活动信息
        promotion_obj = MAppPromotion.query.filter_by(
            id=promotion_id,
            del_flag=0
        ).first()

        if not promotion_obj:
            return jsonify({
                'code': PROMOTION_NOT_FOUND_CODE,
                'data': None,
                'message': 'Promotion does not exist'
            }), 404

        # 从 m_app_bet_order 统计已结算订单的流水和净赢（未结算不计入）
        # 使用 start_time 作为时间下限，确保同一 Promotion 多次参与时只统计本次参与后的投注
        settled_statuses = [BetStatus.Win, BetStatus.Lose, BetStatus.Draw, BetStatus.HalfWin, BetStatus.HalfLose]
        cur_turnover = Decimal(str(db.session.query(
            func.coalesce(func.sum(AppBetOrder.stake), 0)
        ).filter(
            AppBetOrder.mb_id == user_id,
            AppBetOrder.pro_id == promotion_id,
            AppBetOrder.create_time >= activity_record.start_time,
            AppBetOrder.bet_status.in_(settled_statuses)
        ).scalar()))

        # 净赢只统计赢的订单
        cur_netwin = user.money_promotion if user.money_promotion else Decimal('0')

        # 计算进度百分比
        turnover_percentage = 0
        netwin_percentage = 0

        if activity_record.req_turnover and activity_record.req_turnover > 0:
            turnover_percentage = min(100, float((cur_turnover / activity_record.req_turnover) * 100))

        if activity_record.req_netwin and activity_record.req_netwin > 0:
            netwin_percentage = min(100, float((cur_netwin / activity_record.req_netwin) * 100))

        # 检查是否已过期
        is_expired = False
        if activity_record.end_time:
            is_expired = activity_record.end_time < datetime.now()

        # 检查是否已完成
        is_completed = activity_record.status == 'Completed'
        if not is_completed and not is_expired:
            # 检查是否满足条件（基于实时统计）
            if activity_record.req_turnover > 0:
                is_completed = cur_turnover >= activity_record.req_turnover
            elif activity_record.req_netwin > 0:
                is_completed = cur_netwin >= activity_record.req_netwin

        # 判断是否可以结束促销：默认不可结束
        can_end = False
        user = g.user
        if promotion_obj.manual_end_enabled:
            promo_balance = float(user.money_promotion) if user.money_promotion else 0
            min_end_amt = float(promotion_obj.manual_end_min_amount) if promotion_obj.manual_end_min_amount else 0

            # 条件1：余额低于阈值
            balance_condition_met = promo_balance <= min_end_amt

            # 条件2：流水和净赢达标
            turnover_met = turnover_percentage >= 100 or not (
                    activity_record.req_turnover and activity_record.req_turnover > 0)
            netwin_met = netwin_percentage >= 100 or not (activity_record.req_netwin and activity_record.req_netwin > 0)
            requirements_met = turnover_met and netwin_met

            # 只要满足其中一个条件即可
            can_end = balance_condition_met or requirements_met

        progress_data = {
            'has_participated': True,
            'promotion_title': promotion_obj.title,
            'reward_amount': float(promotion_obj.reward_amount) if promotion_obj.reward_amount else 0,
            'target_wallet': 'Promotion',
            'status': activity_record.status,
            'turnover_requirement': float(activity_record.req_turnover) if activity_record.req_turnover else 0,
            'turnover_progress': float(cur_turnover),
            'turnover_percentage': turnover_percentage,
            'netwin_requirement': float(activity_record.req_netwin) if activity_record.req_netwin else 0,
            'netwin_progress': float(cur_netwin),
            'netwin_percentage': netwin_percentage,
            'is_completed': is_completed,
            'is_expired': is_expired,
            'can_end': can_end,
            'max_withdrawal_limit': float(
                promotion_obj.max_withdrawal_amount) if promotion_obj.max_withdrawal_amount else 0,
            'participation_time': activity_record.start_time.strftime(
                '%Y-%m-%d %H:%M:%S') if activity_record.start_time else None,
            'completion_time': activity_record.end_time.strftime(
                '%Y-%m-%d %H:%M:%S') if activity_record.end_time else None,
            'expire_time': activity_record.end_time.strftime('%Y-%m-%d %H:%M:%S') if activity_record.end_time else None
        }

        return jsonify({
            'code': SUCCESS_CODE,
            'data': progress_data,
            'message': 'success'
        }), 200

    except Exception as e:
        return jsonify({
            'code': SYSTEM_ERROR_CODE,
            'data': None,
            'message': str(e)
        }), 500


@promotion.route('/my_promotions', methods=['GET'])
@auth.login_required
def get_my_promotions():
    """获取用户参与的促销活动列表"""
    try:
        user_id = g.user.id
        page = int(request.args.get('page', 1))
        page_size = min(int(request.args.get('page_size', 20)), 100)
        status = request.args.get('status')  # 'Active', 'Completed', 'Expired', 'Cancelled'

        # 构建查询（使用AppPlayerActivityRecord表）
        query = AppPlayerActivityRecord.query.filter(
            AppPlayerActivityRecord.mb_id == user_id,
            AppPlayerActivityRecord.activity_type == 'PROMOTION',
            AppPlayerActivityRecord.del_flag == 0
        )

        if status:
            query = query.filter(AppPlayerActivityRecord.status == status)

        # 获取总数
        total_count = query.count()

        # 分页
        offset = (page - 1) * page_size
        activities = query.order_by(AppPlayerActivityRecord.start_time.desc()).offset(offset).limit(page_size).all()

        # 格式化返回数据
        participation_list = []
        for activity in activities:
            # 获取促销活动信息
            promotion_obj = MAppPromotion.query.filter_by(id=activity.activity_id, del_flag=0).first()

            # 计算进度
            turnover_percentage = 0
            if activity.req_turnover and activity.req_turnover > 0:
                turnover_percentage = min(100, float((activity.cur_turnover / activity.req_turnover) * 100))

            part_info = {
                'id': activity.id,
                'promotion_id': activity.activity_id,
                'promotion_title': activity.activity_name if activity.activity_name else (
                    promotion_obj.title if promotion_obj else 'Unknown'),
                'promotion_image': promotion_obj.image_url if promotion_obj else None,
                'reward_amount': float(
                    promotion_obj.reward_amount) if promotion_obj and promotion_obj.reward_amount else 0,
                'target_wallet': 'Promotion',
                'status': activity.status,
                'turnover_requirement': float(activity.req_turnover) if activity.req_turnover else 0,
                'turnover_progress': float(activity.cur_turnover) if activity.cur_turnover else 0,
                'turnover_percentage': turnover_percentage,
                'participation_time': activity.start_time.strftime(
                    '%Y-%m-%d %H:%M:%S') if activity.start_time else None,
                'completion_time': activity.end_time.strftime('%Y-%m-%d %H:%M:%S') if activity.end_time else None,
                'expire_time': activity.end_time.strftime('%Y-%m-%d %H:%M:%S') if activity.end_time else None
            }
            participation_list.append(part_info)

        return jsonify({
            'code': SUCCESS_CODE,
            'data': {
                'participations': participation_list,
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


@promotion.route('/current_activity', methods=['GET'])
@auth.login_required
def get_current_promotion_activity():
    """获取用户当前最新的促销活动信息"""
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

        # 查询用户最新的一条 PROMOTION 活动
        activity = AppPlayerActivityRecord.query.filter(
            AppPlayerActivityRecord.mb_id == user_id,
            AppPlayerActivityRecord.activity_type == 'PROMOTION',
            AppPlayerActivityRecord.del_flag == 0
        ).order_by(AppPlayerActivityRecord.create_time.desc()).first()

        if not activity:
            return jsonify({
                'code': SUCCESS_CODE,
                'data': {
                    'has_activity': False
                },
                'message': 'No promotion activity found'
            }), 200

        # 获取促销活动配置信息
        promotion = MAppPromotion.query.filter_by(
            id=activity.activity_id,
            del_flag=0
        ).first()

        if not promotion:
            return jsonify({
                'code': SUCCESS_CODE,
                'data': {
                    'has_activity': False
                },
                'message': 'Promotion not found'
            }), 200

        # 获取参与记录
        participation = MAppPromotionParticipation.query.filter_by(
            mb_id=user_id,
            promotion_id=activity.activity_id,
            del_flag=0
        ).first()

        # 统计投注金额
        # ✅ 修正：排除 Draw 状态，与 Coupon 模块保持一致
        # Draw（平局）通常视为投注无效，不应计入有效流水
        valid_statuses = [BetStatus.Win, BetStatus.Lose, BetStatus.HalfWin, BetStatus.HalfLose]
        total_stake = db.session.query(func.sum(AppBetOrder.stake)).filter(
            AppBetOrder.mb_id == user_id,
            AppBetOrder.bet_status.in_(valid_statuses),
            AppBetOrder.pro_id == activity.activity_id,
            AppBetOrder.pay_wallet == 'Promotion',
        ).scalar() or 0

        result = {
            'has_activity': True,
            'activity_name': activity.activity_name or promotion.title,
            'reward_amount': float(promotion.reward_amount) if promotion.reward_amount else 0,
            'status': activity.status,
            'money_promotion': float(user.money_promotion) if user.money_promotion else 0,
            'total_stake': float(total_stake),
            'turnover_requirement': float(
                participation.req_turnover) if participation and participation.req_turnover else 0,
            'turnover_progress': float(
                participation.cur_turnover) if participation and participation.cur_turnover else 0,
            'activity_id': activity.id,
            'promotion_id': promotion.id,
            'participation_id': participation.id if participation else None,
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


@promotion.route('/end', methods=['POST'])
@auth.login_required
def end_promotion():
    """结束促销活动并将促销钱包余额转入主钱包"""
    try:
        user_id = g.user.id
        user = g.user
        data = request.json
        promotion_id = data.get('promotion_id')

        if not promotion_id:
            return jsonify({
                'code': PARAM_ERROR_CODE,
                'data': None,
                'message': 'Promotion ID is required'
            }), 400

        # 获取活动记录（使用AppPlayerActivityRecord表，加锁）
        activity_record = db.session.query(AppPlayerActivityRecord).filter(
            AppPlayerActivityRecord.mb_id == user_id,
            AppPlayerActivityRecord.activity_type == 'PROMOTION',
            AppPlayerActivityRecord.activity_id == promotion_id,
            AppPlayerActivityRecord.del_flag == 0,
            AppPlayerActivityRecord.status == PROMOTION_STATUS_ACTIVE,
        ).with_for_update().first()

        if not activity_record:
            return jsonify({
                'code': PARAM_ERROR_CODE,
                'data': None,
                'message': 'You have not participated in this promotion'
            }), 400

        # 检查状态
        if activity_record.status == 'Completed':
            return jsonify({
                'code': CONDITION_NOT_MET_CODE,
                'data': None,
                'message': 'Promotion has already been completed'
            }), 400

        if activity_record.status == 'Cancelled':
            return jsonify({
                'code': CONDITION_NOT_MET_CODE,
                'data': None,
                'message': 'Promotion has been cancelled'
            }), 400

        # 获取促销活动信息
        promotion_obj = MAppPromotion.query.filter_by(
            id=promotion_id,
            del_flag=0
        ).first()

        if not promotion_obj:
            return jsonify({
                'code': PROMOTION_NOT_FOUND_CODE,
                'data': None,
                'message': 'Promotion does not exist'
            }), 404
        if not promotion_obj.manual_end_enabled or not promotion_obj.manual_end_min_amount:
            return jsonify({
                'code': CONDITION_NOT_MET_CODE,
                'data': None,
                'message': f'The current promotion cannot be manually ended.'
            }), 400
        # ==================== 0. 检查促销钱包余额 ====================
        # 获取会员信息（加锁）
        member = db.session.query(AppMember).filter(
            AppMember.id == user_id
        ).with_for_update().first()
        if not member:
            return jsonify({
                'code': PARAM_ERROR_CODE,
                'data': None,
                'message': 'Member not found'
            }), 400
        promo_balance = member.money_promotion if member.money_promotion else Decimal('0')

        # ==================== 1. 实时查询流水和净赢（与 get_promotion_progress 一致） ====================
        # 使用 start_time 作为时间下限，确保同一 Promotion 多次参与时只统计本次参与后的投注
        settled_statuses = [BetStatus.Win, BetStatus.Lose, BetStatus.Draw, BetStatus.HalfWin, BetStatus.HalfLose]
        cur_turnover = Decimal(str(db.session.query(
            func.coalesce(func.sum(AppBetOrder.stake), 0)
        ).filter(
            AppBetOrder.mb_id == user_id,
            AppBetOrder.pro_id == promotion_id,
            AppBetOrder.create_time >= activity_record.start_time,
            AppBetOrder.bet_status.in_(settled_statuses)
        ).scalar()))

        win_statuses = [BetStatus.Win, BetStatus.HalfWin]
        cur_netwin = member.money_promotion if member.money_promotion else Decimal('0')

        # 检查条件是否满足
        # 逻辑：
        # 1. 如果促销钱包余额 <= 最小结束金额，则允许结束（输光了）
        # 2. 否则，必须满足所有流水/净赢要求才能结束

        balance_condition_met = False
        requirements_met = True
        unmet_conditions = []

        # 检查条件1：余额是否低于阈值
        if promotion_obj.manual_end_min_amount is not None and promo_balance <= promotion_obj.manual_end_min_amount:
            balance_condition_met = True

        # 检查条件2：是否满足流水/净赢要求
        if activity_record.req_turnover and activity_record.req_turnover > 0:
            if cur_turnover < activity_record.req_turnover:
                requirements_met = False
                remaining_turnover = activity_record.req_turnover - cur_turnover
                unmet_conditions.append(
                    f'Turnover requirement not met. Required: {float(activity_record.req_turnover)}, Current: {float(cur_turnover)}, Remaining: {float(remaining_turnover)}')

        if activity_record.req_netwin and activity_record.req_netwin > 0:
            if cur_netwin < activity_record.req_netwin:
                requirements_met = False
                remaining_netwin = activity_record.req_netwin - cur_netwin
                unmet_conditions.append(
                    f'Net win requirement not met. Required: {float(activity_record.req_netwin)}, Current: {float(cur_netwin)}, Remaining: {float(remaining_netwin)}')

        # 综合判断：只要满足其中一个条件即可
        if not balance_condition_met and not requirements_met:
            return jsonify({
                'code': CONDITION_NOT_MET_CODE,
                'data': {
                    'unmet_conditions': unmet_conditions
                },
                'message': 'Promotion conditions not met. ' + '; '.join(unmet_conditions)
            }), 400

        # ==================== 2. 检查是否有未结算订单 ====================
        pending_count = db.session.query(AppBetOrder).filter(
            AppBetOrder.mb_id == user_id,
            AppBetOrder.activity_record_id == activity_record.id,
            AppBetOrder.bet_status == BetStatus.Pending,
            AppBetOrder.del_flag == 0
        ).count()
        if pending_count > 0:
            return jsonify({
                'code': CONDITION_NOT_MET_CODE,
                'data': None,
                'message': f'You have {pending_count} unsettled bet order(s). Please wait for settlement before ending the promotion.'
            }), 400

        # 如果余额 <= 0，直接拒绝（但如果是输光的情况，上面 logic 会允许通过 balance_condition_met，这里需要再次确认是否有余额可转）
        # if promo_balance <= 0:
        #      return jsonify({
        #         'code': INSUFFICIENT_BALANCE_CODE,
        #         'data': None,
        #         'message': 'Promotion wallet balance is zero or negative'
        #     }), 400

        # ==================== 3. 计算转移金额 ====================
        # 优先退还活动奖励金额给代理，多余部分再给玩家
        # 使用 activity_record.bonus_amount，因为如果是百分比奖励，promotion_obj.reward_amount 只是百分比数值
        reward_amount = Decimal(str(activity_record.bonus_amount)) if activity_record.bonus_amount else Decimal('0')
        max_withdrawal = None
        if promotion_obj.max_withdrawal_amount and promotion_obj.max_withdrawal_amount > 0:
            max_withdrawal = Decimal(str(promotion_obj.max_withdrawal_amount))

        # Step 1: 优先退还活动金额给代理
        agent_refund = min(reward_amount, promo_balance)

        # Step 2: 计算玩家可得的盈余
        player_surplus = promo_balance - agent_refund

        # Step 3: 玩家盈余受 max_withdrawal 限制
        if max_withdrawal and player_surplus > max_withdrawal:
            transfer_amount = max_withdrawal
        else:
            transfer_amount = player_surplus

        # Step 4: 超出 max_withdrawal 的盈余也退还给代理
        excess = player_surplus - transfer_amount
        remaining_amount = agent_refund + excess

        # ==================== 4. 更新会员余额 ====================
        now = datetime.now()

        # 从促销钱包扣除（全额清空）
        old_promo_balance = member.money_promotion if member.money_promotion else Decimal('0')
        new_promo_balance = Decimal('0')  # 始终清零促销钱包
        member.money_promotion = new_promo_balance

        # 转入主钱包（只转入限额内金额）
        old_main_balance = member.money if member.money else Decimal('0')
        new_main_balance = old_main_balance + transfer_amount
        member.money = new_main_balance
        if requirements_met:
            member.money_promotion_withdrawable += transfer_amount
        else:
            member.required_turnover_accumulated += transfer_amount
        # ==================== 5. 更新活动记录 ====================
        activity_record.status = 'Completed'
        activity_record.end_time = now
        activity_record.update_time = now
        activity_record.end_time = now
        activity_record.is_requirement_met = 1
        activity_record.update_time = now

        # ==================== 7. 创建余额流水记录 ====================
        # 流水1：从促销钱包扣除（转入主钱包部分）
        balance_log_deduct = AppMemberBalanceLog(
            id=Kits.generate_uuid(),
            sn=f"PROMO_END_DEDUCT_{activity_record.id}",
            type=TransactionType.Activity,
            type_sub=TransactionType.PromotionComplete,
            type_sub_data_id=activity_record.id,
            mb_id=user_id,
            mb_username=member.username if hasattr(member, 'username') else None,
            money=-transfer_amount,  # 负数表示扣除（转入主钱包的金额）
            start_balance=old_promo_balance,
            end_balance=old_promo_balance - transfer_amount,  # 可能还有剩余（待退回代理）
            create_by_id=user_id,
            update_by_id=user_id,
            aid=user.aid if hasattr(user, 'aid') else None,
            source="ProWallet",
            target=TransactionMap.Ewallet,
            pay_wallet="Promotion",
            status=1,
            source_status=0
        )

        # 流水2：转入主钱包
        balance_log_add = AppMemberBalanceLog(
            id=Kits.generate_uuid(),
            sn=f"PROMO_END_ADD_{activity_record.id}",
            type=TransactionType.Activity,
            type_sub=TransactionType.PromotionComplete,
            type_sub_data_id=activity_record.id,
            mb_id=user_id,
            mb_username=member.username if hasattr(member, 'username') else None,
            money=transfer_amount,
            start_balance=old_main_balance,
            end_balance=new_main_balance,
            create_by_id=user_id,
            update_by_id=user_id,
            aid=user.aid if hasattr(user, 'aid') else None,
            source="ProWallet",
            target=TransactionMap.Ewallet,
            pay_wallet="Money",
            status=1,
            source_status=0
        )

        # ==================== 8. 处理剩余金额退回（新增）====================
        # 如果有超出限额的剩余金额，退回给代理/平台
        if remaining_amount > 0:
            refund_remaining_to_agent(member, remaining_amount, old_promo_balance, activity_record)

        # ==================== 9. 保存所有更改 ====================
        db.session.add(activity_record)
        db.session.add(member)
        db.session.add(balance_log_deduct)
        db.session.add(balance_log_add)
        db.session.commit()

        # 准备返回数据
        response_data = {
            'activity_id': activity_record.id,
            'promotion_title': promotion_obj.title,
            'transfer_amount': float(transfer_amount),
            'max_withdrawal': float(max_withdrawal) if max_withdrawal else None,
            'agent_refund': float(remaining_amount),
            'old_promo_balance': float(old_promo_balance),
            'new_promo_balance': 0.0,
            'old_main_balance': float(old_main_balance),
            'new_main_balance': float(new_main_balance),
        }

        # 构建成功消息（包含退回提示）
        success_message = f'Promotion completed successfully! Transferred {float(transfer_amount)} from Promotion Wallet to Main Wallet.'
        if remaining_amount > 0:
            success_message += f' Note: {float(remaining_amount)} was refunded to the system.'

        return jsonify({
            'code': SUCCESS_CODE,
            'data': response_data,
            'message': success_message
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': SYSTEM_ERROR_CODE,
            'data': None,
            'message': str(e)
        }), 500
