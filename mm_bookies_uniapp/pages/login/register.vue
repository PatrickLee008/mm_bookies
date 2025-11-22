<template>
	<view class="login-container">
		<!-- App Title -->
		<view class="app-title">MM Bookies</view>

		<!-- Login Form -->
		<view class="login-form">
			<!-- Welcome Text -->
			<view class="welcome-text">Welcome to MM Bookies</view>

			<!-- Phone Input Field -->
			<view class="input-wrapper">
				<input class="input-field" style="margin-bottom: 40px;" :class="{'input-error': phone_error}" type="number"
					placeholder-class="input-placeholder" v-model="loginInfo.phone"
					placeholder="Please enter phone number" maxlength="11" @blur="handle_phone_blur"
					@input="handle_phone_blur" />
				<view class="error-message" style="bottom: -30px;" v-if="phone_error">
					{{$t("r_input_number_error")}}
				</view>
			</view>

			<!-- Password Input Field -->
			<view class="input-wrapper">
				<input class="input-field" :class="{'input-error': password_error}"
					type="password" placeholder-class="input-placeholder" v-model="loginInfo.password"
					placeholder="Please enter your password" maxlength="32" @blur="handle_password_blur"
					@input="handle_password_blur" />
				<view class="error-message" v-if="password_error">
					{{$t("r_password_limit")}}
				</view>
			</view>

			<!-- Confirm Password Input Field -->
			<view class="input-wrapper">
				<input class="input-field" :class="{'input-error': confirm_password_error}" type="password"
					placeholder-class="input-placeholder" v-model="loginInfo.confirm_password"
					placeholder="Please confirm your password" maxlength="32" @blur="handle_confirm_password_blur"
					@input="handle_confirm_password_blur" />
				<view class="error-message" v-if="confirm_password_error">
					{{$t("those_passwords")}}
				</view>
			</view>

			<!-- Remember Me -->
			<view class="remember-row">
				<text class="remember-text">Remember me</text>
				<switch class="remember-switch" :checked="rememberMe" @change="switchChange" color="#2A6268" />
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

				_this.$http.post('/app_user/login', para, (res) => {
					_this.loadding = '';
					if (res.statusCode == 200) {
						uni.setStorageSync('Authorization', res.data.token);
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
		},
		onLoad(option) {
			uni.removeStorageSync('login_success');
		},
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
		height: 80rpx;
		background-color: #ffffff;
		border-radius: 20rpx;
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