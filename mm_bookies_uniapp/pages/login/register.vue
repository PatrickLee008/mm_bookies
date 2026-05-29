<template>
	<view class="login-container">
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
			<view class="welcome-text">Welcome to MM Bookies</view>

			<!-- Phone Input Field -->
			<view class="input-wrapper">
				<input class="input-field" :class="{'input-error': phone_error}" type="number" placeholder-class="input-placeholder" v-model="loginInfo.phone" placeholder="Please enter phone number" maxlength="11" @blur="handle_phone_blur" @input="handle_phone_blur" />
				<view class="error-message" v-if="phone_error">
					{{$t("r_input_number_error")}}
				</view>
			</view>

			<!-- Password Input Field -->
			<view class="input-wrapper">
				<input class="input-field" :class="{'input-error': password_error}" type="text" :password="!showPassword" placeholder-class="input-placeholder" v-model="loginInfo.password" placeholder="Please enter your password" maxlength="32" @blur="handle_password_blur" @input="handle_password_blur" />
				<view class="password-toggle" @click="togglePasswordVisibility">
					<uni-icons :type="showPassword ? 'eye' : 'eye-slash'" size="24" color="rgba(255,255,255,0.8)"></uni-icons>
				</view>
				<view class="error-message" v-if="password_error">
					{{$t("r_password_limit")}}
				</view>
			</view>

			<!-- Confirm Password Input Field -->
			<view class="input-wrapper">
				<input class="input-field" :class="{'input-error': confirm_password_error}" type="text" :password="!showConfirmPassword" placeholder-class="input-placeholder" v-model="loginInfo.confirm_password" placeholder="Please confirm your password" maxlength="32" @blur="handle_confirm_password_blur" @input="handle_confirm_password_blur" />
				<view class="password-toggle" @click="toggleConfirmPasswordVisibility">
					<uni-icons :type="showConfirmPassword ? 'eye' : 'eye-slash'" size="24" color="rgba(255,255,255,0.8)"></uni-icons>
				</view>
				<view class="error-message" v-if="confirm_password_error">
					{{$t("those_passwords")}}
				</view>
			</view>

			<!-- Remember Me -->
			<view class="remember-row">
				<text class="remember-text">Remember me</text>
				<view class="custom-switch" @click="toggleRememberMe">
					<view class="switch-dot" :class="{'switch-dot-active': rememberMe}"></view>
				</view>
			</view>

			<!-- Sign up Button -->
			<view class="login-btn" @click="register()">
				<text :class="loadding"></text>
				<text>Sign up</text>
			</view>

			<!-- Login Link -->
			<view class="register-link">
				<text class="register-text">Already have an account? </text>
				<text class="register-link-text" @click="toLogin()">Login</text>
				<text class="register-text"> now.</text>
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
</template>

<script>
	import config from '../../utils/config.js'
	import CryptoJS from 'crypto-js';

	export default {
		data() {
			return {
				loginInfo: {
					phone: '',
					password: '',
					confirm_password: '',
				},
				loadding: '',
				language: config.language,
				version: uni.getStorageSync("version"),
				rememberMe: true,

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
			}
		},
		methods: {
			handle_phone_blur() {
				const phone = this.loginInfo.phone;
				this.phone_error = !(phone && phone.startsWith('09') && phone.length >= 9);
			},
			handle_password_blur() {
				const pwd = this.loginInfo.password;
				// 条件：长度 ≥ 8，包含大小写字母和数字
				const isValid =
					pwd &&
					pwd.length >= 3
				// pwd &&
				// pwd.length >= 8 &&
				// /[a-z]/.test(pwd) &&
				// /[A-Z]/.test(pwd) &&
				// /\d/.test(pwd);
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
							uni.showModal({
								title: 'Tips!',
								content: _this.$t('account_repeat'),
								showCancel: false,
								confirmText: 'ok',
							});
						}
					} else {
						_this.loadding = '';
						uni.showModal({
							title: 'Error!',
							content: res.data.message,
							showCancel: false,
							confirmText: 'ok',
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

				uni.showLoading({
					title: "registering"
				})

				_this.$http.post('/app_user/add', para, (res) => {
					_this.loadding = '';
					uni.hideLoading();

					if (res.statusCode == 200) {
						_this.login();
					} else {
						uni.showModal({
							title: 'Error!',
							content: res.data.message,
							showCancel: false,
							confirmText: 'ok',
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
						uni.showModal({
							title: 'Tips',
							content: _this.$t('wrong_password'),
							showCancel: false,
							confirmText: 'ok',
						});
					} else {
						uni.showModal({
							title: 'Tips',
							content: _this.language[res.data.message],
							showCancel: false,
							confirmText: 'ok',
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
		},
	}
</script>

<style lang="scss">
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
		top: 50%;
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