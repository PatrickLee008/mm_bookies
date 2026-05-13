# -*- coding: utf-8 -*-
from app_server import app, app_opt, db
import datetime
from flask import current_app

from app_server.controller.InvitationActivityV2Controller import invitation_v2
from app_server.controller.CouponController import coupon
from app_server.controller.PromotionController import promotion
from app_server.utils.Kits import Kits
from app_server.model.AppMemberBalanceLogModel import AppMemberBalanceLog

from app_server.controller.AppUserController import app_user
from app_server.controller.MatchController import match
from app_server.controller.MdictController import r_conf
from app_server.controller.OrderController import order
from app_server.controller.ChargeApplyController import charge_apply
from app_server.controller.WithDrawController import withdraw
from app_server.controller.BankCardController import bank_card
from app_server.controller.NoticeController import r_notice
from app_server.controller.UploadedImagesController import r_up_image
from app_server.controller.AppOperationController import app_operation
from app_server.controller.TechResultController import r_tech_result
from app_server.controller.ChargeController import r_charge
from app_server.controller.AppFavouriteController import favourite
from app_server.controller.ApiController import api
from app_server.controller.AppBalanceLogController import balance_log
from app_server.controller.AppAgentBankcardController import agent_bankcard
from app_server.controller.WebSocketMessageController import websocket_message
from app_server.controller.AWCGameController import awc_game_bp
from app_server.controller.SplashScreenController import r_splash_screen
from app_server.controller.AdvertisementController import r_advertisement
from app_server.controller.PublicController import public
from app_server.controller.SettingController import setting
from app_server.controller.ShortUrlController import short_url
from app_server.controller.MessageController import message
from app_server.controller.SmsVerifyController import sms_verify

app.register_blueprint(app_user, url_prefix='/app_user')
app.register_blueprint(match, url_prefix='/match')
app.register_blueprint(r_conf, url_prefix='/config')
app.register_blueprint(order, url_prefix='/order')
app.register_blueprint(charge_apply, url_prefix='/charge_apply')
app.register_blueprint(withdraw, url_prefix='/withdraw')
app.register_blueprint(bank_card, url_prefix='/bank_card')
app.register_blueprint(r_notice, url_prefix='/notice')
app.register_blueprint(r_up_image, url_prefix='/up_image')
app.register_blueprint(app_operation, url_prefix='/app_operation')
# app.register_blueprint(digital, url_prefix='/digital')
# app.register_blueprint(digital_3d, url_prefix='/digital_3d')
app.register_blueprint(r_tech_result, url_prefix='/tech_result')
app.register_blueprint(bank_card, url_prefix='/bank_card')
app.register_blueprint(r_charge, url_prefix='/charge')
app.register_blueprint(favourite, url_prefix='/favourite')
app.register_blueprint(api, url_prefix='/api')
app.register_blueprint(balance_log, url_prefix='/balance_log')
app.register_blueprint(agent_bankcard, url_prefix='/agent_bankcard')
app.register_blueprint(coupon, url_prefix='/coupon')
app.register_blueprint(promotion, url_prefix='/promotion')  # 促销活动API
app.register_blueprint(awc_game_bp)  # AWC游戏API
app.register_blueprint(r_splash_screen, url_prefix='/splash_screen')  # 启动页API
app.register_blueprint(r_advertisement, url_prefix='/advertisement')  # 广告API
app.register_blueprint(public, url_prefix='/public')  # 公共API
app.register_blueprint(setting, url_prefix='/setting')  # 设置API
app.register_blueprint(invitation_v2,url_prefix='/invitation_v2')  # 邀请活动v2.0 API（已包含url_prefix）
app.register_blueprint(short_url, url_prefix='/s')  # 短链接重定向API
app.register_blueprint(message, url_prefix='/message')  # 消息API
# app.register_blueprint(sms_verify, url_prefix='/sms_verify')  # SMS验证码API

@app.route('/hello', methods=['GET'])
def hello():
    return "hello"


@app.route('/favicon.ico')
def favicon():
    # 后端返回文件给前端（浏览器），send_static_file是Flask框架自带的函数
    return current_app.send_static_file('static/favicon.ico')


# 会员帐变
@app_opt.connect
def on_app_opt(args):
    print("app opting something:", args["user_account"], datetime.datetime.now(), args["type"], args["amount"],
          args["after_amount"], args["source_id"])
    is_digit = "is_digit" in args
    # 修改使用新model
    opt = AppMemberBalanceLog(
        id=Kits.generate_uuid(),
        sn=Kits.generate_uuid(),
        create_by_id=args.get('create_by_id'),
        type=args.get('type'),
        type_sub=args.get('type_sub'),
        type_sub_data_id=args.get('source_id'),
        pro_id=args.get('pro_id'),  # 使用get方法，如果不存在则返回None
        bet_id=args.get('bet_id'),
        mb_id=args.get('user_account'),
        aid=args.get('aid'),
        mb_username=args.get('user_name'),
        mb_rid=args.get('mb_rid'),
        money=args.get("amount"),
        start_balance=args.get("before_amount"),
        end_balance=args.get("after_amount"),
        source=args.get('source'),
        source_sub=args.get('source_sub'),
        target=args.get("target"),
        target_sub=args.get("target_sub"),
        mc_sn=args.get("mc_sn"),
        mc_name=args.get("mc_name"),
        mn_id=args.get("mn_id"),
        mn_username=args.get("mn_username"),
        source_status=args.get("source_status"),
        pay_wallet=args.get("pay_wallet"),
    )
    opt.remarks = "%s do %s at %s make % amount change %s" % (
        args['user_name'], args.get('type'), str(datetime.datetime.now().replace(microsecond=0)),
        args['amount'], args.get('remark') or '')
    # opt = AppOperation(USER_ACCOUNT=args['user_account'], TYPE=args["type"], AMOUNT=args["amount"],
    #                    BALANCE=args["balance"], SOURCE_ID=args["source_id"], IS_DIGIT=is_digit, MATCH_ID=args.get('match_id') or "")
    # opt.DESC = "%s do %s at %s make % amount change" % (args['user_name'], AppOpType2Name[args['type']], str(datetime.datetime.now().replace(microsecond=0)), args['amount'])
    db.session.add(opt)
    db.session.commit()


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=app.config['PORT'])
