<template>
	<view class="invite-page">
		<zw-header @headerHeightChange="onHeaderHeightChange"></zw-header>
		<view class="invite-header-placeholder"
			:style="{ height: headerHeight + 'px', transition: 'height 0.3s ease' }"></view>
		<scroll-view scroll-y class="padding-bottom invite-scroll" @scroll="handleHeaderScroll"
			@scrolltoupper="handleHeaderTop">
			<view class="padding-sm bonus-dashboard-content">
				<view class="dashboard-filters">
					<view class="type-filter-container">
						<view class="dashboard-filter type-filter">
							<selector :option_list.sync="type_list" :default_label="$t('Type')"
								@click_option="onTypeSelect"></selector>
						</view>
					</view>
					<view class="dashboard-filter-container">
						<view class="dashboard-filter period-filter" :class="{ 'date-filter-selected': date_filtered }"
							@click="openPeriodPicker">
							<theme-icon v-if="!date_filtered" name="calendar" class="dashboard-filter-icon"
								color="var(--theme-icon-on-primary, #fff)"></theme-icon>
							<text class="period-filter-text">{{ periodDisplay }}</text>
							<text v-if="!date_filtered" class="cuIcon-unfold dashboard-filter-arrow"></text>
						</view>
						<date-range-picker ref="date_picker" :inline="true"
							@click_option="date_click"></date-range-picker>
					</view>
				</view>

				<view class="bonus-source-banner">
					<text>{{ `${$t('Where did your bonus come from')}?` }}</text>
				</view>

				<view class="bonus-card bonus-overview-card">
					<text class="bonus-card-title">{{ $t('Overview of Bonus Earnings') }}</text>
					<view class="bonus-overview-row">
						<view class="bonus-overview-label">
							<text class="bonus-index">1.</text>
							<text>{{ $t('Invitation Achievement') }}</text>
						</view>
						<text class="bonus-overview-value">{{ getInvitationAchievementAmount() }}<text
								class="bonus-currency">Ks</text></text>
					</view>
					<view class="bonus-overview-row">
						<view class="bonus-overview-label">
							<text class="bonus-index">2.</text>
							<text>{{ $t('Invitation Share') }}</text>
						</view>
						<text class="bonus-overview-value">{{ getInvitationShareAmount() }}<text
								class="bonus-currency">Ks</text></text>
					</view>
					<view class="bonus-overview-row">
						<view class="bonus-overview-label">
							<text class="bonus-index">3.</text>
							<text>{{ $t('Deposit Share') }}</text>
						</view>
						<text class="bonus-overview-value">{{ getDepositShareAmount() }}<text
								class="bonus-currency">Ks</text></text>
					</view>
					<view class="bonus-overview-row">
						<view class="bonus-overview-label">
							<text class="bonus-index">4.</text>
							<text>{{ $t('Inviter Commission') }}</text>
						</view>
						<text class="bonus-overview-value">{{ getInviterCommissionAmount() }}<text
								class="bonus-currency">Ks</text></text>
					</view>
					<view class="bonus-overview-row">
						<view class="bonus-overview-label">
							<text class="bonus-index">5.</text>
							<text>{{ $t('Invitee Bet Commission') }}</text>
						</view>
						<text class="bonus-overview-value">{{ getInviteeBetCommissionAmount() }}<text
								class="bonus-currency">Ks</text></text>
					</view>
					<view class="bonus-overview-row" v-if="getOtherAmount() !== '0'">
						<view class="bonus-overview-label">
							<text class="bonus-index">6.</text>
							<text>{{ $t('Other') }}</text>
						</view>
						<text class="bonus-overview-value">{{ getOtherAmount() }}<text
								class="bonus-currency">Ks</text></text>
					</view>
					<view class="bonus-total-row">
						<text>{{ $t('Total Bonus') }}</text>
						<text>{{ getTotalAmount() }}<text class="bonus-currency">Ks</text></text>
					</view>
				</view>

				<view class="bonus-card bonus-chart-card">
					<text class="bonus-card-title">{{ $t('Invitees behaviors for your core earnings') }}</text>
					<view v-if="hasChartData" class="bonus-chart-wrap">
						<qiun-data-charts class="bonus-pie-chart" type="ring" :chartData="chartsDataPie1"
							:opts="pieChartOpts" :animation="false" />
						<text v-for="label in pieLabels" :key="label.index" class="pie-label"
							:style="{ left: label.left, top: label.top }">{{ label.text }}</text>
					</view>
					<view v-else class="chart-no-data">
						<text class="text-gray">{{ $t('No data available for the selected period') }}</text>
					</view>

					<view v-if="hasChartData" class="chart-legend">
						<view v-for="(item, index) in chartsDataPie1.series[0].data" :key="`legend-${index}`"
							class="chart-legend-item">
							<view class="chart-legend-dot" :style="{ backgroundColor: getChartColor(index) }"></view>
							<text>{{ $t(item.name) }}</text>
						</view>
					</view>

					<view v-if="hasChartData" class="chart-table">
						<view class="chart-table-header">
							<text>{{ $t('Title') }}</text>
							<text>{{ $t('Reward Count') }}</text>
							<text>{{ $t('Amount') }}</text>
						</view>
						<view v-for="(item, index) in chartsDataPie1.series[0].data" :key="`row-${index}`"
							class="chart-table-row" :style="{ backgroundColor: getChartColor(index) }">
							<text class="chart-table-title">{{ $t(item.name) }}</text>
							<text class="chart-table-count">{{ item.user || 0 }}</text>
							<text class="chart-table-amount">{{ formatAmount(item.value) }} Ks</text>
						</view>
					</view>
				</view>
			</view>
			<view style="height: 30px; width: 100%;"></view>
		</scroll-view>
	</view>
</template>

<script>
	import config from '@/utils/config.js'
	import headerCollapse from '@/mixins/headerCollapse.js'
	import Selector from '@/components/common/selector.vue'

	export default {
		mixins: [headerCollapse],
		components: {
			Selector,
		},
		data() {
			return {
				language: config.language,
				userInfo: null,
				bonusStats: {
					total_amount: 0,
					bonus_type_breakdown: {
						'Invitation Achievement': {
							total_amount: 0,
							reward_count: 0
						},
						'Invitation Share': {
							total_amount: 0,
							reward_count: 0
						},
						'Deposit Share': {
							total_amount: 0,
							reward_count: 0
						},
						'Inviter Commission': {
							total_amount: 0,
							reward_count: 0
						},
						'Invitee Bet Commission': {
							total_amount: 0,
							reward_count: 0
						},
						'Other': {
							total_amount: 0,
							reward_count: 0
						}
					}
				},
				type_list: [],
				date_preset: '',
				date_filtered: false,
				date_range: [{
					show: "00/00/0000",
					value: "0000-00-00",
				}, {
					show: "00/00/0000",
					value: "0000-00-00",
				}],
				chartsDataPie1: {
					"series": [{
						"data": []
					}]
				},
				color_list: ["#3DB7C7", "#1C6B80", "#75C9D3", "#2F5D62", "#8DB2BD", "#DCECEE"],
				pieChartOpts: {
					color: ["#3DB7C7", "#1C6B80", "#75C9D3", "#2F5D62", "#8DB2BD", "#DCECEE"],
					padding: [0, 0, 0, 0],
					dataLabel: false,
					enableLegend: false,
					title: {
						name: '',
					},
					subtitle: {
						name: '',
					},
					legend: {
						show: false
					},
					extra: {
						ring: {
							ringWidth: 60,
							activeOpacity: 0.5,
							activeRadius: 10,
							offsetAngle: 90,
							border: false,
							centerColor: "#FFFFFF"
						}
					}
				}
			}
		},
		computed: {
			hasChartData() {
				return this.chartsDataPie1.series &&
					this.chartsDataPie1.series[0] &&
					this.chartsDataPie1.series[0].data &&
					this.chartsDataPie1.series[0].data.length > 0;
			},
			periodDisplay() {
				if (this.date_preset) return this.date_preset;
				if (this.date_range[0].value === '0000-00-00' || this.date_range[1].value === '0000-00-00') {
					return this.$t('date');
				}
				return `${this.date_range[0].show} - ${this.date_range[1].show}`;
			},
			pieLabels() {
				if (!this.hasChartData) return [];
				const data = this.chartsDataPie1.series[0].data;
				const total = data.reduce((sum, item) => sum + Number(item.value || 0), 0);
				if (!total) return [];

				let startAngle = Math.PI / 2;
				return data.map((item, index) => {
					const ratio = Number(item.value || 0) / total;
					const middleAngle = startAngle + ratio * Math.PI;
					startAngle += ratio * Math.PI * 2;
					return {
						index,
						text: `${Math.round(ratio * 100)}%`,
						left: `${50 + Math.cos(middleAngle) * 32}%`,
						top: `${50 + Math.sin(middleAngle) * 38}%`,
						ratio
					};
				}).filter(item => item.ratio >= 0.04);
			}
		},
		onLoad() {
			this.userInfo = Object.assign({}, this.$store.state.userInfo)
			this.parse_option_list()
			this.get_summary()
		},
		methods: {
			back_to() {
				uni.navigateTo({
					url: './index'
				})
			},
			parse_option_list() {
				function parse_list(list) {
					let list_value = {
						'all': 'all',
						'Invitation Achievement': 'Invitation Achievement',
						'Invitation Share': 'Invitation Share',
						'Deposit Share': 'Deposit Share',
						'Inviter Commission': 'Inviter Commission',
						'Invitee Bet Commission': 'Invitee Bet Commission',
					}
					return list.map((ele, index) => {
						return {
							label: index === 0 ? 'All' : ele,
							checked: index === 0,
							value: list_value[ele] || '',
						}
					})
				}
				let type = ['all', 'Invitation Achievement', 'Invitation Share', 'Deposit Share', 'Inviter Commission',
					'Invitee Bet Commission'
				]
				this.type_list = parse_list(type)
			},
			get_summary() {
				var _this = this;
				const params = {};
				if (_this.date_range[0].value !== '0000-00-00') {
					params.start_date = _this.date_range[0].value;
				}
				if (_this.date_range[1].value !== '0000-00-00') {
					params.end_date = _this.date_range[1].value;
				}
				const selectedType = _this.getSelectedType();
				if (selectedType && selectedType !== 'all') {
					params.bonus_type = selectedType;
				}
				_this.$http.get('/invitation_v2/rewards/bonus-type-summary', {
					data: params
				}, (res) => {
					if (res.statusCode == 200 && res.data.code == 200) {
						_this.bonusStats = res.data.data.summary;
						setTimeout(() => {
							_this.updateChartData();
						}, 100);
					} else {
						_this.bonusStats = {
							total_amount: 0,
							bonus_type_breakdown: {}
						};
						_this.updateChartData();
					}
				})
			},
			updateChartData() {
				const breakdown = this.bonusStats.bonus_type_breakdown || {};
				const chartData = [];
				const keys = ['Invitation Achievement', 'Invitation Share', 'Deposit Share', 'Inviter Commission',
					'Invitee Bet Commission', 'Other'
				];
				keys.forEach(k => {
					if (breakdown[k] && breakdown[k].total_amount > 0) {
						chartData.push({
							name: k,
							value: breakdown[k].total_amount,
							user: breakdown[k].reward_count
						});
					}
				});
				this.$nextTick(() => {
					this.chartsDataPie1 = {
						"series": [{
							"data": chartData
						}]
					};
				});
			},
			formatAmount(amount) {
				if (!amount) return '0';
				// App 端 JS 引擎无 Intl，手动加千分号
				return String(Math.round(Number(amount))).replace(/\B(?=(\d{3})+(?!\d))/g, ',');
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
					}]
				}
				this.get_summary();
			},
			getInvitationAchievementAmount() {
				const b = this.bonusStats.bonus_type_breakdown;
				return this.formatAmount(b && b['Invitation Achievement'] ? b['Invitation Achievement'].total_amount : 0);
			},
			getInvitationShareAmount() {
				const b = this.bonusStats.bonus_type_breakdown;
				return this.formatAmount(b && b['Invitation Share'] ? b['Invitation Share'].total_amount : 0);
			},
			getDepositShareAmount() {
				const b = this.bonusStats.bonus_type_breakdown;
				return this.formatAmount(b && b['Deposit Share'] ? b['Deposit Share'].total_amount : 0);
			},
			getInviterCommissionAmount() {
				const b = this.bonusStats.bonus_type_breakdown;
				return this.formatAmount(b && b['Inviter Commission'] ? b['Inviter Commission'].total_amount : 0);
			},
			getInviteeBetCommissionAmount() {
				const b = this.bonusStats.bonus_type_breakdown;
				return this.formatAmount(b && b['Invitee Bet Commission'] ? b['Invitee Bet Commission'].total_amount : 0);
			},
			getOtherAmount() {
				const b = this.bonusStats.bonus_type_breakdown;
				return this.formatAmount(b && b['Other'] ? b['Other'].total_amount : 0);
			},
			getTotalAmount() {
				return this.formatAmount(this.bonusStats.total_amount || 0);
			},
			getSelectedType() {
				const opt = this.type_list.find(o => o.checked);
				return opt ? opt.value : 'all';
			},
			getChartColor(index) {
				return this.color_list[index % this.color_list.length];
			},
			openPeriodPicker() {
				this.$refs.date_picker.show();
			},
			onTypeSelect(selectedOption) {
				this.type_list.forEach((option) => {
					option.checked = (option.value === selectedOption.value);
				});
				this.get_summary();
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

	.bonus-dashboard-content {
		padding: 20px 20px 0;
		color: $color-primary;
	}

	.dashboard-filters {
		position: relative;
		display: flex;
		align-items: center;
		gap: 8px;
		margin-bottom: 15px;
	}

	.dashboard-filter-container,
	.type-filter-container {
		position: relative;
		flex: 1;
		min-width: 0;
	}

	.dashboard-filter {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 100%;
		min-width: 0;
		height: 32px;
		border-radius: 999px;
		background: $color-primary;
		color: #fff;
		font-size: 13px;
		font-weight: 700;
		line-height: 24px;
		box-sizing: border-box;
	}

	.type-filter {
		width: 100%;
		overflow: visible;
		gap: 5px;
	}

	.period-filter>text:first-child {
		line-height: 22px;
	}

	.type-filter ::v-deep .selector-wrapper {
		display: flex;
		align-items: center;
		width: 100%;
	}

	.type-filter ::v-deep .selector-tag {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 100%;
		height: 32px;
		padding: 0;
		border: none;
		border-radius: 0;
		background-color: transparent !important;
		color: #fff !important;
		font-size: 13px;
		font-weight: bold;
		line-height: 24px;
		gap: 4px;
	}

	.type-filter ::v-deep .selector-tag text {
		overflow: hidden;
		color: #fff;
		font-size: 13px;
		font-weight: 600;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.type-filter ::v-deep .selector-tag .cuIcon-unfold,
	.type-filter ::v-deep .selector-tag .cuIcon-fold {
		flex-shrink: 0;
		margin-left: 2px;
		color: #fff;
		font-size: 10px;
	}

	.dashboard-filter-icon {
		width: 16px;
		height: 16px;
		margin-right: 6px;
	}

	.dashboard-filter-arrow {
		font-size: 10px;
		line-height: 22px;
	}

	.period-filter {
		gap: 4px;
		white-space: nowrap;
	}

	.period-filter-text {
		// flex: 1;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
		text-align: center;
	}

	.period-filter.date-filter-selected {
		gap: 0;
	}

	.bonus-source-banner {
		display: flex;
		align-items: center;
		min-height: 50px;
		margin-bottom: 12px;
		padding: 0 20px;
		border-radius: 16px;
		background: $bg-color-info;
		color: $color-primary;
		font-size: 16px;
		font-weight: 700;
		line-height: 24px;
		box-sizing: border-box;
	}

	.bonus-card {
		border: 1px solid $color-border-other;
		border-radius: $radius-medium;
		background: #fff;
		border: 1px solid #2A626833;
		box-shadow: 0px 2px 2px 0px #2A626833;
		box-sizing: border-box;
	}

	.bonus-overview-card {
		padding: 22px 20px 16px;
	}

	.bonus-card-title {
		display: block;
		margin-bottom: 16px;
		color: $color-primary;
		font-size: 18px;
		font-weight: 700;
		line-height: 24px;
	}

	.bonus-overview-row {
		display: flex;
		align-items: center;
		justify-content: space-between;
		min-height: 40px;
		font-size: 15px;
		line-height: 20px;
	}

	.bonus-overview-label {
		display: flex;
		align-items: flex-start;
		flex: 1;
		min-width: 0;
	}

	.bonus-index {
		flex: 0 0 28px;
		font-weight: 700;
	}

	.bonus-overview-value {
		min-width: 58px;
		margin-left: 12px;
		color: $color-primary;
		font-weight: 700;
		font-size: 15px;
		text-align: right;
		white-space: nowrap;
	}

	.bonus-currency {
		margin-left: 5px;
		font-size: 13px;
	}

	.bonus-total-row {
		display: flex;
		align-items: center;
		justify-content: space-between;
		margin-top: 8px;
		padding-top: 8px;
		color: $color-secondary;
		font-size: 16px;
		font-weight: 700;
		line-height: 22px;
	}

	.bonus-chart-card {
		margin-top: 20px;
		padding: 22px 20px 16px;
	}

	.bonus-chart-card .bonus-card-title {
		margin-bottom: 8px;
		font-size: 17px;
		line-height: 23px;
	}

	.bonus-chart-wrap {
		position: relative;
		width: 100%;
		height: 300px;
		margin-top: 12px;
	}

	.bonus-pie-chart {
		display: block;
		width: 100%;
		height: 300px;
	}

	.pie-label {
		position: absolute;
		z-index: 2;
		transform: translate(-50%, -50%);
		color: #fff;
		font-size: 15px;
		font-weight: 700;
		line-height: 18px;
		pointer-events: none;
	}

	.chart-legend {
		display: flex;
		align-items: center;
		justify-content: center;
		flex-wrap: wrap;
		gap: 16px;
		margin: 0 0 28px;
		color: $color-primary;
		font-size: 13px;
		line-height: 18px;
	}

	.chart-legend-item {
		display: flex;
		align-items: center;
		white-space: nowrap;
	}

	.chart-legend-dot {
		width: 10px;
		height: 10px;
		margin-right: 5px;
		border-radius: 50%;
	}

	.chart-table-header,
	.chart-table-row {
		display: flex;
		align-items: center;
		width: 100%;
		box-sizing: border-box;
	}

	.chart-table-header {
		padding: 0 0 8px;
		color: $color-primary;
		font-size: 13px;
		line-height: 18px;
	}

	.chart-table-header>text:first-child,
	.chart-table-title {
		flex: 1;
		min-width: 0;
	}

	.chart-table-header>text:nth-child(2),
	.chart-table-count {
		width: 30%;
		text-align: center;
	}

	.chart-table-header>text:nth-child(3),
	.chart-table-amount {
		width: 30%;
		text-align: right;
	}

	.chart-table-row {
		min-height: 58px;
		margin-bottom: 8px;
		padding: 8px 10px;
		border-radius: 8px;
		color: #fff;
		font-size: 14px;
		font-weight: 700;
		line-height: 19px;
	}

	.chart-table-title {
		white-space: normal;
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

	.filter-row .text {
		min-width: 60px;
		font-size: 14px;
	}

	.width-38upx {
		width: 38upx;
		cursor: pointer;
		opacity: 0.8;
	}

	.line-height-34px {
		line-height: 34px;
	}

	.chart-no-data {
		display: flex;
		justify-content: center;
		align-items: center;
		height: 200px;
		border-radius: 8px;
		margin: 16px 0;
	}

	.text-gray {
		color: #999;
		font-size: 14px;
	}

	.width-33 {
		width: 33.33%;
	}
</style>