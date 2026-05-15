from app_server import app, db, auth, app_opt
from app_server.model.AppAgentModel import AppAgent
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
import random
import string

from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
import base64
import json

from app_server.utils.Kits import Kits
from app_server.utils.MessageHelper import MessageHelper

app_user = Blueprint('app_user', __name__)


def generate_r_code():
    """生成一个r_code: 2位大写字母 + 6位数字"""
    # 生成2位大写字母
    letters = ''.join(random.choices(string.ascii_uppercase, k=2))
    # 生成6位数字
    numbers = ''.join(random.choices(string.digits, k=6))
    return letters + numbers


def generate_unique_r_code(max_attempts=100):
    """生成唯一的r_code，最多尝试max_attempts次"""
    for _ in range(max_attempts):
        r_code = generate_r_code()
        # 检查r_code是否唯一
        existing = AppMember.query.filter_by(r_code=r_code, del_flag=0).first()
        if not existing:
            return r_code
    raise Exception("无法生成唯一的r_code，请稍后重试")


def check_referrer_frequency_warning(promoter_id, promoter_username=None):
    """检查推广人最新第1条和第5条推广关系是否在3分钟内生成。"""
    from app_server.model.MAppPromotionRelationModel import MAppPromotionRelation

    latest_relations = MAppPromotionRelation.query.filter_by(
        promoter_id=promoter_id,
        del_flag=0
    ).order_by(MAppPromotionRelation.create_time.desc()).limit(5).all()

    if len(latest_relations) < 5:
        return

    latest_time = latest_relations[0].create_time
    fifth_time = latest_relations[4].create_time
    if not latest_time or not fifth_time:
        return

    if latest_time - fifth_time <= datetime.timedelta(minutes=3):
        warning_promoter_username = promoter_username or latest_relations[0].promoter_username or ''
        promoter = AppMember.query.filter_by(id=promoter_id, del_flag=0).first()
        if not promoter or not promoter.aid:
            return

        agent = AppAgent.query.filter_by(id=promoter.aid).first()
        if not agent:
            return

        admin_user_ids = agent.get_admin_user_ids()
        if not admin_user_ids:
            return

        title = "Frequent referral warning"
        content = (
            f"promoter_id={promoter_id}, "
            f"promoter_username={warning_promoter_username}, "
            f"latest_create_time={latest_time}, "
            f"fifth_create_time={fifth_time}"
        )
        MessageHelper.send_to_admin(
            admin_user_ids=admin_user_ids,
            title=title,
            content=content,
            category='SECURITY',
            priority='HIGH'
        )


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
                  description: the encrypted parameters containing account, password, and optional adlink_id
                  example: "ABCDEFG12344Xx"
                adlink_id:
                  type: string
                  description: the adlink_id (广告链接ID) - can be passed directly or in encrypted params
                  example: "adlink_summer2024"
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
    adlink_id = args.get('adlink_id')  # 可以直接传递，不加密

    if not encrypted_params:
        return json
    try:

        decrypted_text = decrypt(encrypted_params)
        params = json.loads(decrypted_text)
        account = params.get('account')
        password = params.get('password')
        # adlink_id 可以在加密参数中，也可以直接传递
        if not adlink_id:
            adlink_id = params.get('adlink_id')
        print(encrypted_params, params, account, password, adlink_id)
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
        # 用户被删除的情况
        if user.del_flag and user.del_flag != 0:
            response = jsonify({'message': "Account has been deleted."})
            response.status_code = 403
            return response
        # ip = request.headers.get('x-forwarded-for') or 0
        # if ip and "," in ip:
        #     ip = ip[0:ip.index(',')]
        # 记录登录信息（先保存旧值用于变化检测）
        prev_log = json.loads(user.log_login) if user.log_login else {}
        prev_ip = prev_log.get('ip_address') or user.last_login_ip
        prev_device = prev_log.get('device')

        client_info = Kits.client_info(request)
        user.last_login_ip = client_info.get('ip_address')
        user.last_login_time = client_info.get('last_login')
        user.log_login = json.dumps(client_info)
        db.session.commit()
        g.user = user

        # 记录登录行为日志
        try:
            from app_server.service.AppBehaviorLogService import AppBehaviorLogService

            AppBehaviorLogService.add_behavior_log(
                request=request,
                event_type='login',
                business_type='adlink' if adlink_id else None,
                business_id=adlink_id if adlink_id else None,
                member_id=user.id,
                event_params={
                    'account': account,
                    'login_ip': client_info.get('ip_address'),
                    'device_type': client_info.get('device'),
                    'browser': client_info.get('browser')
                },
                remark='User login'
            )
        except Exception as e:
            app.logger.warning(f"Failed to add login behavior log: {str(e)}")

        # 检测IP或设备变化，发送安全提醒消息
        try:
            from app_server.utils.MemberMessageService import MemberMessageService
            MemberMessageService.send_login_alert(
                member_id=user.id,
                new_ip=client_info.get('ip_address', ''),
                prev_ip=prev_ip or '',
                new_device=client_info.get('device', ''),
                prev_device=prev_device or '',
                login_time=client_info.get('last_login', ''),
                aid=user.aid if hasattr(user, 'aid') else None,
            )
        except Exception as e:
            app.logger.warning(f"Failed to send login alert message: {str(e)}")

        token = user.generate_auth_token()

        print("the token", token.decode())

        return jsonify({
            "token": "JWT %s" % token.decode()
        })

    except Exception as e:
        print("login error", e)
        response = jsonify({
            'message': "System or Technical Error"
        })
        response.status_code = 500
        return response


@app_user.route('/refresh_token', methods=['POST'])
@auth.login_required
def refresh_token():
    """
    刷新用户Token
    当token即将过期时，用户可调用此接口获取新token
    ---
    tags:
      - app_user
    parameters:
      - in: header
        name: Authorization
        required: true
        description: Current JWT token (format: "JWT <token>")
        schema:
          type: string
          example: "JWT eyJhbGciOiJIUzUxMiIsImlhdCI6MTY0..."
    responses:
      200:
        description: Token refreshed successfully
        schema:
          type: object
          properties:
            token:
              type: string
              description: New JWT token
              example: "JWT eyJhbGciOiJIUzUxMiIsImlhdCI6MTY0..."
            expires_in:
              type: integer
              description: Token expiration time in seconds
              example: 43200
      401:
        description: Unauthorized - Invalid or expired token
      500:
        description: Token refresh failed
    """
    try:
        user = g.user
        if not user:
            response = jsonify({'message': "User not found"})
            response.status_code = 401
            return response

        # 生成新token（12小时有效期）
        new_token = user.generate_auth_token()

        # 记录token刷新日志
        app.logger.info(f"Token refreshed for user: {user.id} ({user.username})")

        return jsonify({
            "token": "JWT %s" % new_token.decode(),
            "expires_in": 43200,  # 12小时，单位：秒
            "refresh_time": datetime.datetime.now().isoformat()
        })
    except Exception as e:
        app.logger.error(f"Token refresh failed: {str(e)}")
        response = jsonify({'message': "Token refresh failed"})
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
        return Kits.rt_error("System or Technical Error")


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
                adlink_id:
                  type: string
                  description: the adlink_id (广告链接ID) of the app user
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
    r_code = args.get("r_code")
    agent_id = args.get("agent_id")
    adlink_id = args.get("adlink_id")  # 获取广告链接ID
    # verify_code = args.get("verify_code")  # NEW: 获取验证码
    currency = 'MMK'
    try:
        if not phone.isdigit():
            response = jsonify({'message': "Phone number format error"})
            response.status_code = 400
            return response
        old_user = AppMember.query.filter_by(phone=phone, del_flag=0).first()
        if old_user:
            response = jsonify(
                {'message': "The phone number already exists. Please register with a different phone number"})
            response.status_code = 409
            return response

        # NEW: 验证OTP验证码
        # if not verify_code:
        #     response = jsonify({'message': "Verification code is required"})
        #     response.status_code = 400
        #     return response

        from app_server.service.MoviderSmsService import MoviderSmsService
        # success, error_msg = MoviderSmsService.verify_code(phone, verify_code)
        # if not success:
        #     response = jsonify({'message': error_msg or "Verification code is invalid"})
        #     response.status_code = 400
        #     return response

        if agent_id:
            agent = AppAgent.query.filter_by(id=agent_id, del_flag=0).first()
            if not agent:
                agent_id = None
        # 创建会员
        user = AppMember(id=Kits.generate_uuid(), phone=phone, name=bank_user_name, username=phone, currency=currency)
        # 获取推荐人信息
        referrer_valid = False
        inviter_activity = None

        if r_code:
            r_member = AppMember.query.filter_by(r_code=r_code, del_flag=0).first()
            if not r_member:
                return Kits.rt_error("Referral code does not exist.")

            # 查询推荐人的活跃邀请活动
            from app_server.model.MAppPromotionRelationModel import MAppPromotionRelation
            from app_server.model.AppPlayerActivityRecordModel import AppPlayerActivityRecord
            from app_server.model.MAppInvitationActivityModel import MAppInvitationActivity
            from app_server.service.PromotionRelationService import PromotionRelationService

            inviter_activity_record = AppPlayerActivityRecord.query.filter_by(
                mb_id=r_member.id,
                activity_type='INVITATION',
                status='Active',
                del_flag=0
            ).first()

            # 获取活动的邀请人数限制（从活动配置中获取，没有活动则不限制）
            if inviter_activity_record:
                inviter_activity = MAppInvitationActivity.query.filter_by(
                    id=inviter_activity_record.activity_id,
                    del_flag=0
                ).first()

            # 检查IP和设备限制（仅当有活动时检查，超限则阻止注册）
            if inviter_activity:
                client_info = Kits.client_info(request)
                invite_ip = client_info.get('ip_address')
                invite_device = client_info.get('device')

                ip_device_passed, ip_device_msg = PromotionRelationService.check_ip_device_limits(
                    inviter_activity.id, invite_ip, invite_device
                )

                if not ip_device_passed:
                    app.logger.warning(f"注册被阻止 - IP或设备限制: ip={invite_ip}, device={invite_device}, reason={ip_device_msg}")
                    return Kits.rt_error(f"Registration failed: {ip_device_msg}")

            # 始终建立推荐关系，邀请人数限制由 PromotionRelationService 处理
            # 如果达到上限，会设置 is_counted_in_activity=False，邀请者不获奖励
            referrer_valid = True
            user.rid = r_member.id
            user.aid = r_member.aid
            user.rusername = r_member.username
            if not agent_id:
                agent_id = r_member.aid
        # 生成用户的r_code
        user.r_code = generate_unique_r_code()
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
        else:
            user.aid = agent_id

        # 处理广告链接信息 不包含用户邀请
        if adlink_id and not r_code:
            from app_server.model.AppAdlinkModel import AppAdlink
            # 保存广告链接ID
            user.ad_link_id = adlink_id
            # 查询广告链接名称并保存到 ads_type
            try:
                adlink = AppAdlink.query.filter_by(id=adlink_id, del_flag=0).first()
                if adlink and adlink.campaign_name:
                    user.ads_type = adlink.campaign_name
                    if adlink.agent_id:
                        user.aid = adlink.agent_id
                else:
                    user.ads_type = 'Unknown Adlink'
            except Exception as e:
                app.logger.warning(f"Failed to get adlink name: {str(e)}")
                user.ads_type = 'Unknown'

        db.session.add(user)
        card = AppMemberBank.query.filter_by(acc_number=bank_card, bank_code=bank_type).first()
        if card:
            response = jsonify(
                {'message': "This bank card has already been saved. Please use a different card to save"})
            response.status_code = 400
            return response
        # 创建用户银卡
        bankcard = AppMemberBank(id=Kits.generate_uuid(), bank_code=bank_type, acc_name=bank_user_name,
                                 acc_number=bank_card, mb_id=user.id, currency=currency, is_default=1)
        db.session.add(bankcard)
        db.session.commit()

        # 创建推广关系记录（始终创建，邀请人数限制由 PromotionRelationService 处理）
        if r_code and user.rid:
            try:
                from app_server.service.PromotionRelationService import PromotionRelationService

                # 获取客户端信息
                client_info = Kits.client_info(request)

                # 使用服务类创建推广关系
                # PromotionRelationService 会自动处理：
                # 1. 邀请人数限制（从活动配置获取 max_invitations_per_user）
                # 2. 超限时设置 is_counted_in_activity=False
                promotion_relation = PromotionRelationService.create_promotion_relation(
                    promoter_id=user.rid,
                    invitee_id=user.id,
                    invite_code=r_code,
                    activity_id=inviter_activity.id if inviter_activity else None,
                    invite_channel='APP',
                    invite_ip=client_info.get('ip_address'),
                    invite_device=client_info.get('device'),
                    tenant_id=user.tenant_id,
                    aid=user.aid
                )

                if promotion_relation:
                    check_referrer_frequency_warning(
                        promoter_id=user.rid,
                        promoter_username=user.rusername
                    )

            except Exception as e:
                app.logger.error(f"创建推广关系失败: {str(e)}")
                # 不影响注册流程，记录错误日志

        # 记录用户注册行为日志
        try:
            from app_server.service.AppBehaviorLogService import AppBehaviorLogService

            AppBehaviorLogService.add_behavior_log(
                request=request,
                event_type='register',
                business_type='adlink' if adlink_id else None,
                business_id=adlink_id if adlink_id else None,
                member_id=user.id,
                event_params={
                    'phone': phone,
                    'referral_code': r_code if r_code else None,
                    'agent_id': user.aid
                },
                remark='User registration completed'
            )
        except Exception as e:
            app.logger.warning(f"Failed to add behavior log: {str(e)}")

        return jsonify({'message': "add successful."})
    except Exception as e:
        print("add user error:", e)
    response = jsonify({'message': "System or Technical Error"})
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
                    {'message': "System or Technical Error"}
        """
    args = request.get_json()
    phone = args.get('PHONE')
    old_password = args.get('OLD_PASSWORD')

    try:
        user = AppMember.query.filter_by(id=g.user.id).first_or_404()
        if phone and not phone.isdigit():
            response = jsonify({'message': "0မှ9သာဖြည့်ရန်."})
            response.status_code = 400
            return response
        if args.get('USER_PWD'):
            if not old_password or not user.check_psw(old_password):
                # print("edit the psw:", args, old_password, user.check_psw(old_password))
                response = jsonify({'message': "old_password_not_right"})
                response.status_code = 400
                return response

            psw_sha1 = hashlib.sha1((args['USER_PWD'] + user.salt).encode(encoding='utf-8')).hexdigest()
            args['USER_PWD'] = psw_sha1
            user.password = psw_sha1
        # OrmUttil.set_field(user, args)

        db.session.commit()
        return jsonify({'message': "change_password_success"})
    except Exception as e:
        print("add match error:", e)
        db.session.rollback()
        response = jsonify({'message': "System or Technical Error"})
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
                    {'message': "System or Technical Error"}
        """

    try:
        repeat_account = AppMember.query.filter_by(phone=pid,del_flag=0).first()
        if repeat_account:
            return jsonify({'message': "User already exist",
                            'status': True})
        return jsonify({'message': "User not already exist",
                        'status': False})
    except Exception as e:
        print("add match error:", e)
        response = jsonify({'message': "System or Technical Error"})
        response.status_code = 400
        return response
