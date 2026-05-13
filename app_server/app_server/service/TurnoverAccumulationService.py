from decimal import Decimal
from app_server import db
from app_server.logger import get_logger
from app_server.model.AppSettingFinanceModel import AppSettingFinanceModel

logger = get_logger()


class TurnoverAccumulationService:
    """累积流水管理服务

    新公式实现：
    - Required Turnover(n) = Required Turnover(n-1) + Deposit(n) × Turnover Rate
    - Current Turnover(n) = Current Turnover(n-1) + Bet(n)
    - 重置条件：Previous Cleared Balance > 0 OR Previous Remaining Balance = 0
    """

    @staticmethod
    def calculate_cleared_balance(user):
        """
        计算已清算余额（Cleared Balance）

        公式：
        IF Current Turnover >= Required Turnover
        THEN Cleared Balance = Remaining Balance (money)
        ELSE Cleared Balance = Promotion Wallet Transfer (money_promotion_withdrawable)

        Args:
            user: AppMember 用户对象

        Returns:
            float: 已清算余额
        """
        current_turnover = float(user.current_turnover_accumulated) if user.current_turnover_accumulated else 0.0
        required_turnover = float(user.required_turnover_accumulated) if user.required_turnover_accumulated else 0.0
        remaining_balance = float(user.money) if user.money else 0.0
        promotion_withdrawable = float(user.money_promotion_withdrawable) if user.money_promotion_withdrawable else 0.0

        if required_turnover == 0 or current_turnover >= required_turnover:
            return remaining_balance
        else:
            return promotion_withdrawable

    @staticmethod
    def check_reset_condition(user):
        """
        检查是否需要重置流水

        重置条件：Previous Cleared Balance > 0 OR Previous Remaining Balance = 0

        注意："Previous" 是指本次操作前的当前状态（不是上次操作后的状态）

        Args:
            user: AppMember 用户对象

        Returns:
            tuple: (should_reset, reason)
        """
        # 获取当前状态（操作前）
        current_balance = float(user.money) if user.money else 0.0
        current_turnover = float(user.current_turnover_accumulated) if user.current_turnover_accumulated else 0.0
        required_turnover = float(user.required_turnover_accumulated) if user.required_turnover_accumulated else 0.0

        # 计算当前的 Cleared Balance（操作前）
        if required_turnover == 0 or current_turnover >= required_turnover:
            cleared_balance = current_balance
        else:
            cleared_balance = 0.0

        # 判断重置条件
        if cleared_balance > 0:
            return True, f"Cleared Balance > 0 (cleared={cleared_balance})"
        elif current_balance == 0:
            return True, "Remaining Balance = 0"
        else:
            return False, None

    @staticmethod
    def on_deposit(user, deposit_amount):
        """
        充值时更新累积流水

        公式：
        - 正常：Required Turnover(n) = Required Turnover(n-1) + Deposit(n) × Turnover Rate
        - 重置：Required Turnover(n) = Deposit(n) × Turnover Rate

        重置条件：Previous Cleared Balance > 0 OR Previous Remaining Balance = 0

        Args:
            user: AppMember 用户对象
            deposit_amount: 充值金额
        """
        # 1. 检查是否需要重置
        should_reset, reset_reason = TurnoverAccumulationService.check_reset_condition(user)

        # 2. 获取周转率
        turnover_rate = TurnoverAccumulationService.get_turnover_rate(user)

        # 3. 更新 Required Turnover
        old_required = float(user.required_turnover_accumulated) if user.required_turnover_accumulated else 0.0
        old_current = float(user.current_turnover_accumulated) if user.current_turnover_accumulated else 0.0

        if should_reset:
            # 重置：Required = 本次充值 × 周转率，Current = 0
            user.required_turnover_accumulated = float(deposit_amount) * turnover_rate
            user.current_turnover_accumulated = 0

            logger.info(f"充值时重置流水 - 用户ID: {user.id}, "
                       f"原因: {reset_reason}, "
                       f"充值金额: {deposit_amount}, 周转率: {turnover_rate}, "
                       f"Required: {old_required} -> {user.required_turnover_accumulated}, "
                       f"Current: {old_current} -> 0")
        else:
            # 不重置：累加
            user.required_turnover_accumulated = old_required + (float(deposit_amount) * turnover_rate)

            logger.info(f"充值更新流水 - 用户ID: {user.id}, "
                       f"充值金额: {deposit_amount}, 周转率: {turnover_rate}, "
                       f"Required: {old_required} -> {user.required_turnover_accumulated}")

    @staticmethod
    def on_bet_settled(user, bet_amount):
        """
        订单结算成功后更新累积流水

        公式：
        - 正常：Current Turnover(n) = Current Turnover(n-1) + Bet(n)
        - 重置：Current Turnover(n) = Bet(n)

        重置条件：Previous Cleared Balance > 0 OR Previous Remaining Balance = 0

        注意：
        1. 只在订单结算成功后调用（Win/Lose/Draw/HalfWin/HalfLose）
        2. 仅主钱包（pay_wallet = 'Money'）计入流水

        Args:
            user: AppMember 用户对象
            bet_amount: 投注金额
        """
        # 1. 检查是否需要重置
        should_reset, reset_reason = TurnoverAccumulationService.check_reset_condition(user)

        # 2. 更新 Current Turnover
        old_current = float(user.current_turnover_accumulated) if user.current_turnover_accumulated else 0.0
        old_required = float(user.required_turnover_accumulated) if user.required_turnover_accumulated else 0.0

        if should_reset:
            # 重置：Current = 本次投注金额，Required = 0
            user.current_turnover_accumulated = float(bet_amount)
            user.required_turnover_accumulated = 0

            logger.info(f"投注结算时重置流水 - 用户ID: {user.id}, "
                       f"原因: {reset_reason}, "
                       f"投注金额: {bet_amount}, "
                       f"Current: {old_current} -> {user.current_turnover_accumulated}, "
                       f"Required: {old_required} -> 0")
        else:
            # 不重置：累加
            user.current_turnover_accumulated = old_current + float(bet_amount)

            logger.info(f"投注结算更新流水 - 用户ID: {user.id}, "
                       f"投注金额: {bet_amount}, "
                       f"Current: {old_current} -> {user.current_turnover_accumulated}")

    @staticmethod
    def calculate_withdrawable_amount(user):
        """
        计算可提现金额

        公式：
        IF Current Turnover >= Required Turnover
        THEN Cleared Balance = Remaining Balance (money)
        ELSE Cleared Balance = Promotion Wallet Transfer (money_promotion_withdrawable)

        Withdrawable Amount = Cleared Balance

        说明：
        - 当流水满足时，可以提现全部余额
        - 当流水不满足时，只能提现促销钱包转入的金额（这部分已经清算过）

        Args:
            user: AppMember 用户对象

        Returns:
            float: 可提现金额
        """
        current_turnover = float(user.current_turnover_accumulated) if user.current_turnover_accumulated else 0.0
        required_turnover = float(user.required_turnover_accumulated) if user.required_turnover_accumulated else 0.0
        remaining_balance = float(user.money) if user.money else 0.0
        promotion_withdrawable = float(user.money_promotion_withdrawable) if user.money_promotion_withdrawable else 0.0

        # 计算 Cleared Balance
        if required_turnover == 0 or current_turnover >= required_turnover:
            cleared_balance = remaining_balance
        else:
            cleared_balance = promotion_withdrawable

        # Withdrawable Amount = Cleared Balance
        return cleared_balance

    @staticmethod
    def on_withdraw_approved(user, withdraw_amount, promotion_wallet_transfer=0):
        """
        提现审核通过后的流水重置逻辑

        重置条件：Withdraw Amount > Promotion Wallet Transfer OR Previous Remaining Balance = 0

        当满足重置条件时：
        - Required Turnover = 0
        - Current Turnover = 0

        Args:
            user: AppMember 用户对象
            withdraw_amount: 提现金额
            promotion_wallet_transfer: 本次提现涉及的促销钱包转入金额（从 money_promotion_withdrawable 扣除的金额）
        """
        # 获取提现前的余额（提现后的余额 + 提现金额）
        current_balance = float(user.money) if user.money else 0.0
        previous_balance = current_balance + float(withdraw_amount)

        old_required = float(user.required_turnover_accumulated) if user.required_turnover_accumulated else 0.0
        old_current = float(user.current_turnover_accumulated) if user.current_turnover_accumulated else 0.0

        # 判断是否需要重置
        should_reset = False
        reset_reason = None

        if float(withdraw_amount) > float(promotion_wallet_transfer):
            should_reset = True
            reset_reason = f"Withdraw Amount ({withdraw_amount}) > Promotion Wallet Transfer ({promotion_wallet_transfer})"
        elif previous_balance == 0:
            should_reset = True
            reset_reason = "Previous Remaining Balance = 0"

        if should_reset:
            # 重置流水
            user.required_turnover_accumulated = 0
            user.current_turnover_accumulated = 0

            logger.info(f"提现审核通过后重置流水 - 用户ID: {user.id}, "
                       f"原因: {reset_reason}, "
                       f"提现金额: {withdraw_amount}, 促销转入: {promotion_wallet_transfer}, "
                       f"提现前余额: {previous_balance}, 提现后余额: {current_balance}, "
                       f"Required: {old_required} -> 0, Current: {old_current} -> 0")
        else:
            logger.info(f"提现审核通过无需重置 - 用户ID: {user.id}, "
                       f"提现金额: {withdraw_amount}, 促销转入: {promotion_wallet_transfer}, "
                       f"提现前余额: {previous_balance}, 提现后余额: {current_balance}, "
                       f"Required: {old_required}, Current: {old_current}")

    @staticmethod
    def get_turnover_rate(user):
        """
        获取周转率配置

        优先使用用户所属代理的配置，如果没有则使用默认配置

        Args:
            user: AppMember 用户对象

        Returns:
            float: 周转率倍数
        """
        finance_config = None
        if user.aid:
            finance_config = AppSettingFinanceModel.get_by_aid(
                aid=user.aid,
                tenant_id=user.tenant_id if hasattr(user, 'tenant_id') else None
            )

        if not finance_config:
            finance_config = AppSettingFinanceModel.get_agent_config(
                aid='0',
                tenant_id=user.tenant_id if hasattr(user, 'tenant_id') else None
            )

        return float(finance_config.withdraw_turnover_rate) if finance_config and finance_config.withdraw_turnover_rate else 1.0
