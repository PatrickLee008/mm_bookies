<template>
	<view class="bg-white full-page">
		<zw-header></zw-header>

		<!-- from tangjq--- header占位元素，防止内容被遮挡 -->
		<view class="header-placeholder"></view>

		<!-- from tangjq--- 标题栏：包含钱包信息和 Tab 页签 -->
		<view class="title-bar">
			<!-- from tangjq--- Tab 页签 -->
			<view class="tab-selector">
				<view class="tab-container">
					<view class="tab-item" :class="{'active': tab_index === 0}" @click="handleTabClick(0)">
						<text class="tab-text">{{ $t('text_button_submit') }}</text>
					</view>
					<view class="tab-item" :class="{'active': tab_index === 1}" @click="handleTabClick(1)">
						<text class="tab-text">{{ $t('whithdraw btn') }}</text>
					</view>
					<view class="tab-item" :class="{'active': tab_index === 2}" @click="handleTabClick(2)">
						<text class="tab-text">{{ $t('deposit_history') }}</text>
					</view>

					<view class="tab-item" :class="{'active': tab_index === 3}" @click="handleTabClick(3)">
						<text class="tab-text">{{ $t('withdraw_history') }}</text>
					</view>

					<!-- from tangjq--- 底部滑动指示器 -->
					<view class="slide-indicator" :style="{
						width: indicator_width + 'px',
						transform: `translateX(${indicator_offset}px)`
					}"></view>
				</view>
			</view>
		</view>

		<!-- from tangjq--- Tab 内容区域 -->
		<view class="tab-content">
			<!-- Deposit 子组件 -->
			<wallet-deposit v-if="tab_index === 0"></wallet-deposit>

			<!-- Withdraw 子组件 -->
			<wallet-withdraw v-if="tab_index === 1"></wallet-withdraw>

			<!-- from tangjq--- History 子组件 -->
			<wallet-history v-if="tab_index === 2" ref="depositHistory"></wallet-history>


			<!-- Withdraw History 子组件 -->
			<wallet-withdraw-history v-if="tab_index === 3" ref="withdrawHistory"></wallet-withdraw-history>
		</view>

		<!-- from tangjq--- 悬浮的 Refresh 按钮，仅在充值/提现记录页签显示，点击刷新列表数据 -->
		<view class="refresh-btn-float" v-if="tab_index === 2 || tab_index === 3" @click="refreshList">
			<image class="refresh-icon" mode="widthFix" src="/static/icon/wallet/reflesh.svg" />
			<text class="refresh-text">{{ $t('refresh') }}</text>
		</view>
	</view>
</template>

<script>
	// from tangjq--- 引入必要的工具和组件
	import config from '../../utils/config.js'
	import dateFormatUtils from "../../utils/utils.js"
	import WalletDeposit from './deposit.vue'
	import WalletWithdraw from './withdraw.vue'
	import WalletHistory from './history.vue'
	import WalletWithdrawHistory from './withdraw_history.vue'

	export default {
		components: {
			// from tangjq--- 注册子组件
			WalletDeposit,
			WalletWithdraw,
			WalletHistory,
			WalletWithdrawHistory,
		},
		data() {
			return {
				isLogin: uni.getStorageSync('Authorization') || false,
				language: config.language,
				userInfo: null,

				// from tangjq--- Tab 相关变量
				tab_index: 0,
				indicator_width: 0,
				indicator_offset: 0,
			}
		},

		methods: {
			// from tangjq--- 刷新当前记录列表数据（仅在充值/提现记录页签有效），不再重新加载页面
			refreshList() {
				const historyRef = this.tab_index === 2 ? this.$refs.depositHistory : this.$refs.withdrawHistory
				if (historyRef && typeof historyRef.refreshData === 'function') {
					historyRef.refreshData()
				}
			},
			goto(url) {
				uni.navigateTo({
					url: url,
				})
			},
			numberFormat(num) {
				return dateFormatUtils.numFormat(num)
			},

			// from tangjq--- 处理 Tab 点击事件
			handleTabClick(index) {
				if (this.tab_index === index) return

				// from tangjq--- 切换 tab，不再跳转
				this.tab_index = index
				this.updateIndicator()
			},

			// from tangjq--- 初始化指示器
			initIndicator() {
				const query = uni.createSelectorQuery().in(this)
				query.selectAll('.tab-item').boundingClientRect().exec((res) => {
					if (res[0] && res[0].length > 0) {
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
						const currentTab = res[0][this.tab_index]
						const container = res[0][0]
						this.indicator_offset = currentTab.left - container.left
						this.indicator_width = currentTab.width
					}
				})
			},
		},

		onLoad() {
			// from tangjq--- 初始化用户信息
			this.userInfo = Object.assign({}, this.$store.state.userInfo)
		},

		mounted() {
			// from tangjq--- 组件挂载后初始化指示器
			this.$nextTick(() => {
				this.initIndicator()
			})
		},

		created() {}
	}
</script>

<style lang="scss">
	/* from tangjq--- header占位元素样式 */
	.header-placeholder {
		height: 210px;
		width: 100%;
	}

	.full-page {
		min-height: 100vh;
		display: flex;
		flex-direction: column;
		background-color: #2F5D62;
	}

	/* from tangjq--- 标题栏样式 */
	.title-bar {
		background: #fff;
		border-radius: 20px 20px 0 0;
		flex-shrink: 0;
	}

	/* from tangjq--- Tab 样式 (参照 coupon.vue) */
	.tab-selector {
		width: 100%;
		background: #fff;
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
		justify-content: center;
		cursor: pointer;
		height: 30px;
		// min-width: 80px;
	}

	/* from tangjq--- 第一个 tab 居左对齐 */
	.tab-item:first-child {
		justify-content: flex-start;
		padding-left: 0;
	}

	/* from tangjq--- 最后一个 tab 居右对齐 */
	.tab-item:last-child {
		justify-content: flex-end;
		padding-right: 0;
	}

	.tab-text {
		font-size: 13px;
		color: #5a7a8f;
		transition: color 0.25s ease;
		font-weight: 400;
	}

	.tab-item.active .tab-text {
		color: #4fb3bf;
	}

	.slide-indicator {
		position: absolute;
		bottom: 0;
		height: 2px;
		background: #4fb3bf;
		border-radius: 2px;
		transition: all 0.3s cubic-bezier(0.4, 0.0, 0.2, 1);
	}

	/* from tangjq--- Tab 内容区域 */
	.tab-content {
		flex: 1;
		height: 0;
		overflow: hidden;
		background: #fff;
		display: flex;
		flex-direction: column;
		padding: 0 10px;
	}

	/* from tangjq--- 悬浮 Refresh 按钮样式 */
	.refresh-btn-float {
		position: fixed;
		right: 20px;
		bottom: 80px;
		width: 60px;
		height: 60px;
		border-radius: 30px;
		background: linear-gradient(135deg, #4fb3bf 0%, #2F5D62 100%);
		box-shadow: 0 4px 12px rgba(47, 93, 98, 0.4);
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		z-index: 999;
	}

	.refresh-icon {
		width: 24px;
		height: 24px;
		margin-bottom: 2px;
	}

	.refresh-text {
		font-size: 10px;
		color: #fff;
		font-weight: 500;
	}
</style>
