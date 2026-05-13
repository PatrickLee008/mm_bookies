from app_server import app, db
from flask import jsonify, Blueprint, request
from app_server.model.AppAdvertisementModel import AppAdvertisement
from sqlalchemy import or_
from datetime import datetime

r_advertisement = Blueprint('advertisement', __name__)


@r_advertisement.route('/get_active', methods=['GET'])
def get_active_advertisements():
    """获取当前有效的广告列表
    ---
    tags:
      - advertisement
    parameters:
      - name: position
        in: query
        type: string
        required: true
        description: 广告位置(Register, Home Banner, Popup, Sidebar, Game List)
      - name: tenant_id
        in: query
        type: string
        required: false
        description: 租户ID，默认为10000
    responses:
      200:
        description: 返回当前有效的广告列表
      400:
        description: 缺少必要参数
    """
    try:
        position = request.args.get('position', type=str)
        if not position:
            return jsonify({
                'code': 400,
                'data': None,
                'message': 'position parameter is required'
            }), 400

        tenant_id = request.args.get('tenant_id', type=str, default='10000')
        now = datetime.now()

        query = AppAdvertisement.query.filter(
            AppAdvertisement.del_flag == 0,
            AppAdvertisement.is_active == 1,
            AppAdvertisement.tenant_id == tenant_id,
            AppAdvertisement.position == position
        )

        query = query.filter(
            or_(
                AppAdvertisement.start_date == None,
                AppAdvertisement.start_date <= now
            ),
            or_(
                AppAdvertisement.end_date == None,
                AppAdvertisement.end_date >= now
            )
        )

        advertisements = query.order_by(AppAdvertisement.sort.desc()).all()
        result = [ad.to_dict() for ad in advertisements]

        return jsonify({
            'code': 200,
            'data': {
                'items': result,
                'total': len(result)
            },
            'message': 'success'
        })

    except Exception as e:
        app.logger.error(f"Error fetching advertisements: {str(e)}")
        return jsonify({
            'code': 500,
            'data': None,
            'message': f'Failed to fetch advertisements: {str(e)}'
        }), 500
