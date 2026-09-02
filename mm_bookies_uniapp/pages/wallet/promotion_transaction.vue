<template>
	<view class="promotion-page">
		<zw-header @headerHeightChange="onHeaderHeightChange"></zw-header>

		<!-- from tangjq--- header占位元素，防止内容被遮挡 -->
		<view class="header-placeholder" :style="{ height: headerHeight + 'px' }"></view>

		<!-- from tangjq--- 页面内容 -->
		<view class="promotion-content">
			<!-- 筛选器 -->
			<view class="filter-bar" @click="toggleFilterDropdown">
				<text class="filter-text">{{getFilterText()}}</text>
				<text class="filter-icon" :class="filterExpanded ? 'cuIcon-fold' : 'cuIcon-unfold'"></text>
			</view>

			<!-- 下拉选项 -->
			<view v-if="filterExpanded" class="filter-dropdown">
				<view v-for="(option, index) in filterOptions" :key="index" class="filter-option"
					@click="toggleFilterOption(option)">
					<text class="option-text">{{ $t(option.label) }}</text>
					<view class="option-radio" :class="{'active': option.checked}">
						<view class="option-radio-inner" v-if="option.checked"></view>
					</view>
				</view>
			</view>

			<scroll-view scroll-y class="history-scroll" @scroll="onScroll" @scrolltoupper="handleHeaderTop" @scrolltolower="loadMore"
				:refresher-enabled="true" @refresherrefresh="onRefresh" @refresherrestore="onRefresherRestore"
				@refresherabort="onRefresherAbort" :refresher-triggered="refresherTriggered">

				<!-- 空状态 -->
				<view v-if="!loading && recordList.length === 0" class="empty-state">
					<image src="/static/image/order/empty.svg" mode="aspectFit" class="empty-icon"></image>
					<text
						class="empty-text">{{ $t('no_records') || 'No transaction records available at the moment.' }}</text>
				</view>

				<!-- 记录项（参考 Wallet_Page.png 卡片样式） -->
				<view v-for="(item, index) in recordList" :key="index" class="record-card">
					<!-- 顶部：Order ID + 时间 -->
					<view class="card-top">
						<text class="order-id">{{$t('order_id')}}：{{item.id}}</text>
						<text class="order-time">{{formatTime(item.create_time)}}</text>
					</view>

					<!-- 类型行：● + 类型 | 支付方式logo+名称 -->
					<view class="card-type-row">
						<view class="type-left">
							<text class="type-name">{{item.display_type || item.type}}</text>
						</view>
						<view class="pay-right">
							<image :src="`/static/icon/register/${item.bank_code || 'KBZ Pay'}.png`" mode="aspectFit"
								class="pay-logo"></image>
							<text class="pay-name">{{item.bank_code || 'KBZ Pay'}}</text>
						</view>
					</view>

					<!-- 金额行 -->
					<view class="card-amount-row">
						<text class="amount-label">{{$t('transaction_amount')}}：</text>
						<text class="amount-value">{{numberFormat(item.money || item.amount)}}
							{{item.currency || 'MMK'}}</text>
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
					<text class="loading-text">{{ $t('loading_dots') || 'Loading...' }}</text>
				</view>
				<view class="blank"></view>
			</scroll-view>
		</view>
	</view>
</template>

<script>
	import config from '../../utils/config.js'
	import dateFormatUtils from "../../utils/utils.js"
	import headerCollapse from '@/mixins/headerCollapse.js'

	export default {
		name: 'PromotionTransaction',
		mixins: [headerCollapse],
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
				// from tangjq--- 钱包筛选：默认 promotion
				filterOptions: [{
						label: 'filter_all',
						value: '',
						checked: false
					},
					{
						label: 'main_wallet',
						value: 'Money',
						checked: false
					},
					{
						label: 'pro_wallet',
						value: 'Promotion',
						checked: true
					},
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
				this.loadRecords();
			},

			onRefresh() {
				if (this.refresherTriggered || this.loading) return
				this.refresherTriggered = true
				this.page = 1
				this.hasMore = true
				this.recordList = []
				this.loadRecords().finally(() => {
					this.refresherTriggered = false
				})
			},

			onRefresherRestore() {
				this.refresherTriggered = false
			},

			onRefresherAbort() {
				this.refresherTriggered = false
			},

			onScroll(e) {
				if (this.refresherTriggered) return
				this.handleHeaderScroll(e)
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
					const selectedWallet = this.filterOptions.find(opt => opt.checked);
					const para = {
						page: this.page,
						limit: this.pageSize,
					};
					// from tangjq--- 仅当未选 all 时传 pay_wallet
					if (selectedWallet && selectedWallet.value) {
						para.pay_wallet = selectedWallet.value;
					}

					await new Promise((resolve, reject) => {
						this.$http.get('/balance_log', {
							data: para
						}, (res) => {
							if (res.statusCode === 200) {
								const items = (res.data.items || []).map(ele => this.parseLog(ele));

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
					console.error('Load balance log failed:', error);
					uni.showToast({
						title: error.message || 'Load failed',
						icon: 'none'
					});
				} finally {
					this.loading = false;
					this.refreshing = false;
				}
			},

			parseLog(ele) {
				// from tangjq--- 格式化时间和显示文字（参考 onex2 balance_log）
				if (ele.create_time) {
					ele.submit_time = this.formatTime(ele.create_time)
					ele.confirm_time = ele.update_time ? this.formatTime(ele.update_time) : null
				}
				ele = this.setTransactionTypeDisplay(ele)
				ele.payment_channel = ele.bank_code || null
				return ele
			},

			setTransactionTypeDisplay(ele) {
				const type = ele.type
				const type_sub = ele.type_sub

				if (type === 'Deposit') {
					if (type_sub === 'Auto') ele.display_type = 'Deposit - Auto'
					else if (type_sub === 'Manual') ele.display_type = 'Deposit - Manual Approval'
					else if (type_sub === 'Adjusted') ele.display_type = 'Deposit - Adjusted'
					else ele.display_type = 'Deposit'
				} else if (type === 'Withdraw') {
					if (type_sub === 'Auto') ele.display_type = 'Withdraw - Auto Instant'
					else if (type_sub === 'Manual') ele.display_type = 'Withdraw - Manual Payout'
					else if (type_sub === 'Adjusted') ele.display_type = 'Withdraw - Adjusted'
					else ele.display_type = 'Withdraw'
				} else if (type === 'Transfer') {
					ele.display_type = ele.money > 0 ? 'Transfer In' : 'Transfer Out'
					ele.display_subtype = ele.money > 0 ? 'From Promo Wallet' : 'To Main Wallet'
				} else if (type === 'Order') {
					ele.display_type = 'Betting'
					ele.display_subtype = type_sub === 'Football' ? 'Football Bet' : type_sub === 'Egame' ?
						'eGame Session' : ''
				} else if (type === 'Settlement') {
					ele.display_type = 'Settlement'
					ele.display_subtype = type_sub === 'Football' ? 'Football Win' : type_sub === 'Egame' ? 'eGame Win' :
						''
				} else if (type === 'Refund') {
					ele.display_type = 'Refund'
					ele.display_subtype = type_sub === 'Football' ? 'Football Refund' : type_sub === 'Egame' ?
						'eGame Refund' : ''
				} else if (type === 'Promotion') {
					if (type_sub === 'Claim') ele.display_type = 'Promo Credited'
					else if (type_sub === 'Release') ele.display_type = 'Promo Released'
					else if (type_sub === 'Expiry') ele.display_type = 'Promo Expired'
					else ele.display_type = 'Promotion'
				} else if (type === 'Adjustment') {
					if (type_sub === 'Credit') ele.display_type = 'Admin Credit'
					else if (type_sub === 'Debit') ele.display_type = 'Admin Debit'
					else if (type_sub === 'Reversal') ele.display_type = 'Reversal / Refund'
					else ele.display_type = 'Adjustment'
				} else if (type === 'Activity') {
					ele.display_type = ele.type_sub
				} else {
					ele.display_type = type
				}
				return ele
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
					'Success': this.$t('success'),
					'Pending': this.$t('pending'),
					'Time Out': this.$t('timeout'),
					'Rejected': this.$t('rejected'),
					'Failed': this.$t('failed'),
				};
				return statusMap[s] || status;
			},

			getStatusClass(status) {
				const s = String(status);
				const classMap = {
					'Success': 'status-success',
					'Pending': 'status-pending',
					'Time Out': 'status-timeout',
					'Rejected': 'status-failed',
					'Failed': 'status-failed',
				};
				return classMap[s] || 'status-default';
			},

			toggleFilterDropdown() {
				this.filterExpanded = !this.filterExpanded;
			},

			toggleFilterOption(option) {
				// 单选逻辑
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
				const checkedOption = this.filterOptions.find(opt => opt.checked);
				if (!checkedOption || !checkedOption.value) {
					return this.$t('all_transaction');
				}
				return this.$t(checkedOption.label);
			},
		},

		mounted() {
			this.loadRecords();
		}
	}
</script>

<style lang="scss" scoped>
	/* from tangjq--- 页面级样式 */
	.promotion-page {
		height: var(--app-viewport-height, 100vh);
		min-height: 0;
		display: flex;
		flex-direction: column;
		overflow: hidden;
	}

	.header-placeholder {
		height: 255px;
		width: 100%;
		flex-shrink: 0;
		transition: height 0.3s ease;
	}

	.promotion-content {
		flex: 1;
		height: 0;
		min-height: 0;
		background: #fff;
		border-radius: 20px 20px 0 0;
		display: flex;
		flex-direction: column;
		padding: 10px;
		overflow: hidden;
	}

	/* 筛选器 */
	.filter-bar {
		background: var(--theme-league-bg, $color-primary);
		border-radius: $radius-large;
		padding: 8px 14px;
		display: flex;
		align-items: center;
		justify-content: space-between;
		flex-shrink: 0;
		margin-bottom: 8px;
	}

	.filter-text {
		font-size: 13px;
		font-weight: 600;
		color: #ffffff;
	}

	.filter-icon {
		font-size: 13px;
		color: #ffffff;
		transition: transform 0.3s ease;
	}

	.filter-dropdown {
		background: $bg-color-info;
		border-radius: 12px;
		flex-shrink: 0;
		margin-bottom: 8px;
		overflow: hidden;
	}

	.filter-option {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 12px 16px;
		cursor: pointer;
	}

	.option-text {
		font-size: 13px;
		font-weight: bold;
		color: $color-primary;
	}

	.option-radio {
		width: 18px;
		height: 18px;
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
		width: 10px;
		height: 10px;
		background-color: $color-secondary;
		border-radius: 50%;
	}

	.history-scroll {
		flex: 1;
		height: 0;
		min-height: 0;
		background-color: #ffffff;
	}

	/* ====== 卡片样式（参考 Wallet_Page.png）====== */
	.record-card {
		margin: 10px 0;
		background-color: $bg-color-info;
		border: 1px solid $color-border;
		border-radius: $radius-medium;
		overflow: hidden;
	}

	/* 顶部：Order ID + 时间 */
	.card-top {
		display: flex;
		justify-content: space-between;
		align-items: start;
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
		color: #888;
	}

	/* 类型行：●类型 | 支付方式 */
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

	/* 金额行 */
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
		color: $color-secondary;
		font-style: italic;
	}

	/* 状态 */
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
		color: $color-secondary;
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
		width: 60px;
		height: 60px;
		opacity: 0.6;
	}

	.empty-text {
		font-size: 14px;
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

	.blank {
		height: 20px;
	}
</style>

<style lang="scss">
	page {
		height: var(--app-viewport-height, 100vh);
		overflow: hidden;
	}
</style>