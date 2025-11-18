import re
from PIL import Image
from datetime import datetime

from app_server import google_credentials


def detect_color(img_path):
    # 读职岛像文件
    # 将图像换numpy数组
    image = Image.open(img_path)
    width, height = image.size

    r_total = 0
    g_total = 0
    b_total = 0

    count = 0
    for x in range(0, width):
        for y in range(0, height):
            r, g, b = image.getpixel((x, y))
            r_total += r
            g_total += g
            b_total += b
            count += 1

    r, g, b = (r_total / count, g_total / count, b_total / count)
    return r, g, b


def get_wave_order_time(_str):
    order_time = re.search(r"(\w+)\s(\d+)\s?,\s?(\d+) (\d{2}:\d{2}:\d{2}) (AM|PM)", _str)
    if order_time:
        datetime_str = " ".join(order_time.groups())
        order_time = datetime.strptime(datetime_str, '%b %d %Y %H:%M:%S %p')
        return str(order_time.date())
    return None


def get_wave_order_time_myan(_str):
    order_time = re.search(r"(\w+)\s(\d+)\s?,\s?(\d+) (\d{2}:\d{2}:\d{2}) (AM|PM)", _str)
    if order_time:
        datetime_str = " ".join(order_time.groups())
        order_time = datetime.strptime(datetime_str, '%b %d %Y %H:%M:%S %p')
        return str(order_time)
    return None


def get_ks_order_time(_str):
    order_time = re.search(r"\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}", _str)
    if order_time:
        order_time = order_time[0]
        order_time = datetime.strptime(order_time, "%d/%m/%Y %H:%M:%S")
        return str(order_time)
    return None


def detect_myan(result_str):
    all_valid_trades = []
    # r, g, b = detect_color(img_path)
    print("it's wave")
    # 新版wave单张
    if "အောင်မြင်ပါသည်" in result_str and "နေ့ရက်နှင့်အချိန်" in result_str:
        transaction_id = re.search(r"လုပ်ဆောင်ချက်အိုင်ဒီ.*?(\d{8,})", result_str, re.DOTALL)
        amount_re = re.search(r"အောင်မြင်ပါသည်\n(.*?) ကျပ်", result_str)
        print("its new wave detail")

        if transaction_id and amount_re:
            transaction_id = transaction_id[1]
            amount = amount_re[1].replace(",", "").replace(" ", "")
            from google.cloud import translate_v2 as translate
            translate_client = translate.Client(credentials=google_credentials)
            translate_result = translate_client.translate(result_str, target_language="en", source_language="my")
            translate_str = translate_result["translatedText"].lower()
            print("got translate result", translate_str)
            order_time = re.search(r"(\d{2}) (\w+) (\d{4}) • (\d+:\d+) (am|pm)", translate_str)
            if order_time:
                datetime_str = " ".join(order_time.groups())
                order_time = datetime.strptime(datetime_str, '%d %b %Y %H:%M %p')
            detect_result = {'transaction_id': transaction_id, 'amount': amount, 'order_time': str(order_time.date())}
            all_valid_trades.append(detect_result)
    # wave 单张安卓
    elif "ငွေလွှဲခြင်း" in result_str:
        transaction_id = re.search(r"လုပ်ငန်းစဉ်.*?(\d{8,})", result_str, re.DOTALL)
        amount_re = re.search(r"စုစုပေါင်းပမာဏ\n(\d+.*?) ကျပ်", result_str)
        if transaction_id and amount_re:
            transaction_id = transaction_id[1]
            amount = int(amount_re[1].replace(",", ""))
            # 加入订单时间判断
            order_time = re.search(r"(\w+)\s(\d+)\s?,\s?(\d+) (\d{2}:\d{2}:\d{2}) (AM|PM)", result_str)
            if order_time:
                datetime_str = " ".join(order_time.groups())
                order_time = datetime.strptime(datetime_str, '%b %d %Y %H:%M:%S %p')
            detect_result = {'transaction_id': transaction_id, 'amount': amount, 'order_time': str(order_time.date())}
            all_valid_trades.append(detect_result)
    # wave 单张苹果
    elif "အောင်မြင်ပါတယ်" in result_str:
        transaction_id = re.search(r"လုပ်ငန်းစဉ်.*?(\d{8,})", result_str, re.DOTALL)
        amount_re = re.search(r"အောင်မြင်ပါတယ်\n(.*?) ကျပ်", result_str)
        if transaction_id and amount_re:
            transaction_id = transaction_id[1]
            amount = amount_re[1].replace(",", "").replace(" ", "")
            # 加入订单时间判断
            order_time = re.search(r"(\d{2} \w+ \d{4})", result_str)
            if order_time:
                order_time = datetime.strptime(order_time[1], '%d %b %Y')
            detect_result = {'transaction_id': transaction_id, 'amount': amount, 'order_time': str(order_time.date())}
            all_valid_trades.append(detect_result)
    # wave ios 列表点击详情
    elif "Send Money" in result_str and "အသေးစိတ်" in result_str:
        transaction_id = re.search(r".*\s(\d{8,})", result_str)
        amount_re = re.search(r"(.*?) ကျပ်", result_str)
        if transaction_id and amount_re:
            transaction_id = transaction_id[1]
            amount = amount_re[1].replace(",", "").replace(" ", "")
            # 加入订单时间判断
            order_time = re.search(r"(\d{2}) (\w+) (\d{4}) • (\d{2}:\d{2}) (AM|PM)", result_str)
            if order_time:
                datetime_str = " ".join(order_time.groups())
                order_time = datetime.strptime(datetime_str, '%d %b %Y %H:%M %p')
            detect_result = {'transaction_id': transaction_id, 'amount': amount, 'order_time': str(order_time.date())}
            all_valid_trades.append(detect_result)
    # wave 列表安卓 (Wave-Adroid-Myan)
    elif "စာရင်း" in result_str:
        trans_ids = re.findall(r"လုပ်ငန်းစဉ်အမှတ် -\n?.*?(\d{8,})", result_str)
        amounts = re.findall(r"([+-].*?) ကျပ်", result_str)
        print("----", trans_ids, amounts)
        print(min(len(trans_ids), len(amounts)))
        for i in range(min(len(trans_ids), len(amounts))):
            if not amounts[i]:
                continue
            print(amounts[i])
            amount = amounts[i]
            if amount.startswith("+"):
                continue
            all_valid_trades.append({'transaction_id': trans_ids[i], 'amount': amounts[i]})

    # ks 单张苹果
    elif "လုပ်ဆောင်မှုအောင်မြင်ပါသည်" in result_str:
        transaction_id = re.search(r"(\d{20})", result_str)
        amount_re = re.search(r"-(\d+,?\d+).00 (Ks)", result_str)
        print(transaction_id, amount_re)
        if amount_re and transaction_id:
            transaction_id = transaction_id[1]
            amount = float(amount_re[1].replace(",", ""))
            amount = abs(amount)
            # 加入订单时间识别
            order_time = re.search(r"\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}", result_str)
            if order_time:
                order_time = order_time[0]
                order_time = datetime.strptime(order_time, "%d/%m/%Y %H:%M:%S")

            detect_result = {'transaction_id': transaction_id, 'amount': amount, 'order_time': str(order_time.date())}
            all_valid_trades.append(detect_result)
    # ks 新版安卓
    elif "Thank you for using KBZPay" in result_str:
        transaction_id = re.search(r"(\d{20})", result_str)
        amount_re = re.search(r"-(\d+,?\d+).00 (Ks)", result_str)
        print(transaction_id, amount_re)
        if amount_re and transaction_id:
            transaction_id = transaction_id[1]
            amount = float(amount_re[1].replace(",", ""))
            amount = abs(amount)
            # 加入订单时间识别
            order_time = re.search(r"\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}", result_str)
            if order_time:
                order_time = order_time[0]
                order_time = datetime.strptime(order_time, "%d/%m/%Y %H:%M:%S")
            detect_result = {'transaction_id': transaction_id, 'amount': amount, 'order_time': str(order_time.date())}
            all_valid_trades.append(detect_result)

    print("mian translate:", all_valid_trades)
    if not len(all_valid_trades):
        transaction_id = re.search(r".*\s(\d{8,})", result_str)
        amount_re = re.search(r"-(\d+,?\d+).00 \wyat", result_str)
        if transaction_id and amount_re:
            transaction_id = transaction_id[1]
            amount = int(amount_re[1].replace(",", ""))

            all_valid_trades.append({'transaction_id': transaction_id, 'amount': amount, 'order_time': get_wave_order_time(result_str)})
    return all_valid_trades


def detect_en_new(result_str):
    all_valid_trades = []
    # 新版wave单张
    if "Successful" in result_str and "Date & Time" in result_str:
        transaction_id = re.search(r"Transaction.*?(\d{8,})", result_str, re.DOTALL)
        amount_re = re.search(r"Successful\n(\d+.*?) Ks", result_str)
        print("its new wave detail")

        if transaction_id and amount_re:
            transaction_id = transaction_id[1]
            amount = amount_re[1].replace(",", "").replace(" ", "")
            order_time = re.search(r"(\d{2}) (\w+) (\d{4})\s?•?\s?(\d+:\d+) (AM|PM)", result_str)
            if order_time:
                datetime_str = " ".join(order_time.groups())
                order_time = datetime.strptime(datetime_str, '%d %b %Y %H:%M %p')
            detect_result = {'transaction_id': transaction_id, 'amount': amount, 'order_time': str(order_time.date())}
            all_valid_trades.append(detect_result)
    # wave 单张安卓
    if re.search(r"Successful(.*?) Kyat", result_str, re.DOTALL):
        transaction_id = re.search(r"Transaction.*?(\d{8,})", result_str, re.DOTALL)
        amount_re = re.search(r"Successful\n?(\d+.*?) Kyat", result_str)
        if transaction_id and amount_re:
            transaction_id = transaction_id[1]
            amount = int(amount_re[1].replace(",", ""))
            # 加入订单时间判断
            order_time = re.search(r"(\d{2} \w+ \d{4})", result_str)
            if order_time:
                order_time = datetime.strptime(order_time[1], '%d %b %Y')
            detect_result = {'transaction_id': transaction_id, 'amount': amount, 'order_time': str(order_time.date())}
            all_valid_trades.append(detect_result)
    # wave 列表安卓 (Wave-Adroid-Myan)
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
            if amount.startswith("+"):
                continue
            amount = int(amount.replace(",", "").replace("-", ""))
            all_valid_trades.append({'transaction_id': trans_ids[i].strip(), 'amount': amount})
    # wave ios Wave-IOS-EN
    elif "Send Money" in result_str and "Details" in result_str:
        transaction_id = re.search(r".*\s(\d{8,})", result_str)
        amount_re = re.search(r"(-?\d+,?\d+) Ks", result_str)
        if transaction_id and amount_re:
            transaction_id = transaction_id[1]
            amount = int(amount_re[1].replace(",", "").replace(" ", ""))
            # 加入订单时间判断
            order_time = re.search(r"(\d{2}) (\w+) (\d{4})\s?•?\s?(\d{2}:\d{2}) (AM|PM)", result_str)
            if order_time:
                datetime_str = " ".join(order_time.groups())
                order_time = datetime.strptime(datetime_str, '%d %b %Y %H:%M %p')
            detect_result = {'transaction_id': transaction_id, 'amount': amount, 'order_time': str(order_time.date())}
            all_valid_trades.append(detect_result)
    # wave 单张苹果 Wave-IOS-Eng-SS
    elif "Send Money" in result_str:
        transaction_id = re.search(r"Transaction.*?(\d{8,})", result_str, re.DOTALL)
        amount_re = re.search(r"(-?\d+,?\d+) Kyat", result_str)
        if transaction_id and amount_re:
            transaction_id = transaction_id[1]
            amount = amount_re[1].replace(",", "").replace(" ", "")
            # 加入订单时间判断
            order_time = re.search(r"(\w+)\s(\d{2})\s?,\s?(\d{4}) (\d{2}:\d{2}:\d{2}) (AM|PM)", result_str)
            if order_time:
                datetime_str = " ".join(order_time.groups())
                order_time = datetime.strptime(datetime_str, '%b %d %Y %H:%M:%S %p')
            detect_result = {'transaction_id': transaction_id, 'amount': amount, 'order_time': str(order_time.date())}
            all_valid_trades.append(detect_result)

    # ks 单张苹果
    elif "Payment Successful" in result_str:
        transaction_id = re.search(r"(\d{20})", result_str)
        amount_re = re.search(r"-(\d+,?\d+).00 (Ks)", result_str)
        print(transaction_id, amount_re)
        if amount_re and transaction_id:
            transaction_id = transaction_id[1]
            amount = float(amount_re[1].replace(",", ""))
            amount = abs(amount)
            # 加入订单时间识别
            order_time = re.search(r"\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}", result_str)
            if order_time:
                order_time = order_time[0]
                order_time = datetime.strptime(order_time, "%d/%m/%Y %H:%M:%S")

            detect_result = {'transaction_id': transaction_id, 'amount': amount, 'order_time': str(order_time.date())}
            all_valid_trades.append(detect_result)
    # 新版ks安卓
    elif "Thank you for using KBZPay" in result_str:
        transaction_id = re.search(r"(\d{20})", result_str)
        amount_re = re.search(r"-(\d+,?\d+).00\s?Ks", result_str)
        print(transaction_id, amount_re)
        if amount_re and transaction_id:
            transaction_id = transaction_id[1]
            amount = float(amount_re[1].replace(",", ""))
            amount = abs(amount)
            # 加入订单时间识别
            order_time = re.search(r"\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}", result_str)
            if order_time:
                order_time = order_time[0]
                order_time = datetime.strptime(order_time, "%d/%m/%Y %H:%M:%S")

            detect_result = {'transaction_id': transaction_id, 'amount': amount, 'order_time': str(order_time.date())}
            all_valid_trades.append(detect_result)

    print("mian translate:", all_valid_trades)
    if not len(all_valid_trades):
        transaction_id = re.search(r".*\s(\d{8,})", result_str)
        amount_re = re.search(r"-(\d+,?\d+).00 \wyat", result_str)
        if transaction_id and amount_re:
            transaction_id = transaction_id[1]
            amount = int(amount_re[1].replace(",", ""))

            all_valid_trades.append({'transaction_id': transaction_id, 'amount': amount, 'order_time': get_wave_order_time(result_str)})
    return all_valid_trades

