<template>
	<view class="customer-service-wrapper">
		<!-- 悬浮客服按钮 -->
		<view class="customer-float-btn" @click="openCustomerService">
			<image
				:src="showModal ? '/static/icon/ai-close.svg' : '/static/icon/ai-chat.svg'"
				mode="aspectFit"
				class="customer-btn-icon"
			></image>
		</view>

		<!-- 模态框遮罩层 -->
		<view class="modal-mask" v-if="showModal" @click="closeModal"></view>

		<!-- 客服选项模态框 -->
		<view class="modal-content" v-if="showModal" @click.stop>
			<!-- 标题区域 -->
			<view class="modal-header">
				<view class="modal-title">{{ $t('welcome_to_live_chat') }}</view>
				<view class="modal-subtitle">{{ $t('how_can_we_help') }}</view>
			</view>

			<!-- 选项列表 -->
			<view class="modal-body">
				<!-- 预定义问题选项 -->
				<view class="modal-option" v-for="(item, index) in faqOptions" :key="index" @click="openCustomerService">
					<text class="option-text">{{ item }}</text>
					<text class="option-arrow">›</text>
				</view>

				<!-- AI Agent 选项 -->
				<view class="modal-option ai-option" @click="openCustomerService">
					<view class="ai-option-content">
						<text class="ai-option-title">{{ $t('chat_with_ai_agent') }}</text>
						<text class="ai-option-subtitle">{{ $t('ai_agent_subtitle') }}</text>
					</view>
					<text class="option-arrow-large">➤</text>
				</view>
			</view>

			<!-- 关闭按钮 -->
			<view class="modal-footer">
				<view class="close-btn" @click="closeModal">
					<text class="close-btn-text">{{ $t('cancel') }}</text>
				</view>
			</view>
		</view>
	</view>
</template>

<script>
export default {
	name: 'CustomerService',
	data() {
		return {
			showModal: false
		}
	},
	computed: {
		// 获取用户信息
		userInfo() {
			return this.$store.state.userInfo || {}
		},
		// 判断是否登录
		isLogin() {
			return this.userInfo && this.userInfo.id
		},
		// FAQ选项列表（使用翻译键）
		faqOptions() {
			return [
				this.$t('faq_how_to_deposit'),
				this.$t('faq_how_to_withdraw'),
				this.$t('faq_bank_account')
			]
		},
		// 生成客服链接
		customerServiceUrl() {
			// TODO: 替换为实际的客服链接
			const baseUrl = 'https://chat.wellytalk.com/MDE5ZDA1MDItYzU3MC03YjYyLThkMGItMjQ4YTJjMjQ0ODkwfGQzZjQwNTg3NzExOTAzMjFmOWU4MWM4ZDZmMGM4ZDQ4YjAyNDg5ZjQyM2EyZjgyZjc2NmJmMjI2ZTdlM2MxMzA='
			const params = []

			if (this.isLogin) {
				params.push(`user_id=${this.userInfo.id}`)
				params.push(`user_name=${encodeURIComponent(this.userInfo.phone || this.userInfo.nick_name || '')}`)
			} else {
				const guest = this.getOrCreateGuestIdentity()
				params.push(`user_id=${guest.id}`)
				params.push(`user_name=${encodeURIComponent(guest.name)}`)
			}

			params.push('website_name=mmbookies')

			return `${baseUrl}?${params.join('&')}`
		}
	},
	methods: {
		// 打开客服链接（用于外部调用）
		showAndOpen() {
			this.showModal = true
		},
		// 切换模态框显示状态
		toggleModal() {
			this.showModal = !this.showModal
		},
		// 关闭模态框
		closeModal() {
			this.showModal = false
		},
		// 打开客服链接
		openCustomerService() {
			const url = this.customerServiceUrl

			uni.navigateTo({
				url: `/pages/webview/index?url=${encodeURIComponent(url)}`
			})

			// 关闭模态框
			this.closeModal()
		},
		// 获取或创建游客唯一身份（持久化存储，保证同一设备每次相同）
		getOrCreateGuestIdentity() {
			const STORAGE_KEY = 'guest_cs_identity'
			let identity = null
			try {
				identity = JSON.parse(uni.getStorageSync(STORAGE_KEY) || 'null')
			} catch (e) {}

			if (!identity || !identity.id || !identity.name) {
				// 生成唯一ID：时间戳 + 随机串
				const rand = Math.random().toString(36).slice(2, 10).toUpperCase()
				const ts = Date.now().toString(36).toUpperCase()
				identity = {
					id: `G_${ts}${rand}`,
					name: `Guest_${Math.floor(Math.random() * 900000) + 100000}`
				}
				try {
					uni.setStorageSync(STORAGE_KEY, JSON.stringify(identity))
				} catch (e) {}
			}
			return identity
		}
	}
}
</script>

<style lang="scss" scoped>
.customer-service-wrapper {
	position: relative;
}

/* 悬浮客服按钮 */
.customer-float-btn {
	position: fixed;
	right: 20px;
	bottom: 100px;
	width: 60px;
	height: 60px;
	border-radius: 50%;
	background: linear-gradient(135deg, #2F5D62, #5FB5BD);
	display: flex;
	align-items: center;
	justify-content: center;
	box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
	z-index: 998;
	cursor: pointer;
}

.customer-btn-icon {
	width: 32px;
	height: 32px;
}

/* 模态框遮罩层 */
.modal-mask {
	position: fixed;
	top: 0;
	left: 0;
	right: 0;
	bottom: 0;
	background-color: rgba(0, 0, 0, 0.5);
	z-index: 999;
	animation: fadeIn 0.3s ease;
}

/* 模态框内容 */
.modal-content {
	position: fixed;
	bottom: 170px;
	right: 20px;
	width: 340px;
	background-color: #ffffff;
	border-radius: 20px;
	box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
	z-index: 1000;
	overflow: hidden;
	animation: slideUp 0.3s ease;
}

/* 标题区域 */
.modal-header {
	background: linear-gradient(135deg, #2F5D62 0%, #5FB5BD 100%);
	padding: 20px;
	color: #ffffff;
}

.modal-title {
	font-size: 18px;
	font-weight: bold;
	margin-bottom: 6px;
	text-align: left;
}

.modal-subtitle {
	font-size: 13px;
	opacity: 0.9;
	text-align: left;
}

/* 选项列表 */
.modal-body {
	padding: 10px 0;
}

.modal-option {
	display: flex;
	align-items: center;
	justify-content: space-between;
	padding: 16px 20px;
	border-bottom: 1px solid #f0f0f0;
	transition: background-color 0.2s ease;

	&:active {
		background-color: #f5f5f5;
	}

	&:last-child {
		border-bottom: none;
	}
}

.option-text {
	font-size: 14px;
	color: #333333;
	flex: 1;
	text-align: left;
}

.option-arrow {
	font-size: 24px;
	color: #999999;
	margin-left: 10px;
	flex-shrink: 0;
}

/* AI Agent 选项特殊样式 */
.ai-option {
	background-color: #f8f9fa;
	margin-top: 5px;
}

.ai-option-content {
	flex: 1;
	display: flex;
	flex-direction: column;
	text-align: left;
}

.ai-option-title {
	font-size: 14px;
	font-weight: bold;
	color: #2F5D62;
	margin-bottom: 4px;
	text-align: left;
}

.ai-option-subtitle {
	font-size: 11px;
	color: #666666;
	text-align: left;
}

.option-arrow-large {
	font-size: 20px;
	color: #2F5D62;
	margin-left: 10px;
	flex-shrink: 0;
}

/* 底部关闭按钮 */
.modal-footer {
	padding: 10px 20px 15px;
}

.close-btn {
	background: #f0f0f0;
	border-radius: 8px;
	padding: 12px;
	text-align: center;
}

.close-btn-text {
	font-size: 14px;
	font-weight: 600;
	color: #666;
}

/* 动画 */
@keyframes fadeIn {
	from { opacity: 0; }
	to { opacity: 1; }
}

@keyframes slideUp {
	from {
		transform: translateY(20px);
		opacity: 0;
	}
	to {
		transform: translateY(0);
		opacity: 1;
	}
}
</style>
