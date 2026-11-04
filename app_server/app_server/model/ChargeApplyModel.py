from datetime import datetime, date
from decimal import Decimal

from sqlalchemy import Column, String, Text
from sqlalchemy.dialects.mysql import DATETIME, DECIMAL, TINYINT

from app_server import db
from app_server.utils.BaseSaasModel import BaseSaasModel


class StatusMap:
    Pending = 0
    Success = 1
    Rejected = 2


class StatusLabelMap:
    """充值申请状态（PascalCase）

    ⚠️ 与 Java 侧 AppConstantsExt.RechargeStatus 必须逐字一致，否则回调与后台认不出。
    状态机：New → Pending → Success / Failed / Timeout
                        └→ Cancelling → Cancelled（取消成功后回调成功仍要入账）
    """
    New = "New"                # 新订单，未成功提交到支付中心
    Pending = "Pending"        # 处理中（已提交支付中心，等待付款）
    Success = "Success"        # 成功入账
    Failed = "Failed"          # 下单失败 / 回调失败
    Rejected = "Rejected"      # 人工拒绝
    Timeout = "Timeout"        # 已过期（惰性判定 + 对账脚本）
    Cancelling = "Cancelling"  # 取消处理中（租约抢占）
    Cancelled = "Cancelled"    # 已取消


# 玩家充值申请表
class ChargeApply(BaseSaasModel):
    __tablename__ = 'm_app_recharge_apply'

    id = Column(String(64), nullable=False, primary_key=True, comment="充值申请ID")
    aid = Column(String(64), nullable=True, comment="会员所属代理ID")
    recharge_id = Column(String(64), nullable=False, server_default='', comment="当充值通过时,对应的充值ID")
    mb_id = Column(String(64), nullable=False, server_default='', comment="会员ID")
    mb_nickname = Column(String(64), nullable=False, server_default='', comment="会员昵称")
    mb_username = Column(String(64), nullable=False, server_default='', comment="会员账号")
    mb_bank_code = Column(String(50), nullable=False, server_default='', comment="会员银行代码")
    mb_acc_name = Column(String(255), nullable=False, server_default='', comment="会员账户名")
    mb_acc_number = Column(String(50), nullable=False, server_default='', comment="会员账号")
    charge_name = Column(String(255), nullable=False, server_default='SYSTEM', comment="上分人员：SYSTEM(系统自动上分)")
    charge_status = Column(TINYINT, nullable=False, server_default='0',
                           comment="上分状态：-1无须上分，0创建，1待上分，2已上分")
    # 下单金额（回调后会被实际入账金额覆盖），原始下单金额保留在 original_amount
    money = Column(DECIMAL(16, 2), nullable=False, server_default='0.00', comment="金额")
    original_amount = Column(DECIMAL(20, 2), nullable=True, comment="原始下单金额")
    remark = Column(String(256), nullable=False, server_default='', comment="备注：申请说明")
    picture = Column(String(256), nullable=False, server_default='', comment="充值图片名称")
    fail_reason = Column(String(256), nullable=False, server_default='', comment="充值不通过原因")
    charge_way = Column(TINYINT, nullable=False, server_default='0', comment="充值途径,0:自动充值,1:手动充值")

    # 通道与支付中心信息
    pay_channel = Column(String(32), comment="支付通道（VIPPay_CashCode 记账时归 VIPPay）")
    out_trade_no = Column(String(64), nullable=False, server_default='', comment="支付中心 tradeNo")
    out_order_id = Column(String(64), comment="支付中心 tradeOrderId")
    pay_url = Column(String(512), comment="外部收银页地址（仅在无收款账号、需跳服务商页时使用）")

    callback_status = Column(TINYINT, nullable=False, server_default='0',
                             comment="回调状态：0无须回调，1待回调，2已回调处理,-1回调异常")
    callback_time = Column(DATETIME, comment="回调时间")
    callback_log = Column(Text, comment="回调日志")
    receive_bank_code = Column(String(64), comment="收款银行")
    receive_account = Column(String(64), comment="收款卡")
    receive_account_name = Column(String(64), comment="收款卡名")

    # 用户提交的交易号后 5 位（MCPay / KingPay）
    txn_last5 = Column(String(8), comment="交易号后 5 位")
    txn_submit_time = Column(DATETIME, comment="交易号提交时间")

    # 取消租约（不能复用 update_time：BaseSaasModel 带 onupdate，每次 UPDATE 都会刷新）
    cancel_lease_at = Column(DATETIME, comment="取消租约抢占时间")

    refund_time = Column(DATETIME, comment="退款时间")
    refund_money = Column(DECIMAL(16, 0), server_default='0', comment="退款金额")
    status = Column(String(20), nullable=False, server_default='New',
                    comment="充值状态：New/Pending/Success/Failed/Rejected/Timeout/Cancelling/Cancelled")
    expire_time = Column(DATETIME, comment="超时时间")

    __mapper_args__ = {
        "order_by": BaseSaasModel.create_time.desc(),
    }

    def remaining_seconds(self):
        """剩余秒数（服务端计算，前端不得用本地时间算倒计时）。"""
        if not self.expire_time:
            return 0
        remain = int((self.expire_time - datetime.now()).total_seconds())
        return remain if remain > 0 else 0

    def to_dict(self, include=None, exclude=None):
        result = {}
        for k in self.__table__.columns.keys():
            if include and k not in include:
                continue
            if exclude and k in exclude:
                continue
            value = getattr(self, k)
            if isinstance(value, (datetime, date, Decimal)):
                value = str(value)
            # None 归一为空串：避免前端拿到字符串 "None"（历史 to_dict 用 str(None) 的坑）
            if value is None:
                value = ""
            result[k] = value

        # 图片字段单独处理，None/空 不拼前缀
        picture_name = result.get("picture") or ""
        result["picture"] = ("static/img/charge_pics/%s" % picture_name) if picture_name else ""

        result["REMAINING_SECONDS"] = self.remaining_seconds()
        return result


db.create_all()
