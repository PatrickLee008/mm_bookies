"""
佣金记录创建服务
在用户下注/结算时创建佣金记录
"""
import datetime
from decimal import Decimal
from app_server import db, app
from app_server.model.MAppCommissionRecordModel import MAppCommissionRecord, RecordType, SubType, RecordStatus, SettleCycle, RefundStatus
from app_server.model.MAppPromotionRelationModel import MAppPromotionRelation, RelationStatus
from app_server.model.MAppInvitationActivityModel import MAppInvitationActivity
from app_server.model.AppPlayerActivityRecordModel import AppPlayerActivityRecord
from app_server.utils.Kits import Kits
import random


class CommissionRecordService:
    """佣金记录服务类"""

    @staticmethod
    def create_commission_on_bet(bet_order, member_id, bet_amount, tenant_id):
        """
        在用户下注后创建佣金记录

        Args:
            bet_order: 投注订单对象或订单ID
            member_id: 用户ID（下注人）
            bet_amount: 投注金额
            tenant_id: 租户ID

        Returns:
            创建的佣金记录列表
        """
        try:
            # 1. 查询用户的推广关系
            relation = MAppPromotionRelation.query.filter_by(
                invitee_id=member_id,
                status=RelationStatus.ACTIVE.value,
                del_flag=0
            ).first()

            if not relation:
                app.logger.debug(f"用户没有推广关系，跳过佣金记录创建: member_id={member_id}")
                return []

            # 2. 查询推广人的邀请活动
            activity_record = AppPlayerActivityRecord.query.filter_by(
                mb_id=relation.promoter_id,
                activity_type='INVITATION',
                status='Active',
                del_flag=0
            ).first()

            if not activity_record:
                app.logger.debug(f"推广人没有活跃的邀请活动: promoter_id={relation.promoter_id}")
                return []

            # 3. 查询邀请活动配置
            activity = MAppInvitationActivity.query.filter_by(
                id=activity_record.activity_id,
                del_flag=0
            ).first()

            if not activity or not activity.status:
                app.logger.debug(f"邀请活动不存在或未激活: activity_id={activity_record.activity_id}")
                return []

            # 4. 根据活动配置创建佣金记录
            created_records = []

            # Method 3: 邀请人佣金 - 检查是否启用
            if hasattr(activity, 'method_commission_enabled') and activity.method_commission_enabled == 1:
                # 获取佣金类型
                commission_type = activity.commission_type if hasattr(activity, 'commission_type') else None
                commission_rate = activity.commission_rate if hasattr(activity, 'commission_rate') else None

                # 流水佣金（下注时创建）
                if commission_type == 'turnover' and commission_rate:
                    record = CommissionRecordService._create_turnover_commission_pending(
                        relation=relation,
                        activity=activity,
                        bet_order=bet_order,
                        member_id=member_id,
                        bet_amount=bet_amount,
                        tenant_id=tenant_id
                    )
                    if record:
                        created_records.append(record)

                # 输赢佣金（win_loss）：不在下注时创建记录
                # 改为在Java端佣金结算时按被邀请人汇总计算平台净盈利
                # 这样可以正确计算：平台净盈利 = Σ(被邀请人所有订单的投注金额 - 派奖金额)

            # Method 4: 被邀请人投注返佣 - 检查是否启用
            if hasattr(activity, 'method_invitee_bet_enabled') and activity.method_invitee_bet_enabled == 1:
                # 获取返佣比例
                invitee_bet_rate = activity.invitee_bet_commission_rate if hasattr(activity, 'invitee_bet_commission_rate') else None

                # 被邀请人投注返佣（下注时创建）
                if invitee_bet_rate:
                    record = CommissionRecordService._create_invitee_bet_cashback(
                        relation=relation,
                        activity=activity,
                        bet_order=bet_order,
                        member_id=member_id,
                        bet_amount=bet_amount,
                        tenant_id=tenant_id
                    )
                    if record:
                        created_records.append(record)

            return created_records

        except Exception as e:
            app.logger.error(f"创建下注佣金记录失败: member_id={member_id}, error={str(e)}")
            return []


    @staticmethod
    def _create_turnover_commission_pending(relation, activity, bet_order, member_id, bet_amount, tenant_id):
        """
        创建流水佣金记录（Method 3）

        Args:
            relation: 推广关系
            activity: 活动配置
            bet_order: 投注订单
            member_id: 下注用户ID
            bet_amount: 投注金额
            tenant_id: 租户ID

        Returns:
            佣金记录对象
        """
        try:
            # 获取订单ID
            order_id = bet_order if isinstance(bet_order, str) else getattr(bet_order, 'id', None)
            if not order_id:
                app.logger.warning("订单ID为空，无法创建佣金记录")
                return None

            # 检查是否已存在该订单的佣金记录
            existing = MAppCommissionRecord.query.filter_by(
                order_id=order_id,
                user_id=relation.promoter_id,
                record_type=RecordType.COMMISSION.value,
                sub_type=SubType.TURNOVER_COMMISSION.value,
                del_flag=0
            ).first()

            if existing:
                app.logger.debug(f"该订单的流水佣金记录已存在: order_id={order_id}")
                return None

            # 投注金额
            bet_amount_decimal = Decimal(str(bet_amount))
            if bet_amount_decimal <= 0:
                app.logger.debug("投注金额为0，跳过佣金记录创建")
                return None

            # 佣金比例
            rate = Decimal(str(activity.commission_rate))

            # 计算佣金金额
            commission_amount = (bet_amount_decimal * rate / Decimal('100')).quantize(Decimal('0.01'))

            # 获取结算周期（映射：weekly→WEEK, monthly→MONTH, manual→MANUAL）
            profit_share_freq = activity.profit_share_frequency if hasattr(activity, 'profit_share_frequency') and activity.profit_share_frequency else 'weekly'
            settle_cycle = CommissionRecordService._map_frequency_to_cycle(profit_share_freq)
            settle_period = CommissionRecordService._calculate_settle_period(settle_cycle)

            # 创建佣金记录
            record = MAppCommissionRecord(
                id=Kits.generate_uuid(),
                record_no=CommissionRecordService._generate_record_no('CR'),
                activity_id=activity.id,
                promotion_relation_id=relation.id,
                order_id=order_id,
                user_id=relation.promoter_id,  # 受益人是推广人
                user_username=relation.promoter_username,
                related_user_id=relation.invitee_id,  # 关联用户是被邀请人
                related_username=relation.invitee_username,
                amount=commission_amount,
                rate=rate,
                actual_amount=commission_amount,
                record_type=RecordType.COMMISSION.value,
                sub_type=SubType.TURNOVER_COMMISSION.value,
                settle_cycle=settle_cycle,
                settle_period=settle_period,
                status=RecordStatus.PENDING.value,
                refund_amount=Decimal('0.00'),
                refund_status=RefundStatus.NONE.value,
                order_amount=bet_amount_decimal,
                order_type='BET',
                base_amount=bet_amount_decimal,
                tenant_id=tenant_id,
                create_time=datetime.datetime.now(),
                update_time=datetime.datetime.now(),
                del_flag=0
            )

            db.session.add(record)
            db.session.commit()

            app.logger.info(
                f"创建流水佣金记录成功: record_no={record.record_no}, "
                f"promoter={relation.promoter_id}, invitee={relation.invitee_id}, "
                f"bet_amount={bet_amount}, commission={commission_amount}"
            )

            return record

        except Exception as e:
            app.logger.error(f"创建流水佣金记录失败: {str(e)}")
            db.session.rollback()
            return None

    @staticmethod
    def _create_win_loss_commission_pending(relation, activity, bet_order, member_id, bet_amount, tenant_id):
        """
        [已废弃] 创建输赢佣金PENDING记录（Method 3）
        
        !! 此方法已废弃，不再调用 !!
        
        win_loss佣金已改为在Java端结算时按被邀请人汇总计算平台净盈利，
        而不是每笔订单单独创建记录。
        
        原因：win_loss佣金应基于周期内平台的总净盈利计算，
        用户的赢钱会抵消输钱，只有最终的净盈利才是平台的真正收益。
        
        示例：
        - 用户A本周：输100 + 赢50 + 输30 = 平台净盈利80
        - 正确佣金 = 80 × 1% = 0.8元
        - 错误佣金 = 1 + 0 + 0.3 = 1.3元（每笔单独计算）

        Args:
            relation: 推广关系
            activity: 活动配置
            bet_order: 投注订单
            member_id: 下注用户ID
            bet_amount: 投注金额
            tenant_id: 租户ID

        Returns:
            None (方法已废弃)
        """
        app.logger.warning(
            "_create_win_loss_commission_pending已废弃，win_loss佣金在结算时汇总计算"
        )
        return None


    @staticmethod
    def _create_invitee_bet_cashback(relation, activity, bet_order, member_id, bet_amount, tenant_id):
        """
        创建被邀请人投注返佣记录（Method 4）

        Args:
            relation: 推广关系
            activity: 活动配置
            bet_order: 投注订单
            member_id: 下注用户ID（被邀请人）
            bet_amount: 投注金额
            tenant_id: 租户ID

        Returns:
            返佣记录对象
        """
        try:
            # 获取订单ID
            order_id = bet_order if isinstance(bet_order, str) else getattr(bet_order, 'id', None)
            if not order_id:
                app.logger.warning("订单ID为空，无法创建返佣记录")
                return None

            # 检查是否已存在该订单的返佣记录
            existing = MAppCommissionRecord.query.filter_by(
                order_id=order_id,
                user_id=relation.invitee_id,  # 注意：受益人是被邀请人
                record_type=RecordType.CASHBACK.value,
                sub_type=SubType.INVITEE_BET_COMMISSION.value,
                del_flag=0
            ).first()

            if existing:
                app.logger.debug(f"该订单的被邀请人返佣记录已存在: order_id={order_id}")
                return None

            # 投注金额
            bet_amount_decimal = Decimal(str(bet_amount))
            if bet_amount_decimal <= 0:
                app.logger.debug("投注金额为0，跳过返佣记录创建")
                return None

            # 返佣比例
            rate = Decimal(str(activity.invitee_bet_commission_rate))

            # 计算返佣金额
            cashback_amount = (bet_amount_decimal * rate / Decimal('100')).quantize(Decimal('0.01'))

            # 获取结算周期（映射：weekly→WEEK, monthly→MONTH, manual→MANUAL）
            profit_share_freq = activity.profit_share_frequency if hasattr(activity, 'profit_share_frequency') and activity.profit_share_frequency else 'weekly'
            settle_cycle = CommissionRecordService._map_frequency_to_cycle(profit_share_freq)
            settle_period = CommissionRecordService._calculate_settle_period(settle_cycle)

            # 创建返佣记录
            record = MAppCommissionRecord(
                id=Kits.generate_uuid(),
                record_no=CommissionRecordService._generate_record_no('CB'),  # CB = Cashback
                activity_id=activity.id,
                promotion_relation_id=relation.id,
                order_id=order_id,
                user_id=relation.invitee_id,  # 受益人是被邀请人自己
                user_username=relation.invitee_username,
                related_user_id=relation.promoter_id,  # 关联推广人
                related_username=relation.promoter_username,
                amount=cashback_amount,
                rate=rate,
                actual_amount=cashback_amount,
                record_type=RecordType.CASHBACK.value,  # 返现
                sub_type=SubType.INVITEE_BET_COMMISSION.value,
                settle_cycle=settle_cycle,
                settle_period=settle_period,
                status=RecordStatus.PENDING.value,
                refund_amount=Decimal('0.00'),
                refund_status=RefundStatus.NONE.value,
                order_amount=bet_amount_decimal,
                order_type='BET',
                base_amount=bet_amount_decimal,
                tenant_id=tenant_id,
                create_time=datetime.datetime.now(),
                update_time=datetime.datetime.now(),
                del_flag=0
            )

            db.session.add(record)
            db.session.commit()

            app.logger.info(
                f"创建被邀请人投注返佣记录成功: record_no={record.record_no}, "
                f"invitee={relation.invitee_id}, promoter={relation.promoter_id}, "
                f"bet_amount={bet_amount}, cashback={cashback_amount}"
            )

            return record

        except Exception as e:
            app.logger.error(f"创建被邀请人投注返佣记录失败: {str(e)}")
            db.session.rollback()
            return None


    @staticmethod
    def _map_frequency_to_cycle(frequency):
        """
        映射结算频率到结算周期类型

        Args:
            frequency: 前端配置的结算频率（weekly/monthly/manual/daily）

        Returns:
            结算周期类型（WEEK/MONTH/MANUAL/DAILY）
        """
        frequency_map = {
            'weekly': 'WEEK',
            'monthly': 'MONTH',
            'manual': 'MANUAL',
            'daily': 'DAILY',
            'quarterly': 'QUARTER',
            'realtime': 'REALTIME'
        }
        return frequency_map.get(frequency.lower() if frequency else '', 'WEEK')

    @staticmethod
    def _calculate_settle_period(settle_cycle):
        """
        计算结算周期字符串

        Args:
            settle_cycle: 结算周期类型（DAILY/WEEK/MONTH/QUARTER/REALTIME/MANUAL）

        Returns:
            结算期字符串
        """
        from datetime import date
        today = date.today()

        settle_cycle_upper = settle_cycle.upper()

        if settle_cycle_upper == 'DAILY':
            return today.strftime('%Y-%m-%d')
        elif settle_cycle_upper == 'WEEK':
            # ISO周（周一为第一天）
            iso_calendar = today.isocalendar()
            return f"{iso_calendar[0]}-W{iso_calendar[1]:02d}"
        elif settle_cycle_upper == 'MONTH':
            return today.strftime('%Y-%m')
        elif settle_cycle_upper == 'QUARTER':
            quarter = (today.month - 1) // 3 + 1
            return f"{today.year}-Q{quarter}"
        elif settle_cycle_upper == 'MANUAL':
            # 手动结算：使用当前日期作为标识
            return f"MANUAL-{today.strftime('%Y-%m-%d')}"
        elif settle_cycle_upper == 'REALTIME':
            return today.strftime('%Y-%m-%d')
        else:
            return today.strftime('%Y-%m')

    @staticmethod
    def _generate_record_no(prefix):
        """
        生成记录编号

        Args:
            prefix: 前缀（CR-佣金/CB-返现）

        Returns:
            记录编号
        """
        date_str = datetime.datetime.now().strftime('%Y%m%d')
        random_str = f"{random.randint(0, 99999):05d}"
        return f"{prefix}{date_str}{random_str}"
