from datetime import datetime
from decimal import Decimal
from app_server import db


class MAppMemberCoupon(db.Model):
    """会员优惠券领取记录模型 - 根据实际数据库表结构定义"""
    __tablename__ = 'm_app_member_coupon'
    
    # 主键和关联
    id = db.Column(db.String(64), primary_key=True, comment='唯一标识ID')
    link_id = db.Column(db.String(64), comment='关联ID（可能关联活动或订单）')
    p_id = db.Column(db.String(64), comment='优惠活动ID')
    p_name = db.Column(db.String(64), comment='优惠活动名称')
    mb_id = db.Column(db.String(64), comment='会员ID')
    mb_username = db.Column(db.String(64), comment='会员用户名')
    
    # 时间信息
    start_time = db.Column(db.DateTime, comment='活动开始时间')
    end_time = db.Column(db.DateTime, comment='活动结束时间')
    claim_time = db.Column(db.DateTime, comment='领取时间')  # 与create_time保持一致
    use_time = db.Column(db.DateTime, comment='使用时间')
    expire_time = db.Column(db.DateTime, comment='过期时间')

    # 游戏相关
    game_hall = db.Column(db.String(64), comment='游戏厅别（如PT、AG等）')
    game_type = db.Column(db.String(64), comment='游戏类型（如slot、live等）')
    
    # 流水和净赢
    cur_turnover = db.Column(db.Numeric(10, 0), comment='当前流水额')
    cur_netwin = db.Column(db.Numeric(10, 0), comment='当前净赢额')
    req_turnover = db.Column(db.Numeric(10, 0), comment='要求流水额')
    req_netwin = db.Column(db.Numeric(10, 0), comment='要求净赢额')
    
    # 金额相关
    money = db.Column(db.Numeric(10, 0), comment='优惠金额/奖金')
    cur_balance = db.Column(db.Numeric(10, 0), comment='当前余额')
    end_balance = db.Column(db.Numeric(10, 0), comment='结束余额')
    
    # 状态和结果
    p_status = db.Column(db.String(32), comment='活动状态（如pending、approved、rejected）')
    p_result = db.Column(db.String(255), comment='活动结果说明')
    
    # 网络相关
    mb_ip = db.Column(db.String(64), comment='会员IP地址')
    mn_id = db.Column(db.String(64), comment='会员数字ID（可能为冗余字段）')
    
    # 渠道信息
    jp_channel = db.Column(db.String(255), comment='奖金派发渠道')
    ep_channel = db.Column(db.String(255), comment='活动参与渠道')
    
    # 基础字段
    status = db.Column(db.String, default=1, comment='状态: Unused, Used, Expired')
    sort = db.Column(db.Integer, comment='排序序号')
    
    # 审计字段
    create_by_id = db.Column(db.String(64), comment='创建人')
    create_time = db.Column(db.DateTime, comment='创建时间')
    update_by_id = db.Column(db.String(64), comment='更新人')
    update_time = db.Column(db.DateTime, comment='更新时间')
    remarks = db.Column(db.String(255), comment='备注信息')
    del_flag = db.Column(db.Integer, default=0, comment='删除标记')
    tenant_id = db.Column(db.String(64), comment='租户ID')
    
    # 兼容性属性 - 保持与原有代码的兼容性
    @property
    def p_code(self):
        """兼容性属性，从关联的优惠券获取code"""
        # 这里可以通过p_id关联查询m_app_coupon表获取p_code
        # 为了避免N+1查询，这里返回None或需要在查询时join表
        return None
    
    @property
    def bonus_amount(self):
        """兼容性属性，返回money字段"""
        return self.money
    
    @property
    def turnover_requirement(self):
        """兼容性属性，返回req_turnover字段"""
        return self.req_turnover
    
    @property
    def turnover_progress(self):
        """兼容性属性，返回cur_turnover字段"""
        return self.cur_turnover

    # expire_time已经是实际字段，不需要property
    
    @property
    def ip_address(self):
        """兼容性属性，返回mb_ip字段"""
        return self.mb_ip
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'mb_id': self.mb_id,
            'p_id': self.p_id,
            'p_name': self.p_name,
            'mb_username': self.mb_username,
            'bonus_amount': float(self.money) if self.money else 0,
            'turnover_requirement': float(self.req_turnover) if self.req_turnover else 0,
            'turnover_progress': float(self.cur_turnover) if self.cur_turnover else 0,
            'status': self.status,
            'p_status': self.p_status,
            'claim_time': self.claim_time.strftime('%Y-%m-%d %H:%M:%S') if self.claim_time else None,
            'use_time': self.use_time.strftime('%Y-%m-%d %H:%M:%S') if self.use_time else None,
            'expire_time': self.expire_time.strftime('%Y-%m-%d %H:%M:%S') if self.expire_time else None,
            'create_time': self.create_time.strftime('%Y-%m-%d %H:%M:%S') if self.create_time else None,
            'ip_address': self.mb_ip
        }