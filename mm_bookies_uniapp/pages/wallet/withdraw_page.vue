<template name="withdraw_page">
	<view class="full-page">
		<zw-header @headerHeightChange="onHeaderHeightChange"></zw-header>

		<!-- from tangjq--- header占位元素，防止内容被遮挡 -->
		<view class="header-placeholder" :style="{ height: headerHeight + 'px' }"></view>

		<!-- from tangjq--- 顶部 tab：Withdraw（提现表单）/ Withdraw History（提现记录） -->
		<view class="title-bar">
			<view class="tab-selector">
				<view class="tab-container">
					<view class="tab-item" :class="{'active': tab_index === 0}" @click="handleTabClick(0)">
						<text class="tab-text">{{ $t('withdraw') }}</text>
					</view>
					<view class="tab-item" :class="{'active': tab_index === 1}" @click="handleTabClick(1)">
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
			<!-- Withdraw 表单（现有 withdraw.vue 子组件） -->
			<wallet-withdraw v-if="tab_index === 0" @contentScroll="handleHeaderScroll"></wallet-withdraw>

			<!-- Withdraw History 列表（现有 withdraw_history.vue 子组件，已去掉 type 限制） -->
			<wallet-withdraw-history v-if="tab_index === 1" ref="withdrawHistory" @contentScroll="handleHeaderScroll"></wallet-withdraw-history>
		</view>

		<!-- from tangjq--- 悬浮的 Refresh 按钮，仅在 Withdraw History tab 显示 -->
		<view class="refresh-btn-float" v-if="tab_index === 1" @click="refreshList">
			<text class="cuIcon-refresh text-white text-bold myfont-20px"></text>
		</view>
	</view>
</template>

<script>
	import config from '../../utils/config.js'
	import dateFormatUtils from "../../utils/utils.js"
	import WalletWithdraw from './withdraw.vue'
	import WalletWithdrawHistory from './withdraw_history.vue'
	import headerCollapse from '@/mixins/headerCollapse.js'

	export default {
		components: {
			WalletWithdraw,
			WalletWithdrawHistory,
		},
		mixins: [headerCollapse],
		data() {
			return {
				isLogin: uni.getStorageSync('Authorization') || false,
				language: config.language,
				userInfo: null,

				tab_index: 0,
				indicator_width: 0,
				indicator_offset: 0,
			}
		},
		methods: {
			refreshList() {
				const historyRef = this.$refs.withdrawHistory
				if (historyRef && typeof historyRef.refreshData === 'function') {
					historyRef.refreshData()
				}
			},

			handleTabClick(index) {
				if (this.tab_index === index) return
				this.tab_index = index
				this.$nextTick(() => {
					this.updateIndicator()
				})
			},

			initIndicator() {
				const query = uni.createSelectorQuery().in(this)
				query.selectAll('.tab-item').boundingClientRect().exec((res) => {
					if (res[0] && res[0].length > 0) {
						this.indicator_width = res[0][0].width
						this.updateIndicator()
					}
				})
			},

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

		onLoad(options) {
			this.userInfo = Object.assign({}, this.$store.state.userInfo)
			if (options && options.tab != null) {
				const idx = parseInt(options.tab)
				if (!isNaN(idx) && idx >= 0 && idx <= 1) {
					this.tab_index = idx
				}
			}
		},

		mounted() {
			this.$nextTick(() => {
				this.initIndicator()
			})
		},

		created() {}
	}
</script>

<style lang="scss">
	.header-placeholder {
		height: 255px;
		width: 100%;
		flex-shrink: 0;
		transition: height 0.3s ease;
	}

	.full-page {
		min-height: 100vh;
		display: flex;
		flex-direction: column;
	}

	.title-bar {
		background: #fff;
		border-radius: 20px 20px 0 0;
		flex-shrink: 0;
		padding: 10px 20px;
	}

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
	}

	.tab-text {
		font-size: 13px;
		color: #5a7a8f;
		transition: color 0.25s ease;
		font-weight: 400;
	}

	.tab-item.active .tab-text {
		color: #4fb3bf;
		font-weight: 600;
	}

	.slide-indicator {
		position: absolute;
		bottom: 0;
		height: 2px;
		background: #4fb3bf;
		border-radius: 2px;
		transition: all 0.3s cubic-bezier(0.4, 0.0, 0.2, 1);
	}

	.tab-content {
		flex: 1;
		height: 0;
		overflow: hidden;
		background: #fff;
		display: flex;
		flex-direction: column;
		padding: 0 15px;
	}

	.refresh-btn-float {
		position: fixed;
		right: 20px;
		bottom: 80px;
		width: 50px;
		height: 50px;
		border-radius: 30px;
		background: $color-primary;
		box-shadow: 0 4px 12px rgba(47, 93, 98, 0.4);
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		z-index: 999;
	}
</style>
