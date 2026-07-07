import time
from sqlalchemy import or_, func, desc
from app_server import db, auth, app_opt, Redis
from app_server.logger import get_logger
from app_server.model.AppMemberBalanceLogModel import AppMemberBalanceLog, TransactionType
from app_server.model.AppMemberBankModel import AppMemberBank
from app_server.model.ChargeApplyModel import ChargeApply, StatusMap, StatusLabelMap
from app_server.model.ChargeModel import Charge
from app_server.model.WithDrawModel import WithDraw
from app_server.model.WithDrawGroupModel import WithDrawGroup
# from app_server.model.AppAdjustmentModel import AppAdjustment
from app_server.utils.Kits import Kits
from app_server.model.AppAgentModel import AppAgent
from app_server.utils.MessageHelper import MessageHelper
from app_server.utils.MemberMessageService import MemberMessageService
from flask import g, request, jsonify, Blueprint
from app_server.model.AppSettingFinanceModel import AppSettingFinanceModel
import uuid
import datetime
from sqlalchemy import literal

withdraw = Blueprint('withdraw', __name__)
logger = get_logger()


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
             description: type of get_wallet_list - "Withdraw" for withdrawals only, "Deposit" for deposits only, "Adjustment" for balance adjustments only, not set or other value means all types
        responses:
          200:
            description: { 'items': [...], 'total': 100}
        """

    # 获取参数
    current_page = request.args.get('page', type=int, default=1)
    limit = request.args.get('limit', type=int, default=20)
    key_word = request.args.get('key_word')
    start_time = request.args.get('start_time')
    end_time = request.args.get('end_time')
    status = request.args.get('status')
    statuses = request.args.getlist('statuses')
    type_filter = request.args.get('type')
    user_id = g.user.id

    # 优化1: 提取公共过滤逻辑，减少重复代码
    def apply_filters_no_date(query, model):
        """应用除日期外的通用过滤条件"""
        query = query.filter(model.mb_id == user_id)

        if key_word:
            query = query.filter(model.mb_nickname.like(f"%{key_word}%"))

        if statuses:
            query = query.filter(model.status.in_(statuses))
        elif status is not None:
            query = query.filter(model.status == status)

        return query

    def apply_date_filters(query, model):
        """应用日期过滤条件"""
        if start_time:
            query = query.filter(model.create_time >= start_time + " 00:00:00")

        if end_time:
            query = query.filter(model.create_time <= end_time + " 23:59:59")

        return query

    def apply_filters(query, model):
        """应用所有过滤条件（含日期）"""
        query = apply_filters_no_date(query, model)
        query = apply_date_filters(query, model)
        return query

    # 优化2: 构建查询基础 - 减少代码重复
    def build_base_query(model, type_label, has_bank_info=True):
        """构建基础查询，返回统一的列结构"""
        if has_bank_info:
            return db.session.query(
                model.id.label("id"),
                model.amount.label("amount"),
                model.create_time.label("create_time"),
                literal(type_label).label("type"),
                model.status.label("status"),
                model.remarks.label("remarks"),
                model.mb_bank_code.label("rc_bank_code"),
                model.pay_type.label("pay_type")
            )
        else:
            return db.session.query(
                model.id.label("id"),
                model.amount.label("amount"),
                model.create_time.label("create_time"),
                literal(type_label).label("type"),
                model.status.label("status"),
                model.remarks.label("remarks"),
                literal("").label("rc_bank_code"),
                literal("").label("pay_type")
            )

    # 优化3: 根据类型选择查询策略
    if type_filter == "Withdraw":
        # 单表查询 - 最快
        # 过滤掉 pay_type 为 ADJUSTMENT 的数据
        union_query = apply_filters(build_base_query(WithDraw, "Withdraw"), WithDraw)
        union_query = union_query.filter(or_(WithDraw.pay_type != 'ADJUSTMENT', WithDraw.pay_type.is_(None)))
        # 保存无日期过滤的查询用于fallback
        union_query_no_date = apply_filters_no_date(build_base_query(WithDraw, "Withdraw"), WithDraw)
        union_query_no_date = union_query_no_date.filter(or_(WithDraw.pay_type != 'ADJUSTMENT', WithDraw.pay_type.is_(None)))

    elif type_filter == "Deposit":
        # 单表查询 - 最快
        # 过滤掉 pay_type 为 ADJUSTMENT 的数据
        union_query = apply_filters(build_base_query(Charge, "Deposit"), Charge)
        union_query = union_query.filter(or_(Charge.pay_type != 'ADJUSTMENT', Charge.pay_type.is_(None)))
        union_query_no_date = apply_filters_no_date(build_base_query(Charge, "Deposit"), Charge)
        union_query_no_date = union_query_no_date.filter(or_(Charge.pay_type != 'ADJUSTMENT', Charge.pay_type.is_(None)))

    elif type_filter == "Adjustment":
        # 查询 WithDraw 和 Charge 表中 pay_type 为 ADJUSTMENT 的数据
        withdraw_query = apply_filters(build_base_query(WithDraw, "Adjustment"), WithDraw)
        withdraw_query = withdraw_query.filter(WithDraw.pay_type == 'ADJUSTMENT')

        charge_query = apply_filters(build_base_query(Charge, "Adjustment"), Charge)
        charge_query = charge_query.filter(Charge.pay_type == 'ADJUSTMENT')

        union_query = withdraw_query.union_all(charge_query)

        withdraw_query_nd = apply_filters_no_date(build_base_query(WithDraw, "Adjustment"), WithDraw)
        withdraw_query_nd = withdraw_query_nd.filter(WithDraw.pay_type == 'ADJUSTMENT')
        charge_query_nd = apply_filters_no_date(build_base_query(Charge, "Adjustment"), Charge)
        charge_query_nd = charge_query_nd.filter(Charge.pay_type == 'ADJUSTMENT')
        union_query_no_date = withdraw_query_nd.union_all(charge_query_nd)

    else:
        # 多表联合查询 - 使用 UNION ALL 避免去重开销
        withdraw_query = apply_filters(build_base_query(WithDraw, "Withdraw"), WithDraw)
        charge_query = apply_filters(build_base_query(Charge, "Deposit"), Charge)
        # adjustment_query = apply_filters(build_base_query(AppAdjustment, "Adjustment", has_bank_info=False),
        #                                  AppAdjustment)

        # 优化4: 使用 UNION ALL 而不是 UNION（避免去重）
        union_query = withdraw_query.union_all(charge_query)

        withdraw_query_nd = apply_filters_no_date(build_base_query(WithDraw, "Withdraw"), WithDraw)
        charge_query_nd = apply_filters_no_date(build_base_query(Charge, "Deposit"), Charge)
        union_query_no_date = withdraw_query_nd.union_all(charge_query_nd)

    def build_items(records):
        """构建结果列表"""
        return [
            {
                "id": r.id,
                "amount": float(r.amount) if r.amount else 0.0,
                "type": r.type,
                "create_time": r.create_time.strftime("%Y-%m-%d %H:%M:%S") if r.create_time else "",
                "status": str(r.status) if r.status else "",
                "bank_code": r.rc_bank_code or "",
                "remarks": r.remarks or "",
                "wallet_type": "Money",
                "pay_type": r.pay_type or "",
            }
            for r in records
        ]

    # 优化5: 先获取总数（使用 count() 而不是查询所有数据）
    total = union_query.count()

    # 优化6: 排序和分页 - 按 create_time 降序
    records = union_query.order_by(desc("create_time")).offset((current_page - 1) * limit).limit(limit).all()

    # 优化7: 使用列表推导式构建结果，更高效
    items = build_items(records)

    # 如果结果不足5条且有日期过滤，去掉日期限制取最新5条
    min_display = 5
    if len(items) < min_display and (start_time or end_time):
        fallback_records = union_query_no_date.order_by(desc("create_time")).limit(min_display).all()
        items = build_items(fallback_records)
        total = union_query_no_date.count()

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
    logger.info(f"提现组名称映射: {name_dict}")
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
            description: System or Technical Error
          200:
            description: edit successful.
        """
    args = request.get_json()
    money = args.get('money')
    withdraw_all = args.get('ALL')
    card_id = args.get('card_id')
    try:
        # 获取默认的提现限制
        finance_default_config = AppSettingFinanceModel.get_agent_config()
        user = g.user
        user_id = user.id
        # del user
        from app_server.model.AppMemberModel import AppMember
        db.session.commit()

        # user = AppMember.query.filter_by(id=user_id).with_for_update(of=AppMember).first()

        repeat_user_key = "withdraw_limit_%s" % user_id
        if repeat_user_key and Redis.exists(repeat_user_key):
            response = jsonify({'message': "withdraw repeat"})
            response.status_code = 409
            return response
        Redis.setex(repeat_user_key, 10, 'processed')

        logger.info(f"提现申请开始 - 用户ID: {user_id}, 当前余额: {user.money}")

        before_amount = float(user.money)
        if withdraw_all:
            money = user.money
        if before_amount < float(money):
            response = jsonify({'message': "money_not_enough"})
            response.status_code = 400
            return response
        withdraw_min_limit = finance_default_config.sf_min_withdrawal
        if float(money) < float(withdraw_min_limit):
            response = jsonify({'message': "withdraw_min_limit"})
            response.status_code = 400
            return response
        if float(money) > float(finance_default_config.sf_max_withdrawal):
            response = jsonify({'message': "withdraw_max_limit"})
            response.status_code = 400
            return response

        # ============= 新的累积制流水验证 =============
        # 公式：
        # - Required Turnover(n) = Required Turnover(n-1) + Deposit(n) × Turnover Rate
        # - Current Turnover(n) = Current Turnover(n-1) + Bet(n)
        # - 重置条件：Withdraw Amount > Promotion Wallet Transfer OR Previous Remaining Balance = 0
        # - IF Current Turnover >= Required Turnover
        #   THEN Cleared Balance = Remaining Balance
        #   ELSE Cleared Balance = Promotion Wallet Transfer
        # - Withdrawable Amount = Cleared Balance
        #
        # ⚠️ 重要：提现申请时只验证可提现金额，不执行重置
        # 重置逻辑应该在后台审核提现通过时执行
        from app_server.service.TurnoverAccumulationService import TurnoverAccumulationService

        # 计算可提现金额（只读取，不修改数据库）
        withdrawable_amount = TurnoverAccumulationService.calculate_withdrawable_amount(user)

        # 如果提现金额超过可提现金额，拒绝申请
        if float(money) > withdrawable_amount:
            current_turnover = float(user.current_turnover_accumulated) if user.current_turnover_accumulated else 0.0
            required_turnover = float(user.required_turnover_accumulated) if user.required_turnover_accumulated else 0.0
            remaining = max(0, required_turnover - current_turnover)

            logger.info(f"流水不满足提现要求 - 用户ID: {user_id}, "
                       f"提现金额: {money}, 可提现金额: {withdrawable_amount}, "
                       f"当前流水: {current_turnover}, 需要流水: {required_turnover}, "
                       f"剩余流水: {remaining}")

            response = jsonify({'message': "current turnover does not meet the minimum requirement"})
            response.status_code = 400
            return response
        # ============= 流水验证结束 =============

        spare_groups = WithDrawGroup.query.filter(WithDrawGroup.HANDLE_ON).all()
        if not len(spare_groups):
            response = jsonify({'message': "Too many players withdrawing cash, please try again later."})
            response.status_code = 429
            return response
            response.status_code = 400
            return response
        spare_groups = [u.ID for u in spare_groups]
        logger.info(f"可用提现组: {spare_groups}")

        now = datetime.datetime.now()
        key_date = now.date()
        # if now.hour < 12:
        #     key_date -= datetime.timedelta(days=1)

        after_amount = before_amount - float(money)
        user.money = after_amount
        user.money_lock = float(user.money_lock) + float(money)
        logger.info(f"提现扣款 - 用户ID: {user.id}, 扣款前: {before_amount}, 扣款后: {after_amount}, 提现金额: {money}")

        date_key = "withdraw_code_%s" % key_date
        if not Redis.exists(date_key):
            Redis.set(date_key, 0, ex=24 * 60 * 60)

        Redis.incr(date_key)
        withdraw_code = "%05d" % int(Redis.get(date_key))

        group_key = "user_withdraw%s" % user.id
        group_value = Redis.get(group_key)
        if group_value and int(group_value) in spare_groups:
            logger.info(f"用户已有提现组 - 用户ID: {user.id}, 组ID: {group_value}, 过期时间(秒): {Redis.ttl(group_key)}")
            next_group_id = int(group_value)
        else:
            cur_work_group = finance_default_config.cur_withdraw_group
            cur_group_id = int(cur_work_group)
            next_group_id = spare_groups[0]
            for gr in spare_groups:
                if gr > cur_group_id:
                    next_group_id = gr
                    break
            cur_work_group = next_group_id
        # 处理达到上限
        next_group = WithDrawGroup.query.filter(WithDrawGroup.ID == next_group_id).with_for_update().first()
        next_group.NOW_HANDLE += 1
        if next_group.NOW_HANDLE >= next_group.MAX_HANDLE:
            next_group.HANDLE_ON = False

        # 组过期时间
        expiration = finance_default_config.withdraw_group_expiration
        logger.info(f"分配新提现组 - 用户ID: {user.id}, 组ID: {next_group_id}, 过期时间(秒): {expiration}, 当前时间: {datetime.datetime.now()}")
        Redis.set("user_withdraw%s" % user.id, next_group_id, expiration)

        bank_card = AppMemberBank.query.filter_by(id=card_id).first()
        current_time = datetime.datetime.now()
        the_withdraw = WithDraw(id=Kits.generate_uuid(), withdraw_code=withdraw_code, aid=user.aid, mb_id=user.id,
                                mb_username=user.username,
                                mb_nickname=bank_card.acc_name, amount=money, status=StatusLabelMap.Pending,
                                withdraw_type="USER", before_amount=before_amount, after_amount=after_amount,
                                mb_acc_name=bank_card.acc_name,
                                work_group_id=next_group_id, mb_bank_code=bank_card.bank_code,
                                mb_acc_number=bank_card.acc_number, confirm_time=current_time)

        if float(money) > float(user.money_promotion_withdrawable):
            the_withdraw.money_promotion_withdrawable = float(user.money_promotion_withdrawable)
            user.money_promotion_withdrawable = 0
        else:
            the_withdraw.money_promotion_withdrawable = float(money)
            user.money_promotion_withdrawable = float(user.money_promotion_withdrawable) - float(money)

        logger.info(f"提现申请提交 - 用户ID: {user.id}, 用户名: {user.username}, 提现金额: {money}, 提现ID: {the_withdraw.id}, 提现编号: {withdraw_code}, 银行卡号: {bank_card.acc_number}, 提现前余额: {before_amount}, 提现后余额: {after_amount}")
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

        db.session.commit()
        logger.info(f"提现申请保存成功 - 提现ID: {the_withdraw.id}, 状态: {StatusLabelMap.Pending}")

        # 发送提现申请通知给管理员
        try:
            if user.aid:
                # 通过aid查询代理信息
                agent = AppAgent.query.filter_by(id=user.aid).first()
                if agent:
                    # 通过sys_user表获取所有关联的管理员ID
                    admin_user_ids = agent.get_admin_user_ids()
                    if admin_user_ids:
                        # 发送通知给管理员
                        MessageHelper.send_withdraw_apply_to_admin(
                            admin_user_ids=admin_user_ids,
                            member_id=user.id,
                            member_name=user.username,
                            order_id=the_withdraw.id,
                            amount=float(money)
                        )
        except Exception as e:
            from app_server import app
            app.logger.warning(f"Failed to send withdrawal notification to admin: {str(e)}")

        # P3: 发送站内通知给会员 — 提现申请已提交
        try:
            MemberMessageService.send_withdraw_submitted(
                member_id=user.id,
                order_id=the_withdraw.id,
                amount=float(money),
                aid=user.aid
            )
        except Exception as e:
            from app_server import app
            app.logger.warning(f"Failed to send withdrawal notification to member: {str(e)}")

        app_opt.send({
            "user_account": user.id,
            "user_name": user.username,
            "type": TransactionType.Withdraw,
            "type_sub": "MANUAL",
            "before_amount": float(before_amount),
            "after_amount": float(after_amount),
            "amount": f"-{float(money)}",
            "source_id": the_withdraw.id,

            "aid": user.aid,
            "create_by_id": user.id,
            "mb_rid": user.rid,
            "source": "System",
            "target": "Ewallet",
            "source_status": StatusMap.Pending,
            "pay_wallet": "Money",
        })

        # 记录提现行为日志
        try:
            from app_server.service.AppBehaviorLogService import AppBehaviorLogService
            from app_server import app

            AppBehaviorLogService.add_behavior_log(
                request=request,
                event_type='withdraw',
                member_id=user.id,
                event_params={
                    'amount': float(money),
                    'withdraw_id': the_withdraw.id,
                    'withdraw_code': withdraw_code,
                    'bank_code': bank_card.bank_code,
                    'bank_account': bank_card.acc_number,
                    'status': StatusLabelMap.Pending
                },
                remark='User withdrawal initiated'
            )
        except Exception as e:
            app.logger.warning(f"Failed to add withdrawal behavior log: {str(e)}")

        return jsonify({'message': "add successful."})
    except Exception as e:
        logger.error(f"提现申请失败 - 用户ID: {g.user.id}, 错误: {e}", exc_info=True)
        response = jsonify({'message': "System or Technical Error"})
        response.status_code = 500
        return response
    response.status_code = 400
    return response
