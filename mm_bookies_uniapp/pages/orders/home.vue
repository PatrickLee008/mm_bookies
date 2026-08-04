<template name="orders">
	<view class="full-page">
		<zw-header></zw-header>

		<!-- from tangjq--- header占位元素，防止内容被遮挡 -->
		<view class="header-placeholder"></view>

		<!-- <view class="flex-row mybg-lprimary padding-tb justify-around myfont-17px line-height-17px">
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
		</view> -->


		<!-- from tangjq--- 标题栏 -->
		<view class="title-bar">
			<view class="tab-selector">
				<view class="tab-container">
					<view class="tab-item" :class="{'active':current_page==='pending'}" @click="page_change('pending')">
						<text class="tab-text">{{$t('pending')}}</text>
					</view>
					<view class="tab-item" :class="{'active':current_page==='Finished'}"
						@click="page_change('Finished')">
						<text class="tab-text">{{$t('Finished')}}</text>
					</view>

					<!-- from tangjq--- 底部滑动指示器 -->
					<view class="slide-indicator" :class="{'indicator-finished': current_page==='Finished'}"></view>
				</view>
			</view>
		</view>

		<view class="padding-lr-sm bg-white">
			<view class="flex-row flex-wrap justify-start filter padding-sm" style="">
				<image mode="widthFix" class="width-38upx" src="/static/image/order/calender.svg"
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
					<view class="text mycolor-primary line-height-28px">Period:
						{{date_range[0].show}}{{' - '}}{{date_range[1].show}}
					</view>
				</view>
			</view>
		</view>

		<scroll-view scroll-y class="main-scroll-view">
			<view class="history-container">
				<view v-for="(item,index) in history_list" :key='index' class="history-item">
					<!-- 单笔投注 -->
					<view class="bet-card" v-if="item.IS_MIX == '0' || item.IS_MIX === false">
						<!-- 卡片头部 -->
						<view class="card-header">
							<!-- from tangjq--- 已结算时右上角显示该场比赛输赢状态 -->
							<view class="status-badge" :class="'badge-'+status_badge(item.bet_status).type"
								v-if="current_page==='Finished' && item.bet_status">
								<text class="status-badge-text">{{status_badge(item.bet_status).label}}</text>
							</view>
							<view class="match-time">{{item.order_time}}</view>
							<view class="header-match">
								<text class="team-name"
									:class="{ 'team-give': give_team_side(item) === 'H' }">{{item.HOME}}</text>
								<text class="vs-text" v-if="current_page==='pending'">VS</text>
								<text class="score-text" v-else>{{item.SCORE}}</text>
								<text class="team-name"
									:class="{ 'team-give': give_team_side(item) === 'A' }">{{item.AWAY}}</text>
							</view>
						</view>

						<!-- 卡片内容 -->
						<view class="card-content">
							<!-- <view class="info-row">
								<text class="label">{{$t('Bet Time')}}</text>
								<text class="value">{{item.order_time}}</text>
							</view> -->
							<view class="info-row">
								<text class="label">{{$t('Type')}}</text>
								<text class="value value-amount">{{item.show_order_type}}</text>
							</view>
							<view class="info-row">
								<text class="label">{{$t('Bet')}}</text>
								<text class="value value-amount">{{item.team_name}}</text>
							</view>
							<view class="info-row">
								<text class="label">{{$t('Odds')}}</text>
								<text class="value value-amount">{{item.real_odds}}</text>
							</view>
							<view class="info-row">
								<text class="label">{{$t('total bet amount')}}</text>
								<text class="value  value-amount"
									style="font-style: italic;">{{$toolbox.num_format(item.BET_MONEY,0)}} MMK</text>
							</view>
							<view class="info-row" v-if="current_page==='pending'">
								<text class="label">{{$t('Potential Win Amount')}}</text>
								<text class="value value-amount">{{item.benefit}} MMK</text>
							</view>
						</view>

						<!-- 已结算状态条 -->
						<view class="result-bar" v-if="current_page==='Finished'"
							:class="{'result-win':item.benefit.indexOf('-') === -1 && item.benefit !== '\\', 'result-lose':item.benefit.indexOf('-') > -1 || item.benefit === '\\'}">
							<text class="result-text"
								v-if="item.benefit.indexOf('-') === -1 && item.benefit !== '\\'">WIN {{item.benefit}}
								MMK</text>
							<text class="result-text" v-else-if="item.benefit === '\\'">CANCEL</text>
							<text class="result-text" v-else>LOSE {{item.benefit}} MMK</text>
						</view>
					</view>

					<!-- 混合投注 Parlay -->
					<view class="bet-card parlay-card" v-else>
						<!-- 单个比赛项 - 折叠时只显示一个 -->
						<view v-if="!item.show_detail">
							<view class="card-header">
								<!-- from tangjq--- 已结算时右上角显示订单输赢状态 -->
								<view class="status-badge" :class="'badge-'+status_badge(item.bet_status).type"
									v-if="current_page==='Finished' && item.bet_status">
									<text class="status-badge-text">{{status_badge(item.bet_status).label}}</text>
								</view>
								<view class="match-time">{{item.order_time}}</view>
								<view class="header-match">
									<text class="team-name"
										:class="{ 'team-give': give_team_side(item) === 'H' }">{{item.HOME}}</text>
									<text class="vs-text" v-if="current_page==='pending' && give_team_side(item)">VS</text>
									<text class="score-text" v-else>{{item.SCORE}}</text>
									<text class="team-name"
										:class="{ 'team-give': give_team_side(item) === 'A' }">{{item.AWAY}}</text>
								</view>
							</view>
							<view class="card-content">
								<!-- <view class="info-row">
									<text class="label">{{$t('Bet Time')}}<</text>
									<text class="value">{{item.order_time}}</text>
								</view> -->
								<view class="info-row">
									<text class="label">{{$t('Type')}}</text>
									<text class="value">MixParlay</text>
								</view>
								<!-- <view class="info-row">
									<text class="label">{{$t('Bet')}}</text>
									<text class="value">{{item.ORDER_COUNT}}X1</text>
								</view> -->
								<view class="info-row">
									<text class="label">{{$t('Odds')}}</text>
									<text class="value">{{item.real_odds}}</text>
								</view>
							</view>
						</view>

						<!-- 展开时显示所有比赛 -->
						<view v-else>
							<view v-for="(detail,_index) in item.detail" :key="_index">
								<view class="card-header">
									<!-- from tangjq--- 已结算时右上角显示该场比赛输赢状态 -->
									<view class="status-badge" :class="'badge-'+status_badge(detail.bet_status).type"
										v-if="current_page==='Finished' && detail.bet_status">
										<text class="status-badge-text">{{status_badge(detail.bet_status).label}}</text>
									</view>
									<!-- 混合投注展开后，仅第一场显示下注日期 -->
									<view class="match-time" v-if="_index === 0">{{detail.order_time}}</view>
									<view class="header-match">
										<text class="team-name"
											:class="{ 'team-give': give_team_side(detail) === 'H' }">{{detail.HOME}}</text>
										<text class="vs-text" v-if="current_page==='pending'">VS</text>
										<text class="score-text" v-else>{{detail.SCORE}}</text>
										<text class="team-name"
											:class="{ 'team-give': give_team_side(detail) === 'A' }">{{detail.AWAY}}</text>
									</view>
								</view>
								<view class="card-content">
									<!-- <view class="info-row">
										<text class="label">{{$t('Bet Time')}}<</text>
										<text class="value">{{detail.order_time}}</text>
									</view> -->
									<view class="info-row">
										<text class="label">{{$t('Type')}}</text>
										<text class="value">{{detail.show_order_type}}</text>
									</view>
									<view class="info-row">
										<text class="label">{{$t('Bet')}}</text>
										<text class="value">{{detail.team_name}}</text>
									</view>
									<view class="info-row">
										<text class="label">{{$t('Odds')}}</text>
										<text class="value">{{detail.real_odds}}</text>
									</view>
								</view>
								<view class="divider"></view>
								<!-- <view class="divider" v-if="_index < item.detail.length - 1"></view> -->
							</view>
						</view>

						<!-- Parlay 底部汇总信息 -->
						<view class="parlay-summary">
							<view class="info-row">
								<text class="label">{{$t('total bet amount')}}</text>
								<text class="value value-amount">{{$toolbox.num_format(item.BET_MONEY,0)}} MMK</text>
							</view>
							<view class="info-row">
								<text class="label">{{$t('Total Match')}}</text>
								<text class="value">{{item.ORDER_COUNT}}</text>
							</view>
							<view class="info-row" v-if="current_page==='pending'">
								<text class="label">{{$t('Potential Win Amount')}}</text>
								<text class="value value-amount">{{item.benefit}} MMK</text>
							</view>
						</view>

						<!-- 已结算状态条 -->
						<view class="result-bar" v-if="current_page==='Finished'"
							:class="{'result-win':item.benefit.indexOf('-') === -1 && item.benefit !== '\\', 'result-lose':item.benefit.indexOf('-') > -1 || item.benefit === '\\'}">
							<text class="result-text"
								v-if="item.benefit.indexOf('-') === -1 && item.benefit !== '\\'">WIN {{item.benefit}}
								MMK</text>
							<text class="result-text" v-else-if="item.benefit === '\\'">CANCEL</text>
							<text class="result-text" v-else>LOSE {{item.benefit}} MMK</text>
						</view>

						<!-- Parlay 折叠/展开按钮：文字左右两侧均显示细双箭头图标 -->
						<view class="parlay-toggle" @click="show_detail(item)">
							<view class="toggle-icon">
								<text class="arrow" :class="item.show_detail ? 'cuIcon-fold' : 'cuIcon-unfold'"></text>
								<text class="arrow" :class="item.show_detail ? 'cuIcon-fold' : 'cuIcon-unfold'"></text>
							</view>
							<text class="parlay-label">{{$t('mixparlay')}} {{item.ORDER_COUNT}} x 1</text>
							<view class="toggle-icon">
								<text class="arrow" :class="item.show_detail ? 'cuIcon-fold' : 'cuIcon-unfold'"></text>
								<text class="arrow" :class="item.show_detail ? 'cuIcon-fold' : 'cuIcon-unfold'"></text>
							</view>
						</view>
					</view>
				</view>

				<!-- 空状态 -->
				<view class="padding-top-5vh flex-column align-center gap-5vh" v-show="history_list.length === 0">
					<image src="/static/image/order/empty.svg" class="width-10vw height-10vw"></image>
					<view class="myfont-14px mycolor-info width-60 myfont-17px line-height-25px">
						{{$t(current_page ==='pending'?'no_pending_bets':'no_settled_bets')}}
					</view>
					<button class="cu-btn radius-12px height-10vw" @click="navi_to_single"
						style="background-color: #1C667C;color: white;">
						<image src="/static/image/order/new_bet.svg" class="width-8vw height-8vw margin-right-sm">
						</image>
						{{$t('Place Bet')}}
					</button>
				</view>
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
				win_status_2_str: ['Lose', 'Win', 'pending'],
				current_page: 'pending',
				history_list: [],
				type_list: [],
				status_list: [],
				wallet_list: [],
				date_range: [{}, {}],
				date_filtered: false,
				send_date: true,
				report: {
					all_stake: 0,
					win: 0,
					loss: 0,
				}
			};
		},
		methods: {
			copy(order) {
				console.log(order)
				uni.setClipboardData({
					data: order.ID || order.id,
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
				if (this.date_range[0].value === '0000-00-00' || this.date_range[1].value === '0000-00-00') {
					this.send_date = false
				} else {
					this.send_date = true
				}
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
				let types = ['All', 'Single', 'Mixparlay', 'AWC']
				let status = ['All', 'Pending', 'Win', 'Lose', 'Draw', 'Cancel', 'Refund', 'Rejected']
				let wallets = ['All', 'Promotion', 'Money']
				this.type_list = parse_list(types, 'bet_type')
				this.status_list = parse_list(status, 'bet_status')
				this.wallet_list = parse_list(wallets, 'pay_wallet')
			},
			page_change(page) {
				if (this.$toolbox.click_too_fast(1)) return
				this.current_page = page
				this.date_filtered = false
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
					start_time: _this.send_date ? _this.date_range[0].value : '',
					end_time: _this.send_date ? _this.date_range[1].value : '',
					date_filtered: _this.date_filtered ? 1 : 0,
					// is_mix: _this.listQuery.is_mix == 'Mixparlay' ? 1 : _this.listQuery.is_mix == 'Single' ? 0 : ''
				};
				// console.log(this.listQuery,paras)
				uni.showLoading({
					title: 'Loading!'
				})
				let url = _this.current_page == 'pending' ? '/order/get' : '/order/get_history';
				// var url = '/order/get'
				_this.$http.get(url, {
					data: paras
				}, (res) => {
					uni.hideLoading()
					if (res.statusCode == 200) {
						var results = res.data.items;
						results.forEach(ele => {
							let money = 0;
							if (ele.platform_source != 'AWC') {
								ele = _this.parse_order(ele)
								money = _this.$toolbox.num_format(ele.BET_MONEY, 0, true)
								_this.report.all_stake += money
							}
							if (_this.current_page === 'Settled') {
								if (ele.platform_source == 'AWC') {
									let bonus_main = _this.$toolbox.num_format(ele.net_main, 0, true)
									let bonus_promo = _this.$toolbox.num_format(ele.net_promo, 0, true)
									let bonus_actual = parseInt(bonus_main) + parseInt(bonus_promo)
									_this.report.win += bonus_actual > 0 ? bonus_actual : 0;
									_this.report.loss += bonus_actual < 0 ? bonus_actual : 0;
									_this.history_list.push(ele);
									return; // 跳过后续的普通订单处理逻辑
								}
								let bonus = _this.$toolbox.num_format(ele.netwin, 0, true)
								// bonus = bonus < money ? bonus - money : bonus;
								let bonus_actual = parseInt(bonus)
								if (ele.netwin_actual < 0 && ele.bet_status != 'Refund') {
									bonus_actual = parseInt(ele.netwin_actual)
								}
								if (ele.bet_status === 'Cancel') {
									bonus = 0
								}
								_this.report.win += bonus_actual > 0 ? bonus_actual : 0;
								_this.report.loss += bonus_actual < 0 ? bonus_actual : 0;
								// _this.report.win += bonus > 0 ? bonus : 0;
								// _this.report.loss += bonus < 0 ? bonus : 0;
							}
							_this.history_list.push(ele);
						})
						if (_this.current_page === 'pending') {
							_this.total = res.data.total
						}
						if (results.length < _this.listQuery.limit) {
							_this.listQuery.end = true
						} else {
							_this.listQuery.page++
						}
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
				let url = _this.current_page == 'pending' ? '/order/get' : '/order/get_history';
				// let url = _this.current_page == 'pending' ? '/order/get' : '/order/get_history';
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
				ele.bet_status = ele.bet_status ? ele.bet_status : `${this.current_page==='pending'?'pending':''}`
				// ele.bet_status = ele.bet_status.replace('Half', '').replace('half', '')
				ele.status_img = `/static/image/order/${ele.bet_status.toLowerCase()}.svg`
				// ele.MATCH_TIME = ele.MATCH_TIME ? ele.MATCH_TIME : ''
				ele.order_type_desc = desc.replace('串', 'x')
				return ele
			},
			order_mapping(order) {
				// Map AppBetOrder fields to Order model fields for compatibility
				if (order.mb_id) {
					// This is an AppBetOrder, map to Order fields
					let bet_type_subs = order.bet_type_sub ? order.bet_type_sub.split(':') : [];
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
						ORDER_TYPE: bet_type_subs.length > 0 ? bet_type_subs[0] : '',
						BET_TYPE: bet_type_subs.length > 1 ? bet_type_subs[1] : order.bet_type_sub2,
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
						MATCH_TIME: order.MATCH_TIME ? order.MATCH_TIME : '',
						// MATCH_TIME: '', // Not directly available

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
			order_type_2_str(attr, typ = 'ORDER_TYPE') {
				if (!attr.hasOwnProperty(typ)) return ''
				let str = ''
				let attr_val = String(attr[typ])
				if ([this.bet_type.SINGLE_BODY, this.bet_type.MIX_BODY].includes(attr_val)) {
					str = 'HANDICAP'
				} else if ([this.bet_type.SINGLE_GOAL, this.bet_type.MIX_GOAL].includes(attr_val)) {
					str = 'O/U';
					//str = attr.BET_TYPE == '1' ? this.$t('over') : this.$t('under');
				} else if ([this.bet_type.SINGLE_EVEN, this.bet_type.MIX_EVEN].includes(attr_val)) {
					str = 'O/E'
					// str = attr.BET_TYPE == '1' ? this.$t('Odd') : this.$t('Even');
				} else if ([this.bet_type.SINGLE_CORRECT].includes(attr_val)) {
					str = "Correct Score";
				} else if ([this.bet_type.SINGLE_BTTS].includes(attr_val)) {
					// switch(attr.BET_TYPE){
					// 	case "1":str="Both";break;
					// 	case "2":str="One";break;
					// 	case "3":str="No Goal";break;
					// }
					str = "BTTS"
				} else if ([this.bet_type.SINGLE_WDL].includes(attr_val)) {
					// switch (attr.BET_TYPE) {
					// 	case "1":
					// 		str = "Home";
					// 		break;
					// 	case "2":
					// 		str = "Away";
					// 		break;
					// 	case "3":
					// 		str = "Draw";
					// 		break;
					// }
					str = "1X2"; //已经处理在：calc_real_odds处理显示
				} else {
					str = "";
				}

				// console.log("order_type_2_str", attr_val, str);
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
						str = attr.BET_TYPE == '1' ? this.$t('over') : this.$t('under');
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
			// 仅 HANDICAP(让球)类型：让球方(odd given team)球队名称显示红色，其余类型球队名称保持原色
			// LOSE_TEAM=='1' 主队为让球方，否则客队为让球方
			give_team_side(attr) {
				if (!attr || !attr.hasOwnProperty('ORDER_TYPE')) return ''
				let attr_val = attr.ORDER_TYPE
				if ([this.bet_type.SINGLE_BODY, this.bet_type.MIX_BODY].includes(attr_val)) {
					return attr.LOSE_TEAM == '1' ? 'H' : 'A'
				}
				return ''
			},
			calc_benefit(order, mix = false) {
				let str = ''
				if (this.current_page === 'Finished') {
					//直接返回
					str = order.BONUS
					if (str < parseInt(order.BET_MONEY) && order.bet_status != 'Refund') {
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
							case "1": //HDP
							case "2": //O/U
							case "6": //O/E
								odds = 1 + odds;
								break;
						}
						str = parseFloat(odds) * parseInt(order.BET_MONEY)
						// str = parseFloat(odds) * parseInt(order.BET_MONEY) * (1 - this.commission)
					}
				}
				if (order.bet_status === 'Cancel') {
					return '\\'
					// str = order.stake
				}
				//盈利添加+号
				let plus = str > 0 ? '' : ''
				// 增加千分号
				str = this.$toolbox.num_format(str, 0)
				return plus + str
			},
			calc_real_odds(attr, typ = 'ORDER_TYPE') {
				if (!attr.hasOwnProperty('ORDER_TYPE')) return ''
				let attr_val = attr.ORDER_TYPE
				let str = ''
				var DRAW_BUNKO = attr.DRAW_BUNKO == '0' ? '+' : '-';
				let body_attr = ''
				if ([this.bet_type.SINGLE_BODY, this.bet_type.MIX_BODY].includes(attr_val)) {
					if (attr.DRAW_ODDS == '0') {
						return attr.LOSE_BALL_NUM + '=';
					}
					let body_attr = attr.LOSE_TEAM == '1' ? 'H' : 'A'
					return `${attr.LOSE_BALL_NUM}(${DRAW_BUNKO}${attr.DRAW_ODDS})${body_attr}`;
				} else if ([this.bet_type.SINGLE_GOAL, this.bet_type.MIX_GOAL].includes(attr_val)) {
					if (attr.DRAW_ODDS == '0') {
						return attr.LOSE_BALL_NUM + '=';
					}
					return `${attr.LOSE_BALL_NUM}(${DRAW_BUNKO}${attr.DRAW_ODDS})${body_attr}`;
				} else if ([this.bet_type.SINGLE_EVEN, this.bet_type.MIX_EVEN].includes(attr_val)) {
					str = attr.BET_TYPE == '1' ? this.$t('Odd') : this.$t('Even');
				} else if ([this.bet_type.SINGLE_CORRECT].includes(attr_val)) {
					str = attr.bet_type_info;
				} else if ([this.bet_type.SINGLE_BTTS].includes(attr_val)) {
					switch (attr.BET_TYPE) {
						case "1":
							str = "Both";
							break;
						case "2":
							str = "One";
							break;
						case "3":
							str = "No Goal";
							break;
					}
				} else if ([this.bet_type.SINGLE_WDL].includes(attr_val)) {
					let num_2_str = [, 'HOME', 'AWAY', 'DRAW']
					str = `1X2:${num_2_str[parseInt(attr.BET_TYPE)]}`
					str = attr.odds;
				} else {
					str = "";
				}
				if (attr.IS_MIX == 1) {
					str = Math.pow(2, attr.ORDER_COUNT);
				}
				return str;
			},
			status_color(status) {
				return status.indexOf('n') > -1 ? 'color:#60C07A' : 'color:#E52626'
			},
			// from tangjq--- 根据bet_status计算右上角徽章的显示文本与配色类型
			status_badge(status) {
				const map = {
					Pending: {
						label: 'PENDING',
						type: 'warn'
					},
					Win: {
						label: 'WIN',
						type: 'win'
					},
					Lose: {
						label: 'LOSE',
						type: 'lose'
					},
					Draw: {
						label: 'DRAW',
						type: 'neutral'
					},
					Cancel: {
						label: 'CANCEL',
						type: 'neutral'
					},
					Refund: {
						label: 'REFUND',
						type: 'warn'
					},
					Rejected: {
						label: 'REJECTED',
						type: 'lose'
					},
					HalfWin: {
						label: 'HALF WIN',
						type: 'win'
					},
					HalfLose: {
						label: 'HALF LOSE',
						type: 'lose'
					},
				}
				return map[status] || {
					label: String(status || '').toUpperCase(),
					type: 'neutral'
				}
			},
			parse_time(order) {
				// 先进行时区转换：从系统时区 (UTC+8) 转到用户时区
				const convertedTime = dateFormatUtils.convertTimezone(order.CREATE_TIME);
				// 将转换后的 YYYY-MM-DD HH:MM:SS 解析为 Date 对象
				const date = dateFormatUtils.stringToDate(convertedTime);

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
			}
		},
		mounted() {
			this.date_range = [this.getCurrentDate(0), this.getCurrentDate(0)]
			this.parse_option_list()
			this.get_list()
		},
		created() {}
	}
</script>

<style scoped lang="scss">
	/* from tangjq--- header占位元素样式 */
	.header-placeholder {
		height: 255px;
		background:
			radial-gradient(circle at 100% 0%, #36BCCB 0%, #1F879B 34%, rgba(31, 135, 155, 0) 68%),
			linear-gradient(135deg, #02455F 0%, #02455F 56%, #1F879B 100%);
		background-size: 100% 552px;
		background-position: center -255px;
		width: 100%;
		flex-shrink: 0;
	}

	page {
		background: #1C667C;
		height: 100vh;
		overflow: hidden;
	}

	.full-page {
		height: 100vh;
		background: #02455F;
		overflow: hidden;
		display: flex;
		flex-direction: column;
	}

	.title-bar {
		background: #fff;
		border-radius: 20px 20px 0 0;
		flex-shrink: 0;
	}

	/* Tab 样式 */
	.tab-selector {
		width: 100%;
		background: #fff;
		border-radius: 20px 20px 0 0;
	}

	.tab-container {
		position: relative;
		display: flex;
		align-items: center;
		justify-content: space-between;
		border-bottom: 1px solid #d9d9d9;
	}

	.tab-item {
		display: flex;
		align-items: center;
		cursor: pointer;
		height: 30px;
		padding: 0 10px;
	}

	.tab-text {
		font-size: 16px;
		color: #5a7a8f;
		transition: color 0.25s ease;
		font-weight: 400;
	}

	.tab-item.active .tab-text {
		color: #4fb3bf;
	}

	.slide-indicator {
		position: absolute;
		bottom: 0;
		left: 10px;
		height: 1px;
		background: #4fb3bf;
		border-radius: 2px;
		transition: all 0.3s cubic-bezier(0.4, 0.0, 0.2, 1);
		width: 60px;
	}

	.slide-indicator.indicator-finished {
		left: auto;
		right: 10px;
	}

	.main-scroll-view {
		flex: 1;
		height: 0;
		background: #fff;
	}

	.history-container {
		padding: 10px 15px;
		background: #ffffff;
	}

	.history-item {
		margin-bottom: 32upx;
	}

	/* 投注卡片 */
	.bet-card {
		background: #FFFFFF;
		border-radius: 15px;
		overflow: hidden;
		box-shadow: 0 4upx 12upx rgba(0, 0, 0, 0.08);
	}

	/* 卡片头部 */
	.card-header {
		background: #1C667C;
		padding: 5px;
		display: flex;
		flex-direction: column;
		align-items: center;
		position: relative;
		overflow: hidden;
	}

	/* from tangjq--- 横向布局的比赛信息 */
	.header-match {
		display: flex;
		flex-direction: row;
		align-items: center;
		justify-content: center;
		width: 100%;
		flex-wrap: wrap;
	}

	.team-name {
		font-size: 12px;
		color: #FFFFFF;
		font-weight: 600;
		text-align: center;
		flex-shrink: 1;
	}

	/* 让球方（odd given team）球队名称显示为红色 */
	.team-give {
		color: #FF4D4F !important;
	}

	/* from tangjq--- 主队名称使用青绿色 */
	.header-match .team-name:first-child {
		color: #5FB5BD;
		min-width: 0;
	}

	.vs-text {
		font-size: 28upx;
		color: #FFFFFF;
		font-weight: 700;
		margin: 0 16upx;
		flex-shrink: 0;
	}

	.score-text {
		font-size: 32upx;
		color: #FFFFFF;
		font-weight: 700;
		margin: 0 16upx;
		flex-shrink: 0;
	}

	.match-time {
		font-size: 20upx;
		color: rgba(255, 255, 255, 0.8);
		margin-bottom: 8upx;
		text-align: center;
	}

	/* 卡片内容 */
	.card-content {
		padding: 20upx 28upx;
	}

	.info-row {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 20upx;
	}

	.info-row:last-child {
		margin-bottom: 0;
	}

	.label {
		font-size: 24upx;
		color: #1C667C;
		font-weight: 400;
	}

	.value {
		font-size: 24upx;
		color: #263238;
		font-weight: 600;
		text-align: right;
	}

	.value-amount {
		color: #2A6268;
		font-weight: 700;
	}

	/* from tangjq--- 卡片右上角的输赢状态徽章（圆形 + 倾斜字体） */
	.status-badge {
		position: absolute;
		top: -10upx;
		right: -6upx;
		width: 72upx;
		height: 72upx;
		border-radius: 50%;
		z-index: 2;
		display: flex;
		align-items: center;
		justify-content: center;
		box-shadow: 0 4upx 12upx rgba(0, 0, 0, 0.25);
		transform: rotate(8deg);
	}

	.status-badge-text {
		font-size: 18upx;
		color: #FFFFFF;
		font-weight: 800;
		font-style: italic;
		letter-spacing: 0upx;
		line-height: 1;
		text-align: center;
		text-shadow: 0 1upx 2upx rgba(0, 0, 0, 0.2);
		white-space: nowrap;
	}

	.badge-win {
		background: radial-gradient(circle at 35% 35%, #6FE8D4 0%, #2CB5A0 60%, #1A8A7A 100%);
	}

	.badge-lose {
		background: radial-gradient(circle at 35% 35%, #F07070 0%, #D32F2F 60%, #A51D1D 100%);
	}

	.badge-neutral {
		background: radial-gradient(circle at 35% 35%, #B0BEC5 0%, #607D8B 60%, #3D5A66 100%);
	}

	.badge-warn {
		background: radial-gradient(circle at 35% 35%, #FFB74D 0%, #F57C00 60%, #C56000 100%);
	}

	/* 结算状态条 */
	.result-bar {
		padding: 5upx;
		margin: 10upx;
		text-align: center;
	}

	/* from tangjq--- 单笔投注的result-bar四个角都圆角 */
	.bet-card:not(.parlay-card) .result-bar {
		border-radius: 15px;
	}

	.result-win {
		background: linear-gradient(90deg, #4DBFBF 0%, #5DD5D5 100%);
		border-radius: 15px;
	}

	.result-lose {
		background: linear-gradient(90deg, #E74C3C 0%, #EC7063 100%);
		border-radius: 15px;
	}

	.result-text {
		font-size: 28upx;
		color: #FFFFFF;
		font-weight: 700;
		letter-spacing: 1upx;
	}

	/* Parlay 特殊样式 */
	.parlay-card {
		/* Parlay卡片的额外样式 */
	}

	/* from tangjq--- Parlay汇总信息，与上方内容连接 */
	.parlay-summary {
		padding: 10px 15px;
		background: #FFFFFF;
	}

	.parlay-toggle {
		display: flex;
		justify-content: center;
		align-items: center;
		padding: 5upx;
		background: #edfffe;
		border-top: 2upx solid #E0E0E0;
		cursor: pointer;
		/* from tangjq--- Parlay的parlay-toggle左下右下圆角 */
		border-radius: 0 0 15px 15px;
	}

	.parlay-label {
		font-size: 28upx;
		color: #2A6268;
		font-weight: 600;
		/* from tangjq--- 文字左右两侧留出箭头间距 */
		margin: 0 16upx;
	}

	.toggle-icon {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
	}

	/* from tangjq--- 细双箭头图标：两个细箭头(cuIcon)上下紧凑堆叠 */
	.toggle-icon .arrow {
		font-size: 22upx;
		line-height: 0.55;
		color: #2A6268;
		font-weight: bold;
	}

	/* 分隔线 */
	.divider {
		height: 2upx;
		background: #E0E0E0;
		margin: 24upx 0 0;
	}

	/* 旧样式保留（以防某些组件仍在使用） */
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
	}

	.page-text {
		margin-right: 15upx;
		padding: 10upx 13upx;
		line-height: 1;
	}
</style>