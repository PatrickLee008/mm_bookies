import requests
import traceback
from app_server import app
from app_server.logger import get_logger
from app_server.model.ChargeApplyModel import ChargeApply
from app_server.utils.Kits import Kits

logger = get_logger()

# 支付中心异常对外统一话术（不把内部地址/堆栈抛给玩家）
MSG_UNAVAILABLE = 'Payment service is temporarily unavailable. Please try again later.'
MSG_BUSY = 'Payment service is busy, please try again later.'
MSG_BAD_RESPONSE = 'Payment service returned an invalid response. Please try again later.'
MSG_FAILED = 'Failed to create order, please try again later.'


def pay_center_error_message(error):
    """把 requests/解析异常翻译成对玩家友好的文案，原文只进日志。"""
    text = str(error) or ''
    lowered = text.lower()
    if any(k in lowered for k in ('connection refused', 'failed to establish', 'max retries',
                                  'connection aborted', 'connection reset', 'newconnectionerror')):
        return MSG_UNAVAILABLE
    if 'timeout' in lowered or 'timed out' in lowered:
        return MSG_BUSY
    if any(k in lowered for k in ('json', 'expecting value', 'decode')):
        return MSG_BAD_RESPONSE
    return MSG_FAILED


class PayOrderService:
    """充值订单服务（对接支付中心 /pay/openapi/*）"""

    def __init__(self):
        self.pay_center_api = app.config.get('PAY_CENTER_API', '')
        self.pay_create_url = self.pay_center_api + '/pay/openapi/paycreate'
        self.pay_cancel_url = self.pay_center_api + '/pay/openapi/ordercancel'
        self.pay_channels_url = self.pay_center_api + '/pay/openapi/channels'
        self.callback_url = app.config.get('CHARGE_CALLBACK_URL', '')
        self.app_id = app.config.get('PAY_CENTER_APP_ID', '')
        self.aes_secret = app.config.get('PAY_CENTER_APP_AES_SECRET', '')
        # 联调用：临时覆盖 agentId（支付中心按 appid 配置代理白名单，
        # 借用他项目 appid 时本项目 aid 不在白名单，可用此项指定一个已登记的值）
        # None = 未配置，使用用户实际 aid；'' = 显式置空（联调跳过代理映射校验）；其它 = 覆盖值

    def create_recharge_order(self, user_id, agent_id, amount, out_trade_no, subject="充值", memo="充值",
                              realname="", bank_code="KBZ", phone="", payment_type="KBZ",
                              receive_account="", receive_account_name="", client_ip="127.0.0.1",
                              channelType=None, nFM2PayCenter=False, cash_code="",
                              order_expire_minutes=None, return_url=""):
        """创建充值订单。

        注意：payment_type / bank_code 必须是「支付中心取值」，调用方先用 BankCodeMap 转换。
        """
        try:
            if channelType is None:
                channelType = app.config.get('PAY_CHANNEL_TYPE', 'VIPPay')

            # NFM2 默认不走支付中心（遗留链路）
            if channelType == "NFM2" and not nFM2PayCenter:
                return {'success': True,
                        'data': {'tradeNo': out_trade_no, 'tradeOrderId': out_trade_no}}

            params = {
                "orderType": "recharge",
                "outTradeNo": out_trade_no,
                "userId": str(user_id),
                "agentId": agent_id,
                "subject": subject,
                "amount": float(amount),
                "memo": memo,
                "realname": realname,
                "bankCode": bank_code,
                "phone": phone,
                "paymentType": payment_type,
                "receiveAccount": receive_account,
                "receiveAccountName": receive_account_name,
                "clientIp": client_ip,
                "callbackUrl": self.callback_url,
                "channelType": channelType,
            }
            if cash_code:
                params["cashCode"] = cash_code
            if order_expire_minutes:
                params["orderExpireMinutes"] = int(order_expire_minutes)
            if return_url:
                params["returnUrl"] = return_url

            logger.info("创建充值订单请求 - 用户:%s 单号:%s 金额:%s 银行:%s 支付方式:%s 通道:%s",
                        user_id, out_trade_no, amount, bank_code, payment_type, channelType)

            headers = {'Content-Type': 'text/plain', 'appid': self.app_id}
            plain_text = Kits.encrypt(Kits.json_dumps(params), self.aes_secret)
            # 只设连接超时：避免支付中心已建单、本地却判失败
            response = requests.post(self.pay_create_url, data=plain_text, headers=headers, timeout=(5, None))
            resp_json = response.json()
            logger.info("充值订单响应 - 单号:%s 响应:%s", out_trade_no, resp_json)

            data = resp_json.get('data') or {}
            if resp_json.get('code') == "OK" and resp_json.get('ok') and data.get('success'):
                return {'success': True, 'data': data, 'message': 'Recharge order created successfully'}

            return {'success': False, 'data': None,
                    'message': resp_json.get('msg') or 'Failed to create recharge order',
                    'error': resp_json}

        except Exception as e:
            logger.error("创建充值订单异常 - 单号:%s 错误:%s\n%s", out_trade_no, e, traceback.format_exc())
            return {'success': False, 'data': None, 'message': pay_center_error_message(e)}

    def cancel_order(self, order_id, order_type='pay'):
        """取消支付中心订单（代收 order_type='pay'，代付 'payout'）。

        返回：
            {'success': True, ...}
            {'success': False, 'outcome_unknown': True}  → 网络异常，结果未知，调用方应保留租约
            {'success': False}                            → 支付中心明确拒绝
        """
        if not order_id:
            return {'success': False, 'message': 'Payment center order id is missing'}

        try:
            params = {'orderId': str(order_id), 'orderType': order_type}
            headers = {'Content-Type': 'text/plain', 'appid': self.app_id}
            plain_text = Kits.encrypt(Kits.json_dumps(params), self.aes_secret)
            response = requests.post(self.pay_cancel_url, data=plain_text, headers=headers, timeout=(5, 20))
            resp_json = response.json()
            logger.info("取消订单响应 - 订单:%s 类型:%s 响应:%s", order_id, order_type, resp_json)

            if resp_json.get('ok') and resp_json.get('code') == "OK":
                return {'success': True, 'data': resp_json.get('data'), 'message': 'cancelled'}
            return {'success': False,
                    'message': resp_json.get('msg') or 'Cancel rejected by payment center',
                    'error': resp_json}

        except Exception as e:
            logger.error("取消订单异常 - 订单:%s 错误:%s\n%s", order_id, e, traceback.format_exc())
            return {'success': False, 'outcome_unknown': True, 'message': pay_center_error_message(e)}

    def get_recharge_order_status(self, out_trade_no):
        """查询本地充值订单状态（不请求支付中心）。"""
        try:
            charge_apply = ChargeApply.query.filter(ChargeApply.id == out_trade_no).first()
            if not charge_apply:
                return {'success': False, 'message': 'Order not found'}
            return {'success': True, 'data': charge_apply.to_dict()}
        except Exception as e:
            logger.error("查询充值订单状态异常 - 单号:%s 错误:%s", out_trade_no, e, exc_info=True)
            return {'success': False, 'message': pay_center_error_message(e)}

    def get_pay_channels(self, channel_type=None, status=None, wallet_provider=None, page=None, limit=None):
        """查询支付中心通道状态（运维用，业务通道列表走 /charge_apply/channels）。"""
        try:
            params = {}
            if channel_type:
                params['channelType'] = channel_type
            if status:
                params['status'] = status
            if wallet_provider:
                params['walletProvider'] = wallet_provider
            if page is not None:
                params['page'] = page
            if limit is not None:
                params['limit'] = limit

            headers = {'Content-Type': 'text/plain', 'appid': self.app_id}
            encrypted_body = Kits.encrypt(Kits.json_dumps(params), self.aes_secret)
            response = requests.post(self.pay_channels_url, data=encrypted_body, headers=headers, timeout=(5, 20))
            resp_json = response.json()
            if resp_json.get('code') == 'OK' and resp_json.get('ok'):
                return {'success': True, 'data': resp_json.get('data') or [], 'message': 'success'}
            return {'success': False, 'data': [],
                    'message': resp_json.get('msg') or 'Failed to query pay channels',
                    'error': resp_json}
        except Exception as e:
            logger.error("查询支付通道异常 - 错误:%s", e, exc_info=True)
            return {'success': False, 'data': [], 'message': pay_center_error_message(e)}


pay_order_service = PayOrderService()
