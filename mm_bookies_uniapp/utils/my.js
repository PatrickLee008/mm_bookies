import http from './http'
import i18n from '../locale/i18n.js'
//const AUTH_TOKEN = "Authorization";
import siteinfo from '@/siteinfo'
http.setBaseUrl(siteinfo.apiUrl);

http.beforeResponseFilter = function(res) {
	//X-Auth-Token
	/*
    if (res.header) {
        var respXAuthToken = res.header[AUTH_TOKEN.toLocaleLowerCase()];
        if (respXAuthToken) {
            uni.setStorageSync(AUTH_TOKEN, respXAuthToken);
            http.header[AUTH_TOKEN] = respXAuthToken;
        }
    }*/
	if (res.statusCode == 401) {
		uni.showToast({
			title: i18n.t('Login Session Expired'),
			image: '../../static/icon/error.png',
			duration: 2000
		})
		uni.removeStorageSync("Authorization");
		uni.removeStorageSync("isLogin");
		uni.removeStorageSync("mix_slip");
		setTimeout(function() {
			uni.reLaunch({
				url: '/pages/match/home'
				// url: '../login/login'
			})
		}, 2000)

	}
	return res;
}


let my = {
	'http': http,
}

export default my