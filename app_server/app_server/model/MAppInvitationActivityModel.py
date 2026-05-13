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
    start_date = Column(DateTime, nullable=False, comment='活动开始日期')
    end_date = Column(DateTime, nullable=False, comment='活动结束日期')
    status = Column(Boolean, default=True, comment='是否激活：1-激活 0-未激活')
    is_closed = Column(Boolean, default=False, comment='是否手动关闭：1-关闭 0-未关闭')
    sort = Column(Integer, comment='排序')
    
    # 奖金池相关字段
    bonus_pool = Column(DECIMAL(10, 2), nullable=True, comment='奖金池总额')
    bonus_pool_remaining = Column(DECIMAL(10, 2), nullable=True, comment='奖金池剩余金额')
    agent_id = Column(String(64), nullable=True, comment='所属代理ID')
    is_pool_exhausted = Column(SmallInteger, default=0, comment='奖金池是否耗尽：1-耗尽 0-未耗尽')

    # v2.0 新增字段
    # 广告图片
    slogan = Column(String(200), nullable=True, comment='活动标语')
    ad_image_url = Column(String(500), nullable=True, comment='活动广告图片URL')

    # 流水倍数和结算频率
    turnover_multiplier = Column(DECIMAL(5, 2), default=1.0, comment='流水倍数（如1.0表示1倍流水）')
    net_win_multiplier = Column(DECIMAL(5, 2), default=0.5, comment='净赢倍数（如0.5表示需要净赢奖金的50%）')
    withdrawal_requirement_type = Column(String(32), default='Turnover', comment='提现要求类型：Turnover/Net Win')
    net_win_amount = Column(DECIMAL(10, 2), default=0.00, comment='净赢金额（用户直接输入的净赢值）')
    profit_share_frequency = Column(String(32), default='weekly', comment='分润频率：weekly/monthly/manual')

    # 4种邀请方法的启用状态
    method_invitation_enabled = Column(SmallInteger, default=0, comment='Method 1: 邀请/成就奖励是否启用（0-否 1-是）')
    method_deposit_enabled = Column(SmallInteger, default=0, comment='Method 2: 存款分享是否启用（0-否 1-是）')
    method_commission_enabled = Column(SmallInteger, default=0, comment='Method 3: 邀请人佣金是否启用（0-否 1-是）')
    method_invitee_bet_enabled = Column(SmallInteger, default=0, comment='Method 4: 被邀请人投注佣金是否启用（0-否 1-是）')

    # Method 3: 邀请人佣金配置
    commission_type = Column(String(32), nullable=True, comment='佣金类型：turnover（流水）/win_loss（输赢）')
    commission_rate = Column(DECIMAL(5, 2), nullable=True, comment='佣金比例（百分比）')

    # Method 4: 被邀请人投注佣金配置
    invitee_bet_commission_rate = Column(DECIMAL(5, 2), nullable=True, comment='被邀请人投注返水比例（百分比）')
    # Method 1.1 Invitation achievement: 邀请成就
    achievement_invitee_min_deposit = Column(DECIMAL(10, 2), default=0.00, comment='邀请成就奖励被邀请人最低存款要求')

    # Method 1.2 Invitation Share: 邀请分享配置（单次邀请奖励）
    invitation_share_one_time_bonus = Column(DECIMAL(10, 2), nullable=True, comment='一次性奖金金额（每成功邀请一人）')
    invitation_share_min_deposit = Column(DECIMAL(10, 2), nullable=True, comment='一次性奖金金额被邀请人最低存款要求')
    invitation_share_min_turnover = Column(DECIMAL(10, 2), nullable=True, comment='一次性奖金金额被邀请人最低流水要求')

    # 资金管理字段（Escrow模型）
    fund_source_type = Column(String(32), default='AGENT', comment='资金来源类型：AGENT-代理余额, HOUSE-平台余额')
    escrow_status = Column(SmallInteger, default=0, comment='托管状态：0-未托管, 1-已托管扣款, 2-已退款')
    used_amount = Column(DECIMAL(10, 2), default=0.00, comment='已使用金额（已发放的奖励总额）')

    # 风险控制字段：IP/设备限制
    ip_limit_count = Column(Integer, default=0, comment='每个IP限制参与次数（0表示不限制）')
    imei_limit_count = Column(Integer, default=0, comment='每个设备限制参与次数（0表示不限制）')

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
        cls.status == True,
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
    if self.del_flag != 0 or not self.status or self.is_closed:
        return False
        
    # 检查奖金池是否耗尽
    if hasattr(self, 'is_pool_exhausted') and self.is_pool_exhausted == 1:
        return False

    # 检查活动时间是否在有效期内
    now = datetime.now()
    if now < self.start_date or now > self.end_date:
        return False

    # 注意：最大奖励次数的检查现在由活动规则表（m_app_invitation_activity_rule）控制
    # 每条规则有自己的 max_claim_count 字段，需要在具体业务逻辑中检查

    return True
db.create_all()