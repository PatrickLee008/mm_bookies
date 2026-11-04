# -*- coding: utf-8 -*-
"""
充值订单对账脚本（Recharge Order Reconciliation）

用途：
  1) 全局扫描处于 Cancelling（取消处理中）但租约已过期的充值订单，
     重新抢占租约并向支付中心重试取消。
     —— 覆盖 worker 在取消过程中崩溃/断网、遗留 Cancelling 订单的场景。
  2) 把 Pending 且已过期的 VIPPay / VIPPay_CashCode 订单置为 Timeout，
     与移动端 /charge_apply/status 的惰性超时判定保持一致。
     其它通道（MCPay/KingPay/TCPay）的过期单只靠接口惰性判定，不在这里改。

运行：
  cd app_server（本文件所在目录）
  <venv>/bin/python reconcile_charge_orders.py

建议 cron（每分钟）—— 三个品牌各配一份，且必须先 cd 到服务目录（否则读不到 .env）：
  * * * * * cd /path/to/mm_bookies/app_server && /path/to/venv/bin/python reconcile_charge_orders.py >> /var/log/reconcile_charge.log 2>&1
"""
import sys
from datetime import datetime, timedelta

from sqlalchemy import or_

from app_server import app, db
from app_server.model.ChargeApplyModel import ChargeApply, StatusLabelMap
# 复用控制器里的租约/取消逻辑，避免重复实现
from app_server.controller.ChargeApplyController import (
    _claim_cancel_lease,
    _execute_cancel_attempt,
    get_cancel_lease_seconds,
    CANCELABLE_CHANNELS,
)


def reconcile_stale_cancellations():
    """全局对账所有用户遗留的 Cancelling 订单。返回 (处理数, 成功数)。"""
    now = datetime.now()
    lease_seconds = get_cancel_lease_seconds()
    lease_cutoff = now - timedelta(seconds=lease_seconds)

    stale_applies = ChargeApply.query.filter(
        ChargeApply.status == StatusLabelMap.Cancelling,
        or_(ChargeApply.cancel_lease_at.is_(None), ChargeApply.cancel_lease_at <= lease_cutoff),
    ).all()

    processed, succeeded = 0, 0
    for apply in stale_applies:
        apply_id = apply.id
        user_id = apply.mb_id
        payment_order_id = apply.out_order_id
        claim_time = datetime.now().replace(microsecond=0)
        if not _claim_cancel_lease(apply, user_id, claim_time, lease_seconds):
            continue
        processed += 1
        try:
            result = _execute_cancel_attempt(apply_id, user_id, payment_order_id, claim_time)
            if result.get('success'):
                succeeded += 1
                print("[reconcile] cancelled apply=%s out_order=%s" % (apply_id, payment_order_id))
            else:
                print("[reconcile] retry failed apply=%s msg=%s" % (apply_id, result.get('message')))
        except Exception as e:
            print("[reconcile] error apply=%s err=%s" % (apply_id, e))
        db.session.expire_all()

    return processed, succeeded


def expire_stale_pending_orders():
    """把已过期仍 Pending 的 VIP 通道订单置为 Timeout。返回受影响行数。"""
    now = datetime.now()
    updated = ChargeApply.query.filter(
        ChargeApply.status == StatusLabelMap.Pending,
        ChargeApply.pay_channel.in_(CANCELABLE_CHANNELS),
        ChargeApply.expire_time < now,
    ).update({ChargeApply.status: StatusLabelMap.Timeout}, synchronize_session=False)
    if updated:
        db.session.commit()
    return updated


def main():
    with app.app_context():
        try:
            processed, succeeded = reconcile_stale_cancellations()
            timed_out = expire_stale_pending_orders()
            print("[reconcile] done at %s cancelling_processed=%s cancelling_succeeded=%s "
                  "pending_timed_out=%s" % (datetime.now().replace(microsecond=0),
                                            processed, succeeded, timed_out))
        except Exception as e:
            db.session.rollback()
            print("[reconcile] fatal error: %s" % e)
            sys.exit(1)


if __name__ == '__main__':
    main()
