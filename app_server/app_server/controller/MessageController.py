# -*- coding: utf-8 -*-
"""
APP会员消息控制器 (Message Controller)
处理用户消息相关的API请求
"""
from flask import g, request, jsonify, Blueprint
from sqlalchemy import and_, or_, func
from datetime import datetime

from app_server import db, auth
from app_server.model.AppMemberMessageModel import AppMemberMessage
from app_server.utils.Kits import Kits

message = Blueprint('message', __name__)


@message.route('/list', methods=['GET','POST'])
@auth.login_required
def get_message_list():
    """
    获取消息列表

    Args (Query Params):
        current: 当前页码 (默认: 1)
        size: 每页数量 (默认: 20)
        message_type: 消息类型过滤 (可选)
        is_read: 已读状态过滤 (可选: 0-未读, 1-已读)

    Returns:
        {
            'code': 200,
            'records': [...],  # 消息列表
            'total': 100,      # 总记录数
            'current': 1,      # 当前页
            'size': 20         # 每页数量
        }
    """
    try:
        # 获取分页参数
        args = request.get_json()
        current = args.get('current')
        size = args.get('size')
        message_type = args.get('message_type')
        is_read = args.get('is_read')

        user_id = g.user.id

        # 构建查询
        query = AppMemberMessage.query.filter(
            AppMemberMessage.member_id == user_id,
            AppMemberMessage.del_flag == 0
        )

        # 过滤消息类型
        if message_type:
            query = query.filter(AppMemberMessage.message_type == message_type)

        # 过滤已读状态
        if is_read is not None:
            query = query.filter(AppMemberMessage.is_read == is_read)

        # 获取总数
        total = query.count()

        # 分页查询
        messages = query.order_by(
            AppMemberMessage.create_time.desc()
        ).offset((current - 1) * size).limit(size).all()

        # 转换为字典
        records = [msg.to_dict(g.user.timezone) for msg in messages]

        return jsonify({
            'code': 200,
            'records': records,
            'total': total,
            'current': current,
            'size': size,
            'message': 'Success'
        })

    except Exception as e:
        print(f"[MessageController] Get message list error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'code': 500,
            'message': 'System or Technical Error'
        }), 500


@message.route('/unread_count', methods=['GET'])
@auth.login_required
def get_unread_count():
    """
    获取未读消息数量

    Returns:
        {
            'code': 200,
            'count': 10,
            'message': 'Success'
        }
    """
    try:
        user_id = g.user.id

        # 查询未读消息数量（排除已删除和已过期的消息）
        count = AppMemberMessage.query.filter(
            AppMemberMessage.member_id == user_id,
            AppMemberMessage.is_read == 0,
            AppMemberMessage.del_flag == 0,
            or_(
                AppMemberMessage.expires_at.is_(None),
                AppMemberMessage.expires_at > datetime.now()
            )
        ).count()

        return jsonify({
            'code': 200,
            'count': count,
            'message': 'Success'
        })

    except Exception as e:
        print(f"[MessageController] Get unread count error: {e}")
        return jsonify({
            'code': 500,
            'message': 'System or Technical Error'
        }), 500


@message.route('/mark_read', methods=['PUT', 'POST'])
@auth.login_required
def mark_as_read():
    """
    标记消息为已读

    Args:
        message_id: 消息ID

    Returns:
        {
            'code': 200,
            'message': 'Success'
        }
    """
    args = request.get_json()
    message_id = args.get('message_id')
    try:
        user_id = g.user.id

        # 查询消息
        msg = AppMemberMessage.query.filter(
            AppMemberMessage.id == message_id,
            AppMemberMessage.member_id == user_id,
            AppMemberMessage.del_flag == 0
        ).first()

        if not msg:
            return jsonify({
                'code': 404,
                'message': 'Message not found'
            }), 404

        # 标记为已读
        if msg.is_read == 0:
            msg.mark_as_read()
            db.session.commit()

        return jsonify({
            'code': 200,
            'message': 'Success'
        })

    except Exception as e:
        db.session.rollback()
        print(f"[MessageController] Mark as read error: {e}")
        return jsonify({
            'code': 500,
            'message': 'System or Technical Error'
        }), 500


@message.route('/mark_all_read', methods=['PUT', 'POST'])
@auth.login_required
def mark_all_as_read():
    """
    标记所有消息为已读

    Returns:
        {
            'code': 200,
            'count': 5,  # 标记的消息数量
            'message': 'Success'
        }
    """
    try:
        user_id = g.user.id

        # 查询所有未读消息
        unread_messages = AppMemberMessage.query.filter(
            AppMemberMessage.member_id == user_id,
            AppMemberMessage.is_read == 0,
            AppMemberMessage.del_flag == 0
        ).all()

        count = 0
        for msg in unread_messages:
            msg.mark_as_read()
            count += 1

        db.session.commit()

        return jsonify({
            'code': 200,
            'count': count,
            'message': 'Success'
        })

    except Exception as e:
        db.session.rollback()
        print(f"[MessageController] Mark all as read error: {e}")
        return jsonify({
            'code': 500,
            'message': 'System or Technical Error'
        }), 500


@message.route('/delete', methods=['DELETE', 'POST'])
@auth.login_required
def delete_message():
    """
    删除消息（软删除）

    Args:
        message_id: 消息ID

    Returns:
        {
            'code': 200,
            'message': 'Success'
        }
    """
    args = request.get_json()
    message_id = args.get('message_id')
    try:
        user_id = g.user.id

        # 查询消息
        msg = AppMemberMessage.query.filter(
            AppMemberMessage.id == message_id,
            AppMemberMessage.member_id == user_id,
            AppMemberMessage.del_flag == 0
        ).first()

        if not msg:
            return jsonify({
                'code': 404,
                'message': 'Message not found'
            }), 404

        # 软删除
        msg.mark_as_deleted()
        db.session.commit()

        return jsonify({
            'code': 200,
            'message': 'Success'
        })

    except Exception as e:
        db.session.rollback()
        print(f"[MessageController] Delete message error: {e}")
        return jsonify({
            'code': 500,
            'message': 'System or Technical Error'
        }), 500


@message.route('/detail/<message_id>', methods=['GET'])
@auth.login_required
def get_message_detail(message_id):
    """
    获取消息详情

    Args:
        message_id: 消息ID

    Returns:
        {
            'code': 200,
            'data': {...},  # 消息详情
            'message': 'Success'
        }
    """
    try:
        user_id = g.user.id

        # 查询消息
        msg = AppMemberMessage.query.filter(
            AppMemberMessage.id == message_id,
            AppMemberMessage.member_id == user_id,
            AppMemberMessage.del_flag == 0
        ).first()

        if not msg:
            return jsonify({
                'code': 404,
                'message': 'Message not found'
            }), 404

        # 自动标记为已读
        if msg.is_read == 0:
            msg.mark_as_read()
            db.session.commit()

        return jsonify({
            'code': 200,
            'data': msg.to_dict(),
            'message': 'Success'
        })

    except Exception as e:
        print(f"[MessageController] Get message detail error: {e}")
        return jsonify({
            'code': 500,
            'message': 'System or Technical Error'
        }), 500


@message.route('/statistics', methods=['GET'])
@auth.login_required
def get_message_statistics():
    """
    获取消息统计信息

    Returns:
        {
            'code': 200,
            'data': {
                'total': 100,        # 总消息数
                'unread': 10,        # 未读数
                'read': 90,          # 已读数
                'by_type': {...}     # 按类型统计
            },
            'message': 'Success'
        }
    """
    try:
        user_id = g.user.id

        # 总消息数
        total = AppMemberMessage.query.filter(
            AppMemberMessage.member_id == user_id,
            AppMemberMessage.del_flag == 0,
            or_(
                AppMemberMessage.expires_at.is_(None),
                AppMemberMessage.expires_at > datetime.now()
            )
        ).count()

        # 未读数
        unread = AppMemberMessage.query.filter(
            AppMemberMessage.member_id == user_id,
            AppMemberMessage.is_read == 0,
            AppMemberMessage.del_flag == 0,
            or_(
                AppMemberMessage.expires_at.is_(None),
                AppMemberMessage.expires_at > datetime.now()
            )
        ).count()

        # 按类型统计
        type_stats = db.session.query(
            AppMemberMessage.message_type,
            func.count(AppMemberMessage.id).label('count')
        ).filter(
            AppMemberMessage.member_id == user_id,
            AppMemberMessage.del_flag == 0,
            or_(
                AppMemberMessage.expires_at.is_(None),
                AppMemberMessage.expires_at > datetime.now()
            )
        ).group_by(AppMemberMessage.message_type).all()

        by_type = {stat.message_type: stat.count for stat in type_stats}

        return jsonify({
            'code': 200,
            'data': {
                'total': total,
                'unread': unread,
                'read': total - unread,
                'by_type': by_type
            },
            'message': 'Success'
        })

    except Exception as e:
        print(f"[MessageController] Get message statistics error: {e}")
        return jsonify({
            'code': 500,
            'message': 'System or Technical Error'
        }), 500
