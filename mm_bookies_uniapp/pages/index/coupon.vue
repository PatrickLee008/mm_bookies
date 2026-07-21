<template name="coupon">
	<view class="full-page">
		<zw-header></zw-header>

		<!-- from tangjq--- header占位元素，防止内容被遮挡 -->
		<view class="header-placeholder"></view>

		<!-- 标题栏 -->
		<view class="title-bar">
			<!-- Coupon / Promotion 顶部切换 -->
			<view class="type-toggle" v-if="isLogin">
				<view class="type-btn" :class="{ 'active': activity_type === 'coupon' }" @click="change_type('coupon')">
					<text>{{ $t('coupon') }}</text>
				</view>
				<view class="type-btn" :class="{ 'active': activity_type === 'promotion' }"
					@click="change_type('promotion')">
					<text>{{ $t('Promotion_title') }}</text>
					<view class="promo-count-badge" v-if="activity_type !== 'promotion' && promotionCount > 0">
						{{ promotionCount > 99 ? '99+' : promotionCount }}
					</view>
				</view>
			</view>

			<!-- 兑换码输入（仅 Coupon 且已登录） -->
			<view class="redeem-row" v-if="isLogin && activity_type === 'coupon'">
				<input class="redeem-input" :class="input_focus ? 'focus-border' : ''"
					:placeholder="$t('Enter coupon code')" placeholder-class="text-gray" v-model="key_word"
					maxlength="20" @focus="input_focus = true" @input="allow_en_num" @blur="input_focus = false" />
				<view class="redeem-btn" :class="key_word ? 'redeem-btn-active' : 'redeem-btn-disabled'"
					@click="submit_code">{{ $t('Claim') }}</view>
			</view>
		</view>

		<scroll-view scroll-y class="main-scroll-view" @scrolltolower="loadMore" :lower-threshold="60">
			<view v-if="isLogin">
				<!-- ============ Coupon 区域 ============ -->
				<view class="list-container" v-if="activity_type === 'coupon'">
					<!-- 当前进行中的优惠券活动（随页面滚动） -->
					<view class="current-activity-box" v-if="currentActivity.has_activity">
						<view class="ca-title-row">
							<text class="ca-title">{{ currentActivity.activity_name || 'Coupon Activity' }}</text>
							<text class="ca-status"
								:class="'ca-status-' + (currentActivity.status || '').toLowerCase()">
								{{ currentActivity.status || '-' }}
							</text>
						</view>
						<view class="ca-credit">
							<text class="ca-credit-label">Credit</text>
							<text
								class="ca-credit-value">{{ $toolbox.num_format(currentActivity.bonus_amount || 0) }}</text>
						</view>
						<view class="ca-stats">
							<view class="ca-stat">
								<text class="ca-stat-label">Turnover</text>
								<text
									class="ca-stat-value">{{ $toolbox.num_format(currentActivity.total_stake || 0) }}</text>
							</view>
							<view class="ca-stat">
								<text class="ca-stat-label">Promo Balance</text>
								<text class="ca-stat-value">
									{{ currentActivity.status === 'Active' ? $toolbox.num_format(currentActivity.money_promotion || 0) : '-' }}
								</text>
							</view>
						</view>
					</view>

					<!-- Tab选择器（仅 Coupon，在当前活动卡片下方，随页面滚动） -->
					<view class="tab-selector" v-if="isLogin && activity_type === 'coupon'">
						<view class="tab-container" ref="container">
							<view v-for="(item, index) in tabs" :key="index" class="tab-item"
								:class="{ 'active': tab_index === index }" @click="handleTabClick(index)">
								<text class="tab-text">{{ $t(item) }}</text>
							</view>
							<!-- 底部滑动指示器 -->
							<view class="slide-indicator" :style="{
					          width: indicator_width + 'px',
					          transform: `translateX(${indicator_offset}px)`
					        }"></view>
						</view>
					</view>

					<!-- 优惠券卡片列表 -->
					<view class="coupon-card" v-for="(coupon, index) in list" :key="index">
						<view class="coupon-card-header" :class="getHeaderClass(coupon.status)">
							<text class="coupon-card-title">{{ coupon.coupon_name || 'Coupon' }}</text>
							<text class="coupon-more" @click="openDetailModal(coupon)">Details ›</text>
						</view>
						<view class="coupon-card-body">
							<view class="coupon-thumbnail" v-if="coupon.p_img_mb && !coupon._imageError">
								<image :src="coupon.p_img_mb" mode="aspectFill" class="thumbnail-image" lazy-load
									@error="handleImageError(coupon)"></image>
							</view>
							<view class="coupon-info-left">
								<view class="info-line">
									<text class="info-label">Min Bet</text>
									<text class="info-val">{{ coupon.min_bet_required || 0 }}</text>
								</view>
								<view class="info-line">
									<text class="info-label">Used</text>
									<text
										class="info-val">{{ `${coupon.used_count || 0}${coupon.usage_limit ? '/' + coupon.usage_limit : ''}` }}</text>
								</view>
							</view>
							<view class="coupon-bonus">
								<text class="bonus-label">Bonus</text>
								<text class="bonus-value">{{ $toolbox.num_format(coupon.bonus_amount) }}</text>
							</view>
						</view>
						<view class="coupon-card-footer">
							<text class="expire-time" v-if="coupon.expire_time">Expires:
								{{ formatDateTime(coupon.expire_time) }}</text>
							<text class="expire-time" v-else>-</text>
							<view class="claim-action-btn" v-if="coupon.status === 'Unused'"
								@click="claimCoupon(coupon)">
								{{ $t('Claim') }}
							</view>
							<text class="status-text" v-else>{{ $t(coupon.status) }}</text>
						</view>
					</view>

					<!-- 空状态 -->
					<view class="empty-state" v-if="list.length === 0 && !loading">
						<image class="empty-icon" mode="heightFix" src="/static/icon/coupon.png"></image>
						<text class="empty-text">No coupons available</text>
					</view>
				</view>

				<!-- ============ Promotion 区域 ============ -->
				<view class="list-container" v-else-if="activity_type === 'promotion'">
					<view class="promotion-card2" v-for="(promo, index) in promotion_list" :key="index"
						@click="showPromotionDetail(promo)">
						<view class="promotion-card2-header" :class="getPromotionHeaderClass(promo.status)">
							<text class="promotion-card2-title">{{ promo.name }}</text>
						</view>
						<view class="promotion-card2-body">
							<view class="promo-thumb-wrap">
								<image class="promo-thumb" :src="promo.image" mode="aspectFill" lazy-load
									@error="handlePromotionImageError(promo)"></image>
							</view>
							<view class="promo-info">
								<text class="promo-label">Promotion Period</text>
								<text class="promo-period">{{ promo.period_start }} - {{ promo.period_end }}</text>
								<view class="promo-countdown"
									v-if="promo.end_time_full && isWithin48Hours(promo.end_time_full)">
									<count-down :count_time="promo.end_time_full"></count-down>
								</view>
								<text class="promo-label promo-label-mt">Terms & Conditions</text>
								<text class="promo-terms">{{ getTruncatedTerms(promo.terms, 60) }}</text>
							</view>
						</view>
						<view class="promotion-card2-footer">
							<text class="promo-amount" v-if="promo.participation_amount_type === 'Fixed'">
								K {{ $toolbox.num_format(promo.min_amount) }}
							</text>
							<text class="promo-amount" v-else>
								K
								{{ promo.min_amount == promo.max_amount ? $toolbox.num_format(promo.min_amount) : `${$toolbox.num_format(promo.min_amount)} - ${$toolbox.num_format(promo.max_amount)}` }}
							</text>
							<view v-if="promo.status === 'Available'" class="promo-status-btn">{{ promo.status }}</view>
							<text v-else class="promo-status-text"
								:style="{ color: promo.status === 'Completed' ? '#9eacb5' : '' }">{{ promo.status }}</text>
						</view>
					</view>

					<!-- 空状态 -->
					<view class="empty-state" v-if="promotion_list.length === 0 && !loading">
						<image class="empty-icon" mode="heightFix" src="/static/icon/coupon.png"></image>
						<text class="empty-text">No promotions available</text>
					</view>
				</view>
			</view>

			<!-- 未登录状态 -->
			<view class="flex-column justify-center margin-top" v-else>
				<view class="flex-column align-center justify-center">
					<image class="yellow2dblue" style="height: 60px;margin-bottom: 6px;" mode="heightFix"
						src="/static/image/deals/deals.png"></image>
					<view class="myfont-20px mycolor-primary">{{ language.please_sign_in_to_receive_the_coupon }}</view>
				</view>
			</view>

			<view style="height: 30px;width: 100%;"></view>
		</scroll-view>

		<!-- ============ 优惠券详情弹窗 ============ -->
		<view class="detail-modal" v-if="showDetailModal && selectedCoupon" @click="closeDetailModal">
			<view class="detail-modal-content" @click.stop="">
				<view class="detail-modal-header">
					<text class="detail-modal-title">Coupon Details</text>
					<text class="detail-modal-close" @click="closeDetailModal">✕</text>
				</view>

				<scroll-view scroll-y class="detail-modal-body">
					<view class="detail-coupon-title">{{ selectedCoupon.coupon_name }}</view>

					<view class="detail-image-wrapper" v-if="selectedCoupon.p_img_mb && !selectedCoupon._imageError">
						<image class="detail-image" mode="widthFix" :src="selectedCoupon.p_img_mb" lazy-load
							@error="handleImageError(selectedCoupon)"></image>
					</view>

					<!-- 兑换码 -->
					<view class="detail-code-row" v-if="selectedCoupon.p_code">
						<text class="detail-code">{{ selectedCoupon.p_code }}</text>
						<text class="detail-code-copy" @click="copyCode">Copy code</text>
					</view>

					<!-- 信息卡片 -->
					<view class="detail-info-cards">
						<view class="detail-info-card">
							<text class="detail-info-label">Expiry Date</text>
							<text class="detail-info-value">
								{{ selectedCoupon.expire_time ? formatDateTime(selectedCoupon.expire_time) : '-' }}
							</text>
						</view>
						<view class="detail-info-card">
							<text class="detail-info-label">Remaining</text>
							<text class="detail-info-value">
								{{ selectedCoupon.usage_limit ? (selectedCoupon.usage_limit - (selectedCoupon.used_count || 0)) : 'Unlimited' }}
							</text>
						</view>
					</view>

					<!-- 奖励 -->
					<view class="detail-bonus-box">
						<text class="detail-bonus-title">+ {{ $toolbox.num_format(selectedCoupon.bonus_amount) }}
							Bonus</text>
						<text class="detail-bonus-desc">Min bet required:
							{{ selectedCoupon.min_bet_required || 0 }}</text>
					</view>

					<!-- 详情描述 -->
					<view class="detail-description-section" v-if="selectedCoupon.p_content">
						<text class="detail-section-title">Details</text>
						<text class="detail-description-text">{{ selectedCoupon.p_content }}</text>
					</view>

					<!-- 使用场景 -->
					<view class="detail-description-section" v-if="couponScenarios.length > 0">
						<text class="detail-section-title">Applicable Scenarios</text>
						<view class="scenario-item" v-for="(sc, i) in couponScenarios" :key="i">
							<text class="scenario-icon">{{ sc.icon }}</text>
							<view class="scenario-text">
								<text class="scenario-label">{{ sc.label }}</text>
								<text class="scenario-detail" v-if="sc.detail">{{ sc.detail }}</text>
							</view>
						</view>
					</view>
				</scroll-view>

				<view class="detail-modal-footer" v-if="selectedCoupon.status === 'Unused'">
					<view class="detail-claim-btn" @click="claimCoupon(selectedCoupon)">
						<text class="detail-claim-text">{{ $t('Get promotions') }}</text>
					</view>
				</view>
			</view>
		</view>

		<!-- ============ Promotion 详情弹窗 ============ -->
		<view class="detail-modal" v-if="showPromotionDetailModal && selectedPromotion" @click="closePromotionDetail">
			<view class="detail-modal-content" @click.stop="">
				<view class="detail-modal-header">
					<text class="detail-modal-title">Promotion Details</text>
					<text class="detail-modal-close" @click="closePromotionDetail">✕</text>
				</view>

				<scroll-view scroll-y class="detail-modal-body">
					<view class="detail-coupon-title">{{ selectedPromotion.name }}</view>
					<view class="promo-slogan" v-if="selectedPromotion.slogan">{{ selectedPromotion.slogan }}</view>

					<view class="detail-image-wrapper">
						<image class="detail-image" mode="widthFix" :src="selectedPromotion.image" lazy-load
							@error="handlePromotionImageError(selectedPromotion)"></image>
					</view>

					<!-- 活动周期 -->
					<view class="detail-info-card full-card">
						<view class="promo-countdown-block"
							v-if="selectedPromotion.end_time_full && isWithin48Hours(selectedPromotion.end_time_full)">
							<text class="detail-info-label">Ends In</text>
							<view class="ends-in"><count-down
									:count_time="selectedPromotion.end_time_full"></count-down></view>
						</view>
						<text class="detail-info-label">Promotion Period</text>
						<text class="detail-info-value">{{ selectedPromotion.period_start_time }} -
							{{ selectedPromotion.period_end_time }}</text>
					</view>

					<!-- 条款 -->
					<view class="detail-description-section" v-if="selectedPromotion.terms">
						<text class="detail-section-title">Terms & Conditions</text>
						<text class="detail-description-text">
							{{ isTermsExpanded ? selectedPromotion.terms : getTruncatedTerms(selectedPromotion.terms, 150) }}
						</text>
						<text v-if="selectedPromotion.terms.length > 150" class="read-more" @click.stop="toggleTerms">
							{{ isTermsExpanded ? 'Show less' : 'Read more' }}
						</text>
					</view>

					<!-- 已参与：进度 -->
					<view v-if="selectedPromotion.status === 'Joined'">
						<view class="detail-description-section" v-if="selectedPromotion.required_turnover > 0">
							<text class="detail-section-title">Turnover Progress</text>
							<view class="progress-row">
								<text class="progress-label">Required</text>
								<text
									class="progress-value">{{ $toolbox.num_format(selectedPromotion.achieved_turnover || 0) }}
									/ {{ $toolbox.num_format(selectedPromotion.required_turnover || 0) }}</text>
							</view>
							<view class="progress-bar-container">
								<view class="progress-bar-fill"
									:style="{ width: (selectedPromotion.turnover_progress || 0) + '%' }"></view>
							</view>
						</view>
						<view class="detail-description-section" v-if="selectedPromotion.required_netwin > 0">
							<text class="detail-section-title">Net Win Progress</text>
							<view class="progress-row">
								<text class="progress-label">Required</text>
								<text
									class="progress-value">{{ $toolbox.num_format(selectedPromotion.achieved_netwin || 0) }}
									/ {{ $toolbox.num_format(selectedPromotion.required_netwin || 0) }}</text>
							</view>
						</view>
						<view class="detail-bonus-box">
							<view class="progress-row">
								<text class="detail-bonus-desc">Max Withdrawal</text>
								<text
									class="detail-bonus-desc">{{ $toolbox.num_format(selectedPromotion.max_withdrawal || 0) }}</text>
							</view>
							<view class="progress-row">
								<text class="detail-bonus-title">Promo Wallet</text>
								<text
									class="detail-bonus-title">{{ $toolbox.num_format(selectedPromotion.promo_wallet_balance || 0) }}</text>
							</view>
						</view>
					</view>

					<!-- 未参与：要求 -->
					<view class="detail-bonus-box" v-else>
						<view class="progress-row" v-if="selectedPromotion.participation_amount_type === 'Fixed'">
							<text class="detail-bonus-desc">Participation Amount</text>
							<text
								class="detail-bonus-desc">{{ $toolbox.num_format(selectedPromotion.min_amount) }}</text>
						</view>
						<view class="progress-row" v-else>
							<text class="detail-bonus-desc">Participation Range</text>
							<text class="detail-bonus-desc">{{ $toolbox.num_format(selectedPromotion.min_amount) }} ~
								{{ $toolbox.num_format(selectedPromotion.max_amount) }}</text>
						</view>
						<view class="progress-row">
							<text class="detail-bonus-title">Reward</text>
							<text
								class="detail-bonus-title">{{ formatRewardAmount(selectedPromotion.reward_amount, selectedPromotion.reward_amount_type) }}</text>
						</view>
					</view>

					<!-- 不可参与原因 -->
					<view class="ineligibility"
						v-if="selectedPromotion.status === 'Available' && selectedPromotion.ineligibility_reason">
						<text>{{ selectedPromotion.ineligibility_reason }}</text>
					</view>
				</scroll-view>

				<view class="detail-modal-footer">
					<view v-if="selectedPromotion.status === 'Available'" class="detail-claim-btn"
						@click="showJoinPromotionDialog">
						<text class="detail-claim-text">Join Promotion</text>
					</view>
					<view v-else-if="selectedPromotion.status === 'Joined'" class="detail-claim-btn"
						:class="{ 'claimed': !selectedPromotion.can_end }"
						@click="selectedPromotion.can_end && showEndPromotionDialog()">
						<text class="detail-claim-text">{{ $t('End Promotion') }}</text>
					</view>
				</view>
			</view>
		</view>

		<!-- ============ Join Promotion 弹窗 ============ -->
		<view class="cu-modal" :class="{ 'show': showJoinPromotionModal && selectedPromotion }"
			@click="closeJoinPromotionModal">
			<view class="join-dialog" @click.stop="" v-if="selectedPromotion">
				<view class="join-dialog-header">Join Promotion</view>
				<view class="join-dialog-content">
					<view class="join-image-wrap">
						<image class="join-image" :src="selectedPromotion.image" mode="widthFix"></image>
					</view>
					<view v-if="selectedPromotion.participation_amount_type === 'Range'">
						<text class="join-hint-label">Enter the amount you want to participate:</text>
						<view class="join-amount-input">
							<text class="join-currency">K</text>
							<input type="digit" class="join-input" v-model="joinAmount" placeholder="0"
								@input="handleAmountInput" />
						</view>
						<text class="join-range-hint">Min: K {{ $toolbox.num_format(selectedPromotion.min_amount) }} ~
							Max: K {{ $toolbox.num_format(selectedPromotion.max_amount) }}</text>
					</view>
					<view v-else>
						<text class="join-hint-label">Participation Amount:</text>
						<view class="join-amount-display">
							<text class="join-currency">K</text>
							<text
								class="join-fixed-value">{{ $toolbox.num_format(selectedPromotion.min_amount) }}</text>
						</view>
					</view>
				</view>
				<view class="join-dialog-actions">
					<view class="join-cancel-btn" @click="closeJoinPromotionModal">Cancel</view>
					<view class="join-continue-btn" @click="confirmJoinPromotion">Continue</view>
				</view>
			</view>
		</view>

	</view>
</template>

<script>
	import config from '../../utils/config.js'
	import language from '../../utils/language.js'
	import siteinfo from '../../siteinfo.js'
	import dateFormatUtils from '../../utils/utils.js'
	import CountDown from '../match/components/count_down.vue'

	export default {
		components: {
			CountDown,
		},
		name: "coupon",
		data() {
			return {
				isLogin: uni.getStorageSync('Authorization') || false,
				language: config.language,
				siteinfo: siteinfo,
				userInfo: null,
				loading: false,

				// 顶部切换：coupon / promotion
				activity_type: 'coupon',

				// Coupon Tab
				tabs: ['Unused', 'Used', 'Expired'],
				tab_index: 0,
				indicator_width: 0,
				indicator_offset: 0,

				// Coupon 列表分页
				list: [],
				page: 1,
				limit: 15,
				list_end: false,

				// 当前活动
				currentActivity: {},

				// 兑换码
				key_word: '',
				input_focus: false,

				// Coupon 详情弹窗
				showDetailModal: false,
				selectedCoupon: null,
				couponScenarios: [],

				// Promotion 列表分页
				promotion_list: [],
				promotion_page: 1,
				promotion_page_size: 20,
				promotion_list_end: false,
				promotionCount: 0,

				// Promotion 详情弹窗
				showPromotionDetailModal: false,
				selectedPromotion: null,
				isTermsExpanded: false,

				// Join Promotion 弹窗
				showJoinPromotionModal: false,
				joinAmount: '',
			}
		},
		onLoad(options) {
			if (options && options.activity_type) {
				this.activity_type = options.activity_type
			}
			if (this.isLogin) {
				this.userInfo = Object.assign({}, this.$store.state.userInfo)
				this.getCurrentActivity()
				this.getCouponList()
				// 静默预加载 promotion 用于角标与切换
				this.loadPromotionList(true)
			}
		},
		mounted() {
			this.$nextTick(() => {
				this.initIndicator()
			})
			this.userInfo = Object.assign({}, this.$store.state.userInfo)
		},
		watch: {
			tab_index() {
				this.updateIndicator()
				this.getCouponList()
			}
		},
		methods: {
			// ==================== 通用 ====================
			goto(url) {
				uni.navigateTo({
					url
				})
			},
			formatDateTime(timeStr, sep = '/') {
				if (!timeStr) return ''
				let str = this.toMyanmarTime(timeStr)
				let parts = str.split(' ')
				let d = parts[0] ? parts[0].split('-') : []
				let t = parts[1] ? parts[1].split(':') : []
				if (d.length < 3) return str
				let date = `${d[0]}${sep}${d[1]}${sep}${d[2]}`
				let time = t.length >= 2 ? ` ${t[0]}:${t[1]}` : ''
				return date + time
			},
			dateOnly(timeStr, sep = '.') {
				if (!timeStr) return ''
				let d = this.toMyanmarTime(timeStr).split(' ')[0].split('-')
				if (d.length < 3) return String(timeStr)
				return `${d[0]}${sep}${d[1]}${sep}${d[2]}`
			},
			toMyanmarTime(timeStr) {
				if (!timeStr) return ''
				const normalized = String(timeStr).replace('T', ' ').replace(/\.\d+Z?$/, '')
				try {
					return dateFormatUtils.convertTimezone(normalized, 'Asia/Yangon')
				} catch (e) {
					return normalized
				}
			},
			parseServerTime(timeStr) {
				if (!timeStr) return null
				const match = String(timeStr).replace('T', ' ').match(
					/^(\d{4})-(\d{2})-(\d{2})\s+(\d{2}):(\d{2})(?::(\d{2}))?/
				)
				if (!match) return new Date(timeStr)
				return new Date(Date.UTC(
					Number(match[1]),
					Number(match[2]) - 1,
					Number(match[3]),
					Number(match[4]),
					Number(match[5]),
					Number(match[6] || 0)
				) - 8 * 60 * 60 * 1000)
			},
			isWithin48Hours(dateStr) {
				if (!dateStr) return false
				let target = this.parseServerTime(dateStr)
				if (isNaN(target.getTime())) return false
				const diff = target - new Date()
				return diff > 0 && diff <= 48 * 60 * 60 * 1000
			},
			getTruncatedTerms(text, limit = 150) {
				if (!text) return ''
				if (text.length <= limit) return text
				return text.substring(0, limit) + '...'
			},
			formatRewardAmount(amount, type) {
				if (!amount || amount <= 0) return '0'
				const v = this.$toolbox.num_format(amount)
				return type === 'Percent' ? `${v}%` : v
			},
			handleImageError(coupon) {
				this.$set(coupon, '_imageError', true)
			},
			handlePromotionImageError(promo) {
				this.$set(promo, 'image', '/static/image/deals/deals.png')
			},
			// 刷新用户信息（余额）
			refreshUserInfo() {
				let _this = this
				if (!uni.getStorageSync('Authorization')) return
				_this.$http.get('/app_user/user_info', {}, (res) => {
					if (res.statusCode === 200 && res.data && res.data.data) {
						_this.$store.dispatch('saveUserInfo', res.data.data)
						_this.userInfo = res.data.data
					}
				})
			},

			// ==================== 切换 ====================
			change_type(type) {
				if (this.activity_type === type) return
				this.activity_type = type
				if (type === 'promotion' && this.promotion_list.length === 0) {
					this.loadPromotionList()
				}
			},
			handleTabClick(index) {
				if (this.tab_index !== index) {
					this.tab_index = index
				}
			},
			initIndicator() {
				const query = uni.createSelectorQuery().in(this)
				query.selectAll('.tab-item').boundingClientRect((res) => {
					if (res && res.length > 0) {
						this.indicator_width = res[0].width
						this.updateIndicator()
					}
				}).exec()
			},
			updateIndicator() {
				const query = uni.createSelectorQuery().in(this)
				query.selectAll('.tab-item').boundingClientRect((res) => {
					if (res && res.length > this.tab_index) {
						const cur = res[this.tab_index]
						const first = res[0]
						this.indicator_offset = cur.left - first.left
						this.indicator_width = cur.width
					}
				}).exec()
			},
			loadMore() {
				if (this.activity_type === 'coupon') {
					if (!this.list_end) this.getCouponList(true)
				} else {
					if (!this.promotion_list_end) this.loadMorePromotions()
				}
			},

			// ==================== Coupon 数据 ====================
			getCurrentActivity() {
				let _this = this
				_this.$http.get('/coupon/current_activity', {}, (res) => {
					if (res.statusCode === 200 && res.data.code === 200) {
						const data = res.data.data
						_this.currentActivity = data && data.has_activity ? data : {}
					}
				}, () => {})
			},
			getCouponList(isLoadMore = false) {
				let _this = this
				if (!isLoadMore) {
					_this.page = 1
					_this.list_end = false
					_this.list = []
				}
				const statusParam = ['Unused', 'Used', 'Expired'][_this.tab_index] || 'Unused'
				let params = {
					page: _this.page,
					page_size: _this.limit,
					status: statusParam
				}
				_this.loading = true
				uni.showLoading({
					title: 'Loading...',
					mask: true
				})
				_this.$http.get('/coupon/history', {
					data: params
				}, (res) => {
					uni.hideLoading()
					_this.loading = false
					if (res.statusCode === 200 && res.data.code === 200) {
						let coupons = res.data.data.history || []
						// 若存在进行中的活动，将对应 Used 记录标记为 Active（参考onex2_test逻辑）
						if (_this.tab_index === 1 && _this.currentActivity.status === 'Active' && _this
							.currentActivity.coupon_id) {
							coupons.forEach(c => {
								if (c.status === 'Used' && c.coupon_id === _this.currentActivity
									.coupon_id) {
									c.status = 'Active'
								}
							})
						}
						_this.list = isLoadMore ? _this.list.concat(coupons) : coupons
						if (coupons.length < _this.limit) {
							_this.list_end = true
						} else {
							_this.page++
						}
					} else {
						if (!isLoadMore) _this.list = []
						uni.showToast({
							icon: 'none',
							title: res.data.message || 'Failed to load coupons',
							duration: 2000
						})
					}
				}, () => {
					uni.hideLoading()
					_this.loading = false
					if (!isLoadMore) _this.list = []
					uni.showToast({
						icon: 'none',
						title: 'Network error',
						duration: 2000
					})
				})
			},

			// ==================== Coupon 操作 ====================
			allow_en_num() {
				this.$nextTick(() => {
					if (this.key_word) {
						this.key_word = this.key_word.replace(/[^a-zA-Z0-9]/g, '')
					}
				})
			},
			submit_code() {
				let _this = this
				let code = (_this.key_word || '').trim()
				if (!code) {
					uni.showToast({
						icon: 'none',
						title: _this.$t('Enter coupon code'),
						mask: true
					})
					return
				}
				uni.showModal({
					title: _this.$t('title_alert'),
					content: _this.$t('Do you want to claim this coupon') + '?',
					confirmText: _this.$t('Confirm'),
					cancelText: _this.$t('Cancel'),
					success: (r) => {
						if (r.confirm) _this.redeemCoupon({
							coupon_code: code
						})
					}
				})
			},
			claimCoupon(coupon) {
				let _this = this
				if (!coupon) return
				uni.showModal({
					title: _this.$t('title_alert'),
					content: _this.$t('Do you want to claim this coupon') + '?',
					confirmText: _this.$t('Confirm'),
					cancelText: _this.$t('Cancel'),
					success: (r) => {
						if (r.confirm) _this.redeemCoupon({
							coupon_id: coupon.coupon_id || coupon.id
						})
					}
				})
			},
			redeemCoupon(params) {
				let _this = this
				uni.showLoading({
					title: params.coupon_code ? 'Processing...' : 'Claiming...',
					mask: true
				})
				_this.$http.post('/coupon/redeem', params, (res) => {
					uni.hideLoading()
					const data = res.data
					if (res.statusCode === 200 && data.code === 200) {
						uni.showToast({
							icon: 'success',
							title: 'Coupon claimed successfully',
							duration: 2000
						})
						if (params.coupon_code) _this.key_word = ''
						if (_this.showDetailModal) _this.closeDetailModal()
						_this.getCurrentActivity()
						_this.getCouponList()
						_this.refreshUserInfo()
					} else {
						uni.showModal({
							title: _this.$t('title_alert'),
							content: data.message || 'Failed to claim coupon',
							showCancel: false
						})
					}
				}, () => {
					uni.hideLoading()
					uni.showToast({
						icon: 'none',
						title: 'Network error',
						duration: 2000
					})
				})
			},
			openDetailModal(coupon) {
				this.selectedCoupon = coupon
				this.couponScenarios = this.parseScenarios(coupon.usage_scenario_config)
				this.showDetailModal = true
			},
			closeDetailModal() {
				this.showDetailModal = false
				this.selectedCoupon = null
				this.couponScenarios = []
			},
			copyCode() {
				if (!this.selectedCoupon || !this.selectedCoupon.p_code) return
				uni.setClipboardData({
					data: this.selectedCoupon.p_code,
					success: () => uni.showToast({
						title: 'Copied!',
						icon: 'success'
					})
				})
			},
			getHeaderClass(status) {
				if (status === 'Expired') return 'header-expired'
				return 'header-unused'
			},
			// 解析 usage_scenario_config -> 可展示的场景列表
			parseScenarios(configStr) {
				let out = []
				if (!configStr) return out
				try {
					const cfg = typeof configStr === 'string' ? JSON.parse(configStr) : configStr
					if (cfg.type === 'All') {
						out.push({
							icon: '✅',
							label: 'All Games',
							detail: ''
						})
						return out
					}
					if (cfg.scenarios && Array.isArray(cfg.scenarios)) {
						cfg.scenarios.forEach(sc => {
							if (!sc.enabled) return
							if (sc.type === '1x2' && sc.config) {
								const bt = sc.config.bet_types || []
								out.push({
									icon: '⚽',
									label: '1x2 Sports Betting',
									detail: bt.length ? bt.join(', ') : 'All Bet Types'
								})
							} else if (sc.type === 'Egame' && sc.config) {
								const ps = (sc.config.platforms || []).map(p => typeof p === 'string' ? p : (p
									.platform_name || p.platform || p.name)).filter(Boolean)
								out.push({
									icon: '🎮',
									label: 'E-Gaming',
									detail: ps.length ? ps.join(', ') : ''
								})
							}
						})
					}
				} catch (e) {
					console.error('parse usage_scenario_config failed', e)
				}
				return out
			},

			// ==================== Promotion 数据 ====================
			mapPromotion(promo) {
				let displayStatus = 'Available'
				if (promo.status === 'Completed') {
					displayStatus = 'Completed'
				} else if (promo.is_participated) {
					displayStatus = promo.participation_status === 'Completed' ? 'Completed' : 'Joined'
				}
				const item = {
					id: promo.id,
					name: promo.title || 'PROMOTION',
					slogan: promo.slogan || '',
					image: promo.image_url || '/static/image/deals/deals.png',
					period_start: this.dateOnly(promo.start_date, '.'),
					period_end: this.dateOnly(promo.end_date, '.'),
					end_time_full: this.parseServerTime(promo.end_date),
					period_start_time: this.formatDateTime(promo.start_date),
					period_end_time: this.formatDateTime(promo.end_date),
					terms: promo.description || '',
					min_amount: promo.min_amount || 0,
					max_amount: promo.max_amount || 0,
					participation_amount_type: promo.participation_amount_type || 'Fixed',
					reward_amount: promo.reward_amount || 0,
					reward_amount_type: promo.reward_mode || 'Fixed',
					status: displayStatus,
					can_participate: promo.can_participate,
					ineligibility_reason: promo.can_participate ? '' : (promo.message || ''),
					max_withdrawal: promo.max_withdrawal_limit || 0,
					manual_end_enabled: promo.manual_end_enabled || 0,
					usage_scenario_config: promo.usage_scenario_config || null,
				}
				if (promo.progress) {
					const p = promo.progress
					item.achieved_turnover = p.turnover_progress || 0
					item.required_turnover = p.turnover_requirement || 0
					item.turnover_progress = p.turnover_percentage || 0
					item.achieved_netwin = p.netwin_progress || 0
					item.required_netwin = p.netwin_requirement || 0
					const uinfo = this.$store.state.userInfo || {}
					item.promo_wallet_balance = uinfo.money_promotion || 0
					item.can_end = p.can_end || false
				}
				return item
			},
			loadPromotionList(silent = false) {
				let _this = this
				_this.promotion_page = 1
				_this.promotion_list_end = false
				if (!silent) {
					_this.loading = true
					uni.showLoading({
						title: 'Loading...',
						mask: true
					})
				}
				_this.$http.get('/promotion/list', {
					data: {
						page: _this.promotion_page,
						page_size: _this.promotion_page_size
					}
				}, (res) => {
					if (!silent) {
						uni.hideLoading();
						_this.loading = false
					}
					if (res.statusCode === 200 && res.data.code === 200) {
						const promotions = res.data.data.promotions || []
						const pagination = res.data.data.pagination || {}
						if (pagination.total_count != null) _this.promotionCount = pagination.total_count
						if (pagination.current_page >= pagination.total_pages || promotions.length === 0) {
							_this.promotion_list_end = true
						} else {
							_this.promotion_page++
						}
						_this.promotion_list = promotions.map(p => _this.mapPromotion(p))
					} else {
						_this.promotion_list = []
						if (!silent) uni.showToast({
							icon: 'none',
							title: res.data.message || 'Failed to load promotions',
							duration: 2000
						})
					}
				}, () => {
					if (!silent) {
						uni.hideLoading();
						_this.loading = false;
						uni.showToast({
							icon: 'none',
							title: 'Network error',
							duration: 2000
						})
					}
					_this.promotion_list = _this.promotion_list || []
				})
			},
			loadMorePromotions() {
				let _this = this
				if (_this.promotion_list_end) return
				_this.$http.get('/promotion/list', {
					data: {
						page: _this.promotion_page,
						page_size: _this.promotion_page_size
					}
				}, (res) => {
					if (res.statusCode === 200 && res.data.code === 200) {
						const promotions = res.data.data.promotions || []
						const pagination = res.data.data.pagination || {}
						if (pagination.current_page >= pagination.total_pages || promotions.length === 0) {
							_this.promotion_list_end = true
						} else {
							_this.promotion_page++
						}
						_this.promotion_list = _this.promotion_list.concat(promotions.map(p => _this.mapPromotion(
							p)))
					}
				}, () => {})
			},
			getPromotionHeaderClass(status) {
				if (status === 'Completed') return 'header-expired'
				return 'header-unused'
			},

			// ==================== Promotion 操作 ====================
			showPromotionDetail(promo) {
				let _this = this
				if (promo.status === 'Available' && promo.can_participate === false && promo.ineligibility_reason) {
					uni.showModal({
						title: _this.$t('title_alert'),
						content: promo.ineligibility_reason,
						showCancel: false
					})
					return
				}
				_this.selectedPromotion = promo
				_this.showPromotionDetailModal = true
				_this.isTermsExpanded = false
				if (promo.status === 'Joined') {
					_this.loadPromotionProgress(promo.id)
				}
			},
			closePromotionDetail() {
				this.showPromotionDetailModal = false
				this.selectedPromotion = null
			},
			toggleTerms() {
				this.isTermsExpanded = !this.isTermsExpanded
			},
			loadPromotionProgress(promotionId) {
				let _this = this
				_this.$http.get(`/promotion/progress/${promotionId}`, {}, (res) => {
					if (res.statusCode === 200 && res.data.code === 200) {
						const d = res.data.data
						if (d.has_participated && _this.selectedPromotion) {
							const uinfo = _this.$store.state.userInfo || {}
							_this.selectedPromotion = Object.assign({}, _this.selectedPromotion, {
								achieved_turnover: d.turnover_progress || 0,
								required_turnover: d.turnover_requirement || 0,
								turnover_progress: d.turnover_percentage || 0,
								achieved_netwin: d.netwin_progress || 0,
								required_netwin: d.netwin_requirement || 0,
								max_withdrawal: d.max_withdrawal_limit || _this.selectedPromotion
									.max_withdrawal || 0,
								promo_wallet_balance: uinfo.money_promotion || 0,
								can_end: d.can_end || false
							})
						}
					}
				}, () => {})
			},
			showJoinPromotionDialog() {
				this.joinAmount = ''
				this.showJoinPromotionModal = true
			},
			closeJoinPromotionModal() {
				this.showJoinPromotionModal = false
				this.joinAmount = ''
			},
			handleAmountInput() {
				this.joinAmount = (this.joinAmount || '').replace(/[^\d]/g, '')
			},
			confirmJoinPromotion() {
				let _this = this
				const promo = _this.selectedPromotion
				if (!promo) return
				let amount = 0
				if (promo.participation_amount_type === 'Fixed') {
					amount = parseFloat(promo.min_amount)
				} else {
					amount = parseFloat(_this.joinAmount)
					if (!_this.joinAmount || amount <= 0) {
						uni.showToast({
							title: 'Please enter a valid amount',
							icon: 'none'
						})
						return
					}
					if (promo.min_amount && amount < promo.min_amount) {
						uni.showToast({
							title: `Minimum amount is K ${_this.$toolbox.num_format(promo.min_amount)}`,
							icon: 'none'
						})
						return
					}
					if (promo.max_amount && amount > promo.max_amount) {
						uni.showToast({
							title: `Maximum amount is K ${_this.$toolbox.num_format(promo.max_amount)}`,
							icon: 'none'
						})
						return
					}
				}
				uni.showLoading({
					title: 'Processing...',
					mask: true
				})
				_this.$http.post('/promotion/participate', {
					promotion_id: promo.id,
					participation_amount: amount
				}, (res) => {
					uni.hideLoading()
					if (res.statusCode === 200 && res.data.code === 200) {
						_this.closeJoinPromotionModal()
						setTimeout(() => _this.closePromotionDetail(), 100)
						uni.showToast({
							title: res.data.message || 'Successfully joined!',
							icon: 'success',
							duration: 2000
						})
						_this.loadPromotionList()
						_this.refreshUserInfo()
					} else {
						uni.showModal({
							title: _this.$t('title_alert'),
							content: res.data.message || 'Failed to join promotion',
							showCancel: false
						})
					}
				}, () => {
					uni.hideLoading()
					uni.showToast({
						icon: 'none',
						title: 'Network error',
						duration: 2000
					})
				})
			},
			showEndPromotionDialog() {
				let _this = this
				uni.showModal({
					title: _this.$t('title_alert'),
					content: _this.$t('are you sure end pro'),
					confirmText: _this.$t('Confirm'),
					cancelText: _this.$t('Cancel'),
					success: (r) => {
						if (r.confirm) _this.endPromotion()
					}
				})
			},
			endPromotion() {
				let _this = this
				const promo = _this.selectedPromotion
				if (!promo) return
				const promotionId = promo.id
				uni.showLoading({
					title: 'Processing...',
					mask: true
				})
				_this.$http.post('/promotion/end', {
					promotion_id: promotionId
				}, (res) => {
					uni.hideLoading()
					if (res.statusCode === 200 && res.data.code === 200) {
						_this.closePromotionDetail()
						_this.loadPromotionList()
						_this.refreshUserInfo()
						uni.showModal({
							title: 'Success',
							content: 'Promotion ended successfully',
							showCancel: false
						})
					} else {
						let msg = res.data.message || 'Failed to end promotion'
						if (res.data.data && res.data.data.unmet_conditions) {
							msg = 'Cannot end promotion:\n' + res.data.data.unmet_conditions.join('\n')
						}
						uni.showModal({
							title: _this.$t('title_alert'),
							content: msg,
							showCancel: false
						})
					}
				}, () => {
					uni.hideLoading()
					uni.showToast({
						icon: 'none',
						title: 'Network error',
						duration: 2000
					})
				})
			},
		},
	}
</script>

<style lang="scss">
	/* header占位元素样式 */
	.header-placeholder {
		height: 190px;
		width: 100%;
		flex-shrink: 0;
	}

	page {
		background: #2F5D62;
		height: 100vh;
		overflow: hidden;
	}

	.full-page {
		height: 100vh;
		background: #2F5D62;
		overflow: hidden;
		display: flex;
		flex-direction: column;
	}

	.title-bar {
		background: #fff;
		border-radius: 20px 20px 0 0;
		flex-shrink: 0;
		padding-top: 6px;
		padding-bottom: 6px;
	}

	.main-scroll-view {
		flex: 1;
		height: 0;
		background: #fff;
	}

	/* 顶部 Coupon / Promotion 切换 */
	.type-toggle {
		display: flex;
		flex-direction: row;
		padding: 8px 12px 4px;
		gap: 10px;
	}

	.type-btn {
		flex: 1;
		height: 34px;
		border-radius: 8px;
		display: flex;
		align-items: center;
		justify-content: center;
		position: relative;
		background: #e8f4f8;
		color: #2A6268;
		font-size: 14px;
		font-weight: 600;
	}

	.type-btn.active {
		background: #2F5D62;
		color: #fff;
	}

	.promo-count-badge {
		position: absolute;
		top: 2px;
		right: 8px;
		min-width: 16px;
		height: 16px;
		padding: 0 3px;
		border-radius: 8px;
		background-color: #FFC436;
		color: #2F5D62;
		font-size: 10px;
		font-weight: 700;
		line-height: 16px;
		text-align: center;
	}

	/* 兑换码输入行 */
	.redeem-row {
		display: flex;
		flex-direction: row;
		align-items: center;
		padding: 6px 12px;
		gap: 8px;
	}

	.redeem-input {
		flex: 1;
		border: solid 1px #D6D6D6;
		border-radius: 8px;
		height: 34px;
		padding: 0 12px;
		font-size: 14px;
		color: #2F5D62;
		text-align: center;
	}

	.focus-border {
		border: solid 2px #2F5D62;
	}

	.redeem-btn {
		min-width: 70px;
		height: 34px;
		line-height: 34px;
		text-align: center;
		border-radius: 8px;
		font-size: 14px;
		font-weight: bold;
	}

	.redeem-btn-active {
		background: #2F5D62;
		color: #fff;
	}

	.redeem-btn-disabled {
		background: #D9D9D9;
		color: #6D6D6D;
	}

	/* Tab 样式 */
	.tab-selector {
		width: 100%;
		background: #fff;
		border-radius: 0;
	}

	.tab-container {
		position: relative;
		display: flex;
		align-items: center;
		justify-content: space-between;
		border-bottom: 1px solid #d9d9d9;
	}

	.tab-item {
		flex: 1;
		display: flex;
		align-items: center;
		justify-content: center;
		height: 34px;
	}

	.tab-text {
		font-size: 15px;
		color: #5a7a8f;
		transition: color 0.25s ease;
	}

	.tab-item.active .tab-text {
		color: #4fb3bf;
		font-weight: 600;
	}

	.slide-indicator {
		position: absolute;
		bottom: 0;
		left: 0;
		height: 2px;
		background: #4fb3bf;
		border-radius: 2px;
		transition: all 0.3s cubic-bezier(0.4, 0.0, 0.2, 1);
	}

	/* 列表容器 */
	.list-container {
		padding: 0 15px 12px;
		background: #ffffff;
	}

	/* 当前活动卡片 */
	.current-activity-box {
		background: #e8f4f8;
		border-radius: 12px;
		padding: 14px 16px;
		margin-bottom: 16px;
	}

	.ca-title-row {
		display: flex;
		justify-content: space-between;
		align-items: center;
	}

	.ca-title {
		font-size: 15px;
		font-weight: 700;
		color: #1e3a5f;
	}

	.ca-status {
		font-size: 12px;
		font-weight: 600;
		padding: 2px 8px;
		border-radius: 6px;
		color: #fff;
		background: #4fb3bf;
	}

	.ca-status-active {
		background: #2ba84a;
	}

	.ca-status-completed {
		background: #4fb3bf;
	}

	.ca-status-cancelled,
	.ca-status-expired {
		background: #9eacb5;
	}

	.ca-credit {
		display: flex;
		flex-direction: column;
		align-items: center;
		margin: 8px 0;
	}

	.ca-credit-label {
		font-size: 11px;
		color: #2A6268;
	}

	.ca-credit-value {
		font-size: 24px;
		font-weight: bold;
		color: #2F5D62;
		line-height: 28px;
	}

	.ca-stats {
		display: flex;
		flex-direction: row;
		gap: 10px;
	}

	.ca-stat {
		flex: 1;
		background: #fff;
		border-radius: 8px;
		padding: 8px 10px;
		display: flex;
		flex-direction: column;
	}

	.ca-stat-label {
		font-size: 11px;
		color: #8B8891;
	}

	.ca-stat-value {
		font-size: 15px;
		font-weight: 700;
		color: #2F5D62;
	}

	/* 优惠券卡片 */
	.coupon-card {
		background: #fff;
		border-radius: 12px;
		margin-bottom: 15px;
		overflow: hidden;
		border: 1px solid rgba(0, 0, 0, 0.08);
		box-shadow: 0px 2px 6px rgba(0, 0, 0, 0.12);
	}

	.coupon-card-header {
		padding: 10px 15px;
		color: #fff;
		display: flex;
		flex-direction: row;
		justify-content: space-between;
		align-items: center;
	}

	.header-unused {
		background: #2F5D62;
	}

	.header-expired {
		background: #8B8891;
	}

	.coupon-card-title {
		font-size: 15px;
		font-weight: 600;
	}

	.coupon-more {
		font-size: 12px;
		opacity: 0.9;
	}

	.coupon-card-body {
		padding: 12px 15px;
		display: flex;
		flex-direction: row;
		align-items: center;
		justify-content: space-between;
	}

	.coupon-thumbnail {
		width: 74px;
		height: 54px;
		flex-shrink: 0;
		border-radius: 8px;
		overflow: hidden;
		margin-right: 12px;
	}

	.thumbnail-image {
		width: 100%;
		height: 100%;
	}

	.coupon-info-left {
		flex: 1;
		display: flex;
		flex-direction: column;
		gap: 10px;
	}

	.info-line {
		display: flex;
		flex-direction: row;
		align-items: center;
		gap: 6px;
	}

	.info-label {
		font-size: 13px;
		color: #8B8891;
		min-width: 56px;
	}

	.info-val {
		font-size: 14px;
		font-weight: 600;
		color: #2F5D62;
	}

	.coupon-bonus {
		display: flex;
		flex-direction: column;
		align-items: center;
		min-width: 90px;
	}

	.bonus-label {
		font-size: 13px;
		color: #2A6268;
	}

	.bonus-value {
		font-size: 22px;
		font-weight: bold;
		color: #2F5D62;
	}

	.coupon-card-footer {
		padding: 0 0 0 15px;
		display: flex;
		justify-content: space-between;
		align-items: center;
		border-top: 1px solid rgba(0, 0, 0, 0.06);
	}

	.expire-time {
		font-size: 12px;
		color: #999;
		flex: 1;
	}

	.claim-action-btn {
		background: #2F5D62;
		color: #fff;
		line-height: 34px;
		text-align: center;
		min-width: 100px;
		font-size: 13px;
		font-weight: bold;
	}

	.claim-action-btn:active {
		opacity: 0.85;
	}

	.status-text {
		font-size: 13px;
		font-weight: 700;
		color: #2F5D62;
		text-align: center;
		min-width: 100px;
		padding: 8px 0;
	}

	/* Promotion 卡片 */
	.promotion-card2 {
		background: #fff;
		border-radius: 12px;
		margin-bottom: 15px;
		overflow: hidden;
		border: 1px solid rgba(0, 0, 0, 0.08);
		box-shadow: 0px 2px 6px rgba(0, 0, 0, 0.12);
	}

	.promotion-card2-header {
		padding: 10px 15px;
		color: #fff;
		text-align: center;
	}

	.promotion-card2-title {
		font-size: 15px;
		font-weight: 600;
	}

	.promotion-card2-body {
		padding: 12px 15px;
		display: flex;
		flex-direction: row;
		gap: 12px;
	}

	.promo-thumb-wrap {
		width: 130px;
		height: 92px;
		flex-shrink: 0;
		border-radius: 8px;
		overflow: hidden;
	}

	.promo-thumb {
		width: 100%;
		height: 100%;
	}

	.promo-info {
		flex: 1;
		display: flex;
		flex-direction: column;
		gap: 3px;
	}

	.promo-label {
		font-size: 12px;
		color: #8B8891;
	}

	.promo-label-mt {
		margin-top: 4px;
	}

	.promo-period {
		font-size: 12px;
		color: #2F5D62;
		font-weight: bold;
	}

	.promo-countdown {
		display: flex;
		flex-direction: row;
		align-items: center;
		color: #2F5D62;
		font-weight: bold;
		font-size: 13px;
		margin-top: 2px;
	}

	.promo-terms {
		font-size: 12px;
		color: #2F5D62;
		line-height: 1.4;
	}

	.promotion-card2-footer {
		padding: 0 0 0 15px;
		display: flex;
		justify-content: space-between;
		align-items: center;
		border-top: 1px solid rgba(0, 0, 0, 0.06);
	}

	.promo-amount {
		font-size: 14px;
		font-weight: bold;
		color: #1e3a5f;
		flex: 1;
	}

	.promo-status-btn {
		background: #2F5D62;
		color: #fff;
		line-height: 34px;
		text-align: center;
		min-width: 100px;
		font-size: 13px;
		font-weight: bold;
	}

	.promo-status-text {
		font-size: 13px;
		font-weight: 700;
		color: #2F5D62;
		text-align: center;
		min-width: 100px;
		padding: 8px 0;
	}

	/* 空状态 */
	.empty-state {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		padding: 60px 20px;
	}

	.empty-icon {
		height: 60px;
		margin-bottom: 16px;
		opacity: 0.4;
	}

	.empty-text {
		font-size: 16px;
		color: #999;
	}

	/* ============ 详情弹窗（通用） ============ */
	.detail-modal {
		position: fixed;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		background: rgba(0, 0, 0, 0.6);
		display: flex;
		align-items: center;
		justify-content: center;
		z-index: 1001;
		padding: 20px;
	}

	.detail-modal-content {
		background: #fff;
		border-radius: 16px;
		width: 100%;
		max-width: 500px;
		max-height: 90vh;
		display: flex;
		flex-direction: column;
		overflow: hidden;
	}

	.detail-modal-header {
		background: #2F5D62;
		padding: 12px 16px;
		display: flex;
		justify-content: space-between;
		align-items: center;
		flex-shrink: 0;
	}

	.detail-modal-title {
		font-size: 16px;
		font-weight: 600;
		color: #fff;
	}

	.detail-modal-close {
		font-size: 18px;
		color: #fff;
		line-height: 1;
	}

	.detail-modal-body {
		flex: 1;
		padding: 16px;
		overflow-y: auto;
	}

	.detail-modal-footer {
		flex-shrink: 0;
		padding: 12px 16px;
		border-top: 1px solid rgba(0, 0, 0, 0.08);
	}

	.detail-coupon-title {
		font-size: 18px;
		font-weight: bold;
		color: #2F5D62;
		text-align: center;
		margin-bottom: 12px;
	}

	.promo-slogan {
		font-size: 13px;
		color: #8B8891;
		text-align: center;
		margin-bottom: 12px;
	}

	.detail-image-wrapper {
		width: 100%;
		border-radius: 10px;
		overflow: hidden;
		margin-bottom: 12px;
	}

	.detail-image {
		width: 100%;
	}

	.detail-code-row {
		display: flex;
		flex-direction: row;
		align-items: center;
		justify-content: space-between;
		background: #e8f4f8;
		border-radius: 8px;
		padding: 10px 14px;
		margin-bottom: 12px;
	}

	.detail-code {
		font-size: 15px;
		font-weight: bold;
		color: #2F5D62;
	}

	.detail-code-copy {
		font-size: 13px;
		color: #4fb3bf;
		font-weight: 600;
	}

	.detail-info-cards {
		display: flex;
		flex-direction: row;
		gap: 12px;
		margin-bottom: 12px;
	}

	.detail-info-card {
		flex: 1;
		background: #e8f4f8;
		border-radius: 8px;
		padding: 10px 12px;
		display: flex;
		flex-direction: column;
		gap: 4px;
	}

	.full-card {
		margin-bottom: 12px;
	}

	.detail-info-label {
		font-size: 12px;
		color: #8B8891;
	}

	.detail-info-value {
		font-size: 14px;
		font-weight: bold;
		color: #2F5D62;
	}

	.promo-countdown-block {
		margin-bottom: 8px;
	}

	.ends-in {
		font-size: 16px;
		font-weight: bold;
		color: #2F5D62;
	}

	.detail-bonus-box {
		background: #e8f4f8;
		border-radius: 10px;
		padding: 14px;
		margin-bottom: 12px;
	}

	.detail-bonus-title {
		font-size: 15px;
		font-weight: 700;
		color: #1e3a5f;
	}

	.detail-bonus-desc {
		font-size: 12px;
		color: #5a7a8f;
	}

	.detail-description-section {
		margin-bottom: 12px;
	}

	.detail-section-title {
		font-size: 15px;
		font-weight: 700;
		color: #2F5D62;
		display: block;
		margin-bottom: 6px;
	}

	.detail-description-text {
		font-size: 13px;
		color: #5a7a8f;
		line-height: 1.6;
	}

	.read-more {
		font-size: 13px;
		color: #4fb3bf;
		font-weight: bold;
		margin-top: 4px;
		display: inline-block;
	}

	.scenario-item {
		display: flex;
		flex-direction: row;
		align-items: flex-start;
		gap: 10px;
		background: #f5f9fb;
		border-radius: 8px;
		padding: 10px;
		margin-bottom: 8px;
	}

	.scenario-icon {
		font-size: 20px;
	}

	.scenario-text {
		display: flex;
		flex-direction: column;
		gap: 2px;
	}

	.scenario-label {
		font-size: 14px;
		font-weight: bold;
		color: #2F5D62;
	}

	.scenario-detail {
		font-size: 12px;
		color: #7F8C8D;
	}

	.progress-row {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 6px;
	}

	.progress-label {
		font-size: 12px;
		color: #8B8891;
	}

	.progress-value {
		font-size: 13px;
		font-weight: 700;
		color: #2F5D62;
	}

	.progress-bar-container {
		width: 100%;
		height: 8px;
		background: #e0e8ec;
		border-radius: 4px;
		overflow: hidden;
	}

	.progress-bar-fill {
		height: 100%;
		background: #4fb3bf;
		border-radius: 4px;
		transition: width 0.3s ease;
	}

	.ineligibility {
		background: #fff4f4;
		border-radius: 8px;
		padding: 10px;
		text-align: center;
		font-size: 12px;
		color: #E74C3C;
		font-weight: bold;
	}

	.detail-claim-btn {
		background: #2F5D62;
		border-radius: 10px;
		padding: 10px;
		text-align: center;
	}

	.detail-claim-btn.claimed {
		background: #9eacb5;
		opacity: 0.6;
	}

	.detail-claim-text {
		font-size: 15px;
		font-weight: 700;
		color: #fff;
	}

	/* ============ Join Promotion 弹窗 ============ */
	.cu-modal {
		position: fixed;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		z-index: 1002;
		background: rgba(0, 0, 0, 0.6);
		display: none;
		align-items: center;
		justify-content: center;
	}

	.cu-modal.show {
		display: flex;
	}

	.join-dialog {
		width: 85%;
		max-width: 400px;
		background: #fff;
		border-radius: 12px;
		overflow: hidden;
	}

	.join-dialog-header {
		background: #2F5D62;
		padding: 12px;
		text-align: center;
		font-size: 15px;
		font-weight: 700;
		color: #fff;
	}

	.join-dialog-content {
		padding: 20px;
	}

	.join-image-wrap {
		width: 100%;
		border-radius: 8px;
		overflow: hidden;
		margin-bottom: 16px;
	}

	.join-image {
		width: 100%;
	}

	.join-hint-label {
		font-size: 14px;
		color: #2F5D62;
		display: block;
		text-align: center;
		margin-bottom: 10px;
	}

	.join-amount-input,
	.join-amount-display {
		background: #e8f4f8;
		border-radius: 8px;
		padding: 12px 15px;
		display: flex;
		flex-direction: row;
		align-items: center;
		gap: 8px;
	}

	.join-currency {
		font-size: 16px;
		font-weight: 700;
		color: #2F5D62;
	}

	.join-input {
		flex: 1;
		font-size: 16px;
		color: #2F5D62;
	}

	.join-fixed-value {
		font-size: 16px;
		font-weight: 700;
		color: #2F5D62;
	}

	.join-range-hint {
		font-size: 12px;
		color: #8B8891;
		display: block;
		text-align: center;
		margin-top: 8px;
	}

	.join-dialog-actions {
		display: flex;
		flex-direction: row;
		padding: 16px 20px;
		gap: 12px;
		border-top: 1px solid #eee;
	}

	.join-cancel-btn,
	.join-continue-btn {
		flex: 1;
		height: 40px;
		line-height: 40px;
		text-align: center;
		border-radius: 8px;
		font-size: 14px;
		font-weight: bold;
	}

	.join-cancel-btn {
		background: #fff;
		color: #E74C3C;
		border: 1px solid #eee;
	}

	.join-continue-btn {
		background: #2F5D62;
		color: #fff;
	}
</style>