from app_server import db, app
from sqlalchemy import Column, String, Integer
from sqlalchemy.dialects.mysql import TIMESTAMP
import datetime


class MDict(db.Model):
    __tablename__ = 'm_dict'
    MDICT_ID = Column(String(32), nullable=False, primary_key=True)
    NAME = Column(String(256), comment="名称")
    TYPE = Column(String(64), comment="类型")
    CODE = Column(String(64), comment="编码")
    TITLE = Column(String(64), comment="标题")
    CONTENT = Column(String(2000), comment="控牌操作，1控牌有效，0控牌无效")
    URL = Column(String(256), comment="链接地址")
    IMAGE_URL = Column(String(256), comment="图片地址")
    REMARK = Column(String(255), comment="描述")
    CREATOR = Column(String(64), comment="创建人")
    CREATOR_TIME = Column(TIMESTAMP, default=datetime.datetime.now)
    UPDATOR = Column(String(64), comment="修改人")
    UPDATOR_TIME = Column(TIMESTAMP, onupdate=datetime.datetime.now)

    def to_dict(self):
        columns = self.__table__.columns.keys()
        result = {}
        for key in columns:

            value = getattr(self, key)
            if key in {'CREATOR_TIME', 'UPDATOR_TIME'}:
                value = str(value)
            result[key] = value
        return result
