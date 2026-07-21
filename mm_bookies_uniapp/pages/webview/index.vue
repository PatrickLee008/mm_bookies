<template>
	<view class="webview-container">
		<global-notice ref="globalNotice"></global-notice>
		<!-- #ifdef APP-PLUS -->
		<web-view :src="gameUrl" @message="handleMessage" @error="handleError"></web-view>
		<!-- #endif -->

		<!-- #ifdef H5 -->
		<view v-if="showIframe">
			<iframe :src="gameUrl" frameborder="0" class="h5-iframe" @load="handleIframeLoad" @error="handleIframeError"></iframe>
			<!-- 如果iframe加载失败，显示直接跳转按钮 -->
			<view v-if="iframeLoadFailed" class="error-container">
				<view class="error-message">Unable to load game in current page</view>
				<button class="open-btn" @click="openInNewWindow">Open Game in New Window</button>
			</view>
		</view>
		<!-- #endif -->

		<!-- #ifdef MP-WEIXIN || MP-ALIPAY || MP-BAIDU || MP-TOUTIAO || MP-QQ -->
		<web-view :src="gameUrl"></web-view>
		<!-- #endif -->
	</view>
</template>

<script>
export default {
	data() {
		return {
			gameUrl: '',
			showIframe: true,
			iframeLoadFailed: false
		}
	},
	onLoad(options) {
		// 获取传入的URL参数
		if (options.url) {
			this.gameUrl = decodeURIComponent(options.url)
			console.log('Loading game URL:', this.gameUrl)

			// #ifdef H5
			// H5环境下使用iframe加载
			// 注意：iOS Safari通常不会进入此页面，因为会在home.vue中直接跳转
			this.checkIframeLoadTimeout()
			// #endif
		} else {
			this.$notice.show({
				title: 'Error',
				content: 'Missing game URL',
				showCancel: false,
				success: () => {
					uni.navigateBack()
				}
			})
		}
	},
	methods: {
		handleMessage(event) {
			console.log('Received webview message:', event)
		},
		handleError(event) {
			console.error('Webview loading error:', event)
			this.$notice.show({
				title: 'Loading Failed',
				content: 'Failed to load game, please try again later',
				showCancel: false,
				confirmText: 'Back',
				success: () => {
					uni.navigateBack()
				}
			})
		},
		handleIframeLoad() {
			console.log('Iframe loaded successfully')
			this.iframeLoadFailed = false
		},
		handleIframeError() {
			console.error('Iframe load failed')
			this.iframeLoadFailed = true
		},
		checkIframeLoadTimeout() {
			// 10秒后检查iframe是否加载成功，如果没有则显示备用方案
			setTimeout(() => {
				// 这里可以添加更复杂的检测逻辑
				console.log('Iframe load timeout check')
			}, 10000)
		},
		openInNewWindow() {
			// 在新窗口打开游戏
			// #ifdef H5
			const newWindow = window.open(this.gameUrl, '_blank')
			if (!newWindow) {
				this.$notice.show({
					title: 'Tips',
					content: 'Please allow pop-ups for this site, then try again',
					showCancel: false
				})
			} else {
				// 打开成功，可以选择返回
				setTimeout(() => {
					uni.navigateBack()
				}, 1000)
			}
			// #endif
		}
	}
}
</script>

<style scoped>
/* 确保页面全屏，覆盖状态栏 */
page {
	width: 100%;
	height: 100%;
	overflow: hidden;
}

.webview-container {
	width: 100%;
	height: 100%;
}

/* #ifdef APP-PLUS || MP-WEIXIN || MP-ALIPAY || MP-BAIDU || MP-TOUTIAO || MP-QQ */
web-view {
	width: 100%;
	height: 100%;
}
/* #endif */

/* #ifdef H5 */
.h5-iframe {
	width: 100%;
	height: 100%;
	border: none;
	position: fixed;
	top: 0;
	left: 0;
	right: 0;
	bottom: 0;
}

.error-container {
	position: fixed;
	top: 50%;
	left: 50%;
	transform: translate(-50%, -50%);
	text-align: center;
	z-index: 9999;
	background: white;
	padding: 30px;
	border-radius: 10px;
	box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.error-message {
	font-size: 16px;
	color: #333;
	margin-bottom: 20px;
}

.open-btn {
	background-color: #007aff;
	color: white;
	border: none;
	padding: 10px 30px;
	border-radius: 5px;
	font-size: 16px;
	cursor: pointer;
}

.open-btn:active {
	background-color: #0062cc;
}
/* #endif */
</style>
