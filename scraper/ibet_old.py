# -*- coding: utf-8 -*-
from sqlalchemy import and_
from lxml import html
import requests
import time
import os
import json
import re


def get_cookies(username, password):
    cookie_path = "%s/static/cookies/ibet789/%s" % (app.config['BASE_DIR'], username)

    cookies = {}
    if os.path.isfile(cookie_path):
        with open(cookie_path, 'r', encoding='utf-8') as f:
            cookies = json.loads(f.read())
    # https://ag.ibet789.com/Header1.aspx?lang=EN-US

    resp = requests.get("https://ag.ibet789.com/accinfo.aspx", cookies=cookies)
    print("cookie query:", resp.text, resp.status_code, resp.url)
    if "Public/Default1.aspx" in resp.url or "Welcome to Ibet789 Management" in resp.text:
        print("cookie invalid..")
        return login(username, password)
    return True, cookies


def get_page_validate(page):
    # 获取页面验证参数
    view_state = re.findall(r'VIEWSTATE\".*value=\"(.*)\"', page)[0]
    view_state_generator = re.findall(r'__VIEWSTATEGENERATOR\".*value=\"(.*)\"', page)[0]
    event_validation = re.findall(r'EVENTVALIDATION\".*value=\"(.*)\"', page)[0]
    return view_state, view_state_generator, event_validation


def login(username, password):
    cookie_path = "%s/static/cookies/ibet789/%s" % (app.config['BASE_DIR'], username)
    session = requests.session()
    resp = session.get("https://ag.ibet789.com/")
    # 获取页面验证参数
    view_state, view_state_generator, event_validation = get_page_validate(resp.text)

    # 构造登录表单
    login_form = {
        "__EVENTTARGET": "btnSignIn",
        "__EVENTARGUMENT": "",
        "__VIEWSTATE": view_state,
        "__VIEWSTATEGENERATOR": view_state_generator,
        "__EVENTVALIDATION": event_validation,
        "txtUserName": username,
        "txtPassword": password
    }

    # 提交登录表单
    session.post(resp.url, login_form)
    # 请求账户信息页面
    resp = session.get("https://ag.ibet789.com/accinfo.aspx")
    print("this shit--------:", resp.text)
    if "Public/Default1.aspx" in resp.url or "Welcome to Ibet789 Management" in resp.text:
        return False, None
    cookies = requests.utils.dict_from_cookiejar(session.cookies)
    with open(cookie_path, "w", encoding="utf-8") as f:
        f.write(json.dumps(cookies))
    print("try to call shit??", resp.text)
    return True, cookies


def sync_mem(conf=None):
    # 从配置读取账号参数
    conf = GameConfig.query.filter_by(ID=1).one_or_none()
    # account = "y7y789"
    # password = "123123"
    # conf = GameConfig.query.filter_by(ID=1).one_or_none()

    account = conf.Account
    password = conf.Password

    state, cookies = get_cookies(account, password)
    if not state:
        return False, "Login error. Please check the account info."

    old_members = MemberCommon.query.filter(and_(MemberCommon.COMPANY_ID == conf.COMPANY_ID, MemberCommon.MANAGER_ID == conf.MANAGER_ID,
                                                 MemberCommon.Game == conf.Game)).all()
    old_members = {mem.UserName for mem in old_members}

    resp = requests.get("https://ag.ibet789.com/_Age/memberlist.aspx", cookies=cookies)
    print("ibet789 got old members:", resp.text, len(old_members))
    time.sleep(1000)
    tree = html.etree.HTML(resp.text)
    members = tree.xpath('//*[@id="MemberList_cm1_g"]/tr[@class!="GridHeader"]')
    print("got such members:", len(members))
    wait_members = []
    for mem in members:
        name = mem.xpath('./td[2]/a/text()')[0]
        enable = 'OPEN' in mem.xpath('./td[29]/text()')[0]
        if name in old_members or not enable:
            continue
        balance = mem.xpath('./td[6]/span/text()')[0]
        phone = mem.xpath('./td[4]/text()')[0]

        print("mem info:", name, balance, enable, phone)

        wait_members.append({'name': name, 'balance': balance, 'phone': phone})
        print(name)
    try:
        db.session.execute(
            MemberCommon.__table__.insert(),
            [{'UserName': mem['name'], 'Balance': mem['balance'], 'Game': conf.Game, 'Phone': mem['phone'],
              'COMPANY_ID': conf.COMPANY_ID, 'MANAGER_ID': conf.MANAGER_ID, 'GameAccount': account,
              'Creator': "tesemployee"} for mem in wait_members]
        )
        db.session.commit()
        return True, "%s Member Synced successfully." % len(wait_members)
    except Exception as e:
        print("ibet789 同步成员出错", e)
        db.session.rollback()

    return False, "Syn member error: unknown"


def create_mem(args, conf, ext):
    # 从配置读取账号参数
    account = conf.Account
    password = conf.Password
    print("%s平台账号 %s 开始创建成员, 密码: %s 序列号: %s" % ("ibet789", account, password, conf.SerialCode))
    print("是否自定义密码:", "txtPassword" in args and args["txtPassword"])
    if not args["txtPassword"]:
        if not conf.DefaultPassword:
            return False, "未配置默认密码,请填写密码", None
        args["txtPassword"] = conf.DefaultPassword

    state, cookies = get_cookies(account, password)
    if not state:
        return False, "Login error. Please check the account info.", None

    session = requests.session()
    # 获取成员创建页面
    resp = session.get("https://ag.ibet789.com/_Age/Member.aspx", cookies=cookies)
    print("what the e?", resp.text, cookies)

    # 获取页面验证参数
    view_state, view_state_generator, event_validation = get_page_validate(resp.text)

    # 数据模型转换为表单
    args.update({
        "__EVENTTARGET": "btnSave",
        "__EVENTARGUMENT": "",
        "__VIEWSTATE": view_state,
        "__VIEWSTATEGENERATOR": view_state_generator,
        "__EVENTVALIDATION": event_validation

    })

    nex_serial = conf.SerialCode
    error = ""

    def post_create():
        nonlocal args
        nonlocal resp
        nonlocal nex_serial
        nonlocal error

        nex_serial = OrmUttil.get_next_letter(nex_serial)
        if nex_serial == "Z999":
            error = "Member create fail: The auto searial code has been use out."
            return False

        args['txtUserName'] = nex_serial
        # print("got mem_form:", mem_form)

        # 表单提交
        resp = session.post("https://ag.ibet789.com/_Age/Member.aspx", args, cookies=cookies)

        if "Profile updated successfully." in resp.text:
            return True
        else:
            tree = html.etree.HTML(resp.text)
            # print("fouding error:", resp.text)
            error = tree.xpath('//*[@id="lblStatus"]/span/text()')[0]
            print("the ibet789 member create result:", error)
            if "User Name already exists." == error:
                print("创建ibet789时名称重复,自动调整序列号")
                return post_create()
            else:
                return False

    if not post_create():
        return False, error, None

    mem_common = MemberCommon(UserName=account + args.get('txtUserName'), Password=args.get('txtPassword'),
                              COMPANY_ID=ext.get('COMPANY_ID'), GameAccount=account, RealName=ext.get('RealName'), Phone=ext.get('Phone'), Code=ext.get('Code'),
                              MANAGER_ID=ext.get('MANAGER_ID'), Balance=0, Game='ibet789', GameID='1', Creator=ext.get('CREATOR'))
    db.session.add(mem_common)
    db.session.commit()

    conf.SerialCode = nex_serial

    mem = MemberIbet789(ID=mem_common.ID)
    db.session.add(mem)
    OrmUttil.set_field(mem, args)
    db.session.commit()

    print(mem_common, type(mem_common))

    return True, "添加成功", mem_common


def edit_mem(mem=None):
    state, cookies = get_cookies("egeaj", "#xx123456")
    if not state:
        return False, "Login error. Please check the account info."

    session = requests.session()
    # 获取成员创建页面
    resp = session.get("https://ag.ibet789.com/_Age/Member.aspx", cookies=cookies)

    # 获取页面验证参数
    view_state, view_state_generator, event_validation = get_page_validate(resp.text)

    # 数据模型转换为表单
    mem_form = mem.to_dict()
    mem_form.pop("ID")
    mem_form.pop("txtUserName")
    mem_form.update({
        "__EVENTTARGET": "btnSave",
        "__EVENTARGUMENT": "",
        "__VIEWSTATE": view_state,
        "__VIEWSTATEGENERATOR": view_state_generator,
        "__EVENTVALIDATION": event_validation
    })

    print("got mem_form:", mem_form)

    # 表单提交
    resp = session.post("https://ag.ibet789.com/_Age/Member.aspx", data=mem_form, params={'userName': mem.ID}, cookies=cookies)

    print("the return:", resp.text)
    if "One of the match limit has exceeded its maximum value, please check the 'MAX=' value beside the limit field." in resp.text:
        return False, "超过限额"
    return True, "修改成功"


def pay_to_mem(conf, target, amount, remark='', is_withdraw=False):
    # 从配置读取账号参数
    account = conf.Account
    password = conf.Password
    print("%s平台账号 %s 开始支付, 密码: %s 支付对象: %s" % ("ibet789", account, password, target))

    state, cookies = get_cookies(account, password)
    if not state:
        return False, "Login error. Please check the account info.", 0

    session = requests.session()

    # 获取成员支付页面
    resp = session.get("https://ag.ibet789.com/_Age/Payment.aspx?pg=payment", cookies=cookies)
    first_mem = re.findall(r'option.*value=\"(.*)\"', resp.text)[0]

    # print("the payment", resp.text, first_mem)

    # 1. 跳转转账界面
    # 获取页面验证参数
    view_state, view_state_generator, event_validation = get_page_validate(resp.text)

    form_data = {
        "__EVENTTARGET": "MemberList1$lstAccounts",
        "__EVENTARGUMENT": "",
        "__LASTFOCUS": "",
        "__VIEWSTATE": view_state,
        "__VIEWSTATEGENERATOR": view_state_generator,
        "__EVENTVALIDATION": event_validation,
        "MemberList1$lstAccounts": target
    }

    resp = session.post('https://ag.ibet789.com/_Age/Payment.aspx?pg=payment', form_data, cookies=cookies)

    # 2. 跳转充值界面
    # 获取页面验证参数
    print("the pay page:----------", resp.text)
    view_state, view_state_generator, event_validation = get_page_validate(resp.text)
    form_data = {
        "__EVENTTARGET": "ctl03$lstPayMode",
        "__EVENTARGUMENT": "",
        "__LASTFOCUS": "",
        "__VIEWSTATE": view_state,
        "__VIEWSTATEGENERATOR": view_state_generator,
        "__EVENTVALIDATION": event_validation,
        "MemberList1$lstAccounts": target,
        "ctl03$lstPayMode": 1,
        "ctl03$lstAccount": first_mem,
        "ctl03$txtAmount": 0

    }
    param = {
        "role": "ag",
        "userName": target,
        "pg": "payment"
    }
    resp = session.post('https://ag.ibet789.com/_Age/Payment.aspx', form_data, params=param, cookies=cookies)
    # print("se payment:", resp.status_code, resp.text)

    # 3. 执行充值操作
    # 获取页面验证参数
    view_state, view_state_generator, event_validation = get_page_validate(resp.text)

    pay_param = {
        "role": "ag",
        "userName": target,
        "pg": "payment"
    }

    pay_data = {
        "__EVENTTARGET": "ctl03$btnSave",
        "__EVENTARGUMENT": "",
        "__LASTFOCUS": "",
        "__VIEWSTATE": view_state,
        "__VIEWSTATEGENERATOR": view_state_generator,
        "__EVENTVALIDATION": event_validation,
        "MemberList1$lstAccounts": target,
        "ctl03$lstPayMode": 1,
        "ctl03$txtAmount": "-" + amount if is_withdraw else amount,
        "ctl03$txtRemark": remark
    }
    print("the pay data:", pay_data, resp.url)

    resp = session.post('https://ag.ibet789.com/_Age/Payment.aspx', data=pay_data, params=pay_param, cookies=cookies, )
    print("pay result is:", resp.status_code, resp.text, resp.headers)
    if resp.status_code == 200:
        # <td align="left"><span id="ctl03_lblBalance"><SPAN class='negative'>-6.00</SPAN></span></td>
        balance = re.findall(r'<span id="ctl03_lblBalance"><SPAN class=\'.*\'>(.*)</SPAN>', resp.text)[0]
        print("got the balance:----", balance)
        return True, "Withdraw succesful." if is_withdraw else "Pay succesful.", float(balance)
    return False, "Withdraw failed." if is_withdraw else "Pay failed.", 0


def mem_withdraw(conf, target, amount, remark=''):
    return pay_to_mem(conf, target, amount, remark, is_withdraw=True)


if __name__ == '__main__':
    # pass
    # login("egeaj", "#xx123456")
    # login("y7y789", "123123")
    # get_cookies("egeaj", "#xx123456")
    # pay_to_mem('egeaj', 'egeajb', "60", 'test pay')
    sync_mem()
