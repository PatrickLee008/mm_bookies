import traceback

from app_server import db, auth, app_opt, Redis
from flask import g, request, jsonify, Blueprint

from app_server.model.AppMemberBalanceLogModel import TransactionType
from app_server.model.MDictModel import MDict
from app_server.model.MatchModel import Match, MatchAttr, VipMatchAttr
from app_server.model import GameType
from app_server.model.OrderModel import Order, OrderType, BetType
from app_server.model.OrderHistoryModel import OrderHistory
from app_server.model.AppBetOrderModel import AppBetOrder, BetStatus, PayWallet
from app_server.utils.Kits import Kits
from sqlalchemy import or_, func, and_
from app_server.utils.sphinxapi import *
import ipaddress
import datetime
import time
import uuid

order = Blueprint('order', __name__)


@order.route('/check_odds', methods=['POST'])
@auth.login_required
def check_odds():
    """
        @@@
        #### Args:
                attrs: {attr_id:{"bet_type": 1, "DRAW_ODDS": 2.3, ...}, ...}
        #### Returns::
                {'code': 200, 'message': "check success!", items: {attr_id:odds, ...}}
                {'code': 500, 'message': "System or Technical Error"}
    """
    args = request.get_json()
    attrs = args.get('attrs')
    print('attrs:', attrs)
    try:
        all_attr = MatchAttr.query.filter(MatchAttr.MATCH_ATTR_ID.in_(attrs)).all()
        change_list = []
        for attr in all_attr:
            remote_attr = attrs[attr.MATCH_ATTR_ID]
            if attr.DRAW_BUNKO != remote_attr['DRAW_BUNKO'] or attr.DRAW_ODDS != remote_attr[
                'DRAW_ODDS'] or attr.LOSE_BALL_NUM != remote_attr['LOSE_BALL_NUM']:
                change_list.append(attr)

        return jsonify({'message': "check success!", 'items': [u.to_dict() for u in change_list]})

    except Exception as e:
        print("check_odds error", e)
        response = jsonify({'message': "Invalid or Expired Odds"})
        response.status_code = 400
        return response


@order.route('/single_bet', methods=['POST'])
@auth.login_required
def single_bet():
    """ single_bet API Endpoint
        ---
        tags:
          - order
        parameters:
          - in: body
            name: body
            required: true
            description: single_bet to add
            schema:
              type: object
              required:
                - bets
                - match_id
              properties:
                bets:
                  type: object
                  properties:
                    amount:
                        type: integer
                        description: the amount of the bet
                        example: 100
                    betType:
                        type: integer
                        description: the bet type of the bet
                        example: 1 # 1.host/over 2.guest/under 3.draw
                    attrType:
                        type: integer
                        description: the attr_type of the bet
                        example: 1 # 1.single hdp 2.single o/u 3.correct score 4.mix hdp 5.mix o/u 6.single even/odd 7.mix even/odd 8.digital 9.digital_3d 10.single win/lose 11. mix win/lose
                  description: the bets of the order
                match_id:
                  type: string
                  description: the match_id of the order
                  example: ""
                coupon_id:
                  type: string
                  description: the member coupon id if using coupon
                  example: ""
        responses:
          500:
            description: Bet failed, no order.
          500:
            description: Bet failed.
          500:
            description: Bet failed.
          500:
            description: Bet failed.
          200:
            description: bet success!
        """
    args = request.get_json()
    bets = args.get('bets')
    coupon_id = args.get('coupon_id')  # 获取优惠券ID
    use_promotion_wallet = args.get('use_promotion_wallet', False)  # 是否使用优惠钱包

    getter_key = "order_bet_%s_%s" % (g.user.id, str(args))
    if not Redis.exists(getter_key):
        Redis.set(getter_key, 0, ex=2)
    else:
        response = jsonify({'message': "same bet request in very short time"})
        response.status_code = 429
        return response

    try:
        total_amount = 0
        coupon_discount = 0  # 优惠券折扣金额
        member_coupon = None  # 会员优惠券对象

        user = g.user
        main_id = user.id
        del user
        from app_server.model.AppMemberModel import AppMember
        from app_server.model.MAppMemberCouponModel import MAppMemberCoupon
        from app_server.model.MAppCouponModel import MAppCoupon
        db.session.commit()
        user = AppMember.query.filter_by(id=main_id).with_for_update(of=AppMember).first()

        # 先行统计总下注额
        for bet in bets:
            total_amount += float(bet['amount'])

        # 如果有优惠券ID，进行优惠券验证
        if coupon_id:
            # 1. 查询会员优惠券记录
            member_coupon = MAppMemberCoupon.query.filter_by(
                id=coupon_id,
                mb_id=user.id,
                del_flag=0
            ).with_for_update().first()

            if not member_coupon:
                db.session.rollback()
                response = jsonify({'message': "Coupon not found or does not belong to you"})
                response.status_code = 400
                return response

            # 2. 检查优惠券是否已使用
            if member_coupon.status != 'Unused':
                db.session.rollback()
                response = jsonify({'message': "Coupon has already been used or expired"})
                response.status_code = 400
                return response

            # 3. 检查优惠券是否过期
            if member_coupon.expire_time and member_coupon.expire_time < datetime.datetime.now():
                db.session.rollback()
                response = jsonify({'message': "Coupon has expired"})
                response.status_code = 400
                return response

            # 4. 查询优惠券主表信息
            coupon_master = MAppCoupon.query.filter_by(
                id=member_coupon.p_id,
                del_flag=0
            ).first()

            if not coupon_master:
                db.session.rollback()
                response = jsonify({'message': "Coupon configuration not found"})
                response.status_code = 400
                return response

            # 5. 检查是否达到最低投注要求
            if coupon_master.min_bet_amount_required and total_amount < float(coupon_master.min_bet_amount_required):
                db.session.rollback()
                response = jsonify({
                    'message': f"Minimum bet amount required: {coupon_master.min_bet_amount_required}"
                })
                response.status_code = 400
                return response

            # 6. 检查总使用次数限制（p_lmu_j_pd）
            if coupon_master.p_lmu_j_pd and coupon_master.p_lmu_j_pd > 0:
                # 统计该用户使用该优惠券的总次数
                total_used_count = MAppMemberCoupon.query.filter(
                    MAppMemberCoupon.mb_id == user.id,
                    MAppMemberCoupon.p_id == coupon_master.id,
                    MAppMemberCoupon.status == 'Used',
                    MAppMemberCoupon.del_flag == 0
                ).count()

                if total_used_count >= coupon_master.p_lmu_j_pd:
                    db.session.rollback()
                    response = jsonify({
                        'message': f"Coupon usage limit reached: {coupon_master.p_lmu_j_pd}"
                    })
                    response.status_code = 400
                    return response

            # 7. 计算优惠金额（从member_coupon.money获取）
            if member_coupon.money and float(member_coupon.money) > 0:
                coupon_discount = float(member_coupon.money)
                # 优惠金额不能超过下注金额
                if coupon_discount > total_amount:
                    coupon_discount = total_amount

        # 计算实际需要扣除的金额（下注金额 - 优惠券折扣）
        actual_deduction = total_amount - coupon_discount

        # 检查余额是否足够（根据使用的钱包类型）
        if use_promotion_wallet:
            # 使用优惠钱包
            promotion_balance = float(user.money_promotion) if user.money_promotion else 0
            if promotion_balance < actual_deduction:
                response = jsonify({'message': "Sorry, your promotion wallet balance is not enough for this bet"
                                    })
                response.status_code = 400
                return response
        else:
            # 使用主钱包
            if float(user.money) < actual_deduction:
                response = jsonify({'message': "Sorry, your current balance is not enough for this bet"
                                    })
                response.status_code = 400
                return response
        single_limit = MDict.query.filter_by(MDICT_ID="888").one()
        single_min = single_limit.CODE
        single_max = single_limit.CONTENT

        for bet in bets:
            if float(bet['amount']) < float(single_min):
                response = jsonify({'message': "single_min"})
                response.status_code = 400
                return response
            if float(bet['amount']) > float(single_max):
                response = jsonify({'message': "single_max"})
                response.status_code = 400
                return response
            match = Match.query.filter_by(MATCH_ID=bet['matchId']).one_or_none()
            if not match:
                db.session.rollback()
                response = jsonify({'message': "Bet failed: match not exist."})
                response.status_code = 400
                return response
            if match.CLOSING_STATE == "1":
                db.session.rollback()
                response = jsonify({'message': "Bet failed: match not exist."})
                response.status_code = 400
                return response
            if match.CLOSING_TIME <= datetime.datetime.now():
                db.session.rollback()
                response = jsonify({'message': "Events already started or closed"})
                response.status_code = 400
                return response

            order_type = bet['attrType']
            attrs = MatchAttr.query.filter_by(MATCH_ID=bet['matchId']).all()
            vip_attrs = VipMatchAttr.query.filter_by(MATCH_ID=bet['matchId']).all()
            vip_attr_dict = {attr.MATCH_ATTR_TYPE: attr for attr in vip_attrs}
            attr_dict = {attr.MATCH_ATTR_TYPE: attr for attr in attrs}

            attr = None
            if order_type in attr_dict:
                attr = attr_dict[order_type]
            # if user.IS_VIP and order_type in vip_attr_dict:
            #     attr = vip_attr_dict[order_type]

            if not attr:
                db.session.rollback()
                response = jsonify({'message': "Invalid Bet Type"})
                response.status_code = 400
                return response

            #   总限额
            single_order_total_limit = MDict.query.filter_by(MDICT_ID="889").one().CONTENT
            match_total_unsettled = Order.query.filter(
                and_(Order.USER_ID == user.id, Order.ORDER_TYPE == order_type, Order.STATUS == "1",
                     Order.MATCH_ID == bet['matchId'])).with_entities(func.sum(Order.BET_MONEY)).scalar() or 0
            print("------", order_type, match_total_unsettled, single_order_total_limit)
            if float(match_total_unsettled) + total_amount > int(single_order_total_limit):
                db.session.rollback()
                response = jsonify({'message': "Bet failed: this match has reached the order limit."})
                response.status_code = 400
                return response

            order_id = "%s-%s" % (user.username, round(time.time() * 1000))
            new_order = Order(ID=str(uuid.uuid4()).replace("-", ""), ORDER_ID=order_id, USER_ID=user.id,
                              USER_NAME=user.username,
                              MATCH_ID=bet['matchId'], ORDER_TYPE=order_type, BET_TYPE=bet['betType'],
                              ORDER_DESC="%s || %s" % (match.HOST_TEAM, match.GUEST_TEAM),
                              BET_MONEY=bet['amount'], order_type_desc="暂无", STATUS="1", IS_MIX="0", IS_WIN="2",
                              BONUS="0", LOSE_TEAM=attr.LOSE_TEAM,
                              BET_ODDS=attr.ODDS, LEAGUE=match.LEAGUE,
                              DRAW_BUNKO=0 if attr.DRAW_BUNKO == '' else attr.DRAW_BUNKO, DRAW_ODDS=attr.DRAW_ODDS,
                              LOSE_BALL_NUM=0 if attr.LOSE_BALL_NUM == '' else attr.LOSE_BALL_NUM,
                              MATCH_TIME=match.MATCH_MD_TIME, IP=int(ipaddress.IPv4Address(request.remote_addr)))

            new_order.BET_TYPE = bet['betType']

            if user.aid:
                new_order.AGENT_CODE = user.aid
            if order_type == "2":
                new_order.BALL_TYPE = bet['betType']

            if g.user.aid:
                new_order.AGENT_CODE = g.user.aid

            # 单双赔率另外赋值
            if order_type == '6':
                new_order.BET_ODDS = attr.ODDS if bet['betType'] == 1 else attr.ODDS_GUEST

            # 独赢赔率另外赋值
            if order_type == '10':
                print("got to set the odds:", bet['betType'])
                new_order.BET_ODDS = attr.ODDS if bet['betType'] == 1 else attr.ODDS_GUEST
                if bet['betType'] == 3:
                    new_order.BET_ODDS = attr.DRAW_ODDS
                print("set result", new_order.BET_ODDS)

            # 根据使用的钱包类型扣除余额
            if use_promotion_wallet:
                # 从优惠钱包扣除
                before_amount = float(user.money_promotion) if user.money_promotion else 0
                user.money_promotion = before_amount - actual_deduction
                after_amount = before_amount - actual_deduction
                pay_wallet_type = PayWallet.Promotion
            else:
                # 从主钱包扣除
                before_amount = float(user.money)
                user.money = before_amount - actual_deduction
                after_amount = before_amount - actual_deduction
                pay_wallet_type = PayWallet.Money

            # 复制订单到主订单表
            new_order.bet_status = BetStatus.Pending
            new_order.pay_wallet = pay_wallet_type
            # bet_order = AppBetOrder.create_from_order(new_order, bet_type_sub=f'{order_type}:{bet["betType"]}')
            bet_order = AppBetOrder.create_from_order(new_order, match)

            # 如果使用了优惠券，设置相关字段
            if member_coupon:
                bet_order.in_promotion = True
                bet_order.pro_id = member_coupon.id
                bet_order.remarks = f"Used coupon: {member_coupon.p_name}, discount: {coupon_discount}"

            db.session.add(bet_order)
            new_order.main_order_id = bet_order.id

            db.session.add(new_order)

            # 如果使用了优惠券，标记为已使用并设置link_id
            if member_coupon:
                member_coupon.status = 'Used'
                member_coupon.use_time = datetime.datetime.now()
                member_coupon.link_id = bet_order.id  # 设置link_id为订单ID
                db.session.add(member_coupon)

            db.session.commit()
            # print('after_money_commit', float(user.money))  # 输出 after_money_commit：321456.1125

            # 构建交易类型描述
            type_sub_parts = []
            if use_promotion_wallet:
                type_sub_parts.append("promotion_wallet")
            else:
                type_sub_parts.append("football")

            if coupon_discount > 0:
                type_sub_parts.append(f"coupon_{coupon_discount}")

            type_sub = "_".join(type_sub_parts)

            app_opt.send({
                "user_account": user.id,
                "user_name": user.username,
                "type": TransactionType.Order,
                "type_sub": type_sub,
                "before_amount": float(before_amount),
                "after_amount": float(after_amount),
                "amount": float(actual_deduction),
                "source_id": order_id,
                "bet_id": order_id,
                "aid": g.user.aid,
                "match_id": bet['matchId']
            })

        return jsonify({'message': "Bet success!"})

    except Exception as e:
        print("single bet error", e)
        traceback.print_exc()
        db.session.rollback()
        response = jsonify({'message': "System or Technical Error"})
        response.status_code = 400
        return response


@order.route('/mix_bet', methods=['POST'])
@auth.login_required
def mix_bet():
    """ mix_bet API Endpoint
        ---
        tags:
          - order
        parameters:
          - in: body
            name: body
            required: true
            description: single_bet to add
            schema:
              type: object
              required:
                - bets
                - match_id
              properties:
                bets:
                  type: object
                  properties:
                    amount:
                        type: integer
                        description: the amount of the bet
                        example: 100
                    betType:
                        type: integer
                        description: the bet type of the bet
                        example: 1 # 1.host/over 2.guest/under 3.draw
                    attrType:
                        type: integer
                        description: the attr_type of the bet
                        example: 1 # 1.single hdp 2.single o/u 3.correct score 4.mix hdp 5.mix o/u 6.single even/odd 7.mix even/odd 8.digital 9.digital_3d 10.single win/lose 11. mix win/lose
                  description: the bets of the order
                match_id:
                  type: string
                  description: the match_id of the order
                  example: ""
        responses:
          500:
            description: Bet failed, no order.
          500:
            description: Bet failed.
          500:
            description: Bet failed.
          500:
            description: Bet failed.
          200:
            description: bet success!
        """
    args = request.get_json()
    bets = args.get('bets')
    # getter_key = "order_bet_%s_%s" % (g.user.id, str(args))

    getter_key = "order_bet_%s" % (g.user.id)
    success = Redis.setnx(getter_key, 1)  # SETNX命令
    if not success:
        response = jsonify({'message': "same bet request in very short time"})
        response.status_code = 429
        return response

    # 设置键的过期时间
    Redis.expire(getter_key, 2)

    # if not Redis.exists(getter_key):
    #     Redis.set(getter_key, 0, ex=2)
    # else:
    #     return jsonify({'code': 50003, "message": "same bet request in very short time"})

    order_id = int(round(time.time() * 1000))
    # 直接给出总金额
    total_amount = float(args.get('totalAmount'))
    print("about to bet:", order_id, bets)

    try:
        mix_limit = MDict.query.filter_by(MDICT_ID="999").one()
        bet_count_limit = MDict.query.filter_by(MDICT_ID="13").one()
        mix_min = mix_limit.CODE
        mix_max = mix_limit.CONTENT
        order_id = "%s-%s" % (g.user.username, round(time.time() * 1000))

        user = g.user
        main_id = user.id
        del user
        from app_server.model.AppMemberModel import AppMember
        db.session.commit()
        user = AppMember.query.filter_by(id=main_id).with_for_update(of=AppMember).first()

        if total_amount < float(mix_min):
            response = jsonify({'message': "mix_min"
                                })
            response.status_code = 400
            return response
        if total_amount > float(mix_max):
            response = jsonify({'message': "mix_max"
                                })
            response.status_code = 400
            return response
        # match_ids = {bet['matchId'] for bet in bets}

        # 单场比赛混合下注判断
        # mix_orders = Order.query.with_entities(Order., Order.ORDER_ID).filter(Order.IS_MIX == "1", Order.STATUS == "1", Order.MATCH_ID.in_(match_ids), Order.USER_ID == user.id)

        match_to_orders = {}
        new_orders = []

        if len(bets) < int(bet_count_limit.CODE):
            response = jsonify({
                'message': "at_least_2_game",
                'limit': bet_count_limit.CODE,
            })
            response.status_code = 400
            return response
        if len(bets) > int(bet_count_limit.CONTENT):
            response = jsonify({
                'message': "at_most_12_game",
                'limit': bet_count_limit.CONTENT,
            })
            response.status_code = 400
            return response

        if len(set([bet['matchId'] for bet in bets])) < len(bets):
            response = jsonify({'message': "Duplicate Bet detected"})
            response.status_code = 400
            return response

        mix_type_dict = {}

        for bet in bets:
            match_id = bet['matchId']
            order_type = bet['attrType']

            already_bet = mix_type_dict.get(match_id)
            if not already_bet:
                mix_type_dict[match_id] = already_bet = set()

            if order_type in already_bet:
                print(">>>>illegal bet found:", g.user.id, datetime.datetime.now(), args, request.remote_addr)
                response = jsonify({'message': "Bet failed: bet data illegal."})
                response.status_code = 400
                return response

            mix_type_dict[match_id].add(order_type)

            match = Match.query.filter_by(MATCH_ID=bet['matchId']).one_or_none()
            if not match:
                db.session.rollback()
                response = jsonify({'message': "Bet failed: match not exist."})
                response.status_code = 400
                return response
            if match.CLOSING_STATE == "1":
                db.session.rollback()
                response = jsonify({'message': "Bet failed: game has closed."})
                response.status_code = 400
                return response
            if match.CLOSING_TIME <= datetime.datetime.now():
                db.session.rollback()
                response = jsonify({'message': "Events already started or closed"})
                response.status_code = 400
                return response

            # 混合单31限制
            # if user.HIGHER_LIMIT:
            #     mix_total_match_limit = MDict.query.filter_by(MDICT_ID="33").one()
            # else:
            #     mix_total_match_limit = MDict.query.filter_by(MDICT_ID="31").one()
            mix_total_match_limit = MDict.query.filter_by(MDICT_ID="31").one()

            link_orders = Order.query.filter(Order.MATCH_ID == bet['matchId'], Order.USER_ID == user.id,
                                             Order.STATUS == 1, Order.IS_MIX == "1").group_by(Order.ORDER_ID).all()
            match_already_bet = 0
            for link_order in link_orders:
                match_already_bet += int(link_order.BET_MONEY)

            if match_already_bet + total_amount > float(mix_total_match_limit.CONTENT):
                response = jsonify({'message': "Bet failed: this match has reached the order limit."})
                response.status_code = 400
                return response

            attrs = MatchAttr.query.filter_by(MATCH_ID=bet['matchId']).all()
            vip_attrs = VipMatchAttr.query.filter_by(MATCH_ID=bet['matchId']).all()
            vip_attr_dict = {attr.MATCH_ATTR_TYPE: attr for attr in vip_attrs}
            attr_dict = {attr.MATCH_ATTR_TYPE: attr for attr in attrs}

            attr = None
            if order_type in attr_dict:
                attr = attr_dict[order_type]
            # if user.IS_VIP and order_type in vip_attr_dict:
            #     attr = vip_attr_dict[order_type]

            if not attr:
                db.session.rollback()
                response = jsonify({'message': "Invalid Bet Type"})
                response.status_code = 400
                return response

            new_order = Order(ID=str(uuid.uuid4()).replace("-", ""), ORDER_ID=order_id, USER_ID=user.id,
                              USER_NAME=user.username, BET_TYPE=bet['betType'],
                              MATCH_ID=bet['matchId'], ORDER_TYPE=order_type,
                              ORDER_DESC="%s || %s" % (match.HOST_TEAM, match.GUEST_TEAM),
                              BET_MONEY=total_amount, order_type_desc="%s串1" % len(bets), STATUS="1", IS_MIX="1",
                              IS_WIN="2", LOSE_TEAM=attr.LOSE_TEAM,
                              BONUS="0", MATCH_TIME=match.MATCH_MD_TIME, LEAGUE=match.LEAGUE,
                              BET_ODDS=attr.ODDS, DRAW_BUNKO=attr.DRAW_BUNKO, DRAW_ODDS=attr.DRAW_ODDS,
                              LOSE_BALL_NUM=attr.LOSE_BALL_NUM, IP=int(ipaddress.IPv4Address(request.remote_addr)))
            print("mix bet ordering:", order_type, bet['betType'])
            new_order.BET_TYPE = bet['betType']
            if user.aid:
                new_order.AGENT_CODE = user.aid
            if order_type == "5":
                new_order.BALL_TYPE = bet['betType']
            if g.user.aid:
                new_order.AGENT_CODE = g.user.aid

            # 单双赔率另外赋值
            if order_type == '7':
                new_order.BET_ODDS = attr.ODDS if bet['betType'] == '1' else attr.ODDS_GUEST

            new_orders.append(new_order)
            match_to_orders[bet['matchId']] = new_order
        if float(user.money) < total_amount:
            db.session.rollback()
            response = jsonify({'message': "Sorry, your current balance is not enough for this bet"})
            response.status_code = 400
            return response

        # 统计同类混合单的注额 进行限制
        # if user.HIGHER_LIMIT:
        #     mix_order_total_limit = MDict.query.filter_by(MDICT_ID="32").one()
        # else:
        #     mix_order_total_limit = MDict.query.filter_by(MDICT_ID="30").one()
        mix_order_total_limit = MDict.query.filter_by(MDICT_ID="30").one()
        mix_already = Order.query.with_entities(func.count(Order.ID), Order.ORDER_ID).filter(
            Order.USER_ID == user.id, Order.STATUS == 1, Order.IS_MIX == "1").group_by(Order.ORDER_ID).all()
        same_order_ids = []
        for length, o_id in mix_already:
            if length != len(bets):
                continue
            same_order_ids.append(o_id)

        print("got same:", same_order_ids)
        count_amount = 0
        for o_id in same_order_ids:
            orders = Order.query.filter_by(ORDER_ID=o_id).all()
            is_same = True
            for o in orders:
                if o.MATCH_ID not in match_to_orders:
                    is_same = False
                    break
                s = match_to_orders[o.MATCH_ID]

                is_same = compare(s.BET_TYPE, o.BET_TYPE) and compare(s.ORDER_TYPE, o.ORDER_TYPE) and compare(
                    s.BALL_TYPE, o.BALL_TYPE)
                if not is_same:
                    break
            print("order:", o_id, "compare result:", is_same)
            if is_same:
                count_amount += float(orders[0].BET_MONEY)

        print("we got same orders with order_id: %s bet_amount: %s others: " % (order_id, count_amount), same_order_ids)

        if count_amount + total_amount > float(mix_order_total_limit.CONTENT):
            print("reaching limit:", count_amount + total_amount, float(mix_order_total_limit.CONTENT))
            db.session.rollback()
            response = jsonify({'message': "mix_order_total"
                                })
            response.status_code = 400
            return response

        # 复制订单到主订单表
        new_order = new_orders[0]
        new_order.bet_status = BetStatus.Pending
        new_order.pay_wallet = PayWallet.Money
        bet_order = AppBetOrder.create_from_order(new_order, Match(), order_count=len(bets), )
        db.session.add(bet_order)

        for o in new_orders:
            o.bet_status = bet_order.bet_status
            o.pay_wallet = bet_order.pay_wallet
            o.main_order_id = bet_order.id
            db.session.add(o)

        before_amount = float(user.money)
        user.money = before_amount - total_amount
        after_amount = before_amount - total_amount

        db.session.commit()

        app_opt.send({
            "user_account": user.id,
            "user_name": user.username,
            "type": TransactionType.Order,
            "type_sub": "football",
            "before_amount": float(before_amount),
            "after_amount": float(after_amount),
            "amount": float(total_amount),
            "source_id": order_id,
            "aid": g.user.aid,
            "bet_id": order_id
        })

        return jsonify({'message': "bet success!"})
    except Exception as e:
        print("mix bet error", e)
        traceback.print_exc()
        response = jsonify({'message': "System or Technical Error"})
        response.status_code = 400
        return response


def compare(a, b):
    if a and b:
        return str(a) == str(b)
    return a == b


# 获取订单列表
@order.route('/get', methods=['GET'])
@auth.login_required
def get_order_list():
    """ get_order_list API Endpoint
        ---
        tags:
          - order
        parameters:
           - name: current_page
             in: query
             type: string
             required: true
             description: current_page of order_history
           - name: limit
             in: query
             type: integer
             description: limit of order_history
           - name: order_id
             in: query
             type: string
             description: order_id of order_history
           - name: key_word
             in: query
             type: string
             description: key_word of order_history
           - name: start_time
             in: query
             type: string
             description: start_time of order_history
           - name: end_time
             in: query
             type: string
             description: end_time of order_history
           - name: order_type
             in: query
             type: string
             description: status of order_history
             example: 1 # 1.single hdp 2.single o/u 3.correct score 4.mix hdp 5.mix o/u 6.single even/odd 7.mix even/odd 8.digital 9.digital_3d 10.single win/lose 11. mix win/lose
           - name: order_types
             in: query
             type: string
             description: order_types of order_history
             example: [1, 2, 3]
           - name: bet_type
             in: query
             type: string
             description: bet_type of order_history
             example: 1 # 1.host/over 2.guest/under 3.draw
           - name: status
             in: query
             type: string
             description: status of order_history   1 valid   0 invalid
           - name: is_mix
             in: query
             type: string
             description: is_mix of order_history 0 not mix   1 mix
           - name: is_win
             in: query
             type: string
             description: is_win of order_history  0 lose  1 win
        responses:
          200:
            description: { 'items': [...], 'total': 100, 'total_bet': 10000, 'total_bonus': 5000 }
        """

    current_page = request.args.get('page', type=int, default=1)
    limit = request.args.get('limit', type=int, default=20)
    order_id = request.args.get('order_id')

    match_id = request.args.get('match_id')
    is_detail = request.args.get('is_detail')

    key_word = request.args.get('key_word')
    start_time = request.args.get('start_time')
    end_time = request.args.get('end_time')

    order_type = request.args.get('order_type')
    order_types = request.args.get('order_types')
    bet_type = request.args.get('bet_type')
    status = request.args.get('status')
    pay_wallet = request.args.get('pay_wallet')
    bet_status = request.args.get('bet_status')

    if is_detail:
        detail_order_list = Order.query.filter(Order.USER_ID == g.user.id, Order.ORDER_ID == order_id, Order.STATUS == "1")
        detail_order_list = detail_order_list.all()
        detail_result = []
        for order in detail_order_list:
            detail_result.append(order.to_dict())

        return jsonify({
            'items': detail_result,
            'total': len(detail_result)
        })

    order_list = AppBetOrder.query.filter(AppBetOrder.mb_id == g.user.id, AppBetOrder.del_flag == 0, AppBetOrder.game_status == 'Pending')

    # if g.user.AGENT_CODE:
    #     users_under = AppUser.query.filter_by(aid=g.user.AGENT_CODE).all()
    #     users_under = set([u.USER_ID for u in users_under])
    #     order_list = order_list.filter(AppBetOrder.mb_id.in_(users_under))

    if order_id:
        order_list = order_list.filter(AppBetOrder.bet_group == order_id)
    if key_word:
        order_list = order_list.filter(
            or_(AppBetOrder.bet_group.like('%{}%'.format(key_word)), AppBetOrder.mb_id.like('%{}%'.format(key_word)),
                AppBetOrder.mb_username.like('%{}%'.format(key_word)), AppBetOrder.game_id.like('%{}%'.format(key_word)),
                AppBetOrder.remarks.like('%{}%'.format(key_word))))

    if match_id:
        order_list = order_list.filter(AppBetOrder.game_id == match_id)
    if order_type:
        order_list = order_list.filter(AppBetOrder.bet_type_sub.like('%{}:%'.format(order_type)))
    if order_types:
        bet_type_patterns = ['%{}:%'.format(ot) for ot in order_types.split(",")]
        order_list = order_list.filter(or_(*[AppBetOrder.bet_type_sub.like(pattern) for pattern in bet_type_patterns]))
    if status and int(status) > 0:
        order_list = order_list.filter(AppBetOrder.bet_status == BetStatus.Pending if status == "1" else AppBetOrder.bet_status != BetStatus.Pending)
    if pay_wallet:
        order_list = order_list.filter(AppBetOrder.pay_wallet == pay_wallet)
    if bet_status:
        order_list = order_list.filter(AppBetOrder.bet_status == bet_status)
    if bet_type:
        order_list = order_list.filter(AppBetOrder.bet_type == bet_type)

    if start_time:
        start_time += " 00:00:00"
        order_list = order_list.filter(AppBetOrder.create_time >= start_time)

    if end_time:
        end_time += " 23:59:59"
        order_list = order_list.filter(AppBetOrder.create_time <= end_time)

    order_list = order_list.group_by(AppBetOrder.bet_group)
    order_list = order_list.offset((current_page - 1) * limit).limit(limit).all()
    result = []
    for u in order_list:
        temp = u.to_dict()
        result.append(temp)

    return jsonify({
        'items': result,
        'total': len(result)})


# 获取订单列表（读历史表）
@order.route('/get_history', methods=['GET'])
@auth.login_required
def get_history_list():
    """
                @@@
                #### Args:
                        current_page = request.args.get('page', type=int, default=1)
                        limit = request.args.get('limit', type=int, default=20)
                        order_id = request.args.get('order_id')

                        key_word = request.args.get('key_word')
                        start_time = request.args.get('start_time')
                        end_time = request.args.get('end_time')

                        order_type = request.args.get('order_type')    订单类型:1胜负(让球)2大小球3波胆 无参表示全部
                        order_types = request.args.get('order_types')  订单类型多选
                        bet_type = request.args.get('bet_type')        下注类型:1主胜,2客胜   无参表示全部
                        status = request.args.get('status')            订单状态:0无效,1有效   无参表示全部
                        is_mix = request.args.get('is_mix')            是否混合过关:0否，1是  无参表示全部
                        is_win = request.args.get('is_win')            订单结果:0、输，1、赢,  2未出结果    无参表示全部
                #### Returns::
                        {
                                            'items': [u.to_dict() for u in order_list],
                            'total': total,
                            'total_bet': total_bet,       下注总金额
                            'total_bonus': total_bonus    总奖金
                        }
            """

    current_page = request.args.get('page', type=int, default=1)
    limit = request.args.get('limit', type=int, default=20)
    order_id = request.args.get('order_id')

    match_id = request.args.get('match_id')
    is_detail = request.args.get('is_detail')

    key_word = request.args.get('key_word')
    start_time = request.args.get('start_time')
    end_time = request.args.get('end_time')

    order_type = request.args.get('order_type')
    order_types = request.args.get('order_types')
    bet_type = request.args.get('bet_type')
    status = request.args.get('status')
    pay_wallet = request.args.get('pay_wallet')
    bet_status = request.args.get('bet_status')

    if is_detail:
        order_list = OrderHistory.query.filter(OrderHistory.USER_ID == g.user.id, OrderHistory.ORDER_ID == order_id)
        order_list = order_list.all()
        return jsonify({
            'items': [u.to_dict() for u in order_list],
        })

    order_list = AppBetOrder.query.filter(AppBetOrder.mb_id == g.user.id, AppBetOrder.del_flag == 0, or_(AppBetOrder.game_status == 'Finished', AppBetOrder.game_status == 'Cancelled'))

    # if g.user.AGENT_CODE:
    #     users_under = AppUser.query.filter_by(aid=g.user.AGENT_CODE).all()
    #     users_under = set([u.USER_ID for u in users_under])
    #     order_list = order_list.filter(OrderHistory.USER_ID.in_(users_under))

    if order_id:
        order_list = order_list.filter(AppBetOrder.bet_group == order_id)
    if key_word:
        order_list = order_list.filter(
            or_(AppBetOrder.bet_group.like('%{}%'.format(key_word)), AppBetOrder.mb_id.like('%{}%'.format(key_word)),
                AppBetOrder.mb_username.like('%{}%'.format(key_word)), AppBetOrder.game_id.like('%{}%'.format(key_word)),
                AppBetOrder.remarks.like('%{}%'.format(key_word))))

    if match_id:
        order_list = order_list.filter(AppBetOrder.game_id == match_id)
    if order_type:
        order_list = order_list.filter(AppBetOrder.bet_type_sub.like('%{}:%'.format(order_type)))
    if order_types:
        bet_type_patterns = ['%{}:%'.format(ot) for ot in order_types.split(",")]
        order_list = order_list.filter(or_(*[AppBetOrder.bet_type_sub.like(pattern) for pattern in bet_type_patterns]))
    if status and int(status) > 0:
        order_list = order_list.filter(AppBetOrder.bet_status == BetStatus.Pending if status == "1" else AppBetOrder.bet_status != BetStatus.Pending)
    if pay_wallet:
        order_list = order_list.filter(AppBetOrder.pay_wallet == pay_wallet)
    if bet_status:
        order_list = order_list.filter(AppBetOrder.bet_status == bet_status)

    if bet_type:
        order_list = order_list.filter(AppBetOrder.bet_type == bet_type)

    if start_time:
        start_time += " 00:00:00"
        order_list = order_list.filter(AppBetOrder.create_time >= start_time)

    if end_time:
        end_time += " 23:59:59"
        order_list = order_list.filter(AppBetOrder.create_time <= end_time)

    order_list = order_list.group_by(AppBetOrder.bet_group)
    order_list = order_list.offset((current_page - 1) * limit).limit(limit).all()
    result = []
    for u in order_list:
        temp = u.to_dict()
        result.append(temp)

    return jsonify({
        'items': result,
        'total': len(result)})


# 获取订单列表
@order.route('/get_history_old', methods=['GET'])
@auth.login_required
def get_order_history_old():
    """ get_order_history API Endpoint
        ---
        tags:
          - order
        parameters:
           - name: current_page
             in: query
             type: string
             required: true
             description: current_page of order_history
           - name: limit
             in: query
             type: integer
             description: limit of order_history
           - name: order_id
             in: query
             type: string
             description: order_id of order_history
           - name: key_word
             in: query
             type: string
             description: key_word of order_history
           - name: start_time
             in: query
             type: string
             description: start_time of order_history
           - name: end_time
             in: query
             type: string
             description: end_time of order_history
           - name: order_type
             in: query
             type: string
             description: status of order_history
             example: 1 # 1.single hdp 2.single o/u 3.correct score 4.mix hdp 5.mix o/u 6.single even/odd 7.mix even/odd 8.digital 9.digital_3d 10.single win/lose 11. mix win/lose
           - name: order_types
             in: query
             type: string
             description: order_types of order_history
             example: [1, 2, 3]
           - name: bet_type
             in: query
             type: string
             description: bet_type of order_history
             example: 1 # 1.host/over 2.guest/under 3.draw
           - name: status
             in: query
             type: string
             description: status of order_history   1 valid   0 invalid
           - name: is_mix
             in: query
             type: string
             description: is_mix of order_history 0 not mix   1 mix
           - name: is_win
             in: query
             type: string
             description: is_win of order_history  0 lose  1 win
        responses:
          200:
            description: { 'items': [...], 'total': 100, 'total_bet': 10000, 'total_bonus': 5000 }
        """
    # response = jsonify({'code': 50001, "message": "under maintence"})
    repeat_key = 'query_history_%s' % g.user.id
    Redis.get(repeat_key)
    is_detail = request.args.get('is_detail', type=bool, default=False)
    if Redis.get(repeat_key) and not is_detail:
        response = jsonify({'message': "Please wait for 60 second"})
        response.status_code = 429
        return response
    else:
        Redis.set(repeat_key, 1, ex=3)
    current_page = request.args.get('page', type=int, default=1)
    limit = request.args.get('limit', type=int, default=20)
    order_id = request.args.get('order_id')

    match_id = request.args.get('match_id')

    key_word = request.args.get('key_word')
    start_time = request.args.get('start_time')
    end_time = request.args.get('end_time')

    order_type = request.args.get('order_type')
    order_types = request.args.get('order_types')
    # 游戏类型 0:所有 1:比赛 2:数字
    game_type = request.args.get('game_type', type=int, default=1)
    bet_type = request.args.get('bet_type')
    is_mix = request.args.get('is_mix')
    is_win = request.args.get('is_win')

    if is_detail:
        order_list = OrderHistory.query.filter(OrderHistory.USER_ID == g.user.id, OrderHistory.ORDER_ID == order_id)
        order_list = order_list.all()
        return jsonify({
            'items': [u.to_dict() for u in order_list],
        })

    cl = SphinxClient()
    cl.SetServer('localhost', 9312)
    cl.SetLimits((current_page - 1) * limit, limit)
    print("????", (current_page - 1) * limit)
    cl.SetSortMode(SPH_SORT_ATTR_DESC, "id")
    print("getting order_history with:", request.args)

    total = 0

    query_str = "@USER_ID %s" % g.user.id

    if key_word:
        query_str += key_word

    if order_id:
        query_str += "@ORDER_ID %s" % order_id
    if match_id:
        query_str += "@MATCH_ID %s" % match_id
    if order_type:
        cl.SetFilter('ORDER_TYPE', [int(order_type)])
    if bet_type:
        cl.SetFilter('BET_TYPE', [bet_type])
    if is_mix:
        cl.SetFilter('IS_MIX', [int(is_mix)])
    if is_win:
        cl.SetFilter('IS_WIN', [int(is_win)])
    if not is_detail:
        cl.SetGroupBy('ORDER_GROUP', SPH_GROUPBY_ATTR, 'id desc')
    if game_type:
        if game_type == GameType.Match:
            cl.SetFilter('ORDER_TYPE', [1, 2, 3, 4, 5, 6, 7, 10])
        if game_type == GameType.Digit:
            cl.SetFilter('ORDER_TYPE', [8])

    # if start_time:
    #     start_time += " 00:00:00"
    #     time_array = time.strptime(start_time, "%Y-%m-%d %H:%M:%S")
    #     now_ts = int(time.time())
    #     start_time = int(time.mktime(time_array))
    #     cl.SetFilterRange('CREATE_TIME', start_time, now_ts)
    #
    # if end_time:
    #     end_time += " 23:59:59"
    #     time_array = time.strptime(end_time, "%Y-%m-%d %H:%M:%S")
    #     ts = int(time.mktime(time_array))
    #     cl.SetFilterRange('CREATE_TIME', start_time or 0, ts)

    print("filter str:", query_str)

    res = cl.Query(query_str, 'order_history;order_history_add')

    whole = {}
    order_ids = {}
    if res:
        whole = {w['id'] for w in res['matches']}
        order_ids = {w["attrs"]['order_group'] for w in res['matches']}
        total = res['total_found']
        print("order_history:", (current_page - 1) * limit, res['total_found'], res['total'])

    print("got result:", len(whole))
    order_list = OrderHistory.query.filter(OrderHistory.ID.in_(whole))

    if not is_detail:
        order_list = order_list.group_by(OrderHistory.ORDER_ID)
        result = []
        # order_list = order_list.with_entities(OrderHistory, func.count(OrderHistory.ORDER_ID))
        order_list = order_list.offset((current_page - 1) * limit).limit(limit).all()
        for u in order_list:
            # temp = u[0].to_dict()
            # temp['ORDER_COUNT'] = u[1]
            temp = u.to_dict()
            result.append(temp)
        return jsonify({
            'items': result,
            'total': len(result)})
        # order_list = order_list.group_by(OrderHistory.ORDER_ID).all()
        # _sum = OrderHistory.query.filter(OrderHistory.ORDER_TYPE == '8',
        #                                  OrderHistory.ORDER_ID.in_(order_ids)).with_entities(func.sum(OrderHistory.BONUS),
        #                                                                                      func.sum(OrderHistory.BET_MONEY), OrderHistory.ORDER_ID,
        #                                                                                      func.sum(OrderHistory.IS_WIN)).group_by(OrderHistory.ORDER_ID).all()
        # sum_dict = {}
        # for bonus, bet_money, order_id, id_win in _sum:
        #     # print("---", type(bonus), type(bet_money), type(id_win))
        #     # print("---", bonus, bet_money, id_win, order_ids)
        #     sum_dict[order_id] = {
        #         "BONUS": str(bonus),
        #         "BET_MONEY": str(bet_money),
        #         "IS_WIN": int(id_win),
        #     }
        # for u in order_list:
        #     temp = u.to_dict()
        #     # if u.ORDER_ID in sum_dict:
        #     #     temp.update(sum_dict[u.ORDER_ID])
        #     result.append(temp)
        # return jsonify({
        #     'items': result,
        #     'total': total
        # })

    order_list = order_list.all()
    return jsonify({
        'items': [u.to_dict() for u in order_list],
        'total': total

    })


@order.route('/promo_bet', methods=['POST'])
@auth.login_required
def promo_bet():
    """
    优惠券下单API
    使用优惠券进行单笔投注
    """
    from app_server.model.MAppMemberCouponModel import MAppMemberCoupon
    from app_server.model.AppMemberModel import AppMember
    from datetime import datetime
    from decimal import Decimal
    
    args = request.get_json()
    bets = args.get('bets')
    promotion_code = args.get('promotion_code', '').strip()

    getter_key = "order_promo_bet_%s_%s" % (g.user.id, str(args))
    if not Redis.exists(getter_key):
        Redis.set(getter_key, 0, ex=2)
    else:
        response = jsonify({'message': "same bet request in very short time"})
        response.status_code = 429
        return response

    try:
        if not promotion_code:
            response = jsonify({'message': "Promotion code is required"})
            response.status_code = 400
            return response

        # 只支持单笔投注
        if len(bets) != 1:
            response = jsonify({'message': "Promotion code can only be used for single bets"})
            response.status_code = 400
            return response

        user = g.user
        main_id = user.id
        del user
        
        db.session.commit()
        user = AppMember.query.filter_by(id=main_id).with_for_update(of=AppMember).first()

        # 查找优惠券 - 通过promotion_code在MAppCoupon表中查找，然后检查用户是否拥有该优惠券
        from app_server.model.MAppCouponModel import MAppCoupon
        coupon_master = MAppCoupon.query.filter_by(
            p_code=promotion_code,
            del_flag=0
        ).first()
        
        if not coupon_master:
            db.session.rollback()
            response = jsonify({'message': "Invalid promotion code"})
            response.status_code = 400
            return response
        if not coupon_master.p_status == "Active":
            response = jsonify({'message': "The Coupon activity has been Expired"})
            response.status_code = 400
            return response
        coupon = MAppMemberCoupon.query.filter_by(
            mb_id=user.id,
            p_id=coupon_master.id,
            del_flag=0
        ).with_for_update().first()

        if not coupon:
            db.session.rollback()
            response = jsonify({'message': "Invalid promotion code or coupon not found"})
            response.status_code = 400
            return response

        # 检查优惠券状态
        if coupon.status != 'Unused':
            db.session.rollback() 
            response = jsonify({'message': "Coupon has already been used or expired"})
            response.status_code = 400
            return response

        # 检查优惠券是否过期
        if coupon.expire_time and coupon.expire_time < datetime.now():
            db.session.rollback()
            response = jsonify({'message': "Coupon has expired"})
            response.status_code = 400
            return response

        bet = bets[0]
        bet_amount = float(coupon.money)  # 使用优惠券金额作为下注金额
        
        # 验证比赛
        match = Match.query.filter_by(MATCH_ID=bet['matchId']).one_or_none()
        if not match:
            db.session.rollback()
            response = jsonify({'message': "Bet failed: match not exist."})
            response.status_code = 400
            return response
            
        if match.CLOSING_STATE == "1":
            db.session.rollback()
            response = jsonify({'message': "Bet failed: match not exist."})
            response.status_code = 400
            return response
            
        if match.CLOSING_TIME <= datetime.now():
            db.session.rollback()
            response = jsonify({'message': "Events already started or closed"})
            response.status_code = 400
            return response

        order_type = bet['attrType']
        attrs = MatchAttr.query.filter_by(MATCH_ID=bet['matchId']).all()
        vip_attrs = VipMatchAttr.query.filter_by(MATCH_ID=bet['matchId']).all()
        vip_attr_dict = {attr.MATCH_ATTR_TYPE: attr for attr in vip_attrs}
        attr_dict = {attr.MATCH_ATTR_TYPE: attr for attr in attrs}

        attr = None
        if order_type in attr_dict:
            attr = attr_dict[order_type]

        if not attr:
            db.session.rollback()
            response = jsonify({'message': "Invalid Bet Type"})
            response.status_code = 400
            return response

        # 创建订单
        order_id = "%s-promo-%s" % (user.username, round(time.time() * 1000))
        new_order = Order(ID=str(uuid.uuid4()).replace("-", ""), ORDER_ID=order_id, USER_ID=user.id,
                         USER_NAME=user.username,
                         MATCH_ID=bet['matchId'], ORDER_TYPE=order_type, BET_TYPE=bet['betType'],
                         ORDER_DESC="%s || %s" % (match.HOST_TEAM, match.GUEST_TEAM),
                         BET_MONEY=bet_amount, order_type_desc="promotion", STATUS="1", IS_MIX="0", IS_WIN="2",
                         BONUS="0", LOSE_TEAM=attr.LOSE_TEAM,
                         BET_ODDS=attr.ODDS, LEAGUE=match.LEAGUE,
                         DRAW_BUNKO=0 if attr.DRAW_BUNKO == '' else attr.DRAW_BUNKO, DRAW_ODDS=attr.DRAW_ODDS,
                         LOSE_BALL_NUM=0 if attr.LOSE_BALL_NUM == '' else attr.LOSE_BALL_NUM,
                         MATCH_TIME=match.MATCH_MD_TIME, IP=int(ipaddress.IPv4Address(request.remote_addr)))

        new_order.BET_TYPE = bet['betType']

        if user.aid:
            new_order.AGENT_CODE = user.aid
        if order_type == "2":
            new_order.BALL_TYPE = bet['betType']

        if g.user.aid:
            new_order.AGENT_CODE = g.user.aid

        # 单双赔率另外赋值
        if order_type == '6':
            new_order.BET_ODDS = attr.ODDS if bet['betType'] == 1 else attr.ODDS_GUEST

        # 独赢赔率另外赋值
        if order_type == '10':
            new_order.BET_ODDS = attr.ODDS if bet['betType'] == 1 else attr.ODDS_GUEST
            if bet['betType'] == 3:
                new_order.BET_ODDS = attr.DRAW_ODDS

        # 扣除促销金额而不是主钱包
        before_promotion = float(user.money_promotion) if user.money_promotion else 0
        if before_promotion < bet_amount:
            db.session.rollback()
            response = jsonify({'message': "Insufficient promotion balance"})
            response.status_code = 400
            return response
            
        user.money_promotion = before_promotion - bet_amount
        after_promotion = before_promotion - bet_amount

        # 复制订单到主订单表，设置优惠券相关字段
        new_order.bet_status = BetStatus.Pending
        new_order.pay_wallet = PayWallet.Promotion
        bet_order = AppBetOrder.create_from_order(new_order, match)
        bet_order.in_promotion = True  # 标记为优惠券下注
        bet_order.pro_id = coupon.id   # 关联优惠券ID
        bet_order.pay_wallet = PayWallet.Promotion
        db.session.add(bet_order)
        new_order.main_order_id = bet_order.id

        # 更新优惠券状态为已使用
        coupon.status = 'Used'
        coupon.use_time = datetime.now()

        db.session.add(new_order)
        db.session.commit()

        # 记录资金流水
        app_opt.send({
            "user_account": user.id,
            "user_name": user.username,
            "type": TransactionType.Order,
            "type_sub": "promotion_bet",
            "before_amount": float(before_promotion),
            "after_amount": float(after_promotion),
            "amount": float(bet_amount),
            "source_id": order_id,
            "bet_id": order_id,
            "aid": g.user.aid,
            "match_id": bet['matchId']
        })

        return jsonify({
            'message': "Promotion bet success!",
            'new_promotion_balance': float(after_promotion)
        })

    except Exception as e:
        print("promo bet error", e)
        traceback.print_exc()
        db.session.rollback()
        response = jsonify({'message': "System or Technical Error"})
        response.status_code = 400
        return response
