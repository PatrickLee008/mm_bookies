<template>
	<view class="login-container">
		<!-- App Title -->
		<view class="app-title">MM Bookies</view>

		<!-- Login Form -->
		<view class="login-form">
			<!-- Welcome Text -->
			<view class="welcome-text">Welcome back</view>
			<!-- Phone Input Field -->
			<view class="input-wrapper">
				<input class="input-field" :class="{'input-error': phoneError}" type="number" placeholder-class="input-placeholder" v-model="loginInfo.account" placeholder="Please enter phone number" maxlength="11" @blur="handlePhoneBlur" @input="handlePhoneBlur" />
				<view class="error-message" v-if="phoneError">
					{{$t("L_input_number_limit")}}
				</view>
			</view>

			<!-- Password Input Field -->
			<view class="input-wrapper">
				<!-- :type="showPassword ? 'text' : 'password'" -->
				<input class="input-field" :class="{'input-error': passwordError}" v-model="loginInfo.password" type="password" placeholder-class="input-placeholder" placeholder="Please enter your password" maxlength="32" @blur="handlePasswordBlur" @input="handlePasswordBlur" />
				<view class="error-message" v-if="passwordError">
					{{$t("L_password_limit")}}
				</view>
			</view>

			<!-- 验证码 - Commented out as requested -->
			<!-- <view class="cu-form-group input-wrapper"
				:class="{'input-focused': isCaptchaFocused, 'input-error': captchaError}">
				<view class="input-label" :class="{'label-focused': isCaptchaFocused || !!Captcha}">
					{{language.enter_captcha}}
				</view>
				<view class="input-container">
					<view class="icon-container">
						<text class="icon-captcha"></text>
					</view>
					<input class="info-input" type="text" v-model="Captcha"
						:placeholder-class="isCaptchaFocused ? 'placeholder-hidden' : ''" maxlength="4"
						@focus="isCaptchaFocused = true" @blur="handleCaptchaBlur" @input="handleCaptchaBlur" />
					<view class="captcha-container" style="">
						<canvas class="captcha" style="" canvas-id="canvas"></canvas>
					</view>
					<view style="height: 80%;width:1px ;background-color: rgba(0, 0, 0, 0.12);"></view>
					<view
						class="cuIcon-refresh mycolor-primary text-bold myfont-20px width-44px flex-row1 justify-center"
						@click="updateImageCode"></view>
				</view>
				<view class="error-message" v-if="captchaError">
					{{$t("L_captcha_limit")}}
				</view>
			</view> -->

			<!-- Remember Me -->
			<view class="remember-row">
				<text class="remember-text">Remember me</text>
				<switch class="remember-switch" :checked="loginInfo.rememberMe" @change="switchChange" color="#2A6268" />
			</view>

			<!-- Login Button -->
			<view class="login-btn" @click="login()">
				<text :class="loadding"></text>
				<text>Login</text>
			</view>

			<!-- Register Link -->
			<view class="register-link">
				<text class="register-text">Dont have an account? </text>
				<text class="register-link-text" @click="toRegister()">Register</text>
				<text class="register-text"> now for free.</text>
			</view>
		</view>

		<!-- Version Info -->
		<view class="version-info">{{version}}</view>
	</view>
</template>

<script>
	import config from '../../utils/config.js'
	import CryptoJS from 'crypto-js';

	// 验证码相关导入 - Commented out as requested
	// import {
	// 	Mcaptcha
	// } from '@/utils/mcaptcha'

	const key = CryptoJS.enc.Utf8.parse('innwa'.padEnd(16, '\0'));
	const iv = CryptoJS.enc.Utf8.parse('1234567890123456'); // 初始向量，16字节

	function encrypt(text) {
		const encrypted = CryptoJS.AES.encrypt(text, key, {
			iv: iv,
			mode: CryptoJS.mode.CBC,
			padding: CryptoJS.pad.Pkcs7
		});
		return encrypted.toString();
	}


	export default {
		components: {},
		data() {
			return {
				// loginDisabled: false,
				loadding: '',
				loginInfo: {
					account: '',
					password: '',
					rememberMe: true,
				},

				intervalID: '',
				version: uni.getStorageSync("version"),
				language: config.language,

				// 验证相关
				// Captcha: '', // Commented out as requested
				isPhoneFocused: false,
				isPasswordFocused: false,
				// isCaptchaFocused: false, // Commented out as requested

				phoneError: false,
				passwordError: false,
				// captchaError: false, // Commented out as requested

				showPassword: false,
				show_x: false,
			};
		},
		computed: {
			loginDisabled() {
				// 移除验证码验证
				if ((!this.loginInfo.account || !this.loginInfo.password) || (this.phoneError || this.passwordError)) {
					return true
				}
				return false
			}
		},
		watch: {
			value(newVal) {
				this.phoneNumber = newVal;
			},
			phoneNumber(newVal) {
				this.$emit('input', newVal);
			}
		},

		mounted() {
			this.reloadUser()
			uni.removeStorageSync('login_success')
		},
		methods: {
			// 创建一个通用的验证处理函数
			validateField(fieldType) {
				// 设置焦点状态
				this[`is${fieldType}Focused`] = false;
				// 定义不同字段的验证规则
				const validationRules = {
					Phone: {
						value: this.loginInfo.account,
						isValid: () => this.loginInfo.account && this.loginInfo.account.startsWith('09') && this
							.loginInfo.account.length >= 9
					},
					Password: {
						value: this.loginInfo.password,
						isValid: () => this.loginInfo.password && this.loginInfo.password.length >= 8
					},
					// Captcha验证规则 - Commented out as requested
					// Captcha: {
					// 	value: this.Captcha,
					// 	isValid: () => this.Captcha && this.Captcha.length >= 4
					// }
				};
				// 获取当前字段的规则
				const rule = validationRules[fieldType];
				if (rule) {
					// 执行验证并设置错误状态
					this[`${fieldType.toLowerCase()}Error`] = !rule.value || !rule.isValid();
				}
			},
			// 调用方式
			handlePhoneBlur() {
				this.validateField('Phone');
			},
			handlePasswordBlur() {
				this.validateField('Password');
			},
			// handleCaptchaBlur() { // Commented out as requested
			// 	this.validateField('Captcha');
			// },
			togglePasswordVisibility() {
				this.showPassword = !this.showPassword;
			},

			toAI() {
				uni.navigateTo({
					url: '/pages/deepseek/index',
					animationType: 'slide-in-right',
					animationDuration: 100
				})
			},
			downloadApp() {
				var u = navigator.userAgent;
				var isAndroid = u.indexOf('Android') > -1 || u.indexOf('Adr') > -1; //android终端
				var isiOS = !!u.match(/\(i[^;]+;( U;)? CPU.+Mac OS X/); //ios终端

				var url = '';
				if (isAndroid) {
					url = 'http://dl.innwabet.net/android/InnwaBet_Android_New.apk'
				} else if (isiOS) {
					url = 'http://dl.innwabet.net/ios/InnwaBet_New.mobileconfig'
				} else {
					url = 'http://dl.innwabet.net/android/InnwaBet_Android_New.apk'
				}
				// #ifdef APP-PLUS
				plus.runtime.openURL(url) //这里默认使用外部浏览器打开而不是内部web-view组件打开
				// #endif
				// #ifdef H5
				window.open(url)
				// #endif
			},

			toRegister() {
				uni.navigateTo({
					url: "./register"
				})
			},
			goto(url) {
				uni.reLaunch({
					url: url,
				})
			},
			switchChange(e) {
				this.loginInfo.rememberMe = e.target.value
			},
			reloadUser() {
				var _this = this;
				//缓存
				var loginInfo = uni.getStorageSync('loginInfo');
				//有缓存就赋值给文本
				if (loginInfo.account && loginInfo.password) {
					_this.loginInfo = loginInfo;
				}
			},
			login() {
				if (this.$toolbox.click_too_fast(2)) return
				var _this = this;

				// 验证码验证 - Commented out as requested
				// let validate = this.mcaptcha.validate(this.Captcha)
				// let testing = uni.getStorageSync('testing')
				// if (!validate && !testing) {
				// 	uni.showModal({
				// 		title: 'Warning',
				// 		content: 'captcha not match',
				// 		showCancel: false,
				// 		confirmText: 'OK',
				// 	})
				// 	return
				// }

				_this.loadding = 'cuIcon-loading2 cuIconfont-spin';
				// _this.loginDisabled = true;

				const account = this.loginInfo.account;
				const password = this.loginInfo.password;
				const timestamp = new Date().getTime().toString();
				const params = JSON.stringify({
					account,
					password,
					timestamp
				});
				const encryptedParams = encrypt(params);
				var para = {
					encryptedParams: encryptedParams
				}

				_this.$http.post('/app_user/login', para, (res) => {
					_this.loadding = '';
					if (res.statusCode == 200) {
						// if (_this.loginInfo.rememberMe) {
						// 	uni.setStorageSync('loginInfo', _this.loginInfo);
						// } else {
						// 	uni.removeStorageSync('loginInfo');
						// };
						uni.setStorageSync('Authorization', res.data.token);
						uni.redirectTo({
							url: '../match/home'
						});
						uni.setStorageSync('login_success', true)
						return
					} else if (res.statusCode == 400) {
						uni.showToast({
							title: _this.$t('wrong_password'),
							image: '../../static/icon/error.png',
							duration: 2000,
						});
					} else {
						uni.showModal({
							title: 'Tips',
							content: _this.$t(res.data.message),
							showCancel: false,
							confirmText: 'ok',
							success: function(res) {}
						});
						// _this.loginDisabled = false;
					}
					// 验证码刷新 - Commented out as requested
					// this.Captcha = ''
					// this.updateImageCode()
				})
			},

			// 验证码相关方法 - Commented out as requested
			// onReady() {
			// 	this.mcaptcha = new Mcaptcha({
			// 		el: 'canvas',
			// 		width: 90,
			// 		height: 45,
			// 		createCodeImg: ""
			// 	});
			// },
			// // 刷新验证码
			// updateImageCode() {
			// 	this.mcaptcha.refresh()
			// },
		}
	}
</script>
<style lang="scss">
	.login-container {
		min-height: 100vh;
		background-color: $color-primary;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: space-between;
		padding: 0 40rpx;
		box-sizing: border-box;
	}

	.app-title {
		margin-top: 8vh;
		font-size: 72rpx;
		font-weight: bold;
		color: #ffffff;
		text-align: center;
	}

	.welcome-text {
		font-size: 28rpx;
		font-weight: 600;
		color: #ffffff;
		text-align: center;
		margin-bottom: 6px;
	}

	.login-form {
		width: 100%;
		max-width: 600rpx;
		padding-bottom: 10vh;
	}

	.input-wrapper {
		position: relative;
	}

	.input-field {
		width: 100%;
		height: 80rpx;
		background-color: #699195;
		border: none;
		border-radius: 20rpx;
		padding: 0 40rpx;
		font-size: 28rpx;
		color: #ffffff;
		box-sizing: border-box;
		text-align: center;
		margin-bottom: 50rpx;
	}

	.input-placeholder {
		color: #204b4f;
		text-align: center;
		font-style: italic;
		font-size: 12px;
	}

	.input-error {
		border: 2rpx solid #e54d42;
	}

	.error-message {
		position: absolute;
		bottom: -20px;
		// left: 20rpx;
		color: #ff6b6b;
		font-size: 24rpx;
	}

	.remember-row {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 20rpx;
		padding: 0 10rpx;
	}

	.remember-text {
		font-size: 24rpx;
		color: #ffffff;
		font-style: italic;
	}

	.remember-switch {
		transform: scale(0.8);
	}

	.login-btn {
		width: 100%;
		height: 90rpx;
		background-color: #ffffff;
		border-radius: 45rpx;
		display: flex;
		justify-content: center;
		align-items: center;
		font-size: 32rpx;
		font-weight: 600;
		color: $color-primary;
		margin-bottom: 40rpx;
	}

	.login-btn:active {
		opacity: 0.9;
	}

	.register-link {
		text-align: center;
		font-size: 24rpx;
		font-style: italic;
	}

	.register-text {
		color: rgba(255, 255, 255, 0.8);
	}

	.register-link-text {
		color: $color-lprimary;
		text-decoration: underline;
		font-weight: 500;
	}

	.version-info {
		position: fixed;
		right: 20rpx;
		bottom: 20rpx;
		font-size: 22rpx;
		color: rgba(255, 255, 255, 0.5);
	}
</style>