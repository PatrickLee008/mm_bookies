from app_server import app, db, auth, app_opt
from flask import jsonify, Blueprint, request, g
from app_server.model.UploadedImageModel import UploadedImage
from sqlalchemy import or_, func

r_up_image = Blueprint('up_image', __name__)


@r_up_image.route('/get', methods=['GET'])
# @auth.login_required
def get_images():
    """ get_tech_results API Endpoint
                ---
                tags:
                  - up_image
                parameters:
                   - name: current_page
                     in: query
                     type: string
                     required: true
                     description: current_page of up_image
                   - name: limit
                     in: query
                     type: integer
                     description: limit of up_image
                responses:
                  200:
                    description: { 'items': [...]}
                """
    current_page = request.args.get('page', type=int, default=1)
    limit = request.args.get('limit', type=int, default=20)

    image_list = UploadedImage.query

    image_list = image_list.offset((current_page - 1) * limit).limit(limit).all()

    return jsonify({
        'items': [u.to_dict() for u in image_list],
    })

