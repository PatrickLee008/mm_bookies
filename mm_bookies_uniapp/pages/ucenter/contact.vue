<template>
	<view class="contact-page full-page">
		<!-- 顶部栏 -->
		<view class="contact-header">
			<text class="header-back-icon" @click="goBack">←</text>
			<text class="header-title">Contact Us</text>
			<text class="header-close-icon" @click="goBack">✕</text>
		</view>

		<scroll-view scroll-y style="height: calc(100vh - 88px);">
			<view class="contact-content">
				<!-- 标题部分 -->
				<text class="contact-section-title">Contact</text>
				<text class="contact-description">Explore our website for more information and updates!</text>

				<!-- 联系方式列表 -->
				<view class="contact-item">
					<text class="contact-label">Viber</text>
					<view class="contact-value-row">
						<text class="contact-value">{{ contactInfo.viber || '09789456123' }}</text>
						<view class="copy-btn" @click="copyText(contactInfo.viber || '09789456123')">
							<text class="copy-btn-text">Copy</text>
							<image class="copy-icon" src="/static/icon/copy.png" mode="aspectFit"></image>
						</view>
					</view>
				</view>

				<view class="contact-item">
					<text class="contact-label">Telegram</text>
					<view class="contact-value-row">
						<text class="contact-value">{{ contactInfo.telegram || '09789456123' }}</text>
						<view class="copy-btn" @click="copyText(contactInfo.telegram || '09789456123')">
							<text class="copy-btn-text">Copy</text>
							<image class="copy-icon" src="/static/icon/copy.png" mode="aspectFit"></image>
						</view>
					</view>
				</view>

				<view class="contact-item">
					<text class="contact-label">Email</text>
					<view class="contact-value-row">
						<text class="contact-value">{{ contactInfo.email || 'mmbookies@test.com' }}</text>
						<view class="copy-btn" @click="copyText(contactInfo.email || 'mmbookies@test.com')">
							<text class="copy-btn-text">Copy</text>
							<image class="copy-icon" src="/static/icon/copy.png" mode="aspectFit"></image>
						</view>
					</view>
				</view>
			</view>
		</scroll-view>
	</view>
</template>

<script>
	export default {
		name: "Contact",
		data() {
			return {
				contactInfo: {}
			}
		},
		onLoad() {
			this.loadContactInfo()
		},
		methods: {
			goBack() {
				uni.navigateBack()
			},
			loadContactInfo() {
				// from tangjq--- 从store或API加载联系方式
				if (this.$store.state.configs && this.$store.state.configs.contact_us) {
					// 解析联系方式数据
					let contactText = this.$store.state.configs.contact_us
					// 这里可以根据实际数据格式解析
					this.contactInfo = {
						viber: this.extractContact(contactText, 'viber'),
						telegram: this.extractContact(contactText, 'telegram'),
						email: this.extractContact(contactText, 'email')
					}
				}
			},
			extractContact(text, type) {
				// from tangjq--- 简单的提取逻辑，根据实际数据格式调整
				if (!text) return ''
				let lines = text.split('\n')
				for (let line of lines) {
					if (line.toLowerCase().includes(type)) {
						return line.split(':')[1]?.trim() || ''
					}
				}
				return ''
			},
			copyText(text) {
				// from tangjq--- 复制文本到剪贴板
				uni.setClipboardData({
					data: text,
					success: function() {
						uni.showToast({
							title: 'Copied!',
							icon: 'success',
							duration: 1500
						})
					},
					fail: function() {
						uni.showToast({
							title: 'Copy failed',
							icon: 'none',
							duration: 1500
						})
					}
				})
			}
		}
	}
</script>

<style lang="scss" scoped>
	.contact-page {
		background: #f5f5f5;
		min-height: 100vh;
	}

	/* 顶部栏 */
	.contact-header {
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
		font-size: 20px;
		font-weight: 700;
		color: #fff;
		flex: 1;
		text-align: center;
	}

	/* 内容区域 */
	.contact-content {
		padding: 30px 20px;
	}

	.contact-section-title {
		font-size: 20px;
		font-weight: 700;
		color: #1e3a5f;
		display: block;
		margin-bottom: 12px;
	}

	.contact-description {
		font-size: 14px;
		color: #5a7a8f;
		line-height: 1.6;
		display: block;
		margin-bottom: 30px;
	}

	.contact-item {
		background: #fff;
		border-radius: 12px;
		padding: 16px;
		margin-bottom: 16px;
		box-shadow: 0 2px 6px rgba(0, 0, 0, 0.06);
	}

	.contact-label {
		font-size: 16px;
		font-weight: 700;
		color: #1e3a5f;
		display: block;
		margin-bottom: 12px;
	}

	.contact-value-row {
		display: flex;
		justify-content: space-between;
		align-items: center;
		background: #f7f9fb;
		border-radius: 8px;
		padding: 12px;
	}

	.contact-value {
		font-size: 14px;
		color: #1e3a5f;
		flex: 1;
	}

	.copy-btn {
		background: #4fb3bf;
		border-radius: 8px;
		padding: 8px 16px;
		display: flex;
		align-items: center;
		gap: 6px;
	}

	.copy-btn-text {
		font-size: 14px;
		font-weight: 600;
		color: #fff;
	}

	.copy-icon {
		width: 18px;
		height: 18px;
	}
</style>
