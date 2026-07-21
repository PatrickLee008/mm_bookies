<template>
	<view class="bg-white full-page">
		<zw-header></zw-header>
		<!-- 顶栏 -->
		<view class="title-bar" style="height: auto;">
			<view class="flex-row justify-between" style="height: 50px;">
				<view class="flex-row align-center" style="">
					<image src="/static/icon/basic/back.svg" mode="widthFix" class="width-30px"
						@click="goto('../index/wallet')"></image>
					<image src="/static/icon/ucenter/wallet2.svg" mode="widthFix" class="width-20px"></image>
					<text class="title-text" style="">{{language.deposit}}</text>
				</view>
				<view class="align-center" style="">
					<view class="charge-history-btn" @click="viewChargeHistory">
						<text class="cuIcon-order myfont-16px mycolor-primary margin-right-xs"></text>
						<text class="myfont-12px mycolor-primary">{{$t('charge_history') || 'Records'}}</text>
					</view>
				</view>
			</view>
			<view class="title-tab justify-around" style="box-shadow: none;">
				<view class="register-btn" :style="`width: ${90/charge_way.length}%`"
					:class="item.checked?'mybg-lprimary':'mycolor-primary route-shadow'"
					@click="select_option(item,'charge_way')" v-for="(item,index) in charge_way" :key="index">
					{{item.label}}
				</view>
			</view>
			<view class="padding-sm"></view>
		</view>
		<scroll-view scroll-y style="height: calc(100vh - 120px - 118px);">
			<view v-if="current_progress==0">
				<!-- 银行选择 -->
				<view class="flex-column justify-center padding-top-sm mycolor-primary">
					<view class="myfont-14px text-bold height-20px">{{'Available bank'}}</view>
					<view class="myfont-10px height-10px">{{'Select bank you would like to transfer to'}}</view>
				</view>
				<view class="flex-row1 justify-center margin-top-sm">
					<image :src="item.src" mode="heightFix" style="height: 60px;border-radius: 8px;margin: 0 10px;"
						:style="!item.checked?'opacity:50%':''" @click="select_option(item,'bank_list')"
						v-for="(item,index) in bank_list" :key="index">
					</image>
					<!-- <image src="/static/icon/register/wave.png" mode="heightFix" style="height: 70px;border-radius: 8px;">
					</image> -->
				</view>
				<!-- tips -->
				<view class="width-100 flex-column1 align-start margin-tb padding-lr-sm text-red myfont-13px"
					style="font-size: 1rem;line-height: 1.1;">
					<view class="text-bold">
						{{$t('important_notice')}}:
					</view>
					<view class="">
						{{$t('deposit_tips1')}}
					</view>
					<view class="">
						{{$t('deposit_tips2')}}
					</view>
				</view>
				<!-- 输入框 -->
				<view class="flex-column mybg-lprimary text-white width-100" style="position: relative">
					<input class="amount-input" style="" type="number" @input='inputNum' v-model="amount"
						placeholder-class="text-white" maxlength="7" placeholder="">
					<!-- <view class="ks" style="">Ks</view> -->
					<view class="limit">Minimum 3,000 and Maximum 1,000,000 Ks</view>
				</view>
				<!-- 快速选择 -->
				<view
					style="display: flex;flex-direction: row;flex-wrap:wrap;justify-content:space-between;padding: 5px 40px;width: 100%;">
					<view class="amount-select" style="" v-for="(item,index) in amount_list" :key="index"
						@click="amount = item">{{numberFormat(item)}}
					</view>
				</view>

				<view class="width-100 flex-row1 justify-start margin-tb padding-lr-sm">
					<view class="mycolor-primary myfont-13px" style="font-size: 1rem;line-height: 1.1;">
						{{$t('deposit_tips3')}}
					</view>
				</view>
				<view class="width-100 flex-row justify-start margin-tb padding-lr-sm">
					<view class=" text-red myfont-13px" style="font-size: 1rem;line-height: 1.1;">
						<text class="text-bold">{{$t('note')}}</text>
						{{$t('deposit_tips4')}}
					</view>
				</view>

			</view>


			<!-- 自动 -->
			<view class="" style="margin-left: 10%;width: 80%;" v-if="current_progress==1 && chargeForm.charge_way==0">
				<!-- <view class="" style="margin-left: 10%;width: 80%;" v-if="chargeForm.charge_way==0"> -->
				<input class="search-rec" style="" placeholder=" Search" placeholder-class="cuIcon-search mycolor-info"
					v-model="card_search" @input="clean_acc" />
				<view class="flex-row justify-between myfont-15px mycolor-primary margin-top-lg">
					<view class="myfont-19px">{{$t('Select_your_bank')}}</view>
					<view class="mybg-grey" style="padding: 0 6px;" v-if="card_list.length>0" @click="edit_card()">
						<text>{{language.edit}}</text>
						<text class="cuIcon-edit myfont-18px margin-left-xs"></text>
					</view>
				</view>

				<view class="flex-column radius-10px" :class="!editing?'round-border':'no-right-border'" style="">
					<view class="flex-row justify-between myfont-10px text-black height-70px"
						v-for="(card,index) in filtered_card_list" :key="index"
						@click="editing?'':select_option(card,'card_list',1)"
						style="line-height: 1.1;padding: 8px 0 8px 8px;border-radius: 4px;"
						:style="index+1<card_list.length?'border-bottom: solid darkgray 1px;':''">
						<view class="flex-row1">
							<view class="flex-column1 justify-center align-center">
								<image class="height-50px width-50px" style="border-radius: 8px;"
									:src="`/static/icon/register/${card.bank_code}.png`"></image>
							</view>
							<view class="flex-column1 justify-center align-start myfont-11px margin-left">
								<view class="myfont-12px text-bold text-black">{{ $t('account_number') }}</view>
								<view>{{card.acc_number}}</view>
								<view style="height: 2px;"></view>
								<view class="myfont-12px text-bold text-black">{{ $t('account_ame') }}</view>
								<view>{{card.acc_name}}</view>
							</view>
						</view>
						<view class="width-70px">
							<view class="height-70px flex-column text-white myfont-14px radius-right-6px"
								:class="card.is_default?'mybg-linfo':''"
								:style="card.is_default?'color:#666666':'background-color: #E02B2B;'" v-if="editing"
								@click="card.is_default?'':removeBank(card)">
								{{ $t('remove') }}
							</view>
							<view class="flex-column1 align-center justify-center" v-else>
								<view class="myfont-10px margin-bottom-xs" :class="!index?'mycolor-primary':''">
									{{index?language.other:language['main account']}}
								</view>
								<radio :class="card.checkeds?'checked':''" :checked="card.checked">
								</radio>
							</view>
						</view>
					</view>
				</view>

				<view class="flex-row myfont-10px text-black height-70px radius-10px margin-top-lg"
					style="border: solid darkgray 1px;padding: 8px 20px;border-radius: 4px;"
					@click="show_add_modal('add')">
					<text class="cuIcon-roundadd myfont-28px mycolor-lprimary" style="">
					</text>
					<text class="myfont-17px margin-left-lg text-black">{{ $t('add_bank_manually') }}</text>
				</view>

				<view class="height-45px radius-10px margin-top flex-column"
					:class="acc_checked?'mybg-lprimary':'mybg-linfo'" @click="auto_submit()">
					{{$t('proceed_selected_account')}}
				</view>
				<view class="flex-row1 width-100vw margin-top-sm align-start height-20px"
					style="line-height: 1;position: absolute;left: 0;">
					<view class="width-45 height-50" style="border-bottom: dashed darkgray 1px;"></view>
					<text class="margin-lr-sm">{{language.or}}</text>
					<view class="width-45 height-50" style="border-bottom: dashed darkgray 1px;"></view>
				</view>
				<view class="mybg-lprimary height-45px radius-10px flex-column" style="margin-top: 40px;"
					@click="show_add_modal('one-time')">
					{{$t('proceed_one_time_payment')}}
				</view>
			</view>

			<!-- 手动 -->
			<view v-if="current_progress==1 && chargeForm.charge_way==1">
				<!-- 收款信息 -->
				<view class="padding">
					<view class="flex-row justify-start myfont-10px text-bold text-black"
						style="line-height: 1.5;box-shadow: rgba(0, 0, 0, 0.5) 0px 4px 8px;padding: 12px;border-radius: 4px;margin-bottom: 15px;">
						<view class="flex-column1 justify-center align-center margin-left-sm" @click="">
							<image class="title-icon" style="border-radius: 0;"
								:src="`/static/icon/register/${agent_bankcard.rc_bank_code}.png`"></image>
						</view>
						<view class="flex-column1 justify-center align-start width-45 margin-left-lg" @click="">
							<view class="bank-title">{{agent_bankcard.rc_bank_username}}</view>
							<view>{{ $t('account_ame') }}</view>
							<view class="bank-title">{{agent_bankcard.rc_bank_account}}<text
									class="cuIcon-copy mycolor-info text-light margin-left"
									@click="copy(agent_bankcard.rc_bank_account)"></text>
							</view>
							<view>{{ $t('account_number') }}</view>
						</view>
					</view>
				</view>

				<!-- 金额显示 -->
				<view class="flex-row justify-center margin-bottom text-black padding-lr"
					style="margin: 0px 0px 16px;font-family: __Inter_7be8ac, __Inter_Fallback_7be8ac;font-weight: 600;font-size: 0.875rem;line-height: 1.13;text-align: center;">
					{{'The bank account can change anytime. Please do not save bank info and reuse it without checking on the 1x2 deposit page. Ensure the receiver’s bank info before making a transfer.'}}
				</view>
				<view class="width-100 flex-column padding-lr-lg" v-if="chargeForm.charge_way">
					<view class="text-center text-red myfont-13px" style="font-size: 1rem;line-height: 1.1;">
						{{"Enter transaction id that matched with the uploaded slip."}}
					</view>
					<input class="width-100 margin-tb-sm height-30px radius-3px text-center"
						style="border: 2px solid #E0E0E0;" :style="transaction_disable?'background:rgb(241,241,241)':''"
						type="number" @input='' v-model="chargeForm.transaction_id" placeholder-class="text-white"
						maxlength="32" placeholder="" :disabled="transaction_disable">
				</view>
				<view class="padding-left-lg myfont-16px text-black text-bold">{{language.amount}}</view>
				<view class="flex-column mycolor-primary" style="position: relative">
					<view class="amount-input">{{numberFormat(amount)}}</view>
					<view class="ks" style="right: 110px;">Ks</view>
				</view>
				<view class="flex-column" v-if="chargeForm.charge_way">
					<!-- 提示 -->
					<view class="tips" style="">
						{{"Notice! For faster investigation and automatic processing, please upload the bank slip in English. Otherwise, customers have to enter the transaction ID that is shown on the bank slip manually. If the transaction ID is not matched, the deposit will be rejected."}}
					</view>
					<view class="bg-img padding-sm" @tap="ViewImage" :data-url="picture"
						style="text-align: center;position: relative;">
						<image :src="picture" mode="aspectFill" style="width:80px;height:80px;border:1px dashed grey">
						</image>
						<!-- <view class="cu-tag bg-red" @tap.stop="DelImg"
							style="position: absolute;top:10px;height:18px;width:18px">
							<text class='cuIcon-close'></text>
						</view> -->
					</view>
					<view
						class="mybg-lprimary height-25px myfont-13px padding-sm flex-row1 justify-center align-center radius-3px"
						@click="ChooseImage">
						<text
							class="cuIcon-upload margin-right-xs"></text>{{picture?language.upload_slip_new:language.upload}}
					</view>
				</view>
			</view>


			<!-- 提交 -->
			<button class="login-btn" style="width: 70%;margin: 20px 15% 10px 15%;" :disabled="confirmDisabled"
				v-if="(!chargeForm.charge_way&&current_progress!=1 ) || chargeForm.charge_way"
				@click="next_or_submit()">
				{{language.submit}}</button>
			<!-- <button class="login-btn" style="width: 70%;margin: 20px 15% 10px 15%;" :disabled="confirmDisabled" v-if=""
				@click="next_or_submit()">
				{{language.submit}}</button> -->
			<view class="padding-xs"></view>
		</scroll-view>

		<!-- 添加 -->
		<view class="cu-modal" style="z-index: 998;" :class="modalName=='add_modal'?'show':''">
			<view class="cu-dialog mycolor-primary bg-white" style="border-radius: 12px;min-height: 446px;">
				<view class="cu-bar justify-around">
					<view></view>
					<view></view>
					<view></view>
					<view class="text-bold">
						{{modal_type=='add'?'Enter Your Bank Account Information':'Confirm your Bank Information'}}
					</view>
					<view class="action" @tap="modalName = ''">
						<text class="cuIcon-close text-grey"></text>
					</view>
				</view>
				<form>
					<view class="flex-column1 align-start justify-start padding-lr-sm" style="position: relative;">
						<view>{{$t('Select_your_bank')}}</view>
						<view class="flex-row justify-between align-center height-42px text-black mybg-grey"
							@click="show_bank_list=!show_bank_list" style="padding: 5px 7px;border: solid 1px #626262;">
							<view class="flex-row1">
								<view style="width: 33px;height:33px;">
									<image :src="`/static/icon/register/${card_conf.bank_code}.png`" mode="widthFix" />
								</view>
								<text class="margin-left-sm">{{card_conf.bank_code}}</text>
							</view>
							<view class="" :class="show_bank_list?'cuIcon-unfold':'cuIcon-fold'"></view>
						</view>
						<view class="bank-select" v-if="show_bank_list" style="">
							<view class="flex-row align-center text-black" style="padding: 10px 46px;"
								v-for="(bank,index) in bank_add_list" @click="select_modal_bank(bank)" :key="index">
								<view style="width: 33px;height:33px;">
									<image :src="`/static/icon/register/${bank.bank_code}.png`" mode="widthFix" />
								</view>
								<text class="margin-left-sm">{{bank.label}}</text>
							</view>
						</view>

						<view class="margin-top-sm">{{'Bank Account Name'}}</view>
						<view class="flex-row justify-between align-center height-42px text-black mybg-grey"
							style="padding: 5px 7px;border: solid 1px #626262;">
							<input type="text" class="" style="text-align: start;width: 100%;"
								@input="set_add_disable()" :placeholder="$t('enter_bank_account_name')"
								v-model="card_conf.acc_name" />
						</view>
						<view class="margin-top-sm">{{'Bank Account Number'}}</view>
						<view class="flex-row justify-between align-center height-42px text-black mybg-grey"
							style="padding: 5px 7px;border: solid 1px #626262;">
							<input type="number" class="" style="text-align: start;width: 100%;" maxlength="17"
								@input="set_add_disable()" :placeholder="$t('enter_bank_account_number')"
								v-model="card_conf.acc_number" />
						</view>
						<view class="width-100 text-left margin-top-sm text-red myfont-13px"
							style="font-size: 1rem;line-height: 1.1;">
							{{$t('add_bank_tips')}}
						</view>
					</view>
					<button class="radius-12px width-50" :class="add_disable?'mybg-linfo':'mybg-primary'"
						style="position: absolute;bottom: 20px;left: 25%;"
						@click="modal_type=='add'?add_card():auto_submit()"
						:disabled="add_disable">{{modal_type=='add'?language.save:language.confirm }}</button>
				</form>
			</view>
		</view>
	</view>
</template>

<script>
	import config from '../../utils/config.js'
	// import ClipboardJS from '../../utils/clipboard.min.js';
	import dateFormatUtils from "../../utils/utils.js"

	export default {
		components: {},
		data() {
			return {
				userInfo: {},
				status: 'more',
				listQuery: {
					page: 1,
					limit: 15,
					end: false,
				},
				picture: '',
				language: config.language,
				list: [],
				currentAccount: null,
				trade_list: [],
				modalName: '',
				lang_select: uni.getStorageSync('lang_select') || config.language.lang,
				bankAccountList: [],
				contentText: {
					contentdown: 'more',
					contentrefresh: 'loading',
					contentnomore: 'no more'
				},
				lastOperate: null,
				imgList: [],
				chargeForm: {
					charge_way: 0,
					bank_code: 'KBZ Pay',

					transaction_id: '',

					acc_name: '',
					acc_number: '',
				},
				acc_checked: false,
				card_search: '',

				bank_list: [{
					value: 'KBZ Pay',
					label: 'KBZPay',
					src: '/static/icon/register/KBZ Pay.png',
					checked: true
				}, {
					value: 'Wave Money',
					label: 'KBZPay',
					src: '/static/icon/register/Wave Money.png',
					checked: false
				}],
				amount: 0.00,
				amount_list: [3000, 5000, 10000, 100000, 500000, 1000000],
				amount_error: true,
				charge_way: [{
					label: 'AUTO',
					value: 0,
					checked: true
				}, {
					label: 'MANUAL',
					value: 1,
					checked: false
				}],
				card_list: [],
				current_progress: 0,
				token: uni.getStorageSync('Authorization') || '',

				bank_add_list: [{
					bank_code: 'KBZ Pay',
					label: 'KBZPay',
					checked: true
				}, {
					bank_code: 'Wave Money',
					label: 'WavePAY',
					checked: false
				}, {
					bank_code: 'AYA',
					label: 'AYA PAY',
					checked: false,
				}, {
					bank_code: 'Citizen Pay',
					label: 'Citizen Pay',
					checked: false,
				}, {
					bank_code: 'UAB Pay',
					label: 'UAB Pay',
					checked: false,
				}],

				card_conf: {},
				show_bank_list: false,
				add_disable: true,
				modal_type: '',
				editing: false,
				agent_bankcard: {},
				agent_no_bankcard: false,
				transaction_disable: false,
			}
		},
		watch: {
			amount(val) {
				const rawAmount = parseInt(this.amount)
				this.amount_error = !(rawAmount >= 3000 && rawAmount <= 1000000)
			},
		},
		computed: {
			confirmDisabled() {
				if (this.current_progress == 0 && this.amount_error) return true
				else if (this.current_progress == 1 && this.chargeForm.charge_way == 1 && (!this.picture || !this
						.chargeForm.transaction_id)) return true
				return false
			},
			filtered_card_list() {
				const keyword = this.card_search.trim().toLowerCase();
				if (!keyword) return this.card_list;
				return this.card_list.filter(item => {
					return (
						(item.acc_name && item.acc_name.toLowerCase().includes(keyword)) ||
						(item.acc_number && item.acc_number.toLowerCase().includes(keyword))
					);
				});
			},
		},
		methods: {
			select_option(selected, list, allow_false) {
				if (selected.checked && !allow_false) return
				selected.checked = !selected.checked
				this[list].forEach((item) => {
					if (item != selected) item.checked = false
				})
				this.set_charge_form()
			},
			set_charge_form() {
				this.chargeForm.bank_code = this.bank_list.find(item => item.checked).value
				this.chargeForm.charge_way = this.charge_way.find(item => item.checked).value

				this.acc_checked = false
				let acc = this.card_list.find(item => item.checked)
				if (acc) {
					this.acc_checked = true
					this.chargeForm.acc_name = acc.acc_name
					this.chargeForm.acc_number = acc.acc_number
				} else {
					this.clean_acc()
				}
				// console.log(this.chargeForm)
			},
			clean_acc() {
				this.acc_checked = false
				this.chargeForm.acc_name = ''
				this.chargeForm.acc_number = ''
				let acc = this.card_list.find(item => item.checked)
				if (acc) acc.checked = false
			},
			goto(url) {
				uni.reLaunch({
					url: url
				})
			},
			inputNum: function(evt) {
				let amount = evt.detail.value.replace('.', '')
				amount = amount ? parseInt(amount) : '0'
				if (amount > 1000000) {
					amount = 1000000
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
			copy(account) {
				const _this = this
				uni.setClipboardData({
					data: account,
					success: function() {
						uni.showToast({
							title: _this.$t('copied_to_clipboard'),
							icon: 'success'
						});
					},
					fail: function() {}
				});
			},
			next_or_submit() {
				if (this.$toolbox.click_too_fast(1)) return
				if (!this.current_progress) {
					this.current_progress++
					this.charge_way = this.charge_way.filter(item => item.checked)
					let _this = this
					if (_this.chargeForm.charge_way == 1 && _this.agent_no_bankcard) {
						this.$notice.show({
							title: _this.$t('tips'),
							content: _this.$t('agent_no_bankcard'),
							showCancel: false,
							confirmText: _this.$t('back'),
							success: res => {
								if (res.confirm) {
									this.goto('/pages/ucenter/charge')
								}
							}
						})
					}
					return
				}
				if (this.current_progress) {
					this.submit()
				}
			},
			show_add_modal(modal_type) {
				if (modal_type == 'add' && this.card_list.length >= 5) {
					this.$notice.show({
						title: this.$t('tips'),
						content: this.$t('max_five_banks'),
						showCancel: false,
						confirmText: this.$t('confirm'),
						success: res => {
							if (res.confirm) {
								uni.reLaunch({
									url: './charge'
								})
							}
						}
					})
					return
				}
				this.card_conf.acc_name = ''
				this.card_conf.acc_number = ''
				this.modal_type = modal_type
				this.modalName = 'add_modal'
			},
			select_modal_bank(bank) {
				this.show_bank_list = false
				this.card_conf.bank_code = bank.bank_code
			},
			set_add_disable() {
				if (!this.card_conf.acc_name || !this.card_conf.acc_number) {
					this.add_disable = true
					return
				}
				this.add_disable = false
			},
			edit_card() {
				this.editing = !this.editing
				this.clean_acc()
			},
			add_card() {
				var _this = this;
				if (!_this.card_conf.acc_number || !_this.card_conf.bank_code || !_this.card_conf.acc_name) return
				var para = {
					acc_number: _this.card_conf.acc_number,
					bank_code: _this.card_conf.bank_code,
					acc_name: _this.card_conf.acc_name,
				}
				_this.$http.post('/bank_card/add', para, (res) => {
					if (res.statusCode == 200) {
						uni.showToast({
							title: _this.$t('saved_success'),
							// title: 'Your Bank Account has been successfully saved',
							icon: 'success',
							duration: 2000
						})
						_this.modalName = ''
						_this.get_bank_card_list();
					} else {
						uni.showToast({
							title: res.data.message,
							icon: 'none',
							duration: 2000
						})
					}
				})
			},
			removeBank(bank) {
				var _this = this;
				if (_this.$toolbox.click_too_fast(.5)) return
				this.$notice.show({
					// content: `Are you sure to remove your bank account ${bank.acc_number}?`,
					content: `${this.$t('remove_bank_confirm')}`,
					confirmText: this.$t('Confirm'),
					cancelText: this.$t('Cancel'),
					complete: function(res) {
						if (res.confirm) {
							var para = {
								id: bank.id,
							}
							_this.$http.post('/bank_card/delete', para, (res) => {
								if (res.statusCode == 200) {
									uni.showToast({
										title: _this.$t('removed_success'),
										// title: 'Your Bank Account has been successfully removed',
										icon: 'success',
										duration: 2000
									})
									_this.editing = false
									_this.get_bank_card_list();
								}
							})
						}
					}
				})
			},

			get_bank_card_list() {
				var _this = this;
				var para = {}
				_this.$http.get('/bank_card/get', {
					data: para
				}, (res) => {
					if (res.statusCode == 200) {
						_this.card_list = res.data.items.map((item, index) => ({
							...item,
							checked: false,
							// checked: index === 0,
						}));

					} else {}
				})
			},
			get_agent_bank_card() {
				var _this = this;
				var para = {}
				_this.$http.get('/agent_bankcard', {
					data: para
				}, (res) => {
					if (res.statusCode == 200) {
						_this.agent_bankcard = res.data.item
						if (_this.agent_bankcard.rc_bank_code == 'CB') _this.agent_bankcard.rc_bank_code = 'CB Pay'

					}
					if (res.statusCode == 501) {
						_this.agent_no_bankcard = true
					} else {

					}

				})
			},


			// getList() {
			// 	var _this = this;
			// 	var para = {
			// 		page: _this.listQuery.page,
			// 		limit: _this.listQuery.limit,
			// 	}
			// 	uni.showLoading({
			// 		title: 'Loading...'
			// 	})
			// 	_this.$http.get('/charge_apply/get', {
			// 		data: para
			// 	}, (res) => {

			// 		uni.hideLoading()
			// 		if (res.statusCode == 200) {
			// 			var results = res.data.items;
			// 			results.forEach(element => {
			// 				element.CREATE_TIME = element.CREATE_TIME.substring(0, 16);
			// 				element.PICTURE = _this.$http.baseUrl + '/' + element.PICTURE
			// 				// console.log(element.PICTURE);
			// 				_this.list.push(element);
			// 			})
			// 			if (results.length == 0) {
			// 				_this.listQuery.end = true
			// 			} else {}
			// 		}
			// 	})
			// },
			changeLanguage(lang) {
				this.lang_select = lang;
				uni.setStorageSync('lang_select', lang);
			},
			uploadPic() {
				var _this = this;
				_this.trade_list = []
				let url = '/charge/order_image'
				// if (_this.lang_select === 'en') {
				// 	url += '_en'
				// }
				if (this.picture) {
					uni.showLoading({
						title: this.$t('upload_pic')
					})
					var con = {
						url: url,
						filePath: _this.picture,
						formData: {
							MONEY: _this.amount,
							lang: _this.lang_select,
						},
						name: 'image',
						success: (res) => {
							if (res.statusCode == 200) {
								uni.hideLoading()
								// 解析响应数据
								let responseData;
								try {
									responseData = JSON.parse(res.data);
								} catch (e) {
									responseData = res.data;
								}
								console.log('完整响应数据:', responseData);

								let trades = responseData.trades;
								console.log('trades数据:', trades);

								if (trades && trades[0]) {
									// _this.checkboxChange(trades[0]);
									_this.chargeForm.transaction_id = trades[0].transaction_id;
									_this.transaction_disable = true;
								}
								// else {
								// 	trades.forEach(ele => {
								// 		ele.checked = false;
								// 	});
								// 	_this.trade_list = trades;
								// }
							} else {
								let tips = res.message
								if (_this.language[res.message]) {
									tips = _this.language[res.message]
								}
								uni.hideLoading()
								this.$notice.show({
									title: _this.$t('tips'),
									content: tips,
									showCancel: false,
									confirmText: _this.$t('ok')
								})
							}
						}
					}
					_this.$http.uploadFile(con)
				} else {
					uni.showToast({
						title: this.$t('upload_charge_pic'),
						image: '../../static/icon/error.png',
						duration: 2000
					})
				}
			},
			// 选择图片方法
			ChooseImage() {
				var _this = this;
				uni.chooseImage({
					count: 1,
					sizeType: ['original', 'compressed'],
					sourceType: ['album'],
					success: (res) => {
						_this.picture = res.tempFilePaths[0];
						_this.imgList = [res.tempFilePaths[0]];
						// console.log('选择的图片路径:', _this.picture);

						_this.uploadPic()
					},
					fail: (err) => {
						// console.error('选择图片失败:', err);
						uni.showToast({
							title: '选择图片失败',
							icon: 'none'
						});
					}
				});
			},
			ViewImage() {
				if (!this.picture) {
					return; // 如果没有选择图片或图片为空，则不执行预览操作
				}
				uni.previewImage({
					urls: [this.picture],
					current: this.picture // 保持不变，当前预览图片URL
				});
			},
			DelImg(e) {
				/*
				this.$notice.show({
					title: '删除图片',
					content: '确定要删除这张图片吗？',
					cancelText: '取消',
					confirmText: '确定',
					success: res => {
						if (res.confirm) {
							this.picture = '';
						}
					}
				})*/
				this.picture = '';
			},
			checkboxChange(e) {
				this.trade_list.forEach(ele => {
					ele.checked = false
				})
				this.$set(e, 'checked', true)

				if (typeof(e.amount) == 'string') {
					if (e.amount.indexOf("-") > -1) {
						e.amount = e.amount.replace("-", "")
					}
				}

				this.$set(this.chargeForm, 'amount', e.amount)
				this.$set(this.chargeForm, 'transaction_id', e.transaction_id)
				this.$set(this.chargeForm, 'transaction_datetime', e.oder_time)
			},
			submit() {
				// 手动充值
				var _this = this;
				uni.showLoading({
					title: _this.$t('loading_dots')
				});
				// 如果有图片需要上传
				if (_this.chargeForm.charge_way && _this.picture) {
					// 先上传图片，再提交表单
					uni.uploadFile({
						url: _this.$http.baseUrl + '/charge/recharge', // 替换为你的完整URL
						filePath: _this.picture,
						name: 'image', // 这个name要和后端接收的字段名一致
						formData: {
							transaction_id: _this.chargeForm.transaction_id,
							amount: _this.amount,
							charge_way: _this.chargeForm.charge_way,
							bank_code: _this.chargeForm.bank_code
						},
						header: {
							Authorization: _this.token // 手动添加 token
						},
						success: (uploadRes) => {
							uni.hideLoading();
							try {
								const data = JSON.parse(uploadRes.data);
								if (data.statusCode == 200) {
									setTimeout(() => {
										uni.reLaunch({
											url: './charge'
										})
									}, 2000)
									uni.showToast({
										title: this.$t('deposit_success')
									});
								} else {
									this.$notice.show({
										confirmText: this.$t('ok'),
										showCancel: false,
										title: this.$t('error_title'),
										content: data.message
									});
								}
							} catch (e) {
								// console.error('解析响应失败:', e);
								this.$notice.show({
									confirmText: this.$t('ok'),
									showCancel: false,
									title: this.$t('error_title'),
									content: this.$t('unknown_error')
								});
							}
						},
						fail: (err) => {
							uni.hideLoading();
							// console.error('上传失败:', err);
							this.$notice.show({
								confirmText: this.$t('ok'),
								showCancel: false,
								title: this.$t('error_title'),
								content: this.$t('upload_fail')
							});
						}
					});
				} else {
					// 旧自动直接充值
					let para = {
						transaction_id: _this.chargeForm.transaction_id,
						amount: _this.amount,
						charge_way: _this.chargeForm.charge_way,
						bank_code: _this.chargeForm.bank_code
					};

					_this.$http.post('/charge/recharge_apply', para, res => {
						uni.hideLoading();
						if (res.statusCode == 200) {
							setTimeout(() => {
								uni.reLaunch({
									url: './charge'
								})
							}, 2000)
							uni.showToast({
								title: this.$t('deposit_success')
							});
						} else {
							this.$notice.show({
								confirmText: this.$t('ok'),
								showCancel: false,
								title: this.$t('error_title'),
								content: res.data.message
							});
						}
					});
				}
			},
			// submit() {
			// 	var _this = this;
			// 	uni.showLoading({
			// 		title: 'Loading...'
			// 	})
			// 	let para = {
			// 		transaction_id: _this.chargeForm.transaction_id,
			// 		// transaction_datetime: _this.chargeForm.transaction_datetime,
			// 		amount: _this.amount,
			// 		charge_way: _this.chargeForm.charge_way,
			// 		bank_code: _this.chargeForm.bank_code
			// 	}
			// 	if (_this.chargeForm.charge_way) {
			// 		para.image = _this.picture
			// 	}
			// 	_this.$http.post('/charge/apply_charge', para, res => {
			// 		uni.hideLoading()

			// 		if (res.statusCode == 200) {
			// 			uni.showToast({
			// 				title: 'success'
			// 			})
			// 		} else {
			// 			this.$notice.show({
			// 				confirmText: 'OK',
			// 				showCancel: false,
			// 				title: 'Error',
			// 				content: res.data.message
			// 			})
			// 		}
			// 	})
			// },
			auto_submit() {
				var _this = this;
				if (_this.$toolbox.click_too_fast(.5)) return
				if (_this.modal_type == 'one-time') {
					_this.chargeForm.acc_name = _this.card_conf.acc_name
					_this.chargeForm.acc_number = _this.card_conf.acc_number
				}
				if (!_this.amount || !_this.chargeForm.acc_number)
					return
				// this.$notice.show({
				// 	title: 'comming soon',
				// 	showCancel: false,
				// })
				// return
				// let info = {
				// 	"state": "completed",
				// 	"tradeNo": "PI202506171500000005",
				// 	"outTradeNo": "1750171515560",
				// 	"amount": 3000.00,
				// 	"msgId": "f869c204b7874cb69d6b83808922dcba",
				// 	"success": true,
				// 	"orderId": "f869c204b7874cb69d6b83808922dcba",
				// 	"orderStatus": 2
				// }
				// uni.navigateTo({
				// 	url: `/pages/payment/payment?id=${'f869c204b7874cb69d6b83808922dcba'}`
				// });
				let para = Object.assign({}, _this.chargeForm)
				para.amount = _this.amount
				para.memo = 'memo'
				para.subject = `charge ${para.amount}`
				delete para.transaction_id
				let acc = this.card_list.find(item => item.checked)
				para.card_id = acc.id
				// uni.showLoading({
				// 	title: 'Loading...'
				// })
				_this.$http.post('/charge_apply/add', para, res => {
					// _this.modalName = ''
					// uni.hideLoading()
					let data = res.data
					console.log(data)
					if (data.code == 200) {
						let order = data.data;
						uni.showToast({
							title: _this.$t('success_excl')
						})
						_this.card_conf = _this.$options.data().card_conf
						uni.navigateTo({
							url: `/pages/payment/payment?id=${order.tradeOrderId}`
							// url: '/pages/payment/payment?id=' + data.data.tradeOrderId
						});
					} else if (data.code == 409) {
						let order = data.data;
						this.$notice.show({
							title: _this.$t('tips'),
							content: res.data.message,
							confirmText: _this.$t('pay_other'),
							showCancel: false,
							success: (res1) => {
								if (res1.confirm) {
									uni.navigateTo({
										url: `/pages/payment/payment?id=${order.out_order_id}`
										// url: '/pages/payment/payment?id=' + data.data.tradeOrderId
									});
								}
							}
						})

					} else {
						this.$notice.show({
							confirmText: this.$t('ok'),
							showCancel: false,
							title: this.$t('error_title'),
							content: res.data.message
						})
					}
				})
			},


			set_info() {
				this.userInfo = Object.assign({}, this.$store.state.userInfo)
				// this.auto_config.realname = this.userInfo.BANK_USER_NAME
				// this.auto_config.phone = this.userInfo.BANK_CARD
			},

			// 查看充值记录
			viewChargeHistory() {
				uni.navigateTo({
					url: './charge_history'
				});
			},

		},
		onLoad() {
			// this.getList();
			this.get_bank_card_list()
			this.get_agent_bank_card()
			this.set_info()
			// this.modalName = 'auto_modal'
		}
	}
</script>

<style>
	.myrect {
		width: 90%;
		margin-left: 5%;
		margin-top: 10px;
		border-radius: 13px;
	}

	.myrect1 {
		width: 44%;
		margin-left: 4%;
		margin-top: 10px;
		border-radius: 13px;
	}

	.add {
		position: fixed;
		bottom: 5vh;
		margin-left: calc(50vw - 7.5vw);
		width: 15vw;

	}

	.text-underline {
		height: 8upx;
		width: 25%;
		border-radius: 10px;
		/* background-image: linear-gradient(45deg, rgb(177, 137, 94), rgb(220, 193, 160)); */
		background-color: #a0a0a0;
		/* margin-top: 2px; */
	}



	.tips {
		width: 100%;
		padding: 15px 30px;
		font-family: __Inter_7be8ac, __Inter_Fallback_7be8ac;
		font-weight: 600;
		line-height: 1.6;
		color: rgb(51, 51, 51);
		text-align: initial;
		font-size: 12px;
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

	.deposit-shadow {
		box-shadow: 0px 4px 4px rgba(0, 0, 0, 0.25);
	}

	.search-rec {
		border-radius: 3px;
		border: #0074BE 1px solid;
		height: 37px;
		display: flex;
		flex-direction: row;
		align-items: center;
		padding: 0 12px;
		margin-top: 15px;
	}

	.bank-select {
		display: flex;
		flex-direction: column;
		background-color: white;
		border-radius: 20px;
		top: 76px;
		padding: 10px 0;
		border: solid 1px #C0BEBE;
		position: absolute;
		width: calc(680upx - 22px);
		z-index: 999;
	}

	.round-border {
		border: solid darkgray 1px;
	}

	.no-right-border {
		border: solid darkgray 1px;
		border-right: none;
		padding-right: 1px;
	}

	.charge-history-btn {
		padding: 3px 6px;
		border-radius: 6px;
		background-color: rgba(0, 129, 255, 0.1);
		border: 1px solid #0081ff;
		display: flex;
		flex-direction: row;
		align-items: center;
	}
</style>