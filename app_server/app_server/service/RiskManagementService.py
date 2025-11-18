from datetime import datetime, timedelta
from decimal import Decimal
from collections import defaultdict
from typing import Dict, List, Set, Optional, Tuple, Any
import hashlib
import logging
from threading import Lock

logger = logging.getLogger(__name__)


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
        self.blacklisted_users: Set[str] = set()
        self.blacklisted_ips: Set[str] = set()
        self.blacklisted_imeis: Set[str] = set()
        self.blacklisted_devices: Set[str] = set()
        
        # 配置默认值
        self.default_config = {
            'ip_limit_count': 10,  # IP限制次数
            'ip_time_window_hours': 1,  # IP时间窗口（小时）
            'imei_limit_count': 5,  # IMEI限制次数
            'device_limit_count': 5,  # 设备限制次数
            'geo_fencing_enabled': False,  # 地理围栏
            'allowed_regions': '',  # 允许的地区
            'suspicious_threshold': 3,  # 可疑行为阈值
            'max_users_per_ip': 3,  # 每个IP最多用户数
            'time_window_minutes': 5  # 行为分析时间窗口
        }
    
    @staticmethod
    def assess_redemption_risk(user_id: str, coupon_id: str, ip: str, 
                               imei: Optional[str] = None, user_agent: Optional[str] = None,
                               location: Optional[str] = None, 
                               coupon_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        综合风险评估
        
        Args:
            user_id: 用户ID
            coupon_id: 优惠券ID
            ip: 用户IP地址
            imei: 设备IMEI
            user_agent: 浏览器用户代理
            location: 用户位置信息
            coupon_config: 优惠券风险配置
            
        Returns:
            风险评估结果字典
        """
        service = RiskManagementService()
        config = {**service.default_config, **(coupon_config or {})}
        
        try:
            logger.info(f"开始风险评估: user_id={user_id}, coupon_id={coupon_id}, ip={ip}")
            
            # 1. 黑名单检查
            blacklist_result = service._check_blacklist(user_id, ip, imei)
            if not blacklist_result['allowed']:
                return blacklist_result
            
            # 2. IMEI限制检查
            if imei:
                imei_result = service._check_imei_restrictions(imei, coupon_id, config)
                if not imei_result['allowed']:
                    return imei_result
            
            # 3. IP地址监控和限流
            ip_result = service._check_ip_throttling(ip, coupon_id, config)
            if not ip_result['allowed']:
                return ip_result
            
            # 4. 设备指纹识别
            if user_agent:
                fingerprint_result = service._check_device_fingerprint(user_id, user_agent, config)
                if not fingerprint_result['allowed']:
                    return fingerprint_result
            
            # 5. 地理围栏控制
            if location and config.get('geo_fencing_enabled'):
                geo_result = service._check_geofencing(location, config)
                if not geo_result['allowed']:
                    return geo_result
            
            # 6. 行为模式分析
            behavior_result = service._analyze_behavior_pattern(user_id, ip, imei, config)
            if not behavior_result['allowed']:
                return behavior_result
            
            # 所有检查通过
            logger.info(f"风险评估通过: user_id={user_id}, coupon_id={coupon_id}")
            return {
                'allowed': True,
                'reason': 'Risk assessment passed',
                'risk_level': 'LOW',
                'details': {
                    'checks_passed': ['blacklist', 'imei', 'ip_throttling', 'device_fingerprint', 'geofencing', 'behavior'],
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
    
    def _check_blacklist(self, user_id: str, ip: str, imei: Optional[str]) -> Dict[str, Any]:
        """黑名单检查"""
        if user_id in self.blacklisted_users:
            return {
                'allowed': False,
                'reason': 'User is blacklisted',
                'risk_level': 'HIGH'
            }
        
        if ip in self.blacklisted_ips:
            return {
                'allowed': False,
                'reason': 'IP address is blacklisted',
                'risk_level': 'HIGH'
            }
        
        if imei and imei in self.blacklisted_imeis:
            return {
                'allowed': False,
                'reason': 'Device IMEI is blacklisted',
                'risk_level': 'HIGH'
            }
        
        return {'allowed': True, 'reason': 'Blacklist check passed', 'risk_level': 'LOW'}
    
    def _check_imei_restrictions(self, imei: str, coupon_id: str, config: Dict) -> Dict[str, Any]:
        """IMEI限制检查"""
        imei_limit = config.get('imei_limit_count', 5)
        if imei_limit <= 0:
            return {'allowed': True, 'reason': 'No IMEI restriction', 'risk_level': 'LOW'}
        
        # 检查该IMEI的兑换次数
        successful_redemptions = sum(
            1 for attempt in self.imei_attempts.get(imei, [])
            if attempt.coupon_id == coupon_id and attempt.successful
        )
        
        if successful_redemptions >= imei_limit:
            return {
                'allowed': False,
                'reason': f'IMEI redemption limit exceeded ({successful_redemptions}/{imei_limit})',
                'risk_level': 'HIGH',
                'details': {
                    'imei_redemption_count': successful_redemptions,
                    'imei_limit': imei_limit
                }
            }
        
        return {'allowed': True, 'reason': 'IMEI restriction check passed', 'risk_level': 'LOW'}
    
    def _check_ip_throttling(self, ip: str, coupon_id: str, config: Dict) -> Dict[str, Any]:
        """IP地址监控和限流"""
        ip_limit = config.get('ip_limit_count', 10)
        time_window_hours = config.get('ip_time_window_hours', 1)
        
        if ip_limit <= 0 or time_window_hours <= 0:
            return {'allowed': True, 'reason': 'No IP restriction', 'risk_level': 'LOW'}
        
        # 计算时间窗口
        window_start = datetime.now() - timedelta(hours=time_window_hours)
        
        # 检查该IP在时间窗口内的兑换次数
        recent_attempts = sum(
            1 for attempt in self.ip_attempts.get(ip, [])
            if attempt.coupon_id == coupon_id and 
               attempt.timestamp > window_start and 
               attempt.successful
        )
        
        if recent_attempts >= ip_limit:
            return {
                'allowed': False,
                'reason': f'IP rate limit exceeded ({recent_attempts}/{ip_limit} in {time_window_hours}h)',
                'risk_level': 'HIGH',
                'details': {
                    'ip_attempt_count': recent_attempts,
                    'ip_limit': ip_limit,
                    'time_window_hours': time_window_hours
                }
            }
        
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
    def add_to_blacklist(blacklist_type: str, value: str):
        """添加到黑名单"""
        service = RiskManagementService()
        
        if blacklist_type.lower() == 'user':
            service.blacklisted_users.add(value)
        elif blacklist_type.lower() == 'ip':
            service.blacklisted_ips.add(value)
        elif blacklist_type.lower() == 'imei':
            service.blacklisted_imeis.add(value)
        elif blacklist_type.lower() == 'device':
            service.blacklisted_devices.add(value)
        
        logger.info(f"添加到黑名单: type={blacklist_type}, value={value}")
    
    @staticmethod
    def remove_from_blacklist(blacklist_type: str, value: str):
        """从黑名单移除"""
        service = RiskManagementService()
        
        if blacklist_type.lower() == 'user':
            service.blacklisted_users.discard(value)
        elif blacklist_type.lower() == 'ip':
            service.blacklisted_ips.discard(value)
        elif blacklist_type.lower() == 'imei':
            service.blacklisted_imeis.discard(value)
        elif blacklist_type.lower() == 'device':
            service.blacklisted_devices.discard(value)
        
        logger.info(f"从黑名单移除: type={blacklist_type}, value={value}")
    
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
            'blacklisted_users_count': len(service.blacklisted_users),
            'blacklisted_ips_count': len(service.blacklisted_ips),
            'blacklisted_imeis_count': len(service.blacklisted_imeis),
            'blacklisted_devices_count': len(service.blacklisted_devices),
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