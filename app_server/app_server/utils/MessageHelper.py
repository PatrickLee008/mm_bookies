# -*- coding: utf-8 -*-
"""
消息助手类 (Message Helper)
用于向Java后台的管理员发送通知消息

使用示例:
    from app_server.utils.message_helper import MessageHelper

    # 发送充值申请通知给管理员
    MessageHelper.send_recharge_apply_to_admin(
        admin_user_ids=['admin_id_1', 'admin_id_2'],
        member_id='member123',
        member_name='John Doe',
        order_id='RC20260120001',
        amount=1000.00
    )

    # 发送提现申请通知给管理员
    MessageHelper.send_withdraw_apply_to_admin(
        admin_user_ids=['admin_id_1'],
        member_id='member123',
        member_name='John Doe',
        order_id='WD20260120001',
        amount=500.00
    )
"""
import logging
from typing import List, Optional
from app_server import db
from app_server.model.NotifyModel import PluginNotify, PluginNotifyRecord

logger = logging.getLogger(__name__)


class MessageHelper:
    """消息助手类 - 发送通知给Java后台的管理员"""

    @staticmethod
    def send_to_admin(admin_user_ids: List[str], title: str, content: str,
                      category: str = 'OPERATION', priority: str = 'NORMAL',
                      target_url: Optional[str] = None, target_type: str = 'NONE') -> Optional[str]:
        """
        发送通知给管理员（通用方法）

        Args:
            admin_user_ids: 管理员用户ID列表
            title: 消息标题
            content: 消息内容
            category: 消息分类（SYSTEM-系统公告, ACTIVITY-活动通知, SECURITY-安全提醒, OPERATION-运营推送）
            priority: 优先级（HIGH-高, NORMAL-普通, LOW-低）
            target_url: 目标页面URL（可选）
            target_type: 跳转类型（NONE-无跳转, PAGE-页面跳转, EXTERNAL-外部链接）

        Returns:
            通知ID，失败返回None
        """
        if not admin_user_ids or not title or not content:
            logger.warning("Failed to send admin notification: incomplete parameters")
            return None

        try:
            # 1. 创建通知对象
            notify = PluginNotify.create_notification(
                title=title,
                content=content,
                category=category,
                priority=priority,
                target_url=target_url,
                target_type=target_type
            )

            # 设置推送统计
            notify.push_count = len(admin_user_ids)
            notify.unread_count = len(admin_user_ids)
            notify.read_count = 0

            # 2. 保存通知到数据库
            db.session.add(notify)

            # 3. 创建通知记录（发送给指定管理员）
            for user_id in admin_user_ids:
                record = PluginNotifyRecord.create_record(
                    notify_id=notify.id,
                    user_id=user_id
                )
                db.session.add(record)

            # 4. 提交事务
            db.session.commit()

            logger.info(f"Admin notification sent successfully: notify_id={notify.id}, title={title}, admin_count={len(admin_user_ids)}")
            return notify.id

        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to send admin notification: title={title}, error={e}")
            return None

    @staticmethod
    def send_recharge_apply_to_admin(admin_user_ids: List[str], member_id: str, member_name: str,
                                      order_id: str, amount: float) -> Optional[str]:
        """
        发送充值申请通知给管理员

        Args:
            admin_user_ids: 管理员用户ID列表
            member_id: 会员ID
            member_name: 会员名称
            order_id: 充值订单号
            amount: 充值金额

        Returns:
            通知ID
        """
        try:
            # 使用Model创建通知
            notify = PluginNotify.create_recharge_notification(
                member_name=member_name,
                order_id=order_id,
                amount=amount
            )

            # 设置推送统计
            notify.push_count = len(admin_user_ids)
            notify.unread_count = len(admin_user_ids)
            notify.read_count = 0

            # 保存通知
            db.session.add(notify)

            # 创建通知记录
            for user_id in admin_user_ids:
                record = PluginNotifyRecord.create_record(
                    notify_id=notify.id,
                    user_id=user_id
                )
                db.session.add(record)

            # 提交事务
            db.session.commit()

            logger.info(f"Recharge application notification sent: notify_id={notify.id}, order_id={order_id}")
            return notify.id

        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to send recharge notification: order_id={order_id}, error={e}")
            return None

    @staticmethod
    def send_withdraw_apply_to_admin(admin_user_ids: List[str], member_id: str, member_name: str,
                                      order_id: str, amount: float) -> Optional[str]:
        """
        发送提现申请通知给管理员

        Args:
            admin_user_ids: 管理员用户ID列表
            member_id: 会员ID
            member_name: 会员名称
            order_id: 提现订单号
            amount: 提现金额

        Returns:
            通知ID
        """
        try:
            # 使用Model创建通知
            notify = PluginNotify.create_withdraw_notification(
                member_name=member_name,
                order_id=order_id,
                amount=amount
            )

            # 设置推送统计
            notify.push_count = len(admin_user_ids)
            notify.unread_count = len(admin_user_ids)
            notify.read_count = 0

            # 保存通知
            db.session.add(notify)

            # 创建通知记录
            for user_id in admin_user_ids:
                record = PluginNotifyRecord.create_record(
                    notify_id=notify.id,
                    user_id=user_id
                )
                db.session.add(record)

            # 提交事务
            db.session.commit()

            logger.info(f"Withdrawal application notification sent: notify_id={notify.id}, order_id={order_id}")
            return notify.id

        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to send withdrawal notification: order_id={order_id}, error={e}")
            return None

    @staticmethod
    def send_abnormal_transaction_to_admin(admin_user_ids: List[str], member_id: str, member_name: str,
                                           transaction_type: str, amount: float, reason: str) -> Optional[str]:
        """
        发送异常交易提醒给管理员

        Args:
            admin_user_ids: 管理员用户ID列表
            member_id: 会员ID
            member_name: 会员名称
            transaction_type: 交易类型（充值/提现/游戏）
            amount: 交易金额
            reason: 异常原因

        Returns:
            通知ID
        """
        try:
            # 使用Model创建通知
            notify = PluginNotify.create_abnormal_transaction_notification(
                member_name=member_name,
                transaction_type=transaction_type,
                amount=amount,
                reason=reason
            )

            # 设置推送统计
            notify.push_count = len(admin_user_ids)
            notify.unread_count = len(admin_user_ids)
            notify.read_count = 0

            # 保存通知
            db.session.add(notify)

            # 创建通知记录
            for user_id in admin_user_ids:
                record = PluginNotifyRecord.create_record(
                    notify_id=notify.id,
                    user_id=user_id
                )
                db.session.add(record)

            # 提交事务
            db.session.commit()

            logger.info(f"Abnormal transaction notification sent: notify_id={notify.id}, member={member_name}")
            return notify.id

        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to send abnormal transaction notification: member={member_name}, error={e}")
            return None

    @staticmethod
    def send_large_amount_transaction_to_admin(admin_user_ids: List[str], member_id: str, member_name: str,
                                                transaction_type: str, amount: float) -> Optional[str]:
        """
        发送大额交易通知给管理员

        Args:
            admin_user_ids: 管理员用户ID列表
            member_id: 会员ID
            member_name: 会员名称
            transaction_type: 交易类型
            amount: 交易金额

        Returns:
            通知ID
        """
        try:
            # 使用Model创建通知
            notify = PluginNotify.create_large_amount_notification(
                member_name=member_name,
                transaction_type=transaction_type,
                amount=amount
            )

            # 设置推送统计
            notify.push_count = len(admin_user_ids)
            notify.unread_count = len(admin_user_ids)
            notify.read_count = 0

            # 保存通知
            db.session.add(notify)

            # 创建通知记录
            for user_id in admin_user_ids:
                record = PluginNotifyRecord.create_record(
                    notify_id=notify.id,
                    user_id=user_id
                )
                db.session.add(record)

            # 提交事务
            db.session.commit()

            logger.info(f"Large transaction notification sent: notify_id={notify.id}, member={member_name}")
            return notify.id

        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to send large transaction notification: member={member_name}, error={e}")
            return None


# 使用示例
if __name__ == '__main__':
    # 配置日志
    logging.basicConfig(level=logging.INFO)

    # 示例1：发送充值申请通知
    notify_id = MessageHelper.send_recharge_apply_to_admin(
        admin_user_ids=['1'],  # 管理员用户ID列表，需要根据实际情况填写
        member_id='test_member_001',
        member_name='Test User',
        order_id='RC20260120000001',
        amount=1000.00
    )
    print(f"Recharge notification ID: {notify_id}")

    # 示例2：发送提现申请通知
    notify_id = MessageHelper.send_withdraw_apply_to_admin(
        admin_user_ids=['1'],
        member_id='test_member_001',
        member_name='Test User',
        order_id='WD20260120000001',
        amount=500.00
    )
    print(f"Withdrawal notification ID: {notify_id}")
