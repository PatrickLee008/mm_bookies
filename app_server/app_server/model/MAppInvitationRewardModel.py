
from sqlalchemy import Column, String, DECIMAL, DateTime, Text, Integer, SmallInteger, ForeignKey, UniqueConstraint

from app_server import db
from app_server.utils.BaseSaasModel import BaseSaasModel
class MAppInvitationReward(BaseSaasModel):
    """邀请奖励领取记录表模型"""
    __tablename__ = 'm_app_invitation_reward'  # 假设表名

    id = Column(String(36), primary_key=True,comment='主键ID(UUID)')
    activity_id = Column(String(36), ForeignKey('m_app_invitation_activity.id'), nullable=False,
                            comment='关联活动ID(UUID)')
    rule_id = Column(String(36), nullable=True,
                     comment='关联ID：Method 1=规则ID, Method 2=档位ID')
    mb_id = Column(String(64), nullable=False, comment='会员ID(推荐人ID)')
    referred_id = Column(String(64), nullable=True, comment='被邀请人ID(某些规则可能不需要)')
    reward_amount = Column(DECIMAL(10, 2), nullable=False, comment='领取的奖励金额')
    bonus_type = Column(String(64), nullable=True, comment='奖励来源：method1_invitation_share/method1_achievement/method2_deposit_share/method3_commission/method4_invitee_bet')
    status = Column(String(20), default='Pending', comment='状态: Pending-待领取, Claimed-已领取, Invalid-无效')
    claimed_at = Column(DateTime, comment='领取时间')
    meta_data = Column(Text, nullable=True, comment='元数据(JSON格式)：存储deposit_id、bet_id等相关信息')

    # 约束说明：同一个用户针对同一规则的奖励可以多次领取（如果规则允许）
    # 但需要在应用层控制最大领取次数
    __table_args__ = (
        # 可以根据业务需求添加约束，这里暂时不加唯一约束
        {'comment': '邀请奖励领取记录表'}
    )
db.create_all()