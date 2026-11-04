<template>
	<view v-if="visible" class="pay-mask" @click.stop="noop" @touchmove.stop="noop">
		<view class="pay-panel">
			<view class="pay-header">
				<text class="pay-title">{{ paymentTitle }}</text>
				<text class="pay-close" @click="onClose">×</text>
			</view>

			<scroll-view scroll-y class="pay-content">
				<view class="qr-wrap">
					<view class="hidden-qr">
						<tki-qrcode v-if="qrValue" ref="qr" cid="payQr" :val="qrValue" :size="320" :onval="false"
							:loadMake="false" @result="onQrResult" :usingComponents="true" />
					</view>
					<image v-if="qrImage" class="qr-image" :src="qrImage" mode="aspectFit" />
					<view v-else-if="paymentError" class="qr-error">{{ paymentError }}</view>
					<view v-else class="qr-loading">{{ $t('loading_dots') }}</view>
					<view class="save-qr" :class="{ disabled: !qrImage }" @click="saveQr">
						<view class="download-icon"></view>
						<text>{{ $t('save_qr') }}</text>
					</view>
				</view>

				<view class="notice-box">
					<text class="notice-copy">{{ $t('scan_qr_notice') }}</text>
					<text class="notice-copy warning">{{ $t('same_account_payment') }}</text>
				</view>

				<view class="amount-row">
					<text class="amount-label">{{ $t('transfer_amount') }} :</text>
					<text class="amount-value">{{ moneyText }} MMK</text>
				</view>

				<view class="validity-card">
					<view class="validity-row">
						<text class="validity-label">{{ $t('valid_period') }}</text>
						<text class="validity-date">{{ expiryText }}</text>
					</view>
					<view class="countdown">{{ countdownText }}</view>
				</view>

				<view class="pay-actions">
					<view class="continue-btn" :class="{ disabled: state !== 'success' }" @click="continueAfterPaid">
						{{ $t('continue_btn') }}
					</view>
				<view v-if="cancelable && state === 'paying'" class="cancel-order-btn"
					@click="confirmCancel">
					{{ $t('cancel_order') }}
				</view>
				</view>
			</scroll-view>
		</view>

		<view v-if="cancelConfirm" class="cancel-layer" @click.self="cancelConfirm = false">
			<view class="cancel-box">
				<text class="cancel-title">{{ $t('cancel_order') }}</text>
				<text class="cancel-desc">{{ $t('cancel_order_confirm') }}</text>
				<view class="cancel-actions">
					<view class="cancel-btn ghost" @click="cancelConfirm = false">{{ $t('keep_order') }}</view>
					<view class="cancel-btn danger" @click="onCancelConfirmed">{{ $t('confirm') }}</view>
				</view>
			</view>
		</view>
	</view>
</template>

<script>
	import tkiQrcode from '@/components/tki-qrcode/tki-qrcode.vue'
	import dateFormatUtils from '../../utils/utils.js'

	export default {
		name: 'PayModal',
		components: {
			tkiQrcode
		},
		props: {
			visible: {
				type: Boolean,
				default: false
			},
			order: {
				type: Object,
				default: () => ({})
			}
		},
		data() {
			return {
				state: 'paying',
				remain: 0,
				timer: null,
				pollTimer: null,
				qrImage: '',
				qrData: '',
				paymentError: '',
				cancelConfirm: false,
				cancelling: false,
				orderId: ''
			}
		},
		computed: {
			channel() {
				return this.order.pay_channel || this.order.CHANNEL || ''
			},
			cancelable() {
				return this.channel === 'VIPPay'
			},
			title() {
				const titles = {
					VIPPay: 'ViPPay',
					TCPay: 'TC Pay'
				}
				return titles[this.channel] || this.channel
			},
			paymentTitle() {
				if (this.channel === 'VIPPay') return this.$t('deposit_with_kpay')
				return (this.$t('auto_deposit') || 'Auto Deposit') + ' - ' + this.title
			},
			moneyText() {
				const value = this.order.money || this.order.MONEY || this.order.amount || 0
				return dateFormatUtils.numFormat(String(value).replace(/,/g, ''))
			},
			qrValue() {
				return this.qrData || this.order.QRCODE || this.order.qrcode || ''
			},
			expiryText() {
				const value = this.order.expire_time || this.order.EXPIRE_TIME || ''
				if (!value) return '--'
				const date = new Date(String(value).replace(' ', 'T'))
				if (isNaN(date.getTime())) return String(value)
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
			visible(value) {
				this.cancelConfirm = false
				if (value) this.start()
				else this.stop()
			},
			order() {
				if (this.visible) this.start()
			},
			state(value) {
				if (value === 'success') {
					this.stop()
					uni.$emit('userInfo:refresh')
				} else if (value === 'timeout' || value === 'cancelled') {
					this.notifyResult(value)
				}
			}
		},
		methods: {
			noop() {},
			start() {
				this.stop()
				this.state = 'paying'
				this.remain = Number(this.order.REMAINING_SECONDS || this.order.remaining_seconds || 0)
				this.orderId = this.order.id || this.order.ID || this.order.out_order_id || this.order.OUT_ORDER_ID || ''
				this.qrData = ''
				this.qrImage = ''
				this.paymentError = ''

				if (this.qrValue) this.makeQr()
				else this.fetchPayInfo()

				this.timer = setInterval(() => {
					if (this.remain > 0) {
						this.remain -= 1
						if (this.remain === 0) this.state = 'timeout'
					}
				}, 1000)
				this.pollTimer = setInterval(this.pollStatus, 2000)
			},
			stop() {
				if (this.timer) {
					clearInterval(this.timer)
					this.timer = null
				}
				if (this.pollTimer) {
					clearInterval(this.pollTimer)
					this.pollTimer = null
				}
			},
			makeQr() {
				this.$nextTick(() => {
					setTimeout(() => {
						const qr = this.$refs.qr
						if (qr && qr._makeCode) qr._makeCode()
					}, 300)
				})
			},
			fetchPayInfo() {
				const id = this.order.out_order_id || this.order.OUT_ORDER_ID || this.order.id || this.order.ID
				if (!id) {
					this.paymentError = 'Payment order ID is missing'
					return
				}
				this.$http.post('/charge_apply/payinfo', { id }, (res) => {
					const data = res.data || {}
					if (data.code !== 20000 || !data.data) {
						this.paymentError = data.message || 'Unable to load payment information'
						return
					}
					const info = data.data
					if (info.success) {
						this.state = 'success'
						return
					}
					if (info.timeout > 0) this.remain = Number(info.timeout)
					if (info.timeout < 0) {
						this.state = 'timeout'
						return
					}
					if (info.qrcode) {
						this.qrData = info.qrcode
						this.makeQr()
						return
					}
					if (/^https?:\/\//i.test(info.payment_url || '')) {
						this.$emit('payment-url', info.payment_url)
						return
					}
					if (info.receive_account || info.receive_account_name) {
						this.$emit('payment-page', Object.assign({}, this.order, {
							receive_account: info.receive_account || '',
							receive_account_name: info.receive_account_name || ''
						}))
						return
					}
					this.paymentError = 'Payment details are unavailable'
				}, {
					fail: () => {
						this.paymentError = 'Unable to load payment information'
					}
				})
			},
			onQrResult(path) {
				this.qrImage = path
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
			saveQr() {
				const qr = this.$refs.qr
				if (qr && qr._saveCode) {
					qr._saveCode()
					return
				}
				uni.showToast({ title: this.$t('save_qr'), icon: 'none' })
			},
			continueAfterPaid() {
				if (this.state !== 'success') return
				this.onClose()
			},
			confirmCancel() {
				if (this.cancelling) return
				this.cancelConfirm = true
			},
			onCancelConfirmed() {
				this.cancelConfirm = false
				this.doCancel()
			},
			doCancel() {
				this.cancelling = true
				this.$http.post('/charge_apply/cancel', {
					order_id: this.order.out_order_id || this.order.OUT_ORDER_ID || this.orderId
				}, (res) => {
					this.cancelling = false
					const data = res.data || {}
					if (data.code === 20000) {
						this.state = 'cancelled'
						return
					}
					const messages = {
						NOT_CANCELLABLE: 'This order can no longer be cancelled.',
						CANCEL_LIMIT_REACHED: "Today's cancellation limit has been reached."
					}
					uni.showToast({
						title: messages[data.error_code] || data.message || 'Unable to cancel',
						icon: 'none'
					})
				}, {
					fail: () => {
						this.cancelling = false
						uni.showToast({ title: 'Unable to cancel, please try again', icon: 'none' })
					}
				})
			},
			notifyResult(state) {
				this.stop()
				this.state = 'paying'
				this.$emit('close')
				if (state === 'timeout') {
					this.$notice.alert(this.$t('payment.orderTimeoutTip'), () => {}, {
						title: this.$t('timeout'),
						confirmText: this.$t('confirm')
					})
				} else {
					this.$notice.alert(this.$t('order_cancelled'), () => {}, {
						title: this.$t('cancelled'),
						confirmText: this.$t('confirm')
					})
				}
			},
			onClose() {
				this.stop()
				this.state = 'paying'
				this.$emit('close')
			}
		},
		beforeDestroy() {
			this.stop()
		}
	}
</script>

<style lang="scss" scoped>
	.pay-mask {
		position: fixed;
		left: 0;
		right: 0;
		top: 0;
		bottom: 0;
		z-index: 9999;
		display: flex;
		align-items: center;
		justify-content: center;
		background: rgba(0, 0, 0, .55);
	}

	.pay-panel {
		display: flex;
		flex-direction: column;
		width: 90vw;
		max-width: 420px;
		max-height: 88vh;
		overflow: hidden;
		border-radius: 12px;
		background: #fff;
	}

	.pay-header {
		position: relative;
		display: flex;
		align-items: center;
		justify-content: center;
		min-height: 44px;
		padding: 0 52px;
		background: $color-primary;
	}

	.pay-title {
		font-size: 15px;
		font-weight: 600;
		color: #fff;
		text-align: center;
	}

	.pay-close {
		position: absolute;
		right: 14px;
		top: 50%;
		width: 28px;
		height: 28px;
		line-height: 26px;
		border-radius: 50%;
		transform: translateY(-50%);
		background: rgba(255, 255, 255, .18);
		color: #fff;
		font-size: 22px;
		text-align: center;
	}

	.pay-content {
		flex: 1;
		min-height: 0;
		max-height: calc(88vh - 44px);
		padding: 16px 20px 20px;
		box-sizing: border-box;
	}

	.qr-wrap {
		display: flex;
		flex-direction: column;
		align-items: center;
	}

	.hidden-qr {
		position: fixed;
		left: -9999px;
		top: 0;
	}

	.qr-image,
	.qr-loading,
	.qr-error {
		width: 200px;
		height: 200px;
		max-width: 60vw;
		max-height: 60vw;
		border-radius: 8px;
	}

	.qr-image {
		background: #fff;
	}

	.qr-loading,
	.qr-error {
		display: flex;
		align-items: center;
		justify-content: center;
		padding: 12px;
		box-sizing: border-box;
		background: $bg-color-info;
		color: $text-color-secondary;
		font-size: 13px;
		text-align: center;
	}

	.qr-error {
		color: #E02B2B;
	}

	.save-qr {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 200px;
		height: 40px;
		margin-top: 12px;
		border-radius: 9px;
		background: $color-primary;
		color: #fff;
		font-size: 13px;
		font-weight: 600;
		box-sizing: border-box;
	}

	.save-qr.disabled {
		opacity: .45;
	}

	.download-icon {
		position: relative;
		width: 13px;
		height: 14px;
		margin-right: 7px;
		border-bottom: 2px solid #fff;
		box-sizing: border-box;
	}

	.download-icon::before {
		position: absolute;
		top: 0;
		left: 5px;
		width: 2px;
		height: 8px;
		background: #fff;
		content: '';
	}

	.download-icon::after {
		position: absolute;
		top: 4px;
		left: 3px;
		width: 6px;
		height: 6px;
		border-right: 2px solid #fff;
		border-bottom: 2px solid #fff;
		transform: rotate(45deg);
		content: '';
	}

	.notice-box {
		margin-top: 14px;
		padding: 16px 20px;
		border-radius: 10px;
		background: #F1F1F1;
		text-align: center;
	}

	.notice-copy {
		display: block;
		margin-top: 0;
		color: $color-primary;
		font-size: 13px;
		line-height: 1.4;
	}

	.notice-copy.warning {
		margin-top: 12px;
		color: #E02B2B;
	}

	.amount-row {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 14px 0 10px;
	}

	.amount-label,
	.validity-label {
		color: $color-primary;
		font-size: 12px;
		font-weight: 600;
	}

	.amount-value {
		color: $color-primary;
		font-size: 14px;
		font-style: italic;
		font-weight: 700;
	}

	.validity-card {
		padding: 0;
	}

	.validity-row {
		display: flex;
		justify-content: space-between;
		align-items: flex-start;
		gap: 12px;
	}

	.validity-date {
		color: $color-primary;
		font-size: 12px;
	}

	.countdown {
		margin-top: 10px;
		text-align: center;
		color: #E02B2B;
		font-size: 22px;
		font-weight: 700;
		font-variant-numeric: tabular-nums;
		text-align: right;
	}

	.success-banner {
		margin-top: 8px;
		padding: 9px;
		border-radius: 7px;
		background: #EAF6EC;
		color: $color-primary;
		font-size: 13px;
		font-weight: 600;
		text-align: center;
	}

	.pay-actions {
		margin-top: 12px;
	}

	.continue-btn {
		height: 42px;
		line-height: 42px;
		border-radius: 8px;
		background: $color-primary;
		color: #fff;
		font-size: 14px;
		font-weight: 600;
		text-align: center;
	}

	.continue-btn.disabled {
		background: rgba($theme-primary-value, .5);
	}

	.cancel-order-btn {
		margin-top: 9px;
		color: #E02B2B;
		font-size: 12px;
		text-align: center;
	}

	.cancel-layer {
		position: fixed;
		left: 0;
		right: 0;
		top: 0;
		bottom: 0;
		z-index: 10000;
		display: flex;
		align-items: center;
		justify-content: center;
		background: rgba(0, 0, 0, .45);
	}

	.cancel-box {
		display: flex;
		flex-direction: column;
		width: 84vw;
		max-width: 340px;
		padding: 24px 20px 16px;
		border-radius: 12px;
		background: #fff;
	}

	.cancel-title {
		color: $text-color;
		font-size: 16px;
		font-weight: 600;
		text-align: center;
	}

	.cancel-desc {
		margin-top: 10px;
		color: $text-color-secondary;
		font-size: 13px;
		line-height: 1.5;
		text-align: center;
	}

	.cancel-actions {
		display: flex;
		gap: 10px;
		margin-top: 22px;
	}

	.cancel-btn.ghost,
	.cancel-btn.danger {
		flex: 1;
		padding: 11px 4px;
		border-radius: 7px;
		font-size: 13px;
		text-align: center;
	}

	.cancel-btn.ghost {
		border: 1px solid $border-color;
		color: $text-color;
	}

	.cancel-btn.danger {
		background: $color-primary;
		color: #fff;
	}
</style>
