from app_server import db, app
from sqlalchemy import Column, String, DECIMAL, DateTime, Text, Integer
from decimal import Decimal
import datetime

from app_server.utils.BaseSaasModel import BaseSaasModel


class AppAgentBalancelog(BaseSaasModel):
    """
    代理余额流水表
    对应数据库表: m_app_agent_balancelog
    用于记录代理/平台的资金变动（包括Promotion结算退回等）
    """
    __tablename__ = 'm_app_agent_balancelog'

    # 主键与基础信息
    id = Column(String(64), primary_key=True, comment="流水ID")

    # 交易时间
    trx_datetime = Column(DateTime, nullable=False, default=datetime.datetime.now, comment="交易时间")

    # 交易类型
    trx_type = Column(String(64), nullable=False, comment="交易类型")

    # 交易金额
    trx_amount = Column(DECIMAL(15, 2), nullable=False, default=Decimal('0.00'), comment="交易金额")

    # 交易前余额
    trx_before = Column(DECIMAL(15, 2), nullable=False, default=Decimal('0.00'), comment="交易前余额")

    # 交易后余额
    trx_after = Column(DECIMAL(15, 2), nullable=False, default=Decimal('0.00'), comment="交易后余额")

    # 关联交易ID
    trx_ref_id = Column(String(64), comment="关联交易ID")

    # 关联凭证图片
    trx_ref_image = Column(String(255), comment="关联凭证图片")

    # 交易备注
    trx_note = Column(Text, comment="交易备注")

    # 交易状态
    trx_status = Column(String(20), comment="交易状态")

    # 代理ID
    agent_id = Column(String(64), nullable=False, index=True, comment="代理ID")

    # 上级ID
    upline_id = Column(String(64), index=True, comment="上级ID")

    # 玩家ID
    player_id = Column(String(64), index=True, comment="玩家ID")

    # 提交人
    submit_by = Column(String(64), comment="提交人")

    # 确认人
    confirm_by = Column(String(64), comment="确认人")

    # 交易子类型
    trx_type_sub = Column(String(64), comment="交易子类型")

    # 银行账户
    trx_b_acc = Column(String(64), comment="银行账户")

    # 银行代码
    trx_b_code = Column(String(20), comment="银行代码")

    # 银行名称
    trx_b_name = Column(String(100), comment="银行名称")

    # 银行账户类型
    trx_b_type = Column(String(20), comment="银行账户类型")

    # 网络地址
    trx_nw_ads = Column(String(255), comment="网络地址")

    # 状态
    status = Column(Integer, nullable=False, default=1, comment="状态: 0-无效, 1-有效")

    def __repr__(self):
        return f"<AppAgentBalancelog(id='{self.id}', agent_id='{self.agent_id}', trx_type='{self.trx_type}', trx_amount={self.trx_amount})>"
