<template>
	<view class="invite-page">
		<zw-header @headerHeightChange="onHeaderHeightChange"></zw-header>
		<view class="invite-header-placeholder" :style="{ height: headerHeight + 'px', transition: 'height 0.3s ease' }"></view>
		<scroll-view class="user-scroll invite-scroll" scroll-y @scroll="handleHeaderScroll" @scrolltoupper="handleHeaderTop">
			<view class="dashboard-content">
				<view class="dashboard-card revenue-card">
					<text class="card-label">{{ $t('Total Revenue from Invitees') }}</text>
					<text class="money-value">{{ formatAmount(bonusSummary.total_amount) }}<text
							class="money-unit"> Ks</text></text>
				</view>

				<view class="dashboard-card invitation-card">
					<text class="invitation-title">{{ $t('invitation') }}</text>
					<view class="invitation-stat-grid">
						<view class="invitation-stat">
							<text class="invitation-stat-label">{{ $t('total') }}</text>
							<text class="invitation-stat-value">{{ inviteStats.total_invited }}</text>
						</view>
						<view class="invitation-stat">
							<text class="invitation-stat-label">{{ $t('Pending') }}</text>
							<text class="invitation-stat-value">{{ inviteStats.pending_invitees }}</text>
						</view>
						<view class="invitation-stat">
							<text class="invitation-stat-label">{{ $t('Active Invitees') }}</text>
							<text class="invitation-stat-value">{{ inviteStats.active_invitees }}</text>
						</view>
					</view>
				</view>

				<view class="financial-list">
					<view class="dashboard-card financial-card">
						<text class="card-label">{{ $t('Total Deposit') }}</text>
						<text class="money-value">{{ formatAmount(inviteesRewardsData.total_deposit || 0) }}<text
								class="money-unit"> Ks</text></text>
					</view>
					<view class="dashboard-card financial-card">
						<text class="card-label">{{ $t('Total Turnover') }}</text>
						<text class="money-value">{{ formatAmount(inviteesRewardsData.total_turnover || 0) }}<text
								class="money-unit"> Ks</text></text>
					</view>
					<view class="dashboard-card financial-card">
						<text class="card-label">{{ $t('Total Net Win') }}</text>
						<text class="money-value">{{ formatAmount(inviteesRewardsData.total_net_win || 0) }}<text
								class="money-unit"> Ks</text></text>
					</view>
				</view>

				<view class="dashboard-filters">
					<view class="date-filter-container">
						<view class="user-filter-pill date-filter"
							:class="{ 'date-filter-selected': date_filtered }"
							@click="$refs.date_picker.show()">
							<theme-icon v-if="!date_filtered" name="calendar" class="user-filter-calendar"
								color="var(--theme-icon-on-primary, #fff)"></theme-icon>
							<text class="calendar-text">{{ dateDisplay }}</text>
							<text v-if="!date_filtered" class="cuIcon-unfold filter-arrow"></text>
						</view>
						<date-range-picker ref="date_picker" :inline="true"
							@click_option="date_click"></date-range-picker>
					</view>
					<view class="user-filter-pill status-filter">
						<selector :option_list.sync="status_list" :default_label="$t('status')"
							@click_option="onStatusSelect"></selector>
					</view>
					<view class="search-box">
						<text class="cuIcon-search search-icon"></text>
						<input type="text" v-model="searchKeyword" :placeholder="$t('search')"
							@input="onSearch" @confirm="onSearch" />
					</view>
				</view>

				<view class="user-list-container">
					<view class="user-card" v-for="(user, index) in filteredUserList" :key="index">
						<view class="user-card-header">
							<text class="user-name">{{ user.name || user.user_name }}</text>
							<view class="user-status-badges">
								<text v-if="user.user_label" class="user-label">{{ user.user_label }}</text>
								<text v-if="getUserStatus(user)" class="status-badge"
									:class="getStatusBadgeClass(getUserStatus(user))">{{ getUserStatus(user) }}</text>
							</view>
						</view>
						<view class="user-card-body">
							<view class="user-stats-row">
								<view class="stat-item">
									<text class="stat-label">{{ $t('Deposit') }}</text>
									<text class="stat-value">{{ formatAmount(user.stats ? user.stats.total_recharge : 0) }}<text
											class="stat-unit"> Ks</text></text>
								</view>
								<view class="stat-item">
									<text class="stat-label">{{ $t('Turnover') }}</text>
									<text class="stat-value">{{ formatAmount(user.stats ? user.stats.total_bet : 0) }}<text
											class="stat-unit"> Ks</text></text>
								</view>
								<view class="stat-item">
									<text class="stat-label">{{ $t('Net Win') }}</text>
									<text class="stat-value">{{ formatAmount(user.stats ? user.stats.net_win : 0) }}<text
											class="stat-unit"> Ks</text></text>
								</view>
							</view>
							<view class="user-footer-row">
								<text class="joined-text" v-if="user.last_login_time">{{ $t('Last Login') }}
									{{ formatDate(user.last_login_time) }}</text>
								<text class="joined-text">{{ $t('Joined') }} {{ formatDate(user.register_time) }}</text>
							</view>
						</view>
					</view>

					<view v-if="filteredUserList.length === 0" class="flex-column align-center" style="padding: 40px 0;">
						<text class="text-gray">{{ $t('No data available for the selected period') }}</text>
					</view>
				</view>
			</view>
			<view style="height: 30px; width: 100%;"></view>
		</scroll-view>
	</view>
</template>

<script>
	import Selector from '../../../components/common/selector.vue'
	import headerCollapse from '@/mixins/headerCollapse.js'

	export default {
		mixins: [headerCollapse],
		components: {
			Selector,
		},
		data() {
			return {
				language: this.$config.language,
				userInfo: null,
				searchKeyword: '',
				inviteStats: {
					active_invitees: 0,
					pending_invitees: 0,
					total_invited: 0,
				},
				inviteesRewardsData: {
					total_deposit: 0,
					total_turnover: 0,
					total_net_win: 0,
				},
				bonusSummary: {
					total_amount: 0,
					bonus_type_breakdown: {}
				},
				status_list: [],
				userList: [],
				filteredUserList: [],
				date_preset: '',
				date_filtered: false,
				date_range: [{
					show: "00/00/0000",
					value: "0000-00-00",
				}, {
					show: "00/00/0000",
					value: "0000-00-00",
				}],
				searchTimeout: null,
			}
		},
		computed: {
			dateDisplay() {
				if (this.date_preset) return this.date_preset;

				const start = this.date_range[0];
				const end = this.date_range[1];
				if (!start || !end || start.value === '0000-00-00' || end.value === '0000-00-00') {
					return this.$t('All');
				}
				return `${start.show} - ${end.show}`;
			},
		},
		onLoad() {
			this.userInfo = Object.assign({}, this.$store.state.userInfo)
			this.parse_option_list()
			this.loadInviteStats()
			this.loadBonusSummary()
			this.loadInviteesRewards()
		},
		mounted() {
			this.$nextTick(() => {
				if (this.$refs.date_picker && this.$refs.date_picker.date_arr) {
					this.$refs.date_picker.date_arr.forEach(e => e.checked = false)
				}
			})
		},
		methods: {
			back_to() {
				uni.navigateTo({ url: './index' })
			},
			onStatusSelect(selectedOption) {
				this.status_list.forEach((option) => {
					option.checked = (option.value === selectedOption.value);
				});
				this.loadInviteesRewards();
			},
			parse_option_list() {
				function parse_list(list) {
					return list.map((ele, index) => {
						return {
							label: ele.toLowerCase(),
							checked: index === 0,
							value: ele.toLowerCase().replace(/ /g, '_'),
						}
					})
				}
				let status = ['All', 'Signed up', 'Active', 'Inactive', 'Pending']
				this.status_list = parse_list(status)
			},
			formatAmount(amount) {
				if (!amount) return '0';
				// App 端 JS 引擎无 Intl，手动加千分号
				return String(Math.round(Number(amount))).replace(/\B(?=(\d{3})+(?!\d))/g, ',');
			},
			loadInviteStats() {
				var _this = this;
				_this.$http.get('/invitation_v2/invitee-stats', {}, (res) => {
					if (res.statusCode == 200 && res.data.code == 200) {
						_this.inviteStats = res.data.data;
					}
				})
			},
			loadInviteesRewards() {
				var _this = this;
				const params = {};
				const dateRange = _this.getDateRange();
				if (dateRange.start_date) params.start_date = dateRange.start_date;
				if (dateRange.end_date) params.end_date = dateRange.end_date;
				if (_this.searchKeyword && _this.searchKeyword.trim()) params.keyword = _this.searchKeyword.trim();
				const selectedStatus = _this.status_list.find(option => option.checked);
				if (selectedStatus && selectedStatus.value !== 'all') params.status = selectedStatus.value;

				_this.$http.get('/invitation_v2/invitees-summary', { data: params }, (res) => {
					if (res.statusCode == 200 && res.data.code == 200) {
						_this.inviteesRewardsData = res.data.data;
						_this.userList = res.data.data.invitee_details || [];
						_this.filterUserList();
					} else {
						_this.userList = [];
						_this.filterUserList();
					}
				})
			},
			loadBonusSummary() {
				const params = {};
				const dateRange = this.getDateRange();
				if (dateRange.start_date) params.start_date = dateRange.start_date;
				if (dateRange.end_date) params.end_date = dateRange.end_date;
				this.$http.get('/invitation_v2/rewards/bonus-type-summary', { data: params }, (res) => {
					if (res.statusCode == 200 && res.data.code == 200) {
						this.bonusSummary = (res.data.data && res.data.data.summary) ? res.data.data.summary : {
							total_amount: 0, bonus_type_breakdown: {}
						};
					} else {
						this.bonusSummary = { total_amount: 0, bonus_type_breakdown: {} };
					}
				})
			},
			getDateRange() {
				if (this.date_range[0].value !== '0000-00-00' && this.date_range[1].value !== '0000-00-00') {
					return { start_date: this.date_range[0].value, end_date: this.date_range[1].value };
				}
				return {};
			},
			onSearch() {
				if (this.searchTimeout) clearTimeout(this.searchTimeout);
				this.searchTimeout = setTimeout(() => { this.loadInviteesRewards(); }, 500);
			},
			filterUserList() {
				this.filteredUserList = this.userList;
			},
			date_click(range, presetLabel) {
				this.date_preset = presetLabel || '';
				this.date_range = range;
				this.date_filtered = true;
				if (this.date_range[0].value === '0000-00-00' || this.date_range[1].value === '0000-00-00') {
					this.date_preset = '';
					this.date_range = [{
						show: "00/00/0000",
						value: "0000-00-00"
					}, {
						show: "00/00/0000",
						value: "0000-00-00"
					}];
				}
				this.loadBonusSummary();
				this.loadInviteesRewards();
			},
			getUserStatus(user) {
				return user.user_status ? user.user_status : 'Pending';
			},
			getStatusBadgeClass(status) {
				switch (status) {
					case 'Active': return 'status-active';
					case 'Inactive': return 'status-inactive';
					case 'Pending': return 'status-pending';
					case 'Signed Up': return 'status-signed';
					default: return 'status-default';
				}
			},
			formatDate(dateString) {
				if (!dateString) return '';
				const date = new Date(String(dateString).replace(/-/g, '/'));
				if (isNaN(date.getTime())) return String(dateString);
				const day = String(date.getDate()).padStart(2, '0');
				const month = date.toLocaleString('en', { month: 'short' });
				const year = date.getFullYear();
				return `${day} ${month} ${year}`;
			},
		}
	}
</script>

<style lang="scss">
	.invite-page {
		height: var(--app-viewport-height, 100vh);
		display: flex;
		flex-direction: column;
		overflow: hidden;
	}

	.invite-header-placeholder {
		width: 100%;
		height: 255px;
		flex-shrink: 0;
		transition: height 0.3s ease;
	}

	.invite-scroll {
		flex: 1;
		height: 0;
		border-radius: 20px 20px 0 0;
		background: #ffffff;
		position: relative;
		z-index: 1;
	}

	.dashboard-content {
		padding: 15px 20px;
		box-sizing: border-box;
		color: $color-primary;
	}

	.dashboard-card {
		border: 1px solid #d3e1e3;
		border-radius: 12px;
		background: #ffffff;
		box-shadow: 0 2px 2px rgba(18, 63, 70, 0.18);
		box-sizing: border-box;
	}

	.revenue-card,
	.financial-card {
		display: flex;
		align-items: center;
		justify-content: space-between;
		min-height: 65px;
		padding: 0 19px;
	}

	.card-label {
		max-width: 70%;
		overflow: hidden;
		color: $color-primary;
		font-size: 13px;
		font-weight: 600;
		line-height: 20px;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.money-value {
		color: $color-primary;
		font-size: 16px;
		font-weight: 700;
		line-height: 20px;
		white-space: nowrap;
	}

	.money-unit,
	.stat-unit {
		font-size: 12px;
		font-weight: 600;
	}

	.invitation-card {
		margin-top: 19px;
		padding: 20px;
	}

	.invitation-title {
		display: block;
		color: $color-primary;
		font-size: 20px;
		font-weight: 700;
		line-height: 25px;
		text-align: center;
		text-transform: capitalize;
	}

	.invitation-stat-grid {
		display: flex;
		align-items: stretch;
		margin-top: 9px;
		padding: 13px 6px;
		border-radius: 12px;
		background: $bg-color-info;
		box-sizing: border-box;
	}

	.invitation-stat {
		display: flex;
		flex: 1;
		flex-direction: column;
		align-items: center;
		justify-content: space-between;
		min-width: 0;
	}

	.invitation-stat-label {
		overflow: hidden;
		color: $color-primary;
		font-size: 12px;
		line-height: 16px;
		text-align: center;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.invitation-stat-value {
		margin-top: 7px;
		color: $color-primary;
		font-size: 16px;
		font-weight: 700;
		line-height: 20px;
	}

	.financial-list {
		margin-top: 19px;
	}

	.financial-card + .financial-card {
		margin-top: 19px;
	}

	.dashboard-filters {
		display: flex;
		flex-wrap: nowrap;
		align-items: center;
		gap: 5px;
		margin-top: 18px;
	}

	.date-filter-container {
		position: relative;
		flex: 1 1 0;
		min-width: 0;
	}

	.user-filter-pill,
	.search-box {
		height: 56upx;
		border-radius: 999upx;
		box-sizing: border-box;
	}

	.user-filter-pill {
		display: flex;
		align-items: center;
		justify-content: center;
		flex: 1 1 0;
		background: $color-primary;
		color: #ffffff;
	}

	.date-filter {
		width: 100%;
		gap: 6px;
		padding: 0 8px;
		overflow: visible;
	}

	.user-filter-calendar {
		width: 17px;
		height: 17px;
		flex-shrink: 0;
	}

	.calendar-text {
		// flex: 1;
		min-width: 0;
		overflow: hidden;
		color: #ffffff;
		font-size: 11px;
		font-weight: bold;
		line-height: 16px;
		text-align: left;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.date-filter-selected .calendar-text {
		flex: 0 1 auto;
		text-align: center;
	}

	.filter-arrow {
		flex-shrink: 0;
		color: #ffffff;
		font-size: 10px;
		line-height: 16px;
	}

	.status-filter {
		flex: 0 0 74px;
		overflow: visible;
	}

	.status-filter ::v-deep .selector-wrapper {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 100%;
	}

	.status-filter ::v-deep .selector-tag {
		display: flex;
		align-items: center;
		justify-content: center;
		height: auto;
		padding: 0;
		border: none;
		border-radius: 0;
		background-color: transparent !important;
		color: #ffffff !important;
		font-size: 11px;
		font-weight: bold;
		line-height: 16px;
	}

	.status-filter ::v-deep .selector-tag text {
		color: #ffffff;
		font-size: 11px;
		font-weight: 600;
	}

	.status-filter ::v-deep .selector-tag .cuIcon-unfold,
	.status-filter ::v-deep .selector-tag .cuIcon-fold {
		margin-left: 3px;
		color: #ffffff;
		font-size: 10px;
	}

	.search-box {
		display: flex;
		flex: 1;
		align-items: center;
		min-width: 0;
		padding: 0 10px;
		border: 2px solid $color-primary;
		border-radius: 999upx;
		color: $color-primary;
	}

	.search-icon {
		flex: 0 0 auto;
		margin-right: 8px;
		font-size: 19px;
		line-height: 20px;
	}

	.search-box input {
		flex: 1;
		min-width: 0;
		height: 27px;
		padding: 0;
		border: 0;
		outline: 0;
		background: transparent;
		color: $color-primary;
		font-size: 12px;
		line-height: 27px;
	}

	.search-box input::placeholder {
		color: $color-primary;
		font-style: italic;
	}

	.user-list-container {
		margin-top: 20px;
	}

	.user-scroll {
		padding-right: 0;
	}

	.user-card {
		overflow: hidden;
		margin-bottom: 19px;
		border: 1px solid #d3e1e3;
		border-radius: 15px;
		background: #ffffff;
		box-shadow: 0 2px 2px rgba(18, 63, 70, 0.18);
	}

	.user-card-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		min-height: 40px;
		padding: 0 19px;
		background: $color-primary;
		box-sizing: border-box;
	}

	.user-name {
		overflow: hidden;
		color: #ffffff;
		font-size: 16px;
		font-weight: 700;
		line-height: 20px;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.user-status-badges {
		display: flex;
		align-items: center;
		gap: 8px;
		margin-left: 10px;
		white-space: nowrap;
	}

	.user-label {
		overflow: hidden;
		max-width: 90px;
		color: #ffffff;
		font-size: 11px;
		font-weight: 700;
		line-height: 20px;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.status-badge {
		padding: 3px 7px;
		border-radius: 8px;
		font-size: 11px;
		font-weight: 700;
		line-height: 18px;
	}

	.status-active {
		background: $color-primary;
		color: #ffffff;
	}

	.status-inactive {
		background: #ff4e4e;
		color: #ffffff;
	}

	.status-pending {
		background: #e7f0f2;
		color: $color-primary;
	}

	.status-signed {
		background: $color-secondary;
		color: #ffffff;
	}

	.status-default {
		background: #e7f0f2;
		color: $color-primary;
	}

	.user-card-body {
		padding: 14px 19px 12px;
		box-sizing: border-box;
	}

	.user-stats-row {
		display: flex;
		align-items: flex-start;
		justify-content: space-between;
		margin-bottom: 10px;
	}

	.stat-item {
		flex: 1;
		min-width: 0;
	}

	.stat-item:first-child {
		text-align: left;
	}

	.stat-item:nth-child(2) {
		text-align: center;
	}

	.stat-item:last-child {
		text-align: right;
	}

	.stat-label {
		display: block;
		overflow: hidden;
		color: $color-primary;
		font-size: 11px;
		line-height: 15px;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.stat-value {
		display: block;
		margin-top: 3px;
		overflow: hidden;
		color: $color-primary;
		font-size: 16px;
		font-weight: 700;
		line-height: 20px;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.user-footer-row {
		display: flex;
		justify-content: space-between;
		color: $color-primary;
	}

	.user-footer-row .joined-text:last-child {
		margin-left: auto;
		text-align: right;
	}

	.joined-text {
		font-size: 11px;
		line-height: 15px;
		white-space: nowrap;
	}

	.text-gray {
		color: #999;
		font-size: 14px;
	}
</style>
