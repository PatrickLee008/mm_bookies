from app_server import db, app
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.dialects.mysql import TINYINT
from datetime import datetime
from sqlalchemy import func


class AppSplashScreen(db.Model):
    """启动页配置模型"""
    __tablename__ = 'm_app_splash_screen'

    id = Column(String(64), primary_key=True, comment="主键ID")
    tenant_id = Column(String(64), nullable=False, default='10000', comment="租户ID")
    title = Column(String(255), nullable=False, comment="标题/名称")
    description = Column(Text, comment="描述说明")
    image_url = Column(String(500), comment="启动屏图片URL")
    image_metadata = Column(Text, comment="图片元数据(JSON: resolution, size, upload_timestamp)")
    display_duration = Column(Integer, nullable=False, default=5, comment="显示时长(秒), 1-10")
    enable_skip_button = Column(TINYINT(1), nullable=False, default=1, comment="是否启用跳过按钮 0:禁用 1:启用")
    start_date = Column(DateTime, comment="开始展示日期时间")
    end_date = Column(DateTime, comment="结束展示日期时间")
    enable_action_button = Column(TINYINT(1), nullable=False, default=0, comment="是否启用动作按钮 0:禁用 1:启用")
    action_button_label = Column(String(100), comment="动作按钮文本(如: 'Bet Now', 'View Promo')")
    action_button_route = Column(String(255), comment="路由目标(home/promotions/bet-history/coupon/match/{id}/deeplink)")
    is_active = Column(TINYINT(1), nullable=False, default=1, comment="启用状态 0:禁用 1:启用")
    sort = Column(Integer, default=100, comment="排序号，数字越小越靠前")
    remarks = Column(String(500), comment="备注说明")
    create_by_id = Column(String(64), comment="创建人ID")
    create_time = Column(DateTime, default=datetime.now, comment="创建时间")
    update_by_id = Column(String(64), comment="更新人ID")
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")
    del_flag = Column(TINYINT(1), default=0, comment="删除标记 0:正常 1:已删除")

    def to_dict(self):
        """转换为字典"""
        columns = self.__table__.columns.keys()
        result = {}
        for key in columns:
            value = getattr(self, key)
            # 将 DateTime 类型转换为字符串
            if isinstance(value, datetime):
                value = value.strftime('%Y-%m-%d %H:%M:%S') if value else None
            # 将 TINYINT 转换为布尔值
            elif key in ('enable_skip_button', 'enable_action_button', 'is_active', 'del_flag'):
                value = bool(value) if value is not None else False
            result[key] = value
        return result
