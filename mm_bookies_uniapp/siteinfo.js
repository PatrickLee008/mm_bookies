//正式环境
var siteinfo = {
	"tenant_id": "10000",
	"apiUrl": "http://m.mmbookies.com/api", //后端接口
	"imgUrl": "http://m.mmbookies.com/img", //java后端图片前缀中心
	"payUrl": "https://pay.okbetmm.com", //支付中心
	"wsUrl": "wss://ag.mmbookies.com", //WebSocket服务器
	"awcImgUrl": "https://tttuat.apihub55.com", //awc图片前缀
	"liveChatLink":"https://chat.wellytalk.com/MDE5ZDA1MDItYzU3MC03YjYyLThkMGItMjQ4YTJjMjQ0ODkwfGQzZjQwNTg3NzExOTAzMjFmOWU4MWM4ZDZmMGM4ZDQ4YjAyNDg5ZjQyM2EyZjgyZjc2NmJmMjI2ZTdlM2MxMzA=",
	version: 'v2.0.1'
};

if (process.env.NODE_ENV == 'development') {
	//开发
	// siteinfo.apiUrl = "http://localhost:8282";
	// siteinfo.payUrl = "http://192.168.1.32:9010"; //支付中心
	// siteinfo.apiUrl = "http://m.1x2mmm.net/api";
	// siteinfo.imgUrl = "http://m.1x2mmm.net/img"; //java后端图片前缀
	siteinfo.payUrl = "http://payapi.1x2mmm.net";
} else {
	//测试环境

}

module.exports = siteinfo;