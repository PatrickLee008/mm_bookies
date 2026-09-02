<template>
	<view class="home-page theme-bg-no-header">
		<global-notice ref="globalNotice"></global-notice>
		<scroll-view scroll-y class="home-scroll">
			<view class="home-top">
				<theme-logo variant="page" height="var(--theme-home-logo-height)" class="home-logo"></theme-logo>
				<view class="home-subtitle"></view>

				<view class="user-summary">
					<view class="user-avatar">
						<image src="/static/user_avatar.svg" class="avatar-img" mode="aspectFit"></image>
					</view>
					<view class="user-details">
						<text class="greeting">{{ $t(greetingKey) }}</text>
						<text class="id-value">My ID : {{ userInfo.id || '' }}</text>
					</view>
					<view class="header-actions">
						<view class="bell-btn" @click="goMessage">
							<image src="/static/icon/nav/notification.svg" class="bell-icon"
								:class="{ 'bell-ring': unreadCount > 0 }" mode="aspectFit"></image>
							<view class="bell-badge" v-if="unreadCount > 0">{{ unreadCount > 99 ? '99+' : unreadCount }}
							</view>
						</view>
						<view class="settings-btn" @click="goto('/pages/ucenter/home')">
							<image src="/static/icon/nav/settings.png" class="settings-icon" mode="aspectFit"></image>
						</view>
					</view>
				</view>

				<view class="balance-card">
					<view class="main-balance-row">
						<view class="balance-item">
							<image src="/static/icon/nav/coin.png" class="coin-icon" mode="aspectFit"></image>
							<text class="balance-value">{{ displayBalance(userInfo.money) }}</text>
						</view>
						<text class="balance-eye"
							:class="balanceVisible ? 'cuIcon-attentionfill' : 'cuIcon-attentionforbidfill'"
							@click="balanceVisible = !balanceVisible"></text>
					</view>
					<view class="promo-row">
						<text class="promo-label">Promo</text>
						<text class="cashout-value">{{ displayBalance(userInfo.money_promotion) }}</text>
					</view>
					<view class="balance-actions">
						<view class="wallet-action" @click="goto('/pages/wallet/wallet?tab=0')">
							<theme-icon name="deposit" class="wallet-action-icon"></theme-icon>
							<text>{{$t('Deposit')}}</text>
						</view>
						<view class="wallet-action" @click="goto('/pages/wallet/wallet?tab=1')">
							<theme-icon name="withdraw" class="wallet-action-icon"></theme-icon>
							<text>{{$t('Withdraw')}}</text>
						</view>
						<view class="cashout-action">{{$t('cash_out')}} {{ displayBalance(userInfo.total_withdraw) }}
						</view>
					</view>
				</view>

				<view class="home-nav">
					<view class="nav-item" @click="goto('/pages/match/home?mix=0')">
						<theme-icon name="single" class="nav-theme-icon"></theme-icon><text>{{$t('single')}}</text>
					</view>
					<view class="nav-item" @click="goto('/pages/match/home?mix=1')">
						<theme-icon name="mixparlay"
							class="nav-theme-icon"></theme-icon><text>{{$t('mixparlay')}}</text>
					</view>
					<view class="nav-item" @click="goto('/pages/ucenter/invite/index')">
						<theme-icon name="referral" class="referral-icon"></theme-icon>
						<text>{{$t('Referral')}}</text>
					</view>
					<view class="nav-item" @click="goto('/pages/orders/home')">
						<theme-icon name="history" class="nav-theme-icon"></theme-icon>
						<text>{{$t('history')}}</text>
					</view>
					<view class="nav-item" @click="goto('/pages/index/coupon')">
						<theme-icon name="deals" class="nav-theme-icon"></theme-icon><text>{{$t('Deals')}}</text>
					</view>
					<view class="nav-item" @click="goto('/pages/wallet/wallet')">
						<theme-icon name="wallet" class="nav-theme-icon"></theme-icon><text>{{$t('wallet')}}</text>
					</view>
				</view>
			</view>

			<view class="news-section" v-if="advertisements.length">
				<text class="section-title">News &amp; Promotions</text>
				<swiper class="promotion-swiper" :circular="true" :autoplay="true" interval="3500" duration="500"
					indicator-dots>
					<swiper-item v-for="(ad, index) in advertisements" :key="index" @click="handleAdClick(ad)">
						<image class="promotion-image"
							:src="ad.image_urls && ad.image_urls.length ? ad.image_urls[0] : ad.url" mode="scaleToFill">
						</image>
					</swiper-item>
				</swiper>
			</view>
		</scroll-view>
		<customer-service></customer-service>
	</view>
</template>

<script>
	import CustomerService from '@/components/common/customer-service.vue'
	import {
		getUnreadCount
	} from '@/utils/api/message.js'

	export default {
		components: {
			CustomerService
		},
		data() {
			return {
				userInfo: {},
				unreadCount: 0,
				advertisements: [],
				balanceVisible: true
			}
		},
		computed: {
			greetingKey() {
				const hour = new Date().getHours()
				if (hour < 12) return 'Good Morning'
				if (hour < 18) return 'Good Afternoon'
				return 'Good Evening'
			}
		},
		methods: {
			displayBalance(value) {
				const formattedBalance = this.$toolbox.floor_format(value || 0)
				return this.balanceVisible ? formattedBalance : formattedBalance.replace(/\d/g, '*')
			},
			goto(url) {
				uni.navigateTo({
					url
				})
			},
			goMessage() {
				uni.navigateTo({
					url: '/pages/ucenter/message'
				})
			},
			updateUnreadCount() {
				if (!uni.getStorageSync('Authorization')) {
					this.unreadCount = 0
					return
				}
				getUnreadCount().then((count) => {
					this.unreadCount = count || 0
				}).catch(() => {
					this.unreadCount = 0
				})
			},
			getUserInfo() {
				this.$http.get('/app_user/user_info', {}, (res) => {
					if (res.statusCode === 200) {
						this.userInfo = res.data.data || {}
						this.$store.dispatch('saveUserInfo', this.userInfo)
					}
				})
			},
			getAdvertisements() {
				const _this = this
				this.$http.post('/advertisement/get_by_page', {
					platform: 'mobile',
					page: 'home',
					position: 'banner'
				}, (res) => {
					if (res.statusCode == 200 && res.data.code == 200) {
						_this.advertisements = res.data.data.items || []
					}
				})
			},
			handleAdClick(ad) {
				if (!ad.link_url) return
				this.$toolbox.openAdvertisementLink(ad.link_url, ad.link_target)
			},
			show_login_toast() {
				// 登录/注册成功后跳转到首页时提示，一次性消费并清除标志
				if (!uni.getStorageSync('login_success')) return
				let title = `${this.$t('Congratulations')}!\r\n${this.$t('login_success')}`
				if (uni.getStorageSync('rigister_success')) {
					title = `${this.$t('Congratulations')}!\r\n${this.$t('register_success')}`
				}
				uni.showToast({
					title: title,
					icon: 'none'
				})
				uni.removeStorageSync('login_success')
				uni.removeStorageSync('rigister_success')
			}
		},
		onShow() {
			if (!uni.getStorageSync('Authorization')) {
				uni.reLaunch({
					url: '/pages/login/login'
				})
				return
			}
			this.show_login_toast()
			this.getUserInfo()
			this.getAdvertisements()
			this.updateUnreadCount()
		},
		onLoad() {
			uni.$on('message:unreadUpdate', this.updateUnreadCount)
			uni.$on('message:update', this.updateUnreadCount)
		},
		onUnload() {
			uni.$off('message:unreadUpdate', this.updateUnreadCount)
			uni.$off('message:update', this.updateUnreadCount)
		}
	}
</script>

<style lang="scss">
	.home-page {
		height: var(--app-viewport-height, 100vh);
		display: flex;
		flex-direction: column;
		overflow: hidden;
	}

	.home-top {
		padding: 18px 20px 16px;
		border-bottom: 2px solid $color-home-top-border;
		box-shadow: 0px 4px 4px 0px #A0FF82;
		box-shadow: 0px 4px 20px 0px #FFFFFF00 inset;
		border-bottom-left-radius: 12px;
		border-bottom-right-radius: 12px;
	}

	/* #ifdef APP-PLUS */
	/* App端显示手机状态栏后，状态栏悬浮在页面顶部，主页内容下移一个状态栏高度 */
	.home-top {
		padding-top: calc(var(--status-bar-height) + 18px);
	}

	/* #endif */

	.home-logo {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 100%;
		height: var(--theme-home-logo-height, #{$theme-home-logo-height-value});
		margin: 3vh 0 5px;
	}

	.home-subtitle {
		display: block;
		margin: 3px auto 3vh;
		color: $theme-background-foreground;
		font-size: 12px;
		text-align: center;
	}

	.home-subtitle::after {
		content: var(--theme-subtitle, "#{$theme-subtitle-value}");
	}

	.user-info-card {
		background-color: white;
		border-radius: 20px;
		padding: 5px 12px 10px;
		box-sizing: border-box;
		display: flex;
		flex-direction: row;
		align-items: center;
		min-height: 90px;
	}

	.user-avatar {
		width: 37px;
		height: 37px;
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
		overflow: hidden;
		flex-shrink: 0;
		margin-right: 10px;
	}

	.avatar-img {
		width: 100%;
		height: 100%;
		background-color: #ffffff;
	}

	.user-details {
		flex: 1;
		min-width: 0;
		display: flex;
		flex-direction: column;
		gap: 4px;
	}

	.user-id {
		display: flex;
		align-items: center;
		flex-direction: row;
		justify-content: space-between;
	}

	.user-id-info {
		display: flex;
		flex: 1;
		min-width: 0;
		align-items: center;
		flex-direction: row;
		font-size: 15px;
	}

	.id-label,
	.id-value,
	.cashout-label,
	.cashout-value {
		color: $color-primary;
	}

	.id-label {
		font-weight: 600;
	}

	.id-value {
		font-weight: bold;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.header-actions {
		display: flex;
		align-items: center;
		gap: 6px;
		flex-shrink: 0;
	}

	.bell-btn,
	.settings-btn {
		position: relative;
		width: 32px;
		height: 32px;
		display: flex;
		align-items: center;
		justify-content: center;
		flex-shrink: 0;
	}

	.bell-icon,
	.settings-icon {
		width: 22px;
		height: 22px;
		filter: $theme-background-foreground-filter;
	}

	.bell-icon.bell-ring {
		animation: bellRing 1s ease-in-out infinite;
		transform-origin: top center;
	}

	.bell-badge {
		position: absolute;
		top: -5px;
		right: -2px;
		width: 18px;
		height: 18px;
		min-width: 18px;
		padding: 0;
		border-radius: 50%;
		background-color: #FF4444;
		color: #ffffff;
		font-size: 8px;
		font-weight: bold;
		line-height: 1;
		display: flex;
		align-items: center;
		justify-content: center;
		text-align: center;
		box-sizing: border-box;
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
		align-items: center;
		flex-direction: row;
		gap: 5px;
		white-space: nowrap;
	}

	.secondary-balance-row {
		display: flex;
		align-items: center;
		gap: 5px;
	}

	.coin-icon {
		width: 20px;
		height: 20px;
		margin-right: 0px;
	}

	.balance-value {
		color: $color-primary;
		font-size: 18px;
	}

	.cashout-label,
	.cashout-value {
		font-size: 12px;
		font-weight: bold;
	}

	.cashout-label {
		white-space: nowrap;
		font-weight: bold;
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


	.home-nav {
		display: grid;
		grid-template-columns: repeat(3, 1fr);
		gap: 16px 10px;
		margin-top: 14px;
	}

	.nav-item {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		height: 86px;
		border: 1px solid $color-border;
		border-radius: $radius-large;
		background: #fff;
		color: $color-primary;
		font-size: 12px;
		font-weight: 700;
	}

	.nav-item image,
	.nav-item .theme-icon {
		width: 38px;
		height: 38px;
		margin-bottom: 7px;
		filter: none;
	}

	.nav-item text {
		max-width: 100%;
		text-align: center;
		line-height: 1.2;
	}

	.nav-item .referral-icon {
		filter: none;
	}

	.home-scroll {
		flex: 1;
		min-height: 0;
		height: 0;
	}

	.news-section {
		padding: 18px 20px 32px;
		background: transparent;
	}

	.section-title {
		display: block;
		margin-bottom: 14px;
		color: $theme-background-foreground;
		font-size: 21px;
		font-weight: 700;
	}

	.promotion-swiper,
	.empty-promotion {
		width: 100%;
		height: 35.73vw;
		overflow: hidden;
		border-radius: $radius-large;
		// background: #e9eeee;
	}

	.promotion-image {
		width: 100%;
		height: 100%;
	}

	.empty-promotion {
		display: flex;
		align-items: center;
		justify-content: center;
		color: $color-primary;
	}

	.user-summary {
		display: flex;
		align-items: center;
		padding: 8px 4px 14px;
		color: $theme-background-foreground;
	}

	.user-summary .user-avatar {
		width: 37px;
		height: 37px;
		margin-right: 12px;
		border: 0;
		background: transparent;
	}

	.user-summary .user-details {
		gap: 2px;
	}

	.greeting {
		font-size: 12px;
		color: $theme-background-foreground;
	}

	.user-summary .id-value {
		color: $theme-background-foreground;
		font-size: 15px;
		display: block;
		max-width: 100%;
		min-width: 0;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.user-summary .header-actions {
		margin-left: auto;
	}

	.user-summary .avatar-img {
		background: transparent;
		filter: $theme-background-foreground-filter;
	}

	.balance-card {
		background: #fff;
		border: 1px solid $color-border;
		border-radius: 16px;
		padding: 14px 20px 16px;
		color: $color-primary;
	}

	.main-balance-row,
	.promo-row,
	.balance-actions {
		display: flex;
		align-items: center;
	}

	.main-balance-row {
		justify-content: space-between;
	}

	.balance-value {
		font-size: 24px;
		font-weight: 700;
	}

	.balance-eye {
		font-size: 20px;
		color: $color-primary;
	}

	.promo-row {
		gap: 8px;
		margin: 7px 0 12px;
	}

	.promo-label {
		padding: 3px 12px;
		border-radius: 12px;
		background: $color-secondary;
		color: white;
		font-size: 11px;
		font-weight: 700;
	}

	.balance-actions {
		justify-content: space-between;
		gap: 8px;
		font-size: 11px;
		font-weight: 700;
	}

	.wallet-action {
		display: flex;
		align-items: center;
		gap: 6px;
		white-space: nowrap;
	}

	.wallet-action image {
		width: 20px;
		height: 20px;
	}

	.wallet-action .wallet-action-icon {
		width: 20px;
		height: 20px;
	}

	.cashout-action {
		white-space: nowrap;
	}

	.customer-service-wrapper :deep(.customer-btn) {
		background: $color-primary;
		border: 1px solid $color-border-other;
		border-radius: 50%;
		box-sizing: border-box;
	}

	.customer-service-wrapper :deep(.customer-btn-icon) {
		width: 24px;
		height: 24px;
	}
</style>