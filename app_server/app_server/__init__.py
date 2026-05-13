# -*- coding: utf-8 -*-
# 2020/03/26 新加字段 m_withdrawal.CARD_NUM, m_withdrawal.BANK_TYPE
# 2020/12/19 增加字段 ALTER TABLE m_app_user ADD COLUMN LAST_LOGIN_IP bigint(20) DEFAULT 0 not null COMMENT '最后登录ip';
# 2020/12/19 增加字段 ALTER TABLE m_app_order ADD COLUMN IP bigint(20) DEFAULT 0 not null COMMENT '下单ip';
# 2020/12/19 增加字段 ALTER TABLE order_history ADD COLUMN IP bigint(20) DEFAULT 0 not null COMMENT '下单ip';

# Gevent monkey patch 条件导入
# 仅在 PyCharm debugger 模式下启用（满足项目特殊需求）
import os
import sys

# 检测是否在 PyCharm debugger 中运行
is_pycharm_debugger = 'pydevd' in sys.modules

# 检测是否在 uWSGI 环境中（检测多个 uWSGI 环境变量）
is_uwsgi = (
    'uwsgi' in sys.modules or
    os.environ.get('UWSGI_ORIGINAL_PROC_NAME') is not None or
    os.environ.get('UWSGI_VERSION') is not None
)

if is_pycharm_debugger and not is_uwsgi:
    from gevent import monkey
    monkey.patch_all()
    print("✅ Gevent enabled (PyCharm debugger detected)")
elif is_uwsgi:
    print("ℹ️  Running under uWSGI, gevent disabled")
else:
    print("ℹ️  Normal mode, gevent disabled")

from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_httpauth import HTTPTokenAuth
from flask_docs import ApiDoc
from flasgger import Swagger
from blinker import Namespace
import datetime
import redis
from google.oauth2 import service_account
from os import path

# 导入全局配置和日志管理模块
from app_server.config import get_config
from app_server.logger import get_logger

my_signals = Namespace()
app_opt = my_signals.signal('app_opt')
base_path = path.abspath(path.dirname(__file__))

app = Flask(__name__)
Swagger(app)
auth = HTTPTokenAuth(scheme="JWT")
CORS(app, resources=r'/*')

# 初始化全局日志
logger = get_logger()

# 加载配置 - 从.env文件读取环境配置
config_class = get_config()
app.config.from_object(config_class)

# 输出详细的启动日志（包含进程PID，方便监控）
import os
logger.info("=" * 60)
logger.info(f"OX2MM App Server Starting... (Worker PID: {os.getpid()})")
logger.info(f"Loaded config: {config_class.__name__} (APP_ENV={path.basename(path.dirname(path.dirname(__file__)))})")
logger.info(f"Database: {app.config.get('DATABASE')}")
logger.info(f"Redis: {app.config.get('REDIS_HOST')}:{app.config.get('REDIS_PORT')}")
logger.info(f"Port: {app.config.get('PORT')}")

# 谷歌账号
# innwalive@gmail.com
# Az@464748
google_credentials = service_account.Credentials.from_service_account_file(
    path.join(base_path, 'static/liquid-galaxy-466810-d0-9360f89e5cc1.json'))

# api文档地址: http://127.0.0.1:8282/docs/api/
# app.config['API_DOC_MEMBER'] = ['app_user', 'match', 'config', 'order', 'charge_apply', 'withdraw', 'bank_card', 'notice', 'up_image', 'app_operation']
# ApiDoc(app)

# 初始化Redis连接
Redis = redis.StrictRedis(app.config['REDIS_HOST'], app.config['REDIS_PORT'], app.config['REDIS_DB'])
logger.info("Redis connection initialized")

# 初始化数据库
db = SQLAlchemy(app)
logger.info("Database initialized")

# 添加数据库引擎到配置，供WebSocket消息控制器使用
app.config['DATABASE_ENGINE'] = db.engine
logger.info("=" * 60)
