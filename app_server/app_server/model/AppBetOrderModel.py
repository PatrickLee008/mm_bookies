from app_server import db
from sqlalchemy import Column, String, DECIMAL, DateTime, Integer, Boolean
from decimal import Decimal
import datetime

from app_server.model.MatchModel import Match
from app_server.model.OrderModel import Order
from app_server.utils.BaseSaasModel import BaseSaasModel
from app_server.utils.Kits import Kits


class BetStatus:
    Pending = "Pending"
    Win = "Win"
    Lose = "Lose"
    Draw = "Draw"
    Cancel = "Cancel"
    Refund = "Refund"
    Rejected = "Rejected"
    HalfWin = "HalfWin"
    HalfLose = "HalfLose"


class GameStatus:
    Pending = "Pending"
    Running = "Running"
    Finished = "Finished"
    Cancelled = "Cancelled"
    Rejected = "Rejected"


class PayWallet:
    Money = "Money"
    Promotion = "Promotion"


# 下注订单
class AppBetOrder(BaseSaasModel):
    __tablename__ = 'm_app_bet_order'

    # 主键
    id = Column(String(64), primary_key=True, comment="订单ID")

    # 用户相关
    aid = Column(String(64), comment="代理ID")
    mb_id = Column(String(64), comment="会员ID")
    mb_username = Column(String(64), comment="会员用户名")
    game_session_id = Column(String(64), comment="游戏会话ID（关联m_app_game_session表）")

    # 游戏相关
    game_id = Column(String(64), comment="游戏ID")
    game_type = Column(String(64), comment="游戏类型：（从字典读取）Sports")
    game_type_sub = Column(String(64), comment="1X2游戏子类型：（从字典读取）Football")
    game_ratio = Column(String(64), comment="游戏赔率比例")
    game_status = Column(String(64), comment="游戏状态（从字典读取）")
    home = Column(String(64), comment="主队")
    away = Column(String(64), comment="客队")
    home_score = Column(String(10), comment="主队得分")
    away_score = Column(String(10), comment="客队得分")

    # 投注相关
    bet_type = Column(String(64), comment="投注类型（单Single、混合Mixparlay）（从字典读取）")
    bet_type_info = Column(String(64), comment="下注描述")
    bet_type_sub = Column(String(64), comment="投注子类型（具体玩法）（从字典读取）")
    bet_type_sub2 = Column(String(64), comment="投注子类型2")
    bet_group = Column(String(64), comment="投注组别")
    bet_status = Column(String(64), comment="投注状态（从字典读取）")

    # 金额相关
    stake = Column(DECIMAL(20, 2), comment="投注金额")
    stake_actual = Column(DECIMAL(20, 2), comment="实际投注金额")
    netwin = Column(DECIMAL(20, 2), default=Decimal('0.00'), comment="净赢金额")
    netwin_actual = Column(DECIMAL(20, 2), default=Decimal('0.00'), comment="实际净赢金额")
    fee_pt = Column(DECIMAL(5, 2), default=Decimal('0.00'), comment="手续费百分比")
    fee_actual = Column(DECIMAL(20, 2), default=Decimal('0.00'), comment="实际手续费")
    odds = Column(DECIMAL(10, 2), comment="赔率")
    league = Column(String(64), comment="联赛")
    order_count = Column(Integer, nullable=False, server_default='1', comment="订单数量")
    lose_team = Column(String(32), comment="让球方1主队,2客队")
    draw_bunko = Column(String(4), comment="平局胜负(0:+;1:-)")
    draw_odds = Column(String(4), comment="平局赔率（%）")
    lose_ball_num = Column(String(16), comment="胜负时：让球数/大小球时：球数")

    # 优惠相关
    in_promotion = Column(Boolean, nullable=False, server_default='0', default=False, comment="是否优惠券下注(0否1是)")
    pro_id = Column(String(64), comment="优惠券ID")
    activity_record_id = Column(String(64), comment="活动记录ID（关联m_app_player_activity_record.id）")

    # 其他信息
    currency = Column(String(5), comment="货币类型")
    is_credit = Column(Boolean, default=False, comment="是否信用投注(0否1是)")
    pay_wallet = Column(String(32), comment="付款账户（Money：主钱包，Promotion：活动钱包）（从字典读取）")
    platform_source = Column(String(32), default="1x2", comment="平台来源")

    __mapper_args__ = {
        "order_by": db.text("create_time desc"),
    }

    # 新增
    @staticmethod
    def create_new(aid=None, mb_id=None, mb_username=None, game_id=None,
                   game_type=None, game_type_sub=None, game_ratio=None,
                   bet_type=None, bet_type_sub=None, bet_group=None,
                   stake=None, stake_actual=None, netwin=0.00, netwin_actual=0.00,
                   fee_pt=0.00, fee_actual=0.00, odds=None, game_status=None,
                   bet_status=None, in_promotion=False, pro_id=None, activity_record_id=None,
                   currency=None, is_credit=False, pay_wallet=None, create_by_id=None, **kwargs):
        """
        创建新的下注订单实例
        
        Args:
            aid: 代理ID
            mb_id: 会员ID  
            mb_username: 会员用户名
            game_id: 游戏ID
            game_type: 游戏类型
            game_type_sub: 游戏子类型
            game_ratio: 游戏赔率比例
            bet_type: 投注类型
            bet_type_sub: 投注子类型
            bet_group: 投注组别
            stake: 投注金额
            stake_actual: 实际投注金额
            netwin: 净赢金额，默认0.00
            netwin_actual: 实际净赢金额，默认0.00
            fee_pt: 手续费百分比，默认0.00
            fee_actual: 实际手续费，默认0.00
            odds: 赔率
            game_status: 游戏状态
            bet_status: 投注状态
            in_promotion: 是否优惠券下注，默认False
            pro_id: 优惠券ID
            activity_record_id: 活动记录ID
            currency: 货币类型
            is_credit: 是否信用投注，默认False
            pay_wallet: 付款账户
            create_by_id: 创建人ID
            **kwargs: 其他参数
            
        Returns:
            AppBetOrder: 新创建的订单实例
        """
        # 自动生成订单ID
        order_id = str(Kits.generate_uuid())

        # 创建订单实例
        bet_order = AppBetOrder(
            id=order_id,
            aid=aid,
            mb_id=mb_id,
            mb_username=mb_username,
            game_id=game_id,
            game_type=game_type,
            game_type_sub=game_type_sub,
            game_ratio=game_ratio,
            bet_type=bet_type,
            bet_type_sub=bet_type_sub,
            bet_group=bet_group,
            stake=Decimal(str(stake)) if stake is not None else None,
            stake_actual=Decimal(str(stake_actual)) if stake_actual is not None else None,
            netwin=Decimal(str(netwin)),
            netwin_actual=Decimal(str(netwin_actual)),
            fee_pt=Decimal(str(fee_pt)),
            fee_actual=Decimal(str(fee_actual)),
            odds=Decimal(str(odds)) if odds is not None else None,
            game_status=game_status,
            bet_status=bet_status,
            in_promotion=in_promotion,
            pro_id=pro_id,
            activity_record_id=activity_record_id,
            currency=currency,
            is_credit=is_credit,
            pay_wallet=pay_wallet,
            create_by_id=create_by_id,
            **kwargs
        )

        return bet_order

    @classmethod
    def create_from_order(cls, order_instance: Order, match: Match, **kwargs):
        """
        从Order模型实例复制数据创建AppBetOrder实例
        
        Args:
            order_instance: Order模型实例
            **kwargs: 额外的参数，用于覆盖或添加字段值
            
        Returns:
            AppBetOrder: 新创建的订单实例
        """
        bet_type_value = getattr(order_instance, 'BET_TYPE', None)
        print(order_instance)

        # 从Order模型映射到AppBetOrder模型的字段
        field_mapping = {
            'aid': order_instance.AGENT_CODE,
            'mb_id': order_instance.USER_ID,
            'mb_username': order_instance.USER_NAME,
            'game_id': order_instance.MATCH_ID,
            'game_type': 'Sports',  # 默认为Sports
            'game_type_sub': 'Football',  # 默认为Football
            'game_ratio': 0.00,
            'bet_type': 'Single' if order_instance.IS_MIX == '0' else 'Mixparlay',
            'bet_type_info':order_instance.BET_TYPE_INFO if order_instance.IS_MIX == '0' else order_instance.order_type_desc,
            'remarks': order_instance.ORDER_DESC,
            'bet_type_sub': order_instance.ORDER_TYPE,  # 使用安全的bet_type_value
            'bet_type_sub2': bet_type_value,  # 使用安全的bet_type_value
            'league': order_instance.LEAGUE,
            'bet_group': order_instance.ORDER_ID,
            'stake': Decimal(str(order_instance.BET_MONEY)) if order_instance.BET_MONEY else None,
            'stake_actual': Decimal(str(order_instance.BET_MONEY)) if order_instance.BET_MONEY else None,
            'odds': Decimal(str(order_instance.BET_ODDS)) if order_instance.BET_ODDS else None,
            'game_status': GameStatus.Pending,  # 默认为Pending
            'bet_status': BetStatus.Pending,  # 默认为Pending
            'netwin': Decimal(str(order_instance.BONUS)) if order_instance.BONUS and order_instance.IS_WIN == '1' else Decimal('0.00'),
            'netwin_actual': Decimal(str(order_instance.BONUS)) if order_instance.BONUS and order_instance.IS_WIN == '1' else Decimal('0.00'),
            'currency': 'CNY',  # 默认货币
            'pay_wallet': order_instance.pay_wallet,  # 默认主钱包
            'lose_team': order_instance.LOSE_TEAM,
            'draw_bunko': order_instance.DRAW_BUNKO,
            'draw_odds': order_instance.DRAW_ODDS,
            'lose_ball_num': order_instance.LOSE_BALL_NUM,
            'home': match.HOST_TEAM,
            'away': match.GUEST_TEAM
        }
        if field_mapping['bet_type'] == 'Mixparlay':
            # 取消比赛相关
            field_mapping['game_id'] = None
            field_mapping['remarks'] = None
            field_mapping['bet_type_sub'] = None
            field_mapping['home'] = None
            field_mapping['away'] = None

        # 使用kwargs覆盖默认映射
        field_mapping.update(kwargs)

        # 创建订单实例
        bet_order = cls.create_new(**field_mapping)

        return bet_order


db.create_all()
