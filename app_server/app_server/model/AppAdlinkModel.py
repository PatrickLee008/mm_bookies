from app_server import db, app
from sqlalchemy import Column, String, DECIMAL, DateTime, Text, Integer, BigInteger
from decimal import Decimal
import datetime

from app_server.utils.BaseSaasModel import BaseSaasModel


class AppAdlink(BaseSaasModel):
    __tablename__ = 'm_app_adlink'

    # 主键
    id = Column(String(64), primary_key=True, comment="主键ID")
    aid = Column(String(64), index=True, comment="所属代理ID")

    # 基础信息
    campaign_name = Column(String(200), comment="活动名称")
    channel = Column(String(100), index=True, comment="投放渠道(YouTube/Facebook/Google等)")
    ad_type = Column(String(100), comment="广告类型(信息流广告/横幅广告等)")
    budget = Column(DECIMAL(15, 2), server_default='0.00', comment="广告预算")
    cpc = Column(DECIMAL(10, 2), server_default='0.00', comment="单次点击成本(CPC)")
    cpm = Column(DECIMAL(10, 2), server_default='0.00', comment="千次曝光成本(CPM)")
    start_date = Column(DateTime, comment="活动开始日期")
    end_date = Column(DateTime, comment="活动结束日期")

    # UTM参数
    utm_source = Column(String(100), index=True, comment="UTM来源参数")
    utm_medium = Column(String(100), comment="UTM媒介参数")
    utm_campaign = Column(String(200), index=True, comment="UTM活动参数")
    utm_content = Column(String(200), comment="UTM内容参数")
    utm_term = Column(String(200), comment="UTM关键词参数")

    # 链接信息
    base_url = Column(String(500), comment="基础链接URL")
    goto_page = Column(String(500), comment="链接默认跳转到的页面")
    full_url = Column(Text, comment="完整广告链接(含UTM参数)")
    short_url = Column(String(200), comment="短链接")

    # 统计数据(可选，也可以关联其他统计表)
    impressions = Column(BigInteger, server_default='0', comment="展示量")
    clicks = Column(BigInteger, server_default='0', comment="点击量")
    unique_visitors = Column(BigInteger, server_default='0', comment="独立访客数")
    downloads = Column(BigInteger, server_default='0', comment="下载量")
    installs = Column(BigInteger, server_default='0', comment="安装量")
    registrations = Column(BigInteger, server_default='0', comment="注册量")
    total_spend = Column(DECIMAL(15, 2), server_default='0.00', comment="总消耗")

    # 状态和备注
    status = Column(String(20), server_default='active', index=True, comment="链接状态(active-有效/paused-暂停/expired-过期)")
    remarks = Column(String(500), comment="备注信息")

    __mapper_args__ = {
        "order_by": BaseSaasModel.create_time.desc(),
    }
