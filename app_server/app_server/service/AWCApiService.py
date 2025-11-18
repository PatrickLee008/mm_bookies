# -*- coding: utf-8 -*-
"""
AWC游戏平台API服务类
实现AWC Common API Functions的调用

@author: Arthur
@date: 2025-10-17
"""

import requests
import json
import logging
from typing import Dict, Any, Optional, List
from flask import current_app

logger = logging.getLogger(__name__)


class AWCApiService:
    """AWC API服务类"""

    def __init__(self):
        """初始化AWC API服务"""
        self.base_url = current_app.config.get('AWC_API_BASE_URL', '')
        self.cert = current_app.config.get('AWC_API_CERT', '')
        self.agent_id = current_app.config.get('AWC_API_AGENT_ID', '')
        self.timeout = current_app.config.get('AWC_API_TIMEOUT', 30)
        self.enabled = current_app.config.get('AWC_API_ENABLED', False)
        self.default_currency = current_app.config.get('AWC_API_DEFAULT_CURRENCY', 'CNY')
        self.default_language = current_app.config.get('AWC_API_DEFAULT_LANGUAGE', 'zh-cn')
        self.default_bet_limit = current_app.config.get('AWC_API_DEFAULT_BET_LIMIT', '')

    def _check_enabled(self):
        """检查AWC API是否启用"""
        if not self.enabled:
            raise Exception("AWC API is not enabled")
        if not self.base_url or not self.cert or not self.agent_id:
            raise Exception("AWC API configuration is incomplete")

    def _make_request(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        发送API请求到AWC平台

        Args:
            endpoint: API端点路径
            data: 请求数据

        Returns:
            响应数据字典
        """
        self._check_enabled()

        url = self.base_url + endpoint

        # 添加认证信息
        request_data = {
            'cert': self.cert,
            'agentId': self.agent_id,
            **data
        }

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        try:
            logger.info(f"AWC API Request: {endpoint}, data: {json.dumps(request_data, ensure_ascii=False)}")

            response = requests.post(
                url,
                data=request_data,
                headers=headers,
                timeout=self.timeout
            )

            response.raise_for_status()
            result = response.json()

            logger.info(f"AWC API Response: {endpoint}, result: {json.dumps(result, ensure_ascii=False)}")

            return result

        except requests.exceptions.RequestException as e:
            logger.error(f"AWC API Request failed: {endpoint}, error: {str(e)}")
            raise Exception(f"AWC API request failed: {str(e)}")
        except json.JSONDecodeError as e:
            logger.error(f"AWC API Response parse error: {endpoint}, error: {str(e)}")
            raise Exception(f"AWC API response parse error: {str(e)}")

    # ========== 6.1. createMember 创建玩家 ==========
    def create_member(self, user_id: str, currency: str, bet_limit: str,
                     language: Optional[str] = None, user_name: Optional[str] = None) -> Dict[str, Any]:
        """
        创建AWC玩家账户

        Args:
            user_id: 独一使用者ID (仅许可 0-9 a-z)
            currency: 货币类型
            bet_limit: 下注限红配置 (JSON格式)
            language: 语言设置
            user_name: 显示名称

        Returns:
            {"status": "0000", "desc": "Success"}
        """
        data = {
            'userId': user_id,
            'currency': currency,
            'language': language or self.default_language
        }

        # betLimit is required for AWC API
        # Use provided betLimit or default from config
        if bet_limit is not None and bet_limit != '':
            data['betLimit'] = bet_limit
        elif self.default_bet_limit:
            data['betLimit'] = self.default_bet_limit

        if user_name:
            data['userName'] = user_name

        return self._make_request('/wallet/createMember', data)

    # ========== 6.2. login 进入游戏 ==========
    def login(self, user_id: str, is_mobile_login: Optional[bool] = None,
             external_url: Optional[str] = None, platform: Optional[str] = None,
             game_type: Optional[str] = None, game_forbidden: Optional[str] = None,
             language: Optional[str] = None, bet_limit: Optional[str] = None,
             **kwargs) -> Dict[str, Any]:
        """
        玩家登入AWC游戏大厅

        Args:
            user_id: 玩家ID
            is_mobile_login: 是否移动端登录
            external_url: 返回URL
            platform: 平台名称
            game_type: 游戏类型
            game_forbidden: 禁止游戏配置 (JSON格式)
            language: 语言
            bet_limit: 下注限红
            **kwargs: 其他参数 (autoBetMode, oddsMode, isEnableJackpot, landingSportId)

        Returns:
            {"status": "0000", "url": "游戏登录URL", "extension": [...]}
        """
        data = {
            'userId': user_id,
            'language': language or self.default_language
        }

        if is_mobile_login is not None:
            data['isMobileLogin'] = is_mobile_login
        if external_url:
            data['externalURL'] = external_url
        if platform:
            data['platform'] = platform
        if game_type:
            data['gameType'] = game_type
        if game_forbidden:
            data['gameForbidden'] = game_forbidden
        if bet_limit:
            data['betLimit'] = bet_limit

        # 添加其他可选参数
        for key in ['autoBetMode', 'oddsMode', 'isEnableJackpot', 'landingSportId']:
            if key in kwargs:
                data[key] = kwargs[key]

        return self._make_request('/wallet/login', data)

    # ========== 6.3. doLoginAndLaunchGame 登入并进入游戏 ==========
    def do_login_and_launch_game(self, user_id: str, platform: str, game_type: str,
                                 game_code: str, is_mobile_login: Optional[bool] = None,
                                 external_url: Optional[str] = None, hall: Optional[str] = None,
                                 language: Optional[str] = None, bet_limit: Optional[str] = None,
                                 **kwargs) -> Dict[str, Any]:
        """
        玩家登入并开启指定游戏

        Args:
            user_id: 玩家ID
            platform: 平台名称 (必填)
            game_type: 游戏类型 (必填)
            game_code: 游戏代码 (必填)
            is_mobile_login: 是否移动端登录
            external_url: 返回URL
            hall: 大厅类型 (仅SEXYBCRT)
            language: 语言
            bet_limit: 下注限红
            **kwargs: 其他参数 (autoBetMode, isLaunchGameTable, gameTableId, oddsMode, isEnableJackpot, landingSportId)

        Returns:
            {"status": "0000", "url": "游戏URL", "extension": [...]}
        """
        data = {
            'userId': user_id,
            'platform': platform,
            'gameType': game_type,
            'gameCode': game_code,
            'language': language or self.default_language
        }

        if is_mobile_login is not None:
            data['isMobileLogin'] = is_mobile_login
        if external_url:
            data['externalURL'] = external_url
        if hall:
            data['hall'] = hall
        if bet_limit:
            data['betLimit'] = bet_limit

        # 添加其他可选参数
        for key in ['autoBetMode', 'isLaunchGameTable', 'gameTableId', 'oddsMode', 'isEnableJackpot', 'landingSportId']:
            if key in kwargs:
                data[key] = kwargs[key]

        return self._make_request('/wallet/doLoginAndLaunchGame', data)

    # ========== 6.4. updateBetLimit 更新限红 ==========
    def update_bet_limit(self, user_id: str, bet_limit: str) -> Dict[str, Any]:
        """
        更新玩家投注限红

        Args:
            user_id: 玩家ID
            bet_limit: 下注限红配置 (JSON格式)

        Returns:
            {"status": "0000", "desc": "Success"}
        """
        data = {
            'userId': user_id,
            'betLimit': bet_limit
        }
        return self._make_request('/wallet/updateBetLimit', data)

    # ========== 6.5. logout 强迫登出玩家 ==========
    def logout(self, user_ids: str) -> Dict[str, Any]:
        """
        强制玩家登出系统

        Args:
            user_ids: 玩家ID列表，用逗号分隔

        Returns:
            {"status": "0000", "logoutUsers": [...], "count": 2}
        """
        data = {
            'userIds': user_ids
        }
        return self._make_request('/wallet/logout', data)

    # ========== 6.6. getTransactionHistoryResult 取得交易历史纪录 ==========
    def get_transaction_history_result(self, user_id: str, platform_tx_id: str,
                                       platform: str, round_id: Optional[str] = None) -> Dict[str, Any]:
        """
        获取玩家交易历史记录链接

        Args:
            user_id: 玩家ID
            platform_tx_id: 平台交易单号
            platform: 平台名称
            round_id: 回合识别码 (SEXYBCRT需要)

        Returns:
            {"status": "0000", "url": "回放URL", "txnUrl": "", "roundUrl": ""}
        """
        data = {
            'userId': user_id,
            'platformTxId': platform_tx_id,
            'platform': platform
        }

        if round_id:
            data['roundId'] = round_id

        return self._make_request('/wallet/getTransactionHistoryResult', data)

    # ========== 6.7. getSummaryByBetTimeHour 取得交易摘要 ==========
    def get_summary_by_bet_time_hour(self, start_time: str, end_time: str, platform: str,
                                    game_type: Optional[str] = None, game_code: Optional[str] = None) -> Dict[str, Any]:
        """
        获取代理商交易摘要 (按小时查询)

        Args:
            start_time: 开始时间 (ISO 8601格式: 2018-09-26T12+08:00)
            end_time: 结束时间 (ISO 8601格式: 2018-09-26T12+08:00)
            platform: 平台名称
            game_type: 游戏类型 (可选)
            game_code: 游戏代码 (可选)

        Returns:
            {"status": "0000", "transactions": [{...}]}
        """
        data = {
            'startTime': start_time,
            'endTime': end_time,
            'platform': platform
        }

        if game_type:
            data['gameType'] = game_type
        if game_code:
            data['gameCode'] = game_code

        return self._make_request('/fetch/getSummaryByBetTimeHour', data)

    # ========== 6.8. resubmitCancelbetNotification 重新要求发送 CancelBet ==========
    def resubmit_cancelbet_notification(self, platform: str, platform_tx_ids: str) -> Dict[str, Any]:
        """
        重新发送CancelBet通知 (仅限2天内)

        Args:
            platform: 平台名称
            platform_tx_ids: 平台交易单号列表，用逗号分隔 (最多10个)

        Returns:
            {"status": "0000", "result": [...]}
        """
        data = {
            'platform': platform,
            'platformTxIds': platform_tx_ids
        }
        return self._make_request('/wallet/resubmitCancelbetNotification', data)

    # ========== 6.9. getTransactionHistoryResultAll 获取赛马赛果 ==========
    def get_transaction_history_result_all(self, platform: str, game_type: str) -> Dict[str, Any]:
        """
        获取赛马当日所有赛果资讯网址 (仅HORSEBOOK)

        Args:
            platform: 平台名称 (HORSEBOOK)
            game_type: 游戏类型

        Returns:
            {"status": "0000", "url": "赛果URL"}
        """
        data = {
            'platform': platform,
            'gameType': game_type
        }
        return self._make_request('/wallet/getTransactionHistoryResultAll', data)

    # ========== 6.10. checkStatus 检查系统状况 ==========
    def check_status(self, platform: Optional[str] = None, game_type: Optional[str] = None,
                    game_code: Optional[str] = None) -> Dict[str, Any]:
        """
        检查系统状态

        Args:
            platform: 平台名称 (可选)
            game_type: 游戏类型 (可选，需要platform)
            game_code: 游戏代码 (可选，需要platform和gameType)

        Returns:
            {"status": "0000"} 或其他状态码
        """
        data = {}

        if platform:
            data['platform'] = platform
        if game_type:
            data['gameType'] = game_type
        if game_code:
            data['gameCode'] = game_code

        return self._make_request('/wallet/checkStatus', data)

    # ========== 6.11. getPromotionSummary 取得活动交易摘要 ==========
    def get_promotion_summary(self, start_time_hr: str, end_time_hr: str,
                             currency: str, platform: str) -> Dict[str, Any]:
        """
        获取活动交易摘要

        Args:
            start_time_hr: 开始时间 (ISO 8601格式)
            end_time_hr: 结束时间 (ISO 8601格式)
            currency: 货币类型
            platform: 平台名称

        Returns:
            {"status": "0000", "transactions": [{...}]}
        """
        data = {
            'startTimeHr': start_time_hr,
            'endTimeHr': end_time_hr,
            'currency': currency,
            'platform': platform
        }
        return self._make_request('/fetch/getPromotionSummary', data)

    # ========== 6.12. updatePlayerStatus 更新玩家状态 ==========
    def update_player_status(self, user_id: str, status: str) -> Dict[str, Any]:
        """
        更新玩家状态

        Args:
            user_id: 玩家ID
            status: 状态 (active: 正常, suspend: 锁定下注, lock: 封锁玩家)

        Returns:
            {"status": "0000", "desc": "Success"}
        """
        data = {
            'userId': user_id,
            'status': status
        }
        return self._make_request('/wallet/updatePlayerStatus', data)

    # ========== 6.13. queryBetLimit 查询玩家下注限红 ==========
    def query_bet_limit(self, user_id: str, platform: str, game_type: str) -> Dict[str, Any]:
        """
        查询玩家下注限额

        Args:
            user_id: 玩家ID
            platform: 平台名称
            game_type: 游戏类型

        Returns:
            {"status": "0000", "betLimit": "{...}"}
        """
        data = {
            'userId': user_id,
            'platform': platform,
            'gameType': game_type
        }
        return self._make_request('/wallet/queryBetLimit', data)

    # ========== 6.14. getSchedule 获取赛事时间 ==========
    def get_schedule(self, start_time: str, end_time: str, platform: str) -> Dict[str, Any]:
        """
        获取赛事时间 (仅SV388)

        Args:
            start_time: 起始月份 (格式: MM/yyyy)
            end_time: 结束月份 (格式: MM/yyyy)
            platform: 平台名称 (SV388)

        Returns:
            {"status": "0000", "data": [{...}]}
        """
        data = {
            'startTime': start_time,
            'endTime': end_time,
            'platform': platform
        }
        return self._make_request('/wallet/getSchedule', data)

    # ========== 6.15. getTransactionStatus 查询交易单状态 ==========
    def get_transaction_status(self, platform: str, platform_tx_id: str) -> Dict[str, Any]:
        """
        查询交易单状态

        Args:
            platform: 平台名称
            platform_tx_id: 平台交易单号

        Returns:
            {"status": "0000", "transactions": [{...}]}
            txStatus: -1(已取消) 0(已投注) 1(已结账) 2(无效) 3(SCRATCH)
        """
        data = {
            'platform': platform,
            'platformTxId': platform_tx_id
        }
        return self._make_request('/wallet/getTransactionStatus', data)

    # ========== 6.16. getPlatformListByAgent 按代理商ID获取平台列表 ==========
    def get_platform_list_by_agent(self) -> Dict[str, Any]:
        """
        查询该代理拥有的游戏商列表

        Returns:
            {"status": "0000", "agentId": "...", "platform": "SPADE,PP,..."}
        """
        data = {}
        return self._make_request('/fetch/getPlatformListByAgent', data)

    # ========== 6.17. getJackpotPool 查询 Jackpot 彩池累计金额 ==========
    def get_jackpot_pool(self, platform: str, game_type: str, currency: str) -> Dict[str, Any]:
        """
        查询Jackpot彩池累计金额 (仅JILI和FC)

        Args:
            platform: 平台名称 (JILI或FC)
            game_type: 游戏类型
            currency: 货币类型

        Returns:
            {"status": "0000", "results": {...}}
        """
        data = {
            'platform': platform,
            'gameType': game_type,
            'currency': currency
        }
        return self._make_request('/wallet/getJackpotPool', data)

    # ========== 6.18. getLobbyState 获取桌子维护状态 ==========
    def get_lobby_state(self, platform: str) -> Dict[str, Any]:
        """
        获取桌子维护状态 (仅SEXYBCRT和EVOLUTION)

        Args:
            platform: 平台名称 (SEXYBCRT或EVOLUTION)

        Returns:
            {"status": "0000", "results": [{...}]}
        """
        data = {
            'platform': platform
        }
        return self._make_request('/wallet/getLobbyState', data)


# 创建全局实例
awc_api_service = None


def get_awc_api_service():
    """获取AWC API服务实例"""
    global awc_api_service
    if awc_api_service is None:
        awc_api_service = AWCApiService()
    return awc_api_service
