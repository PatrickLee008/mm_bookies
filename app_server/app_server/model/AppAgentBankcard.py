from app_server import db, app
from sqlalchemy import Column, String, DECIMAL, DateTime, Text, Integer, SmallInteger
from decimal import Decimal
import datetime


class AppAgentBankcard(db.Model):
    __tablename__ = 'm_app_agent_bankcard'

    id = Column(String(64), primary_key=True, comment='记录ID')
    aid = Column(String(64), comment='代理ID')
    rc_bank_code = Column(String(50), comment='银行代码')
    rc_bank_username = Column(String(255), comment='银行用户名')
    rc_bank_account = Column(String(100), comment='银行账号')
    rc_accept = Column(String(255), comment='接收方式')
    rc_network = Column(String(255), comment='网络类型')
    type = Column(String(255), comment='账户类型（All-全部，Deposit-充值，Withdraw-提现）')
    type_sub = Column(String(255), comment='子账户类型')
    balance = Column(DECIMAL(26, 6), comment='帐户总额')
    limit_balance = Column(DECIMAL(26, 6), comment='交易限额')
    limit_current = Column(DECIMAL(26, 6), comment='当前交易额度')
    reset_limit_type = Column(String(64), comment='限额重置类型')
    auto_type = Column(String(64), comment='自动处理类型')
    reset_date = Column(DateTime, comment='重置日期')
    status = Column(SmallInteger, comment='状态(0-禁用,1-启用)')
    create_time = Column(DateTime, comment='创建时间')
    create_by_id = Column(String(64), comment='创建人')
    update_time = Column(DateTime, comment='更新时间')
    update_by_id = Column(String(64), comment='更新人')
    remarks = Column(Text, comment='备注')
    del_flag = Column(Integer, default=0, comment='删除标记')
    tenant_id = Column(String(64), comment='租户ID')

    def to_dict(self):
        columns = self.__table__.columns.keys()
        result = {}
        for key in columns:
            value = getattr(self, key)
            if isinstance(value, Decimal):
                result[key] = str(value)  # 或 float(value) 如果你需要数字形式
            elif isinstance(value, datetime.datetime):
                result[key] = value.isoformat()  # 日期时间序列化为字符串
            else:
                result[key] = value
        return result

