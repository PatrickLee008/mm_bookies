from sqlalchemy import Column, String, DECIMAL, DateTime, Integer, Text, Boolean
from enum import Enum
from app_server import db
from app_server.utils.BaseSaasModel import BaseSaasModel


class RecordStatus(str, Enum):
    """佣金状态枚举"""
    PENDING = "Pending"  # 待结算
    SETTLED = "Settled"  # 已结算
    PAID = "Paid"  # 已发放
    FAILED = "Failed"  # 失败
    INVALID = "Invalid"  # 已失效
    CANCELLED = "Cancelled"  # 已取消


class RecordType(str, Enum):
    """记录类型枚举"""
    COMMISSION = "COMMISSION"  # 佣金
    CASHBACK = "CASHBACK"  # 返现


class SubType(str, Enum):
    """子类型枚举"""
    FIRST_ORDER_COMMISSION = "FIRST_ORDER_COMMISSION"  # 首单佣金
    REPEAT_COMMISSION = "REPEAT_COMMISSION"  # 复购佣金
    FIRST_ORDER_CASHBACK = "FIRST_ORDER_CASHBACK"  # 首单返现
    INVITEE_BET_COMMISSION = "INVITEE_BET_COMMISSION"  # 被邀请人投注佣金
    TURNOVER_COMMISSION = "TURNOVER_COMMISSION"  # 流水佣金
    WIN_LOSS_COMMISSION = "WIN_LOSS_COMMISSION"  # 输赢佣金


class SettleCycle(str, Enum):
    """结算周期枚举"""
    DAILY = "DAILY"  # 日
    WEEK = "WEEK"  # 周
    MONTH = "MONTH"  # 月
    QUARTER = "QUARTER"  # 季
    REALTIME = "REALTIME"  # 实时


class RefundStatus(str, Enum):
    """退款状态枚举"""
    NONE = "None"  # 无
    PARTIAL = "Partial"  # 部分退款
    FULL = "Full"  # 全额退款


class MAppCommissionRecord(BaseSaasModel):
    """佣金返现记录表模型"""
    __tablename__ = 'm_app_commission_record'

    id = Column(String(64), primary_key=True, comment='主键ID')
    record_no = Column(String(32), nullable=False, comment='记录编号')

    # 关联信息
    activity_id = Column(String(64), comment='活动ID')
    promotion_relation_id = Column(String(64), comment='推广关系ID')
    order_id = Column(String(64), nullable=False, comment='关联订单ID')
    user_id = Column(String(64), nullable=False, comment='用户ID（受益人）')
    user_username = Column(String(100), comment='用户名')
    related_user_id = Column(String(64), comment='关联用户ID')
    related_username = Column(String(100), comment='关联用户名')

    # 金额信息
    amount = Column(DECIMAL(15, 2), nullable=False, comment='原始计算金额')
    rate = Column(DECIMAL(6, 4), comment='佣金/返现比例')
    actual_amount = Column(DECIMAL(15, 2), comment='实际发放金额')

    # 类型区分
    record_type = Column(String(20), nullable=False, comment='记录类型')
    sub_type = Column(String(50), comment='子类型')

    # 结算周期信息
    settle_cycle = Column(String(20), comment='结算周期')
    settle_period = Column(String(30), comment='结算期')

    # 结算发放信息
    payout_id = Column(String(64), comment='发放记录ID')
    payout_no = Column(String(32), comment='发放批次号')
    payout_time = Column(DateTime, comment='发放时间')

    # 状态流转
    status = Column(String(20), default='Pending', comment='状态')
    settle_time = Column(DateTime, comment='结算时间')
    invalid_reason = Column(String(255), comment='失效原因')

    # 退款处理
    refund_amount = Column(DECIMAL(15, 2), default=0.00, comment='已退款金额')
    refund_status = Column(String(20), default='None', comment='退款状态')
    refund_time = Column(DateTime, comment='退款时间')

    # 规则信息
    rule_id = Column(String(64), comment='规则ID')
    rule_config = Column(Text, comment='规则配置快照（JSON）')

    # 业务字段
    order_amount = Column(DECIMAL(15, 2), comment='订单金额')
    order_type = Column(String(50), comment='订单类型')
    product_category = Column(String(50), comment='商品分类')
    base_amount = Column(DECIMAL(15, 2), comment='基础计算金额')

    # 扩展信息
    meta_data = Column(Text, comment='扩展信息（JSON）')

    __table_args__ = {
        'comment': '佣金返现记录表 - 记录所有佣金和返现的明细'
    }

    def __repr__(self):
        return f'<MAppCommissionRecord {self.id}: {self.record_type} {self.amount} ({self.status})>'


db.create_all()
