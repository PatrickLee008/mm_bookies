from app_server import db
from sqlalchemy import Column, String, Integer, Boolean, Text, Numeric, SmallInteger, DateTime
from sqlalchemy.dialects.mysql import BIGINT
from datetime import datetime, date
from decimal import Decimal

from app_server.utils.Kits import Kits


# 多租户模式下的model基类
class BaseSaasModel(db.Model):
    __abstract__ = True

    # sort = Column("sort", Integer, default=100, comment='排序序号')
    create_by_id = Column("create_by_id", String(32), comment='创建人')
    create_time = Column("create_time", DateTime, default=datetime.now, comment='创建时间')
    update_by_id = Column("update_by_id", String(32), comment='更新人')
    update_time = Column("update_time", DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    remarks = Column("remarks", String(500), comment='备注信息')
    del_flag = Column("del_flag", Integer, default=0, comment='删除标记')
    tenant_id = Column("tenant_id", String(64), default=10000, comment='租户ID')

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


    # 生成ID
    @staticmethod
    def generate_id():
        return Kits.generate_uuid()