<template>
	<view class="about-page full-page">
		<!-- 顶部栏 -->
		<view class="about-header">
			<text class="header-back-icon" @click="goBack">←</text>
			<text class="header-title">{{ $t('about') }}</text>
			<text class="header-close-icon" @click="goBack">✕</text>
		</view>

		<scroll-view scroll-y style="height: calc(100vh - 88px);">
			<view class="about-content">
				<!-- Rules 部分 -->
				<view class="about-section">
					<text class="section-title">{{ $t('rules') }}</text>
					<view class="rule-item" v-for="(rule, index) in rules" :key="'rule-' + index">
						<text class="rule-number">{{ index + 1 }}.</text>
						<text class="rule-text">{{ rule }}</text>
					</view>
				</view>

				<!-- Regulation 部分 -->
				<view class="about-section">
					<text class="section-title">{{ $t('regulation') }}</text>
					<view class="rule-item" v-for="(regulation, index) in regulations" :key="'regulation-' + index">
						<text class="rule-number">{{ index + 1 }}.</text>
						<text class="rule-text">{{ regulation }}</text>
					</view>
				</view>
			</view>
		</scroll-view>
	</view>
</template>

<script>
	export default {
		name: "About",
		data() {
			return {
				rules: [
					'Rules and regulation of mm bookies detail explained here',
					'Terms of service for online betting platforms outlined here',
					'Common betting strategies used by successful gamblers',
					'Legal age and identification requirements for placing bets',
					'How to recognize and report suspicious betting activities'
				],
				regulations: [
					'Rules and regulation of mm bookies detail explained here',
					'Terms of service for online betting platforms outlined here',
					'Common betting strategies used by successful gamblers',
					'Legal age and identification requirements for placing bets',
					'How to recognize and report suspicious betting activities'
				]
			}
		},
		onLoad() {
			this.loadAboutInfo()
		},
		methods: {
			goBack() {
				uni.navigateBack()
			},
			loadAboutInfo() {
				// from tangjq--- 从store或API加载About信息
				if (this.$store.state.configs && this.$store.state.configs.about) {
					// 可以根据实际数据格式解析
					// this.rules = ...
					// this.regulations = ...
				}
			}
		}
	}
</script>

<style lang="scss" scoped>
	.about-page {
		background: #f5f5f5;
		min-height: 100vh;
	}

	/* 顶部栏 */
	.about-header {
		background: #3d6877;
		padding: 40px 20px 20px 20px;
		display: flex;
		justify-content: space-between;
		align-items: center;
	}

	.header-back-icon, .header-close-icon {
		width: 40px;
		font-size: 24px;
		color: #fff;
		font-weight: 300;
	}

	.header-title {
		font-size: 20px;
		font-weight: 700;
		color: #fff;
		flex: 1;
		text-align: center;
	}

	/* 内容区域 */
	.about-content {
		padding: 30px 20px;
	}

	.about-section {
		margin-bottom: 30px;
	}

	.section-title {
		font-size: 20px;
		font-weight: 700;
		color: #1e3a5f;
		display: block;
		margin-bottom: 16px;
	}

	.rule-item {
		display: flex;
		margin-bottom: 16px;
		align-items: flex-start;
	}

	.rule-number {
		font-size: 15px;
		color: #3d6877;
		font-weight: 600;
		margin-right: 8px;
		flex-shrink: 0;
	}

	.rule-text {
		font-size: 15px;
		color: #5a7a8f;
		line-height: 1.6;
		flex: 1;
	}
</style>
