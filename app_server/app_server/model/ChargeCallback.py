from app_server import db, app
from sqlalchemy import Column, String, DateTime, DECIMAL
from sqlalchemy.dialects.mysql import TINYINT
from app_server.utils.BaseModel import BaseModel


class ChargeCallbackStatus:
    Not = 0
    Confirm = 1
    Invalid = 2


# 充值回调表
class ChargeCallback(BaseModel):
    __tablename__ = 'm_charge_callback'
    TRANSACTION_ID = Column(String(32), index=True, nullable=False, server_default="", comment="第三方回调充值ID")
    CUSTOMER_BANK_CODE = Column(String(32), nullable=False, server_default="", comment="用户银行代号")
    CUSTOMER_BANK_ACCOUNT = Column(String(32), nullable=False, server_default="", comment="用户银行账号")
    RECEIVER_BANK_ACCOUNT = Column(String(32), index=True, nullable=False, server_default="", comment="收款方银行账号")
    TRANSACTION_DATETIME = Column(DateTime, comment="交易时间")
    AMOUNT = Column(DECIMAL(11, 2), nullable=False, server_default="0", comment="金额")
    SIGNATURE = Column(String(32), nullable=False, server_default="", comment="签名")

    USER_ID = Column(String(64), index=True, nullable=False, server_default="", comment="用户游戏ID")
    NICK_NAME = Column(String(64), nullable=False, server_default="", comment="用户昵称")
    CHARGE_ID = Column(String(64), index=True, nullable=False, server_default="", comment="充值订单ID")
    REMARK = Column(String(256), nullable=False, server_default="", comment="备注：申请说明")
    PICTURE = Column(String(256), nullable=False, server_default="", comment="充值图片名称")
    STATUS = Column(TINYINT, nullable=False, server_default="0", comment="充值状态: 0:未核验;1:已确认;2:作废")
    REASON = Column(String(256), nullable=False, server_default="", comment="充值不通过原因")


# db.create_all()
