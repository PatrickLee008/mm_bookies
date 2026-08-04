<template>
	<view class="full-page">
		<zw-header></zw-header>

		<view class="title-bar" style="height: auto;">
			<view class="flex-row justify-between" style="">
				<view class="flex-row align-center" style="">
					<image src="/static/icon/ucenter/bonus.png" class="lblue2blue" style="height: 28px;"
						mode="heightFix"></image>
					<text class="title-text" style="">{{language.bonus}}</text>
				</view>
			</view>
		</view>
		<view class="flex-column justify-center" style="position: fixed;top: 45vh;">
			<view class="flex-column align-center justify-center" style="">
				<view class="myfont-20px" style="color: #FFFFFF;">{{language.is_coming_soon}}</view>
			</view>
		</view>

	</view>
</template>

<script>
	import language from '../../utils/language.js'
	import config from '../../utils/config.js'
	export default {
		data() {
			return {
				language: config.language,
				userInfo: null,
			}
		},
		onLoad() {
			this.userInfo = Object.assign({}, this.$store.state.userInfo)
		},
		methods: {}
	}
</script>

<style lang="scss">
	.full-page {
		background: linear-gradient(to right, #02455F 0%, #02455F 56%, #1F879B 100%);
	}
</style>