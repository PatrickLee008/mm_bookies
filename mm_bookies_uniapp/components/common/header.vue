<template>
	<view>
		<!-- from tangjq--- 新的统一顶部组件，按照设计稿 -->
		<view class="new-header-wrapper">
			<!-- from tangjq--- 顶部标题区域 -->
			<view class="header-title-bar">
				<text class="header-title">MM Bookies</text>
			</view>

			<!-- from tangjq--- 用户信息卡片 -->
			<view class="user-info-card" v-if="isLogin">
				<!-- 头像 -->
				<view class="user-avatar" @click="goto('/pages/ucenter/home', 1)">
					<image src="/static/icon/nav/user_avatar.png" class="avatar-img" mode="aspectFill"></image>
				</view>

				<!-- 用户信息 -->
				<view class="user-details">
					<view class="user-id">
						<view class="user-id-info">
							<text class="id-label">My ID : </text>
							<text class="id-value">{{userInfo.phone || ''}}</text>
						</view>
						<!-- 右侧操作区：消息铃铛 + 设置 -->
						<view class="header-actions">
							<!-- 消息铃铛入口：有未读时变红并摇动 -->
							<view class="bell-btn" @click="goMessage">
								<image src="/static/icon/nav/notification.svg" class="bell-icon"
									:class="{ 'bell-ring': unreadMessageCount > 0 }" mode="aspectFit"></image>
								<view class="bell-badge" v-if="unreadMessageCount > 0">
									{{ unreadMessageCount > 99 ? '99+' : unreadMessageCount }}
								</view>
							</view>
							<!-- 设置按钮 -->
							<view class="settings-btn" @click="goto('/pages/ucenter/home', 1)">
								<image src="/static/icon/nav/settings.png" class="settings-icon" mode="aspectFit">
								</image>
							</view>
						</view>
					</view>
					<view class="user-balance-row">
						<view class="balance-item">
							<image src="/static/icon/nav/coin.png" class="coin-icon" mode="aspectFit"></image>
							<text
								class="balance-value myfont-18px text-bold">{{$toolbox.num_format(userInfo.money) || '0'}}</text>
						</view>
						<view class="secondary-balance-row">
							<image src="/static/icon/nav/coin.png" class="coin-icon" mode="aspectFit"></image>
							<view class="balance-item">
								<text class="cashout-label">Promo</text>
								<text
									class="cashout-value">{{$toolbox.num_format(userInfo.money_promotion) || '0'}}</text>
							</view>
							<view class="balance-item" style="margin-left: 12px;">
								<text class="cashout-label">{{ $t('cash_out') }}</text>
								<text
									class="cashout-value">{{$toolbox.num_format(userInfo.total_withdraw) || '0'}}</text>
							</view>
						</view>
					</view>
				</view>
			</view>

			<!-- from tangjq--- 未登录状态 -->
			<view class="user-info-card login-prompt-card" v-else>
				<view class="login-prompt-content">
					<text class="login-prompt-text">{{ $t('please_login') }}</text>
					<view class="login-buttons">
						<view class="login-btn2" @click="goto('/pages/login/login')">
							{{$t('signin_button')}}
						</view>
						<view class="register-btn2" @click="goto('/pages/login/register')">
							{{$t('register_button')}}
						</view>
					</view>
				</view>
			</view>

			<view class="header-page-row">
				<view class="header-back" @click="goBack">
					<image src="/static/icon/basic/back.svg" mode="aspectFit"></image>
					<text>{{$t('Back')}}</text>
				</view>
				<text class="header-page-title">{{ $t(pageTitle) }}</text>
			</view>
		</view>
	</view>
</template>

<script>
	import {
		mapGetters
	} from 'vuex';
	import {
		getUnreadCount
	} from '@/utils/api/message.js'

	export default {
		components: {},
		props: {
			// from tangjq--- 接收当前激活的导航项
			active: {
				type: String,
				default: ''
			}
		},
		data() {
			return {
				isLogin: uni.getStorageSync('Authorization') || false,
				userInfo: {},
				mounted: false,
				unreadMessageCount: 0, // 未读消息数量
				activeNav: '', // from tangjq--- 当前激活的导航项
				headerHeight: 0, // 组件实际高度
			}
		},
		computed: {
			currentRoute() {
				const pages = getCurrentPages();
				return pages.length ? pages[pages.length - 1].route : '';
			},
			pageTitle() {
				const titles = {
					'pages/match/home': 'single',
					'pages/orders/home': 'sistory',
					'pages/index/coupon': 'Deals',
					'pages/wallet/wallet': 'wallet',
					'pages/index/game': 'E-Games',
					'pages/index/contact': 'Contact',
					'pages/ucenter/home': 'setting',
					'pages/ucenter/account': 'Account',
					'pages/ucenter/invite/index': 'Referral',
					'pages/ucenter/invite/share': 'Share',
					'pages/ucenter/language': 'Language',
					'pages/ucenter/bonus': 'Bonus',
					'pages/ucenter/download': 'Download',
					'pages/ucenter/message': 'Messages',
					'pages/ucenter/invite/bonus_dashboard': 'Bonus Dashboard',
					'pages/ucenter/invite/user_dashboard': 'User Dashboard',
					'pages/ucenter/withdraw': 'Withdraw',
					'pages/ucenter/charge': 'Deposit',
					'pages/payment/payment': 'Payment'
				}
				const pages = getCurrentPages()
				const current = pages.length ? pages[pages.length - 1] : null
				if (current && current.route === 'pages/match/home' && current.options.mix === '1') {
					return 'MPL'
				}
				return titles[this.currentRoute] || ''
			}
		},
		created() {},
		mounted() {
			this.getUserInfo();
			this.updateActiveNav();
			this.updateUnreadMessageCount();
			this.setupWebSocketMessageListener();
			this.$nextTick(() => {
				this.calculateHeaderHeight();
			});
		},
		activated() {
			this.updateActiveNav();
			this.$nextTick(() => {
				this.calculateHeaderHeight();
			});
		},
		watch: {
			// from tangjq--- 监听active prop变化
			active(newVal) {
				this.activeNav = newVal;
			}
		},
		methods: {
			// from tangjq--- 更新当前激活的导航项
			updateActiveNav() {
				if (this.active) {
					this.activeNav = this.active;
					return;
				}

				// 根据当前路由自动判断
				const pages = getCurrentPages();
				const currentPage = pages[pages.length - 1];
				const currentRoute = currentPage.route;
				const options = currentPage.options;

				if (currentRoute === 'pages/match/home') {
					this.activeNav = options.mix === '1' ? 'mpl' : 'single';
				} else if (currentRoute === 'pages/index/game') {
					this.activeNav = 'games';
				} else if (currentRoute === 'pages/orders/home') {
					this.activeNav = 'history';
				} else if (currentRoute === 'pages/index/coupon') {
					this.activeNav = 'deals';
				} else if (currentRoute === 'pages/wallet/wallet') {
					this.activeNav = 'wallet';
				}
			},

			getUserInfo() {
				var _this = this;
				_this.loading = true;
				if (uni.getStorageSync("Authorization")) {
					_this.$http.get('/app_user/user_info', {}, (res) => {
						_this.loading = false;
						if (res.statusCode == 200) {
							_this.$store.dispatch('saveUserInfo', res.data.data);
							_this.userInfo = res.data.data
							this.mounted = true
							this.$nextTick(() => {
								this.calculateHeaderHeight();
							});
						}
					})
				}
			},

			calculateHeaderHeight() {
				const query = uni.createSelectorQuery().in(this);
				query.select('.new-header-wrapper').boundingClientRect((rect) => {
					if (rect && rect.height) {
						this.headerHeight = rect.height;
						this.$emit('headerHeightChange', rect.height);
					}
				}).exec();
			},

			goto(url, limit_click) {
				if (typeof url === 'object' && url.url) {
					url = url.need_login && !this.isLogin ? '/pages/login/login' : url.url
				}

				if (limit_click) {
					if (url.includes(this.currentRoute) && this.$toolbox.click_too_fast(1)) return
				}

				// 检查是否需要登录
				if (url.includes('/pages/orders/home') || url.includes('/pages/wallet/wallet')) {
					if (!this.isLogin) {
						uni.reLaunch({
							url: '/pages/login/login'
						})
						return
					}
				}

				uni.reLaunch({
					url: url
				})
			},

			// 跳转到消息中心
			goMessage() {
				if (!this.isLogin) {
					uni.reLaunch({
						url: '/pages/login/login'
					})
					return
				}
				uni.navigateTo({
					url: '/pages/ucenter/message'
				})
			},

			goBack() {
				if (this.currentRoute === 'pages/match/home') {
					uni.reLaunch({
						url: '/pages/index/index'
					})
					return
				}
				const pages = getCurrentPages()
				if (pages.length > 1) {
					uni.navigateBack({
						delta: 1,
						fail: () => uni.reLaunch({
							url: '/pages/index/index'
						})
					})
					return
				}
				uni.reLaunch({
					url: '/pages/index/index'
				})
			},

			// 更新未读消息数量（改为从后端接口获取）
			updateUnreadMessageCount() {
				if (!uni.getStorageSync('Authorization')) {
					this.unreadMessageCount = 0
					return
				}
				getUnreadCount().then((count) => {
					this.unreadMessageCount = count || 0
				}).catch(() => {
					this.unreadMessageCount = 0
				})
			},

			// 设置WebSocket消息监听器
			setupWebSocketMessageListener() {
				const _this = this

				uni.$on('websocket:messageSaved', () => {
					_this.updateUnreadMessageCount()
				})

				uni.$on('message:read', () => {
					_this.updateUnreadMessageCount()
				})

				uni.$on('message:update', () => {
					_this.updateUnreadMessageCount()
				})

				// 弹窗组件/消息页标记已读后触发，重新拉取未读数
				uni.$on('message:unreadUpdate', () => {
					_this.updateUnreadMessageCount()
				})
			}
		},

		// 组件销毁时清理监听器
		beforeDestroy() {
			uni.$off('websocket:messageSaved')
			uni.$off('message:read')
			uni.$off('message:update')
			uni.$off('message:unreadUpdate')
		}
	}
</script>

<style lang="scss">
	/* from tangjq--- 新的统一顶部样式 - 固定定位 */
	.new-header-wrapper {
		position: fixed;
		top: 0;
		left: 0;
		right: 0;
		width: 100%;
		background-color: #2F5D62;
		// padding-bottom: 15px;
		z-index: 1000;
		// box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
	}

	/* from tangjq--- 顶部标题栏 */
	.header-title-bar {
		padding: 10px 0;
		text-align: center;
	}

	.header-title {
		color: white;
		font-size: 16px;
		font-weight: bold;
	}

	.header-page-row {
		display: flex;
		align-items: center;
		justify-content: space-between;
		height: 42px;
		padding: 0 20px;
		font-size: 14px;
		color: #ffffff;
	}

	.header-back {
		display: flex;
		align-items: center;
		gap: 10px;
		font-weight: 700;
	}

	.header-back image {
		width: 18px;
		height: 18px;
		filter: brightness(0) invert(1);
	}

	.header-page-title {
		color: #35b6c2;
		font-weight: 700;
	}

	/* from tangjq--- 用户信息卡片 */
	.user-info-card {
		background-color: white;
		border-radius: 20px;
		margin: 5px 15px 10px;
		padding: 5px 12px 10px;
		box-sizing: border-box;
		display: flex;
		flex-direction: row;
		align-items: center;
		min-height: 90px;
	}

	.user-avatar {
		width: 50px;
		height: 50px;
		border-radius: 50%;
		// background-color: #2F5D62;
		display: flex;
		align-items: center;
		justify-content: center;
		overflow: hidden;
		margin-right: 10px;
		flex-shrink: 0;
	}

	.avatar-img {
		width: 100%;
		height: 100%;
		background-color: #ffffff;
	}

	.user-details {
		flex: 1;
		display: flex;
		flex-direction: column;
		gap: 4px;
	}

	.user-id {
		display: flex;
		flex-direction: row;
		align-items: center;
		justify-content: space-between;
	}

	.user-id-info {
		display: flex;
		flex-direction: row;
		align-items: center;
		flex: 1;
		min-width: 0;
		font-size: 15px;
	}

	.id-label {
		color: #2F5D62;
		font-weight: 600;
	}

	.id-value {
		color: #2F5D62;
		// font-size: 14px;
		font-weight: bold;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.user-balance-row {
		display: flex;
		flex-direction: column;
		align-items: flex-start;
		gap: 3px;
	}

	.balance-item {
		display: flex;
		flex-direction: row;
		align-items: center;
		gap: 5px;
		white-space: nowrap;
	}

	.secondary-balance-row {
		display: flex;
		align-items: center;
		gap: 5px;
	}

	.coin-icon {
		width: 18px;
		height: 18px;
		margin-right: 7px;
	}

	.balance-label,
	.cashout-label {
		color: #2F5D62;
		font-size: 12px;
		white-space: nowrap;
		font-weight: bold;
	}

	.balance-value,
	.cashout-value {
		color: #2F5D62;
		font-size: 12px;
	}

	.settings-btn {
		width: 32px;
		height: 32px;
		display: flex;
		align-items: center;
		justify-content: center;
		flex-shrink: 0;
	}

	.settings-icon {
		width: 24px;
		height: 24px;
	}

	/* 右侧操作区：铃铛 + 设置 */
	.header-actions {
		display: flex;
		flex-direction: row;
		align-items: center;
		gap: 6px;
		flex-shrink: 0;
	}

	/* 消息铃铛 */
	.bell-btn {
		position: relative;
		width: 32px;
		height: 32px;
		display: flex;
		align-items: center;
		justify-content: center;
		flex-shrink: 0;
	}

	.bell-icon {
		width: 22px;
		height: 22px;
		transform-origin: top center;
	}

	/* 有未读消息：变红 + 摇动 */
	.bell-ring {
		color: #FF4444;
		animation: bellRing 1s ease-in-out infinite;
	}

	@keyframes bellRing {
		0% {
			transform: rotate(0);
		}

		15% {
			transform: rotate(16deg);
		}

		30% {
			transform: rotate(-14deg);
		}

		45% {
			transform: rotate(11deg);
		}

		60% {
			transform: rotate(-8deg);
		}

		75% {
			transform: rotate(4deg);
		}

		100% {
			transform: rotate(0);
		}
	}

	/* 铃铛未读数角标 */
	.bell-badge {
		position: absolute;
		top: -2px;
		right: -2px;
		min-width: 16px;
		height: 16px;
		padding: 0 4px;
		border-radius: 8px;
		background-color: #FF4444;
		color: #ffffff;
		font-size: 10px;
		font-weight: bold;
		line-height: 16px;
		text-align: center;
		border: 1px solid #ffffff;
	}

	/* from tangjq--- 未登录状态卡片 */
	.login-prompt-card {
		flex-direction: column;
		align-items: stretch;
		justify-content: center;
		padding: 10px 14px;
		height: 90px;
	}

	.login-prompt-content {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 6px;
	}

	.login-prompt-text {
		color: #2F5D62;
		font-size: 16px;
		font-weight: 600;
	}

	.login-buttons {
		display: flex;
		flex-direction: row;
		gap: 10px;
	}

	.login-btn2,
	.register-btn2 {
		// padding: 10px;
		border-radius: 8px;
		font-size: 14px;
		font-weight: bold;
		cursor: pointer;
		min-width: 120px;
		text-align: center;
		display: flex;
		flex-direction: column;
		justify-content: center;
		align-items: center;
		height: 32px;
		border-radius: 4px;
		font-size: 14px;
		font-weight: bold;
		box-shadow: 0px 2px 3px rgba(0, 0, 0, 0.25);
	}

	.login-btn2 {
		background-color: #2F5D62;
		color: white;
	}

	.register-btn2 {
		background-color: #5FB5BD;
		color: white;
	}

	/* from tangjq--- 导航图标区域 */
	.nav-icons-bar {
		display: flex;
		flex-direction: row;
		justify-content: space-around;
		align-items: center;
		padding: 0 10px;
	}

	.nav-icon-item {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: flex-start;
		gap: 8px;
		cursor: pointer;
		padding: 5px;
		transition: all 0.3s;
		flex: 1;
		min-width: 0;
		height: 75px;
	}

	.nav-icon-item:active {
		transform: scale(0.95);
	}

	.nav-icon-wrapper {
		position: relative;
		display: flex;
		align-items: center;
		justify-content: center;
		transition: all 0.3s;
	}

	.nav-icon-active .nav-icon-wrapper {
		background-color: white;
		background-color: #2F5D62;
	}

	.nav-icon {
		width: 35px;
		height: 35px;
	}

	/* from tangjq--- 导航徽章（红点通知） */
	.nav-badge {
		position: absolute;
		top: -2px;
		right: -2px;
		min-width: 18px;
		height: 18px;
		border-radius: 9px;
		background-color: #FF4444;
		color: white;
		font-size: 10px;
		font-weight: bold;
		display: flex;
		align-items: center;
		justify-content: center;
		padding: 0 4px;
		border: 2px solid #2F5D62;
	}

	.nav-icon-label {
		color: rgba(255, 255, 255, 0.7);
		font-size: 12px;
		font-weight: 500;
		transition: all 0.3s;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
		max-width: 100%;
		text-align: center;
	}

	.nav-label-active {
		color: #5FB5BD;
		font-weight: bold;
	}
</style>