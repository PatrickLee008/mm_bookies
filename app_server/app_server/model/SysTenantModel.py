from app_server import db, app
from sqlalchemy import Column, String, Boolean, Integer, Text, DECIMAL
from sqlalchemy.dialects.mysql import TIMESTAMP, DATETIME, TINYINT
from datetime import datetime, date
from decimal import Decimal
from app_server.utils.BaseSaasModel import BaseSaasModel


# 系统租户表
class SysTenant(BaseSaasModel):
    __tablename__ = 'sys_tenant'

    id = Column(String(64), primary_key=True, comment="租户ID")
    name = Column(String(64), nullable=False, server_default='', comment="租户名称")
    begin_date = Column(DATETIME, comment="有效期开始时间")
    end_date = Column(DATETIME, comment="有效期结束时间")
    status = Column(String(1), nullable=False, server_default='1', comment="状态(0停用 1正常)")
    domain = Column(String(64), nullable=False, server_default='', comment="域名")
    color = Column(String(64), nullable=False, server_default='', comment="主题色")

    __mapper_args__ = {
        "order_by": BaseSaasModel.create_time.desc(),
    }

    # 获取tenant_id
    @staticmethod
    def get_tenant_id(request):
        # 获取tenant_id
        host = request.headers.get('host')
        # 处理host，比如localhost:8282，只需要域名部分
        if ':' in host:
            host = host.split(':')[0]
        # 如果是localhost或者127.0.0.1，则默认是tenant_id="10000"
        if host in ['localhost', '127.0.0.1']:
            return "10000"
        # 从数据库表sys_tenant，查询domain对应的tenant_id
        tenant = SysTenant.query.filter_by(domain=host).first()
        if not tenant:
            return None
        return tenant.id

db.create_all()