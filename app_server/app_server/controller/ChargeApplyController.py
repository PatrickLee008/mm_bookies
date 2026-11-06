import time

import requests
from datetime import datetime, timedelta

from flask import g, request, jsonify, Blueprint
from sqlalchemy import or_, and_, func

from app_server import app, db, auth, Redis
from app_server.logger import get_logger
from app_server.model.AppAgentBankcard import AppAgentBankcard
from app_server.model.AppAgentModel import AppAgent
from app_server.model.AppMemberBankModel import AppMemberBank
from app_server.model.ChargeApplyModel import ChargeApply, StatusLabelMap
from app_server.model.SysBisDictModel import SysBisDict
from app_server.service.PayOrderService import pay_order_service
from app_server.utils import BankCodeMap
from app_server.utils.Kits import Kits

charge_apply = Blueprint('charge_apply', __name__)
logger = get_logger()

DEFAULT_ORDER_EXPIRE_MINUTES = 5

# 允许的通道（大小写严格）
VALID_CHANNELS = ('VIPPay', 'VIPPay_CashCode', 'TCPay', 'KingPay', 'MCPay', 'NFM2', 'NFM')
# 免卡通道：不传 CARD_ID，必须传 bank_type
NO_CARD_CHANNELS = ('VIPPay_CashCode', 'MCPay')
# 走服务商外部收银页的通道：即使返回了 receiveAccount 也要持久化 paymentUrl，
# 前端据此直接跳转，不弹二维码弹窗（TCPay 2026-11-04 按用户要求改）
EXTERNAL_PAY_PAGE_CHANNELS = ('TCPay', 'MCPay', 'KingPay')
# 仅这两个通道可取消代收（MCPay/PSP 无取消接口，TCPay/KingPay 不提供）
CANCELABLE_CHANNELS = ('VIPPay', 'VIPPay_CashCode')
# 需要用户提交「交易号后 5 位」的通道
TXN_LAST5_CHANNELS = ('MCPay', 'KingPay')

# 通道显示名
CHANNEL_TITLES = {
    'MCPay': 'MC Pay',
    'KingPay': 'King Pay',
    'VIPPay': 'VIP Pay',
    'VIPPay_CashCode': 'VIP Pay',
    'TCPay': 'TC Pay',
    'NFM2': 'Transfer',
    'NFM': 'Transfer',
}
# 同分时的展示顺序：VIPPay 系 > 扫码 > 免卡 > 转账
CHANNEL_SORT_ORDER = {
    'VIPPay_CashCode': 0, 'VIPPay': 0, 'TCPay': 1, 'KingPay': 1,
    'MCPay': 2, 'NFM2': 3, 'NFM': 4,
}


# ------------------------------------------------------------------
# 配置读取
# ------------------------------------------------------------------
def get_order_expire_minutes(tenant_id=None):
    """订单有效期（分钟）：读 sys_bis_dict 的 platformOrder.orderExpireMinutes，失败回退 5。"""
    try:
        cfg = SysBisDict.get_platform_order_config(tenant_id)
        if cfg and cfg.orderExpireMinutes:
            return max(1, int(cfg.orderExpireMinutes))
    except Exception as e:
        logger.error("读取充值订单过期时间配置失败: %s", e)
    return DEFAULT_ORDER_EXPIRE_MINUTES


def get_cancel_lease_seconds():
    """取消租约秒数：读 sys_bis_dict(payment.cancelLeaseSeconds)，失败回退 60。"""
    default = 60
    try:
        rows = SysBisDict.query.filter(
            SysBisDict.dict_dir == 'payment',
            SysBisDict.dict_code == 'cancelLeaseSeconds',
            SysBisDict.status == 1,
            SysBisDict.del_flag == 0,
        ).all()
        for row in rows:
            value = str(row.dict_value or '').strip()
            if value.isdigit() and int(value) > 0:
                return int(value)
    except Exception as e:
        logger.error("读取取消租约配置失败: %s", e)
    return default


# ------------------------------------------------------------------
# 取消租约（专用字段 cancel_lease_at，不复用 update_time）
# ------------------------------------------------------------------
def _claim_cancel_lease(apply, user_id, claim_time, lease_seconds):
    """抢占取消租约：Pending（或租约已过期的 Cancelling）原子置为 Cancelling。

    用「条件 UPDATE + 影响行数」判定，不做字段值比对。
    """
    query = ChargeApply.query.filter(
        ChargeApply.id == apply.id,
        ChargeApply.mb_id == user_id,
    )
    if apply.status == StatusLabelMap.Pending:
        query = query.filter(ChargeApply.status == StatusLabelMap.Pending)
    elif apply.status == StatusLabelMap.Cancelling:
        cutoff = claim_time - timedelta(seconds=lease_seconds)
        query = query.filter(
            ChargeApply.status == StatusLabelMap.Cancelling,
            or_(ChargeApply.cancel_lease_at.is_(None), ChargeApply.cancel_lease_at <= cutoff),
        )
    else:
        return False

    claimed = query.update({
        ChargeApply.status: StatusLabelMap.Cancelling,
        ChargeApply.cancel_lease_at: claim_time,
    }, synchronize_session=False)
    if claimed != 1:
        db.session.rollback()
        return False
    db.session.commit()
    return True


def _execute_cancel_attempt(apply_id, user_id, payment_order_id, claim_time):
    """在持有租约的前提下调用支付中心取消，并落地本地状态。"""
    gateway_cancelled = False
    try:
        result = pay_order_service.cancel_order(payment_order_id, order_type='pay')
        if not result.get('success'):
            if result.get('outcome_unknown'):
                # 网络异常：可能已受理，保留 Cancelling 租约等对账重试
                return result
            # 明确失败：回退 Pending，允许用户重试
            ChargeApply.query.filter(
                ChargeApply.id == apply_id,
                ChargeApply.mb_id == user_id,
                ChargeApply.status == StatusLabelMap.Cancelling,
                ChargeApply.cancel_lease_at == claim_time,
            ).update({
                ChargeApply.status: StatusLabelMap.Pending,
                ChargeApply.cancel_lease_at: None,
            }, synchronize_session=False)
            db.session.commit()
            return result

        gateway_cancelled = True
        completed = ChargeApply.query.filter(
            ChargeApply.id == apply_id,
            ChargeApply.mb_id == user_id,
            ChargeApply.status == StatusLabelMap.Cancelling,
            ChargeApply.cancel_lease_at == claim_time,
        ).update({
            ChargeApply.status: StatusLabelMap.Cancelled,
            ChargeApply.remark: 'Cancelled by user',
            ChargeApply.fail_reason: 'Cancelled by user',
        }, synchronize_session=False)
        if completed != 1:
            db.session.rollback()
            current = ChargeApply.query.filter_by(id=apply_id, mb_id=user_id).first()
            if current and current.status == StatusLabelMap.Cancelled:
                return result
            raise RuntimeError('Local order cancellation state conflict')
        db.session.commit()
        return result

    except Exception:
        db.session.rollback()
        try:
            recovery = ({
                ChargeApply.status: StatusLabelMap.Cancelled,
                ChargeApply.remark: 'Cancelled by user',
            } if gateway_cancelled else {
                ChargeApply.status: StatusLabelMap.Pending,
                ChargeApply.cancel_lease_at: None,
            })
            ChargeApply.query.filter(
                ChargeApply.id == apply_id,
                ChargeApply.mb_id == user_id,
                ChargeApply.status == StatusLabelMap.Cancelling,
                ChargeApply.cancel_lease_at == claim_time,
            ).update(recovery, synchronize_session=False)
            db.session.commit()
        except Exception:
            db.session.rollback()
            logger.error("取消状态回写失败 - 申请ID:%s", apply_id)
        raise


def reconcile_stale_cancellations(user_id):
    """补偿：扫描该用户租约已过期的 Cancelling 订单并重试取消。"""
    now = datetime.now()
    lease_seconds = get_cancel_lease_seconds()
    cutoff = now - timedelta(seconds=lease_seconds)
    stale = ChargeApply.query.filter(
        ChargeApply.mb_id == user_id,
        ChargeApply.status == StatusLabelMap.Cancelling,
        or_(ChargeApply.cancel_lease_at.is_(None), ChargeApply.cancel_lease_at <= cutoff),
    ).all()

    for apply in stale:
        apply_id = apply.id
        payment_order_id = apply.out_order_id
        claim_time = datetime.now().replace(microsecond=0)
        if not _claim_cancel_lease(apply, user_id, claim_time, lease_seconds):
            continue
        try:
            _execute_cancel_attempt(apply_id, user_id, payment_order_id, claim_time)
        except Exception as e:
            logger.error("遗留取消重试失败 - 申请ID:%s 错误:%s", apply_id, e)
        db.session.expire_all()


def mark_expired_orders(orders):
    """把列表里已过期的 Pending 订单置为 Timeout（批量 commit 一次）。"""
    now = datetime.now()
    changed = 0
    for apply in orders:
        if apply.status == StatusLabelMap.Pending and apply.expire_time and apply.expire_time < now:
            apply.status = StatusLabelMap.Timeout
            db.session.add(apply)
            changed += 1
    if changed:
        db.session.commit()
    return changed


# ------------------------------------------------------------------
# 下单
# ------------------------------------------------------------------
def _create_order_impl():
    args = request.get_json(silent=True) or {}
    user_id = g.user.id

    # 兼容老参数名（/add）与新参数名（POST ''）
    paychannel = args.get('paychannel') or args.get('pay_channel') or app.config.get('PAY_CHANNEL_TYPE')
    card_id = args.get('CARD_ID') or args.get('card_id')
    bank_type = args.get('bank_type')
    amount = args.get('amount') or args.get('money')
    phone = args.get('phone') or args.get('acc_number')
    subject = args.get('subject')
    memo = args.get('memo')
    is_h5 = bool(args.get('is_h5'))
    acc_name = args.get('acc_name')
    acc_number = args.get('acc_number')

    if not paychannel:
        return jsonify({'code': 50002, 'message': 'paychannel cannot be null'})
    if paychannel not in VALID_CHANNELS:
        return jsonify({'code': 50002, 'message': 'Unsupported payment channel'})

    no_card = paychannel in NO_CARD_CHANNELS

    try:
        # 1) 防并发
        getter_key = "charge_%s" % user_id
        if not Redis.set(getter_key, 1, nx=True, ex=10):
            return jsonify({'code': 50003, 'message': 'charge in very short time'})

        # 2) 补偿遗留 Cancelling
        reconcile_stale_cancellations(user_id)

        # 3) 选卡规则
        if not no_card and not card_id:
            return jsonify({'code': 50002, 'message': 'bankcard info is required.'})
        if no_card and not bank_type:
            return jsonify({'code': 50002, 'message': 'bank_type is required for %s.' % paychannel})

        # 4) 金额（整数 MMK）
        if amount is None or isinstance(amount, bool):
            return jsonify({'code': 50002, 'message': 'amount cannot be null'})
        try:
            amount = int(amount)
        except (TypeError, ValueError):
            return jsonify({'code': 50002, 'message': 'amount must be an integer'})
        if amount <= 0 or amount > 10000000:
            return jsonify({'code': 50002, 'message': 'Deposit amount must be between 1 and 10,000,000 MMK'})

        if not phone and not no_card:
            return jsonify({'code': 50002, 'message': 'phone cannot be null'})

        # 5) 未完成订单（处理中且未过期，或取消中）
        unfinished = ChargeApply.query.filter(
            ChargeApply.mb_id == user_id,
            or_(
                and_(ChargeApply.status.in_((StatusLabelMap.New, StatusLabelMap.Pending)),
                     ChargeApply.expire_time > datetime.now()),
                ChargeApply.status == StatusLabelMap.Cancelling,
            ),
        ).order_by(ChargeApply.create_time.desc()).first()
        if unfinished:
            return jsonify({'code': 50005,
                            'message': 'you have unfinished apply order.',
                            'unfinished_apply': unfinished.to_dict()})

        # 6) 用户卡（校验归属）
        bank_card = None
        if not no_card:
            bank_card = AppMemberBank.query.filter(
                AppMemberBank.id == card_id,
                AppMemberBank.mb_id == user_id,
                AppMemberBank.del_flag == 0,
            ).first()
            if not bank_card:
                return jsonify({'code': 50002, 'message': 'this card not exits.'})

        # 7) 银行与通道匹配（归一成库内标准值）
        selected_bank_local = BankCodeMap.normalize(bank_type if no_card else bank_card.bank_code)
        if not BankCodeMap.supported_by(paychannel, selected_bank_local):
            return jsonify({'code': 50002, 'message': 'Bank is not supported by this payment channel'})

        agent_id = g.user.aid or ""
        if not agent_id:
            return jsonify({'code': 50001, 'message': 'No agent id'})
        agent = AppAgent.query.filter(AppAgent.id == agent_id).first()
        if not agent or agent.auto_deposit != 1:
            return jsonify({'code': 50002, 'message': 'Your agent has not enabled the automatic deposit'})

        # 8) 可用收款卡（数据驱动：m_app_agent_bankcard）
        card_query = AppAgentBankcard.query.filter(
            AppAgentBankcard.status == 1,
            AppAgentBankcard.del_flag == 0,
            AppAgentBankcard.aid == agent_id,
            AppAgentBankcard.channel_type == paychannel,
            or_(AppAgentBankcard.type.is_(None), AppAgentBankcard.type.in_(['All', 'Deposit'])),
        )
        if paychannel != 'MCPay':
            # MCPay 免卡、银行由用户选择；其余通道要求存在对应银行的可用卡
            card_query = card_query.filter(AppAgentBankcard.rc_bank_code == selected_bank_local)
        available_cards = card_query.all()
        if not available_cards:
            logger.warning("无可用收款账号 - 用户:%s 代理:%s 通道:%s 银行:%s",
                           user_id, agent_id, paychannel, selected_bank_local)
            return jsonify({'code': 40404,
                            'message': 'There is no available payment account at present. '
                                       'Please contact the customer service.'})

        # 9) 按通道确定收款信息
        cash_code = ""
        if paychannel == 'NFM2':
            selected_card = available_cards[0]
            payment_type_local = BankCodeMap.normalize(selected_card.rc_bank_code)
            receive_account = selected_card.rc_bank_account or ""
            receive_account_name = selected_card.rc_bank_username or ""
        elif paychannel == 'VIPPay_CashCode':
            payment_type_local = selected_bank_local
            receive_account = ""
            receive_account_name = ""
            cash_code = str(getattr(g.user, 'cash_code', '') or "").strip()
            if not cash_code:
                cash_code = g.user.generate_new_cash_code()
                g.user.cash_code = cash_code
                db.session.commit()
        else:
            payment_type_local = selected_bank_local
            receive_account = ""
            receive_account_name = ""

        # 10) 付款人信息（CashCode 不能用昵称/手机号顶替，会被网关拒绝）
        if bank_card:
            payer_real_name = bank_card.acc_name or ""
            payer_phone = bank_card.acc_number or ""
        elif paychannel == 'VIPPay_CashCode':
            payer_real_name = ""
            payer_phone = ""
        else:
            payer_real_name = acc_name or g.user.name or ""
            payer_phone = phone or acc_number or user_id or ""

        # 11) 落本地单
        apply_id = Kits.generate_uuid()
        expire_minutes = get_order_expire_minutes(getattr(g.user, 'tenant_id', None))
        apply = ChargeApply(
            id=apply_id,
            aid=agent_id,
            mb_id=user_id,
            mb_nickname=g.user.name,
            mb_username=g.user.username,
            mb_bank_code=payment_type_local,
            mb_acc_name=payer_real_name,
            mb_acc_number=payer_phone,
            remark=subject or ('Deposit - ' + payment_type_local),
            charge_way=0,
            money=amount,
            original_amount=amount,
            status=StatusLabelMap.New,
            pay_channel=paychannel,
            receive_bank_code=payment_type_local,
            receive_account=receive_account,
            receive_account_name=receive_account_name,
            expire_time=datetime.now() + timedelta(minutes=expire_minutes),
        )
        db.session.add(apply)
        db.session.commit()
        logger.info("充值申请创建 - 申请ID:%s 用户:%s 通道:%s 银行:%s 金额:%s 过期:%s分钟",
                    apply_id, user_id, paychannel, payment_type_local, amount, expire_minutes)

        # 12) 调支付中心（银行代码转支付中心取值）
        result = pay_order_service.create_recharge_order(
            agent_id=agent_id,
            user_id=g.user.username,
            amount=amount,
            out_trade_no=apply_id,
            subject=subject or ('Deposit - ' + payment_type_local),
            memo=memo or ('from ' + payment_type_local),
            bank_code=BankCodeMap.to_pay_center(payment_type_local),
            realname=payer_real_name,
            phone=payer_phone,
            payment_type=BankCodeMap.to_pay_center(payment_type_local),
            receive_account=receive_account,
            receive_account_name=receive_account_name,
            channelType=paychannel,
            cash_code=cash_code,
            order_expire_minutes=expire_minutes,
            return_url=(app.config.get('CHARGE_RETURN_URL', '') or '') if is_h5 else '',
        )

        # 13) 释放快照后加行锁重读，避免覆盖先到的回调
        db.session.rollback()
        apply = ChargeApply.query.filter_by(id=apply_id).with_for_update().one()

        resp_data = result.get('data') or {}
        if resp_data:
            apply.out_trade_no = resp_data.get('tradeNo') or apply.out_trade_no or ''
            apply.out_order_id = resp_data.get('tradeOrderId') or apply.out_order_id
            # 服务商托管页通道：保留 paymentUrl 供前端直接跳转。
            # TCPay 同时返回 receiveAccount 和 paymentUrl，但它走的是外部收银页，
            # 不能再按"有收款账号=内嵌收银台"来丢弃链接。
            if resp_data.get('paymentUrl') and (
                    not resp_data.get('receiveAccount') or paychannel in EXTERNAL_PAY_PAGE_CHANNELS):
                apply.pay_url = resp_data.get('paymentUrl')
            if resp_data.get('receiveAccount'):
                apply.receive_account = resp_data.get('receiveAccount')
            if resp_data.get('receiveAccountName'):
                apply.receive_account_name = resp_data.get('receiveAccountName')

        # 回调可能已经先到：仅在仍是 New 且未上分时推进状态
        if apply.status == StatusLabelMap.New and not apply.recharge_id:
            apply.status = StatusLabelMap.Pending if result.get('success') else StatusLabelMap.Failed
            if not result.get('success'):
                apply.fail_reason = (result.get('message') or '')[:250]
        db.session.commit()

        if not result.get('success') and apply.status == StatusLabelMap.Failed:
            return jsonify({'code': 50004, 'message': result.get('message')})

        # 二维码/收银台地址不落库（有时效），随下单响应直接返回给前端弹窗
        data = apply.to_dict()
        data['QRCODE'] = resp_data.get('qrcode') or ''
        data['PAYMENT_URL'] = resp_data.get('paymentUrl') or ''
        data['PAY_TIMEOUT'] = resp_data.get('payTimeout') or ''

        return jsonify({'code': 20000,
                        'message': 'Order created successfully.',
                        'data': data})

    except Exception as e:
        db.session.rollback()
        logger.error("下单异常 - 用户:%s 通道:%s 错误:%s", user_id, paychannel, e, exc_info=True)
    return jsonify({'code': 50001, 'message': 'unknown error.'})


@charge_apply.route('', methods=['POST'])
@auth.login_required
def create_order():
    return _create_order_impl()


@charge_apply.route('/add', methods=['POST'])
@auth.login_required
def add_apply():
    """老路径，保留下单能力（前端改造完成前继续可用）。"""
    return _create_order_impl()


@charge_apply.route('/unfinished', methods=['GET'])
@auth.login_required
def get_unfinished_apply():
    """查询当前会员是否有未完成的充值单。

    充值页进入时调用：有未完成单就直接弹"继续/取消"，避免用户填完金额
    点 Continue 才被 50005 拦截（那种体验像"点了没反应"）。
    判定口径与下单时的 5) 未完成订单一致。
    """
    user_id = g.user.id
    apply = ChargeApply.query.filter(
        ChargeApply.mb_id == user_id,
        or_(
            and_(ChargeApply.status.in_((StatusLabelMap.New, StatusLabelMap.Pending)),
                 ChargeApply.expire_time > datetime.now()),
            ChargeApply.status == StatusLabelMap.Cancelling,
        ),
    ).order_by(ChargeApply.create_time.desc()).first()
    if not apply:
        return jsonify({'code': 20000, 'data': None})
    return jsonify({'code': 20000, 'data': apply.to_dict()})


# ------------------------------------------------------------------
# 状态 / 取消 / 交易号
# ------------------------------------------------------------------
@charge_apply.route('/status', methods=['POST', 'GET'])
@auth.login_required
def get_apply_status():
    args = request.get_json(silent=True) or {}
    order_id = args.get('id') or args.get('order_id') or request.args.get('id')
    if not order_id:
        return jsonify({'code': 50002, 'message': 'id cannot be null'})

    try:
        apply = ChargeApply.query.filter(
            ChargeApply.mb_id == g.user.id,
            or_(ChargeApply.id == str(order_id), ChargeApply.out_order_id == str(order_id)),
        ).first()
        if not apply:
            return jsonify({'code': 50004, 'message': 'order not found'})

        if (apply.status == StatusLabelMap.Pending and apply.expire_time
                and apply.expire_time < datetime.now()):
            apply.status = StatusLabelMap.Timeout
            db.session.commit()

        return jsonify({'code': 20000,
                        'status': apply.status,
                        'remaining_seconds': apply.remaining_seconds(),
                        'txn_last5': apply.txn_last5 or ''})
    except Exception as e:
        logger.error("查询订单状态异常 - 单号:%s 错误:%s", order_id, e, exc_info=True)
        return jsonify({'code': 50001, 'message': 'unknown error.'})


@charge_apply.route('/cancel', methods=['POST'])
@auth.login_required
def cancel_apply():
    args = request.get_json(silent=True) or {}
    order_id = args.get('order_id') or args.get('orderId')
    if not order_id:
        return jsonify({'code': 400, 'ok': False, 'message': 'order_id is required'})

    try:
        apply = ChargeApply.query.filter(
            ChargeApply.mb_id == g.user.id,
            or_(ChargeApply.id == str(order_id), ChargeApply.out_order_id == str(order_id)),
        ).first()
        if not apply:
            return jsonify({'code': 404, 'ok': False, 'message': 'Order not found'})
        if apply.pay_channel not in CANCELABLE_CHANNELS:
            return jsonify({'code': 400, 'ok': False,
                            'message': 'Cancel is only supported for VIPPay orders'})
        if apply.status == StatusLabelMap.Cancelled:
            return jsonify({'code': 20000, 'data': {'order_id': apply.id, 'status': apply.status}})
        if apply.status not in (StatusLabelMap.Pending, StatusLabelMap.Cancelling):
            return jsonify({'code': 409, 'ok': False, 'message': 'Order is no longer processing'})
        if not apply.out_order_id:
            return jsonify({'code': 409, 'ok': False, 'message': 'Payment center order ID is missing'})

        claim_time = datetime.now().replace(microsecond=0)
        lease_seconds = get_cancel_lease_seconds()
        if not _claim_cancel_lease(apply, g.user.id, claim_time, lease_seconds):
            current = ChargeApply.query.filter_by(id=apply.id, mb_id=g.user.id).first()
            if current and current.status == StatusLabelMap.Cancelled:
                return jsonify({'code': 20000, 'data': {'order_id': current.id, 'status': current.status}})
            return jsonify({'code': 409, 'ok': False, 'message': 'Cancel is being processed, please wait'})

        result = _execute_cancel_attempt(apply.id, g.user.id, apply.out_order_id, claim_time)
        if result.get('success'):
            return jsonify({'code': 20000, 'data': {'order_id': apply.out_order_id,
                                                    'status': StatusLabelMap.Cancelled}})
        if result.get('outcome_unknown'):
            return jsonify({'code': 50003, 'ok': False,
                            'message': 'Cancel result is unknown, please check the record later'})
        return jsonify({'code': 50002, 'ok': False,
                        'message': result.get('message') or 'Cancel rejected'})
    except Exception as e:
        logger.error("取消订单异常 - 单号:%s 错误:%s", order_id, e, exc_info=True)
        return jsonify({'code': 50001, 'ok': False, 'message': 'unknown error.'})


@charge_apply.route('/submit_txn', methods=['POST'])
@auth.login_required
def submit_txn():
    """MCPay / KingPay：提交交易号后 5 位。

    只落库，不改变订单状态、不直接上分；入账仍以支付中心回调为准。
    """
    args = request.get_json(silent=True) or {}
    order_id = args.get('id') or args.get('order_id')
    txn_last5 = str(args.get('txn_last5') or '').strip().replace(' ', '')

    if not order_id:
        return jsonify({'code': 50002, 'message': 'id cannot be null'})
    if not txn_last5.isdigit() or len(txn_last5) != 5:
        return jsonify({'code': 50002, 'message': 'Please enter the last 5 digits of the transaction ID'})

    try:
        apply = ChargeApply.query.filter(
            ChargeApply.mb_id == g.user.id,
            or_(ChargeApply.id == str(order_id), ChargeApply.out_order_id == str(order_id)),
        ).first()
        if not apply:
            return jsonify({'code': 50004, 'message': 'order not found'})
        if apply.pay_channel not in TXN_LAST5_CHANNELS:
            return jsonify({'code': 50002, 'message': 'This channel does not require a transaction ID'})
        if apply.status in (StatusLabelMap.Cancelled, StatusLabelMap.Failed,
                            StatusLabelMap.Timeout, StatusLabelMap.Success):
            return jsonify({'code': 409, 'message': 'The order is already closed, please create a new one'})

        apply.txn_last5 = txn_last5
        apply.txn_submit_time = datetime.now()
        db.session.commit()
        logger.info("提交交易号后5位 - 申请ID:%s 后5位:%s", apply.id, txn_last5)

        return jsonify({'code': 20000, 'message': 'Submitted, waiting for confirmation',
                        'data': {'txn_last5': txn_last5}})
    except Exception as e:
        db.session.rollback()
        logger.error("提交交易号异常 - 单号:%s 错误:%s", order_id, e, exc_info=True)
        return jsonify({'code': 50001, 'message': 'unknown error.'})


@charge_apply.route('/payinfo', methods=['POST'])
@auth.login_required
def get_payinfo():
    """服务端代理查单：返回二维码/收款信息/剩余时间。

    前端不直连支付中心（地址与后端 PAY_CENTER_API 保持一致，也避免跨域）。
    用于「继续付款」——历史订单没有落库二维码时补取。
    """
    args = request.get_json(silent=True) or {}
    order_id = args.get('id') or args.get('order_id')
    if not order_id:
        return jsonify({'code': 50002, 'message': 'id cannot be null'})

    try:
        apply = ChargeApply.query.filter(
            ChargeApply.mb_id == g.user.id,
            or_(ChargeApply.id == str(order_id), ChargeApply.out_order_id == str(order_id)),
        ).first()
        if not apply:
            return jsonify({'code': 50004, 'message': 'order not found'})

        trade_order_id = apply.out_order_id or apply.id
        url = app.config.get('PAY_CENTER_API', '') + '/pay/order/payment'
        resp = requests.post(url, json={'id': trade_order_id}, timeout=(5, 20))
        payload = resp.json()
        data = payload.get('data') or {}
        if not payload.get('ok') or not data:
            return jsonify({'code': 50004, 'message': payload.get('msg') or 'payinfo not found'})

        # 注意：orderStatus=2 并不代表已支付（TCPay 待支付时也返回 2），
        # 真正的成功标志是 success=true；paymentUrl 是 TCPay 的收银页地址。
        return jsonify({'code': 20000, 'data': {
            'qrcode': data.get('qrcode') or '',
            'receive_account': data.get('receiveAccount') or '',
            'receive_account_name': data.get('receiveAccountName') or '',
            'order_status': data.get('orderStatus'),
            'success': bool(data.get('success')),
            'payment_url': data.get('paymentUrl') or '',
            'timeout': int(data.get('timeout') or 0),
            'pay_timeout': data.get('payTimeout') or '',
            'cur_type': data.get('curType') or '',
        }})
    except Exception as e:
        logger.error("查单异常 - 单号:%s 错误:%s", order_id, e, exc_info=True)
        return jsonify({'code': 50001, 'message': 'Payment service is temporarily unavailable.'})


@charge_apply.route('/processing', methods=['GET'])
@auth.login_required
def get_processing():
    order = ChargeApply.query.filter(
        ChargeApply.mb_id == g.user.id,
        ChargeApply.status == StatusLabelMap.Pending,
        ChargeApply.expire_time > datetime.now(),
    ).first()
    if order:
        return jsonify({'code': 20000, 'data': order.to_dict()})
    return jsonify({'code': 50000, 'message': 'no processing apply order.'})


# ------------------------------------------------------------------
# 通道与银行（数据驱动：m_app_agent_bankcard）
# ------------------------------------------------------------------
@charge_apply.route('/channels', methods=['POST'])
@auth.login_required
def get_channels():
    """返回当前代理下已启用的通道，按 score 降序；bank_codes 为库内显示名。"""
    args = request.get_json(silent=True) or {}
    bank_code = args.get('bank_code')
    requested_channel = args.get('channel')
    if not bank_code:
        return jsonify({'code': 50002, 'message': 'bank_code cannot be null'})

    try:
        agent_id = g.user.aid or ""
        query = db.session.query(
            AppAgentBankcard.channel_type,
            AppAgentBankcard.rc_bank_code,
            AppAgentBankcard.SCORE,
            AppAgentBankcard.VIDEO_URL,
        ).filter(
            AppAgentBankcard.status == 1,
            AppAgentBankcard.del_flag == 0,
            AppAgentBankcard.aid == agent_id,
            or_(AppAgentBankcard.type.is_(None), AppAgentBankcard.type != 'Withdraw'),
            AppAgentBankcard.channel_type.isnot(None),
        )
        if bank_code != 'All':
            query = query.filter(AppAgentBankcard.rc_bank_code == BankCodeMap.normalize(bank_code))
        if requested_channel:
            query = query.filter(AppAgentBankcard.channel_type == requested_channel)

        rows = query.distinct().all()

        banks = {}
        scores = {}
        videos = {}
        for channel_code, wallet_code, score, video_url in rows:
            if channel_code not in VALID_CHANNELS:
                continue
            if not BankCodeMap.supported_by(channel_code, wallet_code):
                continue
            local_bank = BankCodeMap.normalize(wallet_code)
            banks.setdefault(channel_code, [])
            if local_bank and local_bank not in banks[channel_code]:
                banks[channel_code].append(local_bank)
            score = int(score or 0)
            scores[channel_code] = max(scores.get(channel_code, score), score)
            if video_url and (channel_code not in videos or score > videos[channel_code][0]):
                videos[channel_code] = (score, video_url)

        result = []
        for code in scores:
            result.append({
                'title': CHANNEL_TITLES.get(code, code),
                'code': code,
                'bank_codes': banks.get(code, []),
                'score': scores.get(code, 0),
                'video_url': videos.get(code, (0, ''))[1],
                'no_card': code in NO_CARD_CHANNELS,
                'need_txn_last5': code in TXN_LAST5_CHANNELS,
                'cancelable': code in CANCELABLE_CHANNELS,
            })
        result.sort(key=lambda x: (-x['score'], CHANNEL_SORT_ORDER.get(x['code'], 9)))
        return jsonify({'code': 20000, 'data': result})

    except Exception as e:
        logger.error("查询通道异常 - 错误:%s", e, exc_info=True)
        return jsonify({'code': 50001, 'message': 'unknown error.'})


@charge_apply.route('/cashcode_banks', methods=['GET'])
@auth.login_required
def get_cashcode_banks():
    """VIPPay_CashCode 可用的钱包类型 + 当前用户现金码。"""
    try:
        rows = db.session.query(AppAgentBankcard.rc_bank_code).filter(
            AppAgentBankcard.status == 1,
            AppAgentBankcard.del_flag == 0,
            AppAgentBankcard.aid == (g.user.aid or ""),
            AppAgentBankcard.channel_type == 'VIPPay_CashCode',
            or_(AppAgentBankcard.type.is_(None), AppAgentBankcard.type.in_(['All', 'Deposit'])),
            AppAgentBankcard.rc_bank_code.isnot(None),
        ).distinct().all()
        banks = []
        for (code,) in rows:
            local = BankCodeMap.normalize(code)
            if local and local not in banks and BankCodeMap.is_wallet(local):
                banks.append(local)
        return jsonify({'code': 20000, 'data': banks, 'cash_code': str(getattr(g.user, 'cash_code', '') or '')})
    except Exception as e:
        logger.error("查询现金码银行异常 - 错误:%s", e, exc_info=True)
        return jsonify({'code': 50001, 'message': 'unknown error.'})


# ------------------------------------------------------------------
# 记录（列表）
# ------------------------------------------------------------------
@charge_apply.route('/get', methods=['GET'])
@auth.login_required
def get_apply_list():
    # 惰性过期：没有定时任务，这里在查询前把「已过 expire_time 但仍是 Pending」的单置为 Timeout，
    # 否则列表里会一直显示可继续支付的订单（弹窗倒计时归零也不消失）。
    try:
        expired = ChargeApply.query.filter(
            ChargeApply.mb_id == g.user.id,
            ChargeApply.status == 'Pending',
            ChargeApply.expire_time.isnot(None),
            ChargeApply.expire_time < datetime.now(),
        ).update({'status': 'Timeout'}, synchronize_session=False)
        if expired:
            db.session.commit()
            logger.info("惰性过期充值单 - 用户:%s 数量:%s", g.user.id, expired)
    except Exception as e:
        db.session.rollback()
        logger.error("惰性过期处理失败: %s", e)

    current_page = request.args.get('page', type=int, default=1)
    limit = request.args.get('limit', type=int, default=20)
    key_word = request.args.get('key_word')
    start_time = request.args.get('start_time')
    end_time = request.args.get('end_time')
    statuses = request.args.getlist('statuses')
    pay_channels = request.args.getlist('pay_channels')

    charge_list = ChargeApply.query.filter(
        ChargeApply.mb_id == g.user.id,
        ChargeApply.del_flag == 0,
    )

    if key_word:
        pattern = '%' + key_word + '%'
        charge_list = charge_list.filter(
            or_(ChargeApply.mb_id.like(pattern),
                ChargeApply.mb_nickname.like(pattern),
                ChargeApply.remark.like(pattern)))
    if start_time:
        charge_list = charge_list.filter(ChargeApply.create_time >= start_time + ' 00:00:00')
    if end_time:
        charge_list = charge_list.filter(ChargeApply.create_time <= end_time + ' 23:59:59')
    if statuses:
        charge_list = charge_list.filter(ChargeApply.status.in_(statuses))
    else:
        # 默认不展示 Failed / Rejected；Timeout 保留（用户要看超时单）
        charge_list = charge_list.filter(
            ChargeApply.status.notin_((StatusLabelMap.Failed, StatusLabelMap.Rejected)))
    if pay_channels:
        charge_list = charge_list.filter(ChargeApply.pay_channel.in_(pay_channels))

    total_amount = charge_list.with_entities(func.sum(ChargeApply.money)).scalar() or 0
    charge_list = charge_list.offset((current_page - 1) * limit).limit(limit).all()

    mark_expired_orders(charge_list)

    return jsonify({
        'items': [u.to_dict() for u in charge_list],
        'total': len(charge_list),
        'total_amount': float(total_amount),
    })


# ------------------------------------------------------------------
# 编辑 / 删除（保留）
# ------------------------------------------------------------------
@charge_apply.route('/edit', methods=['POST'])
@auth.login_required
def edit_apply():
    args = request.get_json(silent=True) or {}
    apply_id = args.get('APPLY_ID') or args.get('id')
    if not apply_id:
        return jsonify({'code': 50002, 'message': 'APPLY_ID cannot be null'})
    try:
        apply = ChargeApply.query.filter_by(id=apply_id, mb_id=g.user.id).one_or_none()
        if not apply:
            return jsonify({'code': 50004, 'message': 'order not found'})
        if apply.status not in (StatusLabelMap.New, StatusLabelMap.Pending):
            return jsonify({'code': 409, 'message': 'order can not be edited'})
        if args.get('REMARK'):
            apply.remark = args.get('REMARK')
        db.session.commit()
        return jsonify({'code': 200, 'message': 'add successful.'})
    except Exception as e:
        db.session.rollback()
        logger.error("修改充值申请失败 - 用户:%s 错误:%s", g.user.id, e, exc_info=True)
        return jsonify({'code': 50001, 'message': 'unknown error.'})


@charge_apply.route('/delete', methods=['POST'])
@auth.login_required
def delete_apply():
    args = request.get_json(silent=True) or {}
    apply_id = args.get('APPLY_ID') or args.get('id')
    if not apply_id:
        return jsonify({'code': 50002, 'message': 'APPLY_ID cannot be null'})
    try:
        apply = ChargeApply.query.filter_by(id=apply_id, mb_id=g.user.id).one_or_none()
        if not apply:
            return jsonify({'code': 50004, 'message': 'order not found'})
        # 软删除，保留对账数据
        apply.del_flag = 1
        db.session.commit()
        return jsonify({'code': 200, 'message': 'delete successful.'})
    except Exception as e:
        db.session.rollback()
        logger.error("删除充值申请失败 - 用户:%s 错误:%s", g.user.id, e, exc_info=True)
        return jsonify({'code': 50001, 'message': 'unknown error.'})
