<template>
	<view class="full-page download-page">
		<zw-header @headerHeightChange="onHeaderHeightChange"></zw-header>
		<!-- header 占位元素，防止标题栏被固定 header 遮挡 -->
		<view class="header-placeholder" :style="{ height: headerHeight + 'px' }"></view>
		<scroll-view scroll-y class="app-safe-scroll">
			<view class="flex-column justify-center align-center text-center text-primary"
				style="position: fixed;top: 30vh;">
				<view class="myfont-31px text-bold" v-if="!noDownloadLink">{{$t('download_thank_you')}}</view>
				<view class="myfont-31px text-bold" v-if="!noDownloadLink">{{$t('download_subtitle')}}</view>
				<view class="myfont-16px" v-if="!noDownloadLink">
					{{'---------------------------------------------------'}}
				</view>
				<view class="mycolor-red margin-tb-lg" v-if="!noDownloadLink">
					{{$t('download_auto_hint')}}
				</view>
				<button class="bg-primary logout-btn" style="" @click="download()"
					v-if="!noDownloadLink">{{$t('Download')}}</button>
				<view class="mycolor-red margin-tb-lg myfont-16px text-bold" v-if="noDownloadLink">
					{{$t('no_download_link')}}
				</view>
				<button class="bg-primary logout-btn" @click="toHome()"
					v-if="noDownloadLink">{{$t('Back')}}</button>
			</view>
			<!-- 底部安全区域占位 -->
			<view style="height: 30px; width: 100%;"></view>
		</scroll-view>

	</view>
</template>

<script>
	import config from '../../utils/config.js'
	import language from '../../utils/language.js'
	import dateFormatUtils from "../../utils/utils.js"
	import {
		getAppInfo
	} from '../../utils/api/config.js'

	export default {
		components: {},
		name: "ucenter",
		data() {
			return {
				download_url: '',
				headerHeight: 0
			}
		},

		methods: {
			onHeaderHeightChange(height) {
				this.headerHeight = height || 0;
			},
			toHome() {
				uni.reLaunch({
					url: '/pages/ucenter/home'
				})
			},
			// 判断是否为 iOS 设备
			isIOSDevice() {
				// #ifdef H5
				const userAgent = navigator.userAgent.toLowerCase();
				return /iphone|ipad|ipod/.test(userAgent);
				// #endif

				// #ifndef H5
				// #ifdef ios / #ifdef android 小写值不是有效条件编译，App 端改为运行时判断
				return uni.getSystemInfoSync().platform === 'ios';
				// #endif
			},

			download() {
				let _this = this
				//#ifdef APP-PLUS
				plus.runtime.openURL(_this.download_url, function(err) {
					console.warn('[Download] openURL failed, fallback to location.href:', JSON.stringify(err));
					// @ts-ignore
					window.location.href = _this.download_url;
				});
				//#endif

				//#ifdef H5
				// debugger
				window.location.href = _this.download_url
				// window.open(url);
				//#endif
			},
			async loadDownloadUrl() {
				// iOS 设备使用后台 "App iOS URL"（appInfo.appIosUrl），其他设备使用 APK 链接
				// 从本地缓存读取应用信息
				const cachedAppInfo = uni.getStorageSync('appInfo');
				if (cachedAppInfo) {
					this.download_url = this.isIOSDevice() ? (cachedAppInfo.appIosUrl || '') : (cachedAppInfo.appApkUrl || '');
					console.log('[Download] Using download URL:', this.download_url);
				}

				// 如果缓存中URL为空，尝试从API重新获取最新appInfo
				if (!this.download_url) {
					console.warn('[Download] Cache URL is empty, fetching from API');
					try {
						const freshAppInfo = await getAppInfo(this.$http);
						if (freshAppInfo) {
							this.download_url = this.isIOSDevice() ? (freshAppInfo.appIosUrl || '') : (freshAppInfo.appApkUrl || '');
							console.log('[Download] API fetch URL:', this.download_url);
						}
					} catch (err) {
						console.error('[Download] Failed to fetch appInfo:', err);
					}
				}

				// 仅当有有效链接时自动下载
				if (!this.noDownloadLink) {
					this.download()
				}
			},
		},
		computed: {
			noDownloadLink() {
				return !this.download_url || !this.download_url.startsWith('http');
			}
		},
		onLoad() {
			this.loadDownloadUrl();
		},

		created() {}
	}
</script>

<style lang="scss">
	/* 无背景：透明容器让应用根节点的主题渐变透到固定 header 后面（与 ucenter/home 一致） */
	.download-page {
		display: flex;
		flex-direction: column;
		min-height: var(--app-viewport-height, 100vh);
		overflow: hidden;
	}

	.app-safe-scroll {
		flex: 1;
		height: 0;
		background: #fff;
		border-radius: 20px 20px 0 0;
		position: relative;
		z-index: 1;
	}

	.header-placeholder {
		width: 100%;
		flex-shrink: 0;
		transition: height 0.3s ease;
	}

	.text-primary {
		color: $color-primary;
	}

	.bg-primary {
		background-color: $color-primary;
	}

	.logout-btn {
		line-height: 35px;
		width: 45%;
		height: 35px;
		border-radius: 8px;
		background-color: $color-primary;
		color: #ffffff;
		box-shadow: rgba(0, 0, 0, 0.25) 0px 2px 2px 0px;
	}
</style>
