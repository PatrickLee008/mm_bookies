from app_server import db, app
from sqlalchemy import Column, String, Integer, Text, BigInteger
from sqlalchemy.dialects.mysql import DATETIME, TINYINT
from datetime import datetime
from typing import Optional

from app_server.utils.BaseSaasModel import BaseSaasModel


# 应用其他设置表
class MAppSettingOther(BaseSaasModel):
    __tablename__ = 'm_app_setting_other'

    # 主键与基础信息
    id = Column(String(64), primary_key=True, comment="主键ID")
    tenant_id = Column(String(64), server_default='10000', comment="租户ID")

    # 设置信息
    setting_key = Column(String(128), nullable=False, comment="设置键（唯一标识）")
    setting_name = Column(String(255), comment="设置名称（显示用）")
    setting_type = Column(String(64), comment="设置类型")
    setting_value = Column(Text, comment="设置值")
    content_type = Column(String(32), server_default='text', comment="内容类型")
    language_type = Column(String(64), comment="语种")

    # 代理信息
    aid = Column(String(64), comment="代理ID")
    agent_name = Column(String(255), comment="代理名称")

    # 状态控制
    status = Column(Integer, server_default='1', comment="状态（0: 禁用, 1: 启用）")
    sort = Column(BigInteger, server_default='100', comment="排序序号")

    # 审计信息
    create_by_id = Column(String(64), comment="创建人ID")
    update_by_id = Column(String(64), comment="更新人ID")
    remarks = Column(String(500), comment="备注信息")
    del_flag = Column(Integer, server_default='0', comment="删除标记（0: 正常, 1: 删除）")

    __mapper_args__ = {
        "order_by": sort.asc(),
    }
