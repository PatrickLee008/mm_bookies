import requests
import traceback
from datetime import datetime
from app_server import app, db
from app_server.logger import get_logger
from app_server.model.ChargeApplyModel import ChargeApply
from app_server.utils.Kits import Kits

logger = get_logger()


class PayOrderService:
    """充值订单服务"""

    def __init__(self):
        self.pay_center_api = app.config.get('PAY_CENTER_API', '')
        self.pay_create_url = self.pay_center_api + '/pay/openapi/paycreate'
        self.pay_channels_url = self.pay_center_api + '/pay/openapi/channels'
        self.callback_url = app.config.get('CHARGE_CALLBACK_URL', '')
        self.app_id = app.config.get('PAY_CENTER_APP_ID', '')
        self.aes_secret = app.config.get('PAY_CENTER_APP_AES_SECRET', '')
    
    def create_recharge_order(self, user_id, agent_id,amount, out_trade_no, subject="充值", memo="充值",
                            realname="", bank_code="KBZ", phone="", payment_type="KBZ",
                            receive_account="", receive_account_name="", client_ip="127.0.0.1", channelType=None, nFM2PayCenter=False):
        """
        创建充值订单
        
        Args:
            user_id: 用户ID
            amount: 充值金额
            out_trade_no: 交易订单编号
            subject: 订单标题
            memo: 交易备注
            realname: 实名用户
            bank_code: 付款银行
            phone: 充值会员手机号
            payment_type: 支付类型
            receive_account: 收款账号
            receive_account_name: 收款账号户名
            client_ip: 客户IP
            
        Returns:
            dict: 返回支付中心响应数据
            {
                "success": True/False,
                "data": {
                    "payUserPhone": "Custo (******2241)",
                    "timeout": 0,
                    "tradeOrderId": "cdb131ec6bf54f39ace2721b8bdd0ff6",
                    "payUserName": "小牛",
                    "paymentUrl": "http://api.wisina.top/mpay/pages/pay/payment?id=cdb131ec6bf54f39ace2721b8bdd0ff6",
                    "tradeNo": "PI202508186400000007",
                    "outTradeNo": "01002789010072577693",
                    "receiveAccount": "09942471300",
                    "success": true,
                    "notifyUrl": "",
                    "curType": "MMK",
                    "qrcode": "",
                    "payTimeout": "2025-08-18 17:40:14",
                    "receiveAccountName": "Custo"
                },
                "message": "success message"
            }
        """
        try:
            # 未指定channelType时，使用配置文件中的默认支付通道
            if channelType is None:
                channelType = app.config.get('PAY_CHANNEL_TYPE', 'VIPPay')

            #转换bank_code
            if payment_type == "KBZ Pay":
                payment_type = "KBZ"

            if payment_type == "Wave Money":
                payment_type = "WaveMoney"

            if channelType == "NFM2" and not nFM2PayCenter:
                # NFM2支付方式，默认不走支付中心
                return {
                    'success': True,
                    'data': {
                        'tradeNo': out_trade_no,
                        'tradeOrderId': out_trade_no
                    }
                }
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
                "channelType": channelType
            }

            logger.info(f"创建充值订单请求 - 用户ID: {user_id}, 交易单号: {out_trade_no}, 金额: {amount}, 支付类型: {payment_type}, 渠道类型: {channelType}")
            #  请求头增加appid
            headers = {'Content-Type': 'text/plain', 'appid': self.app_id}
            # 进行数据加密
            plain_text = Kits.json_dumps(params)
            plain_text = Kits.encrypt(plain_text, self.aes_secret)
            logger.info(f"充值订单请求数据已加密 - 交易单号: {out_trade_no}")
            response = requests.post(self.pay_create_url, data=plain_text, headers=headers)
            resp_json = response.json()

            logger.info(f"充值订单响应 - 交易单号: {out_trade_no}, 响应: {resp_json}")

            if resp_json.get('code') == "OK" and resp_json.get('ok') and resp_json.get('data', {}).get('success'):
                logger.info(f"充值订单创建成功 - 用户ID: {user_id}, 交易单号: {out_trade_no}, 支付中心订单号: {resp_json.get('data', {}).get('tradeNo')}")
                return {
                    'success': True,
                    'data': resp_json.get('data'),
                    'message': 'Recharge order created successfully'
                }
            else:
                logger.warning(f"充值订单创建失败 - 用户ID: {user_id}, 交易单号: {out_trade_no}, 错误信息: {resp_json.get('msg', 'Unknown error')}")
                return {
                    'success': False,
                    'data': None,
                    'message': resp_json.get('msg', 'Failed to create recharge order'),
                    'error': resp_json
                }

        except Exception as e:
            logger.error(f"创建充值订单异常 - 用户ID: {user_id}, 交易单号: {out_trade_no}, 错误: {e}", exc_info=True)
            return {
                'success': False,
                'data': None,
                'message': f'Exception occurred , Please Wait for a moment and try again'
            }

    def get_recharge_order_status(self, out_trade_no):
        """
        查询充值订单状态
        
        Args:
            out_trade_no: 外部交易订单号
            
        Returns:
            dict: 订单状态信息
        """
        try:
            charge_apply = ChargeApply.query.filter(
                ChargeApply.OUT_TRADE_NO == out_trade_no
            ).first()
            
            if not charge_apply:
                return {
                    'success': False,
                    'message': 'Order not found'
                }
            
            return {
                'success': True,
                'data': {
                    'out_trade_no': charge_apply.OUT_TRADE_NO,
                    'trade_no': charge_apply.TRADE_NO,
                    'order_id': charge_apply.ORDER_ID,
                    'status': charge_apply.STATUS,
                    'amount': charge_apply.MONEY,
                    'user_id': charge_apply.USER_ID,
                    'create_time': str(charge_apply.CREATE_TIME),
                    'reason': charge_apply.REASON
                }
            }

        except Exception as e:
            logger.error(f"查询充值订单状态异常 - 交易单号: {out_trade_no}, 错误: {e}", exc_info=True)
            return {
                'success': False,
                'message': f'Exception occurred: {str(e)}'
            }


    def get_pay_channels(self, channel_type=None, status=None, wallet_provider=None, page=None, limit=None):
        """
        获取可用支付通道列表（供前端核查支付是否可用、可路由通道）
        对接 jxboot-apps-pay OpenapiController.channels()

        Args:
            channel_type: 支付通道类型，如 VIPPay；不传则支付中心使用默认通道
            status: 通道状态过滤（ONLINE/BUSY/STANDBY/OFFLINE/ERROR/LOCKED/SUSPENDED/LIMITED）
            wallet_provider: 钱包供应商（KBZPAY/WAVEPAY）
            page: 页码
            limit: 每页数量

        Returns:
            dict: {'success': bool, 'data': [ChannelInfo,...], 'message': str}
        """
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
            # body 采用 AES 加密（与 paycreate 一致）
            plain_text = Kits.json_dumps(params)
            encrypted_body = Kits.encrypt(plain_text, self.aes_secret)

            logger.info(f"查询支付通道请求 - 渠道类型: {channel_type}, 过滤: {params}")
            response = requests.post(self.pay_channels_url, data=encrypted_body, headers=headers)
            resp_json = response.json()
            logger.info(f"查询支付通道响应: {resp_json}")

            if resp_json.get('code') == 'OK' and resp_json.get('ok'):
                return {
                    'success': True,
                    'data': resp_json.get('data') or [],
                    'message': 'success'
                }
            return {
                'success': False,
                'data': [],
                'message': resp_json.get('msg', 'Failed to query pay channels'),
                'error': resp_json
            }

        except Exception as e:
            logger.error(f"查询支付通道异常 - 错误: {e}", exc_info=True)
            return {
                'success': False,
                'data': [],
                'message': f'Exception occurred: {str(e)}'
            }


# 创建全局实例
pay_order_service = PayOrderService()