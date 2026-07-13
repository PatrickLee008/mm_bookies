import json
from app_server import db
from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.dialects.mysql import TINYINT
from datetime import datetime


class AppAdvertisement(db.Model):
    """APP广告管理模型"""
    __tablename__ = 'm_app_advertisement'

    id = Column(String(64), primary_key=True, comment="主键ID")
    tenant_id = Column(String(64), default='10000', comment="租户ID")
    title = Column(String(255), nullable=False, comment="广告标题")
    description = Column(Text, comment="广告描述")
    image_urls = Column(Text, comment="广告图片URL列表(JSON数组格式)")
    video_cover_url = Column(String(500), comment="视频封面图片URL")
    image_metadata = Column(Text, comment="图片元数据(JSON格式)")
    platform = Column(String(32), default='mobile', comment="广告投放平台: mobile-移动端, pc-PC端, h5-H5端")
    page = Column(String(64), default='home', comment="广告投放页面: home-首页, game_list-游戏列表页, profile-个人中心, deposit-充值页, withdraw-提现页, promotions-活动页, news-新闻页")
    position = Column(String(50), comment="页面内位置: banner-横幅, popup-弹窗, sidebar-侧边栏, floating-悬浮, bottom-底部, middle-中间")
    ad_type = Column(String(20), nullable=False, default='Image', comment="广告类型: Image, Video")
    video_url = Column(String(500), comment="视频URL")
    link_url = Column(String(500), comment="点击跳转链接")
    link_target = Column(String(20), default='Blank', comment="链接打开方式: Self, Blank, App")
    start_date = Column(DateTime, comment="开始展示时间")
    end_date = Column(DateTime, comment="结束展示时间")
    view_count = Column(Integer, default=0, comment="展示次数")
    click_count = Column(Integer, default=0, comment="点击次数")
    is_active = Column(TINYINT(1), default=1, comment="启用状态: 0-禁用, 1-启用")
    sort = Column(Integer, default=0, comment="排序号(数字越大越靠前)")
    remarks = Column(String(500), comment="备注说明")
    create_by_id = Column(String(64), comment="创建人ID")
    create_time = Column(DateTime, default=datetime.now, comment="创建时间")
    update_by_id = Column(String(64), comment="更新人ID")
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")
    del_flag = Column(TINYINT(1), default=0, comment="删除标记: 0-正常, 1-删除")

    def to_dict(self):
        columns = self.__table__.columns.keys()
        result = {}
        for key in columns:
            value = getattr(self, key)
            if isinstance(value, datetime):
                value = value.strftime('%Y-%m-%d %H:%M:%S') if value else None
            elif key in ('is_active', 'del_flag'):
                value = bool(value) if value is not None else False
            elif key == 'image_urls':
                try:
                    value = json.loads(value) if value else []
                except (json.JSONDecodeError, TypeError):
                    value = []
            result[key] = value
        return result
