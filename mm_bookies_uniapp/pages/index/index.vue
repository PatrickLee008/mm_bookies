<template>
	<view class="mybg-grey full-page"
		style="background-image: url(../../static/image/index_bg.jpg);background-repeat: no-repeat;background-size: 100% 100%;">
		<cu-custom>
			<block slot="content">INNWA BET</block>
		</cu-custom>
		<view>
			<swiper class="box-shadow myrect screen-swiper" :class="dotStyle?'square-dot':'round-dot'"
				:indicator-dots="false" :circular="true" :autoplay="true" interval="3000" duration="500"
				style="border-radius: 13px;">
				<swiper-item v-for="(item,index) in swiperList" :key="index">
					<image style="border-radius: 13px;" :src="item.url" mode="scaleToFill" v-if="item.type=='image'">
					</image>
					<video :src="item.url" autoplay loop muted :show-play-btn="false" :controls="false"
						objectFit="cover" v-if="item.type=='video'"></video>
				</swiper-item>
			</swiper>
		</view>

		<view class="myrect box-shadow flex-row bg-white padmar" style="width: 90vw;">
			<!-- <image class="icon" src="../../static/image/notice.png"></image> -->
			<uni-notice-bar backgroundColor="white" color="black" :speed="speed" scrollable="true" :text="notice"
				style="margin-bottom: 0;font-weight: bold;"></uni-notice-bar>
		</view>
		<scroll-view>
			<view class="myrect box-shadow bg-white padmar">
				<view class="flex-row" style="justify-content: space-between;">
					<view class="flex-row">
						<!-- <image class="my-icon-plus" src="../../static/image/tocenter.png"></image> -->
						<text class="myfont-bold" style="line-height: 40px;">{{userInfo.nick_name}}</text>
					</view>
					<!-- <image style="width: 14px;height: 10px;float: right;margin: 13px 10px;" src="../../static/image/fanhui(5).png"></image> -->
				</view>
				<view class="mybg-red flex-row"
					style="padding: 5vw 2vw 5vw 2vw;border-radius: 5px;align-items: center;width: 96%;margin-left: 2%;">
					<view class="flex-column">
						<view class="myfont-bold padding-col" style="font-size: 18px;">{{userInfo.total_withdraw}}</view>
						<view class="myfont padding-col">{{language.totalCashOut}}</view>
					</view>
					<view style="height: 5vh;width: 1px;background-color: rgb(190,150,150);"></view>
					<view class="flex-column">
						<view class="myfont-bold padding-col" style="font-size: 18px;">{{userInfo.money}}</view>
						<view class="myfont padding-col">{{language.balance}}</view>
					</view>
				</view>
			</view>
			<view class="myrect flex-row"
				style="line-height: 20px;width: 90vw;margin: 3vw 5vw;justify-content: space-between;">
				<view class="flex-column bg-white myrect2 box-shadow padding-ud20px" style="width: 32%;"
					@click="goto('match/mixed')">
					<!-- <image class="pic" src="../../static/image/mixbet.png"></image> -->
					<text class="myfont-bold mycolor-red">{{language.mixed}}</text>
				</view>
				<view class="flex-column bg-white myrect2 box-shadow padding-ud20px" style="width: 32%;"
					@click="goto('match/home')">
					<!-- <image class="pic" src="../../static/image/zuqiu.png"></image> -->
					<text class="text-bold text-yellow">{{language.single}}</text>
				</view>
				<!-- <view class="flex-column bg-white myrect2 box-shadow padding-ud20px" style="width: 32%;"
					@click="goto(navi2D3D=='3D'? 'number/3d-number-bet' : 'number/number-bet')"> -->
				<view class="flex-column bg-white myrect2 box-shadow padding-ud20px" style="width: 32%;"
					@click="goto('number/3d-number-bet')">
					<!-- <image class="pic" src="../../static/image/2D3D.png"></image> -->
					<text class="text-purple text-bold">2D/3D</text>
				</view>
			</view>
			<view class="myrect flex-row"
				style="width: 90vw;margin: 3vw 5vw;justify-content: space-between;align-items: flex-start;">


				<view class="flex-column bg-white myrect2 box-shadow padding-ud20px" style="width: 32%;"
					@click="to_score_link" :style="{'min-height':dyHeight()}">
					<!-- <image class="pic" src="../../static/image/score.png"></image> -->
					<text class="text-blue text-bold">{{language.score}}</text>
				</view>

				<view class="flex-column bg-white myrect2 box-shadow padding-ud20px " style="width: 32%;"
					@click="goto('orders/home')" :style="{'min-height':dyHeight()}">
					<!-- <image class="pic" src="../../static/image/zhangdan_.png"></image> -->
					<text class="text-green text-bold" style="padding: 0 8px 0 8px;">{{language.myBet}}</text>
				</view>
				<!-- <view class="flex-column bg-white myrect2 box-shadow padding-ud20px" style="width: 32%;" @click="goto('match/score')" :style="{'min-height':dyHeight()}"> -->


				<view class="flex-column bg-white myrect2 box-shadow padding-ud20px " style="width: 32%;"
					@click="goto('ucenter/home')" :style="{'min-height':dyHeight()}">
					<!-- <image class="pic" src="../../static/image/jingjiren_icon.png"></image> -->
					<text class="text-orange text-bold" style="padding: 0 8px 0 8px;">{{language.ucenter}}</text>
				</view>
			</view>
		</scroll-view>

		<uni-popup ref="popup" type="center">
			<view class="bg-white text-bold text-center dialogsTitle">{{temp.title}}</view>
			<scroll-view scroll-y class="bg-white">
				<view class="bg-white dialogs text-center span_box">
					<view class="words_span">{{temp.content}}</view>
				</view>
			</scroll-view>
		</uni-popup>

	</view>
</template>

<script>
	import match from '../match/home.vue'
	import orders from '../orders/home.vue'
	import ucenter from '../ucenter/home.vue'
	import config from '../../utils/config.js'
	import dateFormatUtils from "../../utils/utils.js"
	import uniPopup from "@/components/uni-popup/uni-popup.vue";


	export default {
		components: {
			match,
			orders,
			ucenter
		},
		data() {
			return {
				cardCur: 0,
				// swiperList:[],
				swiperList: [],
				dotStyle: false,
				towerStart: 0,
				direction: '',
				temp: {},
				userInfo: {},
				language: config.language,
				speed: 8,
				contact: '',
				about: '',
				notice: '',
				navi2D3D: null,
				loading: false,
			}
		},
		methods: {
			developingTips() {
				uni.showModal({
					title: 'Tips',
					content: 'Coming Soon',
					confirmText: 'OK',
					cancelText: 'Cancel',
				})
			},
			numberFormat(num) {
				return dateFormatUtils.numFormat(num)
			},
			dyHeight() {
				return this.language.lang == 'mm' ? '160px' : ''
			},
			goto(name) {
				// this.music.play_dede()
				uni.navigateTo({
					url: '/pages/' + name,
					animationType: 'slide-in-right',
					animationDuration: 100
				})
			},
			getUserInfo() {
				var _this = this;
				_this.loading = true;
				if (uni.getStorageSync("Authorization")) {
					_this.$http.get('/app_user/user_info', {}, (res) => {
						_this.loading = false;
						if (res.statusCode == 200) {
							_this.$store.dispatch('saveUserInfo', res.data.data);
							_this.userInfo = res.data.data
						}
					})
				}
			},
			to_score_link() {
				const url = "https://innwasport.com";
				// 在 App 端调用原生浏览器
				// #ifdef APP-PLUS
				plus.runtime.openURL(url);
				// #endif

				// 在 H5 端用新标签页打开
				// #ifdef H5
				window.open(url, "_blank");
				// #endif
			},
			getNotice() {
				var _this = this;
				_this.$http.get('/notice/get', {}, (res) => {
					if (res.statusCode == 200) {
						_this.notice = '';
						res.data.items.forEach(element => {
							_this.notice += '[' + element.TITLE + ']' + element.CONTENT + '           ';
						})
					}
				})
			},
			getImage() {
				var _this = this;
				_this.$http.get('/up_image/get', {}, (res) => {
					if (res.statusCode == 200) {
						_this.swiperList = []
						res.data.items.forEach(element => {
							_this.swiperList.push({
								id: element.ID,
								type: 'image',
								url: 'http://img.innwabet.net/' + element.ADDRESS
							})
						})
					}
				})
			},
			showDialogs(title) {
				// this.music.play_dede()
				this.temp = {
					title: this.language[title],
					content: this.$data[title]
				}
				this.$refs.popup.open()
			},
			showContactDialogs() {
				// this.music.play_dede()
				this.$refs.contactDialogs.open()
			},
			logout() {
				// this.music.play_dede();
				uni.removeStorageSync('Authorization');
				uni.redirectTo({
					url: '../login/login'
				})
			},
		},
		mounted() {
			if (!uni.getStorageSync("Authorization")) {
				uni.redirectTo({
					url: '../login/login'
				})
				return;
			}
			// this.getConfigs();

			this.contact = this.$store.state.configs.contact_us;
			this.about = this.$store.state.configs.help_content;
			this.getNotice();
			this.getImage();
			this.language = config.language;
			console.log(this.language.lang)
		},
		onShow() {
			this.getUserInfo();
			this.navi2D3D = uni.getStorageSync('navi2D3D')
		}
	}
</script>
<style lang="scss">
	.pic {
		width: 45px;
		height: 45px;
		margin-bottom: 15px;
	}

	.padmar {
		padding: 8px 4px 10px 4px;
		margin-top: 3vw;
	}

	.text-purple {
		color: #6030d1;
	}

	.text-yellow {
		color: #ea9d31;
	}

	.text-green {
		color: #44bc6f;
	}

	.text-blue {
		color: #52adff;
	}

	.text-orange {
		color: #ffa56c;
	}

	.padding-col {
		padding: 2vw;
		color: white;
		font-weight: 600;
	}

	.dialogs {
		width: 90vw;
		height: 50vh;
	}

	.icon {
		height: 35px;
		width: 43px;
	}

	.logout {
		position: fixed;
		bottom: 8px;
		right: 8px;
		background-color: white;
		border-radius: 3px;
		display: table;
		height: 42px;
		width: 70px
	}

	.dialogsTitle {
		height: 5vh;
		line-height: 5vh;
		border-bottom: 1px solid lightgrey;
		font-size: 16px;
	}

	.logout-image {
		display: table-cell;
		vertical-align: middle;
		text-align: center;
		padding: 5px 0 0 5px;
	}

	.logout-image image {
		height: 15px;
		width: 15px;
	}

	.logout-label {
		display: table-cell;
		vertical-align: middle;
		text-align: center;
	}

	.background {
		// background: url(../../static/image/index.png) no-repeat center center;
		background-size: cover;
		position: fixed;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
	}

	.user-row {
		width: 100%;
		padding: 0 9px;
		margin-bottom: 5px;
	}

	.user-bar {
		display: table;
		background-color: rgba(255, 255, 255, 0.9);
		padding: 3px 0;
		width: 100%;
		border-radius: 8px;
	}

	.user-bar-cell {
		display: table-cell;
		text-align: left;
		vertical-align: middle;
		height: 100px;
	}

	.user-info-loading {
		height: 15px;
		width: 15px;
		position: absolute;
		right: 5px
	}

	.menu-row {
		width: 100%;
		display: flex;
		flex-direction: row;
		justify-content: space-around;
		align-items: center;
		border-bottom: 1px solid lightgrey;
	}

	.menu-row .menu-cell:first-child {
		border-right: 1px solid lightgrey;
	}

	.menu-cell {
		width: 50%;
		display: flex;
		flex-direction: row;
		align-items: center;
		padding-left: 15px;
		height: 120px;
	}

	.menu-cell view {
		width: 80px;
	}

	.menu-cell image {
		width: 80px;
		height: 80px;
		margin-right: 10px;
	}
</style>