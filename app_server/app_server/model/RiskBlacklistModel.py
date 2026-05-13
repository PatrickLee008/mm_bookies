"""
风险控制黑名单数据模型
Risk Control Blacklist Model
"""

from datetime import datetime
from app_server import db


class RiskBlacklist(db.Model):
    """风险控制黑名单表"""
    __tablename__ = 'm_app_risk_blacklist'

    # 主键
    id = db.Column(db.String(64), primary_key=True, comment='主键ID')

    # 权限管理字段（记录添加者，不参与黑名单匹配）
    aid = db.Column(db.String(64), comment='代理ID（记录哪个代理添加的，用于权限管理）')

    # 黑名单生效范围控制（参与匹配）
    activity_type = db.Column(db.String(50), comment='生效活动类型（为空表示全活动类型）')
    activity_id = db.Column(db.String(64), comment='生效活动ID（为空表示该类型的全活动）')

    # 追溯信息（记录来源，不参与匹配）
    source_activity_type = db.Column(db.String(50), comment='来源活动类型（记录在哪个活动中被加入）')
    source_activity_id = db.Column(db.String(64), comment='来源活动ID（记录具体活动）')

    # 黑名单信息
    blacklist_type = db.Column(db.String(20), nullable=False, comment='黑名单类型: user-用户, ip-IP地址, device-设备ID')
    blacklist_value = db.Column(db.String(255), nullable=False, comment='黑名单值（用户ID/IP地址/设备ID）')
    reason = db.Column(db.String(500), comment='加入黑名单的原因')
    status = db.Column(db.Integer, nullable=False, default=1, comment='状态: 0-禁用, 1-启用')

    # 审计字段
    create_by_id = db.Column(db.String(64), comment='创建人ID')
    create_by_name = db.Column(db.String(100), comment='创建人姓名')
    create_time = db.Column(db.DateTime, nullable=False, default=datetime.now, comment='创建时间')
    update_by_id = db.Column(db.String(64), comment='更新人ID')
    update_by_name = db.Column(db.String(100), comment='更新人姓名')
    update_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    remarks = db.Column(db.String(500), comment='备注')
    del_flag = db.Column(db.Integer, nullable=False, default=0, comment='删除标记: 0-未删除, 1-已删除')
    tenant_id = db.Column(db.String(64), default='10000', comment='租户ID')

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'aid': self.aid,
            'activity_type': self.activity_type,
            'activity_id': self.activity_id,
            'source_activity_type': self.source_activity_type,
            'source_activity_id': self.source_activity_id,
            'blacklist_type': self.blacklist_type,
            'blacklist_value': self.blacklist_value,
            'reason': self.reason,
            'status': self.status,
            'status_text': '启用' if self.status == 1 else '禁用',
            'create_by_id': self.create_by_id,
            'create_by_name': self.create_by_name,
            'create_time': self.create_time.strftime('%Y-%m-%d %H:%M:%S') if self.create_time else None,
            'update_by_id': self.update_by_id,
            'update_by_name': self.update_by_name,
            'update_time': self.update_time.strftime('%Y-%m-%d %H:%M:%S') if self.update_time else None,
            'remarks': self.remarks
        }

    @staticmethod
    def get_active_blacklist(blacklist_type=None):
        """
        获取所有启用的黑名单

        Args:
            blacklist_type: 黑名单类型（可选）User/IP Address/Device ID (也支持旧值 user/ip/device)

        Returns:
            黑名单记录列表
        """
        query = RiskBlacklist.query.filter_by(
            status=1,
            del_flag=0
        )

        if blacklist_type:
            # 规范化类型值
            blacklist_type = RiskBlacklist.normalize_blacklist_type(blacklist_type)
            query = query.filter_by(blacklist_type=blacklist_type)

        return query.all()

    @staticmethod
    def normalize_blacklist_type(blacklist_type):
        """
        规范化黑名单类型值

        Args:
            blacklist_type: 原始类型值

        Returns:
            规范化后的类型值
        """
        if not blacklist_type:
            return blacklist_type

        # 转换映射
        type_mapping = {
            'user': 'User',
            'User': 'User',
            'ip': 'IP Address',
            'IP': 'IP Address',
            'IP Address': 'IP Address',
            'device': 'Device ID',
            'Device': 'Device ID',
            'Device ID': 'Device ID',
            'imei': 'Device ID',  # IMEI 映射到 Device ID
        }

        return type_mapping.get(blacklist_type, blacklist_type)

    @staticmethod
    def normalize_activity_type(activity_type):
        """
        规范化活动类型值

        Args:
            activity_type: 原始活动类型值

        Returns:
            规范化后的活动类型值
        """
        if not activity_type:
            return activity_type

        # 转换映射（统一为首字母大写格式）
        type_mapping = {
            'coupon': 'Coupon',
            'Coupon': 'Coupon',
            'COUPON': 'Coupon',
            'promotion': 'Promotion',
            'Promotion': 'Promotion',
            'PROMOTION': 'Promotion',
            'invitation': 'Invitation',
            'Invitation': 'Invitation',
            'INVITATION': 'Invitation',
        }

        return type_mapping.get(activity_type, activity_type)

    @staticmethod
    def is_blacklisted(blacklist_type, value, activity_type=None, activity_id=None):
        """
        检查某个值是否在黑名单中（基于活动类型和ID匹配）

        Args:
            blacklist_type: 黑名单类型 User/IP Address/Device ID (也支持旧值 user/ip/device)
            value: 要检查的值
            activity_type: 当前活动类型（可选，如 'Coupon'）
            activity_id: 当前活动ID（可选，如 'coupon-001'）

        Returns:
            True: 在黑名单中, False: 不在黑名单中

        匹配逻辑：
        1. 全局黑名单：黑名单的 activity_type=NULL, activity_id=NULL
        2. 类型级黑名单：黑名单的 activity_type=当前类型, activity_id=NULL
        3. 活动级黑名单：黑名单的 activity_type=当前类型, activity_id=当前活动

        注意：
        - aid（代理ID）仅用于权限管理，不参与匹配
        - source_activity_type/id 仅用于追溯，不参与匹配
        """
        from sqlalchemy import or_, and_

        # 规范化类型值
        blacklist_type = RiskBlacklist.normalize_blacklist_type(blacklist_type)
        activity_type = RiskBlacklist.normalize_activity_type(activity_type)

        # 基础条件
        conditions = [
            RiskBlacklist.blacklist_type == blacklist_type,
            RiskBlacklist.blacklist_value == value,
            RiskBlacklist.status == 1,
            RiskBlacklist.del_flag == 0
        ]

        # 构建活动范围匹配条件
        scope_conditions = []

        # 1. 全局黑名单（activity_type 和 activity_id 都为空）
        scope_conditions.append(
            and_(
                RiskBlacklist.activity_type.is_(None),
                RiskBlacklist.activity_id.is_(None)
            )
        )

        # 2. 如果提供了 activity_type
        if activity_type:
            # 类型级黑名单（activity_type 匹配，activity_id 为空）
            scope_conditions.append(
                and_(
                    RiskBlacklist.activity_type == activity_type,
                    RiskBlacklist.activity_id.is_(None)
                )
            )

            # 3. 如果同时提供了 activity_id
            if activity_id:
                # 活动级黑名单（activity_type 和 activity_id 都匹配）
                scope_conditions.append(
                    and_(
                        RiskBlacklist.activity_type == activity_type,
                        RiskBlacklist.activity_id == activity_id
                    )
                )

        # 组合所有条件
        query = RiskBlacklist.query.filter(
            and_(*conditions),
            or_(*scope_conditions)
        )

        count = query.count()
        return count > 0

    @staticmethod
    def add_blacklist(blacklist_type, value, reason=None,
                     aid=None,
                     activity_type=None, activity_id=None,
                     source_activity_type=None, source_activity_id=None,
                     create_by_id=None, create_by_name=None):
        """
        添加到黑名单

        Args:
            blacklist_type: 黑名单类型 User/IP Address/Device ID (也支持旧值 user/ip/device)
            value: 黑名单值
            reason: 原因
            aid: 代理ID（记录哪个代理添加的，用于权限管理）
            activity_type: 生效活动类型（控制黑名单生效范围）
            activity_id: 生效活动ID（控制黑名单生效范围）
            source_activity_type: 来源活动类型（记录在哪个活动中被加入）
            source_activity_id: 来源活动ID（记录具体活动）
            create_by_id: 创建人ID
            create_by_name: 创建人姓名

        Returns:
            RiskBlacklist 对象
        """
        import uuid

        # 规范化类型值
        blacklist_type = RiskBlacklist.normalize_blacklist_type(blacklist_type)
        activity_type = RiskBlacklist.normalize_activity_type(activity_type)
        source_activity_type = RiskBlacklist.normalize_activity_type(source_activity_type)

        # 检查是否已存在相同的黑名单记录（基于生效范围）
        existing = RiskBlacklist.query.filter(
            RiskBlacklist.blacklist_type == blacklist_type,
            RiskBlacklist.blacklist_value == value,
            RiskBlacklist.activity_type == activity_type if activity_type else RiskBlacklist.activity_type.is_(None),
            RiskBlacklist.activity_id == activity_id if activity_id else RiskBlacklist.activity_id.is_(None),
            RiskBlacklist.del_flag == 0
        ).first()

        if existing:
            # 如果存在但被禁用，启用它并更新信息
            if existing.status == 0:
                existing.status = 1
                existing.reason = reason or existing.reason
                existing.aid = aid or existing.aid
                existing.source_activity_type = source_activity_type or existing.source_activity_type
                existing.source_activity_id = source_activity_id or existing.source_activity_id
                existing.update_time = datetime.now()
                db.session.commit()
                return existing
            # 如果已存在且启用，直接返回
            return existing

        # 创建新的黑名单记录
        blacklist = RiskBlacklist(
            id=str(uuid.uuid4()),
            aid=aid,
            activity_type=activity_type,
            activity_id=activity_id,
            source_activity_type=source_activity_type,
            source_activity_id=source_activity_id,
            blacklist_type=blacklist_type,
            blacklist_value=value,
            reason=reason,
            status=1,
            create_by_id=create_by_id,
            create_by_name=create_by_name,
            create_time=datetime.now(),
            del_flag=0,
            tenant_id='10000'
        )

        db.session.add(blacklist)
        db.session.commit()

        return blacklist

    @staticmethod
    def remove_blacklist(blacklist_type, value):
        """
        从黑名单移除（软删除）

        Args:
            blacklist_type: 黑名单类型 User/IP Address/Device ID (也支持旧值 user/ip/device)
            value: 黑名单值

        Returns:
            True: 成功, False: 失败
        """
        # 规范化类型值
        blacklist_type = RiskBlacklist.normalize_blacklist_type(blacklist_type)

        blacklist = RiskBlacklist.query.filter_by(
            blacklist_type=blacklist_type,
            blacklist_value=value,
            del_flag=0
        ).first()

        if blacklist:
            blacklist.del_flag = 1
            blacklist.update_time = datetime.now()
            db.session.commit()
            return True

        return False

    @staticmethod
    def disable_blacklist(blacklist_type, value):
        """
        禁用黑名单（不删除，只禁用）

        Args:
            blacklist_type: 黑名单类型 User/IP Address/Device ID (也支持旧值 user/ip/device)
            value: 黑名单值

        Returns:
            True: 成功, False: 失败
        """
        # 规范化类型值
        blacklist_type = RiskBlacklist.normalize_blacklist_type(blacklist_type)

        blacklist = RiskBlacklist.query.filter_by(
            blacklist_type=blacklist_type,
            blacklist_value=value,
            del_flag=0
        ).first()

        if blacklist:
            blacklist.status = 0
            blacklist.update_time = datetime.now()
            db.session.commit()
            return True

        return False

    def __repr__(self):
        return f'<RiskBlacklist {self.blacklist_type}:{self.blacklist_value}>'
