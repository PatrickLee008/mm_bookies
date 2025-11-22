<template name="ucenter">
	<view class="bg-white full-page">
		<zw-header></zw-header>

		<scroll-view scroll-y :style="{ height: isLogin ? 'calc(100vh - 110px)' : 'calc(100vh - 170px)' }">
			<view class="title-bar" style="padding-bottom: 0;">
				<view class="flex-row justify-between" style="">
					<view class="flex-row align-center" style="">
						<image class="yellow2dblue" style="height: 25px;" mode="heightFix"
							src="/static/icon/coupon.png"></image>
						<text class="title-text" style="">{{language.coupon}}</text>
					</view>
					<view class="mybg-lprimary code-btn" style="" v-if="isLogin" @tap="hidden = false">
						{{'CODE'}}
					</view>
				</view>
				<view class="flex-column mycolor-primary" v-if="isLogin"
					style="background-color: rgb(237, 236, 241);border-radius: 8px;margin-top: 15px;">
					<view class="flex-row" style="padding: 5px 10px;">
						<text class="text-bold">{{'Coupon Name'}}</text>
					</view>
					<view class="flex-column1 align-center width-100" style="margin: 5px 0;position: relative;">
						<view class="flex-row justify-center">
							<text class="credit-text" style="">{{'Credit'}}</text>
						</view>
						<text class="text-bold myfont-22px" style="line-height: 25px;">{{'0.00'}}</text>
					</view>
					<view class="flex-row margin-top-sm">
						<view class="status-rec mybg-active" style="">
							<view class="flex-row height-50">{{'Deposit'}}</view>
							<view class="flex-row height-50 justify-end">{{'-'}}</view>
						</view>
						<view class="status-rec mybg-primary" style="">
							<view class="flex-row height-50">{{'Status'}}</view>
							<view class="flex-row height-50 justify-end">{{'Expired'}}</view>
						</view>
						<view class="status-rec mybg-info" style="">
							<view class="flex-row height-50">{{'Remain'}}</view>
							<view class="flex-row height-50 justify-end">{{''}}</view>
						</view>
					</view>
				</view>

				<view class="tab-selector" v-if="isLogin">
					<view class="tab-container" ref="container">
						<view v-for="(item, index) in tabList" :key="index" class="tab-item"
							:class="{ 'active': tab_index === index }" @click="handleTabClick(index)">
							<text class="tab-text">{{ item }}</text>
						</view>

						<!-- 底部滑动指示器 -->
						<view class="slide-indicator" :style="{ 
				          width: indicator_width + 'px',
				          transform: `translateX(${indicator_offset}px)` 
				        }"></view>
					</view>
				</view>
				<view class="padding-xs" v-else></view>
			</view>
			<view v-if="isLogin">
				<!-- 筛选框 -->
				<date-range-picker ref="date_picker" @click_option="date_click"></date-range-picker>
				<view class="padding-sm" v-show="tab_index">
					<view class="flex-row flex-wrap justify-start filter padding-lr-sm" style="">
						<image mode="widthFix" class="width-38upx " src="/static/image/order/calender.svg"
							@click="$refs.date_picker.show()" v-show="tab_index>=1" />
						<view class="filter-row" v-show="tab_index==1">
							<view class="text mycolor-primary">Type</view>
							<selector :option_list.sync="type_list" @click_option="click_option"></selector>
						</view>
						<view class="filter-row" v-show="tab_index==1">
							<view class="text mycolor-primary">Status</view>
							<selector :option_list.sync="status_list" @click_option="click_option"></selector>
						</view>
						<view class="filter-row" v-show="tab_index>=1">
							<view class="text mycolor-primary line-height-34px">Period:
								{{date_range[0].show}}{{' - '}}{{date_range[1].show}}
							</view>
						</view>
					</view>
				</view>

				<!-- 优惠券列表 -->
				<view class="padding-sm" v-if="couponList.length > 0">
					<view class="coupon-item" v-for="(coupon, index) in couponList" :key="index">
						<view class="coupon-header">
							<view class="coupon-name">{{ coupon.coupon_name }}</view>
							<view class="coupon-status" :class="getStatusClass(coupon.status)">
								{{ coupon.status }}
							</view>
						</view>
						<view class="coupon-body">
							<view class="coupon-info-grid">
								<!-- 奖金金额 -->
								<view class="info-item">
									<text class="info-label">Bonus:</text>
									<text class="info-value primary">{{ coupon.bonus_amount }}</text>
								</view>
								<!-- 最低投注金额 -->
								<view class="info-item justify-end" v-if="coupon.min_bet_required">
									<text class="info-label">Min Bet:</text>
									<text class="info-value">{{ coupon.min_bet_required }}</text>
								</view>
								<!-- 已使用/限制次数 -->
								<view class="info-item" v-if="coupon.used_count !== undefined || coupon.usage_limit">
									<text class="info-label">Used:</text>
									<text
										class="info-value">{{`${coupon.used_count || 0}${coupon.usage_limit?'/'+coupon.usage_limit:''}`}}
									</text>
								</view>
								<!-- USED状态显示比赛状态 -->
								<view class="info-item justify-end"
									v-if="coupon.status === 'Used' && coupon.game_status">
									<text class="info-label">Bet Status:</text>
									<view class="game-status-badge-small"
										:class="getGameStatusClass(coupon.game_status)">
										<text class="status-text-small">{{ coupon.game_status }}</text>
									</view>
								</view>
							</view>
							<!-- <view class="coupon-turnover" v-if="coupon.turnover_requirement > 0">
								<text class="turnover-label">Turnover:</text>
								<text class="turnover-value">{{ coupon.turnover_progress }} /
									{{ coupon.turnover_requirement }}</text>
								<view class="progress-bar">
									<view class="progress-fill" :style="{ width: getProgressWidth(coupon) }"></view>
								</view>
							</view> -->
						</view>
						<view class="coupon-footer">
							<text class="coupon-time-text" v-if="coupon.status === 'Used' && coupon.use_time">
								Used: {{formatTime(coupon.use_time)}}
							</text>
							<text class="coupon-time-text" v-else-if="coupon.expire_time">
								Expires: {{formatTime(coupon.expire_time)}}
							</text>
						</view>
					</view>
				</view>

				<!-- 空状态 -->
				<view class="flex-column justify-center margin-top" style="" v-else>
					<view class="flex-column align-center justify-center text-bold" style="">
						<image class="yellow2dblue" style="height: 28px;margin-bottom: 6px;" mode="heightFix"
							src="/static/icon/coupon.png">
						</image>
						<view class="mycolor-primary">Coupon list is empty</view>
					</view>
				</view>
			</view>

			<view class="flex-column justify-center margin-top" style="" v-else>
				<view class="flex-column align-center justify-center" style="">
					<image class="yellow2dblue" style="height: 60px;margin-bottom: 6px;" mode="heightFix"
						src="/static/icon/coupon.png">
					</image>
					<view class="myfont-20px mycolor-primary">{{language.please_sign_in_to_receive_the_coupon}}</view>
				</view>
			</view>
		</scroll-view>


		<view class="cu-modal" style="z-index: 1;" :class="{'show':!hidden,}" @click="set_dialog_hide(true)">
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
					<input class="width-100 text-left input-rec" :class="input_focus?'focus-border':''"
						placeholder="Enter coupon code" placeholder-class="text-gray" v-model="key_word"
						@focus="input_focus=true" @blur="input_focus=false" />
					<view class="width-100 height-35px radius-8px margin-bottom-sm"
						:class="key_word?'mybg-lprimary':'mybg-info'" @click="submit_code">
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
				tabs: ['UNUSED', 'USED', 'EXPIRED'],

				couponList: [],

				key_word: '',
				input_focus: false,
				hidden: true,
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
			// 初始化指示器
			initIndicator() {
				const query = uni.createSelectorQuery().in(this)
				query.select('.tab-container').boundingClientRect().exec((res) => {
					if (res[0]) {
						this.container_width = res[0].width
						this.indicator_width = this.container_width / this.tabList.length
						this.updateIndicator()
					}
				})
			},
			// 更新指示器位置
			updateIndicator() {
				this.indicator_offset = this.tab_index * this.indicator_width
			},

			// 获取优惠券列表
			getCouponList() {
				let _this = this

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
			}
		},
		created() {}
	}
</script>

<style lang="scss">
	.status-rec {
		width: 25%;
		height: 35px;
		border-radius: 0px 8px 0px 0px;
		padding: 2px 10px;
		font-size: 10px;
		font-weight: bold;
	}

	.code-btn {
		min-width: 64px;
		height: 30px;
		border-radius: 7px;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
	}

	.credit-text {
		font-size: 11px;
		line-height: 12px;
		margin-left: 100px;
		font-weight: 600;
	}



	.tab-selector {
		width: 100%;
		background: #fff;
	}

	.tab-container {
		position: relative;
		display: flex;
		align-items: center;
		border-bottom: 2rpx solid #f0f0f0;
	}

	.tab-item {
		flex: 1;
		display: flex;
		justify-content: center;
		align-items: center;
		// padding: 32rpx 20rpx;
		cursor: pointer;
		height: 48px;
	}

	.tab-text {
		font-size: 28rpx;
		color: #999;
		transition: color 0.25s ease;
		font-weight: 400;
	}

	.tab-item.active .tab-text {
		color: #333;
		font-weight: 600;
	}

	.slide-indicator {
		position: absolute;
		bottom: 0;
		left: 0;
		height: 6rpx;
		background: $color-primary;
		border-radius: 3rpx;
		transition: all 0.3s cubic-bezier(0.4, 0.0, 0.2, 1);
	}

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

	/* 优惠券卡片样式 - 优化紧凑 */
	.coupon-item {
		background: #fff;
		border-radius: 8px;
		margin-bottom: 12px;
		padding: 12px;
		box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
		border-left: 3px solid $color-primary;
	}

	.coupon-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 8px;
	}

	.coupon-name {
		font-size: 15px;
		font-weight: bold;
		color: $color-primary;
		flex: 1;
		line-height: 1.3;
	}

	.coupon-status {
		padding: 3px 8px;
		border-radius: 10px;
		font-size: 11px;
		font-weight: bold;
		white-space: nowrap;
	}

	.status-unused {
		background: #e8f5e8;
		color: #52c41a;
	}

	.status-used {
		background: #f0f0f0;
		color: #999;
	}

	.status-expired {
		background: #fff2e8;
		color: #fa8c16;
	}

	.coupon-body {
		margin-bottom: 8px;
	}

	/* 信息网格布局 - 2列紧凑显示 */
	.coupon-info-grid {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 8px 12px;
	}

	.info-item {
		display: flex;
		align-items: center;
		gap: 6px;
	}

	.info-label {
		font-size: 12px;
		color: #666;
		white-space: nowrap;
	}

	.info-value {
		font-size: 13px;
		font-weight: 600;
		color: #333;
	}

	.info-value.primary {
		font-size: 15px;
		color: $color-primary;
	}

	/* 小号游戏状态标签 */
	.game-status-badge-small {
		padding: 2px 6px;
		border-radius: 8px;
		font-size: 10px;
		font-weight: bold;
	}

	.status-text-small {
		color: white;
		font-size: 10px;
	}

	.coupon-turnover {
		margin-top: 8px;
	}

	.turnover-label {
		font-size: 12px;
		color: #666;
		margin-right: 8px;
	}

	.turnover-value {
		font-size: 12px;
		color: #333;
	}

	.progress-bar {
		width: 100%;
		height: 4px;
		background: #f0f0f0;
		border-radius: 2px;
		margin-top: 5px;
		overflow: hidden;
	}

	.progress-fill {
		height: 100%;
		background: $color-primary;
		border-radius: 2px;
		transition: width 0.3s ease;
	}

	.coupon-footer {
		border-top: 1px solid #f0f0f0;
		padding-top: 6px;
		margin-top: 6px;
	}

	.coupon-time-text {
		font-size: 11px;
		color: #999;
		line-height: 1.3;
	}

	/* 游戏状态颜色 */

	.game-status-pending {
		background: #fa8c16;
	}

	.game-status-running {
		background: #1890ff;
	}

	.game-status-finished {
		background: #52c41a;
	}

	.game-status-cancelled {
		background: #f5222d;
	}

	.game-status-win {
		background: #52c41a;
	}

	.game-status-lose {
		background: #f5222d;
	}

	.game-status-draw {
		background: #722ed1;
	}

	.game-status-default {
		background: #d9d9d9;
		color: #666;
	}

	.game-status-default .status-text {
		color: #666;
	}
</style>