export default {
	phoneNumber: /^(1[3-9]\d{9}$)/,
	email: /^[a-zA-Z0-9_-]+@[a-zA-Z0-9_-]+(\.[a-zA-Z0-9_-]+)+$/,
	password: /^\w{8,20}$/,
	nickName: /^[a-zA-Z\u4E00-\u9FA5][a-zA-Z0-9_\u4E00-\u9FA5]{1,20}$/,
	captcha: /^[\d]{6}$/
}     
