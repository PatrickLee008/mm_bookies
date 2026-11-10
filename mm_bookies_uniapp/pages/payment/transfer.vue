<template>
	<view class="full-page">
		<zw-header @headerHeightChange="onHeaderHeightChange"></zw-header>
		<view class="header-placeholder" :style="{ height: headerHeight + 'px' }"></view>

		<view class="page-heading">
			<view class="heading-back" @click="goBack">
				<theme-icon name="back" class="back-icon"
					color="var(--theme-icon-primary, var(--theme-primary))"></theme-icon>
				<text>{{ $t('back') }}</text>
			</view>
			<text class="page-title">{{ $t('deposit') }}</text>
		</view>

		<scroll-view scroll-y class="transfer-content" @scroll="handleHeaderScroll" @scrolltoupper="handleHeaderTop">
			<view v-if="loading" class="state-card">{{ $t('loading_dots') }}</view>
			<view v-else-if="pageError" class="state-card error-state">
				<text>{{ pageError }}</text>
				<view class="back-action" @click="goBack">{{ $t('back_to_home') }}</view>
			</view>

			<block v-else>
				<view class="account-card">
					<view class="account-card-title">{{ $t('payee_account') }}</view>
					<view v-if="bankCode" class="account-row">
						<text class="account-label">{{ $t('bank_type') }}</text>
						<view class="bank-type-value">
							<image class="bank-type-icon" :src="bankIcon(bankCode)" mode="aspectFit"></image>
							<text>{{ normalizeBank(bankCode) }}</text>
						</view>
					</view>
					<view v-if="cashCode" class="account-row">
						<text class="account-label">{{ $t('cash_code') }}</text>
						<view class="account-copy-field">
							<text class="account-value strong">{{ cashCode }}</text>
							<view class="copy-action" @click="copy(cashCode)">
								<text>{{ $t('copy') }}</text>
								<theme-icon name="copy" size="16px" color="#fff"></theme-icon>
							</view>
						</view>
					</view>
					<view v-if="receiveAccount" class="account-row">
						<text class="account-label">{{ $t('account_no') }}</text>
						<view class="account-copy-field">
							<text class="account-value">{{ receiveAccount }}</text>
							<view class="copy-action" @click="copy(receiveAccount)">
								<text>{{ $t('copy') }}</text>
								<theme-icon name="copy" size="16px" color="#fff"></theme-icon>
							</view>
						</view>
					</view>
					<view v-if="receiveAccountName" class="account-row">
						<text class="account-label">{{ $t('user_name') }}</text>
						<view class="account-copy-field">
							<text class="account-value">{{ receiveAccountName }}</text>
							<view class="copy-action" @click="copy(receiveAccountName)">
								<text>{{ $t('copy') }}</text>
								<theme-icon name="copy" size="16px" color="#fff"></theme-icon>
							</view>
						</view>
					</view>
					<view v-if="!receiveAccount && !cashCode" class="account-missing">
						{{ $t('account_number_missing') }}
					</view>
				</view>

				<view class="payment-summary">
					<view class="summary-row">
						<text class="amount-label">{{ $t('transfer_amount') }} :</text>
						<text class="amount-value">{{ amountText }} MMK</text>
					</view>
					<view class="validity-row">
						<text class="field-label">{{ $t('valid_period') }}</text>
						<text class="validity-date">{{ expiryText }}</text>
					</view>
					<view v-if="state === 'paying'" class="countdown">{{ countdownText }}</view>
					<view v-else-if="state === 'success'" class="status-message success">
						{{ $t('pay_completed') }}
					</view>
					<view v-else class="status-message expired">
						{{ state === 'timeout' ? $t('payment.orderTimeoutTip') : 'Order cancelled' }}
					</view>
				</view>

				<view v-if="needsTxnLast5 && state === 'paying'" class="txn-container">
					<input class="txn-input" type="number" maxlength="5" v-model="txnLast5"
						:disabled="submitted"
						:placeholder="$t('enter_txn_last5')" placeholder-class="txn-placeholder"
						@input="onTxnInput" />
					<text v-if="submitted" class="txn-hint">{{ $t('check_transaction_records') }}</text>
				</view>

				<view class="continue-btn" :class="{ disabled: !canContinue }" @click="continuePayment">
					{{ submitted && state !== 'success' ? $t('submitted') : $t('continue_btn') }}
				</view>

				<view v-if="cancelable && state === 'paying'" class="cancel-order" @click="cancelOrder">
					{{ $t('cancel_order') }}
				</view>

				<view class="notice-card">
					<view class="notice-row" v-for="i in 3" :key="i">
						<text class="notice-dot">•</text>
						<text class="notice-text">{{ $t('transfer_notice_' + i) }}</text>
					</view>
					<text class="notice-warning">{{ $t('same_account_payment') }}</text>
				</view>
			</block>
		</scroll-view>

		<PayModal :visible="qrVisible" :order="qrOrder" @close="onUnexpectedQrClose"
			@payment-url="handleQrPaymentUrl" @payment-page="handleQrPaymentPage" />
	</view>
</template>

<script>
	import headerCollapse from '@/mixins/headerCollapse.js'
	import PayModal from '@/components/payment/PayModal.vue'
	import { openPaymentUrl } from '@/utils/payment-flow.js'
	import dateFormatUtils from '../../utils/utils.js'

	const TXN_LAST5_CHANNELS = ['MCPay', 'KingPay']
	const CANCELABLE_CHANNELS = ['VIPPay_CashCode']

	export default {
		components: { PayModal },
		mixins: [headerCollapse],
		data() {
			return {
				orderId: '',
				channel: '',
				amount: '',
				bankCode: '',
				cashCode: '',
				expireAt: '',
				receiveAccount: '',
				receiveAccountName: '',
				txnLast5: '',
				submitted: false,
				submitting: false,
				loading: true,
				pageError: '',
				state: 'paying',
				remain: 0,
				timer: null,
				pollTimer: null,
				qrVisible: false,
				qrOrder: {}
			}
		},
		computed: {
			needsTxnLast5() {
				return TXN_LAST5_CHANNELS.indexOf(this.channel) !== -1
			},
			cancelable() {
				return CANCELABLE_CHANNELS.indexOf(this.channel) !== -1
			},
			canContinue() {
				if (this.state === 'success') return true
				if (this.state !== 'paying') return false
				if (!this.needsTxnLast5) return true
				return this.submitted || (/^\d{5}$/.test(this.txnLast5) && !this.submitting)
			},
			amountText() {
				return dateFormatUtils.numFormat(String(this.amount || '').replace(/,/g, ''))
			},
			expiryText() {
				if (!this.expireAt) return '--'
				const value = String(this.expireAt)
				const date = new Date(value.replace(' ', 'T'))
				if (isNaN(date.getTime())) return value
				const pad = number => String(number).padStart(2, '0')
				return pad(date.getDate()) + '-' + pad(date.getMonth() + 1) + '-' + date.getFullYear() + ' ' +
					pad(date.getHours()) + ':' + pad(date.getMinutes()) + ':' + pad(date.getSeconds())
			},
			countdownText() {
				const seconds = Math.max(0, this.remain)
				const hours = Math.floor(seconds / 3600)
				const minutes = Math.floor((seconds % 3600) / 60)
				const remainingSeconds = seconds % 60
				return [hours, minutes, remainingSeconds].map(value => String(value).padStart(2, '0')).join(':')
			}
		},
		watch: {
			state(value) {
				if (value === 'success') {
					this.stopTimers()
					uni.$emit('userInfo:refresh')
				} else if (value === 'timeout' || value === 'cancelled') {
					this.stopTimers()
				}
			}
		},
		onLoad(options) {
			this.orderId = String(options.id || '')
			this.channel = String(options.channel || '')
			this.amount = String(options.amount || '')
			this.bankCode = String(options.bank_code || '')
			this.expireAt = String(options.expire_time || '')
			this.txnLast5 = String(options.txn_last5 || '')
			this.submitted = !!this.txnLast5
			this.cashCode = String(options.cash_code || '')

			if (!this.orderId) {
				this.loading = false
				this.pageError = 'Payment order ID is missing'
				return
			}
			this.loadPayInfo()
		},
		onUnload() {
			this.stopTimers()
		},
		methods: {
			normalizeBank(code) {
				const aliases = {
					KBZ: 'KBZ Pay',
					KBZPAY: 'KBZ Pay',
					WaveMoney: 'Wave Money',
					WAVEPAY: 'Wave Money',
					AYAPAY: 'AYAPAY',
					AYABANK: 'AYA BANK'
				}
				return aliases[code] || code
			},
			bankIcon(code) {
				return '/static/icon/register/' + this.normalizeBank(code) + '.png'
			},
			loadPayInfo() {
				this.$http.post('/charge_apply/payinfo', { id: this.orderId }, (res) => {
					this.loading = false
					const data = res.data || {}
					if (data.code !== 20000 || !data.data) {
						this.pageError = data.message || 'Unable to load payment information'
						return
					}

					const info = data.data
					this.receiveAccount = info.receive_account || ''
					this.receiveAccountName = info.receive_account_name || ''
					this.cashCode = info.cash_code || this.cashCode
					if (info.receive_bank_code) this.bankCode = info.receive_bank_code

					if (info.success) {
						this.state = 'success'
						return
					}
					if (info.timeout < 0) {
						this.state = 'timeout'
						return
					}
					if (info.timeout > 0) {
						this.remain = Number(info.timeout)
					} else if (this.expireAt) {
						const expires = new Date(this.expireAt.replace(' ', 'T')).getTime()
						if (!isNaN(expires)) this.remain = Math.max(0, Math.floor((expires - Date.now()) / 1000))
					}

					if (info.qrcode) {
						this.openQr(info.qrcode)
						return
					}
					if (/^https?:\/\//i.test(info.payment_url || '')) {
						this.startTimers()
						this.launchPaymentUrl(info.payment_url)
						return
					}
					if (!this.receiveAccount && !this.cashCode) {
						this.pageError = 'Payment details are unavailable'
						return
					}
					this.startTimers()
				}, {
					fail: () => {
						this.loading = false
						this.pageError = 'Unable to load payment information'
					}
				})
			},
			openQr(qrcode) {
				this.qrOrder = {
					id: this.orderId,
					pay_channel: this.channel,
					money: this.amount,
					QRCODE: qrcode,
					REMAINING_SECONDS: this.remain,
					expire_time: this.expireAt
				}
				this.qrVisible = true
			},
			startTimers() {
				this.stopTimers()
				this.timer = setInterval(() => {
					if (this.remain > 0) {
						this.remain -= 1
						if (this.remain === 0) this.state = 'timeout'
					}
				}, 1000)
				this.pollTimer = setInterval(() => this.pollStatus(), 2000)
			},
			stopTimers() {
				if (this.timer) {
					clearInterval(this.timer)
					this.timer = null
				}
				if (this.pollTimer) {
					clearInterval(this.pollTimer)
					this.pollTimer = null
				}
			},
			pollStatus() {
				if (!this.orderId || this.state !== 'paying') return
				this.$http.post('/charge_apply/status', { id: this.orderId }, (res) => {
					const data = res.data || {}
					if (data.code !== 20000) return
					if (typeof data.remaining_seconds === 'number') this.remain = data.remaining_seconds
					if (data.status === 'Success') {
						this.state = 'success'
					} else if (data.status === 'Timeout') {
						this.state = 'timeout'
					} else if (data.status === 'Cancelled') {
						this.state = 'cancelled'
					}
				})
			},
			onTxnInput(event) {
				this.txnLast5 = String(event.detail.value || '').replace(/\D/g, '').slice(0, 5)
			},
			continuePayment() {
				if (!this.canContinue) return
				if (this.state === 'success' || this.submitted || !this.needsTxnLast5) {
					this.goBack()
					return
				}
				this.submitTxn()
			},
			submitTxn() {
				if (!/^\d{5}$/.test(this.txnLast5) || this.submitting || this.submitted) return
				this.submitting = true
				this.$http.post('/charge_apply/submit_txn', {
					id: this.orderId,
					txn_last5: this.txnLast5
				}, (res) => {
					this.submitting = false
					const data = res.data || {}
					if (data.code === 20000) {
						this.submitted = true
						uni.showToast({ title: data.message || 'Submitted', icon: 'none' })
						return
					}
					uni.showToast({ title: data.message || 'Failed to submit transaction ID', icon: 'none' })
				}, {
					fail: () => {
						this.submitting = false
						uni.showToast({ title: 'Network error', icon: 'none' })
					}
				})
			},
			copy(value) {
				if (!value) return
				uni.setClipboardData({
					data: String(value),
					success: () => uni.showToast({ title: this.$t('copy'), icon: 'none' })
				})
			},
			cancelOrder() {
				this.$notice.confirm(
					this.$t('cancel_order_confirm'),
					() => {
						this.$http.post('/charge_apply/cancel', { order_id: this.orderId }, (res) => {
							const data = res.data || {}
							if (data.code === 20000) {
								this.state = 'cancelled'
								uni.showToast({ title: this.$t('order_cancelled'), icon: 'none' })
								return
							}
							uni.showToast({ title: data.message || 'Unable to cancel', icon: 'none' })
						}, {
							fail: () => uni.showToast({ title: 'Unable to cancel, please try again', icon: 'none' })
						})
					},
					null,
					{ confirmText: this.$t('confirm'), cancelText: this.$t('keep_order') }
				)
			},
			launchPaymentUrl(url) {
				if (!openPaymentUrl(url)) {
					this.pageError = 'Payment link unavailable'
				}
			},
			handleQrPaymentUrl(url) {
				this.qrVisible = false
				this.startTimers()
				this.launchPaymentUrl(url)
			},
			handleQrPaymentPage(order) {
				this.qrVisible = false
				this.receiveAccount = order.receive_account || ''
				this.receiveAccountName = order.receive_account_name || ''
				this.startTimers()
			},
			onUnexpectedQrClose() {
				this.qrVisible = false
				this.goBack()
			},
			goBack() {
				this.stopTimers()
				const refresh = () => {
					uni.$emit('charge:refresh')
					uni.$emit('userInfo:refresh')
				}
				uni.navigateBack({
					success: refresh,
					fail: () => {
						refresh()
						uni.redirectTo({ url: '/pages/wallet/deposit_page?tab=1' })
					}
				})
			}
		}
	}
</script>

<style lang="scss" scoped>
	.full-page {
		min-height: var(--app-viewport-height, 100vh);
		display: flex;
		flex-direction: column;
		background: #fff;
	}

	.header-placeholder {
		width: 100%;
		flex-shrink: 0;
	}

	.page-heading {
		display: flex;
		align-items: center;
		justify-content: space-between;
		height: 48px;
		padding: 0 20px;
		border-bottom: 1px solid $border-color;
		flex-shrink: 0;
	}

	.heading-back {
		display: flex;
		align-items: center;
		gap: 8px;
		color: $color-primary;
		font-size: 14px;
	}

	.back-icon {
		width: 24px;
		height: 24px;
	}

	.page-title {
		color: $color-primary;
		font-size: 14px;
		font-weight: 700;
		text-transform: uppercase;
	}

	.transfer-content {
		flex: 1;
		height: 0;
		padding: 16px 20px 30px;
		box-sizing: border-box;
	}

	.state-card {
		padding: 30px 18px;
		border: 1px solid $border-color;
		border-radius: 10px;
		color: $text-color-secondary;
		font-size: 14px;
		text-align: center;
	}

	.error-state {
		color: #E02B2B;
	}

	.back-action {
		margin-top: 18px;
		padding: 11px;
		border-radius: 8px;
		background: $color-primary;
		color: #fff;
	}

	.account-card {
		margin-bottom: 16px;
		padding: 14px 18px;
		border-radius: 12px;
		background: $bg-color-info;
	}

	.account-card-title {
		margin-bottom: 12px;
		color: $color-primary;
		font-size: 15px;
		font-weight: 700;
		text-align: center;
	}

	.account-row {
		display: flex;
		align-items: center;
		min-height: 34px;
		margin-bottom: 7px;
	}

	.account-label {
		flex: 0 0 114px;
		padding-left: 18px;
		color: $color-primary;
		font-size: 12px;
		font-weight: 600;
		box-sizing: border-box;
	}

	.bank-type-value {
		flex: 1;
		display: flex;
		align-items: center;
		justify-content: flex-end;
		gap: 8px;
		padding-right: 22px;
		color: $color-primary;
		font-size: 13px;
		font-weight: 600;
	}

	.bank-type-icon {
		width: 22px;
		height: 22px;
	}

	.account-copy-field {
		flex: 1;
		min-width: 0;
		display: flex;
		align-items: center;
		height: 30px;
		border: 1px solid $color-primary;
		border-radius: 16px;
		background: #fff;
		overflow: hidden;
	}

	.account-value {
		flex: 1;
		min-width: 0;
		padding: 0 10px;
		color: $color-primary;
		font-size: 12px;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}

	.account-value.strong {
		letter-spacing: 1px;
	}

	.copy-action {
		display: flex;
		align-items: center;
		gap: 5px;
		align-self: stretch;
		flex-shrink: 0;
		padding: 0 10px;
		background: $color-primary;
		color: #fff;
		font-size: 12px;
	}

	.account-missing {
		padding: 10px 0 2px;
		color: #E02B2B;
		font-size: 12px;
	}

	.payment-summary {
		margin-bottom: 14px;
	}

	.summary-row {
		display: flex;
		align-items: center;
		justify-content: space-between;
		margin-bottom: 12px;
	}

	.amount-label {
		color: $color-primary;
		font-size: 14px;
		font-weight: 600;
	}

	.amount-value {
		color: $color-primary;
		font-size: 14px;
		font-style: italic;
		font-weight: 700;
	}

	.validity-row {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 10px;
	}

	.field-label {
		color: $text-color;
		font-size: 12px;
	}

	.validity-date {
		color: $text-color;
		font-size: 12px;
		text-align: right;
	}

	.countdown {
		margin-top: 12px;
		color: #E02B2B;
		font-size: 22px;
		font-weight: 700;
		font-variant-numeric: tabular-nums;
		text-align: center;
	}

	.status-message {
		margin-top: 12px;
		font-size: 13px;
		font-weight: 600;
		text-align: center;
	}

	.status-message.success {
		color: $color-primary;
	}

	.status-message.expired {
		color: #E02B2B;
	}

	.txn-container {
		margin-bottom: 10px;
	}

	.txn-input {
		height: 40px;
		padding: 0 10px;
		border: 1px solid $color-secondary;
		border-radius: 10px;
		background: $bg-color-info;
		color: $color-primary;
		font-size: 13px;
		font-style: italic;
		text-align: center;
		box-sizing: border-box;
	}

	.txn-placeholder {
		color: $color-primary;
		font-size: 12px;
		font-style: italic;
	}

	.txn-hint {
		display: block;
		margin-top: 8px;
		color: $color-primary;
		font-size: 11px;
		line-height: 1.4;
		text-align: center;
	}

	.continue-btn {
		height: 40px;
		margin-bottom: 10px;
		border-radius: 10px;
		background: $color-primary;
		color: #fff;
		font-size: 15px;
		font-weight: 600;
		line-height: 40px;
		text-align: center;
	}

	.continue-btn.disabled {
		background: rgba($theme-primary-value, .5);
	}

	.cancel-order {
		margin: 4px 0 14px;
		color: #E02B2B;
		font-size: 13px;
		text-align: center;
	}

	.notice-card {
		margin-top: 12px;
		padding: 16px 18px;
		border-radius: 12px;
		background: #F1F1F1;
	}

	.notice-row {
		display: flex;
		align-items: flex-start;
		gap: 8px;
		margin-bottom: 4px;
	}

	.notice-dot {
		color: $color-primary;
		font-size: 14px;
		line-height: 1.4;
	}

	.notice-text {
		flex: 1;
		color: $color-primary;
		font-size: 13px;
		line-height: 1.45;
	}

	.notice-warning {
		display: block;
		margin-top: 12px;
		color: #E02B2B;
		font-size: 11px;
		line-height: 1.4;
	}
</style>
