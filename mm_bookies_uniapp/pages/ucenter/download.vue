<template>
	<view class="full-page dark-teal-bg">
		<zw-header></zw-header>
		<scroll-view scroll-y :style="{ height: isLogin ? 'calc(100vh - 110px)' : 'calc(100vh - 170px)', background: '#fff' }">

			<view class="flex-column justify-center align-center text-center text-black"
				style="position: fixed;top: 30vh;">
				<view class="myfont-31px text-bold">{{'Thank you'}}</view>
				<view class="myfont-31px text-bold">{{'for download our app !'}}</view>
				<view class="myfont-16px">{{'---------------------------------------------------'}}
				</view>
				<view class="mycolor-red margin-tb-lg">
					{{"Click 'Download' below if the download does not start automatically."}}
				</view>
				<button class="bg-black logout-btn" style="" @click="download(download_url)"
					v-if="isLogin">{{'Download'}}</button>
			</view>
		</scroll-view>

	</view>
</template>

<script>
	import config from '../../utils/config.js'
	import language from '../../utils/language.js'
	import dateFormatUtils from "../../utils/utils.js"

	export default {
		components: {},
		name: "ucenter",
		data() {
			return {
				isLogin: uni.getStorageSync('Authorization') || false,
				download_url: 'http://m.1x2mmm.net/api/static/download/1x2mm-v1.0.1.apk'
			}
		},

		methods: {
			download() {
				let _this = this
				//#ifdef APP-PLUS
				plus.runtime.openURL(_this.download_url)
				//#endif

				//#ifdef H5
				// debugger
				window.location.href = _this.download_url
				// window.open(url);
				//#endif
				setTimeout(() => {
					_this.to_page('./home')
				}, 2000)
			},
			to_page(path) {
				uni.navigateTo({
					url: path,
					// url: '/pages/ucenter/' + path,
					animationType: 'slide-in-right',
					animationDuration: 100
				})

			},
		},
		onLoad() {
			this.download()
		},
		created() {
			this.download()
		}
	}
</script>

<style lang="scss">
	.dark-teal-bg {
		background-color: var(--theme-page-background-color, #{$theme-header-start});
		background-image: var(--theme-page-background-image, #{$theme-page-background});
		background-position: var(--theme-page-background-position, center);
		background-size: var(--theme-page-background-size, cover);
		background-repeat: var(--theme-page-background-repeat, no-repeat);
		min-height: 100vh;
	}

	.logout-btn {
		line-height: 35px;
		// font-weight: bold;
		width: 45%;
		height: 35px;
		border-radius: 8px;
		// position: absolute;
		// left: 27.5%;
		box-shadow: rgba(0, 0, 0, 0.25) 0px 2px 2px 0px;
	}
</style>