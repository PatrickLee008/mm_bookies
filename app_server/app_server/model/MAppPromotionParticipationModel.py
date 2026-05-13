"""
促销活动参与记录 Model
记录用户参与促销活动的情况
"""
from sqlalchemy import Column, String, Integer, DECIMAL, DateTime, Text
from app_server.utils.BaseSaasModel import BaseSaasModel


class MAppPromotionParticipation(BaseSaasModel):
    __tablename__ = 'm_app_promotion_participation'

    id = Column(String(64), primary_key=True, comment='ID')

    # 关联信息
    promotion_id = Column(String(64), nullable=False, comment='促销活动ID')
    mb_id = Column(String(64), nullable=False, comment='会员ID')
    mb_username = Column(String(100), nullable=True, comment='会员用户名')
    agent_id = Column(String(64), nullable=True, comment='代理ID')

    # 奖励信息
    reward_amount = Column(DECIMAL(20, 2), nullable=True, comment='奖励金额')
    bonus_type = Column(String(50), nullable=True, comment='奖金类型')

    # 流水/净赢要求
    req_turnover = Column(DECIMAL(20, 2), default=0, comment='要求流水')
    req_netwin = Column(DECIMAL(20, 2), default=0, comment='要求净赢')
    cur_turnover = Column(DECIMAL(20, 2), default=0, comment='当前流水')
    cur_netwin = Column(DECIMAL(20, 2), default=0, comment='当前净赢')

    # 状态信息
    status = Column(String(20), nullable=True, comment='状态：Active-进行中 Completed-已完成 Expired-已过期 Cancelled-已取消')
    participation_time = Column(DateTime, nullable=True, comment='参与时间')
    completion_time = Column(DateTime, nullable=True, comment='完成时间')
    expire_time = Column(DateTime, nullable=True, comment='过期时间')

    # 设备信息
    mb_ip = Column(String(50), nullable=True, comment='IP地址')
    device_id = Column(String(200), nullable=True, comment='设备ID')

    # 钱包类型
    target_wallet = Column(String(20), nullable=True, comment='目标钱包：Main-主钱包 Promotion-促销钱包')

    # 备注
    remarks = Column(Text, nullable=True, comment='备注')

    # 审计字段
    create_by_id = Column(String(64), nullable=True, comment='创建人ID')
    create_time = Column(DateTime, nullable=True, comment='创建时间')
    update_by_id = Column(String(64), nullable=True, comment='更新人ID')
    update_time = Column(DateTime, nullable=True, comment='更新时间')
    del_flag = Column(Integer, default=0, comment='删除标记：0-未删除 1-已删除')
    tenant_id = Column(String(64), default='10000', comment='租户ID')

    def __repr__(self):
        return f"<MAppPromotionParticipation(id={self.id}, promotion_id={self.promotion_id}, mb_id={self.mb_id}, status={self.status})>"
