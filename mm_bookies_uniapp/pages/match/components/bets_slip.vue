<template>
	<scroll-view scroll-y class="dialog-wrapper mycolor-primary" v-show="!hidden" @tap.prevent="">
		<view style="background: none;">
			<view class="flex-row text-bold box-shadow padding bg-white mycolor-primary" @click="set_dialog_hide(true)"
				style="position: sticky;top: 0;overflow-y: overlay;z-index: 16;" v-if="mixed">
				<view class="cuIcon-back mycolor-info"></view>

				<view class="margin-left width-100">{{'Bets Slip'}}</view>
			</view>
			<view class="flex-column padding-xs text-bold bg-white mycolor-primary" v-if="mixed">
				<view class="flex-column box-shadow radius-6px margin-bottom-xs" v-for="(match,index) in match_list">
					<view class="padding-sm flex-column myfont-12px gap-5px">
						<view class="flex-row justify-between">
							<view class="text-red">{{match.HOST_TEAM}}</view>
							<view>{{bet_type.MIX_BODY == match.sa.MATCH_ATTR_TYPE ?'HANDICAP':'OU'}}</view>
						</view>
						<view class="flex-row justify-between">
							<view class="">{{match.GUEST_TEAM}}</view>
							<view class="">{{calc_real_odds(match.sa,'bn')}}<text
									class="text-red">{{calc_real_odds(match.sa,'bo')}}</text>{{calc_real_odds(match.sa,'ha')}}
							</view>
						</view>
						<view class="flex-row justify-between">
							<view>{{match.SLIP_DATE}}</view>
							<view></view>
						</view>
					</view>
					<view class="flex-row justify-between mybg-primary padding-sm radius-6px">
						<view
							class="cuIcon-deletefill round bg-white mycolor-primary myfont-10px width-20px height-18px line-height-18px">
						</view>
						<view class="flex-row justify-end">
							<text class="mycolor-active">{{bet_content(match)}}</text>
							<text class="text-white padding-left-sm">@2.00</text>
						</view>
					</view>
				</view>
			</view>
			<view v-if="!mixed" class="single-mask" @click="set_dialog_hide(true)"></view>
			<view class="text-bold flex-column" style="bottom: 0;overflow-y: overlay;z-index: 16;"
				:style="{'position':mixed?'sticky':'fixed'}">
				<view class="flex-column padding-xs single-bottom dialig-bottom" v-if="!mixed">
					<view class="margin-top-sm mybg-primary row-line"></view>
					<view class="flex-row gap-5px justify-center margin-tb-sm">
						<text class="text-red">{{match_ref.bet_match.HOST_TEAM}}</text>
						<text class="text-light">vs</text>
						<text>{{match_ref.bet_match.GUEST_TEAM}}</text>
					</view>
				</view>
				<view class="flex-column padding-xs dialig-bottom">
					<view class="flex-column box-shadow radius-6px margin-bottom-xs myfont-12px gap-5px padding-sm"
						v-if="mixed">
						<view class="flex-row justify-between">
							<view class="">Total Bet</view>
							<view class="">{{match_list.length}}</view>
						</view>
						<view class="flex-row justify-between">
							<view class="">Odds</view>
							<view class="">{{Math.pow(2,match_list.length)}}</view>
						</view>
					</view>
					<view
						class="flex-row justify-between box-shadow radius-6px margin-bottom-xs myfont-12px gap-5px padding-sm">
						<view class="flex-row justify-start">
							<view class="cuIcon-warnfill round mybg-active padding-10px"></view>
							<view class="flex-column margin-left-sm align-start gap-5px" style="align-items: start;">
								<view class="text-light">{{'Balance (Main Wallet)'}}</view>
								<view>{{'10000000'}}</view>
							</view>
						</view>
						<button class="cu-btn mybg-active mycolor-primary myfont-12px">
							<view class="cuIcon-addressbook margin-right-sm"></view>
							<view @click="">Deposit</view>
						</button>
					</view>
					<view class="flex-column box-shadow radius-6px margin-bottom-xs myfont-12px gap-5px padding-sm">
						<view class="flex-row justify-between">
							<view class="flex-row justify-between margin-right radius-6px padding-tb-xs padding-lr-sm"
								style="border: 1px grey solid;">
								<input class="width-100 text-left padding-right-sm" type="number" v-model="amount" />
								<view class="cuIcon-close round width-20px height-18px line-height-16px myfont-10px"
									style="border: 4upx #0c356a solid;" @click="set_amount('')"></view>
							</view>
							<button class="cu-btn mybg-active mycolor-primary myfont-12px"
								@click="submit()">
								<view class="cuIcon-addressbook margin-right-sm"></view>
								<view>Betting</view>
							</button>
						</view>
						<view class="flex-row justify-start text-light text-black" style="">
							<view>Minimum bet <text class="padding-lr-xs text-bold mycolor-primary">{{'100'}}</text> to
								<text class="padding-lr-xs text-bold mycolor-primary">{{'100000'}}</text> MMK.
							</view>
						</view>
						<view class="flex-row justify-start align-center ">
							<view>{{`Potential winnings:`}}<text class="margin-left-sm myfont-20px ">{{Math.pow(2,match_list.length) * amount}}</text>
							</view>
						</view>
						<view class="flex-row justify-start text-light">
							<view>{{`Non maximum wining limit`}}</view>
						</view>
					</view>
					<view class="flex-column box-shadow radius-6px margin-bottom-xs myfont-12px gap-5px padding-sm">
						<view class="flex-row justify-start text-light">
							<view>{{`Quick bets`}}</view>
						</view>
						<view class="flex-row justify-start text-light">
							<view>{{`Select a stake amount to place a bet`}}</view>
						</view>
						<view class="flex-row justify-between text-light">
							<button class="cu-btn mybg-primary width-31" @click="set_amount(i)"
								v-for="(i,index) in [100,50000,100000]">{{i}}</button>
						</view>
					</view>
				</view>
			</view>
		</view>
	</scroll-view>
</template>

<script>
	import match_mixins from './mixins.js'
	export default {
		mixins: [match_mixins],
		props: {
			hidden: true,
			title: String,
			match_ref: {
				type: Object,
				default: function() {
					return {}
				}
			},
			mixed: {
				type: Boolean,
				default: false
			},
			width: {
				type: String,
				default: '880px'
			},
			height: {
				type: String,
				default: '500px'
			},
			showConfrim: {
				type: Boolean,
				default: true
			},
			showCancel: {
				type: Boolean,
				default: true
			},
			confirmText: {
				type: String,
				default: '确定'
			},
			cancelText: {
				type: String,
				default: '取消'
			},
		},
		computed: {
			match_list() {
				let match_list = []
				let leagues = this.match_ref.league_list
				leagues.forEach(league => {
					match_list = match_list.concat(league.match_list)
				})
				let selected = []
				match_list.forEach(match => {
					match.ATTR.some(attr => {
						if (attr.host_selected || attr.guest_selected || attr.draw_selected) {
							selected.push(match)
							match.sa = attr
							return
						}
					})
				})
				return selected
			},
			mask_style() {

			}
		},
		data() {
			return {
				willclose: false,
				amount: '5000',
			}
		},
		methods: {
			set_dialog_hide(e) {
				this.$emit('update:hidden', e)
			},
			set_amount(amount) {
				this.amount = amount
			},
			show_dialog(...args) {

			},
			bet_sc(){
				this.$emit('bet_sucess')
			},
			submit() {
				var _this = this;
				uni.showLoading({
					title: 'loading',
				})
				let url = `/order/${_this.match_ref.mixed?'mix':'single'}_bet`
				clearInterval(this.confirmIntervalId)
				var paras = [];
				var checkAttrs = {}
				_this.match_list.forEach(element => {
					var temp = {
						matchId: element.MATCH_ID,
						attrType: element.sa.MATCH_ATTR_TYPE,
						betType: element.sa.draw_selected ? 3 : element.sa.host_selected || element.sa
							.over_selected ? 1 : 2,
						amount: parseInt(_this.amount)
					}
					checkAttrs[element.sa.MATCH_ATTR_ID] = element.sa;
					checkAttrs[element.sa.MATCH_ATTR_ID].BET_TYPE = element.sa.draw_selected ? 3 : element.sa
						.host_selected || element.sa.over_selected ? 1 : 2
					paras.push(temp)
				})
				//校验是否超出限额
				if (_this.amount > parseInt(_this.$store.state.configs.single_max)) {
					uni.hideLoading();
			
					uni.showModal({
						title: 'Tips',
						content: _this.language.single_max + " (" + _this.$store.state.configs.single_max + ")",
						showCancel: false,
						confirmText: 'ok',
						success: function(res) {}
					});
					return;
				}
				if (_this.amount < parseInt(_this.$store.state.configs.single_min)) {
					uni.hideLoading();
					uni.showModal({
						title: 'Tips',
						content: _this.language.single_min + " (" + _this.$store.state.configs.single_min + ")",
						showCancel: false,
						confirmText: 'ok',
						success: function(res) {}
					});
			
					return;
				}
			
				var changeList = [];
				_this.$http.post('/order/check_odds', {
					attrs: checkAttrs
				}, (res) => {
					if (res.statusCode == 200) {
						changeList = res.data.items;
						if (changeList.length > 0) {
							uni.showModal({
								title: 'tips',
								content: _this.language.odds_change,
								showCancel: false,
								confirmText: 'အတည်ပြုမည်',
								success: function(res) {
									_this.orders.forEach((element, index, ) => {
										changeList.forEach(ele => {
											if (ele.MATCH_ATTR_ID == element.sa
												.MATCH_ATTR_ID) {
												var DRAW_BUNKO = ele.DRAW_BUNKO ==
													'0' ? '+' : '-';
			
												element.sa.ODDS_DESC = '(' + ele
													.LOSE_BALL_NUM +
													DRAW_BUNKO + ele.DRAW_ODDS +
													')' //(2-50)
			
												element.sa.LOSE_BALL_NUM = ele
													.LOSE_BALL_NUM;
												element.sa.DRAW_BUNKO = ele
													.DRAW_BUNKO;
												element.sa.DRAW_ODDS = ele.DRAW_ODDS;
												element.sa.ODDS = ele.ODDS;
												element.sa.ODDS_GUEST = ele
													.ODDS_GUEST;
												Vue.set(_this.match_list, index, element)
											}
										})
									})
									uni.hideLoading()
									return;
								}
							})
						} else {
							_this.$http.post(url, {
								bets: paras,
								totalAmount: parseInt(_this.amount)
							}, (res) => {
								uni.hideLoading();
								if (res.statusCode == 200) {
									uni.showModal({
										content: _this.language.bettingSuccess,
										title: tips,
										showCancel: false,
										confirmText: 'ok',
										success: function() {
											var userInfo = _this.$store.state.userInfo
											userInfo.money = parseInt(userInfo.money) - parseInt(_this.amount);
											_this.$store.dispatch('saveUserInfo', userInfo);
											//把选过的比赛刷掉
											_this.set_dialog_hide(true)
											_this.bet_sc();
										}
									});
								} else {
									var tips = '';
									if (_this.language[res.data.message]) {
										tips = _this.language[res.data.message] + "(" + _this.$store.state
											.configs[res.data.message] + ")"
									} else {
										tips = res.data.message;
									}
									uni.showModal({
										title: 'tips',
										content: tips,
										showCancel: false,
										confirmText: 'ok',
										success: function(res) {}
									});
								}
							})
						}
					}
				})
			},
		}
	}
</script>

<style lang="scss">
	.dialog-wrapper {
		// width: 100vw;
		// position: fixed;
		// left: 0;
		// bottom: 0;
		z-index: 15 !important;
		height: 100vh !important;
	}

	.box-shadow {
		box-shadow: rgba(60, 64, 67, 0.3) 0px 1px 2px 0px, rgba(60, 64, 67, 0.15) 0px 1px 3px 1px;
	}

	.dialig-bottom {
		display: flex;
		flex-direction: column;
		background-color: white;
	}

	.row-line {
		height: 2vw;
		width: 12vw;
		border-radius: 100px;
	}

	.single-bottom {
		border-top-right-radius: 5vw;
		border-top-left-radius: 5vw;
	}

	.single-mask {
		background: none;
		height: 100vh;
		// filter: ;
		opacity: .5;
		background-color: black;
	}
</style>