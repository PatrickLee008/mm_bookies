from app_server import app, db, auth
from app_server.controller.AppUserController import verify_token
from app_server.model.MAppSettingOtherModel import MAppSettingOther
from flask import g, request, jsonify, Blueprint
from app_server.utils import OrmUttil
from app_server.utils import PageConfig
from sqlalchemy import or_, func, and_

setting = Blueprint('setting', __name__)


# 获取其他设置列表（全量查询）
@setting.route('/get_all', methods=['GET'])
def get_all_settings():
    """获取所有其他设置
    ---
    tags:
      - setting
    parameters:
      - name: setting_type
        in: query
        type: string
        required: false
        description: 设置类型（可选，用于过滤）
      - name: status
        in: query
        type: integer
        required: false
        description: 状态（0: 禁用, 1: 启用）
      - name: language_type
        in: query
        type: string
        required: false
        description: 语种（可选，用于过滤）
    responses:
      200:
        description: { 'items': [...], 'total': 100 }
    """
    # 获取查询参数
    setting_type = request.args.get('setting_type')
    status = request.args.get('status', type=int)
    language_type = request.args.get('language_type')

    # 构建查询（2026-11-11：只读取通用或本平台的配置）
    query = MAppSettingOther.query.filter(MAppSettingOther.del_flag == 0, MAppSettingOther.tenant_id == '10000',
                                          PageConfig.platform_condition())

    # 可选过滤条件
    if setting_type:
        query = query.filter(MAppSettingOther.setting_type == setting_type)
    else:
        # 不指定类型时（如公告列表）不返回页面配置，避免充值说明等被当成公告显示
        query = query.filter(~MAppSettingOther.setting_type.like('%/%'))

    if status is not None:
        query = query.filter(MAppSettingOther.status == status)

    if language_type:
        query = query.filter(MAppSettingOther.language_type == language_type)

    # 按排序字段排序
    query = query.order_by(MAppSettingOther.sort.asc(), MAppSettingOther.create_time.desc())

    # 执行查询
    settings = query.all()

    # 转换为字典列表
    items = [setting.to_dict() for setting in settings]

    data = {
        'items': items,
        'total': len(items)
    }
    # 页面配置：附带当前版本，前端与数据一起缓存（见 utils/PageConfig.py）
    if PageConfig.is_page_type(setting_type):
        data['version'] = PageConfig.page_version(setting_type)

    return jsonify({
        'code': 20000,
        'message': 'Success',
        'data': data
    })


# 根据 setting_key 获取单个设置
@setting.route('/get_by_key/<setting_key>', methods=['GET'])
def get_setting_by_key(setting_key):
    """根据 setting_key 获取设置
    ---
    tags:
      - setting
    parameters:
      - name: setting_key
        in: path
        type: string
        required: true
        description: 设置键
      - name: aid
        in: query
        type: string
        required: false
        description: 代理ID（可选）
      - name: language_type
        in: query
        type: string
        required: false
        description: 语种（可选，用于过滤多语言配置）
    responses:
      200:
        description: { 'data': {...} }
      404:
        description: Setting not found
    """
    aid = request.args.get('aid')
    language_type = request.args.get('language_type')

    # 构建查询
    query = MAppSettingOther.query.filter(
        MAppSettingOther.setting_key == setting_key,
        MAppSettingOther.del_flag == 0,
        MAppSettingOther.status == 1,
        PageConfig.platform_condition(),
    ).order_by(
        # 同一个 key 既有通用又有本平台配置时，本平台优先
        MAppSettingOther.platform.desc(), MAppSettingOther.sort.asc()
    )

    # 如果指定了语种，添加语种过滤
    if language_type:
        query = query.filter(MAppSettingOther.language_type == language_type)

    # 如果指定了 aid，优先查询代理级别配置
    if aid:
        setting = query.filter(MAppSettingOther.aid == aid).first()
        if not setting:
            # 如果没有代理级别配置，查询全局配置（aid 为 NULL 或空字符串）
            setting = query.filter(
                or_(MAppSettingOther.aid.is_(None), MAppSettingOther.aid == '')
            ).first()
    else:
        # 只查询全局配置（aid 为 NULL 或空字符串）
        setting = query.filter(
            or_(MAppSettingOther.aid.is_(None), MAppSettingOther.aid == '')
        ).first()

    if not setting:
        return jsonify({
            'code': 40400,
            'message': 'Setting not found',
            'data': None
        }), 404

    return jsonify({
        'code': 20000,
        'message': 'Success',
        'data': setting.to_dict()
    })
