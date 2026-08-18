<template>
	<view class="webview-container">
		<!-- 自定义导航栏 -->
		<view class="custom-nav" :style="{ paddingTop: statusBarHeight + 'px' }">
			<view class="nav-content">
				<view class="nav-left" @click="goBack">
					<text class="cuIcon-back text-white"></text>
				</view>
				<view class="nav-title text-white">{{ pageTitle }}</view>
				<view class="nav-right">
					<text class="cuIcon-refresh text-white" @click="refreshWebview"></text>
				</view>
			</view>
		</view>

		<!-- WebView -->
		<web-view
			:src="gameUrl"
			@message="handleMessage"
			@error="handleError"
			@load="handleLoad"
		></web-view>

		<!-- 加载提示 -->
		<view v-if="loading" class="loading-mask">
			<view class="loading-content">
				<view class="cu-load loading"></view>
				<text class="text-white margin-top-sm">Loading game...</text>
			</view>
		</view>
	</view>
</template>

<script>
export default {
	data() {
		return {
			gameUrl: '',
			pageTitle: 'Game',
			loading: true,
			statusBarHeight: 0
		}
	},
	onLoad(options) {
		// 获取状态栏高度
		const systemInfo = uni.getSystemInfoSync()
		this.statusBarHeight = systemInfo.statusBarHeight || 0

		// 获取URL参数
		if (options.url) {
			this.gameUrl = decodeURIComponent(options.url)
		}

		if (options.title) {
			this.pageTitle = decodeURIComponent(options.title)
		}

		// 如果没有URL，返回上一页
		if (!this.gameUrl) {
			uni.showToast({
				title: 'Invalid game URL',
				icon: 'none'
			})
			setTimeout(() => {
				uni.navigateBack()
			}, 1500)
		}
	},
	methods: {
		// 返回上一页
		goBack() {
			uni.navigateBack({
				delta: 1
			})
		},

		// 刷新webview
		refreshWebview() {
			this.loading = true
			// 重新加载当前URL
			const currentUrl = this.gameUrl
			this.gameUrl = ''
			this.$nextTick(() => {
				this.gameUrl = currentUrl
			})
		},

		// webview加载完成
		handleLoad(e) {
			console.log('webview loaded:', e)
			this.loading = false
		},

		// webview加载错误
		handleError(e) {
			console.error('webview error:', e)
			this.loading = false
			uni.showToast({
				title: 'Failed to load game',
				icon: 'none'
			})
		},

		// 接收webview消息
		handleMessage(e) {
			console.log('webview message:', e)
			// 处理来自webview的消息
			const data = e.detail.data
			if (data && data.length > 0) {
				const message = data[0]
				// 根据消息类型处理
				if (message.type === 'close') {
					this.goBack()
				}
			}
		}
	}
}
</script>

<style scoped>
.webview-container {
	width: 100%;
	height: var(--app-viewport-height, 100vh);
	background-color: #000;
}

.custom-nav {
	position: fixed;
	top: 0;
	left: 0;
	right: 0;
	z-index: 999;
	background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
	box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.nav-content {
	display: flex;
	align-items: center;
	justify-content: space-between;
	height: 44px;
	padding: 0 15px;
}

.nav-left,
.nav-right {
	width: 40px;
	display: flex;
	align-items: center;
	justify-content: center;
	font-size: 20px;
}

.nav-title {
	flex: 1;
	text-align: center;
	font-size: 16px;
	font-weight: bold;
	overflow: hidden;
	text-overflow: ellipsis;
	white-space: nowrap;
	padding: 0 10px;
}

.loading-mask {
	position: fixed;
	top: 0;
	left: 0;
	right: 0;
	bottom: 0;
	background: rgba(0, 0, 0, 0.8);
	display: flex;
	align-items: center;
	justify-content: center;
	z-index: 9999;
}

.loading-content {
	display: flex;
	flex-direction: column;
	align-items: center;
	justify-content: center;
}

.cu-load {
	width: 40px;
	height: 40px;
}
</style>
