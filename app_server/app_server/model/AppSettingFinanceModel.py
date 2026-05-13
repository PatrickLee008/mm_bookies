from app_server import db, app
from sqlalchemy import Column, String, Integer
from sqlalchemy.dialects.mysql import DATETIME, DECIMAL, TINYINT
from datetime import datetime
from typing import Optional

from app_server.utils.BaseSaasModel import BaseSaasModel


# 财务参数配置表
class AppSettingFinanceModel(BaseSaasModel):
    __tablename__ = 'm_app_setting_finance'

    # 主键与基础信息
    id = Column(String(64), primary_key=True, comment="主键ID")
    type = Column(TINYINT, comment="配置类型：1代理会员配置（agent代理配置），2代理配置（充值给代理使用，非agent的配置）")
    aid = Column(String(64), comment="代理ID")
    agent_name = Column(String(64), comment="代理名称")

    # 存款设置
    sf_min_deposit = Column(DECIMAL(16, 4), comment="单笔最低存款金额")
    sf_max_deposit = Column(DECIMAL(16, 4), comment="单笔最高存款金额")

    # 取款设置
    sf_min_withdrawal = Column(DECIMAL(16, 4), comment="单笔最低取款金额")
    sf_max_withdrawal = Column(DECIMAL(16, 4), comment="单笔最高取款金额")

    # 代理转账设置
    sf_min_ag_transfer = Column(DECIMAL(16, 4), comment="代理转账最低金额")
    sf_max_ag_transfer = Column(DECIMAL(16, 4), comment="代理转账最高金额")

    # 限额设置
    sf_recieve_limit_day = Column(DECIMAL(16, 4), comment="每日收款限额（代理/商户）")
    withdraw_turnover_rate = Column(DECIMAL(10, 2), comment="提现周转率")
    cur_withdraw_group = Column(Integer, comment="当前提现组ID")
    withdraw_group_expiration = Column(Integer, comment="提现组操作超时控制")

    # 状态控制
    status = Column(TINYINT, nullable=False, server_default='1', comment="状态(0:禁用,1:启用)")
    sort = Column(Integer, server_default='0', comment="排序序号")

    __mapper_args__ = {
        "order_by": BaseSaasModel.create_time.desc(),
    }

    @staticmethod
    def get_by_aid(aid: str, tenant_id: str = None) -> Optional['AppSettingFinanceModel']:
        """
        通过代理ID获取财务配置
        :param aid: 代理ID
        :param tenant_id: 租户ID
        :return: 财务配置对象
        """
        query = db.session.query(AppSettingFinanceModel).filter_by(
            aid=aid,
            del_flag=0,
            status=1
        )
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        return query.first()

    @staticmethod
    def get_by_type(config_type: int, tenant_id: str = None) -> list:
        """
        通过配置类型获取财务配置列表
        :param config_type: 配置类型
        :param tenant_id: 租户ID
        :return: 财务配置列表
        """
        query = db.session.query(AppSettingFinanceModel).filter_by(
            type=config_type,
            del_flag=0,
            status=1
        )
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        return query.all()

    @staticmethod
    def get_agent_config(aid: str = '0', tenant_id: str = None) -> Optional['AppSettingFinanceModel']:
        """
        获取默认财务配置
        :param aid:
        :param tenant_id: 租户ID
        :return: 财务配置对象
        """
        query = db.session.query(AppSettingFinanceModel).filter_by(
            aid=aid,
            type=1,
            del_flag=0,
            status=1
        )
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)

        return query.first()