<template name="orders">
	<view class="full-page">
		<zw-header @headerHeightChange="onHeaderHeightChange"></zw-header>

		<!-- from tangjq--- header占位元素，防止内容被遮挡 -->
		<view class="header-placeholder" :style="{ height: headerHeight + 'px' }"></view>

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
			<view class="order-filter">
				<view class="order-filter-pill order-filter-calendar-pill">
					<view class="date-filter-trigger" :class="{ 'date-filter-selected': date_filtered }"
						@click="$refs.date_picker.show()">
						<image v-if="!date_filtered" class="order-filter-calendar"
							src="/static/image/order/calender.svg" mode="aspectFit"></image>
						<text
							class="calendar-text">{{date_preset || (date_range[0].show + ' - ' + date_range[1].show)}}</text>
						<text v-if="!date_filtered" class="cuIcon-unfold pill-arrow"></text>
					</view>
					<date-range-picker ref="date_picker" :inline="true" @click_option="date_click"></date-range-picker>
				</view>
				<view class="order-filter-pill">
					<selector :option_list.sync="type_list" :default_label="$t('type')" @click_option="click_option">
					</selector>
				</view>
				<view class="order-filter-pill">
					<selector :option_list.sync="status_list" :default_label="$t('status')"
						@click_option="click_option"></selector>
				</view>
				<view class="order-filter-pill">
					<selector :option_list.sync="wallet_list" :default_label="$t('wallet')"
						@click_option="click_option"></selector>
				</view>
			</view>
		</view>

		<view class="bg-white">
			<view class="promotion-tab-selector">
				<view class="promotion-tab-container">
					<view class="promotion-tab-item" :class="{'active':current_page==='pending'}"
						@click="page_change('pending')">
						<text class="promotion-tab-text">{{$t('pending')}}</text>
					</view>
					<view class="promotion-tab-item" :class="{'active':current_page==='Finished'}"
						@click="page_change('Finished')">
						<text class="promotion-tab-text">{{$t('Finished')}}</text>
					</view>

					<!-- from tangjq--- 底部滑动指示器 -->
					<view class="promotion-slide-indicator" :class="{'indicator-finished': current_page==='Finished'}">
					</view>
				</view>
			</view>
		</view>

		<scroll-view scroll-y class="main-scroll-view" @scroll="handleHeaderScroll" @scrolltoupper="handleHeaderTop">
			<view class="history-container">
				<view v-for="(item,index) in history_list" :key='index' class="history-item">
					<!-- 单笔投注 -->
					<view class="bet-card" v-if="item.IS_MIX == '0' || item.IS_MIX === false">
						<!-- 卡片头部 -->
						<view class="card-header">
							<view class="user-label-badge" :class="getWalletBadgeClass(item.pay_wallet)"
								v-if="item.pay_wallet">
								<text class="user-label-text">{{getWalletBadgeLabel(item.pay_wallet)}}</text>
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
								<text class="label">{{$t('total bet amount')}}
									<!-- <text v-if="item.pay_wallet">
										({{getWalletBadgeLabel(item.pay_wallet)}})</text> -->
								</text>
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
								v-if="item.benefit.indexOf('-') === -1 && item.benefit !== '\\'">WIN +{{item.benefit}}
								MMK</text>
							<text class="result-text" v-else-if="item.benefit === '\\'">CANCEL</text>
							<text class="result-text" v-else>LOSE {{item.benefit}} MMK</text>
						</view>
					</view>

					<!-- 混合投注 Parlay -->
					<view class="bet-card parlay-card" v-else>
						<view class="user-label-badge" :class="getWalletBadgeClass(item.pay_wallet)"
							v-if="item.pay_wallet">
							<text class="user-label-text">{{getWalletBadgeLabel(item.pay_wallet)}}</text>
						</view>

						<!-- Parlay 摘要，点击底部入口后在弹窗中查看全部比赛 -->
						<view class="card-header">
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
							<view class="info-row">
								<text class="label">{{$t('Type')}}</text>
								<text class="value">MixParlay</text>
							</view>
							<view class="info-row">
								<text class="label">{{$t('Odds')}}</text>
								<text class="value">{{item.real_odds}}</text>
							</view>
						</view>

						<!-- Parlay 底部汇总信息 -->
						<view class="parlay-summary">
							<view class="info-row">
								<text class="label">{{$t('total bet amount')}}
								</text>
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
								v-if="item.benefit.indexOf('-') === -1 && item.benefit !== '\\'">WIN +{{item.benefit}}
								MMK</text>
							<text class="result-text" v-else-if="item.benefit === '\\'">CANCEL</text>
							<text class="result-text" v-else>LOSE {{item.benefit}} MMK</text>
						</view>

						<!-- Parlay 折叠/展开按钮：文字左右两侧均显示细双箭头图标 -->
						<view class="parlay-toggle" @click="show_detail(item)">
							<view class="toggle-icon">
								<text class="arrow cuIcon-unfold"></text>
								<text class="arrow cuIcon-unfold"></text>
							</view>
							<text class="parlay-label">{{$t('mixparlay')}} {{item.ORDER_COUNT}} x 1</text>
							<view class="toggle-icon">
								<text class="arrow cuIcon-unfold"></text>
								<text class="arrow cuIcon-unfold"></text>
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
						style="background-color: var(--theme-primary);color: white;">
						<image src="/static/image/order/new_bet.svg" class="width-8vw height-8vw margin-right-sm">
						</image>
						{{$t('Place Bet')}}
					</button>
				</view>
			</view>
		</scroll-view>

		<!-- Parlay 详情弹窗 -->
		<view class="parlay-detail-modal" v-if="show_parlay_modal">
			<view class="parlay-detail-mask" @click="close_parlay_detail"></view>
			<view class="parlay-detail-dialog" @click.stop="">
				<text class="parlay-detail-title"></text>

				<scroll-view scroll-y class="parlay-detail-scroll" v-if="parlay_modal_order">
					<view class="parlay-match-detail-card"
						v-for="(detail, detailIndex) in get_parlay_details(parlay_modal_order)" :key="detailIndex">
						<text class="parlay-match-date">{{format_parlay_match_time(detail)}}</text>
						<view class="parlay-match-score-row">
							<text class="parlay-match-team parlay-match-team-home"
								:class="{ 'team-give': give_team_side(detail) === 'H' }">
								{{detail.HOME}}
							</text>
							<text class="parlay-match-score" v-if="current_page === 'pending'">VS</text>
							<text class="parlay-match-score" v-else>{{detail.SCORE}}</text>
							<text class="parlay-match-team parlay-match-team-away"
								:class="{ 'team-give': give_team_side(detail) === 'A' }">
								{{detail.AWAY}}
							</text>
						</view>

						<view class="parlay-detail-info">
							<view class="parlay-detail-info-row">
								<text class="parlay-detail-label">{{$t('Bet Time')}}</text>
								<text class="parlay-detail-value">{{detail.order_time}}</text>
							</view>
							<view class="parlay-detail-info-row">
								<text class="parlay-detail-label">{{$t('Type')}}</text>
								<text class="parlay-detail-value">{{detail.show_order_type}}</text>
							</view>
							<view class="parlay-detail-info-row">
								<text class="parlay-detail-label">{{$t('Bet')}}</text>
								<text class="parlay-detail-value">{{detail.team_name}}</text>
							</view>
							<view class="parlay-detail-info-row">
								<text class="parlay-detail-label">{{$t('Odds')}}</text>
								<text class="parlay-detail-value">{{detail.real_odds}}</text>
							</view>
						</view>
					</view>
					<view class="padding-bottom-1px"></view>
				</scroll-view>

				<view class="parlay-detail-summary" v-if="parlay_modal_order">
					<view class="parlay-summary-row">
						<text class="parlay-summary-label">{{$t('total bet amount')}}
							<text v-if="parlay_modal_order.pay_wallet">
								({{getWalletBadgeLabel(parlay_modal_order.pay_wallet)}})</text>
						</text>
						<text class="parlay-summary-value">
							{{$toolbox.num_format(parlay_modal_order.BET_MONEY,0)}} MMK
						</text>
					</view>
					<view class="parlay-summary-row">
						<text class="parlay-summary-label">{{$t('Total Match')}}</text>
						<text class="parlay-summary-value">{{parlay_modal_order.ORDER_COUNT}}</text>
					</view>
					<view class="parlay-summary-row" v-if="current_page === 'pending'">
						<text class="parlay-summary-label">{{$t('Potential Win Amount')}}</text>
						<text class="parlay-summary-value">
							{{parlay_modal_order.benefit}} MMK
						</text>
					</view>
					<view class="result-bar" v-if="current_page === 'Finished'"
						:class="{'result-win':parlay_modal_order.benefit.indexOf('-') === -1 && parlay_modal_order.benefit !== '\\', 'result-lose':parlay_modal_order.benefit.indexOf('-') > -1 || parlay_modal_order.benefit === '\\'}">
						<text class="result-text"
							v-if="parlay_modal_order.benefit.indexOf('-') === -1 && parlay_modal_order.benefit !== '\\'">
							WIN +{{parlay_modal_order.benefit}} MMK
						</text>
						<text class="result-text" v-else-if="parlay_modal_order.benefit === '\\'">CANCEL</text>
						<text class="result-text" v-else>LOSE {{parlay_modal_order.benefit}} MMK</text>
					</view>
				</view>

				<view class="parlay-detail-actions">
					<view class="parlay-confirm-button" @click="close_parlay_detail">
						<text>{{$t('Confirm')}}</text>
					</view>
					<view class="parlay-download-button" data-html2canvas-ignore="true"
						:class="{ 'is-downloading': downloading_slip }"
						@click="download_parlay_slip">
						<image class="parlay-download-icon" src="/static/icon/download-slip.svg" mode="aspectFit">
						</image>
						<text>{{$t('Download Slip')}}</text>
					</view>
				</view>
			</view>
			<view class="parlay-export-mask" v-if="downloading_slip" data-html2canvas-ignore="true">
				<view class="parlay-export-status">
					<view class="parlay-export-spinner"></view>
					<text class="parlay-export-text">Generating...</text>
				</view>
			</view>
		</view>

		<!-- 所有平台都保留图片预览，用户可长按保存 -->
		<view class="parlay-slip-preview-modal" v-if="slip_preview_src">
			<view class="parlay-detail-mask" @click="close_slip_preview"></view>
			<view class="parlay-slip-preview-dialog" @click.stop="">
				<text class="parlay-slip-preview-title">{{$t('Download Slip')}}</text>
				<scroll-view class="parlay-slip-preview-scroll" scroll-y>
					<!-- #ifdef H5 -->
					<img class="parlay-slip-preview-image" :src="slip_preview_src" alt="Bet slip"
						draggable="true">
					<!-- #endif -->
					<!-- #ifndef H5 -->
					<image class="parlay-slip-preview-image" :src="slip_preview_src" mode="widthFix"></image>
					<!-- #endif -->
				</scroll-view>
				<text class="parlay-slip-preview-tip">{{$t('save_slip_instruction')}}</text>
				<view class="parlay-slip-preview-share" v-if="can_share_slip"
					:class="{ 'is-sharing': sharing_slip }" @click="share_slip_preview">
					<text>{{$t('share')}}</text>
				</view>
				<view class="parlay-slip-preview-actions">
					<view class="parlay-confirm-button parlay-download-confirm-button"
						@click="download_slip_preview">
						<text>{{$t('Download')}}</text>
					</view>
					<view class="parlay-confirm-button" @click="close_slip_preview">
						<text>{{$t('Confirm')}}</text>
					</view>
				</view>
			</view>
		</view>

	</view>
</template>

<script>
	import Vue from 'vue';
	import config from '../../utils/config.js';
	import dateFormatUtils from "../../utils/utils.js";
	import Selector from '../../components/common/selector.vue'
	import match_mixins from '../match/components/mixins.js'
	import headerCollapse from '@/mixins/headerCollapse.js'


	export default {
		name: 'orders',
		components: {
			Selector,
		},
		mixins: [match_mixins, headerCollapse],
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
				date_preset: '', // from tangjq--- 当前选中的日期预设 label（如 Today / Yesterday / Weekly 等），为空时回退到 date_range 拼接
				date_filtered: false,
				send_date: true,
				report: {
					all_stake: 0,
					win: 0,
					loss: 0,
				},
				show_parlay_modal: false,
				parlay_modal_order: null,
				downloading_slip: false,
				slip_preview_src: '',
				slip_preview_blob: null,
				slip_preview_filename: '',
				sharing_slip: false,
			};
		},
		computed: {
			can_share_slip() {
				return typeof navigator !== 'undefined' &&
					typeof File !== 'undefined' &&
					typeof navigator.share === 'function'
			},
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
			date_click(arr, presetLabel) {
				// from tangjq--- 优先使用预设 label；presetLabel 为空时回退到日期范围拼接
				this.date_preset = presetLabel || ''
				this.date_range = arr
				this.date_filtered = presetLabel !== this.$t('today')
				if (this.date_range[0].value === '0000-00-00' || this.date_range[1].value === '0000-00-00') {
					this.send_date = false
					this.date_preset = ''
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
					this.parlay_modal_order = row
					this.show_parlay_modal = true
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
						let items = res.data.items || []
						items.forEach(ele => {
							row.detail.push(_this.parse_order(ele))
						})
						_this.parlay_modal_order = row
						_this.show_parlay_modal = true
					}
				})
			},
			close_parlay_detail() {
				this.show_parlay_modal = false
				this.parlay_modal_order = null
			},
			load_html2canvas() {
				if (typeof window === 'undefined' || typeof document === 'undefined') {
					return Promise.reject(new Error('Image export requires a browser environment'))
				}
				if (window.html2canvas) {
					return Promise.resolve(window.html2canvas)
				}
				if (this._html2canvas_promise) {
					return this._html2canvas_promise
				}

				this._html2canvas_promise = new Promise((resolve, reject) => {
					const script = document.createElement('script')
					script.src = '/static/vendor/html2canvas.min.js'
					script.async = true
					script.onload = () => {
						if (window.html2canvas) {
							resolve(window.html2canvas)
						} else {
							reject(new Error('Image export library is unavailable'))
						}
					}
					script.onerror = () => reject(new Error('Image export library failed to load'))
					document.head.appendChild(script)
				})
				return this._html2canvas_promise
			},
			wait_for_slip_render() {
				return new Promise((resolve) => {
					const requestFrame = window.requestAnimationFrame || ((callback) => setTimeout(callback, 0))
					requestFrame(() => requestFrame(resolve))
				})
			},
			canvas_to_blob(canvas) {
				return new Promise((resolve, reject) => {
					if (!canvas || typeof canvas.toBlob !== 'function') {
						reject(new Error('Canvas blob export is unavailable'))
						return
					}
					canvas.toBlob((blob) => {
						if (blob) {
							resolve(blob)
							return
						}
						reject(new Error('Canvas blob export failed'))
					}, 'image/png')
				})
			},
			blob_to_data_url(blob) {
				return new Promise((resolve, reject) => {
					if (!blob || typeof FileReader === 'undefined') {
						reject(new Error('Data URL preview is unavailable'))
						return
					}

					const reader = new FileReader()
					reader.onload = () => {
						if (typeof reader.result === 'string' && reader.result) {
							resolve(reader.result)
							return
						}
						reject(new Error('Data URL preview generation failed'))
					}
					reader.onerror = () => reject(
						reader.error || new Error('Data URL preview generation failed')
					)
					reader.readAsDataURL(blob)
				})
			},
			is_ios_browser() {
				const userAgent = navigator.userAgent || ''
				return /iPad|iPhone|iPod/.test(userAgent) ||
					(navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1)
			},
			get_parlay_slip_filename() {
				const orderId = String(
					(this.parlay_modal_order && (
						this.parlay_modal_order.ORDER_ID || this.parlay_modal_order.ID
					)) || 'slip'
				).replace(/[^\w-]+/g, '_')
				return `bet-slip-${orderId}.png`
			},
			open_slip_preview(dataUrl, blob, filename) {
				this.close_slip_preview()
				this.slip_preview_blob = blob
				this.slip_preview_filename = filename
				this.slip_preview_src = dataUrl
			},
			close_slip_preview() {
				this.slip_preview_src = ''
				this.slip_preview_blob = null
				this.slip_preview_filename = ''
			},
			download_slip_blob(blob, filename, showToast = true) {
				const objectUrl = URL.createObjectURL(blob)
				const link = document.createElement('a')
				link.href = objectUrl
				link.download = filename
				document.body.appendChild(link)
				link.click()
				document.body.removeChild(link)
				setTimeout(() => URL.revokeObjectURL(objectUrl), 1000)
				if (showToast) {
					uni.showToast({
						title: 'Download started',
						icon: 'success'
					})
				}
			},
			download_slip_preview() {
				if (!this.slip_preview_blob) return
				this.download_slip_blob(
					this.slip_preview_blob,
					this.slip_preview_filename || this.get_parlay_slip_filename()
				)
			},
			share_slip_blob(blob, filename, showToast = true) {
				if (!blob || !this.can_share_slip) {
					return Promise.resolve(false)
				}

				try {
					const file = new File([blob], filename, {
						type: 'image/png'
					})
					if (typeof navigator.canShare === 'function' &&
						!navigator.canShare({ files: [file] })) {
						return Promise.resolve(false)
					}
					return navigator.share({
						title: filename,
						files: [file]
					}).then(() => {
						if (showToast) {
							uni.showToast({
								title: 'Share completed',
								icon: 'success'
							})
						}
						return true
					}).catch((error) => {
						if (error && error.name !== 'AbortError') {
							console.warn('Share slip failed:', error)
						}
						return false
					})
				} catch (error) {
					console.warn('File sharing is unavailable:', error)
					return Promise.resolve(false)
				}
			},
			share_slip_preview() {
				if (this.sharing_slip || !this.slip_preview_blob) return
				if (!this.can_share_slip) {
					uni.showToast({
						title: this.$t('share_not_supported'),
						icon: 'none'
					})
					return
				}

				this.sharing_slip = true
				this.share_slip_blob(
					this.slip_preview_blob,
					this.slip_preview_filename || this.get_parlay_slip_filename()
				).then((shared) => {
					if (!shared) {
						uni.showToast({
							title: this.$t('share_not_supported'),
							icon: 'none'
						})
					}
					this.sharing_slip = false
				})
			},
			save_parlay_canvas(canvas) {
				return this.canvas_to_blob(canvas).then(async (blob) => {
					const filename = this.get_parlay_slip_filename()
					// Use a data URL for the preview and keep the Blob for download/share.
					const previewDataUrl = await this.blob_to_data_url(blob)
					this.close_parlay_detail()
					this.open_slip_preview(previewDataUrl, blob, filename)
					await this.$nextTick()
					await this.wait_for_slip_render()
					if (this.is_ios_browser()) {
						// Try both automatic download and system sharing; the preview remains available.
						this.download_slip_blob(blob, filename, false)
						this.share_slip_blob(blob, filename, false)
						return
					}

					this.download_slip_blob(blob, filename)
				})
			},
			download_parlay_slip() {
				if (this.downloading_slip || !this.parlay_modal_order) return
				if (typeof window === 'undefined' || typeof document === 'undefined') {
					uni.showToast({
						title: 'Download is not supported',
						icon: 'none'
					})
					return
				}

				this.downloading_slip = true
				uni.showLoading({
					title: 'Generating...',
					mask: true
				})

				let styleSnapshots = []
				let scrollTop = 0
				this.load_html2canvas()
					.then((html2canvas) => {
						return this.$nextTick().then(() => {
							const dialog = document.querySelector('.parlay-detail-dialog')
							const scrollElement = dialog && dialog.querySelector('.parlay-detail-scroll')
							if (!dialog || !scrollElement) {
								throw new Error('Parlay slip element is unavailable')
							}

							const scrollElements = [
								scrollElement,
								...Array.from(scrollElement.querySelectorAll(
									'.uni-scroll-view, .uni-scroll-view-content'))
							]
							const elementsToResize = [dialog, ...scrollElements]
							styleSnapshots = elementsToResize.map((element) => ({
								element,
								cssText: element.style.cssText
							}))
							scrollTop = scrollElement.scrollTop

							dialog.style.height = 'auto'
							dialog.style.maxHeight = 'none'
							dialog.style.overflow = 'visible'
							scrollElements.forEach((element) => {
								element.style.flex = 'none'
								element.style.height = 'auto'
								element.style.minHeight = '0'
								element.style.maxHeight = 'none'
								element.style.overflow = 'visible'
								element.style.overflowY = 'visible'
							})
							scrollElement.scrollTop = 0

							return this.wait_for_slip_render().then(() => html2canvas(dialog, {
								backgroundColor: '#ffffff',
								allowTaint: false,
								logging: false,
								scale: Math.max(1, Math.min(2, window.devicePixelRatio || 1)),
								useCORS: true,
								scrollX: 0,
								scrollY: 0
							}))
						})
					})
					.then((canvas) => this.save_parlay_canvas(canvas))
					.catch((error) => {
						console.error('Download slip failed:', error)
						uni.showToast({
							title: 'Download failed',
							icon: 'none'
						})
					})
					.then(() => {
						styleSnapshots.reverse().forEach((snapshot) => {
							snapshot.element.style.cssText = snapshot.cssText
						})
						const scrollElement = document.querySelector('.parlay-detail-scroll')
						if (scrollElement) {
							scrollElement.scrollTop = scrollTop
						}
						uni.hideLoading()
						this.downloading_slip = false
					})
			},
			get_parlay_details(order) {
				if (!order) return []
				return Array.isArray(order.detail) && order.detail.length ? order.detail : [order]
			},
			format_parlay_match_time(detail) {
				const value = detail && (detail.MATCH_TIME || detail.match_time)
				if (!value) return detail && detail.order_time ? detail.order_time : ''

				const match = String(value).replace('T', ' ').match(
					/^(\d{4})-(\d{2})-(\d{2})\s+(\d{2}):(\d{2})/
				)
				if (!match) return value

				const hour = parseInt(match[4], 10)
				const ampm = hour >= 12 ? 'PM' : 'AM'
				const displayHour = hour % 12 || 12
				return `${match[3]}.${match[2]}.${match[1]} ${String(displayHour).padStart(2, '0')}:${match[5]} ${ampm}`
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
			// from tangjq--- 卡片右上角钱包徽章：Money→Main Wallet，Promotion→Promo Wallet
			getWalletBadgeLabel(payWallet) {
				if (!payWallet) return ''
				const w = String(payWallet).toLowerCase()
				if (w === 'money' || w === 'main' || w === 'main wallet') return 'Main Wallet'
				if (w === 'promotion' || w === 'promo' || w === 'promo wallet') return 'Promo Wallet'
				return payWallet
			},
			// from tangjq--- 卡片右上角钱包徽章：返回颜色类名 badge-main / badge-promo
			getWalletBadgeClass(payWallet) {
				if (!payWallet) return 'badge-main'
				const w = String(payWallet).toLowerCase()
				if (w === 'promotion' || w === 'promo' || w === 'promo wallet') return 'badge-promo'
				return 'badge-main'
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
			// from tangjq--- 初始化时默认选中 today 预设
			this.date_preset = this.$t('today')
			this.parse_option_list()
			this.get_list()
		},
		beforeDestroy() {
			this.close_slip_preview()
		},
		created() {}
	}
</script>

<style scoped lang="scss">
	/* from tangjq--- header占位元素样式 */
	.header-placeholder {
		height: 255px;
		width: 100%;
		flex-shrink: 0;
		transition: height 0.3s ease;
	}

	page {
		height: var(--app-viewport-height, 100vh);
		overflow: hidden;
	}

	.full-page {
		height: var(--app-viewport-height, 100vh);
		overflow: hidden;
		display: flex;
		flex-direction: column;
	}

	.title-bar {
		background: #fff;
		border-radius: 20px 20px 0 0;
		flex-shrink: 0;
		padding: 0 15px;
	}

	.order-filter {
		display: flex;
		flex-wrap: nowrap;
		align-items: center;
		justify-content: space-between;
		background-color: #ffffff;
		// border-radius: 0 0 16px 16px;
		gap: 5px;
		// border-bottom: 1upx solid #eef2f4;
	}

	/* from tangjq--- 参考 History_Finished.png：4 个青绿色填充的胶囊按钮排在同一行 */
	.order-filter-pill {
		display: flex;
		align-items: center;
		justify-content: center;
		position: relative;
		min-width: 0;
		gap: 6upx;
		padding: 0 0;
		height: 56upx;
		border: none;
		border-radius: 999upx;
		background: $color-primary;
		color: #FFFFFF;
		cursor: pointer;
		flex: 1 1 0;
	}

	.order-filter-calendar-pill {
		padding: 0;
		overflow: visible;
	}

	.date-filter-trigger {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 100%;
		min-width: 0;
		height: 100%;
		padding: 0 10upx;
		box-sizing: border-box;
	}

	.order-filter-calendar {
		width: 30upx;
		height: 30upx;
		flex-shrink: 0;
	}

	/* from tangjq--- 日历胶囊内的日期/预设文本，宽度不够时省略号 */
	.calendar-text {
		// flex: 1;
		min-width: 0;
		font-size: 22upx;
		font-weight: bold;
		color: #FFFFFF;
		line-height: 32upx;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
		text-align: left;
	}

	.date-filter-selected .calendar-text {
		flex: 0 1 auto;
		text-align: center;
	}

	.pill-arrow {
		color: #FFFFFF;
		font-size: 22upx;
		margin-left: 2upx;
		flex-shrink: 0;
	}

	/* 让 selector 在 pill 内部显示为白字 + 白箭头（用 ::v-deep 穿透 scoped） */
	/* from tangjq--- 让 selector-wrapper 占满整个 pill 宽度，使下拉面板（.selector-bg 用 left:0）和 pill 左对齐 */
	.order-filter-pill ::v-deep .selector-wrapper {
		width: 100%;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.order-filter-pill ::v-deep .selector-tag {
		height: auto;
		line-height: 32upx;
		padding: 0;
		border: none;
		border-radius: 0;
		background-color: transparent !important;
		color: #FFFFFF !important;
		font-size: 22upx;
		font-weight: bold;
		gap: 4upx;
		justify-content: center;
	}

	.order-filter-pill ::v-deep .selector-tag text {
		color: #FFFFFF;
		font-size: 22upx;
		font-weight: 600;
	}

	.order-filter-pill ::v-deep .selector-tag .cuIcon-unfold,
	.order-filter-pill ::v-deep .selector-tag .cuIcon-fold {
		color: #FFFFFF;
		font-size: 20upx;
		margin-left: 2upx;
	}

	/* Tab 样式 */
	.promotion-tab-selector {
		width: 100%;
		background: #fff;
		margin-bottom: 8px;
		padding: 0 15px;
	}

	.promotion-tab-container {
		position: relative;
		display: flex;
		align-items: center;
		border-bottom: 1px solid #d9d9d9;
	}

	.promotion-tab-item {
		flex: 1;
		display: flex;
		align-items: center;
		justify-content: center;
		height: 38px;
	}

	.promotion-tab-text {
		font-size: 15px;
		color: $color-primary;
		transition: color 0.25s ease;
	}

	.promotion-tab-item.active .promotion-tab-text {
		color: $color-secondary;
		font-weight: 600;
	}

	.promotion-slide-indicator {
		position: absolute;
		bottom: 0;
		left: 0;
		height: 2px;
		width: 50%;
		background: $color-secondary;
		border-radius: 2px;
		transition: all 0.3s cubic-bezier(0.4, 0.0, 0.2, 1);
	}

	.promotion-slide-indicator.indicator-finished {
		transform: translateX(100%);
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
		box-shadow: 0px 2px 2px 0px var(--theme-primary-alpha-20, rgba(28, 102, 124, .2));
		border: 1px solid $color-border;
	}

	/* 卡片头部 */
	.card-header {
		background: $color-primary;
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
		flex-wrap: nowrap;
	}

	.team-name {
		font-size: 12px;
		color: #FFFFFF;
		font-weight: 600;
		text-align: center;
		flex: 1 1 0;
		min-width: 0;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	/* 让球方（odd given team）球队名称显示为红色 */
	.team-give {
		color: #FF4D4F !important;
	}

	/* from tangjq--- 主队名称使用青绿色 */
	.header-match .team-name:first-child {
		color: $color-secondary;
	}

	.vs-text {
		font-size: 28upx;
		color: #FFFFFF;
		font-weight: 700;
		margin: 0 16upx;
		flex: 0 0 auto;
		text-align: center;
	}

	.score-text {
		font-size: 32upx;
		color: #FFFFFF;
		font-weight: 700;
		margin: 0 16upx;
		flex: 0 0 auto;
		text-align: center;
	}

	.match-time {
		font-size: 20upx;
		color: rgba(255, 255, 255, 0.8);
		// margin-bottom: 8upx;
		text-align: center;
	}

	/* 卡片内容 */
	.card-content {
		padding: 10upx 28upx 0;
	}

	.info-row {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 10upx;
	}

	.info-row:last-child {
		margin-bottom: 0;
	}

	.label {
		font-size: 24upx;
		color: $color-primary;
		font-weight: 400;
	}

	.value {
		font-size: 24upx;
		color: #263238;
		font-weight: 600;
		text-align: right;
	}

	.value-amount {
		color: $color-primary;
		font-weight: 700;
	}

	/* 卡片右上角的钱包徽章（pay_wallet），参考 History_Finished.png：
	   Main Wallet = 白底深字 / Promo Wallet = 青绿底白字 */
	.user-label-badge {
		position: absolute;
		top: 0;
		right: 0;
		// max-width: 220upx;
		padding: 4upx 30upx;
		border-top-right-radius: 12px;
		border-bottom-left-radius: 12px;
		display: flex;
		align-items: center;
		justify-content: center;
		z-index: 2;
		color: white;
	}

	.user-label-badge.badge-main {
		background-color: var(--theme-page-background-color, #{$theme-page-start});
	}

	.user-label-badge.badge-promo {
		background-color: $color-secondary;
	}

	.user-label-text {
		max-width: 196upx;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
		font-size: 20upx;
		font-weight: 600;
		line-height: 30upx;
		text-align: center;
	}

	/* 结算状态条 */
	.result-bar {
		// padding: 5upx;
		margin: 10upx;
		text-align: center;
		font-style: italic;
	}

	/* from tangjq--- 单笔投注的result-bar四个角都圆角 */
	.bet-card:not(.parlay-card) .result-bar {
		border-radius: 15px;
	}

	.result-win {
		color: $color-secondary;
	}

	.result-lose {
		color: #FF5341;
	}

	.result-text {
		font-size: 24upx;
		font-weight: 700;
		letter-spacing: 1upx;
	}

	/* Parlay 特殊样式 */
	.parlay-card {
		position: relative;
	}

	/* from tangjq--- Parlay汇总信息，与上方内容连接 */
	.parlay-summary {
		padding: 5px 15px;
		background: #FFFFFF;
	}

	.parlay-toggle {
		display: flex;
		justify-content: center;
		align-items: center;
		background: $color-secondary-light;
		cursor: pointer;
		/* from tangjq--- Parlay的parlay-toggle左下右下圆角 */
		border-radius: 0 0 $radius-large $radius-large;
	}

	.parlay-label {
		font-size: 28upx;
		color: $color-primary;
		font-weight: bold;
		/* from tangjq--- 文字左右两侧留出箭头间距 */
		margin: 0 16upx;
	}

	/* Parlay 详情弹窗 */
	.parlay-detail-modal {
		position: fixed;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		height: var(--app-viewport-height, 100vh);
		z-index: 2000;
		display: flex;
		align-items: center;
		justify-content: center;
		padding: 16px 10px;
		box-sizing: border-box;
	}

	.parlay-detail-mask {
		position: absolute;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		background: rgba(0, 0, 0, 0.45);
	}

	.parlay-detail-dialog {
		position: relative;
		z-index: 1;
		display: flex;
		flex-direction: column;
		width: 100%;
		max-width: 400px;
		height: 86%;
		max-height: calc(var(--app-viewport-height, 100vh) - 32px);
		min-height: 0;
		background: #ffffff;
		border: 8px solid $color-primary;
		border-radius: 22px;
		box-sizing: border-box;
		overflow: hidden;
	}

	.parlay-detail-title {
		display: block;
		flex-shrink: 0;
		padding: 11px 10px 9px;
		color: $color-primary;
		font-size: 18px;
		font-weight: 700;
		text-align: center;
	}

	.parlay-detail-title::after {
		content: var(--theme-title, "#{$theme-title-value}");
	}

	.parlay-detail-scroll {
		flex: 1 1 0%;
		height: 0;
		min-height: 0;
		padding: 0 12px;
		box-sizing: border-box;
		overflow-y: auto;
	}

	.parlay-match-detail-card {
		padding: 10px 10px 12px;
		margin-bottom: 12px;
		border: 1px solid $color-primary;
		border-radius: 8px;
		box-sizing: border-box;
	}

	.parlay-match-date {
		display: block;
		margin-bottom: 5px;
		color: $color-primary;
		font-size: 10px;
		line-height: 1.2;
		text-align: center;
	}

	.parlay-match-score-row {
		display: grid;
		grid-template-columns: minmax(0, 1fr) auto minmax(0, 1fr);
		align-items: center;
		gap: 8px;
		padding: 5px 8px;
		background: $bg-color-info;
		border-radius: 14px;
	}

	.parlay-match-team {
		min-width: 0;
		color: #263238;
		font-size: 13px;
		font-weight: 700;
		line-height: 1.2;
		white-space: normal;
		word-break: break-word;
	}

	.parlay-match-team-home {
		color: $color-secondary;
		text-align: center;
	}

	.parlay-match-team-away {
		text-align: center;
	}

	.parlay-match-score {
		color: $color-primary;
		font-size: 13px;
		font-weight: 700;
		white-space: nowrap;
	}

	.parlay-detail-info {
		padding: 10px 26px 0;
	}

	.parlay-detail-info-row,
	.parlay-summary-row {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 12px;
	}

	.parlay-detail-info-row {
		margin-bottom: 7px;
	}

	.parlay-detail-info-row:last-child {
		margin-bottom: 0;
	}

	.parlay-detail-label,
	.parlay-summary-label {
		min-width: 0;
		color: $color-primary;
		font-size: 12px;
		font-weight: 400;
		line-height: 1.25;
	}

	.parlay-detail-value,
	.parlay-summary-value {
		min-width: 0;
		color: $color-primary;
		font-size: 12px;
		font-weight: 700;
		line-height: 1.25;
		text-align: right;
		word-break: break-word;
	}

	.parlay-detail-summary {
		flex-shrink: 0;
		padding: 10px 15px 0;
		border-top: 1px solid $color-border;
	}

	.parlay-summary-row {
		margin-bottom: 9px;
	}

	.parlay-summary-row:last-of-type {
		margin-bottom: 0;
	}

	.parlay-summary-value {
		font-style: italic;
	}

	.parlay-detail-actions {
		flex-shrink: 0;
		padding: 12px 10px 8px;
		text-align: center;
	}

	.parlay-confirm-button {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 162px;
		height: 42px;
		margin: 0 auto;
		background: $color-primary;
		border-radius: 12px;
		color: #ffffff;
		font-size: 16px;
		font-weight: 700;
	}

	.parlay-download-button {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 8px;
		margin-top: 9px;
		color: $color-primary;
		font-size: 12px;
		font-weight: 600;
	}

	.parlay-download-icon {
		width: 15px;
		height: 14px;
		flex-shrink: 0;
	}

	.parlay-download-button.is-downloading {
		opacity: 0.55;
	}

	.parlay-export-mask {
		position: absolute;
		top: 0;
		right: 0;
		bottom: 0;
		left: 0;
		z-index: 3;
		display: flex;
		align-items: center;
		justify-content: center;
		background: rgba(11, 47, 57, 0.3);
	}

	.parlay-export-status {
		display: flex;
		align-items: center;
		gap: 10px;
		padding: 12px 16px;
		border-radius: 14px;
		background: rgba(255, 255, 255, 0.96);
		box-shadow: 0 4px 16px rgba(0, 0, 0, 0.16);
	}

	.parlay-export-spinner {
		width: 18px;
		height: 18px;
		border: 2px solid rgba(28, 102, 124, 0.24);
		border-top-color: $color-primary;
		border-radius: 50%;
		animation: parlay-export-spin 0.8s linear infinite;
	}

	.parlay-export-text {
		color: $color-primary;
		font-size: 13px;
		font-weight: 600;
	}

	.parlay-slip-preview-modal {
		position: fixed;
		top: 0;
		right: 0;
		bottom: 0;
		left: 0;
		height: var(--app-viewport-height, 100vh);
		z-index: 2100;
		display: flex;
		align-items: center;
		justify-content: center;
		padding: 16px 10px;
		box-sizing: border-box;
	}

	.parlay-slip-preview-dialog {
		position: relative;
		z-index: 1;
		display: flex;
		flex-direction: column;
		width: 100%;
		max-width: 400px;
		height: 86%;
		max-height: calc(var(--app-viewport-height, 100vh) - 32px);
		min-height: 0;
		background: #ffffff;
		border: 8px solid $color-primary;
		border-radius: 22px;
		box-sizing: border-box;
		overflow: hidden;
	}

	.parlay-slip-preview-title {
		display: block;
		flex-shrink: 0;
		padding: 11px 10px 9px;
		color: $color-primary;
		font-size: 18px;
		font-weight: 700;
		text-align: center;
	}

	.parlay-slip-preview-scroll {
		flex: 1 1 auto;
		height: auto;
		min-height: 1px;
		padding: 0 10px;
		background: #f7fafb;
		box-sizing: border-box;
		overflow-y: auto;
		-webkit-overflow-scrolling: touch;
	}

	.parlay-slip-preview-image {
		display: block;
		width: 100%;
		max-width: 100%;
		height: auto;
		-webkit-touch-callout: default;
		-webkit-user-select: auto;
		user-select: auto;
	}

	.parlay-slip-preview-tip {
		display: block;
		flex-shrink: 0;
		padding: 9px 12px 4px;
		color: $color-primary;
		font-size: 12px;
		line-height: 1.35;
		text-align: center;
	}

	.parlay-slip-preview-actions {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 12px;
		flex-shrink: 0;
		margin-bottom: 12px;
	}

	.parlay-slip-preview-actions .parlay-confirm-button {
		width: auto;
		flex: 1 1 0;
		max-width: 162px;
		margin: 0;
	}

	.parlay-download-confirm-button {
		background: $color-secondary;
	}

	.parlay-slip-preview-share {
		display: flex;
		align-items: center;
		justify-content: center;
		flex-shrink: 0;
		width: 162px;
		height: 36px;
		margin: 4px auto 8px;
		border: 1px solid $color-primary;
		border-radius: 12px;
		color: $color-primary;
		font-size: 14px;
		font-weight: 600;
	}

	.parlay-slip-preview-share.is-sharing {
		opacity: 0.55;
	}

	.parlay-slip-preview-dialog .parlay-confirm-button {
		flex-shrink: 0;
		margin: 0;
	}

	@keyframes parlay-export-spin {
		to {
			transform: rotate(360deg);
		}
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
		color: $color-primary;
		font-weight: bold;
	}

	/* 分隔线 */
	.divider {
		height: 2upx;
		background: #E0E0E0;
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