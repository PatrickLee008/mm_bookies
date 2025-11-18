from app_server import db, app
from sqlalchemy import Column, Integer, String, Table, ForeignKey, DateTime
from sqlalchemy.dialects.mysql import TIMESTAMP
from datetime import datetime
from sqlalchemy import func


class Notice(db.Model):
    __tablename__ = 'm_notice'
    MNOTICE_ID = Column(String(64), primary_key=True, comment="公告ID")
    TITLE = Column(String(256), comment="公告标题 ")
    CONTENT = Column(String(2000), comment="公告内容")
    STATUS = Column(String(2), default="1", comment="状态(0：无效；1：有效)")
    CREATOR = Column(String(64), comment="创建人")
    CREATOR_TIME = Column(TIMESTAMP, default=datetime.now, comment="创建时间")
    UPDATOR = Column(String(64), comment="修改人")
    UPDATOR_TIME = Column(TIMESTAMP, onupdate=datetime.now, comment="更新时间")

    def to_dict(self):
        columns = self.__table__.columns.keys()
        result = {}
        for key in columns:

            value = getattr(self, key)
            if key in ('CREATOR_TIME', 'UPDATOR_TIME'):
                value = str(value)
            result[key] = value
        return result
