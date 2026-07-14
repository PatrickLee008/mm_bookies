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
							<text class="id-label">{{ $t('my_phone') }} : </text>
							<text class="id-value">{{userInfo.phone || ''}}</text>
						</view>
						<!-- 右侧操作区：消息铃铛 + 设置 -->
						<view class="header-actions">
							<!-- 消息铃铛入口：有未读时变红并摇动 -->
							<view class="bell-btn" @click="goMessage">
								<text class="cuIcon-noticefill bell-icon" :class="{ 'bell-ring': unreadMessageCount > 0 }"></text>
								<view class="bell-badge" v-if="unreadMessageCount > 0">{{ unreadMessageCount > 99 ? '99+' : unreadMessageCount }}</view>
							</view>
							<!-- 设置按钮 -->
							<view class="settings-btn" @click="goto('/pages/ucenter/home', 1)">
								<image src="/static/icon/nav/settings.png" class="settings-icon" mode="aspectFit"></image>
							</view>
						</view>
					</view>
					<view class="user-balance-row">
						<!-- Balance -->
						<view class="balance-item">
							<image src="/static/icon/nav/coin.png" class="coin-icon" mode="aspectFit"></image>
							<text class="balance-label">{{ $t('balance') }}</text>
							<text class="balance-value">{{$toolbox.num_format(userInfo.money) || '0'}}</text>
						</view>
						<!-- Cash Out -->
						<view class="balance-item">
							<text class="cashout-label">{{ $t('cash_out') }}</text>
							<text class="cashout-value">{{$toolbox.num_format(userInfo.total_withdraw) || '0'}}</text>
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

			<!-- from tangjq--- 导航图标区域 -->
			<view class="nav-icons-bar">
				<!-- Single -->
				<view class="nav-icon-item" :class="{'nav-icon-active': activeNav === 'single'}" @click="goto('/pages/match/home?mix=0', 1)">
					<view class="nav-icon-wrapper">
						<image :src="activeNav === 'single' ? '/static/icon/nav/single_active.png' : '/static/icon/nav/single.png'" class="nav-icon" mode="aspectFit"></image>
					</view>
					<text class="nav-icon-label" :class="{'nav-label-active': activeNav === 'single'}">{{ $t('single') }}</text>
				</view>

				<!-- MPL -->
				<view class="nav-icon-item" :class="{'nav-icon-active': activeNav === 'mpl'}" @click="goto('/pages/match/home?mix=1', 1)">
					<view class="nav-icon-wrapper">
						<image :src="activeNav === 'mpl' ? '/static/icon/nav/mpl_active.png' : '/static/icon/nav/mpl.png'" class="nav-icon" mode="aspectFit"></image>
					</view>
					<text class="nav-icon-label" :class="{'nav-label-active': activeNav === 'mpl'}">{{ $t('MPL') }}</text>
				</view>

				<!-- E-Games -->
				<view class="nav-icon-item" :class="{'nav-icon-active': activeNav === 'games'}" @click="goto('/pages/index/game', 1)" v-if="false">
					<view class="nav-icon-wrapper">
						<image :src="activeNav === 'games' ? '/static/icon/nav/games_active.png' : '/static/icon/nav/games.png'" class="nav-icon" mode="aspectFit"></image>
					</view>
					<text class="nav-icon-label" :class="{'nav-label-active': activeNav === 'games'}">{{ $t('e_games') }}</text>
				</view>

				<!-- History -->
				<view class="nav-icon-item" :class="{'nav-icon-active': activeNav === 'history'}" @click="goto('/pages/orders/home', 1)">
					<view class="nav-icon-wrapper">
						<image :src="activeNav === 'history' ? '/static/icon/nav/history_active.png' : '/static/icon/nav/history.png'" class="nav-icon" mode="aspectFit"></image>
						<!-- from tangjq--- 未读消息红点 -->
						<view class="nav-badge" v-if="unreadMessageCount > 0">{{unreadMessageCount > 9 ? '9+' : unreadMessageCount}}</view>
					</view>
					<text class="nav-icon-label" :class="{'nav-label-active': activeNav === 'history'}">{{ $t('history') }}</text>
				</view>

				<!-- Deals 暂时隐藏优惠券功能-->
				<view class="nav-icon-item" :class="{'nav-icon-active': activeNav === 'deals'}" @click="goto('/pages/index/coupon', 1)" >
					<view class="nav-icon-wrapper">
						<image :src="activeNav === 'deals' ? '/static/icon/nav/deals_active.png' : '/static/icon/nav/deals.png'" class="nav-icon" mode="aspectFit"></image>
					</view>
					<text class="nav-icon-label" :class="{'nav-label-active': activeNav === 'deals'}">Deals</text>
				</view>

				<!-- Wallet -->
				<view class="nav-icon-item" :class="{'nav-icon-active': activeNav === 'wallet'}" @click="goto('/pages/wallet/wallet', 1)">
					<view class="nav-icon-wrapper">
						<image :src="activeNav === 'wallet' ? '/static/icon/nav/wallet_active.png' : '/static/icon/nav/wallet.png'" class="nav-icon" mode="aspectFit"></image>
					</view>
					<text class="nav-icon-label" :class="{'nav-label-active': activeNav === 'wallet'}">{{ $t('wallet') }}</text>
				</view>
			</view>
		</view>
	</view>
</template>

<script>
	import {
		mapGetters
	} from 'vuex';
	import { getUnreadCount } from '@/utils/api/message.js'

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
					uni.reLaunch({ url: '/pages/login/login' })
					return
				}
				uni.navigateTo({ url: '/pages/ucenter/message' })
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

	/* from tangjq--- 用户信息卡片 */
	.user-info-card {
		background-color: white;
		border-radius: 20px;
		margin: 5px 15px 10px;
		padding: 10px 0px;
		display: flex;
		flex-direction: row;
		align-items: center;
		min-height: 70px;
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
		margin-right: 15px;
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
	}

	.id-label {
		color: #2F5D62;
		font-size: 14px;
		font-weight: 600;
	}

	.id-value {
		color: #2F5D62;
		font-size: 14px;
		font-weight: bold;
	}

	.user-balance-row {
		display: flex;
		flex-direction: row;
		align-items: center;
		gap: 15px;
	}

	.balance-item {
		display: flex;
		flex-direction: row;
		align-items: center;
		gap: 5px;
	}

	.coin-icon {
		width: 18px;
		height: 18px;
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
		font-size: 22px;
		color: #2F5D62;
		transform-origin: top center;
	}

	/* 有未读消息：变红 + 摇动 */
	.bell-ring {
		color: #FF4444;
		animation: bellRing 1s ease-in-out infinite;
	}

	@keyframes bellRing {
		0% { transform: rotate(0); }
		15% { transform: rotate(16deg); }
		30% { transform: rotate(-14deg); }
		45% { transform: rotate(11deg); }
		60% { transform: rotate(-8deg); }
		75% { transform: rotate(4deg); }
		100% { transform: rotate(0); }
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
		padding: 20px;
		height: 125px;
	}

	.login-prompt-content {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 15px;
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
		height: 40px;
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