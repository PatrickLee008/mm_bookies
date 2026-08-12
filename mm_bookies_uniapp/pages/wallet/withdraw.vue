<template>
	<view class="withdraw-component">
		<!-- from tangjq--- Withdraw 组件内容从 withdraw.vue 提取 -->
		<scroll-view scroll-y class="withdraw-scroll" @scroll="onScrollEmit">
			<!-- from tangjq--- 银行卡列表界面（仿照deposit.vue） -->
			<view class="bank-list-container">
				<!-- 银行卡列表 -->
				<view class="bank-card-item" v-for="(card,index) in card_list" :key="index">
					<view class="bank-card-content" @click="selectCard(card)">
						<image class="bank-icon" :src="`/static/icon/register/${card.bank_code}.png`"></image>
						<text class="bank-name">{{card.bank_code}}</text>
						<text class="account-number">*****{{(card.acc_number || '').slice(-4)}}</text>
						<!-- 删除按钮 -->
						<view class="delete-btn" @click.stop="removeBank(card)" v-if="!card.is_default">
							<text class="cuIcon-delete delete-icon"></text>
						</view>
					</view>
				</view>

				<!-- 添加银行账户按钮 -->
				<view class="add-bank-btn" @click="show_add_modal('add')">
					<text class="add-bank-text">{{ $t('add bank account') }}</text>
				</view>
			</view>
		</scroll-view>

		<!-- from tangjq--- 提现详情弹窗（仿照deposit-modal-dialog） -->
		<view class="cu-modal" style="z-index: 9999;" :class="modalName=='withdraw_modal'?'show':''">
			<view class="withdraw-modal-dialog">
				<!-- 标题栏 -->
				<view class="withdraw-modal-header">
					<text class="withdraw-modal-title">{{ $t('Withdraw') }}</text>
					<text class="withdraw-modal-close" @click="modalName = ''">✕</text>
				</view>

				<!-- 用户账户信息 -->
				<view class="user-account-section">
					<text class="section-title">{{ $t('user_account') }}</text>

					<!-- Bank Type -->
					<view class="info-row">
						<text class="info-label">{{ $t('bank type') }}</text>
						<view class="bank-type-value">
							<image class="bank-type-icon" :src="`/static/icon/register/${selectedCard.bank_code}.png`"></image>
							<text class="bank-type-text">{{selectedCard.bank_code}}</text>
						</view>
					</view>

					<!-- Account No -->
					<view class="info-row">
						<text class="info-label">{{ $t('account_number') }}</text>
						<view class="info-value-box">
							<text class="info-value-text">{{selectedCard.acc_number}}</text>
						</view>
					</view>

					<!-- User Name -->
					<view class="info-row">
						<text class="info-label">{{ $t('account_ame') }}</text>
						<view class="info-value-box">
							<text class="info-value-text">{{selectedCard.acc_name}}</text>
						</view>
					</view>
				</view>

				<!-- from tangjq--- 钱包信息部分 -->
				<view class="wallet-info-section">
					<view class="wallet-info-row">
						<text class="wallet-info-label">{{ $t('wallet_balance') }} :</text>
						<text class="wallet-info-value">{{$toolbox.floor_format(userInfo.money)}}Ks</text>
					</view>
					<!-- <view class="wallet-info-row">
						<text class="wallet-info-label">{{ $t('amount_unlock') }} :</text>
						<text class="wallet-info-value">{{configs.amount_unlock || '0.00'}}</text>
					</view>
					<view class="wallet-info-row">
						<text class="wallet-info-label">{{ $t('turnover_limit_label') }} :</text>
						<text class="wallet-info-value">{{configs.turnover_limit || '0.00'}}</text>
					</view> -->
				</view>

				<!-- 金额输入 -->
				<view class="amount-section">
					<view class="amount-input-box">
						<input class="amount-input-field" type="number" @input='inputNum' v-model="amount" :placeholder="$t('enter_withdraw_amount')" />
					</view>
					<text class="amount-hint">Current Turnover: {{numberFormat(userInfo.current_turnover_accumulated)}}Ks | Rate Turnover: {{numberFormat(userInfo.required_turnover_accumulated)}}Ks </text>
					<text class="amount-hint">Minimum {{numberFormat(configs.withdraw_min_limit || 5000)}} Ks, Maximum {{numberFormat(configs.withdraw_max_limit || 5000000)}} Ks</text>

					<!-- 快速金额选择 -->
					<view class="quick-amount-grid">
						<view class="quick-amount-btn" :class="amount==item?'selected':''" v-for="(item,index) in withdraw_amount_list" :key="index" @click="amount = item">
							{{numberFormat(item)}}
						</view>
					</view>
				</view>

				<!-- Continue 按钮 -->
				<button class="continue-btn" :disabled="amount_error" @click="withdrawSubmit()">
					{{ $t('continue_btn') }}
				</button>
			</view>
		</view>

		<!-- from tangjq--- 添加/编辑银行卡 Modal（仿照deposit.vue） -->
		<view class="cu-modal" style="z-index: 9999;" :class="modalName=='add_modal'?'show':''">
			<view class="add-bank-dialog">
				<!-- 标题栏 -->
				<view class="dialog-header">
					<text class="dialog-title">{{ $t('bind_wallet_account') }}</text>
					<text class="dialog-close" @click="modalName = ''">✕</text>
				</view>

				<!-- 副标题 -->
				<view class="dialog-subtitle">
					<text>{{ $t('choose_account_type') }}</text>
				</view>

				<!-- 银行图标选择 -->
				<view class="bank-icon-selector">
					<view class="bank-icon-item" v-for="(bank,index) in bank_add_list" :key="index" @click="select_modal_bank(bank)" :class="card_conf.bank_code==bank.bank_code?'selected':''">
						<image class="bank-icon-img" :src="`/static/icon/register/${bank.bank_code}.png`"></image>
					</view>
				</view>

				<!-- 表单 -->
				<view class="dialog-form">
					<!-- Account No -->
					<view class="form-group">
						<text class="form-label">{{ $t('account_number') }}</text>
						<input class="form-input" type="number" maxlength="17" @input="set_add_disable()" :placeholder="$t('enter_account_number')" v-model="card_conf.acc_number" />
					</view>

					<!-- User Name -->
					<view class="form-group">
						<text class="form-label">{{ $t('account_ame') }}</text>
						<input class="form-input" type="text" @input="set_add_disable()" :placeholder="$t('account_ame')" v-model="card_conf.acc_name" />
					</view>
				</view>

				<!-- Confirm 按钮 -->
				<button class="confirm-btn" :class="add_disable?'disabled':''" @click="add_card()" :disabled="add_disable">
					{{ $t('confirm') }}
				</button>
			</view>
		</view>
		<!-- delete bank confirm dialog -->
	<ConfirmDialog
		:visible="showDeleteConfirm"
		:title="$t('remove_bank_title') || 'Delete Bank Account'"
		:message="$t('remove_bank_confirm')"
		:confirmText="$t('Confirm')"
		:cancelText="$t('Cancel')"
		@confirm="confirmDeleteBank"
		@cancel="showDeleteConfirm = false"
	/>
	<!-- 提现结果提示弹窗（单按钮OK模式） -->
	<ConfirmDialog
		:visible="showResultDialog"
		:title="resultDialogTitle"
		:message="resultDialogMessage"
		:confirmText="$t('ok')"
		:showCancel="false"
		@confirm="showResultDialog = false"
	/>
	</view>

</template>

<script>
	// from tangjq--- Withdraw 组件,从 withdraw.vue 提取并简化
	import config from '../../utils/config.js';
	import dateFormatUtils from "../../utils/utils.js"
import ConfirmDialog from '@/components/common/confirm-dialog.vue'

	export default {
		name: 'WalletWithdraw',
		components: {
			ConfirmDialog
		},
		data() {
			return {
				language: config.language,
				amount: '',
				amount_error: true,
				card_list: [],
				userInfo: {},
				configs: {},
				// from tangjq--- 添加银行卡相关变量
				modalName: '',
				card_conf: {},
				selectedCard: {}, // from tangjq--- 选中的银行卡
				withdraw_amount_list: [], // 提现快速金额列表（由系统配置动态生成）
				bank_add_list: [],
				add_disable: true,
				showDeleteConfirm: false,
				deleteTargetBank: null,
				// 提现结果弹窗
				showResultDialog: false,
				resultDialogTitle: '',
				resultDialogMessage: '',
			}
		},
		watch: {
			amount(val) {
				const rawAmount = parseInt(this.amount)
				const minLimit = parseInt(this.configs.withdraw_min_limit) || 5000;
				const maxLimit = parseInt(this.configs.withdraw_max_limit) || 5000000;
				this.amount_error = !(rawAmount >= minLimit && rawAmount <= maxLimit)
			},
			// 监听系统配置变化，动态更新提现金额选择列表
			configs: {
				handler(val) {
					if (val && (val.withdraw_min_limit || val.withdraw_max_limit)) {
						this.withdraw_amount_list = this.dynamicWithdrawAmountList;
					}
				},
				deep: true,
				immediate: true
			},
		},
		computed: {
			// 动态生成提现金额选择列表，基于系统配置的 min/max 限额
			dynamicWithdrawAmountList() {
				const min = parseInt(this.configs.withdraw_min_limit) || 5000;
				const max = parseInt(this.configs.withdraw_max_limit) || 5000000;
				const fixedList = [5000, 10000, 30000, 50000, 100000, 200000, 500000, 1000000];

				if (!min || !max || min >= max) {
					return fixedList;
				}

				// 从固定列表中筛选出在 min 和 max 之间的值（不包括两端）
				const middleValues = fixedList.filter((value) => value > min && value < max);

				// 从中间值中选择最多4个
				let selectedMiddle = [];
				if (middleValues.length <= 4) {
					selectedMiddle = middleValues;
				} else {
					const step = middleValues.length / 4;
					for (let i = 0; i < 4; i++) {
						const index = Math.floor(i * step);
						selectedMiddle.push(middleValues[index]);
					}
				}

				// 组合：[最小值, 中间值, 最大值]
				return [min, ...selectedMiddle, max];
			},
		},
		methods: {
			// from tangjq--- 滚动事件冒泡给父页面，用于驱动 header 收起/展开
			onScrollEmit(e) {
				this.$emit('contentScroll', e)
			},
			inputNum: function(evt) {
				let amount = evt.detail.value.replace('.', '')
				amount = amount ? parseInt(amount) : '0'
				const maxLimit = parseInt(this.configs.withdraw_max_limit) || 5000000;
				if (amount > maxLimit) {
					amount = maxLimit
				}
				this.$nextTick(function() {
					this.$set(this, 'amount', amount)
				})
			},
			numberFormat(number) {
				return dateFormatUtils.numFormat(number);
			},
			get_bank_card_list() {
				var _this = this;
				var para = {}
				_this.$http.get('/bank_card/get', {
					data: para
				}, (res) => {
					if (res.statusCode == 200) {
						_this.card_list = res.data.items;
					}
				})
			},
			// from tangjq--- 选择银行卡，打开提现弹窗
			selectCard(card) {
				this.selectedCard = card
				this.amount = ''
				this.modalName = 'withdraw_modal'
			},
			// from tangjq--- 提现提交
			withdrawSubmit() {
				var _this = this;

				// Validate amount（使用系统配置的动态限额）
				const rawAmount = parseInt(_this.amount)
				const minLimit = parseInt(_this.configs.withdraw_min_limit) || 5000;
				const maxLimit = parseInt(_this.configs.withdraw_max_limit) || 5000000;
				if (!rawAmount || rawAmount < minLimit || rawAmount > maxLimit) {
					uni.showToast({
						title: `Please enter valid amount (${_this.numberFormat(minLimit)} - ${_this.numberFormat(maxLimit)})`,
						icon: 'none'
					})
					return
				}

				// Validate card
				if (!_this.selectedCard || !_this.selectedCard.id) {
					uni.showToast({
						title: _this.$t('select_bank_card'),
						icon: 'none'
					})
					return
				}

				var para = {
					'card_id': _this.selectedCard.id,
					'money': rawAmount,
				}

				uni.showLoading({
					title: _this.$t('withdrawing')
				})

				// Call withdraw API
				_this.$http.post('/withdraw/apply', para, (res) => {
					uni.hideLoading()
					if (res.statusCode == 200) {
						_this.resultDialogTitle = _this.$t('Congratulations')
						_this.resultDialogMessage = `${_this.$t('Amount')}: ${_this.numberFormat(_this.amount)} Ks\n${_this.$t('withdraw_success')}`
						_this.showResultDialog = true

						// Update user balance in store
						var userInfo = _this.$store.state.userInfo
						userInfo.money = String(parseInt(userInfo.money.replaceAll(',', '')) - rawAmount);
						_this.$store.dispatch('saveUserInfo', userInfo);
						_this.userInfo = userInfo

						// Reset and close modal
						_this.amount = '';
						_this.modalName = ''
						_this.selectedCard = {}
					} else {
						_this.modalName = '';
						var tips = '';
						if (_this.language[res.data.message]) {
							tips = res.statusCode == 429 ? _this.language[res.data.message] + "(" + _this.$store.state.configs[res.data.message] + ")" : _this.$t(res.data.message);
						} else {
							tips = res.data.message;
						}
						_this.$nextTick(() => {
							_this.resultDialogTitle = _this.$t('tips')
							_this.resultDialogMessage = tips
							_this.showResultDialog = true
						});
					}
				})
			},
			// from tangjq--- 显示添加银行卡弹窗
			show_add_modal(type) {
				this.modalName = 'add_modal'
				const defaultBank = this.bank_add_list.length > 0 ? this.bank_add_list[0].bank_code : ''
				this.card_conf = {
					bank_code: defaultBank,
					acc_number: '',
					acc_name: '',
				}
				this.add_disable = true
			},
			// from tangjq--- 选择银行
			select_modal_bank(bank) {
				this.card_conf.bank_code = bank.bank_code
			},
			// from tangjq--- 设置添加按钮是否禁用
			set_add_disable() {
				if (!this.card_conf.acc_number || !this.card_conf.bank_code || !this.card_conf.acc_name) {
					this.add_disable = true
					return
				}
				this.add_disable = false
			},
			// from tangjq--- 添加银行卡
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
			// from tangjq--- 删除银行卡
			removeBank(bank) {
				var _this = this;
				_this.deleteTargetBank = bank
				_this.showDeleteConfirm = true
			},
			confirmDeleteBank() {
				var _this = this;
				_this.showDeleteConfirm = false
				var bank = _this.deleteTargetBank
				if (!bank) return
				var para = { id: bank.id }
				_this.$http.post('/bank_card/delete', para, (res) => {
					if (res.statusCode == 200) {
						uni.showToast({
							title: _this.$t('removed_success'),
							icon: 'success',
							duration: 2000
						})
						_this.get_bank_card_list()
					}
				})
				_this.deleteTargetBank = null
			},
			// 通过接口获取 admin 配置的可用银行列表并过滤 bank_add_list
			loadAvailableBanks() {
				var _this = this
				_this.$http.get('/agent_bankcard/available_banks', { data: {} }, (res) => {
					if (res.statusCode == 200 && res.data) {
						const auto = res.data.auto || []
						const manual = res.data.manual || []
						// 合并 auto 和 manual 中的 bank_code，去重
						const codes = new Set()
						auto.forEach(b => codes.add(b.bank_code))
						manual.forEach(b => codes.add(b.bank_code))
						const availableCodes = Array.from(codes)
			
						const allBanks = [
							{ bank_code: 'KBZ Pay', label: 'KBZPay', checked: true },
							{ bank_code: 'Wave Money', label: 'WavePAY', checked: false },
							{ bank_code: 'AYA', label: 'AYA PAY', checked: false },
							{ bank_code: 'Citizen Pay', label: 'Citizen Pay', checked: false },
							{ bank_code: 'UAB Pay', label: 'UAB Pay', checked: false },
						]
						_this.bank_add_list = allBanks.filter(bank => availableCodes.includes(bank.bank_code))
						if (_this.bank_add_list.length > 0) {
							_this.bank_add_list[0].checked = true
						}
					}
				})
			},
		},
		mounted() {
			// from tangjq--- 组件挂载时获取银行卡列表和用户信息
			this.get_bank_card_list()
			this.userInfo = Object.assign({}, this.$store.state.userInfo)
			this.configs = Object.assign({}, this.$store.state.configs)
			this.loadAvailableBanks()
			console.log(this.$store.state.configs);
		},
	}
</script>

<style lang="scss" scoped>
	.withdraw-component {
		width: 100%;
		height: 100%;
		display: flex;
		flex-direction: column;
	}

	.withdraw-scroll {
		flex: 1;
		height: 0;
	}

	/* from tangjq--- 银行卡列表样式（完全仿照deposit.vue） */
	.bank-list-container {
		padding: 20px 5px;
	}

	.bank-card-item {
		width: 100%;
		margin-bottom: 16px;
		border: 2px solid $color-primary;
		border-radius: 16px;
		background-color: #fff;
		overflow: hidden;
	}

	.bank-card-content {
		display: flex;
		flex-direction: row;
		align-items: center;
		padding: 10px;
		gap: 16px;
	}

	.bank-icon {
		width: 40px;
		height: 40px;
		border-radius: 8px;
		flex-shrink: 0;
	}

	.bank-name {
		flex: 1;
		font-size: 16px;
		font-weight: 700;
		color: #003D5B;
	}

	.account-number {
		font-size: 16px;
		font-weight: 400;
		color: #003D5B;
	}

	/* from tangjq--- 删除按钮样式 */
	.delete-btn {
		width: 32px;
		height: 32px;
		display: flex;
		align-items: center;
		justify-content: center;
		background-color: #FF4444;
		border-radius: 8px;
		margin-left: auto;
	}

	.delete-icon {
		color: #fff;
		font-size: 18px;
	}

	.add-bank-btn {
		width: 100%;
		height: 60px;
		border: 2px solid $color-primary;
		border-radius: 16px;
		background-color: #fff;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.add-bank-text {
		font-size: 18px;
		font-weight: 600;
		color: $color-primary;
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
		display: block;
		min-width: 0px;
		width: 100%;
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

	/* from tangjq--- 添加银行卡模态框样式（仿照deposit.vue） */
	.cu-modal {
		position: fixed;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		z-index: 9999;
		background-color: rgba(0, 0, 0, 0.6);
		display: none;
		align-items: center;
		justify-content: center;
	}

	.cu-modal.show {
		display: flex;
	}

	.add-bank-dialog {
		width: 90%;
		max-width: 600px;
		background-color: #fff;
		border-radius: 16px;
		padding: 24px 20px;
		position: relative;
	}

	.dialog-header {
		background-color: $color-primary;
		margin: -24px -20px 0;
		padding: 8px;
		border-radius: 16px 16px 0 0;
		display: flex;
		justify-content: center;
		align-items: center;
		position: relative;
	}

	.dialog-title {
		font-size: 16px;
		font-weight: 600;
		color: #fff;
		text-align: center;
	}

	.dialog-close {
		font-size: 20px;
		color: #fff;
		font-weight: 300;
		line-height: 1;
		cursor: pointer;
		position: absolute;
		right: 8px;
	}

	.dialog-subtitle {
		margin-top: 20px;
		margin-bottom: 16px;
		text-align: center;
	}

	.dialog-subtitle text {
		font-size: 12px;
		font-weight: 400;
		color: #333;
	}

	.bank-icon-selector {
		display: flex;
		flex-direction: row;
		justify-content: center;
		gap: 16px;
		margin-bottom: 24px;
	}

	.bank-icon-item {
		width: 40px;
		height: 40px;
		border-radius: 8px;
		overflow: hidden;
		border: 2px solid transparent;
	}

	.bank-icon-item.selected {
		border-color: #4FB3BF;
	}

	.bank-icon-img {
		width: 100%;
		height: 100%;
	}

	.dialog-form {
		margin-bottom: 24px;
	}

	.form-group {
		margin-bottom: 16px;
		display: flex;
		flex-direction: row;
		align-items: center;
	}

	.form-label {
		font-size: 12px;
		font-weight: 600;
		color: #000;
		width: 120px;
		flex-shrink: 0;
	}

	.form-input {
		flex: 1;
		height: 24px;
		border: 2px solid #4FB3BF;
		border-radius: 12px;
		font-size: 12px;
		color: #000;
		text-align: center;
	}

	.confirm-btn {
		width: 100%;
		height: 30px;
		background-color: $color-primary;
		border-radius: 12px;
		border: none;
		font-size: 15px;
		font-weight: 700;
		color: #fff;
		padding: 8px;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.confirm-btn.disabled {
		opacity: 0.5;
	}

	/* from tangjq--- 提现弹窗样式（仿照deposit-modal-dialog） */
	.withdraw-modal-dialog {
		width: 90%;
		max-width: 650px;
		background-color: #fff;
		border-radius: 16px;
		padding: 0;
		position: relative;
		max-height: 90vh;
		overflow-y: auto;
	}

	.withdraw-modal-header {
		background-color: $color-primary;
		padding: 8px;
		border-radius: 16px 16px 0 0;
		display: flex;
		justify-content: center;
		align-items: center;
		position: relative;
	}

	.withdraw-modal-title {
		font-size: 16px;
		font-weight: 600;
		color: #fff;
		text-align: center;
	}

	.withdraw-modal-close {
		font-size: 20px;
		color: #fff;
		font-weight: 300;
		line-height: 1;
		cursor: pointer;
		position: absolute;
		right: 8px;
	}

	.user-account-section {
		background-color: $bg-color-info;
		padding: 20px;
	}

	.section-title {
		font-size: 18px;
		font-weight: 700;
		color: $color-primary;
		display: block;
		text-align: center;
		margin-bottom: 16px;
	}

	.info-row {
		display: flex;
		flex-direction: row;
		align-items: center;
		margin-bottom: 12px;
	}

	.info-label {
		font-size: 12px;
		font-weight: 600;
		color: #000;
		width: 120px;
		flex-shrink: 0;
	}

	.bank-type-value {
		display: flex;
		flex-direction: row;
		align-items: center;
		gap: 8px;
	}

	.bank-type-icon {
		width: 35px;
		height: 35px;
		border-radius: 6px;
	}

	.bank-type-text {
		font-size: 12px;
		font-weight: 600;
		color: $color-primary;
	}

	.info-value-box {
		flex: 1;
		height: 24px;
		border: 2px solid #4FB3BF;
		border-radius: 12px;
		display: flex;
		align-items: center;
		justify-content: center;
		padding: 0 16px;
	}

	.info-value-text {
		font-size: 12px;
		color: $color-primary;
		font-weight: 600;
	}

	/* from tangjq--- 钱包信息部分样式 */
	.wallet-info-section {
		background-color: $bg-color-info;
		padding: 0 20px 20px;
	}

	.wallet-info-row {
		display: flex;
		flex-direction: row;
		align-items: center;
		justify-content: space-between;
		margin-bottom: 12px;
	}

	.wallet-info-label {
		font-size: 14px;
		font-weight: 400;
		color: $color-primary;
	}

	.wallet-info-value {
		font-size: 16px;
		font-weight: 700;
		color: $color-primary;
	}

	.amount-section {
		padding: 20px;
	}

	.amount-input-box {
		width: 100%;
		height: 40px;
		background-color: $bg-color-info;
		border-radius: 12px;
		display: flex;
		align-items: center;
		justify-content: center;
		margin-bottom: 8px;
	}

	.amount-input-field {
		font-size: 16px;
		font-weight: 600;
		color: $color-primary;
		text-align: center;
		border: none;
		background: transparent;
		width: 100%;
	}

	.amount-input-field::-webkit-input-placeholder {
		font-size: 14px;
		font-weight: 400;
		font-style: italic;
		color: #999;
	}

	.amount-hint {
		font-size: 12px;
		color: #E02B2B;
		text-align: center;
		display: block;
		margin-bottom: 16px;
	}

	.quick-amount-grid {
		display: grid;
		grid-template-columns: repeat(3, 1fr);
		gap: 12px;
	}

	.quick-amount-btn {
		height: 30px;
		background-color: $color-primary;
		border-radius: 12px;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 12px;
		font-weight: 600;
		color: #fff;
		cursor: pointer;
	}

	.quick-amount-btn.selected {
		background-color: #4FB3BF;
	}

	.quick-amount-btn:active {
		background-color: #4FB3BF;
	}

	.continue-btn {
		width: calc(100% - 40px);
		height: 30px;
		background-color: $color-primary;
		border-radius: 12px;
		border: none;
		font-size: 16px;
		font-weight: 700;
		color: #fff;
		margin: 0 20px 20px;
		display: flex;
		align-items: center;
		justify-content: center;
		padding: 8px;
	}

	.continue-btn[disabled] {
		opacity: 0.5;
	}
</style>