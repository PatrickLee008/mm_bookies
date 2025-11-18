from app_server import db, app
from sqlalchemy import Column, String, Integer, SmallInteger , DateTime
from app_server.utils.BaseSaasModel import BaseSaasModel


# 会员银行卡信息
class AppMemberBank(BaseSaasModel):
    __tablename__ = 'm_app_member_bankcard'

    id = Column(String(64), primary_key=True, comment='记录ID')
    mb_id = Column(String(64), comment='会员ID')
    bank_code = Column(String(50), comment='银行代码')
    acc_name = Column(String(255), comment='账户名称')
    acc_number = Column(String(50), comment='账户号码')
    is_default = Column(SmallInteger, default=0, comment='默认卡')
    status = Column(SmallInteger, default=1, comment='状态(0-禁用,1-启用)')
    currency = Column(String(5), comment='货币代码')
    sort = Column(Integer, default=100, comment='排序序号')
    del_flag = Column(Integer, default=0, comment='删除标记')

    __mapper_args__ = {
        "order_by": BaseSaasModel.create_time.desc(),
    }

