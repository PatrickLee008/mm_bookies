from app_server import app, db, auth, app_opt
from flask import jsonify, Blueprint, request, g
from app_server.model.MDictModel import MDict
from app_server.model.ContactFuncModel import ContactFunc
from app_server.utils import OrmUttil

r_conf = Blueprint('config', __name__)


@r_conf.route('/get', methods=['GET'])
# @auth.login_required
def get_configs():
    """ get_configs API Endpoint
            ---
            tags:
              - config
            responses:
              200:
                description: { 'items': [...]}
              500:
                description: System or Technical Error.
            """
    com_configs = MDict.query.filter(MDict.MDICT_ID.in_({'5', '12', '13', '23', '24', '25', '30', '26', '777', '888', '999', '8888', '1333'})).all()

    items = {}
    for conf in com_configs:
        if conf.MDICT_ID == "5":
            items["wl_min"] = conf.CODE
            items["wl_max"] = conf.CONTENT
        elif conf.MDICT_ID == "12":
            items["bs_min"] = conf.CODE
            items["bs_max"] = conf.CONTENT
        elif conf.MDICT_ID == "13":
            items["mix_max_count"] = conf.CONTENT
        elif conf.MDICT_ID == "23":
            items["withdraw_min_limit"] = conf.CONTENT
        elif conf.MDICT_ID == "24":
            items["help_content"] = conf.CONTENT
        elif conf.MDICT_ID == "25":
            items["contact_us"] = conf.CONTENT
        elif conf.MDICT_ID == "30":
            items["mix_order_total"] = conf.CONTENT
        elif conf.MDICT_ID == "777":
            items["wave_min"] = conf.CODE
            items["wave_max"] = conf.CONTENT
        elif conf.MDICT_ID == "888":
            items["single_min"] = conf.CODE
            items["single_max"] = conf.CONTENT
        elif conf.MDICT_ID == "999":
            items["mix_min"] = conf.CODE
            items["mix_max"] = conf.CONTENT
        elif conf.MDICT_ID == "26":
            items["version"] = conf.CONTENT
        elif conf.MDICT_ID == "8888":
            items["under_maintenance"] = conf.CODE
        elif conf.MDICT_ID == "1333":
            items["ai_helper_host"] = conf.CODE
            items["ai_helper_token"] = conf.CONTENT

    # bank_types = BankType.query.all()
    # items['bank_types'] = [u.NAME for u in bank_types]

    contact_funcs = ContactFunc.query.all()
    items['contact_funcs'] = [u.to_dict() for u in contact_funcs]

    print("the limits:", items)
    return jsonify({
        'items': items
    })


@r_conf.route('/updates', methods=['GET'])
# @auth.login_required
def updates():
    version = request.args.get('version')

    source = MDict.query.filter(MDict.MDICT_ID == '26').first()
    if source.CONTENT:
        current_version = source.CONTENT.split(',')
        params_version = version.split(',')

        result = {
            "update": False,
            "wgtUrl": '',
            "pkgUrl": ''
        }
        # 版本不相等,需要更新
        if version != source.CONTENT:
            result['update'] = True
            # 说明是大版本更新
            if current_version[0] > params_version[0]:
                # 热更新资源包地址
                result['wgtUrl'] = source.URL
            else:
                # 完整包地址
                result['pkgUrl'] = source.IMAGE_URL

        return jsonify(result)
