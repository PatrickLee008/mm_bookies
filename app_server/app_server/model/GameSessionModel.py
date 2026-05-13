# -*- coding: utf-8 -*-
"""
游戏会话数据模型
对应数据库表: m_app_game_session

用于追踪用户进入和退出AWC游戏时的钱包余额变化

@author: System
@date: 2025-12-01
"""

from app_server import db
from sqlalchemy import Column, String, DECIMAL, DateTime, Integer, Text
from app_server.utils.BaseSaasModel import BaseSaasModel
from datetime import datetime
from decimal import Decimal

from app_server.utils.Kits import Kits


class SessionStatus:
    """会话状态常量"""
    InProgress = "InProgress"  # 进行中
    Completed = "Completed"    # 已完成
    Timeout = "Timeout"        # 超时


class ResultStatus:
    """结果状态常量"""
    Win = "Win"      # 赢
    Loss = "Loss"    # 输
    Draw = "Draw"    # 平局


class GameSession(BaseSaasModel):
    """游戏会话模型"""
    __tablename__ = 'm_app_game_session'

    # 主键
    id = Column(String(64), primary_key=True, comment="会话ID (UUID)")

    # 代理和会员信息
    aid = Column(String(64), comment="代理ID")
    mb_id = Column(String(64), nullable=False, comment="会员ID")
    mb_username = Column(String(64), comment="会员用户名")

    # 游戏信息
    game_code = Column(String(100), comment="游戏代码")
    game_name = Column(String(200), comment="游戏名称")
    platform = Column(String(50), comment="平台/提供商 (如: CRASH88, SEXYBCRT)")
    game_type = Column(String(50), comment="游戏类型 (如: LIVE, SLOT, EGAME)")

    # 进入时信息
    entry_time = Column(DateTime, comment="进入游戏时间")
    entry_main_wallet = Column(DECIMAL(20, 2), default=Decimal('0.00'), comment="进入时主钱包余额")
    entry_promo_wallet = Column(DECIMAL(20, 2), default=Decimal('0.00'), comment="进入时优惠钱包余额")
    entry_total_wallet = Column(DECIMAL(20, 2), default=Decimal('0.00'), comment="进入时总余额")

    # 退出时信息
    exit_time = Column(DateTime, comment="退出游戏时间")
    exit_main_wallet = Column(DECIMAL(20, 2), comment="退出时主钱包余额")
    exit_promo_wallet = Column(DECIMAL(20, 2), comment="退出时优惠钱包余额")
    exit_total_wallet = Column(DECIMAL(20, 2), comment="退出时总余额")

    # 计算结果
    net_main = Column(DECIMAL(20, 2), comment="主钱包净变化 (exit - entry)")
    net_promo = Column(DECIMAL(20, 2), comment="优惠钱包净变化 (exit - entry)")
    net_total = Column(DECIMAL(20, 2), comment="总净变化 (net_main + net_promo)")

    # 会话状态
    session_status = Column(String(20), default=SessionStatus.InProgress, comment="会话状态")
    result_status = Column(String(20), comment="结果状态: Win/Loss/Draw")

    # 标签和元数据
    label = Column(String(50), default='eGame', comment="标签类型")
    session_duration = Column(Integer, comment="会话时长(秒)")
    awc_game_url = Column(Text, comment="AWC游戏URL")
    last_heartbeat_time = Column(DateTime, comment="最后心跳时间")

    def to_dict(self):
        """
        转换为字典

        Returns:
            dict: 会话数据字典
        """
        return {
            'id': self.id,
            'aid': self.aid,
            'mbId': self.mb_id,
            'mbUsername': self.mb_username,
            'gameCode': self.game_code,
            'gameName': self.game_name,
            'platform': self.platform,
            'gameType': self.game_type,
            'entryTime': self.entry_time.isoformat() if self.entry_time else None,
            'entryMainWallet': float(self.entry_main_wallet) if self.entry_main_wallet else 0,
            'entryPromoWallet': float(self.entry_promo_wallet) if self.entry_promo_wallet else 0,
            'entryTotalWallet': float(self.entry_total_wallet) if self.entry_total_wallet else 0,
            'exitTime': self.exit_time.isoformat() if self.exit_time else None,
            'exitMainWallet': float(self.exit_main_wallet) if self.exit_main_wallet else None,
            'exitPromoWallet': float(self.exit_promo_wallet) if self.exit_promo_wallet else None,
            'exitTotalWallet': float(self.exit_total_wallet) if self.exit_total_wallet else None,
            'netMain': float(self.net_main) if self.net_main else None,
            'netPromo': float(self.net_promo) if self.net_promo else None,
            'netTotal': float(self.net_total) if self.net_total else None,
            'sessionStatus': self.session_status,
            'resultStatus': self.result_status,
            'label': self.label,
            'sessionDuration': self.session_duration,
            'lastHeartbeatTime': self.last_heartbeat_time.isoformat() if self.last_heartbeat_time else None,
            'createTime': self.create_time.isoformat() if self.create_time else None,
            'updateTime': self.update_time.isoformat() if self.update_time else None
        }

    def calculate_results(self, exit_main_wallet, exit_promo_wallet):
        """
        计算会话结果

        Args:
            exit_main_wallet: 退出时主钱包余额
            exit_promo_wallet: 退出时优惠钱包余额
        """
        self.exit_main_wallet = Decimal(str(exit_main_wallet))
        self.exit_promo_wallet = Decimal(str(exit_promo_wallet))
        self.exit_total_wallet = self.exit_main_wallet + self.exit_promo_wallet

        # 计算净变化
        self.net_main = self.exit_main_wallet - self.entry_main_wallet
        self.net_promo = self.exit_promo_wallet - self.entry_promo_wallet
        self.net_total = self.net_main + self.net_promo

        # 计算会话时长
        if self.entry_time and self.exit_time:
            duration = (self.exit_time - self.entry_time).total_seconds()
            self.session_duration = int(duration)

        # 判断结果状态
        if self.net_total > 0:
            self.result_status = ResultStatus.Win
        elif self.net_total < 0:
            self.result_status = ResultStatus.Loss
        else:
            self.result_status = ResultStatus.Draw

    @staticmethod
    def create_session(mb_id, mb_username, game_code, game_name, platform, game_type,
                      main_wallet, promo_wallet, game_url=None, aid=None):
        """
        创建新的游戏会话

        Args:
            mb_id: 会员ID
            mb_username: 会员用户名
            game_code: 游戏代码
            game_name: 游戏名称
            platform: 平台名称
            game_type: 游戏类型
            main_wallet: 主钱包余额
            promo_wallet: 优惠钱包余额
            game_url: 游戏URL
            aid: 代理ID

        Returns:
            GameSession: 新创建的会话对象
        """
        import uuid

        session = GameSession()
        session.id = Kits.generate_uuid()
        session.aid = aid
        session.mb_id = mb_id
        session.mb_username = mb_username
        session.game_code = game_code
        session.game_name = game_name
        session.platform = platform
        session.game_type = game_type
        session.entry_time = datetime.now()
        session.entry_main_wallet = Decimal(str(main_wallet))
        session.entry_promo_wallet = Decimal(str(promo_wallet))
        session.entry_total_wallet = session.entry_main_wallet + session.entry_promo_wallet
        session.session_status = SessionStatus.InProgress
        session.awc_game_url = game_url
        session.last_heartbeat_time = datetime.now()

        return session

    @staticmethod
    def get_active_session(mb_id):
        """
        获取用户的活跃会话

        Args:
            mb_id: 会员ID

        Returns:
            GameSession: 活跃的会话对象或None
        """
        return GameSession.query.filter_by(
            mb_id=mb_id,
            session_status=SessionStatus.InProgress,
            del_flag=0
        ).order_by(GameSession.entry_time.desc()).first()

    @staticmethod
    def get_user_sessions(mb_id, page=1, page_size=20):
        """
        获取用户的会话历史（分页）

        Args:
            mb_id: 会员ID
            page: 页码
            page_size: 每页数量

        Returns:
            tuple: (会话列表, 总数)
        """
        query = GameSession.query.filter_by(
            mb_id=mb_id,
            del_flag=0
        ).order_by(GameSession.entry_time.desc())

        total = query.count()
        sessions = query.paginate(
            page=page,
            per_page=page_size,
            error_out=False
        )

        return sessions.items, total

    def __repr__(self):
        return f'<GameSession {self.id} - {self.mb_username} - {self.game_name} - {self.session_status}>'
