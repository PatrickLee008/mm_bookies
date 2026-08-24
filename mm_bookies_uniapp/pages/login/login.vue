<template>
	<view>
		<global-notice ref="globalNotice"></global-notice>
		<!-- from tangjq--- 开屏广告（由后端 /splash_screen/get_active 控制是否启用与时长） -->
		<view class="splash-screen theme-bg-no-header" v-if="showSplash">
			<!-- Skip 按钮（由 enable_skip_button 控制） -->
			<view class="skip-button" @click="closeSplash" v-if="enableSkipButton">
				<text class="skip-text">{{ $t('skip') }} {{ splashCountdown }}</text>
			</view>

			<!-- 开屏广告图片 -->
			<image class="splash-ad-image" :src="splashImageUrl" mode="aspectFill"></image>

			<!-- 动作按钮（由 enable_action_button 控制） -->
			<view class="splash-action-button" v-if="enableActionButton && actionButtonLabel" @click="onSplashAction">
				<text class="splash-action-text">{{ actionButtonLabel }}</text>
			</view>
		</view>

		<!-- 原有登录页面 -->
		<view class="login-container theme-bg-no-header" v-show="!showSplash">
			<!-- 语言切换按钮 -->
			<view class="lang-switch" @click="openLangModal">
				<image class="lang-switch-icon" src="/static/icon/ucenter/language.png" mode="aspectFit"></image>
				<text class="lang-switch-text">{{ currentLangLabel }}</text>
			</view>

			<!-- 语言切换弹窗 -->
			<view class="lang-modal-mask" v-if="showLangModal" @click="showLangModal = false">
				<view class="lang-modal" @click.stop="">
					<view class="lang-modal-title">{{ $t('change_language') }}</view>
					<view class="lang-option" v-for="opt in langOptions" :key="opt.value"
						@click="selectLang(opt.value)">
						<text class="lang-option-label">{{ opt.label }}</text>
						<view class="lang-radio" :class="{ 'lang-radio-on': currentLang === opt.value }">
							<view class="lang-radio-dot" v-if="currentLang === opt.value"></view>
						</view>
					</view>
				</view>
			</view>

			<view class="height-8vh" v-if="!advertisements.length"></view>

			<!-- 标题图片 -->
			<view class="login-title-container">
				<theme-logo variant="page" height="var(--theme-home-logo-height)" class="login-title-image"></theme-logo>
				<view class="login-subtitle"></view>
			</view>

			<!-- 广告区域 -->
			<view class="ad-container" v-if="!showCaptchaView && advertisements.length">
				<swiper class="ad-swiper" :circular="advertisements.length > 1" :autoplay="advertisements.length > 1"
					interval="3500" duration="500" :indicator-dots="advertisements.length > 1">
					<swiper-item v-for="(ad, index) in advertisements" :key="index" @click="handleAdClick(ad)">
						<image class="ad-image" :src="getAdvertisementImage(ad)" mode="scaleToFill"></image>
					</swiper-item>
				</swiper>
			</view>
			<view class="height-8vh" v-else-if="!showCaptchaView"></view>

			<!-- Login Form -->
			<view class="login-form" v-if="!showCaptchaView">
				<!-- Welcome Text -->
				<view class="welcome-text">{{ $t('Welcome Back') }}</view>

				<!-- Phone Input Field -->
				<view class="input-wrapper">
					<input class="input-field" :class="{'input-error': phoneError}" type="number"
						placeholder-class="input-placeholder" v-model="loginInfo.account"
						:placeholder="$t('Please Enter Username')" maxlength="11" @blur="handlePhoneBlur"
						@input="handlePhoneBlur" />
					<view class="error-message" v-if="phoneError">
						{{$t("L_input_number_limit")}}
					</view>
				</view>

				<!-- Password Input Field -->
				<view class="input-wrapper">
					<input class="input-field" :class="{'input-error': passwordError}" v-model="loginInfo.password"
						type="text" :password="!showPassword" placeholder-class="input-placeholder"
						:placeholder="$t('enter_password')" maxlength="32" @blur="handlePasswordBlur"
						@input="handlePasswordBlur" />
					<view class="password-toggle" @click="togglePasswordVisibility">
						<uni-icons :type="showPassword ? 'eye' : 'eye-slash'" size="24"
							color="rgba(255,255,255,0.8)"></uni-icons>
					</view>
					<view class="error-message" v-if="passwordError">
						{{$t("L_password_limit")}}
					</view>
				</view>

				<!-- Remember Me -->
				<view class="remember-row" @click="toggleRememberMe">
					<view class="custom-switch">
						<view class="switch-dot" :class="{'switch-dot-active': loginInfo.rememberMe}"></view>
					</view>
					<text class="remember-text">{{ $t('Remember me') }}</text>
				</view>

				<!-- Login Button -->
				<view class="login-btn" :class="{ 'login-btn-disabled': loginDisabled }" @click="handleLogin">
					<text :class="loadding"></text>
					<text>{{ $t('login') }}</text>
				</view>

				<!-- Register Link -->
				<view class="register-link">
					<text class="register-text">{{ $t("Don't have an account? ") }}</text>
					<text class="register-link-text" @click="toRegister()">{{ $t('register_button') }}</text>
					<!-- <text class="register-text">{{ $t('now for free') }}</text> -->
				</view>
			</view>

			<!-- Slider verification -->
			<view class="login-form captcha-step" v-else>
				<slider-captcha ref="loginCaptcha" :config="captchaConfig" :trigger-generate="captchaTrigger"
					:show-close="false" @verify="handleCaptchaVerify" @verify-fail="handleCaptchaVerifyFail"
					@refresh="handleCaptchaRefresh" @error="handleCaptchaError" />

				<view class="register-secondary-btn" @click="handleCaptchaBack">{{ $t('Back') }}</view>
				<view class="register-link">
					<text class="register-text">{{ $t("Don't have an account? ") }}</text>
					<text class="register-link-text" @click="toRegister">{{ $t('register_button') }}</text>
				</view>
			</view>

			<!-- Contact Support -->
			<view class="contact-support" v-if="false">
				<text class="contact-text">{{ $t('Contact service') }}</text>
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

			<!-- 客服按钮 -->
			<customer-service></customer-service>
		</view>
	</view>
</template>

<script>
	import config from '../../utils/config.js'
	import language from '../../utils/language.js'
	import siteinfo from '../../siteinfo.js'
	import CryptoJS from 'crypto-js';
	import SliderCaptcha from '@/components/SliderCaptcha.vue'
	import CustomerService from '@/components/common/customer-service.vue'

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
		components: {
			SliderCaptcha,
			CustomerService,
		},
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
				advertisements: [],
				captchaTrigger: 0,
				captchaVerified: false,
				showCaptchaView: false,
				// from tangjq--- 开屏广告相关数据（由后端配置驱动）
				showSplash: false,
				splashCountdown: 5,
				displayDuration: 5,
				splashTimer: null,
				splashImageUrl: '',
				enableSkipButton: true,
				enableActionButton: false,
				actionButtonLabel: '',
				actionButtonRoute: '',
				// 语言切换
				showLangModal: false,
				currentLang: uni.getStorageSync('language') || uni.getStorageSync('UNI_LOCALE') || 'mm',
				langOptions: [{
						value: 'mm',
						label: 'မြန်မာ'
					},
					{
						value: 'en',
						label: 'English'
					},
					{
						value: 'th',
						label: 'ภาษาไทย'
					},
					{
						value: 'cn',
						label: '中文'
					}
				]
			};
		},
		computed: {
			currentLangLabel() {
				const map = {
					mm: 'မြန်မာ',
					en: 'EN',
					th: 'ไทย',
					cn: '中文'
				}
				return map[this.currentLang] || 'EN'
			},
			loginDisabled() {
				// 移除验证码验证
				if ((!this.loginInfo.account || !this.loginInfo.password) || (this.phoneError || this.passwordError)) {
					return true
				}
				return false
			},
			captchaConfig() {
				return {
					title: this.$t('security_check'),
					description: this.$t('human_verification_description'),
					sliderText: this.$t('slide_to_verify_short'),
					successText: this.$t('verification_success'),
					canvasWidth: 300,
					canvasHeight: 202,
					sliderSize: 40,
				}
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
			this.getAdvertisements()
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
						isValid: () => this.loginInfo.password && this.loginInfo.password.length >= 5
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
			handleLogin() {
				this.handlePhoneBlur();
				this.handlePasswordBlur();
				if (this.loginDisabled) return;

				this.captchaVerified = false;
				this.showCaptchaView = true;
				this.$nextTick(() => {
					setTimeout(() => {
						this.captchaTrigger = Date.now();
						this.$refs.loginCaptcha && this.$refs.loginCaptcha.calculateDimensions();
					}, 100);
				});
			},
			handleCaptchaVerify() {
				this.captchaVerified = true;
				setTimeout(() => {
					if (this.showCaptchaView && this.captchaVerified) {
						this.login();
					}
				}, 400);
			},
			handleCaptchaVerifyFail() {
				this.captchaVerified = false;
				uni.showToast({
					title: this.$t('verify_fail'),
					icon: 'none',
				});
			},
			handleCaptchaError() {
				this.captchaVerified = false;
				uni.showToast({
					title: this.$t('error_title'),
					icon: 'none',
				});
			},
			handleCaptchaRefresh() {
				this.captchaVerified = false;
				this.captchaTrigger = Date.now();
			},
			handleCaptchaBack() {
				this.showCaptchaView = false;
				this.captchaVerified = false;
				setTimeout(() => {
					this.captchaTrigger = Date.now();
				}, 300);
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
				// 	this.$notice.show({
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

				const adl = uni.getStorageSync('default_adl');
				if (adl) para.adlink_id = adl;

				_this.$http.post('/app_user/login', para, (res) => {
					_this.loadding = '';
					if (res.statusCode == 200) {
						if (_this.loginInfo.rememberMe) {
							uni.setStorageSync('loginInfo', _this.loginInfo);
						} else {
							uni.removeStorageSync('loginInfo');
						}
						uni.setStorageSync('Authorization', res.data.token);

						// 缓存用户信息（含时区 timezone），供时区转换等工具使用
						if (res.data.data) {
							uni.setStorageSync('user_info', res.data.data);
						}

						// 通知 App 登录成功，立即建立 WebSocket 连接并刷新未读消息
						uni.$emit('user:login');

						// 登录成功后获取配置
						const app = getApp()
						if (app && app.getConfigs) {
							app.getConfigs()
						}

						uni.redirectTo({
							url: '/pages/index/index'
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
						this.$notice.show({
							title: _this.$t('tips'),
							content: _this.$t(res.data.message),
							showCancel: false,
							confirmText: _this.$t('ok'),
							success: function(res) {}
						});
						// _this.loginDisabled = false;
					}
					_this.showCaptchaView = false;
					_this.captchaVerified = false;
					setTimeout(() => {
						_this.captchaTrigger = Date.now();
					}, 300);
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
			// from tangjq--- 开屏广告相关方法
			startSplashTimer() {
				this.clearSplashTimer()
				this.splashTimer = setInterval(() => {
					this.splashCountdown--
					if (this.splashCountdown <= 0) {
						this.closeSplash()
					}
				}, 1000)
			},
			clearSplashTimer() {
				if (this.splashTimer) {
					clearInterval(this.splashTimer)
					this.splashTimer = null
				}
			},
			closeSplash() {
				this.clearSplashTimer()
				this.showSplash = false
				// 记录本次关闭时间（5分钟内不重复显示）
				uni.setStorageSync('splash_last_shown_time', new Date().getTime())
			},
			// 检查是否应显示开屏（5分钟内不重复），再向后端拉取配置
			checkShouldShowSplash() {
				const lastShownTime = uni.getStorageSync('splash_last_shown_time')
				const currentTime = new Date().getTime()
				const FIVE_MINUTES = 5 * 60 * 1000
				if (lastShownTime && (currentTime - lastShownTime < FIVE_MINUTES)) {
					this.showSplash = false
					return
				}
				this.fetchSplashConfig()
			},
			// 拉取后端开屏配置：是否启用（列表非空）、显示时长、图片、跳过/动作按钮
			fetchSplashConfig() {
				let _this = this
				const tenant_id = (siteinfo && siteinfo.tenant_id) || '10000'
				_this.$http.get('/splash_screen/get_active', {
					data: {
						tenant_id
					}
				}, (res) => {
					const ok = res.statusCode === 200 && res.data && res.data.code === 200
					const list = ok && res.data.data ? res.data.data.splash_screens : null
					if (list && list.length > 0 && list[0].image_url) {
						_this.applySplashConfig(list[0])
						_this.showSplash = true
						_this.startSplashTimer()
					} else {
						// 未配置或已禁用 → 不显示开屏，直接进入登录页
						_this.showSplash = false
					}
				}, () => {
					_this.showSplash = false
				})
			},
			applySplashConfig(cfg) {
				// 显示时长限制在 1-10 秒
				let d = parseInt(cfg.display_duration, 10)
				if (!d || d < 1) d = 5
				if (d > 10) d = 10
				this.displayDuration = d
				this.splashCountdown = d
				this.splashImageUrl = this.resolveSplashImage(cfg.image_url)
				// 后端 to_dict 已将 TINYINT 转为布尔
				this.enableSkipButton = cfg.enable_skip_button !== false
				this.enableActionButton = cfg.enable_action_button === true
				this.actionButtonLabel = cfg.action_button_label || ''
				this.actionButtonRoute = cfg.action_button_route || ''
			},
			resolveSplashImage(url) {
				if (!url) return ''
				if (/^https?:\/\//i.test(url)) return url
				let base = (siteinfo && siteinfo.imgUrl) || ''
				if (url.charAt(0) !== '/') url = '/' + url
				return base + url
			},
			onSplashAction() {
				const route = this.actionButtonRoute
				this.closeSplash()
				// 关键词路由（如 'home'）或完整路径都交给 toolbox 统一处理
				if (route) {
					this.$toolbox.navigateToPage(route)
				}
			},
			getAdvertisements() {
				this.advertisements = []
				this.$http.post('/advertisement/get_by_page', {
					platform: 'mobile',
					page: 'register',
					position: 'banner'
				}, (res) => {
					if (res.statusCode == 200 && res.data.code == 200) {
						const items = res.data.data && res.data.data.items ? res.data.data.items : []
						this.advertisements = items.filter((ad) => this.getAdvertisementImage(ad))
					}
				})
			},
			getAdvertisementImage(ad) {
				if (!ad) return ''
				return ad.image_urls && ad.image_urls.length ? ad.image_urls[0] : ad.url || ''
			},
			handleAdClick(ad) {
				if (!ad || !ad.link_url) return
				this.$toolbox.openAdvertisementLink(ad.link_url, ad.link_target)
			},
			toggleRememberMe() {
				this.loginInfo.rememberMe = !this.loginInfo.rememberMe
			},
			// from tangjq--- 语言切换
			openLangModal() {
				this.currentLang = uni.getStorageSync('language') || uni.getStorageSync('UNI_LOCALE') || 'mm'
				this.showLangModal = true
			},
			selectLang(value) {
				if (!value) value = 'mm'
				this.currentLang = value
				// 与 pages/ucenter/language.vue 保持一致：更新全局语言、缓存与 i18n
				config.language = language[value]
				uni.setStorageSync('language', value)
				uni.setStorageSync('UNI_LOCALE', value)
				uni.setLocale(value)
				this.$i18n.locale = value
				this.showLangModal = false
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
		height: var(--app-viewport-height, 100vh);
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
		min-width: 180rpx;
		height: 60rpx;
		padding: 0 5px;
		background-color: $color-primary;
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

	/* 开屏广告图片：铺满全屏 */
	.splash-ad-image {
		width: 100%;
		height: 100%;
	}

	/* 开屏动作按钮 */
	.splash-action-button {
		position: absolute;
		bottom: 120rpx;
		left: 50%;
		transform: translateX(-50%);
		min-width: 300rpx;
		height: 80rpx;
		padding: 0 40rpx;
		background-color: $color-primary;
		border-radius: 40rpx;
		display: flex;
		align-items: center;
		justify-content: center;
		z-index: 10000;
	}

	.splash-action-text {
		color: #FFFFFF;
		font-size: 30rpx;
		font-weight: 600;
	}

	/* 语言切换按钮 */
	.lang-switch {
		position: absolute;
		top: 24rpx;
		right: 24rpx;
		display: flex;
		flex-direction: row;
		align-items: center;
		padding: 8rpx 18rpx;
		background: rgba(255, 255, 255, 1);
		border: 1rpx solid rgba(255, 255, 255, 0.35);
		border-radius: 30rpx;
		z-index: 50;
	}

	/* #ifdef APP-PLUS */
	/* App端显示手机状态栏后，语言按钮避开状态栏 */
	.lang-switch {
		top: calc(var(--status-bar-height) + 24rpx);
	}

	/* #endif */

	.lang-switch-icon {
		width: 32rpx;
		height: 32rpx;
		margin-right: 8rpx;
	}

	.lang-switch-text {
		color: #000000;
		font-size: 24rpx;
		font-weight: 600;
	}

	/* 语言切换弹窗 */
	.lang-modal-mask {
		position: fixed;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		background: rgba(0, 0, 0, 0.5);
		z-index: 9998;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.lang-modal {
		width: 78%;
		max-width: 600rpx;
		background: #ffffff;
		border-radius: 20rpx;
		padding: 30rpx 24rpx;
	}

	.lang-modal-title {
		font-size: 32rpx;
		font-weight: 700;
		color: $color-primary;
		text-align: center;
		margin-bottom: 20rpx;
	}

	.lang-option {
		display: flex;
		flex-direction: row;
		justify-content: space-between;
		align-items: center;
		background: #f5f7f8;
		border-radius: 14rpx;
		padding: 24rpx 28rpx;
		margin-bottom: 16rpx;
	}

	.lang-option-label {
		font-size: 30rpx;
		font-weight: 600;
		color: $color-primary;
	}

	.lang-radio {
		width: 40rpx;
		height: 40rpx;
		border-radius: 50%;
		border: 3rpx solid #ccc;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.lang-radio.lang-radio-on {
		border-color: $color-primary;
	}

	.lang-radio-dot {
		width: 22rpx;
		height: 22rpx;
		border-radius: 50%;
		background: $color-primary;
	}

	/* 原有登录页面样式 */
	.login-container {
		position: relative;
		min-height: var(--app-viewport-height, 100vh);
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
		width: auto;
		height: var(--theme-home-logo-height, #{$theme-home-logo-height-value});
		max-width: 100%;
	}

	.login-subtitle {
		margin-top: 10rpx;
		color: $theme-background-foreground;
		font-size: 24rpx;
		letter-spacing: 2rpx;
	}

	.login-subtitle::after {
		content: var(--theme-subtitle, "#{$theme-subtitle-value}");
	}

	/* 广告区域 */
	.ad-container {
		width: 800rpx;
		margin-bottom: 90rpx;
		padding: 0 55rpx;
		margin-top: 30rpx;
	}

	.ad-swiper {
		width: 100%;
		height: 36.8vw;
		overflow: hidden;
		border-radius: 32rpx;
	}

	.ad-image {
		width: 100%;
		height: 100%;
		border-radius: 32rpx;
		border: 1px solid $color-border-other;
		box-sizing: border-box;
	}

	/* 表单区域 */
	.login-form {
		width: 100%;
		margin-bottom: 30rpx;
	}

	.welcome-text {
		font-size: 28rpx;
		font-weight: 600;
		color: $theme-background-foreground;
		text-align: center;
		margin-bottom: 30rpx;
	}

	.input-wrapper {
		position: relative;
		margin-bottom: 30rpx;
	}

	.input-field {
		height: 85rpx;
		background-color: $bg-login-input;
		border: 2rpx solid $color-border-other;
		border-radius: 20rpx;
		padding: 0 100rpx 0 40rpx;
		font-size: 28rpx;
		color: $color-login-input;
		box-sizing: border-box;
		text-align: center;
		font-style: italic;
	}

	.input-placeholder {
		color: $color-login-input;
		text-align: center;
		font-style: italic;
		font-size: 24rpx;
	}

	.input-error {
		border: 2rpx solid #D0342C;
	}

	.password-toggle {
		position: absolute;
		right: 20rpx;
		top: 42.5rpx;
		transform: translateY(-50%);
		width: 60rpx;
		height: 60rpx;
		display: flex;
		justify-content: center;
		align-items: center;
	}

	.eye-icon {
		font-size: 36rpx;
		color: rgba(255, 255, 255, 0.8);
	}

	.error-message {
		margin-top: 8rpx;
		padding: 0 20rpx;
		color: #ff6b6b;
		font-size: 22rpx;
		line-height: 1.3;
		text-align: left;
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
		color: $theme-background-foreground;
		font-style: italic;
		margin-right: auto;
	}

	/* from tangjq--- 自定义圆形复选框 */
	.custom-switch {
		width: 32rpx;
		height: 32rpx;
		border: 4rpx solid $theme-background-foreground;
		border-radius: 50%;
		position: relative;
		display: flex;
		justify-content: center;
		align-items: center;
		transition: border-color 0.3s;
		margin-right: 10px;
	}

	.custom-switch:active {
		opacity: 0.8;
	}

	.switch-dot {
		width: 0;
		height: 0;
		background-color: $theme-background-foreground;
		border-radius: 50%;
		transition: width 0.2s, height 0.2s;
	}

	.switch-dot-active {
		width: 20rpx;
		height: 20rpx;
	}

	.login-btn {
		height: 70rpx;
		background-color: $theme-auth-button-background;
		border-radius: 25rpx;
		display: flex;
		justify-content: center;
		align-items: center;
		font-size: 32rpx;
		font-weight: 600;
		color: $theme-auth-button-foreground;
		margin-bottom: 30rpx;
		box-shadow: 0 4rpx 12rpx rgba(0, 0, 0, 0.15);
	}

	.login-btn:active {
		opacity: 0.9;
		transform: scale(0.98);
	}

	.login-btn-disabled {
		opacity: 0.55;
	}

	.captcha-step {
		max-width: 620rpx;
		margin-right: auto;
		margin-left: auto;
		margin-top: 15px;
	}

	.step-heading {
		margin-bottom: 30rpx;
		color: $theme-background-foreground;
		font-size: 32rpx;
		font-weight: 700;
		text-align: center;
	}

	.register-secondary-btn {
		height: 70rpx;
		margin-bottom: 30rpx;
		margin-top: 30rpx;
		border: 2rpx solid $theme-background-foreground;
		border-radius: 25rpx;
		display: flex;
		align-items: center;
		justify-content: center;
		color: $theme-background-foreground;
		font-size: 30rpx;
		font-weight: 600;
	}

	.register-link {
		text-align: center;
		font-size: 24rpx;
		font-weight: bold;
		font-style: italic;
	}

	.register-text {
		color: $theme-background-foreground;
	}

	.register-link-text {
		color: $color-secondary;
		text-decoration: underline;
	}

	/* Contact Support 区域 */
	.contact-support {
		display: flex;
		flex-direction: column;
		font-style: italic;
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