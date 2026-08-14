<template name="wallet">
	<view class="full-page">
		<zw-header @headerHeightChange="onHeaderHeightChange"></zw-header>

		<!-- from tangjq--- header占位元素，防止内容被遮挡 -->
		<view class="header-placeholder" :style="{ height: headerHeight + 'px' }"></view>

		<!-- from tangjq--- 入口按钮栏：Deposit / Withdraw / Promotion Transaction（图标使用首页index的同款图标） -->
		<view class="entry-bar">
			<view class="entry-item" @click="goto('/pages/wallet/deposit_page')">
				<theme-icon name="deposit" class="entry-icon entry-icon-svg"
					color="var(--theme-icon-secondary, var(--theme-secondary))"></theme-icon>
				<view class="flex-column align-center" style="min-height: 34px;">
					<text class="entry-text">{{ $t('deposit') }}</text>
				</view>
			</view>
			<view class="entry-item" @click="goto('/pages/wallet/withdraw_page')">
				<theme-icon name="withdraw" class="entry-icon entry-icon-svg"
					color="var(--theme-icon-primary, var(--theme-primary))"></theme-icon>
				<view class="flex-column align-center" style="min-height: 34px;">
					<text class="entry-text">{{ $t('withdraw') }}</text>
				</view>
			</view>
			<view class="entry-item" @click="goto('/pages/wallet/promotion_transaction')">
				<image class="entry-icon entry-icon-coin" mode="aspectFit" src="/static/icon/nav/coin.png" />
				<view class="flex-column align-center" style="min-height: 34px;">
					<text class="entry-text">{{ $t('promotion_transaction') || 'Promotion Transaction' }}</text>
				</view>
			</view>
		</view>

		<!-- from tangjq--- 默认列表：调用 /withdraw/get 不带 type，显示所有充值+提现信息 -->
		<view class="transaction-list-wrap">
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

			<scroll-view scroll-y class="history-scroll" @scroll="handleHeaderScroll" @scrolltoupper="handleHeaderTop" @scrolltolower="loadMore"
				:refresher-enabled="true" @refresherrefresh="onRefresh" :refresher-triggered="refresherTriggered">

				<!-- 空状态 -->
				<view v-if="!loading && recordList.length === 0" class="empty-state">
					<image src="/static/image/order/empty.svg" mode="aspectFit" class="empty-icon"></image>
					<text
						class="empty-text">{{ $t('no_withdraw_records') || 'No transaction records available at the moment.' }}</text>
				</view>

				<!-- 记录项（参考 Wallet_Page.png 卡片样式） -->
				<view v-for="(item, index) in recordList" :key="index" class="record-card">
					<!-- 顶部：Order ID + 时间 -->
					<view class="card-top">
						<text class="order-id">Order ID：{{item.id}}</text>
						<text class="order-time">{{formatTime(item.create_time)}}</text>
					</view>

					<!-- 类型行：● + 类型 | 支付方式logo+名称 -->
					<view class="card-type-row">
						<view class="type-left">
							<theme-icon :name="item.type === 'Deposit' ? 'deposit' : 'withdraw'" class="type-svg"
								:color="item.type === 'Deposit' ? 'var(--theme-icon-secondary, var(--theme-secondary))' : 'var(--theme-icon-primary, var(--theme-primary))'"></theme-icon>
							<text class="type-name">{{item.type || 'Deposit'}}</text>
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
			</scroll-view>
		</view>

		<!-- from tangjq--- 悬浮的 Refresh 按钮，点击刷新列表数据 -->
		<view class="refresh-btn-float" @click="refreshList">
			<text class="cuIcon-refresh text-white text-bold myfont-20px"></text>
		</view>
	</view>
</template>

<script>
	// from tangjq--- wallet 默认页面：入口按钮 + 统一交易列表
	import config from '../../utils/config.js'
	import dateFormatUtils from "../../utils/utils.js"
	import headerCollapse from '@/mixins/headerCollapse.js'

	export default {
		mixins: [headerCollapse],
		data() {
			return {
				isLogin: uni.getStorageSync('Authorization') || false,
				language: config.language,
				userInfo: null,

				// from tangjq--- 默认列表数据（调用 /withdraw/get 不带 type）
				recordList: [],
				loading: false,
				refreshing: false,
				refresherTriggered: false,
				hasMore: true,
				page: 1,
				pageSize: 10,

				filterExpanded: false,
				filterOptions: [{
						label: 'filter_all',
						value: 'all',
						checked: true
					},
					{
						label: 'filter_pending',
						value: 'Pending',
						type: 'status',
						checked: false
					},
					{
						label: 'filter_success',
						value: 'Success',
						type: 'status',
						checked: false
					},
					{
						label: 'filter_rejected',
						value: 'Rejected',
						type: 'status',
						checked: false
					},
				],
			}
		},
		methods: {
			goto(url) {
				uni.navigateTo({
					url: url
				})
			},
			numberFormat(number) {
				return dateFormatUtils.numFormat(number)
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

			refreshList() {
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
						// from tangjq--- 不传 type，显示所有充值+提现
						...filterParams
					};

					await new Promise((resolve, reject) => {
						this.$http.get('/withdraw/get', {
							data: para
						}, (res) => {
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
					console.error('Load records failed:', error);
					uni.showToast({
						title: error.message || 'Load failed',
						icon: 'none'
					});
				} finally {
					this.loading = false;
					this.refreshing = false;
				}
			},

			toggleFilterDropdown() {
				this.filterExpanded = !this.filterExpanded;
			},

			toggleFilterOption(option) {
				this.filterOptions.forEach(opt => {
					opt.checked = opt.value === option.value;
				});
				this.filterExpanded = false;
				this.page = 1;
				this.hasMore = true;
				this.recordList = [];
				this.loadRecords();
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
				return this.$t(checkedOptions[0].label);
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

		onLoad(options) {
			this.userInfo = Object.assign({}, this.$store.state.userInfo)
			// from tangjq--- 默认页面加载列表数据
			this.loadRecords()
		},

		created() {}
	}
</script>

<style lang="scss">
	/* from tangjq--- header占位元素样式 */
	.header-placeholder {
		height: 255px;
		width: 100%;
		flex-shrink: 0;
		transition: height 0.3s ease;
	}

	.full-page {
		min-height: 100vh;
		display: flex;
		flex-direction: column;
	}

	/* from tangjq--- 入口按钮栏（参考 Wallet_Page.png：3个圆角矩形按钮，圆形icon背景+文字） */
	.entry-bar {
		background: #fff;
		border-radius: 20px 20px 0 0;
		padding: 15px 12px 10px;
		display: flex;
		align-items: stretch;
		justify-content: space-between;
		gap: 10px;
		flex-shrink: 0;
	}

	.entry-item {
		flex: 1;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 8px;
		cursor: pointer;
		padding: 16px 6px 10px;
		border: 1.5px solid $color-primary;
		border-radius: $radius-medium;
		background: #FFFFFF;
		transition: background 0.2s ease;
		min-width: 0;
	}

	.entry-icon {
		width: 26px;
		height: 26px;
		flex-shrink: 0;
		/* 与首页 index 同款图标重着色（充值/提现 SVG -> 青色） */
		// filter: brightness(0) saturate(100%) invert(34%) sepia(20%) saturate(1120%) hue-rotate(145deg) brightness(85%) contrast(90%);
	}

	/* 余额金币为 PNG，保持原色，不应用重着色滤镜 */
	.entry-icon-coin {
		filter: none;
	}

	.entry-text {
		font-size: 13px;
		color: $color-primary;
		font-weight: 600;
		line-height: 17px;
		text-align: center;
	}

	/* from tangjq--- 交易列表容器 */
	.transaction-list-wrap {
		flex: 1;
		height: 0;
		background: #fff;
		display: flex;
		flex-direction: column;
		padding: 0 10px;
	}

	/* 筛选器 */
	.filter-bar {
		background: $color-primary;
		border-radius: $radius-large;
		padding: 10px 14px;
		display: flex;
		align-items: center;
		justify-content: space-between;
		flex-shrink: 0;
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
		padding: 8px 16px;
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

	.type-svg {
		width: 20px;
		height: 20px;
		flex-shrink: 0;
		/* 与首页 index / 入口栏同款青色重着色 */
		// filter: brightness(0) saturate(100%) invert(34%) sepia(20%) saturate(1120%) hue-rotate(145deg) brightness(85%) contrast(90%);
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
		font-style: italic;
	}

	.amount-deposit-color {
		color: $color-secondary;
	}

	.amount-withdraw-color {
		color: #E74C3C;
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

	/* from tangjq--- 悬浮 Refresh 按钮样式 */
	.refresh-btn-float {
		position: fixed;
		right: 20px;
		bottom: 80px;
		width: 50px;
		height: 50px;
		border-radius: 30px;
		background: $color-primary;
		// box-shadow: 0 4px 12px rgba(47, 93, 98, 0.4);
		border: 1px solid $color-border-other;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		z-index: 999;
	}
</style>