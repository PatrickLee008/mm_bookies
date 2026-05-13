import re
from PIL import Image, ImageStat
from datetime import datetime

from app_server import google_credentials
from app_server.logger import get_logger

logger = get_logger()

# 懒加载单例: 避免每次翻译请求重建连接
_translate_client = None


def _get_translate_client():
    global _translate_client
    if _translate_client is None:
        from google.cloud import translate_v2 as translate
        _translate_client = translate.Client(credentials=google_credentials)
    return _translate_client


def parse_datetime_flexible(datetime_str, format_patterns):
    """
    尝试使用多个格式解析日期时间字符串

    Args:
        datetime_str: 日期时间字符串
        format_patterns: 格式模式列表，按优先级排序

    Returns:
        datetime: 解析后的datetime对象，如果都失败则返回None
    """
    for pattern in format_patterns:
        try:
            return datetime.strptime(datetime_str, pattern)
        except ValueError:
            continue
    return None


def detect_color(img_path):
    """
    检测图像的平均颜色
    用途:可能用于判断截图类型或验证图片有效性

    Args:
        img_path: 图片文件路径

    Returns:
        tuple: (r, g, b) 平均RGB颜色值
    """
    image = Image.open(img_path).convert('RGB')
    stat = ImageStat.Stat(image)
    return stat.mean[0], stat.mean[1], stat.mean[2]


def get_wave_order_time(_str):
    """
    从Wave支付文本中提取订单日期(仅日期部分)

    匹配格式: "Jan 15, 2024 10:30:45 AM"

    Args:
        _str: 包含时间信息的字符串

    Returns:
        str: 日期字符串(YYYY-MM-DD)或None
    """
    # 正则匹配: 月份 日期, 年份 时:分:秒 AM/PM
    order_time = re.search(r"(\w+)\s(\d+)\s?,\s?(\d+) (\d{2}:\d{2}:\d{2}) (AM|PM)", _str)
    if order_time:
        datetime_str = " ".join(order_time.groups())
        order_time = datetime.strptime(datetime_str, '%b %d %Y %H:%M:%S %p')
        return str(order_time.date())
    return None


def get_wave_order_time_myan(_str):
    """
    从Wave支付文本中提取完整订单时间(包含时分秒)

    与get_wave_order_time类似,但返回完整的日期时间

    Args:
        _str: 包含时间信息的字符串

    Returns:
        str: 完整日期时间字符串或None
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

    Args:
        _str: 包含时间信息的字符串

    Returns:
        str: 完整日期时间字符串或None
    """
    # 正则匹配: DD/MM/YYYY HH:MM:SS
    order_time = re.search(r"\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}", _str)
    if order_time:
        order_time = order_time[0]
        order_time = datetime.strptime(order_time, "%d/%m/%Y %H:%M:%S")
        return str(order_time)
    return None


def detect_myan(result_str):
    """
    识别缅甸语支付截图中的交易信息
    支持Wave Money和KBZPay两种支付方式,多种截图格式

    Args:
        result_str: OCR识别后的文本内容(缅甸语)

    Returns:
        list: 包含交易信息的字典列表
              [{'transaction_id': 'xxx', 'amount': 'xxx', 'order_time': 'xxx'}]
    """
    all_valid_trades = []
    logger.debug("detect_myan: it's wave")

    # ==================== Wave Money 识别 ====================

    # 情况1: 新版Wave单张详情(需要翻译)
    if "အောင်မြင်ပါသည်" in result_str and "နေ့ရက်နှင့်အချိန်" in result_str:
        # 提取交易ID(至少8位数字)
        transaction_id = re.search(r"လုပ်ဆောင်ချက်အိုင်ဒီ.*?(\d{8,})", result_str, re.DOTALL)
        # 提取金额(缅甸语格式)
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
            order_time = re.search(r"(\d{2}) (\w+) (\d{4}) • (\d+:\d+) (am|pm)", translate_str)
            if order_time:
                datetime_str = " ".join(order_time.groups())
                # 尝试月份简写和全称两种格式
                order_time = parse_datetime_flexible(datetime_str, ['%d %b %Y %H:%M %p', '%d %B %Y %H:%M %p'])

            detect_result = {'transaction_id': transaction_id, 'amount': amount, 'order_time': str(order_time.date())}
            all_valid_trades.append(detect_result)

    # 情况2: Wave单张安卓版
    elif "ငွေလွှဲခြင်း" in result_str:
        transaction_id = re.search(r"လုပ်ငန်းစဉ်.*?(\d{8,})", result_str, re.DOTALL)
        amount_re = re.search(r"စုစုပေါင်းပမာဏ\n(\d+.*?) ကျပ်", result_str)
        if transaction_id and amount_re:
            transaction_id = transaction_id[1]
            amount = int(amount_re[1].replace(",", ""))

            # 提取订单时间
            order_time = re.search(r"(\w+)\s(\d+)\s?,\s?(\d+) (\d{2}:\d{2}:\d{2}) (AM|PM)", result_str)
            if order_time:
                datetime_str = " ".join(order_time.groups())
                order_time = datetime.strptime(datetime_str, '%b %d %Y %H:%M:%S %p')

            detect_result = {'transaction_id': transaction_id, 'amount': amount, 'order_time': str(order_time.date())}
            all_valid_trades.append(detect_result)

    # 情况3: Wave单张iOS版
    elif "အောင်မြင်ပါတယ်" in result_str:
        transaction_id = re.search(r"လုပ်ငန်းစဉ်.*?(\d{8,})", result_str, re.DOTALL)
        amount_re = re.search(r"အောင်မြင်ပါတယ်\n(.*?) ကျပ်", result_str)
        if transaction_id and amount_re:
            transaction_id = transaction_id[1]
            amount = amount_re[1].replace(",", "").replace(" ", "")

            # 提取订单时间(仅日期)
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

            # 提取订单时间
            order_time = re.search(r"(\d{2}) (\w+) (\d{4}) • (\d{2}:\d{2}) (AM|PM)", result_str)
            if order_time:
                datetime_str = " ".join(order_time.groups())
                # 尝试月份简写和全称两种格式
                order_time = parse_datetime_flexible(datetime_str, ['%d %b %Y %H:%M %p', '%d %B %Y %H:%M %p'])

            detect_result = {'transaction_id': transaction_id, 'amount': amount, 'order_time': str(order_time.date())}
            all_valid_trades.append(detect_result)

    # 情况5: Wave列表安卓版(可能包含多笔交易)
    elif "စာရင်း" in result_str:
        # 提取所有交易ID
        trans_ids = re.findall(r"လုပ်ငန်းစဉ်အမှတ် -\n?.*?(\d{8,})", result_str)
        # 提取所有金额(带正负号)
        amounts = re.findall(r"([+-].*?) ကျပ်", result_str)
        logger.debug(f"detect_myan wave list: trans_ids={trans_ids}, amounts={amounts}")

        # 遍历匹配的交易
        for i in range(min(len(trans_ids), len(amounts))):
            if not amounts[i]:
                continue
            amount = amounts[i]
            # 跳过收入交易(只记录支出)
            if amount.startswith("+"):
                continue
            all_valid_trades.append({'transaction_id': trans_ids[i], 'amount': amounts[i]})

    # ==================== KBZPay 识别 ====================
    # 情况6: KBZPay新版详情页(英文) - Payment Successful / E-Receipt格式
    elif "Payment Successful" in result_str or "လုပ်ဆောင်မှုအောင်မြင်ပါသည်" in result_str or (
            "E-Receipt" in result_str and "KBZ" in result_str):
        # 提取20位交易ID
        transaction_id = re.search(r"(\d{20})", result_str)
        # 新格式金额: -1.00 (Ks) 或 -100.00 (Ks) 或 -1.00 Ks
        amount_re = re.search(r"-(\d+(?:,?\d+)?(?:\.\d{2})?) ?\(?\s?Ks\)?", result_str)
        logger.debug(f"detect_myan KBZ format: transaction_id={transaction_id}, amount={amount_re}")
        if amount_re and transaction_id:
            transaction_id = transaction_id[1]
            amount = float(amount_re[1].replace(",", ""))
            amount = abs(amount)
            # 提取订单时间: 16/12/2025 10:36:08 或 16/12/2025 11:05:37
            order_time = re.search(r"(\d{2}/\d{2}/\d{4}) (\d{2}:\d{2}:\d{2})", result_str)
            if order_time:
                datetime_str = f"{order_time[1]} {order_time[2]}"
                order_time = datetime.strptime(datetime_str, "%d/%m/%Y %H:%M:%S")
            detect_result = {'transaction_id': transaction_id, 'amount': amount,
                             'order_time': str(order_time.date()) if order_time else None}
            all_valid_trades.append(detect_result)

    # 情况7: 新版KBZPay安卓(旧格式)
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

            detect_result = {'transaction_id': transaction_id, 'amount': amount, 'order_time': str(order_time.date())}
            all_valid_trades.append(detect_result)

    # # 情况6: KBZPay单张iOS版
    # elif "လုပ်ဆောင်မှုအောင်မြင်ပါသည်" in result_str or ("E-Receipt" in result_str and "KBZ" in result_str):
    #     # elif "လုပ်ဆောင်မှုအောင်မြင်ပါသည်" in result_str:
    #     # KBZPay交易ID为20位
    #     transaction_id = re.search(r"(\d{20})", result_str)
    #     # 金额格式: -1,000.00 Ks
    #     amount_re = re.search(r"-(\d+,?\d+).00 (Ks)", result_str)
    #     print(transaction_id, amount_re)
    #
    #     if amount_re and transaction_id:
    #         transaction_id = transaction_id[1]
    #         amount = float(amount_re[1].replace(",", ""))
    #         amount = abs(amount)  # 取绝对值
    #
    #         # 提取订单时间
    #         order_time = re.search(r"\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}", result_str)
    #         if order_time:
    #             order_time = order_time[0]
    #             order_time = datetime.strptime(order_time, "%d/%m/%Y %H:%M:%S")
    #
    #         detect_result = {'transaction_id': transaction_id, 'amount': amount, 'order_time': str(order_time.date())}
    #         all_valid_trades.append(detect_result)
    #
    # # 情况7: KBZPay新版安卓
    # elif "Thank you for using KBZPay" in result_str:
    #     transaction_id = re.search(r"(\d{20})", result_str)
    #     amount_re = re.search(r"-(\d+,?\d+).00 (Ks)", result_str)
    #     print(transaction_id, amount_re)
    #
    #     if amount_re and transaction_id:
    #         transaction_id = transaction_id[1]
    #         amount = float(amount_re[1].replace(",", ""))
    #         amount = abs(amount)
    #
    #         # 提取订单时间
    #         order_time = re.search(r"\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}", result_str)
    #         if order_time:
    #             order_time = order_time[0]
    #             order_time = datetime.strptime(order_time, "%d/%m/%Y %H:%M:%S")
    #
    #         detect_result = {'transaction_id': transaction_id, 'amount': amount, 'order_time': str(order_time.date())}
    #         all_valid_trades.append(detect_result)

    logger.debug(f"detect_myan result: {all_valid_trades}")

    # 兜底逻辑:如果以上都没匹配到,尝试通用模式
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


def detect_en_new(result_str):
    """
    识别英文支付截图中的交易信息
    支持Wave Money和KBZPay两种支付方式,多种截图格式

    Args:
        result_str: OCR识别后的文本内容(英文)

    Returns:
        list: 包含交易信息的字典列表
              [{'transaction_id': 'xxx', 'amount': 'xxx', 'order_time': 'xxx'}]
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

            # 提取时间: "15 Jan 2024 • 10:30 AM" 或 "23 December 2025 10:23 AM"
            order_time = re.search(r"(\d{2}) (\w+) (\d{4})\s?•?\s?(\d+:\d+) (AM|PM)", result_str)
            if order_time:
                datetime_str = " ".join(order_time.groups())
                # 尝试月份简写和全称两种格式
                order_time = parse_datetime_flexible(datetime_str, ['%d %b %Y %H:%M %p', '%d %B %Y %H:%M %p'])

            detect_result = {'transaction_id': transaction_id, 'amount': amount, 'order_time': str(order_time.date())}
            all_valid_trades.append(detect_result)

    # 情况2: Wave单张安卓版
    if re.search(r"Successful(.*?) Kyat", result_str, re.DOTALL):
        transaction_id = re.search(r"Transaction.*?(\d{8,})", result_str, re.DOTALL)
        amount_re = re.search(r"Successful\n?(\d+.*?) Kyat", result_str)
        if transaction_id and amount_re:
            transaction_id = transaction_id[1]
            amount = int(amount_re[1].replace(",", ""))

            # 提取时间
            order_time = re.search(r"(\d{2} \w+ \d{4})", result_str)
            if order_time:
                # 尝试月份简写和全称两种格式
                order_time = parse_datetime_flexible(order_time[1], ['%d %b %Y', '%d %B %Y'])

            detect_result = {'transaction_id': transaction_id, 'amount': amount, 'order_time': str(order_time.date())}
            all_valid_trades.append(detect_result)

    # 情况3: Wave列表安卓版
    elif "History" in result_str:
        trans_ids = re.findall(r"Transaction ID -?\n?.*?(\d{8,})", result_str)
        amounts = re.findall(r"([+-].*?) Kyat", result_str)
        print("----", trans_ids, amounts)
        print(min(len(trans_ids), len(amounts)))

        for i in range(min(len(trans_ids), len(amounts))):
            if not amounts[i]:
                continue
            print(amounts[i])
            amount = amounts[i]
            # 跳过收入交易
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

            order_time = re.search(r"(\d{2}) (\w+) (\d{4})\s?•?\s?(\d{2}:\d{2}) (AM|PM)", result_str)
            if order_time:
                datetime_str = " ".join(order_time.groups())
                # 尝试月份简写和全称两种格式
                order_time = parse_datetime_flexible(datetime_str, ['%d %b %Y %H:%M %p', '%d %B %Y %H:%M %p'])

            detect_result = {'transaction_id': transaction_id, 'amount': amount, 'order_time': str(order_time.date())}
            all_valid_trades.append(detect_result)

    # 情况5: Wave单张iOS版(另一种格式)
    elif "Send Money" in result_str:
        transaction_id = re.search(r"Transaction.*?(\d{8,})", result_str, re.DOTALL)
        amount_re = re.search(r"(-?\d+,?\d+) Kyat", result_str)
        if transaction_id and amount_re:
            transaction_id = transaction_id[1]
            amount = amount_re[1].replace(",", "").replace(" ", "")

            order_time = re.search(r"(\w+)\s(\d{2})\s?,\s?(\d{4}) (\d{2}:\d{2}:\d{2}) (AM|PM)", result_str)
            if order_time:
                datetime_str = " ".join(order_time.groups())
                # 尝试月份简写和全称两种格式
                order_time = parse_datetime_flexible(datetime_str, ['%b %d %Y %H:%M:%S %p', '%B %d %Y %H:%M:%S %p'])

            detect_result = {'transaction_id': transaction_id, 'amount': amount, 'order_time': str(order_time.date())}
            all_valid_trades.append(detect_result)

    # ==================== KBZPay 识别 ====================

    # 情况6: KBZPay新版详情页(英文) - Payment Successful / E-Receipt格式
    elif "Payment Successful" in result_str or ("E-Receipt" in result_str and "KBZ" in result_str):
        # 提取20位交易ID
        transaction_id = re.search(r"(\d{20})", result_str)
        # 新格式金额: -1.00 (Ks) 或 -100.00 (Ks) 或 -1.00 Ks
        amount_re = re.search(r"-(\d+(?:,?\d+)?(?:\.\d{2})?) ?\(?\s?Ks\)?", result_str)

        print("KBZ Payment Successful/E-Receipt format:", transaction_id, amount_re)

        if amount_re and transaction_id:
            transaction_id = transaction_id[1]
            amount = float(amount_re[1].replace(",", ""))
            amount = abs(amount)

            # 提取订单时间: 16/12/2025 10:36:08 或 16/12/2025 11:05:37
            order_time = re.search(r"(\d{2}/\d{2}/\d{4}) (\d{2}:\d{2}:\d{2})", result_str)
            if order_time:
                datetime_str = f"{order_time[1]} {order_time[2]}"
                order_time = datetime.strptime(datetime_str, "%d/%m/%Y %H:%M:%S")

            detect_result = {'transaction_id': transaction_id, 'amount': amount,
                             'order_time': str(order_time.date()) if order_time else None}
            all_valid_trades.append(detect_result)

    # 情况7: 新版KBZPay安卓(旧格式)
    elif "Thank you for using KBZPay" in result_str:
        transaction_id = re.search(r"(\d{20})", result_str)
        amount_re = re.search(r"-(\d+,?\d+)\.00\s?Ks", result_str)
        print(transaction_id, amount_re)

        if amount_re and transaction_id:
            transaction_id = transaction_id[1]
            amount = float(amount_re[1].replace(",", ""))
            amount = abs(amount)

            order_time = re.search(r"\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}", result_str)
            if order_time:
                order_time = order_time[0]
                order_time = datetime.strptime(order_time, "%d/%m/%Y %H:%M:%S")

            detect_result = {'transaction_id': transaction_id, 'amount': amount, 'order_time': str(order_time.date())}
            all_valid_trades.append(detect_result)

    print("mian translate:", all_valid_trades)

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
