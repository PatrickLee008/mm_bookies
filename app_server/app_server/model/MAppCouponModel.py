from datetime import datetime
from decimal import Decimal
from app_server import db


class MAppCoupon(db.Model):
    """优惠券模型 - 根据实际数据库表结构定义"""
    __tablename__ = 'm_app_coupon'
    
    # 主键字段
    id = db.Column(db.String(64), primary_key=True, comment='优惠券唯一ID')
    
    # 代理相关
    aid = db.Column(db.String(64), comment='代理ID')
    p_ag_share = db.Column(db.String(128), comment='代理分成比例/规则')
    target_agents = db.Column(db.Text, comment='目标代理列表（House创建时可指定特定代理，JSON格式存储代理ID列表）')
    
    # 基本信息
    p_name = db.Column(db.String(100), comment='优惠券名称')
    p_start = db.Column(db.DateTime, comment='优惠券有效开始时间')
    p_end = db.Column(db.DateTime, comment='优惠券有效结束时间')
    p_expire = db.Column(db.DateTime, comment='实际过期时间（可手动设置）')
    p_code = db.Column(db.String(30), comment='优惠券兑换码')
    p_type = db.Column(db.String(30), comment='优惠券类型（如首存/再存/通用）')
    p_cond = db.Column(db.Text, comment='使用条件（JSON格式规则）')
    p_at_ep_cond = db.Column(db.Text, comment='自动派发条件（如存款金额触发）')
    p_at_billout = db.Column(db.Integer, comment='是否自动出账（0否1是）')
    p_at_ep = db.Column(db.Integer, comment='是否自动派发（0否1是）')
    p_at_ep_amt = db.Column(db.Numeric(65, 30), comment='自动派发触发金额')
    p_ep_cond = db.Column(db.Text, comment='手动派发条件')
    p_ep_amtrq = db.Column(db.Numeric(65, 30), comment='手动派发要求金额')
    p_lm_bo = db.Column(db.Integer, comment='是否限制返水（0否1是）')
    p_lm_bo_amt = db.Column(db.Numeric(65, 30), comment='返水限制金额')
    
    # 奖金限制相关
    p_lm_j_mp = db.Column(db.Text, comment='奖金限制玩法')
    p_lm_j_pc = db.Column(db.Integer, comment='限制优惠券总数量')
    p_lm_j_wt = db.Column(db.Integer, comment='奖金限制流水倍数')
    p_lm_j_rs = db.Column(db.Text, comment='奖金限制结果（如仅限输局）')
    p_lmu_j_tt = db.Column(db.Integer, comment='用户总奖金上限')
    p_lmu_j_pd = db.Column(db.Integer, comment='用户每日奖金上限')
    p_lm_rank = db.Column(db.String(128), comment='限制会员等级')
    p_lm_game_hall = db.Column(db.String(128), comment='限制游戏平台（如PT/AG）')
    p_lm_game_type = db.Column(db.String(128), comment='限制游戏类型（如老虎机/真人）')
    
    # 显示相关
    p_tray = db.Column(db.Integer, comment='是否显示在托盘（0否1是）')
    p_app_hidden = db.Column(db.Integer, comment='是否APP隐藏（0否1是）')
    
    # 支付渠道相关
    dps_list = db.Column(db.Text, comment='指定支付渠道列表')
    dps_amt_rq = db.Column(db.Numeric(65, 30), comment='支付渠道要求金额')
    
    # 奖金相关
    bonus_type = db.Column(db.String(128), comment='奖金类型（固定金额/百分比）')
    bonus_amount = db.Column(db.Numeric(65, 30), comment='奖金金额/比例')
    bonus_maximum = db.Column(db.Numeric(65, 30), comment='奖金上限金额')
    p_extra_cond = db.Column(db.Text, comment='额外使用条件')
    p_content = db.Column(db.Text, comment='优惠券内容描述')
    p_tt_jc = db.Column(db.Integer, comment='总已领取次数')
    p_status = db.Column(db.String, comment='状态（Active、Finished、Cancelled、Expired）')
    p_remark = db.Column(db.String(255), comment='管理员备注')
    mn_username = db.Column(db.String(50), comment='创建人用户名')
    
    # 链接和图片
    p_link = db.Column(db.String(512), comment='优惠券跳转链接')
    p_img_mb = db.Column(db.String(512), comment='移动端图片URL')
    p_img_dt = db.Column(db.String(512), comment='桌面端图片URL')
    p_min_deposit = db.Column(db.Numeric(65, 30), comment='最低存款额要求')
    min_bet_amount_required = db.Column(db.Numeric(10, 2), comment='使用优惠券所需的最低投注金额')
    
    # 注册时间限制
    p_register_start = db.Column(db.DateTime, comment='注册时间限制-开始')
    p_register_end = db.Column(db.DateTime, comment='注册时间限制-结束')
    p_register_display = db.Column(db.Integer, comment='新注册用户可见性（0否1是）')
    
    # 状态相关
    status = db.Column(db.Integer, default=1, comment='状态: 0-停用, 1-启用')
    sort = db.Column(db.Integer, comment='排序序号')
    
    # 审计字段
    create_by_id = db.Column(db.String(64), comment='创建人')
    create_time = db.Column(db.DateTime, comment='创建时间')
    update_by_id = db.Column(db.String(64), comment='更新人')
    update_time = db.Column(db.DateTime, comment='更新时间')
    remarks = db.Column(db.String(255), comment='备注信息')
    del_flag = db.Column(db.Integer, default=0, comment='删除标记')
    tenant_id = db.Column(db.String(64), comment='租户ID')
    
    # 资金来源和托管
    coupon_total_amount = db.Column(db.Numeric(15, 2), comment='优惠券总金额')
    used_amount = db.Column(db.Numeric(15, 2), default=Decimal('0'), comment='已使用金额')
    remaining_amount = db.Column(db.Numeric(15, 2), comment='剩余金额')
    escrow_status = db.Column(db.Integer, default=0, comment='托管状态：0-未托管，1-已托管，2-已退还')
    fund_source_type = db.Column(db.String(20), comment='资金来源类型：HOUSE-平台资金，AGENT-代理资金')
    
    # 风险管理
    imei_limit_count = db.Column(db.Integer, comment='IMEI设备限制次数')
    ip_time_window_hours = db.Column(db.Integer, comment='IP时间窗口（小时）')
    ip_limit_count = db.Column(db.Integer, comment='IP地址限制次数')
    geo_fencing_enabled = db.Column(db.Integer, default=0, comment='地理围栏是否启用：0-禁用，1-启用')
    allowed_regions = db.Column(db.Text, comment='允许的地区列表（逗号分隔）')
    
    # 净赢条件
    net_win_enabled = db.Column(db.Integer, default=0, comment='净赢条件是否启用：0-禁用，1-启用')
    net_win_condition_type = db.Column(db.String(20), comment='净赢条件类型：GREATER_EQUAL-大于等于，LESS_EQUAL-小于等于')
    net_win_amount = db.Column(db.Numeric(15, 2), comment='净赢目标金额')

    def __repr__(self):
        return f'<MAppCoupon(id={self.id}, p_name={self.p_name}, p_code={self.p_code})>'
    
    @property
    def pname(self):
        """兼容性属性，返回p_name"""
        return self.p_name
    
    @property
    def pcode(self):
        """兼容性属性，返回p_code"""
        return self.p_code
    
    @property
    def pstatus(self):
        """兼容性属性，返回p_status"""
        return self.p_status
    
    @property
    def p_des(self):
        """兼容性属性，返回p_content"""
        return self.p_content
    
    @property
    def plmu_jtt(self):
        """兼容性属性，返回p_lmu_j_tt (用户总奖金上限)"""
        return self.p_lmu_j_tt
    
    @property
    def plmu_jpd(self):
        """兼容性属性，返回p_lmu_j_pd (用户每日奖金上限)"""
        return self.p_lmu_j_pd
    
    @property
    def turnover_rate(self):
        """兼容性属性，返回p_lm_j_wt (流水倍数) 或默认值1"""
        return Decimal(str(self.p_lm_j_wt)) if self.p_lm_j_wt else Decimal('1')

    def is_valid(self):
        """检查优惠券是否有效"""
        if self.del_flag != 0 or self.p_status != 1:
            return False
        
        now = datetime.now()
        
        # 检查有效期
        if self.p_start and now < self.p_start:
            return False
        if self.p_end and now > self.p_end:
            return False
        if self.p_expire and now > self.p_expire:
            return False
        
        # 检查是否是代理创建的优惠券且余额是否充足
        if self.fund_source_type == 'AGENT':
            if not self.remaining_amount or self.remaining_amount <= 0:
                return False
        
        return True
    
    def can_be_claimed_by_user(self, user_id):
        """检查用户是否可以领取此优惠券（基本检查）"""
        if not self.is_valid():
            return False, "Coupon is not valid"
        
        # 这里可以添加更多用户特定的检查逻辑
        # 例如：用户注册时间检查、用户类型检查等
        
        return True, "Can be claimed"
    
    def get_display_info(self):
        """获取用于显示的优惠券信息"""
        return {
            'id': self.id,
            'name': self.p_name,
            'code': self.p_code,
            'type': self.p_type,
            'description': self.p_content,
            'bonus_amount': float(self.bonus_amount) if self.bonus_amount else 0,
            'bonus_maximum': float(self.bonus_maximum) if self.bonus_maximum else 0,
            'start_date': self.p_start.strftime('%Y-%m-%d %H:%M:%S') if self.p_start else None,
            'end_date': self.p_end.strftime('%Y-%m-%d %H:%M:%S') if self.p_end else None,
            'expire_date': self.p_expire.strftime('%Y-%m-%d %H:%M:%S') if self.p_expire else None,
            'min_deposit': float(self.p_min_deposit) if self.p_min_deposit else 0,
            'mobile_image': self.p_img_mb,
            'desktop_image': self.p_img_dt,
            'link': self.p_link,
            'fund_source_type': self.fund_source_type,
            'remaining_amount': float(self.remaining_amount) if self.remaining_amount else 0,
            'net_win_enabled': bool(self.net_win_enabled),
            'net_win_condition_type': self.net_win_condition_type,
            'net_win_amount': float(self.net_win_amount) if self.net_win_amount else 0,
            'status': self.p_status,
            'auto_dispatch': bool(self.p_at_ep) if self.p_at_ep is not None else False,
            'auto_billout': bool(self.p_at_billout) if self.p_at_billout is not None else False
        }
    
    def to_dict(self):
        """转换为字典，保持向后兼容"""
        return {
            'id': self.id,
            'aid': self.aid,
            'pname': self.p_name,
            'pcode': self.p_code,
            'p_des': self.p_content,
            'pstatus': self.p_status,
            'bonus_amount': float(self.bonus_amount) if self.bonus_amount else 0,
            'bonus_type': self.bonus_type,
            'bonus_maximum': float(self.bonus_maximum) if self.bonus_maximum else 0,
            'p_start': self.p_start.strftime('%Y-%m-%d %H:%M:%S') if self.p_start else None,
            'p_end': self.p_end.strftime('%Y-%m-%d %H:%M:%S') if self.p_end else None,
            'p_expire': self.p_expire.strftime('%Y-%m-%d %H:%M:%S') if self.p_expire else None,
            'fund_source_type': self.fund_source_type,
            'remaining_amount': float(self.remaining_amount) if self.remaining_amount else 0,
            'used_amount': float(self.used_amount) if self.used_amount else 0,
            'net_win_enabled': self.net_win_enabled,
            'net_win_condition_type': self.net_win_condition_type,
            'net_win_amount': float(self.net_win_amount) if self.net_win_amount else 0,
            'p_min_deposit': float(self.p_min_deposit) if self.p_min_deposit else 0,
            'create_time': self.create_time.strftime('%Y-%m-%d %H:%M:%S') if self.create_time else None,
            'update_time': self.update_time.strftime('%Y-%m-%d %H:%M:%S') if self.update_time else None
        }