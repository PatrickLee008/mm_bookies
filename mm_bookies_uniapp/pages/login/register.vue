<template>
	<view class="login-container theme-bg-no-header">
		<global-notice ref="globalNotice"></global-notice>
		<!-- 语言切换按钮 -->
		<view class="lang-switch" @click="openLangModal">
			<image class="lang-switch-icon" src="/static/icon/ucenter/language.png" mode="aspectFit"></image>
			<text class="lang-switch-text">{{ currentLangLabel }}</text>
		</view>

		<!-- 语言切换弹窗 -->
		<view class="lang-modal-mask" v-if="showLangModal" @click="showLangModal = false">
			<view class="lang-modal" @click.stop="">
				<view class="lang-modal-title">{{ $t('change_language') }}</view>
				<view class="lang-option" v-for="opt in langOptions" :key="opt.value" @click="selectLang(opt.value)">
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
		<view class="ad-container" v-if="registerStep !== 2 && advertisements.length">
			<swiper class="ad-swiper" :circular="advertisements.length > 1"
				:autoplay="advertisements.length > 1" interval="3500" duration="500"
				:indicator-dots="advertisements.length > 1">
				<swiper-item v-for="(ad, index) in advertisements" :key="index" @click="handleAdClick(ad)">
					<image class="ad-image" :src="getAdvertisementImage(ad)" mode="scaleToFill"></image>
				</swiper-item>
			</swiper>
		</view>
		<view class="height-8vh" v-else-if="registerStep !== 2"></view>

		<!-- Register step 1: account and password -->
		<view class="login-form register-flow" v-if="registerStep === 1">
			<!-- Welcome Text -->
			<view class="welcome-text">
				<template v-if="currentLang === 'mm'">
					<text class="welcome-title"></text>
					<text>{{ $t('welcome_to') }}</text>
				</template>
				<template v-else>
					<text>{{ $t('welcome_to') }}</text>
					<text class="welcome-title"></text>
				</template>
			</view>

			<!-- Phone Input Field -->
			<view class="input-wrapper">
				<input class="input-field" :class="{'input-error': phone_error}" type="number"
					placeholder-class="input-placeholder" v-model="loginInfo.phone"
					:placeholder="$t('Please Enter Username')" maxlength="11" @blur="handle_phone_blur"
					@input="handle_phone_blur" />
				<view class="error-message" v-if="phone_error">
					{{$t("r_input_number_error")}}
				</view>
			</view>

			<!-- Password Input Field -->
			<view class="input-wrapper">
				<input class="input-field" :class="{'input-error': password_error}"
					:password="!showPassword" placeholder-class="input-placeholder" v-model="loginInfo.password"
					:placeholder="$t('enter_password')" maxlength="32" @blur="handle_password_blur"
					@input="handle_password_blur" />
				<view class="password-toggle" @click="togglePasswordVisibility">
					<uni-icons :type="showPassword ? 'eye' : 'eye-slash'" size="24"
						color="rgba(255,255,255,0.8)"></uni-icons>
				</view>
				<view class="error-message" v-if="password_error">
					{{$t("r_password_limit")}}
				</view>
			</view>

			<!-- Confirm Password Input Field -->
			<view class="input-wrapper">
				<input class="input-field" :class="{'input-error': confirm_password_error}"
					:password="!showConfirmPassword" placeholder-class="input-placeholder"
					v-model="loginInfo.confirm_password" :placeholder="$t('confirm_password')" maxlength="32"
					@blur="handle_confirm_password_blur" @input="handle_confirm_password_blur" />
				<view class="password-toggle" @click="toggleConfirmPasswordVisibility">
					<uni-icons :type="showConfirmPassword ? 'eye' : 'eye-slash'" size="24"
						color="rgba(255,255,255,0.8)"></uni-icons>
				</view>
				<view class="error-message" v-if="confirm_password_error">
					{{$t("those_passwords")}}
				</view>
			</view>

			<!-- Referral ID -->
			<view class="referral-field" v-if="false">
				<input class="input-field referral-input" :class="{ 'referral-input-disabled': r_code_disabled }"
					v-model="loginInfo.r_code" :disabled="r_code_disabled" placeholder-class="input-placeholder"
					:placeholder="$t('enter_referral_id_optional')" maxlength="32" @input="handle_r_code_input" />
			</view>

			<!-- Sign up Button -->
			<view class="login-btn" :class="{ 'login-btn-disabled': registerDisabled }"
				@click="continueToCaptcha">
				<text :class="loadding"></text>
				<text>{{ $t('Continue') }}</text>
			</view>

			<!-- Login Link -->
			<view class="register-link">
				<text class="register-text">{{ $t('Back to ') }}</text>
				<text class="register-link-text" @click="toLogin()">{{ $t('login') }}</text>
			</view>
		</view>

		<!-- Register step 2: slider verification -->
		<view class="login-form register-flow captcha-step" v-else-if="registerStep === 2">
			<slider-captcha ref="registerCaptcha" :config="captchaConfig" :trigger-generate="captchaTrigger"
				:show-close="false" @verify="handleCaptchaVerify" @verify-fail="handleCaptchaVerifyFail"
				@refresh="handleCaptchaRefresh" @error="handleCaptchaError" />

			<view class="login-btn" :class="{ 'login-btn-disabled': !captchaVerified || loadding }"
				@click="confirmCaptcha">
				<text :class="loadding"></text>
				<text>{{ $t('verify') }}</text>
			</view>
			<view class="register-secondary-btn" @click="backToCredentials">{{ $t('Back') }}</view>
		</view>

		<!-- Register step 3: referral code -->
		<view class="login-form register-flow referral-step" v-else>
			<view class="step-heading">{{ $t('referral_id') }}</view>
			<view class="referral-question">{{ $t('enter_referral_id_optional') }}</view>
			<view class="referral-field">
				<input class="input-field referral-input"
					:class="{ 'referral-input-disabled': r_code_disabled }" v-model="loginInfo.r_code"
					:disabled="r_code_disabled" placeholder-class="input-placeholder"
					:placeholder="$t('enter_referral_id_optional')" maxlength="32"
					@input="handle_r_code_input" />
			</view>

			<view class="login-btn" :class="{ 'login-btn-disabled': loadding }" @click="register">
				<text :class="loadding"></text>
				<text>{{ $t('Confirm') }}</text>
			</view>
			<view v-if="!r_code_disabled" class="register-secondary-btn" @click="skipReferralAndRegister">
				{{ $t('Skip') }}
			</view>
			<view class="register-link" @click="backToCaptcha">
				<text class="register-link-text">{{ $t('Back') }}</text>
			</view>
		</view>

		<!-- Contact Support -->
		<view class="contact-support" v-if="false">
			<text class="contact-text">{{ $t('Contact service')}}</text>
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
</template>

<script>
	import config from '../../utils/config.js'
	import language from '../../utils/language.js'
	import CryptoJS from 'crypto-js';
	import SliderCaptcha from '@/components/SliderCaptcha.vue'
	import CustomerService from '@/components/common/customer-service.vue'

	export default {
		components: {
			SliderCaptcha,
			CustomerService,
		},
		data() {
			return {
				loginInfo: {
					phone: '',
					password: '',
					confirm_password: '',
					r_code: '',
				},
				loadding: '',
				language: config.language,
				version: uni.getStorageSync("version"),
				rememberMe: true,

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
					},
				],

				// 验证相关
				phone_error: false,
				password_error: false,
				confirm_password_error: false,
				r_code_disabled: false,

				// 密码显隐状态
				showPassword: false,
				showConfirmPassword: false,
				advertisements: [],

				// 注册步骤与滑动验证码
				registerStep: 1,
				captchaTrigger: 0,
				captchaVerified: false,
			}
		},
		computed: {
			registerDisabled() {
				return !this.loginInfo.phone || !this.loginInfo.password || !this.loginInfo.confirm_password ||
					this.phone_error || this.password_error || this.confirm_password_error
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
			},
			currentLangLabel() {
				const map = {
					mm: 'မြန်မာ',
					en: 'EN',
					th: 'ไทย',
					cn: '中文'
				}
				return map[this.currentLang] || 'EN'
			}
		},
		methods: {
			handle_phone_blur() {
				const phone = this.loginInfo.phone;
				this.phone_error = !(phone && phone.startsWith('09') && phone.length >= 9);
			},
			handle_password_blur() {
				const pwd = this.loginInfo.password;
				// 密码只要求至少五个字符，不限制字符类型。
				const isValid = pwd && pwd.length >= 5
				this.password_error = !isValid;

				// 同时检查确认密码
				if (this.loginInfo.confirm_password) {
					this.handle_confirm_password_blur();
				}
			},
			handle_confirm_password_blur() {
				this.confirm_password_error = this.loginInfo.password !== this.loginInfo.confirm_password;
			},
			handle_r_code_input() {
				this.loginInfo.r_code = String(this.loginInfo.r_code || '')
					.replace(/[^a-zA-Z0-9]/g, '')
					.slice(0, 32)
					.toUpperCase();
				if (!this.loginInfo.r_code && !this.r_code_disabled) {
					uni.removeStorageSync('default_r_code');
				}
			},
			togglePasswordVisibility() {
				this.showPassword = !this.showPassword;
			},
			toggleConfirmPasswordVisibility() {
				this.showConfirmPassword = !this.showConfirmPassword;
			},
			continueToCaptcha() {
				this.handle_phone_blur();
				this.handle_password_blur();
				this.handle_confirm_password_blur();
				if (this.registerDisabled) return;

				this.captchaVerified = false;
				this.registerStep = 2;
				this.$nextTick(() => {
					setTimeout(() => {
						this.captchaTrigger = Date.now();
						this.$refs.registerCaptcha && this.$refs.registerCaptcha.calculateDimensions();
					}, 100);
				});
			},
			handleCaptchaVerify() {
				this.captchaVerified = true;
			},
			handleCaptchaVerifyFail() {
				this.captchaVerified = false;
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
			confirmCaptcha() {
				if (!this.captchaVerified || this.loadding) return;

				this.loadding = 'cuIcon-loading2 cuIconfont-spin';
				this.$http.post(`/app_user/${this.loginInfo.phone}`, {}, (res) => {
					this.loadding = '';
					if (res.statusCode == 200) {
						if (!res.data.status) {
							this.registerStep = 3;
						} else {
							this.captchaVerified = false;
							this.$notice.show({
								title: this.$t('tips'),
								content: this.$t('account_repeat'),
								showCancel: false,
								confirmText: this.$t('ok'),
							});
						}
					} else {
						this.captchaVerified = false;
						this.$notice.show({
							title: this.$t('error_title'),
							content: res.data.message,
							showCancel: false,
							confirmText: this.$t('ok'),
						});
					}
				});
			},
			backToCredentials() {
				this.registerStep = 1;
				this.captchaVerified = false;
			},
			backToCaptcha() {
				this.registerStep = 2;
				this.captchaVerified = false;
				this.$nextTick(() => {
					setTimeout(() => {
						this.captchaTrigger = Date.now();
						this.$refs.registerCaptcha && this.$refs.registerCaptcha.calculateDimensions();
					}, 100);
				});
			},
			skipReferralAndRegister() {
				if (this.r_code_disabled) return;
				this.loginInfo.r_code = '';
				uni.removeStorageSync('default_r_code');
				this.register();
			},
			switchChange(e) {
				this.rememberMe = e.target.value;
			},
			toLogin() {
				uni.navigateTo({
					url: "./login"
				})
			},
			// 语言切换
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
			register() {
				if (this.$toolbox.click_too_fast(1)) return

				if (this.registerStep !== 3 || this.registerDisabled) return;

				let _this = this;
				_this.loadding = 'cuIcon-loading2 cuIconfont-spin';

				_this.doRegister();
			},
			doRegister() {
				let _this = this;
				let para = {
					USER_PWD: this.loginInfo.password,
					PHONE: this.loginInfo.phone,
				}

				const defaultAgentId = uni.getStorageSync('default_r_aid');
				if (defaultAgentId) para.agent_id = defaultAgentId;
				const adl = uni.getStorageSync('default_adl');
				if (adl) para.adlink_id = adl;
				// 推荐码（来自邀请链接 ?iv= 或本地缓存），后端匹配 AppMember.r_code
				const rCode = this.loginInfo.r_code || uni.getStorageSync('default_r_code');
				if (rCode) para.r_code = rCode;

				uni.showLoading({
					title: _this.$t('registering')
				})

				_this.$http.post('/app_user/add', para, (res) => {
					_this.loadding = '';
					uni.hideLoading();

					if (res.statusCode == 200) {
						uni.removeStorageSync('default_r_code');
						_this.login();
					} else {
						this.$notice.show({
							title: _this.$t('error_title'),
							content: res.data.message,
							showCancel: false,
							confirmText: _this.$t('ok'),
						});
					}
				})
			},
			login() {
				let _this = this;
				_this.loadding = 'cuIcon-loading2 cuIconfont-spin';

				const account = this.loginInfo.phone;
				const password = this.loginInfo.password;
				const timestamp = new Date().getTime().toString();

				const params = JSON.stringify({
					account,
					password,
					timestamp
				});
				const encryptedParams = _this.encrypt(params);

				let para = {
					encryptedParams: encryptedParams
				}

				const defaultAgentId = uni.getStorageSync('default_r_aid');
				if (defaultAgentId) para.agent_id = defaultAgentId;
				const adl = uni.getStorageSync('default_adl');
				if (adl) para.adlink_id = adl;

				_this.$http.post('/app_user/login', para, (res) => {
					_this.loadding = '';
					if (res.statusCode == 200) {
						uni.setStorageSync('Authorization', res.data.token);

						// 登录成功后获取配置
						const app = getApp()
						if (app && app.getConfigs) {
							app.getConfigs()
						}

						uni.redirectTo({
							url: '../index/index'
						});
						uni.setStorageSync('login_success', true);
						uni.setStorageSync('rigister_success', true);
					} else if (res.statusCode == 400) {
						this.$notice.show({
							title: _this.$t('tips'),
							content: _this.$t('wrong_password'),
							showCancel: false,
							confirmText: _this.$t('ok'),
						});
					} else {
						this.$notice.show({
							title: _this.$t('tips'),
							content: _this.language[res.data.message],
							showCancel: false,
							confirmText: _this.$t('ok'),
						});
					}
				})
			},
			encrypt(text) {
				const key = CryptoJS.enc.Utf8.parse('innwa'.padEnd(16, '\0'));
				const iv = CryptoJS.enc.Utf8.parse('1234567890123456');
				const encrypted = CryptoJS.AES.encrypt(text, key, {
					iv: iv,
					mode: CryptoJS.mode.CBC,
					padding: CryptoJS.pad.Pkcs7
				});
				return encrypted.toString();
			},
			// from tangjq--- 切换记住我状态
			toggleRememberMe() {
				this.rememberMe = !this.rememberMe
			}
		},
		onLoad(option) {
			uni.removeStorageSync('login_success');
			this.getAdvertisements()
			// 捕获邀请码（推荐链接 ?iv=xxx），用于注册时绑定推荐人
			const inviteCode = option && (option.iv || option.r_code)
			const cachedCode = uni.getStorageSync('default_r_code')
			const rCode = inviteCode || cachedCode
			this.r_code_disabled = Boolean(inviteCode)
			if (rCode) {
				this.loginInfo.r_code = String(rCode).trim()
				this.handle_r_code_input()
				if (inviteCode) {
					uni.setStorageSync('default_r_code', this.loginInfo.r_code)
				}
			}
		},
	}
</script>

<style lang="scss">
	.login-container {
		position: relative;
		min-height: var(--app-viewport-height, 100vh);
		display: flex;
		flex-direction: column;
		align-items: center;
		padding: 0 30rpx;
		box-sizing: border-box;
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
		border: 3rpx solid $color-secondary;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.lang-radio.lang-radio-on {
		border-color: $color-secondary;
	}

	.lang-radio-dot {
		width: 22rpx;
		height: 22rpx;
		border-radius: 50%;
		background: $color-secondary;
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

	.referral-field {
		width: 100%;
		margin-bottom: 30rpx;
	}

	.referral-label {
		display: block;
		margin: 0 0 10rpx 10rpx;
		color: rgba(255, 255, 255, 0.9);
		font-size: 24rpx;
	}

	.referral-input {
		width: 100%;
		text-align: left;
	}

	.referral-input-disabled {
		opacity: 0.8;
	}

	/* 广告区域 */
	.ad-container {
		width: 800rpx;
		margin-bottom: 30rpx;
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
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 8rpx;
		flex-wrap: wrap;
	}

	.welcome-title::after {
		content: var(--theme-title, "#{$theme-title-value}");
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
		width: 40rpx;
		height: 40rpx;
		border: 3rpx solid $theme-background-foreground;
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
		background-color: $theme-background-foreground;
		border-radius: 50%;
		transition: width 0.2s, height 0.2s;
	}

	.switch-dot-active {
		width: 24rpx;
		height: 24rpx;
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

	.captcha-step,
	.referral-step {
		max-width: 620rpx;
		margin-right: auto;
		margin-left: auto;
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

	.referral-question {
		margin-bottom: 24rpx;
		color: $theme-background-foreground;
		font-size: 24rpx;
		text-align: center;
	}

	.register-link {
		font-weight: bold;
		text-align: center;
		font-size: 24rpx;
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