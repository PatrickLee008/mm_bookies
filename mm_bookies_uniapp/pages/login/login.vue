<template>
	<view>
		<!-- from tangjq--- 启动界面 -->
		<view class="splash-screen" v-if="showSplash">
			<!-- Skip 按钮 -->
			<view class="skip-button" @click="closeSplash">
				<text class="skip-text">skip {{ splashCountdown }}</text>
			</view>

			<!-- 标题图片 -->
			<view class="splash-title-container">
				<image class="splash-title-image" src="../../figma/login/title.png" mode="widthFix"></image>
			</view>

			<!-- 主体图片 -->
			<view class="splash-body-container">
				<image class="splash-body-image" src="../../figma/login/skip_body.png" mode="widthFix"></image>
			</view>
		</view>

		<!-- 原有登录页面 -->
		<view class="login-container" v-show="!showSplash">
			<!-- 标题图片 -->
			<view class="login-title-container">
				<image class="login-title-image" src="../../figma/login/title.png" mode="widthFix"></image>
			</view>

			<!-- 广告区域 -->
			<view class="ad-container">
				<image class="ad-image" src="../../figma/login/login_ad.png" mode="widthFix"></image>
			</view>

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
					<input class="input-field" :class="{'input-error': passwordError}" v-model="loginInfo.password" type="password" placeholder-class="input-placeholder" placeholder="Please enter your password" maxlength="32" @blur="handlePasswordBlur" @input="handlePasswordBlur" />
					<view class="error-message" v-if="passwordError">
						{{$t("L_password_limit")}}
					</view>
				</view>

				<!-- Remember Me -->
				<view class="remember-row">
					<text class="remember-text">Remember me</text>
					<view class="custom-switch" @click="toggleRememberMe">
						<view class="switch-dot" :class="{'switch-dot-active': loginInfo.rememberMe}"></view>
					</view>
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

			<!-- Contact Support -->
			<view class="contact-support">
				<text class="contact-text">Contact Support</text>
				<view class="social-icons">
					<view class="social-icon facebook-icon">
						<image class="icon-image" src="../../figma/login/facebook.png" mode="aspectFit"></image>
					</view>
					<view class="social-icon call-icon">
						<image class="icon-image" src="../../figma/login/call.png" mode="aspectFit"></image>
					</view>
					<view class="social-icon telegram-icon">
						<image class="icon-image" src="../../figma/login/telegram‌.png" mode="aspectFit"></image>
					</view>
				</view>
			</view>

			<!-- Version Info -->
			<view class="version-info">{{version}}</view>
		</view>
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
					account: '0955555555',
					password: 'Aa123456',
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
				// from tangjq--- 启动界面相关数据
				showSplash: true,
				splashCountdown: 5,
				splashTimer: null
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
			// from tangjq--- 启动启动界面倒计时
			this.checkShouldShowSplash()
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
			// from tangjq--- 启动界面相关方法
			startSplashTimer() {
				this.splashTimer = setInterval(() => {
					this.splashCountdown--
					if (this.splashCountdown <= 0) {
						this.closeSplash()
					}
				}, 1000)
			},
			closeSplash() {
				if (this.splashTimer) {
					clearInterval(this.splashTimer)
					this.splashTimer = null
				}
				this.showSplash = false

				// from tangjq--- 保存本次启动页面关闭的时间戳
				const currentTime = new Date().getTime()
				uni.setStorageSync('splash_last_shown_time', currentTime)
			},
			// from tangjq--- 检查是否应该显示启动页面（5分钟内不重复显示）
			checkShouldShowSplash() {
				const lastShownTime = uni.getStorageSync("splash_last_shown_time")
				const currentTime = new Date().getTime()
				const FIVE_MINUTES = 5 * 60 * 1000 // from tangjq--- 5分钟 = 300000毫秒

				// from tangjq--- 如果有上次显示时间，且距离当前时间不超过5分钟，则跳过启动页面
				if (lastShownTime && (currentTime - lastShownTime < FIVE_MINUTES)) {
					this.showSplash = false
				} else {
					// from tangjq--- 否则显示启动页面，并启动倒计时
					this.showSplash = true
					this.startSplashTimer()
				}
			},
			toggleRememberMe() {
				this.loginInfo.rememberMe = !this.loginInfo.rememberMe
			}
		},
		// from tangjq--- 页面销毁时清理定时器
		beforeDestroy() {
			if (this.splashTimer) {
				clearInterval(this.splashTimer)
				this.splashTimer = null
			}
		}
	}
</script>
<style lang="scss">
	/* from tangjq--- 启动界面样式 */
	.splash-screen {
		position: fixed;
		top: 0;
		left: 0;
		width: 100vw;
		height: 100vh;
		background: linear-gradient(180deg, #28454a 0%, #274850 100%);
		z-index: 9999;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: flex-start;
		overflow: hidden;
	}

	.skip-button {
		position: absolute;
		top: 40rpx;
		right: 40rpx;
		width: 180rpx;
		height: 60rpx;
		background-color: #2A6268;
		border-radius: 30rpx;
		display: flex;
		justify-content: center;
		align-items: center;
		z-index: 10000;
	}

	.skip-text {
		color: #FFFFFF;
		font-size: 28rpx;
		font-weight: 500;
	}

	.splash-title-container {
		margin-top: 180rpx;
		display: flex;
		flex-direction: column;
		align-items: center;
		width: 100%;
	}

	.splash-title-image {
		width: 70%;
		height: auto;
	}

	.splash-subtitle {
		margin-top: 20rpx;
		color: rgba(255, 255, 255, 0.9);
		font-size: 28rpx;
		letter-spacing: 2rpx;
	}

	.splash-body-container {
		flex: 1;
		width: 100%;
		display: flex;
		align-items: center;
		justify-content: center;
		padding: 0;
	}

	.splash-body-image {
		width: 100%;
		height: auto;
	}

	/* 原有登录页面样式 */
	.login-container {
		min-height: 100vh;
		background: linear-gradient(180deg, #28454a 0%, #274850 100%);
		display: flex;
		flex-direction: column;
		align-items: center;
		padding: 0 30rpx;
		box-sizing: border-box;
	}

	/* 标题区域 */
	.login-title-container {
		display: flex;
		flex-direction: column;
		align-items: center;
		width: 100%;
		margin-top: 115rpx;
		margin-bottom: 60rpx;
	}

	.login-title-image {
		width: 75%;
		height: auto;
	}

	.login-subtitle {
		margin-top: 10rpx;
		color: rgba(255, 255, 255, 0.9);
		font-size: 24rpx;
		letter-spacing: 2rpx;
	}

	/* 广告区域 */
	.ad-container {
		width: 800rpx;
		margin-bottom: 90rpx;
		padding: 0 55rpx;
		margin-top: 30rpx;
	}

	.ad-image {
		width: 100%;
		height: auto;
		border-radius: 32rpx;
	}

	/* 表单区域 */
	.login-form {
		width: 100%;
		margin-bottom: 30rpx;
	}

	.welcome-text {
		font-size: 28rpx;
		font-weight: 600;
		color: #ffffff;
		text-align: center;
		margin-bottom: 30rpx;
	}

	.input-wrapper {
		position: relative;
		margin-bottom: 30rpx;
	}

	.input-field {
		height: 85rpx;
		background-color: rgba(105, 145, 149, 0.6);
		border: none;
		border-radius: 20rpx;
		padding: 0 40rpx;
		font-size: 28rpx;
		color: #ffffff;
		box-sizing: border-box;
		text-align: center;
		font-style: italic;
	}

	.input-placeholder {
		color: #103C42;
		text-align: center;
		font-style: italic;
		font-size: 24rpx;
	}

	.input-error {
		border: 2rpx solid #e54d42;
	}

	.error-message {
		position: absolute;
		bottom: -25rpx;
		left: 20rpx;
		color: #ff6b6b;
		font-size: 22rpx;
	}

	.remember-row {
		display: flex;
		justify-content: flex-start;
		align-items: center;
		margin-bottom: 25rpx;
		padding: 0 10rpx;
	}

	.remember-text {
		font-size: 24rpx;
		font-weight: 400;
		color: #ffffff;
		font-style: italic;
		margin-right: auto;
	}

	/* from tangjq--- 自定义圆形复选框 */
	.custom-switch {
		width: 40rpx;
		height: 40rpx;
		border: 3rpx solid rgba(255, 255, 255, 0.6);
		border-radius: 50%;
		position: relative;
		display: flex;
		justify-content: center;
		align-items: center;
		transition: border-color 0.3s;
	}

	.custom-switch:active {
		opacity: 0.8;
	}

	.switch-dot {
		width: 0;
		height: 0;
		background-color: #50C8CE;
		border-radius: 50%;
		transition: width 0.2s, height 0.2s;
	}

	.switch-dot-active {
		width: 24rpx;
		height: 24rpx;
	}

	.login-btn {
		height: 70rpx;
		background-color: #ffffff;
		border-radius: 25rpx;
		display: flex;
		justify-content: center;
		align-items: center;
		font-size: 32rpx;
		font-weight: 600;
		color: #2A5F63;
		margin-bottom: 30rpx;
		box-shadow: 0 4rpx 12rpx rgba(0, 0, 0, 0.15);
	}

	.login-btn:active {
		opacity: 0.9;
		transform: scale(0.98);
	}

	.register-link {
		text-align: center;
		font-size: 24rpx;
	}

	.register-text {
		color: rgba(255, 255, 255, 0.9);
		font-style: italic;
		font-weight: 400;
	}

	.register-link-text {
		color: #50C8CE;
		text-decoration: underline;
		font-weight: 600;
	}

	/* Contact Support 区域 */
	.contact-support {
		display: flex;
		flex-direction: column;
		align-items: center;
		margin-top: 50rpx;
		margin-bottom: 30rpx;
	}

	.contact-text {
		color: #ffffff;
		font-size: 24rpx;
		font-weight: 600;
		margin-bottom: 30rpx;
	}

	.social-icons {
		display: flex;
		justify-content: center;
		align-items: center;
		gap: 40rpx;
	}

	.social-icon {
		width: 80rpx;
		height: 80rpx;
		display: flex;
		justify-content: center;
		align-items: center;
	}

	.icon-image {
		width: 80rpx;
		height: 80rpx;
	}

	.version-info {
		margin-top: auto;
		font-size: 22rpx;
		color: rgba(255, 255, 255, 0.5);
		text-align: center;
	}
</style>