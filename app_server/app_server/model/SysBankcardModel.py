from app_server import db, app
from sqlalchemy import Column, String, Boolean, DECIMAL, INTEGER
from app_server.utils.BaseModel import BaseModel


class SysBankcardStatus:
    Disable = 0
    Enable = 1


class SysBankcard(BaseModel):
    __tablename__ = 'm_sys_bankcard'
    NAME = Column(String(32), nullable=False, server_default="", comment="账号名称")
    ACCOUNT = Column(String(32), index=True, nullable=False, server_default="", comment="入账账号")
    BANK_CODE = Column(String(32), nullable=False, server_default="", comment="银行代号")
    INCOME = Column(DECIMAL(11, 2), nullable=False, server_default="0", comment="总金额")
    DAILY_LIMIT = Column(DECIMAL(11, 2), nullable=False, server_default="0", comment="每日金额限制")
    ENABLE = Column(Boolean, nullable=False, server_default="0", comment="充值状态: 0:停用;1:启用;")
    VISIBLE = Column(Boolean, nullable=False, server_default="0", comment="可见状态: 0:不可见;1:课件;")
    RANK = Column(INTEGER, nullable=False, server_default="0", comment="轮换顺序")
    REMARK = Column(String(256), nullable=False, server_default="", comment="充值不通过原因")


#db.create_all()
