//正式环境
var siteinfo = {
	"tenant_id": "10000",
	"apiUrl": "http://m.mmbookies.com/api", //后端接口
	"imgUrl": "http://m.mmbookies.com/img", //java后端图片前缀中心
	"payUrl": "https://pay.okbetmm.com", //支付中心
	"wsUrl": "wss://ag.mmbookies.com", //WebSocket服务器
	"awcImgUrl": "https://tttuat.apihub55.com", //awc图片前缀
	"liveChatLink":"https://chat.wellytalk.com/MDE5ZjVlMzktNmEzMy03YWE4LWI3ZTUtMDQwOTQ0ZTAwNTEyfDJiMjZkNzlhOWU1NmJiMDJiZWEzMDI1YTcyNWJmNzVlYWVjN2JlYzQxZjIyYWRjZWFhNjJlNzFkZWZiMDIxZTg=",
	version: 'v2.0.1'
};

if (process.env.NODE_ENV == 'development') {
	//开发
	// siteinfo.apiUrl = "http://localhost:8282";
	// siteinfo.payUrl = "http://192.168.1.32:9010"; //支付中心
	// siteinfo.apiUrl = "http://m.1x2mmm.net/api";
	// siteinfo.apiUrl = "http://m.onex2.com/api";
	// siteinfo.imgUrl = "http://m.1x2mmm.net/img"; //java后端图片前缀
	siteinfo.payUrl = "http://payapi.1x2mmm.net";
} else {
	//测试环境
	// siteinfo.payUrl = "http://payapi.1x2mmm.net";
	// 测试环境在线客服链接
	siteinfo.liveChatLink = 'https://chat.wellytalk.com/MDE5ZjVlMzktNmEzMy03YWE4LWI3ZTUtMDQwOTQ0ZTAwNTEyfDJiMjZkNzlhOWU1NmJiMDJiZWEzMDI1YTcyNWJmNzVlYWVjN2JlYzQxZjIyYWRjZWFhNjJlNzFkZWZiMDIxZTg=';

}

module.exports = siteinfo;