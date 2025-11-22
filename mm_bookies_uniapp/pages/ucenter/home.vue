<template name="ucenter">
	<view class="bg-white full-page">
		<zw-header @doSomething=""></zw-header>

		<scroll-view scroll-y style="height: calc(100vh - 110px);">
			<view class="title-bar">
				<view class="flex-row justify-between" style="">
					<view class="flex-row align-center" style="">
						<image class="yellow2dblue" style="height: 25px;" mode="heightFix"
							src="/static/icon/setting.png"></image>
						<text class="title-text" style="">{{$t('setting')}}</text>
					</view>
				</view>
			</view>
			<!-- <view class="myrect flex-row">
				<view>
					<image src="../../static/image/user_img.png" style="width: 70px;height: 70px;"></image>
				</view>
				<view class="flex-column" style="margin-left: 15px;">
					<view class="flex-row" style="font-size: 16px;">
						<text class="myfont-bold">{{currentLanguage.name}}：{{$store.state.userInfo.nick_name}}</text>
					</view>
					<view class="flex-row">
						<text class="myfont-bold">{{currentLanguage.phone}}：{{$store.state.userInfo.phone}}</text>
					</view>
				</view>
			</view> -->

			<!-- <view class="balance-bar myrect box-shadow flex-row">
				<view>
					<image src="../../static/image/cash.png" style="width: 70px;height: 70px;margin-left: 5px;"></image>
				</view>
				<view class="flex-column" style="margin-left: 15px;">
					<view class="flex-row" style="font-size: 16px;">
						<text class="myfont-bold">{{currentLanguage.balance}}</text>
					</view>
					<view class="flex-row">
						<text class="myfont-bold">{{$store.state.userInfo.money}}</text>
					</view>
				</view>

				<view class="flex-column" style="margin-left: 15px;padding:20px 0;">
					<view class="flex-row" style="font-size: 16px;">
						<text class="myfont-bold">{{currentLanguage.cashCode}}</text>
					</view>
					<view class="flex-row">
						<text class="myfont-bold">{{$store.state.userInfo.cash_code}}</text>
					</view>
				</view>

			</view> -->
			<view class="cu-list menu " style="margin-bottom: 20px;">

				<view class="bar-row flex-row" v-for="(bar,index) in bar_list" :key="index" @click="list_method(bar.method,bar.args)"
					v-if="!bar.para.need_login ||(isLogin&&bar.para.need_login)">
					<view class="flex-row content">
						<view class="bar-icon">
							<image class="bar-icon-image" style="" :src="bar.img" mode="heightFix"></image>
						</view>
						<view class="flex-column1">
							<text class="myfont-14px text-bold">{{$t(bar.title)}}</text>
							<text class="myfont-11px mycolor-info">{{bar.content}}</text>
						</view>
					</view>
				</view>


				<!-- #ifdef APP-PLUS -->
				<!-- <view class="cu-item">
				<view class="content">
					<text class="text-grey">version</text>
				</view>
				<view class="action">
					<text class="text-grey text-sm"> {{version}} </text>
				</view>
			</view> -->
				<view class="bar-row flex-row myrect cu-item">
					<view class="flex-row content" style="text-align: left;">
						<view class="bar-icon">
							<!-- <image class="bar-icon-image" :src="bar.img"></image> -->
						</view>
						<text class="text-grey">Version:{{version}}</text>
					</view>
					<view class="action">
						<text class="text-grey text-sm">〉</text>
					</view>
				</view>
				<!-- #endif-->

			</view>

			<button class="mybg-active logout-btn" style="" @click="logout"
				v-if="isLogin">{{$t('sign_out')}}</button>
			<view class="padding"></view>

		</scroll-view>


	</view>
</template>

<script>
	import config from '../../utils/config.js'
	import language from '../../utils/language.js'
	import dateFormatUtils from "../../utils/utils.js"

	export default {
		components: {},
		name: "ucenter",
		data() {
			return {
				isLogin: uni.getStorageSync('Authorization') || false,
				temp: {},
				about: '',
				currentLanguage: config.language,
				picker: '',
				contact2: '',
				contact: [],
				bar_list: [{
						title: 'account_information',
						content: '',
						method: 'goto',
						args: ['/pages/ucenter/account'],
						img: '../../static/icon/ucenter/account.png',
						para: {
							need_login: true
						},
					},
					{
						title: 'awc_game_lobby',
						content: '',
						method: 'enterAWCGameLobby',
						args: [],
						img: '../../static/icon/ucenter/logo-AWC-l-CGTOWzF4.webp',
						para: {
							need_login: true
						},
					},
					{
						title: 'invite',
						content: '',
						method: 'goto',
						args: ['/pages/ucenter/invite/index'],
						img: '../../static/icon/ucenter/invite.png',
						para: {
							need_login: true
						},
					},
					// {
					// 	title: "bank",
					// 	content: '',
					// 	method: 'goto',
					// 	args: ['/pages/ucenter/banks'],
					// 	img: '../../static/icon/ucenter/language.png',
					// 	para: {},
					// },
					{
						title: "contact",
						content: '',
						method: 'goto',
						args: ['/pages/index/contact'],
						img: '../../static/icon/ucenter/contact_lblue.png',
						para: {},
					},
					{
						title: 'bonus',
						content: '',
						method: 'goto',
						args: ['/pages/ucenter/bonus'],
						img: '../../static/icon/ucenter/bonus.png',
						para: {
							need_login: true
						},
					},
					{
						title: "language",
						content: '',
						method: 'goto',
						args: ['/pages/ucenter/language'],
						img: '../../static/icon/ucenter/language.png',
						para: {},
					},
					{
						title: "downloadapp",
						content: 'V 0.0.1',
						// method: 'download',
						// args: ['https://apkdemo.1x2mm.net/'],
						method: 'goto',
						args: ['/pages/ucenter/download'],
						img: '../../static/icon/ucenter/download.png',
						para: {},
					},
					// {
					// 	title: config.language.withdraw_history,
					// 	url: 'withdraw-history',
					// 	img: '../../static/image/withdraw_history.png',
					// },
					// {
					// 	title: config.language.withdraw,
					// 	url: 'withdraw',
					// 	img: '../../static/image/withdraw.png',
					// },
					// {
					// 	title: config.language.recharge,
					// 	url: 'charge',
					// 	img: '../../static/image/withdraw.png',
					// },
					// {
					// 	title: config.language.depositRecords,
					// 	url: 'charge_record',
					// 	img: '../../static/image/withdraw_history.png',
					// },
					// {
					// 	title: config.language.changePassword,
					// 	url: 'change_pwd',
					// 	img: '../../static/image/change_pw.png',
					// },
					// {
					// 	title: config.language.userCharge,
					// 	url: 'charge_upload',
					// 	img: '../../static/image/withdraw.png',
					// },
					// {
					// 	title: config.language.about,
					// 	url: 'about',
					// 	img: '../../static/image/about.png',
					// },
				],
				contact: '',
				dislan: 0,
				dislan2: 0,
				version: uni.getStorageSync("version"),
				modal_name: '',
			}
		},

		methods: {
			show_modal(modal) {
				this.modal_name = modal
			},
			list_method(method, args) {
				// 传入方法名及参数
				if (typeof this[method] === 'function') {
					this[method](...args);
				} else {
					console.error(`${method}方法不存在`);
				}
			},
			// AWC游戏大厅入口
			enterAWCGameLobby() {
				var _this = this

				// 检查是否登录
				if (!_this.isLogin) {
					uni.showModal({
						title: 'Tips',
						content: _this.$t('please_sign_in_to_receive_the_coupon'),
						showCancel: false,
						confirmText: 'OK',
						success: function(res) {
							if (res.confirm) {
								uni.navigateTo({
									url: '/pages/login/login'
								})
							}
						}
					})
					return
				}

				// 获取用户信息
				var userInfo = _this.$store.state.userInfo
				if (!userInfo || !userInfo.phone) {
					uni.showToast({
						title: 'Unable to get user information',
						icon: 'none'
					})
					return
				}

				// 显示加载中
				uni.showLoading({
					title: 'Loading...'
				})

				// 准备请求参数
				var para = {
					userId: userInfo.phone,
					isMobileLogin: true
				}

				// 调用后端API
				_this.$http.post('/awc/enterGameLobby', para, (res) => {
					uni.hideLoading()

					if (res.statusCode == 200 && res.data.ok) {
						var gameUrl = res.data.data.url
						var isNewMember = res.data.data.isNewMember

						// 如果是新会员，提示用户
						if (isNewMember) {
							uni.showToast({
								title: 'Account created successfully',
								icon: 'success',
								duration: 2000
							})
						}

						// 根据不同平台采用不同的打开方式
						// #ifdef H5
						// H5环境下检测是否为iOS Safari
						const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent)
						const isSafari = /Safari/.test(navigator.userAgent) && !/Chrome/.test(navigator.userAgent)

						if (isIOS && isSafari) {
							// iOS Safari直接在当前窗口打开，避免弹窗拦截
							console.log('iOS Safari detected, opening in current window')
							window.location.href = gameUrl
						} else {
							// PC或其他移动浏览器使用新窗口打开
							const newWindow = window.open(gameUrl, '_blank')
							if (!newWindow) {
								// 如果被拦截，提示用户或使用备用方案
								uni.showModal({
									title: 'Tips',
									content: 'Please allow pop-ups for this site',
									confirmText: 'Open Now',
									cancelText: 'Cancel',
									success: (modalRes) => {
										if (modalRes.confirm) {
											// 用户确认后，跳转到webview页面
											uni.navigateTo({
												url: '/pages/webview/index?url=' + encodeURIComponent(gameUrl)
											})
										}
									}
								})
							}
						}
						// #endif

						// #ifdef APP-PLUS || MP
						// APP和小程序环境使用内嵌webview
						uni.navigateTo({
							url: '/pages/webview/index?url=' + encodeURIComponent(gameUrl)
						})
						// #endif

					} else {
						uni.showModal({
							title: 'Error',
							content: res.data.message || 'Unable to enter game lobby',
							showCancel: false,
							confirmText: 'OK'
						})
					}
				})
			},
			download(url) {
				//#ifdef APP-PLUS
				plus.runtime.openURL(url)
				//#endif

				//#ifdef H5
				// debugger
				window.open(url);
				//#endif
				setTimeout(() => {
					goto('./home')
				}, 2000)
			},
			logout() {
				// this.music.play_dede();
				uni.removeStorageSync('Authorization');
				uni.redirectTo({
					url: '../login/login'
				})
			},
			showContactDialogs() {
				// this.music.play_dede();
				this.$refs.contactDialogs.open()
			},
			goto(path) {
				uni.navigateTo({
					url: path,
					// url: '/pages/ucenter/' + path,
					animationType: 'slide-in-right',
					animationDuration: 100
				})

			},
			showDialogs(title) {
				// this.music.play_dede();
				this.temp = {
					title: this.currentLanguage[title],
					content: this.$data[title]
				}
				this.$refs.popup.open()
			},
			hideDialogs() {
				this.$refs.popup.close()
			},
			parseContact() {
				this.contact = []
				if (this.$store.state.configs.contact_us) {
					let arr = this.$store.state.configs.contact_us.split('\n')
					arr.forEach((ele, index) => {
						if (ele.indexOf('https') > -1) {
							this.contact.push({
								'str': ele,
								'type': 'site',
							})
						} else {
							this.contact.push({
								'str': ele,
								'type': 'str',
							})
						}
					})
				}

			},
		},
		mounted(){
		},
		created() {}
	}
</script>

<style lang="scss">
	.bar-row {
		width: calc(100% - 20px);
		height: 55px;
		margin: 5px 10px 5px;
		padding: 5px 1px;
		border-radius: 5px;
		justify-content: space-between;
		color: $color-primary;
		box-shadow: rgba(60, 64, 67, 0.3) 0px 1px 2px 0px, rgba(60, 64, 67, 0.15) 0px 1px 3px 1px;
	}

	.bar-icon {
		height: 48px;
		padding: 10px;
	}

	.bar-icon-image {
		height: 100%;
	}


	.balance-bar {
		width: 90vw;
		padding: 2px;
		background-color: #d54d4a;
		margin-top: 15px;
		color: white;
	}

	.logout-btn {
		line-height: 35px;
		font-weight: bold;
		width: 45%;
		height: 35px;
		border-radius: 5px;
		position: absolute;
		left: 27.5%;
		box-shadow: rgba(0, 0, 0, 0.25) 0px 2px 2px 0px;
	}

	.dialogs {
		height: 50vh;
	}

	.about-text {
		color: rgb(129, 58, 58);
		font-size: 25px;
		width: 100%;
		display: inline-block;
		white-space: pre-wrap;
		word-wrap: break-word;
		height: auto;
	}

	.menu {
		margin-bottom: 60px;
	}

	.dialogsTitle {
		height: 5vh;
		line-height: 5vh;
		border-bottom: 1px solid lightgrey;
		font-size: 16px;
	}

	.span_box {
		display: table;
	}

	.words_span {
		display: table-cell;
		vertical-align: middle;
	}

	.border-right {
		border-right: 1px solid #E2E2E2;
	}

	.head {
		height: 60px;
		width: 100%;
		line-height: 60px
	}

	.height-150 {
		height: 150px;
		padding: 45px 0 0 12px;
		margin: 8px 0 8px 0;
	}

	.head image {
		float: left;
		height: 80px;
		width: 80px;
	}

	.cu-list {
		margin-top: 12px;
	}

	.head view {
		margin-left: 12px;
		float: left;
	}


	.user-info-loading {
		height: 15px;
		width: 15px;
		position: absolute;
		right: 5px
	}
</style>