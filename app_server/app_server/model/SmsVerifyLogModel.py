# -*- coding: utf-8 -*-
from app_server import db
from datetime import datetime


class SmsVerifyLog(db.Model):
    """短信验证码记录表"""
    __tablename__ = 'm_sms_verify_log'

    id = db.Column(db.String(64), primary_key=True, comment='主键UUID')
    phone = db.Column(db.String(20), nullable=False, index=True, comment='手机号码')
    request_id = db.Column(db.String(128), index=True, comment='Movider返回的request_id')
    code = db.Column(db.String(10), comment='验证码（加密存储）')
    code_length = db.Column(db.Integer, default=6, comment='验证码长度')
    status = db.Column(db.String(20), nullable=False, index=True,
                       comment='状态: pending/verified/failed/cancelled/expired')
    verify_attempts = db.Column(db.Integer, default=0, comment='验证尝试次数')
    sent_at = db.Column(db.DateTime, nullable=False, index=True, comment='发送时间')
    verified_at = db.Column(db.DateTime, comment='验证通过时间')
    expired_at = db.Column(db.DateTime, nullable=False, comment='过期时间')
    ip_address = db.Column(db.String(45), comment='请求IP地址')
    device_id = db.Column(db.String(128), comment='设备ID')
    error_message = db.Column(db.Text, comment='错误信息')
    created_at = db.Column(db.DateTime, default=datetime.now, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')

    def __repr__(self):
        return f'<SmsVerifyLog {self.phone} - {self.status}>'


db.create_all()
