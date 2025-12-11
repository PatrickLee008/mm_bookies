<template name="ucenter">
	<view class="full-page">
		<zw-header></zw-header>

		<!-- from tangjq--- header占位元素，防止内容被遮挡 -->
		<view class="header-placeholder"></view>

		<!-- 标题栏 -->
		<view class="title-bar">
			<!-- Tab选择器 -->
			<view class="tab-selector" v-if="isLogin">
				<view class="tab-container" ref="container">
					<view v-for="(item, index) in tabList" :key="index" class="tab-item" :class="{ 'active': tab_index === index }" @click="handleTabClick(index)">
						<text class="tab-text">{{ item }}</text>
					</view>

					<!-- 底部滑动指示器 -->
					<view class="slide-indicator" :style="{
			          width: indicator_width + 'px',
			          transform: `translateX(${indicator_offset}px)`
			        }"></view>
				</view>
			</view>
		</view>

		<scroll-view scroll-y class="main-scroll-view">
			<view v-if="isLogin">
				<!-- Promotions 列表 (tab_index === 0) -->
				<view class="promotions-container" v-if="tab_index === 0">
					<view class="promotion-card" v-for="(coupon, index) in couponList" :key="index" @click="openDetailModal(coupon)">
						<!-- 优惠券图片占位 -->
						<view class="promotion-image-wrapper">
							<image class="promotion-image" mode="aspectFill" :src="coupon.image_url || '/static/image/deals/deals.png'"></image>
						</view>
						<!-- 优惠券标题 -->
						<view class="promotion-title-bar">
							<text class="promotion-title">{{ coupon.coupon_name || 'Promotion Title' }}</text>
						</view>
					</view>

					<!-- 空状态 -->
					<view class="empty-state" v-if="couponList.length === 0">
						<image class="empty-icon" mode="heightFix" src="/static/icon/coupon.png"></image>
						<text class="empty-text">No promotions available</text>
					</view>
				</view>

				<!-- Claim History 列表 (tab_index === 1) -->
				<view class="claim-history-container" v-if="tab_index === 1">
					<!-- 统计信息框 -->
					<view class="claim-stats-box">
						<text class="stats-title">My Claim Stats</text>

						<view class="stats-row">
							<text class="stat-label">Total Promotions</text>
							<text class="stat-value">{{ getClaimStats().totalPromotions }}</text>
							<text class="stat-label stat-label-right">Active Promotions</text>
							<text class="stat-value">{{ getClaimStats().activePromotions }}</text>
						</view>

						<view class="stats-row">
							<text class="stat-label">Total Bonus</text>
							<text class="stat-value-large">{{ getClaimStats().totalBonus }}</text>
						</view>
					</view>

					<!-- 历史记录列表 -->
					<view class="history-card" v-for="(coupon, index) in couponList" :key="index">
						<view class="history-header">
							<text class="history-title">{{ coupon.coupon_name || 'Daily Bonus 3%' }}</text>
							<text class="history-action">Recharge</text>
						</view>

						<view class="history-details">
							<view class="detail-row">
								<text class="detail-label">Participation Time</text>
								<text class="detail-value">{{ formatTime(coupon.use_time || coupon.create_time) }}</text>
							</view>
							<view class="detail-row">
								<text class="detail-label">Completion Time</text>
								<text class="detail-value">{{ formatTime(coupon.expire_time) }}</text>
							</view>
							<view class="detail-row">
								<text class="detail-label">Total Bonus</text>
								<text class="detail-value-bold">{{ coupon.bonus_amount || '10,000' }}</text>
							</view>
						</view>

						<view class="history-status-btn">
							<text class="status-btn-text">Completed</text>
						</view>
					</view>

					<!-- 空状态 -->
					<view class="empty-state" v-if="couponList.length === 0">
						<image class="empty-icon" mode="heightFix" src="/static/icon/coupon.png"></image>
						<text class="empty-text">No claim history</text>
					</view>
				</view>
			</view>

			<!-- 未登录状态 -->
			<view class="flex-column justify-center margin-top" v-else>
				<view class="flex-column align-center justify-center">
					<image class="yellow2dblue" style="height: 60px;margin-bottom: 6px;" mode="heightFix" src="/static/image/deals/deals.png"></image>
					<view class="myfont-20px mycolor-primary">{{language.please_sign_in_to_receive_the_coupon}}</view>
				</view>
			</view>
		</scroll-view>

		<!-- 详情弹窗 (Promotion Details) -->
		<view class="detail-modal" v-if="showDetailModal" @click="closeDetailModal">
			<view class="detail-modal-content" @click.stop="">
				<!-- 弹窗标题栏 -->
				<view class="detail-modal-header">
					<text class="detail-modal-title">Promotion Details</text>
					<text class="detail-modal-close" @click="closeDetailModal">✕</text>
				</view>

				<!-- 优惠券图片和标题 -->
				<view class="detail-coupon-card">
					<view class="detail-image-wrapper">
						<image class="detail-image" mode="aspectFill" :src="selectedCoupon.image_url || '/static/image/deals/deals.png'"></image>
					</view>
					<view class="detail-title-bar">
						<text class="detail-title">{{ selectedCoupon.coupon_name || 'Promotion Title' }}</text>
					</view>
				</view>

				<!-- 详情描述 -->
				<view class="detail-description-section">
					<text class="detail-section-title">Promotion details</text>
					<text class="detail-description-text">
						{{ selectedCoupon.description || 'description' }}
					</text>
				</view>

				<!-- 奖励信息框 -->
				<view class="detail-bonus-box">
					<text class="detail-bonus-title">+ {{ selectedCoupon.bonus_amount }} Bonus</text>
					<text class="detail-bonus-desc">
						{{ 'min_bet_required is '+ selectedCoupon.min_bet_required }}
						{{ ',between ' + selectedCoupon.start_time+' to '+selectedCoupon.start_time }}
					</text>
				</view>

				<!-- Claim 按钮 -->
				<view class="detail-claim-btn" :class="{ 'claimed': isCouponClaimed(selectedCoupon) }" @click="claimCoupon">
					<text class="detail-claim-text">{{ isCouponClaimed(selectedCoupon) ? 'Already Claimed' : 'Claim' }}</text>
				</view>
			</view>
		</view>

		<!-- 兑换码弹窗 (保留原有功能) -->
		<view class="cu-modal" style="z-index: 1001;" :class="{'show':!hidden,}" @click="hidden=true">
			<view class="cu-dialog padding-sm width-100" style="vertical-align: top;background: none;" @click.stop="">
				<view class="height-10vh"></view>
				<view class="min-height-30vw bg-white radius-10px padding flex-column1 justify-start">
					<view class="flex-row justify-between">
						<view class="flex-column1 align-start margin-bottom-sm">
							<view class="myfont-10px">{{language.username}}</view>
							<view class="myfont-20px mycolor-primary text-bold line-height-18px">{{userInfo.username}}
							</view>
						</view>
						<text class="cuIcon-roundclose myfont-20px" @click="hidden=true"></text>
					</view>
					<input class="width-100 text-left input-rec" :class="input_focus?'focus-border':''" placeholder="Enter coupon code" placeholder-class="text-gray" v-model="key_word" @focus="input_focus=true" @blur="input_focus=false" />
					<view class="width-100 height-35px radius-8px margin-bottom-sm" :class="key_word?'mybg-lprimary':'mybg-info'" @click="submit_code">
						{{'Redeem'}}
					</view>
				</view>
			</view>
		</view>

	</view>
</template>

<script>
	import config from '../../utils/config.js'
	import language from '../../utils/language.js'
	import selector from '../../components/common/selector.vue'

	export default {
		components: {
			selector,
		},
		name: "ucenter",
		data() {
			return {
				isLogin: uni.getStorageSync('Authorization') || false,
				language: config.language,
				userInfo: null,

				page: 1,
				list_end: false,
				limit: 15,
				list: [],
				pay_label: ['pending', 'success', 'reject'],
				type_list: [],
				status_list: [],
				date_range: [{}, {}],

				tab_index: 0,
				container_width: 0,
				indicator_width: 0,
				indicator_offset: 0,
				tabs: ['Promotions', 'Claim History'],

				couponList: [],

				key_word: '',
				input_focus: false,
				hidden: true,

				// from tangjq--- 详情弹窗相关变量
				showDetailModal: false,
				selectedCoupon: null,
				claimedCoupons: [], // 存储已领取的优惠券ID

				// from Tangjq--- 模拟数据：Promotions (未使用的优惠券)
				mockPromotionsData: [{
						id: 1,
						coupon_id: 'PROMO001',
						coupon_name: 'Welcome Bonus 100%',
						image_url: '/static/image/deals/deals.png',
						description: 'Get 100% bonus on your first deposit! Minimum deposit of 1,000 required. Valid for sports betting and casino games. Terms and conditions apply.',
						bonus_amount: '5,000',
						min_bet_required: '1,000',
						start_time: '2025-12-01 00:00',
						expire_time: '2025-12-31 23:59',
						create_time: '2025-12-01 10:30:00',
						status: 'Unused',
						turnover_requirement: 0,
						turnover_progress: 0
					},
					{
						id: 2,
						coupon_id: 'PROMO002',
						coupon_name: 'Daily Bonus 3%',
						image_url: '/static/image/deals/deals.png',
						description: 'Daily recharge bonus of 3%! Recharge any amount and get instant 3% bonus. Maximum bonus: 10,000. Can be claimed once per day.',
						bonus_amount: '300',
						min_bet_required: '500',
						start_time: '2025-12-10 00:00',
						expire_time: '2025-12-15 23:59',
						create_time: '2025-12-10 08:00:00',
						status: 'Unused',
						turnover_requirement: 0,
						turnover_progress: 0
					},
					{
						id: 3,
						coupon_id: 'PROMO003',
						coupon_name: 'Weekend Cashback 10%',
						image_url: '/static/image/deals/deals.png',
						description: 'Get 10% cashback on all losses during weekends! Valid from Saturday 00:00 to Sunday 23:59. Maximum cashback: 50,000. Automatically credited on Monday.',
						bonus_amount: '1,500',
						min_bet_required: '2,000',
						start_time: '2025-12-14 00:00',
						expire_time: '2025-12-16 23:59',
						create_time: '2025-12-11 09:15:00',
						status: 'Unused',
						turnover_requirement: 0,
						turnover_progress: 0
					},
					{
						id: 4,
						coupon_id: 'PROMO004',
						coupon_name: 'VIP Exclusive Bonus',
						image_url: '/static/image/deals/deals.png',
						description: 'Exclusive bonus for VIP members! Get extra 20% on deposits above 10,000. Valid for all games. VIP level 3 and above required.',
						bonus_amount: '8,000',
						min_bet_required: '10,000',
						start_time: '2025-12-01 00:00',
						expire_time: '2025-12-31 23:59',
						create_time: '2025-12-05 14:20:00',
						status: 'Unused',
						turnover_requirement: 0,
						turnover_progress: 0
					},
					{
						id: 5,
						coupon_id: 'PROMO005',
						coupon_name: 'Free Bet 500',
						image_url: '/static/image/deals/deals.png',
						description: 'Claim your free bet of 500! No deposit required. Can be used on any sports event with odds 1.5 or higher. Win only, stake not returned.',
						bonus_amount: '500',
						min_bet_required: '0',
						start_time: '2025-12-11 00:00',
						expire_time: '2025-12-13 23:59',
						create_time: '2025-12-11 11:00:00',
						status: 'Unused',
						turnover_requirement: 0,
						turnover_progress: 0
					},
					{
						id: 6,
						coupon_id: 'PROMO006',
						coupon_name: 'Refer a Friend Bonus',
						image_url: '/static/image/deals/deals.png',
						description: 'Invite friends and earn rewards! Get 1,000 bonus for each friend who registers and makes their first deposit. No limit on referrals.',
						bonus_amount: '1,000',
						min_bet_required: '0',
						start_time: '2025-12-01 00:00',
						expire_time: '2025-12-31 23:59',
						create_time: '2025-12-08 16:45:00',
						status: 'Unused',
						turnover_requirement: 0,
						turnover_progress: 0
					}
				],

				// from Tangjq--- 模拟数据：Claim History (已使用的优惠券)
				mockClaimHistoryData: [{
						id: 101,
						coupon_id: 'CLAIM001',
						coupon_name: 'Daily Bonus 3%',
						image_url: '/static/image/deals/deals.png',
						description: 'Daily recharge bonus of 3%',
						bonus_amount: '10,000',
						min_bet_required: '5,000',
						start_time: '2025-12-01 00:00',
						expire_time: '2025-12-05 23:59',
						create_time: '2025-12-01 10:00:00',
						use_time: '2025-12-01 14:30:00',
						status: 'Used',
						game_status: 'Win',
						turnover_requirement: 50000,
						turnover_progress: 50000
					},
					{
						id: 102,
						coupon_id: 'CLAIM002',
						coupon_name: 'Welcome Bonus 100%',
						image_url: '/static/image/deals/deals.png',
						description: 'First deposit bonus',
						bonus_amount: '15,000',
						min_bet_required: '10,000',
						start_time: '2025-11-25 00:00',
						expire_time: '2025-11-30 23:59',
						create_time: '2025-11-25 09:00:00',
						use_time: '2025-11-25 10:15:00',
						status: 'Used',
						game_status: 'Win',
						turnover_requirement: 75000,
						turnover_progress: 75000
					},
					{
						id: 103,
						coupon_id: 'CLAIM003',
						coupon_name: 'Weekend Cashback 10%',
						image_url: '/static/image/deals/deals.png',
						description: 'Weekend special cashback',
						bonus_amount: '8,500',
						min_bet_required: '3,000',
						start_time: '2025-11-30 00:00',
						expire_time: '2025-12-02 23:59',
						create_time: '2025-11-30 08:00:00',
						use_time: '2025-11-30 12:45:00',
						status: 'Used',
						game_status: 'Lose',
						turnover_requirement: 42500,
						turnover_progress: 42500
					},
					{
						id: 104,
						coupon_id: 'CLAIM004',
						coupon_name: 'Free Bet 500',
						image_url: '/static/image/deals/deals.png',
						description: 'Free bet promotion',
						bonus_amount: '2,000',
						min_bet_required: '0',
						start_time: '2025-12-05 00:00',
						expire_time: '2025-12-08 23:59',
						create_time: '2025-12-05 07:30:00',
						use_time: '2025-12-05 16:20:00',
						status: 'Used',
						game_status: 'Win',
						turnover_requirement: 10000,
						turnover_progress: 10000
					},
					{
						id: 105,
						coupon_id: 'CLAIM005',
						coupon_name: 'VIP Exclusive Bonus',
						image_url: '/static/image/deals/deals.png',
						description: 'VIP member special bonus',
						bonus_amount: '25,000',
						min_bet_required: '20,000',
						start_time: '2025-11-20 00:00',
						expire_time: '2025-11-25 23:59',
						create_time: '2025-11-20 11:00:00',
						use_time: '2025-11-20 15:30:00',
						status: 'Used',
						game_status: 'Win',
						turnover_requirement: 125000,
						turnover_progress: 125000
					},
					{
						id: 106,
						coupon_id: 'CLAIM006',
						coupon_name: 'Refer a Friend Bonus',
						image_url: '/static/image/deals/deals.png',
						description: 'Referral reward',
						bonus_amount: '3,500',
						min_bet_required: '1,000',
						start_time: '2025-12-08 00:00',
						expire_time: '2025-12-10 23:59',
						create_time: '2025-12-08 09:30:00',
						use_time: '2025-12-08 13:15:00',
						status: 'Used',
						game_status: 'Pending',
						turnover_requirement: 17500,
						turnover_progress: 8500
					},
					{
						id: 107,
						coupon_id: 'CLAIM007',
						coupon_name: 'Daily Bonus 3%',
						image_url: '/static/image/deals/deals.png',
						description: 'Daily recharge bonus',
						bonus_amount: '6,200',
						min_bet_required: '2,500',
						start_time: '2025-12-09 00:00',
						expire_time: '2025-12-11 23:59',
						create_time: '2025-12-09 08:45:00',
						use_time: '2025-12-09 11:30:00',
						status: 'Used',
						game_status: 'Draw',
						turnover_requirement: 31000,
						turnover_progress: 31000
					}
				]
			}
		},
		onLoad() {
			if (this.isLogin) {
				this.userInfo = Object.assign({}, this.$store.state.userInfo)
				this.date_range = [this.getCurrentDate(0), this.getCurrentDate(0)]
				this.getCouponList();
				this.parse_option_list()
			}

		},
		computed: {
			tabList() {
				return this.tabs
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
			submit_code() {
				let _this = this
				let key_word = _this.key_word.trim()
				if (!key_word) {
					uni.showToast({
						icon: 'none',
						title: 'Please enter coupon code',
						mask: true,
					})
					return
				}

				uni.showModal({
					title: 'Tips',
					content: this.language.do_you_want_to_receive_this_bonus,
					confirmText: this.language.confirm,
					cancelText: 'Cancel',
					success: res => {
						if (res.confirm) {
							_this.redeemCoupon(key_word)
						}
					}
				})
			},

			redeemCoupon(coupon_code) {
				let _this = this

				uni.showLoading({
					title: 'Processing...',
					mask: true
				})

				_this.$http.post('/coupon/redeem', {
					coupon_code: coupon_code
				}, (res) => {
					uni.hideLoading()
					const data = res.data
					if (res.statusCode === 200) {
						if (data.code === 200) {
							// 兑换成功
							uni.showToast({
								icon: 'success',
								title: 'Coupon redeemed successfully!',
								mask: true,
								duration: 2000
							})

							// 清空输入框并关闭弹窗
							_this.key_word = ''
							_this.hidden = true

							// 更新用户信息和促销余额
							_this.updateUserInfo(data.data)

							// 重新加载优惠券列表
							if (_this.isLogin) {
								_this.getCouponList()
							}
						}
					} else {
						let errorMessage = data.message || 'Redemption failed'

						uni.showToast({
							icon: 'none',
							title: errorMessage,
							mask: true,
							duration: 3000
						})
					}
				}, (err) => {
					uni.hideLoading()
					uni.showToast({
						icon: 'none',
						title: 'Request failed, please try again',
						mask: true,
						duration: 2000
					})
				})
			},

			updateUserInfo(redemptionData) {
				// 更新本地用户信息
				let userInfo = this.$store.state.userInfo || {}

				// 如果返回了新的促销余额，更新本地存储
				if (redemptionData.new_promotion_balance !== undefined) {
					userInfo.money_promotion = redemptionData.new_promotion_balance
					this.$store.commit('updateUserInfo', userInfo)
				}

				// 显示详细的兑换信息（可选）
				setTimeout(() => {
					uni.showModal({
						title: 'Redemption Success',
						content: `Coupon: ${redemptionData.coupon_name}\nBonus: ${redemptionData.bonus_amount}\n`,
						showCancel: false,
						confirmText: 'OK'
					})
				}, 2000)
			},
			goto(url) {
				uni.navigateTo({
					url: url,
				})
			},
			get_list() {
				var _this = this;
				var para = {
					page: _this.page,
					limit: _this.limit,
					start_time: _this.date_range[0].value,
					end_time: _this.date_range[1].value,
				}
				let type = _this.type_list.find(item => item.checked)
				let status = _this.status_list.find(item => item.checked)
				if (type && type.value) para.type = type.value - 1
				if (status && status.value) para.status = status.value - 1

				uni.showLoading({
					'title': 'loading'
				})
				// _this.list = []
				_this.$http.get('/withdraw/get', {
					data: para
				}, (res) => {
					if (res.statusCode == 200) {
						uni.hideLoading();
						var results = res.data.items;
						_this.total_withdraw = parseInt(res.data.total_amount)
						results.forEach(element => {
							element.CREATE_TIME = element.CREATE_TIME.substring(0, 16);
							// console.log(_this.list)
							_this.list.push(element);
						})
						if (results.length < _this.limit) {
							_this.list_end = true

						}
					}
				})
			},
			clickLoadMore() {
				if (this.list_end) {
					uni.showToast({
						'title': 'no more',
						'icon': 'none'
					})
					return
				}
				this.page++;
				this.get_list();
			},
			numberFormat(num) {
				return dateFormatUtils.numFormat(num)
			},
			reset_list() {
				this.page = 1
				this.list_end = false
				this.limit = 15
				this.list = []
			},
			parse_option_list() {
				function parse_list(list) {
					return list.map((ele, index) => {
						return {
							label: ele,
							checked: index === 0,
							value: index ? index : '',
						}
					})
				}
				let type = ['all', 'Active', 'Finished', 'Cancelled']
				let status = ['All', 'Pending', 'Win', 'Lose', 'Draw', 'Cancel', 'Refund']
				this.type_list = parse_list(type)
				this.status_list = parse_list(status)
			},
			click_option(item) {
				this.reset_list()
				this.getCouponList()
			},
			date_click(arr) {
				// let start = arr[0]
				// let end = arr[1]
				this.date_range = arr
				this.reset_list()
				this.getCouponList()
			},
			getCurrentDate(n) {
				var dd = new Date();
				if (n) {
					dd.setDate(dd.getDate() - n);
				}
				var year = dd.getFullYear();
				const month = String(dd.getMonth() + 1).padStart(2, '0');
				const day = String(dd.getDate()).padStart(2, '0');
				return {
					value: `${year}-${month}-${day}`,
					show: `${day}/${month}/${year}`,
				};
			},

			// 点击标签
			handleTabClick(index) {
				if (this.tab_index !== index) {
					this.tab_index = index
					this.$emit('change', {
						index,
						value: this.tabList[index]
					})
				}
			},
			// from tangjq--- 初始化指示器
			initIndicator() {
				const query = uni.createSelectorQuery().in(this)
				query.selectAll('.tab-item').boundingClientRect().exec((res) => {
					if (res[0] && res[0].length > 0) {
						// from tangjq--- 获取第一个tab的宽度作为指示器宽度
						this.indicator_width = res[0][0].width
						this.updateIndicator()
					}
				})
			},
			// from tangjq--- 更新指示器位置
			updateIndicator() {
				const query = uni.createSelectorQuery().in(this)
				query.selectAll('.tab-item').boundingClientRect().exec((res) => {
					if (res[0] && res[0].length > this.tab_index) {
						// from tangjq--- 根据当前tab的位置设置指示器偏移
						const currentTab = res[0][this.tab_index]
						const container = res[0][0]
						this.indicator_offset = currentTab.left - container.left
						this.indicator_width = currentTab.width
					}
				})
			},

			// 获取优惠券列表
			getCouponList() {
				let _this = this
				// from Tangjq--- 临时使用模拟数据，注释掉下面这行可恢复API调用
				return this._getCouponList_Mock()

				// 根据tab_index确定status参数
				let statusParam = null
				if (_this.tab_index === 0) {
					// UNUSED
					statusParam = 'Unused'
				} else if (_this.tab_index === 1) {
					// USED
					statusParam = 'Used'
				} else if (_this.tab_index === 2) {
					// EXPIRED
					statusParam = 'Expired'
				}

				let params = {
					page: 1,
					page_size: 50
				}

				// 添加日期筛选 - 根据不同状态筛选不同时间字段
				if (_this.date_range && _this.date_range.length === 2) {
					if (_this.date_range[0].value) {
						params.start_time = _this.date_range[0].value
						// 传递时间类型参数，告诉后端筛选哪个时间字段
						if (_this.tab_index === 1) {
							// Used状态：筛选使用时间（bet_use_time 或 use_time）
							params.time_type = 'use_time'
						} else if (_this.tab_index === 2) {
							// Expired状态：筛选过期时间（expire_time）
							params.time_type = 'expire_time'
						}
					}
					if (_this.date_range[1].value) {
						params.end_time = _this.date_range[1].value
					}
				}

				if (statusParam !== null) {
					params.status = statusParam
				}

				// 如果是USED状态且选择了Status筛选器，则传递game_status参数
				if (_this.tab_index === 1 && _this.status_list) {
					let selectedStatus = _this.status_list.find(item => item.checked)
					if (selectedStatus && selectedStatus.label && selectedStatus.label !== 'All') {
						// status_list中的选项：['All', 'Pending', 'Win', 'Lose', 'Draw', 'Cancel', 'Refund']
						// 直接使用label作为game_status值
						params.game_status = selectedStatus.label
					}
				}

				uni.showLoading({
					title: 'Loading...',
					mask: true
				})

				_this.$http.get('/coupon/history', {
					data: params
				}, (res) => {
					uni.hideLoading()

					if (res.statusCode === 200 && res.data.code === 200) {
						let coupons = res.data.data.history || []
						_this.couponList = coupons
					} else {
						_this.couponList = []
						uni.showToast({
							icon: 'none',
							title: res.data.message || 'Failed to load coupons',
							duration: 2000
						})
					}
				}, (err) => {
					uni.hideLoading()
					_this.couponList = []
					uni.showToast({
						icon: 'none',
						title: 'Network error',
						duration: 2000
					})
				})
			},

			// 获取状态样式类
			getStatusClass(status) {
				switch (status) {
					case 'Used':
						return 'status-used'
					case 'Expired':
						return 'status-expired'
					case 'Unused':
					default:
						return 'status-unused'
				}
			},

			// 获取进度条宽度
			getProgressWidth(coupon) {
				if (!coupon.turnover_requirement || coupon.turnover_requirement <= 0) {
					return '0%'
				}
				let percentage = (coupon.turnover_progress / coupon.turnover_requirement) * 100
				return Math.min(100, percentage) + '%'
			},

			// 格式化时间
			formatTime(timeStr) {
				if (!timeStr) return ''
				let date = new Date(timeStr)
				return date.toLocaleDateString() + ' ' + date.toLocaleTimeString().slice(0, 5)
			},

			// 获取比赛状态样式类
			getGameStatusClass(gameStatus) {
				if (!gameStatus) return 'game-status-default'

				switch (gameStatus.toLowerCase()) {
					case 'pending':
						return 'game-status-pending'
					case 'running':
						return 'game-status-running'
					case 'finished':
						return 'game-status-finished'
					case 'cancelled':
						return 'game-status-cancelled'
					case 'win':
						return 'game-status-win'
					case 'lose':
						return 'game-status-lose'
					case 'draw':
						return 'game-status-draw'
					default:
						return 'game-status-default'
				}
			},

			// from tangjq--- 打开详情弹窗
			openDetailModal(coupon) {
				this.selectedCoupon = coupon
				this.showDetailModal = true
			},

			// from tangjq--- 关闭详情弹窗
			closeDetailModal() {
				this.showDetailModal = false
				this.selectedCoupon = null
			},

			// from tangjq--- 领取优惠券
			claimCoupon() {
				let _this = this
				if (!_this.selectedCoupon) return

				// 检查是否已经领取
				if (_this.isCouponClaimed(_this.selectedCoupon)) {
					return
				}
				// from Tangjq--- 模拟领取操作（临时使用）
				uni.showLoading({
					title: 'Processing...',
					mask: true
				})

				setTimeout(() => {
					uni.hideLoading()

					// 模拟成功领取
					uni.showToast({
						icon: 'success',
						title: 'Claimed successfully!',
						duration: 2000
					})

					// 添加到已领取列表
					let couponId = _this.selectedCoupon.id || _this.selectedCoupon.coupon_id
					_this.claimedCoupons.push(couponId)

					// 关闭弹窗
					_this.closeDetailModal()

					// 刷新列表
					_this.getCouponList()
				}, 800)

				// from Tangjq--- 原有API调用已注释在下方

				// uni.showLoading({
				// 	title: 'Processing...',
				// 	mask: true
				// })

				// 模拟调用领取接口（假设使用优惠券ID或code）
				// _this.$http.post('/coupon/claim', {
				// 	coupon_id: _this.selectedCoupon.id || _this.selectedCoupon.coupon_id
				// }, (res) => {
				// 	uni.hideLoading()
				// 	if (res.statusCode === 200 && res.data.code === 200) {
				// 		uni.showToast({
				// 			icon: 'success',
				// 			title: 'Claimed successfully!',
				// 			duration: 2000
				// 		})

				// 		// 添加到已领取列表
				// 		_this.claimedCoupons.push(_this.selectedCoupon.id || _this.selectedCoupon.coupon_id)

				// 		// 刷新列表
				// 		_this.getCouponList()
				// 	} else {
				// 		uni.showToast({
				// 			icon: 'none',
				// 			title: res.data.message || 'Claim failed',
				// 			duration: 2000
				// 		})
				// 	}
				// }, (err) => {
				// 	uni.hideLoading()
				// 	uni.showToast({
				// 		icon: 'none',
				// 		title: 'Network error',
				// 		duration: 2000
				// 	})
				// })
			},

			// from tangjq--- 检查优惠券是否已领取
			isCouponClaimed(coupon) {
				if (!coupon) return false
				let couponId = coupon.id || coupon.coupon_id
				return this.claimedCoupons.includes(couponId) || coupon.status === 'Used'
			},

			// from tangjq--- 获取统计数据
			getClaimStats() {
				let totalPromotions = this.couponList.length
				let activePromotions = this.couponList.filter(c => c.status === 'Used').length
				let totalBonus = this.couponList.reduce((sum, c) => {
					return sum + (parseFloat(c.bonus_amount) || 0)
				}, 0)

				return {
					totalPromotions,
					activePromotions,
					totalBonus: totalBonus.toFixed(0).replace(/\B(?=(\d{3})+(?!\d))/g, ',')
				}
			},

			// from Tangjq--- 模拟数据版本的getCouponList（临时替换原方法）
			_getCouponList_Mock() {
				let _this = this

				uni.showLoading({
					title: 'Loading...',
					mask: true
				})

				setTimeout(() => {
					uni.hideLoading()

					if (_this.tab_index === 0) {
						// Promotions - 未使用的优惠券
						_this.couponList = JSON.parse(JSON.stringify(_this.mockPromotionsData))
					} else if (_this.tab_index === 1) {
						// Claim History - 已使用的优惠券
						_this.couponList = JSON.parse(JSON.stringify(_this.mockClaimHistoryData))
					} else {
						_this.couponList = []
					}
				}, 500)
			}
		},
		created() {}
	}
</script>

<style lang="scss">
	/* from tangjq--- header占位元素样式 */
	.header-placeholder {
		height: 220px;
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
	}

	.main-scroll-view {
		flex: 1;
		height: 0;
		background: #fff;
	}

	/* Tab 样式 */
	.tab-selector {
		width: 100%;
		background: #fff;
		// padding: 0 10px;
		border-radius: 20px 20px 0 0;
	}

	.tab-container {
		position: relative;
		display: flex;
		align-items: center;
		justify-content: space-between;
		border-bottom: 1px solid #d9d9d9;
	}

	.tab-item {
		display: flex;
		align-items: center;
		cursor: pointer;
		height: 30px;
		padding: 0 10px;
	}

	.tab-text {
		font-size: 16px;
		color: #5a7a8f;
		transition: color 0.25s ease;
		font-weight: 400;
	}

	.tab-item.active .tab-text {
		color: #4fb3bf;
		// font-weight: 600;
	}

	.slide-indicator {
		position: absolute;
		bottom: 0;
		height: 1px;
		background: #4fb3bf;
		border-radius: 2px;
		transition: all 0.3s cubic-bezier(0.4, 0.0, 0.2, 1);
	}

	/* Promotions 列表样式 */
	.promotions-container {
		padding: 10px 15px;
		background: #ffffff;
	}

	.promotion-card {
		background: #fff;
		border-radius: 16px;
		margin-bottom: 16px;
		overflow: hidden;
	}

	.promotion-image-wrapper {
		width: 100%;
		height: 133px;
		overflow: hidden;
	}

	.promotion-image {
		width: 100%;
		height: 100%;
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
	}

	.promotion-title-bar {
		background: #2F5D62;
		padding: 12px;
		text-align: center;
	}

	.promotion-title {
		font-size: 16px;
		font-weight: 600;
		color: #fff;
	}

	/* Claim History 样式 */
	.claim-history-container {
		padding: 16px;
		background: #ffffff;
	}

	.claim-stats-box {
		background: #e8f4f8;
		border-radius: 12px;
		padding: 24px 20px;
		margin-bottom: 20px;
	}

	.stats-title {
		font-size: 16px;
		font-weight: 700;
		color: #1e3a5f;
		display: block;
		margin-bottom: 20px;
		text-align: center;
	}

	.stats-row {
		display: flex;
		align-items: center;
		justify-content: space-between;
		margin-bottom: 12px;
	}

	.stat-label {
		font-size: 14px;
		color: #2A6268;
		font-weight: 400;
	}

	.stat-label-right {
		margin-left: auto;
		margin-right: 12px;
	}

	.stat-value {
		font-size: 16px;
		font-weight: 600;
		color: #2A6268;
		margin-left: 12px;
	}

	.stat-value-large {
		font-size: 16px;
		font-weight: 600;
		color: #2A6268;
	}

	/* History Card 样式 */
	.history-card {
		background: #fff;
		border-radius: 16px;
		padding: 20px;
		margin-bottom: 16px;
		box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
	}

	.history-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 16px;
	}

	.history-title {
		font-size: 18px;
		font-weight: 700;
		color: #1e3a5f;
	}

	.history-action {
		font-size: 16px;
		color: #4fb3bf;
		font-weight: 600;
	}

	.history-details {
		background: #e8f4f8;
		border-radius: 10px;
		padding: 16px;
		margin-bottom: 16px;
	}

	.detail-row {
		display: flex;
		justify-content: space-between;
		margin-bottom: 12px;
	}

	.detail-row:last-child {
		margin-bottom: 0;
	}

	.detail-label {
		font-size: 14px;
		color: #2F5D62;
		font-weight: 400;
	}

	.detail-value {
		font-size: 14px;
		color: #1e3a5f;
		font-weight: 500;
	}

	.detail-value-bold {
		font-size: 16px;
		color: #2F5D62;
		font-weight: 700;
	}

	.history-status-btn {
		background: #2F5D62;
		border-radius: 10px;
		padding: 8px;
		text-align: center;
	}

	.status-btn-text {
		font-size: 16px;
		font-weight: 600;
		color: #fff;
		font-style: italic;
	}

	/* 空状态样式 */
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

	/* 详情弹窗样式 */
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
		overflow-y: auto;
		padding: 0;
	}

	.detail-modal-header {
		background: #2F5D62;
		padding: 10px;
		display: flex;
		justify-content: space-between;
		align-items: center;
		border-radius: 16px 16px 0 0;
	}

	.detail-modal-title {
		font-size: 16px;
		font-weight: 600;
		color: #fff;
	}

	.detail-modal-close {
		font-size: 20px;
		color: #fff;
		font-weight: 300;
		line-height: 1;
	}

	.detail-coupon-card {
		margin: 20px;
		border-radius: 16px;
		overflow: hidden;
		box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
	}

	.detail-image-wrapper {
		width: 100%;
		height: 140px;
		overflow: hidden;
	}

	.detail-image {
		width: 100%;
		height: 100%;
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
	}

	.detail-title-bar {
		background: #2F5D62;
		padding: 10px;
		text-align: center;
	}

	.detail-title {
		font-size: 16px;
		font-weight: 600;
		color: #fff;
	}

	.detail-description-section {
		padding: 20px;
	}

	.detail-section-title {
		font-size: 16px;
		font-weight: 700;
		color: #2F5D62;
		display: block;
		margin-bottom: 8px;
	}

	.detail-description-text {
		font-size: 13px;
		color: #5a7a8f;
		line-height: 1.6;
	}

	.detail-bonus-box {
		margin: 0 20px 20px 20px;
		background: #e8f4f8;
		border-radius: 12px;
		padding: 16px;
	}

	.detail-bonus-title {
		font-size: 16px;
		font-weight: 700;
		color: #1e3a5f;
		display: block;
		margin-bottom: 8px;
	}

	.detail-bonus-desc {
		font-size: 12px;
		color: #5a7a8f;
		line-height: 1.5;
	}

	.detail-claim-btn {
		margin: 0 20px 20px 20px;
		background: #2F5D62;
		border-radius: 10px;
		padding: 8px;
		text-align: center;
		cursor: pointer;
	}

	.detail-claim-btn.claimed {
		background: #9eacb5;
		opacity: 0.6;
	}

	.detail-claim-text {
		font-size: 16px;
		font-weight: 700;
		color: #fff;
	}

	/* 兑换码弹窗样式 (保留原有样式) */
	.input-rec {
		border: solid 1px #D6D6D6;
		border-radius: 8px;
		height: 40px;
		padding: 8.5px 14px;
		margin: 10px 0;
		color: $color-primary;
	}

	.focus-border {
		border: solid 2px $color-primary;
		padding: 7.5px 13px;
	}
</style>