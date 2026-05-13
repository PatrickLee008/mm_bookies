# -*- coding: utf-8 -*-
import requests
from flask import current_app
from datetime import datetime, timedelta
from app_server import db
from app_server.model.SmsVerifyLogModel import SmsVerifyLog
from app_server.utils.Kits import Kits
from app_server.logger import get_logger

logger = get_logger()


class MoviderSmsService:
    """Movider短信验证码服务"""

    # 测试号码列表（跳过真实API调用）
    TEST_PHONES = ['09123456789', '09999999999']
    TEST_VERIFY_CODE = '123456'  # 测试验证码

    @staticmethod
    def _format_phone_e164(phone):
        """
        将手机号转换为Movider API要求的格式（纯数字，不带+号）
        支持的国家格式：
        - 缅甸: 09xxxxxxxx -> 959xxxxxxxx
        - 泰国: 08xxxxxxxx/06xxxxxxxx/09xxxxxxxx -> 668xxxxxxxx/666xxxxxxxx/669xxxxxxxx
        - 中国: 1xxxxxxxxxx (11位) -> 861xxxxxxxxxx
        - 国际格式: +xxxx -> xxxx (去掉+号)
        """
        phone = phone.strip().replace(' ', '').replace('-', '')

        # 如果是+开头，去掉+号（国际格式）
        if phone.startswith('+'):
            return phone[1:]

        # 缅甸号码：09开头，转换为 959xxxxxxxx
        elif phone.startswith('09'):
            return '95' + phone[1:]

        # 泰国号码：08/06开头，转换为 668/666xxxxxxxx
        elif phone.startswith('08') or phone.startswith('06'):
            return '66' + phone[1:]

        # 中国号码：1开头且长度为11位，转换为 861xxxxxxxxxx
        elif phone.startswith('1') and len(phone) == 11:
            return '86' + phone

        # 其他情况，直接返回（可能已经是正确的国际格式）
        else:
            return phone

    @staticmethod
    def check_rate_limit(phone):
        """
        检查发送频率限制
        返回：(is_allowed, remaining_count, error_message)
        """
        config = current_app.config
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)

        # 查询今天已发送次数
        sent_count = SmsVerifyLog.query.filter(
            SmsVerifyLog.phone == phone,
            SmsVerifyLog.sent_at >= today_start,
            SmsVerifyLog.sent_at < today_end
        ).count()

        max_count = config.get('MOVIDER_RATE_LIMIT_PER_PHONE', 3)

        if sent_count >= max_count:
            return False, 0, f"Daily send limit reached ({max_count} times). Please try again tomorrow."

        return True, max_count - sent_count, None

    @staticmethod
    def check_resend_interval(phone):
        """
        检查重发间隔（防止短时间内重复发送）
        返回：(is_allowed, wait_seconds, error_message)
        """
        # 只查询最近一次pending状态的记录（verified/failed/expired状态的不限制重发）
        last_record = SmsVerifyLog.query.filter(
            SmsVerifyLog.phone == phone,
            SmsVerifyLog.status == 'pending'
        ).order_by(SmsVerifyLog.sent_at.desc()).first()

        if last_record:
            # 如果上次验证码还未过期，不允许重发
            if last_record.expired_at > datetime.now():
                wait_seconds = int((last_record.expired_at - datetime.now()).total_seconds())
                return False, wait_seconds, f"Verification code is still valid. Please try again in {wait_seconds} seconds."

        return True, 0, None

    @staticmethod
    def send_verify_code(phone, ip_address=None, device_id=None):
        """
        发送验证码
        返回：(success, data/error_message)
        """
        config = current_app.config

        # 1. 格式化手机号
        phone_e164 = MoviderSmsService._format_phone_e164(phone)

        # 2. 检查频率限制
        is_allowed, remaining, error_msg = MoviderSmsService.check_rate_limit(phone)
        if not is_allowed:
            logger.warning(f"手机号 {phone} 发送频率超限: {error_msg}")
            return False, error_msg

        # 3. 检查重发间隔
        is_allowed, wait_seconds, error_msg = MoviderSmsService.check_resend_interval(phone)
        if not is_allowed:
            logger.warning(f"手机号 {phone} 重发间隔限制: {error_msg}")
            return False, error_msg

        # 4. 测试模式：如果是测试号码，跳过真实API调用
        if phone in MoviderSmsService.TEST_PHONES:
            logger.info(f"[测试模式] 手机号 {phone} 跳过真实API调用，使用模拟数据")

            # 生成模拟的request_id
            test_request_id = f"TEST_{str(Kits.generate_uuid())[:8]}"

            # 记录到数据库
            log_record = SmsVerifyLog(
                id=str(Kits.generate_uuid()),
                phone=phone,
                request_id=test_request_id,
                code_length=config['MOVIDER_CODE_LENGTH'],
                status='pending',
                sent_at=datetime.now(),
                expired_at=datetime.now() + timedelta(minutes=config['MOVIDER_CODE_EXPIRE_MINUTES']),
                ip_address=ip_address,
                device_id=device_id
            )
            db.session.add(log_record)
            db.session.commit()

            logger.info(f"[测试模式] 验证码发送成功: phone={phone}, request_id={test_request_id}, 测试验证码={MoviderSmsService.TEST_VERIFY_CODE}")

            return True, {
                'request_id': test_request_id,
                'phone': phone,
                'expired_at': log_record.expired_at.strftime('%Y-%m-%d %H:%M:%S'),
                'remaining_count': remaining - 1,
                'test_mode': True,
                'test_code': MoviderSmsService.TEST_VERIFY_CODE  # 测试模式下直接返回验证码
            }

        # 5. 调用Movider API（真实号码）
        api_url = f"{config['MOVIDER_API_BASE_URL']}/verify"
        payload = {
            'api_key': config['MOVIDER_API_KEY'],
            'api_secret': config['MOVIDER_API_SECRET'],
            'to': phone_e164,
            'code_length': str(config['MOVIDER_CODE_LENGTH'])
        }

        # 如果配置了发送者名称
        if config.get('MOVIDER_SENDER_NAME'):
            payload['from'] = config['MOVIDER_SENDER_NAME']

        try:
            response = requests.post(api_url, data=payload, timeout=30)

            # 记录详细的响应信息，便于调试
            logger.info(f"Movider API响应: status_code={response.status_code}, body={response.text}")

            response.raise_for_status()
            result = response.json()

            # 5. 记录到数据库
            log_record = SmsVerifyLog(
                id=str(Kits.generate_uuid()),
                phone=phone,
                request_id=result.get('request_id'),
                code_length=config['MOVIDER_CODE_LENGTH'],
                status='pending',
                sent_at=datetime.now(),
                expired_at=datetime.now() + timedelta(minutes=config['MOVIDER_CODE_EXPIRE_MINUTES']),
                ip_address=ip_address,
                device_id=device_id
            )
            db.session.add(log_record)
            db.session.commit()

            logger.info(f"验证码发送成功: phone={phone}, request_id={result.get('request_id')}")

            return True, {
                'request_id': result.get('request_id'),
                'phone': phone,
                'expired_at': log_record.expired_at.strftime('%Y-%m-%d %H:%M:%S'),
                'remaining_count': remaining - 1
            }

        except requests.exceptions.HTTPError as e:
            # HTTP错误（如400, 401, 500等）
            error_detail = ""
            try:
                error_response = e.response.json()
                error_detail = f" - {error_response}"
            except:
                error_detail = f" - {e.response.text}"

            error_msg = f"Movider API调用失败: {str(e)}{error_detail}"
            logger.error(error_msg)
            return False, f"Failed to send SMS. Please try again later. (Error code: {e.response.status_code})"
        except requests.exceptions.RequestException as e:
            error_msg = f"Movider API调用失败: {str(e)}"
            logger.error(error_msg)
            return False, "SMS service is temporarily unavailable. Please try again later."
        except Exception as e:
            error_msg = f"发送验证码异常: {str(e)}"
            logger.error(error_msg)
            db.session.rollback()
            return False, f"Failed to send verification code: {str(e)}"

    @staticmethod
    def verify_code(phone, code, request_id=None):
        """
        验证验证码
        返回：(success, error_message)
        """
        config = current_app.config

        # 1. 查找验证码记录
        if request_id:
            log_record = SmsVerifyLog.query.filter_by(
                request_id=request_id,
                phone=phone,
                status='pending'
            ).first()
        else:
            # 如果没有request_id，查找最近的pending记录
            log_record = SmsVerifyLog.query.filter_by(
                phone=phone,
                status='pending'
            ).order_by(SmsVerifyLog.sent_at.desc()).first()

        if not log_record:
            return False, "Verification code does not exist or has expired"

        # 2. 检查是否过期
        if datetime.now() > log_record.expired_at:
            log_record.status = 'expired'
            db.session.commit()
            return False, "Verification code has expired"

        # 3. 检查验证次数
        if log_record.verify_attempts >= config['MOVIDER_MAX_VERIFY_ATTEMPTS']:
            log_record.status = 'failed'
            db.session.commit()
            return False, f"Verification attempts exceeded ({config['MOVIDER_MAX_VERIFY_ATTEMPTS']} times)"

        # 4. 测试模式：如果是测试号码，直接验证
        if phone in MoviderSmsService.TEST_PHONES:
            logger.info(f"[测试模式] 手机号 {phone} 跳过真实API调用，使用模拟验证")

            # 增加验证次数
            log_record.verify_attempts += 1
            db.session.commit()

            # 验证测试验证码
            if code == MoviderSmsService.TEST_VERIFY_CODE:
                log_record.status = 'verified'
                log_record.verified_at = datetime.now()
                log_record.code = code
                db.session.commit()
                logger.info(f"[测试模式] 验证码验证成功: phone={phone}, request_id={log_record.request_id}")
                return True, None
            else:
                # 验证失败
                remaining_attempts = config['MOVIDER_MAX_VERIFY_ATTEMPTS'] - log_record.verify_attempts
                if remaining_attempts <= 0:
                    log_record.status = 'failed'
                    db.session.commit()
                error_msg = f"Incorrect verification code. {remaining_attempts} attempts remaining."
                log_record.error_message = error_msg
                db.session.commit()
                logger.warning(f"[测试模式] 验证码错误: phone={phone}, 输入={code}, 正确={MoviderSmsService.TEST_VERIFY_CODE}")
                return False, error_msg

        # 5. 调用Movider验证API（真实号码）
        api_url = f"{config['MOVIDER_API_BASE_URL']}/verify/acknowledge"
        payload = {
            'api_key': config['MOVIDER_API_KEY'],
            'api_secret': config['MOVIDER_API_SECRET'],
            'request_id': log_record.request_id,
            'code': code
        }

        try:
            log_record.verify_attempts += 1
            db.session.commit()

            response = requests.post(api_url, data=payload, timeout=30)
            response.raise_for_status()
            result = response.json()

            # 6. 处理验证结果
            if result.get('status') == 'success' or response.status_code == 200:
                log_record.status = 'verified'
                log_record.verified_at = datetime.now()
                log_record.code = code  # 记录验证成功的验证码
                db.session.commit()
                logger.info(f"验证码验证成功: phone={phone}, request_id={log_record.request_id}")
                return True, None
            else:
                # 验证失败
                remaining_attempts = config['MOVIDER_MAX_VERIFY_ATTEMPTS'] - log_record.verify_attempts
                if remaining_attempts <= 0:
                    log_record.status = 'failed'
                    db.session.commit()
                error_msg = f"Incorrect verification code. {remaining_attempts} attempts remaining."
                log_record.error_message = error_msg
                db.session.commit()
                return False, error_msg

        except requests.exceptions.RequestException as e:
            error_msg = f"Movider验证API调用失败: {str(e)}"
            logger.error(error_msg)
            log_record.error_message = error_msg
            db.session.commit()
            return False, "Verification service is temporarily unavailable. Please try again later."
        except Exception as e:
            error_msg = f"验证验证码异常: {str(e)}"
            logger.error(error_msg)
            db.session.rollback()
            return False, "Verification failed. Please try again."

    @staticmethod
    def cancel_verify(request_id):
        """
        取消验证码
        """
        config = current_app.config
        api_url = f"{config['MOVIDER_API_BASE_URL']}/verify/cancel"
        payload = {
            'api_key': config['MOVIDER_API_KEY'],
            'api_secret': config['MOVIDER_API_SECRET'],
            'request_id': request_id
        }

        try:
            response = requests.post(api_url, data=payload, timeout=30)
            response.raise_for_status()

            # 更新数据库记录
            log_record = SmsVerifyLog.query.filter_by(request_id=request_id).first()
            if log_record:
                log_record.status = 'cancelled'
                db.session.commit()

            logger.info(f"验证码已取消: request_id={request_id}")
            return True, None

        except Exception as e:
            error_msg = f"取消验证码失败: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
