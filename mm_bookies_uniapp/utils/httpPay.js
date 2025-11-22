let http = {
    'setBaseUrl': (url) => {
        if (url.charAt(url.length - 1) === "/") {
            url = url.substr(0, url.length - 1)
        }
        http.baseUrl = url;
    },
	'setPayUrl': (url) => {
	    if (url.charAt(url.length - 1) === "/") {
	        url = url.substr(0, url.length - 1)
	    }
	    http.payUrl = url;
	},
    'header': {},
    'beforeRequestFilter': (config) => { return config },
    'beforeResponseFilter': (res) => { return res },
    'afterResponseFilter': (successResult) => { },
    'get': get,
    'post': post,
    'request': request,
    'uploadFile': uploadFile,
    'downloadFile': downloadFile,
}
import siteinfo from '@/siteinfo'
http.setBaseUrl(siteinfo.payUrl);

function init(con) {
    //url
    let url = http.baseUrl;
    if (url && con.url && !con.url.match(/^(http|https):\/\/([\w.]+\/?)\S*$/)) {
        if (con.url.charAt(0) !== "/") {
            con.url = "/" + con.url;
        }
        con.url = url.concat(con.url);
    }
    //header
	con.header = {"Authorization":uni.getStorageSync("Authorization")};
	/*
    if (http.header != undefined && http.header != null) {
        if (!con.header) {
            con.header = http.header;
        } else {
            Object.keys(http.header).forEach(function (key) {
                con.header[key] = http.header[key]
            });
        }
    }
	*/
}
 
function request(con) {
    init(con);
    let config = {
        url: con.url ? con.url : http.baseUrl,
        data: con.data,
        header: con.header,
        method: con.method ? con.method : 'GET',
        dataType: con.dataType ? con.dataType : 'json',
        responseType: con.responseType ? con.responseType : 'text',
        success: con.success ? (res) => {
            http.afterResponseFilter(con.success(http.beforeResponseFilter(res)));
        } : null,
        fail: con.fail ? (res) => {
            con.fail(res);
        } : null,
        complete: con.complete ? (res) => {
            con.complete(res);
        } : null
    }
    return uni.request(http.beforeRequestFilter(config));
}
 
function get(url, con, success) {
    let conf = {};
    if (con && typeof con == 'function') {
        if (success && typeof success == 'object') {
            conf = success;
        }
        conf.success = con
    }else{
        if (con && typeof con == 'object') {
            conf = con;
        }
        conf.success = success;
    }
 
    if (url) {
        conf.url = url
    }
    conf.method = "GET";
    return request(conf);
}
 
function post(url, data, con, success) {
    let conf = {};
    if (con && typeof con == 'function') {
        if (success && typeof success == 'object') {
            conf = success
        }
        conf.success = con;
    } else {
        if (con && typeof con == 'object') {
            conf = con;
        }
        conf.success = success;
    }
    if (url) {
        conf.url = url
    }
    if (data) {
        conf.data = data
    }
    conf.method = "POST";
	//转成字符串
	conf.data = JSON.stringify(conf.data);
    return request(conf);
}
 
function uploadFile(con) {
    init(con);
 
    let config = {
        url: con.url ? con.url : http.baseUrl,
        files: con.files,
        filesType: con.filesType,
        filePath: con.filePath,
        name: con.name,
        header: con.header,
        formData: con.formData,
        success: con.success ? (res) => {
            http.afterResponseFilter(con.success(http.beforeResponseFilter(res)));
        } : null,
        fail: con.fail ? (res) => {
            con.fail(res);
        } : null,
        complete: con.complete ? (res) => {
            con.complete(res);
        } : null
    }
    return uni.uploadFile(http.beforeRequestFilter(config));
}
 
function downloadFile(con) {
    init(con);
 
    let config = {
        url: con.url ? con.url : http.baseUrl,
        header: con.header,
        success: con.success ? (res) => {
            http.afterResponseFilter(con.success(http.beforeResponseFilter(res)));
        } : null,
        fail: con.fail ? (res) => {
            con.fail(res);
        } : null,
        complete: con.complete ? (res) => {
            con.complete(res);
        } : null
    }
    return uni.downloadFile(http.beforeRequestFilter(config));
}

////////////////////////////////////////////支付中学接口
function initPay(con) {
    let url = http.payUrl;
    if (url && con.url && !con.url.match(/^(http|https):\/\/([\w.]+\/?)\S*$/)) {
        if (con.url.charAt(0) !== "/") {
            con.url = "/" + con.url;
        }
        con.url = url.concat(con.url);
    }
	con.header = {"Authorization":uni.getStorageSync("Authorization")};
}
function postPay(url, data, con, success) {
     let conf = {};
     if (con && typeof con == 'function') {
         if (success && typeof success == 'object') {
             conf = success
         }
         conf.success = con;
     } else {
         if (con && typeof con == 'object') {
             conf = con;
         }
         conf.success = success;
     }
     if (url) {
         conf.url = url
     }
     if (data) {
         conf.data = data
     }
     conf.method = "POST";
     return request(conf);
}

//计算当前时间到目标时间的倒计时毫秒数
function getCountdownMilliseconds(targetTimeStr) {
	// 解析目标时间字符串为 Date 对象
	const targetDate = new Date(targetTimeStr);

	// 检查目标时间是否有效
	if (isNaN(targetDate.getTime())) {
		throw new Error('无效的目标时间字符串');
	}

	// 获取当前时间的毫秒数
	const now = Date.now();

	// 计算差值
	const difference = targetDate - now;

	// 如果目标时间已过，返回 0
	return difference > 0 ? difference : 0;
}

export default {
	httpPay:http
}
