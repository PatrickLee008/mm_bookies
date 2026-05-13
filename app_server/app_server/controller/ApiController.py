from app_server import app, db, auth, app_opt
from app_server.model.AppFavouriteModel import AppFavourite
from flask import g, request, jsonify, Blueprint

from app_server.model.SysBisDictModel import SysBisDict
from app_server.model.SysTenantModel import SysTenant
from app_server.service.PayOrderService import pay_order_service
from app_server.utils.Kits import Kits

api = Blueprint('api', __name__)


# 调试方法
@api.route('/test', methods=['GET'])
def test():
    # 获取系统字典
    tenant_id = SysTenant.get_tenant_id(request)
    print(tenant_id)
    sys_config = SysBisDict.get_sys_config(tenant_id)
    return Kits.rt_data(sys_config.member_default_agent_id)


# 调试方法
@api.route('/channels', methods=['GET'])
def pay_channels():
    # 调用支付接口获取支付通道
    channel_type = request.args.get('channelType')
    status = request.args.get('status')
    wallet_provider = request.args.get('walletProvider')
    page = request.args.get('page', type=int)
    limit = request.args.get('limit', type=int)

    result = pay_order_service.get_pay_channels(
        channel_type=channel_type,
        status=status,
        wallet_provider=wallet_provider,
        page=page,
        limit=limit,
    )
    if not result.get('success'):
        return Kits.rt_error(result.get('message') or 'Failed to query pay channels')
    return Kits.rt_data(result.get('data') or [])
