<template>
	<view class="dark-teal-bg">
		<zw-header></zw-header>
		<scroll-view scroll-y style="height: calc(100vh - 120px); background: #fff;">
			<view class="title-bar" style="height: auto;">
				<view class="flex-row justify-between" style="">
					<view class="flex-row align-center" style="">
						<image src="/static/icon/basic/back.svg" mode="widthFix" class="width-30px"
							@click="goto('../index/wallet')"></image>
						<image src="/static/icon/ucenter/wallet2.svg" mode="widthFix" class="width-20px"></image>
						<text class="title-text" style="">{{language.withdraw}}</text>
					</view>
				</view>
				<view class="flex-row justify-between myfont-10px text-bold text-black"
					style="line-height: 1.5;box-shadow: rgba(0, 0, 0, 0.5) 0px 4px 8px;padding: 12px;border-radius: 4px;margin-bottom: 15px;"
					v-if="card_list[0]">
					<view class="flex-column1 justify-center align-center margin-left-sm" @click="">
						<image class="title-icon" :src="`/static/icon/register/${card_list[0].bank_code}.png`"></image>
					</view>
					<view class="flex-column1 justify-center align-start width-45" @click="">
						<view class="bank-title">{{card_list[0].acc_name}}</view>
						<view>{{ $t('account_ame') }}</view>
						<view class="bank-title">{{card_list[0].acc_number}}</view>
						<view>{{ $t('account_number') }}</view>
					</view>
					<view class="flex-column1 justify-center align-center margin-right">
						<image src="/static/icon/wallet/128.png" style="height: 60px;" mode="heightFix"></image>
						<text class="myfont-12px">{{ $t('new_label') }}</text>
					</view>
				</view>
			</view>
			<view class="tips" style="">
				<view class="text-bold">
					{{$t('important_notice')}}:
				</view>
				<view>{{$t('withdraw_tips1')}}</view>
				<view>{{$t('withdraw_tips2')}}</view>
			</view>
			<view class="width-100"
				style="font-family: __Inter_7be8ac, __Inter_l;font-weight: 600;color: black;padding: 0 20px;">
				{{ $t('text_field_amount') }}
			</view>
			<view class="flex-column mybg-lprimary text-white width-100" style="position: relative">
				<input class="amount-input" style="" type="number" @input='inputNum' v-model="amount"
					placeholder-class="text-white" maxlength="7" placeholder=""></input>

				<view class="ks" style="">Ks</view>
				<view class="turnover">
					Turnover Current: 100 Ks
				</view>
				<view class="limit">Minimum 10,000 Ks, Maximum 5,000,000</view>
			</view>
			<view
				style="display: flex;flex-direction: row;flex-wrap:wrap;justify-content:space-between;padding: 5px 40px;width: 100%;">
				<view class="amount-select" style="" v-for="(item,index) in amount_list" :key="index"
					@click="amount_select(item)">{{numberFormat(item)}}
				</view>
			</view>
			<!-- <view class="cu-list menu">
			<view class="bar-row flex-row myrect box-shadow cu-item">
				<view class="flex-row content" style="text-align: left;">
					<view class="bar-icon">
						<image class="bar-icon-image" src="../../static/image/pocket.png"></image>
					</view>
					<text class="text-grey myfont-bold">{{language.withdraw_limit}}</text>
				</view>
				<view class="action">
					<text class="mycolor-red myfont-bold">{{configs.withdraw_min_limit}}</text>
				</view>
			</view>
		
			<view class="bar-row flex-column myrect box-shadow cu-item">
				<view class="flex-row content" style="text-align: left;line-height: 40px;">
					<view class="bar-icon">
						<image class="bar-icon-image" src="../../static/image/pocket.png"></image>
					</view>
					<text class="text-grey myfont-bold">{{language.withdraw_amount}}</text>
				</view>
				<view class="flex-row content-row myrect mybg-grey" style="width: 100%;padding: 0 15px 0 15px;">
					<view class="myfont-bold text-left">Money</view>
		
				</view>
			</view>
		
		
			<view class="bar-row flex-row myrect box-shadow cu-item">
				<view class="flex-row content" style="text-align: left;">
					<view class="bar-icon">
						<image class="bar-icon-image" src="../../static/image/pocket.png"></image>
					</view>
					<text class="text-grey myfont-bold">{{$toolbox.floor_format(userInfo.money)}}</text>
				</view>
				<view class="action" @click="allWithdrawBtn()">
					<text class="mycolor-red myfont-bold">{{language.withdraw_all}}</text>
				</view>
			</view>
			<button class="login-btn" style="width: 70%;margin: 20px 15% 10px 15%;" disabled="" @click="submit()">
				{{'SUBMIT'}}</button>
		</view> -->
			<view class="text-center text-red" style="font-weight: 400;font-size: 1rem;line-height: 1.5;">
				{{$t('withdraw_tips3')}}
			</view>
			<button class="login-btn" style="width: 70%;margin: 20px 15% 10px 15%;" :disabled="amount_error"
				@click="submit()">
				{{'SUBMIT'}}</button>
			<view class="padding-xs"></view>
		</scroll-view>


		<uni-popup ref="popup" type="center">
			<view class="bg-white">
				<form>
					<view class="cu-form-group border-bottom">
						<view class="title">{{language.withdrawAmount}}</view>
						<input type="number" placeholder="" v-model="amount"></input>
					</view>
					<button @click="$noMultipleClicks(submit)" class="bg-green margin-top-sm submit">Yes</button>
				</form>
			</view>
		</uni-popup>
	</view>
</template>

<script>
	import config from '../../utils/config.js';
	import dateFormatUtils from "../../utils/utils.js"


	export default {
		data() {
			return {
				index: -1,
				status: 'more',
				page: 1,
				limit: 15,
				picture: '',
				list: [],
				amount: 0.00,
				contentText: {
					contentdown: 'more',
					contentrefresh: 'loading',
					contentnomore: 'no more'
				},
				cartList: [],
				cartId: [],

				userInfo: null,
				configs: null,
				language: config.language,
				amount_list: [10000, 50000, 100000, 500000, 1000000, 5000000],
				amount_error: true,
				card_list: [],
			}
		},
		watch: {
			amount(val) {
				const rawAmount = parseInt(this.amount)
				this.amount_error = !(rawAmount >= 10000 && rawAmount <= 5000000)
			}
		},
		methods: {
			goto(url) {
				uni.reLaunch({
					url: url,
				})
			},
			amount_select(amount) {
				this.amount = amount
			},
			inputNum: function(evt) {
				let amount = evt.detail.value.replace('.', '')
				amount = amount ? parseInt(amount) : '0'
				if (amount > 5000000) {
					amount = 5000000
				}
				this.$nextTick(function() {
					this.$set(this, 'amount', amount)
					// if (10000 < parseInt(this.amount) && parseInt(this.amount) < 5000000) {
					// 	this.amount_error = false
					// }
				})
			},

			numberFormat(number) {
				return dateFormatUtils.numFormat(number);
			},
			allWithdrawBtn() {
				let info = Object.assign({}, this.userInfo)
				this.$set(this, 'amount', info.money.replace(',', ''))
			},
			getList() {
				var _this = this;
				var para = {
					page: _this.page,
					limit: _this.limit
				}
				uni.showLoading({
					'title': 'loading'
				})
				_this.list = []
				_this.$http.get('/withdraw/get', {
					data: para
				}, (res) => {
					if (res.statusCode == 200) {
						uni.hideLoading();
						var results = res.data.items;
						results.forEach(element => {
							element.CREATE_TIME = element.CREATE_TIME.substring(0, 16);
							switch (element.Work_Group) {
								case 'A': 
									element.color = 'red'
									break;
								case 'B':
									element.color = 'blue'
									break;
								case 'C':
									element.color = 'green'
									break;

							}
							// console.log(_this.list)
							_this.list.push(element);
						})
						if (results.length == 0) {
							uni.showToast({
								'title': 'no more',
								'icon': 'none'
							})
						}
					}
				})
			},
			add() {
				this.$refs.popup.open()
			},
			submit() {
				var _this = this;

				var para = {
					// 'NICK_NAME': _this.userInfo.BANK_USER_NAME,
					// 'BANK_TYPE': _this.userInfo.BANK_TYPE,
					// 'CARD_NUM': _this.userInfo.BANK_CARD,
					'card_id': _this.card_list[0].id,
					'money': parseInt(_this.amount),
				}
				//判断提现金额是否为最小限额  ,如果未满足禁止体现
				if (_this.amount < parseInt(_this.$store.state.configs['withdraw_min_limit']) || _this.amount < 0) {

					this.$notice.show({
						title: 'tips',
						content: this.language['The minimum withdraw must be equal or greater'] + _this.$store
							.state.configs['withdraw_min_limit'],
						showCancel: false,
						confirmText: 'OK',
						success: function(res) {}
					});

					return;
				}

				// if (_this.amount > parseInt(_this.$store.state.userInfo.money.replace(',', ''))) {
				// 	this.$notice.show({
				// 		title: 'tips',
				// 		content: this.language.withdrawTips2,
				// 		showCancel: false,
				// 		confirmText: 'OK',
				// 		success: function(res) {}
				// 	});
				// 	return;
				// }

				// if (_this.amount < 0) {
				// 	this.$notice.show({
				// 		title: 'tips',
				// 		content: this.language.withdrawTips1,
				// 		showCancel: false,
				// 		confirmText: 'OK',
				// 		success: function(res) {}
				// 	});
				// 	return;
				// }
				uni.showLoading({
					title: _this.$t('withdrawing')
				})
				_this.$http.post('/withdraw/apply', para, (res) => {
					uni.hideLoading()
					if (res.statusCode == 200) {
						this.$notice.show({
							title: `${_this.$t('Congratulations')}`,
							content: `${_this.$t('Amount')} (${_this.amount}). ${_this.$t('withdraw_success')}`,
							showCancel: false,
						})
						// uni.showToast({
						// 	title: 'withdraw success',
						// 	icon: 'success',
						// 	duration: 2000
						// })

						var userInfo = _this.$store.state.userInfo
						userInfo.money = String(parseInt(userInfo.money.replaceAll(',', '')) -
							parseInt(
								_this.amount));
						_this.userInfo = userInfo
						_this.$store.dispatch('saveUserInfo', userInfo);

						_this.page = 1;
						_this.list.length = 0;
						// _this.getList();
					} else {

						var tips = '';


						if (_this.language[res.data.message]) {
							//未达到最低提现额，则提示最低提现额额度 
							tips = res.statusCode == 429 ? _this.language[res.data.message] + "(" + this.$store
								.state.configs[res.data.message] + ")" : _this.$t(res.data.message);
						} else {
							tips = res.data.message;
						}

						this.$notice.show({
							title: 'tips',
							content: tips,
							showCancel: false,
							confirmText: 'OK',
							success: function(res) {}
						});
					}
					this.$refs.popup.close()
				})
			},
			get_bank_card_list() {
				var _this = this;
				var para = {}
				_this.$http.get('/bank_card/get', {
					data: para
				}, (res) => {
					if (res.statusCode == 200) {
						_this.card_list = res.data.items;
					} else {}
				})
			},
		},
		onLoad() {
			// this.getList();
			this.get_bank_card_list()
			this.userInfo = Object.assign({}, this.$store.state.userInfo)
			this.configs = Object.assign({}, this.$store.state.configs)

		},
	}
</script>

<style lang="scss">
	.dark-teal-bg {
		background: #02455F;
		min-height: 100vh;
	}

	.amount-input {
		font: inherit;
		letter-spacing: inherit;
		padding: 1px 0px 5px;
		border: 0px;
		box-sizing: content-box;
		background: none;
		height: 1.4375em;
		margin: 0px;
		-webkit-tap-highlight-color: transparent;
		display: block;
		min-width: 0px;
		width: 100%;
		animation-name: mui-auto-fill-cancel;
		animation-duration: 10ms;
		font-size: 35px;
		font-weight: bold;
		text-align: center;
		height: 60px;
	}

	.ks {
		margin: 0px;
		font-family: __Inter_7be8ac, __Inter_Fallback_7be8ac;
		line-height: 1.5;
		font-size: 10px;
		font-weight: 600;
		position: absolute;
		right: 80px;
		top: 0px;
	}

	.turnover {
		margin: 5px 0px 0px;
		font-family: __Inter_7be8ac, __Inter_Fallback_7be8ac;
		line-height: 1.5;
		color: rgb(255, 255, 255);
		font-size: 12px;
		font-weight: 600;
		text-align: center;
		opacity: 1;
	}

	.limit {
		margin: 1px;
		font-family: __Inter_7be8ac, __Inter_Fallback_7be8ac;
		line-height: 1.5;
		color: rgb(255, 255, 255);
		font-size: 11px;
		font-weight: 600;
		text-align: center;
		opacity: 0.6;
	}

	.amount-select {
		width: 100px;
		height: 30px;
		margin-top: 5px;
		border-radius: 10px;
		color: rgb(12, 53, 106);
		font-weight: 600;
		display: flex;
		flex-direction: column;
		justify-content: center;
		text-align: center;
		background-color: rgb(255, 255, 255);
		box-shadow: rgba(60, 64, 67, 0.3) 0px 1px 2px 0px, rgba(60, 64, 67, 0.15) 0px 1px 3px 1px;
	}


	.bar-row {
		width: 90vw;
		margin-top: 10px;
		justify-content: space-between;
	}

	.bar-icon {
		width: 14px;
		height: 15px;
		margin-right: 5px;

	}

	.bar-icon-image {
		width: 100%;
		height: 100%;
	}

	.submit {
		border-radius: 0;
	}

	.bg-green {
		background-color: rgb(185, 1, 0);
	}

	.input {
		background-color: lightgrey;
		height: 30px;
		border-radius: 4px;
		padding-left: 5px;
	}


	.add {
		position: fixed;
		height: 20vw;
		width: 20vw;
		bottom: 2px;
		left: 40vw;
	}

	.border-bottom {
		border: 1px solid lightgrey;
	}

	.content-row {
		justify-content: space-around;
		line-height: 30px;
		margin: 5px 0 15px 0;
	}

	.content-row view {
		padding: 5px 0 5px 0;
	}

	.content-row view:first-child {
		width: 50%;
	}

	.content-row view:nth-child(2) {
		width: 50%;
	}
</style>