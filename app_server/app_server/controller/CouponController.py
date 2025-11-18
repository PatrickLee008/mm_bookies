from datetime import datetime, timedelta
from decimal import Decimal
import uuid

from sqlalchemy import func, and_, or_
from flask import g, request, jsonify, Blueprint

from app_server import app, db, auth
from app_server.model.AppMemberModel import AppMember
from app_server.model.MAppCouponModel import MAppCoupon
from app_server.model.MAppMemberCouponModel import MAppMemberCoupon
from app_server.model.AppMemberBalanceLogModel import AppMemberBalanceLog, TransactionType
from app_server.model.OrderModel import Order
from app_server.model.ChargeModel import Charge
from app_server.model.AppBetOrderModel import AppBetOrder
from app_server.service.NetWinService import NetWinService
from app_server.service.RiskManagementService import RiskManagementService

# 常量定义
SUCCESS_CODE = 200
SYSTEM_ERROR_CODE = 501
PARAM_ERROR_CODE = 401
COUPON_NOT_FOUND_CODE = 402
COUPON_NOT_VALID_CODE = 403
COUPON_ALREADY_CLAIMED_CODE = 404
INSUFFICIENT_BALANCE_CODE = 405
NET_WIN_NOT_MET_CODE = 406
RISK_CHECK_FAILED_CODE = 407

# 创建蓝图
coupon = Blueprint('coupon', __name__)


# 辅助函数：检查优惠券是否有效
def is_coupon_valid(coupon):
    """检查优惠券是否在有效期内且已激活

    优惠券状态说明：
    - Active: 活跃状态，可以被用户领取
    - Finished: 已结束状态，不可领取但已领取的仍可使用
    - Expired: 已过期状态，已领取的优惠券也已过期

    用户端只能领取 Active 状态的优惠券
    """
    if not coupon or coupon.del_flag != 0 or coupon.pstatus not in ['Active']:
        return False
    
    now = datetime.now()

    # 检查领取时间范围 (p_start 和 p_end 是优惠券可领取的时间范围)
    if coupon.p_start and now < coupon.p_start:
        return False
    if coupon.p_end and now > coupon.p_end:
        return False

    # 注意：这里不检查 p_expire，因为 p_expire 是优惠券的最终过期时间
    # 即使超过 p_end，只要状态是 Active，仍可领取
    # p_expire 由后台定时任务处理，前端只需检查状态即可
    
    # 统一检查托管余额是否充足（代理和House优惠券都需要）
    if not coupon.remaining_amount or coupon.remaining_amount <= 0:
        return False
    
    return True


# 辅助函数：检查净赢条件
def check_net_win_condition(user_id, coupon):
    """检查用户是否满足优惠券的净赢条件"""
    # 使用 NetWinService 检查净赢条件
    result = NetWinService.check_net_win_eligibility(
        user_id=user_id,
        net_win_enabled=coupon.net_win_enabled,
        condition_type=coupon.net_win_condition_type,
        required_amount=coupon.net_win_amount,
        start_date=coupon.p_start,
        end_date=coupon.p_end
    )
    
    return result['eligible'], result['message']


# 辅助函数：检查用户领取限制
def check_user_claim_limits(user_id, coupon_id, coupon):
    """检查用户是否超过领取限制"""
    # 检查资金来源权限
    if coupon.fund_source_type == 'AGENT':
        # 获取会员信息检查代理ID
        member = AppMember.query.filter_by(id=user_id, del_flag=0).first()
        if not member:
            return False, "Member not found"
        
        # AGENT类型的优惠券需要会员的aid与优惠券的aid匹配
        if member.aid != coupon.aid:
            return False, "You are not authorized to redeem this agent coupon"
    # HOUSE类型的优惠券所有人都可以领取，无需额外检查
    
    # 检查用户总领取次数
    if coupon.plmu_jtt and coupon.plmu_jtt > 0:
        total_claims = MAppMemberCoupon.query.filter_by(
            mb_id=user_id,
            p_id=coupon_id,
            del_flag=0
        ).count()
        
        if total_claims >= coupon.plmu_jtt:
            return False, f"Total claim limit reached: {coupon.plmu_jtt}"
    
    # 检查用户每日领取次数
    if coupon.plmu_jpd and coupon.plmu_jpd > 0:
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)
        
        daily_claims = MAppMemberCoupon.query.filter(
            MAppMemberCoupon.mb_id == user_id,
            MAppMemberCoupon.p_id == coupon_id,
            MAppMemberCoupon.create_time >= today_start,
            MAppMemberCoupon.create_time < today_end,
            MAppMemberCoupon.del_flag == 0
        ).count()
        
        if daily_claims >= coupon.plmu_jpd:
            return False, f"Daily claim limit reached: {coupon.plmu_jpd}"
    
    return True, "Within claim limits"


# 辅助函数：风险检查
def perform_risk_check(user_id, coupon_id, ip_address=None, imei=None, user_agent=None):
    """使用RiskManagementService进行风险检查"""
    try:
        # 首先检查用户状态
        member = AppMember.query.filter_by(id=user_id, del_flag=0).first()
        if not member:
            return False, "User not found"
        
        if member.status != 1:  # 假设1是正常状态
            return False, "User account is not active"
        
        # 使用RiskManagementService进行综合风险评估
        risk_result = RiskManagementService.assess_redemption_risk(
            user_id=user_id,
            coupon_id=coupon_id,
            ip=ip_address or '0.0.0.0',
            imei=imei,
            user_agent=user_agent,
            location=None,  # 可以从请求中获取位置信息
            coupon_config={
                'ip_limit_count': 10,
                'ip_time_window_hours': 1,
                'imei_limit_count': 5,
                'max_users_per_ip': 3,
                'time_window_minutes': 5
            }
        )
        
        if not risk_result['allowed']:
            return False, risk_result['reason']
        
        return True, "Risk check passed"
        
    except Exception as e:
        print(f"Risk check error: {str(e)}")
        return False, "Risk check failed"


@coupon.route('/list', methods=['GET'])
@auth.login_required
def get_available_coupons():
    """获取可用的优惠券列表"""
    try:
        user_id = g.user.id
        page = int(request.args.get('page', 1))
        page_size = min(int(request.args.get('page_size', 20)), 100)
        
        # 查询所有有效的优惠券
        # 条件：状态为Active + 在领取时间范围内
        now = datetime.now()
        query = MAppCoupon.query.filter(
            MAppCoupon.del_flag == 0,
            MAppCoupon.pstatus == 'Active',  # 只有Active状态才可领取
            MAppCoupon.tenant_id == '10000',
            or_(
                MAppCoupon.p_start.is_(None),
                MAppCoupon.p_start <= now  # 领取开始时间检查
            ),
            or_(
                MAppCoupon.p_end.is_(None),
                MAppCoupon.p_end >= now  # 领取结束时间检查
            )
            # 注意：不检查p_expire，p_expire由后台定时任务处理状态变更
        )
        
        # 获取总数
        total_count = query.count()
        
        # 分页
        offset = (page - 1) * page_size
        coupons = query.order_by(MAppCoupon.create_time.desc()).offset(offset).limit(page_size).all()
        
        # 格式化返回数据
        coupon_list = []
        for c in coupons:
            # 检查用户是否已领取
            user_claims = MAppMemberCoupon.query.filter_by(
                mb_id=user_id,
                p_id=c.id,
                del_flag=0
            ).count()
            
            # 检查是否可以领取
            can_claim = True
            claim_message = "Available"
            
            # 检查领取限制
            limit_check, limit_msg = check_user_claim_limits(user_id, c.id, c)
            if not limit_check:
                can_claim = False
                claim_message = limit_msg
            
            coupon_info = {
                'id': c.id,
                'name': c.pname,
                'code': c.pcode,
                'description': c.p_des,
                'bonus_amount': float(c.bonus_amount) if c.bonus_amount else 0,
                'bonus_type': c.bonus_type,
                'turnover_rate': float(c.turnover_rate) if c.turnover_rate else 0,
                'start_date': c.p_start.strftime('%Y-%m-%d %H:%M:%S') if c.p_start else None,
                'end_date': c.p_end.strftime('%Y-%m-%d %H:%M:%S') if c.p_end else None,
                'user_claimed_count': user_claims,
                'can_claim': can_claim,
                'claim_message': claim_message,
                'fund_source_type': c.fund_source_type,
                'remaining_amount': float(c.remaining_amount) if c.remaining_amount else 0
            }
            coupon_list.append(coupon_info)
        
        return jsonify({
            'code': SUCCESS_CODE,
            'data': {
                'coupons': coupon_list,
                'pagination': {
                    'current_page': page,
                    'page_size': page_size,
                    'total_count': total_count,
                    'total_pages': (total_count + page_size - 1) // page_size
                }
            },
            'message': 'success'
        }), 200
        
    except Exception as e:
        return jsonify({
            'code': SYSTEM_ERROR_CODE,
            'data': None,
            'message': str(e)
        }), 500


@coupon.route('/validate', methods=['POST'])
@auth.login_required
def validate_coupon():
    """验证优惠券是否可以使用"""
    try:
        user_id = g.user.id
        data = request.json
        coupon_id = data.get('coupon_id')
        
        if not coupon_id:
            return jsonify({
                'code': PARAM_ERROR_CODE,
                'data': None,
                'message': 'Coupon ID is required'
            }), 400
        
        # 获取优惠券信息
        coupon_obj = MAppCoupon.query.filter_by(
            id=coupon_id,
            del_flag=0,
            tenant_id='10000'
        ).first()
        
        if not coupon_obj:
            return jsonify({
                'code': COUPON_NOT_FOUND_CODE,
                'data': None,
                'message': 'Coupon does not exist'
            }), 404
        
        # 检查优惠券是否有效
        if not is_coupon_valid(coupon_obj):
            return jsonify({
                'code': COUPON_NOT_VALID_CODE,
                'data': None,
                'message': 'Coupon is not valid or has expired'
            }), 400
        
        # 检查领取限制
        limit_check, limit_msg = check_user_claim_limits(user_id, coupon_id, coupon_obj)
        if not limit_check:
            return jsonify({
                'code': COUPON_ALREADY_CLAIMED_CODE,
                'data': None,
                'message': limit_msg
            }), 400
        
        # 检查净赢条件
        net_win_check, net_win_msg = check_net_win_condition(user_id, coupon_obj)
        if not net_win_check:
            return jsonify({
                'code': NET_WIN_NOT_MET_CODE,
                'data': {
                    'net_win_required': float(coupon_obj.net_win_amount) if coupon_obj.net_win_amount else 0,
                    'condition_type': coupon_obj.net_win_condition_type
                },
                'message': net_win_msg
            }), 400
        
        # 风险检查
        ip_address = request.remote_addr
        user_agent = request.headers.get('User-Agent')
        risk_check, risk_msg = perform_risk_check(user_id, coupon_id, ip_address, user_agent=user_agent)
        if not risk_check:
            return jsonify({
                'code': RISK_CHECK_FAILED_CODE,
                'data': None,
                'message': risk_msg
            }), 400
        
        return jsonify({
            'code': SUCCESS_CODE,
            'data': {
                'can_use': True,
                'coupon_id': coupon_id,
                'bonus_amount': float(coupon_obj.bonus_amount) if coupon_obj.bonus_amount else 0,
                'turnover_requirement': float(coupon_obj.bonus_amount * coupon_obj.turnover_rate) if coupon_obj.bonus_amount and coupon_obj.turnover_rate else 0
            },
            'message': 'Coupon is valid and can be used'
        }), 200
        
    except Exception as e:
        return jsonify({
            'code': SYSTEM_ERROR_CODE,
            'data': None,
            'message': str(e)
        }), 500


@coupon.route('/redeem', methods=['POST'])
@auth.login_required
def redeem_coupon():
    """兑换优惠券 - 支持通过优惠券ID或兑换码"""
    try:
        user_id = g.user.id
        data = request.json
        coupon_id = data.get('coupon_id')
        coupon_code = data.get('coupon_code')
        
        # 验证参数：必须提供其中一个
        if not coupon_id and not coupon_code:
            return jsonify({
                'code': PARAM_ERROR_CODE,
                'data': None,
                'message': 'Either coupon_id or coupon_code is required'
            }), 400
        
        if coupon_id and coupon_code:
            return jsonify({
                'code': PARAM_ERROR_CODE,
                'data': None,
                'message': 'Please provide either coupon_id or coupon_code, not both'
            }), 400
        
        # 根据参数类型查找优惠券
        if coupon_id:
            # 通过ID查找
            coupon_obj = db.session.query(MAppCoupon).filter(
                MAppCoupon.id == coupon_id,
                MAppCoupon.del_flag == 0,
                MAppCoupon.tenant_id == '10000',
                MAppCoupon.p_app_hidden == 1,
            ).with_for_update().first()
            redeem_type = 'id'
        else:
            # 通过兑换码查找
            coupon_obj = db.session.query(MAppCoupon).filter(
                MAppCoupon.p_code == coupon_code.strip(),
                MAppCoupon.del_flag == 0,
                MAppCoupon.tenant_id == '10000'
            ).with_for_update().first()
            redeem_type = 'code'
        
        if not coupon_obj:
            error_message = 'Coupon does not exist' if coupon_id else 'Invalid coupon code'
            return jsonify({
                'code': COUPON_NOT_FOUND_CODE,
                'data': None,
                'message': error_message
            }), 404
        
        # 验证优惠券
        if not is_coupon_valid(coupon_obj):
            return jsonify({
                'code': COUPON_NOT_VALID_CODE,
                'data': None,
                'message': 'Coupon is not valid or has expired'
            }), 400
        
        # 检查领取限制
        limit_check, limit_msg = check_user_claim_limits(user_id, coupon_obj.id, coupon_obj)
        if not limit_check:
            return jsonify({
                'code': COUPON_ALREADY_CLAIMED_CODE,
                'data': None,
                'message': limit_msg
            }), 400
        
        # 检查净赢条件
        net_win_check, net_win_msg = check_net_win_condition(user_id, coupon_obj)
        if not net_win_check:
            return jsonify({
                'code': NET_WIN_NOT_MET_CODE,
                'data': {
                    'net_win_required': float(coupon_obj.net_win_amount) if coupon_obj.net_win_amount else 0,
                    'condition_type': coupon_obj.net_win_condition_type
                },
                'message': net_win_msg
            }), 400
        
        # 风险检查
        ip_address = request.remote_addr
        user_agent = request.headers.get('User-Agent')
        risk_check, risk_msg = perform_risk_check(user_id, coupon_obj.id, ip_address, user_agent=user_agent)
        if not risk_check:
            return jsonify({
                'code': RISK_CHECK_FAILED_CODE,
                'data': None,
                'message': risk_msg
            }), 400
        
        bonus_amount = Decimal(str(coupon_obj.bonus_amount or 0))
        
        # 统一检查和扣除托管余额（代理和House优惠券都需要）
        if not coupon_obj.remaining_amount or coupon_obj.remaining_amount < bonus_amount:
            return jsonify({
                'code': INSUFFICIENT_BALANCE_CODE,
                'data': None,
                'message': 'Insufficient coupon balance'
            }), 400

        # 统一扣除优惠券托管余额
        coupon_obj.used_amount = (coupon_obj.used_amount or Decimal('0')) + bonus_amount
        coupon_obj.remaining_amount = coupon_obj.remaining_amount - bonus_amount

        # 更新总领取次数统计（与Java自动派发保持一致）
        current_total_claims = coupon_obj.p_tt_jc or 0
        coupon_obj.p_tt_jc = current_total_claims + 1
        
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
        
        # 计算过期时间（如果优惠券有过期时间设置）
        now = datetime.now()
        expire_time = None
        if coupon_obj.p_expire:
            expire_time = coupon_obj.p_expire
        elif coupon_obj.p_end:
            expire_time = coupon_obj.p_end
        else:
            # 默认30天后过期
            expire_time = now + timedelta(days=30)
        
        # 创建领取记录
        member_coupon = MAppMemberCoupon(
            id=str(uuid.uuid4()),
            mb_id=user_id,
            p_id=coupon_obj.id,
            p_name=coupon_obj.pname,
            mb_username=member.username if hasattr(member, 'username') else None,
            money=bonus_amount,
            req_turnover=bonus_amount * (coupon_obj.turnover_rate or Decimal('1')),
            cur_turnover=Decimal('0'),
            # p_status='Active',
            status='Unused',
            mb_ip=ip_address,
            claim_time=now,  # 领取时间
            create_time=now,  # 创建时间与领取时间一致
            use_time=None,  # 使用时间，初始为空
            expire_time=expire_time,  # 过期时间
            start_time=coupon_obj.p_start,  # 活动开始时间
            end_time=coupon_obj.p_end,  # 活动结束时间
            game_hall=coupon_obj.p_lm_game_hall,  # 游戏平台限制
            game_type=coupon_obj.p_lm_game_type,  # 游戏类型限制
            # 根据优惠券类型设置奖金派发渠道和活动参与渠道
            jp_channel="Mobile Platform Coupon" if coupon_obj.fund_source_type == 'HOUSE' else "Mobile Agent Coupon",  # 奖金派发渠道
            ep_channel="Mobile Platform Redemption" if coupon_obj.fund_source_type == 'HOUSE' else "Mobile Agent Redemption",  # 活动参与渠道
            create_by_id=user_id,  # 创建人ID (移动端兑换时设为用户自己)
            del_flag=0,
            tenant_id='10000'
        )
        
        # 更新会员促销金额
        old_promotion = member.money_promotion if member.money_promotion else Decimal('0')
        new_promotion = old_promotion + bonus_amount
        member.money_promotion = new_promotion
        
        # 记录余额流水
        redeem_method = "ID" if redeem_type == 'id' else "Code"
        balance_log = AppMemberBalanceLog(
            id=str(uuid.uuid4()),
            sn=f"COUPON_{redeem_type.upper()}_{member_coupon.id}",
            type=TransactionType.CouponRedemption,
            type_sub=f"coupon_{redeem_type}_redeem",
            type_sub_data_id=member_coupon.id,
            mb_id=user_id,
            mb_username=member.name if hasattr(member, 'name') else member.username,
            money=bonus_amount,
            start_balance=old_promotion,
            end_balance=new_promotion,
            source=f"Coupon {redeem_method}",
            target="Promotion",
            status=1,
            source_status=1,
            create_time=datetime.now()
        )
        
        # 保存所有更改
        db.session.add(member_coupon)
        db.session.add(balance_log)
        db.session.add(coupon_obj)  # 统一保存优惠券变更（所有类型都需要更新托管余额）
        db.session.add(member)
        
        db.session.commit()
        
        # 记录成功的兑换尝试
        RiskManagementService.record_redemption_attempt(
            user_id=user_id,
            coupon_id=coupon_id,
            ip=ip_address,
            imei=None,  # 可以从请求中获取IMEI
            successful=True
        )
        
        return jsonify({
            'code': SUCCESS_CODE,
            'data': {
                'redemption_id': member_coupon.id,
                'coupon_name': coupon_obj.pname,
                'coupon_code': coupon_obj.pcode,
                'bonus_amount': float(bonus_amount),
                'new_promotion_balance': float(new_promotion),
                'turnover_requirement': float(member_coupon.req_turnover) if member_coupon.req_turnover else 0,
                'claim_time': member_coupon.claim_time.strftime('%Y-%m-%d %H:%M:%S') if member_coupon.claim_time else None,
                'expire_time': member_coupon.expire_time.strftime('%Y-%m-%d %H:%M:%S') if member_coupon.expire_time else None,
                'redeem_method': redeem_type
            },
            'message': f'Coupon redeemed successfully by {redeem_type}'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': SYSTEM_ERROR_CODE,
            'data': None,
            'message': str(e)
        }), 500


@coupon.route('/history', methods=['GET'])
@auth.login_required
def get_redemption_history():
    """获取用户的优惠券领取历史"""
    try:
        user_id = g.user.id
        page = int(request.args.get('page', 1))
        page_size = min(int(request.args.get('page_size', 20)), 100)
        status = request.args.get('status')  # 'Unused', 'Used', 'Expired'
        game_status = request.args.get('game_status')  # 游戏状态筛选（仅用于Used状态）
        start_time = request.args.get('start_time')  # 开始时间
        end_time = request.args.get('end_time')  # 结束时间
        time_type = request.args.get('time_type')  # 时间类型：'use_time' 或 'expire_time'
        
        # 构建查询
        query = MAppMemberCoupon.query.filter(
            MAppMemberCoupon.mb_id == user_id,
            MAppMemberCoupon.del_flag == 0
        )
        
        if status is not None:
            query = query.filter(MAppMemberCoupon.status == status)
        
        # 日期筛选 - 根据time_type筛选不同的时间字段
        if start_time and time_type:
            try:
                start_date = datetime.strptime(start_time, '%Y-%m-%d')
                if time_type == 'use_time':
                    # Used状态：筛选使用时间
                    query = query.filter(
                        or_(
                            MAppMemberCoupon.use_time >= start_date,
                            # 如果use_time为空，可能需要通过AppBetOrder的create_time判断
                            and_(
                                MAppMemberCoupon.use_time.is_(None),
                                MAppMemberCoupon.status == 'Used'
                            )
                        )
                    )
                elif time_type == 'expire_time':
                    # Expired状态：筛选过期时间
                    query = query.filter(MAppMemberCoupon.expire_time >= start_date)
            except ValueError:
                pass
                
        if end_time and time_type:
            try:
                end_date = datetime.strptime(end_time, '%Y-%m-%d')
                # 结束日期包含整天，所以加一天
                end_date = end_date + timedelta(days=1)
                if time_type == 'use_time':
                    # Used状态：筛选使用时间
                    query = query.filter(
                        or_(
                            MAppMemberCoupon.use_time < end_date,
                            # 如果use_time为空，可能需要通过AppBetOrder的create_time判断
                            and_(
                                MAppMemberCoupon.use_time.is_(None),
                                MAppMemberCoupon.status == 'Used'
                            )
                        )
                    )
                elif time_type == 'expire_time':
                    # Expired状态：筛选过期时间
                    query = query.filter(MAppMemberCoupon.expire_time < end_date)
            except ValueError:
                pass
        
        # 如果状态为Used且传入了game_status，则通过AppBetOrder进行筛选
        if status == 'Used' and game_status:
            # 需要通过AppBetOrder进行关联查询
            query = query.join(
                AppBetOrder,
                AppBetOrder.pro_id == MAppMemberCoupon.id
            ).filter(
                AppBetOrder.game_status == game_status,
                AppBetOrder.del_flag == 0
            )
        
        # 获取总数
        total_count = query.count()
        
        # 分页
        offset = (page - 1) * page_size
        history = query.order_by(MAppMemberCoupon.claim_time.desc()).offset(offset).limit(page_size).all()
        
        # 格式化返回数据
        history_list = []
        for h in history:
            # 获取优惠券信息
            coupon_obj = MAppCoupon.query.filter_by(id=h.p_id, del_flag=0).first()

            # 查询使用日期（通过AppBetOrder）
            game_status = None
            if h.status == 'Used':  # 已使用状态
                bet_order = AppBetOrder.query.filter_by(pro_id=h.id, del_flag=0).order_by(AppBetOrder.create_time.asc()).first()
                if bet_order:
                    game_status = bet_order.game_status if bet_order.game_status else None

            # 统计该优惠券的已使用次数（该用户使用该优惠券类型的次数）
            used_count = MAppMemberCoupon.query.filter(
                MAppMemberCoupon.mb_id == user_id,
                MAppMemberCoupon.p_id == h.p_id,
                MAppMemberCoupon.status == 'Used',
                MAppMemberCoupon.del_flag == 0
            ).count()

            # 获取总次数限制 p_lmu_j_pd
            usage_limit = coupon_obj.p_lmu_j_pd if coupon_obj and coupon_obj.p_lmu_j_pd else None

            # 获取最低投注金额
            min_bet_required = float(coupon_obj.min_bet_amount_required) if coupon_obj and coupon_obj.min_bet_amount_required else None

            history_info = {
                'id': h.id,
                'coupon_id': h.p_id,
                'coupon_name': h.p_name or (coupon_obj.pname if coupon_obj else 'Unknown'),
                'bonus_amount': float(h.money) if h.money else 0,
                'turnover_requirement': float(h.req_turnover) if h.req_turnover else 0,
                'turnover_progress': float(h.cur_turnover) if h.cur_turnover else 0,
                'status': h.status,
                'claim_time': h.claim_time.strftime('%Y-%m-%d %H:%M:%S') if h.claim_time else None,
                'use_time': h.use_time.strftime('%Y-%m-%d %H:%M:%S') if h.use_time else None,
                'game_status': game_status,  # 通过投注记录获取的比赛状态
                'start_time': h.start_time.strftime('%Y-%m-%d %H:%M:%S') if h.start_time else None,
                'end_time': h.end_time.strftime('%Y-%m-%d %H:%M:%S') if h.end_time else None,
                'expire_time': h.expire_time.strftime('%Y-%m-%d %H:%M:%S') if h.expire_time else None,
                'used_count': used_count,  # 该用户已使用该优惠券的次数
                'usage_limit': usage_limit,  # 总次数限制 p_lmu_j_pd
                'min_bet_required': min_bet_required  # 最低投注金额
            }
            history_list.append(history_info)
        
        # 统计信息
        total_redeemed = MAppMemberCoupon.query.filter(
            MAppMemberCoupon.mb_id == user_id,
            MAppMemberCoupon.del_flag == 0
        ).count()
        
        total_used = MAppMemberCoupon.query.filter(
            MAppMemberCoupon.mb_id == user_id,
            MAppMemberCoupon.status == 1,
            MAppMemberCoupon.del_flag == 0
        ).count()
        
        total_bonus = db.session.query(func.sum(MAppMemberCoupon.money)).filter(
            MAppMemberCoupon.mb_id == user_id,
            MAppMemberCoupon.del_flag == 0
        ).scalar() or Decimal('0')
        
        return jsonify({
            'code': SUCCESS_CODE,
            'data': {
                'history': history_list,
                'pagination': {
                    'current_page': page,
                    'page_size': page_size,
                    'total_count': total_count,
                    'total_pages': (total_count + page_size - 1) // page_size
                },
                'statistics': {
                    'total_redeemed': total_redeemed,
                    'total_used': total_used,
                    'total_unused': total_redeemed - total_used,
                    'total_bonus_amount': float(total_bonus)
                }
            },
            'message': 'success'
        }), 200
        
    except Exception as e:
        return jsonify({
            'code': SYSTEM_ERROR_CODE,
            'data': None,
            'message': str(e)
        }), 500


@coupon.route('/progress/<string:coupon_id>', methods=['GET'])
@auth.login_required
def get_coupon_progress(coupon_id):
    """获取用户在特定优惠券的使用进度"""
    try:
        user_id = g.user.id

        # 获取用户的优惠券领取记录
        member_coupon = MAppMemberCoupon.query.filter_by(
            mb_id=user_id,
            p_id=coupon_id,
            del_flag=0
        ).order_by(MAppMemberCoupon.claim_time.desc()).first()

        if not member_coupon:
            return jsonify({
                'code': SUCCESS_CODE,
                'data': {
                    'has_claimed': False,
                    'message': 'Coupon not claimed yet'
                },
                'message': 'success'
            }), 200

        # 获取优惠券信息
        coupon_obj = MAppCoupon.query.filter_by(
            id=coupon_id,
            del_flag=0
        ).first()

        if not coupon_obj:
            return jsonify({
                'code': COUPON_NOT_FOUND_CODE,
                'data': None,
                'message': 'Coupon does not exist'
            }), 404

        # 计算流水进度
        progress_percentage = 0
        if member_coupon.req_turnover and member_coupon.req_turnover > 0:
            progress_percentage = float(
                (member_coupon.cur_turnover / member_coupon.req_turnover) * 100
            )
            progress_percentage = min(100, progress_percentage)

        # 检查是否已过期
        is_expired = False
        if member_coupon.expire_time:
            is_expired = member_coupon.expire_time < datetime.now()

        return jsonify({
            'code': SUCCESS_CODE,
            'data': {
                'has_claimed': True,
                'coupon_name': member_coupon.p_name or coupon_obj.pname,
                'bonus_amount': float(member_coupon.money) if member_coupon.money else 0,
                'turnover_requirement': float(member_coupon.req_turnover) if member_coupon.req_turnover else 0,
                'turnover_progress': float(member_coupon.cur_turnover) if member_coupon.cur_turnover else 0,
                'progress_percentage': progress_percentage,
                'status': member_coupon.status,
                'status_text': 'Used' if member_coupon.status == 1 else 'Unused',
                'can_use': member_coupon.status == 0 and progress_percentage >= 100 and not is_expired,
                'claim_time': member_coupon.claim_time.strftime('%Y-%m-%d %H:%M:%S') if member_coupon.claim_time else None,
                'use_time': member_coupon.use_time.strftime('%Y-%m-%d %H:%M:%S') if member_coupon.use_time else None,
                'expire_time': member_coupon.expire_time.strftime('%Y-%m-%d %H:%M:%S') if member_coupon.expire_time else None,
                'is_expired': is_expired
            },
            'message': 'success'
        }), 200

    except Exception as e:
        return jsonify({
            'code': SYSTEM_ERROR_CODE,
            'data': None,
            'message': str(e)
        }), 500


@coupon.route('/available_for_bet', methods=['POST'])
@auth.login_required
def get_available_coupons_for_bet():
    """获取用户可用于下注的优惠券列表

    筛选条件：
    1. status为Unused（未使用）
    2. expire_time未超过当前时间
    3. 根据p_id在m_app_coupon表查询优惠券要求
    4. 满足用户使用次数上限p_lmu_j_pd（每日使用次数）
    5. 满足最低投注金额要求min_bet_amount_required
    """
    try:
        user_id = g.user.id
        data = request.json
        bet_amount = data.get('bet_amount', 0)

        # 将投注金额转换为Decimal以便比较
        bet_amount_decimal = Decimal(str(bet_amount)) if bet_amount else Decimal('0')

        now = datetime.now()

        # 查询用户未使用且未过期的优惠券
        member_coupons = MAppMemberCoupon.query.filter(
            MAppMemberCoupon.mb_id == user_id,
            MAppMemberCoupon.status == 'Unused',
            MAppMemberCoupon.del_flag == 0,
            or_(
                MAppMemberCoupon.expire_time.is_(None),
                MAppMemberCoupon.expire_time > now
            )
        ).all()

        available_coupons = []

        for mc in member_coupons:
            # 获取对应的优惠券配置
            coupon_config = MAppCoupon.query.filter_by(
                id=mc.p_id,
                del_flag=0
            ).first()

            if not coupon_config:
                continue

            # 检查优惠券配置的最低投注金额要求
            # 使用 min_bet_amount_required 字段（使用优惠券所需的最低投注金额）
            min_bet_required = Decimal('0')
            if hasattr(coupon_config, 'min_bet_amount_required') and coupon_config.min_bet_amount_required:
                min_bet_required = Decimal(str(coupon_config.min_bet_amount_required))

            # 检查投注金额是否满足最低要求
            # 如果优惠券要求最低投注金额，但用户投注金额不足，则跳过该优惠券
            if min_bet_required > 0 and bet_amount_decimal < min_bet_required:
                continue

            # 检查总使用次数限制（p_lmu_j_pd）
            if coupon_config.p_lmu_j_pd and coupon_config.p_lmu_j_pd > 0:
                # 统计该用户使用该优惠券的总次数
                total_usage_count = MAppMemberCoupon.query.filter(
                    MAppMemberCoupon.mb_id == user_id,
                    MAppMemberCoupon.p_id == mc.p_id,
                    MAppMemberCoupon.status == 'Used',
                    MAppMemberCoupon.del_flag == 0
                ).count()

                # 如果已经达到使用次数上限，则跳过
                if total_usage_count >= coupon_config.p_lmu_j_pd:
                    continue

            # 构建返回数据
            coupon_info = {
                'member_coupon_id': mc.id,  # 用户优惠券记录ID
                'coupon_id': mc.p_id,  # 优惠券配置ID
                'coupon_name': mc.p_name or (coupon_config.p_name if coupon_config else 'Unknown'),
                'bonus_amount': float(mc.money) if mc.money else 0,
                'min_bet_required': float(min_bet_required),
                'claim_time': mc.claim_time.strftime('%Y-%m-%d %H:%M:%S') if mc.claim_time else None,
                'expire_time': mc.expire_time.strftime('%Y-%m-%d %H:%M:%S') if mc.expire_time else None,
                'turnover_requirement': float(mc.req_turnover) if mc.req_turnover else 0,
                'turnover_progress': float(mc.cur_turnover) if mc.cur_turnover else 0
            }

            available_coupons.append(coupon_info)

        return jsonify({
            'code': SUCCESS_CODE,
            'data': {
                'coupons': available_coupons,
                'total_count': len(available_coupons)
            },
            'message': 'success'
        }), 200

    except Exception as e:
        return jsonify({
            'code': SYSTEM_ERROR_CODE,
            'data': None,
            'message': str(e)
        }), 500


