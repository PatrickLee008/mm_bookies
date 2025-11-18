import uuid

import redis
from sqlalchemy import or_, func, and_
from app_server import app, db, auth, Redis, app_opt, google_credentials
from app_server.model.AppMemberBalanceLogModel import TransactionType
from app_server.model.ChargeApplyModel import ChargeApply, StatusMap, StatusLabelMap
from app_server.service import detect_myan, detect_en_new
from app_server.utils.Kits import Kits
from app_server.model.ChargeModel import Charge, RechargePayType, RechargeChargeType
from app_server.model.ChargeCallback import ChargeCallback, ChargeCallbackStatus
from app_server.model.SysBankcardModel import SysBankcard, SysBankcardStatus
from app_server.model.AppMemberModel import AppMember
# from app_server.service import translate_re, translate_re_en
from flask import g, request, jsonify, Blueprint
from decimal import Decimal
import platform
import signal
import os
import time
import re

r_charge = Blueprint('charge', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'JPG', 'PNG', 'gif', 'GIF', 'jpeg'}


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

    print(items)
    return items


def detect_transaction(img_path):
    from google.cloud import vision
    # 识别出图片订单号
    client = vision.ImageAnnotatorClient(credentials=google_credentials)

    with open(img_path, "rb") as image_file:
        content = image_file.read()

    image = vision.Image(content=content)
    response = client.document_text_detection(image=image, image_context={"language_hints": ["my", "en"]})

    lan = 'en'
    for _detect in response.full_text_annotation.pages[0].property.detected_languages:
        if _detect.language_code == 'my' and _detect.confidence > 0.1:
            lan = 'my'
            break

    vision_text = response.full_text_annotation.text
    if lan == "my":
        print("got mian text:", vision_text)
        all_valid_trades = detect_myan(vision_text)
    else:
        print("got en text:", vision_text)
        all_valid_trades = detect_en_new(vision_text)
    return all_valid_trades


@r_charge.route('/order_image', methods=['POST'])
# @auth.login_required
def order_image():
    """

                @@@
                #### Args:
                        MONEY : String(64) "金额"
                        REMARK : String(256) "备注：申请说明"
                        file : File "充值图片"
                #### Returns::
                        { 'message': "add successful."}
                        { 'message': "System or Technical Error."}
            """
    picture = request.files.get('image')
    print(request, request.form)
    try:
        # 设置超时信号处理函数
        def handler(signum, frame):
            raise TimeoutError('Query timed out after {} seconds'.format(timeout))

        if 'Linux' == platform.system() and not app.config.get('TESTING'):
            timeout = 20

            # 注册超时信号处理函数
            signal.signal(signal.SIGALRM, handler)
            # 设置超时时间
            signal.alarm(timeout)

        if not picture:
            response = jsonify({'message': "image cannot be null"})
            response.status_code = 400
            return response

        suffix = picture.filename.rsplit('.', 1)[1]
        if suffix not in ALLOWED_EXTENSIONS:
            response = jsonify({'message': "incorrect file format"})
            response.status_code = 400
            return response
        img_path = os.path.join('app_server/static/img/charge_temp', picture.filename)
        picture.save(img_path)

        all_valid_trades = detect_transaction(img_path)
        os.remove(img_path)
        if not len(all_valid_trades):
            return jsonify(
                {'message': "cannot detect the transaction id, please recheck the image or contact customer service"})

        if 'Linux' == platform.system() and signal:
            # 取消超时信号
            signal.alarm(0)

        return jsonify({
            'message': "check successful.",
            'trades': all_valid_trades
        })
    except TimeoutError as e:
        # 查询超时，返回超时信息
        return jsonify({'message': "image reading timeout"})
    except Exception as e:
        print("add r_charge error:", e)
        if img_path and os.path.isfile(img_path):
            os.remove(img_path)

    return jsonify({'message': "System or Technical Error."})


@r_charge.route('/order_image_en', methods=['POST'])
# @auth.login_required
def order_image_en():
    """

                @@@
                #### Args:
                        MONEY : String(64) "金额"
                        REMARK : String(256) "备注：申请说明"
                        file : File "充值图片"
                #### Returns::
                        { 'message': "add successful."}
                        { 'message': "System or Technical Error."}
            """

    """

                @@@
                #### Args:
                        MONEY : String(64) "金额"
                        REMARK : String(256) "备注：申请说明"
                        file : File "充值图片"
                #### Returns::
                        { 'message': "add successful."}
                        { 'message': "System or Technical Error."}
            """
    picture = request.files.get('image')
    print(request, request.form)
    try:
        # 设置超时信号处理函数
        def handler(signum, frame):
            raise TimeoutError('Query timed out after {} seconds'.format(timeout))

        if 'Linux' == platform.system() and not app.config.get('TESTING'):
            timeout = 20

            # 注册超时信号处理函数
            signal.signal(signal.SIGALRM, handler)
            # 设置超时时间
            signal.alarm(timeout)

        if not picture:
            response = jsonify({'message': "image cannot be null"})
            response.status_code = 400
            return response

        suffix = picture.filename.rsplit('.', 1)[1]
        if suffix not in ALLOWED_EXTENSIONS:
            response = jsonify({'message': "incorrect file format"})
            response.status_code = 400
            return response
        img_path = os.path.join('app_server/static/img/charge_temp', picture.filename)
        picture.save(img_path)

        all_valid_trades = detect_transaction(img_path)
        os.remove(img_path)
        if not len(all_valid_trades):
            return jsonify(
                {'message': "cannot detect the transaction id, please recheck the image or contact customer service"})

        if 'Linux' == platform.system() and signal:
            # 取消超时信号
            signal.alarm(0)

        return jsonify({
            'message': "check successful.",
            'trades': all_valid_trades
        })
    except TimeoutError as e:
        # 查询超时，返回超时信息
        return jsonify({'message': "image reading timeout"})
    except Exception as e:
        print("add r_charge error:", e)
        if img_path and os.path.isfile(img_path):
            os.remove(img_path)

    return jsonify({'message': "System or Technical Error."})


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
                        {'code': 500, 'message': "System or Technical Error."}
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

        print("send amount:", amount)
        db.session.add(recharge)
        db.session.commit()

        app_opt.send({
            "user_account": app_member.id,
            "user_name": app_member.username,
            "type": TransactionType.Deposit,
            "type_sub": "recharge_apply",
            "before_amount": float(before_amount),
            "after_amount": float(app_member.money),
            "amount": float(amount),
            "source_id": charge_id,

            "aid": app_member.aid,
            "create_by_id": app_member.id,
            "mb_rid": app_member.rid,
            "source": "Ewallet",
            "target": "System"
        })
        return jsonify({'message': "add successful"})
    except Exception as e:
        print("add r_charge error:", e)

    response = jsonify({'message': "System or Technical Error."})
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
                        {'code': 500, 'message': "System or Technical Error."}
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
        recharge = Charge(id=charge_id, trade_no=Kits.generate_uuid(), amount=amount,
                          mb_id=app_member.id, aid=app_member.aid, mb_username=app_member.username,
                          mb_acc_name=app_member.name,
                          pay_type=RechargePayType.MANUAL, charge_type=RechargeChargeType.USER, mb_bank_code=bank_code)

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
        print(pic_name)
        picture.save(os.path.join(path, pic_name))
        recharge.slip_pic = pic_name
        recharge.out_trade_no = transaction_id

        before_amount = app_member.money
        recharge.status = StatusLabelMap.Pending
        # app_member.money += int(amount)
        after_money = app_member.money + int(amount)

        print("send amount:", amount)
        db.session.add(recharge)
        db.session.commit()

        app_opt.send({
            "user_account": app_member.id,
            "user_name": app_member.username,
            "type": TransactionType.Deposit,
            "type_sub": RechargePayType.MANUAL,
            "before_amount": float(before_amount),
            "after_amount": float(after_money),
            "amount": float(amount),
            "source_id": charge_id,

            "aid": app_member.aid,
            "create_by_id": app_member.id,
            "mb_rid": app_member.rid,
            "source": "Ewallet",
            "target": "System",
            "source_status": StatusMap.Pending
        })
        return jsonify({'message': "add successful"})
    except Exception as e:
        print("add r_charge error:", e)

    response = jsonify({'message': "System or Technical Error."})
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
#                         { 'message': "System or Technical Error."}
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
#     response = jsonify({ 'message': "System or Technical Error."})


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
        print("add r_charge error:", e)

    response = jsonify({'message': "System or Technical Error."})
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
        print("add r_charge error:", e)

    response = jsonify({'message': "System or Technical Error."})
    response.status_code = 500
    return response
