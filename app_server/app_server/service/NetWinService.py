from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy import func, and_
from app_server import db
from app_server.model.AppBetOrderModel import AppBetOrder
import logging

logger = logging.getLogger(__name__)


class NetWinService:
    """净赢计算服务 - 与Java端自动结算逻辑保持一致"""

    @staticmethod
    def calculate_user_net_win(user_id, coupon_id=None, start_date=None, end_date=None):
        """
        计算用户在指定时间段和优惠券活动内的净赢金额
        ✅ 与Java端保持一致：只统计促销钱包、有效结算状态的订单

        净赢 = SUM(netwin_actual)  （直接使用订单的净赢字段）

        Args:
            user_id: 用户ID
            coupon_id: 优惠券ID（如果指定，只统计该优惠券活动的订单）
            start_date: 开始时间
            end_date: 结束时间

        Returns:
            Decimal: 净赢金额（正数为赢，负数为输）
        """
        try:
            # ✅ 构建查询条件（与Java端保持一致）
            query_conditions = [
                AppBetOrder.mb_id == user_id,
                AppBetOrder.pay_wallet == 'Promotion',  # ⭐ 只统计促销钱包
                AppBetOrder.bet_status.in_(['Win', 'Lose', 'HalfWin', 'HalfLose']),  # ⭐ 只统计有效结算状态，排除Refund
                AppBetOrder.game_status == 'Finished',  # ⭐ 确保游戏已结算
                AppBetOrder.del_flag == 0
            ]

            # ⭐ 如果指定了优惠券ID，只统计该优惠券活动的订单
            if coupon_id:
                query_conditions.append(AppBetOrder.pro_id == coupon_id)

            if start_date:
                query_conditions.append(AppBetOrder.create_time >= start_date)
            if end_date:
                query_conditions.append(AppBetOrder.create_time <= end_date)

            # ✅ 查询总净赢（直接使用订单的 netwin_actual 字段）
            result = db.session.query(
                func.sum(AppBetOrder.netwin_actual).label('total_netwin')
            ).filter(*query_conditions).first()

            if not result or result.total_netwin is None:
                logger.info(f"用户 {user_id} 优惠券 {coupon_id} 在指定时间段内无有效投注记录")
                return Decimal('0')

            total_netwin = Decimal(str(result.total_netwin or 0))

            logger.info(f"用户 {user_id} 优惠券 {coupon_id} 净赢计算: 总净赢={total_netwin} (Win/Lose/HalfWin/HalfLose only, excluding Refund)")

            return total_netwin

        except Exception as e:
            logger.error(f"计算用户净赢失败: user_id={user_id}, coupon_id={coupon_id}, error={str(e)}")
            return Decimal('0')
    
    @staticmethod
    def check_net_win_eligibility(user_id, net_win_enabled, condition_type,
                                  required_amount, coupon_id=None, start_date=None, end_date=None):
        """
        检查用户是否满足净赢条件
        ✅ 与Java端保持一致的验证逻辑

        Args:
            user_id: 用户ID
            net_win_enabled: 是否启用净赢条件（0/1）
            condition_type: 条件类型（GREATER_EQUAL/LESS_EQUAL）
            required_amount: 要求的金额
            coupon_id: 优惠券ID（只统计该优惠券活动的订单）
            start_date: 计算开始时间
            end_date: 计算结束时间

        Returns:
            dict: {eligible: bool, message: str, current_value: Decimal, required_value: Decimal}
        """
        try:
            # 如果未启用净赢条件，直接通过
            if not net_win_enabled or net_win_enabled != 1:
                return {
                    'eligible': True,
                    'message': 'No net win condition required',
                    'current_value': Decimal('0'),
                    'required_value': Decimal('0')
                }

            # ✅ 计算用户净赢（只统计指定优惠券活动的订单）
            net_win = NetWinService.calculate_user_net_win(user_id, coupon_id, start_date, end_date)
            required = Decimal(str(required_amount or 0))

            eligible = False
            message = ''

            # ✅ 与Java端保持一致的条件类型
            if condition_type == 'GREATER_EQUAL':
                # 净赢 >= 目标金额
                eligible = net_win >= required
                if not eligible:
                    message = f"Net win condition not met: current={net_win}, required>={required}"
                else:
                    message = f"Net win condition met: {net_win} >= {required}"

            elif condition_type == 'LESS_EQUAL':
                # 净赢 <= 目标金额（控制最大净赢）
                eligible = net_win <= required
                if not eligible:
                    message = f"Net win exceeds limit: current={net_win}, required<={required}"
                else:
                    message = f"Net win condition met: {net_win} <= {required}"
            else:
                # 未知条件类型
                logger.warning(f"Unknown net win condition type: {condition_type}")
                message = f"Unknown condition type: {condition_type}"

            return {
                'eligible': eligible,
                'message': message,
                'current_value': net_win,
                'required_value': required,
                'condition_type': condition_type
            }

        except Exception as e:
            logger.error(f"检查净赢条件失败: user_id={user_id}, coupon_id={coupon_id}, error={str(e)}")
            return {
                'eligible': False,
                'message': f'Failed to check net win condition: {str(e)}',
                'current_value': Decimal('0'),
                'required_value': Decimal(str(required_amount or 0))
            }
    
    @staticmethod
    def get_user_betting_summary(user_id, coupon_id=None, start_date=None, end_date=None):
        """
        获取用户投注汇总信息
        ✅ 与Java端保持一致的过滤条件

        Args:
            user_id: 用户ID
            coupon_id: 优惠券ID（如果指定，只统计该优惠券活动的订单）
            start_date: 开始时间
            end_date: 结束时间

        Returns:
            dict: 包含投注统计信息
        """
        try:
            # ✅ 构建查询条件（与Java端保持一致）
            query_conditions = [
                AppBetOrder.mb_id == user_id,
                AppBetOrder.pay_wallet == 'Promotion',  # 只统计促销钱包
                AppBetOrder.bet_status.in_(['Win', 'Lose', 'HalfWin', 'HalfLose']),  # 只统计有效结算状态
                AppBetOrder.game_status == 'Finished',  # 确保游戏已结算
                AppBetOrder.del_flag == 0
            ]

            if coupon_id:
                query_conditions.append(AppBetOrder.pro_id == coupon_id)

            if start_date:
                query_conditions.append(AppBetOrder.create_time >= start_date)
            if end_date:
                query_conditions.append(AppBetOrder.create_time <= end_date)

            # 查询汇总信息
            result = db.session.query(
                func.count(AppBetOrder.id).label('total_orders'),
                func.sum(AppBetOrder.stake_actual).label('total_bet'),
                func.sum(AppBetOrder.netwin_actual).label('total_netwin'),
                func.min(AppBetOrder.create_time).label('first_bet_time'),
                func.max(AppBetOrder.create_time).label('last_bet_time')
            ).filter(*query_conditions).first()

            if not result or not result.total_orders:
                return {
                    'total_orders': 0,
                    'total_bet': Decimal('0'),
                    'total_netwin': Decimal('0'),
                    'win_rate': Decimal('0'),
                    'first_bet_time': None,
                    'last_bet_time': None
                }

            total_bet = Decimal(str(result.total_bet or 0))
            total_netwin = Decimal(str(result.total_netwin or 0))

            # 计算盈利订单数（净赢 > 0）
            profitable_orders = db.session.query(func.count(AppBetOrder.id)).filter(
                *query_conditions,
                AppBetOrder.netwin_actual > 0
            ).scalar() or 0

            win_rate = Decimal('0')
            if result.total_orders > 0:
                win_rate = (Decimal(str(profitable_orders)) / Decimal(str(result.total_orders))) * 100

            return {
                'total_orders': result.total_orders,
                'total_bet': total_bet,
                'total_netwin': total_netwin,
                'profitable_orders': profitable_orders,
                'win_rate': round(win_rate, 2),
                'first_bet_time': result.first_bet_time,
                'last_bet_time': result.last_bet_time
            }

        except Exception as e:
            logger.error(f"获取用户投注汇总失败: user_id={user_id}, coupon_id={coupon_id}, error={str(e)}")
            return {
                'total_orders': 0,
                'total_bet': Decimal('0'),
                'total_netwin': Decimal('0'),
                'win_rate': Decimal('0'),
                'first_bet_time': None,
                'last_bet_time': None
            }
    
    @staticmethod
    def get_net_win_condition_description(condition_type, amount):
        """
        获取净赢条件的描述文本
        ✅ 与Java端保持一致的条件类型

        Args:
            condition_type: 条件类型（GREATER_EQUAL/LESS_EQUAL）
            amount: 金额

        Returns:
            str: 条件描述
        """
        if not condition_type or not amount:
            return "No condition"

        amount_str = f"{amount:,.2f}" if isinstance(amount, (int, float, Decimal)) else str(amount)

        if condition_type == 'GREATER_EQUAL':
            return f"Net win ≥ {amount_str}"
        elif condition_type == 'LESS_EQUAL':
            return f"Net win ≤ {amount_str}"
        else:
            return f"{condition_type}: {amount_str}"


# 创建全局实例
net_win_service = NetWinService()