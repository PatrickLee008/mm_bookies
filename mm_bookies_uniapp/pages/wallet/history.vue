<template>
	<view class="history-component">
		<!-- from tangjq--- Charge History 子组件，按照设计稿 wallet_history.png 布局 -->

		<!-- from tangjq--- 筛选器 -->
		<view class="filter-bar" @click="toggleFilterDropdown">
			<text class="filter-text">{{getFilterText()}}</text>
			<text class="filter-icon" :class="filterExpanded ? 'cuIcon-fold' : 'cuIcon-unfold'"></text>
		</view>

		<!-- from tangjq--- 下拉选项，按照设计稿 wallet_history_select.png -->
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
				<image src="/static/icon/history.png" mode="aspectFit" class="empty-icon"></image>
				<text class="empty-text">{{$t('no_charge_records') || 'No charge records'}}</text>
			</view>

			<!-- from tangjq--- 记录项，按照设计稿布局，应用筛选 -->
			<view v-for="(item, index) in filterRecordList(recordList)" :key="index" class="record-item">
				<!-- 第一行：Order ID 和 时间 -->
				<view class="record-row">
					<text class="order-id">Order ID : {{item.id}}</text>
					<text class="date-time">{{formatTime(item.create_time)}}</text>
				</view>

				<!-- 第二行：Payment Channel -->
				<view class="record-row">
					<text class="label">Payment Channel :</text>
					<text class="value-right">{{formatPayChannel(item.pay_channel)}}</text>
				</view>

				<!-- 第三行：Transaction Amount -->
				<view class="record-row">
					<text class="label">Transaction Amount :</text>
					<text class="amount-value">{{numberFormat(item.money)}} MMK</text>
				</view>

				<!-- from tangjq--- 状态按钮 -->
				<view class="status-btn" :class="getStatusBtnClass(item.status)" @click="handleStatusClick(item)">
					<text class="status-btn-text">{{getStatusText(item.status)}}</text>
				</view>
			</view>

			<!-- 加载更多 -->
			<view v-if="loading" class="loading-more">
				<text class="cuIcon-loading2 load-icon rotating"></text>
				<text class="loading-text">{{$t('loading') || 'Loading...'}}</text>
			</view>

			<!-- 没有更多 -->
			<view v-if="!loading && hasMore === false && filterRecordList(recordList).length > 0" class="no-more">
				<text>{{$t('no_more_data') || 'No more data'}}</text>
			</view>
		</scroll-view>
	</view>
</template>

<script>
	// from tangjq--- Charge History 子组件,从 charge_history.vue 改造
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

				// from tangjq--- 筛选器相关
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
				return item.status === 'Pending';
			},

			// 继续支付
			continuePayment(item) {
				if (this.$toolbox && this.$toolbox.click_too_fast && this.$toolbox.click_too_fast(1)) return;

				if (item.pay_channel === 'TCPay') {
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

			// from tangjq--- 获取状态按钮样式类
			getStatusBtnClass(status) {
				const classMap = {
					'Pending': 'status-btn-pending',
					'Success': 'status-btn-success',
					'Rejected': 'status-btn-failed',
					'New': 'status-btn-pending',
					'Failed': 'status-btn-failed',
					'Timeout': 'status-btn-timeout'
				};
				return classMap[status] || 'status-btn-default';
			},

			// from tangjq--- 处理状态按钮点击
			handleStatusClick(item) {
				// from tangjq--- Pending状态可以继续支付
				if (item.status === 'Pending' && this.canContinuePayment(item)) {
					this.continuePayment(item);
				}
			},

			// from tangjq--- 切换筛选器下拉框
			toggleFilterDropdown() {
				this.filterExpanded = !this.filterExpanded;
			},

			// from tangjq--- 切换筛选选项
			toggleFilterOption(option) {
				if (option.value === 'all') {
					// from tangjq--- 点击 All，全选或取消全选
					const newCheckedState = !option.checked;
					this.filterOptions.forEach(opt => {
						opt.checked = newCheckedState;
					});
				} else {
					// from tangjq--- 切换单个选项
					option.checked = !option.checked;

					// from tangjq--- 检查是否所有非All选项都被选中
					const otherOptions = this.filterOptions.filter(opt => opt.value !== 'all');
					const allOthersChecked = otherOptions.every(opt => opt.checked);
					const allOthersUnchecked = otherOptions.every(opt => !opt.checked);

					// from tangjq--- 更新All选项状态
					const allOption = this.filterOptions.find(opt => opt.value === 'all');
					if (allOthersChecked || allOthersUnchecked) {
						allOption.checked = allOthersChecked;
					}
				}

				// from tangjq--- 重新加载数据
				this.page = 1;
				this.hasMore = true;
				this.recordList = [];
				this.loadChargeRecords();
			},

			// from tangjq--- 获取筛选器显示文本
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

			// from tangjq--- 获取筛选参数
			getFilterParams() {
				const allOption = this.filterOptions.find(opt => opt.value === 'all');
				if (allOption && allOption.checked) {
					return {}; // from tangjq--- 全选时不添加筛选参数
				}

				const params = {};
				const checkedOptions = this.filterOptions.filter(opt => opt.value !== 'all' && opt.checked);

				if (checkedOptions.length === 0) {
					return {}; // from tangjq--- 没有选中任何选项时，显示全部
				}

				// from tangjq--- 分别处理渠道和状态筛选
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

			// from tangjq--- 筛选记录列表（客户端筛选）
			filterRecordList(records) {
				const filterParams = this.getFilterParams();

				// from tangjq--- 如果没有筛选条件，返回全部
				if (Object.keys(filterParams).length === 0) {
					return records;
				}

				return records.filter(record => {
					let matchChannel = true;
					let matchStatus = true;

					// from tangjq--- 筛选支付渠道
					if (filterParams.pay_channels && filterParams.pay_channels.length > 0) {
						matchChannel = filterParams.pay_channels.includes(record.pay_channel);
					}

					// from tangjq--- 筛选状态
					if (filterParams.statuses && filterParams.statuses.length > 0) {
						matchStatus = filterParams.statuses.includes(record.status);
					}

					return matchChannel && matchStatus;
				});
			},
		},

		mounted() {
			// from tangjq--- 组件挂载时加载数据
			this.loadChargeRecords();
		}
	}
</script>

<style lang="scss" scoped>
	/* from tangjq--- 按照设计稿 wallet_history.png 的样式 */
	.history-component {
		width: 100%;
		height: 100%;
		display: flex;
		flex-direction: column;
	}

	/* from tangjq--- 筛选器样式 */
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

	/* from tangjq--- 下拉选项样式，按照设计稿 wallet_history_select.png */
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

	/* from tangjq--- 圆形单选框样式，参照 game.vue */
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

	/* from tangjq--- 记录项样式，按照设计稿 */
	.record-item {
		margin-top: 10px;
		padding: 15px;
		background-color: #E8F4F5;
		border-radius: 12px;
	}

	/* from tangjq--- 每一行的布局 */
	.record-row {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 10px;
	}

	.record-row:last-of-type {
		margin-bottom: 15px;
	}

	/* from tangjq--- Order ID 样式 */
	.order-id {
		font-size: 14px;
		font-weight: 600;
		color: #2F5D62;
	}

	/* from tangjq--- 日期时间样式 */
	.date-time {
		font-size: 12px;
		color: #2F5D62;
		text-align: right;
	}

	/* from tangjq--- 左侧标签样式 */
	.label {
		font-size: 14px;
		font-weight: 400;
		color: #5A7A8F;
	}

	/* from tangjq--- 右侧值样式 */
	.value-right {
		font-size: 14px;
		font-weight: 600;
		color: #2F5D62;
		text-align: right;
	}

	/* from tangjq--- 金额样式 */
	.amount-value {
		font-size: 16px;
		font-weight: 700;
		color: #4fb3bf;
		text-align: right;
	}

	/* from tangjq--- 状态按钮基础样式 */
	.status-btn {
		width: 100%;
		padding: 3px;
		border-radius: 16px;
		text-align: center;
		cursor: pointer;
	}

	.status-btn-text {
		font-size: 14px;
		font-weight: 600;
		color: #ffffff;
	}

	/* from tangjq--- Success 状态 */
	.status-btn-success {
		background-color: #4fb3bf;
	}

	/* from tangjq--- Pending 状态 */
	.status-btn-pending {
		background-color: #6B8E9A;
	}

	/* from tangjq--- Failed/Rejected 状态 */
	.status-btn-failed {
		background-color: #E74C3C;
	}

	/* from tangjq--- Timeout 状态 */
	.status-btn-timeout {
		background-color: #E74C3C;
	}

	/* from tangjq--- 默认状态 */
	.status-btn-default {
		background-color: #95A5A6;
	}

	/* from tangjq--- 空状态 */
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

	/* from tangjq--- 加载更多 */
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

	/* from tangjq--- 没有更多 */
	.no-more {
		text-align: center;
		padding: 20px;
		color: #999999;
		font-size: 14px;
	}
</style>