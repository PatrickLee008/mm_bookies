from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy import func, and_
from app_server import db
from app_server.model.OrderModel import Order
import logging

logger = logging.getLogger(__name__)


class NetWinService:
    """净赢计算服务"""
    
    @staticmethod
    def calculate_user_net_win(user_id, start_date=None, end_date=None):
        """
        计算用户在指定时间段的净赢金额
        净赢 = 总奖金(包含本金) - 总投注
        
        Args:
            user_id: 用户ID
            start_date: 开始时间
            end_date: 结束时间
            
        Returns:
            Decimal: 净赢金额（正数为赢，负数为输）
        """
        try:
            # 构建查询条件
            query_conditions = [
                Order.USER_ID == user_id,
                Order.STATUS == '1',  # 已结算
                Order.DEL_FLAG == 0,
                Order.TENANT_ID == '10000'
            ]
            
            if start_date:
                query_conditions.append(Order.CREATE_TIME >= start_date)
            if end_date:
                query_conditions.append(Order.CREATE_TIME <= end_date)
            
            # 查询总投注和总奖金
            result = db.session.query(
                func.sum(Order.BET_MONEY).label('total_bet'),
                func.sum(Order.BONUS).label('total_bonus')
            ).filter(*query_conditions).first()
            
            if not result or not result.total_bet:
                logger.info(f"用户 {user_id} 在指定时间段内无投注记录")
                return Decimal('0')
            
            total_bet = Decimal(str(result.total_bet or 0))
            total_bonus = Decimal(str(result.total_bonus or 0))
            
            # 净赢 = 总奖金（包含本金） - 总投注
            net_win = total_bonus - total_bet
            
            logger.info(f"用户 {user_id} 净赢计算: 总投注={total_bet}, 总奖金={total_bonus}, 净赢={net_win}")
            
            return net_win
            
        except Exception as e:
            logger.error(f"计算用户净赢失败: user_id={user_id}, error={str(e)}")
            return Decimal('0')
    
    @staticmethod
    def check_net_win_eligibility(user_id, net_win_enabled, condition_type, 
                                  required_amount, start_date=None, end_date=None):
        """
        检查用户是否满足净赢条件
        
        Args:
            user_id: 用户ID
            net_win_enabled: 是否启用净赢条件（0/1）
            condition_type: 条件类型（WIN/LOSS）
            required_amount: 要求的金额
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
            
            # 计算用户净赢
            net_win = NetWinService.calculate_user_net_win(user_id, start_date, end_date)
            required = Decimal(str(required_amount or 0))
            
            eligible = False
            message = ''
            
            if condition_type == 'WIN':
                # 净赢条件：要求净赢为正且达到指定金额
                eligible = net_win >= required
                if not eligible:
                    if net_win < 0:
                        message = f"User is in loss (net win: {net_win}), requires win of {required}"
                    else:
                        message = f"Insufficient net win: {net_win}, requires {required}"
                else:
                    message = f"Net win condition met: {net_win} >= {required}"
                    
            elif condition_type == 'LOSS':
                # 净输条件：要求净赢为负且绝对值达到指定金额
                if net_win >= 0:
                    eligible = False
                    message = f"User is not in loss (net win: {net_win}), requires loss of {required}"
                else:
                    # net_win是负数，取绝对值比较
                    loss_amount = abs(net_win)
                    eligible = loss_amount >= required
                    if not eligible:
                        message = f"Insufficient loss: {loss_amount}, requires {required}"
                    else:
                        message = f"Net loss condition met: {loss_amount} >= {required}"
            else:
                # 未知条件类型
                message = f"Unknown condition type: {condition_type}"
            
            return {
                'eligible': eligible,
                'message': message,
                'current_value': net_win,
                'required_value': required,
                'condition_type': condition_type
            }
            
        except Exception as e:
            logger.error(f"检查净赢条件失败: user_id={user_id}, error={str(e)}")
            return {
                'eligible': False,
                'message': f'Failed to check net win condition: {str(e)}',
                'current_value': Decimal('0'),
                'required_value': Decimal(str(required_amount or 0))
            }
    
    @staticmethod
    def get_user_betting_summary(user_id, start_date=None, end_date=None):
        """
        获取用户投注汇总信息
        
        Args:
            user_id: 用户ID
            start_date: 开始时间
            end_date: 结束时间
            
        Returns:
            dict: 包含投注统计信息
        """
        try:
            # 构建查询条件
            query_conditions = [
                Order.USER_ID == user_id,
                Order.STATUS == '1',
                Order.DEL_FLAG == 0,
                Order.TENANT_ID == '10000'
            ]
            
            if start_date:
                query_conditions.append(Order.CREATE_TIME >= start_date)
            if end_date:
                query_conditions.append(Order.CREATE_TIME <= end_date)
            
            # 查询汇总信息
            result = db.session.query(
                func.count(Order.ID).label('total_orders'),
                func.sum(Order.BET_MONEY).label('total_bet'),
                func.sum(Order.BONUS).label('total_bonus'),
                func.min(Order.CREATE_TIME).label('first_bet_time'),
                func.max(Order.CREATE_TIME).label('last_bet_time')
            ).filter(*query_conditions).first()
            
            if not result or not result.total_orders:
                return {
                    'total_orders': 0,
                    'total_bet': Decimal('0'),
                    'total_bonus': Decimal('0'),
                    'net_win': Decimal('0'),
                    'win_rate': Decimal('0'),
                    'first_bet_time': None,
                    'last_bet_time': None
                }
            
            total_bet = Decimal(str(result.total_bet or 0))
            total_bonus = Decimal(str(result.total_bonus or 0))
            net_win = total_bonus - total_bet
            
            # 计算盈利订单数
            profitable_orders = db.session.query(func.count(Order.ID)).filter(
                *query_conditions,
                Order.BONUS > Order.BET_MONEY
            ).scalar() or 0
            
            win_rate = Decimal('0')
            if result.total_orders > 0:
                win_rate = (Decimal(str(profitable_orders)) / Decimal(str(result.total_orders))) * 100
            
            return {
                'total_orders': result.total_orders,
                'total_bet': total_bet,
                'total_bonus': total_bonus,
                'net_win': net_win,
                'profitable_orders': profitable_orders,
                'win_rate': round(win_rate, 2),
                'first_bet_time': result.first_bet_time,
                'last_bet_time': result.last_bet_time
            }
            
        except Exception as e:
            logger.error(f"获取用户投注汇总失败: user_id={user_id}, error={str(e)}")
            return {
                'total_orders': 0,
                'total_bet': Decimal('0'),
                'total_bonus': Decimal('0'),
                'net_win': Decimal('0'),
                'win_rate': Decimal('0'),
                'first_bet_time': None,
                'last_bet_time': None
            }
    
    @staticmethod
    def get_net_win_condition_description(condition_type, amount):
        """
        获取净赢条件的描述文本
        
        Args:
            condition_type: 条件类型（WIN/LOSS）
            amount: 金额
            
        Returns:
            str: 条件描述
        """
        if not condition_type or not amount:
            return "No condition"
        
        amount_str = f"{amount:,.2f}" if isinstance(amount, (int, float, Decimal)) else str(amount)
        
        if condition_type == 'WIN':
            return f"Net win ≥ {amount_str}"
        elif condition_type == 'LOSS':
            return f"Net loss ≥ {amount_str}"
        else:
            return f"{condition_type}: {amount_str}"


# 创建全局实例
net_win_service = NetWinService()