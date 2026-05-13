import random
import uuid
import base64
import json

import pytz
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from datetime import datetime, timezone
from typing import List
from decimal import Decimal

from flask import jsonify
from user_agents import parse
from .snowflake import SnowflakeIdGenerator

# 单例实例
_snowflake_gen = SnowflakeIdGenerator(worker_id=1, datacenter_id=1)

# 工具包
class Kits:
    @staticmethod
    def rt_data(data):
        # 先判断是否是简单数据类型，然后再判断是否是字典类型，最后判断是否是对象类型
        # 简单数据类型：str、int、float、bool、list、tuple、set、dict
        # 字典类型：字典类型
        # 对象类型：对象类型
        # 最后返回json数据
        if isinstance(data, (str, int, float, bool, list, tuple, set, dict)):
            return jsonify({'code': 200, 'data': data})
        elif not isinstance(data, dict):
            data = data.to_dict() if hasattr(data, 'to_dict') else data
        return jsonify({'code': 200, 'data': data})

    @staticmethod
    def rt_ok(message):
        return jsonify({'code': 200, 'message': message})

    @staticmethod
    def rt_code(code, message, data=None):
        return jsonify({'code': code, 'message': message, 'ok': True, 'data': data})

    @staticmethod
    def rt_error(message):
        response = jsonify({'code': 502, 'message': message, 'ok': False})
        response.status_code = 500
        return response

    @staticmethod
    def ok(message):
        return {'code': 200, 'message': 'success', 'ok': True}

    @staticmethod
    def ok_data(data):
        return {'code': 200, 'message': 'success', 'ok': True, 'data': data}

    @staticmethod
    def error(message):
        return {'code': 502, 'message': message, 'ok': False}

    def is_empty(arg):
        # 判断是否存在空值，存在则返回True
        return True if arg is None or arg == '' or arg == [] or arg == {} or arg == 'null' or arg == 'undefined' or arg == 'None' else False

    @staticmethod
    def is_all_empty(*args):
        # 判断是否存在空值，存在则返回True
        for arg in args:
            empty = Kits.is_empty(arg)
            if not empty:
                return False
        return True

    @staticmethod
    def is_not_empty(*args):
        # 判断所有参赛是否都是非空，有空则返回False
        for arg in args:
            if arg is None or arg == '' or arg == [] or arg == {} or arg == 'null' or arg == 'undefined' or arg == 'None':
                return False
        return True

    #生成UUID
    @staticmethod
    def generate_uuid():
        # 换成雪花ID
        return _snowflake_gen.generate_id()
        #return str(uuid.uuid4()).replace('-', '')

    # 生成指定位数的随机数字
    @staticmethod
    def generate_random_number(length=4):
        """
        生成指定位数的随机数字

        Args:
            length: 数字位数，默认4位

        Returns:
            str: 随机数字字符串
        """
        return ''.join([str(random.randint(0, 9)) for _ in range(length)])

    @staticmethod
    def get_real_ip(request):
        """
        获取客户端真实IP地址（支持 Nginx 反向代理）
        优先级：X-Forwarded-For > X-Real-IP > Proxy-Client-IP > WL-Proxy-Client-IP > remote_addr
        """
        # 1. 尝试从 X-Forwarded-For 获取（可能包含多个IP，取第一个）
        x_forwarded_for = request.headers.get('X-Forwarded-For')
        if x_forwarded_for:
            # X-Forwarded-For 格式: client_ip, proxy1_ip, proxy2_ip
            ip = x_forwarded_for.split(',')[0].strip()
            if ip and ip != 'unknown':
                return ip

        # 2. 尝试从 X-Real-IP 获取
        x_real_ip = request.headers.get('X-Real-IP')
        if x_real_ip and x_real_ip != 'unknown':
            return x_real_ip

        # 3. 尝试从其他常见代理头获取
        proxy_client_ip = request.headers.get('Proxy-Client-IP')
        if proxy_client_ip and proxy_client_ip != 'unknown':
            return proxy_client_ip

        wl_proxy_client_ip = request.headers.get('WL-Proxy-Client-IP')
        if wl_proxy_client_ip and wl_proxy_client_ip != 'unknown':
            return wl_proxy_client_ip

        # 4. 最后使用 remote_addr
        return request.remote_addr

    # 获取客户端信息
    @staticmethod
    def client_info(request):
        # 获取客户端信息
        # {"os": "Windows", "device": "Unknown", "is_bot": false, "browser": "Edge", "ip_address": "2405:9800:b910:1784:18b:34dd:1bce:9cfb", "last_login": "2025-02-26T04:01:52.722Z", "user_agent": "Edge 133.0.0.0 Windows 10 undefined Blink 133.0.0.0 amd64"}
        # 解析 User-Agent 字符串
        user_agent = request.headers.get('User-Agent')
        if user_agent:
            user_agent_info = parse(user_agent)
        else:
            user_agent_info = None
        if not user_agent_info:
            return {}

        # 获取客户端信息
        info = {
            "os": user_agent_info.os.family if user_agent_info.os else "Unknown",
            "device": user_agent_info.device.family if user_agent_info.device else "Unknown",
            "is_bot": user_agent_info.is_bot if user_agent_info else False,
            "browser": user_agent_info.browser.family if user_agent_info.browser else "Unknown",
            "ip_address": Kits.get_real_ip(request),
            "last_login": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "user_agent": user_agent
        }
        return info  # 返回客户端信息

    @staticmethod
    def get_behavior_log_headers(request):
        """
        从请求头获取行为日志相关参数

        Args:
            request: Flask request对象

        Returns:
            dict: 包含 app_version 和 access_channel 的字典
        """
        return {
            'app_version': request.headers.get('app_version') or request.headers.get('App-Version'),
            'access_channel': request.headers.get('access_channel') or request.headers.get('Access-Channel')
        }

    @staticmethod
    def encrypt(plain_text: str, secret_key: str) -> str:
        """加密数据"""
        # 解码 Base64 密钥
        key = base64.b64decode(secret_key)

        # 确保明文是字节并填充到块大小
        plain_bytes = plain_text.encode('utf-8')
        cipher = AES.new(key, AES.MODE_ECB)  # 默认 ECB 模式（与 Java 兼容）
        encrypted_bytes = cipher.encrypt(pad(plain_bytes, AES.block_size))

        return base64.b64encode(encrypted_bytes).decode('utf-8')

    @staticmethod
    def decrypt(encrypted_text: str, secret_key: str) -> str:
        """解密数据"""
        # 解码 Base64 密钥和密文
        key = base64.b64decode(secret_key)
        encrypted_bytes = base64.b64decode(encrypted_text)

        cipher = AES.new(key, AES.MODE_ECB)
        decrypted_bytes = unpad(cipher.decrypt(encrypted_bytes), AES.block_size)

        return decrypted_bytes.decode('utf-8')

    @staticmethod
    def json_dumps(obj) -> str:
        """将Python对象编码为JSON字符串"""
        try:
            return json.dumps(obj, ensure_ascii=False, separators=(',', ':'))
        except (TypeError, ValueError) as e:
            raise ValueError(f"JSON编码失败: {str(e)}")

    @staticmethod
    def json_loads(json_str: str):
        """将JSON字符串解码为Python对象"""
        try:
            return json.loads(json_str)
        except (TypeError, ValueError) as e:
            raise ValueError(f"JSON解码失败: {str(e)}")

    @staticmethod
    def decimal_to_float(data):
        """
        将对象中的Decimal属性转换为float类型
        支持字典、列表、对象等多种数据结构
        :param data: 需要转换的数据（字典、列表、对象等）
        :return: 转换后的数据
        """
        if data is None:
            return None

        # 处理Decimal类型
        if isinstance(data, Decimal):
            return float(data)

        # 处理字典类型
        elif isinstance(data, dict):
            return {key: Kits.decimal_to_float(value) for key, value in data.items()}

        # 处理列表类型
        elif isinstance(data, list):
            return [Kits.decimal_to_float(item) for item in data]

        # 处理元组类型
        elif isinstance(data, tuple):
            return tuple(Kits.decimal_to_float(item) for item in data)

        # 处理对象类型（有__dict__属性的对象）
        elif hasattr(data, '__dict__'):
            # 创建对象的副本，避免修改原对象
            obj_dict = data.__dict__.copy()
            for key, value in obj_dict.items():
                if isinstance(value, Decimal):
                    setattr(data, key, float(value))
                elif isinstance(value, (dict, list, tuple)):
                    setattr(data, key, Kits.decimal_to_float(value))
                elif hasattr(value, '__dict__'):
                    Kits.decimal_to_float(value)
            return data

        # 其他类型直接返回
        else:
            return data

    @staticmethod
    def convert_timezone_time(source_timezone_str, source_time_str, target_timezone_str='Asia/Shanghai', return_type='datetime'):
        """
        通用时区时间转换方法

        Args:
            source_timezone_str: 源时区字符串，如 'Asia/Shanghai', 'UTC', 'America/New_York' 等
            source_time_str: 源时区的时间字符串，格式为 '%Y-%m-%d %H:%M:%S'
            target_timezone_str: 目标时区字符串，默认为 'Asia/Shanghai'
            return_type: 返回类型，'datetime' 返回日期时间字符串，'date' 返回日期字符串

        Returns:
            str: 转换后的日期或日期时间字符串
        """
        # 创建源时区对象
        source_timezone = pytz.timezone(source_timezone_str)

        # 将源时间字符串解析为datetime对象
        source_datetime = datetime.strptime(source_time_str, '%Y-%m-%d %H:%M:%S')

        # 将源时间标记为源时区
        source_datetime_with_tz = source_timezone.localize(source_datetime)

        # 转换到目标时区
        target_timezone = pytz.timezone(target_timezone_str)
        target_datetime = source_datetime_with_tz.astimezone(target_timezone)

        # 根据返回类型决定输出格式
        if return_type == 'date':
            return target_datetime.strftime('%Y-%m-%d')
        else:  # 默认返回datetime
            return target_datetime.strftime('%Y-%m-%d %H:%M:%S')

    @staticmethod
    def user_time_to_system_time(user_timezone_str, user_date_time_str):
        """
        用户时区时间转系统时间（Asia/Shanghai）

        Args:
            user_timezone_str: 用户时区字符串，如 'Asia/Shanghai', 'UTC', 'America/New_York' 等
            user_date_time_str: 用户时区的时间字符串，格式为 '%Y-%m-%d %H:%M:%S'

        Returns:
            str: 系统时间（上海时区）的字符串，格式为 '%Y-%m-%d %H:%M:%S'
        """
        return Kits.convert_timezone_time(
            source_timezone_str=user_timezone_str,
            source_time_str=user_date_time_str,
            target_timezone_str='Asia/Shanghai',
            return_type='datetime'
        )

    @staticmethod
    def user_time_to_system_date(user_timezone_str, user_date_time_str):
        """
        用户时区时间转系统日期（Asia/Shanghai）

        Args:
            user_timezone_str: 用户时区字符串
            user_date_time_str: 用户时区的时间字符串，格式为 '%Y-%m-%d %H:%M:%S'

        Returns:
            str: 系统日期（上海时区）的字符串，格式为 '%Y-%m-%d'
        """
        return Kits.convert_timezone_time(
            source_timezone_str=user_timezone_str,
            source_time_str=user_date_time_str,
            target_timezone_str='Asia/Shanghai',
            return_type='date'
        )

    @staticmethod
    def system_time_to_user_time(user_timezone_str='Asia/Yangon', system_date_time_str=None,
                                 system_timezone_str='Asia/Shanghai'):
        """
        系统时间转用户时间

        Args:
            system_timezone_str: 系统时区字符串，默认为 'Asia/Shanghai'
            system_date_time_str: 系统时间字符串，格式为 '%Y-%m-%d %H:%M:%S'，如果为None则使用当前时间
            user_timezone_str: 用户时区字符串

        Returns:
            str: 用户时间（用户时区）的字符串，格式为 '%Y-%m-%d %H:%M:%S'
        """
        if system_date_time_str is None:
            # 如果没有提供系统时间，则使用当前系统时间
            system_date_time_str = datetime.now(pytz.timezone(system_timezone_str)).strftime('%Y-%m-%d %H:%M:%S')

        return Kits.convert_timezone_time(
            source_timezone_str=system_timezone_str,
            source_time_str=system_date_time_str,
            target_timezone_str=user_timezone_str,
            return_type='datetime'
        )

    @staticmethod
    def system_time_to_user_date(user_timezone_str='Asia/Yangon', system_date_time_str=None,
                                 system_timezone_str='Asia/Shanghai'):
        """
        系统时间转用户日期

        Args:
            system_timezone_str: 系统时区字符串，默认为 'Asia/Shanghai'
            system_date_time_str: 系统时间字符串，格式为 '%Y-%m-%d %H:%M:%S'，如果为None则使用当前时间
            user_timezone_str: 用户时区字符串

        Returns:
            str: 用户日期（用户时区）的字符串，格式为 '%Y-%m-%d'
        """
        if system_date_time_str is None:
            # 如果没有提供系统时间，则使用当前系统时间
            system_date_time_str = datetime.now(pytz.timezone(system_timezone_str)).strftime('%Y-%m-%d %H:%M:%S')

        return Kits.convert_timezone_time(
            source_timezone_str=system_timezone_str,
            source_time_str=system_date_time_str,
            target_timezone_str=user_timezone_str,
            return_type='date'
        )


