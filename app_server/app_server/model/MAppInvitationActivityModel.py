from sqlalchemy.orm import relationship, session

from app_server import db, app
from sqlalchemy import Column, String, DECIMAL, DateTime, Text, Integer, SmallInteger, Boolean
import datetime

from app_server.model.MAppInvitationRewardModel import MAppInvitationReward
from app_server.utils.BaseSaasModel import BaseSaasModel
class MAppInvitationActivity(BaseSaasModel):
    """邀请活动表模型"""
    __tablename__ = 'm_app_invitation_activity'

    id = Column(String(64), primary_key=True, comment="邀请活动ID")
    title = Column(String(100), nullable=False, comment='活动标题')
    description = Column(Text, nullable=True, comment='活动描述')
    bonus_type = Column(String(32), nullable=True, comment='奖金类型：Invitation Bonus、Turnover bonus、Net Win Bonus')
    start_date = Column(DateTime, nullable=False, comment='活动开始日期')
    end_date = Column(DateTime, nullable=False, comment='活动结束日期')
    reward_amount = Column(DECIMAL(10, 2), nullable=False, comment='单次奖励金额')
    max_reward_count = Column(Integer, nullable=False, comment='最大奖励次数')
    is_active = Column(Boolean, default=True, comment='是否激活：1-激活 0-未激活')
    is_closed = Column(Boolean, default=False, comment='是否手动关闭：1-关闭 0-未关闭')
    sort = Column(Integer, comment='排序')
    
    # 奖金池相关字段
    bonus_pool = Column(DECIMAL(10, 2), nullable=True, comment='奖金池总额')
    bonus_pool_remaining = Column(DECIMAL(10, 2), nullable=True, comment='奖金池剩余金额')
    agent_id = Column(String(64), nullable=True, comment='所属代理ID')
    is_pool_exhausted = Column(SmallInteger, default=0, comment='奖金池是否耗尽：1-耗尽 0-未耗尽')
    
    # 关系：关联该活动的所有奖励领取记录
    reward_records = relationship('MAppInvitationReward', backref='activity', lazy=True)


@classmethod
def get_current_active_activity(cls, tenant_id=None):
    """
    获取当前正在进行的活动（只能有一个）
    :param tenant_id: 租户ID，多租户场景下使用
    :return: 当前有效的活动对象或None
    """
    query = cls.query.filter(
        cls.is_active == True,
        cls.is_closed == False,
        cls.del_flag == 0,
        cls.start_date <= datetime.now(),
        cls.end_date >= datetime.now()
    )

    # 多租户过滤
    if tenant_id:
        query = query.filter(cls.tenant_id == tenant_id)

    # 按排序字段取第一个（sort值小的优先）
    return query.order_by(cls.sort).first()


def can_receive_reward(self):
    """判断当前活动是否还能领取奖励"""
    # 检查活动是否有效（未删除、激活、未关闭）
    if self.del_flag != 0 or not self.is_active or self.is_closed:
        return False
        
    # 检查奖金池是否耗尽
    if hasattr(self, 'is_pool_exhausted') and self.is_pool_exhausted == 1:
        return False

    # 检查活动时间是否在有效期内
    now = datetime.now()
    if now < self.start_date or now > self.end_date:
        return False

    # 检查是否已达最大奖励次数
    from sqlalchemy import func
    current_count = session.query(func.count(MAppInvitationReward.id)).filter(
        MAppInvitationReward.activity_id == self.id,
        MAppInvitationReward.status == 'claimed',
        MAppInvitationReward.del_flag == 0
    ).scalar() or 0

    if current_count >= self.max_reward_count:
        return False

    return True
db.create_all()