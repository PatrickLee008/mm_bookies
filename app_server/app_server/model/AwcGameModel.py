# -*- coding: utf-8 -*-
"""
AWC游戏数据模型
对应数据库表: m_awc_game

@author: Arthur
@date: 2025-11-05
"""

from app_server import db
from sqlalchemy import Column, String, DECIMAL, DateTime, Integer, Text
from app_server.utils.BaseSaasModel import BaseSaasModel


class AwcGame(BaseSaasModel):
    """AWC游戏列表模型"""
    __tablename__ = 'm_awc_game'

    # 主键
    id = Column(String(64), primary_key=True, comment="主键ID")

    # 游戏基本信息
    platform = Column(String(50), nullable=False, comment="游戏平台/游戏商 (如: PP, SEXYBCRT, CRASH88等)")
    game_type = Column(String(50), nullable=False, comment="游戏类型 (如: LIVE, SLOT, EGAME, FISH等)")
    game_code = Column(String(100), nullable=False, unique=True, comment="AWC游戏代码 (唯一标识)")

    # 多语言名称
    name_en = Column(String(200), comment="英文名称")
    name_zh = Column(String(200), comment="中文名称")
    name_th = Column(String(200), comment="泰语名称")
    name_vi = Column(String(200), comment="越南语名称")
    name_id = Column(String(200), comment="印尼文名称")
    name_ms = Column(String(200), comment="马来文名称")

    # 游戏属性
    rtp = Column(DECIMAL(5, 2), comment="返奖率 (Return To Player) 范围0-100")
    volatility = Column(String(20), comment="波动率 (如: Low, Medium, High, Very High)")
    reels = Column(Integer, comment="转轴数量 (老虎机游戏)")
    pay_lines = Column(Integer, comment="赔付线数量 (老虎机游戏)")
    max_multiplier_win = Column(DECIMAL(10, 2), comment="最大赢取倍数")

    # 游戏功能特性
    has_free_spin = Column(Integer, default=0, comment="游戏中是否有免费旋转功能 (0-否, 1-是)")
    can_buy_freespin = Column(Integer, default=0, comment="是否能购买免费旋转 (0-否, 1-是)")
    has_jackpot = Column(Integer, default=0, comment="是否支持游戏内Jackpot功能 (0-否, 1-是)")

    # 环境支持与上线信息
    stg_support = Column(Integer, default=0, comment="测试环境支持度 (0-不支持, 1-支持)")
    stg_release_date = Column(DateTime, comment="测试环境上线时间")
    prd_release_date = Column(DateTime, comment="正式环境上线时间")

    # 状态与排序
    status = Column(Integer, default=1, comment="游戏状态 (0-禁用, 1-启用)")
    is_hot = Column(Integer, default=0, comment="是否热门游戏 (0-否, 1-是)")
    is_new = Column(Integer, default=0, comment="是否新游戏 (0-否, 1-是)")
    sort_order = Column(Integer, default=0, comment="排序权重 (数字越大越靠前)")

    # 图片资源
    icon_url = Column(String(500), comment="游戏图标URL")
    banner_url = Column(String(500), comment="游戏横幅URL")
    thumbnail_url = Column(String(500), comment="游戏缩略图URL")

    # 扩展配置（remarks字段由BaseSaasModel基类提供）
    extra_config = Column(Text, comment="扩展配置 (JSON格式)")

    def to_dict(self, include_fields=None):
        """
        转换为字典

        Args:
            include_fields: 需要包含的字段列表，None表示包含所有字段

        Returns:
            dict: 游戏数据字典
        """
        data = {
            'id': self.id,
            'platform': self.platform,
            'gameType': self.game_type,
            'gameCode': self.game_code,
            'nameEn': self.name_en,
            'nameZh': self.name_zh,
            'nameTh': self.name_th,
            'nameVi': self.name_vi,
            'nameId': self.name_id,
            'nameMs': self.name_ms,
            'rtp': float(self.rtp) if self.rtp else None,
            'volatility': self.volatility,
            'reels': self.reels,
            'payLines': self.pay_lines,
            'maxMultiplierWin': float(self.max_multiplier_win) if self.max_multiplier_win else None,
            'hasFreeSpin': self.has_free_spin,
            'canBuyFreespin': self.can_buy_freespin,
            'hasJackpot': self.has_jackpot,
            'stgSupport': self.stg_support,
            'stgReleaseDate': self.stg_release_date.isoformat() if self.stg_release_date else None,
            'prdReleaseDate': self.prd_release_date.isoformat() if self.prd_release_date else None,
            'status': self.status,
            'isHot': self.is_hot,
            'isNew': self.is_new,
            'sortOrder': self.sort_order,
            'iconUrl': self.icon_url,
            'bannerUrl': self.banner_url,
            'thumbnailUrl': self.thumbnail_url,
            'remarks': self.remarks,
            'extraConfig': self.extra_config,
            'createTime': self.create_time.isoformat() if self.create_time else None,
            'updateTime': self.update_time.isoformat() if self.update_time else None
        }

        # 如果指定了字段列表，只返回这些字段
        if include_fields:
            return {k: v for k, v in data.items() if k in include_fields}

        return data

    def to_mobile_dict(self):
        """
        转换为移动端需要的简化字典格式

        Returns:
            dict: 移动端游戏数据字典
        """
        return {
            'id': self.id,
            'platform': self.platform,
            'gameType': self.game_type,
            'gameCode': self.game_code,
            'nameEn': self.name_en,
            'nameZh': self.name_zh,
            'nameTh': self.name_th,
            'iconUrl': self.icon_url,
            'thumbnailUrl': self.thumbnail_url,
            'bannerUrl': self.banner_url,
            'rtp': float(self.rtp) if self.rtp else None,
            'isHot': self.is_hot,
            'isNew': self.is_new,
            'hasFreeSpin': self.has_free_spin,
            'hasJackpot': self.has_jackpot,
            'sortOrder': self.sort_order,
            'status': self.status
        }

    @staticmethod
    def get_game_list(filter_type='all', game_type=None, platform=None, page_no=1, page_size=20):
        """
        获取游戏列表（分页）

        Args:
            filter_type: 筛选类型 hot/new/all
            game_type: 游戏类型
            platform: 平台名称
            page_no: 页码
            page_size: 每页数量

        Returns:
            tuple: (游戏列表, 总数)
        """
        query = AwcGame.query.filter_by(status=1, del_flag=0)

        # 根据筛选类型添加条件
        if filter_type == 'hot':
            query = query.filter_by(is_hot=1)
        elif filter_type == 'new':
            query = query.filter_by(is_new=1)

        # 按游戏类型筛选
        if game_type:
            query = query.filter_by(game_type=game_type)

        # 按平台筛选
        if platform:
            query = query.filter_by(platform=platform)

        # 获取总数
        total = query.count()

        # 排序和分页
        games = query.order_by(
            AwcGame.sort_order.desc(),
            AwcGame.id.desc()
        ).paginate(
            page=page_no,
            per_page=page_size,
            error_out=False
        )

        return games.items, total

    @staticmethod
    def get_by_game_code(game_code):
        """
        根据游戏代码获取游戏

        Args:
            game_code: 游戏代码

        Returns:
            AwcGame: 游戏对象或None
        """
        return AwcGame.query.filter_by(
            game_code=game_code,
            status=1,
            del_flag=0
        ).first()

    @staticmethod
    def get_platforms():
        """
        获取所有平台列表

        Returns:
            list: 平台名称列表
        """
        platforms = db.session.query(AwcGame.platform).filter_by(
            status=1,
            del_flag=0
        ).distinct().all()

        return [p[0] for p in platforms if p[0]]

    @staticmethod
    def get_game_types():
        """
        获取所有游戏类型列表

        Returns:
            list: 游戏类型列表
        """
        game_types = db.session.query(AwcGame.game_type).filter_by(
            status=1,
            del_flag=0
        ).distinct().all()

        return [gt[0] for gt in game_types if gt[0]]

    def __repr__(self):
        return f'<AwcGame {self.game_code} - {self.name_en}>'
