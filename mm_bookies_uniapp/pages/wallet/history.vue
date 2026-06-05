<template>
	<view class="history-component">
		<!-- 筛选器 -->
		<view class="filter-bar" @click="toggleFilterDropdown">
			<text class="filter-text">{{getFilterText()}}</text>
			<text class="filter-icon" :class="filterExpanded ? 'cuIcon-fold' : 'cuIcon-unfold'"></text>
		</view>

		<!-- 下拉选项 -->
		<view v-if="filterExpanded" class="filter-dropdown">
			<view v-for="(option, index) in filterOptions" :key="index" class="filter-option" @click="toggleFilterOption(option)">
				<text class="option-text">{{option.label}}</text>
				<view class="option-radio" :class="{'active': option.checked}">
					<view class="option-radio-inner" v-if="option.checked"></view>
				</view>
			</view>
		</view>

		<scroll-view scroll-y class="history-scroll" @scrolltolower="loadMore" :refresher-enabled="true" @refresherrefresh="onRefresh" :refresher-triggered="refresherTriggered">

			<!-- 空状态 -->
			<view v-if="!loading && filterRecordList(recordList).length === 0" class="empty-state">
				<image src="/static/image/order/empty.svg" mode="aspectFit" class="empty-icon"></image>
				<text class="empty-text">{{$t('no_charge_records') || 'No deposit records available at the moment. Please check back later.'}}</text>
			</view>

			<!-- 记录项 -->
			<view v-for="(item, index) in filterRecordList(recordList)" :key="index" class="record-item">
				<view class="record-header">
					<view class="flex-row justify-between align-center">
						<view class="flex-row1 align-center">
							<image :src="`/static/icon/register/${item.mb_bank_code || 'KBZ Pay'}.png`"
								mode="aspectFit" class="bank-icon"></image>
							<view class="flex-column1 margin-left-sm">
								<text class="bank-name">{{item.mb_bank_code || 'KBZ Pay'}}</text>
								<text class="order-id">{{item.id}}</text>
							</view>
						</view>
						<view class="flex-column1 align-end">
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
						<text class="value fail-reason">{{getFailReason(item.fail_reason)}}</text>
					</view>
				</view>

				<!-- 操作按钮 -->
				<view class="record-actions" v-if="canContinuePayment(item)">
					<view class="continue-btn" @click="continuePayment(item)">
						<text class="cuIcon-play myfont-14px margin-right-xs"></text>
						<text>{{'Continue Payment'}}</text>
					</view>
				</view>
			</view>

			<!-- 加载更多 -->
			<view v-if="loading" class="loading-more">
				<text class="cuIcon-loading2 load-icon rotating"></text>
				<text class="loading-text">{{$t('loading') || 'Loading...'}}</text>
			</view>
			<view class="blank"></view>

			<!-- 没有更多 不需要提示-->
			<!-- <view v-if="!loading && hasMore === false && filterRecordList(recordList).length > 0" class="no-more">
				<text>{{$t('no_more_data') || 'No more data'}}</text>
			</view> -->
		</scroll-view>
	</view>
</template>

<script>
	import config from '../../utils/config.js'
	import dateFormatUtils from "../../utils/utils.js"

	export default {
		name: 'WalletHistory',
		data() {
			return {
				language: config.language,
				recordList: [],
				loading: false,
				refreshing: false,
				refresherTriggered: false,
				hasMore: true,
				page: 1,
				pageSize: 8,

				filterExpanded: false,
				filterOptions: [
					{ label: 'All', value: 'all', checked: true },
					{ label: 'Transfer', value: 'NFM2', type: 'channel', checked: false },
					{ label: 'QR Pay', value: 'TCPay', type: 'channel', checked: false },
					{ label: 'Pending', value: 'Pending', type: 'status', checked: false },
					{ label: 'Success', value: 'Success', type: 'status', checked: false },
					{ label: 'Time Out', value: 'Timeout', type: 'status', checked: false },
				],
			}
		},
		methods: {
			refreshData() {
				if (this.refreshing) return;
				this.refreshing = true;
				this.page = 1;
				this.hasMore = true;
				this.recordList = [];
				this.loadChargeRecords();
			},

			onRefresh() {
				setTimeout(() => {
					this.refresherTriggered = true;
					this.page = 1;
					this.hasMore = true;
					this.recordList = [];
					this.loadChargeRecords().finally(() => {
						this.refresherTriggered = false;
					});
				}, 500)
			},

			loadMore() {
				if (!this.hasMore || this.loading) return;
				this.page++;
				this.loadChargeRecords();
			},

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

			formatTime(time) {
				if (!time) return '';
				const date = typeof time === 'string' ? new Date(time) : time;
				return dateFormatUtils.formatTime(date);
			},

			numberFormat(number) {
				return dateFormatUtils.numFormat(number);
			},

			formatPayChannel(channel) {
				const channelMap = {
					'TCPay': 'QR Pay',
					'VIPPay': 'QR Pay',
					'NFM2': 'Transfer'
				};
				return channelMap[channel] || channel;
			},

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

			getFailReason(reason) {
				if (!reason) return '';
				// If the reason is an error code string longer than 50 chars,
				// display a user-friendly message instead
				if (reason.length > 50) {
					return this.$t('order_failed') || 'Order failed';
				}
				return reason;
			},

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

			getAmountClass(status) {
				if (status === 'Success') {
					return 'amount-success';
				} else if (status === 'Rejected' || status === 'Failed' || status === 'Timeout') {
					return 'amount-failed';
				}
				return 'amount-pending';
			},

			canContinuePayment(item) {
				return item.status === 'Pending';
			},

			continuePayment(item) {
				if (this.$toolbox && this.$toolbox.click_too_fast && this.$toolbox.click_too_fast(1)) return;

				if (item.pay_channel === 'TCPay' || item.pay_channel === 'VIPPay') {
					uni.navigateTo({
						url: `/pages/payment/payment?id=${item.out_order_id}`
					});
				} else {
					uni.showToast({
						title: this.$t('payment_not_supported') || 'Payment method not supported',
						icon: 'none'
					});
				}
			},

			toggleFilterDropdown() {
				this.filterExpanded = !this.filterExpanded;
			},

			toggleFilterOption(option) {
				if (option.value === 'all') {
					const newCheckedState = !option.checked;
					this.filterOptions.forEach(opt => {
						opt.checked = newCheckedState;
					});
				} else {
					option.checked = !option.checked;

					const otherOptions = this.filterOptions.filter(opt => opt.value !== 'all');
					const allOthersChecked = otherOptions.every(opt => opt.checked);
					const allOthersUnchecked = otherOptions.every(opt => !opt.checked);

					const allOption = this.filterOptions.find(opt => opt.value === 'all');
					if (allOthersChecked || allOthersUnchecked) {
						allOption.checked = allOthersChecked;
					}
				}

				this.page = 1;
				this.hasMore = true;
				this.recordList = [];
				this.loadChargeRecords();
			},

			getFilterText() {
				const allOption = this.filterOptions.find(opt => opt.value === 'all');
				if (allOption && allOption.checked) {
					return 'All Transaction';
				}

				const checkedOptions = this.filterOptions.filter(opt => opt.value !== 'all' && opt.checked);
				if (checkedOptions.length === 0) {
					return 'All Transaction';
				}

				if (checkedOptions.length === 1) {
					return checkedOptions[0].label;
				}

				return `${checkedOptions.length} Selected`;
			},

			getFilterParams() {
				const allOption = this.filterOptions.find(opt => opt.value === 'all');
				if (allOption && allOption.checked) {
					return {};
				}

				const params = {};
				const checkedOptions = this.filterOptions.filter(opt => opt.value !== 'all' && opt.checked);

				if (checkedOptions.length === 0) {
					return {};
				}

				const channels = checkedOptions.filter(opt => opt.type === 'channel').map(opt => opt.value);
				const statuses = checkedOptions.filter(opt => opt.type === 'status').map(opt => opt.value);

				if (channels.length > 0) {
					params.pay_channels = channels;
				}
				if (statuses.length > 0) {
					params.statuses = statuses;
				}

				return params;
			},

			filterRecordList(records) {
				const filterParams = this.getFilterParams();

				if (Object.keys(filterParams).length === 0) {
					return records;
				}

				return records.filter(record => {
					let matchChannel = true;
					let matchStatus = true;

					if (filterParams.pay_channels && filterParams.pay_channels.length > 0) {
						matchChannel = filterParams.pay_channels.includes(record.pay_channel);
					}

					if (filterParams.statuses && filterParams.statuses.length > 0) {
						matchStatus = filterParams.statuses.includes(record.status);
					}

					return matchChannel && matchStatus;
				});
			},
		},

		mounted() {
			this.loadChargeRecords();
		}
	}
</script>

<style lang="scss" scoped>
	.history-component {
		width: 100%;
		height: 100%;
		display: flex;
		flex-direction: column;
	}

	/* 筛选器 */
	.filter-bar {
		background: #2F5D62;
		border-radius: 20px;
		padding: 8px 10px;
		display: flex;
		align-items: center;
		justify-content: space-between;
		flex-shrink: 0;
	}

	.filter-text {
		font-size: 12px;
		font-weight: 600;
		color: #ffffff;
	}

	.filter-icon {
		font-size: 12px;
		color: #ffffff;
		transition: transform 0.3s ease;
	}

	.filter-dropdown {
		background: #E8F4F5;
		border-radius: 12px;
		flex-shrink: 0;
	}

	.filter-option {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 5px 10px;
		cursor: pointer;
	}

	.option-text {
		font-size: 12px;
		font-weight: 500;
		color: #2F5D62;
	}

	.option-radio {
		width: 15px;
		height: 15px;
		border: 2px solid #5FB5BD;
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
		transition: all 0.2s;
	}

	.option-radio.active {
		border-color: #5FB5BD;
	}

	.option-radio-inner {
		width: 12px;
		height: 12px;
		background-color: #5FB5BD;
		border-radius: 50%;
	}

	.history-scroll {
		flex: 1;
		height: 0;
		background-color: #ffffff;
	}

	/* 记录项 */
	.record-item {
		margin: 10px 0;
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

	.fail-reason {
		color: #ff4d4f !important;
		font-weight: bold;
	}

	.record-actions {
		padding: 15px;
		border-top: 1px solid #f5f5f5;
	}

	.continue-btn {
		background-color: #2F5D62;
		color: white;
		padding: 12px 20px;
		border-radius: 8px;
		text-align: center;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	/* 空状态 */
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

	/* 加载更多 */
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

	/* 通用 flex 工具类 */
	.flex-row {
		display: flex;
		flex-direction: row;
	}

	.flex-row1 {
		display: flex;
		flex-direction: row;
		flex: 1;
	}

	.flex-column1 {
		display: flex;
		flex-direction: column;
		flex: 1;
	}

	.justify-between {
		justify-content: space-between;
	}

	.align-center {
		align-items: center;
	}

	.align-end {
		align-items: flex-end;
	}

	.margin-left-sm {
		margin-left: 6px;
	}

	.margin-right-xs {
		margin-right: 4px;
	}

	.myfont-14px {
		font-size: 14px;
	}
</style>
