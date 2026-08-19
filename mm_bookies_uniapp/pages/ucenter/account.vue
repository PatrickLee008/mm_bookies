<template>
	<view class="full-page">
		<zw-header></zw-header>

		<scroll-view scroll-y style="height: calc(var(--app-viewport-height, 100vh) - 110px);">
			<view class="title-bar" style="box-shadow: none;">
				<view class="flex-row justify-between" style="">
					<view class="flex-row align-center" style="">
						<image class="lblue2blue" style="height: 28px;" mode="heightFix"
							src="/static/icon/ucenter/account.png"></image>
						<text class="title-text" style="">{{language.profile}}</text>
					</view>
				</view>
			</view>
			<view class="flex-column1 align-center radius-5px margin-lr-sm bg-white mycolor-primary myfont-14px"
				style="padding: 6vw 3vw;box-shadow: rgba(0, 0, 0, 0.2) 0px 2px 2px 0px;">
				<image src="/static/icon/wallet/128.png" style="height: 60px;" mode="heightFix"></image>
				<view class="text-bold ">{{'Rank:New'}}</view>
				<view class="info-rec">
					<view class="flex-row1 align-center myfont-20px text-bold height-30px">
						<text>{{`User :`}}</text>
						<text class="margin-left-sm">{{userInfo.phone}}</text>
					</view>
					<view class="flex-row1 justify-between align-center">
						<text>{{userInfo.id}}</text>
						<theme-icon name="copy" size="18px"
							color="var(--theme-icon-on-primary, #fff)" @click="copy"></theme-icon>
					</view>
				</view>
				<view class="bank-rec" v-if="card_list[0]">
					<image :src="`/static/icon/register/${card_list[0].bank_code}.png`"
						style="height: 60px;border-radius: 50%;" mode="heightFix"></image>
					<view class="bank-info-text margin-left-sm">
						<text
							class="mycolor-primary text-bold myfont-14px">{{bank_title[card_list[0].bank_code]}}</text>
						<view class="flex-column1">
							<text>{{card_list[0].acc_name}}</text>
							<text>{{card_list[0].acc_number}}</text>
						</view>
					</view>
				</view>
				<view class="flex-row justify-center text-bold" @click="show_set_password = !show_set_password">
					{{language.reset_password}}
				</view>

				<view class="collapse-wrapper" :class="{ 'show': show_set_password }">
					<view class="cu-form-group input-wrapper"
						:class="{'input-focused': old_password_focused, 'input-error': !old_password}">
						<view class="input-label" :class="{'label-focused': old_password_focused || old_password}">
							{{language.current_password}}
						</view>
						<view class="input-container">
							<view class="icon-container">
								<text class="icon-password"></text>
							</view>
							<input class="info-input" :type="show_password ? 'text' : 'password'" v-model="old_password"
								:placeholder-class="old_password_focused ? 'placeholder-hidden' : '' " maxlength="32"
								@focus="old_password_focused = true" @blur="handle_input_blur('old_password')"
								@input="handle_input_blur('old_password')" />
							<view class="eye-icon" @tap="show_password = !show_password">
								<text :class="show_password ? 'cuIcon-attentionfill' : 'cuIcon-attention'"></text>
							</view>
						</view>
						<view class="error-message" v-if="!old_password">
							{{language.required}}
						</view>
					</view>

					<view class="cu-form-group input-wrapper"
						:class="{'input-focused': password_focused, 'input-error': password_error}">
						<view class="input-label" :class="{'label-focused': password_focused || !!password}">
							{{language.new_password}}
						</view>
						<view class="input-container">
							<view class="icon-container">
								<text class="icon-password"></text>
							</view>
							<input class="info-input" :type="show_password ? 'text' : 'password'" v-model="password"
								:placeholder-class="password_focused ? 'placeholder-hidden' : '' " maxlength="32"
								@focus="password_focused = true" @blur="handle_password_blur"
								@input="handle_password_blur" />
							<view class="eye-icon" @tap="show_password = !show_password">
								<text :class="show_password ? 'cuIcon-attentionfill' : 'cuIcon-attention'"></text>
							</view>
						</view>
						<view class="error-message" v-if="password_error">
							{{password_error_contet}}
						</view>
					</view>
					<view class="cu-form-group input-wrapper"
						:class="{'input-focused': password_focused, 'input-error': password_error}">
						<view class="input-label" :class="{'label-focused': password_focused || !!password}">
							{{language.enter_your_password_again}}
						</view>
						<view class="input-container">
							<view class="icon-container">
								<text class="icon-password"></text>
							</view>
							<input class="info-input" :type="show_password ? 'text' : 'password'"
								v-model="confirm_password"
								:placeholder-class="password_focused ? 'placeholder-hidden' : '' " maxlength="32"
								@focus="password_focused = true" @blur="handle_password_blur"
								@input="handle_password_blur" />
							<view class="eye-icon" @tap="toggle_password_visibility">
								<text :class="show_password ? 'cuIcon-attentionfill' : 'cuIcon-attention'"></text>
							</view>
						</view>
						<view class="error-message" v-if="password_error">
							{{password_error_contet}}
						</view>
					</view>

					<button class="login-btn"
						style="width: 50%;margin: 10px 15% 10px 15%;height: 30px;line-height: 30px;padding:0"
						@click="submit()" :disabled="loginDisabled">
						CONFIRM
					</button>
				</view>


			</view>
		</scroll-view>

		<!-- <view class="cu-item" @click="submit">
			<button class="submit" style="background-color: rgb(185, 1, 0);color:white;"
				:disabled="loginDisabled">ok</button>
		</view> -->
	</view>
</template>

<script>
	import language from '../../utils/language.js'
	import config from '../../utils/config.js'
	export default {
		data() {
			return {
				language: config.language,
				old_password: '',
				password: '',
				confirm_password: '',
				userInfo: null,
				bank_title: {
					'aya': 'AYA',
					'cbpay': 'CB',
					'kbz': 'KBZ',
					'kpay': 'KBZ Pay',
					'wave': 'Wave Money',
				},
				show_set_password: false,

				old_password_focused: false,

				show_password: false,
				password_focused: false,
				password_error: false,
				password_error_contet: '',
				card_list: [],
			}
		},
		computed: {
			loginDisabled() {
				if (this.password_error || (!this.old_password || !this.password || !this
						.confirm_password)) {
					return true
				}
				return false
			}
		},
		onShow() {
			this.userInfo = Object.assign({}, this.$store.state.userInfo)
		},
		onLoad() {
			this.get_bank_card_list()
		},
		methods: {
			handle_input_blur(fieldType, options = {}) {
				// 1. 更新焦点状态
				this[`${fieldType}_focused`] = false;
				// 2. 获取值
				const value = this[fieldType];
				// 3. 定义验证规则
				const validations = {
					default: val => val
				};
				// 4. 执行验证
				const validator = options.validator || validations[fieldType] || validations.default;
				this[`${fieldType}_error`] = !validator(value);
			},
			handle_password_blur() {
				this.password_focused = false;
				const pwd = this.password;

				// 条件：长度 ≥ 8，包含大小写字母和数字
				const isValid =
					pwd &&
					pwd.length >= 8 &&
					/[a-z]/.test(pwd) && // 至少一个小写字母
					/[A-Z]/.test(pwd) && // 至少一个大写字母
					/\d/.test(pwd); // 至少一个数字

				this.password_error = !isValid;
				this.password_error_contet = !isValid ?
					this.$t('password_must_contain') :
					this.$t('those_passwords')
				if (this.password != this.confirm_password) {
					this.password_error = true;
				}
			},
			toHome() {
				uni.reLaunch({
					url: '/pages/ucenter/home'
				})
			},
			submit() {
				var _this = this;
				// if (!this.password) {
				// 	this.$notice.show({
				// 		title: 'tips',
				// 		content: this.language['The password cannot be null'],
				// 		showCancel: false,
				// 		confirmText: 'ok',
				// 		success: function(res) {}
				// 	});
				// 	return;
				// }
				if (this.password == this.old_password) {
					this.$notice.show({
						title: 'tips',
						content: this.$t('The new password is the same as the old one'),
						showCancel: false,
						confirmText: 'ok',
						success: function(res) {}
					});
					return;
				}
				var para = {
					USER_PWD: this.password,
					OLD_PASSWORD: this.old_password
				}
				_this.loginDisabled = true;
				_this.$http.post('/app_user/edit', para, (res) => {
					_this.loginDisabled = false;
					var tips = res.data.message;
					if (_this.$t(tips)) {
						tips = _this.$t(tips)
					}
					if (res.statusCode == 200) {
						// uni.showToast({
						// 	title:  this.language['Change Password Success'],
						// 	icon: 'success',
						// 	duration: 2000
						// })
						this.$notice.show({
							// title: this.language['Change Password Success'],
							title: _this.$t('tips'),
							content: tips,
							showCancel: false,
							confirmText: _this.$t('ok'),
							success: function(res) {
								_this.show_set_password = false;
							}
						});
					} else {
						this.$notice.show({
							title: _this.$t('tips'),
							content: tips,
							showCancel: false,
							confirmText: _this.$t('ok'),
							success: function(res) {}
						});
					}
					//this.$refs.popup.close()
				})
			},
			copy() {
				const _this = this
				uni.setClipboardData({
					data: _this.userInfo.id,
					success: function() {
						uni.showToast({
							title: _this.$t('copied_to_clipboard'),
							icon: 'success'
						});
					},
					fail: function() {
						// uni.showToast({
						//   title: '复制失败',
						//   icon: 'none'
						// });
					}
				});

			},
			get_bank_card_list() {
				var _this = this;
				var para = {}
				_this.$http.get('/bank_card/get', {
					data: para
				}, (res) => {
					if (res.statusCode == 200) {
						_this.card_list = res.data.items;
					} else {}
				})
			},
		}
	}
</script>

<style lang="scss">
	.info-rec {
		padding: 10px;
		margin: 10px 10px 0;
		display: flex;
		flex-direction: column;
		background-color: rgb(1, 116, 190);
		border-radius: 8px;
		box-shadow: rgba(0, 0, 0, 0.1) 0px 2px 2px 0px;
		width: 100%;
		color: white;
	}

	.bank-rec {
		width: 100%;
		height: 77px;
		background-color: rgb(237, 236, 241);
		border-radius: 8px;
		display: flex;
		flex-direction: row;
		align-items: center;
		margin: 10px;
		font-size: 12px;
		line-height: 12px;
		padding: 5px;
		box-shadow: rgba(0, 0, 0, 0.1) 0px 2px 2px 0px;
		gap: 16px;
	}

	.bank-info-text {
		display: flex;
		flex-direction: column;
		margin: 0px;
		font-family: __Inter_7be8ac, __Inter_Fallback_7be8ac;
		font-weight: 400;
		line-height: 1.5;
		font-size: 12px;
		color: rgb(125, 125, 125);
	}


	.collapse-wrapper {
		overflow: hidden;
		max-height: 0;
		transition: max-height 0.6s ease;
		width: 100%;
		display: flex;
		flex-direction: column;
		align-items: center;
	}

	.collapse-wrapper.show {
		max-height: 1000px;
		/* 估算一个足够大的值，确保能容纳内容 */
	}

	// 登录样式
	.input-wrapper {
		position: relative;
		border: 1px solid #c0c4cc;
		border-radius: 8rpx;
		padding: 0;
		height: 56px;
		margin: 10px 0 35px;
		transition: all 0.3s;
		width: 100%;
	}

	.input-focused {
		border-color: $color-primary;
		// border-width: 2px;
	}

	.input-error {
		border-color: #D0342C;
	}

	.input-focused .label-focused {
		color: $color-primary;
	}

	.input-error .label-focused {
		color: #D0342C;
	}



	.submit {
		width: 100vw;
	}

	.bg-green {
		background-color: rgb(41, 150, 56)
	}
</style>