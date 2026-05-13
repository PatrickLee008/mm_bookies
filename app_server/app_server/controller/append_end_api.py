# Temporary script to append end promotion API

api_code = '''

@promotion.route('/end', methods=['POST'])
@auth.login_required
def end_promotion():
    """结束促销活动并将促销钱包余额转入主钱包"""
    try:
        user_id = g.user.id
        user = g.user
        data = request.json
        promotion_id = data.get('promotion_id')

        if not promotion_id:
            return jsonify({
                'code': PARAM_ERROR_CODE,
                'data': None,
                'message': 'Promotion ID is required'
            }), 400

        # 获取参与记录（加锁）
        participation = db.session.query(MAppPromotionParticipation).filter(
            MAppPromotionParticipation.mb_id == user_id,
            MAppPromotionParticipation.promotion_id == promotion_id,
            MAppPromotionParticipation.del_flag == 0
        ).with_for_update().first()

        if not participation:
            return jsonify({
                'code': PARAM_ERROR_CODE,
                'data': None,
                'message': 'You have not participated in this promotion'
            }), 400

        # 检查状态
        if participation.status == 'Completed':
            return jsonify({
                'code': CONDITION_NOT_MET_CODE,
                'data': None,
                'message': 'Promotion has already been completed'
            }), 400

        if participation.status == 'Cancelled':
            return jsonify({
                'code': CONDITION_NOT_MET_CODE,
                'data': None,
                'message': 'Promotion has been cancelled'
            }), 400

        # 获取促销活动信息
        promotion_obj = MAppPromotion.query.filter_by(
            id=promotion_id,
            del_flag=0
        ).first()

        if not promotion_obj:
            return jsonify({
                'code': PROMOTION_NOT_FOUND_CODE,
                'data': None,
                'message': 'Promotion does not exist'
            }), 404

        # ==================== 1. 检查条件是否满足 ====================
        conditions_met = True
        unmet_conditions = []

        # 检查流水要求
        if participation.req_turnover and participation.req_turnover > 0:
            if participation.cur_turnover < participation.req_turnover:
                conditions_met = False
                remaining_turnover = participation.req_turnover - participation.cur_turnover
                unmet_conditions.append(f'Turnover requirement not met. Required: {float(participation.req_turnover)}, Current: {float(participation.cur_turnover)}, Remaining: {float(remaining_turnover)}')

        # 检查净赢要求
        if participation.req_netwin and participation.req_netwin > 0:
            if participation.cur_netwin < participation.req_netwin:
                conditions_met = False
                remaining_netwin = participation.req_netwin - participation.cur_netwin
                unmet_conditions.append(f'Net win requirement not met. Required: {float(participation.req_netwin)}, Current: {float(participation.cur_netwin)}, Remaining: {float(remaining_netwin)}')

        # 如果有条件未满足，返回错误
        if not conditions_met:
            return jsonify({
                'code': CONDITION_NOT_MET_CODE,
                'data': {
                    'unmet_conditions': unmet_conditions
                },
                'message': 'Promotion conditions not met. ' + '; '.join(unmet_conditions)
            }), 400

        # ==================== 2. 检查促销钱包余额 ====================
        # 获取会员信息（加锁）
        member = db.session.query(AppMember).filter(
            AppMember.id == user_id
        ).with_for_update().first()

        if not member:
            return jsonify({
                'code': PARAM_ERROR_CODE,
                'data': None,
                'message': 'Member not found'
            }), 400

        promo_balance = member.money_promotion if member.money_promotion else Decimal('0')

        # 检查最小结束金额（如果配置了manual_end_min_amount）
        if promotion_obj.manual_end_enabled and promotion_obj.manual_end_min_amount:
            if promo_balance < promotion_obj.manual_end_min_amount:
                return jsonify({
                    'code': CONDITION_NOT_MET_CODE,
                    'data': None,
                    'message': f'Promotion wallet balance ({float(promo_balance)}) is below minimum end threshold ({float(promotion_obj.manual_end_min_amount)})'
                }), 400

        if promo_balance <= 0:
            return jsonify({
                'code': INSUFFICIENT_BALANCE_CODE,
                'data': None,
                'message': 'Promotion wallet balance is zero or negative'
            }), 400

        # ==================== 3. 计算转移金额 ====================
        # 检查是否有最大取款限制
        transfer_amount = promo_balance
        max_withdrawal = None
        if promotion_obj.max_withdrawal_amount and promotion_obj.max_withdrawal_amount > 0:
            max_withdrawal = Decimal(str(promotion_obj.max_withdrawal_amount))
            if transfer_amount > max_withdrawal:
                transfer_amount = max_withdrawal

        # ==================== 4. 更新会员余额 ====================
        now = datetime.now()

        # 从促销钱包扣除
        old_promo_balance = member.money_promotion if member.money_promotion else Decimal('0')
        new_promo_balance = old_promo_balance - transfer_amount
        member.money_promotion = new_promo_balance

        # 转入主钱包
        old_main_balance = member.money if member.money else Decimal('0')
        new_main_balance = old_main_balance + transfer_amount
        member.money = new_main_balance

        # ==================== 5. 更新参与记录 ====================
        participation.status = 'Completed'
        participation.completion_time = now
        participation.update_time = now

        # ==================== 6. 更新活动记录 ====================
        activity_record = AppPlayerActivityRecord.query.filter(
            AppPlayerActivityRecord.mb_id == user_id,
            AppPlayerActivityRecord.activity_type == 'PROMOTION',
            AppPlayerActivityRecord.activity_id == promotion_id,
            AppPlayerActivityRecord.del_flag == 0
        ).first()

        if activity_record:
            activity_record.status = 'Completed'
            activity_record.end_time = now
            activity_record.is_requirement_met = 1
            activity_record.update_time = now

        # ==================== 7. 创建余额流水记录 ====================
        # 流水1：从促销钱包扣除
        balance_log_deduct = AppMemberBalanceLog(
            id=Kits.generate_uuid(),
            sn=f"PROMO_END_DEDUCT_{participation.id}",
            type=TransactionType.Activity,
            type_sub=TransactionType.PromotionComplete,
            type_sub_data_id=participation.id,
            mb_id=user_id,
            mb_username=member.username if hasattr(member, 'username') else None,
            money=-transfer_amount,  # 负数表示扣除
            start_balance=old_promo_balance,
            end_balance=new_promo_balance,
            create_by_id=user_id,
            update_by_id=user_id,
            aid=user.aid if hasattr(user, 'aid') else None,
            source="ProWallet",
            target=TransactionMap.Ewallet,
            pay_wallet="Promotion",
            status=1,
            source_status=0
        )

        # 流水2：转入主钱包
        balance_log_add = AppMemberBalanceLog(
            id=Kits.generate_uuid(),
            sn=f"PROMO_END_ADD_{participation.id}",
            type=TransactionType.Activity,
            type_sub=TransactionType.PromotionComplete,
            type_sub_data_id=participation.id,
            mb_id=user_id,
            mb_username=member.username if hasattr(member, 'username') else None,
            money=transfer_amount,
            start_balance=old_main_balance,
            end_balance=new_main_balance,
            create_by_id=user_id,
            update_by_id=user_id,
            aid=user.aid if hasattr(user, 'aid') else None,
            source="ProWallet",
            target=TransactionMap.Ewallet,
            pay_wallet="Money",
            status=1,
            source_status=0
        )

        # ==================== 8. 保存所有更改 ====================
        db.session.add(participation)
        db.session.add(member)
        db.session.add(balance_log_deduct)
        db.session.add(balance_log_add)
        if activity_record:
            db.session.add(activity_record)
        db.session.commit()

        # 准备返回数据
        response_data = {
            'participation_id': participation.id,
            'promotion_title': promotion_obj.title,
            'transfer_amount': float(transfer_amount),
            'max_withdrawal': float(max_withdrawal) if max_withdrawal else None,
            'old_promo_balance': float(old_promo_balance),
            'new_promo_balance': float(new_promo_balance),
            'old_main_balance': float(old_main_balance),
            'new_main_balance': float(new_main_balance),
            'completion_time': participation.completion_time.strftime('%Y-%m-%d %H:%M:%S'),
            'turnover_completed': float(participation.cur_turnover) if participation.cur_turnover else 0,
            'netwin_achieved': float(participation.cur_netwin) if participation.cur_netwin else 0
        }

        return jsonify({
            'code': SUCCESS_CODE,
            'data': response_data,
            'message': f'Promotion completed successfully! Transferred {float(transfer_amount)} from Promotion Wallet to Main Wallet.'
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': SYSTEM_ERROR_CODE,
            'data': None,
            'message': str(e)
        }), 500
'''

with open('PromotionController.py', 'a', encoding='utf-8') as f:
    f.write(api_code)

print("Successfully appended end_promotion API to PromotionController.py")
