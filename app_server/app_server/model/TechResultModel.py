from app_server import db, app
from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.mysql import SMALLINT, BIGINT, TINYINT
from sqlalchemy import func
from datetime import datetime, date, timedelta
from decimal import Decimal


TechTypeDef = {
    36: "进球",
    63: "助攻",
    39: "乌龙球",
    43: "黄牌",

}


class TechResult(db.Model):
    __tablename__ = 'tech_result'
    id = Column(BIGINT(20, unsigned=True), nullable=False, primary_key=True, comment="id")
    league = Column(String(128), nullable=False, server_default="", comment="联赛")
    region = Column(String(128), nullable=False, server_default="", comment="地区")
    host_team = Column(String(64), nullable=False, server_default="", comment="主队")
    guest_team = Column(String(64), nullable=False, server_default="", comment="客队")
    begin_time = Column(DateTime, comment="比赛开始时间")
    end_time = Column(DateTime, comment="比赛结束时间")
    half_host_score = Column(SMALLINT(unsigned=True), nullable=False, server_default="0", comment="半场主队分数")
    half_guest_score = Column(SMALLINT(unsigned=True), nullable=False, server_default="0", comment="半场客队分数")
    full_host_score = Column(SMALLINT(unsigned=True), nullable=False, server_default="0", comment="全场主队分数")
    full_guest_score = Column(SMALLINT(unsigned=True), nullable=False, server_default="0", comment="全场客队分数")
    host_team_icon = Column(String(64), nullable=False, server_default="", comment="主队icon")
    guest_team_icon = Column(String(64), nullable=False, server_default="", comment="客队icon")
    create_time = Column(DateTime, nullable=False, server_default=func.now(), comment="创建时间")
    update_time = Column(DateTime, onupdate=func.now(), comment="修改时间 ")
    status = Column(TINYINT(unsigned=True), nullable=False, server_default="0", comment="比赛状态:0未开始 1正在进行 2已结束")
    sta_desc = Column(String(64), nullable=False, server_default="", comment="比赛状态描述")

    def to_dict(self, include=None, exclude=None):
        result = {}
        for k in self.__table__.columns.keys():
            if include and k not in include:
                continue
            if exclude and k in exclude:
                continue
            value = getattr(self, k)
            if k == "begin_time" or k == "end_time" and value:
                value = value - timedelta(hours=1.5)
            if isinstance(value, datetime) or isinstance(value, date) or isinstance(value, Decimal):
                value = str(value)
            result[k] = value
        if self.status == 0 and self.begin_time:
            result['sta_desc'] = result["begin_time"][-5:]

        return result


class TechDetail(db.Model):
    __tablename__ = 'tech_detail'
    id = Column(BIGINT(20, unsigned=True), nullable=False, primary_key=True, comment="id")
    result_id = Column(BIGINT(20, unsigned=True), nullable=False, server_default="0", comment="result id")
    tech_type = Column(SMALLINT(unsigned=True), nullable=False, server_default="0", comment="技术细节类型")
    tech_type_str = Column(String(64), nullable=False, server_default="", comment="细节类型描述")
    minute = Column(SMALLINT(unsigned=True), nullable=False, server_default="0", comment="产生时间(分钟)")
    player_name = Column(String(64), nullable=False, server_default="", comment="队员名称")
    belong_team = Column(TINYINT(unsigned=True), nullable=False, server_default="0", comment="所属队伍: 1主队 2客队")
    phase = Column(TINYINT(unsigned=True), nullable=False, server_default="0", comment="阶段 1:上半 2:下半 3:加时")
    min_ex = Column(TINYINT(unsigned=True), nullable=False, server_default="0", comment="补时")
    host_score = Column(SMALLINT(unsigned=True), comment="主队分数")
    guest_score = Column(SMALLINT(unsigned=True), comment="客队分数")
    create_time = Column(DateTime, nullable=False, server_default=func.now(), comment="创建时间")
    update_time = Column(DateTime, onupdate=func.now(), comment="修改时间")

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
