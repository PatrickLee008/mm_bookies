from datetime import datetime
from app_server import db


class AppPlayerActivityRecord(db.Model):
    """玩家活动记录模型"""
    __tablename__ = 'm_app_player_activity_record'

    # 主键和基本信息
    id = db.Column(db.String(64), primary_key=True, comment='主键ID')
    mb_id = db.Column(db.String(64), nullable=False, comment='玩家ID')
    aid = db.Column(db.String(64), comment='代理ID')
    username = db.Column(db.String(64), nullable=False, comment='玩家账号')

    # 活动信息
    activity_type = db.Column(db.String(20), nullable=False,
                              comment='活动类型：COUPON-优惠券, PROMOTION-优惠活动, INVITATION-邀请活动')
    activity_id = db.Column(db.String(64), nullable=False, comment='活动ID（对应具体活动表的ID）')
    member_coupon_id= db.Column(db.String(64), nullable=False, comment='玩家优惠券表ID')
    activity_name = db.Column(db.String(255), comment='活动名称')

    # 状态和时间
    status = db.Column(db.String(20), nullable=False, default='Active',
                       comment='状态：Active-进行中, Completed-已完成, Cancelled-已取消, Expired-已过期')
    start_time = db.Column(db.DateTime, nullable=False, comment='参与时间')
    end_time = db.Column(db.DateTime, comment='结束时间')

    # 完成条件
    completion_condition = db.Column(db.String(100), comment='完成条件（如达到流水要求、优惠券已使用等）')
    completion_detail = db.Column(db.Text, comment='完成详情（JSON格式，记录具体完成数据）')
    req_turnover = db.Column(db.Numeric(10, 2), comment='要求流水额')
    req_netwin = db.Column(db.Numeric(10, 2), comment='要求净赢额')
    cur_turnover = db.Column(db.Numeric(15, 2), default=0, comment='当前流水额')
    cur_netwin = db.Column(db.Numeric(15, 2), default=0, comment='当前净赢额')
    is_requirement_met = db.Column(db.Integer, default=0, comment='是否达标（0=未达标,1=已达标）')
    bonus_amount = db.Column(db.Numeric(20, 2), default=0, comment='奖励金额（系统/代理赠送的促销奖金，用于取消时计算退款）')
    settlement_round = db.Column(db.Integer, default=1, comment='当前结算轮次，每次达标结算后自增')
    bonus_amount_current_round = db.Column(db.Numeric(20, 2), default=0, comment='当前轮已领取奖励金额，每轮结算后重置')
    turnover_baseline = db.Column(db.Numeric(20, 2), default=0, comment='上一轮结算时的累计流水快照（审计用，不参与流水计算）')
    round_start_time = db.Column(db.DateTime, comment='本轮开始时间，用于隔离本轮投注流水')

    # 审计字段
    remarks = db.Column(db.String(500), comment='备注')
    tenant_id = db.Column(db.String(64), comment='租户ID')
    create_by_id = db.Column(db.String(64), comment='创建人ID')
    create_time = db.Column(db.DateTime, default=datetime.now, comment='创建时间')
    update_by_id = db.Column(db.String(64), comment='更新人ID')
    update_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    del_flag = db.Column(db.Integer, default=0, comment='删除标记（0-正常，1-删除）')

    def to_dict(self):
        """转换为字典"""
        columns = self.__table__.columns.keys()
        result = {}
        for key in columns:
            value = getattr(self, key)
            # 将 DateTime 类型转换为字符串
            if isinstance(value, datetime):
                value = value.strftime('%Y-%m-%d %H:%M:%S') if value else None
            result[key] = value
        return result


db.create_all()
