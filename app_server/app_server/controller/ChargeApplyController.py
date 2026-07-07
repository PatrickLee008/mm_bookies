import time
from datetime import datetime, timedelta
import random
import requests
from sqlalchemy import or_, func, and_
from app_server import app, db, auth, Redis
from app_server.logger import get_logger
from app_server.model.AppAgentBankcard import AppAgentBankcard
from app_server.model.AppAgentModel import AppAgent
from app_server.model.AppMemberBankModel import AppMemberBank
from app_server.model.ChargeApplyModel import ChargeApply, StatusLabelMap
from flask import g, request, jsonify, Blueprint

from app_server.service.PayOrderService import pay_order_service
from app_server.utils import OrmUttil
import os

from app_server.utils.Kits import Kits

charge_apply = Blueprint('charge_apply', __name__)
logger = get_logger()

ALLOWED_EXTENSIONS = {'png', 'jpg', 'JPG', 'PNG', 'gif', 'GIF'}


@charge_apply.route('/add', methods=['POST'])
@auth.login_required
def add_apply():
    """ add_bank_card API Endpoint
        ---
        tags:
          - charge_apply
        parameters:
           - name: file
             in: formData
             type: file
             required: true
             description: image of app_operation
           - name: MONEY
             in: formData
             type: string
             description: money of app_operation
           - name: REMARK
             in: formData
             type: string
             description: remark of app_operation
        responses:
          500:
            description: System or Technical Error
          200:
            description: 绑定成功
        """
    global bank_card
    args = request.get_json()
    logger.info(f"充值申请请求 - 用户ID: {g.user.id}, 用户名: {g.user.username}, 请求参数: {args}")
    # apply args: {'charge_way': 0, 'bank_code': 'KBZ Pay', 'transaction_id': '', 'acc_name': 'Arthur', 'acc_number': '0988888880', 'amount': 5000, 'memo': 'memo', 'subject': 'charge 5000', 'card_id': '1948201677609897984'}
    charge_way = args.get('charge_way')  # 0自动充值，1手动充值
    bank_code = args.get('bank_code')  # 银行名称
    transaction_id = args.get('transaction_id')  # 交易流水号
    acc_name = args.get('acc_name')  # 收款人姓名
    acc_number = args.get('acc_number')  # 收款人账号
    amount = args.get('amount')  # 充值金额
    memo = args.get('memo')  # 备注
    subject = args.get('subject')  # 交易主题
    card_id = args.get('card_id')  # 银行卡ID
    if not all([bank_code, acc_name, acc_number, amount, memo, subject]):
        return Kits.rt_error("Incomplete parameters")

    pay_channel = args.get('pay_channel', app.config['PAY_CHANNEL_TYPE'])  # 支付通道

    # 检查代理是否开启自助充值
    agent_id = g.user.aid if g.user.aid else ""
    if agent_id:
        agent = AppAgent.query.filter(AppAgent.id == agent_id).first()
        if not agent or agent.auto_deposit != 1:
            return jsonify({'code': 50002, 'message': "Your agent has not enabled the automatic deposit"})
    else:
        return jsonify({'code': 50001, 'message': "No agent id"})

    try:
        getter_key = "charge_%s" % g.user.id
        success = Redis.setnx(getter_key, 1)  # SETNX命令
        if not success:
            return Kits.rt_error("charge in very short time.")
        # 设置键的过期时间
        Redis.expire(getter_key, 2)

        # 检查一下是否又未完成的有效订单
        unfinished_apply = ChargeApply.query.filter(ChargeApply.mb_id == g.user.id,
                                                    ChargeApply.status.in_([StatusLabelMap.Pending]),
                                                    ChargeApply.expire_time > datetime.now()).first()
        if unfinished_apply:
            logger.warning(f"用户存在未完成充值订单 - 用户ID: {g.user.id}, 订单ID: {unfinished_apply.id}")
            return Kits.rt_code(409, "you have unfinished apply order.", unfinished_apply.to_dict())
        # 检查银行卡是否存在
        bank_card = None
        if card_id:
            bank_card = AppMemberBank.query.get({'id': card_id})
            if not bank_card:
                return Kits.rt_error("bank card not exist")

        # 轮询获取可用的银行卡信息
        # 构建查询条件：获取代理的可用银行卡，增加type条件，All、Deposit
        query_conditions = and_(
            AppAgentBankcard.status == 1,
            AppAgentBankcard.del_flag == 0,
            AppAgentBankcard.rc_bank_code == bank_code,
            AppAgentBankcard.channel_type == pay_channel,
            AppAgentBankcard.aid == agent_id,
            AppAgentBankcard.type.in_(['All', 'Deposit']),
            AppAgentBankcard.limit_current + amount < AppAgentBankcard.limit_balance,
        )
        # 查询所有符合条件的银行卡
        available_cards = AppAgentBankcard.query.filter(query_conditions).all()

        if not available_cards:
            logger.warning(f"没有可用的收款账号 - 用户ID: {g.user.id}, 用户名: {g.user.username}, 代理ID: {agent_id}, 银行代码: {bank_card.bank_code}, channelType:{pay_channel}")
            return jsonify({'code': 40404,
                            'message': "There is no available payment account at present. Please contact the customer service."})

        if pay_channel == "NFM2":
            # 轮询获取可用的银行卡信息
            try:
                # 智能轮询：从可用卡片中随机选择一张
                selected_card = random.choice(available_cards)
                # 记录选择的银行卡
                logger.info(f"分配收款账号 - 用户ID: {g.user.id}, 用户名: {g.user.username}, 收款账号: {selected_card.ACCOUNT}, 银行: {selected_card.rc_bank_code}")

                # 根据银行代码获取支付类型
                payment_type = selected_card.rc_bank_code
                receive_account = selected_card.rc_bank_account
                receive_account_name = selected_card.rc_bank_username

            except Exception as e:
                logger.error(f"获取银行卡信息失败 - 用户ID: {g.user.id}, 错误: {e}", exc_info=True)
                return jsonify(
                    {'code': 50001, 'message': "Failed to obtain the payment account. Please try again later."})
        else:
            # 支付通道为VIPPay/TCPay,由第三方指定收款账号
            payment_type = bank_code
            receive_account = ""
            receive_account_name = ""

        apply_id = Kits.generate_uuid()
        # 订单有效期
        ORDER_EXPIRE_MINUTES = 5
        apply = ChargeApply(id=apply_id, aid=g.user.aid, mb_id=g.user.id, mb_nickname=g.user.name, mb_username=g.user.username,
                            mb_bank_code=bank_code, mb_acc_name=acc_name, mb_acc_number=acc_number, remark=subject,
                            charge_way=charge_way, money=amount, remarks=memo, status=StatusLabelMap.New, expire_time=datetime.now() + timedelta(minutes=ORDER_EXPIRE_MINUTES))
        db.session.add(apply)
        # 先支持添加充值申请，再调用支付接口
        db.session.commit()
        logger.info(f"充值申请创建 - 申请ID: {apply_id}, 用户ID: {g.user.id}, 用户名: {g.user.username}, 金额: {amount}, 银行代码: {bank_code}, 过期时间: {ORDER_EXPIRE_MINUTES}分钟")

        # 使用PayOrderService创建充值订单
        result = pay_order_service.create_recharge_order(
            agent_id=agent_id,
            user_id=g.user.username,
            amount=amount,
            out_trade_no=apply_id,
            subject=subject or "充值",
            memo=memo or "",
            bank_code=bank_code,
            realname=acc_name,
            phone=acc_number,
            payment_type=payment_type,
            receive_account=receive_account,
            receive_account_name=receive_account_name,
            channelType=pay_channel or app.config['PAY_CHANNEL_TYPE'],
        )

        if not result['success']:
            apply.status = StatusLabelMap.Failed
            apply.fail_reason = result['message']
            db.session.commit()
            logger.warning(f"充值订单创建失败 - 申请ID: {apply_id}, 用户ID: {g.user.id}, 原因: {result['message']}")
            return Kits.rt_error("Failed to create order.")

        # 更新第三方订单信息
        resp_data = result['data']
        apply.pay_channel = pay_channel
        apply.receive_bank_code = payment_type
        apply.receive_account = receive_account if not receive_account else resp_data.get('receiveAccount')
        apply.receive_account_name = receive_account_name
        apply.out_trade_no = resp_data.get('tradeNo')
        apply.out_order_id = resp_data.get('tradeOrderId')
        apply.status = StatusLabelMap.Pending
        # 订单创建成功
        db.session.commit()
        logger.info(f"充值订单创建成功 - 申请ID: {apply_id}, 用户ID: {g.user.id}, 支付中心订单号: {resp_data.get('tradeNo')}, 支付通道: {pay_channel}, 状态: {StatusLabelMap.Pending}")

        return Kits.rt_data(resp_data)
    except Exception as e:
        logger.error(f"充值申请失败 - 用户ID: {g.user.id}, 错误: {e}", exc_info=True)

    return Kits.rt_error("System or Technical Error")


@charge_apply.route('/edit', methods=['POST'])
@auth.login_required
def edit_apply():
    """ edit_apply API Endpoint
        ---
        tags:
          - charge_apply
        parameters:
          - in: body
            name: body
            required: true
            description: charge_apply info to add
            schema:
              type: object
              required:
                - APPLY_ID
              properties:
                PICTURE:
                  type: string
                  description: the acc_number of the charge_apply
                  example: ""
                MONEY:
                  type: string
                  description: the MONEY of the charge_apply
                  example: ""
                REMARK:
                  type: string
                  description: the REMARK of the charge_apply
                  example: ""
        responses:
          500:
            description: System or Technical Error
          500:
            description: 文件格式不正确.
          200:
            description: add successful.
        """
    args = request.get_json()

    try:
        apply_id = args['APPLY_ID']
        apply = ChargeApply.query.filter_by(id=apply_id).one_or_none()
        if args['PICTURE']:
            picture = request.files.get('PICTURE')
            path = app.config['CHARGE_APPLY_PIC_DIR']
            # 图片后缀
            suffix = picture.filename.rsplit('.', 1)[1]
            if suffix not in ALLOWED_EXTENSIONS:
                response = jsonify({'message': "文件格式不正确"})
                response.status_code = 400
                return response

            # 删除原有图片
            if os.path.isfile(os.path.join(path, apply.picture)):
                os.remove(os.path.join(path, apply.picture))

            pic_name = "%s_%s.%s" % (g.user.USER_ID, int(round(time.time() * 1000)), suffix)
            picture.save(os.path.join(path, pic_name))

            args['PICTURE'] = pic_name
        # TODO 修改指定字段，修改前判断状态
        OrmUttil.set_field(apply, request.args)

        db.session.add(apply)
        db.session.commit()
        logger.info(f"充值申请修改成功 - 申请ID: {apply_id}, 用户ID: {g.user.id}")
        return jsonify({'message': "add successful."})
    except Exception as e:
        logger.error(f"充值申请修改失败 - 用户ID: {g.user.id}, 错误: {e}", exc_info=True)

    response = jsonify({'message': "System or Technical Error"})
    response.status_code = 500
    return response


@charge_apply.route('/delete', methods=['POST'])
@auth.login_required
def delete_apply():
    """ delete_apply API Endpoint
        ---
        tags:
          - charge_apply
        parameters:
          - in: body
            name: body
            required: true
            description: charge_apply info to add
            schema:
              type: object
              required:
                - APPLY_ID
              properties:
                PICTURE:
                  type: string
                  description: the acc_number of the charge_apply
                  example: ""
        responses:
          500:
            description: System or Technical Error
          500:
            description: 文件格式不正确.
          200:
            description: add successful.
        """
    args = request.get_json()

    try:
        apply_id = args['APPLY_ID']
        apply = ChargeApply.query.filter_by(id=apply_id).delete()

        # 删除原有图片
        if args['PICTURE']:
            path = app.config['CHARGE_APPLY_PIC_DIR']

            if os.path.isfile(os.path.join(path, apply.picture)):
                os.remove(os.path.join(path, apply.picture))
        db.session.commit()
        logger.info(f"充值申请删除成功 - 申请ID: {apply_id}, 用户ID: {g.user.id}")
        return jsonify({'message': "delete successful."})
    except Exception as e:
        logger.error(f"充值申请删除失败 - 用户ID: {g.user.id}, 错误: {e}", exc_info=True)

    response = jsonify({'message': "System or Technical Error"})
    response.status_code = 500
    return response


# 获取订单列表
@charge_apply.route('/get', methods=['GET'])
@auth.login_required
def get_apply_list():
    """ get_apply_list API Endpoint
        ---
        tags:
          - charge_apply
        parameters:
           - name: page
             in: query
             type: string
             required: true
             description: page of charge_apply
           - name: limit
             in: query
             type: integer
             description: limit of charge_apply
           - name: key_word
             in: query
             type: string
             description: key_word of charge_apply
           - name: start_time
             in: query
             type: string
             description: start_time of charge_apply
           - name: end_time
             in: query
             type: string
             description: end_time of charge_apply
        responses:
          200:
            description: { 'items': [...], 'total': 100 }
        """

    current_page = request.args.get('page', type=int, default=1)
    limit = request.args.get('limit', type=int, default=20)
    key_word = request.args.get('key_word')
    start_time = request.args.get('start_time')
    end_time = request.args.get('end_time')

    charge_list = ChargeApply.query.filter_by(mb_id=g.user.id)

    if key_word:
        charge_list = charge_list.filter(
            or_(ChargeApply.mb_id.like('%{}%'.format(key_word)), ChargeApply.mb_nickname.like('%{}%'.format(key_word)),
                ChargeApply.remark.like('%{}%'.format(key_word))))

    if start_time:
        start_time += ' 00:00:00'
        charge_list = charge_list.filter(ChargeApply.create_time >= start_time)

    if end_time:
        end_time += ' 23:59:59'
        charge_list = charge_list.filter(ChargeApply.create_time <= end_time)

    # LRC 剔除失败的订单
    charge_list = charge_list.filter(ChargeApply.status != 'Failed')

    total_amount = charge_list.with_entities(func.sum(ChargeApply.money)).scalar() or 0

    charge_list = charge_list.offset((current_page - 1) * limit).limit(limit).all()
    # 遍历处判断是否超时
    for apply in charge_list:
        if apply.status == StatusLabelMap.Pending and apply.expire_time < datetime.now():
            apply.status = 'Timeout'
            db.session.add(apply)
            db.session.commit()

    total = len(charge_list)

    return jsonify({
        'items': [u.to_dict() for u in charge_list],
        'total': total,
        'total_amount': float(total_amount)
    })
