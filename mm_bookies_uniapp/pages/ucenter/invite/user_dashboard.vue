<template>
	<view class="bg-white ">
		<zw-header></zw-header>
		<scroll-view class="user-scroll" scroll-y style="height: calc(100vh - 120px);">
			<view class="padding">
				<view class="title-text margin-tb-sm" style="margin-left: 0;">
					<text class="cuIcon-back text-bold mycolor-primary margin-right-sm" @click="back_to()"></text>
					{{'User Dashboard'}}
				</view>

				<!-- Total Revenue Card -->
				<view class="flex-row justify-between shadow-rec padding-lr text-bold text-black" style="height: 44px;">
					<text class="myfont-12px">{{'Total Revenue from Invitees'}}</text>
					<text
						class="myfont-20px">{{formatAmount(inviteesRewardsData.total_summary ? inviteesRewardsData.total_summary.total_amount : 0)}}<text
							class="myfont-10px margin-left-xs">Ks</text></text>
				</view>

				<!-- Invitation Stats -->
				<view class="flex-row justify-between shadow-rec text-black flex-wrap margin-top-sm"
					style="border: 0px;">
					<view class="flex-column mybg-primary line-height-28px radius-top-10px text-white">
						<text>{{'Invitation'}}</text>
					</view>
					<view class="shadow-rec flex-row justify-around radius-top-1px myfont-14px padding-tb-xs"
						style="line-height: 1;">
						<view class="flex-column1 text-center width-33">
							<view class="padding-tb-xs">{{'Total'}}</view>
							<view class="padding-tb-xs text-bold">{{inviteStats.total_invited}}</view>
						</view>
						<view class="flex-column1 text-center width-33">
							<view class="padding-tb-xs">{{'Pending'}}</view>
							<view class="padding-tb-xs text-bold">{{inviteStats.pending_invitees}}</view>
						</view>
						<view class="flex-column1 text-center width-33">
							<view class="padding-tb-xs">{{'Active Invitees'}}</view>
							<view class="padding-tb-xs text-bold">{{inviteStats.active_invitees}}</view>
						</view>
					</view>
				</view>

				<!-- Financial Stats -->
				<view class="financial-stats">
					<view class="financial-item">
						<text class="financial-label">{{'Total Deposit'}}</text>
						<text
							class="financial-amount">{{formatAmount(inviteesRewardsData.total_deposit ? inviteesRewardsData.total_deposit : 0)}}</text>
						<text class="financial-currency">Ks</text>
					</view>
					<view class="financial-item">
						<text class="financial-label">{{'Total Turnover'}}</text>
						<text
							class="financial-amount">{{formatAmount(inviteesRewardsData.total_turnover ? inviteesRewardsData.total_turnover : 0)}}</text>
						<text class="financial-currency">Ks</text>
					</view>
					<view class="financial-item">
						<text class="financial-label">{{'Total Net Win'}}</text>
						<text
							class="financial-amount">{{formatAmount(inviteesRewardsData.total_net_win ? inviteesRewardsData.total_net_win : 0)}}</text>
						<text class="financial-currency">Ks</text>
					</view>
				</view>

				<!-- Filter Controls -->
				<date-range-picker ref="date_picker" @click_option="date_click"></date-range-picker>
				<view class="flex-row flex-wrap justify-start filter padding-lr-sm margin-tb-sm" style="">
					<view class="filter-row">
						<view class="date-selector" @click="$refs.date_picker.show()">
							<text class="date-range-text">{{getDateRangeText()}}</text>
							<text class="cuIcon-unfold margin-left-xs"></text>
						</view>
					</view>
					<view class="date-selector" style="padding: 0px 12px;">
						<selector :option_list.sync="status_list" @click_option="onStatusSelect" top="36px"
							left="-14px">
						</selector>
					</view>
					<view class="search-container">
						<input type="text" v-model="searchKeyword" class="search-input-field" placeholder="Search"
							@input="onSearch" @confirm="onSearch" />
					</view>
				</view>

				<!-- User List -->
				<view class="user-list-container">
					<view class="user-card" v-for="(user, index) in filteredUserList" :key="index">
						<view class="user-top-row">
							<text class="user-id">{{user.name || user.user_name}}</text>
							<view class="user-status-badges">
								<text v-if="user.user_label" class="user-label-badge"
									:class="getUserLabelClass(user.user_label)">{{user.user_label}}</text>
								<text v-if="getUserStatus(user)" class="status-badge"
									:class="getStatusBadgeClass(getUserStatus(user))">{{user.user_status}}</text>
							</view>
						</view>
						<view class="user-info-row">
							<view class="info-section">
								<text class="info-label">Contribution</text>
								<text class="info-value">{{getContributionText(user)}}</text>
								<text v-if="getLastCompletedActivityText(user)"
									class="info-secondary">{{getLastCompletedActivityText(user)}}</text>
							</view>
							<view class="info-section">
								<text class="info-label text-right">Next Milestone</text>
								<text class="info-value text-right">{{getMilestoneText(user)}}</text>
								<view class="user-activity-row text-right">
									<text class="joined-text">Joined Date {{formatDate(user.register_time)}}</text>
								</view>
							</view>
						</view>

					</view>
				</view>
			</view>
		</scroll-view>
	</view>
</template>

<script>
	import config from '@/utils/config.js'
	import Selector from '../../../components/common/selector.vue'

	export default {
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
					invitation_bonus: {
						total_amount: 0,
						count: 0
					},
					turnover_bonus: {
						total_amount: 0,
						count: 0
					},
					net_win_bonus: {
						total_amount: 0,
						count: 0
					},
					total_summary: {
						total_amount: 0,
						total_count: 0
					},
				},
				status_list: [],
				userList: [],
				filteredUserList: [],
				date_range: [{
					show: "00/00/0000",
					value: "0000-00-00",
				}, {
					show: "00/00/0000",
					value: "0000-00-00",
				}],
				selectedDateOption: 'last_month', // Track selected date option
				searchTimeout: null,
			}
		},
		onLoad() {
			this.userInfo = Object.assign({}, this.$store.state.userInfo)
			// this.date_range = [this.getCurrentDate(30), this.getCurrentDate(0)]
			this.date_range = [this.getCurrentDate(30), this.getCurrentDate(0)]
			this.detectSelectedDateOption() // Detect initial selected option
			this.parse_option_list()
			this.loadInviteStats()
			this.loadInviteesRewards()
		},
		methods: {
			onStatusSelect(selectedOption) {
				this.status_list.forEach((option, index) => {
					option.checked = (option.value === selectedOption.value);
				});
				// Reload data with new status filter instead of front-end filtering
				this.loadInviteesRewards();
			},
			back_to() {
				uni.navigateBack({
					delta: 1,
				})
			},
			parse_option_list() {
				function parse_list(list) {
					return list.map((ele, index) => {
						return {
							label: ele,
							checked: index === 0,
							value: ele.toLowerCase().replace(/ /g, '_'),
						}
					})
				}
				let status = ['All', 'Signed up', 'Active', 'Inactive', 'Pending']
				this.status_list = parse_list(status)
			},
			getCurrentDate(n) {
				var dd = new Date();
				if (n) {
					dd.setDate(dd.getDate() - n);
				}
				var year = dd.getFullYear();
				const month = String(dd.getMonth() + 1).padStart(2, '0');
				const day = String(dd.getDate()).padStart(2, '0');
				return {
					value: `${year}-${month}-${day}`,
					show: `${day}/${month}/${year}`,
				};
			},
			formatAmount(amount) {
				if (!amount) return '0';
				return new Intl.NumberFormat('en-US', {
					minimumFractionDigits: 0,
					maximumFractionDigits: 0
				}).format(amount);
			},
			loadInviteStats() {
				var _this = this;
				_this.$http.get('/activity/invitee-stats', {}, (res) => {
					if (res.statusCode == 200 && res.data.code == 200) {
						console.log(res.data.data)
						_this.inviteStats = res.data.data;
						_this.totalRevenue = _this.inviteStats.total_recharge_amount || 0;
					} else {
						console.error('Failed to load invite stats:', res.data?.message || 'Unknown error');
					}
				})
			},
			loadInviteesRewards() {
				var _this = this;
				const params = {};

				// Add date range based on selected filter
				const dateRange = _this.getDateRange();
				console.log(dateRange)
				if (dateRange.start_date) {
					params.start_date = dateRange.start_date;
				}
				if (dateRange.end_date) {
					params.end_date = dateRange.end_date;
				}

				// Add search keyword
				if (_this.searchKeyword && _this.searchKeyword.trim()) {
					params.keyword = _this.searchKeyword.trim();
				}

				// Add status filter
				const selectedStatus = _this.status_list.find(option => option.checked);
				if (selectedStatus && selectedStatus.value !== 'all') {
					params.status = selectedStatus.value;
				}

				_this.$http.get('/activity/invitees-rewards', {
					data: params
				}, (res) => {
					if (res.statusCode == 200 && res.data.code == 200) {
						_this.inviteesRewardsData = res.data.data;
						_this.userList = res.data.data.invitee_details || [];
						_this.filterUserList();
					} else {
						console.error('Failed to load invitees rewards:', res.data?.message || 'Unknown error');
						_this.userList = [];
						_this.filterUserList();
					}
				})
			},
			getDateRange() {
				// Use the current date_range from date-range-picker component
				if (this.date_range[0].value !== '0000-00-00' && this.date_range[1].value !== '0000-00-00') {
					return {
						start_date: this.date_range[0].value,
						end_date: this.date_range[1].value
					};
				}

				// Default: Last Month (30 days ago to today)
				return {
					start_date: this.getCurrentDate(30).value,
					end_date: this.getCurrentDate(0).value
				};
			},
			onSearch() {
				// Clear previous timeout
				if (this.searchTimeout) {
					clearTimeout(this.searchTimeout);
				}
				// Debounce search to avoid too many API calls
				this.searchTimeout = setTimeout(() => {
					this.loadInviteesRewards();
				}, 500);
			},
			filterUserList() {
				// Since status filtering is now done by API, we only need to handle search keyword filtering
				// But search is also done by API, so we just assign the userList directly
				this.filteredUserList = this.userList;
			},
			date_click(range) {
				this.date_range = range;
				// Detect which option was selected based on the date range
				this.detectSelectedDateOption();
				this.loadInviteesRewards();
			},
			getIsTopUser(user) {
				// Determine if user is a top user based on contribution or status
				return (user.recharge_stats && user.recharge_stats.total_recharge > 50000) ||
					(user.bet_stats && user.bet_stats.total_bet > 100000);
			},
			getUserStatus(user) {
				// Determine user status based on available data
				console.log(user.user_status)
				if (user.user_status) {
					return user.user_status;
				}
				return 'pending';
			},
			getStatusBadgeClass(status) {
				switch (status) {
					case 'Active':
						return 'status-active';
					case 'Inactive':
						return 'status-inactive';
					case 'Pending':
						return 'status-pending';
					case 'Signed Up':
						return 'status-signed';
					default:
						return 'status-default';
				}
			},
			getUserLabelClass(userLabel) {
				// Top User uses green color, others use gray
				if (userLabel === 'Top User') {
					return 'label-top-user';
				}
				return 'label-default';
			},
			getContributionText(user) {
				// Show stats.total_recharge if available
				if (user.stats && user.stats.total_recharge) {
					return `Deposited : ${this.formatAmount(user.stats.total_recharge)} Ks`;
				}
				// Fallback to recharge_stats for compatibility
				if (user.recharge_stats && user.recharge_stats.total_recharge) {
					return `Deposited : ${this.formatAmount(user.recharge_stats.total_recharge)} Ks`;
				}
				return 'Registered';
			},
			getMilestoneText(user) {
				// Show next activity progress title if available
				if (user.next_activity_progress && user.next_activity_progress.activity_title) {
					return user.next_activity_progress.activity_title;
				}
				// Default milestone text
				return '';
			},
			getLastCompletedActivityText(user) {
				// Show last completed activity if available
				if (user.last_completed_activity && user.last_completed_activity.activity_title) {
					const activityTitle = user.last_completed_activity.activity_title;
					const completedTime = user.last_completed_activity.completed_time ?
						`(${this.formatDate(user.last_completed_activity.completed_time)})` : '';
					return `${activityTitle}${completedTime}`;
				}
				return 'Attempted Login';
			},
			formatDate(dateString) {
				if (!dateString) return '';
				const date = new Date(dateString);
				const day = String(date.getDate()).padStart(2, '0');
				const month = date.toLocaleString('en', {
					month: 'short'
				});
				const year = date.getFullYear();
				return `${day} ${month} ${year}`;
			},
			detectSelectedDateOption() {
				if (this.date_range[0].value === '0000-00-00' || this.date_range[1].value === '0000-00-00') {
					this.selectedDateOption = 'all';
					return;
				}

				const start = this.date_range[0].value;
				const end = this.date_range[1].value;
				const today = new Date();
				today.setHours(0, 0, 0, 0);

				// Helper function to format date like the date-range-picker component
				const formatCompareDate = (date) => {
					const year = date.getFullYear();
					const month = String(date.getMonth() + 1).padStart(2, '0');
					const day = String(date.getDate()).padStart(2, '0');
					return `${year}-${month}-${day}`;
				};

				// Today
				const todayStr = formatCompareDate(today);
				if (start === todayStr && end === todayStr) {
					this.selectedDateOption = 'today';
					return;
				}

				// Yesterday
				const yesterday = new Date(today);
				yesterday.setDate(today.getDate() - 1);
				const yesterdayStr = formatCompareDate(yesterday);
				if (start === yesterdayStr && end === yesterdayStr) {
					this.selectedDateOption = 'yesterday';
					return;
				}

				// Weekly (本周，周一开始)
				const weekStart = new Date(today);
				weekStart.setDate(today.getDate() - today.getDay() + (today.getDay() === 0 ? -6 : 1));
				const weekStartStr = formatCompareDate(weekStart);
				if (start === weekStartStr && end === todayStr) {
					this.selectedDateOption = 'weekly';
					return;
				}

				// Last week
				const lastWeekStart = new Date(today);
				lastWeekStart.setDate(today.getDate() - today.getDay() - 6);
				const lastWeekEnd = new Date(lastWeekStart);
				lastWeekEnd.setDate(lastWeekStart.getDate() + 6);
				const lastWeekStartStr = formatCompareDate(lastWeekStart);
				const lastWeekEndStr = formatCompareDate(lastWeekEnd);
				if (start === lastWeekStartStr && end === lastWeekEndStr) {
					this.selectedDateOption = 'last_week';
					return;
				}

				// Monthly (本月)
				const monthStart = new Date(today.getFullYear(), today.getMonth(), 1);
				const monthStartStr = formatCompareDate(monthStart);
				if (start === monthStartStr && end === todayStr) {
					this.selectedDateOption = 'monthly';
					return;
				}

				// Last month
				const lastMonthStart = new Date(today.getFullYear(), today.getMonth() - 1, 1);
				const lastMonthEnd = new Date(today.getFullYear(), today.getMonth(), 0);
				const lastMonthStartStr = formatCompareDate(lastMonthStart);
				const lastMonthEndStr = formatCompareDate(lastMonthEnd);
				if (start === lastMonthStartStr && end === lastMonthEndStr) {
					this.selectedDateOption = 'last_month';
					return;
				}

				// Default fallback
				this.selectedDateOption = 'custom';
			},
			getDateRangeText() {
				const optionLabels = {
					'today': 'Today',
					'yesterday': 'Yesterday',
					'weekly': 'Weekly',
					'last_week': 'Last Week',
					'monthly': 'Monthly',
					'last_month': 'Last Month',
					'all': 'All',
					'custom': `All`
				};

				return optionLabels[this.selectedDateOption] || 'All';
			},
		}
	}
</script>

<style lang="scss">
	// Financial Stats
	.financial-stats {
		display: flex;
		flex-direction: row;
		gap: 12px;
		margin: 16px 0;
	}

	.financial-item {
		flex: 1;
		background: white;
		border-radius: 10px;
		box-shadow: 0px 2px 4px rgba(0, 0, 0, 0.1);
		padding: 16px 12px;
		text-align: center;
	}

	.financial-label {
		display: block;
		font-size: 12px;
		color: #666;
		margin-bottom: 8px;
	}

	.financial-amount {
		display: block;
		font-size: 16px;
		font-weight: bold;
		color: #333;
	}

	.financial-currency {
		display: block;
		font-size: 12px;
		color: #333;
		margin-top: 4px;
	}

	// Filter
	.filter {
		background-color: #f8f9fa;
		border-radius: 8px;
		margin-bottom: 16px;
	}

	.filter-row {
		display: flex;
		align-items: center;
		margin: 8px 0;
		gap: 8px;
	}

	.filter-row .text {
		min-width: 60px;
		font-size: 14px;
	}

	.width-38upx {
		width: 38upx;
		cursor: pointer;
		opacity: 0.8;
	}

	.width-38upx:hover {
		opacity: 1;
	}

	.search-container {
		flex: 1;
	}

	.search-input-field {
		width: 100%;
		height: 36px;
		border: 1px solid #00000040;
		border-radius: 10px;
		padding: 8px 16px;
		font-size: 14px;
		background: white;
	}

	.date-selector {
		display: flex;
		align-items: center;
		padding: 3.5px 12px;
		border: 1px solid #bdbdbd;
		border-radius: 10px;
		background: #bdbdbd;
		color: white;
		cursor: pointer;
		gap: 4px;
	}

	.date-range-text {
		font-size: 12px;
		font-weight: 500;
	}

	// User List Container
	.user-list-container {
		margin-top: 16px;
	}

	.user-scroll {
		padding-right: 4px;
	}

	// User Card - New design
	.user-card {
		background: white;
		border-radius: 12px;
		margin-bottom: 12px;
		padding: 16px;
		box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
		border: 1px solid #f3f4f6;
	}

	.user-top-row {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 12px;
	}

	.user-id {
		font-size: 16px;
		font-weight: 600;
		color: #1f2937;
	}

	.user-status-badges {
		display: flex;
		gap: 6px;
		align-items: center;
	}

	.user-label-badge {
		padding: 4px 8px;
		border-radius: 12px;
		font-size: 10px;
		font-weight: 600;
	}

	.label-top-user {
		background: #079417;
		color: white;
	}

	.label-default {
		background: #949191;
		color: white;
	}

	.status-badge {
		padding: 4px 10px;
		border-radius: 12px;
		font-size: 11px;
		font-weight: 500;
	}

	.status-active {
		background: #d1fae5;
		color: #065f46;
	}

	.status-inactive {
		background: #fee2e2;
		color: #991b1b;
	}

	.status-pending {
		background: #fef3c7;
		color: #92400e;
	}

	.status-signed {
		background: #dbeafe;
		color: #1e40af;
	}

	.status-default {
		background: #f3f4f6;
		color: #6b7280;
	}

	.activity-date {
		color: #9ca3af;
		font-size: 12px;
	}

	.joined-text {
		font-size: 10px;
		color: #9ca3af;
	}

	.user-info-row {
		display: flex;
		justify-content: space-between;
		margin-bottom: 12px;
		gap: 16px;
	}

	.info-section {
		flex: 1;
		display: flex;
		flex-direction: column;
		gap: 4px;
	}

	.info-label {
		font-size: 12px;
		color: #6b7280;
		font-weight: 500;
	}

	.info-value {
		font-size: 14px;
		color: #374151;
		font-weight: 500;
	}

	.info-secondary {
		font-size: 10px;
		color: #6b7280;
		font-weight: 400;
		margin-top: 4px;
	}

	.user-activity-row {
		display: flex;
		flex-direction: column;
		gap: 4px;
	}

	.activity-text {
		font-size: 13px;
		color: #4b5563;
	}

	// Legacy styles - keeping for compatibility
	.shadow-rec {
		box-shadow: 0px 2px 2px 0px #00000040;
		border: 1px solid #00000040;
		border-radius: 10px;
	}
</style>