var siteinfo = {
	"tenant_id": "10000",
	"apiUrl": "http://m.1x2mmm.net/api", //后端接口
	"imgUrl": "http://m.1x2mmm.net/img", //java后端图片前缀
	"payUrl": "http://m.okbetmm.com/payapi", //支付中心
	"wsUrl": "ws://ag.1x2mmm.net", //WebSocket服务器
	"awcImgUrl": "https://tttuat.apihub55.com", //awc图片前缀
	version: 'v2.0.1'
};

if (process.env.NODE_ENV == 'development') {
	//开发
	//siteinfo.apiUrl = "http://192.168.99.126:8282";
	// siteinfo.apiUrl = "http://localhost:8282";
	siteinfo.apiUrl = "http://m.1x2mmm.net/api";
	siteinfo.imgUrl = "http://m.1x2mmm.net/img"; //java后端图片前缀
	// siteinfo.wsUrl = "ws://192.168.99.126:8082";//开发环境WebSocket服务器
	siteinfo.payUrl = "http://192.168.99.125:9010";
	siteinfo.awcImgUrl = "https://tttuat.apihub55.com"; //awc图片前缀

} else {
	//正式环境默认

}

module.exports = siteinfo;