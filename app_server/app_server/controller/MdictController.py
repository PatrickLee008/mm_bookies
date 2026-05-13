from app_server import app, db, auth, app_opt
from flask import jsonify, Blueprint, request, g

from app_server.model.AppSettingBet1x2Model import AppSettingBet1x2Model
from app_server.model.AppSettingFinanceModel import AppSettingFinanceModel
from app_server.model.ContactFuncModel import ContactFunc
from app_server.model.SysBisDictModel import SysBisDict
from app_server.utils import OrmUttil
from app_server.utils.Kits import Kits

r_conf = Blueprint('config', __name__)


@r_conf.route('/get', methods=['GET'])
@auth.login_required
def get_configs():
    """ get_configs API Endpoint
            ---
            tags:
              - config
            responses:
              200:
                description: { 'items': [...]}
              500:
                description: System or Technical Error
            """
    # 获取代理下注配置和默认下注配置
    betting_config = AppSettingBet1x2Model.get_agent_config(g.user.aid)
    # 获取默认的下注配置（混合下注单场最大和订单数最大限制）
    betting_default_config = AppSettingBet1x2Model.get_agent_config()
    # 获取资金配置
    finance_default_config = AppSettingFinanceModel.get_agent_config();
    # 应用配置
    app_front_setting = SysBisDict.get_app_front_setting()
    items = {
        "hdp_min": betting_config.sb_sg_min_bet_hdp,# 单笔HDP最小限制
        "hdp_max": betting_config.sb_sg_max_bet_hdp,# 单笔HDP最大限制
        "ou_min": betting_config.sb_sg_min_bet_ou,  # 单笔O/U最小限制
        "ou_max": betting_config.sb_sg_max_bet_ou,  # 单笔O/U最大限制
        "mix_min_count": betting_config.sb_mix_min_matches_amt,  # 单场混合最小比赛限制
        "mix_max_count": betting_config.sb_mix_max_matches_amt,# 单场混合最多比赛限制
        "withdraw_min_limit": finance_default_config.sf_min_withdrawal,# 提现最小限制
        "withdraw_max_limit": finance_default_config.sf_max_withdrawal,  # 提现最大限制
        "deposit_min_limit": finance_default_config.sf_min_deposit, # 充值最小限制
        "deposit_max_limit": finance_default_config.sf_max_deposit, # 充值最大限制
        "help_content": app_front_setting.helpContent,# 帮助内容
        "contact_us": app_front_setting.contactContent,# 联系我们
        "mix_order_total": betting_default_config.mix_order_total_limit,# 单场混合订单数限制
        "wave_min": betting_config.sb_sg_min_bet_other,# 单场最小限制
        "wave_max": betting_config.sb_sg_max_bet_other,# 单场最大限制
        "single_min": betting_config.sb_sg_min_bet_1x2,# 单场最小限制
        "single_max": betting_config.sb_sg_max_bet_1x2,# 单场最大限制
        "1x2_min": betting_config.sb_sg_min_bet_1x2,  # 单场最小限制
        "1x2_max": betting_config.sb_sg_max_bet_1x2,  # 单场最大限制
        "mix_min": betting_config.sb_mix_min_bet,# 单场最小限制
        "mix_max": betting_config.sb_mix_max_bet,# 单场
        "version": app_front_setting.appVersion,
        "under_maintenance": app_front_setting.updateState,
        "ai_helper_host": app_front_setting.aiHelperHost,
        "ai_helper_token": app_front_setting.aiHelperToken,
    }
    #items属性重decimal转float
    items = Kits.decimal_to_float( items)
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
    # 应用配置
    app_front_setting = SysBisDict.get_app_front_setting()
    if app_front_setting.appVersion:
        current_version = app_front_setting.appVersion
        print("the current_version:", current_version)
        current_version_arr = current_version.split('.')
        params_version = version.split('.')
        print("the current_version:", version,current_version)
        result = {
            "update": False,
            "wgtUrl": '',
            "oisUrl": app_front_setting.appIosUrl,
            "pkgUrl": app_front_setting.appApkUrl,
            "version": app_front_setting.appVersion
        }
        # 版本不相等,需要更新
        if version != current_version:
            result['update'] = True
            # 说明是大版本更新
            if current_version_arr[0] > params_version[0]:
                # 完整包地址
                result['pkgUrl'] = app_front_setting.appApkUrl
            else:
                # 小版本热更新资源包地址
                result['wgtUrl'] = app_front_setting.appWgtUrl

        return jsonify(result)


@r_conf.route('/appinfo', methods=['GET'])
def appinfo():
    # 应用配置
    app_front_setting = SysBisDict.get_app_front_setting()
    result = app_front_setting.to_dict()
    return Kits.rt_data(result)