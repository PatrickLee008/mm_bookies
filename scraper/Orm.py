from decimal import Decimal
from typing import Optional
from sqlalchemy import create_engine, Column, String, DateTime, SmallInteger, Integer
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.mysql import TIMESTAMP, TINYINT, DATETIME, INTEGER, VARCHAR
from datetime import datetime, date
import redis
from sqlalchemy.pool import QueuePool

# alter table m_app_match modify column MATCH_DESC varchar(127);
# alter table m_app_match modify column REMARK varchar(127);
# 创建对象的基类:
Base = declarative_base()


# 定义Match对象:
class Match(Base):
    # 表的名字:
    __tablename__ = 'm_app_match'

    # 表的结构:
    ID = Column(String(20), primary_key=True, comment="比赛号:系统主机，用时间戳生成，MH201804240001")
    MATCH_ID = Column(String(40), comment="比赛ID（兼容历史代码与ID值一致）")
    MATCH_DESC = Column(String(127), comment="比赛描述")
    MATCH_TIME = Column(TIMESTAMP, comment="比赛时间")
    CLOSING_TIME = Column(TIMESTAMP, comment="封盘时间")
    CLOSING_STATE = Column(String(4), default="0", comment="封盘状态")
    COUNTRY = Column(String(64), comment="比赛盘")
    LEAGUE = Column(String(64), comment="联赛名称")
    REMARK = Column(String(127), comment="备注")
    CREATE_TIME = Column(TIMESTAMP, default=datetime.now, comment="创建时间")
    UPDATE_TIME = Column(TIMESTAMP, onupdate=datetime.now, comment="更新时间")
    HOST_TEAM = Column(String(64), comment="主队")
    GUEST_TEAM = Column(String(64), comment="客队")
    HOST_TEAM_RESULT = Column(String(4), comment="主队得分")
    GUEST_TEAM_RESULT = Column(String(4), comment="客队得分")
    IS_GAME_OVER = Column(String(2), default="0", comment="比赛是否结束:0否,1是")
    MATCH_WEB_ID = Column(String(20), comment="爬虫对应的网页ID")
    HOST_TEAM_ENG = Column(String(64), comment="主队英文名称")
    GUEST_TEAM_ENG = Column(String(64), comment="客队英文名称")
    MATCH_MD_TIME = Column(TIMESTAMP, comment="比赛时间(缅甸)")
    MANUAL_ON = Column(String(64), default="0", comment="是否切换到人工配置,0:否,1:是")
    hide = Column(String(2), default="0", comment="是否隐藏")
    exception = Column(TINYINT(3), nullable=False, default="0", comment="比赛异常状态：0正常，1可能异常，2确认异常")
    HIDE_REASON = Column(String(256), comment="隐藏原因")
    HIDE_CONFIRM = Column(String(2), comment="隐藏确认：0未确认，1已确认")
    HOST_TEAM_WEBID = Column(String(32), comment="主队ID")
    GUEST_TEAM_WEBID = Column(String(32), comment="客队ID")
    TENANT_ID = Column("TENANT_ID", String(64), default=10000, comment='租户ID')
    status = Column(String(10), default="1", comment="比赛状态：1:未开始，2:进行中，3:已结束，4:结算，0:取消")

    def to_dict(self):
        columns = self.__table__.columns.keys()
        result = {}
        for key in columns:
            value = getattr(self, key)
            if key in ('MATCH_TIME', 'CLOSING_TIME', 'CREATE_TIME', 'UPDATE_TIME', 'MATCH_MD_TIME'):
                value = str(value)
            result[key] = value
        return result

    def to_cache_dict(self):
        """
        返回用于Redis缓存的精简字段（仅包含前端和后端需要的字段）
        注意：HOST_TEAM_WEBID和GUEST_TEAM_WEBID仅在写入缓存时查询logo用，写入后应删除
        """
        return {
            'MATCH_ID': self.MATCH_ID,
            'LEAGUE': self.LEAGUE,
            'HOST_TEAM': self.HOST_TEAM,
            'GUEST_TEAM': self.GUEST_TEAM,
            'MATCH_TIME': str(self.MATCH_TIME) if self.MATCH_TIME else None,  # 后端计算时区转换必需
            'status': self.status,
            # 以下两个字段仅用于写缓存时查询logo，写入Redis前会被删除
            'HOST_TEAM_WEBID': self.HOST_TEAM_WEBID,
            'GUEST_TEAM_WEBID': self.GUEST_TEAM_WEBID,
        }


# 定义MatchAttr对象:
class MatchAttr(Base):
    # 表的名字:
    __tablename__ = 'm_app_match_attr'

    # 表的结构:
    ID = Column(String(40), primary_key=True, comment="比赛属性id  系统主机，用时间戳生成，MH201804240001")
    MATCH_ATTR_ID = Column(String(40), comment="比赛属性id（兼容历史代码与ID值一致）")
    MATCH_ATTR_DESC = Column(String(32), comment="比赛赔率属性描述")
    MATCH_ATTR_TYPE = Column(String(2), comment="赔率类型:1胜负(让球)2大小球3波胆")
    ODDS = Column(String(6), comment="输赢赔率(输赢和大小球时做主队和大球赔率)|波胆赔率")
    ODDS_GUEST = Column(String(6), comment="输赢和大小球时做客队和小球赔率  波胆不用")
    DRAW_BUNKO = Column(String(4), comment="平局胜负(0:+;1:-)")
    DRAW_ODDS = Column(String(6), comment="平局赔率（%）")
    MATCH_ID = Column(String(20), comment="比赛号")
    ODDS_HOST_TEAM_RESULT = Column(String(16), comment="比赛主队结果")
    ODDS_GUEST_TEAM_RESULT = Column(String(16), comment="比赛客队结果")
    CS_SCORE = Column(String(20), comment="波胆比分")
    CS_INDEX = Column(String(20), comment="波胆比分索引")
    REMARK = Column(String(64), comment="备注")
    CREATE_TIME = Column(TIMESTAMP, default=datetime.now, comment="创建时间")
    UPDATE_TIME = Column(TIMESTAMP, onupdate=datetime.now, comment="更新时间")
    LOSE_TEAM = Column(String(16), comment="让球方1主队,2客队")
    LOSE_BALL_NUM = Column(String(32), comment="胜负时：让球数/大小球时：球数")
    MATCH_WEB_ID = Column(String(20), comment="网页上爬取到的比赛id")
    TENANT_ID = Column("TENANT_ID", String(64), default=10000, comment='租户ID')

    def to_dict(self):
        columns = self.__table__.columns.keys()
        result = {}
        for key in columns:
            value = getattr(self, key)
            if key in ('UPDATE_TIME', 'CREATE_TIME'):
                value = str(value)
            result[key] = value
        return result

    def to_cache_dict(self):
        """
        返回用于Redis缓存的精简字段（仅包含前端需要的字段）
        """
        # 前端需要的核心字段
        return {
            'MATCH_ATTR_ID': self.MATCH_ATTR_ID,
            'MATCH_ATTR_TYPE': self.MATCH_ATTR_TYPE,
            'ODDS': self.ODDS,
            'ODDS_GUEST': self.ODDS_GUEST,
            'DRAW_BUNKO': self.DRAW_BUNKO,
            'DRAW_ODDS': self.DRAW_ODDS,
            'MATCH_ID': self.MATCH_ID,
            'ODDS_HOST_TEAM_RESULT': self.ODDS_HOST_TEAM_RESULT,
            'ODDS_GUEST_TEAM_RESULT': self.ODDS_GUEST_TEAM_RESULT,
            'CS_SCORE': self.CS_SCORE,
            'CS_INDEX': self.CS_INDEX,
            'LOSE_TEAM': self.LOSE_TEAM,
            'LOSE_BALL_NUM': self.LOSE_BALL_NUM,
            'MATCH_WEB_ID': self.MATCH_WEB_ID,
        }


class Result(Base):
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
            if key in ('MATCH_TIME', 'CREATE_TIME'):
                value = str(value)
            result[key] = value
        return result



# 记录联赛球队信息
class LeagueTteamScraper(Base):
    # 表的名字:
    __tablename__ = 'm_app_league_team_scraper'

    # 主键与基础信息
    id = Column(String(64), primary_key=True, comment="主键ID")
    league_id = Column(String(64), index=True, comment="所属联赛ID")
    league_name = Column(String(255), comment="联赛名称")

    # 球队信息
    name = Column(String(128), comment="爬虫球队名称")
    show_name = Column(String(128), comment="爬虫球队名称（前端显示名称）")
    web_id = Column(String(128), comment="爬虫球队ID")
    team_id = Column(String(64), index=True, comment="球队ID")
    team_name = Column(String(128), comment="球队名称")
    logo = Column(String(255), comment="球队图标URL")

    # 状态与排序
    status = Column(TINYINT, nullable=False, default='0', comment="状态(0:禁用,1:启用)")
    sort = Column(Integer, server_default='0', comment="排序序号")

    # 审计字段
    create_by_id = Column(String(64), comment="创建人")
    create_time = Column(DATETIME, default=datetime.now, comment="创建时间")
    update_by_id = Column(String(64), comment="更新人")
    update_time = Column(DATETIME, onupdate=datetime.now, comment="更新时间")
    remarks = Column(String(255), comment="备注信息")
    del_flag = Column(Integer, nullable=False, server_default='0', comment="删除标记")
    tenant_id = Column(String(64), index=True, default=10000, comment="租户ID")

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

    # 通过web_id获取球队信息
    @staticmethod
    def get_match_icon(web_id: str, session=None) -> Optional[str]:
        should_close = False
        if session is None:
            session = DBSession()
            should_close = True

        try:
            # 增加条件可能
            obj = session.query(LeagueTteamScraper).filter_by(web_id=web_id,status=1,del_flag=0).order_by(LeagueTteamScraper.sort.desc()).first()
            if obj and obj.logo:
                return obj.logo.strip()
            else:
                return None
        finally:
            if should_close:
                session.close()

    def get_match_team(web_id: str, session=None) -> Optional[str]:
        should_close = False
        if session is None:
            session = DBSession()
            should_close = True

        try:
            # 增加条件可能
            obj = session.query(LeagueTteamScraper).filter_by(web_id=web_id,status=1,del_flag=0).order_by(LeagueTteamScraper.sort.desc()).first()
            if obj:
                return obj
            else:
                return None
        finally:
            if should_close:
                session.close()

# 导入配置
from env_config import Config

# Redis连接
Redis = redis.StrictRedis(
    host=Config.REDIS_HOST,
    port=Config.REDIS_PORT,
    db=Config.REDIS_DB,
    decode_responses=Config.REDIS_DECODE_RESPONSES,
    password=Config.REDIS_PASSWORD
)

# 初始化数据库连接
engine = create_engine(
    Config.get_database_uri(),
    pool_size=Config.DB_POOL_SIZE,
    max_overflow=Config.DB_MAX_OVERFLOW,
    pool_timeout=Config.DB_POOL_TIMEOUT,
    pool_recycle=Config.DB_POOL_RECYCLE,
    pool_pre_ping=Config.DB_POOL_PRE_PING
)

# 创建DBSession类型
DBSession = sessionmaker(bind=engine)
Base.metadata.create_all(engine)
