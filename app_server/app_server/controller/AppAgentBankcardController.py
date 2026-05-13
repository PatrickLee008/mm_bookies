import math

from sqlalchemy import or_, func, desc
from app_server import db, auth, app_opt, Redis, app
from app_server.model.AppAgentBankcard import AppAgentBankcard
from flask import g, request, jsonify, Blueprint

from app_server.model.ChargeModel import Charge
from app_server.model.WithDrawModel import WithDraw
from app_server.model.SysTenantModel import SysTenant
from app_server.model.SysBisDictModel import SysBisDict

agent_bankcard = Blueprint('agent_bankcard', __name__)


@agent_bankcard.route('', methods=['GET'])
@auth.login_required
def get_agent_bankcard():
    """获取代理的收款银行卡

    参数：
        bank_code: 银行代码 (KBZ Pay, Wave Money等)
        charge_way: 充值方式 (0=自动, 1=手动) - 新增参数
        channel_type: 支付通道类型 (Manual, VIPPay/TCPay, NFM2) - 兼容旧版本
    """
    bank_code = request.args.get('bank_code')
    charge_way = request.args.get('charge_way')  # 新增：接收充值方式
    channel_type = request.args.get('channel_type')  # 兼容旧版本参数

    # 根据充值方式确定 channel_type
    if charge_way is not None:
        charge_way_int = int(charge_way)
        if charge_way_int == 1:  # 手动充值
            channel_type = 'Manual'
        elif charge_way_int == 0:  # 自动充值
            # 自动充值：支持配置的 PAY_CHANNEL_TYPE 和 NFM2，设置为 None 后续用 IN 查询
            channel_type = None

    # 如果既没有 charge_way 也没有 channel_type，默认为手动
    if channel_type is None and charge_way is None:
        channel_type = 'Manual'

    try:
        # 构建查询
        query = AppAgentBankcard.query.filter(
            AppAgentBankcard.aid == g.user.aid,
            AppAgentBankcard.del_flag == 0,
            AppAgentBankcard.tenant_id == '10000',
            AppAgentBankcard.rc_bank_code == bank_code,
            AppAgentBankcard.status == 1,
            AppAgentBankcard.type.in_(['All', 'Deposit'])
        )

        # 根据 channel_type 添加过滤条件
        if channel_type == 'Manual':
            query = query.filter(AppAgentBankcard.channel_type == 'Manual')
        elif charge_way is not None and int(charge_way) == 0:
            # 自动充值：所有非Manual的都算（VIPPay/TCPay、NFM2、QR Pay等）
            query = query.filter(AppAgentBankcard.channel_type != 'Manual')
        elif channel_type:
            # 兼容旧版本：直接使用传入的 channel_type
            query = query.filter(AppAgentBankcard.channel_type == channel_type)

        # 按余额降序排序，返回第一张卡
        agent_bankcard = query.order_by(AppAgentBankcard.balance.desc()).first()

        if not agent_bankcard:
            response = jsonify({
                'message': f'No available bank card found for {bank_code} with charge_way={charge_way}',
                'item': []
            })
            response.status_code = 404
            return response

        return jsonify({
            'message': 'success',
            'item': agent_bankcard.to_dict(),
        })

    except Exception as e:
        print("get agent bankcard error:", e)

    response = jsonify({'message': "get agent bankcard error"})
    response.status_code = 500
    return response


@agent_bankcard.route('/supported_bank_types', methods=['GET'])
def get_supported_bank_types():
    """获取代理支持的银行卡类型（无需登录，用于注册和添加银行卡）

    参数：
        agent_id: 代理ID（可选，不传则使用系统默认代理）

    返回：
        可用的银行代码列表：["KBZ Pay", "Wave Money", ...]
    """
    agent_id = request.args.get('agent_id')

    try:
        tenant_id = SysTenant.get_tenant_id(request) or '10000'

        # 如果没有传agent_id，使用系统默认代理
        if not agent_id:
            sysconfig = SysBisDict.get_sys_config(tenant_id)
            agent_id = sysconfig.member_default_agent_id
        # 查询该代理启用的、未删除的银行卡的不重复bank_code
        bank_codes = db.session.query(AppAgentBankcard.rc_bank_code).filter(
            AppAgentBankcard.aid == agent_id,
            AppAgentBankcard.del_flag == 0,
            AppAgentBankcard.tenant_id == tenant_id,
            AppAgentBankcard.status == 1,
            AppAgentBankcard.type != 'Withdraw',
            or_(
                AppAgentBankcard.channel_type == 'Manual',
                AppAgentBankcard.channel_type == app.config['PAY_CHANNEL_TYPE'],
            ),
        ).distinct().all()

        bank_list = [row[0] for row in bank_codes if row[0]]

        return jsonify({
            'message': 'success',
            'item': bank_list
        })

    except Exception as e:
        print("get supported bank types error:", e)
        response = jsonify({'message': 'get supported bank types error'})
        response.status_code = 500
        return response


@agent_bankcard.route('/available_banks', methods=['GET'])
@auth.login_required
def get_available_banks():
    """获取Manual和Auto两种充值方式下的可用银行列表（一次返回）

    返回：
        manual: Manual模式可用银行列表
        auto: Auto模式可用银行列表
    """
    try:
        # 基础查询条件
        base_filter = [
            AppAgentBankcard.aid == g.user.aid,
            AppAgentBankcard.del_flag == 0,
            AppAgentBankcard.tenant_id == '10000',
            AppAgentBankcard.status == 1,
            AppAgentBankcard.type.in_(['All', 'Deposit'])
        ]

        # 查询所有符合条件的银行卡
        bankcards = AppAgentBankcard.query.filter(*base_filter).all()

        pay_channel_type = app.config['PAY_CHANNEL_TYPE']
        manual_dict = {}
        auto_dict = {}
        for card in bankcards:
            bank_code = card.rc_bank_code
            if not bank_code:
                continue
            if card.channel_type == 'Manual':
                if bank_code not in manual_dict:
                    manual_dict[bank_code] = {'bank_code': bank_code, 'count': 0}
                manual_dict[bank_code]['count'] += 1
            elif card.channel_type == pay_channel_type:
                if bank_code not in auto_dict:
                    auto_dict[bank_code] = {'bank_code': bank_code, 'count': 0}
                auto_dict[bank_code]['count'] += 1

        return jsonify({
            'message': 'success',
            'manual': list(manual_dict.values()),
            'auto': list(auto_dict.values())
        })

    except Exception as e:
        print("get available banks error:", e)
        response = jsonify({'message': 'get available banks error'})
        response.status_code = 500
        return response
