from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy import func

from app_server import app, db, auth, app_opt
from app_server.model.AppMemberModel import AppMember
from app_server.model.MAppInvitationActivityModel import MAppInvitationActivity
from app_server.model.MAppInvitationRewardModel import MAppInvitationReward
from app_server.model.ChargeModel import Charge
from app_server.model.OrderModel import Order  # 假设存在下注模型
from app_server.model.MAppInvitationActivityRuleModel import MAppInvitationActivityRule, RewardRuleType  # 规则模型
from flask import g, request, jsonify, Blueprint

# 常量定义
SUCCESS_CODE = 200
SYSTEM_ERROR_CODE = 501
MIN_RECHARGE_AMOUNT = 5000
PARAM_ERROR_CODE = 401
ACTIVITY_NOT_FOUND_CODE = 402
REWARD_NOT_AVAILABLE_CODE = 403
RULE_NOT_FOUND_CODE = 404
ACTIVITY_NOT_VALID_CODE = 405

# 创建蓝图
activity = Blueprint('activity', __name__)


# 辅助函数：确保数值类型正确转换以避免JSON序列化错误
def ensure_serializable(obj):
    """
    递归确保对象中所有Decimal类型都转换为float，避免JSON序列化错误
    同时确保布尔值保持为bool类型
    """
    if isinstance(obj, dict):
        return {key: ensure_serializable(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [ensure_serializable(item) for item in obj]
    elif isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, bool):
        return bool(obj)  # 确保布尔值保持为bool类型
    else:
        return obj


# 辅助函数：检查用户是否可以访问指定的活动
def can_user_access_activity(user_agent_id, activity):
    """
    检查用户是否可以访问指定的活动
    规则：
    1. 如果活动没有指定agent_id，所有用户都可以访问
    2. 如果活动指定了agent_id，只有该代理下的用户可以访问
    """
    try:
        if not activity:
            return False

        # 如果活动没有指定代理，所有用户都可以访问
        if not hasattr(activity, 'agent_id') or not activity.agent_id:
            return True

        # 检查用户代理ID是否匹配活动的代理ID
        return str(user_agent_id) == str(activity.agent_id)

    except Exception as e:
        print(f"Error checking user access to activity: {str(e)}")
        return False


# 辅助函数：过滤用户可访问的活动列表
def filter_activities_by_user_agent(user_agent_id, activities):
    """
    根据用户的代理权限过滤活动列表
    """
    try:
        if not activities:
            return []

        accessible_activities = []
        for activity in activities:
            if can_user_access_activity(user_agent_id, activity):
                accessible_activities.append(activity)

        return accessible_activities

    except Exception as e:
        print(f"Error filtering activities by user agent: {str(e)}")
        return []


# 辅助函数：检查活动是否有效
def is_activity_valid(activity):
    if not activity or activity.del_flag != 0 or activity.is_closed == 1 or activity.is_active == 0:
        return False

    # 检查奖金池是否耗尽
    if hasattr(activity, 'is_pool_exhausted') and activity.is_pool_exhausted == 1:
        return False

    # 检查奖金池余额是否足够（如果设置了奖金池）
    if (hasattr(activity, 'bonus_pool') and activity.bonus_pool is not None and
            activity.bonus_pool > 0 and
            (not activity.bonus_pool_remaining or activity.bonus_pool_remaining <= 0)):
        return False

    now = datetime.now()
    return activity.start_date <= now <= activity.end_date


# 辅助函数：批量获取用户统计信息以优化性能
def get_user_stats_for_activity(user_id, activity_id):
    """
    批量获取用户统计信息，减少重复查询
    返回用户在指定活动期间的各项统计数据
    """
    try:
        # 获取活动信息
        activity = MAppInvitationActivity.query.filter_by(id=activity_id, del_flag=0).first()
        if not activity:
            return None

        # 构建时间范围条件
        time_conditions = [
            Order.CREATE_TIME >= activity.start_date,
            Order.CREATE_TIME <= activity.end_date
        ]

        # 基础查询条件
        base_conditions = [
                              Order.USER_ID == user_id,
                              Order.STATUS == '1',
                              Order.DEL_FLAG == 0
                          ] + time_conditions

        # 一次性查询获取所有需要的统计信息
        orders_in_period = Order.query.filter(*base_conditions).all()

        # 计算各项统计
        total_bet_amount = sum(float(order.BET_MONEY or 0) for order in orders_in_period)
        total_orders = len(orders_in_period)
        first_order = min(orders_in_period, key=lambda x: x.create_time) if orders_in_period else None

        # 计算盈利订单: BONUS(总奖金包括本金) > BET_MONEY(下注金额)
        profitable_orders = 0
        for order in orders_in_period:
            try:
                if hasattr(order, 'BONUS') and order.BONUS and hasattr(order, 'BET_MONEY'):
                    # 净盈利 = 奖金(包括本金) - 投注金额
                    net_profit = float(order.BONUS or 0) - float(order.BET_MONEY or 0)
                    if net_profit > 0:
                        profitable_orders += 1
            except (AttributeError, ValueError, TypeError):
                continue

        return {
            'activity': activity,
            'total_bet_amount': total_bet_amount,
            'total_orders': total_orders,
            'first_order': first_order,
            'profitable_orders': profitable_orders,
            'orders_in_period': orders_in_period
        }

    except Exception as e:
        print(f"Error in get_user_stats_for_activity: {str(e)}")
        return None


def get_user_activity_progress(user_id, recharge_info, order_info):
    """获取用户在所有活动中的进度情况"""
    try:
        # 获取所有活动（按sort排序）
        activities = MAppInvitationActivity.query.filter(
            MAppInvitationActivity.del_flag == 0,
            MAppInvitationActivity.tenant_id == '10000'
        ).order_by(MAppInvitationActivity.sort.asc()).all()

        completed_activities = []
        pending_activities = []
        last_completed_activity = None
        last_activity_time = None
        next_suggested_activity = None
        next_activity_progress = {}

        for activity in activities:
            # 获取活动的所有规则
            rules = MAppInvitationActivityRule.query.filter(
                MAppInvitationActivityRule.activity_id == activity.id,
                MAppInvitationActivityRule.del_flag == 0
            ).order_by(MAppInvitationActivityRule.sequence).all()

            activity_completed_rules = []
            activity_pending_rules = []

            for rule in rules:
                # 检查用户是否已完成该规则
                completed = check_rule_completion(user_id, rule, recharge_info, order_info)

                if completed['is_completed']:
                    activity_completed_rules.append({
                        'rule_id': rule.id,
                        'rule_type': rule.rule_type,
                        'description': rule.description,
                        'threshold': float(rule.threshold_value or 0),
                        'reward_amount': float(rule.reward_amount or 0),
                        'completed_time': completed['completed_time'],
                        'completed_value': completed['completed_value']
                    })

                    # 更新最后完成的活动
                    if completed['completed_time'] and (
                            not last_activity_time or completed['completed_time'] > last_activity_time):
                        last_activity_time = completed['completed_time']
                        # 格式化阈值显示
                        threshold_value = float(rule.threshold_value)
                        rule_type_display = completed.get('rule_type_display', rule.rule_type)

                        if rule.rule_type == RewardRuleType.INVITE_COUNT.value:
                            threshold_display = f"{threshold_value:.0f}人"
                        else:
                            threshold_display = f"{threshold_value:.2f}元"

                        last_completed_activity = {
                            'activity_title': activity.title,
                            'rule_description': rule.description,
                            'rule_type': rule.rule_type,
                            'rule_type_display': rule_type_display,
                            'threshold': float(threshold_value),
                            'threshold_display': threshold_display,
                            'completed_value': completed['completed_value'],
                            'reward_amount': float(rule.reward_amount or 0),
                            'completion_status': f"已完成 {completed['completed_value']}/{threshold_display}",
                            'completion_description': f"{rule_type_display}达到{completed['completed_value']}(要求{threshold_display})，获得奖励{float(rule.reward_amount or 0):.2f}元",
                            'completed_time': completed['completed_time'].strftime('%Y-%m-%d %H:%M:%S') if completed[
                                'completed_time'] else None
                        }
                else:
                    activity_pending_rules.append({
                        'rule_id': rule.id,
                        'rule_type': rule.rule_type,
                        'description': rule.description,
                        'threshold': float(rule.threshold_value or 0),
                        'reward_amount': float(rule.reward_amount or 0),
                        'current_progress': completed['current_progress'],
                        'progress_percentage': completed['progress_percentage']
                    })

            # 整理活动完成情况
            if activity_completed_rules:
                completed_rules_desc = ', '.join([rule['description'] for rule in activity_completed_rules])
                completed_activities.append({
                    'activity_id': activity.id,
                    'title': activity.title,
                    'completed_rules': activity_completed_rules,
                    'completed_rules_desc': completed_rules_desc
                })

            if activity_pending_rules:
                pending_activities.append({
                    'activity_id': activity.id,
                    'title': activity.title,
                    'pending_rules': activity_pending_rules
                })

                # 设置下一个建议活动（第一个有待完成规则的活动）
                if not next_suggested_activity:
                    next_rule = activity_pending_rules[0]
                    next_suggested_activity = f"{activity.title}: {next_rule['description']}"
                    next_activity_progress = {
                        'activity_title': activity.title,
                        'rule_description': next_rule['description'],
                        'current_progress': next_rule['current_progress'],
                        'threshold': next_rule['threshold'],
                        'progress_percentage': next_rule['progress_percentage']
                    }

        return {
            'completed_activities': completed_activities,
            'pending_activities': pending_activities,
            'last_completed_activity': last_completed_activity,
            'last_activity_time': last_activity_time.strftime('%Y-%m-%d %H:%M:%S') if last_activity_time else None,
            'next_suggested_activity': next_suggested_activity,
            'next_activity_progress': next_activity_progress
        }

    except Exception as e:
        print(f"Error in get_user_activity_progress: {str(e)}")
        return {
            'completed_activities': [],
            'pending_activities': [],
            'last_completed_activity': None,
            'last_activity_time': None,
            'next_suggested_activity': None,
            'next_activity_progress': {}
        }


def check_rule_completion(user_id, rule, recharge_info, order_info):
    """检查用户是否完成了特定规则"""
    try:
        rule_type = rule.rule_type
        threshold = float(rule.threshold_value)

        if rule_type == RewardRuleType.INVITE_COUNT.value:
            # 邀请人数规则
            invited_count = AppMember.query.filter(
                AppMember.rid == user_id,
                AppMember.del_flag == 0
            ).count()

            is_completed = invited_count >= threshold
            return {
                'is_completed': is_completed,
                'completed_time': datetime.now() if is_completed else None,
                'completed_value': f"{invited_count}人",
                'current_progress': float(invited_count),
                'progress_percentage': float(min(100, (invited_count / threshold) * 100)) if threshold > 0 else 0.0,
                'rule_type_display': '邀请人数'
            }

        elif rule_type == RewardRuleType.INVITEE_FIRST_RECHARGE.value:
            # 被邀请人首充规则
            total_recharge = recharge_info.get('total_recharge', 0)
            is_completed = total_recharge >= threshold
            completed_time = recharge_info.get('first_recharge_time') if is_completed else None

            return {
                'is_completed': is_completed,
                'completed_time': completed_time,
                'completed_value': f"{total_recharge:.2f}元",
                'current_progress': float(total_recharge),
                'progress_percentage': float(min(100, (total_recharge / threshold) * 100)) if threshold > 0 else 0.0,
                'rule_type_display': '首次充值'
            }

        elif rule_type in [RewardRuleType.FIRST_BET.value, RewardRuleType.BET_CASHBACK.value]:
            # 下注相关规则
            total_bet = order_info.get('total_bet', 0)
            is_completed = total_bet >= threshold
            completed_time = order_info.get('first_bet_time') if is_completed else None
            rule_display = '首次下注' if rule_type == RewardRuleType.FIRST_BET.value else '累计下注'

            return {
                'is_completed': is_completed,
                'completed_time': completed_time,
                'completed_value': f"{total_bet:.2f}元",
                'current_progress': float(total_bet),
                'progress_percentage': float(min(100, (total_bet / threshold) * 100)) if threshold > 0 else 0.0,
                'rule_type_display': rule_display
            }

        else:
            # 其他规则类型
            return {
                'is_completed': False,
                'completed_time': None,
                'completed_value': '0',
                'current_progress': 0.0,
                'progress_percentage': 0.0
            }

    except Exception as e:
        print(f"Error checking rule completion: {str(e)}")
        return {
            'is_completed': False,
            'completed_time': None,
            'completed_value': '0',
            'current_progress': 0.0,
            'progress_percentage': 0.0
        }


# 1. 邀请人数达标进度计算
def calculate_invite_count_progress(activity_id, user_id, rule):
    # 查询该用户成功邀请的有效用户数（排除用户自己）
    invited_users = AppMember.query.filter(
        AppMember.rid == user_id,
        AppMember.id != user_id,  # 明确排除用户自己
        AppMember.del_flag == 0
    ).all()

    invited_count = len(invited_users)

    # 已领取该规则奖励的次数
    claimed_count = MAppInvitationReward.query.filter_by(
        activity_id=activity_id,
        referrer_id=user_id,
        rule_id=rule.id,
        status='claimed',
        del_flag=0
    ).count()

    # 计算差额和可领取状态
    threshold = float(rule.threshold_value)
    difference = max(0, threshold - invited_count)
    # 每邀请达到阈值的整数倍数量就可以领取一次奖励
    eligible_claims = invited_count // int(threshold) if threshold > 0 else 0
    available_claims = max(0, eligible_claims - claimed_count)
    can_claim = bool(available_claims > 0 and
                     (int(rule.max_claim_count or 0) == 0 or claimed_count < int(rule.max_claim_count or 0)))

    # 构建qualified_users列表（按邀请时间排序）
    qualified_users = []
    for user in invited_users:
        qualified_users.append({
            'user_id': user.id,
            'user_name': user.name,
            'create_time': user.create_time.strftime('%Y-%m-%d %H:%M:%S') if user.create_time else None
        })

    # 按创建时间排序，最新的在最后
    qualified_users.sort(key=lambda x: x['create_time'] or '0000-00-00 00:00:00')

    return {
        'rule_id': rule.id,
        'rule_type': rule.rule_type,
        'description': rule.description,
        'threshold': float(threshold),
        'current_value': invited_count,
        'difference': float(difference),
        'reward_amount': float(rule.reward_amount or 0),
        'claimed_count': claimed_count,
        'max_claim_count': int(rule.max_claim_count or 0),
        'can_claim': can_claim,
        'is_reached': invited_count >= threshold,
        'available_claims': available_claims,  # 可领取次数
        'qualified_users': qualified_users  # 添加符合条件的用户列表
    }


# 2. 被邀请人首充进度计算
def calculate_invitee_first_recharge_progress(activity_id, user_id, rule):
    # 获取该用户邀请的所有用户（排除用户自己）
    invited_users = AppMember.query.filter(
        AppMember.rid == user_id,
        AppMember.id != user_id,  # 明确排除用户自己
        AppMember.del_flag == 0
    ).all()

    if not invited_users:
        return {
            'rule_id': rule.id,
            'rule_type': rule.rule_type,
            'description': rule.description,
            'threshold': float(rule.threshold_value or 0),
            'current_value': 0,
            'difference': float(rule.threshold_value or 0),
            'reward_amount': float(rule.reward_amount or 0),
            'claimed_count': 0,
            'max_claim_count': int(rule.max_claim_count or 0),
            'can_claim': False,
            'is_reached': False,
            'available_claims': 0
        }

    # 对于首次充值规则，需要检查已经触发过奖励的被邀请用户，避免重复奖励
    already_rewarded_users = set()
    rewarded_records = MAppInvitationReward.query.filter_by(
        activity_id=activity_id,
        referrer_id=user_id,
        rule_id=rule.id,
        status='claimed',
        del_flag=0
    ).all()

    for record in rewarded_records:
        if record.referred_user_id:
            already_rewarded_users.add(record.referred_user_id)

    # 统计被邀请人中首充达到阈值且未获得过奖励的人数
    qualified_count = 0
    invited_user_ids = [user.id for user in invited_users]

    for invited_user_id in invited_user_ids:
        # 跳过已经获得过奖励的用户
        if invited_user_id in already_rewarded_users:
            continue

        # 检查是否有首充记录且金额达标
        first_recharge = Charge.query.filter_by(
            mb_id=invited_user_id,
            status='Success'  # 假设充值成功状态
        ).order_by(Charge.create_time).first()

        if first_recharge and float(first_recharge.amount) >= float(rule.threshold_value):
            qualified_count += 1

    # 已领取该规则奖励的次数
    claimed_count = len(rewarded_records)

    # 可领取次数：有新的合格用户且未达到最大领取次数
    available_claims = max(0, qualified_count - claimed_count)

    can_claim = bool(available_claims > 0 and
                     (int(rule.max_claim_count or 0) == 0 or claimed_count < int(rule.max_claim_count or 0)))

    return {
        'rule_id': rule.id,
        'rule_type': rule.rule_type,
        'description': rule.description,
        'threshold': float(rule.threshold_value or 0),
        'current_value': qualified_count,
        'difference': max(0, (claimed_count + 1) - qualified_count),
        'reward_amount': float(rule.reward_amount or 0),
        'claimed_count': claimed_count,
        'max_claim_count': int(rule.max_claim_count or 0),
        'available_claims': available_claims,  # 新增：可领取次数
        'can_claim': can_claim,
        'is_reached': qualified_count > 0
    }


# 3. 被邀请用户首次下注进度计算(重构版)
def calculate_first_bet_progress(activity_id, user_id, rule):
    """
    计算被邀请用户首次下注进度，邀请者获得奖励
    规则：被邀请用户第一次下注金额达到规则数值，邀请者可以领取一次奖励

    业务逻辑：
    1. 查询当前用户(邀请者)的所有被邀请用户
    2. 统计被邀请用户中首次下注达到阈值的人数
    3. 计算邀请者可领取的奖励次数
    """
    try:
        # 获取活动信息以限制时间范围
        activity = MAppInvitationActivity.query.filter_by(id=activity_id, del_flag=0).first()
        threshold_value = float(rule.threshold_value or 0)

        # 查询邀请者的所有被邀请用户（排除用户自己）
        invited_users = AppMember.query.filter(
            AppMember.rid == user_id,
            AppMember.id != user_id,  # 明确排除用户自己
            AppMember.del_flag == 0
        ).all()

        if not invited_users:
            return {
                'rule_id': rule.id,
                'rule_type': rule.rule_type,
                'description': rule.description or f'被邀请用户首次下注达到{threshold_value}',
                'threshold': float(threshold_value),
                'current_value': 0.0,
                'difference': 1.0,
                'reward_amount': float(rule.reward_amount or 0),
                'claimed_count': 0,
                'max_claim_count': int(rule.max_claim_count or 0),
                'can_claim': False,
                'is_reached': False,
                'available_claims': 0,
                'qualified_users': []
            }

        invited_user_ids = [user.id for user in invited_users]
        qualified_users = []

        # 统计每个被邀请用户的首次下注情况
        for invited_user_id in invited_user_ids:
            # 构建查询条件
            query = Order.query.filter(
                Order.USER_ID == invited_user_id,
                Order.STATUS == '1',
                Order.DEL_FLAG == 0
            )

            # 如果活动存在，限制时间范围
            if activity:
                query = query.filter(
                    Order.CREATE_TIME >= activity.start_date,
                    Order.CREATE_TIME <= activity.end_date
                )

            # 获取首次下注记录
            first_bet = query.order_by(Order.CREATE_TIME).first()

            if first_bet:
                bet_amount = float(first_bet.BET_MONEY or 0)
                if bet_amount >= threshold_value:
                    # 找到用户信息
                    invited_user = next((u for u in invited_users if u.id == invited_user_id), None)
                    qualified_users.append({
                        'user_id': invited_user_id,
                        'user_name': invited_user.name if invited_user else '',
                        'bet_amount': float(bet_amount),
                        'bet_time': first_bet.CREATE_TIME.strftime('%Y-%m-%d %H:%M:%S')
                    })

        # 已领取该规则奖励的次数
        claimed_count = MAppInvitationReward.query.filter_by(
            activity_id=activity_id,
            referrer_id=user_id,
            rule_id=rule.id,
            status='claimed',
            del_flag=0
        ).count()

        # 计算可领取次数
        qualified_count = len(qualified_users)
        max_claim = int(rule.max_claim_count or 0)
        available_claims = max(0, qualified_count - claimed_count)
        can_claim = bool(available_claims > 0 and
                         (max_claim == 0 or claimed_count < max_claim))

        return {
            'rule_id': rule.id,
            'rule_type': rule.rule_type,
            'description': rule.description or f'被邀请用户首次下注达到{threshold_value}',
            'threshold': threshold_value,
            'current_value': qualified_count,
            'difference': max(0, (claimed_count + 1) - qualified_count),
            'reward_amount': float(rule.reward_amount or 0),
            'claimed_count': claimed_count,
            'max_claim_count': max_claim,
            'can_claim': can_claim,
            'is_reached': qualified_count > 0,
            'qualified_users': qualified_users,
            'available_claims': available_claims,
            'total_invited_users': len(invited_users)
        }

    except Exception as e:
        # 异常情况返回安全默认值
        return {
            'rule_id': rule.id,
            'rule_type': rule.rule_type,
            'description': rule.description or '被邀请用户首次下注规则',
            'threshold': float(rule.threshold_value or 0),
            'current_value': 0,
            'difference': 1,
            'reward_amount': float(rule.reward_amount or 0),
            'claimed_count': 0,
            'max_claim_count': int(rule.max_claim_count or 0),
            'can_claim': False,
            'is_reached': False,
            'error': str(e)
        }


# 4. 被邀请用户首次下注盈利进度计算(重构版)
def calculate_bet_profit_progress(activity_id, user_id, rule):
    """
    计算被邀请用户首次下注盈利进度，邀请者获得奖励
    规则：被邀请用户第一次下注净赢数值达到规则数值，邀请者可以领取一次奖励

    业务逻辑：
    1. 查询当前用户(邀请者)的所有被邀请用户
    2. 统计被邀请用户中首次下注净赢达到阈值的人数
    3. 计算邀请者可领取的奖励次数
    """
    try:
        # 获取活动信息以限制时间范围
        activity = MAppInvitationActivity.query.filter_by(id=activity_id, del_flag=0, tenant_id='10000').first()
        threshold_value = float(rule.threshold_value or 0)

        # 查询邀请者的所有被邀请用户（排除用户自己）
        invited_users = AppMember.query.filter(
            AppMember.rid == user_id,
            AppMember.id != user_id,  # 明确排除用户自己
            AppMember.del_flag == 0,
            AppMember.tenant_id == '10000'
        ).all()

        if not invited_users:
            return {
                'rule_id': rule.id,
                'rule_type': rule.rule_type,
                'description': rule.description or f'被邀请用户首次下注净赢达到{threshold_value}',
                'threshold': float(threshold_value),
                'current_value': 0.0,
                'difference': 1.0,
                'reward_amount': float(rule.reward_amount or 0),
                'claimed_count': 0,
                'max_claim_count': int(rule.max_claim_count or 0),
                'can_claim': False,
                'is_reached': False,
                'available_claims': 0,
                'qualified_users': []
            }

        invited_user_ids = [user.id for user in invited_users]
        qualified_users = []

        # 统计每个被邀请用户的首次下注净赢情况
        for invited_user_id in invited_user_ids:
            # 构建查询条件
            query = Order.query.filter(
                Order.USER_ID == invited_user_id,
                Order.STATUS == 1,
                Order.DEL_FLAG == 0,
                Order.TENANT_ID == '10000'
            )

            # 如果活动存在，限制时间范围
            if activity:
                query = query.filter(
                    Order.CREATE_TIME >= activity.start_date,
                    Order.CREATE_TIME <= activity.end_date
                )

            # 获取首次下注记录
            first_bet = query.order_by(Order.CREATE_TIME).first()

            if first_bet:
                # 计算净赢金额: BONUS(总奖金包括本金) - BET_MONEY(下注金额) = 实际盈利
                net_profit = 0
                try:
                    if hasattr(first_bet, 'BONUS') and first_bet.BONUS and hasattr(first_bet, 'BET_MONEY'):
                        # 净盈利 = 奖金(包括本金) - 投注金额
                        net_profit = float(first_bet.BONUS or 0) - float(first_bet.BET_MONEY or 0)
                except (AttributeError, ValueError, TypeError):
                    net_profit = 0

                if net_profit >= threshold_value:
                    # 找到用户信息
                    invited_user = next((u for u in invited_users if u.id == invited_user_id), None)
                    qualified_users.append({
                        'user_id': invited_user_id,
                        'user_name': invited_user.name if invited_user else '',
                        'bet_amount': float(first_bet.BET_MONEY or 0),
                        'net_profit': float(net_profit),
                        'bet_time': first_bet.CREATE_TIME.strftime('%Y-%m-%d %H:%M:%S')
                    })

        # 已领取该规则奖励的次数
        claimed_count = MAppInvitationReward.query.filter_by(
            activity_id=activity_id,
            referrer_id=user_id,
            rule_id=rule.id,
            status='claimed',
            del_flag=0
        ).count()

        # 计算可领取次数
        qualified_count = len(qualified_users)
        max_claim = int(rule.max_claim_count or 0)
        available_claims = max(0, qualified_count - claimed_count)
        can_claim = bool(available_claims > 0 and
                         (max_claim == 0 or claimed_count < max_claim))

        return {
            'rule_id': rule.id,
            'rule_type': rule.rule_type,
            'description': rule.description or f'被邀请用户首次下注净赢达到{threshold_value}',
            'threshold': threshold_value,
            'current_value': qualified_count,
            'difference': max(0, (claimed_count + 1) - qualified_count),
            'reward_amount': float(rule.reward_amount or 0),
            'claimed_count': claimed_count,
            'max_claim_count': max_claim,
            'can_claim': can_claim,
            'is_reached': qualified_count > 0,
            'qualified_users': qualified_users,
            'available_claims': available_claims,
            'total_invited_users': len(invited_users)
        }

    except Exception as e:
        # 异常情况返回安全默认值
        return {
            'rule_id': rule.id,
            'rule_type': rule.rule_type,
            'description': rule.description or '被邀请用户首次下注盈利规则',
            'threshold': float(rule.threshold_value or 0),
            'current_value': 0,
            'difference': 1,
            'reward_amount': float(rule.reward_amount or 0),
            'claimed_count': 0,
            'max_claim_count': int(rule.max_claim_count or 0),
            'can_claim': False,
            'is_reached': False,
            'error': str(e)
        }


# 5. 被邀请用户累计下注返还进度计算(重构版)
def calculate_bet_cashback_progress(activity_id, user_id, rule):
    """
    计算被邀请用户累计下注返还进度，邀请者获得奖励
    规则：被邀请用户下注达到规则数值（累计，不是单次），邀请者可以领取一次奖励

    业务逻辑：
    1. 查询当前用户(邀请者)的所有被邀请用户
    2. 统计被邀请用户中累计下注达到阈值的人数
    3. 计算邀请者可领取的奖励次数
    """
    try:
        # 获取活动信息以限制时间范围
        activity = MAppInvitationActivity.query.filter_by(id=activity_id, del_flag=0).first()
        threshold = float(rule.threshold_value or 0)

        if threshold <= 0:
            # 阈值无效，返回默认值
            return {
                'rule_id': rule.id,
                'rule_type': rule.rule_type,
                'description': rule.description or '被邀请用户累计下注返还规则',
                'threshold': 0,
                'current_value': 0.0,
                'difference': 0,
                'reward_amount': float(rule.reward_amount or 0),
                'claimed_count': 0,
                'max_claim_count': int(rule.max_claim_count or 0),
                'can_claim': False,
                'is_reached': False,
                'qualified_users': [],
                'error': '阈值配置无效'
            }

        # 查询邀请者的所有被邀请用户（排除用户自己）
        invited_users = AppMember.query.filter(
            AppMember.rid == user_id,
            AppMember.id != user_id,  # 明确排除用户自己
            AppMember.del_flag == 0
        ).all()

        if not invited_users:
            return {
                'rule_id': rule.id,
                'rule_type': rule.rule_type,
                'description': rule.description or f'被邀请用户累计下注达到{threshold}',
                'threshold': float(threshold),
                'current_value': 0.0,
                'difference': 1.0,
                'reward_amount': float(rule.reward_amount or 0),
                'claimed_count': 0,
                'max_claim_count': int(rule.max_claim_count or 0),
                'can_claim': False,
                'is_reached': False,
                'available_claims': 0,
                'qualified_users': []
            }

        invited_user_ids = [user.id for user in invited_users]
        qualified_users = []

        # 统计每个被邀请用户的累计下注情况
        for invited_user_id in invited_user_ids:
            # 构建查询条件统计累计下注金额
            query_conditions = [
                Order.USER_ID == invited_user_id,
                Order.STATUS == '1',
                Order.DEL_FLAG == 0
            ]

            # 如果活动存在，限制时间范围
            if activity:
                query_conditions.extend([
                    Order.CREATE_TIME >= activity.start_date,
                    Order.CREATE_TIME <= activity.end_date
                ])

            # 统计该用户在活动期间的累计下注金额
            total_bet_amount = db.session.query(func.sum(Order.BET_MONEY)).filter(
                *query_conditions
            ).scalar() or 0

            total_bet_amount = float(total_bet_amount)

            if total_bet_amount >= threshold:
                # 找到用户信息
                invited_user = next((u for u in invited_users if u.id == invited_user_id), None)

                # 计算该用户的下注详情
                bet_count = db.session.query(func.count(Order.ID)).filter(
                    *query_conditions
                ).scalar() or 0

                # 获取最近一次下注时间
                last_bet = Order.query.filter(*query_conditions).order_by(
                    Order.CREATE_TIME.desc()
                ).first()

                qualified_users.append({
                    'user_id': invited_user_id,
                    'user_name': invited_user.name if invited_user else '',
                    'total_bet_amount': float(total_bet_amount),
                    'bet_count': bet_count,
                    'excess_amount': float(total_bet_amount - threshold),  # 超出阈值的金额
                    'last_bet_time': last_bet.create_time.strftime('%Y-%m-%d %H:%M:%S') if last_bet else None
                })

        # 已领取该规则奖励的次数
        claimed_count = MAppInvitationReward.query.filter_by(
            activity_id=activity_id,
            referrer_id=user_id,
            rule_id=rule.id,
            status='claimed',
            del_flag=0
        ).count()

        # 计算可领取次数
        qualified_count = len(qualified_users)
        max_claim = int(rule.max_claim_count or 0)
        available_claims = max(0, qualified_count - claimed_count)
        can_claim = bool(available_claims > 0 and
                         (max_claim == 0 or claimed_count < max_claim))

        # 计算总的累计下注金额和进度信息
        total_all_bets = sum(user['total_bet_amount'] for user in qualified_users)
        progress_summary = {
            'total_qualified_amount': float(total_all_bets),
            'average_bet_per_user': float(total_all_bets / qualified_count) if qualified_count > 0 else 0.0,
            'completion_rate': round((qualified_count / len(invited_users) * 100), 2) if invited_users else 0.0
        }

        return {
            'rule_id': rule.id,
            'rule_type': rule.rule_type,
            'description': rule.description or f'被邀请用户累计下注达到{threshold}',
            'threshold': float(threshold),
            'current_value': qualified_count,
            'difference': max(0, (claimed_count + 1) - qualified_count),
            'reward_amount': float(rule.reward_amount or 0),
            'claimed_count': claimed_count,
            'max_claim_count': max_claim,
            'can_claim': can_claim,
            'is_reached': qualified_count > 0,
            'qualified_users': qualified_users,
            'available_claims': available_claims,
            'total_invited_users': len(invited_users),
            'progress_summary': progress_summary
        }

    except Exception as e:
        # 异常情况返回安全默认值
        return {
            'rule_id': rule.id,
            'rule_type': rule.rule_type,
            'description': rule.description or '被邀请用户累计下注返还规则',
            'threshold': float(rule.threshold_value or 0),
            'current_value': 0,
            'difference': 1,
            'reward_amount': float(rule.reward_amount or 0),
            'claimed_count': 0,
            'max_claim_count': int(rule.max_claim_count or 0),
            'can_claim': False,
            'is_reached': False,
            'error': str(e)
        }


@activity.route('/rewards/claim', methods=['POST'])
@auth.login_required
def claim_reward():
    """领取奖励"""
    try:
        # 获取请求数据
        data = request.json
        activity_id = data.get('activity_id')
        rule_id = data.get('rule_id')

        # 验证参数
        if not all([activity_id, rule_id]):
            return jsonify({
                'code': PARAM_ERROR_CODE,
                'data': None,
                'message': 'Activity ID and rule ID are required parameters'
            }), 400

        # 获取当前用户ID和代理ID
        user_id = g.user.id
        user_agent_id = g.user.aid

        # 检查活动是否存在且有效
        activity = MAppInvitationActivity.query.filter(
            MAppInvitationActivity.id == activity_id,
            MAppInvitationActivity.del_flag == 0,
            MAppInvitationActivity.tenant_id == '10000'
        ).first()

        if not activity:
            return jsonify({
                'code': ACTIVITY_NOT_FOUND_CODE,
                'data': None,
                'message': 'Activity not found or deleted'
            }), 404

        # 检查用户是否有权限访问该活动
        if not can_user_access_activity(user_agent_id, activity):
            return jsonify({
                'code': ACTIVITY_NOT_VALID_CODE,
                'data': None,
                'message': 'You do not have permission to access this activity'
            }), 403

        if not is_activity_valid(activity):
            return jsonify({
                'code': ACTIVITY_NOT_VALID_CODE,
                'data': None,
                'message': 'Activity is inactive, closed or not in valid period'
            }), 400

        # 额外检查活动是否因奖金池耗尽而关闭
        if activity.is_closed:
            return jsonify({
                'code': ACTIVITY_NOT_VALID_CODE,
                'data': None,
                'message': 'Activity is closed, cannot claim rewards'
            }), 400

        # 检查规则是否存在
        rule = MAppInvitationActivityRule.query.filter_by(
            id=rule_id,
            activity_id=activity_id,
            del_flag=0
        ).first()

        if not rule:
            return jsonify({
                'code': RULE_NOT_FOUND_CODE,
                'data': None,
                'message': 'Reward rule not found'
            }), 404

        # 检查是否可以领取
        rule_processors = {
            RewardRuleType.INVITE_COUNT.value: calculate_invite_count_progress,
            RewardRuleType.INVITEE_FIRST_RECHARGE.value: calculate_invitee_first_recharge_progress,
            RewardRuleType.FIRST_BET.value: calculate_first_bet_progress,
            RewardRuleType.BET_PROFIT.value: calculate_bet_profit_progress,
            RewardRuleType.BET_CASHBACK.value: calculate_bet_cashback_progress
        }

        processor = rule_processors.get(rule.rule_type)
        if not processor:
            return jsonify({
                'code': SYSTEM_ERROR_CODE,
                'data': None,
                'message': f'Unsupported rule type: {rule.rule_type}'
            }), 500

        progress = processor(activity_id, user_id, rule)
        # 添加活动标题到进度信息中
        progress['activity_title'] = activity.title
        if not progress['can_claim']:
            # 生成详细的错误提示信息
            error_message = 'Cannot claim reward: '
            error_details = []

            # 检查是否达到要求
            if not progress.get('is_reached', False):
                current = progress.get('current_value', 0)
                threshold = progress.get('threshold', 0)
                difference = progress.get('difference', 0)
                error_details.append(f'requirement not met (current: {current}, required: {threshold}, need {difference} more)')

            # 检查是否达到最大领取次数
            claimed_count = progress.get('claimed_count', 0)
            max_claim = progress.get('max_claim_count', 0)
            if max_claim > 0 and claimed_count >= max_claim:
                error_details.append(f'maximum claim limit reached ({claimed_count}/{max_claim})')

            # 检查是否有可领取次数
            available_claims = progress.get('available_claims', 0)
            if available_claims <= 0:
                error_details.append('no available claims')

            # 合并错误信息
            if error_details:
                error_message += ', '.join(error_details)
            else:
                error_message = 'Requirements not met or maximum claims reached'

            return jsonify({
                'code': REWARD_NOT_AVAILABLE_CODE,
                'data': progress,
                'message': error_message
            }), 400

        # 开始事务，使用行锁防止并发问题
        try:
            # 使用行锁重新获取活动信息防止并发
            activity = db.session.query(MAppInvitationActivity).filter(
                MAppInvitationActivity.id == activity_id,
                MAppInvitationActivity.del_flag == 0
            ).with_for_update().first()

            if not activity:
                return jsonify({
                    'code': ACTIVITY_NOT_FOUND_CODE,
                    'data': None,
                    'message': 'Activity not found or deleted'
                }), 404

            # 检查奖金池余额是否足够（如果活动设置了奖金池）
            if hasattr(activity, 'bonus_pool') and activity.bonus_pool is not None:
                # 如果奖金池为0或者余额不足，禁止领取
                if (activity.bonus_pool <= 0 or
                        not activity.bonus_pool_remaining or
                        activity.bonus_pool_remaining <= 0 or
                        activity.bonus_pool_remaining < rule.reward_amount):
                    # 奖金池余额不足，标记活动为已关闭和奖金池耗尽
                    activity.is_pool_exhausted = 1
                    activity.is_closed = True
                    db.session.commit()
                    return jsonify({
                        'code': REWARD_NOT_AVAILABLE_CODE,
                        'data': None,
                        'message': 'Insufficient bonus pool balance, activity automatically closed'
                    }), 400

            # 获取符合条件的被邀请用户（如果有的话）
            qualified_users = progress.get('qualified_users', [])
            referred_user_id = None

            # 根据规则类型决定如何设置referred_user_id
            if qualified_users:
                if rule.rule_type in [
                    RewardRuleType.INVITEE_FIRST_RECHARGE.value,
                    RewardRuleType.FIRST_BET.value,
                    RewardRuleType.BET_PROFIT.value,
                    RewardRuleType.BET_CASHBACK.value
                ]:
                    # 对于基于特定用户行为的规则，记录触发奖励的具体用户
                    # 这里我们可以记录最近符合条件的用户，或者按照业务逻辑选择
                    referred_user_id = qualified_users[-1].get('user_id')  # 取最后一个（最新的）
                elif rule.rule_type == RewardRuleType.INVITE_COUNT.value:
                    # 对于邀请数量规则，记录最新邀请的用户
                    referred_user_id = qualified_users[-1].get('user_id') if qualified_users else None

            # 创建奖励记录
            from uuid import uuid4
            reward = MAppInvitationReward(
                id=str(uuid4()),
                activity_id=activity_id,
                rule_id=rule_id,
                referrer_id=user_id,
                referred_user_id=referred_user_id,  # 保存触发奖励的被邀请用户ID
                reward_amount=rule.reward_amount,
                bonus_type=activity.bonus_type,  # 保存奖金类型
                status='claimed',
                claimed_at=datetime.now(),
                create_time=datetime.now(),
                del_flag=0,
                tenant_id='10000'
            )

            # 更新奖金池余额（如果活动设置了奖金池）
            if hasattr(activity, 'bonus_pool') and activity.bonus_pool is not None and activity.bonus_pool > 0:
                activity.bonus_pool_remaining = activity.bonus_pool_remaining - rule.reward_amount

                # 如果奖金池耗尽，标记状态并关闭活动
                if activity.bonus_pool_remaining <= 0:
                    activity.is_pool_exhausted = 1
                    activity.is_closed = True

            # 为会员增加奖励金额到余额
            from app_server.model.AppMemberModel import AppMember
            from app_server.model.AppMemberBalanceLogModel import AppMemberBalanceLog, TransactionType

            # 使用行锁获取会员信息防止并发
            member = db.session.query(AppMember).filter(
                AppMember.id == user_id
            ).with_for_update().first()

            if not member:
                return jsonify({
                    'code': PARAM_ERROR_CODE,
                    'data': None,
                    'message': 'Member not found'
                }), 400

            # 更新会员促销活动金额
            old_balance = member.money_promotion if member.money_promotion else 0
            new_balance = old_balance + rule.reward_amount
            member.money_promotion = new_balance

            # 记录会员促销活动金额流水
            balance_log = AppMemberBalanceLog(
                id=str(uuid4()),
                sn=f"REWARD_{reward.id}",
                type=TransactionType.Reward,
                type_sub="invitation_reward",
                type_sub_data_id=reward.id,
                mb_id=user_id,
                mb_username=member.name if hasattr(member, 'name') else member.username,
                money=rule.reward_amount,
                start_balance=old_balance,
                end_balance=new_balance,
                source="System",
                target="Ewallet",
                status=1,
                source_status=1
            )

            db.session.add(reward)
            db.session.add(member)  # 添加更新后的member到session
            # db.session.add(balance_log)
            db.session.commit()

        except Exception as transaction_error:
            db.session.rollback()
            return jsonify({
                'code': SYSTEM_ERROR_CODE,
                'data': None,
                'message': f'事务处理失败: {str(transaction_error)}'
            }), 500

        return jsonify({
            'code': SUCCESS_CODE,
            'data': {
                'reward_id': reward.id,
                'amount': float(reward.reward_amount),
                'claimed_at': reward.claimed_at.strftime('%Y-%m-%d %H:%M:%S'),
                'rule_type': rule.rule_type,
                'member_balance': {
                    'old_money_promotion': float(old_balance),
                    'new_money_promotion': float(new_balance),
                    'promotion_change': float(rule.reward_amount)
                },
                'bonus_pool': {
                    'remaining': float(activity.bonus_pool_remaining or 0),
                    'is_exhausted': bool(activity.is_pool_exhausted),
                    'activity_closed': bool(activity.is_closed)
                } if hasattr(activity, 'bonus_pool') and activity.bonus_pool is not None else None
            },
            'message': 'Reward claimed successfully'
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': SYSTEM_ERROR_CODE,
            'data': None,
            'message': str(e)
        }), 500


@activity.route('/active', methods=['GET'])
@auth.login_required
def get_active_activities():
    """获取当前激活状态的活动列表"""
    try:
        # 获取当前用户的代理ID
        user_agent_id = g.user.aid
        now = datetime.now()

        # 查询激活状态的活动
        all_activities = MAppInvitationActivity.query.filter(
            MAppInvitationActivity.del_flag == 0,
            MAppInvitationActivity.is_active == 1,
            MAppInvitationActivity.is_closed == 0,
            MAppInvitationActivity.start_date <= now,
            MAppInvitationActivity.end_date >= now,
            MAppInvitationActivity.tenant_id == '10000'
        ).order_by(MAppInvitationActivity.sort.asc(), MAppInvitationActivity.create_time.desc()).all()

        # 过滤用户可访问的活动
        activities = filter_activities_by_user_agent(user_agent_id, all_activities)

        # 格式化活动数据
        activity_list = []
        for activity in activities:
            activity_list.append({
                'id': activity.id,
                'title': activity.title,
                'description': activity.description,
                'bonus_type': activity.bonus_type,  # 新增奖金类型字段
                'start_date': activity.start_date.strftime('%Y-%m-%d %H:%M:%S'),
                'end_date': activity.end_date.strftime('%Y-%m-%d %H:%M:%S'),
                'reward_amount': float(activity.reward_amount) if activity.reward_amount else 0,
                'max_reward_count': activity.max_reward_count,
                'is_active': activity.is_active,
                'create_time': activity.create_time.strftime('%Y-%m-%d %H:%M:%S') if activity.create_time else None,
                # 奖金池相关字段
                'bonus_pool': float(activity.bonus_pool or 0),
                'bonus_pool_remaining': float(activity.bonus_pool_remaining or 0),
                'agent_id': activity.agent_id,
                'is_pool_exhausted': bool(activity.is_pool_exhausted) if hasattr(activity,
                                                                                 'is_pool_exhausted') else False
            })

        return jsonify({
            'code': SUCCESS_CODE,
            'data': {
                'activities': activity_list,
                'count': len(activity_list)
            },
            'message': 'success'
        }), 200

    except Exception as e:
        return jsonify({
            'code': SYSTEM_ERROR_CODE,
            'data': None,
            'message': str(e)
        }), 500


@activity.route('/activities_with_progress', methods=['GET'])
@auth.login_required
def get_activities_with_progress():
    """获取所有活动及其进度信息"""
    try:
        # 获取当前用户ID和代理ID
        user_id = g.user.id
        user_agent_id = g.user.aid
        now = datetime.now()

        # 查询所有活动（按创建时间倒序）
        all_activities = MAppInvitationActivity.query.filter(
            MAppInvitationActivity.del_flag == 0,
            MAppInvitationActivity.tenant_id == '10000'
        ).order_by(MAppInvitationActivity.sort.asc(), MAppInvitationActivity.create_time.desc()).all()

        # 过滤用户可访问的活动
        activities = filter_activities_by_user_agent(user_agent_id, all_activities)

        # 规则处理器映射
        rule_processors = {
            RewardRuleType.INVITE_COUNT.value: calculate_invite_count_progress,
            RewardRuleType.INVITEE_FIRST_RECHARGE.value: calculate_invitee_first_recharge_progress,
            RewardRuleType.FIRST_BET.value: calculate_first_bet_progress,
            RewardRuleType.BET_PROFIT.value: calculate_bet_profit_progress,
            RewardRuleType.BET_CASHBACK.value: calculate_bet_cashback_progress
        }

        activities_data = []
        total_claimable_reward = 0
        total_invited_users = 0

        for activity in activities:
            # 检查活动状态
            is_active = is_activity_valid(activity)

            # 获取活动的所有规则
            rules = MAppInvitationActivityRule.query.filter_by(
                activity_id=activity.id,
                del_flag=0,
                tenant_id='10000'
            ).order_by(MAppInvitationActivityRule.sequence).all()

            # 计算规则进度
            progress_list = []
            activity_claimable = 0

            for rule in rules:
                processor = rule_processors.get(rule.rule_type)
                if processor:
                    progress = processor(activity.id, user_id, rule)
                    # 添加活动标题到进度信息中
                    progress['activity_title'] = activity.title
                    progress_list.append(progress)
                    if progress['can_claim']:
                        activity_claimable += progress['reward_amount']

            # 计算邀请用户数（只计算一次，排除用户自己）
            if not total_invited_users:
                total_invited_users = AppMember.query.filter(
                    AppMember.rid == user_id,
                    AppMember.id != user_id,  # 明确排除用户自己
                    AppMember.del_flag == 0
                ).count()

            total_claimable_reward += activity_claimable

            activities_data.append({
                'id': activity.id,
                'title': activity.title,
                'description': activity.description,
                'bonus_type': activity.bonus_type,  # 新增奖金类型字段
                'start_date': activity.start_date.strftime('%Y-%m-%d %H:%M:%S'),
                'end_date': activity.end_date.strftime('%Y-%m-%d %H:%M:%S'),
                'reward_amount': float(activity.reward_amount) if activity.reward_amount else 0,
                'max_reward_count': activity.max_reward_count,
                'is_active': is_active,
                'is_valid': is_active,  # 向后兼容
                'status': 'active' if is_active else 'inactive',
                'progress': progress_list,
                'claimable_reward': float(activity_claimable),
                'rules_count': len(rules),
                'completed_rules': len([p for p in progress_list if p['is_reached']]),
                'create_time': activity.create_time.strftime('%Y-%m-%d %H:%M:%S') if activity.create_time else None,
                # 奖金池相关字段
                'bonus_pool': float(activity.bonus_pool or 0),
                'bonus_pool_remaining': float(activity.bonus_pool_remaining or 0),
                'agent_id': activity.agent_id,
                'is_pool_exhausted': bool(activity.is_pool_exhausted) if hasattr(activity,
                                                                                 'is_pool_exhausted') else False
            })

        # 确保所有数据都能正确JSON序列化
        response_data = {
            'code': SUCCESS_CODE,
            'data': {
                'activities': activities_data,
                'summary': {
                    'total_activities': len(activities_data),
                    'active_activities': len([a for a in activities_data if a['is_active']]),
                    'total_claimable_reward': float(total_claimable_reward),
                    'total_invited_users': total_invited_users,
                    'activities_with_claimable': len([a for a in activities_data if a['claimable_reward'] > 0])
                }
            },
            'message': 'success'
        }
        
        return jsonify(ensure_serializable(response_data)), 200

    except Exception as e:
        return jsonify({
            'code': SYSTEM_ERROR_CODE,
            'data': None,
            'message': str(e)
        }), 500


@activity.route('/progress', methods=['GET'])
@auth.login_required
def get_activity_progress():
    """查询用户在指定活动中的所有规则进度（支持不传activity_id获取第一个激活活动）"""
    activity_id = request.args.get('activity_id')
    try:
        # 获取当前用户ID和代理ID
        user_id = g.user.id
        user_agent_id = g.user.aid

        # 如果没有传activity_id，获取第一个激活的活动
        if not activity_id:
            now = datetime.now()
            all_active_activities = MAppInvitationActivity.query.filter(
                MAppInvitationActivity.del_flag == 0,
                MAppInvitationActivity.is_active == 1,
                MAppInvitationActivity.is_closed == 0,
                MAppInvitationActivity.start_date <= now,
                MAppInvitationActivity.end_date >= now,
                MAppInvitationActivity.tenant_id == '10000'
            ).order_by(MAppInvitationActivity.sort.asc(), MAppInvitationActivity.create_time.desc()).all()

            # 过滤用户可访问的活动，取第一个
            accessible_activities = filter_activities_by_user_agent(user_agent_id, all_active_activities)
            activity = accessible_activities[0] if accessible_activities else None

            if not activity:
                return jsonify({
                    'code': ACTIVITY_NOT_FOUND_CODE,
                    'data': None,
                    'message': 'No active invitation activities currently'
                }), 404

            activity_id = activity.id
        else:
            # 查询指定活动信息
            activity = MAppInvitationActivity.query.filter(
                MAppInvitationActivity.id == activity_id,
                MAppInvitationActivity.del_flag == 0,
                MAppInvitationActivity.tenant_id == '10000'
            ).first()

            # 检查用户是否有权限访问该活动
            if activity and not can_user_access_activity(user_agent_id, activity):
                return jsonify({
                    'code': ACTIVITY_NOT_VALID_CODE,
                    'data': None,
                    'message': 'You do not have permission to access this activity'
                }), 403

        # 检查活动是否存在
        if not activity:
            return jsonify({
                'code': ACTIVITY_NOT_FOUND_CODE,
                'data': None,
                'message': 'Activity not found or deleted'
            }), 404

        # 检查活动是否有效
        if not is_activity_valid(activity):
            return jsonify({
                'code': ACTIVITY_NOT_VALID_CODE,
                'data': None,
                'message': 'Activity is inactive, closed or not in valid period'
            }), 400

        # 获取活动的所有规则
        rules = MAppInvitationActivityRule.query.filter_by(
            activity_id=activity_id,
            del_flag=0,
            tenant_id='10000'
        ).order_by(MAppInvitationActivityRule.sequence).all()

        if not rules:
            return jsonify({
                'code': SUCCESS_CODE,
                'data': {
                    'activity_id': activity.id,
                    'activity_title': activity.title,
                    'activity_description': activity.description,
                    'bonus_type': activity.bonus_type,  # 新增奖金类型字段
                    'reward_amount': float(activity.reward_amount) if activity.reward_amount else 0,
                    'max_reward_count': activity.max_reward_count,
                    'start_date': activity.start_date.strftime('%Y-%m-%d %H:%M:%S'),
                    'end_date': activity.end_date.strftime('%Y-%m-%d %H:%M:%S'),
                    'progress': [],
                    'total_available_reward': 0,
                    # 奖金池相关字段
                    'bonus_pool': float(activity.bonus_pool or 0),
                    'bonus_pool_remaining': float(activity.bonus_pool_remaining or 0),
                    'agent_id': activity.agent_id,
                    'is_pool_exhausted': bool(activity.is_pool_exhausted) if hasattr(activity,
                                                                                     'is_pool_exhausted') else False
                },
                'message': 'This activity has no reward rules currently'
            }), 200

        # 规则处理器映射
        rule_processors = {
            RewardRuleType.INVITE_COUNT.value: calculate_invite_count_progress,
            RewardRuleType.INVITEE_FIRST_RECHARGE.value: calculate_invitee_first_recharge_progress,
            RewardRuleType.FIRST_BET.value: calculate_first_bet_progress,
            RewardRuleType.BET_PROFIT.value: calculate_bet_profit_progress,
            RewardRuleType.BET_CASHBACK.value: calculate_bet_cashback_progress
        }

        # 计算所有规则的进度
        progress_list = []
        for rule in rules:
            processor = rule_processors.get(rule.rule_type)
            if processor:
                progress = processor(activity_id, user_id, rule)
                # 添加活动标题到进度信息中
                progress['activity_title'] = activity.title
                progress_list.append(progress)

        # 计算可领取的奖励总额
        total_available = sum(p['reward_amount'] for p in progress_list if p['can_claim'])

        return jsonify({
            'code': SUCCESS_CODE,
            'data': {
                'activity_id': activity.id,
                'activity_title': activity.title,
                'activity_description': activity.description,
                'bonus_type': activity.bonus_type,  # 新增奖金类型字段
                'reward_amount': float(activity.reward_amount) if activity.reward_amount else 0,
                'max_reward_count': activity.max_reward_count,
                'start_date': activity.start_date.strftime('%Y-%m-%d %H:%M:%S'),
                'end_date': activity.end_date.strftime('%Y-%m-%d %H:%M:%S'),
                'user_id': user_id,
                'is_valid': is_activity_valid(activity),
                'progress': progress_list,
                'total_available_reward': float(total_available),
                # 奖金池相关字段
                'bonus_pool': float(activity.bonus_pool or 0),
                'bonus_pool_remaining': float(activity.bonus_pool_remaining or 0),
                'agent_id': activity.agent_id,
                'is_pool_exhausted': bool(activity.is_pool_exhausted) if hasattr(activity,
                                                                                 'is_pool_exhausted') else False
            },
            'message': 'success'
        }), 200

    except Exception as e:
        return jsonify({
            'code': SYSTEM_ERROR_CODE,
            'data': None,
            'message': str(e)
        }), 500


@activity.route('/activities/rules/<string:activity_id>', methods=['GET'])
@auth.login_required
def get_activity_rules(activity_id):
    """获取活动的所有奖励规则"""
    try:
        # 获取当前用户的代理ID
        user_agent_id = g.user.aid

        # 查询活动
        activity = MAppInvitationActivity.query.filter(
            MAppInvitationActivity.id == activity_id,
            MAppInvitationActivity.del_flag == 0,
            MAppInvitationActivity.tenant_id == '10000'
        ).first()

        if not activity:
            return jsonify({
                'code': ACTIVITY_NOT_FOUND_CODE,
                'data': None,
                'message': 'Activity not found or deleted'
            }), 404

        # 检查用户是否有权限访问该活动
        if not can_user_access_activity(user_agent_id, activity):
            return jsonify({
                'code': ACTIVITY_NOT_VALID_CODE,
                'data': None,
                'message': 'You do not have permission to access this activity'
            }), 403

        # 检查活动是否在有效期内
        if not is_activity_valid(activity):
            return jsonify({
                'code': ACTIVITY_NOT_VALID_CODE,
                'data': None,
                'message': 'Activity is inactive, closed or not in valid period'
            }), 400

        # 查询规则
        rules = MAppInvitationActivityRule.query.filter_by(
            activity_id=activity_id,
            del_flag=0
        ).order_by(MAppInvitationActivityRule.sequence).all()

        # 格式化规则数据
        rule_list = []
        for rule in rules:
            rule_list.append({
                'id': rule.id,
                'rule_type': rule.rule_type,
                'threshold_value': float(rule.threshold_value) if rule.threshold_value else 0,
                'reward_amount': float(rule.reward_amount or 0),
                'max_claim_count': int(rule.max_claim_count or 0),
                'sequence': rule.sequence,
                'description': rule.description,
                'create_time': rule.create_time.strftime('%Y-%m-%d %H:%M:%S') if rule.create_time else None
            })

        return jsonify({
            'code': SUCCESS_CODE,
            'data': {
                'activity_id': activity.id,
                'activity_title': activity.title,
                'activity_description': activity.description,
                'bonus_type': activity.bonus_type,  # 新增奖金类型字段
                'reward_amount': float(activity.reward_amount) if activity.reward_amount else 0,
                'max_reward_count': activity.max_reward_count,
                'start_date': activity.start_date.strftime('%Y-%m-%d %H:%M:%S'),
                'end_date': activity.end_date.strftime('%Y-%m-%d %H:%M:%S'),
                'is_active': activity.is_active,
                'rules': rule_list,
                'rule_count': len(rule_list),
                # 奖金池相关字段
                'bonus_pool': float(activity.bonus_pool or 0),
                'bonus_pool_remaining': float(activity.bonus_pool_remaining or 0),
                'agent_id': activity.agent_id,
                'is_pool_exhausted': bool(activity.is_pool_exhausted) if hasattr(activity,
                                                                                 'is_pool_exhausted') else False
            },
            'message': 'success'
        }), 200

    except Exception as e:
        return jsonify({
            'code': SYSTEM_ERROR_CODE,
            'data': None,
            'message': str(e)
        }), 500


@activity.route('/invited_users', methods=['GET'])
@auth.login_required
def get_invited_users():
    """查询当前用户下被邀请的用户列表"""
    try:
        # 获取当前用户ID
        user_id = g.user.id

        # 获取分页参数
        page = int(request.args.get('page', 1))
        page_size = min(int(request.args.get('page_size', 20)), 100)  # 限制最大页面大小

        # 获取排序参数
        sort_by = request.args.get('sort_by', 'create_time')  # 默认按注册时间排序
        sort_order = request.args.get('sort_order', 'desc')  # desc/asc

        # 获取过滤参数
        has_recharged = request.args.get('has_recharged')  # true/false - 是否充值过
        min_recharge = request.args.get('min_recharge')  # 最小充值金额
        start_date = request.args.get('start_date')  # 注册开始时间
        end_date = request.args.get('end_date')  # 注册结束时间
        keyword = request.args.get('keyword', '').strip()  # 搜索关键词(用户名/手机号)

        # 构建查询
        query = AppMember.query.filter(
            AppMember.rid == user_id,
            AppMember.del_flag == 0
        )

        # 应用过滤条件
        if keyword:
            query = query.filter(
                db.or_(
                    AppMember.name.like(f'%{keyword}%'),
                    AppMember.phone.like(f'%{keyword}%')
                )
            )

        if start_date:
            try:
                start_dt = datetime.strptime(start_date, '%Y-%m-%d')
                query = query.filter(AppMember.create_time >= start_dt)
            except ValueError:
                pass

        if end_date:
            try:
                end_dt = datetime.strptime(end_date, '%Y-%m-%d')
                end_dt = end_dt.replace(hour=23, minute=59, second=59)
                query = query.filter(AppMember.create_time <= end_dt)
            except ValueError:
                pass

        # 应用排序
        if sort_by == 'create_time':
            if sort_order == 'asc':
                query = query.order_by(AppMember.create_time.asc())
            else:
                query = query.order_by(AppMember.create_time.desc())
        elif sort_by == 'name':
            if sort_order == 'asc':
                query = query.order_by(AppMember.name.asc())
            else:
                query = query.order_by(AppMember.name.desc())
        else:
            query = query.order_by(AppMember.create_time.desc())

        # 获取总数
        total_count = query.count()

        # 应用分页
        offset = (page - 1) * page_size
        invited_users = query.offset(offset).limit(page_size).all()

        # 获取用户ID列表用于批量查询统计信息
        user_ids = [user.id for user in invited_users]

        # 批量查询充值统计
        recharge_stats = {}
        if user_ids:
            recharge_query = db.session.query(
                Charge.mb_id,
                func.sum(Charge.amount).label('total_recharge'),
                func.count(Charge.id).label('recharge_count'),
                func.min(Charge.create_time).label('first_recharge_time')
            ).filter(
                Charge.mb_id.in_(user_ids),
                Charge.status == 'success',
                Charge.del_flag == 0
            ).group_by(Charge.mb_id).all()

            for stat in recharge_query:
                recharge_stats[stat.user_id] = {
                    'total_recharge': float(stat.total_recharge or 0),
                    'recharge_count': stat.recharge_count or 0,
                    'first_recharge_time': stat.first_recharge_time.strftime(
                        '%Y-%m-%d %H:%M:%S') if stat.first_recharge_time else None
                }

        # 批量查询下注统计
        bet_stats = {}
        if user_ids:
            bet_query = db.session.query(
                Order.USER_ID,
                func.sum(Order.BET_MONEY).label('total_bet'),
                func.count(Order.ID).label('bet_count')
            ).filter(
                Order.USER_ID.in_(user_ids),
                Order.STATUS == '1',
                Order.DEL_FLAG == 0
            ).group_by(Order.USER_ID).all()

            for stat in bet_query:
                bet_stats[stat.USER_ID] = {
                    'total_bet': float(stat.total_bet or 0),
                    'bet_count': stat.bet_count or 0
                }

        # 应用充值过滤（在获取统计后）
        if has_recharged is not None:
            has_recharged_bool = has_recharged.lower() == 'true'
            if has_recharged_bool:
                invited_users = [user for user in invited_users if user.id in recharge_stats]
            else:
                invited_users = [user for user in invited_users if user.id not in recharge_stats]

        if min_recharge:
            try:
                min_recharge_amount = float(min_recharge)
                invited_users = [user for user in invited_users
                                 if recharge_stats.get(user.id, {}).get('total_recharge', 0) >= min_recharge_amount]
            except ValueError:
                pass

        # 格式化返回数据
        user_list = []
        for user in invited_users:
            user_recharge_stat = recharge_stats.get(user.id, {})
            user_bet_stat = bet_stats.get(user.id, {})

            user_info = {
                'id': user.id,
                'name': user.name,
                'mobile': user.phone,
                'create_time': user.create_time.strftime('%Y-%m-%d %H:%M:%S') if user.create_time else None,
                'status': getattr(user, 'status', None),
                'recharge_stats': {
                    'total_recharge': user_recharge_stat.get('total_recharge', 0),
                    'recharge_count': user_recharge_stat.get('recharge_count', 0),
                    'first_recharge_time': user_recharge_stat.get('first_recharge_time'),
                    'has_recharged': user.id in recharge_stats
                },
                'bet_stats': {
                    'total_bet': user_bet_stat.get('total_bet', 0),
                    'bet_count': user_bet_stat.get('bet_count', 0)
                }
            }
            user_list.append(user_info)

        # 计算总统计
        total_stats = {
            'total_invited': total_count,
            'total_recharged_users': len(recharge_stats),
            'total_recharge_amount': sum(stat['total_recharge'] for stat in recharge_stats.values()),
            'total_bet_users': len(bet_stats),
            'total_bet_amount': sum(stat['total_bet'] for stat in bet_stats.values()),
            'recharge_rate': round((len(recharge_stats) / total_count * 100), 2) if total_count > 0 else 0
        }

        # 分页信息
        pagination = {
            'current_page': page,
            'page_size': page_size,
            'total_count': len(user_list),  # 过滤后的总数
            'total_pages': (len(user_list) + page_size - 1) // page_size,
            'has_next': page * page_size < len(user_list),
            'has_prev': page > 1
        }

        return jsonify({
            'code': SUCCESS_CODE,
            'data': {
                'users': user_list,
                'pagination': pagination,
                'stats': total_stats,
                'filters': {
                    'has_recharged': has_recharged,
                    'min_recharge': min_recharge,
                    'start_date': start_date,
                    'end_date': end_date,
                    'keyword': keyword,
                    'sort_by': sort_by,
                    'sort_order': sort_order
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


@activity.route('/invited_users/<string:invited_user_id>/detail', methods=['GET'])
@auth.login_required
def get_invited_user_detail(invited_user_id):
    """获取被邀请用户的详细信息"""
    try:
        # 获取当前用户ID
        user_id = g.user.id

        # 验证被邀请用户是否属于当前用户
        invited_user = AppMember.query.filter(
            AppMember.id == invited_user_id,
            AppMember.rid == user_id,
            AppMember.del_flag == 0
        ).first()

        if not invited_user:
            return jsonify({
                'code': PARAM_ERROR_CODE,
                'data': None,
                'message': 'User not found or not invited by you'
            }), 404

        # 获取充值详细信息
        recharges = Charge.query.filter(
            Charge.mb_id == invited_user_id,
            Charge.status == 'success',
            Charge.del_flag == 0
        ).order_by(Charge.create_time.desc()).limit(10).all()

        recharge_list = []
        total_recharge = 0
        for charge in recharges:
            amount = float(charge.amount or 0)
            total_recharge += amount
            recharge_list.append({
                'id': charge.id,
                'amount': amount,
                'create_time': charge.create_time.strftime('%Y-%m-%d %H:%M:%S') if charge.create_time else None,
                'payment_method': getattr(charge, 'payment_method', None)
            })

        # 获取下注详细信息
        orders = Order.query.filter(
            Order.USER_ID == invited_user_id,
            Order.STATUS == '1',
            Order.DEL_FLAG == 0
        ).order_by(Order.CREATE_TIME.desc()).limit(10).all()

        order_list = []
        total_bet = 0
        for order in orders:
            amount = float(order.BET_MONEY or 0)
            total_bet += amount
            order_list.append({
                'id': order.ID,
                'amount': amount,
                'create_time': order.CREATE_TIME.strftime('%Y-%m-%d %H:%M:%S') if order.CREATE_TIME else None,
                'game_type': getattr(order, 'ORDER_TYPE', None)
            })

        # 计算用户对邀请者的贡献（可根据业务规则调整）
        contribution_stats = {
            'total_contribution': total_recharge * 0.1 + total_bet * 0.05,  # 示例计算规则
            'recharge_contribution': total_recharge * 0.1,
            'bet_contribution': total_bet * 0.05
        }

        return jsonify({
            'code': SUCCESS_CODE,
            'data': {
                'user_info': {
                    'id': invited_user.id,
                    'name': invited_user.name,
                    'mobile': invited_user.mobile,
                    'create_time': invited_user.create_time.strftime(
                        '%Y-%m-%d %H:%M:%S') if invited_user.create_time else None,
                    'status': getattr(invited_user, 'status', None),
                    'register_days': (datetime.now() - invited_user.create_time).days if invited_user.create_time else 0
                },
                'recharge_info': {
                    'total_recharge': total_recharge,
                    'recharge_count': len(recharges),
                    'recent_recharges': recharge_list,
                    'first_recharge_time': recharge_list[-1]['create_time'] if recharge_list else None
                },
                'bet_info': {
                    'total_bet': total_bet,
                    'bet_count': len(orders),
                    'recent_orders': order_list,
                    'first_bet_time': order_list[-1]['create_time'] if order_list else None
                },
                'contribution_stats': contribution_stats
            },
            'message': 'success'
        }), 200

    except Exception as e:
        return jsonify({
            'code': SYSTEM_ERROR_CODE,
            'data': None,
            'message': str(e)
        }), 500


@activity.route('/rewards/total-summary', methods=['GET'])
@auth.login_required
def get_total_rewards_summary():
    """分别统计当前用户作为邀请者领取的奖金总和，以及其邀请的用户领取的奖金总和（优化版：基于bonus_type字段）"""
    try:
        # 获取当前用户ID
        user_id = g.user.id

        # 获取查询参数
        start_date = request.args.get('start_date')  # 开始时间 YYYY-MM-DD
        end_date = request.args.get('end_date')  # 结束时间 YYYY-MM-DD

        # 构建时间过滤条件
        time_filters = []
        if start_date:
            try:
                start_dt = datetime.strptime(start_date, '%Y-%m-%d')
                time_filters.append(MAppInvitationReward.claimed_at >= start_dt)
            except ValueError:
                return jsonify({
                    'code': PARAM_ERROR_CODE,
                    'data': None,
                    'message': 'Invalid start_date format, please use YYYY-MM-DD format'
                }), 400

        if end_date:
            try:
                end_dt = datetime.strptime(end_date, '%Y-%m-%d')
                # 包含结束日期的整天
                end_dt = end_dt.replace(hour=23, minute=59, second=59)
                time_filters.append(MAppInvitationReward.claimed_at <= end_dt)
            except ValueError:
                return jsonify({
                    'code': PARAM_ERROR_CODE,
                    'data': None,
                    'message': 'Invalid end_date format, please use YYYY-MM-DD format'
                }), 400

        # 1. 统计当前用户作为邀请者领取的奖励（总体和分类）
        # 总体统计
        referrer_total_query = db.session.query(func.sum(MAppInvitationReward.reward_amount)).filter(
            MAppInvitationReward.referrer_id == user_id,
            MAppInvitationReward.status == 'claimed',
            MAppInvitationReward.del_flag == 0,
            *time_filters
        )
        referrer_total = float(referrer_total_query.scalar() or 0)

        # 按奖金类型分组统计当前用户的奖励
        referrer_by_type_query = db.session.query(
            MAppInvitationReward.bonus_type,
            func.sum(MAppInvitationReward.reward_amount).label('total_amount'),
            func.count(MAppInvitationReward.id).label('reward_count')
        ).filter(
            MAppInvitationReward.referrer_id == user_id,
            MAppInvitationReward.status == 'claimed',
            MAppInvitationReward.del_flag == 0,
            *time_filters
        ).group_by(MAppInvitationReward.bonus_type).all()

        referrer_by_type = {}
        referrer_count = 0
        for stat in referrer_by_type_query:
            bonus_type_key = stat.bonus_type or 'Unknown'
            amount = float(stat.total_amount or 0)
            count = stat.reward_count or 0
            referrer_by_type[bonus_type_key] = {
                'total_amount': amount,
                'reward_count': count
            }
            referrer_count += count

        # 2. 统计当前用户邀请的用户领取的奖励总和
        # 首先获取当前用户邀请的所有用户ID
        invited_user_ids = db.session.query(AppMember.id).filter(
            AppMember.rid == user_id,
            AppMember.del_flag == 0
        ).all()
        invited_user_ids = [uid[0] for uid in invited_user_ids]

        invited_users_rewards_total = 0
        invited_users_reward_count = 0
        invited_users_by_type = {}

        if invited_user_ids:
            # 总体统计被邀请用户的奖励
            invited_users_query = db.session.query(func.sum(MAppInvitationReward.reward_amount)).filter(
                MAppInvitationReward.referrer_id.in_(invited_user_ids),
                MAppInvitationReward.status == 'claimed',
                MAppInvitationReward.del_flag == 0,
                *time_filters
            )
            invited_users_rewards_total = float(invited_users_query.scalar() or 0)

            # 按奖金类型分组统计被邀请用户的奖励
            invited_users_by_type_query = db.session.query(
                MAppInvitationReward.bonus_type,
                func.sum(MAppInvitationReward.reward_amount).label('total_amount'),
                func.count(MAppInvitationReward.id).label('reward_count')
            ).filter(
                MAppInvitationReward.referrer_id.in_(invited_user_ids),
                MAppInvitationReward.status == 'claimed',
                MAppInvitationReward.del_flag == 0,
                *time_filters
            ).group_by(MAppInvitationReward.bonus_type).all()

            for stat in invited_users_by_type_query:
                bonus_type_key = stat.bonus_type or 'Unknown'
                amount = float(stat.total_amount or 0)
                count = stat.reward_count or 0
                invited_users_by_type[bonus_type_key] = {
                    'total_amount': amount,
                    'reward_count': count
                }
                invited_users_reward_count += count

        # 3. 统计各被邀请用户的详细信息
        invited_users_details = []
        if invited_user_ids:
            # 批量获取每个被邀请用户的奖励统计
            user_rewards_query = db.session.query(
                MAppInvitationReward.referrer_id,
                func.sum(MAppInvitationReward.reward_amount).label('total_rewards'),
                func.count(MAppInvitationReward.id).label('reward_count')
            ).filter(
                MAppInvitationReward.referrer_id.in_(invited_user_ids),
                MAppInvitationReward.status == 'claimed',
                MAppInvitationReward.del_flag == 0,
                *time_filters
            ).group_by(MAppInvitationReward.referrer_id).all()

            # 批量获取用户信息
            users_info = {user.id: user for user in AppMember.query.filter(
                AppMember.id.in_([stat.referrer_id for stat in user_rewards_query]),
                AppMember.del_flag == 0
            ).all()}

            for stat in user_rewards_query:
                user_info = users_info.get(stat.referrer_id)
                invited_users_details.append({
                    'user_id': stat.referrer_id,
                    'user_name': user_info.name if user_info else 'Unknown',
                    'user_mobile': user_info.phone if user_info else 'Unknown',
                    'total_rewards': float(stat.total_rewards),
                    'reward_count': stat.reward_count
                })

        # 4. 统计按月份分组的奖励趋势（最近12个月）
        monthly_stats = []
        for i in range(12):
            month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            month_start = month_start.replace(
                month=month_start.month - i if month_start.month > i else month_start.month - i + 12,
                year=month_start.year if month_start.month > i else month_start.year - 1)
            if month_start.month == 12:
                month_end = month_start.replace(year=month_start.year + 1, month=1) - timedelta(days=1)
            else:
                month_end = month_start.replace(month=month_start.month + 1) - timedelta(days=1)

            # 当前用户的月度奖励
            month_referrer = db.session.query(func.sum(MAppInvitationReward.reward_amount)).filter(
                MAppInvitationReward.referrer_id == user_id,
                MAppInvitationReward.status == 'claimed',
                MAppInvitationReward.del_flag == 0,
                MAppInvitationReward.claimed_at >= month_start,
                MAppInvitationReward.claimed_at <= month_end
            ).scalar() or 0

            # 被邀请用户的月度奖励
            month_invited_users = 0
            if invited_user_ids:
                month_invited_users = db.session.query(func.sum(MAppInvitationReward.reward_amount)).filter(
                    MAppInvitationReward.referrer_id.in_(invited_user_ids),
                    MAppInvitationReward.status == 'claimed',
                    MAppInvitationReward.del_flag == 0,
                    MAppInvitationReward.claimed_at >= month_start,
                    MAppInvitationReward.claimed_at <= month_end
                ).scalar() or 0

            monthly_stats.append({
                'month': month_start.strftime('%Y-%m'),
                'referrer_rewards': float(month_referrer),
                'invited_users_rewards': float(month_invited_users),
                'total_month_rewards': float(month_referrer) + float(month_invited_users)
            })

        # 按时间倒序排列（最新的月份在前）
        monthly_stats.reverse()

        # 确保所有奖金类型都有数据（即使为0）
        all_bonus_types = ['Invitation Bonus', 'Turnover bonus', 'Net Win Bonus']
        for bt in all_bonus_types:
            if bt not in referrer_by_type:
                referrer_by_type[bt] = {'total_amount': 0.0, 'reward_count': 0}
            if bt not in invited_users_by_type:
                invited_users_by_type[bt] = {'total_amount': 0.0, 'reward_count': 0}

        return jsonify({
            'code': SUCCESS_CODE,
            'data': {
                'summary': {
                    'referrer_total_rewards': referrer_total,
                    'referrer_reward_count': referrer_count,
                    'referrer_by_bonus_type': referrer_by_type,
                    'invited_users_total_rewards': invited_users_rewards_total,
                    'invited_users_reward_count': invited_users_reward_count,
                    'invited_users_by_bonus_type': invited_users_by_type,
                    'grand_total_rewards': referrer_total + invited_users_rewards_total,
                    'total_reward_count': referrer_count + invited_users_reward_count,
                    'total_invited_users': len(invited_user_ids),
                    'invited_users_with_rewards': len(invited_users_details)
                },
                'invited_users_details': invited_users_details,
                'monthly_trends': monthly_stats,
                'filters': {
                    'start_date': start_date,
                    'end_date': end_date,
                    'date_range_applied': bool(start_date or end_date)
                },
                'query_info': {
                    'user_id': user_id,
                    'query_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'optimization': 'Direct bonus_type field query for better performance'
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


@activity.route('/rewards/bonus-type-summary', methods=['GET'])
@auth.login_required
def get_bonus_type_summary():
    """分别统计当前用户领取的Invitation、Turnover、Net Win类型奖金，支持时间段过滤"""
    try:
        # 获取当前用户ID
        user_id = g.user.id

        # 获取查询参数
        start_date = request.args.get('start_date')  # 开始时间 YYYY-MM-DD
        end_date = request.args.get('end_date')  # 结束时间 YYYY-MM-DD
        bonus_type = request.args.get('bonus_type')  # 可选：过滤特定的奖金类型

        # 构建时间过滤条件
        time_filters = []
        if start_date:
            try:
                start_dt = datetime.strptime(start_date, '%Y-%m-%d')
                time_filters.append(MAppInvitationReward.claimed_at >= start_dt)
            except ValueError:
                return jsonify({
                    'code': PARAM_ERROR_CODE,
                    'data': None,
                    'message': 'Invalid start_date format, please use YYYY-MM-DD format'
                }), 400

        if end_date:
            try:
                end_dt = datetime.strptime(end_date, '%Y-%m-%d')
                # 包含结束日期的整天
                end_dt = end_dt.replace(hour=23, minute=59, second=59)
                time_filters.append(MAppInvitationReward.claimed_at <= end_dt)
            except ValueError:
                return jsonify({
                    'code': PARAM_ERROR_CODE,
                    'data': None,
                    'message': 'Invalid end_date format, please use YYYY-MM-DD format'
                }), 400

        # 构建bonus_type过滤条件
        bonus_type_filter = []
        if bonus_type:
            valid_bonus_types = ['Invitation Bonus', 'Turnover bonus', 'Net Win Bonus']
            if bonus_type not in valid_bonus_types:
                return jsonify({
                    'code': PARAM_ERROR_CODE,
                    'data': None,
                    'message': f'Invalid bonus_type parameter, valid values: {valid_bonus_types}'
                }), 400
            bonus_type_filter.append(MAppInvitationReward.bonus_type == bonus_type)

        # 查询当前用户作为邀请者的奖励，按bonus_type分组统计（直接使用奖励表的bonus_type字段）
        bonus_stats_query = db.session.query(
            MAppInvitationReward.bonus_type,
            func.sum(MAppInvitationReward.reward_amount).label('total_amount'),
            func.count(MAppInvitationReward.id).label('reward_count')
        ).filter(
            MAppInvitationReward.referrer_id == user_id,
            MAppInvitationReward.status == 'claimed',
            MAppInvitationReward.del_flag == 0,
            *time_filters,
            *bonus_type_filter
        ).group_by(MAppInvitationReward.bonus_type).all()

        # 查询每个bonus_type的被邀请者数量（不重复计算）
        invitee_stats_query = db.session.query(
            MAppInvitationReward.bonus_type,
            func.count(func.distinct(MAppInvitationReward.referred_user_id)).label('invitee_count')
        ).filter(
            MAppInvitationReward.referrer_id == user_id,
            MAppInvitationReward.status == 'claimed',
            MAppInvitationReward.del_flag == 0,
            MAppInvitationReward.referred_user_id.isnot(None),  # 排除没有被推荐人ID的记录
            *time_filters,
            *bonus_type_filter
        ).group_by(MAppInvitationReward.bonus_type).all()

        # 整理被邀请者数量统计结果
        invitee_count_stats = {}
        for stat in invitee_stats_query:
            bonus_type_key = stat.bonus_type or 'Unknown'
            invitee_count_stats[bonus_type_key] = stat.invitee_count or 0

        # 整理按类型分组的统计结果
        bonus_type_stats = {}
        total_amount = 0
        total_count = 0

        for stat in bonus_stats_query:
            bonus_type_key = stat.bonus_type or 'Unknown'
            amount = float(stat.total_amount or 0)
            count = stat.reward_count or 0

            bonus_type_stats[bonus_type_key] = {
                'total_amount': amount,
                'reward_count': count,
                'invitee_count': invitee_count_stats.get(bonus_type_key, 0),
                'percentage': 0  # 稍后计算
            }
            total_amount += amount
            total_count += count

        # 计算各类型的百分比
        for bonus_type_key in bonus_type_stats:
            if total_amount > 0:
                bonus_type_stats[bonus_type_key]['percentage'] = round(
                    (bonus_type_stats[bonus_type_key]['total_amount'] / total_amount) * 100, 2
                )

        # 确保所有类型都有数据（即使为0）
        all_bonus_types = ['Invitation Bonus', 'Turnover bonus', 'Net Win Bonus']
        for bt in all_bonus_types:
            if bt not in bonus_type_stats:
                bonus_type_stats[bt] = {
                    'total_amount': 0.0,
                    'reward_count': 0,
                    'invitee_count': invitee_count_stats.get(bt, 0),
                    'percentage': 0.0
                }

        # 查询详细的奖励记录（最近20条）
        recent_rewards_query = db.session.query(
            MAppInvitationReward.id,
            MAppInvitationReward.reward_amount,
            MAppInvitationReward.claimed_at,
            MAppInvitationReward.bonus_type,  # 直接使用奖励记录表的bonus_type字段
            MAppInvitationActivity.title.label('activity_title')
        ).join(
            MAppInvitationActivity, MAppInvitationReward.activity_id == MAppInvitationActivity.id
        ).filter(
            MAppInvitationReward.referrer_id == user_id,
            MAppInvitationReward.status == 'claimed',
            MAppInvitationReward.del_flag == 0,
            MAppInvitationActivity.del_flag == 0,
            *time_filters,
            *bonus_type_filter
        ).order_by(MAppInvitationReward.claimed_at.desc()).limit(20).all()

        recent_rewards = []
        for reward in recent_rewards_query:
            recent_rewards.append({
                'reward_id': reward.id,
                'amount': float(reward.reward_amount),
                'claimed_at': reward.claimed_at.strftime('%Y-%m-%d %H:%M:%S') if reward.claimed_at else None,
                'bonus_type': reward.bonus_type or 'Unknown',
                'activity_title': reward.activity_title
            })

        # 按月份统计各类型奖励趋势（最近6个月）
        monthly_bonus_trends = []
        for i in range(6):
            month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            month_start = month_start.replace(
                month=month_start.month - i if month_start.month > i else month_start.month - i + 12,
                year=month_start.year if month_start.month > i else month_start.year - 1)
            if month_start.month == 12:
                month_end = month_start.replace(year=month_start.year + 1, month=1) - timedelta(days=1)
            else:
                month_end = month_start.replace(month=month_start.month + 1) - timedelta(days=1)

            month_bonus_stats = db.session.query(
                MAppInvitationReward.bonus_type,  # 直接使用奖励记录表的bonus_type字段
                func.sum(MAppInvitationReward.reward_amount).label('total_amount')
            ).filter(
                MAppInvitationReward.referrer_id == user_id,
                MAppInvitationReward.status == 'claimed',
                MAppInvitationReward.del_flag == 0,
                MAppInvitationReward.claimed_at >= month_start,
                MAppInvitationReward.claimed_at <= month_end
            ).group_by(MAppInvitationReward.bonus_type).all()

            month_data = {
                'month': month_start.strftime('%Y-%m'),
                'Invitation Bonus': 0.0,
                'Turnover bonus': 0.0,
                'Net Win Bonus': 0.0,
                'total': 0.0
            }

            for stat in month_bonus_stats:
                bonus_type_key = stat.bonus_type or 'Unknown'
                amount = float(stat.total_amount or 0)
                if bonus_type_key in month_data:
                    month_data[bonus_type_key] = amount
                    month_data['total'] += amount

            monthly_bonus_trends.append(month_data)

        # 按时间倒序排列（最新的月份在前）
        monthly_bonus_trends.reverse()

        return jsonify({
            'code': SUCCESS_CODE,
            'data': {
                'summary': {
                    'total_amount': total_amount,
                    'total_count': total_count,
                    'bonus_type_breakdown': bonus_type_stats
                },
                'recent_rewards': recent_rewards,
                'monthly_trends': monthly_bonus_trends,
                'filters': {
                    'start_date': start_date,
                    'end_date': end_date,
                    'bonus_type': bonus_type,
                    'date_range_applied': bool(start_date or end_date),
                    'bonus_type_filtered': bool(bonus_type)
                },
                'query_info': {
                    'user_id': user_id,
                    'query_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'available_bonus_types': all_bonus_types
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


@activity.route('/invitee-stats', methods=['GET'])
@auth.login_required
def get_invitee_statistics():
    """当前用户的被邀请人统计：Active Invitees（有充值记录）、Pending Invitees（无充值记录）、Total Invited（总数）"""
    try:
        # 获取当前用户ID
        user_id = g.user.id

        # 查询当前用户邀请的所有用户（排除用户自己）
        invited_users = AppMember.query.filter(
            AppMember.rid == user_id,
            AppMember.id != user_id,  # 明确排除用户自己
            AppMember.del_flag == 0
        ).all()

        if not invited_users:
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

        invited_user_ids = [user.id for user in invited_users]

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
        total_invited_count = len(invited_users)

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


@activity.route('/invitees-rewards', methods=['GET'])
@auth.login_required
def get_invitees_rewards_summary():
    """当前用户下被邀请人的数据统计，包括总充值、总营业额、总净赢，支持时间段、被邀请者状态过滤和用户名过滤"""
    try:
        # 获取当前用户ID
        user_id = g.user.id

        # 获取查询参数
        start_date = request.args.get('start_date')  # YYYY-MM-DD
        end_date = request.args.get('end_date')  # YYYY-MM-DD
        invitee_user_status = request.args.get('status')  # signed up, active, inactive, pending (前端传小写)
        keyword = request.args.get('keyword')  # 被邀请用户的用户名过滤

        # 转换前端传来的小写状态值为首字母大写格式
        status_mapping = {
            'signed up': 'Signed Up',
            'signed_up': 'Signed Up',  # 处理空格被转换为下划线的情况
            'active': 'Active',
            'inactive': 'Inactive',
            'pending': 'Pending'
        }

        # 如果提供了状态参数，进行转换和验证
        if invitee_user_status:
            invitee_user_status_lower = invitee_user_status.lower()
            if invitee_user_status_lower in status_mapping:
                invitee_user_status = status_mapping[invitee_user_status_lower]
            else:
                return jsonify({
                    'code': PARAM_ERROR_CODE,
                    'data': None,
                    'message': f'Invalid status parameter, valid values: {list(status_mapping.keys())}'
                }), 400

        # 构建时间过滤条件（基于用户注册时间）
        time_filters_for_registration = []
        if start_date:
            try:
                start_dt = datetime.strptime(start_date, '%Y-%m-%d')
                time_filters_for_registration.append(AppMember.create_time >= start_dt)
            except ValueError:
                return jsonify({
                    'code': PARAM_ERROR_CODE,
                    'data': None,
                    'message': 'Invalid start_date format, please use YYYY-MM-DD format'
                }), 400

        if end_date:
            try:
                end_dt = datetime.strptime(end_date, '%Y-%m-%d')
                end_dt = end_dt.replace(hour=23, minute=59, second=59)
                time_filters_for_registration.append(AppMember.create_time <= end_dt)
            except ValueError:
                return jsonify({
                    'code': PARAM_ERROR_CODE,
                    'data': None,
                    'message': 'Invalid end_date format, please use YYYY-MM-DD format'
                }), 400

        # 获取当前用户邀请的所有用户详细信息（基于注册时间过滤）
        query = AppMember.query.filter(
            AppMember.rid == user_id,
            AppMember.del_flag == 0
        )

        # 添加注册时间过滤
        if time_filters_for_registration:
            query = query.filter(*time_filters_for_registration)

        # 添加用户名过滤
        if keyword:
            query = query.filter(
                db.or_(
                    AppMember.username.like(f'%{keyword}%'),
                    AppMember.name.like(f'%{keyword}%')
                )
            )

        invited_users = query.all()

        if not invited_users:
            return jsonify({
                'code': SUCCESS_CODE,
                'data': {
                    'total_deposit': 0,
                    'total_turnover': 0,
                    'total_net_win': 0,
                    'total_invited_users': 0,
                    'filtered_invited_users': 0,
                    'invitee_details': []
                },
                'message': 'success'
            }), 200

        invited_user_ids = [user.id for user in invited_users]

        # 批量获取用户充值统计（不基于时间过滤，统计所有历史数据）
        user_recharge_stats = {}
        if invited_user_ids:
            recharge_query = db.session.query(
                Charge.mb_id,
                func.count(Charge.id).label('recharge_count'),
                func.sum(Charge.amount).label('total_recharge'),
                func.min(Charge.create_time).label('first_recharge_time'),
                func.max(Charge.create_time).label('last_recharge_time')
            ).filter(
                Charge.mb_id.in_(invited_user_ids),
                Charge.status == 'Success',
                Charge.del_flag == 0
            ).group_by(Charge.mb_id).all()

            for recharge in recharge_query:
                user_recharge_stats[recharge.mb_id] = {
                    'recharge_count': recharge.recharge_count or 0,
                    'total_recharge': float(recharge.total_recharge or 0),
                    'first_recharge_time': recharge.first_recharge_time,
                    'last_recharge_time': recharge.last_recharge_time
                }

        # 批量获取用户下注统计和净赢计算（不基于时间过滤，统计所有历史数据）
        user_order_stats = {}
        if invited_user_ids:
            order_query = db.session.query(
                Order.USER_ID,
                func.count(Order.ID).label('order_count'),
                func.sum(Order.BET_MONEY).label('total_bet'),
                func.sum(Order.BONUS).label('total_bonus'),
                func.min(Order.CREATE_TIME).label('first_bet_time'),
                func.max(Order.CREATE_TIME).label('last_bet_time')
            ).filter(
                Order.USER_ID.in_(invited_user_ids),
                Order.STATUS == '1',
                Order.DEL_FLAG == 0
            ).group_by(Order.USER_ID).all()

            for order in order_query:
                total_bet = float(order.total_bet or 0)
                total_bonus = float(order.total_bonus or 0)
                net_win = total_bonus - total_bet  # 净赢 = 奖金 - 下注金额

                user_order_stats[order.USER_ID] = {
                    'order_count': order.order_count or 0,
                    'total_bet': total_bet,
                    'total_bonus': total_bonus,
                    'net_win': net_win,
                    'first_bet_time': order.first_bet_time,
                    'last_bet_time': order.last_bet_time
                }

        # 批量获取用户活动完成情况和奖励统计（不基于时间过滤，统计所有历史数据）
        user_reward_stats = {}
        if invited_user_ids:
            reward_query = db.session.query(
                MAppInvitationReward.referrer_id,
                func.count(MAppInvitationReward.id).label('reward_count'),
                func.sum(MAppInvitationReward.reward_amount).label('total_rewards'),
                func.max(MAppInvitationReward.claimed_at).label('last_reward_time')
            ).filter(
                MAppInvitationReward.referrer_id.in_(invited_user_ids),
                MAppInvitationReward.status == 'claimed',
                MAppInvitationReward.del_flag == 0
            ).group_by(MAppInvitationReward.referrer_id).all()

            for reward in reward_query:
                user_reward_stats[reward.referrer_id] = {
                    'reward_count': reward.reward_count or 0,
                    'total_rewards': float(reward.total_rewards or 0),
                    'last_reward_time': reward.last_reward_time
                }

        # 分类用户状态并生成详细信息
        invitee_details = []
        current_time = datetime.now()

        for user in invited_users:
            user_id = user.id
            recharge_info = user_recharge_stats.get(user_id, {
                'recharge_count': 0, 'total_recharge': 0,
                'first_recharge_time': None, 'last_recharge_time': None
            })
            order_info = user_order_stats.get(user_id, {
                'order_count': 0, 'total_bet': 0, 'total_bonus': 0, 'net_win': 0,
                'first_bet_time': None, 'last_bet_time': None
            })
            reward_info = user_reward_stats.get(user_id, {
                'reward_count': 0, 'total_rewards': 0, 'last_reward_time': None
            })

            # 确定用户状态和标识
            has_deposit = recharge_info['recharge_count'] > 0
            has_bet = order_info['order_count'] > 0

            # 计算最后活动时间（充值、下注、奖励中的最新时间）
            last_activity_times = [t for t in [
                recharge_info.get('last_recharge_time'),
                order_info.get('last_bet_time'),
                reward_info.get('last_reward_time')
            ] if t]
            last_activity_time = max(last_activity_times) if last_activity_times else user.create_time

            # 计算沉寂天数
            days_since_last_activity = (current_time - last_activity_time).days if last_activity_time else 0

            # 状态分类逻辑
            if not has_deposit and not has_bet:
                user_status = 'Pending'  # 自注册以来，用户未进行任何存款或下注操作
                user_label = 'Idle User'
            elif has_deposit and not has_bet:
                user_status = 'Signed Up'  # 用户已注册并存款，但尚未下注
                user_label = 'No Bet Yet'
            elif has_deposit and has_bet and days_since_last_activity <= 30:
                user_status = 'Active'  # 用户已注册并存款且下注，且最近活跃
                user_label = 'Top User'
            elif (has_deposit or has_bet) and days_since_last_activity > 30:
                user_status = 'Inactive'  # 曾经活跃但已沉寂超过30天
                user_label = 'Idle User'
            else:
                user_status = 'Active'  # 默认活跃状态
                user_label = 'Top User'

            # 应用被邀请者状态过滤
            if invitee_user_status and user_status != invitee_user_status:
                continue

            # 查询该用户参与的所有活动和规则完成情况
            user_activity_progress = get_user_activity_progress(user_id, recharge_info, order_info)

            # 生成基于真实活动的完成描述
            activity_descriptions = []
            if user_activity_progress['completed_activities']:
                for activity in user_activity_progress['completed_activities']:
                    activity_descriptions.append(f"{activity['title']}: {activity['completed_rules_desc']}")

            if not activity_descriptions:
                if has_deposit:
                    activity_descriptions.append(f"充值{recharge_info['total_recharge']:.2f}")
                if has_bet:
                    activity_descriptions.append(f"累计下注{order_info['total_bet']:.2f}")
                if reward_info['reward_count'] > 0:
                    activity_descriptions.append(f"获得奖励{reward_info['reward_count']}次")

            activity_description = '; '.join(activity_descriptions) if activity_descriptions else '暂无活动记录'

            # 最后完成的活动（基于真实活动数据）
            last_completed_activity_data = user_activity_progress.get('last_completed_activity')
            last_activity_time_str = user_activity_progress.get('last_activity_time')

            # 格式化最后完成的活动显示
            last_completed_activity_display = None
            if last_completed_activity_data:
                if isinstance(last_completed_activity_data, dict):
                    last_completed_activity_display = last_completed_activity_data.get('completion_description',
                                                                                       f"{last_completed_activity_data['activity_title']}: {last_completed_activity_data['rule_description']} ({last_completed_activity_data.get('completion_status', '')})")
                else:
                    last_completed_activity_display = str(last_completed_activity_data)

            # 下一个建议活动（基于真实活动数据）
            next_suggested_activity = user_activity_progress.get('next_suggested_activity',
                                                                 '充值激活账户' if not has_deposit else (
                                                                     '开始下注体验' if not has_bet else '继续参与活动'))

            invitee_details.append({
                'user_id': user.id,
                'username': user.username,
                'user_name': user.name,
                'user_mobile': user.phone,
                'register_time': user.create_time.strftime('%Y-%m-%d %H:%M:%S') if user.create_time else None,
                'user_status': user_status,
                'user_label': user_label,
                'activity_description': activity_description,
                'last_completed_activity': last_completed_activity_data,  # 详细的活动完成信息
                'last_completed_activity_display': last_completed_activity_display,  # 格式化显示文本
                'last_activity_time': last_activity_time_str,
                'next_suggested_activity': next_suggested_activity,
                'next_activity_progress': user_activity_progress.get('next_activity_progress', {}),
                'days_since_last_activity': days_since_last_activity,
                'total_rewards': reward_info['total_rewards'],
                'reward_count': reward_info['reward_count'],
                'completed_activities': user_activity_progress.get('completed_activities', []),
                'pending_activities': user_activity_progress.get('pending_activities', []),
                'stats': {
                    'recharge_count': recharge_info['recharge_count'],
                    'total_recharge': recharge_info['total_recharge'],
                    'order_count': order_info['order_count'],
                    'total_bet': order_info['total_bet'],
                    'total_bonus': order_info['total_bonus'],
                    'net_win': order_info['net_win']
                }
            })

        # 计算过滤后用户的总统计数据
        total_deposit = 0  # 总充值
        total_turnover = 0  # 总营业额（下注金额）
        total_net_win = 0  # 总净赢

        for detail in invitee_details:
            total_deposit += detail['stats']['total_recharge']
            total_turnover += detail['stats']['total_bet']
            total_net_win += detail['stats']['net_win']

        # 统计各状态用户数量
        status_counts = {}
        for detail in invitee_details:
            status = detail['user_status']
            status_counts[status] = status_counts.get(status, 0) + 1

        return jsonify({
            'code': SUCCESS_CODE,
            'data': {
                'total_deposit': total_deposit,
                'total_turnover': total_turnover,
                'total_net_win': total_net_win,
                'total_summary': total_deposit + total_turnover + total_net_win,
                'total_invited_users': len(invited_user_ids),
                'filtered_invited_users': len(invitee_details),
                'invitee_details': invitee_details,
                # 'status_summary': {
                #     'signed_up_count': status_counts.get('Signed Up', 0),
                #     'active_count': status_counts.get('Active', 0),
                #     'inactive_count': status_counts.get('Inactive', 0),
                #     'pending_count': status_counts.get('Pending', 0),
                #     'total_filtered': len(invitee_details)
                # },
            },
            'message': 'success'
        }), 200

    except Exception as e:
        return jsonify({
            'code': SYSTEM_ERROR_CODE,
            'data': None,
            'message': str(e)
        }), 500


@activity.route('/downline-count', methods=['GET'])
@auth.login_required
def get_downline_count():
    """获取当前用户的下级用户数量"""
    try:
        # 获取当前用户ID
        user_id = g.user.id

        # 查询下级用户数量（rid字段为当前用户ID的用户数量）
        downline_count = AppMember.query.filter(
            AppMember.rid == user_id,
            AppMember.del_flag == 0
        ).count()

        # 检查是否达到最大邀请数限制
        max_invites = 10
        can_invite = downline_count < max_invites

        return jsonify({
            'code': SUCCESS_CODE,
            'data': {
                'downline_count': downline_count,
                'max_invites': max_invites,
                'can_invite': can_invite,
                'remaining_invites': max(0, max_invites - downline_count)
            },
            'message': 'success'
        }), 200

    except Exception as e:
        return jsonify({
            'code': SYSTEM_ERROR_CODE,
            'data': None,
            'message': str(e)
        }), 500


@activity.route('/rewards/records', methods=['GET'])
@auth.login_required
def get_user_reward_records():
    """获取当前用户的领取记录，可以根据活动ID过滤"""
    try:
        # 获取当前用户ID
        user_id = g.user.id

        # 获取查询参数
        activity_id = request.args.get('activity_id')  # 可选：过滤特定活动
        page = int(request.args.get('page', 1))
        page_size = min(int(request.args.get('page_size', 20)), 100)  # 限制最大页面大小
        status = request.args.get('status', 'claimed')  # 默认只查询已领取的
        start_date = request.args.get('start_date')  # 开始时间 YYYY-MM-DD
        end_date = request.args.get('end_date')  # 结束时间 YYYY-MM-DD
        bonus_type = request.args.get('bonus_type')  # 奖金类型过滤

        # 构建基础查询条件
        base_filters = [
            MAppInvitationReward.referrer_id == user_id,
            MAppInvitationReward.tenant_id == '10000',
            MAppInvitationReward.del_flag == 0
        ]

        # 添加状态过滤
        if status:
            base_filters.append(MAppInvitationReward.status == status)

        # 添加活动ID过滤
        if activity_id:
            base_filters.append(MAppInvitationReward.activity_id == activity_id)

        # 添加时间过滤
        if start_date:
            try:
                start_dt = datetime.strptime(start_date, '%Y-%m-%d')
                base_filters.append(MAppInvitationReward.claimed_at >= start_dt)
            except ValueError:
                return jsonify({
                    'code': PARAM_ERROR_CODE,
                    'data': None,
                    'message': 'Invalid start_date format, please use YYYY-MM-DD format'
                }), 400

        if end_date:
            try:
                end_dt = datetime.strptime(end_date, '%Y-%m-%d')
                end_dt = end_dt.replace(hour=23, minute=59, second=59)
                base_filters.append(MAppInvitationReward.claimed_at <= end_dt)
            except ValueError:
                return jsonify({
                    'code': PARAM_ERROR_CODE,
                    'data': None,
                    'message': 'Invalid end_date format, please use YYYY-MM-DD format'
                }), 400

        # 添加奖金类型过滤
        if bonus_type:
            valid_bonus_types = ['Invitation Bonus', 'Turnover bonus', 'Net Win Bonus']
            if bonus_type not in valid_bonus_types:
                return jsonify({
                    'code': PARAM_ERROR_CODE,
                    'data': None,
                    'message': f'Invalid bonus_type parameter, valid values: {valid_bonus_types}'
                }), 400
            base_filters.append(MAppInvitationReward.bonus_type == bonus_type)

        # 构建主查询，联接活动和规则表获取详细信息
        query = db.session.query(
            MAppInvitationReward.id,
            MAppInvitationReward.activity_id,
            MAppInvitationReward.rule_id,
            MAppInvitationReward.referred_user_id,
            MAppInvitationReward.reward_amount,
            MAppInvitationReward.bonus_type,
            MAppInvitationReward.status,
            MAppInvitationReward.claimed_at,
            MAppInvitationReward.create_time,
            MAppInvitationActivity.title.label('activity_title'),
            MAppInvitationActivity.description.label('activity_description'),
            MAppInvitationActivityRule.rule_type,
            MAppInvitationActivityRule.description.label('rule_description'),
            MAppInvitationActivityRule.threshold_value
        ).join(
            MAppInvitationActivity,
            MAppInvitationReward.activity_id == MAppInvitationActivity.id
        ).outerjoin(
            MAppInvitationActivityRule,
            MAppInvitationReward.rule_id == MAppInvitationActivityRule.id
        ).filter(
            *base_filters,
            MAppInvitationActivity.del_flag == 0
        )

        # 获取总数
        total_count = query.count()

        # 应用分页和排序
        offset = (page - 1) * page_size
        rewards = query.order_by(
            MAppInvitationReward.claimed_at.desc(),
            MAppInvitationReward.create_time.desc()
        ).offset(offset).limit(page_size).all()

        # 格式化返回数据
        reward_list = []
        for reward in rewards:
            # 获取被邀请用户信息
            referred_user_info = None
            if reward.referred_user_id:
                referred_user = AppMember.query.filter_by(
                    id=reward.referred_user_id,
                    del_flag=0
                ).first()
                if referred_user:
                    referred_user_info = {
                        'user_id': referred_user.id,
                        'user_name': referred_user.name,
                        'user_phone': referred_user.phone
                    }

            reward_info = {
                'reward_id': reward.id,
                'activity_id': reward.activity_id,
                'activity_title': reward.activity_title,
                'activity_description': reward.activity_description,
                'rule_id': reward.rule_id,
                'rule_type': reward.rule_type,
                'rule_description': reward.rule_description,
                'threshold_value': float(reward.threshold_value) if reward.threshold_value else 0,
                'reward_amount': float(reward.reward_amount),
                'bonus_type': reward.bonus_type,
                'status': reward.status,
                'claimed_at': reward.claimed_at.strftime('%Y-%m-%d %H:%M:%S') if reward.claimed_at else None,
                'create_time': reward.create_time.strftime('%Y-%m-%d %H:%M:%S') if reward.create_time else None,
                'referred_user': referred_user_info  # 新增：触发此奖励的被邀请用户信息
            }
            reward_list.append(reward_info)

        # 统计信息
        stats_query = db.session.query(
            func.sum(MAppInvitationReward.reward_amount).label('total_amount'),
            func.count(MAppInvitationReward.id).label('total_count')
        ).filter(*base_filters)

        stats_result = stats_query.first()
        total_reward_amount = float(stats_result.total_amount or 0)

        # 按奖金类型分组统计
        type_stats_query = db.session.query(
            MAppInvitationReward.bonus_type,
            func.sum(MAppInvitationReward.reward_amount).label('total_amount'),
            func.count(MAppInvitationReward.id).label('count')
        ).filter(*base_filters).group_by(MAppInvitationReward.bonus_type).all()

        bonus_type_stats = {}
        for stat in type_stats_query:
            bonus_type_key = stat.bonus_type or 'Unknown'
            bonus_type_stats[bonus_type_key] = {
                'total_amount': float(stat.total_amount or 0),
                'count': stat.count or 0
            }

        # 分页信息
        pagination = {
            'current_page': page,
            'page_size': page_size,
            'total_count': total_count,
            'total_pages': (total_count + page_size - 1) // page_size,
            'has_next': page * page_size < total_count,
            'has_prev': page > 1
        }

        return jsonify({
            'code': SUCCESS_CODE,
            'data': {
                'records': reward_list,
                'pagination': pagination,
                'summary': {
                    'total_reward_amount': total_reward_amount,
                    'total_record_count': total_count,
                    'bonus_type_breakdown': bonus_type_stats
                },
                'filters': {
                    'activity_id': activity_id,
                    'status': status,
                    'start_date': start_date,
                    'end_date': end_date,
                    'bonus_type': bonus_type
                },
                'query_info': {
                    'user_id': user_id,
                    'query_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
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