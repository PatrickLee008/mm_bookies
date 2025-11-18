from app_server import db
from sqlalchemy import Column, String, Integer, Boolean, Text, Numeric, SmallInteger, DateTime
import datetime

# 收藏夹
class AppFavourite(db.Model):
    __tablename__ = 'm_app_favourite'
    id = Column(String(32), primary_key=True, comment='用户唯一标识ID')
    mb_id = Column(String(32), comment='会员ID')
    league = Column(String(255), comment='联赛')
    team = Column(String(100), comment='球队')
    status = Column(SmallInteger, default=1, comment='状态: 0-停用, 1-启用')
    sort = Column(Integer, default=100, comment='排序序号')
    create_by_id = Column(String(32), comment='创建人')
    create_time = Column(DateTime, default=datetime.datetime.now, comment='创建时间')
    update_by_id = Column(String(32), comment='更新人')
    update_time = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now, comment='更新时间')
    remarks = Column(String(500), comment='备注信息')
    del_flag = Column(Integer, default=0, comment='删除标记')
    tenant_id = Column(String(64), default=10000, comment='租户ID')

    def to_dict(self):
        columns = ['id','league', 'team','status','sort']
        result = {}
        for key in columns:
            value = getattr(self, key)
            result[key] = value
        return result
