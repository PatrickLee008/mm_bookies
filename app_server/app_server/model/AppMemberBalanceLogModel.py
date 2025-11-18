from app_server import db, app
from sqlalchemy import Column, String, Integer, Text
from sqlalchemy.dialects.mysql import DATETIME, DECIMAL, TINYINT
from datetime import datetime
from typing import Optional

from app_server.utils.BaseSaasModel import BaseSaasModel


class TransactionType:
    """
    交易类型
    """
    Deposit = "Deposit"               # 存款
    Withdraw = "Withdraw"             # 提款
    Transfer = "Transfer"             # 转账
    Reward = "Reward"                 # 奖励
    Refund = "Refund"                 # 退款
    Bonus = "Bonus"                   # 红利
    Settlement = "Settlement"         # 结算
    Adjustment = "Adjustment"         # 调整（变动）
    Fee = "Fee"                       # 手续费
    Commission = "Commission"         # 佣金
    Promotion = "Promotion"           # 促销活动
    Exchange = "Exchange"             # 兑换
    CouponRedemption = "CouponRedemption"  # 优惠券兑换
    Other = "Other"                   # 其他
    Void = "Void"                     # 作废交易
    Formal = "Formal"                 # 正式交易
    NoneFormal = "NoneFormal"         # 非正式交易
    FundsAdjustments = "FundsAdjustments"  # 资金调整
    Order = "Order"                   # 下注

class TransactionMap:
    """
    交易Source Target类型
    """
    System = "System"         # 系统钱包
    Ewallet = "Ewallet"       # 电子钱包
    ProWallet = "ProWallet"   # 专业钱包
    Provider = "Provider"     # 提供商
    Merchant = "Merchant"     # 商户

# 会员余额日志模型
class AppMemberBalanceLog(BaseSaasModel):
    __tablename__ = 'm_app_member_balancelog'

    # 主键与交易标识
    id = Column(String(64), primary_key=True, comment="交易流水号")
    sn = Column(String(64), unique=True, comment="业务流水号")

    # 交易类型信息
    type = Column(String(64), nullable=False, comment="日志类型（投注、充值、提现）")
    type_sub = Column(String(64), comment="子类型（具体业务表类型）")
    type_sub_data_id = Column(String(64), comment="子类型数据ID")

    # 关联方信息
    aid = Column(String(64), index=True, comment="代理ID")
    pro_id = Column(String(64), comment="优惠券ID")
    bet_id = Column(String(64), comment="下注ID")

    # 会员信息
    mb_id = Column(String(64), index=True, comment="会员ID")
    mb_username = Column(String(64), comment="会员用户名")
    mb_rid = Column(String(64), comment="推荐人ID")

    # 金额信息（使用DECIMAL替代FLOAT）
    money = Column(DECIMAL(26, 6), nullable=False, server_default='0.000000', comment="交易金额")
    start_balance = Column(DECIMAL(26, 6), nullable=False, server_default='0.000000', comment="交易前余额")
    end_balance = Column(DECIMAL(26, 6), nullable=False, server_default='0.000000', comment="交易后余额")

    # 资金流向
    source = Column(String(64), comment="资金来源")
    source_sub = Column(String(64), comment="资金来源子类型")
    target = Column(String(64), comment="资金去向")
    target_sub = Column(String(64), comment="资金去向子类型")

    # 商户信息
    mc_sn = Column(String(64), comment="商户流水号")
    mc_name = Column(String(64), comment="商户名称")

    # 操作人信息
    mn_id = Column(String(64), comment="会员操作人ID")
    mn_username = Column(String(50), comment="会员操作人用户名")

    # 状态与备注
    status = Column(TINYINT, nullable=False, server_default="1", comment="状态: 0-无效，1-有效")
    source_status = Column(TINYINT, nullable=False, server_default="0", comment="原数据状态: 0: 请求中,1: 成功,2: 拒绝")

    __mapper_args__ = {
        "order_by": BaseSaasModel.create_time.desc(),
    }

