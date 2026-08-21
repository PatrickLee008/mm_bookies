<template>
	<view class="customer-service-page" :style="pageStyle">
		<web-view
			v-if="pageUrl"
			:src="pageUrl"
			@load="handleLoad"
			@error="handleError"
		></web-view>

		<view v-if="loading" class="loading-mask">
			<view class="loading-content">
				<view class="cu-load loading"></view>
				<text class="text-white margin-top-sm">Loading...</text>
			</view>
		</view>
	</view>
</template>

<script>
export default {
	data() {
		return {
			pageUrl: '',
			pageTitle: 'Customer Service',
			loading: true,
			nativeCloseButton: null,
			isIOS: false,
			keyboardHeight: 0
		}
	},
	computed: {
		pageStyle() {
			if (this.isIOS) {
				const offset = 85 + this.keyboardHeight
				return { height: `calc(100vh - ${offset}px)` }
			}
			return {}
		}
	},
	onLoad(options) {
		const systemInfo = uni.getSystemInfoSync()
		this.isIOS = systemInfo.platform === 'ios'

		if (options.title) {
			this.pageTitle = decodeURIComponent(options.title)
			uni.setNavigationBarTitle({
				title: this.pageTitle
			})
		}

		if (!options.url) {
			uni.showToast({
				title: 'Missing URL',
				icon: 'none'
			})
			setTimeout(() => {
				uni.navigateBack()
			}, 1200)
			return
		}

		this.pageUrl = decodeURIComponent(options.url)
	},
	onReady() {
		// #ifdef APP-PLUS
		// 监听键盘事件（iOS web-view内输入时键盘遮挡问题）
		if (this.isIOS) {
			try {
				const currentWebview = this.$scope.$getAppWebview()
				currentWebview.addEventListener('resize', (e) => {
					if (e && e.keyboardHeight !== undefined) {
						this.keyboardHeight = e.keyboardHeight || 0
					}
				})
			} catch (e) {
				console.warn('keyboard listener failed:', e)
			}
		}
		// #endif
	},
	onShow() {
		// #ifdef APP-PLUS
		this.showNativeActionButtons()
		// #endif
	},
	onHide() {
		// #ifdef APP-PLUS
		this.hideNativeActionButtons()
		// #endif
	},
	onUnload() {
		// #ifdef APP-PLUS
		this.destroyNativeActionButtons()
		// #endif
	},
	onNavigationBarButtonTap(event) {
		if (event.index === 0) {
			this.closePage()
			return
		}
		if (event.index === 1) {
			this.refreshPage()
		}
	},
	methods: {
		// #ifdef APP-PLUS
		// createNativeActionButtons() {
		// 	if (typeof plus === 'undefined' || !plus.nativeObj || !plus.nativeObj.View) {
		// 		return
		// 	}
		// 	this.destroyNativeActionButtons()
		// 	const systemInfo = uni.getSystemInfoSync()
		// 	const top = (Number(systemInfo.statusBarHeight) || 0) + 12
		// 	const buttonSize = 42
		// 	const horizontalMargin = 12
		// 	const windowWidth = Number(systemInfo.windowWidth) || 0
		// 	const closeLeft = Math.max(windowWidth - buttonSize - horizontalMargin, horizontalMargin)
		// 	this.nativeCloseButton = this.createNativeButton('cs-native-close-btn', {
		// 		top: `${top}px`,
		// 		left: `${closeLeft}px`
		// 	}, 'X', () => {
		// 		this.closePage()
		// 	})
		// 	this.showNativeActionButtons()
		// },
		createNativeButton(id, position, text, onClick) {
			const button = new plus.nativeObj.View(id, {
				top: position.top,
				left: position.left,
				right: position.right,
				width: '42px',
				height: '42px'
			})
			button.drawRect({
				color: 'rgba(12, 53, 105, 0.82)',
				radius: '21px',
				borderWidth: '0px'
			}, {
				top: '0px',
				left: '0px',
				width: '42px',
				height: '42px'
			})
			button.drawText(text, {
				top: '0px',
				left: '0px',
				width: '42px',
				height: '42px'
			}, {
				size: '20px',
				color: '#ffffff',
				align: 'center',
				verticalAlign: 'middle',
				weight: 'bold'
			})
			button.addEventListener('click', onClick)
			return button
		},
		showNativeActionButtons() {
			if (this.nativeCloseButton) {
				this.nativeCloseButton.show()
			}
		},
		hideNativeActionButtons() {
			if (this.nativeCloseButton) {
				this.nativeCloseButton.hide()
			}
		},
		destroyNativeActionButtons() {
			if (this.nativeCloseButton) {
				this.nativeCloseButton.close()
				this.nativeCloseButton = null
			}
		},
		// #endif
		closePage() {
			uni.navigateBack({
				delta: 1
			})
		},
		refreshPage() {
			if (!this.pageUrl) {
				return
			}
			const currentUrl = this.pageUrl
			this.loading = true
			this.pageUrl = ''
			this.$nextTick(() => {
				this.pageUrl = currentUrl
			})
		},
		handleLoad() {
			this.loading = false
		},
		handleError() {
			this.loading = false
			uni.showToast({
				title: 'Load failed',
				icon: 'none'
			})
		}
	}
}
</script>

<style scoped>
.customer-service-page {
	width: 100%;
	height: 100vh;
	background-color: #ffffff;
	overflow: auto;
	-webkit-overflow-scrolling: touch;
}

.loading-mask {
	position: fixed;
	top: 0;
	left: 0;
	right: 0;
	bottom: 0;
	z-index: 1999;
	background: rgba(0, 0, 0, 0.35);
	display: flex;
	align-items: center;
	justify-content: center;
}

.loading-content {
	display: flex;
	flex-direction: column;
	align-items: center;
	justify-content: center;
	padding: 24px 28px;
	border-radius: 12px;
	background: rgba(0, 0, 0, 0.6);
}

.cu-load {
	width: 40px;
	height: 40px;
}
</style>
