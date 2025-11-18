from app_server import app, db, auth, app_opt
from app_server.model.AppFavouriteModel import AppFavourite
from flask import g, request, jsonify, Blueprint

from app_server.model.SysBisDictModel import SysBisDict
from app_server.model.SysTenantModel import SysTenant
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
