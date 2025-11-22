<template>
	<view class="full-page cu-list menu languageDialogs mybg-grey">
		<zw-header @doSomething=""></zw-header>
		<view class="mybg-grey flex-row margin-top-lg">
			<!-- <view class="content">
				<text class="text-grey">English</text>
			</view> -->
			<button style="border-radius: 10px;width: 90%;margin: 5% 5% 0 5%;"
				:class="picker=='en'? 'mybg-primary':'bg-white'" @click="pickerChange('en')">English</button>
		</view>
		<view class="mybg-grey flex-row">
			<button style="border-radius: 10px;width: 90%;margin: 4% 5% 0 5%;"
				:class="picker=='mm'? 'mybg-primary':'bg-white'" @click="pickerChange('mm')">မြန်မာ</button>
		</view>
		<view class="mybg-grey flex-row">
			<button style="border-radius: 10px;width: 90%;margin: 4% 5% 0 5%;"
				:class="picker=='th'? 'mybg-primary':'bg-white'" @click="pickerChange('th')">ภาษาไทย</button>
		</view>
		<view class="mybg-grey flex-row">
			<button style="border-radius: 10px;width: 90%;margin: 4% 5% 0 5%;"
				:class="picker=='cn'? 'mybg-primary':'bg-white'" @click="pickerChange('cn')">中文</button>
		</view>
		<!-- <view class="myrect cu-item flex-row" :class="{'bg-gradual-purple':picker=='mm'}" @click="pickerChange('mm')">
			<view class="content">
				<text class="text-grey">မြန်မာ</text>
			</view>
		</view> -->
		<!--
		<view class="cu-item" :class="{'bg-gradual-pink':picker=='cn'}" @click="pickerChange('cn')">
			<view class="content">
				<text class="text-grey">中文</text>
			</view>
		</view>
		-->
		<button class="register-btn mybg-active" style="width: 70%;margin: 30px 15% 10px 15%;" @click="submit()">
			{{language.confirm}}</button>
	</view>
</template>

<script>
	import language from '../../utils/language.js'
	import config from '../../utils/config.js'
	export default {
		data() {
			return {
				picker: uni.getStorageSync('UNI_LOCALE') || 'mm',
				language: config.language
			}
		},
		methods: {
			toHome() {
				uni.reLaunch({
					url: '/pages/ucenter/home'
				})
			},
			pickerChange(value) {
				// this.music.play_dede() ;
				this.picker = value;
			},
			submit() {
				// this.music.play_dede() ;
				if (!this.picker) this.picker = 'mm';
				config.language = language[this.picker];
				uni.setStorageSync('language', this.picker);
				
				uni.setLocale(this.picker)
				this.$i18n.locale = this.picker;
				
				this.toHome()
			}
		},
		onLoad() {},
	}
</script>

<style>
	.submit {
		width: 100vw;
	}

	.bg-green {
		background-color: rgb(41, 150, 56)
	}
</style>