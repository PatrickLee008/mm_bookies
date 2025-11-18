from app_server import db
from sqlalchemy import Column, String, DECIMAL, DateTime, func
from sqlalchemy.dialects.mysql import TINYINT, INTEGER, SMALLINT
from datetime import datetime, timedelta


class Digit3DStatus:
    NotOpened = 0
    Opened = 1
    Closed = 2
    Settled = 3


class Digital3D(db.Model):
    __tablename__ = 'm_digital_3d'
    ID = Column(INTEGER(unsigned=True), autoincrement=True, primary_key=True)
    STAGE = Column(String(40), nullable=False, server_default="", comment="期数")
    ODDS = Column(DECIMAL(5, 2), nullable=False, server_default='0', comment="赔率")
    STATUS = Column(TINYINT(unsigned=True), nullable=False, server_default="0", comment="状态:0:未开盘, 1:已开盘, 2:已封盘 3:已结算")
    OPEN_TIME = Column(DateTime, comment="开盘时间")
    CLOSE_TIME = Column(DateTime, comment="封盘时间")
    BET_NUM = Column(INTEGER(unsigned=True), nullable=False, server_default='0', comment='投注单量')
    BET_SUM = Column(INTEGER(unsigned=True), nullable=False, server_default='0', comment='投注总额')
    BENEFIT = Column(INTEGER, nullable=False, server_default='0', comment='盈利总额')
    RESULT = Column(SMALLINT(unsigned=True), nullable=False, server_default='0', comment='开奖结果')
    CREATE_TIME = Column(DateTime, nullable=False, comment="创建时间", server_default=func.now())
    UPDATE_TIME = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    CREATOR = Column(String(32), nullable=False, server_default="", comment="创建者")
    UPDATER = Column(String(32), nullable=False, server_default="", comment="更新者")
    REMARK = Column(String(64), nullable=False, server_default='', comment="备注")

    LIMIT_CODE = Column(TINYINT(unsigned=True), nullable=False, server_default='0', comment='总期数限额参数')
    LIMIT_NUM = Column(INTEGER(unsigned=True), nullable=False, server_default='0', comment='单数字限额')
    SINGLE_MIN = Column(INTEGER(unsigned=True), nullable=False, server_default='0', comment='单笔最小')
    SINGLE_MAX = Column(INTEGER(unsigned=True), nullable=False, server_default='0', comment='单笔最大')
    USER_MAX = Column(INTEGER(unsigned=True), nullable=False, server_default='0', comment='单用户最大')
    EX_LIMIT = Column(INTEGER(unsigned=True), nullable=False, server_default='0', comment='扩展限额')
    NUM_USER_LIMIT = Column(INTEGER(unsigned=True), nullable=False, server_default='0', comment='单用户单数字限额')

    def to_dict(self):
        columns = self.__table__.columns.keys()
        result = {}

        for key in columns:
            value = getattr(self, key)
            if key in {'CLOSE_TIME', 'OPEN_TIME'}:
                value -= timedelta(hours=1.5)
                value = (str(value))[0:16]
            if key == "ODDS":
                value = int(value)
            result[key] = value

        return result


#db.create_all()
