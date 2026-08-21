<template>
	<view class="dialog-wrapper" v-show="!hidden">
		<view class="flex-row text-bold box-shadow padding-lr-sm padding-tb-xs" @click="set_dialog_hide(true)">
			<view class="cuIcon-back mycolor-info"></view>
			<view class="margin-left mycolor-primary">{{match_ref.match_detail.REMARK}}</view>
		</view>
		<view class="flex-row justify-center padding-tb-xl mycolor-primary text-bold width-100 padding-lr" style="line-height: 1.5;">
			<view class="flex-column gap-5px myfont-11px">
				<image :src="match_ref.match_detail.home_pic" class="height-10vw width-10vw" @error="error_pic(match_ref.match_detai,'home')"></image>
				<view :class="{'text-red':match_ref.match_detail.LOSE_TEAM ==='1',}">{{match_ref.match_detail.HOST_TEAM}}</view>
			</view>
			<view class="flex-column myfont-10px">
				<view>{{'TODAY'}}</view>
				<view>{{'MATCH START IN'}}</view>
				<view class="myfont-18px">
					<text>{{'14'}}</text>：<text>{{'38'}}</text>：<text>{{'59'}}</text>
				</view>
				<view class="myfont-7px">
					<text>{{'HOUR'}}</text>：<text>{{'MINUTE'}}</text>：<text>{{'SECOND'}}</text>
				</view>
			</view>
			<view class="flex-column gap-5px myfont-11px">
				<image :src="match_ref.match_detail.away_pic" class="height-10vw width-10vw" @error="error_pic(match_ref.match_detai,'away')"></image>
				<view :class="{'text-red':match_ref.match_detail.LOSE_TEAM ==='1',}">{{match_ref.match_detail.GUEST_TEAM}}</view>
			</view>
		</view>
		<view class="flex-column width-100 gap-10vh padding-lr">
			<view class="league-match-attr" v-for="(attr,__index) in match_ref.match_detail.ATTR" :key="__index">
				<view class="league-match-attr-type">
					{{[,'HDP','OU',,'HDP','OU',,,,,'1X2'][parseInt(attr.MATCH_ATTR_TYPE)]}}
				</view>
				<view class="league-match-attr-detail"
					@click="bet_click('host',__index,attr)"
					:class="{'mybg-active':attr.host_selected,}">
					<view class="league-match-attr-detail-up"
						:class="{'text-red':(attr.LOSE_TEAM==='1' || [bet_type.SINGLE_GOAL,bet_type.MIX_GOAL].includes(attr.MATCH_ATTR_TYPE)),'mybg-active':attr.host_selected,}">
						{{attr.LOSE_TEAM==='1' || [bet_type.SINGLE_GOAL,bet_type.MIX_GOAL].includes(attr.MATCH_ATTR_TYPE)?calc_real_odds(attr):'HOME'}}
					</view>
					<view class="league-match-attr-detail-down">{{attr.ODDS}}</view>
				</view>
				<view class="league-match-attr-detail"
					@click="bet_click('draw',__index,attr)"
					:class="{'mybg-active':attr.draw_selected,}"
					v-if="attr.MATCH_ATTR_TYPE==bet_type.SINGLE_WDL">
					<view class="league-match-attr-detail-up">{{ $t('draw') }}</view>
					<view class="league-match-attr-detail-down">{{attr.DRAW_ODDS}}</view>
				</view>
				<view class="league-match-attr-detail"
					@click="bet_click('guest',__index,attr)"
					:class="{'mybg-active':attr.guest_selected,}">
					<view class="league-match-attr-detail-up"
						:class="{'text-red':attr.LOSE_TEAM==='2' && [bet_type.SINGLE_BODY,bet_type.MIX_BODY].includes(attr.MATCH_ATTR_TYPE),'mybg-active':attr.guest_selected,}">
						{{attr.LOSE_TEAM==='2' && [bet_type.SINGLE_BODY,bet_type.MIX_BODY].includes(attr.MATCH_ATTR_TYPE)?calc_real_odds(attr):'AWAY'}}
					</view>
					<view class="league-match-attr-detail-down">{{attr.ODDS_GUEST}}</view>
				</view>
			</view>
		</view>
	</view>
</template>

<script>
	import match_mixins from './mixins.js'
	export default {
		mixins: [match_mixins],
		props: {
			hidden: true,
			title: String,
			mixed: {
				type: Boolean,
				default: false
			},
			league_list: {
				type: Array,
				default: function() {
					return []
				}
			},
			match_ref: {
				type: Object,
				default: function() {
					return {
						match_detail:{}
					}
				}
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
		data() {
			return {
				willclose: false
			}
		},
		methods: {
			set_dialog_hide(e) {
				this.$emit('update:hidden', e)
			},
			bet_click(type, __index, attr){
				// this.$emit('bet_click',[type, this.match.index, this.match._index, __index, attr])
				console.log(this.league_list)
				console.log(this.league_list[0])
				// this.$parent.betClick(type, this.match.index, this.match._index, __index, attr)
				this.betClick(type, this.match_ref.match_detail.index, this.match_ref.match_detail._index, __index, attr,true)
			},
			open(){
				
			},
		}
	}
</script>

<style lang="scss">
	@import './match.css';

	.dialog-wrapper {
		z-index: 10000;
		background-color: white;
		position: fixed;
		left: 0;
		bottom: 0;
		height: calc(var(--app-viewport-height, 100vh) - 55px);
		width: 100vw;
	}


	.league-match-attr {
		font-weight: 400;
		line-height: 1.5;
		height: 75px;
		width: 100%;
		max-width: 100%;
	}

	.league-match-attr-type {
		font-size: 16px;
		font-weight: 700;
		line-height: 100%;
		transform: scale(1);
	}

	.league-match-attr-detail {
		height: 65px;
		width: 50%;
		margin: 0px 10px;
		padding: 0px;
		border-radius: 5px;
		max-width: 100%;
	}

	.league-match-attr-detail-up {
		font-weight: 700;
		font-size: 10px;
		transform: scale(1);
		padding: 2px;
	}

	.league-match-attr-detail-down {
		transform: scale(1);
		font-size: 0.875rem;
		width: 100%;
		border-radius: 0px 0px 5px 5px;
		height: calc(100% - 25px);
		background-color: rgb(255, 255, 255);
		display: grid;
		place-items: center;
	}
</style>