<template>
	<view class="invite-page">
		<zw-header></zw-header>
		<view class="invite-header-placeholder"></view>
		<scroll-view class="user-scroll invite-scroll" scroll-y>
			<view class="padding">
				<view class="title-text margin-tb-sm" style="margin-left: 0;">
					<!-- <text class="cuIcon-back text-bold mycolor-primary margin-right-sm" @click="back_to()"></text> -->
					{{ $t('User Dashboard') }}
				</view>

				<!-- Total Revenue Card -->
				<view class="flex-row justify-between shadow-rec padding-lr text-bold text-black" style="height: 44px;">
					<text class="myfont-12px">{{ $t('Total Revenue from Invitees') }}</text>
					<text class="myfont-20px">{{ formatAmount(bonusSummary.total_amount) }}<text
							class="myfont-10px margin-left-xs">Ks</text></text>
				</view>

				<!-- Invitation Stats -->
				<view class="flex-row justify-between shadow-rec text-black flex-wrap margin-top-sm" style="border: 0px;">
					<view class="flex-column mybg-primary line-height-28px radius-top-10px text-white">
						<text>{{ $t('invitation') }}</text>
					</view>
					<view class="shadow-rec flex-row justify-around radius-top-1px myfont-14px padding-tb-xs"
						style="line-height: 1;">
						<view class="flex-column1 text-center width-33">
							<view class="padding-tb-xs">{{ $t('total') }}</view>
							<view class="padding-tb-xs text-bold">{{ inviteStats.total_invited }}</view>
						</view>
						<view class="flex-column1 text-center width-33">
							<view class="padding-tb-xs">{{ $t('Pending') }}</view>
							<view class="padding-tb-xs text-bold">{{ inviteStats.pending_invitees }}</view>
						</view>
						<view class="flex-column1 text-center width-33">
							<view class="padding-tb-xs">{{ $t('Active Invitees') }}</view>
							<view class="padding-tb-xs text-bold">{{ inviteStats.active_invitees }}</view>
						</view>
					</view>
				</view>

				<!-- Financial Stats -->
				<view class="financial-stats">
					<view class="financial-item">
						<text class="financial-label">{{ $t('Total Deposit') }}</text>
						<text class="financial-amount">{{ formatAmount(inviteesRewardsData.total_deposit || 0) }}</text>
						<text class="financial-currency">MMK</text>
					</view>
					<view class="financial-item">
						<text class="financial-label">{{ $t('Total Turnover') }}</text>
						<text class="financial-amount">{{ formatAmount(inviteesRewardsData.total_turnover || 0) }}</text>
						<text class="financial-currency">MMK</text>
					</view>
					<view class="financial-item">
						<text class="financial-label">{{ $t('Total Net Win') }}</text>
						<text class="financial-amount">{{ formatAmount(inviteesRewardsData.total_net_win || 0) }}</text>
						<text class="financial-currency">MMK</text>
					</view>
				</view>

				<!-- Filter Controls -->
				<date-range-picker ref="date_picker" @click_option="date_click"></date-range-picker>
				<view class="flex-row flex-wrap justify-start filter padding-lr-sm padding-tb-xs margin-tb-sm" style="">
					<image mode="widthFix" class="width-38upx" src="/static/image/order/calender.svg"
						@click="$refs.date_picker.show()" />
					<view class="filter-row">
						<view class="date-selector" style="font-size: 12px;">
							<selector :option_list.sync="status_list" @click_option="onStatusSelect" top="36px"
								left="-14px"></selector>
						</view>
					</view>
					<view class="search-container">
						<input type="text" v-model="searchKeyword" class="search-input-field" :placeholder="$t('Search')"
							@input="onSearch" @confirm="onSearch" />
					</view>
				</view>

				<!-- User List -->
				<view class="user-list-container">
					<view class="user-card" v-for="(user, index) in filteredUserList" :key="index">
						<view class="user-top-row">
							<text class="user-id">{{ user.name || user.user_name }}</text>
							<view class="user-status-badges">
								<text v-if="user.user_label" class="user-label-badge"
									:class="getUserLabelClass(user.user_label)">{{ user.user_label }}</text>
								<text v-if="getUserStatus(user)" class="status-badge"
									:class="getStatusBadgeClass(getUserStatus(user))">{{ user.user_status }}</text>
							</view>
						</view>
						<view class="user-stats-row">
							<view class="stat-item">
								<text class="stat-label">{{ $t('Deposit') }}</text>
								<text class="stat-value">{{ formatAmount(user.stats ? user.stats.total_recharge : 0) }}</text>
								<text class="stat-label">MMK</text>
							</view>
							<view class="stat-item">
								<text class="stat-label">{{ $t('Turnover') }}</text>
								<text class="stat-value">{{ formatAmount(user.stats ? user.stats.total_bet : 0) }}</text>
								<text class="stat-label">MMK</text>
							</view>
							<view class="stat-item">
								<text class="stat-label">{{ $t('Net Win') }}</text>
								<text class="stat-value">{{ formatAmount(user.stats ? user.stats.net_win : 0) }}</text>
								<text class="stat-label">MMK</text>
							</view>
						</view>
						<view class="user-footer-row">
							<text class="joined-text" v-if="user.last_login_time">{{ $t('Last Login') }}
								{{ formatDate(user.last_login_time) }}</text>
							<text class="joined-text">{{ $t('Joined') }} {{ formatDate(user.register_time) }}</text>
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
				return new Intl.NumberFormat('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 }).format(amount);
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
			date_click(range) {
				if (this.date_range[0].value == range[0].value && this.date_range[1].value == range[1].value) {
					this.date_range = [{ show: "00/00/0000", value: "0000-00-00" }, { show: "00/00/0000", value: "0000-00-00" }]
					if (this.$refs.date_picker && this.$refs.date_picker.date_arr) {
						this.$refs.date_picker.date_arr.forEach(e => e.checked = false)
					}
				} else {
					this.date_range = range;
				}
				this.loadBonusSummary();
				this.loadInviteesRewards();
			},
			getUserStatus(user) {
				return user.user_status ? user.user_status : 'pending';
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
			getUserLabelClass(userLabel) {
				return userLabel === 'Top User' ? 'label-top-user' : 'label-default';
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
		height: 100vh;
		display: flex;
		flex-direction: column;
		background: #02455F;
		overflow: hidden;
	}

	.invite-header-placeholder {
		width: 100%;
		height: 255px;
		background:
			radial-gradient(circle at 100% 0%, #36BCCB 0%, #1F879B 34%, rgba(31, 135, 155, 0) 68%),
			linear-gradient(135deg, #02455F 0%, #02455F 56%, #1F879B 100%);
		background-size: 100% 552px;
		background-position: center -255px;
		flex-shrink: 0;
	}

	.invite-scroll {
		flex: 1;
		height: 0;
		border-radius: 20px 20px 0 0;
		background: #ffffff;
		position: relative;
		z-index: 1;
	}

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
		display: flex;
		flex-direction: column;
		justify-content: space-between;
	}

	.financial-label {
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 12px;
		color: #666;
		margin-bottom: 8px;
		line-height: 1.6;
		min-height: 40px;
	}

	.financial-amount {
		display: block;
		font-size: 16px;
		font-weight: bold;
		color: #1C667C;
		line-height: 1.6;
	}

	.financial-currency {
		display: block;
		font-size: 12px;
		color: #333;
		margin-top: 4px;
	}

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

	.width-38upx {
		width: 38upx;
		cursor: pointer;
		opacity: 0.8;
	}

	.search-container {
		flex: 1;
	}

	.search-input-field {
		width: 100%;
		height: 36px;
		border: 1px solid #00000040;
		border-radius: 8px;
		padding: 8px 16px;
		font-size: 14px;
		background: white;
	}

	.date-selector {
		display: flex;
		align-items: center;
		padding: 0 12px;
		border: 1px solid #1C667C;
		border-radius: 8px;
		background: #1C667C;
		color: white;
		cursor: pointer;
		gap: 4px;
		height: 25px;
	}

	.user-list-container {
		margin-top: 16px;
	}

	.user-scroll {
		padding-right: 4px;
	}

	.user-card {
		background: white;
		border-radius: 12px;
		margin-bottom: 12px;
		padding: 16px;
		box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
		border: 1px solid #f3f4f6;
	}

	.user-stats-row {
		display: flex;
		justify-content: space-between;
		margin-bottom: 8px;
	}

	.stat-item {
		flex: 1;
		text-align: center;
	}

	.stat-label {
		display: block;
		font-size: 11px;
		color: #9ca3af;
		margin-bottom: 4px;
	}

	.stat-value {
		display: block;
		font-size: 13px;
		font-weight: 600;
		color: #374151;
	}

	.user-footer-row {
		display: flex;
		justify-content: space-between;
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

	.joined-text {
		font-size: 10px;
		color: #9ca3af;
	}

	.text-gray {
		color: #999;
		font-size: 14px;
	}

	.shadow-rec {
		box-shadow: 0px 2px 2px 0px #00000040;
		border: 1px solid #00000040;
		border-radius: 10px;
	}
</style>
