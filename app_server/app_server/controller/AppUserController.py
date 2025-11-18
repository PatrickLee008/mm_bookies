from app_server import app, db, auth, app_opt
from app_server.model.AppMemberModel import AppMember
from app_server.model.AppMemberBankModel import AppMemberBank
from flask import g, request, jsonify, Blueprint

from app_server.model.SysBisDictModel import SysBisDict
from app_server.model.SysTenantModel import SysTenant
from app_server.utils import OrmUttil
import ipaddress
import uuid
import hashlib
import datetime

from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
import base64
import json

from app_server.utils.Kits import Kits

app_user = Blueprint('app_user', __name__)


@auth.verify_token
def verify_token(token):
    if not token:
        return False

    user = AppMember.verify_auth_token(token)

    if not user:
        return False

    # 开启部分账号测试
    if app.config['TESTING']:
        if user.USER_ID not in {"09428215939", "09897003434", "09899223535", "0988888888"}:
            return False

    g.user = user
    return True


@auth.error_handler
def unauthorized():
    # print("kw", kw)
    # abort(401)
    response = jsonify({'message': "Unauthorized access"})
    response.status_code = 401
    return response


key = 'innwa'.ljust(16, '\0').encode('utf-8')  # 密钥不足16字节的情况
iv = '1234567890123456'.encode('utf-8')  # 初始向量


# 解密函数
def decrypt(cipher_text):
    cipher_text_bytes = base64.b64decode(cipher_text)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    decrypted_bytes = unpad(cipher.decrypt(cipher_text_bytes), AES.block_size, style='pkcs7')
    return decrypted_bytes.decode('utf-8')


@app_user.route('/login', methods=['POST'])
def login():
    """ Login API Endpoint        
        ---
        tags:
          - app_user        
        parameters:
          - in: body
            name: body
            required: true
            description: Message to echo
            schema:
              type: object
              required:
                - encryptedParams
              properties:
                encryptedParams:
                  type: string
                  description: the encrypted parameters containing account and password
                  example: "ABCDEFG12344Xx"
        responses:
          500:
            description: Invalid Credentials
          500:
            description: Invalid parameters or decryption failed
          200:
            description: Login successful, returns a JWT token
        """

    print(request.get_json())
    args = request.get_json()

    encrypted_params = args.get('encryptedParams')

    if not encrypted_params:
        return json
    try:

        decrypted_text = decrypt(encrypted_params)
        params = json.loads(decrypted_text)
        account = params.get('account')
        password = params.get('password')
        print(encrypted_params, params, account, password)
        user = AppMember.query.filter(AppMember.username == account).first()

        if user is None or not user.check_psw(password):
            response = jsonify({'message': "Invalid Credentials."
                                })
            response.status_code = 400
            return response

        # 用户被ban的情况
        if not user.status:
            response = jsonify({'message': "Unauthorized or Blocked Account"})
            response.status_code = 403
            return response

        # ip = request.headers.get('x-forwarded-for') or 0
        # if ip and "," in ip:
        #     ip = ip[0:ip.index(',')]
        # 记录登录信息
        client_info = Kits.client_info(request)
        user.last_login_ip = client_info.get('ip_address')
        user.last_login_time = client_info.get('last_login')
        user.log_login = json.dumps(client_info)
        db.session.commit()
        g.user = user

        token = user.generate_auth_token()

        print("the token", token.decode())

        return jsonify({
            "token": "JWT %s" % token.decode()
        })

    except Exception as e:
        print("login error", e)
        response = jsonify({
            'message': "System or Technical Error."
        })
        response.status_code = 500
        return response


@app_user.route('/user_info', methods=['GET'])
@auth.login_required
def get_user_info():
    try:
        mb_id = g.user.id
        user = AppMember.query.filter_by(id=mb_id).first()
        if not user:
            return Kits.rt_error("User does not exist.")
        user_info = user.to_dict()
        # 获取用户默认卡
        bank_card = AppMemberBank.query.filter_by(mb_id=mb_id, is_default=1).first()
        user_info['bank_card'] = bank_card.to_dict() if bank_card else None
        return Kits.rt_data(user_info)
    except Exception as e:
        print("user info error:", e)
        return Kits.rt_error("System or Technical Error.")


@app_user.route('/add', methods=['POST'])
def add_app_user():
    """ add_app_user API Endpoint
        ---
        tags:
          - app_user
        parameters:
          - in: body
            name: body
            required: true
            description: App Member Info To Add
            schema:
              type: object
              required:
                - phone
              properties:
                name:
                  type: string
                  description: the name of the app user
                  example: ""
                username:
                  type: string
                  description: the username of the app user
                  example: ""
                password:
                  type: string
                  description: the password of the app user
                  example: ""
                cash_code:
                  type: string
                  description: the cash_code of the app user
                  example: ""
                phone:
                  type: string
                  description: the phone of the app user
                  example: ""
                mn_username:
                  type: string
                  description: the mn_username of the app user
                  example: ""
                ads_type:
                  type: string
                  description: the ads_type of the app user
                  example: ""
                line_id:
                  type: string
                  description: the line_id of the app user
                  example: ""
                tg_id:
                  type: string
                  description: the tg_id of the app user
                  example: ""
                fb_id:
                  type: string
                  description: the fb_id of the app user
                  example: ""
                email:
                  type: string
                  description: the email of the app user
                  example: ""
        responses:
          500:
            description: Invalid Credentials
          500:
            description: Invalid parameters or decryption failed
          200:
            description: Login successful, returns a JWT token
        """

    args = request.get_json()

    phone = args.get("PHONE")
    psw = args.get("USER_PWD")
    nick_name = args.get("NICK_NAME")
    bank_type = args.get("BANK_TYPE")
    bank_user_name = args.get("BANK_USER_NAME")
    bank_card = args.get("BANK_CARD")
    r_majuser_id = args.get("r_majuser_id")
    agent_id = args.get("agent_id")
    currency = 'MMK'
    try:
        if not phone.isdigit():
            response = jsonify({'message': "Phone number format error"})
            response.status_code = 400
            return response
        old_user = AppMember.query.filter_by(phone=phone).first()
        if old_user:
            response = jsonify(
                {'message': "The phone number already exists. Please register with a different phone number"})
            response.status_code = 409
            return response

        # 创建会员
        user = AppMember(id=Kits.generate_uuid(), phone=phone, name=bank_user_name, username=phone, currency=currency)
        # 获取推荐人信息
        if r_majuser_id:
            r_member = AppMember.query.filter_by(id=r_majuser_id).first()
            if not r_member:
                return Kits.rt_error("Referral user does not exist.")
            user.rid = r_majuser_id
            user.aid = r_member.aid
            user.rusername = r_member.username
            if not agent_id:  # 没有推荐代理直接传推荐人的代理
                agent_id = r_member.aid
        # 加密密码
        user.salt = Kits.generate_uuid()
        user.password = hashlib.sha1((psw + f'{user.salt}').encode(encoding='utf-8')).hexdigest()
        user.cash_code = user.generate_new_cash_code()
        user.log_login = json.dumps(Kits.client_info(request))
        user.ranking = 'New'
        # 获取默认租户ID和默认代理
        tenant_id = SysTenant.get_tenant_id(request)
        sysconfig = SysBisDict.get_sys_config(tenant_id)
        user.tenant_id = tenant_id
        if not agent_id:
            user.aid = sysconfig.member_default_agent_id

        db.session.add(user)

        # 创建用户银卡
        bankcard = AppMemberBank(id=Kits.generate_uuid(), bank_code=bank_type, acc_name=bank_user_name,
                                 acc_number=bank_card, mb_id=user.id, currency=currency, is_default=1)
        db.session.add(bankcard)
        db.session.commit()

        return jsonify({'message': "add successful."})
    except Exception as e:
        print("add user error:", e)
    response = jsonify({ 'message': "System or Technical Error."})
    response.status_code = 500
    return response


@app_user.route('/edit', methods=['POST'])
@auth.login_required
def edit_app_user():
    """
            @@@
            #### Args:
                    OLD_PASSWORD: 用于修改密码
                    NICK_NAME = Column(String(255), comment="昵称")
                    SEX = Column(String(2), comment="性别（0:男 1：女）")
                    PHONE = Column(String(40), comment="手机号码")
                    ROOM_CARD = Column(Integer)

                    USER_PWD = Column(String(100), comment="用户密码")
                    BANK_CARD = Column(String(64), comment="银行卡")
            #### Returns::
                    {'message': "edit successful."}
                    {'message': "System or Technical Error."}
        """
    args = request.get_json()
    phone = args.get('PHONE')
    old_password = args.get('OLD_PASSWORD')

    try:
        user = AppMember.query.filter_by(id=g.user.id).first_or_404()
        if phone and not phone.isdigit():
            response = jsonify({ 'message': "0မှ9သာဖြည့်ရန်."})
            response.status_code = 400
            return response
        if args.get('USER_PWD'):
            if not old_password or not user.check_psw(old_password):
                # print("edit the psw:", args, old_password, user.check_psw(old_password))
                response = jsonify({ 'message': "old_password_not_right"})
                response.status_code = 400
                return response

            psw_sha1 = hashlib.sha1((args['USER_PWD'] + user.salt).encode(encoding='utf-8')).hexdigest()
            args['USER_PWD'] = psw_sha1
            user.password = psw_sha1
        # OrmUttil.set_field(user, args)

        db.session.commit()
        return jsonify({ 'message': "change_password_success"})
    except Exception as e:
        print("add match error:", e)
        db.session.rollback()
        response = jsonify({ 'message': "System or Technical Error."})
        response.status_code = 400
        return response


@app_user.route('/<int:pid>', methods=['POST'])
def check_repeat_account(pid):
    """
        Check The Repeat App User Account
        ---
        tags:
          - app_user
        parameters:
          - name: user phone
            in: path
            type: integer
            required: true
            description: the id of the app user to check
        responses:
          200:
            description: {'message': "User already exist", status': True}
        """

    """
            @@@
            #### Args:
                    PHONE = <int:pid> Column(String(40), comment="手机号码")

            #### Returns::
                    {'message': "no repeat., 'status'：True"}
                    {'message': "repeat account., 'status'：False"}
                    {'message': "System or Technical Error."}
        """

    try:
        repeat_account = AppMember.query.filter_by(phone=pid).first()
        if repeat_account:
            return jsonify({ 'message': "User already exist",
                            'status': True})
        return jsonify({ 'message': "User not already exist",
                        'status': False})
    except Exception as e:
        print("add match error:", e)
        response = jsonify({ 'message': "System or Technical Error."})
        response.status_code = 400
        return response
