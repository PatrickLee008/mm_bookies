from app_server import db
from sqlalchemy import Column, String, Integer, Boolean, Text, Numeric, SmallInteger, DateTime
from sqlalchemy.dialects.mysql import BIGINT
from datetime import datetime, date
from decimal import Decimal


# 多租户模式下的model基类（大写字段，临时过渡）
class BaseSaasModel2(db.Model):
    __abstract__ = True

    SORT = Column("SORT", Integer, default=100, comment='排序序号')
    CREATE_BY_ID = Column("CREATE_BY_ID", String(32), comment='创建人')
    CREATE_TIME = Column("CREATE_TIME", DateTime, default=datetime.now, comment='创建时间')
    UPDATE_BY_ID = Column("UPDATE_BY_ID", String(32), comment='更新人')
    UPDATE_TIME = Column("UPDATE_TIME", DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    REMARKS = Column("REMARKS", String(500), comment='备注信息')
    DEL_FLAG = Column("DEL_FLAG", Integer, default=0, comment='删除标记')
    TENANT_ID = Column("TENANT_ID", String(64), default=10000, comment='租户ID')

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
            result[k] = value

        return result

    def set_field(self, data):
        for key in self.__table__.columns.keys():
            if key in data:
                value = data[key]
                if value == "0" or value == "1":
                    value = int(value)
                setattr(self, key, value)


