# -*- coding: utf-8 -*-
"""
会员消息服务 (MemberMessageService)
向 APP 会员发送站内通知。
与 MessageHelper（向管理员发送通知）不同，本服务面向普通 App 会员。

使用示例:
    from app_server.utils.MemberMessageService import MemberMessageService

    MemberMessageService.send_recharge_submitted(
        member_id='member123',
        order_id='RC20260120001',
        amount=1000.00
    )
"""
import logging
from app_server import db
from app_server.model.AppMemberMessageModel import AppMemberMessage

logger = logging.getLogger(__name__)


class MemberMessageService:
    """会员消息服务 - 发送站内通知给 APP 会员"""

    @staticmethod
    def send_to_member(member_id: str, title: str, content: str,
                       message_type: str = 'SYSTEM', **kwargs) -> bool:
        """
        发送站内通知给会员（通用方法）

        Args:
            member_id: 会员ID
            title: 消息标题
            content: 消息内容
            message_type: 消息类型（SYSTEM/ORDER/RECHARGE/WITHDRAW/NOTIFICATION/BROADCAST/PROMOTION/GAME）
            **kwargs: 可选参数
                - priority: 优先级（HIGH/NORMAL/LOW），默认 NORMAL
                - source: 消息来源，默认 SYSTEM
                - category: 消息分类（GENERAL/SECURITY/ACTIVITY/OPERATION），默认 GENERAL
                - business_id: 关联业务ID（订单号等）
                - target_url: 跳转页面 URL
                - target_type: 跳转类型（NONE/PAGE/EXTERNAL），默认 NONE
                - target_params: 目标页面参数（JSON格式字符串）
                - payload: 额外数据（JSON格式字符串，供业务扩展）
                - device_info: 设备信息（JSON格式字符串）
                - expires_at: 过期时间（datetime对象）
                - aid: 代理ID

        Returns:
            True 表示成功，False 表示失败
        """
        try:
            message = AppMemberMessage.create_message(
                member_id=member_id,
                title=title,
                content=content,
                message_type=message_type,
                source=kwargs.get('source', 'SYSTEM'),
                category=kwargs.get('category', 'GENERAL'),
                priority=kwargs.get('priority', 'NORMAL'),
                business_id=kwargs.get('business_id'),
                target_url=kwargs.get('target_url'),
                target_type=kwargs.get('target_type', 'NONE'),
                target_params=kwargs.get('target_params'),
                payload=kwargs.get('payload'),
                device_info=kwargs.get('device_info'),
                expires_at=kwargs.get('expires_at'),
            )
            if kwargs.get('aid'):
                message.aid = kwargs['aid']
            db.session.add(message)
            db.session.commit()
            logger.info(
                f"Member notification sent: member_id={member_id}, "
                f"title={title}, type={message_type}, business_id={kwargs.get('business_id')}"
            )
            return True
        except Exception as e:
            db.session.rollback()
            logger.error(
                f"Failed to send member notification: member_id={member_id}, "
                f"title={title}, error={e}"
            )
            return False

    @staticmethod
    def send_recharge_submitted(member_id: str, order_id: str, amount: float,
                                aid: str = None) -> bool:
        """
        充值申请已提交 — 发送通知给会员

        Args:
            member_id: 会员ID
            order_id: 充值单号
            amount: 充值金额
            aid: 所属代理ID（可选）
        """
        title = 'Deposit Submitted'
        content = (
            f'Your deposit request of {amount:.2f} MMK has been submitted successfully.\n'
            f'Order ID: {order_id}\n'
            f'Please wait for approval.'
        )
        return MemberMessageService.send_to_member(
            member_id=member_id,
            title=title,
            content=content,
            message_type='RECHARGE',
            source='SYSTEM',
            business_id=order_id,
            aid=aid,
        )

    @staticmethod
    def send_withdraw_submitted(member_id: str, order_id: str, amount: float,
                                aid: str = None) -> bool:
        """
        提现申请已提交 — 发送通知给会员

        Args:
            member_id: 会员ID
            order_id: 提现单号
            amount: 提现金额
            aid: 所属代理ID（可选）
        """
        title = 'Withdrawal Submitted'
        content = (
            f'Your withdrawal request of {amount:.2f} MMK has been submitted successfully.\n'
            f'Order ID: {order_id}\n'
            f'Please wait for processing.'
        )
        return MemberMessageService.send_to_member(
            member_id=member_id,
            title=title,
            content=content,
            message_type='WITHDRAW',
            source='SYSTEM',
            business_id=order_id,
            aid=aid,
        )

    @staticmethod
    def send_security_alert(member_id: str, title: str, content: str,
                            security_type: str, aid: str = None,
                            extra: dict = None) -> bool:
        """
        发送安全提醒消息给会员（高优先级）

        Args:
            member_id: 会员ID
            title: 提醒标题
            content: 提醒内容
            security_type: 安全类型（PASSWORD_CHANGE/LOGIN_ALERT/IP_CHANGE/DEVICE_CHANGE/ACCOUNT_FREEZE）
            aid: 所属代理ID（可选）
            extra: 额外数据字典（可选），会序列化为 payload
        """
        import json as _json
        payload_data = {'securityType': security_type, 'priority': 'HIGH'}
        if extra:
            payload_data.update(extra)
        return MemberMessageService.send_to_member(
            member_id=member_id,
            title=title,
            content=content,
            message_type='NOTIFICATION',
            category='SECURITY',
            priority='HIGH',
            source='SYSTEM',
            payload=_json.dumps(payload_data),
            aid=aid,
        )

    @staticmethod
    def send_login_alert(member_id: str, new_ip: str, prev_ip: str,
                         new_device: str, prev_device: str,
                         login_time: str, aid: str = None) -> bool:
        """
        登录时IP或设备发生变化 — 发送安全提醒给会员

        Args:
            member_id: 会员ID
            new_ip: 当前登录IP
            prev_ip: 上次登录IP
            new_device: 当前设备
            prev_device: 上次设备
            login_time: 登录时间字符串
            aid: 所属代理ID（可选）
        """
        import json as _json
        ip_changed = prev_ip and new_ip != prev_ip
        device_changed = prev_device and new_device != prev_device

        if not ip_changed and not device_changed:
            return True

        changes = []
        if ip_changed:
            changes.append(f'IP address changed from {prev_ip} to {new_ip}')
        if device_changed:
            changes.append(f'Device changed from {prev_device} to {new_device}')

        title = 'Security Alert: Login from New Location/Device'
        content = (
            f'A new login was detected on your account.\n'
            f'{chr(10).join(changes)}\n'
            f'Login time: {login_time}\n'
            f'If this was not you, please change your password immediately.'
        )
        extra = {
            'newIp': new_ip,
            'prevIp': prev_ip,
            'newDevice': new_device,
            'prevDevice': prev_device,
            'loginTime': login_time,
            'ipChanged': ip_changed,
            'deviceChanged': device_changed,
        }
        return MemberMessageService.send_security_alert(
            member_id=member_id,
            title=title,
            content=content,
            security_type='LOGIN_ALERT',
            aid=aid,
            extra=extra,
        )

    @staticmethod
    def send_order_placed(member_id: str, order_id: str, amount: float,
                          aid: str = None) -> bool:
        """
        下注成功 — 发送通知给会员

        Args:
            member_id: 会员ID
            order_id: 订单ID
            amount: 下注金额
            aid: 所属代理ID（可选）
        """
        title = 'Bet Placed Successfully'
        content = (
            f'Your bet of {amount:.2f} MMK has been placed successfully.\n'
            f'Order ID: {order_id}'
        )
        return MemberMessageService.send_to_member(
            member_id=member_id,
            title=title,
            content=content,
            message_type='ORDER',
            source='SYSTEM',
            business_id=order_id,
            aid=aid,
        )
