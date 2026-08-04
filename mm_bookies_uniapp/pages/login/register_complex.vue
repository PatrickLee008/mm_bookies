<template>
	<view class="dark-teal-bg">
		<zw-header></zw-header>
		<!-- <cu-custom isBack backUrl="/pages/login/login">
			<block slot="content">{{$t('registerTitle')}}</block>
		</cu-custom> -->
		<view class="login-page" style="background: #fff;">
			<view class="flex-column width-100">
				<view class="myfont-11px margin-bottom">{{language[title_list[current_progress - 1]]}}</view>
				<view class="flex-row justify-center width-100">
					<view class="progress-btn"
						:style="loginDisabled?'background-color:gray':'background-image: linear-gradient(130deg, rgb(12, 53, 106) 60%, rgb(50, 106, 178) 100%);'"
						@click="progressChange(-1)">
						<view class="text-white cuIcon-triangleupfill myfont-12px" style="transform: rotate(-90deg);">
						</view>
					</view>
					<view class="cu-progress round xs width-25 margin-lr-sm"
						style="background-color: rgb(162, 178, 198);">
						<view class="mybg-primary" :style="[{ width:loading?(current_progress*25)+'%':''}]"></view>
					</view>
					<view class="progress-btn" @click="progressChange(1)"
						:style="loginDisabled?'background-color:gray':'background-image: linear-gradient(130deg, rgb(12, 53, 106) 60%, rgb(50, 106, 178) 100%);'">
						<view class="text-white cuIcon-triangleupfill myfont-12px" style="transform: rotate(90deg);">
						</view>
					</view>
				</view>
			</view>


			<!-- 1 -->
			<view class="login-form">
				<!-- <view> -->
				<view v-if="current_progress == 1">
					<view class="cu-form-group input-wrapper"
						:class="{'input-focused': phone_focused, 'input-error': phone_error}">
						<view class="input-label" :class="{'label-focused': phone_focused || !!loginInfo.phone}">
							{{$t('phone')}}*
						</view>
						<view class="input-container">
							<view class="icon-container">
								<text class="icon-phone"></text>
							</view>
							<input class="info-input" type="number" v-model="loginInfo.phone"
								:placeholder-class="phone_focused ? 'placeholder-hidden' : ''" maxlength="11"
								@focus="phone_focused = true" @blur="handle_input_blur('phone')"
								@input="handle_input_blur('phone')" />
						</view>
						<view class="error-message" v-if="phone_error">
							{{$t("r_input_number_error")}}
						</view>
					</view>

					<!-- 验证码 -->
					<view class="cu-form-group input-wrapper"
						:class="{'input-focused': captcha_focused, 'input-error': captcha_error}">
						<view class="input-label" :class="{'label-focused': captcha_focused || !!loginInfo.captcha}">
							{{language.enter_captcha}}
						</view>
						<view class="input-container">
							<view class="icon-container">
								<text class="icon-captcha"></text>
							</view>
							<input class="info-input" type="text" v-model="loginInfo.captcha"
								:placeholder-class="captcha_focused ? 'placeholder-hidden' : ''" maxlength="4"
								@focus="captcha_focused = true" @blur="handle_input_blur('captcha')"
								@input="handle_input_blur('captcha')" />
							<view class="captcha-container" style="">
								<canvas class="captcha" style="" canvas-id="canvas"></canvas>
							</view>
							<view style="height: 80%;width:1px ;background-color: rgba(0, 0, 0, 0.12);"></view>
							<view
								class="cuIcon-refresh mycolor-primary text-bold myfont-20px width-44px flex-row1 justify-center"
								@click="updateImageCode"></view>
						</view>
						<view class="error-message" v-if="captcha_error">
							{{$t("r_captcha_limit")}}
						</view>
					</view>

				</view>

				<!-- 2 -->
				<!-- <view> -->
				<view v-if="current_progress == 2">
					<view class="cu-form-group input-wrapper" style="margin-bottom: 65px;"
						:class="{'input-focused': password_focused, 'input-error': password_error}">
						<view class="input-label" :class="{'label-focused': password_focused || !!loginInfo.password}">
							{{$t('password')}}
						</view>
						<view class="input-container">
							<view class="icon-container">
								<text class="icon-password"></text>
							</view>
							<input class="info-input" :type="show_password ? 'text' : 'password'"
								v-model="loginInfo.password"
								:placeholder-class="password_focused ? 'placeholder-hidden' : '' " maxlength="32"
								@focus="password_focused = true" @blur="handle_password_blur"
								@input="handle_password_blur" />
							<view class="eye-icon" @tap="toggle_password_visibility">
								<text :class="show_password ? 'cuIcon-attentionfill' : 'cuIcon-attention'"></text>
							</view>
						</view>
						<view class="error-message" v-if="password_error">
							{{$t("r_password_limit")}}
						</view>
					</view>
					<view class="cu-form-group input-wrapper" style="margin-bottom: 60px;"
						:class="{'input-focused': password_focused, 'input-error': password_error}">
						<view class="input-label"
							:class="{'label-focused': password_focused || !!loginInfo.confirm_password}">
							{{$t('confirm_password')}}
						</view>
						<view class="input-container">
							<view class="icon-container">
								<text class="icon-password"></text>
							</view>
							<input class="info-input" :type="show_password ? 'text' : 'password'"
								v-model="loginInfo.confirm_password"
								:placeholder-class="password_focused ? 'placeholder-hidden' : '' " maxlength="32"
								@focus="password_focused = true" @blur="handle_password_blur"
								@input="handle_password_blur" />
							<view class="eye-icon" @tap="toggle_password_visibility">
								<text :class="show_password ? 'cuIcon-attentionfill' : 'cuIcon-attention'"></text>
							</view>
						</view>
						<view class="error-message" v-if="password_error">
							{{$t("r_password_limit")}}
						</view>
					</view>
				</view>


				<!-- 3 -->
				<!-- <view class="text-bold text-black myfont-15px margin-top-lg">What is your favourite Football Club?
					</view>
					<view class="cu-form-group input-wrapper" style="margin: 8px 0 30px;"
						:class="{'input-error': security_answer1_error}">
						<view class="input-container">
							<input class="info-input" type="text" v-model="loginInfo.security_answer1"
								placeholder="Enter your Answer" maxlength="32"
								@blur="handleDefaultBlur('security_answer1')" />
						</view>
						<view class="error-message" v-if="security_answer1_error">
							security security_answer can not be none.
						</view>
					</view>

					<view class="text-bold text-black myfont-15px">Which league do you support most?</view>
					<view class="cu-form-group input-wrapper" style="margin: 8px 0 30px;"
						:class="{'input-error': security_answer2_error}">
						<view class="input-container">
							<input class="info-input" type="text" v-model="loginInfo.security_answer2"
								placeholder="Enter your Answer" maxlength="32"
								@blur="handleDefaultBlur('security_answer2')" />
						</view>
						<view class="error-message" v-if="security_answer2_error">
							security security_answer can not be none.
						</view>
					</view>

					<view class="text-bold text-black myfont-15px">What is your favourite national team?</view>
					<view class="cu-form-group input-wrapper" style="margin: 8px 0 30px;"
						:class="{'input-error': security_answer3_error}">
						<view class="input-container">
							<input class="info-input" type="text" v-model="loginInfo.security_answer3"
								placeholder="Enter your Answer" maxlength="32"
								@blur="handleDefaultBlur('security_answer3')" />
						</view>
						<view class="error-message" v-if="security_answer3_error">
							security security_answer can not be none.
						</view>
					</view> -->

				<!-- 4 -->
				<!-- <view> -->
				<view v-if="current_progress == 3">
					<view class="flex-row width-100 justify-between margin-top">
						<view class="bank-horizon">
						</view>
						<text class="myfont-14px text-black">{{$t('please_select_your_bank')}}</text>
						<view class="bank-horizon">
						</view>
					</view>
					<view
						class="flex-row justify-center align-center width-100 height-48px margin-top-xs margin-bottom">
						<image :src="img.url" :class="img.checked?'checked-bank':'default-bank'" mode="scaleToFill"
							@click="bank_select(img)" v-for="(img,index) in bank_list" :key="index">
						</image>
					</view>

					<view class="cu-form-group input-wrapper" style="margin-top: 10px;"
						:class="{'input-focused': bank_card_focused, 'input-error': bank_card_error}">
						<view class="input-label"
							:class="{'label-focused': bank_card_focused || !!loginInfo.bank_card}">
							{{$t('account_number')}}*
						</view>
						<view class="input-container">
							<view class="icon-container">
								<text class="icon-bankcard"></text>
							</view>
							<input class="info-input" type="number" v-model="loginInfo.bank_card"
								:placeholder-class="bank_card_focused ? 'placeholder-hidden' : ''" maxlength="17"
								@focus="bank_card_focused = true" @blur="handle_input_blur('bank_card')" />
						</view>
						<view class="error-message" v-if="bank_card_error">
							{{$t("r_number_limit")}}
						</view>
					</view>
					<view class="cu-form-group input-wrapper" style="margin-bottom: 20px;"
						:class="{'input-focused': bank_user_name_focused, 'input-error': bank_user_name_error}">
						<view class="input-label"
							:class="{'label-focused': bank_user_name_focused || !!loginInfo.bank_user_name}">
							{{$t('fullname')}}*
						</view>
						<view class="input-container">
							<view class="icon-container">
								<text class="icon-fullname"></text>
							</view>
							<input class="info-input" v-model="loginInfo.bank_user_name"
								:placeholder-class="bank_user_name_focused ? 'placeholder-hidden' : ''"
								@focus="bank_user_name_focused = true" @blur="handle_input_blur('bank_user_name')" />
						</view>
						<view class="error-message" v-if="bank_user_name_error">
							{{$t("r_Enter_full_name")}}
						</view>
					</view>
					<view class="flex-row width-100 justify-center"
						style="margin: 0px;font-family: __Inter_7be8ac, __Inter_Fallback_7be8ac;font-size: 0.875rem;line-height: 1.43;color: rgb(211, 47, 47);text-align: center;font-weight: 600;padding-bottom: 16px;padding-top: 10px;">
						{{$t('please_fill_in_real_information')}}
					</view>
					<view class="flex-row width-100 justify-center margin-bottom"
						style="margin: 0px 0px 16px;font-family: __Inter_7be8ac, __Inter_Fallback_7be8ac;font-weight: 400;font-size: 0.875rem;line-height: 1.43;color: rgb(211, 47, 47);text-align: center;">
						{{$t('cautions_register_information')}}
					</view>
				</view>



				<!-- <view class="cu-form-group input-wrapper" :class="{'input-focused': r_majuser_id_focused}"> -->
				<view class="cu-form-group input-wrapper" :class="{'input-focused': r_majuser_id_focused}"
					v-if="current_progress == 4">
					<view class="input-label"
						:class="{'label-focused': r_majuser_id_focused || !!loginInfo.r_majuser_id}">
						{{$t('referral_id')}}*
					</view>
					<view class="input-container">
						<view class="icon-container">
							<text class="icon-fullname"></text>
						</view>
						<input class="info-input" v-model="loginInfo.r_majuser_id" :disabled="r_majuser_id_disable"
							:placeholder-class="r_majuser_id_focused ? 'placeholder-hidden' : ''"
							@focus="r_majuser_id_focused = true" />
					</view>
				</view>


				<button class="login-btn" style="width: 70%;margin: 10px 15% 10px 15%;" @click="next_method()"
					:disabled="loginDisabled">
					<text
						:class="loadding"></text>{{$t('confirm')}}{{current_progress == 4?`(${$t('skip')})`:''}}</button>


				<!-- <button class="login-btn" style="width: 70%;margin: 10px 15% 10px 15%;" @click="register()"
						:disabled="loginDisabled">
						<text :class="loadding"></text>{{$t('register}}</button> -->

				<!-- <view style="position: fixed;right:10px;bottom:300px;" @click="toAI()">
						<image src="/static/image/ai.png" mode="aspectFill" style="width: 50px;height:50px"></image>
					</view> -->

			</view>

			<view class="width-100 margin-top-lg" v-if="current_progress == 1">
				<view class="width-100 text-center myfont-13px">
					<text>{{$t('your_already_have_user_account')}}<text @click="goto('/pages/login/login')"
							class="mycolor-primary margin-left-xs text-bold">{{$t('login')}}</text></text>
				</view>
				<view class="width-100 text-center myfont-13px margin-top-xs">
					<text>{{$t('found_a_problem')}}<text @click="goto('/pages/index/contact')"
							class="mycolor-primary margin-left-xs text-bold">{{$t('contact_service')}}</text></text>
				</view>
			</view>
		</view>

		<!-- <view class="myrect bg-white" style="padding: 6vw;">
			<view class="flex-row">
				<image src="../../static/image/jiju.png" class="my-icon"></image>
				<text class="myfont-bold myfont-12px">{{$t('phone')}}</text>
			</view>

			<input class="mybg-grey my-input" v-model="loginInfo.phone" placeholder="Please enter phone number " />

			<view class="flex-row">
				<image src="../../static/image/jiju.png" class="my-icon"></image>
				<text class="myfont-bold myfont-12px">{{$t('name')}}</text>
			</view>

			<input class="mybg-grey my-input" v-model="loginInfo.nickname" placeholder="Please enter your nickname" />

			<view class="flex-row">
				<image src="../../static/image/mima.png" class="my-icon"></image>
				<text class="myfont-bold myfont-12px">{{$t('input_password')}}</text>
			</view>
			<input class="mybg-grey my-input" v-model="loginInfo.password" password="true"
				placeholder="Please enter your password" />

			<view class="flex-row">
				<image src="../../static/image/mima.png" class="my-icon"></image>
				<text class="myfont-bold myfont-12px">{{$t('passwordConfirm')}}</text>
			</view>
			<input class="mybg-grey my-input" v-model="loginInfo.confirm_password" password="true"
				placeholder="Please confirm your password" />
		</view> -->
	</view>
</template>

<script>
	// import advertisement from '../plugin/advertisement.vue'
	import config from '../../utils/config.js'
	import CryptoJS from 'crypto-js';

	import {
		Mcaptcha
	} from '@/utils/mcaptcha'
	import language from '../../utils/language';

	export default {
		components: {
			// advertisement
		},
		data() {
			return {
				// loginDisabled: true,
				loginInfo: {
					nickname: '',
					phone: '',
					password: '',
					confirm_password: '',
					// security_answer1: '',
					// security_answerr2: '',
					// security_answerr3: '',

					bank_type: '',
					bank_user_name: '',
					bank_card: '',

					captcha: '',
					r_majuser_id: '',
				},
				loadding: '',
				language: config.language,
				// 当前进度
				current_progress: 1,
				max_progress: 1,
				// 验证相关
				phone_focused: false,
				password_focused: false,
				captcha_focused: false,
				bank_card_focused: false,
				bank_card_focused: false,
				bank_user_name_focused: false,
				r_majuser_id_focused: false,

				phone_error: false,
				password_error: false,
				captcha_error: false,
				// security_answer1_error: false,
				// security_answer2_error: false,
				// security_answer3_error: false,
				bank_card_error: false,
				bank_user_name_error: false,

				show_password: false,
				loading: false,

				password_error_contet: '',
				bank_list: [{
					bank_type: 'AYA',
					url: '/static/icon/register/AYA.png',
					checked: false,
				}, {
					bank_type: 'CB Pay',
					url: '/static/icon/register/CB Pay.png',
					checked: false,
				}, {
					bank_type: 'KBZ',
					url: '/static/icon/register/KBZ.png',
					checked: false,
				}, {
					bank_type: 'KBZ Pay',
					url: '/static/icon/register/KBZ Pay.png',
					checked: false,
				}, {
					bank_type: 'Wave Money',
					url: '/static/icon/register/Wave Money.png',
					checked: false,
				}],
				title_list: ['apply_for_membership', 'set_password', 'choose_account_bank', 'reference_information'],
				r_majuser_id_disable: false,
			}
		},
		computed: {
			loginDisabled() {
				if (this.current_progress == 1 && ((this.phone_error) || (!this.loginInfo
						.phone))) {
					return true
				}
				// if (this.current_progress == 1 && ((this.phone_error || this.captcha_error) || (!this.loginInfo
				// 		.phone || !this.loginInfo.captcha))) {
				// 	return true
				// }
				if (this.current_progress == 2 && (this.password_error || (!this.loginInfo
						.password || !this.loginInfo.confirm_password))) {
					return true
				}
				if (this.current_progress == 3 && ((this.bank_card_error || this.bank_user_name_error) || (!this
						.loginInfo
						.bank_type || !this.loginInfo
						.bank_user_name || !this.loginInfo.bank_card))) {
					return true
				}
				return false
			}
		},
		methods: {
			goto(url) {
				uni.reLaunch({
					url: url,
				})
			},
			handle_password_blur() {
				// this.password_focused = false;
				const pwd = this.loginInfo.password;

				// 密码只要求至少五个字符，不限制字符类型。
				const isValid = pwd && pwd.length >= 5

				this.password_error = !isValid;
				this.password_error_contet = !isValid ?
					this.$t('password_must_contain') :
					this.$t('those_passwords')
				if (this.loginInfo.password != this.loginInfo.confirm_password) {
					this.password_error = true;
				}
			},
			// 统一处理输入框失焦事件的函数
			handle_input_blur(fieldType, options = {}) {
				// 1. 更新焦点状态
				this[`${fieldType}_focused`] = false;

				// 2. 获取值
				const value = this.loginInfo[fieldType];

				// 3. 定义验证规则
				const validations = {
					phone: val => val && val.startsWith('09') && val.length >= 9,
					captcha: val => val && val.length >= 4,
					bank_card: val => val && val.length >= 6,
					default: val => val
				};

				// 4. 执行验证
				const validator = options.validator || validations[fieldType] || validations.default;
				this[`${fieldType}_error`] = !validator(value);
			},
			toggle_password_visibility() {
				this.show_password = !this.show_password;
			},
			progressChange(up_or_down) {
				let _this = this
				if (this.loginDisabled) {
					return
				}
				if (_this.current_progress == 1 && up_or_down == -1) {
					return
				}
				if (_this.max_progress == _this.current_progress && up_or_down == +1) {
					return
				}
				if (_this.current_progress >= 1) {
					_this.current_progress += up_or_down
					// console.log(this.current_progress)
				}
				if (_this.current_progress == 1) {
					_this.loginInfo.captcha = ''
					_this.$nextTick(() => {
						_this.updateImageCode()
					})
				}
			},
			next_method() {
				if (this.$toolbox.click_too_fast(1)) return
				switch (this.current_progress) {
					case 1:
						this.checkRepeatAccount()
						break;
					case 2:
						if (this.password_error || !this.loginInfo.password || !this.loginInfo.confirm_password) {
							return
						} else {
							this.current_progress += 1
							this.max_progress += 1
						}
						break;
					case 3:
						if (!this.loginInfo.bank_type) {
							this.$notice.show({
								title: 'res.data.message',
								content: this.$t('please_select_your_bank'),
								// content: this.language[res.data.message],
								showCancel: false,
								confirmText: 'ok',
								success: function(res) {}
							});
							return
						}
						if (!this.loginInfo.bank_card || !this.loginInfo.bank_user_name) {
							return
						} else {
							this.current_progress += 1
							this.max_progress += 1
						}
						break;
					case 4:
						this.register()
						break;
				}
			},
			checkRepeatAccount() {
				let _this = this
				// let validate = this.mcaptcha.validate(this.loginInfo.captcha)
				// if (!validate) {
				// 	this.$notice.show({
				// 		title: this.language.warning,
				// 		content: this.language.captcha_not_match,
				// 		showCancel: false,
				// 		confirmText: 'OK',
				// 	})
				// 	return
				// }
				// if (this.infoVerify()) {
				// 	return
				// }
				_this.$http.post(`/app_user/${this.loginInfo.phone}`, {}, (res) => {
					_this.loadding = ''
					// _this.loginDisabled = false
					if (res.statusCode == 200) {
						if (!res.data.status) {
							this.current_progress += 1
							this.max_progress += 1
							return
						} else {
							this.$notice.show({
								title: 'Tips!',
								content: _this.$t('account_repeat'),
								// content: this.language[res.data.message],
								showCancel: false,
								confirmText: 'ok',
								success: function(res) {}
							});
						}
					} else {
						this.$notice.show({
							title: 'error!',
							content: res.data.message,
							// content: this.language[res.data.message],
							showCancel: false,
							confirmText: 'ok',
							success: function(res) {}
						});
					}
					this.loginInfo.captcha = ''
					this.updateImageCode()
				})
			},
			bank_select(bank) {
				let _this = this
				let checked = _this.bank_list.find(item => item.checked)
				if (checked) {
					checked.checked = false
				}
				bank.checked = !bank.checked
				_this.loginInfo.bank_type = bank.bank_type
				// console.log(_this.loginInfo)
			},

			register() {
				let _this = this;
				let para = {
					NICK_NAME: this.loginInfo.nickname,
					USER_PWD: this.loginInfo.password,
					PHONE: this.loginInfo.phone,
					BANK_TYPE: this.loginInfo.bank_type,
					BANK_USER_NAME: this.loginInfo.bank_user_name,
					BANK_CARD: this.loginInfo.bank_card,
				}
				if (this.loginInfo.r_majuser_id) para.r_majuser_id = this.loginInfo.r_majuser_id
				_this.loadding = 'cuIcon-loading2 cuIconfont-spin';
				// _this.loginDisabled = true
				uni.showLoading({
					title: "registering"
				})
				_this.$http.post('/app_user/add', para, (res) => {
					_this.loadding = ''
					if (res.statusCode == 200) {
						_this.login()
						// this.$notice.show({
						// 	title: 'Success!',
						// 	content: 'Welcome',
						// 	showCancel: false,
						// 	confirmText: 'ok',
						// 	success: function(res) {
						// 		_this.login()
						// 	}
						// });

					} else {
						// _this.loginDisabled = false
						this.$notice.show({
							title: '_error!',
							content: res.data.message,
							// content: this.language[res.data.message],
							showCancel: false,
							confirmText: 'ok',
							success: function(res) {}
						});
					}
					uni.hideLoading();
				})
			},
			login() {
				var _this = this;
				_this.loadding = 'cuIcon-loading2 cuIconfont-spin';
				// _this.loginDisabled = true;

				const account = this.loginInfo.phone;
				const password = this.loginInfo.password;


				const timestamp = new Date().getTime().toString();

				const params = JSON.stringify({
					account,
					password,
					timestamp
				});
				const encryptedParams = _this.encrypt(params);

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
						uni.setStorageSync('rigister_success', true)
					} else if (res.statusCode == 400) {
						this.$notice.show({
							title: 'Tips',
							content: this.$t('wrong_password'),
							showCancel: false,
							confirmText: 'ok',
							success: function(res) {}
						});
						// _this.loginDisabled = false;
					} else {
						this.$notice.show({
							title: 'Tips',
							content: this.language[res.data.message],
							showCancel: false,
							confirmText: 'ok',
							success: function(res) {}
						});
						// _this.loginDisabled = false;
					}
				})
			},
			encrypt(text) {
				const key = CryptoJS.enc.Utf8.parse('innwa'.padEnd(16, '\0'));
				const iv = CryptoJS.enc.Utf8.parse('1234567890123456'); // 初始向量，16字节
				const encrypted = CryptoJS.AES.encrypt(text, key, {
					iv: iv,
					mode: CryptoJS.mode.CBC,
					padding: CryptoJS.pad.Pkcs7
				});
				return encrypted.toString();
			},
			// infoVerify() {
			// 	let _this = this
			// 	let content = ''
			// 	switch (this.current_progress) {
			// 		case 1:
			// 			let validate = this.mcaptcha.validate(this.loginInfo.captcha)
			// 			if (!validate) {
			// 				content = 'captcha not match'
			// 			}
			// 			if (this.phone_error) {
			// 				// return ''
			// 				content = 'Invalid input'
			// 			}
			// 			break;
			// 		case 2:
			// 			if (this.password_error) {
			// 				// return ''
			// 				content = 'Invalid input'
			// 			}
			// 			break;
			// 		case 3:
			// 			if (this.bank_card_error || this.bank_user_name_error) {
			// 				// return ''
			// 				content = 'Invalid input'
			// 			}
			// 			if (!this.loginInfo.bank_type) {
			// 				// return ''
			// 				content = 'Please select your bank'
			// 			}
			// 			break;
			// 	}

			// 	if (content) {
			// 		this.$notice.show({
			// 			title: 'Warning',
			// 			content: content,
			// 			showCancel: false,
			// 			confirmText: 'OK',
			// 		})
			// 		return true
			// 	} else {
			// 		return false
			// 	}
			// 	let validate = this.mcaptcha.validate(this.loginInfo.captcha)
			// 	if (!validate) {
			// 		return 'captcha not match'
			// 	}
			// },
			onReady() {
				this.mcaptcha = new Mcaptcha({
					el: 'canvas',
					width: 90,
					height: 45,
					createCodeImg: ""
				});
			},
			// 刷新验证码
			updateImageCode() {
				this.mcaptcha.refresh()
			},
		},
		onLoad(option) {
			let that = this;
			setTimeout(function() {
				that.loading = true
			}, 500)

			if (option.iv) {
				this.loginInfo.r_majuser_id = option.iv
				this.r_majuser_id_disable = true
			}

			uni.removeStorageSync('login_success')
		},
	}
</script>

<style lang="scss">
	.dark-teal-bg {
		background: #02455F;
		min-height: 100vh;
	}

	.default-bank {
		height: 32px;
		width: 32px;
		margin: 0 8px;
		border-radius: 6px;
	}

	.checked-bank {
		height: 48px;
		width: 48px;
		margin: 0 0px;
		border-radius: 9px;
		box-shadow: 0px 5upx 10px 1px $color-primary;
	}

	.bank-horizon {
		background-color: rgba(0, 0, 0, 0.12);
		height: 1px;
		width: calc((100% - 170px) / 2);
	}

	.progress-btn {
		display: flex;
		flex-direction: column;
		justify-content: center;
		align-items: center;
		width: 25px;
		height: 25px;
		border-radius: 50%;
		filter: drop-shadow(rgb(12, 53, 106) 0px 0px 2px);
	}

	// 登录样式
	.input-wrapper {
		position: relative;
		border: 1px solid #c0c4cc;
		border-radius: 8rpx;
		padding: 0;
		height: 56px;
		margin: 40px 0;
		transition: all 0.3s;
		width: 100%;
	}

	.input-focused {
		border-color: $color-primary;
		// border-width: 2px;
	}

	.input-error {
		border-color: #e54d42;
	}

	.input-focused .label-focused {
		color: $color-primary;
	}

	.input-error .label-focused {
		color: #e54d42;
	}
</style>