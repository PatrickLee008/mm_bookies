# -*- coding: utf-8 -*-
"""
页面配置（Setting → Other，m_app_setting_other）公共方法（2026-11-11）

1. 平台过滤：javasaas-game 后台由 onex2 / mmbookies 两套前端共用，只读取
   platform 为空（通用）或等于本服务 APP_PLATFORM 的配置。
2. 配置版本号：前端缓存页面配置，版本变了才重新拉取。
   - 版本由数据推算：每个页面 MAX(update_time) + COUNT(*) 取短哈希。后台新增、修改、
     删除（逻辑删除也会更新 update_time，且 COUNT 变化）、导入、直接改库都会让版本变化，
     不需要在每个写入口维护版本号。
   - /config/get 下发 page_config_versions（Redis 缓存 PAGE_VERSION_CACHE_SECONDS 秒）；
   - /setting/get_all?setting_type=<页面> 返回数据时附带当时的 version（不走缓存，保证数据和版本一致）。
页面配置的 setting_type 是页面路由（含 "/"，如 wallet/deposit），与原有 GameGuide 等通用类型区分。
"""
import hashlib
import json

from sqlalchemy import func, or_

from app_server import app, db, Redis
from app_server.logger import get_logger
from app_server.model.MAppSettingOtherModel import MAppSettingOther

logger = get_logger()

PAGE_VERSION_CACHE_SECONDS = 60
TENANT_ID = '10000'


def current_platform():
    return (app.config.get('APP_PLATFORM') or '').strip()


def platform_condition():
    """platform 为空（通用）或等于本服务平台"""
    platform = current_platform()
    conds = [MAppSettingOther.platform == '', MAppSettingOther.platform.is_(None)]
    if platform:
        conds.append(MAppSettingOther.platform == platform)
    return or_(*conds)


def is_page_type(setting_type):
    return bool(setting_type) and '/' in setting_type


def _version_of(max_update, count):
    if hasattr(max_update, 'strftime'):
        max_update = max_update.strftime('%Y-%m-%d %H:%M:%S')
    raw = '%s|%s' % (max_update or '', count or 0)
    return hashlib.md5(raw.encode('utf-8')).hexdigest()[:12]


def _query_versions(setting_type=None):
    query = db.session.query(
        MAppSettingOther.setting_type,
        func.max(MAppSettingOther.update_time),
        func.count(MAppSettingOther.id),
    ).filter(
        MAppSettingOther.del_flag == 0,
        MAppSettingOther.tenant_id == TENANT_ID,
        MAppSettingOther.setting_type.like('%/%'),
        platform_condition(),
    )
    if setting_type:
        query = query.filter(MAppSettingOther.setting_type == setting_type)
    rows = query.group_by(MAppSettingOther.setting_type).all()
    return {st: _version_of(max_update, cnt) for st, max_update, cnt in rows}


def page_version(setting_type):
    """单个页面的当前版本（不走缓存）；没有任何配置时返回 'empty'"""
    return _query_versions(setting_type).get(setting_type, 'empty')


def page_versions():
    """本平台所有页面的版本 {页面: 版本}，Redis 缓存 60 秒；Redis 不可用时直接查库"""
    cache_key = 'page_cfg_versions:%s' % (current_platform() or 'common')
    try:
        cached = Redis.get(cache_key)
        if cached:
            return json.loads(cached)
    except Exception as e:
        logger.warning('读取页面配置版本缓存失败: %s', e)
    try:
        versions = _query_versions()
    except Exception as e:
        # 表未升级（缺 platform 列）等情况：不影响 /config/get 其他配置
        logger.error('计算页面配置版本失败: %s', e)
        db.session.rollback()
        return {}
    try:
        Redis.set(cache_key, json.dumps(versions), ex=PAGE_VERSION_CACHE_SECONDS)
    except Exception as e:
        logger.warning('写入页面配置版本缓存失败: %s', e)
    return versions
