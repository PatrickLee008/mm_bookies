<template>
	<view class="full-page dark-teal-bg">
		<zw-header></zw-header>


		<!-- 标题栏 -->
		<view class="title-bar" style="height: 183px; background: #fff;">
			<view class="flex-row justify-between" style="">
				<view class="flex-row align-center" style="">
					<image class="yellow2dblue" style="height: 25px;" mode="heightFix" src="/static/icon/wallet.png">
					</image>
					<text class="title-text" style="">{{language.wallet}}</text>
				</view>
			</view>
			<view class="flex-row justify-between">
				<view class="info-rec" style="">
					<view>{{ $t('money') }}</view>
					<view class="flex-row justify-between">
						<text>{{$toolbox.floor_format(userInfo.money)}}</text>
						<text class="myfont-10px">Ks</text>
					</view>
				</view>
				<view class="info-rec" style="">
					<view>{{ $t('in_promo_wallet') }}</view>
					<view class="flex-row justify-between">
						<text>{{$toolbox.floor_format(userInfo.money_promotion)}}</text>
						<text class="myfont-10px">Points</text>
					</view>
				</view>
			</view>
			<!-- tab -->
			<view class="flex-row justify-between padding-lr-sm padding-top-sm myfont-10px text-bold"
				style="line-height: 1.5;">
				<!-- <view class="flex-column1 justify-center align-center" @click=""> -->
				<view class="flex-column1 justify-center align-center" @click="goto('../ucenter/charge')">
					<theme-icon name="deposit" class="title-icon"
						color="var(--theme-icon-secondary, var(--theme-secondary))"></theme-icon>
					<text class="mycolor-lprimary">{{language.deposit}}</text>
				</view>

				<view class="flex-column1 justify-center align-center" @click="goto('../ucenter/withdraw')">
					<theme-icon name="withdraw" class="title-icon"
						color="var(--theme-icon-primary, var(--theme-primary))"></theme-icon>
					<text class="mycolor-lprimary">{{language.withdraw}}</text>
				</view>
				<view class="flex-column1 justify-center align-center" @click="goto('../orders/home')">
					<theme-icon name="history" class="title-icon"
						color="var(--theme-icon-primary, var(--theme-primary))"></theme-icon>
					<text class="mycolor-lprimary">{{language.bet_history}}</text>
				</view>
				<view class="flex-column1 justify-center align-center" @click="relaunch">
					<theme-icon name="refresh" class="title-icon"
						color="var(--theme-icon-primary, var(--theme-primary))"></theme-icon>

					<text class="mycolor-lprimary">{{ $t('refresh') }}</text>
				</view>

			</view>
		</view>

		<!-- 筛选框 -->
		<date-range-picker ref="date_picker" @click_option="date_click"></date-range-picker>
		<view class="padding-sm bg-white">
			<view class="flex-row flex-wrap justify-start filter padding-lr-sm" style="">
				<theme-icon name="calendar" class="width-38upx"
					color="var(--theme-icon-primary, var(--theme-primary))"
					@click="$refs.date_picker.show()"></theme-icon>
				<!-- <view class="cuIcon-calendar mycolor-info text-bold myfont-18px" @click="$refs.date_picker.show()">
				</view> -->
				<view class="filter-row">
					<view class="text mycolor-primary">{{ $t('Type') }}</view>
					<selector :option_list.sync="type_list" @click_option="click_option"></selector>
				</view>
				<view class="filter-row">
					<view class="text mycolor-primary">{{ $t('status') }}</view>
					<selector :option_list.sync="status_list" @click_option="click_option"></selector>
				</view>
				<view class="filter-row">
					<view class="text mycolor-primary line-height-34px">{{ $t('period') }}:
						{{date_range[0].show}}{{' - '}}{{date_range[1].show}}
					</view>
				</view>
			</view>
		</view>
		<!-- <view class="padding-top-sm padding-lr-sm">
			<view class="flex-row flex-wrap justify-start filter padding-sm">
				<svg class="MuiSvgIcon-root MuiSvgIcon-fontSizeMedium mui-319tb2" focusable="false" aria-hidden="true"
					width="20" height="21" viewBox="0 0 20 21" fill="none" xmlns="http://www.w3.org/2000/svg">
					<path fill-rule="evenodd" clip-rule="evenodd"
						d="M6.09634 1.63857C6.09634 1.1994 5.74032 0.843384 5.30116 0.843384C4.862 0.843384 4.50598 1.1994 4.50598 1.63857V3.31296C2.97994 3.43516 1.97812 3.73506 1.2421 4.47108C0.506075 5.2071 0.206175 6.20892 0.0839817 7.73496H21.1207C20.9986 6.20892 20.6986 5.2071 19.9626 4.47108C19.2266 3.73506 18.2248 3.43516 16.6988 3.31296V1.63857C16.6988 1.1994 16.3427 0.843384 15.9036 0.843384C15.4644 0.843384 15.1084 1.1994 15.1084 1.63857V3.24261C14.403 3.22893 13.6124 3.22893 12.7229 3.22893H12.7229H8.48189H8.48184C7.59229 3.22893 6.80168 3.22893 6.09634 3.24261V1.63857ZM16.9639 15.6868C15.6464 15.6868 14.5783 16.7549 14.5783 18.0723C14.5783 19.3898 15.6464 20.4579 16.9639 20.4579C18.2813 20.4579 19.3494 19.3898 19.3494 18.0723C19.3494 16.7549 18.2813 15.6868 16.9639 15.6868ZM12.9879 18.0723C12.9879 15.8765 14.768 14.0964 16.9639 14.0964C19.1597 14.0964 20.9398 15.8765 20.9398 18.0723C20.9398 18.8827 20.6973 19.6364 20.281 20.2649L21.7671 21.7511C22.0776 22.0616 22.0776 22.565 21.7671 22.8755C21.4565 23.1861 20.9531 23.1861 20.6426 22.8755L19.1564 21.3895C18.5279 21.8058 17.7742 22.0482 16.9639 22.0482C14.768 22.0482 12.9879 20.2682 12.9879 18.0723ZM21.2049 13.8313V11.7109C21.2049 10.8213 21.2049 10.0307 21.1912 9.32532H0.0136772C0 10.0307 0 10.8213 0 11.7109V13.8313C0 17.8297 0 19.829 1.24215 21.0711C2.48431 22.3133 4.48351 22.3133 8.48194 22.3133H12.7229C12.9406 22.3133 13.1523 22.3133 13.3582 22.3131C12.1585 21.2921 11.3976 19.771 11.3976 18.0723C11.3976 14.9981 13.8897 12.506 16.9639 12.506C18.6626 12.506 20.1836 13.267 21.2046 14.4666C21.2049 14.2607 21.2049 14.049 21.2049 13.8313Z"
						fill="#A1A0A1"></path>
				</svg>
				<view class="filter-row gap-5px">
					<view class="text mycolor-primary">{{ $t('Type') }}</view>
					<view class="cu-tag round sm tag">
						<selector :option_list.sync="type_list" @click_option="click_option"></selector>
					</view>
				</view>
				<view class="filter-row gap-5px">
					<view class="text mycolor-primary">{{ $t('status') }}</view>
					<view class="cu-tag round sm tag">
						<selector :option_list.sync="status_list" @click_option="click_option"></selector>
					</view>
				</view>
				<view class="filter-row gap-5px">
					<view class="text mycolor-primary">Period: {{'01/05/2025 - 01/05/2025'}}</view>
				</view>
			</view>
		</view> -->
		<scroll-view scroll-y class="" style="height:calc(100vh - 110px - 187px - 73px)" @scrolltolower="clickLoadMore">
			<!-- 列表 -->
			<view class="flex-column1 justify-around" v-for="(element,index) in list" :key='index'
				style="min-height: 140px;font-weight: 400;line-height: 1.5;font-size: 10px;border-radius: 10px;background-color: #fff;padding: 5px 30px;margin: 5px 11px;box-shadow: rgba(60, 64, 67, 0.3) 0px 1px 2px 0px, rgba(60, 64, 67, 0.15) 0px 1px 3px 1px;">
				<view class="flex-row justify-between">
					<view class="flex-column1 align-center">
						<image :src="`/static/icon/register/${element.bank_code}.png`"
							style="border-radius: 10px;height: 30px;width: 30px;" mode=""></image>
						<text class="text-black"
							style="font-family: __Inter_7be8ac, __Inter_Fallback_7be8ac;line-height: 1.5;font-weight: 600;font-size: 10px;">{{element.type}}</text>
					</view>
					<view class="flex-row1">
						<view class="flex-column1 align-start">
							<text>{{ $t('text_field_amount') }}</text>
							<text>{{ $t('submit') }}</text>
							<text>{{ $t('confirm') }}</text>
							<text>{{ $t('remark') }}</text>
						</view>
						<view class="flex-column1 align-start">
							<text>: {{numberFormat(element.amount)}}<text style="margin-left: 1px;">Ks</text></text>
							<text>: {{append_ap(element.create_time)}}</text>
							<text>: {{'-'}}</text>
							<text>: {{'-'}}</text>
							<!-- <text>: {{element.remarks?element.remarks:'-'}}</text> -->
						</view>
					</view>
					<view class="flex-column1 align-end text-bold">
						<text class="myfont-14px text-black">{{numberFormat(element.amount)}}</text>
						<view class=""
							:class="{'text-orange':element.status=='Pending','text-green':element.status=='Success','text-red':element.status=='Rejected',}">
							{{language[element.status.toLowerCase()]}}
						</view>
						<!-- <view>
									{{element.STATUS=='0'?language.have_not_transfer:element.STATUS=='1'?'paid':element.STATUS=='2'?'reject':'unknow'}}
								</view> -->
					</view>
				</view>
				<view class="width-100 text-center">{{element.id}}</view>
			</view>
			<view class="padding"></view>

			<!-- <view class="myrect box-shadow flex-column bg-white" style="width: 90vw;justify-content: flex-start;">
				<view v-for="(element,index) in list" :keys='element.WITHDRAWAL_ID'>
					<view class="mybg-grey" style="width: 90vw;height: 2px;"></view>
					<view class="flex-column">
						<view class="flex-row myfont-bold content-row"
							style="justify-content: space-around;width: 90%;">
							<view>
								{{element.STATUS=='0'?language.have_not_transfer:element.STATUS=='1'?'paid':element.STATUS=='2'?'reject':'unknow'}}
							</view>
							<view>{{language.withdraw_code}}</view>
							<view>{{language.withdraw_history_amount}}</view>
						</view>
						<view class="content-row2 flex-row content-row myrect mybg-grey" style="width: 95%;">
							<view style="margin-left: 2px;">{{append_ap(element.CREATE_TIME)}}</view>
							<view>
								<text class="myfont-bold"
									:style="'color:' + element.color">{{element.Work_Group + '-'}}</text>
								<text>{{element.WITHDRAWAL_CODE}}</text>
							</view>
							<view>{{numberFormat(element.MONEY)}}</view>
						</view>
					</view>
				</view>
			</view> -->

			<!-- <view class="flex-column justify-center" style="position: fixed;top: 45vh;">
				<view class="flex-column align-center justify-center" style="">
					<view class="myfont-20px mycolor-primary">{{language.is_coming_soon}}</view>
				</view>
			</view> -->
		</scroll-view>


	</view>
</template>

<script>
	import config from '../../utils/config.js'
	import language from '../../utils/language.js'
	import dateFormatUtils from "../../utils/utils.js"
	import selector from '../../components/common/selector.vue'

	export default {
		components: {
			selector,
		},
		data() {
			return {
				isLogin: uni.getStorageSync('Authorization') || false,
				language: config.language,
				userInfo: null,

				page: 1,
				list_end: false,
				limit: 15,
				picture: '',
				list: [],
				pay_label: ['pending', 'success', 'reject'],
				type_list: [],
				status_list: [],
				date_range: [{}, {}],
			}
		},

		methods: {
			append_ap(datetimeStr) {
				// 假设格式为 "2025-05-29 15:07"
				const [datePart, timePart] = datetimeStr.split(' ');
				const [hourStr, minuteStr] = timePart.split(':');
				const hour = parseInt(hourStr);

				const period = hour < 12 ? 'AM' : 'PM';
				// console.log(period)
				return `${datetimeStr} ${period}`;
			},
			relaunch() {
				uni.reLaunch({
					url: './wallet'
				})
			},
			goto(url) {
				uni.navigateTo({
					url: url,
				})
			},
			get_list() {
				var _this = this;
				var para = {
					page: _this.page,
					limit: _this.limit,
					start_time: _this.date_range[0].value,
					end_time: _this.date_range[1].value,
				}
				let type = _this.type_list.find(item => item.checked)
				let status = _this.status_list.find(item => item.checked)
				if (type && type.value) para.type = type.value
				let status_label = ['', 'Pending', 'Success', 'Rejected']
				if (status && status.value) para.status = status_label[status.value]

				uni.showLoading({
					'title': 'loading'
				})
				// _this.list = []
				_this.$http.get('/withdraw/get', {
					data: para
				}, (res) => {
					if (res.statusCode == 200) {
						uni.hideLoading();
						var results = res.data.items;
						results.forEach(element => {
							element.create_time = element.create_time.substring(0, 16);
							// console.log(_this.list)
							_this.list.push(element);
						})
						if (results.length < _this.limit) {
							_this.list_end = true

						}
					}
				})
			},
			clickLoadMore() {
				if (this.list_end) {
					uni.showToast({
						'title': 'no more',
						'icon': 'none'
					})
					return
				}
				this.page++;
				this.get_list();
			},
			numberFormat(num) {
				return dateFormatUtils.numFormat(num)
			},
			reset_list() {
				this.page = 1
				this.list_end = false
				this.limit = 15
				this.list = []
			},
			parse_option_list() {
				function parse_list(list) {
					let list_value = {
						'all': '',
						'deposit': 'Deposit',
						'withdraw': 'Withdraw'
					}
					return list.map((ele, index) => {
						return {
							label: ele,
							checked: index === 0,
							// value: index ? index : '',
							value: list_value[ele] ? list_value[ele] : index,
						}
					})
				}
				let type = ['all', 'withdraw', 'deposit']
				let status = ['all', 'pending', 'success', 'reject']
				this.type_list = parse_list(type)
				this.status_list = parse_list(status)
			},
			click_option(item) {
				this.reset_list()
				this.get_list()
			},
			date_click(arr) {
				console.log(1)
				// let start = arr[0]
				// let end = arr[1]
				this.date_range = arr
				this.reset_list()
				this.get_list()
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
		},
		onLoad() {
			this.userInfo = Object.assign({}, this.$store.state.userInfo)
			this.date_range = [this.getCurrentDate(0), this.getCurrentDate(0)]
			this.get_list();
			this.parse_option_list()
		},
		created() {}
	}
</script>

<style lang="scss">
	.dark-teal-bg {
		background-color: var(--theme-page-background-color, #{$theme-header-start});
		background-image: var(--theme-page-background-image, #{$theme-page-background});
		background-position: var(--theme-page-background-position, center);
		background-size: var(--theme-page-background-size, cover);
		background-repeat: var(--theme-page-background-repeat, no-repeat);
		min-height: 100vh;
	}

	.info-rec {
		margin-top: 5px;
		width: 49%;
		height: 70px;
		font-size: 14px;
		font-weight: bold;
		display: flex;
		flex-direction: column;
		justify-content: center;
		padding: 10px;
		background-color: #F5F5F5;
		color: $color-primary;
		border-radius: 8px;
		box-shadow: rgba(99, 99, 99, 0.2) 0px 2px 2px 0px;
		line-height: 1.5;
	}

	.title-icon {
		transition: fill 200ms cubic-bezier(0.4, 0, 0.2, 1) 0ms;
		font-size: 1.5rem;
		width: 28px;
		height: 28px;
		margin-bottom: 2px;
	}
</style>