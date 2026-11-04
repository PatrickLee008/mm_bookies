# -*- coding: utf-8 -*-
"""
银行代码映射层（mm_bookies 专用）

背景（2026-10-29 按库内实际数据核对）：
    库内 m_app_bank_code 的取值是「混合语义」的，不能想当然：
      'KBZ Pay'     = KBZ Pay 钱包
      'Wave Money'  = Wave Money 钱包
      'KBZ'         = Kanbawza Bank（银行，不是钱包）
      'AYA'         = Ayeyarwaddy Bank（银行，不是 AYA Pay；前端 label 写成 "AYA PAY" 是错的）
      'YOMA'        = YOMA Banking（银行）
      'KBZBANK' / 'AYA BANK' / 'AYAPAY' = 本次新增，用于区分银行与钱包
    支付中心标准码：KBZ（钱包）/ WaveMoney（钱包）/ KBZBANK / YOMA / AYA（银行）/ AYAPAY（钱包）。

    ⚠️ 关键歧义：库内 'KBZ' 是银行，支付中心 'KBZ' 是钱包，不能直接透传。
       实际业务数据（m_app_member_bankcard / m_app_agent_bankcard）只有
       'KBZ Pay' 与 'Wave Money' 两种钱包，因此：
         · 'KBZ Pay' → 支付中心 'KBZ'（钱包）
         · 库内 'KBZ'（银行）→ 支付中心 'KBZBANK'
       为兼容老前端可能传 'KBZ'，normalize('KBZ') 仍按钱包处理（见下）。

约定：
    1) 库内标准值一律使用 BANK_* 常量；
    2) 出入支付中心的 bankCode / paymentType 必须经过本模块；
    3) Java 侧 PayBankCode 必须与本文件逐字一致。
"""
from app_server.logger import get_logger

logger = get_logger()

# ---- 库内标准值（写库用）----
BANK_WALLET_KBZ = 'KBZ Pay'
BANK_WALLET_WAVE = 'Wave Money'
BANK_BANK_KBZ = 'KBZBANK'
BANK_BANK_YOMA = 'YOMA'
BANK_BANK_AYA = 'AYA'          # Ayeyarwaddy Bank（库内既有值，不改）
BANK_WALLET_AYA = 'AYAPAY'     # AYA Pay 钱包（新增，与银行区分）

# 钱包类（所有通道都支持）
WALLET_BANKS = (BANK_WALLET_KBZ, BANK_WALLET_WAVE)
# MCPay 支持钱包 + 银行
MCPAY_BANKS = WALLET_BANKS + (BANK_BANK_KBZ, BANK_BANK_YOMA, BANK_BANK_AYA, BANK_WALLET_AYA)

# 库内值 → 支付中心值
_TO_PAY_CENTER = {
    'KBZ Pay': 'KBZ',            # 钱包
    'KBZPAY': 'KBZ',
    'KBZ': 'KBZBANK',            # 库内 'KBZ' 是 Kanbawza Bank（银行）
    'KBZBANK': 'KBZBANK',
    'Wave Money': 'WaveMoney',   # 钱包
    'WaveMoney': 'WaveMoney',
    'WAVEPAY': 'WaveMoney',
    'YOMA': 'YOMA',              # 银行
    'AYA': 'AYA',                # 银行（Ayeyarwaddy）
    'AYA BANK': 'AYA',
    'AYAPAY': 'AYAPAY',          # 钱包
}

# 支付中心值 → 库内标准值
_FROM_PAY_CENTER = {
    'KBZ': BANK_WALLET_KBZ,
    'KBZPAY': BANK_WALLET_KBZ,
    'KBZBANK': BANK_BANK_KBZ,
    'WaveMoney': BANK_WALLET_WAVE,
    'WAVEPAY': BANK_WALLET_WAVE,
    'YOMA': BANK_BANK_YOMA,
    'AYA': BANK_BANK_AYA,
    'AYAPAY': BANK_WALLET_AYA,
}

# 任意写法 → 库内标准值（前端传值 / 历史数据兼容）
# 注意 'KBZ' 按钱包归一：业务数据里用户的 KBZ 卡都是 'KBZ Pay'
_NORMALIZE = {
    'KBZ': BANK_WALLET_KBZ,
    'KBZ Pay': BANK_WALLET_KBZ,
    'KBZPAY': BANK_WALLET_KBZ,
    'WaveMoney': BANK_WALLET_WAVE,
    'Wave Money': BANK_WALLET_WAVE,
    'WAVEPAY': BANK_WALLET_WAVE,
    'KBZBANK': BANK_BANK_KBZ,
    'YOMA': BANK_BANK_YOMA,
    'AYA': BANK_BANK_AYA,
    'AYA BANK': BANK_BANK_AYA,
    'AYABANK': BANK_BANK_AYA,
    'AYAPAY': BANK_WALLET_AYA,
}


def to_pay_center(code):
    """库内银行代码 → 支付中心 bankCode / paymentType。未知值原样返回并记日志。"""
    if not code:
        return code
    mapped = _TO_PAY_CENTER.get(code)
    if mapped is None:
        logger.warning('BankCodeMap: 未知库内银行代码 %r，原样传给支付中心', code)
        return code
    return mapped


def from_pay_center(code):
    """支付中心 bankCode → 库内标准值。未知值原样返回。"""
    if not code:
        return code
    mapped = _FROM_PAY_CENTER.get(code)
    if mapped is None:
        logger.warning('BankCodeMap: 未知支付中心银行代码 %r，原样落库', code)
        return code
    return mapped


def normalize(code):
    """把任意写法归一成库内标准值（前端传值 / 历史数据兼容用）。"""
    if not code:
        return code
    normalized = _NORMALIZE.get(code)
    if normalized is None:
        logger.warning('BankCodeMap: 无法识别的银行代码 %r', code)
        return code
    return normalized


def is_wallet(code):
    return normalize(code) in WALLET_BANKS


def supported_by(channel, code):
    """该通道是否支持这个银行（库内值或任意写法都可传入）。"""
    bank = normalize(code)
    if channel == 'MCPay':
        return bank in MCPAY_BANKS
    return bank in WALLET_BANKS
