from app_server import db
from sqlalchemy import Column, String, func, DateTime, Boolean
from sqlalchemy.dialects.mysql import INTEGER, SMALLINT


class WithDrawGroup(db.Model):
    __tablename__ = 'm_withdrawal_group'
    ID = Column(INTEGER(unsigned=True), autoincrement=True, primary_key=True)
    GROUP_NAME = Column(String(255), server_default="", nullable=False, comment="组名称")
    CREATOR = Column(String(32), nullable=False, server_default="", comment="创建人")
    CREATE_TIME = Column(DateTime, nullable=False, server_default=func.now())
    UPDATE_TIME = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    REMARK = Column(String(255), nullable=False, server_default="", comment="备注")

    MAX_HANDLE = Column(SMALLINT(unsigned=True), nullable=False, server_default="10", comment="最大处理数量")
    NOW_HANDLE = Column(SMALLINT(unsigned=True), nullable=False, server_default="0", comment="当前处理数量")
    HANDLE_ON = Column(Boolean, nullable=False, server_default="1", comment="处理开关: 0:关 1:开")

    def to_dict(self):
        columns = self.__table__.columns.keys()
        result = {}
        for key in columns:

            value = getattr(self, key)
            if key in {'CREATE_TIME', 'UPDATE_TIME'}:
                value = str(value)
            result[key] = value
        return result


db.create_all()
