from app_server import app, db, auth, app_opt
from flask import jsonify, Blueprint, request, g
from app_server.model.NoticeModel import Notice
from sqlalchemy import or_, func

r_notice = Blueprint('notice', __name__)


@r_notice.route('/get', methods=['GET'])
# @auth.login_required
def get_notices():
    """ get_notices API Endpoint
        ---
        tags:
          - notice
        parameters:
          - name: current_page
            in: query
            type: string
            required: true
            description: page of digital_3d
          - name: limit
            in: query
            type: integer
            description: limit of digital_3d
        responses:
          200:
            description: { 'items': [...]}
        """
    current_page = request.args.get('page', type=int, default=1)
    limit = request.args.get('limit', type=int, default=20)

    notice_list = Notice.query.filter(Notice.STATUS == "1")

    notice_list = notice_list.offset((current_page - 1) * limit).limit(limit).all()

    return jsonify({
        'items': [u.to_dict() for u in notice_list],
    })

