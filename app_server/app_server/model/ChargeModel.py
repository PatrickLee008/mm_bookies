from app_server import db, app
from sqlalchemy import Column, String, Integer, Text
from sqlalchemy.dialects.mysql import TIMESTAMP, DATETIME, DECIMAL
from datetime import datetime
from app_server.utils.BaseSaasModel import BaseSaasModel


class RechargePayType:
    AUTO = "AUTO"  # 自动充值
    MANUAL = "MANUAL"  # 手动


class RechargeChargeType:
    USER = "USER"  # 用户
    AGENT = "AGENT"  # 代理


class Charge(BaseSaasModel):
    __tablename__ = 'm_app_recharge'

    # 主键与基础信息
    id = Column(String(64), primary_key=True, comment="唯一标识符")
    aid = Column(String(64), index=True, comment="代理ID")
    trade_no = Column(String(64), unique=True, comment="订单编号")
    out_trade_no = Column(String(64), comment="第三方交易订单号")

    # 支付信息
    pay_type = Column(String(50), nullable=False, server_default='MANUAL', comment="充值方式（KBZ，KBZ-AUTO，MANUAL）")
    charge_type = Column(String(10), nullable=False, server_default='USER', comment="充值类型（USER、AGENT）")
    amount = Column(DECIMAL(65, 0), nullable=False, server_default='0', comment="存款金额")

    # 会员信息
    mb_id = Column(String(36), index=True, comment="会员ID")
    mb_username = Column(String(64), nullable=False, server_default='', comment="会员账号")
    mb_nickname = Column(String(64), comment="会员昵称")
    mb_bank_code = Column(String(50), comment="会员银行代码")
    mb_acc_name = Column(String(255), comment="会员账户名")
    mb_acc_number = Column(String(50), comment="会员账号")

    # 代理/管理员信息
    mn_id = Column(String(64), comment="管理员ID")
    mn_name = Column(String(64), comment="管理员名称")
    mn_username = Column(String(64), comment="管理员用户名")
    mn_add_name = Column(String(255), comment="操作人姓名（后台新增方式）")

    # 收款账户信息
    rc_id = Column(String(64), comment="收款账户ID")
    rc_bank_code = Column(String(50), comment="收款银行代码")
    rc_acc_name = Column(String(255), comment="收款账户名")
    rc_acc_number = Column(String(50), comment="收款账号")

    # 凭证信息
    slip = Column(String(255), comment="存款凭证/回执单")
    slip_pic = Column(String(255), comment="凭证图片")

    # 时间信息
    confirm_time = Column(DATETIME, comment="确认时间")
    process_time = Column(DATETIME, comment="处理时间")
    refund_time = Column(DATETIME, comment="退款时间")

    # 状态与日志
    callback_status = Column(Integer, nullable=False, server_default='0',
                             comment="回调状态：0无须回调，1待回调，2已回调处理")
    callback_log = Column(Text, comment="回调日志")
    order_log = Column(Text, comment="订单日志")
    status = Column(String(20), nullable=False, server_default='new',
                    comment="充值状态：new,processing,verify,reject,completed,failed,refund")

    # 优惠信息
    mb_pro_id = Column(Integer, comment="会员优惠券ID")

    __mapper_args__ = {
        "order_by": BaseSaasModel.create_time.desc(),
    }


db.create_all()
