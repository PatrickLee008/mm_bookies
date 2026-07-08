# -*- coding: utf-8 -*-
"""
全局配置管理模块
支持任意环境配置文件(.env.{APP_ENV})
所有配置项从对应的 .env 文件中动态加载
"""
import os
import sys
from dotenv import load_dotenv

# 获取项目根目录
base_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

# 第一步：加载主配置文件.env，获取APP_ENV
main_env_path = os.path.join(base_dir, '.env')
load_dotenv(main_env_path)

# 获取当前环境
app_env = os.getenv('APP_ENV', 'local').lower()

# 第二步：根据APP_ENV加载对应的环境配置文件
env_file = f'.env.{app_env}'
env_file_path = os.path.join(base_dir, env_file)

if not os.path.exists(env_file_path):
    print(f"错误: 配置文件 {env_file} 不存在！")
    print(f"请创建 {env_file} 文件，可以参考 .env.example")
    sys.exit(1)

# 加载环境配置文件（override=True 表示覆盖之前加载的同名变量）
load_dotenv(env_file_path, override=True)

print(f"[Config] 加载配置: APP_ENV={app_env}, 配置文件={env_file}")


def get_env_required(key):
    """获取必需的环境变量，如果不存在则抛出异常"""
    value = os.getenv(key)
    if value is None:
        raise ValueError(f"配置项 {key} 未在 {env_file} 中定义！")
    return value


def get_env_int(key):
    """获取整型环境变量"""
    value = get_env_required(key)
    try:
        return int(value)
    except ValueError:
        raise ValueError(f"配置项 {key} 的值 '{value}' 不是有效的整数！")


def get_env_bool(key):
    """获取布尔型环境变量"""
    value = get_env_required(key)
    return value.lower() in ('true', '1', 'yes', 'on')


def get_env_optional(key, default=''):
    """获取可选的环境变量，如果不存在则返回默认值"""
    return os.getenv(key, default)


class Config(object):
    """
    统一配置类
    所有配置项从对应的 .env.{APP_ENV} 文件中动态读取
    """
    # 环境标识
    APP_ENV = app_env

    # 调试模式（从环境变量读取，默认为 False）
    DEBUG = get_env_bool('DEBUG') if os.getenv('DEBUG') else False
    TESTING = get_env_bool('TESTING') if os.getenv('TESTING') else False

    # 基础配置
    SECRET_KEY = get_env_required('SECRET_KEY')
    DATABASE = get_env_required('DATABASE')
    CHARGE_APPLY_PIC_DIR = os.path.join(os.path.dirname(__file__), 'static/img/charge_pics')

    # 数据库配置
    DB_ADDRESS = get_env_required('DB_ADDRESS')
    DB_PASSWORD = get_env_required('DB_PASSWORD')
    DB_USER = get_env_required('DB_USER')
    PORT = get_env_int('PORT')
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://%s:%s@%s:3306/%s?charset=utf8mb4' % (
        DB_USER, DB_PASSWORD, DB_ADDRESS, DATABASE)

    # SQLAlchemy配置
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_POOL_SIZE = get_env_int('SQLALCHEMY_POOL_SIZE')
    SQLALCHEMY_POOL_TIMEOUT = get_env_int('SQLALCHEMY_POOL_TIMEOUT')
    SQLALCHEMY_POOL_RECYCLE = get_env_int('SQLALCHEMY_POOL_RECYCLE')

    # Redis配置
    REDIS_HOST = get_env_required('REDIS_HOST')
    REDIS_PORT = get_env_int('REDIS_PORT')
    REDIS_DB = get_env_int('REDIS_DB')
    REDIS_EXPIRE = get_env_int('REDIS_EXPIRE')

    # 支付配置
    CHARGE_CALLBACK_URL = get_env_required('CHARGE_CALLBACK_URL')
    PAY_CENTER_API = get_env_required('PAY_CENTER_API')
    PAY_CENTER_APP_ID = get_env_required('PAY_CENTER_APP_ID')
    PAY_CENTER_APP_AES_SECRET = get_env_required('PAY_CENTER_APP_AES_SECRET')
    # 支付通道类型：VIPPay 或 TCPay
    PAY_CHANNEL_TYPE = get_env_optional('PAY_CHANNEL_TYPE', 'VIPPay')

    # AWC API配置
    AWC_API_ENABLED = get_env_bool('AWC_API_ENABLED')
    AWC_API_BASE_URL = get_env_required('AWC_API_BASE_URL')
    AWC_API_CERT = get_env_required('AWC_API_CERT')
    AWC_API_AGENT_ID = get_env_required('AWC_API_AGENT_ID')
    AWC_API_TIMEOUT = get_env_int('AWC_API_TIMEOUT')
    AWC_API_DEFAULT_CURRENCY = get_env_required('AWC_API_DEFAULT_CURRENCY')
    AWC_API_DEFAULT_LANGUAGE = get_env_required('AWC_API_DEFAULT_LANGUAGE')
    AWC_API_DEFAULT_BET_LIMIT = get_env_required('AWC_API_DEFAULT_BET_LIMIT')

    # AWC游戏闲置超时配置
    AWC_GAME_IDLE_TIMEOUT_ENABLED = get_env_bool('AWC_GAME_IDLE_TIMEOUT_ENABLED')
    AWC_GAME_IDLE_TIMEOUT_MINUTES = get_env_int('AWC_GAME_IDLE_TIMEOUT_MINUTES')
    AWC_GAME_IDLE_WARNING_MINUTES = get_env_int('AWC_GAME_IDLE_WARNING_MINUTES')
    AWC_GAME_AUTO_LOGOUT = get_env_bool('AWC_GAME_AUTO_LOGOUT')
    AWC_GAME_SESSION_HEARTBEAT_INTERVAL = get_env_int('AWC_GAME_SESSION_HEARTBEAT_INTERVAL')
    AWC_GAME_SESSION_MAX_DURATION = get_env_int('AWC_GAME_SESSION_MAX_DURATION')

    # Movider SMS验证码配置
    MOVIDER_API_KEY = get_env_required('MOVIDER_API_KEY')
    MOVIDER_API_SECRET = get_env_required('MOVIDER_API_SECRET')
    MOVIDER_API_BASE_URL = get_env_optional('MOVIDER_API_BASE_URL', 'https://api.movider.co/v1')
    MOVIDER_SENDER_NAME = get_env_optional('MOVIDER_SENDER_NAME', '')
    MOVIDER_CODE_LENGTH = get_env_int('MOVIDER_CODE_LENGTH') if os.getenv('MOVIDER_CODE_LENGTH') else 6
    MOVIDER_CODE_EXPIRE_MINUTES = get_env_int('MOVIDER_CODE_EXPIRE_MINUTES') if os.getenv('MOVIDER_CODE_EXPIRE_MINUTES') else 5
    MOVIDER_MAX_VERIFY_ATTEMPTS = get_env_int('MOVIDER_MAX_VERIFY_ATTEMPTS') if os.getenv('MOVIDER_MAX_VERIFY_ATTEMPTS') else 3
    MOVIDER_RATE_LIMIT_PER_PHONE = get_env_int('MOVIDER_RATE_LIMIT_PER_PHONE') if os.getenv('MOVIDER_RATE_LIMIT_PER_PHONE') else 3

def get_config():
    """
    获取配置类
    返回统一的 Config 类，所有配置项从 .env.{APP_ENV} 文件中动态加载
    """
    return Config
