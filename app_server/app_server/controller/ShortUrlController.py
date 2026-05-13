# -*- coding: utf-8 -*-
from app_server import app, db, get_logger
from flask import Blueprint, redirect, abort
from app_server.model.AppAdlinkModel import AppAdlink

logger = get_logger()
short_url = Blueprint('short_url', __name__)


@short_url.route('/<ad_link_id>/<random_str>', methods=['GET'])
def redirect_to_full_url(ad_link_id, random_str):
    """
    短链接重定向接口
    根据广告链接ID从数据库中查询完整URL并重定向

    访问示例:
    http://127.0.0.1:8282/s/adLinkId/randomStr
    或
    http://a.sort/adLinkId/randomStr (通过nginx反向代理)

    :param ad_link_id: 广告链接ID
    :param random_str: 随机字符串(用于防止缓存)
    :return: 重定向到完整URL或404错误
    """
    try:
        # 从数据库查询广告链接
        adlink = AppAdlink.query.filter_by(id=ad_link_id).first()

        # 如果找不到或状态不是active，返回404
        if not adlink:
            logger.warning(f"AdLink not found: {ad_link_id}")
            abort(404)

        # 检查链接状态
        if adlink.status != 'active':
            logger.warning(f"AdLink is not active: {ad_link_id}, status: {adlink.status}")
            abort(404)

        # 检查是否有完整URL
        if not adlink.full_url:
            logger.error(f"AdLink full_url is empty: {ad_link_id}")
            abort(404)

        # 可选：更新点击量统计（前端已经处理了点击，除非取消前端处理，因为要记录点击日志）
        # try:
        #     adlink.clicks = (adlink.clicks or 0) + 1
        #     db.session.commit()
        # except Exception as e:
        #     # 统计更新失败不影响重定向
        #     logger.error(f"Failed to update clicks for {ad_link_id}: {str(e)}")
        #     db.session.rollback()

        # 执行302重定向到完整URL
        logger.info(f"Redirecting {ad_link_id}/{random_str} to {adlink.full_url}")
        return redirect(adlink.full_url, code=302)

    except Exception as e:
        logger.error(f"Short URL redirect exception for {ad_link_id}: {str(e)}")
        abort(500)
