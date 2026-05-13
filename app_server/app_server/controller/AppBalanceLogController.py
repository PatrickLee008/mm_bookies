import math

from sqlalchemy import or_, func, desc
from app_server import db, auth, app_opt, Redis
from app_server.model.AppMemberBalanceLogModel import AppMemberBalanceLog
from flask import g, request, jsonify, Blueprint

from app_server.model.ChargeModel import Charge
from app_server.model.WithDrawModel import WithDraw

balance_log = Blueprint('balance_log', __name__)


@balance_log.route('', methods=['GET'])
@auth.login_required
def get_balance_logs():
    """
                    @@@
                    #### Args:
                           {
                                page: 1,
                                limit: 20,
                                filter: {},
                                start_time: "2021-09-10",
                                end_time: "2021-09-12",
                                type: "Deposit|Withdraw|Transfer|Order|Settlement|Refund|Promotion|Adjustment",
                                type_sub: "Auto|Manual|Football|Egame|etc",
                                pay_wallet: "Money|Promotion",
                                status: "0|1|2"  (0=Pending, 1=Success, 2=Failed/Rejected)
                            }
                    #### Returns::
                            {
                                'items': [u.to_dict() for u in balance_log_list],
                            }
                """
    page = request.args.get('page', type=int, default=1)
    limit = request.args.get('limit', type=int, default=20)
    start_time = request.args.get('start_time')
    end_time = request.args.get('end_time')
    query_filter = request.args.get('filter')
    status = request.args.get('status')
    type = request.args.get('type')
    pay_wallet = request.args.get('pay_wallet')
    type_sub = request.args.get('type_sub')

    try:
        balance_log_list = (
            AppMemberBalanceLog.query.filter_by(mb_id=g.user.id).order_by(AppMemberBalanceLog.create_time.desc())
        )

        if query_filter:
            balance_log_list = balance_log_list.filter_by(balance_log_list, query_filter, AppMemberBalanceLog)

        if start_time:
            balance_log_list = balance_log_list.filter(db.cast(AppMemberBalanceLog.create_time, db.Date) >= start_time)

        if end_time:
            balance_log_list = balance_log_list.filter(db.cast(AppMemberBalanceLog.create_time, db.Date) <= end_time)

        if status is not None:
            balance_log_list = balance_log_list.filter(AppMemberBalanceLog.source_status == status)
        if type is not None:
            balance_log_list = balance_log_list.filter(AppMemberBalanceLog.type == type)
        if pay_wallet is not None:
            balance_log_list = balance_log_list.filter(AppMemberBalanceLog.pay_wallet == pay_wallet)
        if type_sub is not None:
            balance_log_list = balance_log_list.filter(AppMemberBalanceLog.type_sub == type_sub)

        total = balance_log_list.count()

        balance_log_list = balance_log_list.offset((page - 1) * limit).limit(limit).all()

        result = []

        for balance_log in balance_log_list:
            temp = balance_log.to_dict()
            source_data = WithDraw.query.filter(WithDraw.id == balance_log.type_sub_data_id).first()
            if balance_log.type == 'Deposit':
                source_data = Charge.query.filter(Charge.id == balance_log.type_sub_data_id).first()
            if source_data:
                temp['bank_code'] = source_data.mb_bank_code

            result.append(temp)

        return jsonify({
            'message': 'success',
            'items': result,
            'totalCount': total,
            'TotalPageCount': math.ceil(int(total / limit))
        })
    except Exception as e:
        print("get balance_logs error:", e)

    response = jsonify({'message': "get balance_logs error"})
    response.status_code = 500
    return response
