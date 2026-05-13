# -*- coding: utf-8 -*-
from app_server import db
from sqlalchemy import Column, String
from sqlalchemy.dialects.mysql import DATETIME, DECIMAL
from app_server.utils.BaseSaasModel import BaseSaasModel


class AdjustmentType:
    """调整类型枚举"""
    MANUAL = "Manual"  # 手动
    SYSTEM = "System"  # 系统
    COMPENSATION = "Compensation"  # 补偿


class AdjustmentStatus:
    """调整状态枚举"""
    PENDING = "Pending"  # 待处理
    SUCCESS = "Success"  # 成功
    REJECTED = "Rejected"  # 拒绝


class AppAdjustment(BaseSaasModel):
    """
    会员余额调整模型
    对应表: m_app_adjustment
    """
    __tablename__ = 'm_app_adjustment'

    # 主键
    id = Column(String(64), primary_key=True, comment="主键ID")

    # 会员信息
    mb_id = Column(String(64), index=True, comment="会员ID")
    mb_username = Column(String(64), comment="会员用户名")
    mb_nickname = Column(String(64), comment="会员昵称")

    # 调整信息
    adjustment_type = Column(String(32), nullable=False, server_default='Manual',
                            comment="调整类型：Manual-手动，System-系统，Compensation-补偿")
    amount = Column(DECIMAL(20, 2), nullable=False, server_default='0.00',
                   comment="调整金额（正数为增加，负数为减少）")
    before_balance = Column(DECIMAL(20, 2), server_default='0.00', comment="调整前余额")
    after_balance = Column(DECIMAL(20, 2), server_default='0.00', comment="调整后余额")

    # 管理员信息
    mn_id = Column(String(64), comment="管理员ID")
    mn_name = Column(String(64), comment="管理员姓名")
    mn_username = Column(String(64), comment="管理员用户名")

    # 状态与时间
    status = Column(String(32), nullable=False, server_default='Success',
                   comment="状态：Pending-待处理，Success-成功，Rejected-拒绝")
    process_time = Column(DATETIME, comment="处理时间")

    # 原因与备注
    reason = Column(String(255), comment="调整原因")
    remarks = Column(String(500), comment="管理员备注")

    __mapper_args__ = {
        "order_by": BaseSaasModel.create_time.desc(),
    }


db.create_all()
