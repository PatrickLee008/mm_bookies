import time
from sqlalchemy import or_, func, desc
from app_server import db, auth, app_opt, Redis
from app_server.model.AppMemberBalanceLogModel import AppMemberBalanceLog, TransactionType
from app_server.model.AppMemberBankModel import AppMemberBank
from app_server.model.ChargeApplyModel import ChargeApply, StatusMap, StatusLabelMap
from app_server.model.ChargeModel import Charge
from app_server.model.WithDrawModel import WithDraw
from app_server.model.WithDrawGroupModel import WithDrawGroup
from app_server.utils.Kits import Kits
from flask import g, request, jsonify, Blueprint
from app_server.model.MDictModel import MDict
import uuid
import datetime
from sqlalchemy import literal

withdraw = Blueprint('withdraw', __name__)


# 钱包
@withdraw.route('/get', methods=['GET'])
@auth.login_required
def get_wallet_list():
    """ get_wallet_list API Endpoint
        ---
        tags:
          - withdraw
        parameters:
           - name: page
             in: query
             type: string
             required: true
             description: page of get_wallet_list
           - name: limit
             in: query
             type: integer
             description: limit of get_wallet_list
           - name: key_word
             in: query
             type: string
             required: true
             description: key_word of get_wallet_list
           - name: start_time
             in: query
             type: string
             description: start_time of get_wallet_list
           - name: end_time
             in: query
             type: string
             description: end_time of get_wallet_list
           - name: status
             in: query
             type: string
             description: status of get_wallet_list
           - name: type
             in: query
             type: string
             description: type of get_wallet_list 0 only withdraw list   1 only charge list   not set or other value means both
        responses:
          200:
            description: { 'items': [...], 'total': 100}
        """

    """
    同时查询充值记录（ChargeApply）与提现记录（WithDraw）
    """

    current_page = request.args.get('page', type=int, default=1)
    limit = request.args.get('limit', type=int, default=20)

    key_word = request.args.get('key_word')
    start_time = request.args.get('start_time')
    end_time = request.args.get('end_time')
    status = request.args.get('status')
    type = request.args.get('type')
    user_id = g.user.id

    # 默认空查询
    union_query = None

    # 如果 type 是字符串 '0'，仅查提现记录
    if type == "Withdraw":
        print(1)
        union_query = db.session.query(
            WithDraw.id.label("id"),
            WithDraw.amount.label("amount"),
            WithDraw.create_time.label("create_time"),
            literal("Withdraw").label("type"),
            WithDraw.status.label("status"),
            WithDraw.remarks.label("remarks"),
            WithDraw.mb_bank_code.label("rc_bank_code"),
        ).filter(WithDraw.mb_id == user_id)

        if key_word:
            union_query = union_query.filter(WithDraw.mb_nickname.like(f"%{key_word}%"))

        if start_time:
            union_query = union_query.filter(WithDraw.create_time >= start_time + " 00:00:00")

        if end_time:
            union_query = union_query.filter(WithDraw.create_time <= end_time + " 23:59:59")

        if status is not None:
            union_query = union_query.filter(WithDraw.status == status)

    # 如果 type 是字符串 '1'，仅查充值记录
    elif type == "Deposit":
        union_query = db.session.query(
            Charge.id.label("id"),
            Charge.amount.label("amount"),
            Charge.create_time.label("create_time"),
            literal("Deposit").label("type"),
            Charge.status.label("status"),
            Charge.remarks.label("remarks"),
            Charge.mb_bank_code.label("rc_bank_code"),
        ).filter(Charge.mb_id == user_id)

        if key_word:
            union_query = union_query.filter(Charge.mb_nickname.like(f"%{key_word}%"))

        if start_time:
            union_query = union_query.filter(Charge.create_time >= start_time + " 00:00:00")

        if end_time:
            union_query = union_query.filter(Charge.create_time <= end_time + " 23:59:59")

        if status is not None:  # TODO 修改为对应的状态值
            union_query = union_query.filter(Charge.status == status)

    # 查询全部
    else:
        withdraw_query = db.session.query(
            WithDraw.id.label("id"),
            WithDraw.amount.label("amount"),
            WithDraw.create_time.label("create_time"),
            literal("Withdraw").label("type"),
            WithDraw.status.label("status"),
            WithDraw.remarks.label("remarks"),
            WithDraw.mb_bank_code.label("rc_bank_code"),
        ).filter(WithDraw.mb_id == user_id)

        charge_query = db.session.query(
            Charge.id.label("id"),
            Charge.amount.label("amount"),
            Charge.create_time.label("create_time"),
            literal("Deposit").label("type"),
            Charge.status.label("status"),
            Charge.remarks.label("remarks"),
            Charge.mb_bank_code.label("rc_bank_code"),
        ).filter(Charge.mb_id == user_id)

        if key_word:
            withdraw_query = withdraw_query.filter(WithDraw.mb_nickname.like(f"%{key_word}%"))
            charge_query = charge_query.filter(Charge.mb_nickname.like(f"%{key_word}%"))

        if start_time:
            withdraw_query = withdraw_query.filter(WithDraw.create_time >= start_time + " 00:00:00")
            charge_query = charge_query.filter(Charge.create_time >= start_time + " 00:00:00")

        if end_time:
            withdraw_query = withdraw_query.filter(WithDraw.create_time <= end_time + " 23:59:59")
            charge_query = charge_query.filter(Charge.create_time <= end_time + " 23:59:59")

        if status is not None:
            withdraw_query = withdraw_query.filter(WithDraw.status == status)
            charge_query = charge_query.filter(Charge.status == status)

        union_query = withdraw_query.union_all(charge_query)

    # 如果 union_query 仍为 None，返回空数据
    if union_query is None:
        return jsonify({
            'items': [],
            'total': 0,
        })

    # 排序和分页
    union_query = union_query.order_by(desc("create_time"))
    total = union_query.count()
    records = union_query.offset((current_page - 1) * limit).limit(limit).all()

    items = []
    for r in records:
        items.append({
            "id": r.id,
            "amount": float(r.amount),
            "type": r.type,
            "create_time": r.create_time.strftime("%Y-%m-%d %H:%M:%S"),
            "status": str(r.status),
            "bank_code": r.rc_bank_code,
            "remarks": r.remarks,
        })

    return jsonify({
        'items': items,
        'total': total,
    })


# 获取订单列表
@withdraw.route('/get', methods=['GET'])
@auth.login_required
def get_withdraw_list():
    """ get_withdraw_list API Endpoint
            ---
            tags:
              - withdraw
            parameters:
               - name: current_page
                 in: query
                 type: string
                 required: true
                 description: current_page of withdraw_list
               - name: limit
                 in: query
                 type: integer
                 description: limit of withdraw_list
               - name: key_word
                 in: query
                 type: string
                 required: true
                 description: key_word of withdraw_list
               - name: start_time
                 in: query
                 type: string
                 description: start_time of withdraw_list
               - name: end_time
                 in: query
                 type: string
                 description: end_time of withdraw_list
               - name: is_pay
                 in: query
                 type: string
                 description: status of withdraw_list 0 not paid  1 paid, not set or other value means all
            responses:
              200:
                description: { 'items': [...], 'total': 100, 'total_amount': 1000 }
            """

    current_page = request.args.get('page', type=int, default=1)
    limit = request.args.get('limit', type=int, default=20)

    withdraw_list = WithDraw.query.filter_by(id=g.user.id).order_by(WithDraw.create_time.desc())

    key_word = request.args.get('key_word')
    start_time = request.args.get('start_time')
    end_time = request.args.get('end_time')
    is_pay = request.args.get('is_pay')

    if key_word:
        withdraw_list = withdraw_list.filter(
            or_(WithDraw.id.like('%{}%'.format(key_word)), WithDraw.mb_nickname.like('%{}%'.format(key_word))))

    if is_pay:
        withdraw_list = withdraw_list.filter(WithDraw.status == is_pay)

    if start_time:
        start_time += " 00:00:00"
        withdraw_list = withdraw_list.filter(WithDraw.create_time >= start_time)

    if end_time:
        end_time += " 23:59:59"
        withdraw_list = withdraw_list.filter(WithDraw.create_time <= end_time)

    total_amount = withdraw_list.with_entities(func.sum(WithDraw.amount)).scalar() or 0

    total = withdraw_list.count()

    withdraw_list = withdraw_list.offset((current_page - 1) * limit).limit(limit).all()

    # 修改提现组名称
    all_group_names = WithDrawGroup.query.all()
    name_dict = {u.id: u.GROUP_NAME for u in all_group_names}
    print(name_dict)
    items = []
    for wd in withdraw_list:
        wd = wd.to_dict()
        if wd['Work_Group'] in name_dict:
            wd['Work_Group'] = name_dict[wd['Work_Group']]
        items.append(wd)

    return jsonify({
        'items': items,
        'total': total,
        'total_amount': total_amount
    })


@withdraw.route('/apply', methods=['POST'])
@auth.login_required
def apply_withdraw():
    """ apply_withdraw API Endpoint
        ---
        tags:
          - withdraw
        parameters:
          - in: body
            name: body
            required: true
            description: withdraw to apply
            schema:
              type: object
              required:
                - money
                - card_id
              properties:
                amount:
                  type: string
                  description: the money of the withdraw
                ALL:
                  type: string
                  description: the money of the withdraw 0 means not all, 1 means all
                CARD_id:
                  type: string
                  description: the card_id of the user bankcard
                  example: "132"
        responses:
          500:
            description: System or Technical Error.
          200:
            description: edit successful.
        """
    args = request.get_json()
    money = args.get('money')
    withdraw_all = args.get('ALL')
    card_id = args.get('card_id')
    try:
        user = g.user
        main_id = user.id
        # del user
        from app_server.model.AppMemberModel import AppMember
        db.session.commit()

        # user = AppMember.query.filter_by(id=main_id).with_for_update(of=AppMember).first()

        repeat_user_key = "withdraw_limit_%s" % main_id
        if repeat_user_key and Redis.exists(repeat_user_key):
            response = jsonify({'message': "withdraw repeat"})
            response.status_code = 409
            return response
        Redis.setex(repeat_user_key, 10, 'processed')

        print("what have we got:", user.money)

        before_amount = float(user.money)
        if withdraw_all:
            money = user.money
        if before_amount < float(money):
            response = jsonify({'message': "money_not_enough"})
            response.status_code = 400
            return response
        withdraw_min_limit = MDict.query.filter_by(MDICT_ID="23").first().CONTENT
        if float(money) < float(withdraw_min_limit):
            response = jsonify({'message': "withdraw_min_limit"})
            response.status_code = 400
            return response

        spare_groups = WithDrawGroup.query.filter(WithDrawGroup.HANDLE_ON).all()
        if not len(spare_groups):
            response = jsonify({'message': "Too many players withdrawing cash, please try again later."})
            response.status_code = 429
            return response
            response.status_code = 400
            return response
        spare_groups = [u.ID for u in spare_groups]
        print("we got spare groups:", spare_groups)

        now = datetime.datetime.now()
        key_date = now.date()
        # if now.hour < 12:
        #     key_date -= datetime.timedelta(days=1)

        after_amount = before_amount - float(money)
        user.money = after_amount
        user.money_lock = float(user.money_lock) + float(money)
        print("app got to write:", before_amount, after_amount)

        date_key = "withdraw_code_%s" % key_date
        if not Redis.exists(date_key):
            Redis.set(date_key, 0, ex=24 * 60 * 60)

        Redis.incr(date_key)
        withdraw_code = "%05d" % int(Redis.get(date_key))

        group_key = "user_withdraw%s" % user.id
        group_value = Redis.get(group_key)
        if group_value and int(group_value) in spare_groups:
            print("user", user.id, "got group:", group_value, "expiring:", Redis.ttl(group_key))
            next_group_id = int(group_value)
        else:
            cur_work_group = MDict.query.filter_by(MDICT_ID='28').with_for_update().first()
            cur_group_id = int(cur_work_group.CONTENT)
            next_group_id = spare_groups[0]
            for gr in spare_groups:
                if gr > cur_group_id:
                    next_group_id = gr
                    break
            cur_work_group.CONTENT = next_group_id
        # 处理达到上限
        next_group = WithDrawGroup.query.filter(WithDrawGroup.ID == next_group_id).with_for_update().first()
        next_group.NOW_HANDLE += 1
        if next_group.NOW_HANDLE >= next_group.MAX_HANDLE:
            next_group.HANDLE_ON = False

        # 组过期时间
        expiration = int(MDict.query.filter_by(MDICT_ID='29').with_for_update().first().CONTENT) * 60
        print("user", user.id, "got no group, write:", next_group_id, expiration, "at:", datetime.datetime.now())
        Redis.set("user_withdraw%s" % user.id, next_group_id, expiration)

        bank_card = AppMemberBank.query.filter_by(id=card_id).first()
        the_withdraw = WithDraw(id=Kits.generate_uuid(), withdraw_code=withdraw_code, aid=user.aid, mb_id=user.id,
                                mb_username=user.username,
                                mb_nickname=bank_card.acc_name, amount=money, status=StatusLabelMap.Pending,
                                withdraw_type="USER", before_amount=before_amount, after_amount=after_amount,
                                mb_acc_name=bank_card.acc_name,
                                work_group_id=next_group_id, mb_bank_code=bank_card.bank_code,
                                mb_acc_number=bank_card.acc_number)
        print("user withdrawing:", money, user.id, before_amount, after_amount)
        # if card_id:
        #     bank_card = BankCard.query.get({'id': card_id})
        #     the_withdraw.CARD_NUM = bank_card.CARD_NUM
        #     the_withdraw.rc_bank_code = bank_card.rc_bank_code
        # balance_log = AppMemberBalanceLog(id=Kits.generate_uuid(), sn=Kits.generate_uuid(), type="Withdraw",
        #                                   aid=user.aid, mb_id=user.id, mb_username=user.username, mb_rid=user.rid,
        #                                   money=money,
        #                                   start_balance=before_amount, end_balance=after_amount, source="System",
        #                                   target="Ewallet")

        db.session.add(the_withdraw)
        # db.session.add(balance_log)
        # print(balance_log.id)
        db.session.commit()
        app_opt.send({
            "user_account": user.id,
            "user_name": user.username,
            "type": TransactionType.Withdraw,
            "type_sub": "MANUAL",
            "before_amount": float(before_amount),
            "after_amount": float(after_amount),
            "amount": float(money),
            "source_id": the_withdraw.id,

            "aid": user.aid,
            "create_by_id": user.id,
            "mb_rid": user.rid,
            "source": "System",
            "target": "Ewallet",
            "source_status": StatusMap.Pending
        })
        return jsonify({'message': "add successful."})
    except Exception as e:
        print("add_user_withdraw error", e)
        response = jsonify({'message': "System or Technical Error."})
        response.status_code = 500
        return response
    response.status_code = 400
    return response
