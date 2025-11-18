from app_server import db, app
from sqlalchemy import Column, String, Integer
from sqlalchemy.dialects.mysql import TIMESTAMP
from datetime import datetime


class ContactFunc(db.Model):
    __tablename__ = 'm_contact_func'
    ID = Column(Integer, nullable=False, autoincrement=True, primary_key=True, comment="ID")
    TYPE = Column(String(32), comment="联系方式")
    CONTENT = Column(String(64), comment="联系详情")

    def to_dict(self):
        columns = self.__table__.columns.keys()
        result = {}
        for key in columns:
            value = getattr(self, key)
            result[key] = value
        return result

db.create_all()