"""
促销活动 Model
对应 Java 端的 MAppPromotion
"""
from sqlalchemy import Column, String, Integer, DECIMAL, DateTime, Text
from app_server.utils.BaseSaasModel import BaseSaasModel


class MAppPromotion(BaseSaasModel):
    __tablename__ = 'm_app_promotion'

    id = Column(String(64), primary_key=True, comment='ID')

    # 基本信息
    title = Column(String(200), nullable=True, comment='活动标题')
    slogan = Column(String(300), nullable=True, comment='宣传语')
    description = Column(Text, nullable=True, comment='活动描述')
    image_url = Column(String(500), nullable=True, comment='促销图片URL')

    # 时间配置
    start_date = Column(DateTime, nullable=True, comment='开始日期')
    end_date = Column(DateTime, nullable=True, comment='结束日期')
    scheduled_start_time = Column(DateTime, nullable=True, comment='计划开始时间')

    # 参与条件
    reward_amount = Column(DECIMAL(20, 2), nullable=True, comment='固定奖励金额')
    reward_amount_type = Column(String(20), default='Fixed', comment='奖励金额类型：Fixed-固定金额/Percent-百分比')
    participation_amount_type = Column(String(20), default='Fixed', comment='参与金额类型：Fixed-固定金额/Range-范围')
    participation_amount = Column(DECIMAL(10, 2), default=0.00, comment='参与金额（当 participation_amount_type=Fixed 时使用）')
    min_participation_amount = Column(DECIMAL(10, 2), default=0.00, comment='最小参与金额（当 participation_amount_type=Range 时使用）')
    max_participation_amount = Column(DECIMAL(10, 2), default=0.00, comment='最大参与金额（当 participation_amount_type=Range 时使用）')
    usage_scenario_config = Column(Text, nullable=True, comment='使用场景配置（JSON格式，存储游戏场景、游戏类型等限制）')
    auto_end_amount = Column(DECIMAL(10, 2), default=0.00, comment='自动结束金额阈值（Promo Wallet余额低于此值时自动结束活动）')

    # 注册条件
    registration_criteria = Column(String(50), nullable=True, comment='注册条件：ALL_USERS-所有用户 NEW_USERS-新用户 TIME_PERIOD-时间段')
    registration_start_date = Column(DateTime, nullable=True, comment='注册开始日期')
    registration_end_date = Column(DateTime, nullable=True, comment='注册结束日期')

    # 支付条件
    turnover_multiplier = Column(DECIMAL(10, 2), nullable=True, comment='流水倍数')
    net_win_amount = Column(DECIMAL(20, 2), nullable=True, comment='净赢金额')
    payout_limit = Column(DECIMAL(20, 2), nullable=True, comment='最大支付限额')

    # 游戏配置
    egames_config = Column(Text, nullable=True, comment='eGames配置（JSON格式）')
    football_config = Column(Text, nullable=True, comment='足球配置（JSON格式）')

    # 结束与提现
    manual_end_enabled = Column(Integer, default=0, comment='是否启用手动结束：1-启用 0-禁用')
    manual_end_min_amount = Column(DECIMAL(20, 2), nullable=True, comment='手动结束最小金额')
    auto_withdrawal_enabled = Column(Integer, default=0, comment='是否启用自动提现：1-启用 0-禁用')
    max_withdrawal_amount = Column(DECIMAL(20, 2), nullable=True, comment='最大提现金额')

    # 状态与代理
    status = Column(String(20), default='Active', comment='状态：Inactive-未激活 Active-激活 Scheduled-计划中')
    agent_id = Column(String(64), nullable=True, comment='创建活动的代理ID')

    # 奖金池
    bonus_pool = Column(DECIMAL(20, 2), nullable=True, comment='奖金池总额：代理投入的促销资金')
    bonus_pool_remaining = Column(DECIMAL(20, 2), nullable=True, comment='奖金池余额：剩余可用资金')
    is_pool_exhausted = Column(Integer, default=0, comment='奖金池是否耗尽：1-耗尽 0-未耗尽')

    # 资金管理
    fund_source_type = Column(String(20), default='AGENT', comment='资金来源类型：AGENT-代理余额, HOUSE-平台余额')
    escrow_status = Column(Integer, default=0, comment='托管状态：0-未托管, 1-已托管扣款, 2-已退款')
    used_amount = Column(DECIMAL(20, 2), default=0.00, comment='已使用金额（已发放的奖励总额）')

    # 参与次数限制
    max_total_participations = Column(Integer, default=0, comment='活动总参与次数上限（0表示无限制，所有玩家累计）')
    current_total_participations = Column(Integer, default=0, comment='当前总参与次数（所有玩家累计）')
    participation_frequency = Column(String(20), default='Daily', comment='用户参与频率限制类型：Daily-每天，Weekly-每周，Monthly-每月，Once-仅一次')
    max_participations_per_user = Column(Integer, default=0, comment='每个用户在频率周期内可参与次数上限（0表示无限制）')

    # 其他
    sort = Column(Integer, default=0, comment='排序')
    remarks = Column(Text, nullable=True, comment='备注信息')

    # 审计字段
    create_by_id = Column(String(64), nullable=True, comment='创建人ID')
    create_time = Column(DateTime, nullable=True, comment='创建时间')
    update_by_id = Column(String(64), nullable=True, comment='更新人ID')
    update_time = Column(DateTime, nullable=True, comment='更新时间')
    del_flag = Column(Integer, default=0, comment='删除标记：0-未删除 1-已删除')
    tenant_id = Column(String(64), default='10000', comment='租户ID')

    def __repr__(self):
        return f"<MAppPromotion(id={self.id}, title={self.title}, status={self.status})>"
