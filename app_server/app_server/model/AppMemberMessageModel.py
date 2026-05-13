# -*- coding: utf-8 -*-
"""
APP会员消息模型 (App Member Message Model)
用于映射 m_app_member_message 表
"""
from app_server import db
from sqlalchemy import Column, String, Integer, Text, DateTime, SmallInteger
from app_server.utils.BaseSaasModel import BaseSaasModel
from datetime import datetime

from app_server.utils.Kits import Kits


class AppMemberMessage(BaseSaasModel):
    """APP会员消息表"""
    __tablename__ = 'm_app_member_message'

    # 主键
    id = Column(String(64), primary_key=True, comment='消息ID（主键）')
    aid = Column(String(64), index=True, comment="所属代理ID")

    # 消息基本信息
    message_id = Column(String(100), nullable=False, comment='消息唯一标识（格式：MSG_时间戳_随机数）')
    member_id = Column(String(64), nullable=False, index=True, comment='接收会员ID（关联m_app_member.id）')
    title = Column(String(200), nullable=False, comment='消息标题')
    content = Column(Text, nullable=False, comment='消息内容')

    # 消息分类
    message_type = Column(String(50), default='SYSTEM', index=True, comment='消息类型：SYSTEM-系统, ORDER-订单, PROMOTION-推广, NOTICE-公告, NOTIFICATION-通知, RECHARGE-充值, WITHDRAW-提现, GAME-游戏')
    category = Column(String(50), default='GENERAL', comment='消息分类（可自定义）')
    priority = Column(String(20), default='NORMAL', index=True, comment='优先级：HIGH-高, NORMAL-普通, LOW-低')

    # 目标跳转
    target_url = Column(String(500), comment='目标页面URL（用于消息点击跳转）')
    target_type = Column(String(50), default='NONE', comment='跳转类型：NONE-无跳转, PAGE-页面跳转, EXTERNAL-外部链接')
    target_params = Column(String(2000), comment='目标页面参数（JSON格式）')
    payload = Column(Text, comment='额外数据（JSON格式，供业务模块扩展使用）')

    # 已读状态
    is_read = Column(SmallInteger, default=0, index=True, comment='是否已读：0-未读, 1-已读')
    read_time = Column(DateTime, comment='阅读时间')

    # 消息来源与关联
    source = Column(String(50), default='SYSTEM', comment='消息来源：SYSTEM-系统, BUSINESS-业务触发')
    business_id = Column(String(64), index=True, comment='关联业务ID（如：订单号、充值单号、提现单号等）')

    # 过期时间
    expires_at = Column(DateTime, index=True, comment='过期时间（过期后不再显示）')

    # 设备信息
    device_info = Column(String(1000), comment='设备信息（JSON格式）')

    # 推送状态
    push_status = Column(String(20), default='PENDING', index=True, comment='推送状态：PENDING-待推送, SENT-已推送, FAILED-推送失败')
    push_time = Column(DateTime, comment='推送时间（WebSocket推送成功的时间）')
    push_error = Column(String(500), comment='推送失败原因')

    # 创建和更新信息继承自BaseSaasModel
    # create_by_id, create_time, update_by_id, update_time, del_flag, tenant_id

    __mapper_args__ = {
        "order_by": BaseSaasModel.create_time.desc(),
    }

    def to_dict(self, user_timezone_str, include=None, exclude=None):
        """
        转换为字典

        Args:
            include: 要包含的字段集合
            exclude: 要排除的字段集合

        Returns:
            dict: 消息数据字典
        """
        data = {
            'id': self.id,
            'messageId': self.message_id,
            'memberId': self.member_id,
            'title': self.title,
            'content': self.content,
            'messageType': self.message_type,
            'category': self.category,
            'priority': self.priority,
            'targetUrl': self.target_url,
            'targetType': self.target_type,
            'targetParams': self.target_params,
            'payload': self.payload,
            'isRead': self.is_read,
            'readTime': self.read_time.strftime('%Y-%m-%d %H:%M:%S') if self.read_time else None,
            'source': self.source,
            'businessId': self.business_id,
            'expiresAt': self.expires_at.strftime('%Y-%m-%d %H:%M:%S') if self.expires_at else None,
            'deviceInfo': self.device_info,
            'pushStatus': self.push_status,
            'pushTime': self.push_time.strftime('%Y-%m-%d %H:%M:%S') if self.push_time else None,
            'pushError': self.push_error,
            'createTime': self.create_time.strftime('%Y-%m-%d %H:%M:%S') if self.create_time else None,
            'updateTime': self.update_time.strftime('%Y-%m-%d %H:%M:%S') if self.update_time else None,
        }
        # createTime 和 pushTime 转为用户时区
        data['createTime'] = Kits.system_time_to_user_time(user_timezone_str,system_date_time_str=data['createTime'])
        data['pushTime'] = Kits.system_time_to_user_time(user_timezone_str,system_date_time_str=data['pushTime'])

        # 处理 include 和 exclude
        if include:
            data = {k: v for k, v in data.items() if k in include}
        if exclude:
            data = {k: v for k, v in data.items() if k not in exclude}

        return data

    @staticmethod
    def create_message(member_id, title, content, message_type='SYSTEM', **kwargs):
        """
        创建消息（工厂方法）

        Args:
            member_id: 会员ID
            title: 消息标题
            content: 消息内容
            message_type: 消息类型
            **kwargs: 其他可选参数

        Returns:
            AppMemberMessage: 消息对象
        """
        from app_server.utils.Kits import Kits
        import time

        # 生成消息ID和唯一标识
        message_id = f"MSG_{int(time.time() * 1000)}_{Kits.generate_random_number(4)}"

        message = AppMemberMessage(
            id=Kits.generate_uuid(),
            message_id=message_id,
            member_id=member_id,
            title=title,
            content=content,
            message_type=message_type,
            category=kwargs.get('category', 'GENERAL'),
            priority=kwargs.get('priority', 'NORMAL'),
            target_url=kwargs.get('target_url'),
            target_type=kwargs.get('target_type', 'NONE'),
            target_params=kwargs.get('target_params'),
            payload=kwargs.get('payload'),
            source=kwargs.get('source', 'SYSTEM'),
            business_id=kwargs.get('business_id'),
            expires_at=kwargs.get('expires_at'),
            device_info=kwargs.get('device_info'),
            push_status=kwargs.get('push_status', 'PENDING')
        )

        return message

    def mark_as_read(self):
        """标记为已读"""
        self.is_read = 1
        self.read_time = datetime.now()

    def mark_as_deleted(self):
        """标记为已删除（软删除）"""
        self.del_flag = 1

    def is_expired(self):
        """检查消息是否过期"""
        if not self.expires_at:
            return False
        return datetime.now() > self.expires_at
