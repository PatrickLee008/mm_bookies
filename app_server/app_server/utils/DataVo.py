# 使用基础VO
from decimal import Decimal


class BaseVO:
    @classmethod
    def from_dict(cls, data: dict):
        """通过字典创建VO对象"""
        vo = cls()
        for key, value in data.items():
            if hasattr(vo, key):
                setattr(vo, key, value)
        return vo

    def to_dict(self) -> dict:
        """将VO对象转为字典"""
        return {k: v for k, v in self.__dict__.items() if not k.startswith('_')}

    def map_from(self, source, field_mapping: dict = None):
        """
        从源对象映射字段
        :param source: 源对象或字典
        :param field_mapping: 字段映射字典 {源字段: 目标字段}
        """
        if isinstance(source, dict):
            source_dict = source
        else:
            source_dict = source.__dict__

        if field_mapping:
            for src_key, dest_key in field_mapping.items():
                if src_key in source_dict and hasattr(self, dest_key):
                    converted_value = self._convert_type(dest_key, source_dict[src_key])
                    setattr(self, dest_key, converted_value)
        else:
            for key, value in source_dict.items():
                if hasattr(self, key):
                    converted_value = self._convert_type(key, value)
                    setattr(self, key, converted_value)
        return self

    def _convert_type(self, field_name: str, value):
        """
        根据字段的默认类型转换值
        :param field_name: 字段名
        :param value: 源值
        :return: 转换后的值
        """
        if not hasattr(self, field_name):
            return value

        # 获取字段当前的默认值，以确定目标类型
        default_value = getattr(self, field_name)

        # 如果值为空或None，返回默认值
        if value is None or value == '':
            return default_value

        # 根据默认值的类型进行转换
        if isinstance(default_value, bool):
            # 布尔类型转换
            if isinstance(value, bool):
                return value
            if isinstance(value, str):
                return value.lower() in ('true', '1', 'yes', 'on')
            return bool(value)

        elif isinstance(default_value, float):
            # 浮点类型转换
            try:
                return float(value)
            except (ValueError, TypeError):
                return default_value

        elif isinstance(default_value, int):
            # 整数类型转换
            try:
                return int(value)
            except (ValueError, TypeError):
                return default_value
        elif isinstance(default_value, Decimal):
            # Decimal类型转换为浮点
            try:
                return float(value)
            except (ValueError, TypeError):
                return default_value
        # 其他类型保持原样
        return value


# 租户配置
class SysConfigVO(BaseVO):
    def __init__(self):
        self.member_default_agent_id = None # 会员注册默认代理ID


# Scraper配置
class ScraperCfgVo(BaseVO):
    def __init__(self):
        self.LeagueFilter = None  # League Filter List
        self.scraperApiUrl = None  # Scraper API Address
        self.scraperTimeout = None  # API Timeout Period
        self.scraperRetryCount = None  # Retry Count
        self.scraperAppId = None  # Application ID
        self.scraperAesKey = None  # AES Key
        self.scraperRateLimit = None  # Request Rate Limit
        self.scraperEnabled = False  # Enable Scraper
        self.scraperDebugMode = False  # Debug Mode
        self.scraperCacheTime = None  # Data Cache Time
        self.scraperDataSource = None  # Scraper Data Source
        self.pickAccount = None  # Pick Account
        self.pickPassword = None  # Pick Password
        self.minOddWinLose = 0.0  # HDP Spider Min Odd
        self.minOddBallNum = 0.0  # O/U Spider Min Odd
        self.minOddCond4 = 0.0  # Mix(HDP) Spider Min Odd
        self.minOddCond5 = 0.0  # Mix(O/U) Spider Min Odd
        self.singleSpiderEnabled = False  # Single Spider Enabled
        self.mixParlaySpiderEnabled = False  # Mix Parlay Spider Enabled
        self.minOdd1x2 = 0.0  # 1x2 Spider Min Odd
        self.minOddCorrectScore = 0.0  # Correct Score Spider Min Odd
        self.minOddOddEven = 0.0  # Odd/Even Spider Min Odd


# 平台订单配置
class PlatformOrderCfgVo(BaseVO):
    def __init__(self):
        self.settleOn = False  # Settlement Switch
        self.singleRatio = 0.0  # Single Match Commission Rate
        self.singleDoubleRatio = 0.0  # Odd/Even Commission Rate
        self.singleDodanRatio = 0.0  # Correct Score Commission Rate
        self.blendRatio = 0.0  # Mixed Commission Rate
        self.orderExpireMinutes = 5  # 充值订单过期时间（分钟）


# App前端配置
class AppFrontSettingVo(BaseVO):
    def __init__(self):
        self.helpContent = None  # Help Content
        self.contactContent = None  # Contact Content
        self.telegramUrl = None  # App telegramUrl
        self.viberUrl = None  # App viberUrl
        self.phone = None  # App phone
        self.appVersion = None  # App Version
        self.appApkUrl = None  # App APK URL
        self.appWgtUrl = None  # App WGT URL
        self.appIosUrl = None  # App iOS URL
        self.transferVideoLink = None  # Transfer Video Link
        self.nfmVideoLink = None  # NFM Video Link
        self.aiHelperHost = None  # AI Helper Host
        self.aiHelperToken = None  # AI Helper Token
        self.updateState = 0 # Update State


