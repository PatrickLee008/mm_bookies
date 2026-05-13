"""
邀请活动 v2.0 API Controller
提供给 UniApp 移动端使用的邀请活动接口

支持 4 种邀请奖励方法：
- Method 1: 邀请/成就奖励（基于规则阶梯）
- Method 2: 存款分享（被邀请人存款时给奖励）
- Method 3: 邀请人佣金（基于流水或输赢）
- Method 4: 被邀请人投注返佣（被邀请人自己获得返佣）

参考 CouponController.py 风格重构
"""

from datetime import datetime, timedelta
from decimal import Decimal
import json

from sqlalchemy import func, and_, or_, false, case
from flask import g, request, jsonify, Blueprint

from app_server import app, db, auth

# 导入模型
from app_server.model.AppMemberModel import AppMember
from app_server.model.MAppInvitationActivityModel import MAppInvitationActivity
from app_server.model.MAppInvitationAchievementModel import MAppInvitationAchievement, AchievementType
from app_server.model.MAppInvitationDepositShareModel import MAppInvitationDepositShare
from app_server.model.MAppCommissionRecordModel import MAppCommissionRecord
from app_server.model.MAppInvitationRewardModel import MAppInvitationReward
from app_server.model.AppMemberBalanceLogModel import AppMemberBalanceLog, TransactionType, TransactionMap
from app_server.model.AppPlayerActivityRecordModel import AppPlayerActivityRecord
from app_server.model.MAppMemberCouponModel import MAppMemberCoupon
from app_server.model.ChargeModel import Charge
from app_server.model.AppBetOrderModel import AppBetOrder, BetStatus
from app_server.model.MAppPromotionRelationModel import MAppPromotionRelation

from app_server.service.RiskManagementService import RiskManagementService
from app_server.utils.Kits import Kits

# 常量定义（与 CouponController 保持一致）
SUCCESS_CODE = 200
SYSTEM_ERROR_CODE = 501
PARAM_ERROR_CODE = 401
ACTIVITY_NOT_FOUND_CODE = 402
ACTIVITY_NOT_VALID_CODE = 403
ALREADY_CLAIMED_CODE = 404
INSUFFICIENT_BALANCE_CODE = 405
CONDITION_NOT_MET_CODE = 406
RISK_CHECK_FAILED_CODE = 407

# 创建蓝图
invitation_v2 = Blueprint('invitation_v2', __name__)


# ==================== 辅助函数 ====================

def ensure_serializable(obj):
    """递归确保对象中所有 Decimal 类型都转换为 float"""
    if isinstance(obj, dict):
        return {key: ensure_serializable(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [ensure_serializable(item) for item in obj]
    elif isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, datetime):
        return obj.strftime('%Y-%m-%d %H:%M:%S')
    elif isinstance(obj, bool):
        return bool(obj)
    else:
        return obj


def is_activity_valid(activity):
    """检查活动是否有效（参考 CouponController.is_coupon_valid）"""
    if not activity or activity.del_flag != 0:
        return False

    # 检查是否激活和关闭状态
    if activity.is_closed == 1 or activity.status == 0:
        return False

    # 检查奖金池是否耗尽
    if hasattr(activity, 'is_pool_exhausted') and activity.is_pool_exhausted == 1:
        return False

    # 检查托管状态：已退款的活动不可参与
    if hasattr(activity, 'escrow_status') and activity.escrow_status == 2:
        return False

    # 检查奖金池余额
    if activity.bonus_pool_remaining is not None and activity.bonus_pool_remaining <= 0:
        return False

    # 检查时间范围
    now = datetime.now()
    if activity.start_date and now < activity.start_date:
        return False
    if activity.end_date and now > activity.end_date:
        return False

    return True


def check_user_agent_access(user, activity):
    """检查用户是否有权限访问该活动（参考 CouponController.check_user_claim_limits）"""
    # HOUSE类型活动所有人都可以访问
    if hasattr(activity, 'fund_source_type') and activity.fund_source_type == 'HOUSE':
        return True

    # AGENT类型活动需要检查用户的aid与活动的agent_id匹配
    if hasattr(activity, 'fund_source_type') and activity.fund_source_type == 'AGENT':
        user_agent_id = user.aid if hasattr(user, 'aid') else None
        if not user_agent_id:
            return False
        return str(user_agent_id) == str(activity.agent_id)

    # 如果没有fund_source_type字段，保持向后兼容：没有agent_id视为HOUSE活动
    if not activity.agent_id:
        return True
    return False


def check_user_claim_limits_for_rule(user_id, activity_id, rule):
    """检查用户是否超过规则的领取限制"""
    if not rule.max_claim_count or rule.max_claim_count <= 0:
        return True, "No claim limit"

    # 统计用户已领取该规则的次数
    claimed_count = MAppInvitationReward.query.filter(
        MAppInvitationReward.mb_id == user_id,
        MAppInvitationReward.activity_id == activity_id,
        MAppInvitationReward.rule_id == rule.id,
        MAppInvitationReward.status.in_(['Claimed', 'Pending']),
        MAppInvitationReward.del_flag == 0
    ).count()

    if claimed_count >= rule.max_claim_count:
        return False, f"Claim limit reached: {rule.max_claim_count}"

    return True, "Within claim limits"


def should_use_main_wallet(activity, user_id=None):
    """
    判断奖励是否应该直接转入主钱包

    规则：
    1. 如果玩家已经完成该活动的流水要求并结算 → 主钱包
    2. 如果选择了 Turnover：turnover_multiplier = 0 时 → 主钱包
    3. 如果选择了 Net Win：net_win_amount = 0 时 → 主钱包
    4. 其他情况 → 促销钱包

    注意：净赢要求只使用固定值 net_win_amount，不考虑倍数
    注意：只会选择 Turnover 或 Net Win 其中之一，不会同时使用两者

    Args:
        activity: 活动对象
        user_id: 用户ID（用于检查是否已完成结算）

    Returns:
        bool: True = 主钱包, False = 促销钱包
    """
    # 检查玩家是否已经达到该活动的流水/净赢要求
    if user_id:
        met_record = AppPlayerActivityRecord.query.filter_by(
            mb_id=user_id,
            activity_id=activity.id,
            activity_type='INVITATION',
            is_requirement_met=1,
            del_flag=0
        ).first()

        if met_record:
            # 玩家已达标，后续奖励直接转主钱包
            return True

    withdrawal_type = activity.withdrawal_requirement_type if hasattr(activity,
                                                                      'withdrawal_requirement_type') else 'turnover'

    # 获取流水倍数
    turnover_multiplier = float(activity.turnover_multiplier) if hasattr(activity,
                                                                         'turnover_multiplier') and activity.turnover_multiplier else 0

    # 获取净赢要求（只使用固定值）
    net_win_amount = float(activity.net_win_amount) if hasattr(activity,
                                                               'net_win_amount') and activity.net_win_amount else 0

    if withdrawal_type == 'Net Win':
        # 检查净赢要求（固定值）
        return net_win_amount == 0
    else:
        # 默认检查流水要求（包括 'Turnover' 和 None）
        return turnover_multiplier == 0


def check_coupon_invitation_exclusion(user_id, activity):
    """
    检查优惠券和邀请活动的互斥条件

    规则：
    - 如果玩家有进行中的优惠券活动（状态为Active），不能领取有流水/净赢要求的邀请活动奖励
    - 如果邀请活动没有流水/净赢要求（会进主钱包），则不受限制

    Args:
        user_id: 用户ID
        activity: 邀请活动对象

    Returns:
        tuple: (bool, str) - (是否通过检查, 错误消息)
    """
    # 检查该邀请活动是否有流水/净赢要求
    # 如果会转入主钱包，说明没有流水/净赢要求，不需要检查互斥
    use_main_wallet = should_use_main_wallet(activity, user_id)
    if use_main_wallet:
        return True, None

    # 检查是否有进行中的优惠券活动（使用 AppPlayerActivityRecord 表）
    active_coupon_activity = AppPlayerActivityRecord.query.filter(
        AppPlayerActivityRecord.mb_id == user_id,
        AppPlayerActivityRecord.activity_type.in_(['COUPON', 'PROMOTION']),
        AppPlayerActivityRecord.status == 'Active',
        AppPlayerActivityRecord.del_flag == 0
    ).first()

    if active_coupon_activity:
        return False, f'You have an active coupon activity ({active_coupon_activity.activity_name}). Please complete or cancel it before claiming invitation rewards with turnover/net win requirements.'

    return True, None


def perform_risk_check(user_id, activity_id, activity_obj, ip_address=None, device_id=None, user_agent=None):
    """使用RiskManagementService进行风险检查（参考 CouponController）"""
    try:
        member = AppMember.query.filter_by(id=user_id, del_flag=0).first()
        if not member:
            return False, "User not found"

        if member.status != 1:
            return False, "User account is not active"

        # 风险检查配置（使用默认值，可根据活动配置调整）
        config = {
            'ip_limit_count': 10,
            'ip_time_window_hours': 1,
            'imei_limit_count': 5
        }

        risk_result = RiskManagementService.assess_redemption_risk(
            user_id=user_id,
            coupon_id=activity_id,  # 复用优惠券的风险检查
            ip=ip_address or '0.0.0.0',
            imei=device_id,
            user_agent=user_agent,
            location=None,
            coupon_config=config,
            username=member.username
        )

        if not risk_result['allowed']:
            return False, risk_result['reason']

        return True, "Risk check passed"

    except Exception as e:
        print(f"Risk check error: {str(e)}")
        return False, "Risk check failed"


def get_activity_brief_progress(user_id, activity_id, activity):
    """
    获取活动进度信息（用于列表展示和领取操作）
    包含每个规则的详细进度，供用户直接在列表页操作
    保持与旧API相同的字段格式
    """
    try:
        # 统计被邀请人（只统计计入活动奖励的）
        total_invitees = MAppPromotionRelation.query.filter(
            MAppPromotionRelation.promoter_id == user_id,
            MAppPromotionRelation.status == 'Active',
            MAppPromotionRelation.is_counted_in_activity == True,  # 只统计计入活动的
            MAppPromotionRelation.del_flag == 0
        ).count()

        # 统计活动时间段内的被邀请人（只统计计入活动奖励的）
        period_invitees = MAppPromotionRelation.query.join(
            AppMember, MAppPromotionRelation.invitee_id == AppMember.id
        ).filter(
            MAppPromotionRelation.promoter_id == user_id,
            MAppPromotionRelation.status == 'Active',
            MAppPromotionRelation.is_counted_in_activity == True,  # 只统计计入活动的
            MAppPromotionRelation.del_flag == 0,
            AppMember.create_time >= activity.start_date,
            AppMember.create_time <= activity.end_date
        ).count()

        # 获取活动期间的推广关系（用于统计存款和流水）
        promotion_relations = MAppPromotionRelation.query.join(
            AppMember, MAppPromotionRelation.invitee_id == AppMember.id
        ).filter(
            MAppPromotionRelation.promoter_id == user_id,
            MAppPromotionRelation.status == 'Active',
            MAppPromotionRelation.is_counted_in_activity == True,  # 只统计计入活动的
            MAppPromotionRelation.del_flag == 0,
            AppMember.create_time >= activity.start_date,
            AppMember.create_time <= activity.end_date
        ).all()

        total_invitee_deposits = 0
        total_invitee_turnover = 0
        for relation in promotion_relations:
            deposits = db.session.query(func.sum(Charge.amount)).filter(
                Charge.mb_id == relation.invitee_id,
                Charge.status == 'Success',
                Charge.del_flag == 0,
                Charge.create_time >= activity.start_date,
                Charge.create_time <= activity.end_date
            ).scalar() or 0
            total_invitee_deposits += float(deposits)

            turnover = db.session.query(func.sum(AppBetOrder.stake)).filter(
                AppBetOrder.mb_id == relation.invitee_id,
                AppBetOrder.bet_status.in_(
                    [BetStatus.Win, BetStatus.Lose, BetStatus.Draw, BetStatus.HalfWin, BetStatus.HalfLose]),
                AppBetOrder.del_flag == 0,
                AppBetOrder.create_time >= activity.start_date,
                AppBetOrder.create_time <= activity.end_date
            ).scalar() or 0
            total_invitee_turnover += float(turnover)

        # 规则进度列表（Method 1）
        rules_progress = []
        total_claimable = 0

        if hasattr(activity, 'method_invitation_enabled') and activity.method_invitation_enabled == 1:
            rules = MAppInvitationAchievement.query.filter_by(
                activity_id=activity_id,
                del_flag=0
            ).order_by(MAppInvitationAchievement.sequence).all()

            for rule in rules:
                progress = calculate_rule_progress(user_id, activity, rule)

                threshold = float(rule.threshold_value) if rule.threshold_value else 0
                current_value = progress['current_value']
                difference = max(0, threshold - current_value)

                rule_info = {
                    'rule_id': rule.id,
                    'rule_type': rule.rule_type,
                    'description': rule.description,
                    'threshold': threshold,
                    'current_value': current_value,
                    'difference': difference,
                    'reward_amount': float(rule.reward_amount) if rule.reward_amount else 0,
                    'claimed_count': progress['claimed_count'],
                    'max_claim_count': rule.max_claim_count or 0,
                    'can_claim': progress['can_claim'],
                    'is_reached': progress['is_reached'],
                    'available_claims': progress['remaining_claims'],
                    'activity_title': activity.title  # 添加活动标题
                }
                rules_progress.append(rule_info)

                if progress['can_claim']:
                    total_claimable += float(rule.reward_amount) if rule.reward_amount else 0

        # Method 1.2: Invitation Share - One-Time Reward (单次邀请一次性奖励)
        invitation_share_info = None
        # 只有配置了一次性奖励金额才显示
        if hasattr(activity, 'invitation_share_one_time_bonus') and activity.invitation_share_one_time_bonus and float(
                activity.invitation_share_one_time_bonus) > 0:
            # 获取配置
            one_time_bonus = float(activity.invitation_share_one_time_bonus)
            min_deposit = float(activity.invitation_share_min_deposit) if hasattr(activity,
                                                                                  'invitation_share_min_deposit') and activity.invitation_share_min_deposit else 0
            min_turnover = float(activity.invitation_share_min_turnover) if hasattr(activity,
                                                                                    'invitation_share_min_turnover') and activity.invitation_share_min_turnover else 0

            # 查询已领取过的被邀请人 ID（按 referred_id 逐个追踪）
            already_claimed_invitee_ids = set(
                r.referred_id for r in MAppInvitationReward.query.filter(
                    MAppInvitationReward.mb_id == user_id,
                    MAppInvitationReward.activity_id == activity_id,
                    MAppInvitationReward.bonus_type == 'invitation_share_one_time',
                    MAppInvitationReward.status.in_(['Claimed', 'Pending']),
                    MAppInvitationReward.del_flag == 0
                ).all()
                if r.referred_id
            )

            # 统计符合条件的被邀请人数量（只统计计入活动的、且尚未领取过的）
            qualified_invitees = 0
            promotion_relations_share = MAppPromotionRelation.query.join(
                AppMember, MAppPromotionRelation.invitee_id == AppMember.id
            ).filter(
                MAppPromotionRelation.promoter_id == user_id,
                MAppPromotionRelation.status == 'Active',
                MAppPromotionRelation.is_counted_in_activity == True,  # 只统计计入活动的
                MAppPromotionRelation.del_flag == 0,
                AppMember.create_time >= activity.start_date,
                AppMember.create_time <= activity.end_date
            ).all()

            for relation in promotion_relations_share:
                invitee_id = relation.invitee_id
                # 跳过已经领取过的被邀请人
                if invitee_id in already_claimed_invitee_ids:
                    continue
                # 检查存款条件
                if min_deposit > 0:
                    deposits = db.session.query(func.sum(Charge.amount)).filter(
                        Charge.mb_id == invitee_id,
                        Charge.status == 'Success',
                        Charge.del_flag == 0,
                        Charge.create_time >= activity.start_date,
                        Charge.create_time <= activity.end_date
                    ).scalar() or 0
                    if float(deposits) < min_deposit:
                        continue

                # 检查流水条件
                if min_turnover > 0:
                    turnover = db.session.query(func.sum(AppBetOrder.stake)).filter(
                        AppBetOrder.mb_id == invitee_id,
                        AppBetOrder.bet_status.in_(
                            [BetStatus.Win, BetStatus.Lose, BetStatus.Draw, BetStatus.HalfWin, BetStatus.HalfLose]),
                        AppBetOrder.del_flag == 0,
                        AppBetOrder.create_time >= activity.start_date,
                        AppBetOrder.create_time <= activity.end_date
                    ).scalar() or 0
                    if float(turnover) < min_turnover:
                        continue

                qualified_invitees += 1

            # 统计已获得的一次性奖励（历史总额，含已领取的被邀请人）
            one_time_rewards = db.session.query(func.sum(MAppInvitationReward.reward_amount)).filter(
                MAppInvitationReward.activity_id == activity_id,
                MAppInvitationReward.mb_id == user_id,
                MAppInvitationReward.bonus_type == 'invitation_share_one_time',
                MAppInvitationReward.del_flag == 0
            ).scalar() or 0

            has_claimed = len(already_claimed_invitee_ids) > 0
            # 只要有新的符合条件的被邀请人尚未领取，就可以领取
            can_claim = qualified_invitees > 0

            invitation_share_info = {
                'one_time_bonus': one_time_bonus,
                'min_deposit': min_deposit,
                'min_turnover': min_turnover,
                'qualified_invitees': qualified_invitees,
                'total_one_time_rewards': float(one_time_rewards),
                'potential_rewards': qualified_invitees * one_time_bonus,
                'can_claim': can_claim,
                'has_claimed': has_claimed
            }

            # 如果可以领取，将一次性奖励金额加到 total_claimable
            if can_claim:
                total_claimable += qualified_invitees * one_time_bonus

        # Method 2: 存款分享进度
        deposit_share_progress = []
        total_deposit_share_rewards = 0
        total_claimable_deposits = 0
        total_claimable_amount = 0

        if hasattr(activity, 'method_deposit_enabled') and activity.method_deposit_enabled == 1:
            # 获取存款分享规则配置
            deposit_shares = MAppInvitationDepositShare.query.filter_by(
                activity_id=activity_id,
                del_flag=0
            ).order_by(MAppInvitationDepositShare.sequence).all()

            # 获取被邀请人列表（只统计计入活动的）
            promotion_relations_deposit = MAppPromotionRelation.query.join(
                AppMember, MAppPromotionRelation.invitee_id == AppMember.id
            ).filter(
                MAppPromotionRelation.promoter_id == user_id,
                MAppPromotionRelation.status == 'Active',
                MAppPromotionRelation.is_counted_in_activity == True,  # 只统计计入活动的
                MAppPromotionRelation.del_flag == 0,
                AppMember.create_time >= activity.start_date,
                AppMember.create_time <= activity.end_date
            ).all()

            invitee_ids = [rel.invitee_id for rel in promotion_relations_deposit] if promotion_relations_deposit else []

            # 查询所有符合条件的充值记录（用于计算可领取的存款）
            # ✅ 修复：按充值时间升序排序，确保先到先领，claimable金额不会因新充值而变化
            if invitee_ids:
                all_deposits = Charge.query.filter(
                    Charge.mb_id.in_(invitee_ids),
                    Charge.status == 'Success',
                    Charge.del_flag == 0,
                    Charge.create_time >= activity.start_date,
                    Charge.create_time <= activity.end_date
                ).order_by(Charge.create_time.asc()).all()
            else:
                all_deposits = []

            # ✅ 优化1: 在循环外查询一次所有 deposit_share 奖励（提高性能）
            all_deposit_rewards = MAppInvitationReward.query.filter(
                MAppInvitationReward.activity_id == activity_id,
                MAppInvitationReward.mb_id == user_id,
                MAppInvitationReward.bonus_type == 'deposit_share',
                MAppInvitationReward.del_flag == 0
            ).all()

            # ✅ 修复：改为外层遍历充值、内层匹配档位（与领取接口逻辑一致）
            # 预先统计每个档位的已领取次数
            tier_claimed_counts = {}
            for share in deposit_shares:
                tier_rewards = [r for r in all_deposit_rewards if r.rule_id == share.id]
                tier_claimed_counts[share.id] = len(tier_rewards)

            # 已领取的deposit_id集合（用于快速跳过）
            claimed_deposit_ids = set()
            for r in all_deposit_rewards:
                if r.meta_data:
                    try:
                        meta = json.loads(r.meta_data) if isinstance(r.meta_data, str) else r.meta_data
                        did = meta.get('deposit_id')
                        if did:
                            claimed_deposit_ids.add(did)
                    except:
                        if f'"deposit_id": "{r}"' in (r.meta_data or ''):
                            pass

            # ✅ 修复：按充值时间顺序处理，先到先领
            # 临时存储每个档位的进度数据
            tier_progress = {}
            for share in deposit_shares:
                tier_rewards = [r for r in all_deposit_rewards if r.rule_id == share.id]
                max_claims = share.max_claims if hasattr(share, 'max_claims') and share.max_claims is not None else 0
                tier_progress[share.id] = {
                    'share': share,
                    'max_claims': max_claims,
                    'triggered_count': len(tier_rewards),
                    'total_rewards_in_tier': sum(float(r.reward_amount or 0) for r in tier_rewards),
                    'claimable_in_tier': 0,
                    'claimable_amount_in_tier': 0,
                    'can_claim_more': not (max_claims > 0 and len(tier_rewards) >= max_claims)
                }

            # 外层遍历充值（按时间升序），内层匹配档位
            for deposit in all_deposits:
                # 跳过已领取的充值
                if deposit.id in claimed_deposit_ids:
                    continue

                deposit_amount = float(deposit.amount)

                # 匹配存款档位（按sequence顺序）
                for share in deposit_shares:
                    min_dep = float(share.min_deposit) if share.min_deposit else 0
                    max_dep = float(share.max_deposit) if share.max_deposit else float('inf')

                    if min_dep <= deposit_amount <= max_dep:
                        prog = tier_progress[share.id]

                        # 检查是否达到最大领取次数
                        if not prog['can_claim_more']:
                            continue

                        # 检查剩余可领取次数
                        if prog['max_claims'] > 0:
                            remaining = prog['max_claims'] - prog['triggered_count'] - prog['claimable_in_tier']
                            if remaining <= 0:
                                prog['can_claim_more'] = False
                                continue

                        bonus_rate = float(share.bonus_rate) / 100
                        reward_amount = deposit_amount * bonus_rate
                        prog['claimable_in_tier'] += 1
                        prog['claimable_amount_in_tier'] += reward_amount
                        break  # 匹配到档位后不再继续匹配

            # 汇总各档位进度
            for share in deposit_shares:
                prog = tier_progress[share.id]
                total_deposit_share_rewards += prog['total_rewards_in_tier']
                total_claimable_deposits += prog['claimable_in_tier']
                total_claimable_amount += prog['claimable_amount_in_tier']

                custom_description = share.description if hasattr(share, 'description') and share.description else None
                auto_description = f"存款 {float(share.min_deposit or 0)}-{float(share.max_deposit or 0) if share.max_deposit else '以上'}，奖励 {float(share.bonus_rate or 0)}%"

                deposit_share_progress.append({
                    'tier_id': share.id,
                    'min_deposit': float(share.min_deposit) if share.min_deposit else 0,
                    'max_deposit': float(share.max_deposit) if share.max_deposit else None,
                    'bonus_rate': float(share.bonus_rate) if share.bonus_rate else 0,
                    'max_claims': prog['max_claims'],
                    'triggered_count': prog['triggered_count'],
                    'total_rewards': prog['total_rewards_in_tier'],
                    'claimable_count': prog['claimable_in_tier'],
                    'claimable_amount': prog['claimable_amount_in_tier'],
                    'can_claim_more': prog['can_claim_more'],
                    'description': custom_description or auto_description
                })

        # Method 3: 邀请人佣金（基于被邀请人流水/净赢）
        # 注意：这里显示的是"我作为被邀请人，给我的邀请人创造的佣金"
        method3_info = None
        if hasattr(activity, 'method_commission_enabled') and activity.method_commission_enabled == 1:
            # 获取活动的佣金类型并转换为正确的 commission_type
            activity_commission_type = activity.commission_type if hasattr(activity, 'commission_type') else 'turnover'

            # 构建 Method 3 的 sub_type：TURNOVER_COMMISSION 或 WIN_LOSS_COMMISSION
            if activity_commission_type == 'win_loss':
                method3_sub_type = 'WIN_LOSS_COMMISSION'
            else:
                method3_sub_type = 'TURNOVER_COMMISSION'

            # 查询 Method 3 已发放佣金
            method3_paid = db.session.query(func.sum(MAppCommissionRecord.amount)).filter(
                MAppCommissionRecord.activity_id == activity_id,
                MAppCommissionRecord.user_id == user_id,
                MAppCommissionRecord.sub_type == method3_sub_type,
                MAppCommissionRecord.status == 'Paid',
                MAppCommissionRecord.del_flag == 0
            ).scalar() or 0

            if activity_commission_type == 'win_loss':
                # win_loss 类型：结算前无 DB 记录，实时计算当前周期预估佣金
                rt = calculate_win_loss_commission_realtime(user_id, activity)
                method3_info = {
                    'commission_stats': {
                        'pending': float(rt['estimated_amount']),
                        'paid': float(method3_paid),
                        'total': float(rt['estimated_amount']) + float(method3_paid),
                        'estimated': True,
                        'period': rt['period_str'],
                        'invitee_count': rt['invitee_count'],
                        'order_count': rt['order_count'],
                    },
                    'config': {
                        'commission_type': activity_commission_type,
                        'commission_rate': float(activity.commission_rate) if activity.commission_rate else 0
                    }
                }
            else:
                # turnover 类型：从 DB 查 Pending 记录
                method3_pending = db.session.query(func.sum(MAppCommissionRecord.amount)).filter(
                    MAppCommissionRecord.activity_id == activity_id,
                    MAppCommissionRecord.user_id == user_id,
                    MAppCommissionRecord.sub_type == method3_sub_type,
                    MAppCommissionRecord.status == 'Pending',
                    MAppCommissionRecord.del_flag == 0
                ).scalar() or 0

                method3_info = {
                    'commission_stats': {
                        'pending': float(method3_pending),
                        'paid': float(method3_paid),
                        'total': float(method3_pending + method3_paid),
                        'estimated': False,
                    },
                    'config': {
                        'commission_type': activity_commission_type,
                        'commission_rate': float(activity.commission_rate) if activity.commission_rate else 0
                    }
                }

        # Method 4: 被邀请人投注返佣（返佣给被邀请人自己）
        method4_info = None
        if hasattr(activity, 'method_invitee_bet_enabled') and activity.method_invitee_bet_enabled == 1:
            # Method 4 的 sub_type，与 CommissionRecordService._create_invitee_bet_cashback() 保持一致
            method4_sub_type = 'INVITEE_BET_COMMISSION'

            # 查询 Method 4 的返佣（注意：Method 4 是给被邀请人的，所以查询 user_id）
            method4_pending = db.session.query(func.sum(MAppCommissionRecord.amount)).filter(
                MAppCommissionRecord.activity_id == activity_id,
                MAppCommissionRecord.user_id == user_id,  # Method 4: 我作为受益人
                MAppCommissionRecord.sub_type == method4_sub_type,
                MAppCommissionRecord.status == 'Pending',
                MAppCommissionRecord.del_flag == 0
            ).scalar() or 0

            method4_paid = db.session.query(func.sum(MAppCommissionRecord.amount)).filter(
                MAppCommissionRecord.activity_id == activity_id,
                MAppCommissionRecord.user_id == user_id,  # Method 4: 我作为受益人
                MAppCommissionRecord.sub_type == method4_sub_type,
                MAppCommissionRecord.status == 'Paid',
                MAppCommissionRecord.del_flag == 0
            ).scalar() or 0

            method4_info = {
                'commission_stats': {
                    'pending': float(method4_pending),
                    'paid': float(method4_paid),
                    'total': float(method4_pending + method4_paid)
                },
                'config': {
                    'commission_rate': float(activity.invitee_bet_commission_rate) if hasattr(activity,
                                                                                              'invitee_bet_commission_rate') and activity.invitee_bet_commission_rate else 0
                }
            }

        # 已领取的奖励总额
        total_rewards_claimed = db.session.query(func.sum(MAppInvitationReward.reward_amount)).filter(
            MAppInvitationReward.activity_id == activity_id,
            MAppInvitationReward.mb_id == user_id,
            MAppInvitationReward.status == 'Claimed',
            MAppInvitationReward.del_flag == 0
        ).scalar() or 0

        # 返回格式 - 方案 A：按 Method 分组
        result = {
            'activity_id': activity_id,
            'activity_title': activity.title,
            'is_valid': is_activity_valid(activity),

            # Method 1: Invitation/Achievement 邀请奖励
            'method1': {
                'achievement_rules': rules_progress,  # 规则奖励列表
                'invitation_share': invitation_share_info  # 一次性奖励
            },

            # Method 2: Deposit Share 存款分享
            'method2': {
                'deposit_share_tiers': deposit_share_progress,  # 存款分享档位
                'total_rewards': total_deposit_share_rewards,
                'total_claimable_deposits': total_claimable_deposits,  # 可领取的存款数量
                'total_claimable_amount': total_claimable_amount,  # 可领取的奖励总额
                'can_claim': total_claimable_deposits > 0  # 是否可以领取
            },

            # Method 3: 邀请人佣金（基于被邀请人存款/流水）
            'method3': method3_info,

            # Method 4: 被邀请人投注返佣（给被邀请人自己）
            'method4': method4_info,

            # 邀请人统计
            'invitee_stats': {
                'total_invitees': total_invitees,
                'period_invitees': period_invitees,
                'total_invitee_deposits': total_invitee_deposits,
                'total_invitee_turnover': total_invitee_turnover
            },

            # 汇总信息
            'summary': {
                'total_claimable': (
                        total_claimable +  # Method 1 可领取总额
                        total_claimable_amount +  # Method 2 可领取总额
                        (float(method3_info['commission_stats']['pending']) if method3_info else 0) +  # Method 3 可领取
                        (float(method4_info['commission_stats']['pending']) if method4_info else 0)  # Method 4 可领取
                ),
                'total_rewards_claimed': float(total_rewards_claimed)  # 所有已领取总额
            }
        }

        return result

    except Exception as e:
        print(f"Error getting brief progress for activity {activity_id}: {str(e)}")
        return {
            'activity_id': activity_id,
            'activity_title': getattr(activity, 'title', 'Unknown'),
            'is_valid': False,
            'method1': {
                'achievement_rules': [],
                'invitation_share': None
            },
            'method2': {
                'deposit_share_tiers': [],
                'total_rewards': 0
            },
            'method3': None,
            'method4': None,
            'invitee_stats': {
                'total_invitees': 0,
                'period_invitees': 0,
                'total_invitee_deposits': 0,
                'total_invitee_turnover': 0
            },
            'summary': {
                'total_claimable': 0,
                'total_rewards_claimed': 0
            }
        }


def calculate_rule_progress(user_id, activity, rule):
    """
    计算用户在某规则下的进度
    返回: {current_value, threshold_value, progress_percentage, is_reached, can_claim, claimed_count, remaining_claims}
    """
    rule_type = rule.rule_type
    threshold = float(rule.threshold_value) if rule.threshold_value else 0
    current_value = 0

    # 统计已领取次数
    claimed_count = MAppInvitationReward.query.filter(
        MAppInvitationReward.mb_id == user_id,
        MAppInvitationReward.activity_id == activity.id,
        MAppInvitationReward.rule_id == rule.id,
        MAppInvitationReward.status.in_(['Claimed', 'Pending']),
        MAppInvitationReward.del_flag == 0
    ).count()

    max_claims = rule.max_claim_count or 0
    remaining_claims = max(0, max_claims - claimed_count) if max_claims > 0 else 999

    # 根据规则类型计算当前值
    if rule_type == AchievementType.INVITE_COUNT.value:
        # 邀请人数达标
        # 通过推广关系表统计，只统计计入活动奖励的邀请
        promotion_relations = MAppPromotionRelation.query.join(
            AppMember, MAppPromotionRelation.invitee_id == AppMember.id
        ).filter(
            MAppPromotionRelation.promoter_id == user_id,
            MAppPromotionRelation.status == 'Active',
            MAppPromotionRelation.is_counted_in_activity == True,  # 只统计计入活动的
            MAppPromotionRelation.del_flag == 0,
            AppMember.create_time >= activity.start_date,
            AppMember.create_time <= activity.end_date
        ).all()

        # 直接统计邀请人数，验证被邀请人存款
        current_value = 0
        # 获取被邀请人最低充值要求
        min_deposit = float(activity.achievement_invitee_min_deposit) if hasattr(activity,
                                                                                 'achievement_invitee_min_deposit') and activity.achievement_invitee_min_deposit else 0

        for relation in promotion_relations:
            total_charge = db.session.query(func.sum(Charge.amount)).filter(
                Charge.mb_id == relation.invitee_id,
                Charge.status == 'Success',
                Charge.del_flag == 0,
                Charge.create_time >= activity.start_date,
                Charge.create_time <= activity.end_date
            ).scalar() or 0

            # 只有被邀请人充值达到最低要求，才计入成就人数
            if total_charge >= min_deposit:
                current_value += 1
    elif rule_type == AchievementType.INVITEE_FIRST_RECHARGE.value:
        # 被邀请人首充金额达标
        # 通过推广关系表统计，只统计计入活动奖励的邀请
        promotion_relations = MAppPromotionRelation.query.join(
            AppMember, MAppPromotionRelation.invitee_id == AppMember.id
        ).filter(
            MAppPromotionRelation.promoter_id == user_id,
            MAppPromotionRelation.status == 'Active',
            MAppPromotionRelation.is_counted_in_activity == True,  # 只统计计入活动的
            MAppPromotionRelation.del_flag == 0,
            AppMember.create_time >= activity.start_date,
            AppMember.create_time <= activity.end_date
        ).all()

        total_first_recharge = 0
        for relation in promotion_relations:
            first_charge = Charge.query.filter(
                Charge.mb_id == relation.invitee_id,
                Charge.status == 'Success',
                Charge.del_flag == 0,
                Charge.create_time >= activity.start_date,
                Charge.create_time <= activity.end_date
            ).order_by(Charge.create_time.asc()).first()

            if first_charge:
                total_first_recharge += float(first_charge.amount or 0)

        current_value = total_first_recharge

    elif rule_type == AchievementType.FIRST_BET.value:
        # 首次下注金额达标（邀请人自己）
        first_bet = AppBetOrder.query.filter(
            AppBetOrder.mb_id == user_id,
            AppBetOrder.bet_status.in_(
                [BetStatus.Win, BetStatus.Lose, BetStatus.Draw, BetStatus.HalfWin, BetStatus.HalfLose]),
            AppBetOrder.del_flag == 0,
            AppBetOrder.create_time >= activity.start_date,
            AppBetOrder.create_time <= activity.end_date
        ).order_by(AppBetOrder.create_time.asc()).first()

        current_value = float(first_bet.stake or 0) if first_bet else 0

    elif rule_type == AchievementType.BET_PROFIT.value:
        # 下注盈利达标
        # 统计被邀请人的总盈利（只统计计入活动的）
        promotion_relations_profit = MAppPromotionRelation.query.filter(
            MAppPromotionRelation.promoter_id == user_id,
            MAppPromotionRelation.status == 'Active',
            MAppPromotionRelation.is_counted_in_activity == True,  # 只统计计入活动的
            MAppPromotionRelation.del_flag == 0
        ).all()

        total_profit = 0
        for relation in promotion_relations_profit:
            profit = db.session.query(
                func.sum(AppBetOrder.win_amount) - func.sum(AppBetOrder.stake)
            ).filter(
                AppBetOrder.mb_id == relation.invitee_id,
                AppBetOrder.bet_status.in_(
                    [BetStatus.Win, BetStatus.Lose, BetStatus.Draw, BetStatus.HalfWin, BetStatus.HalfLose]),
                AppBetOrder.del_flag == 0,
                AppBetOrder.create_time >= activity.start_date,
                AppBetOrder.create_time <= activity.end_date
            ).scalar() or 0
            total_profit += float(profit)

        current_value = max(0, total_profit)

    elif rule_type == AchievementType.BET_CASHBACK.value:
        # 下注返还（被邀请人总流水，只统计计入活动的）
        promotion_relations_cashback = MAppPromotionRelation.query.filter(
            MAppPromotionRelation.promoter_id == user_id,
            MAppPromotionRelation.status == 'Active',
            MAppPromotionRelation.is_counted_in_activity == True,  # 只统计计入活动的
            MAppPromotionRelation.del_flag == 0
        ).all()

        total_turnover = 0
        for relation in promotion_relations_cashback:
            turnover = db.session.query(func.sum(AppBetOrder.stake)).filter(
                AppBetOrder.mb_id == relation.invitee_id,
                AppBetOrder.bet_status.in_(
                    [BetStatus.Win, BetStatus.Lose, BetStatus.Draw, BetStatus.HalfWin, BetStatus.HalfLose]),
                AppBetOrder.del_flag == 0,
                AppBetOrder.create_time >= activity.start_date,
                AppBetOrder.create_time <= activity.end_date
            ).scalar() or 0
            total_turnover += float(turnover)

        current_value = total_turnover

    # 计算进度百分比
    progress_percentage = min(100, (current_value / threshold * 100)) if threshold > 0 else 0
    is_reached = current_value >= threshold
    can_claim = is_reached and remaining_claims > 0

    return {
        'current_value': current_value,
        'threshold_value': threshold,
        'progress_percentage': progress_percentage,
        'is_reached': is_reached,
        'can_claim': can_claim,
        'claimed_count': claimed_count,
        'remaining_claims': remaining_claims
    }


# ==================== API 接口 ====================

@invitation_v2.route('/list', methods=['GET'])
@auth.login_required
def get_available_activities_progress():
    """获取可参与的邀请活动列表（参考 CouponController.get_available_coupons）"""
    try:
        user_id = g.user.id
        user = g.user
        page = int(request.args.get('page', 1))
        page_size = min(int(request.args.get('page_size', 20)), 100)

        now = datetime.now()

        # 查询所有有效的邀请活动
        query = MAppInvitationActivity.query.filter(
            MAppInvitationActivity.del_flag == 0,
            MAppInvitationActivity.status == 1,
            MAppInvitationActivity.is_closed == 0,
            MAppInvitationActivity.start_date <= now,
            MAppInvitationActivity.end_date >= now
        )

        # 过滤用户有权限访问的活动（HOUSE或匹配的AGENT）
        user_agent_id = user.aid if hasattr(user, 'aid') else None
        query = query.filter(
            or_(
                MAppInvitationActivity.agent_id.is_(None),
                MAppInvitationActivity.agent_id == '',
                MAppInvitationActivity.agent_id == user_agent_id,
                MAppInvitationActivity.fund_source_type == 'HOUSE'
            )
        )

        # 获取总数
        total_count = query.count()

        # 分页和排序
        offset = (page - 1) * page_size
        activities = query.order_by(MAppInvitationActivity.sort.asc()).offset(offset).limit(page_size).all()
        # 格式化返回数据
        activity_list = []
        for a in activities:
            # 检查是否可以参与
            can_participate = is_activity_valid(a)

            # 检查用户是否已参与活动
            activity_record = AppPlayerActivityRecord.query.filter_by(
                mb_id=user_id,
                activity_type='INVITATION',
                activity_id=a.id,
                del_flag=0
            ).first()
            has_joined = activity_record is not None

            # 获取活动简要进度
            brief_progress = get_activity_brief_progress(user_id, a.id, a)

            # 计算规则统计（向后兼容）
            method1 = brief_progress.get('method1', {})
            achievement_rules = method1.get('achievement_rules', [])
            rules_count = len(achievement_rules)
            completed_rules = len([p for p in achievement_rules if p.get('is_reached')])

            summary = brief_progress.get('summary', {})
            claimable_reward = summary.get('total_claimable', 0)

            # 计算启用的 Methods
            enabled_methods = []
            if hasattr(a, 'method_invitation_enabled') and a.method_invitation_enabled == 1:
                enabled_methods.append('method1')
            if hasattr(a, 'method_deposit_enabled') and a.method_deposit_enabled == 1:
                enabled_methods.append('method2')
            if hasattr(a, 'method_commission_enabled') and a.method_commission_enabled == 1:
                enabled_methods.append('method3')
            if hasattr(a, 'method_invitee_bet_enabled') and a.method_invitee_bet_enabled == 1:
                enabled_methods.append('method4')

            activity_info = {
                'id': a.id,
                'title': a.title,
                'description': a.description,
                'enabled_methods': enabled_methods,  # 替代 bonus_type
                'start_date': a.start_date.strftime('%Y-%m-%d %H:%M:%S') if a.start_date else None,
                'end_date': a.end_date.strftime('%Y-%m-%d %H:%M:%S') if a.end_date else None,
                'status': can_participate,
                'is_valid': can_participate,
                'status': 'active' if can_participate else 'inactive',
                'claimable_reward': claimable_reward,
                'rules_count': rules_count,
                'completed_rules': completed_rules,
                'create_time': a.create_time.strftime('%Y-%m-%d %H:%M:%S') if a.create_time else None,
                'bonus_pool': float(a.bonus_pool) if a.bonus_pool else 0,
                'bonus_pool_remaining': float(a.bonus_pool_remaining) if a.bonus_pool_remaining else 0,
                'agent_id': a.agent_id if hasattr(a, 'agent_id') else None,
                'is_pool_exhausted': bool(a.is_pool_exhausted) if hasattr(a, 'is_pool_exhausted') else False,

                # 额外字段（V2特有）
                'slogan': a.slogan if hasattr(a, 'slogan') else None,
                'ad_image_url': a.ad_image_url if hasattr(a, 'ad_image_url') else None,
                'fund_source_type': a.fund_source_type if hasattr(a, 'fund_source_type') else 'HOUSE',
                'turnover_multiplier': float(a.turnover_multiplier) if hasattr(a,
                                                                               'turnover_multiplier') and a.turnover_multiplier else 1.0,
                'enabled_methods': {
                    'method1_invitation': bool(a.method_invitation_enabled) if hasattr(a,
                                                                                       'method_invitation_enabled') else False,
                    'method2_deposit': bool(a.method_deposit_enabled) if hasattr(a,
                                                                                 'method_deposit_enabled') else False,
                    'method3_commission': bool(a.method_commission_enabled) if hasattr(a,
                                                                                       'method_commission_enabled') else False,
                    'method4_invitee_bet': bool(a.method_invitee_bet_enabled) if hasattr(a,
                                                                                         'method_invitee_bet_enabled') else False
                },

                # 方案A：按Method分组的进度数据
                'method1': brief_progress.get('method1', {}),
                'method2': brief_progress.get('method2', {}),
                'method3': brief_progress.get('method3'),
                'method4': brief_progress.get('method4'),
                'invitee_stats': brief_progress.get('invitee_stats', {}),
                'summary': summary,

                # 参与状态
                'has_joined': has_joined
            }

            activity_list.append(activity_info)

        return jsonify({
            'code': SUCCESS_CODE,
            'data': {
                'activities': ensure_serializable(activity_list),
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


@invitation_v2.route('/detail/<string:activity_id>', methods=['GET'])
@auth.login_required
def get_activity_detail(activity_id):
    """获取活动详情，包括所有规则和进度"""
    try:
        user_id = g.user.id
        user = g.user

        # 获取活动信息
        activity = MAppInvitationActivity.query.filter_by(
            id=activity_id,
            del_flag=0
        ).first()

        if not activity:
            return jsonify({
                'code': ACTIVITY_NOT_FOUND_CODE,
                'data': None,
                'message': 'Activity does not exist'
            }), 404

        # 检查访问权限
        if not check_user_agent_access(user, activity):
            return jsonify({
                'code': PARAM_ERROR_CODE,
                'data': None,
                'message': 'You are not authorized to access this activity'
            }), 403

        # 计算启用的 Methods
        enabled_methods = []
        if hasattr(activity, 'method_invitation_enabled') and activity.method_invitation_enabled == 1:
            enabled_methods.append('method1')
        if hasattr(activity, 'method_deposit_enabled') and activity.method_deposit_enabled == 1:
            enabled_methods.append('method2')
        if hasattr(activity, 'method_commission_enabled') and activity.method_commission_enabled == 1:
            enabled_methods.append('method3')
        if hasattr(activity, 'method_invitee_bet_enabled') and activity.method_invitee_bet_enabled == 1:
            enabled_methods.append('method4')

        # 基本信息
        activity_data = {
            'id': activity.id,
            'title': activity.title,
            'slogan': activity.slogan if hasattr(activity, 'slogan') else None,
            'description': activity.description,
            'ad_image_url': activity.ad_image_url if hasattr(activity, 'ad_image_url') else None,
            'enabled_methods': enabled_methods,  # 替代 bonus_type：显示启用的 Methods
            'start_date': activity.start_date.strftime('%Y-%m-%d %H:%M:%S') if activity.start_date else None,
            'end_date': activity.end_date.strftime('%Y-%m-%d %H:%M:%S') if activity.end_date else None,
            'bonus_pool': float(activity.bonus_pool) if activity.bonus_pool else 0,
            'bonus_pool_remaining': float(activity.bonus_pool_remaining) if activity.bonus_pool_remaining else 0,
            'status': activity.status,
            'is_valid': is_activity_valid(activity),
            'turnover_multiplier': float(activity.turnover_multiplier) if hasattr(activity,
                                                                                  'turnover_multiplier') and activity.turnover_multiplier else 1.0,
            'profit_share_frequency': activity.profit_share_frequency if hasattr(activity,
                                                                                 'profit_share_frequency') else 'weekly',
            'fund_source_type': activity.fund_source_type if hasattr(activity, 'fund_source_type') else 'HOUSE'
        }

        # Method 1: 邀请规则及进度
        if hasattr(activity, 'method_invitation_enabled') and activity.method_invitation_enabled == 1:
            rules = MAppInvitationAchievement.query.filter_by(
                activity_id=activity_id,
                del_flag=0
            ).order_by(MAppInvitationAchievement.sequence).all()

            rules_with_progress = []
            total_claimable = 0

            for rule in rules:
                progress = calculate_rule_progress(user_id, activity, rule)
                rule_data = {
                    'id': rule.id,
                    'rule_type': rule.rule_type,
                    'threshold_value': float(rule.threshold_value) if rule.threshold_value else 0,
                    'reward_amount': float(rule.reward_amount) if rule.reward_amount else 0,
                    'max_claim_count': rule.max_claim_count,
                    'description': rule.description,
                    'sequence': rule.sequence,
                    'progress': progress
                }
                rules_with_progress.append(rule_data)

                if progress['can_claim']:
                    total_claimable += float(rule.reward_amount) if rule.reward_amount else 0

            activity_data['method1_rules'] = rules_with_progress
            activity_data['method1_claimable_total'] = total_claimable

            # 邀请分享配置（单次邀请奖励）
            activity_data['invitation_share_config'] = {
                'one_time_bonus': float(activity.invitation_share_one_time_bonus) if hasattr(activity,
                                                                                             'invitation_share_one_time_bonus') and activity.invitation_share_one_time_bonus else 0,
                'min_deposit': float(activity.invitation_share_min_deposit) if hasattr(activity,
                                                                                       'invitation_share_min_deposit') and activity.invitation_share_min_deposit else 0,
                'min_turnover': float(activity.invitation_share_min_turnover) if hasattr(activity,
                                                                                         'invitation_share_min_turnover') and activity.invitation_share_min_turnover else 0
            }

        # Method 2: 存款分享配置
        if hasattr(activity, 'method_deposit_enabled') and activity.method_deposit_enabled == 1:
            deposit_shares = MAppInvitationDepositShare.query.filter_by(
                activity_id=activity_id,
                del_flag=0
            ).order_by(MAppInvitationDepositShare.sequence).all()

            activity_data['method2_deposit_shares'] = [
                {
                    'id': share.id,
                    'min_deposit': float(share.min_deposit) if share.min_deposit else 0,
                    'max_deposit': float(share.max_deposit) if share.max_deposit else None,
                    'bonus_rate': float(share.bonus_rate) if share.bonus_rate else 0,
                    'sequence': share.sequence
                }
                for share in deposit_shares
            ]

        # Method 3: 邀请人佣金配置
        if hasattr(activity, 'method_commission_enabled') and activity.method_commission_enabled == 1:
            # 根据佣金类型确定 sub_type
            activity_commission_type = activity.commission_type if hasattr(activity, 'commission_type') else 'turnover'
            method3_sub_type = 'WIN_LOSS_COMMISSION' if activity_commission_type == 'win_loss' else 'TURNOVER_COMMISSION'

            # 计算待发放和已发放佣金
            pending_commission = db.session.query(func.sum(MAppCommissionRecord.amount)).filter(
                MAppCommissionRecord.activity_id == activity_id,
                MAppCommissionRecord.user_id == user_id,  # 我作为邀请人（受益人）
                MAppCommissionRecord.sub_type == method3_sub_type,
                MAppCommissionRecord.status == 'Pending',
                MAppCommissionRecord.del_flag == 0
            ).scalar() or 0

            paid_commission = db.session.query(func.sum(MAppCommissionRecord.amount)).filter(
                MAppCommissionRecord.activity_id == activity_id,
                MAppCommissionRecord.user_id == user_id,  # 我作为邀请人（受益人）
                MAppCommissionRecord.sub_type == method3_sub_type,
                MAppCommissionRecord.status == 'Paid',
                MAppCommissionRecord.del_flag == 0
            ).scalar() or 0

            activity_data['method3_commission'] = {
                'commission_type': activity.commission_type if hasattr(activity, 'commission_type') else 'turnover',
                'commission_rate': float(activity.commission_rate) if hasattr(activity,
                                                                              'commission_rate') and activity.commission_rate else 0,
                'pending_commission': float(pending_commission),
                'paid_commission': float(paid_commission),
                'total_commission': float(pending_commission + paid_commission)
            }

        # Method 4: 被邀请人投注返佣配置（返佣给被邀请人自己）
        if hasattr(activity, 'method_invitee_bet_enabled') and activity.method_invitee_bet_enabled == 1:
            # Method 4 的 sub_type，与 CommissionRecordService._create_invitee_bet_cashback() 保持一致
            method4_sub_type = 'INVITEE_BET_COMMISSION'

            # Method 4: 查询我作为被邀请人获得的返佣
            pending_bet_commission = db.session.query(func.sum(MAppCommissionRecord.amount)).filter(
                MAppCommissionRecord.activity_id == activity_id,
                MAppCommissionRecord.user_id == user_id,  # Method 4: 我作为受益人
                MAppCommissionRecord.sub_type == method4_sub_type,
                MAppCommissionRecord.status == 'Pending',
                MAppCommissionRecord.del_flag == 0
            ).scalar() or 0

            activity_data['method4_invitee_bet'] = {
                'commission_rate': float(activity.invitee_bet_commission_rate) if hasattr(activity,
                                                                                          'invitee_bet_commission_rate') and activity.invitee_bet_commission_rate else 0,
                'pending_commission': float(pending_bet_commission)
            }

        # 添加邀请限制信息
        from app_server.service.PromotionRelationService import PromotionRelationService
        can_invite, error_msg, invitation_stats = PromotionRelationService.check_invitation_limit(user_id, activity_id)

        activity_data['invitation_limit'] = {
            'max_invitations': invitation_stats.get('max_invitations', 0),
            'current_invitations': invitation_stats.get('current_invitations', 0),
            'remaining_invitations': invitation_stats.get('remaining_invitations', -1),
            'can_invite': can_invite,
            'message': error_msg if not can_invite else ''
        }

        return jsonify({
            'code': SUCCESS_CODE,
            'data': ensure_serializable(activity_data),
            'message': 'success'
        }), 200

    except Exception as e:
        return jsonify({
            'code': SYSTEM_ERROR_CODE,
            'data': None,
            'message': str(e)
        }), 500


@invitation_v2.route('/claim-achievement-reward', methods=['POST'])
@auth.login_required
def claim_achievement_reward():
    """
    领取邀请成就奖励 - Method 1 规则奖励
    参考 CouponController.redeem_coupon

    请求参数:
    - activity_id: 活动ID
    - rule_id: 规则ID（可选，不传则领取所有可领取的规则奖励）
    """
    try:
        user_id = g.user.id
        user = g.user
        data = request.json
        activity_id = data.get('activity_id')
        rule_id = data.get('rule_id')  # 可选

        if not activity_id:
            return jsonify({
                'code': PARAM_ERROR_CODE,
                'data': None,
                'message': 'Activity ID is required'
            }), 400

        # 获取活动信息（加锁）
        activity = db.session.query(MAppInvitationActivity).filter(
            MAppInvitationActivity.id == activity_id,
            MAppInvitationActivity.del_flag == 0
        ).with_for_update().first()

        if not activity:
            return jsonify({
                'code': ACTIVITY_NOT_FOUND_CODE,
                'data': None,
                'message': 'Activity does not exist'
            }), 404

        # 检查活动是否有效
        if not is_activity_valid(activity):
            return jsonify({
                'code': ACTIVITY_NOT_VALID_CODE,
                'data': None,
                'message': 'Activity is not valid or has expired'
            }), 400

        # 检查访问权限
        if not check_user_agent_access(user, activity):
            return jsonify({
                'code': PARAM_ERROR_CODE,
                'data': None,
                'message': 'You are not authorized to access this activity'
            }), 403

        # 检查 Method 1 是否启用
        if not hasattr(activity, 'method_invitation_enabled') or activity.method_invitation_enabled != 1:
            return jsonify({
                'code': ACTIVITY_NOT_VALID_CODE,
                'data': None,
                'message': 'Invitation reward method is not enabled for this activity'
            }), 400

        # 【新增】检查用户是否已参与活动（加行锁防止并发领取）
        # 注意：这里查询的记录会在后面复用，避免重复查询
        activity_record_for_claim = db.session.query(AppPlayerActivityRecord).filter(
            AppPlayerActivityRecord.mb_id == user_id,
            AppPlayerActivityRecord.activity_type == 'INVITATION',
            AppPlayerActivityRecord.activity_id == activity_id,
            AppPlayerActivityRecord.status == 'Active',
            AppPlayerActivityRecord.del_flag == 0
        ).with_for_update().first()

        if not activity_record_for_claim:
            return jsonify({
                'code': CONDITION_NOT_MET_CODE,
                'data': None,
                'message': 'Please join the activity first before claiming rewards',
                'need_join': True
            }), 400

        # 风险检查
        ip_address = request.remote_addr
        user_agent_str = request.headers.get('User-Agent')
        device_id = (request.headers.get('X-Device-ID') or
                     request.headers.get('Device-ID') or
                     request.headers.get('X-Device-IMEI') or
                     request.headers.get('IMEI'))

        risk_check, risk_msg = perform_risk_check(user_id, activity_id, activity, ip_address, device_id, user_agent_str)
        if not risk_check:
            return jsonify({
                'code': RISK_CHECK_FAILED_CODE,
                'data': None,
                'message': risk_msg
            }), 400

        # 检查优惠券和邀请活动互斥
        exclusion_check, exclusion_msg = check_coupon_invitation_exclusion(user_id, activity)
        if not exclusion_check:
            return jsonify({
                'code': CONDITION_NOT_MET_CODE,
                'data': None,
                'message': exclusion_msg
            }), 400

        # 获取要领取的规则
        if rule_id:
            rules = MAppInvitationAchievement.query.filter_by(
                id=rule_id,
                activity_id=activity_id,
                del_flag=0
            ).all()
        else:
            rules = MAppInvitationAchievement.query.filter_by(
                activity_id=activity_id,
                del_flag=0
            ).order_by(MAppInvitationAchievement.sequence).all()

        if not rules:
            return jsonify({
                'code': ACTIVITY_NOT_FOUND_CODE,
                'data': None,
                'message': 'No rules found for this activity'
            }), 404

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

        # 处理每个规则
        claimed_rewards = []
        total_reward_amount = Decimal('0')
        now = datetime.now()

        for rule in rules:
            # 计算进度
            progress = calculate_rule_progress(user_id, activity, rule)

            # 检查是否可以领取
            if not progress['can_claim']:
                continue

            # 检查领取限制
            limit_check, limit_msg = check_user_claim_limits_for_rule(user_id, activity_id, rule)
            if not limit_check:
                continue

            # 检查奖金池余额
            reward_amount = Decimal(str(rule.reward_amount)) if rule.reward_amount else Decimal('0')
            if activity.bonus_pool_remaining is not None and activity.bonus_pool_remaining < reward_amount:
                continue

            # 扣除奖金池
            if activity.bonus_pool_remaining is not None:
                activity.bonus_pool_remaining = activity.bonus_pool_remaining - reward_amount
                activity.used_amount = (activity.used_amount or Decimal('0')) + reward_amount

            # 创建奖励领取记录
            reward_record = MAppInvitationReward(
                id=Kits.generate_uuid(),
                activity_id=activity_id,
                rule_id=rule.id,
                mb_id=user_id,
                referred_id=None,
                reward_amount=reward_amount,
                bonus_type='method1_achievement',
                status='Claimed',
                claimed_at=now,
                create_time=now,
                create_by_id=user_id,
                del_flag=0,
                tenant_id='10000'
            )
            db.session.add(reward_record)

            total_reward_amount += reward_amount
            claimed_rewards.append({
                'rule_id': rule.id,
                'rule_type': rule.rule_type,
                'reward_amount': float(reward_amount),
                'description': rule.description
            })

        if not claimed_rewards:
            return jsonify({
                'code': CONDITION_NOT_MET_CODE,
                'data': None,
                'message': 'No rewards available to claim. Please check your progress.'
            }), 400

        # 计算流水要求
        turnover_multiplier = Decimal(str(activity.turnover_multiplier)) if hasattr(activity,
                                                                                    'turnover_multiplier') and activity.turnover_multiplier else Decimal(
            '1')
        req_turnover = total_reward_amount * turnover_multiplier

        # 计算净赢要求：只使用固定值
        req_netwin = Decimal(str(activity.net_win_amount)) if hasattr(activity,
                                                                      'net_win_amount') and activity.net_win_amount else Decimal(
            '0')

        # 判断应该转入哪个钱包
        use_main_wallet = should_use_main_wallet(activity, user_id)

        # 如果没有流水/净赢要求，直接标记为已达标
        initial_requirement_met = 1 if use_main_wallet else 0

        if use_main_wallet:
            # 转入主钱包
            old_balance = member.money if member.money else Decimal('0')
            new_balance = old_balance + total_reward_amount
            member.money = new_balance

            # 增加可提现金额
            old_withdrawable = member.money_promotion_withdrawable if member.money_promotion_withdrawable else Decimal(
                '0')
            member.money_promotion_withdrawable = old_withdrawable + total_reward_amount

            wallet_type = "Money"
            target_wallet = TransactionMap.Ewallet
        else:
            # 转入促销钱包
            old_balance = member.money_promotion if member.money_promotion else Decimal('0')
            new_balance = old_balance + total_reward_amount
            member.money_promotion = new_balance

            wallet_type = "Promotion"
            target_wallet = TransactionMap.ProWallet

        # 记录余额流水
        balance_log = AppMemberBalanceLog(
            id=Kits.generate_uuid(),
            sn=f"INVITE_{Kits.generate_uuid()}",
            type=TransactionType.Activity,
            type_sub=TransactionType.InvitationReward if hasattr(TransactionType,
                                                                 'InvitationReward') else TransactionType.Activity,
            type_sub_data_id=activity_id,
            mb_id=user_id,
            mb_username=member.username if hasattr(member, 'username') else None,
            money=total_reward_amount,
            start_balance=old_balance,
            end_balance=new_balance,
            create_by_id=user_id,
            update_by_id=user_id,
            aid=user.aid if hasattr(user, 'aid') else None,
            source="System",
            target=target_wallet,
            pay_wallet=wallet_type,
            status=1,
            source_status=0
        )
        db.session.add(balance_log)

        # 使用前面查询的活动参与记录（已确保存在）
        activity_record = activity_record_for_claim

        # 更新已存在的活动记录
        # 解析现有的 completion_detail
        existing_detail = {}
        if activity_record.completion_detail:
            try:
                existing_detail = json.loads(activity_record.completion_detail)
            except:
                existing_detail = {}

        # 周期管理：如果上一轮已达标（is_requirement_met=1），进入新一轮
        if activity_record.is_requirement_met == 1:
            # 新一轮：重置当前轮数据
            new_settlement_round = (activity_record.settlement_round or 1) + 1
            new_bonus_current_round = total_reward_amount
            activity_record.is_requirement_met = 0
            activity_record.settlement_round = new_settlement_round
            activity_record.round_start_time = now  # 记录本轮开始时间
        else:
            # 同一轮：累加当前轮奖励金额
            new_settlement_round = activity_record.settlement_round or 1
            new_bonus_current_round = (activity_record.bonus_amount_current_round or Decimal('0')) + total_reward_amount
            # round_start_time 保持不变（本轮首次领取时已设置）
            if not activity_record.round_start_time:
                activity_record.round_start_time = now  # 兼容旧数据

        activity_record.bonus_amount_current_round = new_bonus_current_round

        # 基于当前轮奖励金额计算本轮流水要求
        new_req_turnover = new_bonus_current_round * turnover_multiplier

        # 更新 completion_detail
        existing_rules_claimed = existing_detail.get('rules_claimed', [])
        for r in claimed_rewards:
            if r['rule_id'] not in existing_rules_claimed:
                existing_rules_claimed.append(r['rule_id'])

        activity_record.completion_detail = json.dumps({
            'reward_amount': float((activity_record.bonus_amount or Decimal('0')) + total_reward_amount),
            'turnover_required': float(new_req_turnover),
            'settlement_round': new_settlement_round,
            'bonus_amount_current_round': float(new_bonus_current_round),
            'rules_claimed': existing_rules_claimed
        })
        activity_record.req_turnover = new_req_turnover
        # req_netwin 不需要更新（参与活动时已设置固定值）
        activity_record.completion_condition = f'Round {new_settlement_round} Turnover: {float(new_req_turnover)}'

        # 累加奖励金额（历史总额）
        activity_record.bonus_amount = (activity_record.bonus_amount or Decimal('0')) + total_reward_amount

        # 如果本次领取无流水/净赢要求（直接进主钱包），则标记达标
        if initial_requirement_met == 1:
            activity_record.is_requirement_met = 1

        activity_record.update_time = now
        activity_record.update_by_id = user_id

        # 保存更改
        db.session.commit()

        # 记录成功的领取
        RiskManagementService.record_redemption_attempt(
            user_id=user_id,
            coupon_id=activity_id,
            ip=ip_address,
            imei=device_id,
            successful=True
        )

        return jsonify({
            'code': SUCCESS_CODE,
            'data': {
                'claimed_rewards': claimed_rewards,
                'total_reward_amount': float(total_reward_amount),
                'turnover_requirement': float(req_turnover),
                'new_balance': float(new_balance),
                'wallet_type': wallet_type,
                'claim_time': now.strftime('%Y-%m-%d %H:%M:%S')
            },
            'message': f'Successfully claimed {len(claimed_rewards)} reward(s)'
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': SYSTEM_ERROR_CODE,
            'data': None,
            'message': str(e)
        }), 500


@invitation_v2.route('/claim-one-time-reward', methods=['POST'])
@auth.login_required
def claim_one_time_reward():
    """
    领取一次性邀请奖励 (Method 1.2)

    请求体:
    {
        "activity_id": "活动ID"
    }
    """
    try:
        user_id = g.user.id
        user = g.user
        data = request.json
        activity_id = data.get('activity_id')

        if not activity_id:
            return jsonify({
                'code': PARAM_ERROR_CODE,
                'data': None,
                'message': 'Activity ID is required'
            }), 400

        # 获取活动信息（加锁）
        activity = db.session.query(MAppInvitationActivity).filter(
            MAppInvitationActivity.id == activity_id,
            MAppInvitationActivity.del_flag == 0
        ).with_for_update().first()

        if not activity:
            return jsonify({
                'code': ACTIVITY_NOT_FOUND_CODE,
                'data': None,
                'message': 'Activity does not exist'
            }), 404

        # 检查活动是否有效
        if not is_activity_valid(activity):
            return jsonify({
                'code': ACTIVITY_NOT_VALID_CODE,
                'data': None,
                'message': 'Activity is not valid or has expired'
            }), 400

        # 检查访问权限
        if not check_user_agent_access(user, activity):
            return jsonify({
                'code': PARAM_ERROR_CODE,
                'data': None,
                'message': 'You are not authorized to access this activity'
            }), 403

        # 检查 Method 1 是否启用
        if not hasattr(activity, 'method_invitation_enabled') or activity.method_invitation_enabled != 1:
            return jsonify({
                'code': ACTIVITY_NOT_VALID_CODE,
                'data': None,
                'message': 'Invitation method is not enabled for this activity'
            }), 400

        # 检查是否配置了一次性奖励
        if not activity.invitation_share_one_time_bonus or activity.invitation_share_one_time_bonus <= 0:
            return jsonify({
                'code': PARAM_ERROR_CODE,
                'data': None,
                'message': 'One-time reward is not configured for this activity'
            }), 400

        # 【新增】检查用户是否已参与活动（加行锁防止并发领取）
        # 注意：这里查询的记录会在后面复用，避免重复查询
        activity_record_for_claim = db.session.query(AppPlayerActivityRecord).filter(
            AppPlayerActivityRecord.mb_id == user_id,
            AppPlayerActivityRecord.activity_type == 'INVITATION',
            AppPlayerActivityRecord.activity_id == activity_id,
            AppPlayerActivityRecord.status == 'Active',
            AppPlayerActivityRecord.del_flag == 0
        ).with_for_update().first()

        if not activity_record_for_claim:
            return jsonify({
                'code': CONDITION_NOT_MET_CODE,
                'data': None,
                'message': 'Please join the activity first before claiming rewards',
                'need_join': True
            }), 400

        # 风险检查
        ip_address = request.remote_addr
        user_agent_str = request.headers.get('User-Agent')
        device_id = (request.headers.get('X-Device-ID') or
                     request.headers.get('Device-ID') or
                     request.headers.get('X-Device-IMEI') or
                     request.headers.get('IMEI'))

        risk_check, risk_msg = perform_risk_check(user_id, activity_id, activity, ip_address, device_id, user_agent_str)
        if not risk_check:
            return jsonify({
                'code': RISK_CHECK_FAILED_CODE,
                'data': None,
                'message': risk_msg
            }), 400

        # 检查优惠券和邀请活动互斥
        exclusion_check, exclusion_msg = check_coupon_invitation_exclusion(user_id, activity)
        if not exclusion_check:
            return jsonify({
                'code': CONDITION_NOT_MET_CODE,
                'data': None,
                'message': exclusion_msg
            }), 400

        # 查询已领取过的被邀请人 ID（按 referred_id 逐个追踪，避免重复发奖）
        already_claimed_invitee_ids = set(
            r.referred_id for r in MAppInvitationReward.query.filter(
                MAppInvitationReward.mb_id == user_id,
                MAppInvitationReward.activity_id == activity_id,
                MAppInvitationReward.bonus_type == 'invitation_share_one_time',
                MAppInvitationReward.status.in_(['Claimed', 'Pending']),
                MAppInvitationReward.del_flag == 0
            ).all()
            if r.referred_id
        )

        # 统计符合条件的被邀请人（只统计计入活动的、且尚未领取过的）
        promotion_relations_onetime = MAppPromotionRelation.query.join(
            AppMember, MAppPromotionRelation.invitee_id == AppMember.id
        ).filter(
            MAppPromotionRelation.promoter_id == user_id,
            MAppPromotionRelation.status == 'Active',
            MAppPromotionRelation.is_counted_in_activity == True,  # 只统计计入活动的
            MAppPromotionRelation.del_flag == 0,
            AppMember.create_time >= activity.start_date,
            AppMember.create_time <= activity.end_date
        ).all()

        qualified_count = 0
        qualified_invitee_ids = []
        for relation in promotion_relations_onetime:
            # 跳过已经领取过的被邀请人
            if relation.invitee_id in already_claimed_invitee_ids:
                continue

            # 检查存款条件
            if activity.invitation_share_min_deposit and activity.invitation_share_min_deposit > 0:
                total_deposit = db.session.query(func.sum(Charge.amount)).filter(
                    Charge.mb_id == relation.invitee_id,
                    Charge.status == 'Success',
                    Charge.del_flag == 0
                ).scalar() or 0
                if total_deposit < activity.invitation_share_min_deposit:
                    continue

            # 检查流水条件
            if activity.invitation_share_min_turnover and activity.invitation_share_min_turnover > 0:
                total_turnover = db.session.query(func.sum(AppBetOrder.stake)).filter(
                    AppBetOrder.mb_id == relation.invitee_id,
                    AppBetOrder.bet_status.in_(
                        [BetStatus.Win, BetStatus.Lose, BetStatus.Draw, BetStatus.HalfWin, BetStatus.HalfLose]),
                    AppBetOrder.del_flag == 0
                ).scalar() or 0
                if total_turnover < activity.invitation_share_min_turnover:
                    continue

            qualified_count += 1
            qualified_invitee_ids.append(relation.invitee_id)

        if qualified_count == 0:
            return jsonify({
                'code': CONDITION_NOT_MET_CODE,
                'data': None,
                'message': 'No qualified invitees found. Please check the requirements.'
            }), 400

        # 计算奖励金额
        one_time_bonus = Decimal(str(activity.invitation_share_one_time_bonus))
        total_reward_amount = one_time_bonus * qualified_count

        # 检查奖金池余额
        if activity.bonus_pool_remaining is not None and activity.bonus_pool_remaining < total_reward_amount:
            return jsonify({
                'code': 1001,
                'data': None,
                'message': 'Insufficient bonus pool balance'
            }), 400

        # 扣除奖金池
        if activity.bonus_pool_remaining is not None:
            activity.bonus_pool_remaining = activity.bonus_pool_remaining - total_reward_amount
            activity.used_amount = (activity.used_amount or Decimal('0')) + total_reward_amount

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

        now = datetime.now()

        # 每个被邀请人创建一条独立记录，通过 referred_id 追踪避免重复发奖
        for invitee_id in qualified_invitee_ids:
            reward_record = MAppInvitationReward(
                id=Kits.generate_uuid(),
                activity_id=activity_id,
                rule_id=None,
                mb_id=user_id,
                referred_id=invitee_id,
                reward_amount=one_time_bonus,
                bonus_type='invitation_share_one_time',
                status='Claimed',
                claimed_at=now,
                create_time=now,
                create_by_id=user_id,
                del_flag=0,
                tenant_id='10000'
            )
            db.session.add(reward_record)

        # 计算流水要求
        turnover_multiplier = Decimal(str(activity.turnover_multiplier)) if hasattr(activity,
                                                                                    'turnover_multiplier') and activity.turnover_multiplier else Decimal(
            '1')
        req_turnover = total_reward_amount * turnover_multiplier

        # 计算净赢要求：只使用固定值
        req_netwin = Decimal(str(activity.net_win_amount)) if hasattr(activity,
                                                                      'net_win_amount') and activity.net_win_amount else Decimal(
            '0')

        # 判断应该转入哪个钱包
        use_main_wallet = should_use_main_wallet(activity, user_id)

        # 如果没有流水/净赢要求，直接标记为已达标
        initial_requirement_met = 1 if use_main_wallet else 0

        if use_main_wallet:
            # 转入主钱包
            old_balance = member.money if member.money else Decimal('0')
            new_balance = old_balance + total_reward_amount
            member.money = new_balance

            # 增加可提现金额
            old_withdrawable = member.money_promotion_withdrawable if member.money_promotion_withdrawable else Decimal(
                '0')
            member.money_promotion_withdrawable = old_withdrawable + total_reward_amount

            wallet_type = "Money"
            target_wallet = TransactionMap.Ewallet
        else:
            # 转入促销钱包
            old_balance = member.money_promotion if member.money_promotion else Decimal('0')
            new_balance = old_balance + total_reward_amount
            member.money_promotion = new_balance

            wallet_type = "Promotion"
            target_wallet = TransactionMap.ProWallet

        # 记录余额流水
        balance_log = AppMemberBalanceLog(
            id=Kits.generate_uuid(),
            sn=f"INVITE_ONETIME_{Kits.generate_uuid()}",
            type=TransactionType.Activity,
            type_sub=TransactionType.InvitationReward if hasattr(TransactionType,
                                                                 'InvitationReward') else TransactionType.Activity,
            type_sub_data_id=activity_id,
            mb_id=user_id,
            mb_username=member.username if hasattr(member, 'username') else None,
            money=total_reward_amount,
            start_balance=old_balance,
            end_balance=new_balance,
            create_by_id=user_id,
            update_by_id=user_id,
            aid=user.aid if hasattr(user, 'aid') else None,
            source="System",
            target=target_wallet,
            pay_wallet=wallet_type,
            status=1,
            source_status=0
        )
        db.session.add(balance_log)

        # 使用前面查询的活动参与记录（已确保存在）
        activity_record = activity_record_for_claim

        # 更新已存在的活动记录
        # 解析现有的 completion_detail
        existing_detail = {}
        if activity_record.completion_detail:
            try:
                existing_detail = json.loads(activity_record.completion_detail)
            except:
                existing_detail = {}

        # 周期管理：如果上一轮已达标（is_requirement_met=1），进入新一轮
        if activity_record.is_requirement_met == 1:
            new_settlement_round = (activity_record.settlement_round or 1) + 1
            new_bonus_current_round = total_reward_amount
            activity_record.is_requirement_met = 0
            activity_record.settlement_round = new_settlement_round
            activity_record.round_start_time = now  # 记录本轮开始时间
        else:
            new_settlement_round = activity_record.settlement_round or 1
            new_bonus_current_round = (activity_record.bonus_amount_current_round or Decimal('0')) + total_reward_amount
            # round_start_time 保持不变（本轮首次领取时已设置）
            if not activity_record.round_start_time:
                activity_record.round_start_time = now  # 兼容旧数据

        activity_record.bonus_amount_current_round = new_bonus_current_round

        # 基于当前轮奖励金额重新计算流水要求，净赢要求保持不变
        new_req_turnover = new_bonus_current_round * turnover_multiplier

        # 更新 completion_detail
        activity_record.completion_detail = json.dumps({
            'reward_amount': float((activity_record.bonus_amount or Decimal('0')) + total_reward_amount),
            'turnover_required': float(new_req_turnover),
            'settlement_round': new_settlement_round,
            'bonus_amount_current_round': float(new_bonus_current_round),
            'qualified_invitees': qualified_count,
            'one_time_bonus_per_invitee': float(one_time_bonus)
        })
        activity_record.req_turnover = new_req_turnover
        # req_netwin 保持不变，不更新
        activity_record.completion_condition = f'Round {new_settlement_round} Turnover: {float(new_req_turnover)}'

        # 累加奖励金额（历史总额）
        activity_record.bonus_amount = (activity_record.bonus_amount or Decimal('0')) + total_reward_amount

        # 如果本次领取无流水/净赢要求（直接进主钱包），则标记达标
        if initial_requirement_met == 1:
            activity_record.is_requirement_met = 1

        activity_record.update_time = now
        activity_record.update_by_id = user_id

        # 保存更改
        db.session.commit()

        # 记录成功的领取
        RiskManagementService.record_redemption_attempt(
            user_id=user_id,
            coupon_id=activity_id,
            ip=ip_address,
            imei=device_id,
            successful=True
        )

        return jsonify({
            'code': SUCCESS_CODE,
            'data': {
                'qualified_invitees': qualified_count,
                'one_time_bonus_per_invitee': float(one_time_bonus),
                'total_reward_amount': float(total_reward_amount),
                'turnover_requirement': float(req_turnover),
                'new_promotion_balance': float(new_balance),
                'claim_time': now.strftime('%Y-%m-%d %H:%M:%S')
            },
            'message': f'Successfully claimed one-time reward for {qualified_count} qualified invitees'
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': SYSTEM_ERROR_CODE,
            'data': None,
            'message': str(e)
        }), 500


@invitation_v2.route('/claim-deposit-share-reward', methods=['POST'])
@auth.login_required
def claim_deposit_share_reward():
    """
    领取存款分享奖励 (Method 2)

    请求体:
    {
        "activity_id": "活动ID",
        "deposit_id": "存款记录ID"  // 可选，如果不提供则领取所有未领取的存款分享奖励
    }
    """
    try:
        user_id = g.user.id
        user = g.user
        data = request.json
        activity_id = data.get('activity_id')
        deposit_id = data.get('deposit_id')  # 可选

        if not activity_id:
            return jsonify({
                'code': PARAM_ERROR_CODE,
                'data': None,
                'message': 'Activity ID is required'
            }), 400

        # 获取活动信息（加锁）
        activity = db.session.query(MAppInvitationActivity).filter(
            MAppInvitationActivity.id == activity_id,
            MAppInvitationActivity.del_flag == 0
        ).with_for_update().first()

        if not activity:
            return jsonify({
                'code': ACTIVITY_NOT_FOUND_CODE,
                'data': None,
                'message': 'Activity does not exist'
            }), 404

        # 检查活动是否有效
        if not is_activity_valid(activity):
            return jsonify({
                'code': ACTIVITY_NOT_VALID_CODE,
                'data': None,
                'message': 'Activity is not valid or has expired'
            }), 400

        # 检查访问权限
        if not check_user_agent_access(user, activity):
            return jsonify({
                'code': PARAM_ERROR_CODE,
                'data': None,
                'message': 'You are not authorized to access this activity'
            }), 403

        # 检查 Method 2 是否启用
        if not hasattr(activity, 'method_deposit_enabled') or activity.method_deposit_enabled != 1:
            return jsonify({
                'code': ACTIVITY_NOT_VALID_CODE,
                'data': None,
                'message': 'Deposit share method is not enabled for this activity'
            }), 400

        # 【新增】检查用户是否已参与活动
        # 注意：这里查询的记录会在后面复用，避免重复查询
        activity_record_for_claim = AppPlayerActivityRecord.query.filter_by(
            mb_id=user_id,
            activity_type='INVITATION',
            activity_id=activity_id,
            status='Active',
            del_flag=0
        ).first()

        if not activity_record_for_claim:
            return jsonify({
                'code': CONDITION_NOT_MET_CODE,
                'data': None,
                'message': 'Please join the activity first before claiming rewards',
                'need_join': True
            }), 400

        # 获取存款分享配置
        deposit_share_tiers = MAppInvitationDepositShare.query.filter(
            MAppInvitationDepositShare.activity_id == activity_id,
            MAppInvitationDepositShare.del_flag == 0
        ).order_by(MAppInvitationDepositShare.sequence).all()

        if not deposit_share_tiers:
            return jsonify({
                'code': PARAM_ERROR_CODE,
                'data': None,
                'message': 'Deposit share configuration not found'
            }), 400

        # 风险检查
        ip_address = request.remote_addr
        user_agent_str = request.headers.get('User-Agent')
        device_id = (request.headers.get('X-Device-ID') or
                     request.headers.get('Device-ID') or
                     request.headers.get('X-Device-IMEI') or
                     request.headers.get('IMEI'))

        risk_check, risk_msg = perform_risk_check(user_id, activity_id, activity, ip_address, device_id, user_agent_str)
        if not risk_check:
            return jsonify({
                'code': RISK_CHECK_FAILED_CODE,
                'data': None,
                'message': risk_msg
            }), 400

        # 检查优惠券和邀请活动互斥
        exclusion_check, exclusion_msg = check_coupon_invitation_exclusion(user_id, activity)
        if not exclusion_check:
            return jsonify({
                'code': CONDITION_NOT_MET_CODE,
                'data': None,
                'message': exclusion_msg
            }), 400

        # 获取被邀请人列表（只统计计入活动的）
        promotion_relations_m2 = MAppPromotionRelation.query.join(
            AppMember, MAppPromotionRelation.invitee_id == AppMember.id
        ).filter(
            MAppPromotionRelation.promoter_id == user_id,
            MAppPromotionRelation.status == 'Active',
            MAppPromotionRelation.is_counted_in_activity == True,  # 只统计计入活动的
            MAppPromotionRelation.del_flag == 0,
            AppMember.create_time >= activity.start_date,
            AppMember.create_time <= activity.end_date
        ).all()

        if not promotion_relations_m2:
            return jsonify({
                'code': CONDITION_NOT_MET_CODE,
                'data': None,
                'message': 'No invitees found'
            }), 400

        invitee_ids = [rel.invitee_id for rel in promotion_relations_m2]

        # 查询符合条件的充值记录
        # ✅ 修复：按充值时间升序排序，确保先到先领，与进度查询逻辑一致
        deposit_query = Charge.query.filter(
            Charge.mb_id.in_(invitee_ids),
            Charge.status == 'Success',
            Charge.del_flag == 0,
            Charge.create_time >= activity.start_date,
            Charge.create_time <= activity.end_date
        ).order_by(Charge.create_time.asc())

        if deposit_id:
            deposit_query = deposit_query.filter(Charge.id == deposit_id)

        deposits = deposit_query.all()

        if not deposits:
            return jsonify({
                'code': CONDITION_NOT_MET_CODE,
                'data': None,
                'message': 'No qualified deposits found'
            }), 400

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

        now = datetime.now()
        total_reward_amount = Decimal('0')
        claimed_deposits = []

        # ✅ 优化1: 预先查询所有已领取的奖励（避免在循环中重复查询）
        all_claimed_rewards = MAppInvitationReward.query.filter(
            MAppInvitationReward.mb_id == user_id,
            MAppInvitationReward.activity_id == activity_id,
            MAppInvitationReward.bonus_type == 'deposit_share',
            MAppInvitationReward.del_flag == 0
        ).all()

        # ✅ 优化2: 预先统计每个档位的已领取次数（避免嵌套循环中查询）
        tier_claimed_counts = {}
        for tier in deposit_share_tiers:
            if hasattr(tier, 'max_claims') and tier.max_claims is not None and tier.max_claims > 0:
                # 统计该档位已领取的次数（包括 claimed 和 pending）
                count = sum(1 for r in all_claimed_rewards
                            if r.rule_id == tier.id and r.status in ['Claimed', 'Pending'])
                tier_claimed_counts[tier.id] = count
            else:
                tier_claimed_counts[tier.id] = 0

        # 处理每笔充值
        for deposit in deposits:
            # ✅ 优化3: 在内存中检查是否已领取（不查数据库）
            existing_reward = next((r for r in all_claimed_rewards
                                    if r.meta_data and f'"deposit_id": "{deposit.id}"' in r.meta_data), None)

            if existing_reward:
                continue

            deposit_amount = Decimal(str(deposit.amount))

            # 匹配存款档位
            matched_tier = None
            for tier in deposit_share_tiers:
                min_dep = Decimal(str(tier.min_deposit)) if tier.min_deposit else Decimal('0')
                max_dep = Decimal(str(tier.max_deposit)) if tier.max_deposit else None

                if deposit_amount >= min_dep:
                    if max_dep is None or deposit_amount <= max_dep:
                        # ✅ 优化4: 直接使用预先统计的次数（不查数据库）
                        if hasattr(tier, 'max_claims') and tier.max_claims is not None and tier.max_claims > 0:
                            claimed_count = tier_claimed_counts.get(tier.id, 0)

                            if claimed_count >= tier.max_claims:
                                # 该档位已达到最大领取次数，跳过
                                continue

                        matched_tier = tier
                        break

            if not matched_tier:
                continue

            # 计算奖励金额
            bonus_rate = Decimal(str(matched_tier.bonus_rate)) / Decimal('100')
            reward_amount = deposit_amount * bonus_rate

            # 检查奖金池余额
            if activity.bonus_pool_remaining is not None and activity.bonus_pool_remaining < reward_amount:
                continue

            # 扣除奖金池
            if activity.bonus_pool_remaining is not None:
                activity.bonus_pool_remaining = activity.bonus_pool_remaining - reward_amount
                activity.used_amount = (activity.used_amount or Decimal('0')) + reward_amount

            # 创建奖励领取记录
            reward_record = MAppInvitationReward(
                id=Kits.generate_uuid(),
                activity_id=activity_id,
                rule_id=matched_tier.id,
                mb_id=user_id,
                referred_id=deposit.mb_id,
                reward_amount=reward_amount,
                bonus_type='deposit_share',
                status='Claimed',
                claimed_at=now,
                meta_data=json.dumps({  # ✅ 修复：使用正确的字段名 meta_data
                    'deposit_id': deposit.id,
                    'deposit_amount': float(deposit_amount),
                    'bonus_rate': float(matched_tier.bonus_rate),
                    'tier_id': matched_tier.id
                }),
                create_time=now,
                create_by_id=user_id,
                del_flag=0,
                tenant_id='10000'
            )
            db.session.add(reward_record)

            # ✅ 优化5: 更新档位计数（确保同一请求中的多笔充值次数限制正确）
            tier_claimed_counts[matched_tier.id] = tier_claimed_counts.get(matched_tier.id, 0) + 1

            total_reward_amount += reward_amount
            claimed_deposits.append({
                'deposit_id': deposit.id,
                'deposit_amount': float(deposit_amount),
                'bonus_rate': float(matched_tier.bonus_rate),
                'reward_amount': float(reward_amount)
            })

        if not claimed_deposits:
            return jsonify({
                'code': CONDITION_NOT_MET_CODE,
                'data': None,
                'message': 'No rewards available to claim. All deposits may have been claimed already.'
            }), 400

        # 计算流水要求
        turnover_multiplier = Decimal(str(activity.turnover_multiplier)) if hasattr(activity,
                                                                                    'turnover_multiplier') and activity.turnover_multiplier else Decimal(
            '1')
        req_turnover = total_reward_amount * turnover_multiplier

        # 计算净赢要求：只使用固定值
        req_netwin = Decimal(str(activity.net_win_amount)) if hasattr(activity,
                                                                      'net_win_amount') and activity.net_win_amount else Decimal(
            '0')

        # 判断应该转入哪个钱包
        use_main_wallet = should_use_main_wallet(activity, user_id)

        # 如果没有流水/净赢要求，直接标记为已达标
        initial_requirement_met = 1 if use_main_wallet else 0

        if use_main_wallet:
            # 转入主钱包
            old_balance = member.money if member.money else Decimal('0')
            new_balance = old_balance + total_reward_amount
            member.money = new_balance

            # 增加可提现金额
            old_withdrawable = member.money_promotion_withdrawable if member.money_promotion_withdrawable else Decimal(
                '0')
            member.money_promotion_withdrawable = old_withdrawable + total_reward_amount

            wallet_type = "Money"
            target_wallet = TransactionMap.Ewallet
        else:
            # 转入促销钱包
            old_balance = member.money_promotion if member.money_promotion else Decimal('0')
            new_balance = old_balance + total_reward_amount
            member.money_promotion = new_balance

            wallet_type = "Promotion"
            target_wallet = TransactionMap.ProWallet

        # 记录余额流水
        balance_log = AppMemberBalanceLog(
            id=Kits.generate_uuid(),
            sn=f"INVITE_DEPOSIT_{Kits.generate_uuid()}",
            type=TransactionType.Activity,
            type_sub=TransactionType.InvitationReward if hasattr(TransactionType,
                                                                 'InvitationReward') else TransactionType.Activity,
            type_sub_data_id=activity_id,
            mb_id=user_id,
            mb_username=member.username if hasattr(member, 'username') else None,
            money=total_reward_amount,
            start_balance=old_balance,
            end_balance=new_balance,
            create_by_id=user_id,
            update_by_id=user_id,
            aid=user.aid if hasattr(user, 'aid') else None,
            source="System",
            target=target_wallet,
            pay_wallet=wallet_type,
            status=1,
            source_status=0
        )
        db.session.add(balance_log)

        # 使用前面查询的活动参与记录（已确保存在）
        activity_record = activity_record_for_claim

        # 更新已存在的活动记录
        # 解析现有的 completion_detail
        existing_detail = {}
        if activity_record.completion_detail:
            try:
                existing_detail = json.loads(activity_record.completion_detail)
            except:
                existing_detail = {}

        # 累加奖励金额
        existing_reward = Decimal(str(existing_detail.get('reward_amount', 0)))
        new_total_reward = existing_reward + total_reward_amount

        # 基于总奖励金额重新计算流水要求，净赢要求保持不变
        new_req_turnover = new_total_reward * turnover_multiplier

        # 更新 completion_detail
        existing_claimed_count = existing_detail.get('claimed_deposits_count', 0)
        new_claimed_count = existing_claimed_count + len(claimed_deposits)

        activity_record.completion_detail = json.dumps({
            'reward_amount': float(new_total_reward),
            'turnover_required': float(new_req_turnover),
            'claimed_deposits_count': new_claimed_count
        })
        activity_record.req_turnover = new_req_turnover
        # req_netwin 保持不变，不更新
        activity_record.completion_condition = f'Turnover: {float(new_req_turnover)}'

        # 累加奖励金额（用于Java端结算时检查是否已领取奖励）
        activity_record.bonus_amount = (activity_record.bonus_amount or Decimal('0')) + total_reward_amount

        # 更新达标状态：如果已达标或本次领取无要求，则保持/设置为已达标
        if activity_record.is_requirement_met == 1 or initial_requirement_met == 1:
            activity_record.is_requirement_met = 1

        activity_record.update_time = now
        activity_record.update_by_id = user_id

        # 保存更改
        db.session.commit()

        # 记录成功的领取
        RiskManagementService.record_redemption_attempt(
            user_id=user_id,
            coupon_id=activity_id,
            ip=ip_address,
            imei=device_id,
            successful=True
        )

        return jsonify({
            'code': SUCCESS_CODE,
            'data': {
                'claimed_deposits': claimed_deposits,
                'total_reward_amount': float(total_reward_amount),
                'turnover_requirement': float(req_turnover),
                'new_promotion_balance': float(new_balance),
                'claim_time': now.strftime('%Y-%m-%d %H:%M:%S')
            },
            'message': f'Successfully claimed deposit share rewards for {len(claimed_deposits)} deposits'
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': SYSTEM_ERROR_CODE,
            'data': None,
            'message': str(e)
        }), 500


@invitation_v2.route('/history', methods=['GET'])
@auth.login_required
def get_reward_history():
    """
    获取邀请奖励历史记录
    参考 CouponController.get_redemption_history

    Query参数:
    - status: Unused/Used/Expired（可选，与优惠券保持一致的风格）
    - activity_id: 活动ID（可选）
    - page: 页码
    - page_size: 每页数量
    """
    try:
        user_id = g.user.id
        page = int(request.args.get('page', 1))
        page_size = min(int(request.args.get('page_size', 20)), 100)
        status = request.args.get('status')
        activity_id = request.args.get('activity_id')

        # 构建查询
        query = MAppInvitationReward.query.filter(
            MAppInvitationReward.mb_id == user_id,
            MAppInvitationReward.del_flag == 0
        )

        if status:
            if status == 'Used':
                query = query.filter(MAppInvitationReward.status == 'Claimed')
            elif status == 'Unused':
                query = query.filter(MAppInvitationReward.status == 'Pending')
            elif status == 'Expired':
                query = query.filter(MAppInvitationReward.status == 'invalid')

        if activity_id:
            query = query.filter(MAppInvitationReward.activity_id == activity_id)

        # 获取总数
        total_count = query.count()

        # 分页
        offset = (page - 1) * page_size
        rewards = query.order_by(MAppInvitationReward.create_time.desc()).offset(offset).limit(page_size).all()

        # 格式化返回数据
        history_list = []
        for r in rewards:
            # 获取活动信息
            activity = MAppInvitationActivity.query.filter_by(id=r.activity_id).first()
            # 获取规则信息
            rule = MAppInvitationAchievement.query.filter_by(id=r.rule_id).first()

            history_info = {
                'id': r.id,
                'activity_id': r.activity_id,
                'activity_title': activity.title if activity else 'Unknown',
                'rule_id': r.rule_id,
                'rule_type': rule.rule_type if rule else None,
                'rule_description': rule.description if rule else None,
                'reward_amount': float(r.reward_amount) if r.reward_amount else 0,
                'bonus_type': r.bonus_type,
                'status': r.status,
                'claimed_at': r.claimed_at.strftime('%Y-%m-%d %H:%M:%S') if r.claimed_at else None,
                'create_time': r.create_time.strftime('%Y-%m-%d %H:%M:%S') if r.create_time else None
            }
            history_list.append(history_info)

        # 统计信息
        total_claimed = db.session.query(func.sum(MAppInvitationReward.reward_amount)).filter(
            MAppInvitationReward.mb_id == user_id,
            MAppInvitationReward.status == 'Claimed',
            MAppInvitationReward.del_flag == 0
        ).scalar() or 0

        total_pending = db.session.query(func.sum(MAppInvitationReward.reward_amount)).filter(
            MAppInvitationReward.mb_id == user_id,
            MAppInvitationReward.status == 'Pending',
            MAppInvitationReward.del_flag == 0
        ).scalar() or 0

        return jsonify({
            'code': SUCCESS_CODE,
            'data': {
                'history': ensure_serializable(history_list),
                'pagination': {
                    'current_page': page,
                    'page_size': page_size,
                    'total_count': total_count,
                    'total_pages': (total_count + page_size - 1) // page_size
                },
                'statistics': {
                    'total_claimed': float(total_claimed),
                    'total_pending': float(total_pending),
                    'total_records': total_count
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


@invitation_v2.route('/activity/<string:activity_id>/progress', methods=['GET'])
@auth.login_required
def get_activity_detailed_progress(activity_id):
    """
    获取用户在特定活动的详细进度
    包括完整的邀请统计、规则进度、佣金统计等
    参考 CouponController.get_coupon_progress
    """
    try:
        user_id = g.user.id
        user = g.user

        # 获取活动信息
        activity = MAppInvitationActivity.query.filter_by(
            id=activity_id,
            del_flag=0
        ).first()

        if not activity:
            return jsonify({
                'code': ACTIVITY_NOT_FOUND_CODE,
                'data': None,
                'message': 'Activity does not exist'
            }), 404

        # 检查访问权限
        if not check_user_agent_access(user, activity):
            return jsonify({
                'code': PARAM_ERROR_CODE,
                'data': None,
                'message': 'You are not authorized to access this activity'
            }), 403

        # 统计被邀请人数量（只统计计入活动的）
        total_invitees = MAppPromotionRelation.query.filter(
            MAppPromotionRelation.promoter_id == user_id,
            MAppPromotionRelation.status == 'Active',
            MAppPromotionRelation.is_counted_in_activity == True,  # 只统计计入活动的
            MAppPromotionRelation.del_flag == 0
        ).count()

        # 活动期间被邀请人数量（只统计计入活动的）
        period_invitees = MAppPromotionRelation.query.join(
            AppMember, MAppPromotionRelation.invitee_id == AppMember.id
        ).filter(
            MAppPromotionRelation.promoter_id == user_id,
            MAppPromotionRelation.status == 'Active',
            MAppPromotionRelation.is_counted_in_activity == True,  # 只统计计入活动的
            MAppPromotionRelation.del_flag == 0,
            AppMember.create_time >= activity.start_date,
            AppMember.create_time <= activity.end_date
        ).count()

        # 统计被邀请人总存款（活动期间，只统计计入活动的）
        promotion_relations_progress = MAppPromotionRelation.query.filter(
            MAppPromotionRelation.promoter_id == user_id,
            MAppPromotionRelation.status == 'Active',
            MAppPromotionRelation.is_counted_in_activity == True,  # 只统计计入活动的
            MAppPromotionRelation.del_flag == 0
        ).all()

        total_invitee_deposits = 0
        total_invitee_turnover = 0
        for relation in promotion_relations_progress:
            deposits = db.session.query(func.sum(Charge.amount)).filter(
                Charge.mb_id == relation.invitee_id,
                Charge.status == 'Success',
                Charge.del_flag == 0,
                Charge.create_time >= activity.start_date,
                Charge.create_time <= activity.end_date
            ).scalar() or 0
            total_invitee_deposits += float(deposits)

            turnover = db.session.query(func.sum(AppBetOrder.stake)).filter(
                AppBetOrder.mb_id == relation.invitee_id,
                AppBetOrder.bet_status.in_(
                    [BetStatus.Win, BetStatus.Lose, BetStatus.Draw, BetStatus.HalfWin, BetStatus.HalfLose]),
                AppBetOrder.del_flag == 0,
                AppBetOrder.create_time >= activity.start_date,
                AppBetOrder.create_time <= activity.end_date
            ).scalar() or 0
            total_invitee_turnover += float(turnover)

        # 规则进度
        rules_progress = []
        total_claimable = 0
        if hasattr(activity, 'method_invitation_enabled') and activity.method_invitation_enabled == 1:
            rules = MAppInvitationAchievement.query.filter_by(
                activity_id=activity_id,
                del_flag=0
            ).order_by(MAppInvitationAchievement.sequence).all()

            for rule in rules:
                progress = calculate_rule_progress(user_id, activity, rule)
                rule_progress = {
                    'rule_id': rule.id,
                    'rule_type': rule.rule_type,
                    'description': rule.description,
                    'threshold_value': rule.threshold_value if rule.threshold_value else 0,
                    'reward_amount': rule.reward_amount if rule.reward_amount else 0,
                    **progress
                }
                rules_progress.append(rule_progress)

                if progress['can_claim']:
                    total_claimable += float(rule.reward_amount) if rule.reward_amount else 0

        # 佣金统计
        total_pending_commission = db.session.query(func.sum(MAppCommissionRecord.amount)).filter(
            MAppCommissionRecord.activity_id == activity_id,
            MAppCommissionRecord.user_id == user_id,  # 我作为邀请人（受益人）
            MAppCommissionRecord.status == 'Pending',
            MAppCommissionRecord.del_flag == 0
        ).scalar() or 0

        total_paid_commission = db.session.query(func.sum(MAppCommissionRecord.amount)).filter(
            MAppCommissionRecord.activity_id == activity_id,
            MAppCommissionRecord.user_id == user_id,  # 我作为邀请人（受益人）
            MAppCommissionRecord.status == 'Paid',
            MAppCommissionRecord.del_flag == 0
        ).scalar() or 0

        # 已领取的奖励总额
        total_rewards_claimed = db.session.query(func.sum(MAppInvitationReward.reward_amount)).filter(
            MAppInvitationReward.activity_id == activity_id,
            MAppInvitationReward.mb_id == user_id,
            MAppInvitationReward.status == 'Claimed',
            MAppInvitationReward.del_flag == 0
        ).scalar() or 0

        return jsonify({
            'code': SUCCESS_CODE,
            'data': {
                'activity_id': activity_id,
                'activity_title': activity.title,
                'is_valid': is_activity_valid(activity),
                # 邀请统计
                'invitee_stats': {
                    'total_invitees': total_invitees,
                    'period_invitees': period_invitees,
                    'total_invitee_deposits': total_invitee_deposits,
                    'total_invitee_turnover': total_invitee_turnover
                },
                # 规则进度
                'rules_progress': ensure_serializable(rules_progress),
                'total_claimable': total_claimable,
                # 佣金统计
                'commission_stats': {
                    'pending': float(total_pending_commission),
                    'paid': float(total_paid_commission),
                    'total': float(total_pending_commission + total_paid_commission)
                },
                # 已领取奖励
                'total_rewards_claimed': float(total_rewards_claimed)
            },
            'message': 'success'
        }), 200


    except Exception as e:
        return jsonify({
            'code': SYSTEM_ERROR_CODE,
            'data': None,
            'message': str(e)
        }), 500


@invitation_v2.route('/current_activity', methods=['GET'])
@auth.login_required
def get_current_invitation_activity():
    """
    获取用户当前参与的邀请活动信息
    参考 CouponController.get_current_coupon_activity
    """
    try:
        user_id = g.user.id
        user = g.user

        # 获取用户信息
        member = AppMember.query.filter_by(id=user_id, del_flag=0).first()
        if not member:
            return jsonify({
                'code': PARAM_ERROR_CODE,
                'data': None,
                'message': 'User not found'
            }), 404

        # 查询用户最新的邀请活动参与记录
        activity_record = AppPlayerActivityRecord.query.filter(
            AppPlayerActivityRecord.mb_id == user_id,
            AppPlayerActivityRecord.activity_type == 'INVITATION',
            AppPlayerActivityRecord.del_flag == 0
        ).order_by(AppPlayerActivityRecord.create_time.desc()).first()

        if not activity_record:
            return jsonify({
                'code': SUCCESS_CODE,
                'data': {
                    'has_activity': False
                },
                'message': 'No invitation activity found'
            }), 200

        # 获取活动配置信息
        activity = MAppInvitationActivity.query.filter_by(
            id=activity_record.activity_id,
            del_flag=0
        ).first()

        if not activity:
            return jsonify({
                'code': SUCCESS_CODE,
                'data': {
                    'has_activity': False
                },
                'message': 'Activity not found'
            }), 200

        # 统计被邀请人数量（只统计计入活动的）
        total_invitees = MAppPromotionRelation.query.filter(
            MAppPromotionRelation.promoter_id == user_id,
            MAppPromotionRelation.status == 'Active',
            MAppPromotionRelation.is_counted_in_activity == True,  # 只统计计入活动的
            MAppPromotionRelation.del_flag == 0
        ).count()

        # 统计总奖励
        total_rewards = db.session.query(func.sum(MAppInvitationReward.reward_amount)).filter(
            MAppInvitationReward.activity_id == activity.id,
            MAppInvitationReward.mb_id == user_id,
            MAppInvitationReward.status == 'Claimed',
            MAppInvitationReward.del_flag == 0
        ).scalar() or 0

        # 统计待发放佣金
        pending_commission = db.session.query(func.sum(MAppCommissionRecord.amount)).filter(
            MAppCommissionRecord.activity_id == activity.id,
            MAppCommissionRecord.user_id == user_id,  # 我作为邀请人（受益人）
            MAppCommissionRecord.status == 'Pending',
            MAppCommissionRecord.del_flag == 0
        ).scalar() or 0

        result = {
            'has_activity': True,
            'activity_id': activity.id,
            'activity_name': activity.title,
            'activity_record_id': activity_record.id,
            'status': activity_record.status,
            'start_time': activity_record.start_time.strftime(
                '%Y-%m-%d %H:%M:%S') if activity_record.start_time else None,
            'end_time': activity_record.end_time.strftime('%Y-%m-%d %H:%M:%S') if activity_record.end_time else None,
            # 用户促销钱包余额
            'money_promotion': float(member.money_promotion) if member.money_promotion else 0,
            # 统计数据
            'total_invitees': total_invitees,
            'total_rewards_claimed': float(total_rewards),
            'pending_commission': float(pending_commission),
            # 活动时间
            'activity_start_date': activity.start_date.strftime('%Y-%m-%d %H:%M:%S') if activity.start_date else None,
            'activity_end_date': activity.end_date.strftime('%Y-%m-%d %H:%M:%S') if activity.end_date else None,
            'is_activity_valid': is_activity_valid(activity)
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


@invitation_v2.route('/invitees', methods=['GET'])
@auth.login_required
def get_my_invitees():
    """
    获取我邀请的用户列表
    """
    try:
        user_id = g.user.id
        page = int(request.args.get('page', 1))
        page_size = min(int(request.args.get('page_size', 20)), 100)
        activity_id = request.args.get('activity_id')  # 可选，按活动时间筛选

        # 构建查询（只统计计入活动的）
        query = MAppPromotionRelation.query.join(
            AppMember, MAppPromotionRelation.invitee_id == AppMember.id
        ).filter(
            MAppPromotionRelation.promoter_id == user_id,
            MAppPromotionRelation.status == 'Active',
            MAppPromotionRelation.is_counted_in_activity == True,  # 只统计计入活动的
            MAppPromotionRelation.del_flag == 0
        )

        # 如果指定了活动ID，按活动时间筛选
        if activity_id:
            activity = MAppInvitationActivity.query.filter_by(id=activity_id, del_flag=0).first()
            if activity:
                query = query.filter(
                    AppMember.create_time >= activity.start_date,
                    AppMember.create_time <= activity.end_date
                )

        # 获取总数
        total_count = query.count()

        # 分页
        offset = (page - 1) * page_size
        promotion_relations_list = query.order_by(AppMember.create_time.desc()).offset(offset).limit(page_size).all()

        # 格式化返回数据
        invitee_list = []
        for relation in promotion_relations_list:
            invitee_id = relation.invitee_id
            # 获取被邀请人信息
            invitee = AppMember.query.filter_by(id=invitee_id, del_flag=0).first()
            if not invitee:
                continue

            # 统计充值总额
            total_deposit = db.session.query(func.sum(Charge.amount)).filter(
                Charge.mb_id == invitee_id,
                Charge.status == 'Success',
                Charge.del_flag == 0
            ).scalar() or 0

            # 统计投注总额
            total_bet = db.session.query(func.sum(AppBetOrder.stake)).filter(
                AppBetOrder.mb_id == invitee_id,
                AppBetOrder.bet_status.in_(
                    [BetStatus.Win, BetStatus.Lose, BetStatus.Draw, BetStatus.HalfWin, BetStatus.HalfLose]),
                AppBetOrder.del_flag == 0
            ).scalar() or 0

            # 隐藏用户名中间部分
            username = invitee.username if hasattr(invitee, 'username') else invitee.login_name
            if username and len(username) > 4:
                masked_username = username[:2] + '***' + username[-2:]
            else:
                masked_username = username

            invitee_info = {
                'id': invitee.id,
                'username': masked_username,
                'register_date': invitee.create_time.strftime('%Y-%m-%d %H:%M:%S') if invitee.create_time else None,
                'total_deposit': float(total_deposit),
                'total_bet': float(total_bet),
                'status': invitee.status if hasattr(invitee, 'status') else 1
            }
            invitee_list.append(invitee_info)

        return jsonify({
            'code': SUCCESS_CODE,
            'data': {
                'invitees': invitee_list,
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


def get_current_period_range(frequency):
    """
    根据结算频率计算当前结算周期的起止时间
    返回 (start_dt, end_dt, period_str)
    """
    from datetime import date, time
    today = datetime.now().date()
    if frequency == 'weekly':
        start = today - timedelta(days=today.weekday())  # 本周一
        end = start + timedelta(days=7)
        iso = today.isocalendar()
        period_str = f"{iso[0]}-W{iso[1]:02d}"
    elif frequency == 'monthly':
        start = today.replace(day=1)
        if today.month == 12:
            end = today.replace(year=today.year + 1, month=1, day=1)
        else:
            end = today.replace(month=today.month + 1, day=1)
        period_str = today.strftime('%Y-%m')
    else:  # manual / 其他，默认按当月
        start = today.replace(day=1)
        if today.month == 12:
            end = today.replace(year=today.year + 1, month=1, day=1)
        else:
            end = today.replace(month=today.month + 1, day=1)
        period_str = today.strftime('%Y-%m')
    start_dt = datetime.combine(start, time.min)
    end_dt = datetime.combine(end, time.min)
    return start_dt, end_dt, period_str


def calculate_win_loss_commission_realtime(user_id, activity):
    """
    实时计算 Method 3 win_loss 类型的预估佣金。
    逻辑与 Java previewWinLossSettlement 对齐：
      - 找到该用户邀请的所有被邀请人
      - 统计他们在当前结算周期内已结算订单的 -netwin_actual（平台盈利）
      - 平台净盈利 > 0 时，佣金 = 平台盈利 × commission_rate / 100
    """
    commission_rate = activity.commission_rate
    if not commission_rate:
        return {
            'estimated_amount': Decimal('0'),
            'platform_profit': Decimal('0'),
            'total_stake': Decimal('0'),
            'invitee_count': 0,
            'order_count': 0,
            'period_str': '',
            'start_date': None,
            'end_date': None,
        }

    start_dt, end_dt, period_str = get_current_period_range(activity.profit_share_frequency)

    relations = MAppPromotionRelation.query.filter(
        MAppPromotionRelation.promoter_id == user_id,
        MAppPromotionRelation.activity_id == activity.id,
        MAppPromotionRelation.status == 'Active',
        MAppPromotionRelation.del_flag == 0
    ).all()

    if not relations:
        return {
            'estimated_amount': Decimal('0'),
            'platform_profit': Decimal('0'),
            'total_stake': Decimal('0'),
            'invitee_count': 0,
            'order_count': 0,
            'period_str': period_str,
            'start_date': start_dt,
            'end_date': end_dt,
        }

    invitee_ids = [r.invitee_id for r in relations]

    settled_statuses = [
        BetStatus.Win, BetStatus.Lose, BetStatus.Draw,
        BetStatus.Cancel, BetStatus.Refund, BetStatus.HalfWin, BetStatus.HalfLose
    ]
    orders = AppBetOrder.query.filter(
        AppBetOrder.mb_id.in_(invitee_ids),
        AppBetOrder.bet_status.in_(settled_statuses),
        AppBetOrder.create_time >= start_dt,
        AppBetOrder.create_time < end_dt,
        AppBetOrder.del_flag == 0
    ).all()

    total_platform_profit = Decimal('0')
    total_stake = Decimal('0')
    for order in orders:
        netwin_actual = order.netwin_actual or Decimal('0')
        total_platform_profit += -netwin_actual  # 平台盈利 = -netwin_actual
        total_stake += order.stake or Decimal('0')

    estimated_amount = Decimal('0')
    if total_platform_profit > 0:
        estimated_amount = (total_platform_profit * commission_rate / 100).quantize(Decimal('0.01'))

    return {
        'estimated_amount': estimated_amount,
        'platform_profit': total_platform_profit,
        'total_stake': total_stake,
        'invitee_count': len(invitee_ids),
        'order_count': len(orders),
        'period_str': period_str,
        'start_date': start_dt,
        'end_date': end_dt,
    }


@invitation_v2.route('/commissions', methods=['GET'])
@auth.login_required
def get_my_commissions():
    """
    获取我的佣金记录（Method 3 & 4）

    参数：
    - commission_type: 佣金类型
      · method3_turnover: Method 3 基于流水
      · method3_win_loss: Method 3 基于净赢
      · method4_invitee_bet: Method 4 被邀请人投注返佣
    """
    try:
        user_id = g.user.id
        page = int(request.args.get('page', 1))
        page_size = min(int(request.args.get('page_size', 20)), 100)
        activity_id = request.args.get('activity_id')
        status = request.args.get('status')  # Pending/Paid/Cancelled
        commission_type = request.args.get('commission_type')  # method3_turnover/method3_win_loss/method4_invitee_bet

        # ── method3_win_loss：结算前 m_app_commission_record 无记录，直接实时计算 ──
        if commission_type == 'method3_win_loss':
            # 找到关联的 win_loss 活动
            act_query = MAppInvitationActivity.query.filter(
                MAppInvitationActivity.commission_type == 'win_loss',
                MAppInvitationActivity.method_commission_enabled == 1,
                MAppInvitationActivity.del_flag == 0
            )
            if activity_id:
                act_query = act_query.filter(MAppInvitationActivity.id == activity_id)
            activities = act_query.all()

            commission_list = []

            # 当前周期实时预估（每个活动一条）
            for act in activities:
                rt = calculate_win_loss_commission_realtime(user_id, act)
                commission_list.append({
                    'id': None,
                    'activity_id': act.id,
                    'activity_title': act.title,
                    'commission_type': 'WIN_LOSS_COMMISSION',
                    'base_amount': float(rt['platform_profit']),
                    'commission_rate': float(act.commission_rate or 0),
                    'commission_amount': float(rt['estimated_amount']),
                    'status': 'Estimated',  # 标记为预估，尚未结算
                    'invitee_count': rt['invitee_count'],
                    'order_count': rt['order_count'],
                    'total_stake': float(rt['total_stake']),
                    'settlement_period': rt['period_str'],
                    'period_start': rt['start_date'].strftime('%Y-%m-%d') if rt['start_date'] else None,
                    'period_end': rt['end_date'].strftime('%Y-%m-%d') if rt['end_date'] else None,
                    'paid_at': None,
                    'create_time': None,
                })

            # 历史已结算记录（从 DB 查）
            history_query = MAppCommissionRecord.query.filter(
                MAppCommissionRecord.user_id == user_id,
                MAppCommissionRecord.sub_type == 'WIN_LOSS_COMMISSION',
                MAppCommissionRecord.del_flag == 0
            )
            if activity_id:
                history_query = history_query.filter(MAppCommissionRecord.activity_id == activity_id)
            if status and status != 'Estimated':
                history_query = history_query.filter(MAppCommissionRecord.status == status)

            history_total = history_query.count()
            offset = (page - 1) * page_size
            history_records = history_query.order_by(
                MAppCommissionRecord.create_time.desc()
            ).offset(offset).limit(page_size).all()

            for c in history_records:
                act = MAppInvitationActivity.query.filter_by(id=c.activity_id).first()
                commission_list.append({
                    'id': c.id,
                    'activity_id': c.activity_id,
                    'activity_title': act.title if act else 'Unknown',
                    'commission_type': c.sub_type,
                    'base_amount': float(c.base_amount) if c.base_amount else 0,
                    'commission_rate': float(c.rate) if c.rate else 0,
                    'commission_amount': float(c.amount) if c.amount else 0,
                    'status': c.status,
                    'invitee_count': None,
                    'order_count': None,
                    'total_stake': None,
                    'settlement_period': c.settle_period,
                    'period_start': None,
                    'period_end': None,
                    'paid_at': c.payout_time.strftime('%Y-%m-%d %H:%M:%S') if c.payout_time else None,
                    'create_time': c.create_time.strftime('%Y-%m-%d %H:%M:%S') if c.create_time else None,
                })

            estimated_total = sum(
                float(item['commission_amount']) for item in commission_list if item['status'] == 'Estimated'
            )
            paid_total = db.session.query(func.sum(MAppCommissionRecord.amount)).filter(
                MAppCommissionRecord.user_id == user_id,
                MAppCommissionRecord.sub_type == 'WIN_LOSS_COMMISSION',
                MAppCommissionRecord.status == 'Paid',
                MAppCommissionRecord.del_flag == 0
            ).scalar() or Decimal('0')

            return jsonify({
                'code': SUCCESS_CODE,
                'data': {
                    'commissions': commission_list,
                    'pagination': {
                        'current_page': page,
                        'page_size': page_size,
                        'total_count': len(activities) + history_total,
                        'total_pages': max(1, (history_total + page_size - 1) // page_size),
                    },
                    'statistics': {
                        'estimated_current_period': estimated_total,
                        'total_paid': float(paid_total),
                        'total': estimated_total + float(paid_total),
                    }
                },
                'message': 'success'
            }), 200

        # ── 其他类型：从 m_app_commission_record 查 ──
        from sqlalchemy import or_, and_

        query = MAppCommissionRecord.query.filter(
            MAppCommissionRecord.user_id == user_id,
            MAppCommissionRecord.del_flag == 0
        )

        if activity_id:
            query = query.filter(MAppCommissionRecord.activity_id == activity_id)

        if status:
            query = query.filter(MAppCommissionRecord.status == status)

        if commission_type:
            sub_type_map = {
                'method3_turnover': 'TURNOVER_COMMISSION',
                'method4_invitee_bet': 'INVITEE_BET_COMMISSION'
            }
            mapped_sub_type = sub_type_map.get(commission_type, commission_type)
            query = query.filter(MAppCommissionRecord.sub_type == mapped_sub_type)

        total_count = query.count()
        offset = (page - 1) * page_size
        commissions = query.order_by(
            MAppCommissionRecord.status.asc(),
            MAppCommissionRecord.create_time.desc()
        ).offset(offset).limit(page_size).all()

        commission_list = []
        for c in commissions:
            activity = MAppInvitationActivity.query.filter_by(id=c.activity_id).first()
            commission_list.append({
                'id': c.id,
                'activity_id': c.activity_id,
                'activity_title': activity.title if activity else 'Unknown',
                'invitee_id': c.related_user_id,
                'commission_type': c.sub_type,
                'base_amount': float(c.base_amount) if c.base_amount else 0,
                'commission_rate': float(c.rate) if c.rate else 0,
                'commission_amount': float(c.amount) if c.amount else 0,
                'status': c.status,
                'paid_at': c.payout_time.strftime('%Y-%m-%d %H:%M:%S') if c.payout_time else None,
                'settlement_period': c.settle_period,
                'create_time': c.create_time.strftime('%Y-%m-%d %H:%M:%S') if c.create_time else None,
            })

        total_pending = db.session.query(func.sum(MAppCommissionRecord.amount)).filter(
            MAppCommissionRecord.user_id == user_id,
            MAppCommissionRecord.status == 'Pending',
            MAppCommissionRecord.del_flag == 0
        ).scalar() or 0

        total_paid = db.session.query(func.sum(MAppCommissionRecord.amount)).filter(
            MAppCommissionRecord.user_id == user_id,
            MAppCommissionRecord.status == 'Paid',
            MAppCommissionRecord.del_flag == 0
        ).scalar() or 0

        return jsonify({
            'code': SUCCESS_CODE,
            'data': {
                'commissions': commission_list,
                'pagination': {
                    'current_page': page,
                    'page_size': page_size,
                    'total_count': total_count,
                    'total_pages': (total_count + page_size - 1) // page_size
                },
                'statistics': {
                    'total_pending': float(total_pending),
                    'total_paid': float(total_paid),
                    'total': float(total_pending + total_paid)
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


@invitation_v2.route('/invite_code', methods=['GET'])
@auth.login_required
def get_invite_code():
    """获取用户的邀请码"""
    try:
        user_id = g.user.id
        user = g.user

        # 获取用户信息
        member = AppMember.query.filter_by(id=user_id, del_flag=0).first()
        if not member:
            return jsonify({
                'code': PARAM_ERROR_CODE,
                'data': None,
                'message': 'User not found'
            }), 404

        # 获取邀请码（如果有的话）
        invite_code = member.invite_code if hasattr(member, 'invite_code') else None

        # 如果没有邀请码，可以生成一个
        if not invite_code:
            invite_code = Kits.generate_invite_code(user_id) if hasattr(Kits, 'generate_invite_code') else user_id[
                                                                                                           :8].upper()

        # 统计邀请数据（只统计计入活动的）
        total_invitees = MAppPromotionRelation.query.filter(
            MAppPromotionRelation.promoter_id == user_id,
            MAppPromotionRelation.status == 'Active',
            MAppPromotionRelation.is_counted_in_activity == True,  # 只统计计入活动的
            MAppPromotionRelation.del_flag == 0
        ).count()

        total_rewards = db.session.query(func.sum(MAppInvitationReward.reward_amount)).filter(
            MAppInvitationReward.mb_id == user_id,
            MAppInvitationReward.status == 'Claimed',
            MAppInvitationReward.del_flag == 0
        ).scalar() or 0

        return jsonify({
            'code': SUCCESS_CODE,
            'data': {
                'invite_code': invite_code,
                'user_id': user_id,
                'total_invitees': total_invitees,
                'total_rewards': float(total_rewards)
            },
            'message': 'success'
        }), 200

    except Exception as e:
        return jsonify({
            'code': SYSTEM_ERROR_CODE,
            'data': None,
            'message': str(e)
        }), 500


@invitation_v2.route('/join-activity', methods=['POST'])
@auth.login_required
def join_invitation_activity():
    """
    参与邀请活动

    用户主动点击参与按钮，创建活动参与记录
    只有参与后才能：
    1. 领取奖励（Method 1/2）
    2. 被邀请人下注时为推广人创建佣金（Method 3/4）

    请求体:
    {
        "activity_id": "活动ID"  # 可选，不传则参与当前激活的活动
    }

    返回:
    {
        "code": 200,
        "data": {
            "activity_record_id": "记录ID",
            "activity_id": "活动ID",
            "activity_name": "活动名称",
            "status": "Active",
            "already_joined": false
        },
        "message": "Successfully joined the invitation activity"
    }
    """
    try:
        # 获取当前用户
        user_id = g.user.id
        user = AppMember.query.filter_by(id=user_id, del_flag=0).first()

        if not user:
            return jsonify({
                'code': PARAM_ERROR_CODE,
                'data': None,
                'message': 'User not found'
            }), 404

        # 获取请求参数
        data = request.get_json() or {}
        activity_id = data.get('activity_id')

        # 如果没有指定活动ID，查询当前激活的邀请活动
        if not activity_id:
            now = datetime.now()
            activity = MAppInvitationActivity.query.filter(
                MAppInvitationActivity.del_flag == 0,
                MAppInvitationActivity.status == True,
                MAppInvitationActivity.start_date <= now,
                MAppInvitationActivity.end_date >= now
            ).first()

            if not activity:
                return jsonify({
                    'code': ACTIVITY_NOT_FOUND_CODE,
                    'data': None,
                    'message': 'No active invitation activity found'
                }), 404

            activity_id = activity.id
        else:
            # 验证活动是否存在且激活
            activity = MAppInvitationActivity.query.filter_by(
                id=activity_id,
                del_flag=0
            ).first()

            if not activity:
                return jsonify({
                    'code': ACTIVITY_NOT_FOUND_CODE,
                    'data': None,
                    'message': 'Activity not found'
                }), 404

            if not activity.status:
                return jsonify({
                    'code': ACTIVITY_NOT_VALID_CODE,
                    'data': None,
                    'message': 'Activity is not active'
                }), 400

            # 检查活动时间
            now = datetime.now()
            if activity.start_date and now < activity.start_date:
                return jsonify({
                    'code': ACTIVITY_NOT_VALID_CODE,
                    'data': None,
                    'message': 'Activity has not started yet'
                }), 400

            if activity.end_date and now > activity.end_date:
                return jsonify({
                    'code': ACTIVITY_NOT_VALID_CODE,
                    'data': None,
                    'message': 'Activity has ended'
                }), 400

        # 检查是否已经参与过该活动
        existing_record = AppPlayerActivityRecord.query.filter_by(
            mb_id=user_id,
            activity_type='INVITATION',
            activity_id=activity_id,
            del_flag=0
        ).first()

        if existing_record:
            # 如果已经参与，返回现有记录
            return jsonify({
                'code': SUCCESS_CODE,
                'data': {
                    'activity_record_id': existing_record.id,
                    'activity_id': activity_id,
                    'activity_name': activity.title,
                    'status': existing_record.status,
                    'already_joined': True
                },
                'message': 'You have already joined this activity'
            }), 200

        # 检查是否已有其他活跃的邀请活动（每个玩家只能参与一个邀请活动）
        other_active_invitation = AppPlayerActivityRecord.query.filter(
            AppPlayerActivityRecord.mb_id == user_id,
            AppPlayerActivityRecord.activity_type == 'INVITATION',
            AppPlayerActivityRecord.status == 'Active',
            AppPlayerActivityRecord.del_flag == 0,
            AppPlayerActivityRecord.activity_id != activity_id
        ).first()

        if other_active_invitation:
            return jsonify({
                'code': CONDITION_NOT_MET_CODE,
                'data': None,
                'message': 'You already have an active invitation activity. Please complete or cancel it before joining another.'
            }), 400

        # 检查优惠券和邀请活动的互斥条件
        # 如果邀请活动设置了流水/净赢要求（>0），则用户不能在有活跃优惠券/促销时参与
        # 如果邀请活动没有流水/净赢要求（=0），则允许用户参与
        exclusion_check, exclusion_msg = check_coupon_invitation_exclusion(user_id, activity)
        if not exclusion_check:
            return jsonify({
                'code': CONDITION_NOT_MET_CODE,
                'data': None,
                'message': exclusion_msg
            }), 400

        # 判断活动是否有流水/净赢要求
        use_main_wallet = should_use_main_wallet(activity)

        # 计算初始流水和净赢要求
        # 参与活动时不领取奖励，所以流水/净赢要求都是0，但需要记录活动本身是否有要求
        withdrawal_type = activity.withdrawal_requirement_type if hasattr(activity,
                                                                          'withdrawal_requirement_type') else 'Turnover'
        turnover_multiplier = Decimal(str(activity.turnover_multiplier)) if hasattr(activity,
                                                                                    'turnover_multiplier') and activity.turnover_multiplier else Decimal(
            '0')
        net_win_amount = Decimal(str(activity.net_win_amount)) if hasattr(activity,
                                                                          'net_win_amount') and activity.net_win_amount else Decimal(
            '0')

        # 如果活动没有流水/净赢要求（use_main_wallet = True），标记为已达标
        # 如果有要求，初始为未达标，领取奖励后才会有具体要求
        initial_requirement_met = 1 if use_main_wallet else 0

        # 构建完成条件描述
        if use_main_wallet:
            completion_condition = 'Participated in invitation activity (No requirements)'
        else:
            if withdrawal_type == 'Net Win':
                completion_condition = f'Net Win Required: {float(net_win_amount)}'
            else:
                completion_condition = f'Turnover Multiplier: {float(turnover_multiplier)}x'

        # 根据提现要求类型设置初始要求
        # - Net Win 模式：req_netwin 设置为活动的固定净赢值，req_turnover 为 0
        # - Turnover 模式：req_turnover 初始为 0（领取奖励后才计算），req_netwin 为 0
        if withdrawal_type == 'Net Win':
            initial_req_turnover = Decimal('0.00')
            initial_req_netwin = net_win_amount  # 净赢是固定值，参与时就设置
        else:
            initial_req_turnover = Decimal('0.00')  # 流水要求领取奖励后才计算
            initial_req_netwin = Decimal('0.00')

        # 创建活动参与记录
        now = datetime.now()
        activity_record = AppPlayerActivityRecord(
            id=Kits.generate_uuid(),
            mb_id=user_id,
            aid=user.aid,
            username=user.username if hasattr(user, 'username') else None,
            activity_type='INVITATION',
            activity_id=activity_id,
            member_coupon_id='',  # 邀请活动没有优惠券ID
            activity_name=activity.title,
            status='Active',
            start_time=now,
            completion_condition=completion_condition,
            req_turnover=initial_req_turnover,
            req_netwin=initial_req_netwin,
            is_requirement_met=initial_requirement_met,  # 根据活动配置判断
            tenant_id=user.tenant_id,
            create_time=now,
            create_by_id=user_id,
            del_flag=0
        )

        db.session.add(activity_record)
        db.session.commit()

        app.logger.info(
            f"用户参与邀请活动: user_id={user_id}, activity_id={activity_id}, "
            f"record_id={activity_record.id}"
        )

        return jsonify({
            'code': SUCCESS_CODE,
            'data': {
                'activity_record_id': activity_record.id,
                'activity_id': activity_id,
                'activity_name': activity.title,
                'status': 'Active',
                'already_joined': False
            },
            'message': 'Successfully joined the invitation activity'
        }), 200

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"参与邀请活动失败: user_id={user_id}, error={str(e)}")
        return jsonify({
            'code': SYSTEM_ERROR_CODE,
            'data': None,
            'message': f'Failed to join activity: {str(e)}'
        }), 500


@invitation_v2.route('/total-summary', methods=['GET'])
@auth.login_required
def get_total_summary():
    """
    获取邀请奖励汇总统计
    返回当前用户作为邀请者领取的奖金总和、邀请用户数等信息
    简化版：只返回前端需要的核心数据
    """
    try:
        user_id = g.user.id

        # 1. 统计当前用户作为邀请者领取的奖励总额 (Method 1 & 2)
        referrer_total_rewards_claimed = db.session.query(func.sum(MAppInvitationReward.reward_amount)).filter(
            MAppInvitationReward.mb_id == user_id,
            MAppInvitationReward.status == 'Claimed',
            MAppInvitationReward.del_flag == 0
        ).scalar() or 0

        # 2. 统计佣金总额 (Method 3: Inviter Commission)
        # 注意：只统计“已发放” (Paid) 的佣金
        referrer_total_commissions = db.session.query(func.sum(MAppCommissionRecord.amount)).filter(
            MAppCommissionRecord.user_id == user_id,
            MAppCommissionRecord.sub_type.in_(['TURNOVER_COMMISSION', 'WIN_LOSS_COMMISSION']),
            MAppCommissionRecord.status == 'Paid',  # 只统计已发放
            MAppCommissionRecord.del_flag == 0
        ).scalar() or 0

        # 3. 统计被邀请人投注返佣 (Method 4: Invitee Bet Commission)
        # 注意：只统计“已发放” (Paid) 的佣金
        invitee_bet_commissions = db.session.query(func.sum(MAppCommissionRecord.amount)).filter(
            MAppCommissionRecord.user_id == user_id,
            MAppCommissionRecord.sub_type == 'INVITEE_BET_COMMISSION',
            MAppCommissionRecord.status == 'Paid',  # 只统计已发放
            MAppCommissionRecord.del_flag == 0
        ).scalar() or 0

        # 汇总
        total_rewards_all = float(referrer_total_rewards_claimed) + float(referrer_total_commissions) + float(invitee_bet_commissions)

        # 4. 统计邀请的用户总数（只统计计入活动的）
        total_invited_users = MAppPromotionRelation.query.filter(
            MAppPromotionRelation.promoter_id == user_id,
            MAppPromotionRelation.status == 'Active',
            MAppPromotionRelation.is_counted_in_activity == True,  # 只统计计入活动的
            MAppPromotionRelation.del_flag == 0
        ).count()

        # 3. 统计当前可领取的奖励金额（通过活动列表计算）
        total_claimable_reward = 0
        # 这里简化处理，实际应该调用活动列表API获取，但为了避免循环依赖，直接返回0
        # 前端会通过活动列表获取详细的可领取信息

        return jsonify({
            'code': SUCCESS_CODE,
            'data': {
                'summary': {
                    'referrer_total_rewards': total_rewards_all,
                    'total_invited_users': total_invited_users,
                    'total_claimable_reward': float(total_claimable_reward)
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


@invitation_v2.route('/rules-detail/<string:activity_id>', methods=['GET'])
def get_activity_rules_detail(activity_id):
    """
    获取活动规则详情（用于前端规则弹窗展示）
    返回完整的规则说明信息，包括所有Method的配置
    """
    try:
        # 获取活动信息
        activity = MAppInvitationActivity.query.filter_by(
            id=activity_id,
            del_flag=0
        ).first()

        if not activity:
            return jsonify({
                'code': ACTIVITY_NOT_FOUND_CODE,
                'data': None,
                'message': 'Activity does not exist'
            }), 404

        # 基本信息
        rules_detail = {
            'activity_id': activity.id,
            'activity_title': activity.title,
            'activity_description': activity.description,
            'start_date': activity.start_date.strftime('%Y-%m-%d %H:%M:%S') if activity.start_date else None,
            'end_date': activity.end_date.strftime('%Y-%m-%d %H:%M:%S') if activity.end_date else None,
            'withdrawal_requirement_type': activity.withdrawal_requirement_type if hasattr(activity,
                                                                                           'withdrawal_requirement_type') else None,
            'turnover_multiplier': float(activity.turnover_multiplier) if hasattr(activity,
                                                                                  'turnover_multiplier') and activity.turnover_multiplier else None,
            'net_win_amount': float(activity.net_win_amount) if hasattr(activity,
                                                                        'net_win_amount') and activity.net_win_amount else None,
            'profit_share_frequency': activity.profit_share_frequency if hasattr(activity,
                                                                                 'profit_share_frequency') else None
        }

        # Method 1: 邀请/成就分享详情
        if hasattr(activity, 'method_invitation_enabled') and activity.method_invitation_enabled == 1:
            # 获取成就规则列表
            achievement_rules = MAppInvitationAchievement.query.filter_by(
                activity_id=activity_id,
                del_flag=0
            ).order_by(MAppInvitationAchievement.sequence).all()

            achievement_rules_list = [
                {
                    'id': rule.id,
                    'rule_type': rule.rule_type,
                    'threshold_value': int(rule.threshold_value) if rule.threshold_value else 0,
                    'reward_amount': float(rule.reward_amount) if rule.reward_amount else 0,
                    'max_claim_count': int(rule.max_claim_count) if rule.max_claim_count else 0,
                    'description': rule.description,
                    'sequence': int(rule.sequence) if rule.sequence else 0
                }
                for rule in achievement_rules
            ]

            rules_detail['method1'] = {
                'enabled': True,
                'one_time_bonus': float(activity.invitation_share_one_time_bonus) if hasattr(activity,
                                                                                             'invitation_share_one_time_bonus') and activity.invitation_share_one_time_bonus else 0,
                'min_deposit': float(activity.invitation_share_min_deposit) if hasattr(activity,
                                                                                       'invitation_share_min_deposit') and activity.invitation_share_min_deposit else 0,
                'min_turnover': float(activity.invitation_share_min_turnover) if hasattr(activity,
                                                                                         'invitation_share_min_turnover') and activity.invitation_share_min_turnover else 0,
                'achievement_rules': achievement_rules_list
            }
        else:
            rules_detail['method1'] = {'enabled': False}

        # Method 2: 存款分享详情
        if hasattr(activity, 'method_deposit_enabled') and activity.method_deposit_enabled == 1:
            # 获取存款档位列表
            deposit_tiers = MAppInvitationDepositShare.query.filter_by(
                activity_id=activity_id,
                del_flag=0
            ).order_by(MAppInvitationDepositShare.sequence).all()

            deposit_tiers_list = [
                {
                    'id': tier.id,
                    'min_deposit': float(tier.min_deposit) if tier.min_deposit else 0,
                    'max_deposit': float(tier.max_deposit) if tier.max_deposit else None,
                    'bonus_rate': float(tier.bonus_rate) if tier.bonus_rate else 0,
                    'max_claims': int(tier.max_claims) if hasattr(tier, 'max_claims') and tier.max_claims else 0,
                    'description': tier.description if hasattr(tier, 'description') else None,
                    'sequence': int(tier.sequence) if tier.sequence else 0
                }
                for tier in deposit_tiers
            ]

            rules_detail['method2'] = {
                'enabled': True,
                'deposit_tiers': deposit_tiers_list
            }
        else:
            rules_detail['method2'] = {'enabled': False}

        # Method 3: 邀请者佣金详情
        if hasattr(activity, 'method_commission_enabled') and activity.method_commission_enabled == 1:
            rules_detail['method3'] = {
                'enabled': True,
                'commission_type': activity.commission_type if hasattr(activity, 'commission_type') else 'turnover',
                'commission_rate': float(activity.commission_rate) if hasattr(activity,
                                                                              'commission_rate') and activity.commission_rate else 0,
                'settlement_frequency': activity.profit_share_frequency if hasattr(activity,
                                                                                   'profit_share_frequency') else 'weekly'
            }
        else:
            rules_detail['method3'] = {'enabled': False}

        # Method 4: 被邀请人投注返佣详情（返佣给被邀请人自己）
        if hasattr(activity, 'method_invitee_bet_enabled') and activity.method_invitee_bet_enabled == 1:
            rules_detail['method4'] = {
                'enabled': True,
                'rebate_rate': float(activity.invitee_bet_commission_rate) if hasattr(activity,
                                                                                      'invitee_bet_commission_rate') and activity.invitee_bet_commission_rate else 0
            }
        else:
            rules_detail['method4'] = {'enabled': False}

        return jsonify({
            'code': SUCCESS_CODE,
            'data': ensure_serializable(rules_detail),
            'message': 'success'
        }), 200

    except Exception as e:
        app.logger.error(f"Error getting activity rules detail: {str(e)}")
        return jsonify({
            'code': SYSTEM_ERROR_CODE,
            'data': None,
            'message': f'System error: {str(e)}'
        }), 500


@invitation_v2.route('/invitees-summary', methods=['GET'])
@auth.login_required
def get_invitees_summary():
    """
    获取被邀请人数据汇总统计
    包括总充值、总流水（下注金额）、总净赢
    支持时间段、被邀请者状态过滤和用户名过滤

    查询参数:
    - start_date: 开始日期 (YYYY-MM-DD)，基于用户注册时间过滤
    - end_date: 结束日期 (YYYY-MM-DD)，基于用户注册时间过滤
    - status: 被邀请者状态 (all/signed_up/active/inactive/pending)
    - keyword: 用户名关键词搜索
    """
    try:
        user_id = g.user.id

        # 获取查询参数
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        invitee_status = request.args.get('status', '').lower()
        keyword = request.args.get('keyword', '').strip()

        # 状态映射
        status_mapping = {
            'signed_up': 'Signed Up',
            'active': 'Active',
            'inactive': 'Inactive',
            'pending': 'Pending'
        }

        # 转换状态参数
        if invitee_status and invitee_status != 'all':
            invitee_status = status_mapping.get(invitee_status)
            if not invitee_status:
                return jsonify({
                    'code': PARAM_ERROR_CODE,
                    'data': None,
                    'message': f'Invalid status, valid values: {list(status_mapping.keys())}'
                }), 400
        else:
            invitee_status = None

        # 构建查询：获取被邀请人列表（只统计计入活动的）
        query = MAppPromotionRelation.query.join(
            AppMember, MAppPromotionRelation.invitee_id == AppMember.id
        ).filter(
            MAppPromotionRelation.promoter_id == user_id,
            MAppPromotionRelation.status == 'Active',
            MAppPromotionRelation.is_counted_in_activity == True,  # 只统计计入活动的
            MAppPromotionRelation.del_flag == 0
        )

        # 时间过滤（基于注册时间）
        if start_date:
            try:
                start_dt = datetime.strptime(start_date, '%Y-%m-%d')
                query = query.filter(AppMember.create_time >= start_dt)
            except ValueError:
                return jsonify({
                    'code': PARAM_ERROR_CODE,
                    'data': None,
                    'message': 'Invalid start_date format (use YYYY-MM-DD)'
                }), 400

        if end_date:
            try:
                end_dt = datetime.strptime(end_date, '%Y-%m-%d')
                end_dt = end_dt.replace(hour=23, minute=59, second=59)
                query = query.filter(AppMember.create_time <= end_dt)
            except ValueError:
                return jsonify({
                    'code': PARAM_ERROR_CODE,
                    'data': None,
                    'message': 'Invalid end_date format (use YYYY-MM-DD)'
                }), 400

        # 用户名过滤（不区分大小写）
        if keyword:
            kw = keyword.lower()
            query = query.filter(
                db.or_(
                    func.lower(AppMember.username).like(f'%{kw}%'),
                    func.lower(AppMember.name).like(f'%{kw}%')
                )
            )

        promotion_relations_invitee_list = query.all()

        if not promotion_relations_invitee_list:
            return jsonify({
                'code': SUCCESS_CODE,
                'data': {
                    'total_deposit': 0,
                    'total_turnover': 0,
                    'total_net_win': 0,
                    'invitee_details': []
                },
                'message': 'success'
            }), 200

        invited_user_ids = [rel.invitee_id for rel in promotion_relations_invitee_list]

        # 查询被邀请人的详细信息
        invited_users = AppMember.query.filter(
            AppMember.id.in_(invited_user_ids),
            AppMember.del_flag == 0
        ).all()

        # 创建用户ID到用户对象的映射
        user_map = {user.id: user for user in invited_users}

        # 批量查询充值统计
        recharge_stats = {}
        if invited_user_ids:
            recharge_query = db.session.query(
                Charge.mb_id,
                func.count(Charge.id).label('count'),
                func.sum(Charge.amount).label('total')
            ).filter(
                Charge.mb_id.in_(invited_user_ids),
                Charge.status == 'Success',
                Charge.del_flag == 0
            ).group_by(Charge.mb_id).all()

            for r in recharge_query:
                recharge_stats[r.mb_id] = {
                    'count': r.count or 0,
                    'total': float(r.total or 0)
                }

        # 批量查询下注统计（✅ 使用 AppBetOrder 模型，对应 m_app_bet_order 表）
        # - net_win: 统一使用 netwin_actual
        order_stats = {}
        if invited_user_ids:
            order_query = db.session.query(
                AppBetOrder.mb_id,
                func.count(AppBetOrder.id).label('count'),
                func.sum(AppBetOrder.stake).label('total_bet'),
                func.sum(AppBetOrder.netwin_actual).label('total_netwin')
            ).filter(
                AppBetOrder.mb_id.in_(invited_user_ids),
                AppBetOrder.bet_status.in_(
                    [BetStatus.Win, BetStatus.Lose, BetStatus.Draw, BetStatus.HalfWin, BetStatus.HalfLose]),
                AppBetOrder.del_flag == 0
            ).group_by(AppBetOrder.mb_id).all()

            for o in order_query:
                total_bet = float(o.total_bet or 0)
                total_netwin = float(o.total_netwin or 0)
                order_stats[o.mb_id] = {
                    'count': o.count or 0,
                    'total_bet': total_bet,
                    'total_bonus': total_bet + total_netwin,
                    'net_win': total_netwin
                }

        # 构建被邀请人详情
        invitee_details = []
        current_time = datetime.now()

        for user in invited_users:
            recharge = recharge_stats.get(user.id, {'count': 0, 'total': 0})
            order = order_stats.get(user.id, {'count': 0, 'total_bet': 0, 'total_bonus': 0, 'net_win': 0})

            # 判断用户状态
            has_deposit = recharge['count'] > 0
            has_bet = order['count'] > 0

            # 计算最后活动时间（简化版）
            last_activity = user.create_time
            days_inactive = (current_time - last_activity).days if last_activity else 0

            # 状态分类
            if not has_deposit and not has_bet:
                user_status = 'Pending'
                user_label = 'Idle User'
            elif has_deposit and not has_bet:
                user_status = 'Signed Up'
                user_label = 'No Bet Yet'
            elif has_deposit and has_bet and days_inactive <= 30:
                user_status = 'Active'
                user_label = 'Top User'
            elif (has_deposit or has_bet) and days_inactive > 30:
                user_status = 'Inactive'
                user_label = 'Idle User'
            else:
                user_status = 'Active'
                user_label = 'Top User'

            # 状态过滤
            if invitee_status and user_status != invitee_status:
                continue

            invitee_details.append({
                'user_id': user.id,
                'username': user.username,
                'name': user.name or user.username,
                'user_name': user.name or user.username,
                'register_time': user.create_time.strftime('%Y-%m-%d %H:%M:%S') if user.create_time else None,
                'last_login_time': user.last_login_time.strftime('%Y-%m-%d %H:%M:%S') if user.last_login_time else None,
                'user_status': user_status,
                'user_label': user_label,
                'stats': {
                    'recharge_count': recharge['count'],
                    'total_recharge': recharge['total'],
                    'order_count': order['count'],
                    'total_bet': order['total_bet'],
                    'total_bonus': order['total_bonus'],
                    'net_win': order['net_win']
                }
            })

        # 计算汇总数据
        total_deposit = sum(d['stats']['total_recharge'] for d in invitee_details)
        total_turnover = sum(d['stats']['total_bet'] for d in invitee_details)
        total_net_win = sum(d['stats']['net_win'] for d in invitee_details)

        return jsonify({
            'code': SUCCESS_CODE,
            'data': {
                'total_deposit': total_deposit,
                'total_turnover': total_turnover,
                'total_net_win': total_net_win,
                'invitee_details': invitee_details
            },
            'message': 'success'
        }), 200

    except Exception as e:
        app.logger.error(f"Error getting invitees summary: {str(e)}")
        return jsonify({
            'code': SYSTEM_ERROR_CODE,
            'data': None,
            'message': f'System error: {str(e)}'
        }), 500


@invitation_v2.route('/rewards/bonus-type-summary', methods=['GET'])
@auth.login_required
def get_bonus_type_summary():
    """按4个Method统计当前用户的奖金，支持时间段和类型过滤
    Method 1 & 2 来自 MAppInvitationReward，Method 3 & 4 来自 MAppCommissionRecord
    """
    try:
        user_id = g.user.id

        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        bonus_type = request.args.get('bonus_type')

        # 解析时间范围
        start_dt = None
        end_dt = None
        if start_date:
            try:
                start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            except ValueError:
                pass
        if end_date:
            try:
                end_dt = datetime.strptime(end_date, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
            except ValueError:
                pass

        # bonus_type 映射
        BONUS_TYPE_TO_DISPLAY = {
            'invitation_share_one_time': 'Invitation Share',
            'method1_invitation_share': 'Invitation Share',
            'method1_achievement': 'Invitation Achievement',
            'deposit_share': 'Deposit Share',
            'method2_deposit_share': 'Deposit Share',
        }
        DEFAULT_DISPLAY = 'Other'  # 默认不统计未知的

        COMMISSION_SUB_TYPE_TO_DISPLAY = {
            'TURNOVER_COMMISSION': 'Inviter Commission',
            'WIN_LOSS_COMMISSION': 'Inviter Commission',
            'INVITEE_BET_COMMISSION': 'Invitee Bet Commission',
        }

        valid_types = ['Invitation Achievement', 'Invitation Share', 'Deposit Share', 'Inviter Commission',
                       'Invitee Bet Commission', 'Other']
        display_stats = {name: {'total_amount': 0.0, 'reward_count': 0} for name in valid_types}
        total_amount = 0.0

        # ========== Method 1 & 2: 查询 MAppInvitationReward ==========
        if not bonus_type or bonus_type in ['Invitation Achievement', 'Invitation Share', 'Deposit Share']:
            reward_filters = [
                MAppInvitationReward.mb_id == user_id,
                MAppInvitationReward.status == 'Claimed',
                MAppInvitationReward.del_flag == 0
            ]
            if start_dt:
                reward_filters.append(MAppInvitationReward.claimed_at >= start_dt)
            if end_dt:
                reward_filters.append(MAppInvitationReward.claimed_at <= end_dt)

            reward_stats = db.session.query(
                MAppInvitationReward.bonus_type,
                func.sum(MAppInvitationReward.reward_amount).label('total_amount'),
                func.count(MAppInvitationReward.id).label('reward_count')
            ).filter(*reward_filters).group_by(MAppInvitationReward.bonus_type).all()

            for stat in reward_stats:
                amount = float(stat.total_amount or 0)
                count = stat.reward_count or 0
                display_name = BONUS_TYPE_TO_DISPLAY.get(stat.bonus_type, DEFAULT_DISPLAY)

                # 如果指定了筛选类型，只累加匹配的
                if bonus_type and display_name != bonus_type:
                    continue
                
                # 跳过未知的类型
                if display_name not in display_stats:
                    continue

                display_stats[display_name]['total_amount'] += amount
                display_stats[display_name]['reward_count'] += count
                total_amount += amount

        # ========== Method 3 & 4: 查询 MAppCommissionRecord ==========
        if not bonus_type or bonus_type in ['Inviter Commission', 'Invitee Bet Commission']:
            commission_filters = [
                MAppCommissionRecord.user_id == user_id,
                MAppCommissionRecord.status == 'Paid',  # 只统计已发放
                MAppCommissionRecord.del_flag == 0
            ]
            if start_dt:
                commission_filters.append(MAppCommissionRecord.create_time >= start_dt)
            if end_dt:
                commission_filters.append(MAppCommissionRecord.create_time <= end_dt)

            # 限定 sub_type 范围
            target_sub_types = list(COMMISSION_SUB_TYPE_TO_DISPLAY.keys())
            if bonus_type == 'Inviter Commission':
                target_sub_types = ['TURNOVER_COMMISSION', 'WIN_LOSS_COMMISSION']
            elif bonus_type == 'Invitee Bet Commission':
                target_sub_types = ['INVITEE_BET_COMMISSION']
            commission_filters.append(MAppCommissionRecord.sub_type.in_(target_sub_types))

            commission_stats = db.session.query(
                MAppCommissionRecord.sub_type,
                func.sum(MAppCommissionRecord.amount).label('total_amount'),
                func.count(MAppCommissionRecord.id).label('reward_count')
            ).filter(*commission_filters).group_by(MAppCommissionRecord.sub_type).all()

            for stat in commission_stats:
                amount = float(stat.total_amount or 0)
                count = stat.reward_count or 0
                display_name = COMMISSION_SUB_TYPE_TO_DISPLAY.get(stat.sub_type)
                if display_name:
                    display_stats[display_name]['total_amount'] += amount
                    display_stats[display_name]['reward_count'] += count
                    total_amount += amount

        return jsonify({
            'code': SUCCESS_CODE,
            'data': {
                'summary': {
                    'total_amount': total_amount,
                    'bonus_type_breakdown': display_stats
                }
            },
            'message': 'success'
        }), 200

    except Exception as e:
        app.logger.error(f"Error getting bonus type summary: {str(e)}")
        return jsonify({
            'code': SYSTEM_ERROR_CODE,
            'data': None,
            'message': f'System error: {str(e)}'
        }), 500


@invitation_v2.route('/check_invitation_limit', methods=['POST'])
@auth.login_required
def check_invitation_limit():
    """
    检查邀请人数限制

    请求参数:
    - activity_id: 活动ID

    返回:
    - current_invitations: 当前已邀请人数
    - max_invitations: 最大邀请人数（0表示无限制）
    - remaining_invitations: 剩余可邀请人数（-1表示无限制）
    - can_invite: 是否可以继续邀请
    """
    try:
        from app_server.service.PromotionRelationService import PromotionRelationService

        user_id = g.user.id
        data = request.json
        activity_id = data.get('activity_id')

        if not activity_id:
            return jsonify({
                'code': PARAM_ERROR_CODE,
                'data': None,
                'message': 'Activity ID is required'
            }), 400

        # 检查活动是否存在
        activity = MAppInvitationActivity.query.filter_by(
            id=activity_id,
            del_flag=0
        ).first()

        if not activity:
            return jsonify({
                'code': ACTIVITY_NOT_FOUND_CODE,
                'data': None,
                'message': 'Activity does not exist'
            }), 404

        # 检查邀请限制
        can_invite, error_msg, stats = PromotionRelationService.check_invitation_limit(user_id, activity_id)

        return jsonify({
            'code': SUCCESS_CODE,
            'data': {
                'can_invite': can_invite,
                'current_invitations': stats.get('current_invitations', 0),
                'max_invitations': stats.get('max_invitations', 0),
                'remaining_invitations': stats.get('remaining_invitations', -1),
                'message': error_msg if not can_invite else 'You can invite more people'
            },
            'message': 'success'
        }), 200

    except Exception as e:
        app.logger.error(f"Error checking invitation limit: {str(e)}")
        return jsonify({
            'code': SYSTEM_ERROR_CODE,
            'data': None,
            'message': f'System error: {str(e)}'
        }), 500


@invitation_v2.route('/invitee-stats', methods=['GET'])
@auth.login_required
def get_invitee_statistics():
    """当前用户的被邀请人统计：Active Invitees（有充值记录）、Pending Invitees（无充值记录）、Total Invited（总数）"""
    try:
        # 获取当前用户ID
        user_id = g.user.id

        # 查询当前用户邀请的所有用户（使用 MAppPromotionRelation，与 total-summary 一致）
        promotion_relations = MAppPromotionRelation.query.filter(
            MAppPromotionRelation.promoter_id == user_id,
            MAppPromotionRelation.status == 'Active',
            MAppPromotionRelation.is_counted_in_activity == True,
            MAppPromotionRelation.del_flag == 0
        ).all()

        if not promotion_relations:
            return jsonify({
                'code': SUCCESS_CODE,
                'data': {
                    'active_invitees': 0,
                    'pending_invitees': 0,
                    'total_invited': 0,
                    'active_percentage': 0.0,
                    'pending_percentage': 0.0
                },
                'message': 'success'
            }), 200

        invited_user_ids = [rel.invitee_id for rel in promotion_relations]

        # 统计有充值记录的用户
        users_with_recharge = db.session.query(Charge.mb_id).filter(
            Charge.mb_id.in_(invited_user_ids),
            Charge.status == 'Success',
            Charge.del_flag == 0
        ).distinct().all()
        users_with_recharge_ids = {uid[0] for uid in users_with_recharge}

        # Active Invitees: 有充值记录的用户
        active_invitees_count = len(users_with_recharge_ids)

        # Pending Invitees: 没有充值记录的用户
        pending_invitees_count = len(invited_user_ids) - active_invitees_count

        # Total Invited: 被邀请用户总数
        total_invited_count = len(invited_user_ids)

        # 计算百分比
        active_percentage = round((active_invitees_count / total_invited_count) * 100,
                                  2) if total_invited_count > 0 else 0
        pending_percentage = round((pending_invitees_count / total_invited_count) * 100,
                                   2) if total_invited_count > 0 else 0

        # 统计Active用户的总充值金额
        total_recharge_amount = 0
        if users_with_recharge_ids:
            total_recharge = db.session.query(func.sum(Charge.amount)).filter(
                Charge.mb_id.in_(users_with_recharge_ids),
                Charge.status == 'Success',
                Charge.del_flag == 0
            ).scalar()
            total_recharge_amount = float(total_recharge or 0)

        # 统计充值用户的平均充值金额
        average_recharge_per_user = round(total_recharge_amount / active_invitees_count,
                                          2) if active_invitees_count > 0 else 0

        return jsonify({
            'code': SUCCESS_CODE,
            'data': {
                'active_invitees': active_invitees_count,
                'pending_invitees': pending_invitees_count,
                'total_invited': total_invited_count,
                'active_percentage': active_percentage,
                'pending_percentage': pending_percentage,
                'total_recharge_amount': total_recharge_amount,
                'average_recharge_per_user': average_recharge_per_user
            },
            'message': 'success'
        }), 200

    except Exception as e:
        return jsonify({
            'code': SYSTEM_ERROR_CODE,
            'data': None,
            'message': str(e)
        }), 500


@invitation_v2.route('/commission_payouts', methods=['GET'])
@auth.login_required
def get_my_commission_payouts():
    """
    获取我的佣金发放批次记录

    参数：
    - page: 页码，默认1
    - page_size: 每页数量，默认20
    - status: 状态筛选（PendingAudit/Approved/Paid/Rejected/Failed）
    - settle_period: 结算期筛选（如：2025-W06, 2025-02）
    """
    try:
        from app_server.model.MAppCommissionPayoutModel import MAppCommissionPayout

        user_id = g.user.id
        page = int(request.args.get('page', 1))
        page_size = min(int(request.args.get('page_size', 20)), 100)
        status = request.args.get('status')
        settle_period = request.args.get('settle_period')

        # 构建查询
        query = MAppCommissionPayout.query.filter(
            MAppCommissionPayout.user_id == user_id,
            MAppCommissionPayout.del_flag == 0
        )

        if status:
            query = query.filter(MAppCommissionPayout.payout_status == status)

        if settle_period:
            query = query.filter(MAppCommissionPayout.settle_period == settle_period)

        # 获取总数
        total_count = query.count()

        # 分页和排序
        offset = (page - 1) * page_size
        payouts = query.order_by(
            MAppCommissionPayout.create_time.desc()
        ).offset(offset).limit(page_size).all()

        # 格式化返回数据
        payout_list = []
        for p in payouts:
            activity = MAppInvitationActivity.query.filter_by(id=p.activity_id).first() if p.activity_id else None

            payout_info = {
                'id': p.id,
                'payout_no': p.payout_no,
                'activity_id': p.activity_id,
                'activity_title': activity.title if activity else 'All Activities',
                'settle_cycle': p.settle_cycle,
                'settle_period': p.settle_period,
                'total_amount': float(p.total_amount) if p.total_amount else 0,
                'actual_amount': float(p.actual_amount) if p.actual_amount else 0,
                'record_count': p.record_count or 0,
                'payout_status': p.payout_status,
                'audit_status': p.audit_status,
                'need_audit': p.need_audit == 1,
                'payout_time': p.payout_time.strftime('%Y-%m-%d %H:%M:%S') if p.payout_time else None,
                'complete_time': p.complete_time.strftime('%Y-%m-%d %H:%M:%S') if p.complete_time else None,
                'create_time': p.create_time.strftime('%Y-%m-%d %H:%M:%S') if p.create_time else None
            }
            payout_list.append(payout_info)

        # 统计信息
        stats_pending = db.session.query(func.sum(MAppCommissionPayout.actual_amount)).filter(
            MAppCommissionPayout.user_id == user_id,
            MAppCommissionPayout.payout_status == 'PendingAudit',
            MAppCommissionPayout.del_flag == 0
        ).scalar() or 0

        stats_paid = db.session.query(func.sum(MAppCommissionPayout.actual_amount)).filter(
            MAppCommissionPayout.user_id == user_id,
            MAppCommissionPayout.payout_status == 'Paid',
            MAppCommissionPayout.del_flag == 0
        ).scalar() or 0

        return jsonify({
            'code': SUCCESS_CODE,
            'data': {
                'payouts': payout_list,
                'pagination': {
                    'current_page': page,
                    'page_size': page_size,
                    'total_count': total_count,
                    'total_pages': (total_count + page_size - 1) // page_size
                },
                'statistics': {
                    'pending_audit_amount': float(stats_pending),
                    'paid_amount': float(stats_paid),
                    'total': float(stats_pending + stats_paid)
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


@invitation_v2.route('/commission_summary', methods=['GET'])
@auth.login_required
def get_commission_summary():
    """
    获取佣金汇总信息

    返回：
    - 待结算佣金总额
    - 已结算待发放金额
    - 已发放总额
    - 本周期预计佣金
    """
    try:
        user_id = g.user.id

        # 待结算（Pending状态的佣金记录）
        pending_amount = db.session.query(func.sum(MAppCommissionRecord.amount)).filter(
            MAppCommissionRecord.user_id == user_id,
            MAppCommissionRecord.status == 'Pending',
            MAppCommissionRecord.del_flag == 0
        ).scalar() or Decimal('0')

        # 已结算待发放（Settled状态）
        settled_amount = db.session.query(func.sum(MAppCommissionRecord.amount)).filter(
            MAppCommissionRecord.user_id == user_id,
            MAppCommissionRecord.status == 'Settled',
            MAppCommissionRecord.del_flag == 0
        ).scalar() or Decimal('0')

        # 已发放（Paid状态）
        paid_amount = db.session.query(func.sum(MAppCommissionRecord.amount)).filter(
            MAppCommissionRecord.user_id == user_id,
            MAppCommissionRecord.status == 'Paid',
            MAppCommissionRecord.del_flag == 0
        ).scalar() or Decimal('0')

        # 本周期的佣金（根据当前日期计算）
        from datetime import date
        today = date.today()
        # 计算当前周的结算期
        iso_calendar = today.isocalendar()
        current_week_period = f"{iso_calendar[0]}-W{iso_calendar[1]:02d}"
        # 计算当前月的结算期
        current_month_period = today.strftime('%Y-%m')

        # 本周期待结算金额（包括周结和月结）
        current_period_amount = db.session.query(func.sum(MAppCommissionRecord.amount)).filter(
            MAppCommissionRecord.user_id == user_id,
            MAppCommissionRecord.status == 'Pending',
            MAppCommissionRecord.del_flag == 0,
            or_(
                MAppCommissionRecord.settle_period == current_week_period,
                MAppCommissionRecord.settle_period == current_month_period
            )
        ).scalar() or Decimal('0')

        # 统计各类型佣金（DB 已入库部分）
        turnover_commission = db.session.query(func.sum(MAppCommissionRecord.amount)).filter(
            MAppCommissionRecord.user_id == user_id,
            MAppCommissionRecord.sub_type == 'TURNOVER_COMMISSION',
            MAppCommissionRecord.del_flag == 0
        ).scalar() or Decimal('0')

        win_loss_commission_db = db.session.query(func.sum(MAppCommissionRecord.amount)).filter(
            MAppCommissionRecord.user_id == user_id,
            MAppCommissionRecord.sub_type == 'WIN_LOSS_COMMISSION',
            MAppCommissionRecord.del_flag == 0
        ).scalar() or Decimal('0')

        cashback = db.session.query(func.sum(MAppCommissionRecord.amount)).filter(
            MAppCommissionRecord.user_id == user_id,
            MAppCommissionRecord.record_type == 'CASHBACK',
            MAppCommissionRecord.del_flag == 0
        ).scalar() or Decimal('0')

        # win_loss 当前周期实时预估（结算前无 DB 记录，需实时计算）
        win_loss_estimated = Decimal('0')
        win_loss_activities = MAppInvitationActivity.query.filter(
            MAppInvitationActivity.commission_type == 'win_loss',
            MAppInvitationActivity.method_commission_enabled == 1,
            MAppInvitationActivity.del_flag == 0
        ).all()
        for act in win_loss_activities:
            rt = calculate_win_loss_commission_realtime(user_id, act)
            win_loss_estimated += rt['estimated_amount']

        win_loss_commission = win_loss_commission_db + win_loss_estimated
        # current_period_amount 同样补入 win_loss 实时预估
        current_period_amount = current_period_amount + win_loss_estimated

        return jsonify({
            'code': SUCCESS_CODE,
            'data': {
                'pending_amount': float(pending_amount),
                'settled_amount': float(settled_amount),
                'paid_amount': float(paid_amount),
                'total_earned': float(pending_amount + settled_amount + paid_amount),
                'current_period_amount': float(current_period_amount),
                'by_type': {
                    'turnover_commission': float(turnover_commission),
                    'win_loss_commission': float(win_loss_commission),
                    'win_loss_estimated_current_period': float(win_loss_estimated),
                    'cashback': float(cashback)
                },
                'current_periods': {
                    'week': current_week_period,
                    'month': current_month_period
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


# ==================== 邀请限制检查 ====================
@invitation_v2.route('/downline-count', methods=['GET'])
@auth.login_required
def get_downline_count():
    """获取当前用户的下线数量和邀请限制"""
    try:
        MAX_INVITES = 10
        user_id = g.user.id
        # 统计邀请的用户总数（参考 get_total_summary，使用 MAppPromotionRelation）
        downline_count = MAppPromotionRelation.query.filter(
            MAppPromotionRelation.promoter_id == user_id,
            MAppPromotionRelation.status == 'Active',
            MAppPromotionRelation.is_counted_in_activity == True,
            MAppPromotionRelation.del_flag == 0
        ).count()

        can_invite = downline_count < MAX_INVITES

        return jsonify({
            'code': SUCCESS_CODE,
            'data': {
                'downline_count': downline_count,
                'max_invites': MAX_INVITES,
                'can_invite': can_invite
            },
            'message': 'success'
        })

    except Exception as e:
        app.logger.error(f"get downline count error: {e}")
        return jsonify({
            'code': SYSTEM_ERROR_CODE,
            'data': None,
            'message': str(e)
        }), 500

# 注意：蓝图已在 app.py 中注册
# 实际路径：/api/invitation_v2/... (使用下划线)
# app.register_blueprint(invitation_v2, url_prefix='/invitation_v2')
