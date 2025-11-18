
from sqlalchemy import Column, String, DECIMAL, DateTime, Text, Integer, SmallInteger, ForeignKey, UniqueConstraint

from app_server import db
from app_server.utils.BaseSaasModel import BaseSaasModel
class MAppInvitationReward(BaseSaasModel):
    """邀请奖励领取记录表模型"""
    __tablename__ = 'm_app_invitation_reward'  # 假设表名

    id = Column(String(36), primary_key=True,comment='主键ID(UUID)')
    activity_id = Column(String(36), ForeignKey('m_app_invitation_activity.id'), nullable=False,
                            comment='关联活动ID(UUID)')
    rule_id = Column(String(36), ForeignKey('m_app_invitation_activity_rule.id'), nullable=False,
                     comment='关联规则ID(UUID)')
    referrer_id = Column(String(64), nullable=False, comment='推荐人ID')
    referred_user_id = Column(String(64), nullable=True, comment='被推荐人ID(某些规则可能不需要)')
    reward_amount = Column(DECIMAL(10, 2), nullable=False, comment='领取的奖励金额')
    bonus_type = Column(String(32), nullable=True, comment='奖金类型：Invitation Bonus、Turnover bonus、Net Win Bonus')
    status = Column(String(20), default='pending', comment='状态: pending-待领取, claimed-已领取, invalid-无效')
    claimed_at = Column(DateTime, comment='领取时间')

    # 约束说明：同一个用户针对同一规则的奖励可以多次领取（如果规则允许）
    # 但需要在应用层控制最大领取次数
    __table_args__ = (
        # 可以根据业务需求添加约束，这里暂时不加唯一约束
        {'comment': '邀请奖励领取记录表'}
    )
db.create_all()