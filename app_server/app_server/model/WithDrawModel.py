from app_server import db, app
from sqlalchemy import Column, String, Integer, Text
from sqlalchemy.dialects.mysql import DATETIME, DECIMAL
from datetime import datetime
from typing import Optional

from app_server.utils.BaseSaasModel import BaseSaasModel


# 系统提现记录
class WithDraw(BaseSaasModel):
    __tablename__ = 'm_app_withdraw'

    # 主键与交易信息
    id = Column(String(64), primary_key=True, comment="唯一提现记录ID")
    aid = Column(String(64), index=True, comment="代理ID")
    trade_no = Column(String(64), unique=True, comment="系统提现单号")
    out_trade_no = Column(String(64), comment="第三方交易ID（如银行流水号）")

    # 提现方式与金额
    pay_type = Column(String(255), nullable=False, server_default='MANUAL', comment="提现方式（KBZ，KBZ-AUTO，MANUAL）")
    withdraw_type = Column(String(32), nullable=False, server_default='USER', comment="提现类型（USER、AGENT）")
    withdraw_code = Column(String(32), nullable=False, server_default='', comment="提现码")
    work_group_id = Column(String(32), nullable=False, server_default='', comment="提现工作组ID")
    amount = Column(DECIMAL(10, 0), nullable=False, server_default=None, comment="申请提现金额")
    before_amount = Column(DECIMAL(16, 4), nullable=False, server_default=None,comment="提现前余额")
    after_amount = Column(DECIMAL(16, 4), nullable=False, server_default=None, comment="提现后余额")

    # 会员信息
    mb_id = Column(String(64), index=True, comment="会员账号ID")
    mb_username = Column(String(255), comment="会员账号")
    mb_nickname = Column(String(64), comment="会员昵称")
    mb_bank_code = Column(String(255), comment="会员银行代码（如ICBC）")
    mb_acc_name = Column(String(255), comment="会员银行账户名")
    mb_acc_number = Column(String(255), comment="会员银行账号")

    # 管理员/操作人信息
    mn_id = Column(String(64), comment="管理员ID（审核人）")
    mn_name = Column(String(255), comment="管理员姓名")
    mn_username = Column(String(255), comment="管理员登录名")
    mn_add_name = Column(String(255), comment="操作人员姓名（后台新增方式）")

    # 收款账户信息
    rc_id = Column(String(64), comment="收款账户ID（可能为代理或公司账户）")
    rc_bank_code = Column(String(255), comment="收款方银行代码")
    rc_acc_name = Column(String(255), comment="收款方账户名")
    rc_acc_number = Column(String(255), comment="收款方银行账号")

    # 时间信息
    confirm_time = Column(DATETIME, comment="财务确认时间")
    process_time = Column(DATETIME, comment="实际处理完成时间")

    # 状态与日志
    status = Column(String(32), nullable=False, server_default='new',comment="提现状态：new,processing,verify,reject,completed,failed")
    callback_log = Column(Text, comment="第三方回调日志（JSON格式）")
    order_log = Column(Text, comment="提现订单状态变更日志")
    slip = Column(Text, comment="付款凭证（如转账截图URL）")

    __mapper_args__ = {
        "order_by": BaseSaasModel.create_time.desc(),
    }
