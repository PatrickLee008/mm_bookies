# -*- coding: utf-8 -*-
"""
WebSocket消息管理控制器
与Java后端WebSocket推送配合使用
"""

from flask import Blueprint, request, jsonify, current_app, g
from datetime import datetime, timedelta
import json
import logging
from app_server.utils.BaseModel import BaseModel
from sqlalchemy import text, desc, and_, or_, func
from sqlalchemy.orm import sessionmaker

# 创建蓝图
websocket_message = Blueprint('websocket_message', __name__)

# 日志配置
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 常量定义 - 参考InviteController
SUCCESS_CODE = 20000
SYSTEM_ERROR_CODE = 50001
PARAM_ERROR_CODE = 40001
MESSAGE_NOT_FOUND_CODE = 40002
MESSAGE_ALREADY_READ_CODE = 40003
PERMISSION_DENIED_CODE = 40004

class WebSocketMessageModel(BaseModel):
    """WebSocket消息模型"""
    __tablename__ = 'm_app_message'
    
    def __init__(self):
        super().__init__()
        self.message_id = None          # 消息ID（对应Java端的messageId）
        self.user_id = None             # 接收用户ID
        self.title = None               # 消息标题
        self.content = None             # 消息内容
        self.message_type = None        # 消息类型（SYSTEM, BROADCAST, NOTIFICATION）
        self.payload = None             # 额外数据（JSON格式）
        self.is_read = False            # 是否已读
        self.read_time = None           # 阅读时间
        self.created_time = None        # 创建时间
        self.updated_time = None        # 更新时间
        self.device_info = None         # 设备信息（JSON格式）
        self.source = None              # 消息来源（JAVA_BACKEND, SYSTEM等）
        self.target_page = None         # 目标页面
        self.priority = None            # 消息优先级（HIGH, NORMAL, LOW）
        self.expires_at = None          # 过期时间

@websocket_message.route('/messages', methods=['POST'])
def save_message():
    """
    保存WebSocket消息到数据库
    用于UniApp端将接收到的消息同步到服务器
    """
    try:
        data = request.get_json()
        
        # 验证必需参数
        required_fields = ['message_id', 'user_id', 'title', 'content']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'code': PARAM_ERROR_CODE,
                    'data': None,
                    'message': f"缺少必需参数: {field}"
                }), 400
        
        # 检查消息是否已存在
        Session = sessionmaker(bind=current_app.config['DATABASE_ENGINE'])
        session = Session()
        
        try:
            existing_message = session.execute(
                text("SELECT id FROM m_app_message WHERE message_id = :message_id AND user_id = :user_id"),
                {"message_id": data['message_id'], "user_id": data['user_id']}
            ).fetchone()
            
            if existing_message:
                return jsonify({
                    'code': SUCCESS_CODE,
                    'data': {"id": existing_message[0], "status": "already_exists"},
                    'message': "消息已存在"
                }), 200
            
            # 创建消息记录
            message_data = {
                'message_id': data['message_id'],
                'user_id': data['user_id'],
                'title': data['title'],
                'content': data['content'],
                'message_type': data.get('message_type', 'GENERAL'),
                'payload': json.dumps(data.get('payload', {})) if data.get('payload') else None,
                'is_read': data.get('is_read', False),
                'read_time': datetime.fromisoformat(data['read_time']) if data.get('read_time') else None,
                'created_time': datetime.now(),
                'updated_time': datetime.now(),
                'device_info': json.dumps(data.get('device_info', {})) if data.get('device_info') else None,
                'source': data.get('source', 'JAVA_BACKEND'),
                'target_page': data.get('target_page'),
                'priority': data.get('priority', 'NORMAL'),
                'expires_at': datetime.fromisoformat(data['expires_at']) if data.get('expires_at') else None
            }
            
            # 插入数据库
            insert_sql = text("""
                INSERT INTO m_app_message (
                    message_id, user_id, title, content, message_type, payload, 
                    is_read, read_time, created_time, updated_time, device_info, 
                    source, target_page, priority, expires_at
                ) VALUES (
                    :message_id, :user_id, :title, :content, :message_type, :payload,
                    :is_read, :read_time, :created_time, :updated_time, :device_info,
                    :source, :target_page, :priority, :expires_at
                )
            """)
            
            result = session.execute(insert_sql, message_data)
            session.commit()
            
            logger.info(f"保存WebSocket消息成功: {data['message_id']}")
            
            return jsonify({
                'code': SUCCESS_CODE,
                'data': {
                    "message_id": data['message_id'],
                    "user_id": data['user_id'],
                    "created_time": message_data['created_time'].strftime('%Y-%m-%d %H:%M:%S'),
                    "message_type": message_data['message_type'],
                    "status": "saved"
                },
                'message': "消息保存成功"
            }), 200
            
        except Exception as e:
            session.rollback()
            logger.error(f"保存WebSocket消息失败: {str(e)}")
            return jsonify({
                'code': SYSTEM_ERROR_CODE,
                'data': None,
                'message': f"保存消息失败: {str(e)}"
            }), 500
        finally:
            session.close()
            
    except Exception as e:
        logger.error(f"WebSocket消息保存接口异常: {str(e)}")
        return jsonify({
            'code': SYSTEM_ERROR_CODE,
            'data': None,
            'message': f"接口异常: {str(e)}"
        }), 500

@websocket_message.route('/messages', methods=['GET'])
def get_messages():
    """
    获取用户的WebSocket消息列表
    支持分页、筛选、搜索
    """
    try:
        # 获取查询参数
        user_id = request.args.get('user_id')
        page = int(request.args.get('page', 1))
        page_size = min(int(request.args.get('page_size', 20)), 100)  # 限制最大页面大小
        message_type = request.args.get('message_type')
        is_read = request.args.get('is_read')
        keyword = request.args.get('keyword', '').strip()
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        priority = request.args.get('priority')
        source = request.args.get('source')
        
        if not user_id:
            return jsonify({
                'code': PARAM_ERROR_CODE,
                'data': None,
                'message': "缺少用户ID参数"
            }), 400
        
        Session = sessionmaker(bind=current_app.config['DATABASE_ENGINE'])
        session = Session()
        
        try:
            # 构建查询条件
            conditions = ["user_id = :user_id"]
            params = {"user_id": user_id}
            
            if message_type:
                conditions.append("message_type = :message_type")
                params["message_type"] = message_type
            
            if is_read is not None:
                conditions.append("is_read = :is_read")
                params["is_read"] = is_read.lower() == 'true'
            
            if keyword:
                conditions.append("(title LIKE :keyword OR content LIKE :keyword)")
                params["keyword"] = f"%{keyword}%"
            
            if start_date:
                try:
                    start_dt = datetime.strptime(start_date, '%Y-%m-%d')
                    conditions.append("created_time >= :start_date")
                    params["start_date"] = start_dt
                except ValueError:
                    pass
            
            if end_date:
                try:
                    end_dt = datetime.strptime(end_date, '%Y-%m-%d')
                    end_dt = end_dt.replace(hour=23, minute=59, second=59)
                    conditions.append("created_time <= :end_date")
                    params["end_date"] = end_dt
                except ValueError:
                    pass
            
            if priority:
                conditions.append("priority = :priority")
                params["priority"] = priority
            
            if source:
                conditions.append("source = :source")
                params["source"] = source
            
            # 添加过期时间筛选
            conditions.append("(expires_at IS NULL OR expires_at > :now)")
            params["now"] = datetime.now()
            
            where_clause = " AND ".join(conditions)
            
            # 查询总数
            count_sql = text(f"SELECT COUNT(*) FROM m_app_message WHERE {where_clause}")
            total_count = session.execute(count_sql, params).scalar()
            
            # 查询数据
            offset = (page - 1) * page_size
            query_sql = text(f"""
                SELECT 
                    id, message_id, user_id, title, content, message_type, payload,
                    is_read, read_time, created_time, updated_time, device_info,
                    source, target_page, priority, expires_at
                FROM m_app_message 
                WHERE {where_clause}
                ORDER BY created_time DESC
                LIMIT :page_size OFFSET :offset
            """)
            
            params.update({"page_size": page_size, "offset": offset})
            result = session.execute(query_sql, params).fetchall()
            
            # 格式化返回数据
            messages = []
            for row in result:
                message = {
                    "id": row[0],
                    "message_id": row[1],
                    "user_id": row[2],
                    "title": row[3],
                    "content": row[4],
                    "message_type": row[5],
                    "payload": json.loads(row[6]) if row[6] else None,
                    "is_read": bool(row[7]),
                    "read_time": row[8].strftime('%Y-%m-%d %H:%M:%S') if row[8] else None,
                    "created_time": row[9].strftime('%Y-%m-%d %H:%M:%S') if row[9] else None,
                    "updated_time": row[10].strftime('%Y-%m-%d %H:%M:%S') if row[10] else None,
                    "device_info": json.loads(row[11]) if row[11] else None,
                    "source": row[12],
                    "target_page": row[13],
                    "priority": row[14],
                    "expires_at": row[15].strftime('%Y-%m-%d %H:%M:%S') if row[15] else None
                }
                messages.append(message)
            
            # 分页信息
            pagination = {
                "current_page": page,
                "page_size": page_size,
                "total_count": total_count,
                "total_pages": (total_count + page_size - 1) // page_size,
                "has_next": page * page_size < total_count,
                "has_prev": page > 1
            }
            
            # 过滤器信息
            filters = {
                "message_type": message_type,
                "is_read": is_read,
                "keyword": keyword,
                "start_date": start_date,
                "end_date": end_date,
                "priority": priority,
                "source": source
            }
            
            return jsonify({
                'code': SUCCESS_CODE,
                'data': {
                    "messages": messages,
                    "pagination": pagination,
                    "filters": filters
                },
                'message': 'success'
            }), 200
            
        except Exception as e:
            logger.error(f"获取WebSocket消息列表失败: {str(e)}")
            return jsonify({
                'code': SYSTEM_ERROR_CODE,
                'data': None,
                'message': f"获取消息失败: {str(e)}"
            }), 500
        finally:
            session.close()
            
    except Exception as e:
        logger.error(f"WebSocket消息查询接口异常: {str(e)}")
        return jsonify({
            'code': SYSTEM_ERROR_CODE,
            'data': None,
            'message': f"接口异常: {str(e)}"
        }), 500

@websocket_message.route('/messages/read', methods=['POST'])
def mark_messages_read():
    """
    标记消息为已读
    支持单个或批量标记
    """
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        message_ids = data.get('message_ids', [])
        mark_all = data.get('mark_all', False)
        
        if not user_id:
            return jsonify({
                'code': PARAM_ERROR_CODE,
                'data': None,
                'message': "缺少用户ID参数"
            }), 400
        
        if not mark_all and not message_ids:
            return jsonify({
                'code': PARAM_ERROR_CODE,
                'data': None,
                'message': "请指定要标记的消息ID或选择全部标记"
            }), 400
        
        Session = sessionmaker(bind=current_app.config['DATABASE_ENGINE'])
        session = Session()
        
        try:
            read_time = datetime.now()
            
            if mark_all:
                # 标记所有未读消息为已读
                update_sql = text("""
                    UPDATE m_app_message 
                    SET is_read = TRUE, read_time = :read_time, updated_time = :updated_time
                    WHERE user_id = :user_id AND is_read = FALSE
                """)
                params = {
                    "read_time": read_time,
                    "updated_time": read_time,
                    "user_id": user_id
                }
            else:
                # 标记指定消息为已读
                placeholders = ','.join([f':msg_id_{i}' for i in range(len(message_ids))])
                update_sql = text(f"""
                    UPDATE m_app_message 
                    SET is_read = TRUE, read_time = :read_time, updated_time = :updated_time
                    WHERE user_id = :user_id AND message_id IN ({placeholders}) AND is_read = FALSE
                """)
                params = {
                    "read_time": read_time,
                    "updated_time": read_time,
                    "user_id": user_id
                }
                for i, msg_id in enumerate(message_ids):
                    params[f'msg_id_{i}'] = msg_id
            
            result = session.execute(update_sql, params)
            affected_rows = result.rowcount
            session.commit()
            
            logger.info(f"标记WebSocket消息已读成功: 用户={user_id}, 影响行数={affected_rows}")
            
            return jsonify({
                'code': SUCCESS_CODE,
                'data': {
                    "user_id": user_id,
                    "affected_count": affected_rows,
                    "read_time": read_time.strftime('%Y-%m-%d %H:%M:%S'),
                    "mark_type": "all" if mark_all else "selected",
                    "message_ids": message_ids if not mark_all else []
                },
                'message': "标记已读成功"
            }), 200
            
        except Exception as e:
            session.rollback()
            logger.error(f"标记WebSocket消息已读失败: {str(e)}")
            return jsonify({
                'code': SYSTEM_ERROR_CODE,
                'data': None,
                'message': f"标记已读失败: {str(e)}"
            }), 500
        finally:
            session.close()
            
    except Exception as e:
        logger.error(f"WebSocket消息标记已读接口异常: {str(e)}")
        return jsonify({
            'code': SYSTEM_ERROR_CODE,
            'data': None,
            'message': f"接口异常: {str(e)}"
        }), 500

@websocket_message.route('/messages/stats', methods=['GET'])
def get_message_stats():
    """
    获取用户消息统计信息
    """
    try:
        user_id = request.args.get('user_id')
        
        if not user_id:
            return jsonify({
                'code': PARAM_ERROR_CODE,
                'data': None,
                'message': "缺少用户ID参数"
            }), 400
        
        Session = sessionmaker(bind=current_app.config['DATABASE_ENGINE'])
        session = Session()
        
        try:
            # 获取统计数据
            stats_sql = text("""
                SELECT 
                    COUNT(*) as total_count,
                    SUM(CASE WHEN is_read = FALSE THEN 1 ELSE 0 END) as unread_count,
                    SUM(CASE WHEN is_read = TRUE THEN 1 ELSE 0 END) as read_count,
                    SUM(CASE WHEN message_type = 'SYSTEM' THEN 1 ELSE 0 END) as system_count,
                    SUM(CASE WHEN message_type = 'BROADCAST' THEN 1 ELSE 0 END) as broadcast_count,
                    SUM(CASE WHEN message_type = 'NOTIFICATION' THEN 1 ELSE 0 END) as notification_count,
                    SUM(CASE WHEN priority = 'HIGH' THEN 1 ELSE 0 END) as high_priority_count,
                    SUM(CASE WHEN DATE(created_time) = CURDATE() THEN 1 ELSE 0 END) as today_count,
                    SUM(CASE WHEN created_time >= DATE_SUB(NOW(), INTERVAL 7 DAY) THEN 1 ELSE 0 END) as week_count
                FROM m_app_message 
                WHERE user_id = :user_id 
                AND (expires_at IS NULL OR expires_at > :now)
            """)
            
            result = session.execute(stats_sql, {
                "user_id": user_id,
                "now": datetime.now()
            }).fetchone()
            
            # 获取最新未读消息
            latest_unread_sql = text("""
                SELECT title, created_time, message_type, priority
                FROM m_app_message 
                WHERE user_id = :user_id AND is_read = FALSE
                AND (expires_at IS NULL OR expires_at > :now)
                ORDER BY created_time DESC
                LIMIT 5
            """)
            
            latest_unread_result = session.execute(latest_unread_sql, {
                "user_id": user_id,
                "now": datetime.now()
            }).fetchall()
            
            latest_unread_messages = []
            for row in latest_unread_result:
                latest_unread_messages.append({
                    "title": row[0],
                    "created_time": row[1].strftime('%Y-%m-%d %H:%M:%S') if row[1] else None,
                    "message_type": row[2],
                    "priority": row[3]
                })
            
            stats = {
                "total_count": result[0] or 0,
                "unread_count": result[1] or 0,
                "read_count": result[2] or 0,
                "system_count": result[3] or 0,
                "broadcast_count": result[4] or 0,
                "notification_count": result[5] or 0,
                "high_priority_count": result[6] or 0,
                "today_count": result[7] or 0,
                "week_count": result[8] or 0,
                "read_rate": round((result[2] or 0) / max(result[0] or 1, 1) * 100, 2),
                "latest_unread": latest_unread_messages
            }
            
            return jsonify({
                'code': SUCCESS_CODE,
                'data': {
                    "user_id": user_id,
                    "stats": stats,
                    "generated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                },
                'message': 'success'
            }), 200
            
        except Exception as e:
            logger.error(f"获取WebSocket消息统计失败: {str(e)}")
            return jsonify({
                'code': SYSTEM_ERROR_CODE,
                'data': None,
                'message': f"获取统计失败: {str(e)}"
            }), 500
        finally:
            session.close()
            
    except Exception as e:
        logger.error(f"WebSocket消息统计接口异常: {str(e)}")
        return jsonify({
            'code': SYSTEM_ERROR_CODE,
            'data': None,
            'message': f"接口异常: {str(e)}"
        }), 500

@websocket_message.route('/messages', methods=['DELETE'])
def delete_messages():
    """
    删除WebSocket消息
    支持单个或批量删除
    """
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        message_ids = data.get('message_ids', [])
        delete_all = data.get('delete_all', False)
        delete_read_only = data.get('delete_read_only', False)
        
        if not user_id:
            return jsonify({
                'code': PARAM_ERROR_CODE,
                'data': None,
                'message': "缺少用户ID参数"
            }), 400
        
        if not delete_all and not message_ids:
            return jsonify({
                'code': PARAM_ERROR_CODE,
                'data': None,
                'message': "请指定要删除的消息ID或选择删除选项"
            }), 400
        
        Session = sessionmaker(bind=current_app.config['DATABASE_ENGINE'])
        session = Session()
        
        try:
            if delete_all:
                if delete_read_only:
                    # 只删除已读消息
                    delete_sql = text("DELETE FROM m_app_message WHERE user_id = :user_id AND is_read = TRUE")
                    params = {"user_id": user_id}
                    delete_type = "read_only"
                else:
                    # 删除所有消息
                    delete_sql = text("DELETE FROM m_app_message WHERE user_id = :user_id")
                    params = {"user_id": user_id}
                    delete_type = "all"
            else:
                # 删除指定消息
                placeholders = ','.join([f':msg_id_{i}' for i in range(len(message_ids))])
                delete_sql = text(f"DELETE FROM m_app_message WHERE user_id = :user_id AND message_id IN ({placeholders})")
                params = {"user_id": user_id}
                for i, msg_id in enumerate(message_ids):
                    params[f'msg_id_{i}'] = msg_id
                delete_type = "selected"
            
            result = session.execute(delete_sql, params)
            affected_rows = result.rowcount
            session.commit()
            
            logger.info(f"删除WebSocket消息成功: 用户={user_id}, 影响行数={affected_rows}")
            
            return jsonify({
                'code': SUCCESS_CODE,
                'data': {
                    "user_id": user_id,
                    "deleted_count": affected_rows,
                    "delete_type": delete_type,
                    "message_ids": message_ids if not delete_all else [],
                    "deleted_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                },
                'message': "删除消息成功"
            }), 200
            
        except Exception as e:
            session.rollback()
            logger.error(f"删除WebSocket消息失败: {str(e)}")
            return jsonify({
                'code': SYSTEM_ERROR_CODE,
                'data': None,
                'message': f"删除消息失败: {str(e)}"
            }), 500
        finally:
            session.close()
            
    except Exception as e:
        logger.error(f"WebSocket消息删除接口异常: {str(e)}")
        return jsonify({
            'code': SYSTEM_ERROR_CODE,
            'data': None,
            'message': f"接口异常: {str(e)}"
        }), 500

@websocket_message.route('/messages/cleanup', methods=['POST'])
def cleanup_expired_messages():
    """
    清理过期的WebSocket消息
    """
    try:
        data = request.get_json() or {}
        days_to_keep = data.get('days_to_keep', 30)  # 默认保留30天
        user_id = data.get('user_id')  # 可选，指定用户
        
        Session = sessionmaker(bind=current_app.config['DATABASE_ENGINE'])
        session = Session()
        
        try:
            # 删除过期消息
            cleanup_time = datetime.now() - timedelta(days=days_to_keep)
            
            if user_id:
                # 清理指定用户的过期消息
                delete_sql = text("""
                    DELETE FROM m_app_message 
                    WHERE user_id = :user_id 
                    AND (created_time < :cleanup_time OR (expires_at IS NOT NULL AND expires_at < :now))
                """)
                params = {
                    "user_id": user_id,
                    "cleanup_time": cleanup_time,
                    "now": datetime.now()
                }
            else:
                # 清理所有用户的过期消息
                delete_sql = text("""
                    DELETE FROM m_app_message 
                    WHERE created_time < :cleanup_time 
                    OR (expires_at IS NOT NULL AND expires_at < :now)
                """)
                params = {
                    "cleanup_time": cleanup_time,
                    "now": datetime.now()
                }
            
            result = session.execute(delete_sql, params)
            deleted_count = result.rowcount
            session.commit()
            
            logger.info(f"清理过期WebSocket消息成功: 用户={user_id or '全部'}, 删除数量={deleted_count}")
            
            return jsonify({
                'code': SUCCESS_CODE,
                'data': {
                    "user_id": user_id,
                    "deleted_count": deleted_count,
                    "days_to_keep": days_to_keep,
                    "cleanup_time": cleanup_time.strftime('%Y-%m-%d %H:%M:%S'),
                    "cleaned_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                },
                'message': "清理过期消息成功"
            }), 200
            
        except Exception as e:
            session.rollback()
            logger.error(f"清理过期WebSocket消息失败: {str(e)}")
            return jsonify({
                'code': SYSTEM_ERROR_CODE,
                'data': None,
                'message': f"清理失败: {str(e)}"
            }), 500
        finally:
            session.close()
            
    except Exception as e:
        logger.error(f"WebSocket消息清理接口异常: {str(e)}")
        return jsonify({
            'code': SYSTEM_ERROR_CODE,
            'data': None,
            'message': f"接口异常: {str(e)}"
        }), 500

@websocket_message.route('/messages/<string:message_id>/detail', methods=['GET'])
def get_message_detail(message_id):
    """
    获取消息详情
    """
    try:
        user_id = request.args.get('user_id')
        
        if not user_id:
            return jsonify({
                'code': PARAM_ERROR_CODE,
                'data': None,
                'message': "缺少用户ID参数"
            }), 400
        
        Session = sessionmaker(bind=current_app.config['DATABASE_ENGINE'])
        session = Session()
        
        try:
            # 查询消息详情
            detail_sql = text("""
                SELECT 
                    id, message_id, user_id, title, content, message_type, payload,
                    is_read, read_time, created_time, updated_time, device_info,
                    source, target_page, priority, expires_at
                FROM m_app_message 
                WHERE message_id = :message_id AND user_id = :user_id
                AND (expires_at IS NULL OR expires_at > :now)
            """)
            
            result = session.execute(detail_sql, {
                "message_id": message_id,
                "user_id": user_id,
                "now": datetime.now()
            }).fetchone()
            
            if not result:
                return jsonify({
                    'code': MESSAGE_NOT_FOUND_CODE,
                    'data': None,
                    'message': "消息不存在或已过期"
                }), 404
            
            # 格式化消息详情
            message_detail = {
                "id": result[0],
                "message_id": result[1],
                "user_id": result[2],
                "title": result[3],
                "content": result[4],
                "message_type": result[5],
                "payload": json.loads(result[6]) if result[6] else None,
                "is_read": bool(result[7]),
                "read_time": result[8].strftime('%Y-%m-%d %H:%M:%S') if result[8] else None,
                "created_time": result[9].strftime('%Y-%m-%d %H:%M:%S') if result[9] else None,
                "updated_time": result[10].strftime('%Y-%m-%d %H:%M:%S') if result[10] else None,
                "device_info": json.loads(result[11]) if result[11] else None,
                "source": result[12],
                "target_page": result[13],
                "priority": result[14],
                "expires_at": result[15].strftime('%Y-%m-%d %H:%M:%S') if result[15] else None
            }
            
            # 如果消息未读，自动标记为已读
            if not result[7]:  # is_read = False
                read_time = datetime.now()
                update_sql = text("""
                    UPDATE m_app_message 
                    SET is_read = TRUE, read_time = :read_time, updated_time = :updated_time
                    WHERE message_id = :message_id AND user_id = :user_id
                """)
                session.execute(update_sql, {
                    "read_time": read_time,
                    "updated_time": read_time,
                    "message_id": message_id,
                    "user_id": user_id
                })
                session.commit()
                
                # 更新返回数据
                message_detail["is_read"] = True
                message_detail["read_time"] = read_time.strftime('%Y-%m-%d %H:%M:%S')
                message_detail["updated_time"] = read_time.strftime('%Y-%m-%d %H:%M:%S')
            
            return jsonify({
                'code': SUCCESS_CODE,
                'data': {
                    "message": message_detail,
                    "auto_marked_read": not result[7]  # 是否自动标记为已读
                },
                'message': 'success'
            }), 200
            
        except Exception as e:
            session.rollback()
            logger.error(f"获取WebSocket消息详情失败: {str(e)}")
            return jsonify({
                'code': SYSTEM_ERROR_CODE,
                'data': None,
                'message': f"获取消息详情失败: {str(e)}"
            }), 500
        finally:
            session.close()
            
    except Exception as e:
        logger.error(f"WebSocket消息详情接口异常: {str(e)}")
        return jsonify({
            'code': SYSTEM_ERROR_CODE,
            'data': None,
            'message': f"接口异常: {str(e)}"
        }), 500