# -*- coding: utf-8 -*-
from flask import Blueprint, request, jsonify
from app_server.service.MoviderSmsService import MoviderSmsService
from app_server.utils.Kits import Kits
from datetime import datetime

sms_verify = Blueprint('sms_verify', __name__)


@sms_verify.route('/send', methods=['POST'])
def send_verify_code():
    """
    发送验证码
    ---
    tags:
      - SMS验证码
    parameters:
      - name: phone
        in: formData
        type: string
        required: true
        description: 手机号码
    responses:
      20000:
        description: 发送成功
      50001:
        description: 发送失败
    """
    # 支持JSON和表单两种格式
    if request.is_json:
        phone = request.get_json().get('phone')
    else:
        phone = request.form.get('phone')

    if not phone:
        return jsonify({'code': 40001, 'message': 'Phone number is required'})

    # 获取IP和设备ID
    ip_address = Kits.get_real_ip(request)
    device_id = request.headers.get('X-Device-ID')

    success, result = MoviderSmsService.send_verify_code(phone, ip_address, device_id)

    if success:
        return jsonify({
            'code': 20000,
            'message': 'Verification code sent successfully',
            'data': result
        })
    else:
        return jsonify({
            'code': 50001,
            'message': result  # result已经是英文错误信息
        })


@sms_verify.route('/verify', methods=['POST'])
def verify_code():
    """
    验证验证码
    ---
    tags:
      - SMS验证码
    parameters:
      - name: phone
        in: formData
        type: string
        required: true
        description: 手机号码
      - name: code
        in: formData
        type: string
        required: true
        description: 验证码
      - name: request_id
        in: formData
        type: string
        required: false
        description: 验证请求ID（可选）
    responses:
      20000:
        description: 验证成功
      50002:
        description: 验证失败
    """
    # 支持JSON和表单两种格式
    if request.is_json:
        data = request.get_json()
        phone = data.get('phone')
        code = data.get('code')
        request_id = data.get('request_id')
    else:
        phone = request.form.get('phone')
        code = request.form.get('code')
        request_id = request.form.get('request_id')

    if not phone or not code:
        return jsonify({'code': 40001, 'message': 'Phone number and verification code are required'})

    success, error_msg = MoviderSmsService.verify_code(phone, code, request_id)

    if success:
        return jsonify({
            'code': 20000,
            'message': 'Verification successful'
        })
    else:
        return jsonify({
            'code': 50002,
            'message': error_msg or 'Verification failed'
        })


@sms_verify.route('/check_pending', methods=['POST'])
def check_pending():
    """
    检查是否有pending状态的验证码
    ---
    tags:
      - SMS验证码
    parameters:
      - name: phone
        in: formData
        type: string
        required: true
        description: 手机号码
    responses:
      20000:
        description: 有pending验证码
      40004:
        description: 无pending验证码
    """
    # 支持JSON和表单两种格式
    if request.is_json:
        phone = request.get_json().get('phone')
    else:
        phone = request.form.get('phone')

    if not phone:
        return jsonify({'code': 40001, 'message': 'Phone number is required'})

    from app_server.model.SmsVerifyLogModel import SmsVerifyLog

    # 查找最近的pending记录
    pending_record = SmsVerifyLog.query.filter_by(
        phone=phone,
        status='pending'
    ).order_by(SmsVerifyLog.sent_at.desc()).first()

    if not pending_record:
        return jsonify({
            'code': 40004,
            'message': 'No pending verification code'
        })

    # 检查是否过期
    if datetime.now() > pending_record.expired_at:
        pending_record.status = 'expired'
        from app_server import db
        db.session.commit()
        return jsonify({
            'code': 40004,
            'message': 'Verification code has expired'
        })

    # 返回pending验证码信息
    return jsonify({
        'code': 20000,
        'message': 'Pending verification code found',
        'data': {
            'request_id': pending_record.request_id,
            'phone': phone,
            'expired_at': pending_record.expired_at.strftime('%Y-%m-%d %H:%M:%S'),
            'sent_at': pending_record.sent_at.strftime('%Y-%m-%d %H:%M:%S')
        }
    })
