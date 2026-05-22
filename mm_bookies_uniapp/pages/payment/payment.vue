<template>
	<view class="bg-white full-page">
		<zw-header></zw-header>
		<view class="header-placeholder"></view>
		<!-- 滚动内容区域 -->
		<scroll-view scroll-y class="payment-content">
			<block>
				<!-- <block v-if="isload && payInfo"> -->
				<view class=""
					style="width: calc(100vw - 36px);margin: 10px 18px 0;border: 1px solid #D9D9D9;border-radius: 10px;">
					<view class="top-image">
						<image src="/static/icon/register/KBZ Pay.png" mode="aspectFit" class="logo"
							style="width: 45px;" v-if="payInfo.paymentType=='KBZ'" />
						<text v-if="payInfo.paymentType=='KBZ'" class="margin-left-sm">{{'KBZPay'}}</text>
						<image src="/static/image/pay/wave-logo.svg" mode="aspectFit" class="logo"
							v-if="payInfo.paymentType=='WaveMoney'" />
					</view>
					<!-- <view class="qrcode">
						<view class="timeout">
							<block v-if="payInfo.orderStatus==1">
								<view v-if="!istimeout">
									<view>{{$t('payment.timoutTip')}}</view>
									<view class="time">
										{{countdownDisplay}}
									</view>
								</view>
								<text class="margin-top text-red" v-else>{{$t('payment.orderTimeoutTip')}}</text>
							</block>
							<block v-else-if="payInfo.orderStatus==2">
								<view class="text-green text-bold">Pay Completed</view>
							</block>
						</view>
					</view> -->
					<view class="qrcode">
						<view class="image">
							<tki-qrcode style="margin: 0 auto;" cid="qrcode2" ref="qrcode" :val="payInfo.qrcode"
								loadingText="loading" v-if="!istimeout && payInfo.orderStatus==1" :size="250"
								:onval="false" :loadMake="false" @result="resultPath" :usingComponents="true" />
							<image src="/static/image/pay/qqqrcode2.png" mode="aspectFit" class="image2" v-else />
						</view>
						<view class="money">
							<text>{{$toolbox.formatCurrencyManual(payInfo.amount,'',0)}}</text><text
								class="margin-left-sm">{{payInfo.curType}}</text>
						</view>
						<view class="due-date" v-if="formattedDueDate">
							{{formattedDueDate}}
						</view>
						<block v-if="!istimeout">
							<button class="cu-btn mybg-primary round margin-top height-27px" style="padding: 0 25px;"
								@click="saveCode" v-if="payInfo.orderStatus==1">
								<image src="/static/image/pay/download.png" mode="aspectFit" class=" margin-right-sm"
									style="width: 15px;height: 15px;" />
								<!-- <text class="cuIcon-down margin-right-sm"></text> -->
								<text class="text-sm">Save QR Image</text>
							</button>
							<!-- <button v-if="payInfo.orderStatus==1" icon="download"
							style="width: 140px;background-color: black;border: 0px;border-radius: 10px;" class="margin-top"
							size="normal" type="primary" @click="saveCode" >
							<image src="/static/image/pay/save.png" class="my-icon2"></image> Save QR</button> -->
						</block>

					</view>
				</view>

				<!-- <view class="intro text-center padding" v-if="payInfo.orderStatus==1">
					<view class="payTips">Please use <text>{{payInfo.payUserPhone}}</text> to pay
						<text>{{$toolbox.formatCurrencyManual(payInfo.amount,'',0)}}{{payInfo.curType}}</text> to
						<text>{{payInfo.receiveAccount}}</text>
					</view>
					<button class="cu-btn mybg-primary margin-top" @click="copyCardNo">
						<text class="cuIcon-copy margin-right-sm"></text>
						<text class="text-sm">Copy CardNo</text>
					</button>
				</view> -->
				<view class="intro text-center padding-xs">
					<view class="notice-text">*{{$t('important_notice')}}*</view>
					<view class="notice-text">{{$t('payment.operatingTips1')}}</view>
					<view class="notice-text">{{$t('payment.operatingTips2')}}</view>
					<image class="width-100" src="/static/image/pay/dash-border.png" style="height: 1px;"></image>
					<view class="text-left padding">
						<view class="pay-tips">{{$t('payment.how_to_pay')}}</view>
						<view class="pay-tips margin-left-xs">{{$t('payment.pay_tips1')}}</view>
						<view class="pay-tips margin-left-xs">{{$t('payment.pay_tips2')}}</view>
						<view class="pay-tips margin-left-xs">{{$t('payment.pay_tips3')}}</view>
						<view class="pay-tips margin-left-xs">{{$t('payment.pay_tips4')}}</view>
					</view>

				</view>
				<!-- <view class="padding text-center">
				<image src="/static/image/img_scan_qr.png" mode="aspectFit" style="width: 250px;" />
			</view> -->
			</block>
			<block v-if="payInfo==null">
				<u-empty mode="order" text="404 | NOT FOUND" style="margin-top: 30vh;">
				</u-empty>
			</block>

			<view class="text-center padding">
				<button class="cu-btn mybg-primary" @click="back_home">
					<text class="cuIcon-home margin-right-sm"></text>
					<text class="text-sm">Back to Home</text>
				</button>
			</view>
			<view class="bottom-confirmation-bar" @click="">
				<view class="flex-row1 align-center" v-if="!istimeout">
					<image src="/static/image/pay/loading.png" class="loading-spinner" mode="aspectFit"></image>
					<view class="confirm-text">{{$t('payment.confirming_payment')}}</view>
				</view>

				<block v-if="payInfo.orderStatus==1">
					<view v-if="!istimeout">
						<view class="countdown-time">
							{{countdownDisplay}}
						</view>
					</view>
					<text class="timeout-text" v-else>{{$t('payment.orderTimeoutTip')}}</text>
				</block>
				<block v-else-if="payInfo.orderStatus==2">
					<view class="completed-text">Pay Completed</view>
				</block>
			</view>
		</scroll-view>
		<view class="cu-modal" style="z-index: 998;" :class="modalName=='error_modal'?'show':''">
			<view class="cu-dialog bg-white" style="border-radius: 12px;color: #FF0000;line-height: 1.3;">
				<view class="flex-column">
					<view class="padding"></view>
					<image src="/static/image/pay/error.png" style="height: 45px;width: 45px;"></image>
					<text class="padding-tb">{{$t('payment.payment_not_successful')}}</text>
					<view class="text-left flex-column1 align-start width-80">
						<text>{{$t('payment.error_description')}}</text>
						<text>{{$t('payment.payment_not_successful_tips1')}}</text>
						<text>{{$t('payment.payment_not_successful_tips2')}}</text>
						<text>{{$t('payment.payment_not_successful_tips3')}}</text>
					</view>
					<view class="padding-sm"></view>
					<view class="solid-top flex-row justify-between height-57px text-black"
						style="border-top: 1px solid #626262;">
						<view class="width-50" @click="modalName=''">
							{{$t('payment.cancel')}}
						</view>
						<view class="height-100 width-1px" style="background-color: #626262;"></view>
						<view class="width-50" @click="back_home">
							{{$t('payment.try_again')}}
						</view>
					</view>
				</view>
			</view>
		</view>
		<!--
			<u-loading-page :loading="!isload"></u-loading-page>
		-->
	</view>
</template>
<script>
	import tkiQrcode from '@/components/tki-qrcode/tki-qrcode.vue'
	let intervalSearch;
	export default {
		components: {
			tkiQrcode
		},
		data() {
			return {
				dataId: '',
				payInfo: {
					qrcode: "",
					amount: 0,
					curType: "",
					payTimeout: "",
				},
				istimeout: false,
				timeout: 1000,
				timeData: {},
				isload: false,
				countdown: 0, // 倒计时总秒数
				countdownDisplay: '00:00', // 格式化后的显示时间
				countdownTimer: null, // 计时器ID
				qrcode_path: '', //二维码地址
				modalName: '',
				formattedDueDate: '', // 格式化后的到期时间
			};
		},
		onLoad(opt) {
			this.dataId = opt.id;
			this.getdata();
		},
		onUnload() {
			if (intervalSearch) clearInterval(intervalSearch);
		},
		methods: {
			getdata() {
				let that = this;
				that.$httpPay.post('/pay/order/payment', {
					id: this.dataId
				}, res => {
					if (res.statusCode === 200 && res.data && res.data.ok) {
						this.payInfo = res.data.data;
						// 格式化到期时间
						this.formattedDueDate = this.formatDueDate(res.data.data.createTime);
						//计算倒计时时间
						// this.timeout = that.util.getCountdownSeconds(this.payInfo.payTimeout);
						this.timeout = this.payInfo.timeout;
						if (this.timeout <= 0 || this.payInfo.orderStatus != 1) {
							this.istimeout = true;
							that.modalName = 'error_modal';
						} else {
							this.startCountdown(this.timeout);
							if (intervalSearch) clearInterval(intervalSearch);
							intervalSearch = setInterval(this.startSearch, 3000);
						}
						this.isload = true;
						if (!this.istimeout) {
							setTimeout(() => {
								that.$refs.qrcode._makeCode()
							}, 500);
						}
					} else {
						// 请求成功但业务失败的情况
						that.modalName = 'error_modal';
						uni.showModal({
							title: 'Tips',
							content: res.data ? res.data.msg : 'Network error',
							confirmText: 'OK',
							showCancel: false
						})
					}
				}, err => {
					// 网络请求失败的情况
					console.error('Network request failed:', err);
					that.modalName = 'error_modal';
					that.isload = true;
					uni.showModal({
						title: 'Network Error',
						content: 'Please check your network connection and try again',
						confirmText: 'OK',
						showCancel: false
					});
				});

			},
			startSearch() {
				let that = this;
				that.$httpPay.post('/pay/order/payment', {
					id: this.dataId
				}, res => {
					if (res.statusCode === 200 && res.data && res.data.ok) {
						that.payInfo = res.data.data;
						if (that.payInfo.orderStatus == 2) {
							//支付成功
							uni.showModal({
								title: 'Tips',
								content: "Pay Completed. Back Home",
								showCancel: false,
								confirmText: 'Back Home',
								success: function(res) {
									uni.redirectTo({
										url: "/?mix=0"
									})
								}
							});
							if (intervalSearch) clearInterval(intervalSearch);
							return;
						}
						//计算倒计时时间
						// let timeout = that.util.getCountdownSeconds(this.payInfo.payTimeout)
						let timeout = this.payInfo.timeout;
						if (timeout <= 0 || that.payInfo.orderStatus != 1) {
							if (intervalSearch) clearInterval(intervalSearch);
						}
					} else {
						that.payInfo = null;
						that.modalName = 'error_modal'
					}
				});
			},
			/**
			 * 开始倒计时
			 * @param {number} seconds - 倒计时总秒数
			 */
			startCountdown(seconds) {
				// 清除之前的计时器
				if (this.countdownTimer) {
					clearInterval(this.countdownTimer);
					this.countdownTimer = null;
				}

				// 设置初始倒计时值
				this.countdown = seconds;

				// 立即更新一次显示
				this.updateCountdownDisplay();

				// 启动计时器，每秒更新一次
				this.countdownTimer = setInterval(() => {
					this.countdown--;
					this.updateCountdownDisplay();

					// 倒计时结束
					if (this.countdown <= 0) {
						if (this.countdownTimer) {
							clearInterval(this.countdownTimer);
							this.countdownTimer = null;
						}
						this.istimeout = true;
					}
				}, 1000);
			},
			/**
			 * 更新倒计时显示格式为 00:00
			 */
			updateCountdownDisplay() {
				const hours = Math.floor(this.countdown / 3600);
				const minutes = Math.floor((this.countdown % 3600) / 60);
				const secs = this.countdown % 60;
				let arr = [];
				if (hours > 0) {
					arr = [hours, minutes, secs];
				} else {
					arr = [minutes, secs];
				}
				this.countdownDisplay = arr
					.map(unit => unit.toString().padStart(2, '0'))
					.join(':');
			},
			saveCode() {
				// #ifdef H5
				if (this.qrcode_path) {
					this.saveBase64Image(this.qrcode_path);
				}
				// #endif
				// #ifndef H5
				this.$refs.qrcode._saveCode();
				// #endif
			},
			// 在methods中添加保存Base64图片的方法
			saveBase64Image(base64Data) {
				// 创建a标签
				const link = document.createElement('a');
				link.href = base64Data;

				// 设置下载文件名
				const timestamp = new Date().getTime();
				link.download = `recharge_${this.payInfo.amount}_${timestamp}.png`;

				// 触发点击事件
				document.body.appendChild(link);
				link.click();
				document.body.removeChild(link);

				// 提示用户
				uni.showToast({
					title: 'qrcode photo download starting',
					icon: 'success'
				});
			},
			resultPath(res) {
				this.qrcode_path = res;
			},
			onChange(e) {
				this.timeData = e;
				if (e.minutes == 0 && e.seconds == 0) {
					this.istimeout = true;
				}
			},
			copyCardNo() {
				uni.setClipboardData({
					data: this.payInfo.receiveAccount,
					success: function() {
						console.log('copy success');
					}
				});
			},
			back_home() {
				uni.redirectTo({
					url: '/pages/wallet/wallet'
				})
			},
			formatDueDate(createTime) {
				if (!createTime) return '';

				// 将中国时间转换为缅甸时间（减去1.5小时）
				const chinaDate = new Date(createTime);
				const myanmarTime = new Date(chinaDate.getTime() - (1.5 * 60 * 60 * 1000));

				const options = {
					weekday: 'long',
					day: '2-digit',
					month: 'short',
					year: 'numeric',
					hour: '2-digit',
					minute: '2-digit',
					hour12: true,
					timeZone: 'Asia/Yangon' // 使用缅甸时区
				};

				const formattedDate = myanmarTime.toLocaleDateString('en-US', options);
				return `Due by ${formattedDate}`;
			},
		}
	};
</script>
<style scoped>
	page {
		background-color: white;
	}

	.header-placeholder {
		height: 220px;
		width: 100%;
	}

	.full-page {
		display: flex;
		flex-direction: column;
	}

	.payment-content {
		background-color: white;
		flex: 1;
		height: 0;
		overflow-y: auto;
	}

	.top-image {
		display: flex;
		justify-content: center;
		background-color: #D9D9D9;
		height: 60px;
		align-items: center;
		color: black;
		font-size: 20px;
		border-top-right-radius: 10px;
		border-top-left-radius: 10px;
	}

	.top-image .logo {
		height: 45px;
		border-radius: 10px;
	}

	.timeout {
		width: 180px;
		margin: 0px auto;
		text-align: center;
		padding: 10px;
		border: 1px solid #E0E0E0;
		border-radius: 10px;
		background-color: #FAFAFA;
	}

	.timeout .time {
		font-size: 22px;
	}

	.qrcode {
		text-align: center;
		padding: 10px 50px;
	}

	.qrcode .image {
		display: flex;
		justify-content: center;
		align-items: center;
		/* 垂直居中 */
		width: 150px;
		height: 150px;
		background-color: #fff;
		margin: 0 auto;
		position: relative;
		margin-top: 10px;
	}

	.qrcode .image2 {
		width: 150px;
		height: 150px;
		margin-bottom: 10px;
	}

	.qrcode .money {
		font-size: 14px;
		line-height: 1;
		color: #0B356A;
	}

	.due-date {
		font-size: 12px;
		color: #9B9999;
		margin-top: 8px;
		text-align: center;
	}

	.qrcode .time {
		color: #BD1812;
		font-weight: bold;
	}

	.intro {
		margin: 10px auto;
		border-radius: 10px;
		background-color: #F1F1F1;
		width: calc(100vw - 36px);
	}

	.my-icon2 {
		width: 20px;
		height: 20px;
		margin-right: 8px;
	}

	.payTips text {
		color: #0B356A;
		font-weight: bold;
		margin: 0px 6px;
	}

	.pay-tips {
		line-height: 1.3;
		color: black;
		margin-bottom: 10px;
	}

	/* 底部确认支付条 */
	.bottom-confirmation-bar {
		position: fixed;
		bottom: 0;
		left: 0;
		right: 0;
		background-color: #E6EFFF;
		display: flex;
		flex-direction: row;
		align-items: center;
		justify-content: space-between;
		gap: 15px;
		padding: 10px 25px;
		/* box-shadow: 0 -2px 8px rgba(0, 0, 0, 0.1); */
		z-index: 1;
		border-top: 1px solid #e5e7eb;
		border-top-right-radius: 10px;
		border-top-left-radius: 10px;
	}

	/* 加载动画 */
	.loading-spinner {
		width: 25px;
		height: 25px;
		animation: spin 1s linear infinite;
	}

	@keyframes spin {
		0% {
			transform: rotate(0deg);
		}

		100% {
			transform: rotate(360deg);
		}
	}

	/* 确认文字 */
	.confirm-text {
		font-size: 14px;
		font-weight: bold;
		color: #0B356A;
		margin-left: 12px;
	}

	/* 倒计时时间 */
	.countdown-time {
		font-size: 14px;
		font-weight: bold;
		color: #0B356A;
	}

	/* 超时文字 */
	.timeout-text {
		font-size: 14px;
		color: #ef4444;
		line-height: 1.3;
	}

	/* 完成文字 */
	.completed-text {
		font-size: 16px;
		font-weight: bold;
		color: #10b981;
	}

	/* 为固定底部栏留出空间 */
	.payment-content {
		padding-bottom: 52px;
	}

	.notice-text {
		color: #FB0000;
		font-weight: bold;
		line-height: 1.3;
		margin-top: 10px;
		padding: 0 15px;
	}
</style>