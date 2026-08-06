<template>
	<view class="login-container">
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
		<!-- 标题图片 -->
		<view class="login-title-container">
			<image class="login-title-image" src="../../figma/login/title.png" mode="widthFix"></image>
			<!-- TODO: 替换为正确的缅甸文翻译 -->
			<text class="login-subtitle">ရွှေမြန်မာတို့ အကြိုက် မြန်မာဘောဒိုင်</text>
		</view>

		<!-- 广告区域 -->
		<view class="ad-container">
			<image class="ad-image" src="../../figma/login/login_ad.png" mode="widthFix"></image>
		</view>

		<!-- Login Form -->
		<view class="login-form">
			<!-- Welcome Text -->
			<view class="welcome-text">{{ $t('Welcome to MM Bookies') }}</view>

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
				<input class="input-field" :class="{'input-error': password_error}" type="text"
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
				<input class="input-field" :class="{'input-error': confirm_password_error}" type="text"
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

			<!-- Sign up Button -->
			<view class="login-btn" @click="register()">
				<text :class="loadding"></text>
				<text>{{ $t('Sign up') }}</text>
			</view>

			<!-- Login Link -->
			<view class="register-link">
				<text class="register-text">{{ $t('Back to ') }}</text>
				<text class="register-link-text" @click="toLogin()">{{ $t('login') }}</text>
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
	import CustomerService from '@/components/common/customer-service.vue'

	export default {
		components: {
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
				currentLang: uni.getStorageSync('UNI_LOCALE') || uni.getStorageSync('language') || 'mm',
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

				// 密码显隐状态
				showPassword: false,
				showConfirmPassword: false,
			}
		},
		computed: {
			registerDisabled() {
				return !this.loginInfo.phone || !this.loginInfo.password || !this.loginInfo.confirm_password ||
					this.phone_error || this.password_error || this.confirm_password_error
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
			togglePasswordVisibility() {
				this.showPassword = !this.showPassword;
			},
			toggleConfirmPasswordVisibility() {
				this.showConfirmPassword = !this.showConfirmPassword;
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
				this.currentLang = uni.getStorageSync('UNI_LOCALE') || uni.getStorageSync('language') || 'mm'
				this.showLangModal = true
			},
			selectLang(value) {
				if (!value) value = 'mm'
				this.currentLang = value
				// 与 pages/ucenter/language.vue 保持一致：更新全局语言、缓存与 i18n
				config.language = language[value]
				uni.setStorageSync('language', value)
				uni.setLocale(value)
				this.$i18n.locale = value
				this.showLangModal = false
			},
			register() {
				if (this.$toolbox.click_too_fast(1)) return

				// 验证所有字段
				this.handle_phone_blur();
				this.handle_password_blur();
				this.handle_confirm_password_blur();

				if (this.registerDisabled) {
					return;
				}

				let _this = this;
				_this.loadding = 'cuIcon-loading2 cuIconfont-spin';

				// 先检查账号是否重复
				_this.$http.post(`/app_user/${this.loginInfo.phone}`, {}, (res) => {
					if (res.statusCode == 200) {
						if (!res.data.status) {
							// 账号不重复，进行注册
							_this.doRegister();
						} else {
							_this.loadding = '';
							this.$notice.show({
								title: _this.$t('tips'),
								content: _this.$t('account_repeat'),
								showCancel: false,
								confirmText: _this.$t('ok'),
							});
						}
					} else {
						_this.loadding = '';
						this.$notice.show({
							title: _this.$t('error_title'),
							content: res.data.message,
							showCancel: false,
							confirmText: _this.$t('ok'),
						});
					}
				})
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
							url: '../match/home'
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
			// 捕获邀请码（推荐链接 ?iv=xxx），用于注册时绑定推荐人
			const iv = option && (option.iv || option.r_code)
			if (iv) {
				this.loginInfo.r_code = iv
				uni.setStorageSync('default_r_code', iv)
			}
		},
	}
</script>

<style lang="scss">
	.login-container {
		position: relative;
		min-height: 100vh;
		background:
			/* 第三层（最上层）：左下角光晕 */
			radial-gradient(circle at 0% 100%, #36BCCB 0%, #103D43 30%, rgba(31, 135, 155, 0) 50%),
			/* 第二层：右上角光晕 */
			radial-gradient(circle at 100% 0%, #36BCCB 0%, #103D43 30%, rgba(31, 135, 155, 0) 50%),
			/* 第一层（最底层）：线性渐变底色 */
			linear-gradient(135deg, #103D43 0%, #103D43 56%, #103D43 100%);
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
		color: #1e3a5f;
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
		color: #1e3a5f;
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
		border-color: #2A6268;
	}

	.lang-radio-dot {
		width: 22rpx;
		height: 22rpx;
		border-radius: 50%;
		background: #2A6268;
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
		margin-bottom: 30rpx;
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
		padding: 0 100rpx 0 40rpx;
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