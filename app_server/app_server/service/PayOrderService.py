import requests
import traceback
from datetime import datetime
from app_server import app, db
from app_server.model.ChargeApplyModel import ChargeApply
from app_server.utils.Kits import Kits


class PayOrderService:
    """充值订单服务"""
    
    def __init__(self):
        self.pay_create_url = app.config.get('PAY_CENTER_API', '') + '/pay/openapi/paycreate'
        self.callback_url = app.config.get('CHARGE_CALLBACK_URL', '')
        self.app_id = app.config.get('PAY_CENTER_APP_ID', '')
        self.aes_secret = app.config.get('PAY_CENTER_APP_AES_SECRET', '')
    
    def create_recharge_order(self, user_id, agent_id,amount, out_trade_no, subject="充值", memo="充值",
                            realname="", bank_code="KBZ", phone="", payment_type="KBZ",
                            receive_account="", receive_account_name="", client_ip="127.0.0.1", channelType="TCPay", nFM2PayCenter=False):
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
            
            print(f"Creating recharge order with params: {params}")
            #  请求头增加appid
            headers = {'Content-Type': 'text/plain', 'appid': self.app_id}
            # 进行数据加密
            plain_text = Kits.json_dumps(params)
            plain_text = Kits.encrypt(plain_text, self.aes_secret)
            print(f"Encrypted data: {plain_text}")
            response = requests.post(self.pay_create_url, data=plain_text, headers=headers)
            resp_json = response.json()
            
            print(f"Recharge order response: {resp_json}")
            
            if resp_json.get('code') == "OK" and resp_json.get('ok') and resp_json.get('data', {}).get('success'):
                return {
                    'success': True,
                    'data': resp_json.get('data'),
                    'message': 'Recharge order created successfully'
                }
            else:
                return {
                    'success': False,
                    'data': None,
                    'message': resp_json.get('msg', 'Failed to create recharge order'),
                    'error': resp_json
                }
                
        except Exception as e:
            print(f"Create recharge order error: {e}")
            traceback.print_exc()
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
            print(f"Get recharge order status error: {e}")
            traceback.print_exc()
            return {
                'success': False,
                'message': f'Exception occurred: {str(e)}'
            }


# 创建全局实例
pay_order_service = PayOrderService()