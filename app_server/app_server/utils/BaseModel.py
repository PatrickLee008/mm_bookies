from app_server import db
from sqlalchemy import Column, DateTime, func
from sqlalchemy.dialects.mysql import BIGINT
from datetime import datetime, date
from decimal import Decimal


class BaseModel(db.Model):
    __abstract__ = True
    ID = Column(BIGINT(20, unsigned=True), autoincrement=True, nullable=False, primary_key=True, comment="id")
    CREATE_TIME = Column(DateTime, nullable=False, server_default=func.now(), comment="创建时间")
    UPDATE_TIME = Column(DateTime, onupdate=func.now(), comment="修改时间 ")

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


