
from app_server import db, app
from sqlalchemy import Column, Integer, String, Table, ForeignKey, DateTime
from sqlalchemy.dialects.mysql import TIMESTAMP
from datetime import datetime
from sqlalchemy import func
from app_server.utils.BaseSaasModel2 import BaseSaasModel2

class Match(BaseSaasModel2):
    __tablename__ = 'm_app_match'
    ID = Column(String(20), primary_key=True, comment="比赛号:系统主机，用时间戳生成，MH201804240001")
    MATCH_ID = Column(String(20), comment="比赛号:系统主机，用时间戳生成，MH201804240001")
    MATCH_DESC = Column(String(127), comment="比赛描述")
    MATCH_TIME = Column(TIMESTAMP, comment="比赛时间")
    CLOSING_TIME = Column(TIMESTAMP, comment="封盘时间")
    CLOSING_STATE = Column(String(4), comment="封盘状态")
    REMARK = Column(String(64), comment="备注")
    HOST_TEAM = Column(String(64), comment="主队")
    GUEST_TEAM = Column(String(64), comment="客队")
    HOST_TEAM_RESULT = Column(String(4), comment="主队得分")
    GUEST_TEAM_RESULT = Column(String(4), comment="客队得分")
    IS_GAME_OVER = Column(String(2), comment="比赛是否结束:0否,1是")
    MATCH_WEB_ID = Column(String(20), comment="爬虫对应的网页ID")
    HOST_TEAM_ENG = Column(String(64), comment="主队英文名称")
    GUEST_TEAM_ENG = Column(String(64), comment="客队英文名称")
    LEAGUE = Column(String(64), comment="联赛")
    MATCH_MD_TIME = Column(TIMESTAMP, comment="比赛时间(缅甸)")
    MANUAL_ON = Column(String(64), comment="是否切换到人工配置,0:否,1:是")
    hide = Column(String(2), comment="是否隐藏")

    __mapper_args__ = {
        "order_by": MATCH_ID.desc(),
    }

    def to_dict(self):
        columns = self.__table__.columns.keys()
        result = {}
        # attrs = MatchAttr.query.filter_by(MATCH_ID=self.MATCH_ID).all()
        # result['ATTR'] = [attr.to_dict() for attr in attrs]
        for key in columns:

            value = getattr(self, key)
            if key in ('MATCH_TIME', 'CLOSING_TIME', 'CREATE_TIME', 'UPDATE_TIME', 'MATCH_MD_TIME'):
                value = str(value)
            result[key] = value
        return result


class MatchAttr(db.Model):
    __tablename__ = 'm_app_match_attr'
    ID = Column(String(20), primary_key=True, comment="比赛号:系统主机，用时间戳生成，MH201804240001")
    MATCH_ATTR_ID = Column(String(40), comment="比赛属性id  系统主机，用时间戳生成，MH201804240001")
    MATCH_ATTR_DESC = Column(String(32), comment="比赛赔率属性描述")
    MATCH_ATTR_TYPE = Column(String(2), comment="赔率类型:1胜负(让球)2大小球3波胆")
    ODDS = Column(String(6), comment="输赢赔率(输赢和大小球时做主队和大球赔率)|波胆赔率")
    ODDS_GUEST = Column(String(6), comment="输赢和大小球时做客队和小球赔率  波胆不用")
    DRAW_BUNKO = Column(String(4), comment="平局胜负(0:+;1:-)")
    DRAW_ODDS = Column(String(6), comment="平局赔率（%）")
    MATCH_ID = Column(String(20), comment="比赛号")
    ODDS_HOST_TEAM_RESULT = Column(String(16), comment="比赛主队结果")
    ODDS_GUEST_TEAM_RESULT = Column(String(16), comment="比赛客队结果")
    REMARK = Column(String(64), comment="备注")
    CREATE_TIME = Column(TIMESTAMP, default=datetime.now, comment="创建时间")
    UPDATE_TIME = Column(TIMESTAMP, onupdate=datetime.now, comment="更新时间")
    LOSE_TEAM = Column(String(16), comment="让球方1主队,2客队")
    LOSE_BALL_NUM = Column(String(32), comment="胜负时：让球数/大小球时：球数")
    MATCH_WEB_ID = Column(String(20), comment="网页上爬取到的比赛id")

    def to_dict(self):
        columns = self.__table__.columns.keys()
        result = {}
        for key in columns:

            value = getattr(self, key)
            if key in ('UPDATE_TIME', 'CREATE_TIME'):
                value = str(value)
            result[key] = value
        return result


# 定义MatchAttr对象:
class VipMatchAttr(db.Model):
    # 表的名字:
    __tablename__ = 'm_app_match_attr_vip'
    # 表的结构:
    MATCH_ATTR_ID = Column(String(40), primary_key=True, comment="比赛属性id  系统主机，用时间戳生成，MH201804240001")
    MATCH_ATTR_DESC = Column(String(32), comment="比赛赔率属性描述")
    MATCH_ATTR_TYPE = Column(String(2), comment="赔率类型:1胜负(让球)2大小球3波胆")
    ODDS = Column(String(4), comment="输赢赔率(输赢和大小球时做主队和大球赔率)|波胆赔率")
    ODDS_GUEST = Column(String(4), comment="输赢和大小球时做客队和小球赔率  波胆不用")
    DRAW_BUNKO = Column(String(4), comment="平局胜负(0:+;1:-)")
    DRAW_ODDS = Column(String(4), comment="平局赔率（%）")
    MATCH_ID = Column(String(20), comment="比赛号")
    ODDS_HOST_TEAM_RESULT = Column(String(16), comment="比赛主队结果")
    ODDS_GUEST_TEAM_RESULT = Column(String(16), comment="比赛客队结果")
    REMARK = Column(String(64), comment="备注")
    CREATE_TIME = Column(TIMESTAMP, default=datetime.now, comment="创建时间")
    UPDATE_TIME = Column(TIMESTAMP, onupdate=datetime.now, comment="更新时间")
    LOSE_TEAM = Column(String(16), comment="让球方1主队,2客队")
    LOSE_BALL_NUM = Column(String(32), comment="胜负时：让球数/大小球时：球数")
    MATCH_WEB_ID = Column(String(20), comment="网页上爬取到的比赛id")

    def to_dict(self):
        columns = self.__table__.columns.keys()
        result = {}
        for key in columns:
            value = getattr(self, key)
            if key in ('UPDATE_TIME', 'CREATE_TIME'):
                value = str(value)
            result[key] = value
        return result
