# -*- coding: utf-8 -*-
# 2020/03/26 新加字段 m_withdrawal.CARD_NUM, m_withdrawal.BANK_TYPE
# 2020/12/19 增加字段 ALTER TABLE m_app_user ADD COLUMN LAST_LOGIN_IP bigint(20) DEFAULT 0 not null COMMENT '最后登录ip';
# 2020/12/19 增加字段 ALTER TABLE m_app_order ADD COLUMN IP bigint(20) DEFAULT 0 not null COMMENT '下单ip';
# 2020/12/19 增加字段 ALTER TABLE order_history ADD COLUMN IP bigint(20) DEFAULT 0 not null COMMENT '下单ip';
from gevent import monkey

monkey.patch_all()

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


my_signals = Namespace()
app_opt = my_signals.signal('app_opt')
base_path = path.abspath(path.dirname(__file__))

app = Flask(__name__)
Swagger(app)
auth = HTTPTokenAuth(scheme="JWT")
CORS(app, resources=r'/*')

# 谷歌账号
# innwalive@gmail.com
# Az@464748
google_credentials = service_account.Credentials.from_service_account_file(path.join(base_path, 'static/liquid-galaxy-466810-d0-9360f89e5cc1.json'))

# api文档地址: http://127.0.0.1:8282/docs/api/
# app.config['API_DOC_MEMBER'] = ['app_user', 'match', 'config', 'order', 'charge_apply', 'withdraw', 'bank_card', 'notice', 'up_image', 'app_operation']
# ApiDoc(app)

# 此处切换环境配置
# 正式服配置
app.config.from_object('app_server.setting.ProductionConfig')
# 开发配置
#app.config.from_object('app_server.setting.DevelopConfig')
# 本地配置
#app.config.from_object('app_server.setting.LocalTestConfig')
Redis = redis.StrictRedis(app.config['REDIS_HOST'], app.config['REDIS_PORT'], app.config['REDIS_DB'])
db = SQLAlchemy(app)
