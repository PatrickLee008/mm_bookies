from sqlalchemy import Column, String, DECIMAL, Integer, SmallInteger, ForeignKey, Enum as SQLEnum, UniqueConstraint
from enum import Enum

from app_server import db
from app_server.utils.BaseSaasModel import BaseSaasModel

# 奖励规则类型枚举（与之前逻辑保持一致）
class RewardRuleType(str, Enum):
    INVITE_COUNT = "invite_count"  # 邀请人数达标
    INVITEE_FIRST_RECHARGE = "invitee_first_recharge"  # 被邀请人首充
    FIRST_BET = "first_bet"  # 首次下注
    BET_PROFIT = "bet_profit"  # 下注盈利
    BET_CASHBACK = "bet_cashback"  # 下注返还

class MAppInvitationActivityRule(BaseSaasModel):
    """邀请活动奖励规则表模型"""
    __tablename__ = 'm_app_invitation_activity_rule'  # 规则表名

    id = Column(String(36), primary_key=True, comment='主键ID(UUID)')
    activity_id = Column(String(36), ForeignKey('m_app_invitation_activity.id'), nullable=False,
                         comment='关联活动ID(UUID)')
    # 临时修复：使用 String 类型避免枚举验证问题
    # rule_type = Column(SQLEnum(RewardRuleType), nullable=False, comment='规则类型')
    rule_type = Column(String(50), nullable=False, comment='规则类型')
    threshold_value = Column(DECIMAL(10, 2), nullable=False, comment='阈值(数量/金额，如邀请人数10、首充金额5000)')
    reward_amount = Column(DECIMAL(10, 2), nullable=False, comment='规则对应的奖励金额')
    max_claim_count = Column(Integer, default=1, comment='最大可领取次数(0表示无限制)')
    sequence = Column(Integer, default=0, comment='规则顺序(用于多阶梯规则排序)')
    description = Column(String(255), comment='规则描述(如"邀请10人奖励5000")')

    # 联合唯一约束：同一活动中，同类型同阈值的规则唯一
    __table_args__ = (
        UniqueConstraint('activity_id', 'rule_type', 'threshold_value', name='unique_activity_rule_type_threshold'),
        {'comment': '邀请活动奖励规则配置表'}
    )
    
    @property
    def rule_type_enum(self):
        """获取规则类型对应的枚举值"""
        try:
            return RewardRuleType(self.rule_type)
        except ValueError:
            # 如果数据库中的值不在枚举中，返回 None 或抛出更友好的错误
            raise ValueError(f"无效的规则类型: {self.rule_type}，有效值: {[e.value for e in RewardRuleType]}")
    
    def is_valid_rule_type(self):
        """检查规则类型是否有效"""
        try:
            RewardRuleType(self.rule_type)
            return True
        except ValueError:
            return False

db.create_all()