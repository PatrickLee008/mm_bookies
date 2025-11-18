from sqlalchemy import or_, func
from app_server import app, db, auth
from app_server.model.AppMemberBalanceLogModel import AppMemberBalanceLog
from flask import g, request, jsonify, Blueprint
from datetime import datetime

app_operation = Blueprint('app_operation', __name__)


@app_operation.route('/get', methods=['GET'])
@auth.login_required
def get_app_operations():
    """ get_app_operations API Endpoint
        ---
        tags:
          - app_operation
        parameters:
           - name: page
             in: query
             type: string
             required: true
             description: page of app_operation
           - name: limit
             in: query
             type: integer
             description: limit of app_operation
           - name: key_word
             in: query
             type: string
             description: key_word of app_operation
           - name: start_time
             in: query
             type: string
             description: start_time of app_operation
           - name: end_time
             in: query
             type: string
             description: end_time of app_operation
        responses:
          200:
            description: { 'items': [...], 'total': 100 }
        """

    current_page = request.args.get('page', type=int, default=1)
    limit = request.args.get('limit', type=int, default=20)
    key_word = request.args.get('key_word')
    start_time = request.args.get('start_time')
    end_time = request.args.get('end_time')

    opt_list = AppMemberBalanceLog.query.filter(AppMemberBalanceLog.mb_id == g.user.id).order_by(AppMemberBalanceLog.create_time.desc())
    if key_word:
        opt_list = opt_list.filter(
            or_(AppMemberBalanceLog.type_sub_data_id.like('%{}%'.format(key_word)), AppMemberBalanceLog.remarks.like('%{}%'.format(key_word))))

    if start_time:
        opt_list = AppMemberBalanceLog.filter(AppMemberBalanceLog.create_time >= start_time)

    if end_time:
        end_time += ' 23:59:59'
        opt_list = AppMemberBalanceLog.filter(AppMemberBalanceLog.create_time <= end_time)

    total = opt_list.count()

    opt_list = opt_list.offset((current_page - 1) * limit).limit(limit).all()

    return jsonify({
        'items': [u.to_dict() for u in opt_list],
        'total': total
    })
