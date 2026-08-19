<template>
	<view class="support-page full-page">
		<!-- 顶部栏 -->
		<view class="support-header">
			<text class="header-back-icon" @click="goBack">←</text>
			<text class="header-title">{{ $t('customer_support') }}</text>
			<text class="header-close-icon" @click="goBack">✕</text>
		</view>

		<scroll-view scroll-y style="height: calc(var(--app-viewport-height, 100vh) - 88px);">
			<view class="support-content">
				<!-- 标题部分 -->
				<text class="support-main-title">{{ $t('contact us') }}</text>
				<text class="support-description">{{ $t('explore_website') }}</text>

				<!-- 支持渠道列表 -->
				<view class="support-channel-section" v-for="(channel, channelIndex) in supportChannels" :key="channelIndex">
					<text class="channel-title">{{ channel.name }}</text>
					<view class="support-link" v-for="(link, linkIndex) in channel.links" :key="linkIndex" @click="openLink(link)">
						<text class="link-text">{{ link }}</text>
					</view>
				</view>
			</view>
		</scroll-view>
	</view>
</template>

<script>
	export default {
		name: "CustomerSupport",
		data() {
			return {
				supportChannels: [
					{
						name: 'KBZPay',
						links: [
							'https://contact.mmbookies/D1',
							'https://contact.mmbookies/D1',
							'https://contact.mmbookies/D1',
							'https://contact.mmbookies/D1'
						]
					},
					{
						name: 'KBZPay',
						links: [
							'https://contact.mmbookies/D1',
							'https://contact.mmbookies/D1',
							'https://contact.mmbookies/D1',
							'https://contact.mmbookies/D1'
						]
					}
				]
			}
		},
		onLoad() {
			this.loadSupportInfo()
		},
		methods: {
			goBack() {
				uni.navigateBack()
			},
			loadSupportInfo() {
				// from tangjq--- 从store或API加载客服信息
				if (this.$store.state.configs && this.$store.state.configs.customer_support) {
					// 可以根据实际数据格式解析
					// this.supportChannels = ...
				}
			},
			openLink(url) {
				// from tangjq--- 打开链接
				//#ifdef H5
				window.open(url, '_blank')
				//#endif

				//#ifdef APP-PLUS
				plus.runtime.openURL(url)
				//#endif

				//#ifdef MP
				uni.setClipboardData({
					data: url,
					success: function() {
						uni.showToast({
							title: 'Link copied',
							icon: 'success'
						})
					}
				})
				//#endif
			}
		}
	}
</script>

<style lang="scss" scoped>
	.support-page {
		background: #f5f5f5;
		min-height: var(--app-viewport-height, 100vh);
	}

	/* 顶部栏 */
	.support-header {
		background: #3d6877;
		padding: 40px 20px 20px 20px;
		display: flex;
		justify-content: space-between;
		align-items: center;
	}

	.header-back-icon, .header-close-icon {
		width: 40px;
		font-size: 24px;
		color: #fff;
		font-weight: 300;
	}

	.header-title {
		font-size: 18px;
		font-weight: 700;
		color: #fff;
		flex: 1;
		text-align: center;
	}

	/* 内容区域 */
	.support-content {
		padding: 30px 20px;
	}

	.support-main-title {
		font-size: 18px;
		font-weight: 700;
		color: #1e3a5f;
		display: block;
		margin-bottom: 12px;
	}

	.support-description {
		font-size: 14px;
		color: #5a7a8f;
		line-height: 1.6;
		display: block;
		margin-bottom: 30px;
	}

	.support-channel-section {
		margin-bottom: 30px;
	}

	.channel-title {
		font-size: 16px;
		font-weight: 700;
		color: #1e3a5f;
		display: block;
		margin-bottom: 12px;
	}

	.support-link {
		background: #fff;
		border-radius: 8px;
		padding: 14px;
		margin-bottom: 8px;
		box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
	}

	.link-text {
		font-size: 14px;
		color: #3d6877;
		text-decoration: underline;
	}
</style>
