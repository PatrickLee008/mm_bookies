// ============================================================
// 站点开关：mmbookies / shwegoal / phoe_wa_maung
// 与 uni.scss 中的 $site 同名同步。
// 切换站点只需改这里 siteinfo.site 与 uni.scss 的 $site 两处，
// 各站点的请求地址会随 site 自动切换，无需再手动注释。
// ============================================================
var siteinfo = {
	"site": "mmbookies",
	// "site": "shwegoal",
	// "site": "phoe_wa_maung",
	"version": 'v1.0.7',
	"tenant_id": "10000",
	"awcImgUrl": "https://tttuat.apihub55.com", //awc图片前缀（各站点共用）
};

// 各站点地址表：apiUrl/imgUrl/wsUrl 随站点切换
var SITES = {
	mmbookies: {
		"apiUrl": "http://m.mmbookies.com/api", //后端接口
		"imgUrl": "http://m.mmbookies.com/img", //java后端图片前缀中心
		"wsUrl": "wss://ag.mmbookies.com", //WebSocket服务器
	},
	shwegoal: {
		"apiUrl": "https://m.shwegoal.net/api",
		"imgUrl": "https://m.shwegoal.net/img",
		"wsUrl": "wss://ag.shwegoal.net",
	},
	phoe_wa_maung: {
		// 暂无独立地址，复用 mmbookies 的地址
		"apiUrl": "http://m.pwmaung.com/api",
		"imgUrl": "http://m.pwmaung.com/img",
		"wsUrl": "wss://ag.pwmaung.com",
	}
};
// 应用所选站点的基础地址（未知站点回退 mmbookies）
Object.assign(siteinfo, SITES[siteinfo.site] || SITES.mmbookies);
// 支付中心、在线客服链接（与站点无关，按环境覆盖）
siteinfo.payUrl = "https://pay.okbetmm.com"; //支付中心
siteinfo.liveChatLink =
	"https://chat.wellytalk.com/MDE5ZjVlMzktNmEzMy03YWE4LWI3ZTUtMDQwOTQ0ZTAwNTEyfDJiMjZkNzlhOWU1NmJiMDJiZWEzMDI1YTcyNWJmNzVlYWVjN2JlYzQxZjIyYWRjZWFhNjJlNzFkZWZiMDIxZTg=";

if (process.env.NODE_ENV == 'development') {
	//开发：仅覆盖支付中心差异
	// siteinfo.apiUrl = "http://localhost:8282";
	// siteinfo.payUrl = "http://192.168.1.32:9010"; //支付中心
	// siteinfo.apiUrl = "http://m.1x2mmm.net/api";
	// siteinfo.apiUrl = "http://m.onex2.com/api";
	// siteinfo.imgUrl = "http://m.1x2mmm.net/img"; //java后端图片前缀
	// siteinfo.payUrl = "http://payapi.1x2mmm.net";
} else {
	//测试环境在线客服链接（与正式相同，保留原分支语义）
	// siteinfo.payUrl = "http://payapi.1x2mmm.net";
	// siteinfo.liveChatLink =
	// 	'https://chat.wellytalk.com/MDE5ZjVlMzktNmEzMy03YWE4LWI3ZTUtMDQwOTQ0ZTAwNTEyfDJiMjZkNzlhOWU1NmJiMDJiZWEzMDI1YTcyNWJmNzVlYWVjN2JlYzQxZjIyYWRjZWFhNjJlNzFkZWZiMDIxZTg=';
}

module.exports = siteinfo;