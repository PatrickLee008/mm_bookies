from sqlalchemy import Column, String, DECIMAL, Integer, ForeignKey
from app_server import db
from app_server.utils.BaseSaasModel import BaseSaasModel


class MAppInvitationDepositShare(BaseSaasModel):
    """邀请活动存款分享配置表模型（Method 2）"""
    __tablename__ = 'm_app_invitation_deposit_share'

    id = Column(String(64), primary_key=True, comment='主键ID')
    activity_id = Column(String(64), nullable=False, comment='关联活动ID')
    min_deposit = Column(DECIMAL(10, 2), nullable=False, comment='最小存款金额')
    max_deposit = Column(DECIMAL(10, 2), nullable=True, comment='最大存款金额（null表示无上限）')
    bonus_rate = Column(DECIMAL(5, 2), nullable=False, comment='奖励比例（百分比，如5.00表示5%）')
    max_claims = Column(Integer, nullable=True, default=0, comment='最大领取次数（0表示无限制）')
    description = Column(String(255), nullable=True, comment='描述（自定义档位说明）')
    sequence = Column(Integer, default=0, comment='排序序号（用于多档位配置排序）')

    __table_args__ = {
        'comment': '邀请活动存款分享配置表 - 被邀请人存款时给邀请人的奖励'
    }

    def __repr__(self):
        return f'<MAppInvitationDepositShare {self.id}: {self.min_deposit}-{self.max_deposit} @ {self.bonus_rate}%>'


db.create_all()
