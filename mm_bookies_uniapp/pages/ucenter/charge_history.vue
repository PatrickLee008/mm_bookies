<template>
	<view class="bg-white full-page">
		<zw-header></zw-header>
		<!-- 顶栏 -->
		<view class="title-bar" style="height: auto;">
			<view class="flex-row justify-between align-center" style="padding: 10px 15px;">
				<view class="flex-row align-center" style="">
					<image src="/static/icon/basic/back.svg" mode="widthFix" class="width-30px"
						@click="goBack()"></image>
					<image src="/static/icon/ucenter/wallet2.svg" mode="widthFix" class="width-20px margin-left-sm"></image>
					<text class="title-text margin-left-sm">{{$t('charge_history') || 'Charge Records'}}</text>
				</view>
				<view class="flex-row align-center">
					<text class="cuIcon-refresh myfont-18px mycolor-primary" @click="refreshData" :class="refreshing ? 'rotating' : ''"></text>
				</view>
			</view>
		</view>

		<!-- 记录列表 -->
		<scroll-view scroll-y style="height: calc(100vh - 190px);padding-top: 2px;" @scrolltolower="loadMore" :refresher-enabled="true" 
			@refresherrefresh="onRefresh" :refresher-triggered="refresherTriggered">
			
			<!-- 空状态 -->
			<view v-if="!loading && recordList.length === 0" class="empty-state">
				<image src="/static/icon/history.png" mode="aspectFit" class="empty-icon"></image>
				<text class="empty-text">{{$t('no_charge_records') || 'No charge records'}}</text>
			</view>

			<!-- 记录项 -->
			<view v-for="(item, index) in recordList" :key="index" class="record-item">
				<view class="record-header">
					<view class="flex-row justify-between align-center">
						<view class="flex-row align-center">
							<image :src="`/static/icon/register/${item.mb_bank_code || 'KBZ Pay'}.png`" 
								mode="aspectFit" class="bank-icon"></image>
							<view class="flex-column margin-left-sm">
								<text class="bank-name">{{item.mb_bank_code || 'KBZ Pay'}}</text>
								<text class="order-id">{{item.id}}</text>
							</view>
						</view>
						<view class="flex-column align-end">
							<text class="amount-text" :class="getAmountClass(item.status)">
								{{item.status === 'Success' ? '+' : ''}}{{numberFormat(item.money)}} Ks
							</text>
							<text class="status-text" :class="getStatusClass(item.status)">
								{{getStatusText(item.status)}}
							</text>
						</view>
					</view>
				</view>
				
				<view class="record-content">
					<view class="info-row">
						<text class="label">{{$t('create_time') || 'Create Time'}}:</text>
						<text class="value">{{formatTime(item.create_time)}}</text>
					</view>
					<view class="info-row" v-if="item.pay_channel">
						<text class="label">{{$t('pay_channel') || 'Pay Channel'}}:</text>
						<text class="value">{{formatPayChannel(item.pay_channel)}}</text>
					</view>
					<view class="info-row" v-if="item.out_trade_no">
						<text class="label">{{$t('trade_no') || 'Trade No'}}:</text>
						<text class="value">{{item.out_trade_no}}</text>
					</view>
					<view class="info-row" v-if="item.mb_acc_name">
						<text class="label">{{$t('payer_name') || 'Payer Name'}}:</text>
						<text class="value">{{item.mb_acc_name}}</text>
					</view>
					<view class="info-row" v-if="item.mb_acc_number">
						<text class="label">{{$t('payer_account') || 'Payer Account'}}:</text>
						<text class="value">{{item.mb_acc_number}}</text>
					</view>
					<view class="info-row" v-if="item.receive_account_name">
						<text class="label">{{$t('receiver_name') || 'Receiver Name'}}:</text>
						<text class="value">{{item.receive_account_name}}</text>
					</view>
					<view class="info-row" v-if="item.receive_account">
						<text class="label">{{$t('receiver_account') || 'Receiver Account'}}:</text>
						<text class="value">{{item.receive_account}}</text>
					</view>
					<view class="info-row" v-if="item.fail_reason && item.status=='Failed'">
						<text class="label">{{$t('fail_reason') || 'Fail Reason'}}:</text>
						<text class="value fail-reason">{{item.fail_reason}}</text>
					</view>
				</view>

				<!-- 操作按钮 -->
				<view class="record-actions" v-if="canContinuePayment(item)">
					<view class="continue-btn" @click="continuePayment(item)">
						<text class="cuIcon-play myfont-14px margin-right-xs"></text>
						<text>{{$t('continue_payment') || 'Continue Payment'}}</text>
					</view>
				</view>
			</view>

			<!-- 加载更多 -->
			<view v-if="loading" class="loading-more">
				<text class="cuIcon-loading2 load-icon rotating"></text>
				<text class="loading-text">{{$t('loading') || 'Loading...'}}</text>
			</view>
			
			<!-- 没有更多 -->
			<view v-if="!loading && hasMore === false && recordList.length > 0" class="no-more">
				<text>{{$t('no_more_data') || 'No more data'}}</text>
			</view>
		</scroll-view>
	</view>
</template>

<script>
import config from '../../utils/config.js'
import dateFormatUtils from "../../utils/utils.js"

export default {
	data() {
		return {
			language: config.language,
			recordList: [],
			loading: false,
			refreshing: false,
			refresherTriggered: false,
			hasMore: true,
			page: 1,
			pageSize: 8
		}
	},
	methods: {
		// 返回上一页
		goBack() {
			uni.navigateBack();
		},
		
		// 刷新数据
		refreshData() {
			if (this.refreshing) return;
			this.refreshing = true;
			this.page = 1;
			this.hasMore = true;
			this.recordList = [];
			this.loadChargeRecords();
		},
		
		// 下拉刷新
		onRefresh() {
			setTimeout(()=>{
				this.refresherTriggered = true;
				this.page = 1;
				this.hasMore = true;
				this.recordList = [];
				this.loadChargeRecords().finally(() => {
					this.refresherTriggered = false;
				});
			},500)
		},
		
		// 加载更多
		loadMore() {
			if (!this.hasMore || this.loading) return;
			this.page++;
			this.loadChargeRecords();
		},
		
		// 加载充值记录
		async loadChargeRecords() {
			if (this.loading) return;
			
			this.loading = true;
			
			try {
				const para = {
					page: this.page,
					limit: this.pageSize
				};
				
				await new Promise((resolve, reject) => {
					this.$http.get('/charge_apply/get', { data: para }, (res) => {
						if (res.statusCode === 200) {
							const items = res.data.items || [];
							
							if (this.page === 1) {
								this.recordList = items;
							} else {
								this.recordList.push(...items);
							}
							
							// 判断是否还有更多数据
							this.hasMore = items.length === this.pageSize;
							
							resolve();
						} else {
							reject(new Error(res.data.message || 'Load failed'));
						}
					});
				});
			} catch (error) {
				console.error('Load charge records failed:', error);
				uni.showToast({
					title: error.message || 'Load failed',
					icon: 'none'
				});
			} finally {
				this.loading = false;
				this.refreshing = false;
			}
		},
		
		// 格式化时间
		formatTime(time) {
			if (!time) return '';
			// 如果是字符串，先转换为Date对象
			const date = typeof time === 'string' ? new Date(time) : time;
			return dateFormatUtils.formatTime(date);
		},
		
		// 格式化金额
		numberFormat(number) {
			return dateFormatUtils.numFormat(number);
		},
		
		// 格式化支付渠道显示
		formatPayChannel(channel) {
			const channelMap = {
				'TCPay': 'QR Pay',
				'NFM2': 'Transfer'
			};
			return channelMap[channel] || channel;
		},
		
		// 获取状态文本
		getStatusText(status) {
			const statusMap = {
				'Pending': this.$t('processing') || 'Pending',
				'Success': this.$t('success') || 'Success', 
				'Rejected': this.$t('rejected') || 'Rejected',
				'New': this.$t('new') || 'New',
				'Failed': this.$t('failed') || 'Failed',
				'Timeout': this.$t('timeout') || 'Timeout'
			};
			return statusMap[status] || status;
		},
		
		// 获取状态样式类
		getStatusClass(status) {
			const classMap = {
				'Pending': 'status-pending',
				'Success': 'status-success',
				'Rejected': 'status-failed', 
				'New': 'status-new',
				'Failed': 'status-failed',
				'Timeout': 'status-timeout'
			};
			return classMap[status] || 'status-default';
		},
		
		// 获取金额样式类
		getAmountClass(status) {
			if (status === 'Success') {
				return 'amount-success';
			} else if (status === 'Rejected' || status === 'Failed' || status === 'Timeout') {
				return 'amount-failed';
			}
			return 'amount-pending';
		},
		
		// 判断是否可以继续支付
		canContinuePayment(item) {
			// 只有待处理状态的订单可以继续支付
			return item.status === 'Pending';
		},
		
		// 继续支付
		continuePayment(item) {
			if (this.$toolbox && this.$toolbox.click_too_fast && this.$toolbox.click_too_fast(1)) return;
			
			// TCPay渠道跳转到支付页面
			if (item.pay_channel === 'TCPay') {
				uni.navigateTo({
					url: `/pages/payment/payment?id=${item.out_order_id}`
				});
			} else {
				// 其他支付方式的处理
				uni.showToast({
					title: this.$t('payment_not_supported') || 'Payment method not supported',
					icon: 'none'
				});
			}
		}
	},
	
	onLoad() {
		this.loadChargeRecords();
	}
}
</script>

<style scoped>
.record-item {
	margin: 10px 15px;
	background-color: #ffffff;
	border-radius: 12px;
	box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
	overflow: hidden;
}

.record-header {
	padding: 15px;
	border-bottom: 1px solid #f5f5f5;
}

.bank-icon {
	width: 40px;
	height: 40px;
	border-radius: 8px;
}

.bank-name {
	font-size: 16px;
	font-weight: bold;
	color: #333333;
}

.order-id {
	font-size: 12px;
	color: #999999;
	margin-top: 2px;
}

.amount-text {
	font-size: 18px;
	font-weight: bold;
	text-align: right;
}

.amount-success {
	color: #52c41a;
}

.amount-failed {
	color: #ff4d4f;
}

.amount-pending {
	color: #fa8c16;
}

.status-text {
	font-size: 12px;
	margin-top: 4px;
	padding: 2px 8px;
	border-radius: 12px;
	text-align: center;
}

.status-success {
	background-color: #f6ffed;
	color: #52c41a;
}

.status-failed {
	background-color: #fff2f0;
	color: #ff4d4f;
}

.status-timeout {
	background-color: #fff2f0;
	color: #ff4d4f;
}

.status-pending {
	background-color: #fff7e6;
	color: #fa8c16;
}

.status-processing {
	background-color: #e6f7ff;
	color: #1890ff;
}

.status-new {
	background-color: #f0f9ff;
	color: #0284c7;
}

.status-default {
	background-color: #fafafa;
	color: #999999;
}

.record-content {
	padding: 15px;
	background-color: #fafafa;
}

.info-row {
	display: flex;
	justify-content: space-between;
	margin-bottom: 8px;
}

.info-row:last-child {
	margin-bottom: 0;
}

.label {
	font-size: 14px;
	color: #666666;
	flex-shrink: 0;
}

.value {
	font-size: 14px;
	color: #333333;
	text-align: right;
	flex: 1;
	margin-left: 10px;
}

.record-actions {
	padding: 15px;
	border-top: 1px solid #f5f5f5;
}

.continue-btn {
	background-color: #0081ff;
	color: white;
	padding: 12px 20px;
	border-radius: 8px;
	text-align: center;
	display: flex;
	align-items: center;
	justify-content: center;
}

.empty-state {
	display: flex;
	flex-direction: column;
	align-items: center;
	justify-content: center;
	padding: 60px 20px;
}

.empty-icon {
	width: 120px;
	height: 120px;
	opacity: 0.6;
}

.empty-text {
	font-size: 16px;
	color: #999999;
	margin-top: 20px;
}

.loading-more {
	display: flex;
	align-items: center;
	justify-content: center;
	padding: 20px;
}

.load-icon {
	margin-right: 10px;
}

.rotating {
	animation: rotate 1s linear infinite;
}

@keyframes rotate {
	from {
		transform: rotate(0deg);
	}
	to {
		transform: rotate(360deg);
	}
}

.loading-text {
	font-size: 14px;
	color: #999999;
}

.no-more {
	text-align: center;
	padding: 20px;
	color: #999999;
	font-size: 14px;
}

.fail-reason {
	color: #ff4d4f !important;
	font-weight: bold;
}
</style>