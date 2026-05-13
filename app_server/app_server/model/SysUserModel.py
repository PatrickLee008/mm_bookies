# -*- coding: utf-8 -*-
"""
系统用户模型 (System User Model)
用于映射 Java 后台的 sys_user 表
"""
from app_server import db
from sqlalchemy import Column, String, Integer, DateTime

from app_server.utils.BaseSaasModel import BaseSaasModel


class SysUser(BaseSaasModel):
    """系统用户表 - Java后台管理员用户"""
    __tablename__ = 'sys_user'

    # 主键
    id = Column(String(64), primary_key=True, comment="用户ID")
    aid = Column(String(64), index=True, comment="关联的代理ID")
    login_name = Column(String(64), comment="用户名")
    login_flag = Column(String(1), default='1', comment="登录标记")

    # 其他字段可以根据实际需要添加
    # nickname = Column(String(64), comment="昵称")
    # status = Column(String(10), comment="状态")
    # create_time = Column(DateTime, comment="创建时间")

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'aid': self.aid,
            'login_name': self.login_name
        }

    @staticmethod
    def get_admin_ids_by_aid(aid):
        """
        通过 aid 获取所有关联的管理员用户ID列表

        Args:
            aid: 代理ID

        Returns:
            List[str]: 管理员用户ID列表
        """
        if not aid:
            return []

        users = SysUser.query.filter_by(aid=aid,del_flag=0,login_flag='1').all()
        return [user.id for user in users if user.id]
