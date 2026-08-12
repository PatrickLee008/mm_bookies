<template>
	<view class="contact-page full-page">
		<!-- 顶部栏 -->
		<view class="contact-header">
			<text class="header-back-icon" @click="goBack">←</text>
			<text class="header-title">{{ $t('contact us') }}</text>
			<text class="header-close-icon" @click="goBack">✕</text>
		</view>

		<scroll-view scroll-y style="height: calc(100vh - 88px);">
			<view class="contact-content">
				<!-- 标题部分 -->
				<text class="contact-section-title">{{ $t('Contact') }}</text>
				<!-- 隐藏 contact-description -->
				<text class="contact-description" v-if="false">{{ $t('explore_website') }}</text>

				<!-- 富文本显示 contact_us 内容 -->
				<view class="contact-rich-text" v-if="$store.state.configs && $store.state.configs.contact_us">
					<rich-text :nodes="contactUsRichText" @itemclick="handleRichTextClick"></rich-text>
				</view>

				<!-- 原来的联系方式列表，用 v-if="false" 隐藏 -->
				<view v-if="false">
					<view class="contact-item">
						<text class="contact-label">{{ $t('viber') }}</text>
						<view class="contact-value-row">
							<text class="contact-value">{{ contactInfo.viber || '09789456123' }}</text>
							<view class="copy-btn" @click="copyText(contactInfo.viber || '09789456123')">
								<text class="copy-btn-text">{{ $t('copy') }}</text>
								<image class="copy-icon" src="/static/icon/copy.png" mode="aspectFit"></image>
							</view>
						</view>
					</view>

					<view class="contact-item">
						<text class="contact-label">{{ $t('telegram') }}</text>
						<view class="contact-value-row">
							<text class="contact-value">{{ contactInfo.telegram || '09789456123' }}</text>
							<view class="copy-btn" @click="copyText(contactInfo.telegram || '09789456123')">
								<text class="copy-btn-text">{{ $t('copy') }}</text>
								<image class="copy-icon" src="/static/icon/copy.png" mode="aspectFit"></image>
							</view>
						</view>
					</view>

					<view class="contact-item">
						<text class="contact-label">{{ $t('email') }}</text>
						<view class="contact-value-row">
							<text class="contact-value">{{ contactInfo.email || 'mmbookies@test.com' }}</text>
							<view class="copy-btn" @click="copyText(contactInfo.email || 'mmbookies@test.com')">
								<text class="copy-btn-text">{{ $t('copy') }}</text>
								<image class="copy-icon" src="/static/icon/copy.png" mode="aspectFit"></image>
							</view>
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
		computed: {
			contactUsRichText() {
				// 将 contact_us 内容转换为 rich-text 组件所需的 nodes 格式
				if (this.$store.state.configs && this.$store.state.configs.contact_us) {
					return this.parseHtmlToNodes(this.$store.state.configs.contact_us)
				}
				return []
			}
		},
		methods: {
			// 富文本点击事件处理
			handleRichTextClick(e) {
				const node = e.detail.node
				if (node && node.name === 'a' && node.attrs) {
					const href = node.attrs.href
					if (href) {
						if (href.startsWith('http://') || href.startsWith('https://')) {
							// 处理网页链接
							// #ifdef H5
							window.open(href, '_blank')
							// #endif
							// #ifndef H5
							uni.navigateTo({
								url: `/pages/webview/index?url=${encodeURIComponent(href)}`
							})
							// #endif
						} else if (href.startsWith('tel:')) {
							// 处理电话链接
							const phoneNumber = href.replace('tel:', '')
							uni.makePhoneCall({
								phoneNumber: phoneNumber
							})
						}
					}
				}
			},
			// 解析 HTML 为 rich-text nodes 数组
			parseHtmlToNodes(html) {
				if (!html) return []
				
				// 简单的 HTML 解析器，提取 a 标签并保持其他内容
				const nodes = []
				let tempHtml = html
				
				// 正则匹配 a 标签
				const linkRegex = /<a[^>]*href=["']([^"']+)["'][^>]*>(.*?)<\/a>/gi
				let lastIndex = 0
				let match
				
				while ((match = linkRegex.exec(tempHtml)) !== null) {
					// 添加链接前的文本
					if (match.index > lastIndex) {
						const textBefore = tempHtml.substring(lastIndex, match.index)
						if (textBefore.trim()) {
							nodes.push({
								name: 'text',
								attrs: {},
								children: [{
									type: 'text',
									text: textBefore
								}]
							})
						}
					}
					
					// 添加链接节点
					const href = match[1]
					const linkText = match[2]
					nodes.push({
						name: 'a',
						attrs: {
							href: href,
							style: 'color: var(--theme-primary, #1C667C); text-decoration: underline;'
						},
						children: [{
							type: 'text',
							text: linkText
						}]
					})
					
					lastIndex = match.index + match[0].length
				}
				
				// 添加剩余文本
				if (lastIndex < tempHtml.length) {
					const textAfter = tempHtml.substring(lastIndex)
					if (textAfter.trim()) {
						nodes.push({
							name: 'text',
							attrs: {},
							children: [{
								type: 'text',
								text: textAfter
							}]
						})
					}
				}
				
				// 如果没有解析到任何节点，就把整个 HTML 作为一个文本节点
				if (nodes.length === 0) {
					return [{
						name: 'div',
						attrs: {},
						children: [{
							type: 'text',
							text: html
						}]
					}]
				}
				
				return nodes
			},
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
				const _this = this
				// from tangjq--- 复制文本到剪贴板
				uni.setClipboardData({
					data: text,
					success: function() {
						uni.showToast({
							title: _this.$t('copied'),
							icon: 'success',
							duration: 1500
						})
					},
					fail: function() {
						uni.showToast({
							title: _this.$t('copy_failed'),
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
		background: $color-primary;
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
