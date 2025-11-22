<template name="ucenter">
	<view class="bg-white full-page">
		<zw-header></zw-header>

		<view class="title-bar">
			<view class="flex-row justify-between" style="">
				<view class="flex-row align-center" style="">
					<image class="yellow2dblue" style="height: 25px;" mode="heightFix" src="/static/icon/contact.png">
					</image>
					<text class="title-text" style="">{{language.contact}}</text>
				</view>
			</view>
		</view>
		<view class="flex-column justify-center align-center width-100 padding">
			<view class="flex-row justify-center align-center height-56px">
				<text class="margin-top-sm margin-bottom-lg text-black"
					style="font-weight: 600;">{{language.customer_support}}
				</text>
			</view>
			<view class="flex-row align-center padding-bottom-sm padding-top-xs" style="border-top: solid #EDEDED 1px;"
				@click="toURL('https://t.me/onextwosport')">
				<image src="/static/image/contact/telegram.png" style="height: 22px;width: 22px;;margin: 0 16px;"
					mode="aspectFit"></image>
				<view class="flex-column justify-between" style="height: 42px;justify-content: space-between;">
					<view class="flex-row">
						<text class="height-22px">Telegram</text>
					</view>
					<view class="flex-row myfont-12px ">
						<text class="" style="">Telegram သို့ဆက ်သွယ်ရန်</text>
					</view>
				</view>
			</view>
			<view class="flex-row align-center padding-bottom-sm padding-top-xs" style="border-top: solid #EDEDED 1px;"
				@click="toURL('https://connect.viber.com/en/business/747e966c-dd95-11ef-8de5-ce9e812ba80c?utm_source=manage&utm_medium=copy_link')">
				<image src="/static/image/contact/viber.png" style="height: 22px;width: 22px;;margin: 0 16px;"
					mode="aspectFit"></image>
				<view class="flex-column justify-between" style="height: 42px;justify-content: space-between;">
					<view class="flex-row">
						<text class="height-22px">Viber</text>
					</view>
					<view class="flex-row myfont-12px">
						<text>Viber သို့ဆက်သွယ်ရန််</text>
					</view>
				</view>
			</view>

			<view class="flex-row align-center padding-bottom-sm padding-top-xs" style="border-top: solid #EDEDED 1px;"
				@click="handlePhoneTap()">
				<image src="/static/image/contact/telephone-call.png" style="height: 22px;width: 22px;;margin: 0 16px;"
					mode="aspectFit"></image>
				<view class="flex-column justify-between" style="height: 42px;justify-content: space-around;">
					<view class="flex-row">
						<text class="height-22px">Phone</text>
					</view>
					<view class="flex-row myfont-12px">
						<text>Hotline Phone</text>
					</view>
				</view>
			</view>
		</view>
		<!-- <view class="flex-column justify-center" style="position: fixed;top: 45vh;">
			<view class="flex-column align-center justify-center" style="">
				<view class="myfont-20px mycolor-primary">{{language.is_coming_soon}}</view>
			</view>
		</view> -->



	</view>
</template>

<script>
	import config from '../../utils/config.js'
	import language from '../../utils/language.js'

	export default {
		components: {},
		name: "ucenter",
		data() {
			return {
				isLogin: uni.getStorageSync('Authorization') || false,
				language: config.language,
			}
		},

		methods: {
			handlePhoneTap() {
				const phoneNumber = '959944182182'
				wx.makePhoneCall({
					phoneNumber,
					success() {
						console.log('拨打电话成功');
					},
					fail(err) {
						console.error('拨打电话失败', err);
					},
				});
			},
			toURL(url) {
				console.log(url)
				//#ifdef APP-PLUS
				plus.runtime.openURL(url)
				//#endif


				//#ifdef H5
				// debugger
				window.location.href = url;
				//#endif
			},
		},
		created() {}
	}
</script>

<style lang="scss">
</style>