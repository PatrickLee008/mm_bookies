<template>
	<view class="invite-page">
		<zw-header @headerHeightChange="onHeaderHeightChange"></zw-header>
		<view class="invite-header-placeholder" :style="{ height: headerHeight + 'px', transition: 'height 0.3s ease' }"></view>
		<scroll-view scroll-y class="padding-bottom invite-scroll" @scroll="handleHeaderScroll">
			<view class="flex-column1 align-start text-bold" style="line-height: 1;">
				<text class="title-text margin-tb" style="">
					<!-- <text class="cuIcon-back text-bold mycolor-primary margin-right-sm" @click="back_to()"></text> -->
					{{ $t('Bonus Dashboard') }}</text>
				<text class="margin-left-sm text-black margin-bottom-sm">{{ `${$t('Where did your bonus come from')}?` }}</text>
			</view>

			<date-range-picker ref="date_picker" @click_option="date_click"></date-range-picker>
			<view class="padding-sm">
				<view class="flex-row flex-wrap justify-start filter padding-lr-sm" style="">
					<image mode="widthFix" class="width-38upx" src="/static/image/order/calender.svg"
						@click="$refs.date_picker.show()" />
					<view class="filter-row">
						<view class="text mycolor-primary">{{ $t('type') }}</view>
						<selector :option_list.sync="type_list" @click_option="onTypeSelect"></selector>
					</view>
					<view class="filter-row">
						<view class="text mycolor-primary line-height-34px">Period:
							{{ date_range[0].value === '0000-00-00' ? 'All' : `${date_range[0].show} - ${date_range[1].show}` }}
						</view>
					</view>
				</view>

				<view class="filter flex-column margin-top-sm text-black text-bold myfont-14px">
					<text class="">{{ $t('Overview of Bonus Earnings') }}</text>
					<view class="flex-row justify-between padding-lr-sm">
						<text class="">{{ `1. ${$t('Invitation Achievement')}` }}</text>
						<text class="">{{ getInvitationAchievementAmount() }}<text class="margin-left-xs">Ks</text></text>
					</view>
					<view class="flex-row justify-between padding-lr-sm">
						<text class="">{{ `2. ${$t('Invitation Share')}` }}</text>
						<text class="">{{ getInvitationShareAmount() }}<text class="margin-left-xs">Ks</text></text>
					</view>
					<view class="flex-row justify-between padding-lr-sm">
						<text class="">{{ `3. ${$t('Deposit Share')}` }}</text>
						<text class="">{{ getDepositShareAmount() }}<text class="margin-left-xs">Ks</text></text>
					</view>
					<view class="flex-row justify-between padding-lr-sm">
						<text class="">{{ `4. ${$t('Inviter Commission')}` }}</text>
						<text class="">{{ getInviterCommissionAmount() }}<text class="margin-left-xs">Ks</text></text>
					</view>
					<view class="flex-row justify-between padding-lr-sm">
						<text class="">{{ `5. ${$t('Invitee Bet Commission')}` }}</text>
						<text class="">{{ getInviteeBetCommissionAmount() }}<text class="margin-left-xs">Ks</text></text>
					</view>
					<view class="flex-row justify-between padding-lr-sm" v-if="getOtherAmount() !== '0'">
						<text class="">{{ `6. ${$t('Other')}` }}</text>
						<text class="">{{ getOtherAmount() }}<text class="margin-left-xs">Ks</text></text>
					</view>
					<view class="flex-row justify-between padding-lr-sm mycolor-primary">
						<text class="margin-left text-bold">{{ $t('Total Bonus') }}</text>
						<text class="text-bold">{{ getTotalAmount() }}<text class="margin-left-xs">Ks</text></text>
					</view>
				</view>

				<view class="filter flex-column margin-top-sm text-black">
					<text class="text-bold">{{ $t('Invitees behaviors for your core earnings') }}</text>
					<qiun-data-charts v-if="hasChartData" type="pie" :chartData="chartsDataPie1" />
					<view v-else class="chart-no-data">
						<text class="text-gray">{{ $t('No data available for the selected period') }}</text>
					</view>
					<view v-if="hasChartData" class="flex-row justify-between text-bold padding-lr-sm">
						<text>{{ $t('Insights') }}</text>
						<text>{{ $t('user') }}</text>
						<text>{{ $t('amount') }}</text>
					</view>
					<view v-if="hasChartData" class="flex-row justify-between padding-lr-sm"
						:style="`background-color: ${color_list[index % color_list.length]}`"
						v-for="(item, index) in chartsDataPie1.series[0].data" :key="index">
						<text class="width-33 text-left">{{ item.name }}</text>
						<text class="width-33 text-center">{{ item.user }}</text>
						<text class="width-33 text-right">{{ formatAmount(item.value) }}</text>
					</view>
				</view>
			</view>
			<view style="height: 30px; width: 100%;"></view>
		</scroll-view>
	</view>
</template>

<script>
	import config from '@/utils/config.js'
	import Selector from '../../../components/common/selector.vue'
	import headerCollapse from '@/mixins/headerCollapse.js'

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
						'Invitation Achievement': { total_amount: 0, reward_count: 0 },
						'Invitation Share': { total_amount: 0, reward_count: 0 },
						'Deposit Share': { total_amount: 0, reward_count: 0 },
						'Inviter Commission': { total_amount: 0, reward_count: 0 },
						'Invitee Bet Commission': { total_amount: 0, reward_count: 0 },
						'Other': { total_amount: 0, reward_count: 0 }
					}
				},
				type_list: [],
				date_range: [{
					show: "00/00/0000",
					value: "0000-00-00",
				}, {
					show: "00/00/0000",
					value: "0000-00-00",
				}],
				chartsDataPie1: {
					"series": [{ "data": [] }]
				},
				color_list: ["rgb(47,93,98)", "rgb(79,179,191)", "rgb(232,244,248)"]
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
			this.parse_option_list()
			this.get_summary()
		},
		methods: {
			back_to() {
				uni.navigateTo({ url: './index' })
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
							label: ele,
							checked: index === 0,
							value: list_value[ele] || '',
						}
					})
				}
				let type = ['all', 'Invitation Achievement', 'Invitation Share', 'Deposit Share', 'Inviter Commission', 'Invitee Bet Commission']
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
				_this.$http.get('/invitation_v2/rewards/bonus-type-summary', { data: params }, (res) => {
					if (res.statusCode == 200 && res.data.code == 200) {
						_this.bonusStats = res.data.data.summary;
						setTimeout(() => { _this.updateChartData(); }, 100);
					} else {
						_this.bonusStats = { total_amount: 0, bonus_type_breakdown: {} };
						_this.updateChartData();
					}
				})
			},
			updateChartData() {
				const breakdown = this.bonusStats.bonus_type_breakdown || {};
				const chartData = [];
				const keys = ['Invitation Achievement', 'Invitation Share', 'Deposit Share', 'Inviter Commission', 'Invitee Bet Commission', 'Other'];
				keys.forEach(k => {
					if (breakdown[k] && breakdown[k].total_amount > 0) {
						chartData.push({ name: k, value: breakdown[k].total_amount, user: breakdown[k].reward_count });
					}
				});
				this.$nextTick(() => {
					this.chartsDataPie1 = { "series": [{ "data": chartData }] };
				});
			},
			formatAmount(amount) {
				if (!amount) return '0';
				return new Intl.NumberFormat('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 }).format(amount);
			},
			date_click(range) {
				this.date_range = range;
				if (this.date_range[0].value === '0000-00-00' || this.date_range[1].value === '0000-00-00') {
					this.date_range = [{ show: "00/00/0000", value: "0000-00-00" }, { show: "00/00/0000", value: "0000-00-00" }]
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
		height: 100vh;
		display: flex;
		flex-direction: column;
		background: linear-gradient(to right, #02455F 0%, #02455F 56%, #1F879B 100%);
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
