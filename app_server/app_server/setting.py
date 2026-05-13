# -*- coding: utf-8 -*-
# 此处修改配置参数
import os

base_dir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    DEBUG = False
    TESTING = False
    SECRET_KEY = 'abc123'
    DATABASE = "elszuqiu"
    CHARGE_APPLY_PIC_DIR = os.path.join(base_dir, 'static/img/charge_pics')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_POOL_SIZE = 10000
    SQLALCHEMY_POOL_TIMEOUT = 10
    SQLALCHEMY_POOL_RECYCLE = 10600

    REDIS_HOST = "127.0.0.1"
    REDIS_PORT = 6379
    REDIS_DB = 0
    REDIS_EXPIRE = 60


class ProductionConfig(Config):
    DB_ADDRESS = "localhost"
    DB_PASSWORD = "NthAiX2mRmNFWwr3"
    DATABASE = "onex2_db"
    PORT = 8282
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://onex2_db:%s@%s:3306/%s?charset=utf8' % (
        DB_PASSWORD, DB_ADDRESS, DATABASE)

    # 支付配置
    CHARGE_CALLBACK_URL = "http://ag.1x2mmm.net/api/openapi/jpay/recharge_callback"
    PAY_CENTER_API = "http://pay.okbetmm.com"
    PAY_CENTER_APP_ID = "5b2a9256790d1c7f800d6460cf437968"
    PAY_CENTER_APP_AES_SECRET = "kcjNMLZfu3jUlPvdMEycJw=="

    # AWC API配置（生产环境）
    AWC_API_ENABLED = True  # 启用AWC API
    AWC_API_BASE_URL = "https://tttint.apihub55.com"  # AWC生产环境地址
    AWC_API_CERT = "Xb80KCEti0wdbT78rij"  # TODO: 填写你的AWC认证码
    AWC_API_AGENT_ID = "1x2ag"  # TODO: 填写你的AWC代理ID
    AWC_API_TIMEOUT = 30
    AWC_API_DEFAULT_CURRENCY = "MMK"
    AWC_API_DEFAULT_LANGUAGE = "en"
    # 多平台betLimit配置 - 根据API文档8.6配置
    # 注意: 实际使用时需要联系AWC获取你的代理商可用的limitId
    AWC_API_DEFAULT_BET_LIMIT = '{"HORSEBOOK":{"LIVE":{"minbet":2000,"maxbet":5000000,"maxBetSumPerHorse":5000000,"minorMinbet":2000,"minorMaxbet":1600000,"minorMaxBetSumPerHorse":1600000}},"HOTROAD":{"LIVE":{"limitId":[2500006,2500007,2500008,2500009,2500010]}},"PP":{"LIVE":{"limitId":["G1"]}},"SEXYBCRT":{"LIVE":{"limitId":[282006,282007,282501,282502,282503]}},"SV388":{"LIVE":{"maxbet":1000000,"minbet":2000,"mindraw":2000,"matchlimit":1000000,"maxdraw":200000}},"VIACASINO":{"LIVE":{"limitId":["A1","B2","J1","I1","H1"]}}}'
    # AWC游戏闲置超时配置
    AWC_GAME_IDLE_TIMEOUT_ENABLED = True  # 是否启用游戏闲置超时
    AWC_GAME_IDLE_TIMEOUT_MINUTES = 15  # 闲置超时时间（分钟）
    AWC_GAME_IDLE_WARNING_MINUTES = 2  # 超时警告提前时间（分钟）
    AWC_GAME_AUTO_LOGOUT = True  # 闲置超时时是否自动登出AWC
    AWC_GAME_SESSION_HEARTBEAT_INTERVAL = 30  # 会话心跳间隔（秒）
    AWC_GAME_SESSION_MAX_DURATION = 120  # 会话最大时长（分钟）

class LocalTestConfig(Config):
    DB_ADDRESS = "localhost"
    DB_PASSWORD = "123456"
    DATABASE = "javasaas-game-local"
    PORT = 8282
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:%s@%s:3306/%s?charset=utf8' % (DB_PASSWORD, DB_ADDRESS, DATABASE)

    # 支付配置
    CHARGE_CALLBACK_URL = "http://192.168.99.125:8082/openapi/jpay/recharge_callback"
    PAY_CENTER_API = "http://192.168.99.125:9010"
    PAY_CENTER_APP_ID = "5625827305dea85a3c94b4173817e6fd"
    PAY_CENTER_APP_AES_SECRET = "qfgZ2JkeZlf/H3BE1Yr6xQ=="

    # AWC API配置（本地测试环境）
    AWC_API_ENABLED = True  # 启用AWC API
    AWC_API_BASE_URL = "https://tttint.apihub55.com"  # AWC测试环境地址
    AWC_API_CERT = "Xb80KCEti0wdbT78rij"  # TODO: 填写你的AWC测试认证码
    AWC_API_AGENT_ID = "1x2ag"  # TODO: 填写你的AWC测试代理ID
    AWC_API_TIMEOUT = 30
    AWC_API_DEFAULT_CURRENCY = "MMK"
    AWC_API_DEFAULT_LANGUAGE = "en"
    # 多平台betLimit配置 - 根据API文档8.6配置
    # 注意: 实际使用时需要联系AWC获取你的代理商可用的limitId
    AWC_API_DEFAULT_BET_LIMIT = '{"HORSEBOOK":{"LIVE":{"minbet":2000,"maxbet":5000000,"maxBetSumPerHorse":5000000,"minorMinbet":2000,"minorMaxbet":1600000,"minorMaxBetSumPerHorse":1600000}},"HOTROAD":{"LIVE":{"limitId":[2500006,2500007,2500008,2500009,2500010]}},"PP":{"LIVE":{"limitId":["G1"]}},"SEXYBCRT":{"LIVE":{"limitId":[282006,282007,282501,282502,282503]}},"SV388":{"LIVE":{"maxbet":1000000,"minbet":2000,"mindraw":2000,"matchlimit":1000000,"maxdraw":200000}},"VIACASINO":{"LIVE":{"limitId":["A1","B2","J1","I1","H1"]}}}'
    # AWC游戏闲置超时配置
    AWC_GAME_IDLE_TIMEOUT_ENABLED = True  # 是否启用游戏闲置超时
    AWC_GAME_IDLE_TIMEOUT_MINUTES = 15  # 闲置超时时间（分钟）
    AWC_GAME_IDLE_WARNING_MINUTES = 2  # 超时警告提前时间（分钟）
    AWC_GAME_AUTO_LOGOUT = True  # 闲置超时时是否自动登出AWC
    AWC_GAME_SESSION_HEARTBEAT_INTERVAL = 30  # 会话心跳间隔（秒）
    AWC_GAME_SESSION_MAX_DURATION = 120  # 会话最大时长（分钟）

class DevelopConfig(Config):
    DB_ADDRESS = "192.168.1.200"
    DB_PASSWORD = "123456"
    DATABASE = "1x2_db"
    PORT = 8282
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:%s@%s:3306/%s?charset=utf8' % (DB_PASSWORD, DB_ADDRESS, DATABASE)

    # 支付配置
    CHARGE_CALLBACK_URL = "http://192.168.99.125:8082/openapi/jpay/recharge_callback"
    PAY_CENTER_API = "http://192.168.99.125:9010"
    PAY_CENTER_APP_ID = "5625827305dea85a3c94b4173817e6fd"
    PAY_CENTER_APP_AES_SECRET = "qfgZ2JkeZlf/H3BE1Yr6xQ=="

    # AWC API配置（开发环境）
    AWC_API_ENABLED = True  # 启用AWC API
    AWC_API_BASE_URL = "https://tttint.apihub55.com"  # AWC测试环境地址
    AWC_API_CERT = "Xb80KCEti0wdbT78rij"  # TODO: 填写你的AWC测试认证码
    AWC_API_AGENT_ID = "1x2ag"  # TODO: 填写你的AWC测试代理ID
    AWC_API_TIMEOUT = 30
    AWC_API_DEFAULT_CURRENCY = "MMK"
    AWC_API_DEFAULT_LANGUAGE = "en"
    # 多平台betLimit配置 - 根据API文档8.6配置
    # 注意: 实际使用时需要联系AWC获取你的代理商可用的limitId
    AWC_API_DEFAULT_BET_LIMIT = '{"HORSEBOOK":{"LIVE":{"minbet":2000,"maxbet":5000000,"maxBetSumPerHorse":5000000,"minorMinbet":2000,"minorMaxbet":1600000,"minorMaxBetSumPerHorse":1600000}},"HOTROAD":{"LIVE":{"limitId":[2500006,2500007,2500008,2500009,2500010]}},"PP":{"LIVE":{"limitId":["G1"]}},"SEXYBCRT":{"LIVE":{"limitId":[282006,282007,282501,282502,282503]}},"SV388":{"LIVE":{"maxbet":1000000,"minbet":2000,"mindraw":2000,"matchlimit":1000000,"maxdraw":200000}},"VIACASINO":{"LIVE":{"limitId":["A1","B2","J1","I1","H1"]}}}'
    # AWC游戏闲置超时配置
    AWC_GAME_IDLE_TIMEOUT_ENABLED = True  # 是否启用游戏闲置超时
    AWC_GAME_IDLE_TIMEOUT_MINUTES = 15  # 闲置超时时间（分钟）
    AWC_GAME_IDLE_WARNING_MINUTES = 2  # 超时警告提前时间（分钟）
    AWC_GAME_AUTO_LOGOUT = True  # 闲置超时时是否自动登出AWC
    AWC_GAME_SESSION_HEARTBEAT_INTERVAL = 30  # 会话心跳间隔（秒）
    AWC_GAME_SESSION_MAX_DURATION = 120  # 会话最大时长（分钟）