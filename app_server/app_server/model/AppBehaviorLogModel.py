from app_server import db, app
from sqlalchemy import Column, String, DateTime, Integer, SmallInteger, JSON
from decimal import Decimal
import datetime

from app_server.utils.BaseSaasModel import BaseSaasModel
from app_server.utils.Kits import Kits
from app_server.model.SysTenantModel import SysTenant


class AppBehaviorLog(BaseSaasModel):
    __tablename__ = 'm_app_behavior_log'

    # 主键
    id = Column(String(64), primary_key=True, comment="主键ID")
    aid = Column(String(64), comment="代理ID")
    # 业务关联（灵活设计）
    business_type = Column(String(50), index=True, comment="业务类型(adlink-广告链接/promotion-活动/coupon-优惠券)")
    business_id = Column(String(64), index=True, comment="业务ID")

    # 用户关联
    member_id = Column(String(64), index=True, comment="会员ID(注册后关联)")
    session_id = Column(String(100), index=True, comment="会话ID(追踪同一用户多次访问)")

    # 事件信息
    event_type = Column(String(50), index=True, comment="事件类型(visit/register/login/deposit/bet/withdraw)")
    event_time = Column(DateTime, index=True, comment="事件发生时间")

    # 核心追踪参数
    utm_source = Column(String(100), index=True, comment="UTM来源")
    utm_campaign = Column(String(200), index=True, comment="UTM活动名称")

    # 设备与访问信息
    access_channel = Column(String(50), index=True, comment="访问途径(h5/app/pc)")
    app_version = Column(String(50), comment="APP版本号")
    device_type = Column(String(50), index=True, comment="设备类型(mobile/tablet/desktop)")
    ip_address = Column(String(50), comment="IP地址")
    country = Column(String(100), comment="国家")
    city = Column(String(100), comment="城市")

    # 浏览器和系统信息
    os = Column(String(50), comment="操作系统名称")
    browser = Column(String(50), comment="浏览器名称")
    referrer = Column(String(500), comment="来源页面完整URL")
    user_agent = Column(String(1000), comment="完整的用户代理字符串")

    # 转化标识
    is_converted = Column(SmallInteger, server_default='0', index=True, comment="是否已转化(0-未转化/1-已转化)")
    converted_time = Column(DateTime, comment="转化时间")

    # 扩展信息（JSON格式存储非核心字段）
    extra_data = Column(JSON, comment="扩展数据(utm_medium/utm_content/utm_term等)")
    event_params = Column(JSON, comment="事件参数(JSON格式存储事件相关的自定义参数)")

    # 注意：remark 字段已在 BaseSaasModel 中定义为 remarks

    __mapper_args__ = {
        "order_by": event_time.desc(),
    }

    @staticmethod
    def add_behavior_log(request, business_type, business_id, event_type, member_id=None, session_id=None,
                        utm_source=None, utm_campaign=None, access_channel=None, app_version=None,
                        device_type=None, extra_data=None, event_params=None, remark=None):
        """
        通用的添加行为日志方法
        :param request: Flask request对象
        :param business_type: 业务类型(adlink-广告链接/promotion-活动/coupon-优惠券)
        :param business_id: 业务ID
        :param event_type: 事件类型(visit/register/login/deposit/bet/withdraw)
        :param member_id: 会员ID(可选)
        :param session_id: 会话ID(可选)
        :param utm_source: UTM来源(可选)
        :param utm_campaign: UTM活动名称(可选)
        :param access_channel: 访问途径(可选)
        :param app_version: APP版本号(可选)
        :param device_type: 设备类型(可选)
        :param extra_data: 扩展数据(可选)
        :param event_params: 事件参数(可选)
        :param remark: 备注(可选)
        :return: AppBehaviorLog对象
        """
        try:
            # 获取租户ID
            tenant_id = SysTenant.get_tenant_id(request)

            # 获取客户端信息
            client_info = Kits.client_info(request)

            # 创建日志对象
            log = AppBehaviorLog()
            log.id = str(Kits.generate_uuid())
            log.tenant_id = tenant_id
            log.business_type = business_type
            log.business_id = business_id
            log.event_type = event_type
            log.event_time = datetime.datetime.now()

            # 用户关联
            log.member_id = member_id
            log.session_id = session_id if session_id else request.cookies.get('session_id')

            # 获取用户的代理ID
            if member_id:
                try:
                    from app_server.model.AppMemberModel import AppMember
                    member = AppMember.query.filter_by(id=member_id).first()
                    if member and member.aid:
                        log.aid = member.aid
                except Exception as e:
                    app.logger.warning(f"Failed to get member aid for {member_id}: {str(e)}")

            # UTM参数（从request参数或函数参数获取）
            log.utm_source = utm_source or request.args.get('utm_source')
            log.utm_campaign = utm_campaign or request.args.get('utm_campaign')

            # 设备与访问信息
            log.access_channel = access_channel
            log.app_version = app_version
            log.device_type = device_type or ('mobile' if client_info.get('device') in ['Mobile', 'Tablet'] else 'desktop')
            log.ip_address = client_info.get('ip_address')

            # 扩展数据
            if extra_data is None:
                extra_data = {}
            extra_data['utm_medium'] = request.args.get('utm_medium')
            extra_data['utm_content'] = request.args.get('utm_content')
            extra_data['utm_term'] = request.args.get('utm_term')
            extra_data['user_agent'] = client_info.get('user_agent')
            extra_data['referrer'] = request.headers.get('Referer')
            extra_data['browser'] = client_info.get('browser')
            extra_data['os'] = client_info.get('os')
            log.extra_data = extra_data

            # 转化标识默认为未转化
            log.is_converted = 0

            # 事件参数和备注
            log.event_params = event_params
            log.remarks = remark

            # 保存到数据库
            db.session.add(log)
            db.session.commit()

            return log
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"添加行为日志失败: {str(e)}")
            return None

    @staticmethod
    def add_adlink_log(request, adlink_id, event_type, member_id=None, session_id=None, event_params=None, remark=None):
        """
        添加广告链接行为日志（简化参数）
        :param request: Flask request对象
        :param adlink_id: 广告链接ID
        :param event_type: 事件类型(visit/register/login/deposit/bet/withdraw)
        :param member_id: 会员ID(可选)
        :param session_id: 会话ID(可选)
        :param event_params: 事件参数(可选)
        :param remark: 备注(可选)
        :return: AppBehaviorLog对象
        """
        return AppBehaviorLog.add_behavior_log(
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
    def add_promotion_log(request, promotion_id, event_type, member_id=None, session_id=None, event_params=None, remark=None):
        """
        添加活动行为日志（简化参数）
        :param request: Flask request对象
        :param promotion_id: 活动ID
        :param event_type: 事件类型(visit/register/login/deposit/bet/withdraw)
        :param member_id: 会员ID(可选)
        :param session_id: 会话ID(可选)
        :param event_params: 事件参数(可选)
        :param remark: 备注(可选)
        :return: AppBehaviorLog对象
        """
        return AppBehaviorLog.add_behavior_log(
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
    def add_coupon_log(request, coupon_id, event_type, member_id=None, session_id=None, event_params=None, remark=None):
        """
        添加优惠券行为日志（简化参数）
        :param request: Flask request对象
        :param coupon_id: 优惠券ID
        :param event_type: 事件类型(visit/register/login/deposit/bet/withdraw)
        :param member_id: 会员ID(可选)
        :param session_id: 会话ID(可选)
        :param event_params: 事件参数(可选)
        :param remark: 备注(可选)
        :return: AppBehaviorLog对象
        """
        return AppBehaviorLog.add_behavior_log(
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
    def add_general_log(request, event_type, member_id=None, session_id=None, extra_data=None, event_params=None, remark=None):
        """
        添加通用行为日志（不关联具体业务）
        :param request: Flask request对象
        :param event_type: 事件类型(visit/register/login/deposit/bet/withdraw)
        :param member_id: 会员ID(可选)
        :param session_id: 会话ID(可选)
        :param extra_data: 扩展数据(可选)
        :param event_params: 事件参数(可选)
        :param remark: 备注(可选)
        :return: AppBehaviorLog对象
        """
        return AppBehaviorLog.add_behavior_log(
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
