<template>
	<view class="customer-service-wrapper">
		<!-- 悬浮客服按钮 -->
		<draggable-button :initial-right="20" :initial-bottom="100" storage-key="customer_btn_position" :btn-size="60"
			@click="toggleModal">
			<view class="customer-btn">
				<theme-icon :name="showModal ? 'ai-close' : 'ai-chat'" class="customer-btn-icon"
					color="var(--theme-icon-on-primary, #fff)"></theme-icon>
			</view>
		</draggable-button>

		<!-- #ifdef H5 -->
		<!-- 模态框遮罩层 -->
		<view class="modal-mask" v-if="showModal" @click="closeModal"></view>

		<!-- 聊天模态框 -->
		<view class="modal-content" :class="{'fullscreen': isFullscreen}" v-if="showModal" @click.stop>
			<!-- 标题区域 -->
			<view class="modal-header">
				<view class="header-left">
					<view class="modal-title">{{$t('welcome_to_live_chat')}}</view>
				</view>
				<view class="header-controls">
					<view class="control-btn" @click.stop="toggleFullscreen">
					<text class="control-icon">{{isFullscreen ? '⤡' : '⤢'}}</text>
					</view>
					<view class="control-btn" @click.stop="closeModal">
						<text class="control-icon" style="font-size:14px;line-height:1;font-weight:bold;">✕</text>
					</view>
				</view>
			</view>

			<!-- iframe 聊天内容 -->
			<view class="modal-iframe-body">
				<iframe :src="iframeUrl" frameborder="0" class="cs-iframe" @load="handleIframeLoad"></iframe>
			</view>
		</view>
		<!-- #endif -->

		<!-- #ifdef APP-PLUS -->
		<!-- App 端遮罩层 -->
		<view class="app-modal-mask" v-if="showModal" @click="closeModal"></view>

		<!-- App 端模态框 -->
		<view class="app-modal-wrapper" :class="{'fullscreen': isFullscreen}" :style="appModalWrapperStyle" v-if="showModal">
			<view class="app-modal-container" :style="appModalContainerStyle">
				<view class="app-modal-header">
					<view class="header-left">
						<view class="modal-title">{{$t('welcome_to_live_chat')}}</view>
					</view>
					<view class="header-controls">
						<view class="control-btn" @click.stop="toggleFullscreen">
							<image class="control-icon-img" :src="isFullscreen ? '/static/icon/fullscreen-off.svg' : '/static/icon/fullscreen.svg'" style="height: 12px;" mode="heightFix"></image>
						</view>
						<view class="control-btn" @click.stop="closeModal">
							<text class="control-icon" style="font-size:14px;line-height:1;font-weight:bold;">✕</text>
						</view>
					</view>
				</view>
				<view class="app-modal-body"></view>
				<view v-if="appKeyboardSpacerHeight > 0" class="app-keyboard-spacer" :style="{ height: appKeyboardSpacerHeight + 'px' }"></view>
			</view>
		</view>
		<!-- #endif -->
	</view>
</template>

<script>
	import DraggableButton from '@/components/common/draggable-button.vue'
	import siteinfo from '@/siteinfo'

	export default {
		name: 'CustomerService',
		components: {
			DraggableButton
		},
		data() {
			return {
				showModal: false,
				isFullscreen: false,
				iframeUrl: '',
				appWebview: null,
				isTogglingFullscreen: false,
				keyboardHeight: 0,
				baseWindowHeight: 0,
				keyboardHeightChangeHandler: null,
				keyboardResizeTimer: null,
				appLayoutSyncTimers: []
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
			// 生成客服链接
			customerServiceUrl() {
				const baseUrl = siteinfo.liveChatLink;
				const params = []

				if (this.isLogin) {
					params.push(`user_id=${this.userInfo.id}`)
					params.push(`user_name=${encodeURIComponent(this.userInfo.phone || this.userInfo.nick_name || '')}`)
				} else {
					const guest = this.getOrCreateGuestIdentity()
					params.push(`user_id=${guest.id}`)
					params.push(`user_name=${encodeURIComponent(guest.name)}`)
				}

				params.push('website_name=onex2')

				return `${baseUrl}?${params.join('&')}`
			},
			appModalWrapperStyle() {
				// #ifdef APP-PLUS
				if (this.isFullscreen) {
					return {}
				}
				return {
					height: `${this.getAppVisibleHeight()}px`
				}
				// #endif
				return {}
			},
			appModalContainerStyle() {
				// #ifdef APP-PLUS
				if (this.isFullscreen) {
					return {}
				}
				const layout = this.getAppModalLayout()
				return {
					top: `${layout.top}px`,
					height: `${layout.height}px`
				}
				// #endif
				return {}
			},
			appKeyboardSpacerHeight() {
				// #ifdef APP-PLUS
				return this.isFullscreen && this.keyboardHeight > 0 ? this.keyboardHeight : 0
				// #endif
				return 0
			}
		},
		mounted() {
			uni.$on('open-customer-service', this.toggleModal)
			uni.$on('open-customer-service-fullscreen', this.openFullscreenModal)
		},
		beforeDestroy() {
			uni.$off('open-customer-service', this.toggleModal)
			uni.$off('open-customer-service-fullscreen', this.openFullscreenModal)
		},
		methods: {
			openFullscreenModal() {
				// #ifdef APP-PLUS
				this.openAppCustomerServicePage()
				return
				// #endif
				this.toggleModal({
					fullscreen: true
				})
			},
			openAppCustomerServicePage() {
				const url = encodeURIComponent(this.customerServiceUrl)
				const title = encodeURIComponent(this.$t('welcome_to_live_chat'))
				uni.navigateTo({
					url: `/pages/customer-service/index?url=${url}&title=${title}`
				})
			},
			// 切换模态框显示状态，打开时直接加载聊天
			toggleModal(options = {}) {
				const openInFullscreen = !!(options && options.fullscreen)
				// #ifdef APP-PLUS
				this.openAppCustomerServicePage()
				return
				// #endif

				// #ifdef H5
				this.showModal = !this.showModal
				if (this.showModal) {
					this.isFullscreen = openInFullscreen
					this.iframeUrl = this.customerServiceUrl
				} else {
					this.isFullscreen = false
					this.iframeUrl = ''
				}
				// #endif
			},
			// 关闭模态框
			closeModal() {
				this.showModal = false
				this.isFullscreen = false
				this.iframeUrl = ''
				// #ifdef APP-PLUS
				this.keyboardHeight = 0
				this.clearAppLayoutSyncTimers()
				this.destroyAppWebview()
				// #endif
			},
			// 全屏切换
			toggleFullscreen() {
				// #ifdef APP-PLUS
				if (this.isTogglingFullscreen) return
				this.isTogglingFullscreen = true
				this.blurAppWebviewInput()
				this.hideAppKeyboard()
				setTimeout(() => {
					this.isFullscreen = !this.isFullscreen
					this.$nextTick(() => {
						this.queueAppWebviewLayoutSync(this.isFullscreen ? [20, 100, 220] : [80, 180, 320, 460])
					})
					setTimeout(() => {
						this.isTogglingFullscreen = false
					}, this.isFullscreen ? 280 : 560)
				}, 180)
				return
				// #endif
				this.isFullscreen = !this.isFullscreen
			},
			handleIframeLoad() {
				console.log('[CS] Iframe loaded')
			},
			// #ifdef APP-PLUS
			refreshAppWindowHeight() {
				const systemInfo = uni.getSystemInfoSync()
				const windowHeight = Number(systemInfo.windowHeight) || 0
				if (windowHeight > 0) {
					this.baseWindowHeight = windowHeight
				}
			},
			getAppVisibleHeight() {
				const baseHeight = this.baseWindowHeight || Number(uni.getSystemInfoSync().windowHeight) || 0
				return Math.max(baseHeight - this.keyboardHeight, 260)
			},
			getAppModalLayout() {
				const visibleHeight = this.getAppVisibleHeight()
				const outerMargin = this.keyboardHeight > 0 ? 12 : 20
				const baseHeight = this.baseWindowHeight || visibleHeight
				const targetHeight = Math.round(baseHeight * 0.6)
				const maxHeight = Math.max(baseHeight - outerMargin * 2, 220)
				const height = Math.min(targetHeight, maxHeight)
				let top = Math.max(outerMargin, Math.round((baseHeight - height) / 2))
				if (this.keyboardHeight > 0) {
					const maxTop = Math.max(outerMargin, visibleHeight - height - outerMargin)
					top = Math.min(top, maxTop)
				}
				return {
					top,
					height
				}
			},
			scheduleAppWebviewResize(delay = 60) {
				if (this.keyboardResizeTimer) {
					clearTimeout(this.keyboardResizeTimer)
				}
				this.keyboardResizeTimer = setTimeout(() => {
					this.resizeAppWebview()
				}, delay)
			},
			hideAppKeyboard() {
				if (typeof uni.hideKeyboard === 'function') {
					uni.hideKeyboard()
				}
				if (typeof plus !== 'undefined' && plus.key && typeof plus.key.hideSoftKeybord === 'function') {
					plus.key.hideSoftKeybord()
				}
			},
			blurAppWebviewInput() {
				if (!this.appWebview) return
				this.appWebview.evalJS(`
					(function () {
						var active = document.activeElement;
						if (active && typeof active.blur === 'function') {
							active.blur();
						}
					})();
				`)
			},
			syncFocusedInputIntoView(delay = 120) {
				if (!this.appWebview) return
				setTimeout(() => {
					if (!this.appWebview) return
					this.appWebview.evalJS(`
						(function () {
							try {
								var active = document.activeElement;
								if (!active) return;
								var tagName = (active.tagName || '').toLowerCase();
								if (tagName !== 'input' && tagName !== 'textarea') return;
								if (typeof active.scrollIntoView === 'function') {
									active.scrollIntoView({
										block: 'center',
										inline: 'nearest',
										behavior: 'auto'
									});
								}
								var rect = active.getBoundingClientRect();
								var viewportHeight = window.innerHeight || document.documentElement.clientHeight || 0;
								var overflow = rect.bottom - viewportHeight + 24;
								if (overflow > 0) {
									window.scrollBy(0, overflow);
								}
								window.dispatchEvent(new Event('resize'));
							} catch (e) {}
						})();
					`)
				}, delay)
			},
			applyWebviewKeyboardOffset() {
				if (!this.appWebview) return
				const offset = Math.max(Number(this.keyboardHeight) || 0, 0)
				this.appWebview.evalJS(`
					(function () {
						try {
							var offset = ${offset};
							var styleId = 'cs-keyboard-offset-style';
							var styleEl = document.getElementById(styleId);
							if (!styleEl) {
								styleEl = document.createElement('style');
								styleEl.id = styleId;
								document.head.appendChild(styleEl);
							}
							document.documentElement.style.setProperty('--cs-keyboard-offset', offset + 'px');
							document.documentElement.style.setProperty('--cs-keyboard-safe-offset', (offset ? offset + 24 : 0) + 'px');
							if (document.body) {
								document.body.style.paddingBottom = offset ? (offset + 24) + 'px' : '';
							}
							styleEl.textContent = offset ? [
								'html, body { padding-bottom: ' + (offset + 24) + 'px !important; }',
								'[style*="position:fixed"][style*="bottom"], [style*="position: fixed"][style*="bottom"] { bottom: var(--cs-keyboard-safe-offset) !important; }',
								'[style*="position:sticky"][style*="bottom"], [style*="position: sticky"][style*="bottom"] { bottom: var(--cs-keyboard-safe-offset) !important; }',
								'[class*="input"], [class*="Input"], [class*="composer"], [class*="Composer"], [class*="footer"], [class*="Footer"], [class*="send"], [class*="Send"] { bottom: auto; }'
							].join('\\n') : '';
							window.dispatchEvent(new Event('resize'));
						} catch (e) {}
					})();
				`)
			},
			bindKeyboardHeightChange() {
				if (typeof uni.onKeyboardHeightChange !== 'function' || this.keyboardHeightChangeHandler) {
					return
				}
				this.keyboardHeightChangeHandler = res => {
					this.keyboardHeight = Number(res && res.height) || 0
					if (!this.keyboardHeight) {
						this.applyWebviewKeyboardOffset()
						setTimeout(() => {
							this.refreshAppWindowHeight()
							this.scheduleAppWebviewResize(80)
						}, 120)
						return
					}
					this.applyWebviewKeyboardOffset()
					this.scheduleAppWebviewResize(80)
					this.syncFocusedInputIntoView(140)
					this.syncFocusedInputIntoView(260)
				}
				uni.onKeyboardHeightChange(this.keyboardHeightChangeHandler)
			},
			unbindKeyboardHeightChange() {
				if (typeof uni.offKeyboardHeightChange !== 'function' || !this.keyboardHeightChangeHandler) {
					return
				}
				uni.offKeyboardHeightChange(this.keyboardHeightChangeHandler)
				this.keyboardHeightChangeHandler = null
			},
			clearAppLayoutSyncTimers() {
				if (!this.appLayoutSyncTimers.length) {
					return
				}
				this.appLayoutSyncTimers.forEach(timer => clearTimeout(timer))
				this.appLayoutSyncTimers = []
			},
			queueAppWebviewLayoutSync(delays = [0]) {
				this.clearAppLayoutSyncTimers()
				delays.forEach(delay => {
					const timer = setTimeout(() => {
						this.resizeAppWebview()
						this.appLayoutSyncTimers = this.appLayoutSyncTimers.filter(item => item !== timer)
					}, delay)
					this.appLayoutSyncTimers.push(timer)
				})
			},
			scheduleAppWebviewCreate(delay = 0) {
				this.clearAppLayoutSyncTimers()
				const timer = setTimeout(() => {
					if (!this.showModal || !this.iframeUrl) {
						this.appLayoutSyncTimers = this.appLayoutSyncTimers.filter(item => item !== timer)
						return
					}
					this.createAppWebview()
					this.appLayoutSyncTimers = this.appLayoutSyncTimers.filter(item => item !== timer)
				}, delay)
				this.appLayoutSyncTimers.push(timer)
			},
			notifyAppWebviewResize() {
				if (!this.appWebview) return
				this.appWebview.evalJS(`
					(function () {
						try {
							window.dispatchEvent(new Event('resize'));
							document.dispatchEvent(new Event('resize'));
						} catch (e) {}
					})();
				`)
			},
			createAppWebview() {
				this.destroyAppWebview()

				const query = uni.createSelectorQuery().in(this)
				query.select('.app-modal-body').boundingClientRect(rect => {
					if (!rect) return

					this.appWebview = plus.webview.create(
						this.iframeUrl,
						`cs-child-webview-${Date.now()}`, {
							top: rect.top + 'px',
							left: rect.left + 'px',
							width: rect.width + 'px',
							height: rect.height + 'px',
							softinputMode: 'adjustResize',
							scrollIndicator: 'none',
							progress: {
								color: '#FFD671',
								height: '3px'
							}
						}
					)
					this.appWebview.show()
					this.applyWebviewKeyboardOffset()
					this.notifyAppWebviewResize()
					this.queueAppWebviewLayoutSync([0, 80, 180])
					this.syncFocusedInputIntoView(300)
				}).exec()
			},
			destroyAppWebview() {
				if (this.appWebview) {
					this.appWebview.close()
					this.appWebview = null
				}
			},
			resizeAppWebview() {
				if (!this.appWebview) return

				this.$nextTick(() => {
					const query = uni.createSelectorQuery().in(this)
					query.select('.app-modal-body').boundingClientRect(rect => {
						if (!rect) return
						this.appWebview.setStyle({
							top: rect.top + 'px',
							left: rect.left + 'px',
							width: rect.width + 'px',
							height: rect.height + 'px'
						})
						this.appWebview.show('none')
						this.applyWebviewKeyboardOffset()
						this.notifyAppWebviewResize()
					}).exec()
				})
			},
			// #endif
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
	.customer-btn {
		width: 50px;
		height: 50px;
		display: flex;
		align-items: center;
		justify-content: center;
		background: $color-primary;
		border: 1px solid $color-border-other;
		border-radius: 50%;
		box-sizing: border-box;
	}

	.customer-btn-icon {
		width: 20px;
		height: 20px;
		display: block;
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
		bottom: 20vh;
		right: 5vw;
		width: 90vw;
		height: 60vh;
		background-color: #ffffff;
		border-radius: 20px;
		box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
		z-index: 1000;
		overflow: hidden;
		display: flex;
		flex-direction: column;
		animation: slideUp 0.3s ease;
		transition: all 0.3s ease;
	}

	/* 全屏模式 */
	.modal-content.fullscreen {
		top: 0;
		right: 0;
		bottom: 0;
		left: 0;
		width: 100vw;
		height: 100vh;
		border-radius: 0;
		z-index: 1001;
	}

	/* 标题区域 */
	.modal-header {
		background: linear-gradient(135deg, $color-primary 0%, #3c787d 100%);
		padding: 8px 20px;
		color: #ffffff;
		display: flex;
		align-items: center;
		justify-content: space-between;
		flex-shrink: 0;
	}

	.header-left {
		flex: 1;
	}

	.modal-title {
		font-size: 14px;
		font-weight: bold;
		text-align: left;
	}

	.header-controls {
		display: flex;
		align-items: center;
		gap: 8px;
		flex-shrink: 0;
	}

	.control-btn {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 4px;
		padding: 6px 12px;
		border-radius: 8px;
		height: 28px;
		width: 36px;
		background: rgba(255, 255, 255, 0.15);
		cursor: pointer;
		transition: background 0.2s;
	}

	.control-btn:active {
		background: rgba(255, 255, 255, 0.3);
	}

	.control-icon {
		font-size: 16px;
		line-height: 1;
	}

	/* H5 全屏 SVG 图标 */
	.h5-fullscreen-icon {
		height: 16px;
		width: auto;
		display: block;
	}

	.control-text {
		font-size: 12px;
		line-height: 1;
	}

	/* iframe 容器 */
	.modal-iframe-body {
		flex: 1;
		overflow: hidden;
		position: relative;
	}

	.cs-iframe {
		width: 100%;
		height: 100%;
		border: none;
	}

	/* 动画 */
	@keyframes fadeIn {
		from {
			opacity: 0;
		}

		to {
			opacity: 1;
		}
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

	/* #ifdef APP-PLUS */
	/* App 端遮罩层 */
	.app-modal-mask {
		position: fixed;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		background-color: rgba(0, 0, 0, 0.5);
		z-index: 999;
		animation: fadeIn 0.3s ease;
	}

	/* App 端模态框（非全屏：居中带间距，类似 Web） */
	.app-modal-wrapper:not(.fullscreen) {
		position: fixed;
		top: 0;
		left: 0;
		right: 0;
		z-index: 1000;
		pointer-events: none;
		overflow: hidden;
	}

	.app-modal-wrapper:not(.fullscreen) .app-modal-container {
		width: 90vw;
		position: absolute;
		left: 5vw;
		background: #ffffff;
		border-radius: 20px;
		overflow: hidden;
		box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
		pointer-events: auto;
		display: flex;
		flex-direction: column;
	}

	.app-modal-wrapper:not(.fullscreen) .app-modal-body {
		flex: 1;
		position: relative;
	}

	/* App 端全屏模式 */
	.app-modal-wrapper.fullscreen {
		position: fixed;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		background: #ffffff;
		z-index: 1001;
		display: flex;
		flex-direction: column;
		pointer-events: none;
	}

	.app-modal-wrapper.fullscreen .app-modal-container {
		flex: 1;
		display: flex;
		flex-direction: column;
		pointer-events: auto;
	}

	.app-modal-wrapper.fullscreen .app-modal-body {
		flex: 1;
		position: relative;
	}

	.app-keyboard-spacer {
		flex-shrink: 0;
		width: 100%;
	}

	.app-modal-header {
		background: linear-gradient(135deg, #0C3569 0%, #1a4d8f 100%);
		color: #ffffff;
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 8px 20px;
		pointer-events: auto;
		flex-shrink: 0;
	}

	.app-modal-wrapper.fullscreen .app-modal-header {
		padding-top: calc(8px + constant(safe-area-inset-top));
		padding-top: calc(8px + env(safe-area-inset-top));
	}

	/* App 端 SVG 图标样式 */
	.control-icon-img {
		height: 12px;
		width: auto;
		display: block;
	}

	@keyframes slideDown {
		from {
			transform: translateY(-20px);
			opacity: 0;
		}

		to {
			transform: translateY(0);
			opacity: 1;
		}
	}

	/* #endif */
</style>