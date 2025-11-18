from app_server import db, auth
from flask import jsonify, Blueprint, request, g
from ..model.TechResultModel import TechResult, TechDetail
from app_server.utils.OrmUttil import query_by_field
import math

r_tech_result = Blueprint('tech_result', __name__)


@r_tech_result.route('', methods=['GET'])
# @auth.login_required
def get_tech_results():
    """ get_tech_results API Endpoint
        ---
        tags:
          - tech_result
        parameters:
           - name: page
             in: query
             type: string
             required: true
             description: current_page of tech_result
           - name: limit
             in: query
             type: integer
             description: limit of tech_result
           - name: filter
             in: query
             type: string
             description: order_id of tech_result
           - name: start_time
             in: query
             type: string
             description: key_word of tech_result
           - name: end_time
             in: query
             type: string
             description: start_time of tech_result

        responses:
          200:
            description: { 'items': [...], 'totalCount': 100, 'TotalPageCount': 5 }
        """
    page = request.args.get('page', type=int, default=1)
    limit = request.args.get('limit', type=int, default=20)
    key_word = request.args.get('key_word')
    start_time = request.args.get('start_time')
    end_time = request.args.get('end_time')
    query_filter = request.args.get('filter')

    try:

        tech_result_list = TechResult.query

        tech_result_list = query_by_field(tech_result_list, query_filter, TechResult)

        if start_time:
            tech_result_list = tech_result_list.filter(db.cast(TechResult.begin_time, db.Date) >= start_time)

        if end_time:
            tech_result_list = tech_result_list.filter(db.cast(TechResult.begin_time, db.Date) <= end_time)
        if key_word:
            tech_result_list = tech_result_list.filter(TechResult.body.like('%{}%'.format(key_word)))
        total = tech_result_list.count()

        tech_result_list = tech_result_list.offset((page - 1) * limit).limit(limit).all()

        return jsonify({
            'message': 'success',
            'items': [u.to_dict() for u in tech_result_list],
            'totalCount': total,
            'TotalPageCount': math.ceil(int(total / limit))
        })
    except Exception as e:
        print("get tech_results error:", e)

    response = jsonify({'message': "error when query match results"})
    response.status_code = 500
    return response


@r_tech_result.route('/<int:pid>', methods=['GET'])
# @auth.login_required
def get_detail(pid):
    """ get_tech_results API Endpoint
            ---
            tags:
              - tech_result
            parameters:
               - name: tech_result_id
                 in: path
                 type: integer
                 required: true
                 description: tech_result_id of tech_result
            responses:
              200:
                description: { 'item': {}}
            """
    tech_result = TechResult.query.filter_by(id=pid).first()
    if not tech_result:
        response = jsonify({
            'message': 'not result detail found!'
        })
        response.status_code = 404
        return response
    details = TechDetail.query.filter(TechDetail.result_id == tech_result.id).order_by(TechDetail.minute + TechDetail.min_ex).all()
    result = tech_result.to_dict()
    result['details'] = [u.to_dict() for u in details]

    return jsonify({
        'message': 'success',
        'item': result,
    })
