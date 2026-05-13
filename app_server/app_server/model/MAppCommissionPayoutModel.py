from sqlalchemy import Column, String, DECIMAL, DateTime, Integer, Text, Boolean
from enum import Enum
from app_server import db
from app_server.utils.BaseSaasModel import BaseSaasModel


class PayoutStatus(str, Enum):
    """发放状态枚举"""
    PENDING_AUDIT = "PendingAudit"  # 待审核
    APPROVED = "Approved"  # 已批准
    REJECTED = "Rejected"  # 已拒绝
    PAID = "Paid"  # 已发放
    FAILED = "Failed"  # 发放失败
    CANCELLED = "Cancelled"  # 已取消


class AuditStatus(str, Enum):
    """审核状态枚举"""
    PENDING = "Pending"  # 待审核
    APPROVED = "Approved"  # 通过
    REJECTED = "Rejected"  # 驳回


class PayoutType(str, Enum):
    """发放方式枚举"""
    WECHAT = "WECHAT"  # 微信
    ALIPAY = "ALIPAY"  # 支付宝
    BANK = "BANK"  # 银行卡
    BALANCE = "BALANCE"  # 余额
    MANUAL = "MANUAL"  # 手动


class MAppCommissionPayout(BaseSaasModel):
    """佣金发放记录表模型"""
    __tablename__ = 'm_app_commission_payout'

    id = Column(String(64), primary_key=True, comment='主键ID')
    payout_no = Column(String(32), nullable=False, unique=True, comment='发放批次号')
    batch_name = Column(String(100), comment='批次名称')

    # 发放范围信息
    activity_id = Column(String(64), comment='活动ID')
    settle_period = Column(String(30), nullable=False, comment='结算期')
    settle_cycle = Column(String(20), comment='结算周期')
    record_type = Column(String(20), comment='记录类型')

    # 发放方式信息
    payout_type = Column(String(20), nullable=False, comment='发放方式')
    payout_account = Column(String(100), comment='发放账号')
    payout_channel = Column(String(50), comment='发放渠道')

    # 金额统计
    total_amount = Column(DECIMAL(15, 2), nullable=False, comment='发放总金额')
    total_count = Column(Integer, nullable=False, comment='发放总笔数')
    success_amount = Column(DECIMAL(15, 2), default=0.00, comment='成功金额')
    success_count = Column(Integer, default=0, comment='成功笔数')
    fail_amount = Column(DECIMAL(15, 2), default=0.00, comment='失败金额')
    fail_count = Column(Integer, default=0, comment='失败笔数')
    pending_amount = Column(DECIMAL(15, 2), default=0.00, comment='待处理金额')
    pending_count = Column(Integer, default=0, comment='待处理笔数')

    # 关联记录信息
    commission_record_ids = Column(Text, comment='关联的佣金记录ID列表（JSON）')
    user_count = Column(Integer, default=0, comment='涉及用户数')

    # 状态流转
    payout_status = Column(String(20), default='PendingAudit', comment='发放状态')
    payout_time = Column(DateTime, comment='实际发放时间')
    complete_time = Column(DateTime, comment='完成时间')

    # 审核流程
    need_audit = Column(Boolean, default=False, comment='是否需要审核')
    auditor_id = Column(String(64), comment='审核人ID')
    auditor_name = Column(String(100), comment='审核人名称')
    audit_time = Column(DateTime, comment='审核时间')
    audit_status = Column(String(20), default='Pending', comment='审核状态')
    audit_remark = Column(String(500), comment='审核备注')

    # 发放结果详情
    result_detail = Column(Text, comment='发放结果详情（JSON）')
    error_message = Column(Text, comment='错误信息')
    success_detail = Column(Text, comment='成功明细（JSON）')
    fail_detail = Column(Text, comment='失败明细（JSON）')

    # 业务控制字段
    retry_count = Column(Integer, default=0, comment='重试次数')
    max_retry_count = Column(Integer, default=3, comment='最大重试次数')
    last_retry_time = Column(DateTime, comment='最后重试时间')
    can_retry = Column(Boolean, default=True, comment='是否可重试')

    # 操作人信息
    operator_id = Column(String(64), comment='操作人ID')
    operator_name = Column(String(100), comment='操作人名称')

    # 时间限制
    start_time = Column(DateTime, comment='开始发放时间（计划）')
    end_time = Column(DateTime, comment='结束发放时间（计划）')

    # 扩展信息
    config = Column(Text, comment='发放配置（JSON）')
    meta_data = Column(Text, comment='扩展信息（JSON）')

    __table_args__ = {
        'comment': '佣金发放记录表 - 记录佣金返现的发放批次和结果'
    }

    def __repr__(self):
        return f'<MAppCommissionPayout {self.id}: {self.payout_no} {self.total_amount} ({self.payout_status})>'


db.create_all()
