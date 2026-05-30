<template>
	<view class="bg-white full-page">
		<zw-header></zw-header>

		<view class="flex-column1 align-start text-bold" style="line-height: 1;">
			<text class="title-text margin-tb" style="">
				<text class="cuIcon-back text-bold mycolor-primary margin-right-sm" @click="back_to()"></text>
				{{ $t('bonus_dashboard_title') }}</text>
			<text class="margin-left-sm text-black margin-bottom-sm">{{'Where did your bonus come from?'}}</text>
		</view>

		<date-range-picker ref="date_picker" @click_option="date_click"></date-range-picker>
		<view class="padding-sm">
			<view class="flex-row flex-wrap justify-start filter padding-lr-sm" style="">
				<!-- <view class="cuIcon-calendar mycolor-info text-bold myfont-18px" @click="$refs.date_picker.show()">
						</view> -->
				<image mode="widthFix" class="width-38upx " src="/static/image/order/calender.svg"
					@click="$refs.date_picker.show()" />
				<view class="filter-row">
					<view class="text mycolor-primary">{{$t('type')}}</view>
					<selector :option_list.sync="type_list" @click_option="onTypeSelect"></selector>
				</view>
				<!-- <view class="filter-row">
					<view class="text mycolor-primary">Status</view>
					<selector :option_list.sync="status_list" @click_option="onStatusSelect"></selector>
				</view> -->
				<view class="filter-row">
					<view class="text mycolor-primary line-height-34px">{{ $t('period') }}:
						{{date_range[0].show}}{{' - '}}{{date_range[1].show}}
					</view>
				</view>
			</view>
			<view class="filter flex-column margin-top-sm text-black text-bold myfont-14px">
				<text class="">{{ $t('overview_bonus_earnings') }}</text>
				<view class="flex-row justify-between padding-lr-sm">
					<text class="">{{ $t('invitation_bonus_item') }}</text>
					<text class="">{{getInvitationAmount()}}<text class="margin-left-xs">Ks</text></text>
				</view>
				<view class="flex-row justify-between padding-lr-sm">
					<text class="">{{ $t('turnover_bonus_item') }}</text>
					<text class="">{{getTurnoverAmount()}}<text class="margin-left-xs">Ks</text></text>
				</view>
				<view class="flex-row justify-between padding-lr-sm">
					<text class="">{{ $t('netwin_bonus_item') }}</text>
					<text class="">{{getNetWinAmount()}}<text class="margin-left-xs">Ks</text></text>
				</view>
				<view class="flex-row justify-between padding-lr-sm mycolor-lprimary">
					<text class="margin-left">{{ $t('total_bonus') }}</text>
					<text class="">{{getTotalAmount()}}<text class="margin-left-xs">Ks</text></text>
				</view>
			</view>
			<view class="filter flex-column margin-top-sm text-black">
				<text class="text-bold">{{ $t('invitees_behaviors') }}</text>
				<qiun-data-charts v-if="hasChartData" type="pie" :chartData="chartsDataPie1" />
				<view v-else class="chart-no-data">
					<text class="text-gray">{{ $t('no_data_period') }}</text>
				</view>
				<view v-if="hasChartData" class="flex-row justify-between text-bold padding-lr-sm">
					<text>{{ $t('insights') }}</text>
					<text>{{'User'}}</text>
					<text>{{'Amount'}}</text>
				</view>
				<view v-if="hasChartData" class="flex-row justify-between padding-lr-sm" :style="`background-color: ${color_list[index % color_list.length]}`"
					v-for="(item,index) in chartsDataPie1.series[0].data" :key="index">
					<text class="width-33 text-left">{{item.name}}</text>
					<text class="width-33 text-center">{{item.user}}</text>
					<text class="width-33 text-right">{{formatAmount(item.value)}}</text>
				</view>
			</view>
		</view>


	</view>
</template>

<script>
	import language from '@/utils/language.js'
	import config from '@/utils/config.js'
	import Selector from '../../../components/common/selector.vue'


	export default {
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
						'Invitation Bonus': { total_amount: 0, reward_count: 0 },
						'Turnover bonus': { total_amount: 0, reward_count: 0 },
						'Net Win Bonus': { total_amount: 0, reward_count: 0 }
					}
				},

				type_list: [],
				status_list: [],
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
				color_list: ["rgb(24,144,255)", "rgb(45,203,116)", "rgb(250,200,88)"]
			}
		},
		computed: {
			hasChartData() {
				return this.chartsDataPie1.series && 
					   this.chartsDataPie1.series[0] && 
					   this.chartsDataPie1.series[0].data && 
					   this.chartsDataPie1.series[0].data.length > 0;
			}
		},
		onLoad() {
			this.userInfo = Object.assign({}, this.$store.state.userInfo)
			// Initialize date range to current month
			this.date_range = [this.getCurrentDate(30), this.getCurrentDate(0)]
			// console.log('Initial date range:', this.date_range)
			this.parse_option_list()
			this.get_summary()
		},
		methods: {
			back_to() {
				uni.navigateBack({
					delta: 1,
				})
			},
			parse_option_list() {
				function parse_list(list) {
					let list_value = {
						'all': 'all',
						'Invitation': 'Invitation Bonus',
						'Turnover': 'Turnover bonus',
						'Net Win': 'Net Win Bonus',
						'Claimed': 'claimed',
						'Pending': 'pending',
						'Expired': 'expired',
					}
					return list.map((ele, index) => {
						return {
							label: ele,
							checked: index === 0,
							value: list_value[ele] || '',
						}
					})
				}
				let type = ['all', 'Invitation', 'Turnover', 'Net Win']
				// let status = ['all', 'Claimed', 'Pending', 'Expired']
				this.type_list = parse_list(type)
				// this.status_list = parse_list(status)
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
			click_option(item) {
				// console.log('Option clicked:', item);
				this.reset_list()
				this.get_list()
			},
			reset_list() {
				// Reset and reload data when filters change
				// Add a small delay to ensure .sync has updated the data
				this.$nextTick(() => {
					this.get_summary();
				});
			},
			get_list() {
				// Placeholder for future list functionality
			},
			get_summary() {
				var _this = this;
				const params = {};
				
				// Add date range if available
				if (_this.date_range[0].value !== '0000-00-00') {
					params.start_date = _this.date_range[0].value;
				}
				if (_this.date_range[1].value !== '0000-00-00') {
					params.end_date = _this.date_range[1].value;
				}
				
				// Add bonus type filter if selected
				const selectedType = _this.getSelectedType();
				console.log('Selected type for API:', selectedType);
				if (selectedType && selectedType !== 'all') {
					params.bonus_type = selectedType;
				}
				
				console.log('API params:', params);
				
				_this.$http.get('/activity/rewards/bonus-type-summary', { data: params }, (res) => {
					if (res.statusCode == 200 && res.data.code == 200) {
						_this.bonusStats = res.data.data.summary;
						// Add a small delay to ensure component is ready
						setTimeout(() => {
							_this.updateChartData();
						}, 100);
						// console.log('Bonus stats loaded:', _this.bonusStats);
					} else {
						// console.error('Failed to load bonus stats:', res.data?.message || 'Unknown error');
						// Set empty data on error
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
				
				// Build chart data from API response
				if (breakdown['Invitation Bonus'] && breakdown['Invitation Bonus'].total_amount > 0) {
					chartData.push({
						name: 'Invitation Bonus',
						value: breakdown['Invitation Bonus'].total_amount,
						user: breakdown['Invitation Bonus'].reward_count
					});
				}
				
				if (breakdown['Turnover bonus'] && breakdown['Turnover bonus'].total_amount > 0) {
					chartData.push({
						name: 'Turnover Bonus',
						value: breakdown['Turnover bonus'].total_amount,
						user: breakdown['Turnover bonus'].reward_count
					});
				}
				
				if (breakdown['Net Win Bonus'] && breakdown['Net Win Bonus'].total_amount > 0) {
					chartData.push({
						name: 'Net Win Bonus',
						value: breakdown['Net Win Bonus'].total_amount,
						user: breakdown['Net Win Bonus'].reward_count
					});
				}
				
				// Use Vue.nextTick to ensure DOM update before chart update
				this.$nextTick(() => {
					// Create a new chart data object to force reactivity
					this.chartsDataPie1 = {
						"series": [{
							"data": chartData
						}]
					};
				});
			},
			formatAmount(amount) {
				if (!amount) return '0';
				return new Intl.NumberFormat('en-US', {
					minimumFractionDigits: 0,
					maximumFractionDigits: 0
				}).format(amount);
			},
			date_click(range) {
				this.date_range = range;
				this.get_summary(); // Refresh data when date changes
			},
			getInvitationAmount() {
				const breakdown = this.bonusStats.bonus_type_breakdown;
				return this.formatAmount(breakdown && breakdown['Invitation Bonus'] ? breakdown['Invitation Bonus'].total_amount : 0);
			},
			getTurnoverAmount() {
				const breakdown = this.bonusStats.bonus_type_breakdown;
				return this.formatAmount(breakdown && breakdown['Turnover bonus'] ? breakdown['Turnover bonus'].total_amount : 0);
			},
			getNetWinAmount() {
				const breakdown = this.bonusStats.bonus_type_breakdown;
				return this.formatAmount(breakdown && breakdown['Net Win Bonus'] ? breakdown['Net Win Bonus'].total_amount : 0);
			},
			getTotalAmount() {
				return this.formatAmount(this.bonusStats.total_amount || 0);
			},
			getSelectedType() {
				// Find the selected type from type_list
				const selectedTypeOption = this.type_list.find(option => option.checked);
				// console.log('Type list:', this.type_list);
				// console.log('Selected type option:', selectedTypeOption);
				const selectedValue = selectedTypeOption ? selectedTypeOption.value : 'all';
				// console.log('Selected type value:', selectedValue);
				return selectedValue;
			},
			getSelectedStatus() {
				// Find the selected status from status_list  
				const selectedStatusOption = this.status_list.find(option => option.checked);
				return selectedStatusOption ? selectedStatusOption.value : 'all';
			},
			onTypeSelect(selectedOption) {
				console.log('Type selector clicked:', selectedOption);
				console.log('Selected option value:', selectedOption.value);
				
				// Manually update the type_list to ensure the correct option is selected
				this.type_list.forEach((option, index) => {
					option.checked = (option.value === selectedOption.value);
				});
				
				console.log('Manually updated type_list:', this.type_list);
				console.log('Selected type after manual update:', this.getSelectedType());
				
				// Now call the API with the updated selection
				this.get_summary();
			},
			onStatusSelect(selectedOption) {
				console.log('Status selector clicked:', selectedOption);
				
				// Manually update the status_list to ensure the correct option is selected
				this.status_list.forEach((option, index) => {
					option.checked = (option.value === selectedOption.value);
				});
				
				console.log('Updated status_list:', this.status_list);
				console.log('Selected status:', selectedOption.value);
				
				// Note: Status filtering is for rewards records API, not bonus-type-summary
				// For this dashboard (bonus type summary), we don't need to filter by status
				// If you want to implement status filtering, it should use the /activity/rewards/records API
				console.log('Status filtering not applicable for bonus-type-summary API');
			}
		}
	}
</script>

<style lang="scss">
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

.line-height-34px {
	line-height: 34px;
}

.chart-no-data {
	display: flex;
	justify-content: center;
	align-items: center;
	height: 200px;
	background-color: #f5f5f5;
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