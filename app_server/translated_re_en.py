from app_server.service import translate_re_en
import re

with open("translated_sample_en", encoding="utf-8") as f:
    result_str = f.read()

    all_valid_trades = translate_re_en(result_str)
    print(all_valid_trades)

    # for tid in trans_ids:
    #     print(tid, tid.isdigit())
    # for amount in amounts:
    #     print(amount)
