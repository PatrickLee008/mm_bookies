from app_server import db, app
from sqlalchemy import Column, String, Integer, Text
from sqlalchemy.dialects.mysql import DATETIME, DECIMAL, TINYINT
from datetime import datetime
from typing import Optional

from app_server.utils.BaseSaasModel import BaseSaasModel


# 球队映射表
class LeagueTeamScraperModel(BaseSaasModel):
    __tablename__ = 'm_app_league_team_scraper'

    # 主键与基础信息
    id = Column(String(64), primary_key=True, comment="主键ID")
    league_id = Column(String(64), index=True, comment="所属联赛ID")
    league_name = Column(String(255), comment="联赛名称")

    # 球队标识信息
    name = Column(String(128), comment="爬虫原始球队名称")
    web_id = Column(String(128), unique=True, comment="爬虫球队ID（唯一）")
    team_id = Column(String(64), unique=True, comment="系统球队ID（唯一）")
    team_name = Column(String(128), nullable=False, comment="标准球队名称")
    logo = Column(String(255), comment="球队图标URL")

    # 状态控制
    status = Column(TINYINT, nullable=False, server_default='1', comment="状态(0:禁用,1:启用)")
    sort = Column(Integer, server_default='0', comment="排序序号")

    __mapper_args__ = {
        "order_by": BaseSaasModel.create_time.desc(),
    }

    #通过web_id获取球队信息
    @staticmethod
    def get_match_icon(web_id: str) -> Optional['LeagueTeamScraperModel']:
        obj = db.session.query(LeagueTeamScraperModel).filter_by(web_id=web_id).first()
        if obj:
            return obj.logo
        else:
            return None


