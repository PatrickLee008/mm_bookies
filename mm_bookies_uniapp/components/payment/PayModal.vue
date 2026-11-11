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
					<view v-if="state === 'success'" class="success-banner">{{ $t('success') }}</view>
					<view v-else-if="localExpired && state === 'paying'" class="status-checking">
						{{ $t(statusCheckLimitReached ? 'in progress' : 'pending') }}
					</view>
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
	import siteinfo from '@/siteinfo'

	// 支付码合成底图：与 pages/payment/payment.vue 保持一致，按站点切换
	const PAY_BG = {
		mmbookies: '/static/image/pay/payment-qrcode-bg.jpg',
		shwegoal: '/static/image/pay/swg-bg.jpg',
		phoe_wa_maung: '/static/image/pay/pwm-bg.jpg'
	}
	// 银行图标（合成图底部用）
	const BANK_ICON = {
		KBZ: '/static/icon/register/KBZ Pay.png',
		'KBZ Pay': '/static/icon/register/KBZ Pay.png',
		KBZPAY: '/static/icon/register/KBZ Pay.png',
		WaveMoney: '/static/icon/register/Wave Money.png',
		'Wave Money': '/static/icon/register/Wave Money.png',
		WAVEPAY: '/static/icon/register/Wave Money.png'
	}
	const LOCAL_EXPIRY_POLL_INTERVAL = 10000
	const MAX_LOCAL_EXPIRY_POLL_MS = 30 * 60 * 1000

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
				localExpired: false,
				statusCheckDeadline: 0,
				statusCheckLimitReached: false,
				timer: null,
				pollTimer: null,
				successCloseTimer: null,
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
			paymentBank() {
				return String(this.order.receive_bank_code || this.order.RECEIVE_BANK_CODE ||
					this.order.bank_type || this.order.BANK_TYPE || '').trim()
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
				if (this.channel === 'VIPPay') {
					return /wave/i.test(this.paymentBank) ? this.$t('deposit_with_wave') : this.$t('deposit_with_kpay')
				}
				return (this.$t('auto_deposit') || 'Auto Deposit') + ' - ' + this.title
			},
			moneyText() {
				const value = this.order.money || this.order.MONEY || this.order.amount || 0
				return dateFormatUtils.numFormat(String(value).replace(/,/g, ''))
			},
			qrValue() {
				return this.qrData || this.order.QRCODE || this.order.qrcode || this.order.pay_url || ''
			},
			expiryText() {
				const value = this.order.expire_time || this.order.EXPIRE_TIME || ''
				if (!value) return '--'
				// 服务器给的是 UTC+8 钟面时间，必须转成用户时区（缅甸 UTC+6:30）再展示，
				// 统一走 utils 里的 convertTimezone，和 coupon.vue 保持一致。
				const normalized = String(value).replace('T', ' ')
				const converted = dateFormatUtils.convertTimezone(normalized)
				const m = String(converted).match(/(\d{4})-(\d{2})-(\d{2})[ T](\d{2}):(\d{2}):(\d{2})/)
				if (!m) return String(value)
				// 展示成 DD-MM-YYYY HH:mm:ss
				return m[3] + '-' + m[2] + '-' + m[1] + ' ' + m[4] + ':' + m[5] + ':' + m[6]
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
					const completedOrderId = this.orderId
					this.stop()
					uni.$emit('userInfo:refresh')
					this.successCloseTimer = setTimeout(() => {
						this.successCloseTimer = null
						if (this.visible && this.state === 'success' && this.orderId === completedOrderId) {
							this.onClose()
						}
					}, 1500)
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
				this.localExpired = false
				this.statusCheckDeadline = 0
				this.statusCheckLimitReached = false
				this.orderId = this.order.id || this.order.ID || this.order.out_order_id || this.order.OUT_ORDER_ID || ''
				this.qrData = ''
				this.qrImage = ''
				this.paymentError = ''

				const hasQr = !!this.qrValue
				if (hasQr) this.makeQr()

				this.startCountdown()
				this.setPollInterval(2000)
				if (this.remain <= 0) this.markLocallyExpired()
				if (!hasQr) this.fetchPayInfo()
			},
			stop() {
				if (this.timer) {
					clearInterval(this.timer)
					this.timer = null
				}
				this.stopPolling()
				if (this.successCloseTimer) {
					clearTimeout(this.successCloseTimer)
					this.successCloseTimer = null
				}
			},
			startCountdown() {
				if (this.timer) clearInterval(this.timer)
				this.timer = setInterval(() => {
					if (this.remain > 0) {
						this.remain -= 1
						if (this.remain === 0) this.markLocallyExpired()
					}
				}, 1000)
			},
			stopPolling() {
				if (this.pollTimer) {
					clearInterval(this.pollTimer)
					this.pollTimer = null
				}
			},
			setPollInterval(interval) {
				this.stopPolling()
				// 用箭头函数保留组件 this，避免轮询时丢失订单号。
				this.pollTimer = setInterval(() => this.pollStatus(), interval)
			},
			markLocallyExpired() {
				if (this.localExpired) return
				this.localExpired = true
				if (this.timer) {
					clearInterval(this.timer)
					this.timer = null
				}
				this.statusCheckLimitReached = false
				this.statusCheckDeadline = Date.now() + MAX_LOCAL_EXPIRY_POLL_MS
				this.setPollInterval(LOCAL_EXPIRY_POLL_INTERVAL)
			},
			clearLocalExpiry() {
				if (!this.localExpired) return
				this.localExpired = false
				this.statusCheckDeadline = 0
				this.statusCheckLimitReached = false
				this.startCountdown()
				this.setPollInterval(2000)
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
				const activeOrderId = this.orderId
				const id = this.order.out_order_id || this.order.OUT_ORDER_ID || this.order.id || this.order.ID
				if (!id) {
					this.paymentError = 'Payment order ID is missing'
					return
				}
				this.$http.post('/charge_apply/payinfo', { id }, (res) => {
					if (!this.visible || this.orderId !== activeOrderId) return
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
					if (info.timeout > 0) {
						this.remain = Number(info.timeout)
						this.clearLocalExpiry()
					}
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
						// TCPay / VIPPay：服务商只返回收银页链接、没有 qrcode 字段，
						// 用链接本身生成二维码，让用户在本弹窗内扫码，不跳出 App。
						// MCPay / KingPay 仍走外部跳转。
						const ch = info.pay_channel || this.order.pay_channel || this.order.CHANNEL || ''
						if (ch === 'TCPay' || ch === 'VIPPay' || ch === 'VIPPay_CashCode') {
							this.qrData = info.payment_url
							this.makeQr()
							return
						}
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
				// 弹窗只展示纯二维码；带底图的合成图在点「保存」时才生成
				this.qrImage = path
			},
			pollStatus() {
				if (!this.orderId || this.state !== 'paying') return
				if (this.localExpired && this.statusCheckDeadline && Date.now() >= this.statusCheckDeadline) {
					this.statusCheckLimitReached = true
					this.stopPolling()
					return
				}
				const orderId = this.orderId
				this.$http.post('/charge_apply/status', { id: orderId }, (res) => {
					if (!this.visible || this.state !== 'paying' || this.orderId !== orderId) return
					const data = res.data || {}
					if (data.code !== 20000) return
					if (data.status === 'Success') {
						this.state = 'success'
					} else if (data.status === 'Timeout') {
						this.state = 'timeout'
					} else if (data.status === 'Cancelled') {
						this.state = 'cancelled'
					} else if (typeof data.remaining_seconds === 'number') {
						this.remain = Math.max(0, data.remaining_seconds)
						if (this.remain > 0) this.clearLocalExpiry()
						else this.markLocallyExpired()
					}
				})
			},
			// H5 专用：把二维码合成到站点底图上（位置算法照搬 pages/payment/payment.vue）
			composeQrPoster() {
				const loadEl = (src) => new Promise((resolve, reject) => {
					const img = new Image()
					img.crossOrigin = 'anonymous'
					img.onload = () => resolve(img)
					img.onerror = () => reject(new Error('load fail: ' + src))
					img.src = src
				})
				const bgSrc = PAY_BG[siteinfo.site] || PAY_BG.mmbookies
				return Promise.all([loadEl(bgSrc), loadEl(this.qrImage)])
					.then(([bg, qr]) => {
						const canvas = document.createElement('canvas')
						const w = bg.naturalWidth || bg.width
						const h = bg.naturalHeight || bg.height
						canvas.width = w
						canvas.height = h
						const ctx = canvas.getContext('2d')

						// 1) 底图
						ctx.drawImage(bg, 0, 0, w, h)

						// 2) 二维码：白框内居中，整体下移 30px（与旧版一致）
						const boxTop = h * 0.243
						const boxBottom = h * 0.725
						const boxH = boxBottom - boxTop
						const boxW = w * 0.8125
						const padding = w * 0.075
						const qrSize = Math.min(boxW - padding * 2, boxH - padding * 2, 500)
						const qrX = (w - qrSize) / 2
						const qrY = boxTop + (boxH - qrSize) / 2 + 30
						ctx.drawImage(qr, qrX, qrY, qrSize, qrSize)

						// 3) 银行图标（圆角裁剪）
						const payType = this.order.pay_channel === 'TCPay' || this.order.pay_channel === 'MCPay'
							? (this.order.receive_bank_code || 'KBZ')
							: (this.order.bank_type || this.order.receive_bank_code || 'KBZ')
						const iconSrc = BANK_ICON[payType] || BANK_ICON[this.order.bank_type] || ''
						const iconSize = Math.min(w * 0.15, 120)
						const iconX = (w - iconSize) / 2
						const iconY = h * 0.784
						const drawAccount = () => {
							const fontSize = Math.floor(w * 0.035) + 2
							ctx.font = 'bold ' + fontSize + 'px sans-serif'
							ctx.fillStyle = '#FFFFFF'
							ctx.textAlign = 'center'
							const raw = this.order.receive_account || this.order.receive_acc_number || ''
							const masked = raw && raw.length > 4 ? '****' + String(raw).slice(-4) : String(raw || '')
							ctx.fillText(masked, w / 2, iconY + iconSize + fontSize + 13)
						}
						if (iconSrc) {
							return loadEl(iconSrc).then((icon) => {
								const r = 5
								ctx.save()
								ctx.beginPath()
								ctx.moveTo(iconX + r, iconY)
								ctx.lineTo(iconX + iconSize - r, iconY)
								ctx.arc(iconX + iconSize - r, iconY + r, r, 1.5 * Math.PI, 2 * Math.PI)
								ctx.lineTo(iconX + iconSize, iconY + iconSize - r)
								ctx.arc(iconX + iconSize - r, iconY + iconSize - r, r, 0, 0.5 * Math.PI)
								ctx.lineTo(iconX + r, iconY + iconSize)
								ctx.arc(iconX + r, iconY + iconSize - r, r, 0.5 * Math.PI, Math.PI)
								ctx.lineTo(iconX, iconY + r)
								ctx.arc(iconX + r, iconY + r, r, Math.PI, 1.5 * Math.PI)
								ctx.closePath()
								ctx.clip()
								ctx.drawImage(icon, iconX, iconY, iconSize, iconSize)
								ctx.restore()
								drawAccount()
								return canvas.toDataURL('image/png')
							}).catch(() => {
								drawAccount()
								return canvas.toDataURL('image/png')
							})
						}
						drawAccount()
						return canvas.toDataURL('image/png')
					})
					.catch(() => '')
			},
			saveQr() {
				// #ifdef H5
				// H5 没有 saveImageToPhotosAlbum（uni 仅 App/小程序实现），
				// 且保存的是「底图 + 二维码 + 银行图标 + 账号」的合成图（与旧 payment 页一致），
				// 所以这里先用原生 canvas 合成，再用 <a download> 下载。
				if (this.qrImage) {
					this.composeQrPoster().then((dataUrl) => {
						if (!dataUrl) {
							uni.showToast({ title: this.$t('save_qr'), icon: 'none' })
							return
						}
						const a = document.createElement('a')
						a.href = dataUrl
						a.download = 'pay-qr-' + (this.orderId || 'code') + '.png'
						document.body.appendChild(a)
						a.click()
						document.body.removeChild(a)
						uni.showToast({ title: this.$t('save_qr'), icon: 'none' })
					})
					return
				}
				// #endif
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
				this.localExpired = false
				this.statusCheckDeadline = 0
				this.statusCheckLimitReached = false
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
				this.localExpired = false
				this.statusCheckDeadline = 0
				this.statusCheckLimitReached = false
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

	.status-checking {
		margin-top: 8px;
		color: #777;
		font-size: 12px;
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
