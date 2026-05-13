from sqlalchemy import Column, String, Integer, Text, DateTime
from sqlalchemy.dialects.mysql import TINYINT

from app_server.utils.BaseSaasModel import BaseSaasModel

# 联赛信息管理表
class MAppLeague(BaseSaasModel):
    __tablename__ = 'm_app_league'

    id = Column(String(64), primary_key=True, comment="主键ID")
    name = Column(String(100), nullable=False, comment="联赛名称")
    is_scraper = Column(TINYINT, server_default='0', comment="是否用于爬虫")
    scraper_name = Column(String(100), comment="爬虫联赛名称")
    code = Column(String(50), comment="联赛代码/缩写")
    type = Column(String(32), comment="联赛类型")
    logo = Column(String(255), comment="联赛图标URL")
    logo2 = Column(String(128), comment="图片oss地址")
    country = Column(String(50), comment="所属国家/地区")
    country_code = Column(String(32), comment="国家代码")
    country_flag = Column(String(255), comment="国家国旗")
    continent = Column(String(20), comment="所属大洲")
    league_level = Column(String(2), comment="联赛级别(1:顶级,2:次级,3:三级等)")
    founded_year = Column(Integer, comment="成立年份")
    current_champion = Column(String(64), comment="当前冠军球队ID")
    season_year = Column(Integer, comment="赛季年份")
    season_start = Column(String(10), comment="赛季开始月份(1-12)")
    season_end = Column(String(10), comment="赛季结束月份(1-12)")
    total_teams = Column(Integer, comment="参赛球队总数")
    description = Column(Text, comment="联赛描述")
    official_website = Column(String(255), comment="官方网站")
    api_league_id = Column(String(32), comment="三方平台联赛ID")
    sync_team_time = Column(DateTime, comment="同步球队时间")
    status = Column(TINYINT, comment="状态(0:禁用,1:启用)")
    sort = Column(Integer, comment="排序序号")

    @staticmethod
    def get_scraper_leagues(for_sort = False, tenant_id=None):
        """
        获取所有启用爬虫的联赛
        条件: is_scraper=1, del_flag=0, status=1
        返回: scraper_name列表
        """
        query = MAppLeague.query.filter(
            MAppLeague.is_scraper == 1,
            MAppLeague.del_flag == 0,
            MAppLeague.status == 1
        )
        # 为了排序，则获取优先排序的联赛
        if for_sort:
            query = query.filter(MAppLeague.sort>0)

        if tenant_id is not None:
            query = query.filter(MAppLeague.tenant_id == tenant_id)

        leagues = query.order_by(MAppLeague.sort.desc(), MAppLeague.create_time.desc()).all()

        # 提取scraper_name并过滤掉None值
        scraper_names = [league.scraper_name for league in leagues if league.scraper_name]

        return scraper_names

    @staticmethod
    def get_scraper_league_objects(session=None, tenant_id=None):
        """
        获取所有启用爬虫的联赛对象
        条件: is_scraper=1, del_flag=0, status=1
        返回: MAppLeague对象列表
        """
        query = MAppLeague.query.filter(
            MAppLeague.is_scraper == 1,
            MAppLeague.del_flag == 0,
            MAppLeague.status == 1
        )

        if tenant_id is not None:
            query = query.filter(MAppLeague.tenant_id == tenant_id)

        leagues = query.order_by(MAppLeague.sort.asc()).all()

        return leagues
