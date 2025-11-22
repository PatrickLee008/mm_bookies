<template name="orders">
	<view class="mybg-grey " :style="{'height':calc_page_height,}">
		<zw-header></zw-header>
		<view class="flex-row mybg-lprimary padding-tb justify-around myfont-17px line-height-17px">
			<view class="flex-column gap-5px">
				<view class="myfont-12px">{{$t('winnings')}}</view>
				<view class="text-bold">{{$toolbox.num_format(report.win)}}</view>
			</view>
			<view class="flex-column gap-5px">
				<view class="myfont-12px">{{$t('loss')}}</view>
				<view class="text-bold">{{$toolbox.num_format(report.loss)}}</view>
			</view>
			<view class="flex-column gap-5px">
				<view class="myfont-12px">{{$t('all_stake')}} / {{$t('betting')}}</view>
				<view class="text-bold">{{$toolbox.num_format(report.all_stake,0)}} / {{history_list.length}}</view>
			</view>
		</view>
		<view class="padding-sm">
			<view class="flex-row flex-wrap justify-start filter padding-lr-sm" style="">
				<!-- <view class="cuIcon-calendar mycolor-info text-bold myfont-18px" @click="$refs.date_picker.show()">
				</view> -->
				<image mode="widthFix" class="width-38upx " src="/static/image/order/calender.svg"
					@click="$refs.date_picker.show()" />
				<view class="filter-row">
					<view class="text mycolor-primary">{{$t('type')}}</view>
					<selector :option_list.sync="type_list" @click_option="click_option"></selector>
				</view>
				<view class="filter-row">
					<view class="text mycolor-primary">{{$t('status')}}</view>
					<selector :option_list.sync="status_list" @click_option="click_option"></selector>
				</view>
				<view class="filter-row">
					<view class="text mycolor-primary">{{$t('wallet')}}</view>
					<selector :option_list.sync="wallet_list" @click_option="click_option"></selector>
				</view>
				<view class="filter-row">
					<view class="text mycolor-primary line-height-34px">Period:
						{{date_range[0].show}}{{' - '}}{{date_range[1].show}}
					</view>
				</view>
			</view>
		</view>
		<view class="flex-row padding-lr padding-bottom-8px myfont-12px">
			<view class="grey-border radius-8px width-50 height-37px" style="position: relative;"
				@click="page_change('Pending')" :class="{'mybg-primary':current_page==='Pending',}">
				<view class="line-height-35px" :class="{'myfont-11px':$t('lang')==='mm',}">{{$t('Pending')}}</view>
				<view class="flex-row text-container">
					<view style="" class="myfont-8px radius-5px page-text mycolor-primary"
						:class="current_page==='Pending'?'bg-white':'mybg-info'">{{total}}</view>
				</view>
			</view>
			<view class="grey-border radius-8px width-50 height-37px" style="" @click="page_change('Settled')"
				:class="{'mybg-primary':current_page==='Settled',}">
				<view class="line-height-35px" :class="{'myfont-11px':$t('lang')==='mm',}">{{$t('Settled')}}</view>
				<view></view>
			</view>
		</view>
		<scroll-view scroll-y class="page padding-lr-sm myfont-9px line-height-13px"
			style="height: calc(100% - 560upx);">
			<view v-for="(item,index) in history_list" class="padding-top-xs " :key='index'>
				<!-- 单笔 -->
				<view class="bet-row text-left text-bold" v-if="item.IS_MIX == '0' || item.IS_MIX === false">
					<view class="wallet">{{item.pay_wallet ==='Money'?$t('main_wallet'):$t('pro_wallet')}}</view>
					<!-- 左 -->
					<view class="flex-row justify-between">
						<view class="flex-column width-20 " style="align-items: start;">
							<view class="myfont-9px">Single</view>
							<view class="flex-row">
								<image mode="widthFix" class="status-icon margin-right-3upx" :src="item.status_img" />
								<text>{{item.bet_status}}</text>
							</view>
							<view class="myfont-6px margin-top-2px" style="">{{item.order_time}}</view>
						</view>
						<!-- 中间 -->
						<view class="flex-column width-50">
							<view class="flex-row align-center">
								<text>
									<text class="icon-single width-10px height-10px margin-right-xs"
										style="padding: 0;">
									</text>{{item.LEAGUE}}
								</text>
							</view>
							<view class="flex-row" style="align-items: flex-start;">
								<view class="width-40" :class="{'text-red':item.LOSE_TEAM=='1',}">{{item.HOME}}</view>
								<view class="width-20">
									<text>{{item.SCORE}}</text>
								</view>
								<view class="width-40" :class="{'text-red':item.LOSE_TEAM=='2',}">{{item.AWAY}}</view>
							</view>
							<view class="flex-row myfont-6px justify-between mycolor-info ">
								<view class="flex-column">
									<view class="width-100">Stake</view>
									<view class="myfont-12px line-height-16px">
										{{$toolbox.num_format(item.BET_MONEY,0)}} <text class="myfont-5px margin-left-xs">Ks</text>
									</view>
								</view>
								<view class="width-100">
									<image mode="widthFix" class="width-22upx margin-right-3upx max-height-30upx"
										src="/static/image/order/copy.svg" @click="copy(item)" />
									<text>Bet ID: {{item.ORDER_ID}}</text>
								</view>
							</view>
						</view>
						<!-- 右 -->
						<view class="flex-column width-20" style="align-items: flex-start;">
							<view>{{item.show_order_type}}</view>
							<view class="myfont-8px">
								<text class="" :class="{'text-red':item.DRAW_BUNKO==='1',}">{{item.real_odds}}</text>
								<text class="">@</text>
								<text class="bg-green margin-left-2px">{{$toolbox.num_format(item.BET_ODDS,2)}}</text>
							</view>
							<view :class="{'text-red':item.team_name===(item.LOSE_TEAM == 1 ?item.HOME:item.AWAY),}">{{item.team_name}}</view>
							<view class="flex-column">
								<view class="width-100 mycolor-info myfont-6px">{{$t('potential')}}</view>
								<view class="myfont-12px line-height-16px width-100">
									<text :class="{'text-red':item.benefit.indexOf('-') > -1,}">{{item.benefit}}</text>
									<text class="myfont-5px margin-left-xs">Ks</text>
								</view>
							</view>
						</view>
					</view>
				</view>

				<view v-else @click="show_detail(item)">
					<!-- 混合 -->
					<view class="bet-row text-left myfont-9px line-height-13px text-bold" style="position: relative;">
						<view class="wallet">{{item.pay_wallet ==='Money'?$t('main_wallet'):$t('pro_wallet')}}</view>
						<!-- <image mode="widthFix" class="width-48upx" v-show="item.show_detail" src="/static/image/order/unfold-order.svg" style="position: absolute;right: 0px;top: -5px;"/> -->
						<image mode="widthFix" class="width-48upx" :style="{visibility:item.show_detail?'':'hidden'}"
							src="/static/image/order/unfold-order.svg"
							style="position: absolute;right: 0px;top: -5px;" />
						<!-- <text class="cuIcon-copy width-48upx line-height-26px myfont-18px text-center"
							@click="copy(item)" style="position: absolute;right: 48upx;top: -3px;" /> -->
						<image mode="widthFix" class="width-48upx" :style="{visibility:!item.show_detail?'':'hidden'}"
							src="/static/image/order/fold-order.svg" style="position: absolute;right: 0px;top: -5px;" />
						<!-- 左 -->
						<view class="flex-row justify-between">
							<view class="flex-column width-25" style="align-items: start;">
								<view class="myfont-9px">Mixparlay</view>
								<view class="flex-row" v-if="current_page==='Pending'">
									<image mode="widthFix" class="status-icon margin-right-3upx"
										:src="`/static/image/order/pending.svg`" />
									<text>Pending</text>
								</view>
								<view class="flex-row" v-else>
									<image mode="widthFix" class="status-icon margin-right-3upx"
										:src="item.status_img" />
									<text>{{item.bet_status}}</text>
								</view>
								<view class="myfont-6px margin-top-2px" style="">{{item.order_time}}</view>
							</view>
							<!-- 中间 -->
							<view class="flex-column width-50">
								<view>
									<text class="">{{item.ORDER_COUNT}}</text>
									<text class="padding-lr-xs">@</text>
									<text
										class="bg-green">{{$toolbox.num_format(Math.pow(2,item.ORDER_COUNT),2)}}</text>
								</view>
								<view class="flex-row myfont-6px justify-between mycolor-info">
									<view class="flex-column">
										<view class="width-100 text-center">{{$t('stake')}}</view>
										<view class="myfont-12px line-height-16px">
											{{$toolbox.num_format(item.BET_MONEY,0)}} <text class="myfont-5px margin-left-xs">Ks</text>
										</view>
									</view>
								</view>
							</view>
							<!-- 右 -->
							<view class="flex-column width-25" style="align-items: flex-start;">
								<view class="flex-column">
									<view class="width-100 mycolor-info myfont-6px">
										{{current_page==='Pending'?$t('potential_winnings_over'):$t('potential')}}
									</view>
									<view class="myfont-12px line-height-16px width-100">
										<text
											:class="{'text-red':item.benefit.indexOf('-') > -1,}">{{item.benefit}}</text>
										<text class="myfont-5px margin-left-xs">Ks</text>
									</view>
								</view>
								<view>
									<image mode="widthFix" class="width-22upx margin-right-3upx max-height-30upx"
										src="/static/image/order/copy.svg" @click="copy(item)" />
									<text class="myfont-6px line-height-9px mycolor-info">Bet ID:
										{{item.ORDER_ID}}</text>
								</view>
							</view>
						</view>
					</view>

					<!-- 混合详情 -->
					<view class="flex-column" v-show="item.show_detail">
						<view v-for="(detail,_index) in item.detail" class="width-100" :key='_index'>
							<view class="flex-row justify-between padding-sm text-bold mix-detail">
								<view class="flex-column width-20 " style="align-items: start;">
									<view class="flex-row">
										<image mode="widthFix" class="status-icon margin-right-3upx"
											:src="detail.status_img" />
										<text>{{detail.bet_status}}</text>
									</view>
								</view>
								<!-- 中间 -->
								<view class="flex-column width-50">
									<view class="flex-row align-center">
										<text>
											<text class="icon-single width-10px height-10px margin-right-xs"
												style="padding: 0;">
											</text>{{detail.LEAGUE}}
										</text>
									</view>
									<view class="flex-row text-left" style="align-items: flex-start;">
										<view class="width-40" :class="{'text-red':detail.LOSE_TEAM=='1',}">
											{{detail.HOME}}
										</view>
										<view class="width-20">
											<text>{{detail.SCORE}}</text>
										</view>
										<view class="width-40" :class="{'text-red':detail.LOSE_TEAM=='2',}">
											{{detail.AWAY}}
										</view>
									</view>

								</view>
								<!-- 右 -->
								<view class="flex-column width-20" style="">
									<view>{{detail.show_order_type}}</view>
									<view class="myfont-8px">
										<text class=""
											:class="{'text-red':detail.DRAW_BUNKO==='1',}">{{detail.real_odds}}</text>
										<text class="">@</text>
										<text class="bg-green margin-left-2px">2.00</text>
									</view>
									<view :class="{'text-red':detail.team_name===(detail.LOSE_TEAM == 1 ?detail.HOME:detail.AWAY),}">{{detail.team_name}}
									</view>
								</view>
							</view>
						</view>
					</view>
				</view>
			</view>
			<view class="padding-top-5vh flex-column align-center gap-5vh" v-show="history_list.length === 0">
				<image src="/static/image/order/empty.svg" class="width-10vw height-10vw"></image>
				<view class="myfont-14px mycolor-info width-60 myfont-17px line-height-25px">
					{{$t(current_page ==='Pending'?'no_pending_bets':'no_settled_bets')}}
				</view>
				<!-- <view class="myfont-12px margin-top-sm">{{language['add more predictions for winner']}}</view> -->

				<button class="cu-btn mybg-lprimary radius-12px height-10vw" @click="navi_to_single">
					<image src="/static/image/order/new_bet.svg" class="width-8vw height-8vw margin-right-sm"></image>
					{{$t('Place Bet')}}
				</button>
			</view>
		</scroll-view>

		<date-range-picker ref="date_picker" @click_option="date_click"></date-range-picker>

	</view>
</template>

<script>
	import Vue from 'vue';
	import config from '../../utils/config.js';
	import dateFormatUtils from "../../utils/utils.js";
	import Selector from '../../components/common/selector.vue'
	import match_mixins from '../match/components/mixins.js'


	export default {
		name: 'orders',
		components: {
			Selector,
		},
		mixins: [match_mixins],
		data() {
			return {
				listQuery: {
					end: false,
					time: 0,
					type: 0,
					is_mix: '',
					limit: 100,
					page: 1,
				},
				total: 0,
				win_status_2_str: ['Lose', 'Win', 'Pending'],
				current_page: 'Pending',
				history_list: [],
				type_list: [],
				status_list: [],
				wallet_list: [],
				date_range: [{}, {}],
				report: {
					all_stake: 0,
					win: 0,
					loss: 0,
				}
			};
		},
		methods: {
			copy(order) {
				uni.setClipboardData({
					data: order.ID,
					success: function() {
						uni.showToast({
							title: 'Order ID Copied to clipboard',
							icon: 'success'
						});
					},
					fail: function() {
						// uni.showToast({
						//   title: '复制失败',
						//   icon: 'none'
						// });
					}
				});

			},
			navi_to_single() {
				uni.reLaunch({
					url: '/pages/match/home'
				})
			},
			click_option(item) {
				let value = item.value === 'All' ? null : item.value
				this.listQuery[item.attr] = value
				this.reset_list()
				this.get_list()
			},
			date_click(arr) {
				// let start = arr[0]
				// let end = arr[1]
				this.date_range = arr
				this.reset_list()
				this.get_list()
			},
			parse_option_list() {
				function parse_list(list, attr) {
					return list.map((ele, index) => {
						return {
							label: ele.toLowerCase(),
							checked: index === 0,
							_index: index,
							value: ele,
							attr: attr,
						}
					})
				}
				let types = ['All', 'Single', 'Mixparlay']
				let status = ['All', 'Pending', 'Win', 'Lose', 'Draw', 'Cancel', 'Refund', 'Rejected']
				// let status = ['all', 'pending', 'win', 'lose', 'draw', ]
				let wallets = ['All', 'Money', 'Promotion']
				this.type_list = parse_list(types, 'bet_type')
				this.status_list = parse_list(status, 'bet_status')
				this.wallet_list = parse_list(wallets, 'pay_wallet')
			},
			page_change(page) {
				if (this.$toolbox.click_too_fast(1)) return
				this.current_page = page
				this.reset_list()
				this.get_list()
			},
			calParlay(betContent) {
				let a = ''
				if (this.$t('lang') == 'mm') {
					a = betContent.REMARK.slice(0, betContent.REMARK.indexOf('x')) + this.$t('parlay')
				} else {
					a = this.$t('parlay') + betContent.REMARK
				}
				return a
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
			numberFormat(num) {
				return dateFormatUtils.numFormat(num)
			},
			reset_list() {
				this.listQuery.end = false
				this.listQuery.page = 1
				this.history_list = [];
				this.report = this.$options.data().report
			},
			clickLoadMore(type) {
				if (this.listQuery.end) {
					return
				}
				this.get_list()
			},
			get_list() {
				let _this = this;
				let paras = {
					..._this.listQuery,
					// page: _this.listQuery.page,
					// limit: _this.listQuery.limit,
					// status: _this.listQuery.status,
					// order_type: _this.listQuery.type == 3 ? 3 : '',
					// game_type: 1,
					start_time: _this.date_range[0].value,
					end_time: _this.date_range[1].value,
					// is_mix: _this.listQuery.is_mix == 'Mixparlay' ? 1 : _this.listQuery.is_mix == 'Single' ? 0 : ''
				};
				// console.log(this.listQuery,paras)
				uni.showLoading({
					title: 'Loading!'
				})
				let url = _this.current_page == 'Pending' ? '/order/get' : '/order/get_history';
				// var url = '/order/get'
				_this.$http.get(url, {
					data: paras
				}, (res) => {
					uni.hideLoading()
					if (res.statusCode == 200) {
						var results = res.data.items;
						results.forEach(ele => {
							ele = _this.parse_order(ele)
							let money = _this.$toolbox.num_format(ele.BET_MONEY, 0, true)
							if (_this.current_page === 'Settled') {
								let bonus = _this.$toolbox.num_format(ele.netwin_actual, 0, true)
								// bonus = bonus < money ? bonus - money : bonus;
								if (ele.bet_status === 'Cancel') {
									bonus = 0
								}
								_this.report.win += bonus > 0 ? bonus : 0;
								_this.report.loss += bonus < 0 ? bonus : 0;

							}
							_this.report.all_stake += money

							_this.history_list.push(ele);
						})
						if (_this.current_page === 'Pending') {
							_this.total = res.data.total
						}
						if (results.length == 0) {
							_this.listQuery.end = true
						} else {}
					}
				})
			},
			show_detail(row, type) {
				if (row.IS_MIX != '1') return;
				if (row.has_detail) {
					row.show_detail = !row.show_detail
					return
				}
				let _this = this;
				let url = _this.current_page == 'Pending' ? '/order/get' : '/order/get_history';
				// let url = _this.current_page == 'Pending' ? '/order/get' : '/order/get_history';
				// var url = '/order/get'
				if (this.$toolbox.click_too_fast(1)) return
				let paras = {
					order_id: row.ORDER_ID.replace(/\s*/g, ""),
					is_detail: true
				};
				_this.$http.get(url, {
					data: paras
				}, (res) => {
					if (res.statusCode == 200) {
						row.has_detail = true
						let items = res.data.items
						items.forEach(ele => {
							row.detail.push(_this.parse_order(ele))
						})
						row.show_detail = true
					}
				})
			},
			parse_order(ele) {
				ele = this.order_mapping(ele)
				// Use HOME and AWAY from order_mapping if available, otherwise parse from ORDER_DESC
				if (!ele.HOME || !ele.AWAY) {
					var temp = ele.ORDER_DESC.split('||');
					ele.HOME = ele.HOME || temp[0] || '';
					ele.AWAY = ele.AWAY || temp[1] || '';
				}
				ele.SCORE = `${this.parse_score(ele.BET_HOST_TEAM_RESULT)}-${this.parse_score(ele.BET_GUEST_TEAM_RESULT)}`
				ele.show_detail = false
				ele.has_detail = false
				ele.detail = []
				ele.BET_ODDS = ele.BET_ODDS === '1' || ele.BET_ODDS === 1 ? '2.00' : ele.BET_ODDS
				ele.real_odds = this.calc_real_odds(ele)
				let desc = ele.order_type_desc || ele.REMARK
				ele.ORDER_COUNT = desc == '暂无' ? 1 : desc.split('串')[0]
				ele.benefit = this.calc_benefit(ele, ele.IS_MIX == 1)
				ele.team_name = this.calc_team_name(ele)
				ele.show_order_type = this.order_type_2_str(ele)
				ele.order_time = this.parse_time(ele)
				ele.bet_status = ele.bet_status ? ele.bet_status : `${this.current_page==='Pending'?'pending':''}`
				ele.bet_status = ele.bet_status.replace('Half','').replace('half','')
				ele.status_img = `/static/image/order/${ele.bet_status.toLowerCase()}.svg`

				ele.order_type_desc = desc.replace('串', 'x')
				return ele
			},
			order_mapping(order) {
				// Map AppBetOrder fields to Order model fields for compatibility
				if (order.mb_id) {
					// This is an AppBetOrder, map to Order fields
					const mappedOrder = {
						// Basic identifiers
						ID: order.id,
						ORDER_ID: order.bet_group,
						USER_ID: order.mb_id,
						USER_NAME: order.mb_username,
						AGENT_CODE: order.aid || '',

						// Match and game info
						MATCH_ID: order.game_id,
						ORDER_DESC: order.remarks || '',
						LEAGUE: order.league || '',

						// Betting info - parse bet_type_sub format "ORDER_TYPE:BET_TYPE"
						ORDER_TYPE: order.bet_type_sub ? order.bet_type_sub.split(':')[0] : '',
						BET_TYPE: order.bet_type_sub ? order.bet_type_sub.split(':')[1] : '',
						BET_MONEY: order.stake,
						BET_ODDS: order.odds,

						// Mix betting
						IS_MIX: order.bet_type === 'Mixparlay' ? '1' : '0',

						// Status mapping
						STATUS: '1', // Always valid for AppBetOrder
						IS_WIN: order.bet_status === 'Win' ? '1' : order.bet_status === 'Lose' ? '0' : '2',
						bet_status: order.bet_status,

						// Financial info
						BONUS: order.netwin,
						pay_wallet: order.pay_wallet,

						// Match odds info
						DRAW_BUNKO: order.draw_bunko || '',
						DRAW_ODDS: order.draw_odds || '',
						LOSE_TEAM: order.lose_team || '',
						LOSE_BALL_NUM: order.lose_ball_num || '',

						// Team names and scores from AppBetOrder
						HOME: order.home || '',
						AWAY: order.away || '',
						
						// Results (if available)
						BET_HOST_TEAM_RESULT: order.home_score || '',
						BET_GUEST_TEAM_RESULT: order.away_score || '',

						// Timestamps
						CREATE_TIME: order.create_time,
						MATCH_TIME: '', // Not directly available

						// Additional fields
						main_order_id: order.id,
						order_type_desc: order.bet_type === 'Mixparlay' ? `${order.order_count}串1` : '暂无',
						ORDER_COUNT: order.order_count || 1,

						// Copy any other fields that might exist
						...order
					};
					return mappedOrder;
				}

				// If it's already an Order model, return as is
				return order
			},
			parse_score(score) {
				if (typeof score !== 'number') {
					score = score ? score : -1
				}
				score = parseInt(score)
				score = score > -1 && score < 100 ? score : ''
				return score
			},
			parse_time(order) {
				const date = new Date(order.CREATE_TIME);

				// 获取日期组件
				const day = String(date.getDate()).padStart(2, '0');
				const month = String(date.getMonth() + 1).padStart(2, '0');
				const year = date.getFullYear();

				// 获取时间组件并转换为12小时制
				let hours = date.getHours();
				const ampm = hours >= 12 ? 'PM' : 'AM';
				hours = hours % 12;
				hours = hours ? hours : 12; // 0点转换为12
				const minutes = String(date.getMinutes()).padStart(2, '0');
				const seconds = String(date.getSeconds()).padStart(2, '0');

				return `${day}/${month}/${year} ${String(hours).padStart(2, '0')}:${minutes}:${seconds} ${ampm}`;
			},
			order_type_2_str(attr, typ = 'ORDER_TYPE') {
				if (!attr.hasOwnProperty(typ)) return ''
				let str = ''
				let attr_val = String(attr[typ])
				switch (true) {
					case [this.bet_type.SINGLE_BODY, this.bet_type.MIX_BODY].includes(attr_val):
						str = 'HANDICAP'
						break
					case [this.bet_type.SINGLE_GOAL, this.bet_type.MIX_GOAL].includes(attr_val):
						str = attr.BET_TYPE == '1' ? this.$t('over') : this.$t('under');
						break
					case [this.bet_type.SINGLE_EVEN, this.bet_type.MIX_EVEN].includes(attr_val):
						// str = 'EVEN'
						break
					case [this.bet_type.SINGLE_WDL].includes(attr_val):
						// str = '1X2'
						break
				}
				return str
			},
			calc_team_name(attr, typ = 'ORDER_TYPE') {
				if (!attr.hasOwnProperty(typ)) return ''
				let str = ''
				let attr_val = String(attr[typ])
				switch (true) {
					case [this.bet_type.SINGLE_BODY, this.bet_type.MIX_BODY].includes(attr_val):
						str = attr.BET_TYPE == '1' ? attr.HOME : attr.AWAY;
						break
					case [this.bet_type.SINGLE_GOAL, this.bet_type.MIX_GOAL].includes(attr_val):
						break
					case [this.bet_type.SINGLE_EVEN, this.bet_type.MIX_EVEN].includes(attr_val):
						// str = 'EVEN'
						break
					case [this.bet_type.SINGLE_WDL].includes(attr_val):
						let num_2_str = [, attr.HOME, attr.AWAY, 'DRAW']
						str = num_2_str[parseInt(attr.BET_TYPE)];
						break
				}
				return str
			},
			calc_benefit(order, mix = false) {
				let str = ''
				if (this.current_page === 'Settled') {
					//直接返回
					str = order.BONUS
					if (str < order.BET_MONEY) {
						// str = str - order.BET_MONEY
						str = order.netwin_actual
					}
				} else {
					// 赔率设置在match_mixins中
					if (mix) {
						str = Math.pow(2, order.ORDER_COUNT) * parseFloat(order.BET_MONEY) * (1 - this.commission)
					} else {
						let odds = parseFloat(order.BET_ODDS);
						switch (order.ORDER_TYPE) {
							case "10": //1x2，直接取赔率
								break;
							default: //其他，1+赔率
								odds = 1 + odds;
						}
						str = parseFloat(odds) * parseInt(order.BET_MONEY)
						// str = parseFloat(odds) * parseInt(order.BET_MONEY) * (1 - this.commission)
					}
				}
				if(order.bet_status ==='Cancel'){
					return '\\'
					// str = order.stake
				}
				//盈利添加+号
				let plus = str > 0 ? '+' : ''
				// 增加千分号
				str = this.$toolbox.num_format(str, 0)
				return plus + str
			},
			calc_real_odds(attr, typ = 'ORDER_TYPE') {
				if (!attr.hasOwnProperty('ORDER_TYPE')) return ''
				let str = ''
				// 胜平负盘
				if ([this.bet_type.SINGLE_WDL].includes(attr.ORDER_TYPE)) {
					let num_2_str = [, 'HOME', 'AWAY', 'DRAW']
					return `1X2:${num_2_str[parseInt(attr.BET_TYPE)]}`
				}
				var DRAW_BUNKO = attr.DRAW_BUNKO == '0' ? '+' : '-';
				if (attr.DRAW_ODDS == '0') {
					return attr.LOSE_BALL_NUM + '=';
				} else {
					let body_attr = [this.bet_type.SINGLE_BODY, this.bet_type.MIX_BODY].includes(attr.ORDER_TYPE) ||
						''
					if (body_attr) {
						body_attr = attr.LOSE_TEAM == '1' ? 'H' : 'A'
					}
					return `${attr.LOSE_BALL_NUM}(${DRAW_BUNKO}${attr.DRAW_ODDS})${body_attr}`;
				}
			},
		},
		mounted() {
			this.date_range = [this.getCurrentDate(0), this.getCurrentDate(0)]
			this.parse_option_list()
			this.get_list()
		},
		created() {}
	}
</script>

<style>
	.bet-row {
		display: flex;
		flex-direction: column;
		justify-content: center;
		align-items: center;
		width: 100%;
		justify-content: space-evenly;
		border: 1px solid rgba(0, 0, 0, 0.12);
		border-radius: 5px;
		padding: 0px 5px;
	}

	.status-icon {
		width: 30upx;
		max-height: 50upx;
	}

	.wallet {
		font-weight: 500;
		width: 30%;
		background-color: rgb(255, 196, 54);
		color: rgb(0, 0, 0);
		border-radius: 0px 0px 8px 8px;
		height: 15px;
		justify-content: center;
		display: flex;
		align-items: center;
		margin-bottom: 3px;
		font-size: 8px;
	}

	.mix-detail {
		border-width: 0px 0px thin;
		border-style: solid;
		border-color: rgba(0, 0, 0, 0.12);
	}

	.grey-border {
		border: 1upx #dddddd solid;
	}

	.text-container {
		top: 0;
		position: absolute;
		right: 0;
		align-items: center;
		height: 100%;
		justify-content: end;
		/* top: 15upx; */
	}

	.page-text {
		margin-right: 15upx;
		padding: 10upx 13upx;
		line-height: 1;
	}
</style>