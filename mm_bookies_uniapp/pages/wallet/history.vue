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
				<text class="option-text">{{ $t(option.label) }}</text>
				<view class="option-radio" :class="{'active': option.checked}">
					<view class="option-radio-inner" v-if="option.checked"></view>
				</view>
			</view>
		</view>

		<scroll-view scroll-y class="history-scroll" @scroll="onScrollEmit" @scrolltoupper="onScrollTopEmit" @scrolltolower="loadMore" :refresher-enabled="true" @refresherrefresh="onRefresh" :refresher-triggered="refresherTriggered">

			<!-- 空状态 -->
			<view v-if="!loading && recordList.length === 0" class="empty-state">
				<image src="/static/image/order/empty.svg" mode="aspectFit" class="empty-icon"></image>
				<text class="empty-text">{{$t('no_charge_records') || 'No deposit records available at the moment. Please check back later.'}}</text>
			</view>

			<!-- 记录项 -->
			<view v-for="(item, index) in recordList" :key="index" class="record-item">
				<!-- 订单信息区 -->
				<view class="record-body">
					<!-- Order ID + 时间 -->
					<view class="record-row">
						<text class="order-id-label">Order ID : {{formatOrderId(item.id)}}</text>
						<text class="record-date">{{formatTime(item.create_time)}}</text>
					</view>
					<!-- 支付渠道 -->
					<view class="record-row">
						<text class="row-label">{{$t('pay_channel') || 'Payment Channel'}} :</text>
						<text class="row-value">{{formatPayChannel(item.pay_channel)}}</text>
					</view>
					<!-- 交易金额 -->
					<view class="record-row">
						<text class="row-label">{{$t('trans_amount') || 'Transaction Amount'}} :</text>
						<text class="row-value amount-value">{{numberFormat(item.money)}} MMK</text>
					</view>
					<!-- 失败原因（失败时显示） -->
					<view class="record-row" v-if="item.fail_reason && item.status=='Failed'">
						<text class="row-label">{{$t('fail_reason') || 'Fail Reason'}} :</text>
						<text class="row-value fail-reason">{{getFailReason(item.fail_reason)}}</text>
					</view>
				</view>

				<!-- 底部状态条 -->
				<view class="status-bar" :class="getStatusClass(item.status)">
					<text class="status-bar-text">{{getStatusText(item.status)}}</text>
				</view>

				<!-- 操作按钮（Pending 可继续支付） -->
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
					{ label: 'filter_all', value: 'all', checked: true },
					{ label: 'filter_pending', value: 'Pending', type: 'status', checked: false },
					{ label: 'filter_success', value: 'Success', type: 'status', checked: false },
					{ label: 'filter_timeout', value: 'Timeout', type: 'status', checked: false },
				],
			}
		},
		methods: {
			// from tangjq--- 滚动事件冒泡给父页面，用于驱动 header 收起/展开
			onScrollEmit(e) {
				this.$emit('contentScroll', e)
			},
			// from tangjq--- 原生滚动到顶部事件冒泡给父页面，保证到达顶部时 header 一定展开还原
			onScrollTopEmit() {
				this.$emit('contentScrollTop')
			},
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
					const filterParams = this.getFilterParams();
					const para = {
						page: this.page,
						limit: this.pageSize,
						...filterParams
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
				const convertedTime = dateFormatUtils.convertTimezone(time);
				const date = typeof convertedTime === 'string' ? new Date(convertedTime) : new Date(convertedTime);
				if (isNaN(date.getTime())) return '';
				const pad = (n) => (n < 10 ? '0' + n : '' + n);
				const dd = pad(date.getDate());
				const mm = pad(date.getMonth() + 1);
				const yyyy = date.getFullYear();
				const hh = pad(date.getHours());
				const min = pad(date.getMinutes());
				return `${dd}/${mm}/${yyyy} ${hh}:${min}`;
			},

			// Order ID 仅显示后 10 位
			formatOrderId(id) {
				if (id === null || id === undefined) return '';
				return String(id).slice(-10);
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
				// 单选逻辑：点击任意项时仅选中该项，其余（含 All）全部取消，
				// 避免 All 与具体筛选项同时选中导致 getFilterParams 短路、过滤失效
				this.filterOptions.forEach(opt => {
					opt.checked = opt.value === option.value;
				});

				// 关闭下拉框并重新加载列表
				this.filterExpanded = false;
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
					return this.$t(checkedOptions[0].label);
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
		background: $color-primary;
		border-radius: $radius-large;
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
		background: $bg-color-info;
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
		color: $color-primary;
	}

	.option-radio {
		width: 15px;
		height: 15px;
		border: 2px solid $color-secondary;
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
		transition: all 0.2s;
	}

	.option-radio.active {
		border-color: $color-secondary;
	}

	.option-radio-inner {
		width: 12px;
		height: 12px;
		background-color: $color-secondary;
		border-radius: 50%;
	}

	.history-scroll {
		flex: 1;
		height: 0;
		background-color: #ffffff;
	}

	/* 记录项 - 参照设计稿：浅薄荷色卡片 + 底部状态条 */
	.record-item {
		margin: 12px 0;
		background-color: $bg-color-info;
		border: 1px solid $color-border;
		border-radius: 12px;
		padding: 14px 16px;
		overflow: hidden;
	}

	/* 订单信息区 */
	.record-body {
		display: flex;
		flex-direction: column;
		gap: 10px;
		margin-bottom: 12px;
	}

	.record-row {
		display: flex;
		flex-direction: row;
		justify-content: space-between;
		align-items: center;
	}

	.order-id-label {
		font-size: 14px;
		font-weight: 700;
		color: $color-primary;
	}

	.record-date {
		font-size: 13px;
		font-weight: 600;
		color: $color-primary;
	}

	.row-label {
		font-size: 14px;
		font-weight: 500;
		color: $color-primary;
		flex-shrink: 0;
	}

	.row-value {
		font-size: 14px;
		font-weight: 700;
		color: $color-primary;
		text-align: right;
		margin-left: 10px;
		word-break: break-word;
	}

	/* 交易金额：斜体青色，突出显示 */
	.amount-value {
		color: $color-secondary;
		font-style: italic;
		font-weight: 700;
	}

	.fail-reason {
		color: #D0342C !important;
		font-weight: 700;
	}

	/* 底部状态条 - 整条圆角药丸样式 */
	.status-bar {
		border-radius: 20px;
		padding: 7px 12px;
		text-align: center;
		background-color: #8A9BA0;
	}

	.status-bar-text {
		font-size: 14px;
		font-weight: 700;
		color: #ffffff;
	}

	.status-bar.status-success {
		background-color: $color-secondary;
	}

	.status-bar.status-new {
		background-color: $color-secondary;
	}

	.status-bar.status-pending {
		background-color: #8A9BA0;
	}

	.status-bar.status-processing {
		background-color: #8A9BA0;
	}

	.status-bar.status-failed,
	.status-bar.status-timeout {
		background-color: #D0342C;
	}

	.status-bar.status-default {
		background-color: #8A9BA0;
	}

	.record-actions {
		margin-top: 12px;
	}

	.continue-btn {
		background-color: $color-primary;
		color: white;
		padding: 10px 20px;
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
		width: 60px;
		height: 60px;
		opacity: 0.6;
	}

	.empty-text {
		font-size: 16px;
		color: #999999;
		margin-top: 20px;
		text-align: center;
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
