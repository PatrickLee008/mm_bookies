from app_server import app, db
from app_server.model.AppBehaviorLogModel import AppBehaviorLog
from app_server.model.SysTenantModel import SysTenant
from app_server.model.AppAdlinkModel import AppAdlink
from app_server.model.MAppCouponModel import MAppCoupon
from app_server.model.MAppInvitationActivityModel import MAppInvitationActivity
from app_server.model.AppMemberModel import AppMember
from app_server.utils.Kits import Kits
import datetime


class AppBehaviorLogService:
    """用户行为日志服务"""

    @staticmethod
    def _get_business_info(business_type, business_id):
        """
        获取业务信息（名称）

        Args:
            business_type: 业务类型
            business_id: 业务ID

        Returns:
            str: 业务名称，如果未找到返回 None
        """
        try:
            if not business_type or not business_id:
                return None

            # 根据业务类型查询对应的表
            if business_type == 'adlink':
                # 查询广告链接表
                adlink = AppAdlink.query.filter_by(id=business_id, del_flag=0).first()
                if adlink:
                    return f"Adlink: {adlink.campaign_name or 'Unknown'}"

            elif business_type == 'promotion':
                # 查询活动表
                promotion = MAppInvitationActivity.query.filter_by(id=business_id, del_flag=0).first()
                if promotion:
                    return f"Promotion: {promotion.title or 'Unknown'}"

            elif business_type == 'coupon':
                # 查询优惠券表
                coupon = MAppCoupon.query.filter_by(id=business_id).first()
                if coupon:
                    return f"Coupon: {coupon.p_name or 'Unknown'}"

            return None

        except Exception as e:
            app.logger.warning(f"Failed to get business info: {str(e)}")
            return None

    @staticmethod
    def _update_adlink_stats(adlink_id, event_type):
        """
        更新广告链接的统计字段

        Args:
            adlink_id: 广告链接ID
            event_type: 事件类型

        根据事件类型更新对应的统计字段：
        - visit -> clicks
        - register -> registrations
        - download -> downloads
        - install -> installs
        """
        try:
            # 定义事件类型与字段的映射关系
            event_field_mapping = {
                'visit': 'clicks',
                'register': 'registrations',
                'download': 'downloads',
                'install': 'installs'
            }

            # 检查是否需要更新统计
            field_name = event_field_mapping.get(event_type)
            if not field_name:
                # 如果事件类型不在映射中，不做处理
                return

            # 查询广告链接记录
            adlink = AppAdlink.query.filter_by(id=adlink_id, del_flag=0).first()
            if not adlink:
                app.logger.warning(f"Adlink not found for stats update: {adlink_id}")
                return

            # 对应字段自增1
            current_value = getattr(adlink, field_name, 0) or 0
            setattr(adlink, field_name, current_value + 1)

            app.logger.info(f"Updated adlink {adlink_id} {field_name}: {current_value} -> {current_value + 1}")

        except Exception as e:
            app.logger.error(f"Failed to update adlink stats: {str(e)}")
            # 不抛出异常，避免影响主流程
            pass

    @staticmethod
    def add_behavior_log(request, business_type=None, business_id=None, event_type=None,
                        member_id=None, session_id=None, utm_source=None, utm_campaign=None,
                        access_channel=None, app_version=None, device_type=None,
                        extra_data=None, event_params=None, remark=None):
        """
        添加行为日志（通用方法）

        Args:
            request: Flask request对象
            business_type: 业务类型(adlink-广告链接/promotion-活动/coupon-优惠券/general-通用)
            business_id: 业务ID
            event_type: 事件类型(visit/register/login/deposit/bet/withdraw)
            member_id: 会员ID
            session_id: 会话ID
            utm_source: UTM来源
            utm_campaign: UTM活动名称
            access_channel: 访问途径(h5/app/pc)
            app_version: APP版本号
            device_type: 设备类型
            extra_data: 扩展数据(dict)
            event_params: 事件参数(dict)
            remark: 备注

        Returns:
            dict: {'success': True/False, 'message': str, 'data': log_id}
        """
        try:
            # 参数验证
            if not event_type:
                return {'success': False, 'message': 'event_type is required'}

            # 业务类型特定验证
            if business_type in ['adlink', 'promotion', 'coupon'] and not business_id:
                return {'success': False, 'message': f'business_id is required for {business_type} type'}

            member = None
            if member_id:
                member = AppMember.query.filter_by(id=member_id).first()
            # 强制一种业务类型
            if business_type is None and member and member.ad_link_id:
                # 获取用户是否是通过推广连接推广的
                business_type = 'adlink'
                business_id = member.ad_link_id

            # 获取租户ID
            tenant_id = SysTenant.get_tenant_id(request)

            # 获取客户端信息
            client_info = Kits.client_info(request)

            # 获取请求头信息（app_version、access_channel）
            header_info = Kits.get_behavior_log_headers(request)

            # 创建日志对象
            log = AppBehaviorLog()
            log.id = str(Kits.generate_uuid())
            log.tenant_id = tenant_id
            log.business_type = business_type or 'general'
            log.business_id = business_id
            log.event_type = event_type
            log.event_time = datetime.datetime.now()

            # 用户关联
            log.member_id = member_id
            log.session_id = session_id if session_id else request.cookies.get('session_id')

            # 获取用户的代理ID
            if member and member.aid:
                log.aid = member.aid

            # UTM参数（优先使用传入参数，否则从URL参数获取）
            log.utm_source = utm_source or request.args.get('utm_source')
            log.utm_campaign = utm_campaign or request.args.get('utm_campaign')

            # 设备与访问信息（优先使用请求头中的信息，参数值作为备用）
            log.access_channel = access_channel or header_info.get('access_channel')
            log.app_version = app_version or header_info.get('app_version')
            log.device_type = device_type or ('mobile' if client_info.get('device') in ['Mobile', 'Tablet'] else 'desktop')
            log.ip_address = client_info.get('ip_address')

            # 浏览器和系统信息（独立字段）
            log.os = client_info.get('os')
            log.browser = client_info.get('browser')
            log.referrer = request.headers.get('Referer')
            log.user_agent = client_info.get('user_agent')

            # 扩展数据（合并URL参数和传入的扩展数据）
            if extra_data is None:
                extra_data = {}
            extra_data['utm_medium'] = request.args.get('utm_medium')
            extra_data['utm_content'] = request.args.get('utm_content')
            extra_data['utm_term'] = request.args.get('utm_term')
            log.extra_data = extra_data

            # 事件参数和备注
            log.event_params = event_params

            # 获取业务名称并拼接到备注
            business_info = AppBehaviorLogService._get_business_info(business_type, business_id)
            if business_info:
                # 如果有用户传入的备注，拼接在业务信息后面
                if remark:
                    log.remarks = f"{business_info} | {remark}"
                else:
                    log.remarks = business_info
            else:
                log.remarks = remark

            # 转化标识默认为未转化
            log.is_converted = 0

            # 保存到数据库
            db.session.add(log)

            # 如果是广告链接类型，更新对应的统计字段
            if business_type == 'adlink' and business_id:
                AppBehaviorLogService._update_adlink_stats(business_id, event_type)

            db.session.commit()

            return {
                'success': True,
                'message': 'Behavior log added successfully',
                'data': log.id
            }

        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Failed to add behavior log: {str(e)}")
            return {
                'success': False,
                'message': f'Failed to add behavior log: {str(e)}'
            }

    @staticmethod
    def add_adlink_log(request, adlink_id, event_type, member_id=None, session_id=None,
                      event_params=None, remark=None):
        """
        添加广告链接行为日志（简化方法）

        Args:
            request: Flask request对象
            adlink_id: 广告链接ID
            event_type: 事件类型
            member_id: 会员ID
            session_id: 会话ID
            event_params: 事件参数
            remark: 备注

        Returns:
            dict: {'success': True/False, 'message': str, 'data': log_id}
        """
        if not adlink_id:
            return {'success': False, 'message': 'adlink_id is required'}

        return AppBehaviorLogService.add_behavior_log(
            request=request,
            business_type='adlink',
            business_id=adlink_id,
            event_type=event_type,
            member_id=member_id,
            session_id=session_id,
            event_params=event_params,
            remark=remark
        )

    @staticmethod
    def add_promotion_log(request, promotion_id, event_type, member_id=None, session_id=None,
                         event_params=None, remark=None):
        """
        添加活动行为日志（简化方法）

        Args:
            request: Flask request对象
            promotion_id: 活动ID
            event_type: 事件类型
            member_id: 会员ID
            session_id: 会话ID
            event_params: 事件参数
            remark: 备注

        Returns:
            dict: {'success': True/False, 'message': str, 'data': log_id}
        """
        if not promotion_id:
            return {'success': False, 'message': 'promotion_id is required'}

        return AppBehaviorLogService.add_behavior_log(
            request=request,
            business_type='promotion',
            business_id=promotion_id,
            event_type=event_type,
            member_id=member_id,
            session_id=session_id,
            event_params=event_params,
            remark=remark
        )

    @staticmethod
    def add_coupon_log(request, coupon_id, event_type, member_id=None, session_id=None,
                      event_params=None, remark=None):
        """
        添加优惠券行为日志（简化方法）

        Args:
            request: Flask request对象
            coupon_id: 优惠券ID
            event_type: 事件类型
            member_id: 会员ID
            session_id: 会话ID
            event_params: 事件参数
            remark: 备注

        Returns:
            dict: {'success': True/False, 'message': str, 'data': log_id}
        """
        if not coupon_id:
            return {'success': False, 'message': 'coupon_id is required'}

        return AppBehaviorLogService.add_behavior_log(
            request=request,
            business_type='coupon',
            business_id=coupon_id,
            event_type=event_type,
            member_id=member_id,
            session_id=session_id,
            event_params=event_params,
            remark=remark
        )

    @staticmethod
    def add_general_log(request, event_type, member_id=None, session_id=None,
                       extra_data=None, event_params=None, remark=None):
        """
        添加通用行为日志（简化方法）

        Args:
            request: Flask request对象
            event_type: 事件类型
            member_id: 会员ID
            session_id: 会话ID
            extra_data: 扩展数据
            event_params: 事件参数
            remark: 备注

        Returns:
            dict: {'success': True/False, 'message': str, 'data': log_id}
        """
        return AppBehaviorLogService.add_behavior_log(
            request=request,
            business_type='general',
            business_id=None,
            event_type=event_type,
            member_id=member_id,
            session_id=session_id,
            extra_data=extra_data,
            event_params=event_params,
            remark=remark
        )

    @staticmethod
    def mark_as_converted(log_id, converted_time=None):
        """
        标记日志为已转化

        Args:
            log_id: 日志ID
            converted_time: 转化时间（可选，默认为当前时间）

        Returns:
            dict: {'success': True/False, 'message': str}
        """
        try:
            log = AppBehaviorLog.query.filter_by(id=log_id).first()
            if not log:
                return {'success': False, 'message': 'Log not found'}

            log.is_converted = 1
            log.converted_time = converted_time or datetime.datetime.now()
            db.session.commit()

            return {'success': True, 'message': 'Marked as converted successfully'}

        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Failed to mark as converted: {str(e)}")
            return {'success': False, 'message': f'Failed to mark as converted: {str(e)}'}

    @staticmethod
    def get_logs_by_member(member_id, limit=100, offset=0):
        """
        根据会员ID获取行为日志

        Args:
            member_id: 会员ID
            limit: 返回数量限制
            offset: 偏移量

        Returns:
            dict: {'success': True/False, 'data': [...], 'total': int}
        """
        try:
            query = AppBehaviorLog.query.filter_by(member_id=member_id, del_flag=0)
            total = query.count()
            logs = query.order_by(AppBehaviorLog.event_time.desc()).offset(offset).limit(limit).all()

            return {
                'success': True,
                'data': [log.to_dict() for log in logs],
                'total': total
            }

        except Exception as e:
            app.logger.error(f"Failed to query behavior logs: {str(e)}")
            return {'success': False, 'message': f'Query failed: {str(e)}'}

    @staticmethod
    def get_logs_by_business(business_type, business_id, limit=100, offset=0):
        """
        根据业务类型和业务ID获取行为日志

        Args:
            business_type: 业务类型
            business_id: 业务ID
            limit: 返回数量限制
            offset: 偏移量

        Returns:
            dict: {'success': True/False, 'data': [...], 'total': int}
        """
        try:
            query = AppBehaviorLog.query.filter_by(
                business_type=business_type,
                business_id=business_id,
                del_flag=0
            )
            total = query.count()
            logs = query.order_by(AppBehaviorLog.event_time.desc()).offset(offset).limit(limit).all()

            return {
                'success': True,
                'data': [log.to_dict() for log in logs],
                'total': total
            }

        except Exception as e:
            app.logger.error(f"Failed to query behavior logs: {str(e)}")
            return {'success': False, 'message': f'Query failed: {str(e)}'}
