# -*- coding: utf-8 -*-
"""
通知模型 (Notify Model)
用于管理后台管理员通知
"""
from app_server import db
from sqlalchemy import Column, String, Integer, Text, DateTime
from app_server.utils.BaseSaasModel import BaseSaasModel
import datetime
import uuid


class PluginNotify(BaseSaasModel):
    """通知表 plugin_notify"""
    __tablename__ = 'plugin_notify'

    id = Column(String(64), primary_key=True, comment='通知ID')
    type = Column(String(1), default='1', comment='类型: 1-通知, 0-公告')
    title = Column(String(200), comment='标题')
    content = Column(Text, comment='内容')
    files = Column(String(2000), comment='附件')
    status = Column(String(1), default='1', comment='状态: 0-草稿, 1-发布')
    remarks = Column(String(500), comment='描述')
    target_url = Column(String(500), comment='目标页面URL')
    target_type = Column(String(50), default='NONE', comment='跳转类型: NONE-无跳转, PAGE-页面跳转, EXTERNAL-外部链接')
    category = Column(String(50), default='OPERATION', comment='消息分类: SYSTEM-系统公告, ACTIVITY-活动通知, SECURITY-安全提醒, OPERATION-运营推送')
    priority = Column(String(20), default='NORMAL', comment='优先级: HIGH-高, NORMAL-普通, LOW-低')
    schedule_time = Column(DateTime, comment='定时发送时间')
    audit_status = Column(String(1), default='3', comment='审核状态: 0-待审核, 1-审核通过, 2-审核拒绝, 3-无需审核')
    audit_by_id = Column(String(64), comment='审核人ID')
    audit_time = Column(DateTime, comment='审核时间')
    audit_remark = Column(String(500), comment='审核备注')
    is_top = Column(Integer, default=0, comment='是否置顶: 0-否, 1-是')
    read_count = Column(Integer, default=0, comment='已读数量')
    unread_count = Column(Integer, default=0, comment='未读数量')
    push_count = Column(Integer, default=0, comment='推送总数')
    expires_at = Column(DateTime, comment='过期时间')

    @classmethod
    def create_notification(cls, title, content, category='OPERATION', priority='NORMAL',
                           target_url=None, target_type='NONE'):
        """
        创建通知对象

        Args:
            title: 消息标题
            content: 消息内容
            category: 消息分类（SYSTEM/ACTIVITY/SECURITY/OPERATION）
            priority: 优先级（HIGH/NORMAL/LOW）
            target_url: 目标页面URL（可选）
            target_type: 跳转类型（NONE/PAGE/EXTERNAL）

        Returns:
            PluginNotify对象
        """
        notify = cls()
        notify.id = cls.generate_id()
        notify.type = '1'  # 1-通知
        notify.title = title
        notify.content = content
        notify.status = '1'  # 1-发布
        notify.category = category
        notify.priority = priority
        notify.target_url = target_url
        notify.target_type = target_type
        notify.audit_status = '3'  # 3-无需审核
        notify.is_top = 0  # 0-不置顶
        notify.del_flag = 0  # 0-未删除
        notify.create_by_id = '1'
        notify.create_time = datetime.datetime.now()
        notify.update_time = datetime.datetime.now()
        return notify

    @classmethod
    def create_recharge_notification(cls, member_name, order_id, amount):
        """
        创建充值申请通知

        Args:
            member_name: 会员名称
            order_id: 充值订单号
            amount: 充值金额

        Returns:
            PluginNotify对象
        """
        title = "New Recharge Application"
        content = f"Member [{member_name}] has submitted a recharge application. Order ID: {order_id}, Amount: {amount}. Please process it promptly."
        target_url = f"/finance/recharge/MAppRechargeList"

        return cls.create_notification(
            title=title,
            content=content,
            category='OPERATION',
            priority='HIGH',
            target_url=target_url,
            target_type='PAGE'
        )

    @classmethod
    def create_withdraw_notification(cls, member_name, order_id, amount):
        """
        创建提现申请通知

        Args:
            member_name: 会员名称
            order_id: 提现订单号
            amount: 提现金额

        Returns:
            PluginNotify对象
        """
        title = "New Withdrawal Application"
        content = f"Member [{member_name}] has submitted a withdrawal application. Order ID: {order_id}, Amount: {amount}. Please review it promptly."
        target_url = f"/finance/withdraw/MAppWithdrawList"

        return cls.create_notification(
            title=title,
            content=content,
            category='OPERATION',
            priority='HIGH',
            target_url=target_url,
            target_type='PAGE'
        )

    @classmethod
    def create_abnormal_transaction_notification(cls, member_name, transaction_type, amount, reason):
        """
        创建异常交易通知

        Args:
            member_name: 会员名称
            transaction_type: 交易类型
            amount: 交易金额
            reason: 异常原因

        Returns:
            PluginNotify对象
        """
        title = "Abnormal Transaction Alert"
        content = f"Abnormal transaction detected for member [{member_name}]: Type={transaction_type}, Amount={amount}, Reason: {reason}"

        return cls.create_notification(
            title=title,
            content=content,
            category='SECURITY',
            priority='HIGH'
        )

    @classmethod
    def create_large_amount_notification(cls, member_name, transaction_type, amount):
        """
        创建大额交易通知

        Args:
            member_name: 会员名称
            transaction_type: 交易类型
            amount: 交易金额

        Returns:
            PluginNotify对象
        """
        title = "Large Transaction Notification"
        content = f"Large transaction detected for member [{member_name}]: Type={transaction_type}, Amount={amount}"

        return cls.create_notification(
            title=title,
            content=content,
            category='OPERATION',
            priority='NORMAL'
        )

    def to_dict(self):
        """转换为字典"""
        columns = ['id', 'type', 'title', 'content', 'status', 'category', 'priority',
                   'target_url', 'target_type', 'read_count', 'unread_count', 'push_count']
        result = {}
        for key in columns:
            value = getattr(self, key, None)
            if key in {'create_time', 'update_time', 'schedule_time', 'audit_time', 'expires_at'}:
                value = str(value) if value else None
            result[key] = value
        return result


class PluginNotifyRecord(BaseSaasModel):
    """通知记录表 plugin_notify_record"""
    __tablename__ = 'plugin_notify_record'

    id = Column(String(64), primary_key=True, comment='记录ID')
    notify_id = Column(String(64), comment='通知ID')
    user_id = Column(String(64), comment='接收用户ID')
    read_flag = Column(String(1), default='0', comment='阅读标记: 0-未读, 1-已读')
    read_date = Column(DateTime, comment='阅读时间')

    @classmethod
    def create_record(cls, notify_id, user_id):
        """
        创建通知记录

        Args:
            notify_id: 通知ID
            user_id: 接收用户ID

        Returns:
            PluginNotifyRecord对象
        """
        record = cls()
        record.id = cls.generate_id()
        record.notify_id = notify_id
        record.user_id = user_id
        record.read_flag = '0'  # 0-未读
        record.del_flag = 0  # 0-未删除
        record.create_time = datetime.datetime.now()
        record.update_time = datetime.datetime.now()
        return record

    def to_dict(self):
        """转换为字典"""
        columns = ['id', 'notify_id', 'user_id', 'read_flag', 'read_date']
        result = {}
        for key in columns:
            value = getattr(self, key, None)
            if key in {'create_time', 'update_time', 'read_date'}:
                value = str(value) if value else None
            result[key] = value
        return result
