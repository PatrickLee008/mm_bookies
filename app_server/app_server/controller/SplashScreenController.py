from app_server import app, db, auth
from flask import jsonify, Blueprint, request, g
from app_server.model.AppSplashScreenModel import AppSplashScreen
from sqlalchemy import or_, and_
from datetime import datetime

r_splash_screen = Blueprint('splash_screen', __name__)


@r_splash_screen.route('/get_active', methods=['GET'])
def get_active_splash_screens():
    """获取当前有效的启动页配置
    ---
    tags:
      - splash_screen
    parameters:
      - name: tenant_id
        in: query
        type: string
        required: false
        description: 租户ID，默认为10000
    responses:
      200:
        description: 返回当前有效的启动页列表
        schema:
          type: object
          properties:
            code:
              type: integer
              example: 200
            data:
              type: object
              properties:
                splash_screens:
                  type: array
                  items:
                    type: object
            message:
              type: string
              example: "success"
    """
    try:
        # 获取租户ID，默认为10000
        tenant_id = request.args.get('tenant_id', type=str, default='10000')

        # 获取当前时间
        now = datetime.now()

        # 查询条件:
        # 1. 未删除 (del_flag = 0)
        # 2. 启用状态 (is_active = 1)
        # 3. 租户匹配
        # 4. 当前时间在展示期间内
        query = AppSplashScreen.query.filter(
            AppSplashScreen.del_flag == 0,
            AppSplashScreen.is_active == 1,
            AppSplashScreen.tenant_id == tenant_id
        )

        # 时间范围过滤
        query = query.filter(
            or_(
                AppSplashScreen.start_date == None,
                AppSplashScreen.start_date <= now
            ),
            or_(
                AppSplashScreen.end_date == None,
                AppSplashScreen.end_date >= now
            )
        )

        # 按 sort 排序
        splash_screens = query.order_by(AppSplashScreen.sort.asc()).all()

        # 转换为字典列表
        result = [screen.to_dict() for screen in splash_screens]

        return jsonify({
            'code': 200,
            'data': {
                'splash_screens': result,
                'total': len(result)
            },
            'message': 'success'
        })

    except Exception as e:
        app.logger.error(f"Error fetching splash screens: {str(e)}")
        return jsonify({
            'code': 500,
            'data': None,
            'message': f'Failed to fetch splash screens: {str(e)}'
        }), 500


@r_splash_screen.route('/get_all', methods=['GET'])
@auth.login_required
def get_all_splash_screens():
    """获取所有启动页配置（管理员用）
    ---
    tags:
      - splash_screen
    security:
      - JWT: []
    parameters:
      - name: page
        in: query
        type: integer
        required: false
        default: 1
        description: 页码
      - name: limit
        in: query
        type: integer
        required: false
        default: 20
        description: 每页数量
      - name: tenant_id
        in: query
        type: string
        required: false
        description: 租户ID筛选
    responses:
      200:
        description: 返回启动页列表
    """
    try:
        # 获取分页参数
        page = request.args.get('page', type=int, default=1)
        limit = request.args.get('limit', type=int, default=20)
        tenant_id = request.args.get('tenant_id', type=str, default=None)

        # 构建查询
        query = AppSplashScreen.query.filter(AppSplashScreen.del_flag == 0)

        # 租户过滤
        if tenant_id:
            query = query.filter(AppSplashScreen.tenant_id == tenant_id)

        # 获取总数
        total = query.count()

        # 分页查询
        splash_screens = query.order_by(
            AppSplashScreen.sort.asc(),
            AppSplashScreen.create_time.desc()
        ).offset((page - 1) * limit).limit(limit).all()

        return jsonify({
            'code': 200,
            'data': {
                'items': [screen.to_dict() for screen in splash_screens],
                'total': total,
                'page': page,
                'limit': limit
            },
            'message': 'success'
        })

    except Exception as e:
        app.logger.error(f"Error fetching all splash screens: {str(e)}")
        return jsonify({
            'code': 500,
            'data': None,
            'message': f'Failed to fetch splash screens: {str(e)}'
        }), 500
