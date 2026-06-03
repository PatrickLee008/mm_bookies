# -*- coding: utf-8 -*-
"""
独立图片交易检测工具 - test_detect_transaction.py
===================================================
从 ChargeController 的 order_image 逻辑重构而来的独立文件，
包含所有 OCR 图片解析和处理方法，可独立完成从图片到交易信息的完整解析。

实现方式: 沿用 ChargeController 原有的 google-cloud-vision/translate 方案，
          增加超时保护防止 gRPC 在代理下挂死。

支持的支付方式:
  - Wave Money (缅甸语/英语, 多种截图格式)
  - KBZPay (缅甸语/英语, 多种截图格式)

提取字段:
  - transaction_id: 交易ID
  - amount: 金额 (Ks)
  - order_time: 交易时间 (精确到秒, 如 2025-06-05 16:41:37)
  - transfer_to: 转账对象 (如 Han Min Aung (******9133) / Hae Satin 9689023844 active)
  - notes: 备注信息 (如 Salary / payment)

使用方式:
  python test_detect_transaction.py <image_path>

依赖:
  pip install google-cloud-vision google-cloud-translate Pillow
"""

import re
import os
import sys
import time
import logging
import threading

from datetime import datetime
from PIL import Image, ImageStat

from google.cloud import vision
from google.cloud import translate_v2 as translate
from google.oauth2 import service_account
from google.api_core.exceptions import ServiceUnavailable

# ============================================================
# 日志配置
# ============================================================
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] [%(filename)s:%(lineno)d] - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


# ============================================================
# Google API 凭证与客户端（完全沿用 ChargeController 的方式）
# ============================================================
_credentials = None
_vision_client = None
_translate_client = None
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def _get_credentials():
    """获取 Google 服务账号凭证 — 与 app_server/__init__.py 完全一致"""
    global _credentials
    if _credentials is not None:
        return _credentials
    cred_paths = [
        os.path.join(BASE_DIR, 'app_server', 'static', 'liquid-galaxy-466810-d0-9360f89e5cc1.json'),
        os.path.join(BASE_DIR, 'static', 'liquid-galaxy-466810-d0-9360f89e5cc1.json'),
    ]
    cred_path = None
    for p in cred_paths:
        if os.path.exists(p):
            cred_path = p
            break
    if cred_path is None:
        raise FileNotFoundError(
            f"Google credentials file not found. Tried:\n" +
            "\n".join(f"  - {p}" for p in cred_paths)
        )
    logger.info(f"加载 Google 凭证: {cred_path}")
    _credentials = service_account.Credentials.from_service_account_file(cred_path)
    return _credentials


def _get_vision_client(force_new=False):
    """懒加载 Vision API 客户端 — 与 ChargeController 完全一致"""
    global _vision_client
    if _vision_client is None or force_new:
        _vision_client = vision.ImageAnnotatorClient(credentials=_get_credentials())
    return _vision_client


def _get_translate_client():
    """懒加载 Translate API 客户端 — 与 service/__init__.py 完全一致"""
    global _translate_client
    if _translate_client is None:
        _translate_client = translate.Client(credentials=_get_credentials())
    return _translate_client


# ============================================================
# 超时包装: 解决 gRPC 在代理/VPN 下无限挂起的问题
# ============================================================

def _call_with_timeout(func, timeout_sec, error_msg="操作超时"):
    """
    在独立线程中执行函数，超时则抛出 TimeoutError。
    Windows 上用 threading；Unix 上优先用 signal.alarm（可中断 C 级别的 gRPC 阻塞）。
    """
    if os.name != 'nt':
        # Unix: signal.alarm 可以中断 gRPC 的 C 层阻塞
        import signal

        result = [None]
        error = [None]

        def _handler(signum, frame):
            raise TimeoutError(f'{error_msg} ({timeout_sec}s)')

        old_handler = signal.signal(signal.SIGALRM, _handler)
        signal.alarm(timeout_sec)
        try:
            return func()
        finally:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)
    else:
        # Windows: 没有 signal.alarm，用 threading
        result = [None]
        error = [None]
        done = threading.Event()

        def _call():
            try:
                result[0] = func()
            except Exception as e:
                error[0] = e
            finally:
                done.set()

        t = threading.Thread(target=_call, daemon=True)
        t.start()
        if not done.wait(timeout=timeout_sec):
            raise TimeoutError(f'{error_msg} ({timeout_sec}s) - 请检查网络/代理')
        if error[0]:
            raise error[0]
        return result[0]


# ============================================================
# Vision OCR 调用（沿用 ChargeController.detect_transaction）
# ============================================================

def _call_vision_ocr(image_bytes):
    """调用 Vision API document_text_detection，失败时重建客户端重试一次"""
    client = _get_vision_client()
    image = vision.Image(content=image_bytes)

    try:
        return client.document_text_detection(
            image=image, image_context={"language_hints": ["my", "en"]}
        )
    except ServiceUnavailable:
        logger.warning("Vision API 服务不可用，重建客户端重试...")
        client = _get_vision_client(force_new=True)
        return client.document_text_detection(
            image=image, image_context={"language_hints": ["my", "en"]}
        )


# ============================================================
# 工具函数
# ============================================================

def parse_datetime_flexible(datetime_str, format_patterns):
    """
    尝试使用多个格式解析日期时间字符串
    """
    for pattern in format_patterns:
        try:
            return datetime.strptime(datetime_str, pattern)
        except ValueError:
            continue
    return None


def detect_color(img_path):
    """
    检测图像的平均颜色，可用于判断截图类型或验证图片有效性
    """
    image = Image.open(img_path).convert('RGB')
    stat = ImageStat.Stat(image)
    return stat.mean[0], stat.mean[1], stat.mean[2]


def get_wave_order_time(_str):
    """
    从Wave支付文本中提取订单日期（仅日期部分）
    匹配格式: "Jan 15, 2024 10:30:45 AM"
    """
    order_time = re.search(r"(\w+)\s(\d+)\s?,\s?(\d+) (\d{2}:\d{2}:\d{2}) (AM|PM)", _str)
    if order_time:
        datetime_str = " ".join(order_time.groups())
        order_time = datetime.strptime(datetime_str, '%b %d %Y %H:%M:%S %p')
        return str(order_time.date())
    return None


def get_wave_order_time_myan(_str):
    """
    从Wave支付文本中提取完整订单时间（包含时分秒）
    """
    order_time = re.search(r"(\w+)\s(\d+)\s?,\s?(\d+) (\d{2}:\d{2}:\d{2}) (AM|PM)", _str)
    if order_time:
        datetime_str = " ".join(order_time.groups())
        order_time = datetime.strptime(datetime_str, '%b %d %Y %H:%M:%S %p')
        return str(order_time)
    return None


def get_ks_order_time(_str):
    """
    从KBZPay支付文本中提取订单时间
    匹配格式: "15/01/2024 10:30:45"
    """
    order_time = re.search(r"\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}", _str)
    if order_time:
        order_time = order_time[0]
        order_time = datetime.strptime(order_time, "%d/%m/%Y %H:%M:%S")
        return str(order_time)
    return None


def get_transfer_to(_str):
    """
    从支付文本中提取转账对象 (Transfer To / To)
    支持 KBZPay: "Transfer To Han Min Aung (******9133)"
    支持 Wave:    "To Hae Satin 9689023844 active"
    支持缅甸语标签: "လွှဲပြောင်းရန်"
    """
    # KBZPay 英文标签: "Transfer To\n..."
    transfer_to = re.search(r"Transfer To\s*\n\s*(.+)", _str, re.IGNORECASE)
    if transfer_to:
        return transfer_to[1].strip()
    # KBZPay 缅甸语标签: "လွှဲပြောင်းရန်\n..."
    transfer_to = re.search(r"လွှဲပြောင်းရန်\s*\n\s*(.+)", _str)
    if transfer_to:
        return transfer_to[1].strip()
    # Wave Money: "To\nName AccountNumber status"
    transfer_to = re.search(r"^To\s*\n\s*(.+)", _str, re.MULTILINE | re.IGNORECASE)
    if transfer_to:
        return transfer_to[1].strip()
    return None


def get_notes(_str):
    """
    从支付文本中提取备注信息 (Notes / Note)
    支持 KBZPay: "Notes Salary"
    支持 Wave:    "Note payment"
    支持缅甸语标签: "မှတ်ချက်"
    """
    # KBZPay 英文标签: "Notes\n..."
    notes = re.search(r"Notes\s*\n\s*(.+)", _str, re.IGNORECASE)
    if notes:
        note_text = notes[1].strip()
        if note_text and not re.match(r'^[\d\s,/.-]+$', note_text):
            return note_text
    # Wave 英文标签: "Note\n..." (单数)
    notes = re.search(r"Note\s*\n\s*(.+)", _str, re.IGNORECASE)
    if notes:
        note_text = notes[1].strip()
        if note_text and not re.match(r'^[\d\s,/.-]+$', note_text):
            return note_text
    # 缅甸语标签: "မှတ်ချက်\n..."
    notes = re.search(r"မှတ်ချက်\s*\n\s*(.+)", _str)
    if notes:
        note_text = notes[1].strip()
        if note_text and not re.match(r'^[\d\s,/.-]+$', note_text):
            return note_text
    return None


# ============================================================
# OCR 文本重组（来自 ChargeController.regen_words）
# ============================================================

def regen_words(text_annotations):
    """
    将 Vision API 返回的 text_annotations 按行重组为可读文本
    """
    items = []
    lines = {}

    for text in text_annotations[1:]:
        top_x_axis = text.bounding_poly.vertices[0].x
        top_y_axis = text.bounding_poly.vertices[0].y
        bottom_y_axis = text.bounding_poly.vertices[3].y

        if top_y_axis not in lines:
            lines[top_y_axis] = [(top_y_axis, bottom_y_axis), []]

        for s_top_y_axis, s_item in lines.items():
            if top_y_axis < s_item[0][1]:
                lines[s_top_y_axis][1].append((top_x_axis, text.description))
                break

    for _, item in lines.items():
        if item[1]:
            words = sorted(item[1], key=lambda t: t[0])
            items.append((' '.join([word for _, word in words])))

    logger.info(f"OCR识别结果: {items}")
    return items


# ============================================================
# 缅甸语交易信息识别 (detect_myan) — 来自 service/__init__.py
# ============================================================

def detect_myan(result_str):
    """
    识别缅甸语支付截图中的交易信息
    支持Wave Money和KBZPay两种支付方式，多种截图格式

    Returns:
        list: [{'transaction_id': 'xxx', 'amount': 'xxx', 'order_time': 'xxx',
                'transfer_to': 'xxx', 'notes': 'xxx'}]
    """
    all_valid_trades = []
    logger.debug("detect_myan: it's wave")

    # ==================== Wave Money 识别 ====================

    # 情况1: 新版Wave单张详情（需要翻译）
    if "အောင်မြင်ပါသည်" in result_str and "နေ့ရက်နှင့်အချိန်" in result_str:
        transaction_id = re.search(r"လုပ်ဆောင်ချက်အိုင်ဒီ.*?(\d{8,})", result_str, re.DOTALL)
        amount_re = re.search(r"အောင်မြင်ပါသည်\n(.*?) ကျပ်", result_str)
        logger.debug("detect_myan: new wave detail")

        if transaction_id and amount_re:
            transaction_id = transaction_id[1]
            amount = amount_re[1].replace(",", "").replace(" ", "")

            # 使用Google翻译API将缅甸语翻译为英文（复用单例客户端）
            translate_client = _get_translate_client()
            translate_result = translate_client.translate(result_str, target_language="en", source_language="my")
            translate_str = translate_result["translatedText"].lower()
            logger.debug(f"detect_myan: got translate result: {translate_str}")

            # 从翻译后的文本提取时间
            order_time = re.search(r"(\d{1,2}) (\w+) (\d{4}) [•·] (\d+:\d+) (am|pm)", translate_str)
            if order_time:
                datetime_str = " ".join(order_time.groups())
                order_time = parse_datetime_flexible(datetime_str, ['%d %b %Y %H:%M %p', '%d %B %Y %H:%M %p'])

            detect_result = {'transaction_id': transaction_id, 'amount': amount,
                             'order_time': str(order_time) if order_time else None,
                             'transfer_to': get_transfer_to(result_str),
                             'notes': get_notes(result_str)}
            all_valid_trades.append(detect_result)

    # 情况2: Wave单张安卓版
    elif "ငွေလွှဲခြင်း" in result_str:
        transaction_id = re.search(r"လုပ်ငန်းစဉ်.*?(\d{8,})", result_str, re.DOTALL)
        amount_re = re.search(r"စုစုပေါင်းပမာဏ\n(\d+.*?) ကျပ်", result_str)
        if transaction_id and amount_re:
            transaction_id = transaction_id[1]
            amount = int(amount_re[1].replace(",", ""))

            order_time = re.search(r"(\w+)\s(\d+)\s?,\s?(\d+) (\d{2}:\d{2}:\d{2}) (AM|PM)", result_str)
            if order_time:
                datetime_str = " ".join(order_time.groups())
                order_time = datetime.strptime(datetime_str, '%b %d %Y %H:%M:%S %p')

            detect_result = {'transaction_id': transaction_id, 'amount': amount,
                             'order_time': str(order_time) if order_time else None,
                             'transfer_to': get_transfer_to(result_str),
                             'notes': get_notes(result_str)}
            all_valid_trades.append(detect_result)

    # 情况3: Wave单张iOS版
    elif "အောင်မြင်ပါတယ်" in result_str:
        transaction_id = re.search(r"လုပ်ငန်းစဉ်.*?(\d{8,})", result_str, re.DOTALL)
        amount_re = re.search(r"အောင်မြင်ပါတယ်\n(.*?) ကျပ်", result_str)
        if transaction_id and amount_re:
            transaction_id = transaction_id[1]
            amount = amount_re[1].replace(",", "").replace(" ", "")

            order_time = re.search(r"(\d{2} \w+ \d{4})", result_str)
            if order_time:
                order_time = datetime.strptime(order_time[1], '%d %b %Y')

            detect_result = {'transaction_id': transaction_id, 'amount': amount, 'order_time': str(order_time.date())}
            all_valid_trades.append(detect_result)

    # 情况4: Wave iOS列表点击详情
    elif "Send Money" in result_str and "အသေးစိတ်" in result_str:
        transaction_id = re.search(r".*\s(\d{8,})", result_str)
        amount_re = re.search(r"(.*?) ကျပ်", result_str)
        if transaction_id and amount_re:
            transaction_id = transaction_id[1]
            amount = amount_re[1].replace(",", "").replace(" ", "")

            order_time = re.search(r"(\d{1,2}) (\w+) (\d{4}) [•·] (\d{1,2}:\d{2}) (AM|PM)", result_str)
            if order_time:
                datetime_str = " ".join(order_time.groups())
                order_time = parse_datetime_flexible(datetime_str, ['%d %b %Y %H:%M %p', '%d %B %Y %H:%M %p'])

            detect_result = {'transaction_id': transaction_id, 'amount': amount,
                             'order_time': str(order_time) if order_time else None,
                             'transfer_to': get_transfer_to(result_str),
                             'notes': get_notes(result_str)}
            all_valid_trades.append(detect_result)

    # 情况5: Wave列表安卓版（可能包含多笔交易）
    elif "စာရင်း" in result_str:
        trans_ids = re.findall(r"လုပ်ငန်းစဉ်အမှတ် -\n?.*?(\d{8,})", result_str)
        amounts = re.findall(r"([+-].*?) ကျပ်", result_str)
        logger.debug(f"detect_myan wave list: trans_ids={trans_ids}, amounts={amounts}")

        for i in range(min(len(trans_ids), len(amounts))):
            if not amounts[i]:
                continue
            amount = amounts[i]
            if amount.startswith("+"):
                continue
            all_valid_trades.append({'transaction_id': trans_ids[i], 'amount': amounts[i]})

    # ==================== KBZPay 识别 ====================
    # 情况6: KBZPay新版详情页 - Payment Successful / E-Receipt格式
    elif "Payment Successful" in result_str or "လုပ်ဆောင်မှုအောင်မြင်ပါသည်" in result_str or (
            "E-Receipt" in result_str and "KBZ" in result_str):
        transaction_id = re.search(r"(\d{20})", result_str)
        amount_re = re.search(r"-(\d+(?:,?\d+)?(?:\.\d{2})?) ?\(?\s?Ks\)?", result_str)
        logger.debug(f"detect_myan KBZ format: transaction_id={transaction_id}, amount={amount_re}")
        if amount_re and transaction_id:
            transaction_id = transaction_id[1]
            amount = float(amount_re[1].replace(",", ""))
            amount = abs(amount)

            order_time = re.search(r"(\d{2}/\d{2}/\d{4}) (\d{2}:\d{2}:\d{2})", result_str)
            if order_time:
                datetime_str = f"{order_time[1]} {order_time[2]}"
                order_time = datetime.strptime(datetime_str, "%d/%m/%Y %H:%M:%S")
            detect_result = {'transaction_id': transaction_id, 'amount': amount,
                             'order_time': str(order_time) if order_time else None,
                             'transfer_to': get_transfer_to(result_str),
                             'notes': get_notes(result_str)}
            all_valid_trades.append(detect_result)

    # 情况7: 新版KBZPay安卓 (旧格式)
    elif "Thank you for using KBZPay" in result_str:
        transaction_id = re.search(r"(\d{20})", result_str)
        amount_re = re.search(r"-(\d+,?\d+)\.00\s?Ks", result_str)
        logger.debug(f"detect_myan KBZ old format: transaction_id={transaction_id}, amount={amount_re}")

        if amount_re and transaction_id:
            transaction_id = transaction_id[1]
            amount = float(amount_re[1].replace(",", ""))
            amount = abs(amount)

            order_time = re.search(r"\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}", result_str)
            if order_time:
                order_time = order_time[0]
                order_time = datetime.strptime(order_time, "%d/%m/%Y %H:%M:%S")

            detect_result = {'transaction_id': transaction_id, 'amount': amount,
                             'order_time': str(order_time) if order_time else None,
                             'transfer_to': get_transfer_to(result_str),
                             'notes': get_notes(result_str)}
            all_valid_trades.append(detect_result)

    logger.debug(f"detect_myan result: {all_valid_trades}")

    # 兜底逻辑
    if not len(all_valid_trades):
        transaction_id = re.search(r".*\s(\d{8,})", result_str)
        amount_re = re.search(r"-(\d+,?\d+).00 \wyat", result_str)
        if transaction_id and amount_re:
            transaction_id = transaction_id[1]
            amount = int(amount_re[1].replace(",", ""))
            all_valid_trades.append({
                'transaction_id': transaction_id,
                'amount': amount,
                'order_time': get_wave_order_time(result_str)
            })

    return all_valid_trades


# ============================================================
# 英文交易信息识别 (detect_en_new) — 来自 service/__init__.py
# ============================================================

def detect_en_new(result_str):
    """
    识别英文支付截图中的交易信息
    支持Wave Money和KBZPay两种支付方式，多种截图格式

    Returns:
        list: [{'transaction_id': 'xxx', 'amount': 'xxx', 'order_time': 'xxx',
                'transfer_to': 'xxx', 'notes': 'xxx'}]
    """
    all_valid_trades = []

    # ==================== Wave Money 识别 ====================

    # 情况1: 新版Wave单张详情
    if "Successful" in result_str and "Date & Time" in result_str:
        transaction_id = re.search(r"Transaction.*?(\d{8,})", result_str, re.DOTALL)
        amount_re = re.search(r"Successful\n(\d+.*?) Ks", result_str)
        logger.debug("detect_en_new: new wave detail")

        if transaction_id and amount_re:
            transaction_id = transaction_id[1]
            amount = amount_re[1].replace(",", "").replace(" ", "")

            order_time = re.search(r"(\d{1,2}) (\w+) (\d{4})\s?[•·]?\s?(\d+:\d+) (AM|PM)", result_str)
            if order_time:
                datetime_str = " ".join(order_time.groups())
                order_time = parse_datetime_flexible(datetime_str, ['%d %b %Y %H:%M %p', '%d %B %Y %H:%M %p'])

            detect_result = {'transaction_id': transaction_id, 'amount': amount,
                             'order_time': str(order_time) if order_time else None,
                             'transfer_to': get_transfer_to(result_str),
                             'notes': get_notes(result_str)}
            all_valid_trades.append(detect_result)

    # 情况2: Wave单张安卓版
    if re.search(r"Successful(.*?) Kyat", result_str, re.DOTALL):
        transaction_id = re.search(r"Transaction.*?(\d{8,})", result_str, re.DOTALL)
        amount_re = re.search(r"Successful\n?(\d+.*?) Kyat", result_str)
        if transaction_id and amount_re:
            transaction_id = transaction_id[1]
            amount = int(amount_re[1].replace(",", ""))

            order_time = re.search(r"(\d{2} \w+ \d{4})", result_str)
            if order_time:
                order_time = parse_datetime_flexible(order_time[1], ['%d %b %Y', '%d %B %Y'])

            detect_result = {'transaction_id': transaction_id, 'amount': amount, 'order_time': str(order_time.date())}
            all_valid_trades.append(detect_result)

    # 情况3: Wave列表安卓版
    elif "History" in result_str:
        trans_ids = re.findall(r"Transaction ID -?\n?.*?(\d{8,})", result_str)
        amounts = re.findall(r"([+-].*?) Kyat", result_str)
        logger.debug(f"detect_en_new History: trans_ids={trans_ids}, amounts={amounts}")

        for i in range(min(len(trans_ids), len(amounts))):
            if not amounts[i]:
                continue
            amount = amounts[i]
            if amount.startswith("+"):
                continue
            amount = int(amount.replace(",", "").replace("-", ""))
            all_valid_trades.append({'transaction_id': trans_ids[i].strip(), 'amount': amount})

    # 情况4: Wave iOS详情页
    elif "Send Money" in result_str and "Details" in result_str:
        transaction_id = re.search(r".*\s(\d{8,})", result_str)
        amount_re = re.search(r"(-?\d+,?\d+) Ks", result_str)
        if transaction_id and amount_re:
            transaction_id = transaction_id[1]
            amount = int(amount_re[1].replace(",", "").replace(" ", ""))

            order_time = re.search(r"(\d{1,2}) (\w+) (\d{4})\s?[•·]?\s?(\d{1,2}:\d{2}) (AM|PM)", result_str)
            if order_time:
                datetime_str = " ".join(order_time.groups())
                order_time = parse_datetime_flexible(datetime_str, ['%d %b %Y %H:%M %p', '%d %B %Y %H:%M %p'])

            detect_result = {'transaction_id': transaction_id, 'amount': amount,
                             'order_time': str(order_time) if order_time else None,
                             'transfer_to': get_transfer_to(result_str),
                             'notes': get_notes(result_str)}
            all_valid_trades.append(detect_result)

    # 情况5: Wave单张iOS版 (另一种格式)
    elif "Send Money" in result_str:
        transaction_id = re.search(r"Transaction.*?(\d{8,})", result_str, re.DOTALL)
        amount_re = re.search(r"(-?\d+,?\d+) Kyat", result_str)
        if transaction_id and amount_re:
            transaction_id = transaction_id[1]
            amount = amount_re[1].replace(",", "").replace(" ", "")

            order_time = re.search(r"(\w+)\s(\d{2})\s?,\s?(\d{4}) (\d{2}:\d{2}:\d{2}) (AM|PM)", result_str)
            if order_time:
                datetime_str = " ".join(order_time.groups())
                order_time = parse_datetime_flexible(datetime_str, ['%b %d %Y %H:%M:%S %p', '%B %d %Y %H:%M:%S %p'])

            detect_result = {'transaction_id': transaction_id, 'amount': amount,
                             'order_time': str(order_time) if order_time else None,
                             'transfer_to': get_transfer_to(result_str),
                             'notes': get_notes(result_str)}
            all_valid_trades.append(detect_result)

    # ==================== KBZPay 识别 ====================

    # 情况6: KBZPay新版详情页 - Payment Successful / E-Receipt格式
    elif "Payment Successful" in result_str or ("E-Receipt" in result_str and "KBZ" in result_str):
        transaction_id = re.search(r"(\d{20})", result_str)
        amount_re = re.search(r"-(\d+(?:,?\d+)?(?:\.\d{2})?) ?\(?\s?Ks\)?", result_str)

        logger.debug(f"detect_en_new KBZ Payment Successful: transaction_id={transaction_id}, amount={amount_re}")

        if amount_re and transaction_id:
            transaction_id = transaction_id[1]
            amount = float(amount_re[1].replace(",", ""))
            amount = abs(amount)

            order_time = re.search(r"(\d{2}/\d{2}/\d{4}) (\d{2}:\d{2}:\d{2})", result_str)
            if order_time:
                datetime_str = f"{order_time[1]} {order_time[2]}"
                order_time = datetime.strptime(datetime_str, "%d/%m/%Y %H:%M:%S")

            detect_result = {'transaction_id': transaction_id, 'amount': amount,
                             'order_time': str(order_time) if order_time else None,
                             'transfer_to': get_transfer_to(result_str),
                             'notes': get_notes(result_str)}
            all_valid_trades.append(detect_result)

    # 情况7: 新版KBZPay安卓 (旧格式)
    elif "Thank you for using KBZPay" in result_str:
        transaction_id = re.search(r"(\d{20})", result_str)
        amount_re = re.search(r"-(\d+,?\d+)\.00\s?Ks", result_str)
        logger.debug(f"detect_en_new KBZ old format: transaction_id={transaction_id}, amount={amount_re}")

        if amount_re and transaction_id:
            transaction_id = transaction_id[1]
            amount = float(amount_re[1].replace(",", ""))
            amount = abs(amount)

            order_time = re.search(r"\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}", result_str)
            if order_time:
                order_time = order_time[0]
                order_time = datetime.strptime(order_time, "%d/%m/%Y %H:%M:%S")

            detect_result = {'transaction_id': transaction_id, 'amount': amount,
                             'order_time': str(order_time) if order_time else None,
                             'transfer_to': get_transfer_to(result_str),
                             'notes': get_notes(result_str)}
            all_valid_trades.append(detect_result)

    logger.debug(f"detect_en_new result: {all_valid_trades}")

    # 兜底逻辑
    if not len(all_valid_trades):
        transaction_id = re.search(r".*\s(\d{8,})", result_str)
        amount_re = re.search(r"-(\d+,?\d+).00 \wyat", result_str)
        if transaction_id and amount_re:
            transaction_id = transaction_id[1]
            amount = int(amount_re[1].replace(",", ""))
            all_valid_trades.append({
                'transaction_id': transaction_id,
                'amount': amount,
                'order_time': get_wave_order_time(result_str)
            })

    return all_valid_trades


# ============================================================
# 核心识别函数: detect_transaction（沿用 ChargeController 逻辑 + 超时保护）
# ============================================================

def detect_transaction(image_bytes):
    """
    接收图片字节内容，调用 Vision API OCR，自动检测语言并解析交易信息。
    完全沿用 ChargeController 的逻辑，仅增加了超时保护。

    Args:
        image_bytes: 图片的字节内容（bytes）

    Returns:
        list: [{'transaction_id': 'xxx', 'amount': 'xxx', 'order_time': 'xxx',
                'transfer_to': 'xxx', 'notes': 'xxx'}]
    """
    t0 = time.time()

    # 准备 Vision 客户端
    client = _get_vision_client()
    image = vision.Image(content=image_bytes)
    t1 = time.time()
    logger.info(f"[detect_transaction] Vision 客户端就绪: {t1 - t0:.3f}s")
    logger.info(f"[detect_transaction] 正在调用 Google Vision OCR (超时保护: 60s)...")

    # 调用 Vision API（带超时保护）
    try:
        response = _call_with_timeout(
            lambda: _call_vision_ocr(image_bytes),
            timeout_sec=60,
            error_msg="Google Vision OCR 调用超时"
        )
    except TimeoutError as e:
        raise RuntimeError(
            f"Google Vision API 调用超时 (60s)。\n"
            f"可能原因:\n"
            f"  1. VPN/代理连接不稳定\n"
            f"  2. 网络连接问题\n"
            f"  3. Google Cloud 服务响应慢\n"
            f"建议: 检查代理状态后重试"
        ) from e

    t2 = time.time()
    logger.info(f"[detect_transaction] Vision API 调用完成: {t2 - t1:.3f}s")

    vision_text = response.full_text_annotation.text
    logger.debug(f"OCR 原始文本 ({len(vision_text)} 字符): {vision_text[:300]}...")

    # 语言检测（沿用原逻辑）
    lan = 'en'

    # 方法1: 检查缅甸文Unicode字符 (U+1000 到 U+109F)
    has_myanmar_chars = any('က' <= char <= '႟' for char in vision_text)

    # 方法2: 检查缅文关键词
    myanmar_keywords = [
        'လုပ်ဆောင်ချက်', 'အောင်မြင်', 'ငွေလွှဲ', 'ကျပ်',
        'နေ့ရက်', 'အချိန်', 'စာရင်း', 'မှတ်ချက်'
    ]
    has_myanmar_keywords = any(keyword in vision_text for keyword in myanmar_keywords)

    if has_myanmar_chars or has_myanmar_keywords:
        lan = 'my'
    else:
        # 降级使用API的语言检测
        for _detect in response.full_text_annotation.pages[0].property.detected_languages:
            if _detect.language_code == 'my' and _detect.confidence > 0.1:
                lan = 'my'
                break

    t3 = time.time()
    logger.info(f"[detect_transaction] 语言检测: {lan} ({t3 - t2:.3f}s)")

    if lan == "my":
        logger.info("检测到缅甸语文本")
        all_valid_trades = detect_myan(vision_text)
    else:
        logger.info("检测到英文文本")
        all_valid_trades = detect_en_new(vision_text)

    t4 = time.time()
    logger.info(f"[detect_transaction] 文本解析完成: {t4 - t3:.3f}s, 总耗时: {t4 - t0:.3f}s")

    return all_valid_trades


# ============================================================
# 便捷函数
# ============================================================

def detect_transaction_from_file(image_path):
    """从图片文件路径读取并识别交易信息"""
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image file not found: {image_path}")

    with open(image_path, 'rb') as f:
        image_bytes = f.read()

    logger.info(f"读取图片: {image_path}, 大小: {len(image_bytes)} bytes")
    return detect_transaction(image_bytes)


# ============================================================
# 命令行入口
# ============================================================

# ============================================================
# 调试模式配置（直接运行即生效，无需命令行参数）
# ============================================================
DEBUG_MODE = True           # True=调试模式, False=正常模式
DEBUG_KBZ_IMAGE = '/www/tmp/kbz02.jpg'        # KBZPay 测试图片路径，例如: '/www/tmp/kbz01.jpg'
DEBUG_WAVE_IMAGE = '/www/tmp/wave01.jpg'       # Wave Money 测试图片路径，例如: '/www/tmp/wave01.jpg'
DEBUG_VERBOSE = True        # 调试模式下是否开启详细日志


def main():
    """命令行入口函数"""
    # --- 调试模式：直接运行 ---
    if DEBUG_MODE:
        verbose = DEBUG_VERBOSE
        show_color = False

        # 收集有效的测试图片路径
        test_images = []
        if DEBUG_KBZ_IMAGE:
            test_images.append(('KBZPay', DEBUG_KBZ_IMAGE))
        if DEBUG_WAVE_IMAGE:
            test_images.append(('Wave Money', DEBUG_WAVE_IMAGE))

        if not test_images:
            print("=" * 60)
            print("  调试模式: 请填写 DEBUG_KBZ_IMAGE 和/或 DEBUG_WAVE_IMAGE 路径")
            print("=" * 60)
            sys.exit(0)

        # 依次识别所有测试图片
        for label, image_path in test_images:
            print(f"\n{'=' * 60}")
            print(f"  📱 支付方式: {label}")
            print(f"{'=' * 60}")
            _process_image(image_path, verbose, show_color)
    # --- 正常模式：命令行参数 ---
    else:
        if len(sys.argv) < 2:
            print("=" * 60)
            print("  交易截图识别工具 - test_detect_transaction.py")
            print("=" * 60)
            print()
            print("用法:")
            print("  python test_detect_transaction.py <image_path> [选项]")
            print()
            print("选项:")
            print("  --verbose, -v   显示详细日志（DEBUG级别）")
            print("  --color         同时输出图片平均颜色信息")
            print()
            sys.exit(0)

        image_path = sys.argv[1]
        verbose = '--verbose' in sys.argv or '-v' in sys.argv
        show_color = '--color' in sys.argv
        _process_image(image_path, verbose, show_color)


def _process_image(image_path, verbose=False, show_color=False):
    """处理单张图片并输出识别结果"""
    if verbose:
        logger.setLevel(logging.DEBUG)
        for handler in logger.handlers:
            handler.setLevel(logging.DEBUG)

    ALLOWED_EXTENSIONS = {'png', 'jpg', 'JPG', 'PNG', 'gif', 'GIF', 'jpeg'}
    if '.' in image_path:
        suffix = image_path.rsplit('.', 1)[1]
        if suffix not in ALLOWED_EXTENSIONS:
            print(f"错误: 不支持的文件格式 '.{suffix}'")
            print(f"支持的格式: {', '.join(ALLOWED_EXTENSIONS)}")
            sys.exit(1)

    try:
        if show_color:
            try:
                r, g, b = detect_color(image_path)
                print(f"图片平均颜色: R={r:.1f}, G={g:.1f}, B={b:.1f}")
            except Exception as e:
                logger.warning(f"颜色检测失败: {e}")

        print(f"\n🔍 正在识别: {image_path}")
        print("-" * 40)

        t_start = time.time()
        all_valid_trades = detect_transaction_from_file(image_path)
        t_elapsed = time.time() - t_start

        print(f"\n📊 识别结果 (耗时: {t_elapsed:.2f}s):")
        print("-" * 40)

        if not all_valid_trades:
            print("❌ 未能识别到任何交易信息")
            print("   请检查图片是否清晰，或联系客服处理")
        else:
            print(f"✅ 成功识别到 {len(all_valid_trades)} 笔交易:\n")
            for i, trade in enumerate(all_valid_trades):
                print(f"  [{i + 1}] 交易ID:     {trade.get('transaction_id', 'N/A')}")
                print(f"      金额:       {trade.get('amount', 'N/A')} Ks")
                print(f"      时间:       {trade.get('order_time', 'N/A')}")
                if trade.get('transfer_to'):
                    print(f"      转账对象:   {trade.get('transfer_to')}")
                if trade.get('notes'):
                    print(f"      备注:       {trade.get('notes')}")
                print()

        print("-" * 40)
        print(f"总耗时: {t_elapsed:.2f}s")

    except FileNotFoundError as e:
        print(f"错误: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"识别失败: {e}", exc_info=True)
        print(f"\n❌ 识别失败: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
