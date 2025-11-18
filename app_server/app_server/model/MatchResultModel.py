from app_server import db, app
from sqlalchemy import Column, Integer, String, Table, ForeignKey, DateTime, SmallInteger
from sqlalchemy.dialects.mysql import TIMESTAMP
from datetime import datetime
from sqlalchemy import func


class Result(db.Model):
    # 表的名字:
    __tablename__ = 'result'
    # 表的结构:
    MATCH_ID = Column(String(20), primary_key=True)
    LEAGUE_NAME = Column(String(128))
    HOST_TEAM = Column(String(64))
    GUEST_TEAM = Column(String(64))
    MATCH_TIME = Column(DateTime)
    HALF_HOST_SCORE = Column(SmallInteger)
    HALF_GUEST_SCORE = Column(SmallInteger)
    FULL_HOST_SCORE = Column(SmallInteger)
    FULL_GUEST_SCORE = Column(SmallInteger)
    CREATE_TIME = Column(DateTime, default=datetime.now)

    def to_dict(self):
        columns = self.__table__.columns.keys()
        result = {}
        for key in columns:
            value = getattr(self, key)
            if key in {'CREATE_TIME', "MATCH_TIME"}:
                value = str(value)
            result[key] = value
        return result
