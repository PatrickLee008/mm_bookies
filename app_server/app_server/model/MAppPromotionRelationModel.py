from sqlalchemy import Column, String, DECIMAL, DateTime, Integer, Boolean
from enum import Enum
from app_server import db
from app_server.utils.BaseSaasModel import BaseSaasModel


class RelationStatus(str, Enum):
    """关系状态枚举"""
    ACTIVE = "Active"  # 正常
    INVALID = "Invalid"  # 失效
    FROZEN = "Frozen"  # 冻结


class InviteChannel(str, Enum):
    """邀请渠道枚举"""
    WECHAT = "WECHAT"  # 微信
    QQ = "QQ"  # QQ
    LINK = "LINK"  # 链接
    APP = "APP"  # 应用内
    H5 = "H5"  # H5页面


class MAppPromotionRelation(BaseSaasModel):
    """推广关系表模型"""
    __tablename__ = 'm_app_promotion_relation'

    id = Column(String(64), primary_key=True, comment='主键ID')

    # 关联信息
    activity_id = Column(String(64), comment='活动ID')
    promoter_id = Column(String(64), nullable=False, comment='推广人ID')
    promoter_username = Column(String(100), comment='推广人用户名')
    invitee_id = Column(String(64), nullable=False, comment='被邀请人ID')
    invitee_username = Column(String(100), comment='被邀请人用户名')

    # 关系层级
    relation_level = Column(Integer, default=1, comment='关系层级')
    parent_relation_id = Column(String(64), comment='上级关系ID')

    # 时间信息
    invite_time = Column(DateTime, comment='邀请时间')
    register_time = Column(DateTime, comment='被邀请人注册时间')
    first_deposit_time = Column(DateTime, comment='被邀请人首次存款时间')
    first_deposit_amount = Column(DECIMAL(10, 2), default=0.00, comment='被邀请人首次存款金额')

    # 邀请信息
    invite_channel = Column(String(50), comment='邀请渠道')
    invite_code = Column(String(32), comment='邀请码')
    invite_ip = Column(String(50), comment='邀请IP地址')
    invite_device = Column(String(100), comment='邀请设备信息')

    # 状态信息
    status = Column(String(20), default='Active', comment='关系状态')
    is_counted_in_activity = Column(Boolean, default=True, comment='是否计入活动统计（True-计入奖励/False-不计入奖励，超出邀请限制的设为False）')
    invalid_reason = Column(String(255), comment='失效原因')
    invalid_time = Column(DateTime, comment='失效时间')

    # 统计字段
    total_deposit = Column(DECIMAL(15, 2), default=0.00, comment='被邀请人累计存款金额')
    total_bet = Column(DECIMAL(15, 2), default=0.00, comment='被邀请人累计投注金额')
    total_commission = Column(DECIMAL(15, 2), default=0.00, comment='已产生的总佣金金额')
    is_effective = Column(Boolean, default=False, comment='是否有效会员')
    effective_time = Column(DateTime, comment='成为有效会员的时间')

    # 代理信息
    aid = Column(String(64), comment='代理ID')

    __table_args__ = {
        'comment': '推广关系表 - 记录用户间的邀请推广关系'
    }

    def __repr__(self):
        return f'<MAppPromotionRelation {self.id}: {self.promoter_id} -> {self.invitee_id} ({self.status})>'


db.create_all()
