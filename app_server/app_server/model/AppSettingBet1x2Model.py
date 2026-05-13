from app_server import db, app
from sqlalchemy import Column, String, Integer, Index
from sqlalchemy.dialects.mysql import DATETIME, DECIMAL, TINYINT
from datetime import datetime
from typing import Optional

from app_server.utils.BaseSaasModel import BaseSaasModel


# 代理1x2下注参数配置表
class AppSettingBet1x2Model(BaseSaasModel):
    __tablename__ = 'm_app_setting_bet_1x2'

    # 主键与基础信息
    id = Column(String(64), primary_key=True, comment="唯一标识符")
    aid = Column(String(64), unique=True, comment="代理ID")
    upline_id = Column(String(64), comment="上级ID")
    provider = Column(String(64), comment="供应商")
    game_type = Column(String(64), comment="游戏类型")
    game_type_sub = Column(String(64), comment="游戏子类型")

    # 1X2玩法投注限额
    sb_sg_min_bet_1x2 = Column(DECIMAL(16, 2), comment="单场1X2玩法最小投注额")
    sb_sg_max_bet_1x2 = Column(DECIMAL(16, 2), comment="单场1X2玩法最大投注额")
    sb_mix_min_bet_1x2 = Column(DECIMAL(16, 2), comment="混合1X2玩法最小投注额")
    sb_mix_max_bet_1x2 = Column(DECIMAL(16, 2), comment="混合1X2玩法最大投注额")

    # 让球玩法投注限额
    sb_sg_min_bet_hdp = Column(DECIMAL(16, 2), comment="单场让球玩法最小投注额")
    sb_sg_max_bet_hdp = Column(DECIMAL(16, 2), comment="单场让球玩法最大投注额")
    sb_mix_min_bet_hdp = Column(DECIMAL(16, 2), comment="混合让球玩法最小投注额")
    sb_mix_max_bet_hdp = Column(DECIMAL(16, 2), comment="混合让球玩法最大投注额")

    # 大小球玩法投注限额
    sb_sg_min_bet_ou = Column(DECIMAL(16, 2), comment="单场大小球玩法最小投注额")
    sb_sg_max_bet_ou = Column(DECIMAL(16, 2), comment="单场大小球玩法最大投注额")
    sb_mix_min_bet_ou = Column(DECIMAL(16, 2), comment="混合大小球玩法最小投注额")
    sb_mix_max_bet_ou = Column(DECIMAL(16, 2), comment="混合大小球玩法最大投注额")

    # 其他玩法投注限额
    sb_sg_min_bet_other = Column(DECIMAL(16, 2), comment="单场其他玩法最小投注额")
    sb_sg_max_bet_other = Column(DECIMAL(16, 2), comment="单场其他玩法最大投注额")
    sb_mix_min_bet_other = Column(DECIMAL(16, 2), comment="混合其他玩法最小投注额")
    sb_mix_max_bet_other = Column(DECIMAL(16, 2), comment="混合其他玩法最大投注额")

    # 混合玩法总限额
    sb_mix_min_bet = Column(DECIMAL(16, 2), comment="混合玩法总最小投注额")
    sb_mix_max_bet = Column(DECIMAL(16, 2), comment="混合玩法总最大投注额")

    # 最大赢额和派彩
    sb_sg_max_win = Column(DECIMAL(16, 2), comment="单场最大赢额")
    sb_mix_max_win = Column(DECIMAL(16, 2), comment="混合玩法最大赢额")
    sb_sg_max_payout = Column(DECIMAL(20, 2), server_default='0.00', comment="单场最大派彩额")
    sb_mix_max_payout = Column(DECIMAL(20, 2), server_default='0.00', comment="混合玩法最大派彩额")
    sb_sg_max_exposure_per_match = Column(DECIMAL(20, 2), server_default='0.00', comment="单场比赛最大风险敞口")
    sb_sg_max_per_match = Column(DECIMAL(20, 2), server_default='0.00', comment="单场比赛最大下注")

    # 玩法启用开关
    enable_single_1x2 = Column(TINYINT(1), server_default='1', comment="启用单场1X2玩法 (0=禁用, 1=启用)")
    enable_handicap = Column(TINYINT(1), server_default='1', comment="启用让球玩法 (0=禁用, 1=启用)")
    enable_over_under = Column(TINYINT(1), server_default='1', comment="启用大小球玩法 (0=禁用, 1=启用)")
    enable_mix_parlay = Column(TINYINT(1), server_default='1', comment="启用混合玩法 (0=禁用, 1=启用)")

    # 混合玩法比赛数量限制
    sb_mix_min_matches_amt = Column(DECIMAL(16, 2), comment="混合玩法最小比赛数量")
    sb_mix_max_matches_amt = Column(DECIMAL(16, 2), comment="混合玩法最大比赛数量")
    mix_total_match_limit = Column(Integer, comment="混合单场比赛最大下注限制")
    mix_order_total_limit = Column(Integer, comment="混合单最多订单数")

    # 佣金设置
    commission_sg = Column(DECIMAL(16, 2), comment="单场佣金率")
    commission_mix = Column(DECIMAL(16, 2), comment="混合玩法佣金率")

    # 状态控制
    status = Column(TINYINT, comment="状态(0:禁用,1:启用)")
    sort = Column(Integer, comment="排序序号")

    __mapper_args__ = {
        "order_by": BaseSaasModel.create_time.desc(),
    }

    __table_args__ = (
        Index('idx_aid_unique', 'aid', unique=True),
    )

    @staticmethod
    def get_agent_config(aid: str = '0', tenant_id: str = None) -> Optional['AppSettingBet1x2Model']:
        """
        通过代理ID获取1x2下注参数配置
        :param aid: 代理ID
        :param tenant_id: 租户ID
        :return: 下注参数配置对象
        """
        query = db.session.query(AppSettingBet1x2Model).filter_by(
            aid=aid,
            del_flag=0,
            status=1
        )
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        obj = query.first()
        return obj

    def get_min_max_by_order_type(self, order_type: str) -> dict:
        """
        根据订单类型获取下注的最大和最小限制
        :param order_type: 订单类型 (参考 OrderType 类)
        :return: 字典包含 min_bet 和 max_bet
        """
        # 导入OrderType用于类型判断
        from app_server.model.OrderModel import OrderType

        # 订单类型映射到字段
        type_mapping = {
            # 单场1X2
            OrderType.SG_1X2: {
                'min': self.sb_sg_min_bet_1x2,
                'max': self.sb_sg_max_bet_1x2
            },
            # 单场让球(HDP)
            OrderType.SG_HDP: {
                'min': self.sb_sg_min_bet_hdp,
                'max': self.sb_sg_max_bet_hdp
            },
            # 混合让球
            OrderType.MIX_HDP: {
                'min': self.sb_mix_min_bet_hdp,
                'max': self.sb_mix_max_bet_hdp
            },
            # 单场大小球(O/U)
            OrderType.SG_OU: {
                'min': self.sb_sg_min_bet_ou,
                'max': self.sb_sg_max_bet_ou
            },
            # 混合大小球
            OrderType.MIX_OU: {
                'min': self.sb_mix_min_bet_ou,
                'max': self.sb_mix_max_bet_ou
            },
            # 单场其他玩法 (波胆、单双等)
            OrderType.SG_CS: {  # 波胆
                'min': self.sb_sg_min_bet_other,
                'max': self.sb_sg_max_bet_other
            },
            OrderType.SG_OE: {  # 单双
                'min': self.sb_sg_min_bet_other,
                'max': self.sb_sg_max_bet_other
            },
            OrderType.SG_BTTS: {  # Both/One/Neither
                'min': self.sb_sg_min_bet_other,
                'max': self.sb_sg_max_bet_other
            }
        }

        # 获取对应订单类型的限制
        limits = type_mapping.get(order_type)

        if limits is None:
            # 如果找不到对应的订单类型，返回默认值
            return {
                'min_bet': 0.0,
                'max_bet': 0.0,
                'error': f'Unknown order type: {order_type}'
            }

        return {
            'min_bet': float(limits['min']) if limits['min'] is not None else 0.0,
            'max_bet': float(limits['max']) if limits['max'] is not None else 0.0
        }

