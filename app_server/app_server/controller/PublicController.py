from app_server import app, db
from flask import jsonify, Blueprint, request, g

from app_server.model.AppAdlinkModel import AppAdlink
from app_server.service.AppBehaviorLogService import AppBehaviorLogService
from app_server.utils.Kits import Kits

public = Blueprint('public', __name__)


@public.route('/behavior/log', methods=['POST'])
def add_behavior_log():
    """
    添加行为日志 - 统一接口
    支持所有业务类型，参数尽可能简化

    必填参数: event_type
    可选参数: business_type, business_id, member_id, event_params, remark

    授权支持: 如果请求头包含 Authorization JWT Token，会自动解析获取用户ID

    使用场景示例：
    1. 广告链接访问: {event_type: 'visit', business_type: 'adlink', business_id: 'xxx'}
    2. 用户注册: {event_type: 'register', member_id: 'xxx'}
    3. 用户登录: {event_type: 'login', member_id: 'xxx'}
    4. 充值: {event_type: 'deposit', member_id: 'xxx', event_params: {amount: 100}}
    ---
    tags:
      - public
    parameters:
      - name: Authorization
        in: header
        type: string
        required: false
        description: JWT Token (格式: "JWT <token>") - 可选，如果提供会自动解析用户ID
      - name: app_version
        in: header
        type: string
        required: false
        description: APP版本号 (如: "1.0.0", "2.3.1") - 可选，用于记录用户使用的APP版本
      - name: access_channel
        in: header
        type: string
        required: false
        description: 访问途径 (h5/app/pc) - 可选，用于记录用户访问渠道
      - name: event_type
        in: body
        type: string
        required: true
        description: 事件类型(visit/register/login/deposit/bet/withdraw) - 必填
      - name: business_type
        in: body
        type: string
        required: false
        description: 业务类型(adlink/promotion/coupon/general) - 可选，默认general
      - name: business_id
        in: body
        type: string
        required: false
        description: 业务ID - 可选
      - name: member_id
        in: body
        type: string
        required: false
        description: 会员ID - 可选，如果提供JWT Token会自动获取
      - name: event_params
        in: body
        type: object
        required: false
        description: 事件参数 - 可选
      - name: remark
        in: body
        type: string
        required: false
        description: 备注 - 可选
    responses:
      200:
        description: Success
        schema:
          properties:
            code:
              type: integer
              example: 200
            message:
              type: string
              example: Behavior log added successfully
      500:
        description: Error
        schema:
          properties:
            code:
              type: integer
              example: 502
            message:
              type: string
              example: event_type is required
    """
    try:
        data = request.get_json() or {}

        # 尝试从JWT Token中获取用户ID
        member_id = data.get('member_id')

        # 如果没有传member_id，尝试从Authorization header中解析
        if not member_id:
            auth_header = request.headers.get('Authorization')
            if auth_header:
                try:
                    # 解析 "JWT <token>" 格式
                    if auth_header.startswith('JWT '):
                        token = auth_header[4:]  # 去掉 "JWT " 前缀

                        # 使用 AppMember 的 verify_auth_token 方法验证token
                        from app_server.model.AppMemberModel import AppMember
                        user = AppMember.verify_auth_token(token)

                        if user:
                            member_id = user.id
                            app.logger.info(f"Parsed member_id from JWT token: {member_id}")
                except Exception as e:
                    # Token解析失败不影响日志记录，只记录警告
                    app.logger.warning(f"Failed to parse JWT token: {str(e)}")

        # 调用 Service 层处理
        business_type = data.get('business_type')
        business_id = data.get('business_id')
        result = AppBehaviorLogService.add_behavior_log(
            request=request,
            business_type=business_type,
            business_id=business_id,
            event_type=data.get('event_type'),
            member_id=member_id,
            session_id=data.get('session_id'),
            event_params=data.get('event_params'),
            remark=data.get('remark')
        )

        # 特殊处理广告链接点击，返回广告链接要跳转的页面
        if business_type == 'adlink':
            # 获取ID
            adlink = AppAdlink.query.filter_by(id=business_id, del_flag=0).first()
            if adlink:
                return Kits.rt_data(adlink.goto_page)

        if result['success']:
            return Kits.rt_ok(result['message'])
        else:
            return Kits.rt_error(result['message'])

    except Exception as e:
        app.logger.error(f"Add behavior log exception: {str(e)}")
        return Kits.rt_error(f'Failed to add behavior log: {str(e)}')
