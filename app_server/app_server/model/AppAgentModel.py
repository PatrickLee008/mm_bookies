from app_server import db, app
from sqlalchemy import Column, String, DECIMAL, DateTime, Text, Integer, SmallInteger
from decimal import Decimal
import datetime

from app_server.utils.BaseSaasModel import BaseSaasModel


class AppAgent(BaseSaasModel):
    __tablename__ = 'm_app_agent'

    # 主键与基础信息
    id = Column(String(64), primary_key=True, comment="代理ID")
    agent_name = Column(String(64), nullable=False, comment="代理姓名/昵称")
    agent_account = Column(String(64), comment="代理绑定默认的卡号")

    # 代理层级关系
    agent_lvl = Column(String(64), nullable=False, server_default='agent', comment="代理等级（house/manager/master/agent）")
    agent_pt = Column(String(64), server_default='0.0', comment="代理分润比例（如0.3表示30%）")
    upline_id = Column(String(64), index=True, comment="上级代理ID（空值表示顶级代理）")

    # 财务信息
    balance = Column(DECIMAL(15, 2), nullable=False, server_default='0.00', comment="账户可提现余额")

    # 关联信息
    mn_id = Column(String(255), comment="关联的管理员ID")

    # 配置信息
    auto_deposit = Column(Integer, nullable=False, server_default='0', comment="是否支持自助充值（0-否，1-是）")

    # 状态控制
    status = Column(String(10), nullable=False, server_default='1', comment="状态: 0-停用, 1-启用")
    sort = Column(Integer, server_default='0', comment="排序序号")

    __mapper_args__ = {
        "order_by": sort.asc(),
    }

