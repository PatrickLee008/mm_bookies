# -*- coding: utf-8 -*-
"""
AWC游戏收藏模型
对应数据库表: m_awc_game_favourite

@author: Arthur
@date: 2025-11-06
"""

from app_server import db
from sqlalchemy import Column, String, DateTime
from datetime import datetime


class AwcGameFavourite(db.Model):
    """AWC游戏收藏模型"""
    __tablename__ = 'm_awc_game_favourite'

    # 主键
    id = Column(String(64), primary_key=True, comment="主键ID")

    # 关联字段
    mb_id = Column(String(64), nullable=False, comment="会员ID")
    game_id = Column(String(64), nullable=False, comment="游戏ID")
    game_code = Column(String(100), nullable=False, comment="游戏代码")

    # 时间字段
    create_time = Column(DateTime, default=datetime.now, comment="收藏时间")

    # 状态字段
    del_flag = Column(db.Integer, default=0, comment="删除标记(0-正常,1-删除)")
    tenant_id = Column(String(64), default='10000', comment="租户ID")

    @staticmethod
    def is_favourite(mb_id, game_code):
        """
        检查游戏是否已收藏

        Args:
            mb_id: 会员ID
            game_code: 游戏代码

        Returns:
            bool: 是否已收藏
        """
        return AwcGameFavourite.query.filter_by(
            mb_id=mb_id,
            game_code=game_code,
            del_flag=0
        ).first() is not None

    @staticmethod
    def get_user_favourites(mb_id):
        """
        获取用户收藏的游戏代码列表

        Args:
            mb_id: 会员ID

        Returns:
            list: 游戏代码列表
        """
        favourites = AwcGameFavourite.query.filter_by(
            mb_id=mb_id,
            del_flag=0
        ).order_by(AwcGameFavourite.create_time.desc()).all()

        return [fav.game_code for fav in favourites]

    @staticmethod
    def add_favourite(mb_id, game_id, game_code):
        """
        添加收藏

        Args:
            mb_id: 会员ID
            game_id: 游戏ID
            game_code: 游戏代码

        Returns:
            bool: 是否添加成功
        """
        from app_server.utils.Kits import Kits

        # 检查是否已收藏
        existing = AwcGameFavourite.query.filter_by(
            mb_id=mb_id,
            game_code=game_code,
            del_flag=0
        ).first()

        if existing:
            return False  # 已存在

        # 创建新收藏
        favourite = AwcGameFavourite(
            id=Kits.generate_uuid(),
            mb_id=mb_id,
            game_id=game_id,
            game_code=game_code
        )

        db.session.add(favourite)
        db.session.commit()
        return True

    @staticmethod
    def remove_favourite(mb_id, game_code):
        """
        取消收藏

        Args:
            mb_id: 会员ID
            game_code: 游戏代码

        Returns:
            bool: 是否取消成功
        """
        favourite = AwcGameFavourite.query.filter_by(
            mb_id=mb_id,
            game_code=game_code,
            del_flag=0
        ).first()

        if favourite:
            # 为了避免unique constraint 'uk_member_game'冲突，直接删除记录而不是标记删除
            db.session.delete(favourite)
            db.session.commit()
            return True

        return False

    def __repr__(self):
        return f'<AwcGameFavourite {self.mb_id} - {self.game_code}>'
