from app_server import db, app
from sqlalchemy import Column, String, Integer, Boolean, Text, Numeric, SmallInteger, DateTime
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import BadSignature, SignatureExpired
from sqlalchemy.dialects.mysql import TIMESTAMP, BIGINT
import ipaddress
from app_server.model import Redis
import datetime
import hashlib
import app_server.utils.DictDef as DictDef
from app_server.utils.BaseSaasModel import BaseSaasModel


# 新会员新表
class AppMember(BaseSaasModel):
    __tablename__ = 'm_app_member'
    id = Column(String(32), primary_key=True, comment='用户唯一标识ID')
    rid = Column(String(32), comment='推荐人ID')
    aid = Column(String(32), comment='所属代理ID')
    cpid = Column(String(32), comment='关联合作伙伴ID')
    name = Column(String(50), comment='用户真实姓名')
    username = Column(String(50), unique=True, comment='登录用户名')
    password = Column(String(255), comment='加密后的密码')
    cash_code = Column(String(100), comment='提现验证码')
    money = Column(Numeric(20, 2), default=0, comment='可用余额')
    money_promotion = Column(Numeric(20, 2), default=0, comment='促销活动金额')
    phone = Column(String(20), comment='绑定手机号')
    favourite = Column(Text, comment='用户偏好设置(JSON格式)')
    favourite_list = Column(Text, comment='偏好选项列表')
    currency = Column(String(10), default='CNY', comment='货币类型')
    money_lock = Column(Numeric(20, 2), default=0, comment='冻结金额')
    mn_username = Column(String(100), comment='MN平台用户名')
    ads_type = Column(String(50), comment='广告投放类型')
    count_deposit = Column(SmallInteger, default=0, comment='存款总次数')
    count_withdraw = Column(SmallInteger, default=0, comment='提现总次数')
    total_deposit = Column(Numeric(20, 2), default=0, comment='累计存款金额')
    total_withdraw = Column(Numeric(20, 2), default=0, comment='累计提现金额')
    total_bet = Column(Integer, default=0, comment='总投注次数')
    first_favourite_list = Column(Text, comment='首次偏好设置')
    ranking = Column(Text, comment='用户排名数据')
    line_id = Column(String(100), comment='Line社交账号ID')
    tg_id = Column(String(100), comment='Telegram账号ID')
    fb_id = Column(String(100), comment='Facebook账号ID')
    ss_img = Column(String(255), comment='用户截图或头像路径')
    email = Column(Text, comment='电子邮箱地址')
    emailVerified = Column(DateTime, comment='邮箱验证时间')
    image = Column(Text, comment='用户头像(Base64或URL)')
    rusername = Column(Text, comment='推荐人用户名')
    pushSubscription = Column(Text, comment='推送订阅信息(JSON格式)')
    salt = Column(Text, comment='密码加密盐值')
    log_login = Column(Text, comment='登录日志(JSON格式)')
    last_login_ip = Column(String(255), comment='最近登陆IP')
    last_login_time = Column(DateTime, comment='最近登陆时间')
    setting_bet = Column(Text, comment='投注设置(JSON格式)')
    status = Column(SmallInteger, default=1, comment='状态: 0-停用, 1-启用')
    awc = Column(String(1), default='0', comment='AWC注册状态: 0-未注册, 1-已注册')
    awc_createtime = Column(DateTime, comment='AWC账号创建时间')


    def set_psw(self, password):
        self.password = hashlib.sha1((password + self.salt).encode(encoding='utf-8')).hexdigest()

    def check_psw(self, password):
        # print(hashlib.sha1(('Aa123456' + 'e0e35b14ebd840ee87ff58cceb152060').encode(encoding='utf-8')).hexdigest())
        # print(hashlib.sha1(('Aa123456' + self.salt).encode(encoding='utf-8')).hexdigest())
        return hashlib.sha1((password + self.salt).encode(encoding='utf-8')).hexdigest() == self.password

    # 获取token，有效时间10min
    def generate_auth_token(self, expiration=60 * 60 * 12):
        s = Serializer(app.config['SECRET_KEY'], expires_in=expiration)
        token = s.dumps({'member_id': self.id})
        Redis.write("user_token|%s" % self.id, token, expiration)
        return token

    def generate_new_cash_code(self):
        last_user = AppMember.query.order_by(AppMember.cash_code.desc()).first()
        if last_user and last_user.cash_code:
            # 直接将CASH_CODE转换为整数
            last_index = int(last_user.cash_code)
            new_index = last_index + 1
        else:
            new_index = 1
        # 格式化新的CASH_CODE，保持至少为6位数
        new_cash_code = f'{new_index:06d}'
        return new_cash_code

    @staticmethod
    def verify_auth_token(token):
        s = Serializer(app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
            # print("token verifying:", token, data)
        except SignatureExpired:
            return None  # valid token, but expired
        except BadSignature:
            return None  # invalid token
            # token has been logout
        r_token = Redis.read("user_token|%s" % data['member_id'])
        if not r_token or token != r_token:
            print("token has been logout")
            return None
        admin = AppMember.query.get(data['member_id'])
        if not admin or not admin.status:
            return None
        return admin

    def to_dict(self, include=None, exclude=None):
        if exclude is None:
            exclude = DictDef.DbToDictExclude
        columns = self.__table__.columns.keys()
        result = {}
        for key in columns:

            if include and key not in include:
                continue
            if exclude and key in exclude:
                continue

            value = getattr(self, key)
            if key in {'create_time', 'update_time', 'last_login_time', 'awc_createtime'}:
                value = str(value)
            if key == 'last_login_ip':
                value = str(ipaddress.ip_address(value))
            result[key] = value
        result['money'] = format(self.money, ",")
        result['money_promotion'] = format(self.money_promotion, ",")
        result['total_deposit'] = format(self.total_deposit, ",")
        result['total_withdraw'] = format(self.total_withdraw, ",")
        result['money_lock'] = format(self.money_lock, ",")
        #log_login
        #/{"os": "Windows", "device": "Unknown", "is_bot": false, "browser": "Chrome", "ip_address": "122.154.228.132", "last_login": "2025-01-24T17:05:14.015Z", "user_agent": "Chrome 131.0.0.0 Windows 10 undefined Blink 131.0.0.0 amd64"}
        return result
