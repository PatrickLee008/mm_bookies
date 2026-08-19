import uuid

import redis
from sqlalchemy import or_, func, and_
from app_server import app, db, auth, Redis, app_opt, google_credentials
from app_server.logger import get_logger
from app_server.model.AppMemberBalanceLogModel import TransactionType
from app_server.model.ChargeApplyModel import ChargeApply, StatusMap, StatusLabelMap
from app_server.service import detect_myan, detect_en_new
from app_server.utils.Kits import Kits
from app_server.model.ChargeModel import Charge, RechargePayType, RechargeChargeType
from app_server.model.ChargeCallback import ChargeCallback, ChargeCallbackStatus
from app_server.model.SysBankcardModel import SysBankcard, SysBankcardStatus
from app_server.model.AppMemberModel import AppMember
from app_server.model.AppAgentModel import AppAgent
from app_server.utils.MessageHelper import MessageHelper
from app_server.utils.MemberMessageService import MemberMessageService
# from app_server.service import translate_re, translate_re_en
from flask import g, request, jsonify, Blueprint
from decimal import Decimal
from datetime import datetime
import platform
import signal
import os
import time
import re

r_charge = Blueprint('charge', __name__)
logger = get_logger()

ALLOWED_EXTENSIONS = {'png', 'jpg', 'JPG', 'PNG', 'gif', 'GIF', 'jpeg'}


from google.cloud import vision
from google.api_core.exceptions import ServiceUnavailable

# 懒加载单例: 避免每次请求重建 gRPC 连接
_vision_client = None


def _get_vision_client(force_new=False):
    global _vision_client
    if _vision_client is None or force_new:
        _vision_client = vision.ImageAnnotatorClient(credentials=google_credentials)
    return _vision_client


def regen_words(text_annotations):
    items = []
    lines = {}

    for text in text_annotations[1:]:
        top_x_axis = text.bounding_poly.vertices[0].x
        top_y_axis = text.bounding_poly.vertices[0].y
        bottom_y_axis = text.bounding_poly.vertices[3].y

        if top_y_axis not in lines:
            lines[top_y_axis] = [(top_y_axis, bottom_y_axis), []]

        for s_top_y_axis, s_item in lines.items():
            if top_y_axis < s_item[0][1]:
                lines[s_top_y_axis][1].append((top_x_axis, text.description))
                break

    for _, item in lines.items():
        if item[1]:
            words = sorted(item[1], key=lambda t: t[0])
            items.append((' '.join([word for _, word in words])))

    logger.info(f"OCR识别结果: {items}")
    return items


def detect_transaction(image_bytes):
    """接收图片字节内容，直接调用 Vision API，无需磁盘 I/O"""
    t0 = time.time()

    client = _get_vision_client()
    t1 = time.time()
    logger.info(f"[detect_transaction] 获取客户端: {t1 - t0:.3f}s")

    image = vision.Image(content=image_bytes)

    try:
        response = client.document_text_detection(image=image, image_context={"language_hints": ["my", "en"]})
    except ServiceUnavailable:
        # gRPC channel 断开，重建客户端重试一次
        logger.warning("Vision API 连接失败，重建客户端重试")
        client = _get_vision_client(force_new=True)
        response = client.document_text_detection(image=image, image_context={"language_hints": ["my", "en"]})

    t2 = time.time()
    logger.info(f"[detect_transaction] Vision API 调用: {t2 - t1:.3f}s")

    vision_text = response.full_text_annotation.text

    # 改进的语言检测逻辑
    lan = 'en'

    # 方法1: 检查是否包含缅甸文Unicode字符范围 (U+1000 到 U+109F)
    has_myanmar_chars = any('\u1000' <= char <= '\u109F' for char in vision_text)

    # 方法2: 检查常见的缅文关键词
    myanmar_keywords = [
        'လုပ်ဆောင်ချက်', 'အောင်မြင်', 'ငွေလွှဲ', 'ကျပ်',
        'နေ့ရက်', 'အချိန်', 'စာရင်း', 'မှတ်ချက်'
    ]
    has_myanmar_keywords = any(keyword in vision_text for keyword in myanmar_keywords)

    # 如果包含缅文字符或关键词,判定为缅文
    if has_myanmar_chars or has_myanmar_keywords:
        lan = 'my'
    else:
        # 降级使用API的语言检测
        for _detect in response.full_text_annotation.pages[0].property.detected_languages:
            if _detect.language_code == 'my' and _detect.confidence > 0.1:
                lan = 'my'
                break

    t3 = time.time()
    logger.info(f"[detect_transaction] 语言检测({lan}): {t3 - t2:.3f}s")

    if lan == "my":
        logger.info(f"检测到缅甸语文本")
        # logger.info(f"检测到缅甸语文本: {vision_text}")
        all_valid_trades = detect_myan(vision_text)
    else:
        logger.info(f"检测到英文文本")
        # logger.info(f"检测到英文文本: {vision_text}")
        all_valid_trades = detect_en_new(vision_text)

    t4 = time.time()
    logger.info(f"[detect_transaction] 文本解析({lan}): {t4 - t3:.3f}s, 总计: {t4 - t0:.3f}s")

    return all_valid_trades


@r_charge.route('/order_image', methods=['POST'])
@auth.login_required
def order_image():
    t_start = time.time()
    picture = request.files.get('image')

    try:
        if not picture:
            return jsonify({'message': "image cannot be null"}), 400

        if '.' not in picture.filename:
            return jsonify({'message': "incorrect file format"}), 400

        suffix = picture.filename.rsplit('.', 1)[1]
        if suffix not in ALLOWED_EXTENSIONS:
            return jsonify({'message': "incorrect file format"}), 400

        # 直接读取字节，不落盘
        image_bytes = picture.read()
        t_read = time.time()
        logger.info(f"[order_image] 读取图片: {len(image_bytes)} bytes, 耗时: {t_read - t_start:.3f}s")

        all_valid_trades = detect_transaction(image_bytes)
        t_detect = time.time()
        logger.info(f"[order_image] detect_transaction 完成, 耗时: {t_detect - t_read:.3f}s, 结果数: {len(all_valid_trades)}")

        if not len(all_valid_trades):
            return jsonify({
                'message': "cannot detect the transaction id, please recheck the image or contact customer service"
            })

        logger.info(f"[order_image] 总耗时: {time.time() - t_start:.3f}s")
        return jsonify({
            'message': "check successful.",
            'trades': all_valid_trades
        })

    except Exception as e:
        logger.error(f"图片识别订单号失败: {e}, 已耗时: {time.time() - t_start:.3f}s", exc_info=True)
        return jsonify({'message': "System or Technical Error"})


@r_charge.route('/order_image_en', methods=['POST'])
# @auth.login_required
def order_image_en():
    picture = request.files.get('image')
    logger.info(f"收到图片订单识别请求: {request.form}")
    try:
        # 设置超时信号处理函数
        def handler(signum, frame):
            raise TimeoutError('Query timed out after {} seconds'.format(timeout))

        if 'Linux' == platform.system() and not app.config.get('TESTING'):
            timeout = 20
            signal.signal(signal.SIGALRM, handler)
            signal.alarm(timeout)

        if not picture:
            return jsonify({'message': "image cannot be null"}), 400

        suffix = picture.filename.rsplit('.', 1)[1]
        if suffix not in ALLOWED_EXTENSIONS:
            return jsonify({'message': "incorrect file format"}), 400

        # 直接读取字节，不落盘
        image_bytes = picture.read()

        all_valid_trades = detect_transaction(image_bytes)

        if not len(all_valid_trades):
            return jsonify(
                {'message': "cannot detect the transaction id, please recheck the image or contact customer service"})

        if 'Linux' == platform.system() and signal:
            signal.alarm(0)

        return jsonify({
            'message': "check successful.",
            'trades': all_valid_trades
        })
    except TimeoutError as e:
        return jsonify({'message': "image reading timeout"})
    except Exception as e:
        logger.error(f"图片识别订单号失败(en): {e}", exc_info=True)

    return jsonify({'message': "System or Technical Error"})


# 自动充值
@r_charge.route('/recharge_apply', methods=['POST'])
@auth.login_required
def recharge_apply():
    """

                @@@
                #### Args:
                        MONEY : String(64) "金额"
                        REMARK : String(256) "备注：申请说明"
                #### Returns::
                        {'code': 200, 'message': "add successful."}
                        {'code': 500, 'message': "System or Technical Error"}
            """

    args = request.get_json()

    transaction_id = args.get('transaction_id')
    amount = args.get('amount')
    charge_way = args.get('charge_way')
    bank_code = args.get('bank_code')
    try:

        # 防止并发
        getter_key = "charge_%s" % g.user.id
        success = Redis.setnx(getter_key, 1)  # SETNX命令
        if not success:
            response = jsonify({"message": "charge in very short time"})
            response.status_code = 400
            return response

        # 设置键的过期时间
        Redis.expire(getter_key, 10)

        if not amount:
            response = jsonify({'message': "amount cannot be null"})
            response.status_code = 400
            return response

        if int(amount) < 100:
            response = jsonify({'message': "amount cannot be less than 100"})
            response.status_code = 400
            return response
        if int(amount) > 1000000:
            response = jsonify({'message': "amount cannot be greater than 1000000"})
            response.status_code = 400
            return response

        # 开始充值
        app_member = AppMember.query.filter_by(id=g.user.id).with_for_update().first()
        charge_id = Kits.generate_uuid()
        recharge = ChargeApply(id=charge_id, recharge_id=charge_id, mb_id=app_member.id, money=amount,
                               charge_way="0", mb_bank_code=bank_code)
        # 自助充值，调用接口发起自助充值申请
        return Kits.rt_error("not support auto recharge")

        before_amount = app_member.money
        # if charge_way == 0:
        #     recharge.STATUS = 1
        #     app_member.money += amount
        recharge.status = StatusMap.Success
        app_member.money += int(amount)

        logger.info(f"自动充值申请提交 - 用户ID: {app_member.id}, 充值金额: {amount}, 充值ID: {charge_id}")
        db.session.add(recharge)
        db.session.commit()

        # app_opt.send({
        #     "user_account": app_member.id,
        #     "user_name": app_member.username,
        #     "type": TransactionType.Deposit,
        #     "type_sub": "recharge_apply",
        #     "before_amount": float(before_amount),
        #     "after_amount": float(app_member.money),
        #     "amount": float(amount),
        #     "source_id": charge_id,
        #
        #     "aid": app_member.aid,
        #     "create_by_id": app_member.id,
        #     "mb_rid": app_member.rid,
        #     "source": "Ewallet",
        #     "target": "System"
        # })
        return jsonify({'message': "add successful"})
    except Exception as e:
        logger.error(f"自动充值申请失败 - 用户ID: {g.user.id}, 错误: {e}", exc_info=True)

    response = jsonify({'message': "System or Technical Error"})
    response.status_code = 500
    return response


# 充值
@r_charge.route('/recharge', methods=['POST'])
@auth.login_required
def recharge():
    """

                @@@
                #### Args:
                        MONEY : String(64) "金额"
                        REMARK : String(256) "备注：申请说明"
                        file : File "充值图片"
                #### Returns::
                        {'code': 200, 'message': "add successful."}
                        {'code': 500, 'message': "System or Technical Error"}
            """
    picture = request.files.get('image')

    args = request.form
    transaction_id = args.get('transaction_id')
    amount = args.get('amount')
    bank_code = args.get('bank_code')
    try:

        # 防止并发
        getter_key = "charge_%s" % g.user.id
        success = Redis.setnx(getter_key, 1)  # SETNX命令
        if not success:
            response = jsonify({"message": "charge in very short time"})
            response.status_code = 400
            return response

        # 设置键的过期时间
        Redis.expire(getter_key, 10)

        if not amount:
            response = jsonify({'message': "amount cannot be null"})
            response.status_code = 400
            return response
        recharge_record = Charge.query.filter(Charge.out_trade_no == transaction_id).first()
        if recharge_record:
            response = jsonify({'message': "this transaction id has exist"})
            response.status_code = 400
            return response

        if int(amount) < 100:
            response = jsonify({'message': "amount cannot be less than 100"})
            response.status_code = 400
            return response
        if int(amount) > 1000000:
            response = jsonify({'message': "amount cannot be greater than 1000000"})
            response.status_code = 400
            return response

        # 开始充值
        app_member = AppMember.query.filter_by(id=g.user.id).with_for_update().first()
        charge_id = Kits.generate_uuid()
        current_time = datetime.now()
        recharge = Charge(id=charge_id, trade_no=Kits.generate_uuid(), amount=amount,
                          mb_id=app_member.id, aid=app_member.aid, mb_username=app_member.username,
                          mb_acc_name=app_member.name,
                          pay_type=RechargePayType.MANUAL, charge_type=RechargeChargeType.USER, mb_bank_code=bank_code,
                          confirm_time=current_time)

        if not picture:
            response = jsonify({'message': "slip cannot be null"})
            response.status_code = 400
            return response

        suffix = picture.filename.rsplit('.', 1)[1]
        if suffix not in ALLOWED_EXTENSIONS:
            response = jsonify({'message': "incorrect file format"})
            response.status_code = 400
            return response
        path = app.config['CHARGE_APPLY_PIC_DIR']
        # 如果目录不存在就创建
        os.makedirs(path, exist_ok=True)
        pic_name = "%s.%s" % (transaction_id, suffix)
        logger.info(f"保存充值凭证图片: {pic_name}")
        picture.save(os.path.join(path, pic_name))
        recharge.slip_pic = pic_name
        recharge.out_trade_no = transaction_id

        before_amount = app_member.money
        recharge.status = StatusLabelMap.Pending
        # app_member.money += int(amount)
        after_money = app_member.money + int(amount)

        logger.info(
            f"充值申请提交 - 用户ID: {app_member.id}, 用户名: {app_member.username}, 充值金额: {amount}, 交易单号: {transaction_id}, 充值ID: {charge_id}, 银行代码: {bank_code}")
        db.session.add(recharge)
        db.session.commit()
        logger.info(f"充值申请保存成功 - 充值ID: {charge_id}, 状态: {StatusLabelMap.Pending}")

        # 发送充值申请通知给管理员
        try:
            if app_member.aid:
                # 通过aid查询代理信息
                agent = AppAgent.query.filter_by(id=app_member.aid).first()
                if agent:
                    # 通过sys_user表获取所有关联的管理员ID
                    admin_user_ids = agent.get_admin_user_ids()
                    if admin_user_ids:
                        # 发送通知给管理员
                        MessageHelper.send_recharge_apply_to_admin(
                            admin_user_ids=admin_user_ids,
                            member_id=app_member.id,
                            member_name=app_member.username,
                            order_id=transaction_id,
                            amount=float(amount)
                        )
        except Exception as e:
            app.logger.warning(f"Failed to send recharge notification to admin: {str(e)}")

        # P3: 发送站内通知给会员 — 充值申请已提交
        try:
            MemberMessageService.send_recharge_submitted(
                member_id=app_member.id,
                order_id=transaction_id,
                amount=float(amount),
                aid=app_member.aid
            )
        except Exception as e:
            app.logger.warning(f"Failed to send recharge notification to member: {str(e)}")

        # app_opt.send({
        #     "user_account": app_member.id,
        #     "user_name": app_member.username,
        #     "type": TransactionType.Deposit,
        #     "type_sub": RechargePayType.MANUAL,
        #     "before_amount": float(before_amount),
        #     "after_amount": float(after_money),
        #     "amount": float(amount),
        #     "source_id": charge_id,
        #
        #     "aid": app_member.aid,
        #     "create_by_id": app_member.id,
        #     "mb_rid": app_member.rid,
        #     "source": "Ewallet",
        #     "target": "System",
        #     "source_status": StatusMap.Pending
        # })

        # 记录充值行为日志
        try:
            from app_server.service.AppBehaviorLogService import AppBehaviorLogService

            AppBehaviorLogService.add_behavior_log(
                request=request,
                event_type='deposit',
                member_id=app_member.id,
                event_params={
                    'amount': float(amount),
                    'transaction_id': transaction_id,
                    'bank_code': bank_code,
                    'charge_id': charge_id,
                    'status': StatusLabelMap.Pending
                },
                remark='User deposit initiated'
            )
        except Exception as e:
            app.logger.warning(f"Failed to add deposit behavior log: {str(e)}")

        return jsonify({'message': "add successful", "statusCode": 200})
    except Exception as e:
        logger.error(f"充值申请失败 - 用户ID: {g.user.id}, 错误: {e}", exc_info=True)

    response = jsonify({'message': "System or Technical Error"})
    response.status_code = 500
    return response


# @r_charge.route('/apply_charge', methods=['POST'])
# @auth.login_required
# def apply_charge():
#     """
#
#                 @@@
#                 #### Args:
#                         MONEY : String(64) "金额"
#                         REMARK : String(256) "备注：申请说明"
#                         file : File "充值图片"
#                 #### Returns::
#                         {'code': 20000, 'message': "add successful."}
#                         { 'message': "System or Technical Error"}
#             """
#     picture = request.files.get('image')
#
#     if picture:
#         args = request.form
#     else:
#         args = request.get_json()
#
#     transaction_id = args.get('transaction_id')
#     amount = args.get('amount')
#     try:
#
#         # 防止并发
#         getter_key = "charge_%s" % g.user.id
#         success = Redis.setnx(getter_key, 1)  # SETNX命令
#         if not success:
#             return jsonify({ "message": "charge in very short time"})
#
#         # 设置键的过期时间
#         Redis.expire(getter_key, 10)
#
#         if not amount:
#             response = jsonify({'message': "amount cannot be null"})
#
#         if int(amount) < 5000:
#             response = jsonify({'code': 50002, 'message': "amount cannot be less than 5000"})
#
#         # if not picture:
#         #     response = jsonify({'code': 50002, 'message': "image cannot be null"})
#         charge_callback = ChargeCallback.query.filter(ChargeCallback.TRANSACTION_ID ==transaction_id,
#                                                       ChargeCallback.AMOUNT == Decimal(amount),
#                                                       ChargeCallback.STATUS == ChargeCallbackStatus.Not).first()
#
#         if not charge_callback:
#             response = jsonify({#                             'message': "cannot find order by this order number, please recheck or contact customer service"})
#
#         if picture:
#             suffix = picture.filename.rsplit('.', 1)[1]
#             if suffix not in ALLOWED_EXTENSIONS:
#                 return jsonify({
#                     'code': 50002, 'message': "incorrect file format"})
#
#             path = app.config['CHARGE_APPLY_PIC_DIR']
#             pic_name = "%s.%s" % (transaction_id, suffix)
#             picture.save(os.path.join(path, pic_name))
#             charge_callback.PICTURE = pic_name
#
#         # 开始充值
#         app_member = AppMember.query.filter_by(id=g.user.id).with_for_update().first()
#         charge_id = int(round(time.time() * 1000))
#         charge_callback.CHARGE_ID = charge_id
#
#         recharge = Charge(RECHARGE_ID=charge_id)
#         before_amount = Decimal(app_member.money)
#         after_amount = before_amount + charge_callback.AMOUNT
#         app_member.money = after_amount
#
#         recharge.BEFORE_MONEY = before_amount
#         recharge.AFTER_MONEY = after_amount
#         charge_callback.USER_ID = recharge.USER_ID = app_member.id
#         charge_callback.NICK_NAME = recharge.NICK_NAME = app_member.NICK_NAME
#         recharge.MONEY = charge_callback.AMOUNT
#         recharge.CHARGE_WAY = 1
#
#         print("send amount:", amount, "data amount:", charge_callback.AMOUNT)
#
#         if int(amount) != int(charge_callback.AMOUNT):
#             return jsonify({
#                 'code': 50002, 'message': "amount not right"})
#
#         db.session.add(recharge)
#         charge_callback.STATUS = ChargeCallbackStatus.Confirm
#
#         db.session.commit()
#
#         app_opt.send({
#             "user_account": app_member.OPENID,
#             "user_name": app_member.NICK_NAME,
#             "type": AppOpType.CHARGE,
#             "amount": before_amount,
#             "balance": Decimal(app_member.money),
#             "source_id": charge_id
#         })
#         return jsonify({'code': 20000, 'message': "add successfull"})
#     except Exception as e:
#         print("add r_charge error:", e)
#
#     response = jsonify({ 'message': "System or Technical Error"})


# 获取订单列表
@r_charge.route('/active_bankcard', methods=['GET'])
@auth.login_required
def get_active_bankcard():
    """
                @@@
                #### Args:
                        current_page = request.args.get('page', type=int, default=1)
                        limit = request.args.get('limit', type=int, default=20)
                        key_word = request.args.get('key_word')
                        start_time = request.args.get('start_time')
                        end_time = request.args.get('end_time')
                        is_pay =
                #### Returns::
                        {
                                                        'items': [u.to_dict() for u in order_list],
                            'total': total,
                            'total_amount': total_amount
                        }
            """
    bank_code = request.args.get('bank_code')
    try:
        # if g.user.id != '09899223535':
        #     return jsonify({'code': 20000, 'items': [], })

        # if g.user.id not in ['09254338254', '0988888888'] and bank_code != 'KBZ':
        #     return jsonify({'code': 20000, 'items': [], })

        visible_cards = 'visible_cards_kbz' if bank_code == 'KBZ' else 'visible_cards_wave'
        cards_queue = 'cards_queue_kbz' if bank_code == 'KBZ' else 'cards_queue_wave'
        members = Redis.smembers(visible_cards)

        banks_id = [m.decode() for m in members]
        bankcards = SysBankcard.query.filter(SysBankcard.ID.in_(banks_id)).all()

        active_bankcards = []
        for card in bankcards:
            if card.ENABLE:
                active_bankcards.append(card)

            else:
                Redis.srem(visible_cards, card.ID)
                Redis.lrem(cards_queue, 1, card.ID)

        if not len(active_bankcards):
            response = jsonify({'message': "no active bankcards."})
            response.status_code = 400
            return response

        return jsonify({
            'items': [u.to_dict(include={'ID', 'ACCOUNT', 'BANK_CODE', 'NAME'}) for u in active_bankcards],
        })
    except Exception as e:
        logger.error(f"获取活动银行卡失败 - 错误: {e}", exc_info=True)

    response = jsonify({'message': "System or Technical Error"})
    response.status_code = 500
    return response


# 获取订单列表
@r_charge.route('/get', methods=['GET'])
@auth.login_required
def get_charge_list():
    """
                @@@
                #### Args:
                        current_page = request.args.get('page', type=int, default=1)
                        limit = request.args.get('limit', type=int, default=20)
                        key_word = request.args.get('key_word')
                        start_time = request.args.get('start_time')
                        end_time = request.args.get('end_time')
                        is_pay =
                #### Returns::
                        {
                            'code': 200,
                            'items': [u.to_dict() for u in order_list],
                            'total': total,
                            'total_amount': total_amount
                        }
            """

    current_page = request.args.get('page', type=int, default=1)
    limit = request.args.get('limit', type=int, default=20)

    charge_list = ChargeCallback.query.filter(ChargeCallback.USER_ID == g.user.id, ChargeCallback.STATUS == 1)

    total_amount = charge_list.with_entities(func.sum(Charge.amount)).scalar() or 0

    charge_list = charge_list.order_by(ChargeCallback.CREATE_TIME.desc())

    charge_list = charge_list.offset((current_page - 1) * limit).limit(limit).all()
    total = len(charge_list)

    return jsonify({
        'items': [u.to_dict() for u in charge_list],
        'total': total,
        'total_amount': total_amount
    })


# 检查会员流水验证状态（新累积制）
@r_charge.route('/check_deposit_stake', methods=['POST'])
@auth.login_required
def check_deposit_stake():
    """
    检查会员流水验证状态（新累积制）

    使用累积制流水验证逻辑：
    - Required Turnover(n) = Required Turnover(n-1) + Deposit(n) × Turnover Rate
    - Current Turnover(n) = Current Turnover(n-1) + Bet(n)
    - 重置条件：Withdraw Amount > Promotion Wallet Transfer OR Previous Remaining Balance = 0

    可提现金额计算：
    - IF Current Turnover >= Required Turnover
      THEN Cleared Balance = Remaining Balance
      ELSE Cleared Balance = Promotion Wallet Transfer
    - Withdrawable Amount = Cleared Balance

    ⚠️ 重要：此查询接口只读取数据，不执行重置。重置逻辑在后台审核通过或订单结算时执行。

    @@@
    #### Args:
        无需参数，使用当前登录用户
    #### Returns::
        {
            'code': 20000,
            'current_turnover': 1000.00,        // 当前累积流水
            'required_turnover': 1500.00,       // 需要的累积流水
            'turnover_rate': 1.5,               // 周转率倍数
            'remaining': 500.00,                // 剩余需要的流水
            'is_satisfied': false,              // 是否满足提现条件
            'withdrawable_amount': 0.00,        // 可提现金额
            'withdrawal_amount': 0.00,          // 兼容旧字段
            'current_balance': 1000.00,         // 当前余额
            'message': 'Success'
        }
    """
    try:
        from app_server.service.TurnoverAccumulationService import TurnoverAccumulationService
        from app_server.model.AppMemberModel import AppMember

        user = g.user

        # ⚠️ 重要：查询接口不应该修改数据库状态！
        # 重置逻辑应该在后台审核提现通过或订单结算时执行，而不是在查询时执行

        # 获取累积值（只读取，不修改）
        current_turnover = float(user.current_turnover_accumulated) if user.current_turnover_accumulated else 0.0
        required_turnover = float(user.required_turnover_accumulated) if user.required_turnover_accumulated else 0.0
        current_balance = float(user.money) if user.money else 0.0
        money_promo_withdrawable = float(
            user.money_promotion_withdrawable) if user.money_promotion_withdrawable else 0.0

        # 计算可提现金额（只读取，不修改数据库）
        # Withdrawable Amount = Cleared Balance
        # 流水满足时：Cleared Balance = Remaining Balance
        # 流水不满足时：Cleared Balance = Promotion Wallet Transfer
        withdrawable_amount = TurnoverAccumulationService.calculate_withdrawable_amount(user)

        # 判断是否满足流水条件
        is_satisfied = (required_turnover == 0 or current_turnover >= required_turnover)

        # 计算剩余需要的流水
        remaining = max(0, required_turnover - current_turnover)

        # 获取周转率
        turnover_rate = TurnoverAccumulationService.get_turnover_rate(user)

        logger.info(f"查询流水状态 - 用户ID: {user.id}, "
                    f"Balance: {current_balance}, Promo Withdrawable: {money_promo_withdrawable}, "
                    f"Current Turnover: {current_turnover}, Required Turnover: {required_turnover}, "
                    f"Satisfied: {is_satisfied}, Withdrawable: {withdrawable_amount}, "
                    f"Remaining: {remaining}")

        return jsonify({
            'code': 20000,
            'current_turnover': round(current_turnover, 2),
            'required_turnover': round(required_turnover, 2),
            'turnover_rate': turnover_rate,
            'remaining': round(remaining, 2),
            'is_satisfied': is_satisfied,
            'withdrawable_amount': round(withdrawable_amount, 2),
            'withdrawal_amount': round(withdrawable_amount, 2),
            'current_balance': round(current_balance, 2),
            'message': 'Success'
        })

    except Exception as e:
        logger.error(f"检查流水状态失败 - 用户ID: {g.user.id}, 错误: {e}", exc_info=True)
        response = jsonify({'message': "System or Technical Error"})
        response.status_code = 500
        return response


# 获取订单列表
@r_charge.route('/change_card_visible', methods=['POST'])
@auth.login_required
def change_card_visible():
    args = request.get_json()
    card_id = args.get("ID")

    try:
        card = SysBankcard.query.filter_by(ID=card_id).first()
        cards_queue = 'cards_queue_kbz' if card.BANK_CODE == 'KBZ' else 'cards_queue_wave'
        visible_cards = 'visible_cards_kbz' if card.BANK_CODE == 'KBZ' else 'visible_cards_wave'

        # 如果可视集合中没这张卡，就不做任何处理
        if not Redis.sismember(visible_cards, card_id):
            return jsonify({})

        # 从可视队列删除
        Redis.srem(visible_cards, card_id)

        current = SysBankcard.query.filter_by(ID=card_id).with_for_update().one()
        # 转入等待队列
        if current.ENABLE:
            Redis.rpush(cards_queue, card_id)
        current.VISIBLE = 0

        # 从等待队列取出下一张
        next_card = Redis.lpop(cards_queue)
        # 如果下一张卡不在VISIBLE集合中，将其添加

        next_bank_card = SysBankcard.query.filter_by(ID=next_card).with_for_update().one()
        if next_bank_card.ENABLE:
            next_bank_card.VISIBLE = 1
            Redis.sadd(visible_cards, next_card.decode())

        db.session.commit()

        return jsonify({})
    except Exception as e:
        logger.error(f"切换银行卡可见性失败 - 错误: {e}", exc_info=True)

    response = jsonify({'message': "System or Technical Error"})
    response.status_code = 500
    return response
