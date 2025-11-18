from app_server import db, app
from sqlalchemy import Column, String, Boolean, Integer, Text, DECIMAL
from sqlalchemy.dialects.mysql import TIMESTAMP, DATETIME, TINYINT
from datetime import datetime, date
from decimal import Decimal
from app_server.utils.BaseSaasModel import BaseSaasModel


class StatusMap:
    Pending = 0
    Success = 1
    Rejected = 2
    # New = "new"  # 新订单
    # Processing = "processing"  # 处理中
    # Verify = "verify"  # 待確認
    # Reject = "reject"  # 拒绝
    # Completed = "completed"  # 成功
    # Failed = "failed"  # 失败
    # Refund = "refund"  # 冲回


class StatusLabelMap:
    Pending = "Pending"
    Success = "Success"
    Rejected = "Rejected"
    New = "New"  # 新订单，未成功提交到接口
    # Processing = "processing"  # 处理中
    # Verify = "verify"  # 待確認
    # Reject = "reject"  # 拒绝
    # Completed = "completed"  # 成功
    Failed = "Failed"  # 失败
    # Refund = "refund"  # 冲回


# 玩家充值申请表
class ChargeApply(BaseSaasModel):
    __tablename__ = 'm_app_recharge_apply'

    id = Column(String(64), nullable=False, primary_key=True, comment="充值申请ID")
    aid = Column(String(64), nullable=True, comment="会员所属代理ID")
    recharge_id = Column(String(64), nullable=False, server_default='', comment="当充值通过时,对应的充值ID")
    mb_id = Column(String(64), nullable=False, server_default='', comment="会员ID")
    mb_nickname = Column(String(64), nullable=False, server_default='', comment="会员昵称")
    mb_username = Column(String(64), nullable=False, server_default='', comment="会员账号")
    mb_bank_code = Column(String(50), nullable=False, server_default='', comment="会员银行代码")
    mb_acc_name = Column(String(255), nullable=False, server_default='', comment="会员账户名")
    mb_acc_number = Column(String(50), nullable=False, server_default='', comment="会员账号")
    charge_name = Column(String(255), nullable=False, server_default='SYSTEM', comment="上分人员：SYSTEM(系统自动上分)")
    charge_status = Column(Integer, nullable=False, server_default='0',
                           comment="上分状态：-1无须上分，0创建，1待上分，2已上分")
    money = Column(DECIMAL(16, 0), nullable=False, server_default='0.00', comment="金额")
    remark = Column(String(256), nullable=False, server_default='', comment="备注：申请说明")
    picture = Column(String(256), nullable=False, server_default='', comment="充值图片名称")
    fail_reason = Column(String(256), nullable=False, server_default='', comment="充值不通过原因")
    charge_way = Column(TINYINT, nullable=False, server_default='0', comment="充值途径,0:自动充值,1:手动充值")
    pay_channel = Column(String(32), comment="支付通道")
    out_trade_no = Column(String(64), nullable=False, server_default='', comment="第三方回调充值ID")
    out_order_id = Column(String(64), comment="支付中心订单ID")
    callback_status = Column(Integer, nullable=False, server_default='0',
                             comment="回调状态：0无须回调，1待回调，2已回调处理")
    callback_time = Column(DATETIME, comment="回调时间")
    callback_log = Column(Text, comment="回调日志")
    receive_bank_code = Column(String(64), comment="收款银行")
    receive_account = Column(String(64), comment="收款卡")
    receive_account_name = Column(String(64), comment="收款卡名")

    refund_time = Column(DATETIME, comment="退款时间")
    refund_money = Column(DECIMAL(16, 0), server_default='0', comment="退款金额")
    status = Column(String(20), nullable=False, server_default='new',
                    comment="充值状态：new => 新订单、processing => 处理中、verify => 待確認、reject => 拒绝、completed => 成功、failed => 失败、refund => 冲回")
    expire_time = Column(DATETIME, comment="超时时间")

    __mapper_args__ = {
        "order_by": BaseSaasModel.create_time.desc(),
    }

    def to_dict(self, include=None, exclude=None):
        result = {}
        for k in self.__table__.columns.keys():
            if include and k not in include:
                continue
            if exclude and k in exclude:
                continue
            value = getattr(self, k)
            if isinstance(value, datetime) or isinstance(value, date) or isinstance(value, Decimal):
                value = str(value)
            if k == "picture":
                value = "%s%s" % ("static/img/charge_pics/", value) if value else ""
            result[k] = value

        return result


db.create_all()
