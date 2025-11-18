from app_server import db, app
from sqlalchemy import Column, String, Integer, SmallInteger, DateTime, Text
from sqlalchemy.dialects.mysql import TIMESTAMP
from datetime import datetime


# 银行代码表
class AppBankCode(db.Model):
    __tablename__ = 'm_app_bank_code'

    id = Column(String(64), primary_key=True, comment='记录ID')
    code = Column(String(50), comment='银行代码')
    name = Column(String(100), comment='银行名称')
    img_icon = Column(String(255), nullable=True, comment='图标URL')
    code_verify = Column(Text, nullable=True, comment='验证码规则')
    type = Column(String(50), nullable=True, comment='银行类型')
    status = Column(SmallInteger, default=1, comment='状态(0-禁用,1-启用)')
    sort = Column(Integer, nullable=True, comment='排序序号')
    create_by_id = Column(String(64), comment='创建人')
    create_time = Column(DateTime, default=datetime.now, comment='创建时间')
    update_by_id = Column(String(64), nullable=True, comment='更新人')
    update_time = Column(DateTime, nullable=True, onupdate=datetime.now, comment='更新时间')
    remarks = Column(String(255), nullable=True, comment='备注信息')
    del_flag = Column(Integer, default=0, comment='删除标记')
    tenant_id = Column(String(64), default=10000, comment='租户ID')

    def to_dict(self):
        columns = self.__table__.columns.keys()
        result = {}
        for key in columns:
            value = getattr(self, key)
            result[key] = value
        return result


# 创建数据库表
db.create_all()
