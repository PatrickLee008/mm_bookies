<template>
	<view class="bg-white full-page">
		<zw-header></zw-header>
		<view class="header-placeholder"></view>
		<!-- 滚动内容区域 -->
		<scroll-view scroll-y class="payment-content">
			<block>
				<!-- <block v-if="isload && payInfo"> -->
				<!-- 隐藏的二维码生成组件 -->
				<view style="position: fixed; left: -9999px; top: 0;">
					<tki-qrcode cid="qrcode2" ref="qrcode" :val="payInfo.qrcode"
						loadingText="loading" v-if="!istimeout && payInfo.orderStatus==1" :size="250"
						:onval="false" :loadMake="false" @result="resultPath" :usingComponents="true" />
				</view>

				<!-- 显示合成后的完整图片 -->
				<view class=""
					style="width: calc(100vw - 36px);margin: 10px 18px 0;border: 1px solid #D9D9D9;border-radius: 10px;overflow: hidden;">
					<view class="qrcode">
						<!-- 合成图片展示区域 -->
						<view class="image" style="padding: 10px;">
							<!-- 加载中状态 -->
							<view v-if="isCompositing" class="text-center" style="padding: 100px 0;">
								<text>Generating QR Image...</text>
							</view>

							<!-- 显示合成图片 -->
							<image
								v-else-if="compositeImagePath && !compositeError"
								:src="compositeImagePath"
								mode="widthFix"
								style="width: 100%; display: block; margin: 0 auto;"
							/>

							<!-- 默认图片（合成失败或超时） -->
							<image
								v-else
								src="/static/image/pay/qqqrcode2.png"
								mode="aspectFit"
								class="image2"
								style="width: 100%; display: block; margin: 0 auto;"
							/>
						</view>

						<!-- 保存按钮 -->
						<block v-if="!istimeout">
							<button class="cu-btn mybg-primary round margin-top margin-bottom height-27px" style="padding: 0 25px;"
								@click="saveCode" v-if="payInfo.orderStatus==1">
								<image src="/static/image/pay/download.png" mode="aspectFit" class=" margin-right-sm"
									style="width: 15px;height: 15px;" />
								<text class="text-sm">Save QR Image</text>
							</button>
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
					<text class="text-sm">{{ $t('back_to_home') }}</text>
				</button>
			</view>
		</scroll-view>
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
				<view class="completed-text">{{ $t('pay_completed') }}</view>
			</block>
		</view>
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

		<!-- 隐藏的canvas用于图片合成 -->
		<canvas
			canvas-id="paymentCanvas"
			id="paymentCanvas"
			:style="{width: '400px', height: '600px', position: 'fixed', left: '-9999px', top: '0'}"
		></canvas>
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
				compositeImagePath: '', // 合成后的完整图片路径
				isCompositing: false, // 是否正在合成图片
				compositeError: false, // 合成图片是否出错
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
							title: that.$t('tips'),
							content: res.data ? res.data.msg : that.$t('network_error'),
							confirmText: that.$t('ok'),
							showCancel: false
						})
					}
				}, err => {
					// 网络请求失败的情况
					console.error('Network request failed:', err);
					that.modalName = 'error_modal';
					that.isload = true;
					uni.showModal({
						title: that.$t('network_error'),
						content: that.$t('check_network'),
						confirmText: that.$t('ok'),
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
								title: that.$t('tips'),
								content: that.$t('pay_completed_back_home'),
								showCancel: false,
								confirmText: that.$t('back_home_btn'),
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
							that.istimeout = true;
							// auto redirect back to deposit page
							setTimeout(() => {
								uni.redirectTo({
									url: '/pages/wallet/wallet'
								})
							}, 2000)
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
						if (intervalSearch) {
							clearInterval(intervalSearch);
							intervalSearch = null;
						}
						this.istimeout = true;
						// 自动跳转回充值页面
						this.$nextTick(() => {
							setTimeout(() => {
								uni.redirectTo({
									url: '/pages/wallet/wallet'
								})
							}, 2000)
						})
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
			async saveCode() {
				try {
					// 如果合成图片还未生成或生成失败，尝试重新生成
					if (!this.compositeImagePath || this.compositeError) {
						uni.showLoading({
							title: 'Generating...',
							mask: true
						});
						await this.generateCompositeImage();
						uni.hideLoading();
					}

					// 检查是否有可用的图片
					if (!this.compositeImagePath) {
						uni.showToast({
							title: 'No image available',
							icon: 'none'
						});
						return;
					}

					const imagePath = this.compositeImagePath;

					// #ifdef H5
					// H5端下载
					this.downloadImageH5(imagePath);
					// #endif

					// #ifndef H5
					// App端和小程序保存到相册
					uni.saveImageToPhotosAlbum({
						filePath: imagePath,
						success: () => {
							uni.showToast({
								title: 'Saved successfully',
								icon: 'success'
							});
						},
						fail: (err) => {
							console.error('Save failed:', err);
							uni.showToast({
								title: 'Save failed',
								icon: 'none'
							});
						}
					});
					// #endif

				} catch (error) {
					console.error('Save image failed:', error);
					uni.showToast({
						title: 'Failed to save image',
						icon: 'none'
					});
				}
			},
			/**
			 * H5端下载图片
			 */
			downloadImageH5(base64Data) {
				const link = document.createElement('a');
				link.href = base64Data;
				const timestamp = new Date().getTime();
				link.download = `payment_qr_${this.payInfo.amount}_${timestamp}.png`;
				document.body.appendChild(link);
				link.click();
				document.body.removeChild(link);
				uni.showToast({
					title: 'Download started',
					icon: 'success'
				});
			},
			resultPath(res) {
				this.qrcode_path = res;
				// 二维码生成后，自动合成完整图片
				this.generateCompositeImage();
			},
			/**
			 * 合成完整的支付二维码图片（背景图 + 二维码 + 银行logo + 打星卡号）
			 */
			async compositePaymentImage() {
				return new Promise((resolve, reject) => {
					// 先加载底图获取其实际尺寸
					this.loadImage('/static/image/pay/payment-qrcode-bg.jpg').then((bgImage) => {
						const ctx = uni.createCanvasContext('paymentCanvas', this);

						// 使用底图的实际尺寸作为Canvas尺寸
						const canvasWidth = bgImage.width;
						const canvasHeight = bgImage.height;

						// 加载其他图片资源
						const loadImages = [
							this.loadImage(this.qrcode_path), // 二维码
						];

						// 根据paymentType加载对应的银行图标
						let bankIconPath = null;
						if (this.payInfo.paymentType === 'KBZ') {
							bankIconPath = '/static/icon/register/KBZ Pay.png';
						} else if (this.payInfo.paymentType === 'WaveMoney') {
							bankIconPath = '/static/icon/register/Wave Money.png';
						}

						if (bankIconPath) {
							loadImages.push(this.loadImage(bankIconPath));
						}

						Promise.all(loadImages).then((images) => {
							const [qrImage, bankIcon] = images;

							// 1. 绘制底图（使用实际尺寸）
							ctx.drawImage(bgImage.path, 0, 0, canvasWidth, canvasHeight);

							// 2. 绘制二维码（在白色矩形框内居中，下移10px）
							const whiteBoxTop = canvasHeight * 0.243;
							const whiteBoxBottom = canvasHeight * 0.725;
							const whiteBoxHeight = whiteBoxBottom - whiteBoxTop;
							const whiteBoxWidth = canvasWidth * 0.8125;

							const padding = canvasWidth * 0.075;
							const qrSize = Math.min(whiteBoxWidth - padding * 2, whiteBoxHeight - padding * 2, 500);

							const qrX = (canvasWidth - qrSize) / 2;
							const qrY = whiteBoxTop + (whiteBoxHeight - qrSize) / 2 + 30;

							ctx.drawImage(qrImage.path, qrX, qrY, qrSize, qrSize);

							// 3. 绘制银行图标（上移20px，带圆角5px裁剪）
							const iconSize = Math.min(canvasWidth * 0.15, 120);
							const iconX = (canvasWidth - iconSize) / 2;
							const iconY = canvasHeight * 0.784;
							if (bankIcon && bankIcon.path) {
								const borderRadius = 5;

								ctx.save();
								ctx.beginPath();
								ctx.moveTo(iconX + borderRadius, iconY);
								ctx.lineTo(iconX + iconSize - borderRadius, iconY);
								ctx.arc(iconX + iconSize - borderRadius, iconY + borderRadius, borderRadius, 1.5 * Math.PI, 2 * Math.PI);
								ctx.lineTo(iconX + iconSize, iconY + iconSize - borderRadius);
								ctx.arc(iconX + iconSize - borderRadius, iconY + iconSize - borderRadius, borderRadius, 0, 0.5 * Math.PI);
								ctx.lineTo(iconX + borderRadius, iconY + iconSize);
								ctx.arc(iconX + borderRadius, iconY + iconSize - borderRadius, borderRadius, 0.5 * Math.PI, Math.PI);
								ctx.lineTo(iconX, iconY + borderRadius);
								ctx.arc(iconX + borderRadius, iconY + borderRadius, borderRadius, Math.PI, 1.5 * Math.PI);
								ctx.closePath();
								ctx.clip();

								ctx.drawImage(bankIcon.path, iconX, iconY, iconSize, iconSize);
								ctx.restore();
							}

							// 4. 绘制账户号码文字（在银行logo下方，脱敏处理，字体加大2号）
							const fontSize = Math.floor(canvasWidth * 0.035) + 2;
							ctx.setFontSize(fontSize);
							ctx.setFillStyle('#FFFFFF');
							ctx.setTextAlign('center');
							const rawAccount = this.payInfo.receiveAccount || 'Account Number';
							const accountText = this.maskAccountNumber(rawAccount);
							const accountY = iconY + iconSize + fontSize + 13;
							ctx.fillText(accountText, canvasWidth / 2, accountY);

							// 5. 执行绘制
							ctx.draw(false, () => {
								setTimeout(() => {
									uni.canvasToTempFilePath({
										canvasId: 'paymentCanvas',
										destWidth: canvasWidth,
										destHeight: canvasHeight,
										fileType: 'png',
										quality: 1,
										success: (res) => {
											this.compositeImagePath = res.tempFilePath;
											resolve(res.tempFilePath);
										},
										fail: (err) => {
											console.error('canvasToTempFilePath failed:', err);
											reject(err);
										}
									}, this);
								}, 500);
							});
						}).catch((err) => {
							console.error('Load images failed:', err);
							reject(err);
						});
					}).catch((err) => {
						console.error('Load background image failed:', err);
						reject(err);
					});
				});
			},

			/**
			 * 银行卡账号脱敏处理（只保留后四位，前面用*替代）
			 */
			maskAccountNumber(accountNumber) {
				if (!accountNumber || accountNumber === 'Account Number') {
					return accountNumber;
				}
				const str = String(accountNumber);
				if (str.length <= 4) {
					return str;
				}
				const lastFour = str.slice(-4);
				const maskedPart = '*'.repeat(str.length - 4);
				return maskedPart + lastFour;
			},

			/**
			 * 加载图片资源
			 */
			loadImage(src) {
				return new Promise((resolve, reject) => {
					// 如果是base64图片，直接返回
					if (src && src.startsWith('data:image')) {
						resolve({
							path: src,
							width: 250,
							height: 250
						});
						return;
					}

					uni.getImageInfo({
						src: src,
						success: (res) => {
							resolve(res);
						},
						fail: (err) => {
							console.error('Load image failed:', src, err);
							reject(err);
						}
					});
				});
			},

			/**
			 * 生成合成图片（内部调用）
			 */
			async generateCompositeImage() {
				if (!this.qrcode_path || !this.payInfo) {
					return;
				}

				try {
					this.isCompositing = true;
					this.compositeError = false;

					const imagePath = await this.compositePaymentImage();
					this.compositeImagePath = imagePath;
				} catch (error) {
					console.error('Failed to generate composite image:', error);
					this.compositeError = true;
				} finally {
					this.isCompositing = false;
				}
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
		padding: 10px 15px;
	}

	.qrcode .image {
		display: flex;
		justify-content: center;
		align-items: center;
		width: 100%;
		max-width: 100%;
		height: auto;
		background-color: #fff;
		margin: 0 auto;
		position: relative;
		margin-top: 10px;
	}

	.qrcode .image2 {
		width: 100%;
		max-width: 100%;
		height: auto;
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
		/* iOS 安全区适配：避免计时器被底部 Home 横条遮挡 */
		padding-bottom: calc(10px + constant(safe-area-inset-bottom));
		padding-bottom: calc(10px + env(safe-area-inset-bottom));
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