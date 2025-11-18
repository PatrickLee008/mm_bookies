import math

from sqlalchemy import or_, func, desc
from app_server import db, auth, app_opt, Redis
from app_server.model.AppAgentBankcard import AppAgentBankcard
from flask import g, request, jsonify, Blueprint

from app_server.model.ChargeModel import Charge
from app_server.model.WithDrawModel import WithDraw

agent_bankcard = Blueprint('agent_bankcard', __name__)


@agent_bankcard.route('', methods=['GET'])
@auth.login_required
def get_agent_bankcard():
    try:
        agent_bankcard = AppAgentBankcard.query.filter(
            AppAgentBankcard.aid == g.user.aid,
            AppAgentBankcard.del_flag == 0,
            AppAgentBankcard.tenant_id == '10000',
            AppAgentBankcard.type.in_(['All', 'Deposit'])
        ).order_by(AppAgentBankcard.balance.desc()).first()

        if not agent_bankcard:
            response = jsonify({'message': 'agent no bankcard',
                                'item': []})
            response.status_code = 501
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
