from sqlalchemy import Column, String, DECIMAL, Integer, SmallInteger, ForeignKey, Enum as SQLEnum, UniqueConstraint
from enum import Enum

from app_server import db
from app_server.utils.BaseSaasModel import BaseSaasModel

# 成就规则类型枚举（Method 1: Achievement Share）
class AchievementType(str, Enum):
    INVITE_COUNT = "invite_count"  # 邀请人数达标
    INVITEE_FIRST_RECHARGE = "invitee_first_recharge"  # 被邀请人首充
    FIRST_BET = "first_bet"  # 首次下注
    BET_PROFIT = "bet_profit"  # 下注盈利
    BET_CASHBACK = "bet_cashback"  # 下注返还

class MAppInvitationAchievement(BaseSaasModel):
    """邀请活动成就规则表模型 (Method 1: Achievement Share)"""
    __tablename__ = 'm_app_invitation_achievement'  # 成就表名

    id = Column(String(36), primary_key=True, comment='主键ID(UUID)')
    activity_id = Column(String(36), ForeignKey('m_app_invitation_activity.id'), nullable=False,
                         comment='关联活动ID(UUID)')
    # 临时修复：使用 String 类型避免枚举验证问题
    # rule_type = Column(SQLEnum(AchievementType), nullable=False, comment='成就类型')
    rule_type = Column(String(50), nullable=False, comment='成就类型')
    threshold_value = Column(DECIMAL(10, 2), nullable=False, comment='阈值(数量/金额，如邀请人数10、首充金额5000)')
    reward_amount = Column(DECIMAL(10, 2), nullable=False, comment='成就对应的奖励金额')
    max_claim_count = Column(Integer, default=1, comment='最大可领取次数(0表示无限制)')
    sequence = Column(Integer, default=0, comment='成就顺序(用于多阶梯成就排序)')
    description = Column(String(255), comment='成就描述(如"邀请10人奖励5000")')

    # 联合唯一约束：同一活动中，同类型同阈值的成就唯一
    __table_args__ = (
        UniqueConstraint('activity_id', 'rule_type', 'threshold_value', name='unique_activity_achievement_type_threshold'),
        {'comment': '邀请活动成就规则配置表 (Method 1: Achievement Share)'}
    )

    @property
    def achievement_type_enum(self):
        """获取成就类型对应的枚举值"""
        try:
            return AchievementType(self.rule_type)
        except ValueError:
            # 如果数据库中的值不在枚举中，返回 None 或抛出更友好的错误
            raise ValueError(f"无效的成就类型: {self.rule_type}，有效值: {[e.value for e in AchievementType]}")

    def is_valid_achievement_type(self):
        """检查成就类型是否有效"""
        try:
            AchievementType(self.rule_type)
            return True
        except ValueError:
            return False

db.create_all()