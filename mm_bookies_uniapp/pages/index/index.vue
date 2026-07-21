<template>
	<view class="home-page">
		<global-notice ref="globalNotice"></global-notice>
		<view class="home-top">
			<image class="home-logo" src="../../figma/login/title.png" mode="widthFix"></image>
			<text class="home-subtitle">ရွှေမြန်မာတို့ အကြိုက် မြန်မာဘောဒိုင်</text>

			<view class="user-info-card">
				<view class="user-avatar">
					<image src="/static/icon/nav/user_avatar.png" class="avatar-img" mode="aspectFill"></image>
				</view>
				<view class="user-details">
					<view class="user-id">
						<view class="user-id-info">
							<text class="id-label">My ID : </text>
							<text class="id-value">{{ userInfo.phone || userInfo.nick_name || '' }}</text>
						</view>
						<view class="header-actions">
							<view class="bell-btn" @click="goMessage">
								<image src="/static/icon/nav/notification.svg" class="bell-icon"
									:class="{ 'bell-ring': unreadCount > 0 }" mode="aspectFit"></image>
								<view class="bell-badge" v-if="unreadCount > 0">
									{{ unreadCount > 99 ? '99+' : unreadCount }}
								</view>
							</view>
							<view class="settings-btn" @click="goto('/pages/ucenter/home')">
								<image src="/static/icon/nav/settings.png" class="settings-icon" mode="aspectFit">
								</image>
							</view>
						</view>
					</view>
					<view class="user-balance-row">
						<view class="balance-item">
							<image src="/static/icon/nav/coin.png" class="coin-icon" mode="aspectFit"></image>
							<text
								class="balance-value myfont-18px text-bold">{{ $toolbox.num_format(userInfo.money || 0) }}</text>
						</view>
						<view class="secondary-balance-row">
							<image src="/static/icon/nav/coin.png" class="coin-icon" mode="aspectFit"></image>
							<view class="balance-item">
								<text class="cashout-label">Promo</text>
								<text
									class="cashout-value">{{ $toolbox.num_format(userInfo.money_promotion || 0) }}</text>
							</view>
							<view class="balance-item" style="margin-left: 12px;">
								<text class="cashout-label">Cash Out</text>
								<text
									class="cashout-value">{{ $toolbox.num_format(userInfo.total_withdraw || 0) }}</text>
							</view>
						</view>
					</view>
				</view>
			</view>

			<view class="home-nav">
				<view class="nav-item" @click="goto('/pages/match/home?mix=0')">
					<image src="/static/icon/nav/single.png" mode="aspectFit"></image><text>{{$t('single')}}</text>
				</view>
				<view class="nav-item" @click="goto('/pages/match/home?mix=1')">
					<image src="/static/icon/nav/mpl.png" mode="aspectFit"></image><text>{{$t('mixparlay')}}</text>
				</view>
				<view class="nav-item" @click="goto('/pages/ucenter/invite/index')">
					<image class="referral-icon" src="/static/icon/ucenter/referral.svg" mode="aspectFit"></image>
					<text>{{$t('Referral')}}</text>
				</view>
				<view class="nav-item" @click="goto('/pages/orders/home')">
					<image src="/static/icon/nav/history.png" mode="aspectFit"></image><text>{{$t('history')}}</text>
				</view>
				<view class="nav-item" @click="goto('/pages/index/coupon')">
					<image src="/static/icon/nav/deals.png" mode="aspectFit"></image><text>{{$t('Deals')}}</text>
				</view>
				<view class="nav-item" @click="goto('/pages/wallet/wallet')">
					<image src="/static/icon/nav/wallet.png" mode="aspectFit"></image><text>{{$t('wallet')}}</text>
				</view>
			</view>
		</view>

		<scroll-view scroll-y class="home-scroll">
			<view class="news-section" v-if="advertisements.length">
				<text class="section-title">News &amp; Promotions</text>
				<swiper class="promotion-swiper" :circular="true" :autoplay="true" interval="3500" duration="500"
					indicator-dots>
					<swiper-item v-for="(ad, index) in advertisements" :key="index" @click="handleAdClick(ad)">
						<image class="promotion-image"
							:src="ad.image_urls && ad.image_urls.length ? ad.image_urls[0] : ad.url" mode="aspectFill">
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
				advertisements: []
			}
		},
		methods: {
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
					page: 'index',
					position: 'banner'
				}, (res) => {
					if (res.statusCode == 200 && res.data.code == 200) {
						_this.advertisements = res.data.data.items || []
					}
				})
			},
			handleAdClick(ad) {
				if (ad.link_url) uni.navigateTo({
					url: ad.link_url
				})
			}
		},
		onShow() {
			if (!uni.getStorageSync('Authorization')) {
				uni.reLaunch({
					url: '/pages/login/login'
				})
				return
			}
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
		height: 100vh;
		display: flex;
		flex-direction: column;
		overflow: hidden;
		background: #2a6268;
	}

	.home-top {
		flex-shrink: 0;
		padding: 18px 20px 16px;
	}

	.home-logo {
		display: block;
		width: 320px;
		max-width: 90%;
		margin: 3vh auto 5px;
	}

	.home-subtitle {
		display: block;
		margin: 3px auto 3vh;
		color: #fff;
		font-size: 12px;
		text-align: center;
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
		width: 50px;
		height: 50px;
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
		color: #2F5D62;
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
	}

	.bell-icon.bell-ring {
		animation: bellRing 1s ease-in-out infinite;
		transform-origin: top center;
	}

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
		line-height: normal;
		display: flex;
		align-items: center;
		justify-content: center;
		text-align: center;
		border: 1px solid #ffffff;
		box-sizing: border-box;
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
		width: 18px;
		height: 18px;
		margin-right: 7px;
	}

	.balance-value {
		color: #2F5D62;
		font-size: 18px;
	}

	.cashout-label,
	.cashout-value {
		font-size: 12px;
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
		gap: 12px 20px;
		margin-top: 14px;
	}

	.nav-item {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		height: 92px;
		border-radius: 16px;
		background: #fff;
		color: #2a6268;
		font-size: 12px;
		font-weight: 700;
	}

	.nav-item image {
		width: 38px;
		height: 38px;
		margin-bottom: 7px;
		filter: brightness(0) saturate(100%) invert(31%) sepia(14%) saturate(1119%) hue-rotate(138deg) brightness(89%) contrast(90%);
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
		background-color: #2a6268;
	}

	.section-title {
		display: block;
		margin-bottom: 14px;
		color: white;
		font-size: 21px;
		font-weight: 700;
	}

	.promotion-swiper,
	.empty-promotion {
		width: 100%;
		height: 200px;
		overflow: hidden;
		border-radius: 15px;
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
		color: #2a6268;
	}
</style>