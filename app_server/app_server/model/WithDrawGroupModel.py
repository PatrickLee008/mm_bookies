from app_server import db
from sqlalchemy import Column, String, Integer, DateTime, Boolean
from sqlalchemy.dialects.mysql import DECIMAL, TINYINT


class WithDrawGroup(db.Model):
    """提现组

    2026-11-11 改用新表 m_app_withdrawal_group（原表 m_withdrawal_group 没有租户 ID、不符合标准表规范）：
      - 由原表迁移的记录保持原 ID（字符串），提现单 work_group_id 仍能对上；后台新建的组 ID 为雪花字符串；
      - AID 为空 = 默认（平台）提现组；有值 = 该代理自己的提现组；
      - 逻辑删除（DEL_FLAG=1 的组不参与分配）。
    属性名保持原来的大写写法，列名映射到新表的小写列。
    需先执行 javasaas-game/功能迭代/20261111_jp-console_MMBookies测试缺陷修复/sql/03_app_withdrawal_group.sql
    """
    __tablename__ = 'm_app_withdrawal_group'
    ID = Column('id', String(64), primary_key=True)
    AID = Column('aid', String(64), nullable=False, server_default="", comment="代理ID，空=默认提现组")
    GROUP_NAME = Column('group_name', String(255), server_default="", nullable=False, comment="组名称")
    REMARK = Column('remark', String(255), nullable=False, server_default="", comment="备注")

    MAX_HANDLE = Column('max_handle', Integer, nullable=False, server_default="10", comment="最大处理数量")
    NOW_HANDLE = Column('now_handle', Integer, nullable=False, server_default="0", comment="当前处理数量")
    HANDLE_ON = Column('handle_on', Boolean, nullable=False, server_default="1", comment="处理开关: 0:关 1:开")

    # 2026-10-29 支付中心接入：按金额区间路由 + 是否允许网关自动出款
    MIN_AMOUNT = Column('min_amount', DECIMAL(20, 2), nullable=False, server_default="0.00", comment="处理提现金额下限(含)")
    MAX_AMOUNT = Column('max_amount', DECIMAL(20, 2), nullable=False, server_default="0.00", comment="处理提现金额上限(含)")
    AUTO_PAY = Column('auto_pay', TINYINT, nullable=False, server_default="0", comment="1=允许网关自动出款")

    CREATE_BY_ID = Column('create_by_id', String(64))
    CREATE_TIME = Column('create_time', DateTime)
    UPDATE_BY_ID = Column('update_by_id', String(64))
    UPDATE_TIME = Column('update_time', DateTime)
    DEL_FLAG = Column('del_flag', Integer, nullable=False, server_default="0", comment="删除标记")
    TENANT_ID = Column('tenant_id', String(64), server_default="10000", comment="租户ID")

    def to_dict(self):
        result = {}
        for attr in self.__mapper__.column_attrs:
            value = getattr(self, attr.key)
            if attr.key in {'CREATE_TIME', 'UPDATE_TIME'}:
                value = str(value)
            result[attr.key] = value
        return result


db.create_all()
