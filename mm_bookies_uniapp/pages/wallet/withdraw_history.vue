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

		<scroll-view scroll-y class="history-scroll" @scroll="onScrollEmit" @scrolltolower="loadMore" :refresher-enabled="true" @refresherrefresh="onRefresh" :refresher-triggered="refresherTriggered">

			<!-- 空状态 -->
			<view v-if="!loading && recordList.length === 0" class="empty-state">
				<image src="/static/image/order/empty.svg" mode="aspectFit" class="empty-icon"></image>
				<text class="empty-text">{{ $t('no_withdraw_records') || 'No withdrawal records available at the moment. Please check back later.' }}</text>
			</view>

			<!-- 记录项（参考 wallet/wallet 卡片样式） -->
			<view v-for="(item, index) in recordList" :key="index" class="record-card">
				<!-- 顶部：Order ID + 时间 -->
				<view class="card-top">
					<text class="order-id">Order ID：{{item.id}}</text>
					<text class="order-time">{{formatTime(item.create_time)}}</text>
				</view>

				<!-- 类型行：类型 | 支付方式 logo + 名称 -->
				<view class="card-type-row">
					<view class="type-left">
						<theme-icon :name="item.type === 'Deposit' ? 'deposit' : 'withdraw'" class="type-svg"
							:color="item.type === 'Deposit' ? 'var(--theme-icon-secondary, var(--theme-secondary))' : 'var(--theme-icon-primary, var(--theme-primary))'"></theme-icon>
						<text class="type-name">{{item.type || 'Withdraw'}}</text>
					</view>
					<view class="pay-right">
						<text class="pay-name">{{item.bank_code || 'KBZ Pay'}}</text>
						<image :src="`/static/icon/register/${item.bank_code || 'KBZ Pay'}.png`" mode="aspectFit"
							class="pay-logo"></image>
					</view>
				</view>

				<!-- 金额行 -->
				<view class="card-amount-row">
					<text class="amount-label">Transaction Amount：</text>
					<text class="amount-value"
						:class="item.type === 'Deposit' ? 'amount-deposit-color' : 'amount-withdraw-color'">{{item.type === 'Deposit' ? '+' : '-'}}{{numberFormat(item.amount)}}
						MMK</text>
				</view>

				<!-- 状态 -->
				<view class="card-status">
					<text class="status-text"
						:class="getStatusClass(item.status)">{{getStatusText(item.status)}}</text>
				</view>
			</view>

			<!-- 加载更多 -->
			<view v-if="loading" class="loading-more">
				<text class="cuIcon-loading2 load-icon rotating"></text>
				<text class="loading-text">{{ $t('loading_dots') }}</text>
			</view>
			<view class="blank"></view>
			<!-- 没有更多 不需要提示-->
			<!-- <view v-if="!loading && hasMore === false && filterRecordList(recordList).length > 0" class="no-more">
				<text>{{ $t('no_more_data') }}</text>
			</view> -->
		</scroll-view>
	</view>
</template>

<script>
	import config from '../../utils/config.js'
	import dateFormatUtils from "../../utils/utils.js"

	export default {
		name: 'WalletWithdrawHistory',
		data() {
			return {
				language: config.language,
				recordList: [],
				loading: false,
				refreshing: false,
				refresherTriggered: false,
				hasMore: true,
				page: 1,
				pageSize: 10,

				filterExpanded: false,
				filterOptions: [
					{ label: 'filter_all', value: 'all', checked: true },
					{ label: 'filter_pending', value: 'Pending', type: 'status', checked: false },
					{ label: 'filter_success', value: 'Success', type: 'status', checked: false },
					{ label: 'filter_rejected', value: 'Rejected', type: 'status', checked: false },
				],
			}
		},
		methods: {
			// from tangjq--- 滚动事件冒泡给父页面，用于驱动 header 收起/展开
			onScrollEmit(e) {
				this.$emit('contentScroll', e)
			},
			refreshData() {
				if (this.refreshing) return;
				this.refreshing = true;
				this.page = 1;
				this.hasMore = true;
				this.recordList = [];
				this.loadRecords();
			},

			onRefresh() {
				setTimeout(() => {
					this.refresherTriggered = true;
					this.page = 1;
					this.hasMore = true;
					this.recordList = [];
					this.loadRecords().finally(() => {
						this.refresherTriggered = false;
					});
				}, 500)
			},

			loadMore() {
				if (!this.hasMore || this.loading) return;
				this.page++;
				this.loadRecords();
			},

async loadRecords() {
			if (this.loading) return;

			this.loading = true;

			try {
				const filterParams = this.getFilterParams();
				const para = {
					page: this.page,
					limit: this.pageSize,
					// from tangjq--- 去掉 type=Withdraw 限制，显示所有交易类型（Deposit/Withdraw 都会显示）
					...filterParams
				};

					await new Promise((resolve, reject) => {
						this.$http.get('/withdraw/get', { data: para }, (res) => {
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
					console.error('Load withdraw records failed:', error);
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
				const timeMatch = String(convertedTime).match(
					/^(\d{4})-(\d{2})-(\d{2})\s+(\d{2}):(\d{2})/
				);
				if (timeMatch) {
					return `${timeMatch[3]}/${timeMatch[2]}/${timeMatch[1]} ${timeMatch[4]}:${timeMatch[5]}`;
				}
				const date = typeof convertedTime === 'string' ? new Date(convertedTime) : convertedTime;
				if (!(date instanceof Date) || isNaN(date.getTime())) return '';
				const pad = value => String(value).padStart(2, '0');
				return `${pad(date.getDate())}/${pad(date.getMonth() + 1)}/${date.getFullYear()} ${pad(date.getHours())}:${pad(date.getMinutes())}`;
			},

			numberFormat(number) {
				return dateFormatUtils.numFormat(number);
			},

			getStatusText(status) {
				const s = String(status);
				const statusMap = {
					'Pending': this.$t('processing') || 'Pending',
					'Success': this.$t('success') || 'Success',
					'Rejected': this.$t('Rejected') || 'Rejected',
					'Time Out': 'Time Out',
				};
				return statusMap[s] || status;
			},

			getStatusClass(status) {
				const s = String(status);
				const classMap = {
					'Pending': 'status-pending',
					'Success': 'status-success',
					'Rejected': 'status-failed',
					'Time Out': 'status-timeout',
				};
				return classMap[s] || 'status-default';
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
				this.loadRecords();
			},

			getFilterText() {
				const allOption = this.filterOptions.find(opt => opt.value === 'all');
				if (allOption && allOption.checked) {
					return 'All Withdraw';
				}

				const checkedOptions = this.filterOptions.filter(opt => opt.value !== 'all' && opt.checked);
				if (checkedOptions.length === 0) {
					return 'All Withdraw';
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

				const statusOption = checkedOptions.find(opt => opt.type === 'status');
				if (statusOption) {
					params.status = statusOption.value;
				}

				return params;
			},
		},

		mounted() {
			this.loadRecords();
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

	/* 记录项（参考 wallet/wallet 卡片样式） */
	.record-card {
		margin: 10px 0;
		background-color: $bg-color-info;
		border-radius: 14px;
		overflow: hidden;
	}

	.card-top {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 14px 16px 8px;
	}

	.order-id {
		font-size: 12px;
		font-weight: 700;
		color: $color-primary;
		max-width: 60%;
	}

	.order-time {
		font-size: 12px;
		color: $color-primary;
	}

	.card-type-row {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 6px 16px 10px;
	}

	.type-left {
		display: flex;
		align-items: center;
		gap: 8px;
	}

	.type-svg {
		width: 20px;
		height: 20px;
		flex-shrink: 0;
	}

	.type-name {
		font-size: 15px;
		font-weight: 600;
		color: $color-primary;
	}

	.pay-right {
		display: flex;
		align-items: center;
		gap: 6px;
	}

	.pay-logo {
		width: 28px;
		height: 28px;
		border-radius: 6px;
	}

	.pay-name {
		font-size: 14px;
		font-weight: 600;
		color: $color-primary;
	}

	.card-amount-row {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 4px 16px 12px;
	}

	.amount-label {
		font-size: 14px;
		color: $color-primary;
	}

	.amount-value {
		font-size: 17px;
		font-weight: 700;
		font-style: italic;
	}

	.amount-deposit-color {
		color: $color-secondary-light;
	}

	.amount-withdraw-color {
		color: #E74C3C;
	}

	.card-status {
		display: flex;
		justify-content: center;
		align-items: center;
		padding: 0 16px 14px;
	}

	.status-text {
		font-size: 14px;
		font-weight: 600;
	}

	.status-success {
		color: $color-secondary-light;
	}

	.status-pending {
		color: #888;
	}

	.status-timeout {
		color: #E74C3C;
	}

	.status-failed {
		color: #E74C3C;
	}

	.status-default {
		color: #888;
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
</style>
