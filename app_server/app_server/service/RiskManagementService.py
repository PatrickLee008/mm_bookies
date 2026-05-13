from datetime import datetime, timedelta
from decimal import Decimal
from collections import defaultdict
from typing import Dict, List, Set, Optional, Tuple, Any
import hashlib
import logging
from threading import Lock

logger = logging.getLogger(__name__)


# 延迟导入 Model，避免循环导入
def get_blacklist_model():
    """延迟导入黑名单模型"""
    try:
        from app_server.model.RiskBlacklistModel import RiskBlacklist
        return RiskBlacklist
    except ImportError:
        logger.warning("无法导入 RiskBlacklist 模型，黑名单检查将被跳过")
        return None


class RiskManagementService:
    """
    风险管理服务
    负责处理优惠券兑换的风险控制，防止滥用
    """

    # 单例模式
    _instance = None
    _lock = Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """初始化服务"""
        # 内存缓存，用于临时存储风险控制数据
        self.ip_attempts: Dict[str, List[RedemptionAttempt]] = defaultdict(list)
        self.imei_attempts: Dict[str, List[RedemptionAttempt]] = defaultdict(list)
        self.device_attempts: Dict[str, List[RedemptionAttempt]] = defaultdict(list)

        # 配置默认值（简化版：只包含核心配置）
        self.default_config = {
            'ip_limit_count': 10,  # IP限制次数
            'ip_time_window_hours': 1,  # IP时间窗口（小时）
            'imei_limit_count': 5  # IMEI/设备ID限制次数
        }

    @staticmethod
    def assess_redemption_risk(user_id: str, coupon_id: str, ip: str,
                               imei: Optional[str] = None, user_agent: Optional[str] = None,
                               location: Optional[str] = None,
                               coupon_config: Optional[Dict[str, Any]] = None,
                               aid: Optional[str] = None,
                               activity_type: Optional[str] = 'Coupon',
                               username: Optional[str] = None) -> Dict[str, Any]:
        """
        综合风险评估（简化版）

        核心检查项：
        1. 黑名单检查（支持多层级：全面/代理级/活动级）
        2. IMEI/设备ID 限制（全局限制，时间窗口内）
        3. IP 限流检查（全局限制，时间窗口内）

        Args:
            user_id: 用户ID
            coupon_id: 优惠券ID
            ip: 用户IP地址
            imei: 设备唯一标识 (IMEI/Device ID)
            user_agent: 浏览器用户代理（保留参数但不使用）
            location: 用户位置信息（保留参数但不使用）
            coupon_config: 优惠券风险配置
            aid: 代理ID（可选）
            activity_type: 活动类型（默认：Coupon，支持 Coupon/Promotion/Invitation）
            username: 用户名（可选，用于黑名单检查）

        Returns:
            风险评估结果字典
        """
        service = RiskManagementService()
        config = {**service.default_config, **(coupon_config or {})}

        # 规范化活动类型
        RiskBlacklist = get_blacklist_model()
        if RiskBlacklist:
            activity_type = RiskBlacklist.normalize_activity_type(activity_type)

        try:
            logger.info(
                f"开始风险评估: user_id={user_id}, username={username}, coupon_id={coupon_id}, ip={ip}, device_id={imei}, aid={aid}, activity_type={activity_type}")

            # 1. 黑名单检查（基于活动类型和ID匹配）
            blacklist_result = service._check_blacklist(
                user_id=user_id,
                username=username,
                ip=ip,
                imei=imei,
                activity_type=activity_type,
                activity_id=coupon_id
            )
            if not blacklist_result['allowed']:
                logger.warning(f"黑名单拦截: {blacklist_result['reason']}")
                return blacklist_result

            # 2. IMEI/设备ID 限制检查（全局限制）
            if imei:
                imei_result = service._check_imei_restrictions(imei, coupon_id, config)
                if not imei_result['allowed']:
                    logger.warning(f"设备限制拦截: {imei_result['reason']}")
                    return imei_result

            # 3. IP地址限流检查（全局限制）
            ip_result = service._check_ip_throttling(ip, coupon_id, config)
            if not ip_result['allowed']:
                logger.warning(f"IP限制拦截: {ip_result['reason']}")
                return ip_result

            # 所有检查通过
            logger.info(f"风险评估通过: user_id={user_id}, coupon_id={coupon_id}")
            return {
                'allowed': True,
                'reason': 'Risk assessment passed',
                'risk_level': 'LOW',
                'details': {
                    'checks_passed': ['blacklist', 'imei_restriction', 'ip_throttling'],
                    'assessment_time': datetime.now().isoformat()
                }
            }

        except Exception as e:
            logger.error(f"风险评估失败: {str(e)}")
            return {
                'allowed': False,
                'reason': f'Risk assessment system error: {str(e)}',
                'risk_level': 'HIGH',
                'details': {'error': str(e)}
            }

    def _check_blacklist(self, user_id: str, ip: str, imei: Optional[str],
                         activity_type: Optional[str] = None,
                         activity_id: Optional[str] = None,
                         username: Optional[str] = None) -> Dict[str, Any]:
        """
        黑名单检查（直接查询数据库，基于活动类型和ID匹配）

        黑名单匹配逻辑（基于 activity_type 和 activity_id）：
        1. 全局黑名单：黑名单的 activity_type=NULL, activity_id=NULL
        2. 类型级黑名单：黑名单的 activity_type=当前类型, activity_id=NULL
        3. 活动级黑名单：黑名单的 activity_type=当前类型, activity_id=当前活动

        注意：
        - aid（代理ID）仅用于权限管理，不参与匹配
        - source_activity_type/id 仅用于追溯，不参与匹配
        - User类型黑名单检查username字段
        """
        try:
            RiskBlacklist = get_blacklist_model()
            if not RiskBlacklist:
                # 如果模型不可用，跳过黑名单检查
                return {'allowed': True, 'reason': 'Blacklist check skipped (model unavailable)', 'risk_level': 'LOW'}

            # 检查用户名黑名单（User类型黑名单使用username进行匹配）
            if username and RiskBlacklist.is_blacklisted('User', username, activity_type=activity_type,
                                                         activity_id=activity_id):
                logger.warning(f"用户在黑名单中: username={username}, activity={activity_type}:{activity_id}")
                return {
                    'allowed': False,
                    'reason': 'User is blacklisted',
                    'risk_level': 'HIGH'
                }

            # 检查IP黑名单（支持新旧类型值）
            if RiskBlacklist.is_blacklisted('IP Address', ip, activity_type=activity_type, activity_id=activity_id):
                logger.warning(f"IP在黑名单中: ip={ip}, activity={activity_type}:{activity_id}")
                return {
                    'allowed': False,
                    'reason': 'IP address is blacklisted',
                    'risk_level': 'HIGH'
                }

            # 检查设备ID黑名单（支持新旧类型值）
            if imei and RiskBlacklist.is_blacklisted('Device ID', imei, activity_type=activity_type,
                                                     activity_id=activity_id):
                logger.warning(f"设备在黑名单中: device_id={imei}, activity={activity_type}:{activity_id}")
                return {
                    'allowed': False,
                    'reason': 'Device is blacklisted',
                    'risk_level': 'HIGH'
                }

            return {'allowed': True, 'reason': 'Blacklist check passed', 'risk_level': 'LOW'}

        except Exception as e:
            logger.error(f"黑名单检查失败: {str(e)}")
            # 黑名单检查失败时，允许通过，避免影响正常业务
            return {'allowed': True, 'reason': f'Blacklist check error: {str(e)}', 'risk_level': 'LOW'}

    def _check_imei_restrictions(self, imei: str, coupon_id: str, config: Dict) -> Dict[str, Any]:
        """IMEI限制检查 - 针对当前优惠券的限制"""
        imei_limit = config.get('imei_limit_count', 5)
        time_window_hours = config.get('ip_time_window_hours', 1)  # 使用相同的时间窗口

        # 如果限制次数为0或负数，或时间窗口为0，跳过检查
        if imei_limit <= 0 or time_window_hours <= 0:
            return {'allowed': True, 'reason': 'No IMEI restriction', 'risk_level': 'LOW'}

        # 计算时间窗口
        window_start = datetime.now() - timedelta(hours=time_window_hours)

        # 检查该IMEI在时间窗口内对当前优惠券的成功兑换次数
        successful_redemptions = sum(
            1 for attempt in self.imei_attempts.get(imei, [])
            if attempt.timestamp > window_start and attempt.successful and attempt.coupon_id == coupon_id
        )

        if successful_redemptions >= imei_limit:
            return {
                'allowed': False,
                'reason': f'You have reached the limit for this device ({imei_limit} time{"s" if imei_limit > 1 else ""} per {time_window_hours}h). Please try again later.',
                'risk_level': 'HIGH',
                'details': {
                    'imei_redemption_count': successful_redemptions,
                    'imei_limit': imei_limit,
                    'time_window_hours': time_window_hours,
                    'message': f'Device limit: {imei_limit} per {time_window_hours}h'
                }
            }

        logger.info(
            f"IMEI检查通过: imei={imei}, redemptions={successful_redemptions}/{imei_limit}, window={time_window_hours}h")
        return {'allowed': True, 'reason': 'IMEI restriction check passed', 'risk_level': 'LOW'}

    def _check_ip_throttling(self, ip: str, coupon_id: str, config: Dict) -> Dict[str, Any]:
        """IP地址监控和限流 - 针对当前优惠券的限制"""
        ip_limit = config.get('ip_limit_count', 10)
        time_window_hours = config.get('ip_time_window_hours', 1)

        # 如果限制次数为0或负数，或时间窗口为0，跳过检查
        if ip_limit <= 0 or time_window_hours <= 0:
            return {'allowed': True, 'reason': 'No IP restriction', 'risk_level': 'LOW'}

        # 计算时间窗口
        window_start = datetime.now() - timedelta(hours=time_window_hours)

        # 检查该IP在时间窗口内对当前优惠券的成功兑换次数
        recent_attempts = sum(
            1 for attempt in self.ip_attempts.get(ip, [])
            if attempt.timestamp > window_start and attempt.successful and attempt.coupon_id == coupon_id
        )
      
        if recent_attempts >= ip_limit:
            return {
                'allowed': False,
                'reason': 'ip_limit',
                # 'reason': f'Too many redemptions from this network ({ip_limit} time{"s" if ip_limit > 1 else ""} per {time_window_hours}h). Please try again later.',
                'risk_level': 'HIGH',
                'details': {
                    'ip_attempt_count': recent_attempts,
                    'ip_limit': ip_limit,
                    'time_window_hours': time_window_hours,
                    'message': f'IP limit: {ip_limit} per {time_window_hours}h'
                }
            }

        logger.info(f"IP检查通过: ip={ip}, attempts={recent_attempts}/{ip_limit}, window={time_window_hours}h")
        return {'allowed': True, 'reason': 'IP throttling check passed', 'risk_level': 'LOW'}

    def _check_device_fingerprint(self, user_id: str, user_agent: str, config: Dict) -> Dict[str, Any]:
        """设备指纹识别"""
        if not user_agent:
            return {
                'allowed': False,
                'reason': 'Unable to obtain device fingerprint',
                'risk_level': 'MEDIUM'
            }

        # 生成设备指纹
        fingerprint = self._generate_device_fingerprint(user_agent)

        # 检查是否为可疑设备指纹
        if self._is_suspicious_fingerprint(fingerprint):
            return {
                'allowed': False,
                'reason': 'Suspicious device fingerprint detected',
                'risk_level': 'HIGH',
                'details': {'fingerprint': fingerprint}
            }

        # 检查设备是否在黑名单中
        if fingerprint in self.blacklisted_devices:
            return {
                'allowed': False,
                'reason': 'Device is blacklisted',
                'risk_level': 'HIGH'
            }

        return {'allowed': True, 'reason': 'Device fingerprint check passed', 'risk_level': 'LOW'}

    def _check_geofencing(self, location: str, config: Dict) -> Dict[str, Any]:
        """地理围栏控制"""
        if not config.get('geo_fencing_enabled'):
            return {'allowed': True, 'reason': 'Geofencing not enabled', 'risk_level': 'LOW'}

        if not location:
            return {
                'allowed': False,
                'reason': 'Unable to obtain user location',
                'risk_level': 'MEDIUM'
            }

        allowed_regions = config.get('allowed_regions', '')
        if not allowed_regions:
            return {'allowed': True, 'reason': 'No region restriction', 'risk_level': 'LOW'}

        # 检查用户位置是否在允许的地区内
        allowed_region_list = [r.strip().lower() for r in allowed_regions.split(',')]
        location_lower = location.lower()

        location_allowed = any(
            region in location_lower for region in allowed_region_list
        )

        if not location_allowed:
            return {
                'allowed': False,
                'reason': 'User location not in allowed regions',
                'risk_level': 'HIGH',
                'details': {
                    'user_location': location,
                    'allowed_regions': allowed_region_list
                }
            }

        return {'allowed': True, 'reason': 'Geofencing check passed', 'risk_level': 'LOW'}

    def _analyze_behavior_pattern(self, user_id: str, ip: str, imei: Optional[str], config: Dict) -> Dict[str, Any]:
        """行为模式分析"""
        # 检查同一IP短时间内多用户兑换
        time_window_minutes = config.get('time_window_minutes', 5)
        max_users_per_ip = config.get('max_users_per_ip', 3)

        recent_time = datetime.now() - timedelta(minutes=time_window_minutes)
        recent_attempts = [
            attempt for attempt in self.ip_attempts.get(ip, [])
            if attempt.timestamp > recent_time
        ]

        unique_users = set(attempt.user_id for attempt in recent_attempts)

        if len(unique_users) > max_users_per_ip:
            return {
                'allowed': False,
                'reason': f'Suspicious batch redemption behavior detected',
                'risk_level': 'HIGH',
                'details': {
                    'unique_users_count': len(unique_users),
                    'max_users_per_ip': max_users_per_ip,
                    'time_window_minutes': time_window_minutes
                }
            }

        # 检查用户快速切换设备
        if imei:
            user_devices = set()
            for attempts in self.imei_attempts.values():
                for attempt in attempts:
                    if attempt.user_id == user_id and attempt.timestamp > recent_time:
                        user_devices.add(attempt.imei)

            if len(user_devices) > 2:  # 短时间内使用超过2个设备
                return {
                    'allowed': False,
                    'reason': 'User switching devices too frequently',
                    'risk_level': 'HIGH',
                    'details': {
                        'device_count': len(user_devices),
                        'time_window_minutes': time_window_minutes
                    }
                }

        return {'allowed': True, 'reason': 'Behavior pattern analysis passed', 'risk_level': 'LOW'}

    @staticmethod
    def record_redemption_attempt(user_id: str, coupon_id: str, ip: str,
                                  imei: Optional[str] = None, successful: bool = False):
        """记录兑换尝试"""
        service = RiskManagementService()
        attempt = RedemptionAttempt(user_id, coupon_id, ip, imei, successful)

        # 记录到IP尝试历史
        service.ip_attempts[ip].append(attempt)

        # 记录到IMEI尝试历史
        if imei:
            service.imei_attempts[imei].append(attempt)

        # 清理过期记录
        service._cleanup_expired_attempts()

        logger.info(f"记录兑换尝试: user_id={user_id}, coupon_id={coupon_id}, ip={ip}, successful={successful}")

    @staticmethod
    def add_to_blacklist(blacklist_type: str, value: str, reason: Optional[str] = None,
                         aid: Optional[str] = None,
                         activity_type: Optional[str] = None,
                         activity_id: Optional[str] = None,
                         source_activity_type: Optional[str] = None,
                         source_activity_id: Optional[str] = None,
                         create_by_id: Optional[str] = None,
                         create_by_name: Optional[str] = None) -> bool:
        """
        添加到黑名单（写入数据库）

        Args:
            blacklist_type: 黑名单类型 User/IP Address/Device ID (也支持旧值 user/ip/device/imei)
            value: 黑名单值
            reason: 加入黑名单的原因
            aid: 代理ID（记录哪个代理添加的，用于权限管理）
            activity_type: 生效活动类型（控制黑名单生效范围，为空表示全活动类型）
            activity_id: 生效活动ID（控制黑名单生效范围，为空表示该类型的全活动）
            source_activity_type: 来源活动类型（记录在哪个活动中被加入，仅用于追溯）
            source_activity_id: 来源活动ID（记录具体活动，仅用于追溯）
            create_by_id: 创建人ID
            create_by_name: 创建人姓名

        Returns:
            True: 添加成功, False: 添加失败

        黑名单范围说明（基于 activity_type 和 activity_id）：
            - activity_type=None, activity_id=None → 全局黑名单（所有活动）
            - activity_type=有值, activity_id=None → 类型级黑名单（该类型的所有活动）
            - activity_type=有值, activity_id=有值 → 活动级黑名单（特定活动）

        权限管理说明：
            - aid: 记录哪个代理添加的，该代理可以解除此黑名单

        追溯信息说明：
            - source_activity_type/id: 记录在哪个活动中发现并加入黑名单，用于审计
        """
        try:
            RiskBlacklist = get_blacklist_model()
            if not RiskBlacklist:
                logger.error("黑名单模型不可用，无法添加黑名单")
                return False

            # 添加到数据库（类型规范化在 Model 层处理）
            RiskBlacklist.add_blacklist(
                blacklist_type=blacklist_type,
                value=value,
                reason=reason,
                aid=aid,
                activity_type=activity_type,
                activity_id=activity_id,
                source_activity_type=source_activity_type,
                source_activity_id=source_activity_id,
                create_by_id=create_by_id,
                create_by_name=create_by_name
            )

            # 构建日志消息
            scope = "全局黑名单"
            if activity_type and activity_id:
                scope = f"活动级黑名单({activity_type}:{activity_id})"
            elif activity_type:
                scope = f"类型级黑名单({activity_type})"

            aid_info = f", aid={aid}" if aid else ""
            source_info = f", source={source_activity_type}:{source_activity_id}" if source_activity_id else ""

            logger.info(
                f"已添加到黑名单: type={blacklist_type}, value={value}, scope={scope}{aid_info}{source_info}, reason={reason}")
            return True

        except Exception as e:
            logger.error(f"添加黑名单失败: {str(e)}")
            return False

    def _generate_device_fingerprint(self, user_agent: str) -> str:
        """生成设备指纹"""
        # 使用SHA256生成指纹
        return hashlib.sha256(user_agent.encode()).hexdigest()[:16]

    def _is_suspicious_fingerprint(self, fingerprint: str) -> bool:
        """检查是否为可疑设备指纹"""
        # 已知的机器人、爬虫指纹列表
        known_bot_fingerprints = [
            # 可以添加已知的机器人指纹
        ]
        return fingerprint in known_bot_fingerprints

    def _cleanup_expired_attempts(self):
        """清理过期的尝试记录"""
        cutoff_time = datetime.now() - timedelta(hours=24)

        # 清理IP尝试记录
        for ip in list(self.ip_attempts.keys()):
            self.ip_attempts[ip] = [
                attempt for attempt in self.ip_attempts[ip]
                if attempt.timestamp > cutoff_time
            ]
            if not self.ip_attempts[ip]:
                del self.ip_attempts[ip]

        # 清理IMEI尝试记录
        for imei in list(self.imei_attempts.keys()):
            self.imei_attempts[imei] = [
                attempt for attempt in self.imei_attempts[imei]
                if attempt.timestamp > cutoff_time
            ]
            if not self.imei_attempts[imei]:
                del self.imei_attempts[imei]

    @staticmethod
    def get_risk_statistics() -> Dict[str, Any]:
        """获取风险统计信息"""
        service = RiskManagementService()

        total_attempts = sum(len(attempts) for attempts in service.ip_attempts.values())
        successful_attempts = sum(
            1 for attempts in service.ip_attempts.values()
            for attempt in attempts if attempt.successful
        )

        stats = {
            'monitored_ips_count': len(service.ip_attempts),
            'monitored_imeis_count': len(service.imei_attempts),
            'total_redemption_attempts': total_attempts,
            'successful_attempts': successful_attempts,
            'success_rate': (successful_attempts / total_attempts * 100) if total_attempts > 0 else 0,
            'last_updated': datetime.now().isoformat()
        }

        return stats


class RedemptionAttempt:
    """兑换尝试记录"""

    def __init__(self, user_id: str, coupon_id: str, ip: str,
                 imei: Optional[str] = None, successful: bool = False):
        self.user_id = user_id
        self.coupon_id = coupon_id
        self.ip = ip
        self.imei = imei
        self.timestamp = datetime.now()
        self.successful = successful


# 创建全局实例（单例）
risk_management_service = RiskManagementService()
