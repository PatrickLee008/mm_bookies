<template>
	<view class="deposit-component">
		<global-notice ref="globalNotice"></global-notice>
		<scroll-view scroll-y class="deposit-scroll" @scroll="onScrollEmit" @scrolltoupper="onScrollTopEmit">
			<!-- ============ 1. 网关横排 ============ -->
			<view class="section-title gateway-heading">{{ $t('choose_payment_gateway') }}</view>
			<view class="gw-row" v-if="channels.length">
				<view class="gw-item" v-for="m in channels" :key="m.code"
					:class="{ active: selectedChannel === m.code }" @click="selectChannel(m)">
					<view class="gw-logo-box">
						<image v-if="logoOf(m.code)" class="gw-logo" :src="logoOf(m.code)" mode="aspectFit"></image>
						<text v-else class="gw-badge">{{ shortName(m) }}</text>
					</view>
					<text class="gw-name">{{ m.title }}</text>
				</view>
			</view>
			<view class="gw-empty" v-else-if="channelsLoaded">
				No payment channel available, please contact customer service.
			</view>

			<!-- ============ 2. 银行宫格 ============ -->
			<view class="section" v-if="selectedChannel">
				<view class="section-title">{{ $t('choose_account_type') }}</view>
				<view class="bank-grid">
					<view class="bank-cell" v-for="b in currentBanks" :key="b" :class="{ active: selectedBank === b }"
						@click="selectBank(b)">
						<image class="bank-logo" :src="bankIcon(b)" mode="aspectFit"></image>
						<text class="bank-name">{{ bankName(b) }}</text>
					</view>
				</view>
			</view>

			<!-- ============ 3. 我的银行卡（仅选卡通道） ============ -->
			<view class="section" v-if="selectedBank && needCard">
				<view class="section-title">{{ $t('choose_bank_account') }}</view>
				<view class="card-list">
					<view class="card-item" v-for="c in matchedCards" :key="c.id"
						:class="{ active: selectedCardId === c.id }" @click="selectedCardId = c.id">
						<image class="card-icon" :src="bankIcon(c.bank_code)" mode="aspectFit"></image>
						<view class="card-info">
							<text class="card-name">{{ c.acc_name || bankName(c.bank_code) }}</text>
							<text class="card-num">{{ maskNumber(c.acc_number) }}</text>
						</view>
						<view class="card-radio">
							<view v-if="selectedCardId === c.id" class="radio-dot"></view>
						</view>
						<!-- 主卡不可删（is_default=1），非主卡才显示删除 -->
						<view v-if="c.is_default != 1" class="card-del" @click.stop="removeCard(c)">
							<text class="card-del-x">×</text>
						</view>
					</view>
					<view class="card-item add" @click="openAddCard">
						<text class="add-text">{{ $t('add_bank_account') }}</text>
					</view>
				</view>
				<view class="card-empty" v-if="matchedCards.length === 0">
					No {{ bankName(selectedBank) }} account yet, please add one.
				</view>
			</view>

			<!-- ============ 4. 金额 ============ -->
			<view class="section" v-if="selectedBank">
				<view class="amount-heading">
					<text class="amount-label">{{ $t('enter_deposit_amount') }}</text>
				</view>
				<view class="amount-box">
					<input class="amount-input" type="number" maxlength="8" v-model="amount"
						:placeholder="$t('please_enter_deposit_amount')" placeholder-class="ph" />
				</view>
				<view class="limit-text">
					{{ minimumAmountHint }}
				</view>
				<view class="quick-row">
					<view class="quick-item" v-for="q in quickAmounts" :key="q"
						:class="{ active: amountValue === q }" @click="amount = String(q)">
						{{ numberFormat(q) }}
					</view>
				</view>
				<view class="pay-btn" :class="{ disabled: !canContinue || submitting }" @click="submit">
					{{ submitting ? $t('processing') : $t('continue_btn') }}
				</view>
			</view>

			<!-- ============ 5. 教程 ============ -->
			<view class="section steps" v-if="selectedChannel">
				<view v-if="configuredSteps">
					<view class="steps-title">{{ $t('how_to_recharge') }}</view>
					<!-- 无启用的页面配置时不显示充值提示 -->
					<text class="step-text configured-text">{{ configuredSteps }}</text>
				</view>
				<view class="video-guide">
					<text class="video-guide-title">{{ $t('watch_video_guide') }}</text>
					<view class="video-btn" :class="{ disabled: !currentVideo }" @click="openVideoGuide">
						<text class="video-icon">▶</text>
						<text>{{ $t('watch_now') }}</text>
					</view>
				</view>
			</view>

			<!-- ============ 6. Manual（上传凭证） ============ -->
			<view class="section manual" v-if="selectedChannel === 'Manual'">
				<view class="section-title">Manual Transfer</view>
				<view class="manual-tip">
					Transfer to the account above, then upload the receipt and fill in the transaction ID.
				</view>
				<input class="manual-input" v-model="manualTxn" placeholder="Transaction ID" />
				<view class="manual-upload" @click="chooseImage">
					<text>{{ manualPic ? 'Receipt selected' : 'Upload receipt' }}</text>
				</view>
				<view class="pay-btn" :class="{ disabled: !manualCanSubmit }" @click="submitManual">
					{{ manualSubmitting ? 'Submitting...' : 'Submit' }}
				</view>
			</view>

			<view class="notice-card" v-if="noticeText">
				<text class="notice-title">{{ $t('notice_title') }}</text>
				<text class="notice-text configured-text">{{ noticeText }}</text>
			</view>
			<view style="height: 40rpx;"></view>
		</scroll-view>

		<!-- ============ 付款弹窗 ============ -->
		<PayModal :visible="payVisible" :order="payOrder" @close="onPayClose" @payment-url="handlePaymentUrl"
			@payment-page="handlePaymentPage" />

		<!-- ============ 新增银行卡弹窗 ============ -->
		<view class="modal-mask" v-if="showAddCard" @click="showAddCard = false">
			<view class="modal-panel" @click.stop>
				<view class="modal-header">
					{{ $t('bind_wallet_account') }}
					<view class="modal-close" @click="showAddCard = false">×</view>
				</view>
				<view class="modal-form">
					<view class="modal-field">
						<text class="field-label">{{ $t('account_no') }}</text>
						<input class="modal-input" type="number" maxlength="20" v-model="newCard.acc_number"
							:placeholder="$t('account_no')" @input="onCardNumberInput" />
					</view>
					<view class="modal-field">
						<text class="field-label">{{ $t('user_name') }}</text>
						<input class="modal-input" type="text" maxlength="50" v-model="newCard.acc_name"
							:placeholder="$t('user_name')" @input="onCardNameInput" />
					</view>
					<view class="modal-btn primary" :class="{ disabled: !canSaveCard }" @click="saveCard">
						{{ $t('confirm') }}
					</view>
				</view>
			</view>
		</view>
	</view>
</template>

<script>
	import PayModal from '@/components/payment/PayModal.vue'
	import { getPaymentAction, getTransferPageUrl, openPaymentUrl } from '@/utils/payment-flow.js'
	import dateFormatUtils from '../../utils/utils.js'
	import { syncPageConfig, latestVersionOf, pickText, pageConfigLang } from '@/utils/page-config.js'
	import { fetchConfigShared } from '@/utils/api/config.js'
	import { sanitizeAccNumber, sanitizeAccName, validateAccNumber, validateAccName } from '@/utils/bank-card.js'

	// 后台页面配置的页面标识（Setting → Other，平台 MMBookies，类型 wallet/deposit）
	const PAGE_CONFIG_PAGE = 'wallet/deposit'

	// 同分时的展示顺序
	const SORT_ORDER = {
		VIPPay: 0,
		VIPPay_CashCode: 0,
		TCPay: 1,
		KingPay: 1,
		MCPay: 2,
		NFM2: 3,
		Manual: 9
	}
	// 免卡通道
	const NO_CARD_CHANNELS = ['VIPPay_CashCode', 'MCPay']
	// 支付渠道图标（未配置的通道回退首字母徽标）
	const CHANNEL_LOGO = {
		VIPPay: '/static/image/pay/vip_logo.png',
		VIPPay_CashCode: '/static/image/pay/vip_logo.png',
		KingPay: '/static/image/pay/king_logo.png',
		MCPay: '/static/image/pay/mc_logo.png',
		TCPay: '/static/image/pay/tc_logo.jpg'
	}
	// 通道 → 步骤组的映射（VIPPay_CashCode 与 VIPPay 共用）
	const STEPS_KEY_BY_CHANNEL = {
		VIPPay: 'VIPPay',
		VIPPay_CashCode: 'VIPPay',
		TCPay: 'TCPay',
		MCPay: 'MCPay',
		KingPay: 'KingPay',
		Manual: 'Manual'
	}

	export default {
		name: 'WalletDeposit',
		components: {
			PayModal
		},
		data() {
			return {
				channelsLoaded: false,
				channels: [],
				selectedChannel: '',
				selectedBank: '',
				selectedCardId: null,
				cardList: [],
				amount: '',
				submitting: false,
				payVisible: false,
				payOrder: {},
				showAddCard: false,
				newCard: {
					acc_number: '',
					acc_name: ''
				},
				manualTxn: '',
				manualPic: '',
				manualSubmitting: false,
				manualCards: [],
				configs: {},
				// 后台 setting/AppConfigForm 的「前端展示」配置（page_config_versions 用于页面配置版本比对）
				appConfig: {},
				// 后台启用的页面配置（wallet/deposit 的 notice / steps.<通道>，全部语言）
				pageConfigItems: []
			}
		},
		computed: {
			selectedMethod() {
				return this.channels.find(m => m.code === this.selectedChannel) || {}
			},
			currentBanks() {
				if (this.selectedChannel === 'Manual') return this.manualCards
				return this.selectedMethod.bank_codes || []
			},
			needCard() {
				return NO_CARD_CHANNELS.indexOf(this.selectedChannel) === -1 && this.selectedChannel !== 'Manual'
			},
			matchedCards() {
				if (!this.selectedBank) return []
				return this.cardList.filter(c => this.normalizeBank(c.bank_code) === this.selectedBank)
			},
			// 页面配置只支持英语和缅语；其他或未设置时使用默认缅语
			pageConfigLang() {
				return pageConfigLang(this.$i18n.locale)
			},
			// 只显示后台启用的当前通道步骤；未配置时为空。
			// Manual 不在配置清单里；VIPPay_CashCode 与 VIPPay 共用
			configuredSteps() {
				const groupKey = STEPS_KEY_BY_CHANNEL[this.selectedChannel]
				if (!groupKey || groupKey === 'Manual') return ''
				return pickText(this.pageConfigItems, 'steps.' + groupKey, this.pageConfigLang)
			},
			// 底部 Notice 只显示后台启用的配置
			noticeText() {
				return pickText(this.pageConfigItems, 'notice', this.pageConfigLang)
			},
			currentVideo() {
				// 视频只从 House AppConfig 读取；VIP Pay 按所选银行分别取链接，不跨银行回退。
				const ch = this.selectedChannel
				const bank = this.selectedBank || ''
				let configKey = ''
				if (ch === 'VIPPay' || ch === 'VIPPay_CashCode') {
					if (/wave/i.test(bank)) {
						configKey = 'vip_wave_video_link'
					} else if (/kbz/i.test(bank)) {
						configKey = 'vip_kbz_video_link'
					}
				} else if (ch === 'TCPay') {
					configKey = 'tc_video_link'
				} else if (ch === 'MCPay') {
					configKey = 'mc_video_link'
				} else if (ch === 'KingPay') {
					configKey = 'king_video_link'
				}
				const value = configKey ? this.appConfig[configKey] : ''
				return typeof value === 'string' ? value.trim() : ''
			},
			minLimit() {
				return Number(this.configs.deposit_min_limit) || 3000
			},
			maxLimit() {
				return Number(this.configs.deposit_max_limit) || 1000000
			},
			minimumAmountHint() {
				if (this.minLimit === 3000) return this.$t('min_deposit_3000')
				return 'Minimum deposit amount is ' + this.numberFormat(this.minLimit) + ' MMK.'
			},
			quickAmounts() {
				return [5000, 10000, 30000, 50000, 100000, 500000].filter(value =>
					value >= this.minLimit && value <= this.maxLimit)
			},
			amountValue() {
				return Number(this.amount || 0)
			},
			canSaveCard() {
				return !validateAccNumber(this.newCard.acc_number) && !validateAccName(this.newCard.acc_name)
			},
			amountValid() {
				const v = this.amountValue
				return Number.isInteger(v) && v >= this.minLimit && v <= this.maxLimit
			},
			canContinue() {
				if (!this.selectedBank) return false
				if (this.selectedChannel === 'Manual') return false
				if (!this.amountValid) return false
				if (this.needCard && !this.selectedCardId) return false
				return true
			},
			manualCanSubmit() {
				return !!this.manualTxn && !!this.manualPic && this.amountValid && !this.manualSubmitting
			}
		},
		created() {
			this.configs = Object.assign({}, this.$store.state.configs)
		},
		mounted() {
			this.loadAppConfig()
			this.checkUnfinishedOrder()
			this.loadChannels()
			this.loadCards()
			this.loadManualCards()
		},
		methods: {
			// ---------- 加载 ----------
			// 进入页面先查有没有未完成的充值单：有就直接弹「继续 / 取消」，
			// 而不是等用户选完通道金额、点 Continue 才被 50005 挡回来
			checkUnfinishedOrder() {
				this.$http.get('/charge_apply/unfinished', {}, (res) => {
					const d = res.data || {}
					if (d.code !== 20000 || !d.data) return
					const order = d.data
					this.$notice.confirm(
						'You have an unfinished deposit order. Continue with it?',
						() => this.openPay(order),
						null,
						{ confirmText: 'Continue', cancelText: 'Cancel' }
					)
				})
			},
			loadAppConfig() {
				fetchConfigShared(this.$http).then((res) => {
					if (!res) return
					// 共享请求走 skipFilter，这里补上统一的 401 会话过期处理
					this.$http.beforeResponseFilter(res)
					const d = res.data || {}
					this.appConfig = d.items || {}
					// 每次读取当前启用项，防止本地缓存显示已禁用的提示。
					syncPageConfig(this.$http, PAGE_CONFIG_PAGE, latestVersionOf(this.appConfig, PAGE_CONFIG_PAGE),
						(items) => {
							this.pageConfigItems = items
						}, true)
				})
			},
			loadChannels() {
				this.$http.post('/charge_apply/channels', {
					bank_code: 'All'
				}, (res) => {
					const d = res.data || {}
					let list = (d.code === 20000 && Array.isArray(d.data)) ? d.data : []
					list = list.filter(m => (m.bank_codes || []).length > 0)
					this.channels = list
					this.channelsLoaded = true
					if (list.length) {
						// 优先选第一个真实网关通道（Manual 是手工转账入口，排在末尾且不默认选中）
						const first = list.find(m => m.code !== 'Manual') || list[0]
						this.selectedChannel = first.code
						this.selectedBank = ''
					}
				}, {
					fail: () => {
						this.channelsLoaded = true
						this.channels = []
					}
				})
			},
			// 删除银行卡（主卡由后端拦，前端也隐藏按钮）
			removeCard(card) {
				this.$notice.confirm('Remove this bank account?', () => {
					this.$http.post('/bank_card/delete', { id: card.id }, (res) => {
						const d = res.data || {}
						if (d.code === 20000) {
							uni.showToast({ title: 'Removed', icon: 'success' })
							if (this.selectedCardId === card.id) this.selectedCardId = null
							this.loadCards()
						} else if (d.message === 'primary_card_cannot_delete') {
							this.$notice.alert('Primary account cannot be removed')
						} else if (d.message === 'bank card not found') {
							this.$notice.alert('Bank account not found')
							this.loadCards()
						} else {
							this.$notice.alert(d.message || 'Failed to remove')
						}
					})
				})
			},
			loadCards() {
				this.$http.get('/bank_card/get', {}, (res) => {
					const d = res.data || {}
					// 该接口只返回 {items: [...]}，没有 code 字段
					if (res.statusCode === 200 && Array.isArray(d.items)) {
						this.cardList = d.items
						this.$nextTick(this.ensureCard)
					}
				})
			},
			loadManualCards() {
				// Manual 不在 /channels 里，用 available_banks 判断后台是否配了手工转账卡
				this.$http.get('/agent_bankcard/available_banks', {}, (res) => {
					const d = res.data || {}
					const manual = Array.isArray(d.manual) ? d.manual : []
					const banks = []
					manual.forEach(item => {
						const code = item.bank_code || item.rc_bank_code
						if (code && banks.indexOf(code) === -1) banks.push(code)
					})
					this.manualCards = banks
					if (banks.length && !this.channels.some(m => m.code === 'Manual')) {
						this.channels.push({
							code: 'Manual',
							title: 'Manual Transfer',
							bank_codes: banks,
							score: 0,
							video_url: '',
							no_card: false,
							cancelable: false
						})
					}
					// 两个请求的返回顺序不确定：若此时还没选中通道，补选第一个网关通道
					if (!this.selectedChannel) {
						const firstAuto = this.channels.find(m => m.code !== 'Manual')
						if (firstAuto) this.selectedChannel = firstAuto.code
					}
				}, {
					fail: () => {}
				})
			},
			// ---------- 选择 ----------
			selectChannel(m) {
				if (this.selectedChannel === m.code) return
				this.selectedChannel = m.code
				// 切换通道清空银行/卡/金额
				this.selectedBank = ''
				this.selectedCardId = null
				this.amount = ''
				this.manualTxn = ''
				this.manualPic = ''
			},
			selectBank(b) {
				this.selectedBank = b
				this.ensureCard()
			},
			ensureCard() {
				const list = this.matchedCards
				if (!list.some(c => c.id === this.selectedCardId)) {
					this.selectedCardId = list.length ? list[0].id : null
				}
			},
			// ---------- 展示 ----------
			logoOf(code) {
				return CHANNEL_LOGO[code] || ''
			},
			shortName(m) {
				if (m.code === 'MCPay') return 'MC'
				if (m.code === 'KingPay') return 'KP'
				if (m.code === 'VIPPay' || m.code === 'VIPPay_CashCode') return 'VP'
				if (m.code === 'TCPay') return 'QR'
				return (m.title || m.code).slice(0, 2).toUpperCase()
			},
			normalizeBank(code) {
				const map = {
					'KBZ': 'KBZ Pay',
					'KBZPAY': 'KBZ Pay',
					'WaveMoney': 'Wave Money',
					'WAVEPAY': 'Wave Money',
					'AYAPAY': 'AYAPAY',
					'AYABANK': 'AYA BANK'
				}
				return map[code] || code
			},
			bankIcon(code) {
				const c = this.normalizeBank(code)
				return '/static/icon/register/' + c + '.png'
			},
			bankName(code) {
				return this.normalizeBank(code)
			},
			maskNumber(num) {
				const s = String(num || '')
				return s.length > 4 ? '****' + s.slice(-4) : s
			},
			numberFormat(n) {
				return dateFormatUtils.numFormat(n)
			},
			// ---------- 下单 ----------
			submit() {
				if (!this.canContinue || this.submitting) return
				this.submitting = true
				const card = this.matchedCards.find(c => c.id === this.selectedCardId)
				const para = {
					paychannel: this.selectedChannel,
					amount: this.amountValue,
					CARD_ID: this.needCard ? this.selectedCardId : null,
					bank_type: this.selectedBank,
					phone: card ? card.acc_number : '',
					subject: 'Deposit - ' + this.bankName(this.selectedBank),
					memo: '',
					is_h5: false
				}
				// #ifdef H5
				para.is_h5 = true
				// #endif

				this.$http.post('/charge_apply', para, (res) => {
					this.submitting = false
					const d = res.data || {}
					if (d.code === 20000) {
						this.openPay(d.data)
					} else if (d.code === 50005 && d.unfinished_apply) {
						this.$notice.confirm(
							'You have an unfinished deposit order. Continue with it?',
							() => this.openPay(d.unfinished_apply),
							null,
							{ confirmText: 'Continue', cancelText: 'Cancel' }
						)
					} else if (d.code === 40404) {
						this.$notice.alert(
							d.message || 'No payment account available, please contact customer service.'
						)
					} else {
						this.$notice.alert(d.message || 'Failed to create order, please try again.')
					}
				}, {
					fail: () => {
						this.submitting = false
						uni.showToast({
							title: 'Network error, please retry',
							icon: 'none'
						})
					}
				})
			},
			openPay(order) {
				if (!order) return
				const action = getPaymentAction(order)
				if (action.type === 'qr') {
					this.payOrder = order
					this.payVisible = true
					return
				}
				if (action.type === 'external') {
					this.launchPaymentUrl(action.url)
					return
				}

				this.openTransferPage(order)
			},
			openTransferPage(order) {
				const url = getTransferPageUrl(order)
				if (!url) {
					uni.showToast({ title: 'Payment order ID is missing', icon: 'none' })
					return
				}
				uni.navigateTo({
					url,
					fail: () => uni.showToast({ title: 'Unable to open payment page', icon: 'none' })
				})
			},
			onPayClose() {
				this.payVisible = false
				this.payOrder = {}
				this.loadCards()
				// 关闭弹窗时也刷新一次顶栏余额（用户可能已付款，回调早于关闭）
				uni.$emit('userInfo:refresh')
			},
			handlePaymentUrl(url) {
				this.payVisible = false
				this.payOrder = {}
				this.launchPaymentUrl(url)
			},
			handlePaymentPage(order) {
				this.payVisible = false
				this.payOrder = {}
				this.openTransferPage(order)
			},
			launchPaymentUrl(url) {
				if (!openPaymentUrl(url)) {
					uni.showToast({ title: 'Payment link unavailable', icon: 'none' })
				}
			},
			// ---------- 视频 ----------
			openVideoGuide() {
				const url = this.currentVideo
				if (!url || !/^https?:\/\//i.test(url)) {
					uni.showToast({
						title: 'No video guide',
						icon: 'none'
					})
					return
				}
				// #ifdef APP-PLUS
				plus.runtime.openURL(url)
				// #endif
				// #ifdef H5
				window.open(url, '_blank')
				// #endif
			},
			// ---------- 银行卡 ----------
			onCardNumberInput(e) {
				this.newCard.acc_number = sanitizeAccNumber(e.detail.value)
			},
			onCardNameInput(e) {
				this.newCard.acc_name = sanitizeAccName(e.detail.value)
			},
			openAddCard() {
				this.newCard = {
					acc_number: '',
					acc_name: ''
				}
				this.showAddCard = true
			},
			saveCard() {
				if (!this.canSaveCard) return
				const num = String(this.newCard.acc_number || '').trim()
				const name = String(this.newCard.acc_name || '').trim()
				this.$http.post('/bank_card/add', {
					bank_code: this.selectedBank,
					acc_number: num,
					acc_name: name
				}, (res) => {
					const d = res.data || {}
					if (res.statusCode === 200) {
						this.showAddCard = false
						this.loadCards()
					} else {
						uni.showToast({
							title: d.message || 'Failed to save',
							icon: 'none'
						})
					}
				}, {
					fail: () => uni.showToast({
						title: 'Failed to save',
						icon: 'none'
					})
				})
			},
			// ---------- Manual ----------
			chooseImage() {
				uni.chooseImage({
					count: 1,
					success: (r) => {
						this.manualPic = r.tempFilePaths[0]
					}
				})
			},
			submitManual() {
				if (!this.manualCanSubmit) return
				this.manualSubmitting = true
				uni.uploadFile({
					url: this.$http.baseUrl + '/charge/recharge',
					filePath: this.manualPic,
					name: 'image',
					formData: {
						transaction_id: this.manualTxn,
						amount: this.amountValue,
						charge_way: 1,
						bank_code: this.selectedBank
					},
					header: {
						Authorization: uni.getStorageSync('Authorization')
					},
					success: (res) => {
						this.manualSubmitting = false
						try {
							const d = JSON.parse(res.data)
							if (d.code === 200 || d.statusCode === 200) {
								uni.showToast({
									title: 'Submitted',
									icon: 'success'
								})
								this.manualTxn = ''
								this.manualPic = ''
								this.amount = ''
							} else {
								uni.showToast({
									title: d.message || 'Failed',
									icon: 'none'
								})
							}
						} catch (e) {
							uni.showToast({
								title: 'Failed',
								icon: 'none'
							})
						}
					},
					fail: () => {
						this.manualSubmitting = false
						uni.showToast({
							title: 'Upload failed',
							icon: 'none'
						})
					}
				})
			},
			// ---------- 父页面滚动联动 ----------
			onScrollEmit(e) {
				this.$emit('contentScroll', e)
			},
			onScrollTopEmit(e) {
				this.$emit('contentScrollTop', e)
			}
		}
	}
</script>

<style lang="scss" scoped>
	.deposit-component {
		width: 100%;
		height: 100%;
	}

	.deposit-scroll {
		height: 100%;
		padding: 0 5px;
		box-sizing: border-box;
	}

	/* ---------- 网关 ---------- */
	.gw-row {
		display: flex;
		gap: 20px;
		padding: 6px 0 14px;
	}

	.gw-item {
		flex: 1;
		min-width: 0; /* 关键：允许被压缩，否则 "Manual Transfer" 会把卡片撑宽，导致图标视觉大小不一 */
		display: flex;
		flex-direction: column;
		align-items: center;
		padding: 6px 4px 0;
		border-radius: $radius-large;
		background: #fff;
		border: 2px solid $color-secondary;
	}

	/* 选中：白底配主题色描边 */
	.gw-item.active {
		border-color: $color-primary;
		background: $color-primary;
	}

	/* 图标白托：三个 logo 自带底色，选中态深绿底上需要白色衬底才看得清 */
	.gw-logo-box {
		width: 40px;
		height: 40px;
		border-radius: 11px;
		background: #fff;
		display: flex;
		align-items: center;
		justify-content: center;
		margin-bottom: 6px;
		overflow: hidden;
	}

	.gw-logo {
		width: 36px;
		height: 36px;
		border-radius: 9px;
	}

	/* 无图标的通道回退首字母 */
	.gw-badge {
		width: 36px;
		height: 36px;
		line-height: 36px;
		text-align: center;
		border-radius: 9px;
		font-size: 13px;
		font-weight: 700;
		color: #fff;
		background: $color-primary;
	}

	.gw-item.active .gw-badge {
		background: #fff;
		color: $color-primary;
	}

	.card-del {
		width: 28px;
		height: 28px;
		display: flex;
		align-items: center;
		justify-content: center;
		margin-left: 6px;
	}

	.card-del-x {
		font-size: 20px;
		line-height: 1;
		color: #b0b0b0;
	}

	.gw-name {
		font-size: 12px;
		color: $color-primary;
		max-width: 100%;
		/* 允许换行：Manual Transfer 这类长标题折成两行，不再撑宽卡片 */
		white-space: normal;
		word-break: break-word;
		overflow: hidden;
		display: -webkit-box;
		-webkit-box-orient: vertical;
		-webkit-line-clamp: 2;
		line-height: 1.25;
		/* 固定两行高度，保证 1 行 / 2 行标题的卡片高度一致（图标纵向对齐） */
		min-height: 30px;
		text-align: center;
	}

	.gw-item.active .gw-name {
		color: #fff;
		font-weight: 600;
	}

	.gw-empty {
		padding: 24px 0;
		text-align: center;
		font-size: 13px;
		color: $text-color-secondary;
	}

	/* ---------- 通用区块 ---------- */
	.section {
		margin-bottom: 16px;
	}

	.gateway-heading {
		margin-top: 8px;
	}

	.section-title {
		font-size: 14px;
		font-weight: 600;
		color: $color-primary;
		margin: 10px 0;
	}

	/* ---------- 银行宫格 ---------- */
	.bank-grid {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 20px;
	}

	.bank-cell {
		display: flex;
		align-items: center;
		border-radius: 12px;
		border: 2px solid $color-primary;
		background: #fff;
		min-height: 56px;
		padding: 4px;
		box-sizing: border-box;
	}

	.bank-cell.active {
		border-color: $color-primary;
		background: $color-primary;
	}

	.bank-logo {
		width: 46px;
		height: 46px;
		border-radius: 8px;
		margin-right: 8px;
	}

	.bank-name {
		font-size: 13px;
		color: $color-primary;
	}

	.bank-cell.active .bank-name {
		color: #fff;
	}

	/* ---------- 卡片列表 ---------- */
	.card-list {
		display: flex;
		flex-direction: column;
		gap: 10px;
	}

	.card-item {
		display: flex;
		align-items: center;
		min-height: 56px;
		padding: 6px 16px;
		border-radius: 12px;
		border: 1px solid $color-primary;
		background: #fff;
		box-sizing: border-box;
	}

	.card-item.active {
		border-color: $color-secondary;
		background: #fff;
	}

	.card-item.add {
		justify-content: center;
		border-color: $color-primary;
	}

	.add-text {
		font-size: 14px;
		color: $color-primary;
	}

	.card-icon {
		flex: 0 0 46px;
		width: 46px;
		height: 46px;
		border-radius: 6px;
		margin-right: 12px;
	}

	.card-info {
		flex: 1;
		display: flex;
		align-items: center;
		justify-content: space-between;
		min-width: 0;
	}

	.card-num {
		margin-left: 8px;
		text-align: right;
		white-space: nowrap;
		font-size: 14px;
		color: $color-primary;
	}

	.card-name {
		min-width: 0;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
		font-size: 14px;
		font-weight: 600;
		color: $color-primary;
	}

	.card-item.active .card-num {
		color: $color-primary;
	}

	.card-item.active .card-name {
		color: $color-primary;
	}

	.card-radio {
		flex: 0 0 18px;
		width: 18px;
		height: 18px;
		margin-left: 12px;
		border-radius: 50%;
		border: 1px solid $color-secondary;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.radio-dot {
		width: 9px;
		height: 9px;
		border-radius: 50%;
		background: $color-primary;
	}

	.card-empty {
		margin-top: 8px;
		font-size: 12px;
		color: #E02B2B;
	}

	/* ---------- 金额 ---------- */
	.amount-heading {
		display: flex;
		align-items: center;
		margin: 10px 0 8px;
	}

	.amount-label {
		font-size: 14px;
		font-weight: 400;
		color: $color-primary;
	}

	.amount-box {
		display: flex;
		align-items: center;
		justify-content: center;
		text-align: center;
		height: 40px;
		border-radius: $radius-medium;
		background: $bg-color-info;
		border: 1px solid $color-secondary;
	}

	.amount-cur {
		font-size: 16px;
		font-weight: 600;
		color: $color-primary;
		margin-right: 8px;
	}

	.amount-input {
		flex: 1;
		text-align: center;
		font-size: 18px;
		font-weight: 600;
		font-style: italic;
		color: $color-primary;
	}

	.ph {
		color: $color-primary;
		font-weight: 400;
		font-size: 12px;
		font-style: italic;
	}

	.limit-text {
		margin: 8px 0;
		text-align: center;
		font-size: 10px;
		color: #E02B2B;
	}

	.quick-row {
		display: grid;
		grid-template-columns: repeat(3, 1fr);
		gap: 10px;
		margin: 8px 0 14px;
	}

	.quick-item {
		padding: 8px 0;
		text-align: center;
		font-size: 13px;
		font-weight: 600;
		color: $color-primary;
		border: 1px solid $color-primary;
		border-radius: 12px;
		background: #fff;
	}

	.quick-item.active {
		border-color: $color-primary;
		background: $color-primary;
		color: #fff;
	}

	.pay-btn {
		height: 40px;
		line-height: 40px;
		text-align: center;
		border-radius: $radius-medium;
		background: $color-primary;
		color: #fff;
		font-size: 15px;
		font-weight: 600;
	}

	.pay-btn.disabled {
		background: rgba($theme-primary-value, .5);
	}

	/* ---------- 教程 ---------- */
	.steps {
		padding: 16px 18px;
		border-radius: 12px;
		background: #fff;
		border: 2px solid $color-primary;
		box-shadow: 0 1px 3px rgba(0, 0, 0, .12);
	}

	.steps-title {
		font-size: 15px;
		font-weight: 700;
		color: $color-primary;
		margin-bottom: 10px;
	}

	.step-row {
		display: flex;
		margin-bottom: 6px;
	}

	.step-no {
		width: 20px;
		font-size: 13px;
		font-weight: 600;
		color: $color-primary;
	}

	.step-text {
		flex: 1;
		font-size: 13px;
		font-weight: 600;
		color: $color-primary;
		line-height: 1.5;
	}

	.video-guide {
		display: flex;
		align-items: center;
		justify-content: space-between;
		margin-top: 12px;
		padding-top: 12px;
		border-top: 1px solid rgba(0, 0, 0, .1);
	}

	.video-guide-title {
		font-size: 15px;
		font-weight: 700;
		color: $color-primary;
	}

	.video-btn {
		display: flex;
		align-items: center;
		justify-content: center;
		min-width: 160px;
		height: 40px;
		padding: 0 14px;
		border-radius: 8px;
		background: $color-primary;
		font-size: 13px;
		font-weight: 600;
		color: #fff;
	}

	.video-btn.disabled {
		opacity: .45;
	}

	.video-icon {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 17px;
		height: 17px;
		margin-right: 7px;
		border: 1.5px solid #fff;
		border-radius: 50%;
		color: #fff;
		font-size: 8px;
		line-height: 1;
	}

	/* ---------- Manual ---------- */
	.manual-tip {
		font-size: 12px;
		color: $text-color-secondary;
		margin-bottom: 10px;
		line-height: 1.5;
	}

	.manual-input {
		height: 44px;
		border: 1px solid #E0E0E0;
		border-radius: 10px;
		padding: 0 14px;
		margin-bottom: 10px;
		font-size: 14px;
	}

	.manual-upload {
		height: 44px;
		line-height: 44px;
		text-align: center;
		border: 1px dashed $color-secondary;
		border-radius: 10px;
		color: $color-primary;
		font-size: 13px;
		margin-bottom: 12px;
	}

	/* ---------- Notice ---------- */
	.notice-card {
		padding: 16px 18px;
		border-radius: 12px;
		border: 2px solid $color-primary;
		background: #fff;
		box-shadow: 0 1px 3px rgba(0, 0, 0, .12);
	}

	.notice-title {
		display: block;
		font-size: 13px;
		font-weight: 600;
		color: #E02B2B;
		margin-bottom: 6px;
	}

	.notice-text {
		display: block;
		font-size: 13px;
		font-weight: 600;
		color: $color-primary;
		line-height: 1.5;
	}

	/* 后台页面配置的文案：按原文显示并保留换行（2026-11-11） */
	.configured-text {
		display: block;
		white-space: pre-line;
		word-break: break-word;
	}

	/* ---------- 新增卡弹窗 ---------- */
	.modal-mask {
		position: fixed;
		left: 0;
		right: 0;
		top: 0;
		bottom: 0;
		background: rgba(0, 0, 0, .5);
		z-index: 9998;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.modal-panel {
		width: 90vw;
		max-width: 400px;
		background: #fff;
		border-radius: 12px;
		overflow: hidden;
		box-sizing: border-box;
	}

	.modal-header {
		position: relative;
		height: 44px;
		line-height: 44px;
		padding: 0 44px;
		background: $color-primary;
		font-size: 16px;
		font-weight: 600;
		color: #fff;
		text-align: center;
	}

	/* 右上角关闭按钮（文档第 14 项） */
	.modal-close {
		position: absolute;
		right: 6px;
		top: 50%;
		transform: translateY(-50%);
		width: 32px;
		height: 32px;
		line-height: 30px;
		text-align: center;
		font-size: 22px;
		font-weight: 400;
		color: #fff;
		opacity: 0.85;
	}

	.modal-form {
		padding: 12px 22px 18px;
	}

	.modal-field {
		display: flex;
		align-items: center;
		height: 32px;
		margin-bottom: 12px;
		font-size: 13px;
		color: $text-color-secondary;
	}

	.field-label {
		flex: 0 0 84px;
		color: $color-primary;
	}

	.modal-input {
		flex: 1;
		min-width: 0;
		height: 30px;
		padding: 0 8px;
		border: 1px solid $color-primary;
		border-radius: 16px;
		background: #fff;
		font-size: 13px;
		color: $color-primary;
		text-align: center;
		box-sizing: border-box;
	}

	.modal-btn {
		height: 40px;
		line-height: 40px;
		text-align: center;
		border-radius: 10px;
		font-size: 15px;
		font-weight: 600;
	}

	.modal-btn.primary {
		background: $color-primary;
		color: #fff;
	}

	.modal-btn.disabled {
		background: rgba($theme-primary-value, .5);
	}
</style>