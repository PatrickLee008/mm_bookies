from app_server import db, app
from sqlalchemy import Column, Integer, String, Table, ForeignKey, DateTime
from sqlalchemy.dialects.mysql import TIMESTAMP
from datetime import datetime
from sqlalchemy import func


class UploadedImage(db.Model):
    __tablename__ = 'm_up_images'
    ID = Column(Integer, autoincrement=True, primary_key=True, comment="图片ID")
    NAME = Column(String(128), comment="图片名称")
    ADDRESS = Column(String(256), comment="图片地址")
    CREATE_TIME = Column(TIMESTAMP, default=datetime.now, comment="创建时间")
    UPDATE_TIME = Column(TIMESTAMP, onupdate=datetime.now, comment="更新时间")

    def to_dict(self):
        columns = self.__table__.columns.keys()
        result = {}
        for key in columns:

            value = getattr(self, key)
            if key in ('CREATE_TIME', 'UPDATE_TIME'):
                value = str(value)
            result[key] = value
        return result

db.create_all()