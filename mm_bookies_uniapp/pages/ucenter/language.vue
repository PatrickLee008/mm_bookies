<template>
	<view class="language-page full-page">
		<!-- 顶部栏 -->
		<view class="language-header">
			<text class="header-back-icon" @click="goBack">←</text>
			<text class="header-title">{{ $t('change_language') }}</text>
			<text class="header-placeholder"></text>
		</view>

		<scroll-view scroll-y style="height: calc(100vh - 88px);">
			<view class="language-content">
				<!-- 语言选项列表 -->
				<view class="language-item" @click="pickerChange('mm')">
					<text class="language-label">မြန်မာ</text>
					<view class="radio-circle" :class="{ 'radio-selected': picker === 'mm' }">
						<view class="radio-dot" v-if="picker === 'mm'"></view>
					</view>
				</view>

				<view class="language-item" @click="pickerChange('en')">
					<text class="language-label">{{ $t('English') }}</text>
					<view class="radio-circle" :class="{ 'radio-selected': picker === 'en' }">
						<view class="radio-dot" v-if="picker === 'en'"></view>
					</view>
				</view>

				<view class="language-item" @click="pickerChange('th')">
					<text class="language-label">ภาษาไทย</text>
					<view class="radio-circle" :class="{ 'radio-selected': picker === 'th' }">
						<view class="radio-dot" v-if="picker === 'th'"></view>
					</view>
				</view>

				<view class="language-item" @click="pickerChange('cn')">
					<text class="language-label">中文</text>
					<view class="radio-circle" :class="{ 'radio-selected': picker === 'cn' }">
						<view class="radio-dot" v-if="picker === 'cn'"></view>
					</view>
				</view>

				<!-- Confirm 按钮 -->
				<view class="confirm-btn" @click="submit()">
					<text class="confirm-btn-text">{{language.confirm || 'Confirm'}}</text>
				</view>
			</view>
		</scroll-view>
	</view>
</template>

<script>
	import language from '../../utils/language.js'
	import config from '../../utils/config.js'
	export default {
		data() {
			return {
				picker: uni.getStorageSync('UNI_LOCALE') || 'mm',
				language: config.language
			}
		},
		methods: {
			// from tangjq--- 返回上一页
			goBack() {
				uni.navigateBack()
			},
			toHome() {
				uni.reLaunch({
					url: '/pages/ucenter/home'
				})
			},
			pickerChange(value) {
				// this.music.play_dede() ;
				this.picker = value;
			},
			submit() {
				// this.music.play_dede() ;
				if (!this.picker) this.picker = 'mm';
				config.language = language[this.picker];
				uni.setStorageSync('language', this.picker);

				uni.setLocale(this.picker)
				this.$i18n.locale = this.picker;

				this.toHome()
			}
		},
		onLoad() {},
	}
</script>

<style lang="scss" scoped>
	.language-page {
		background: linear-gradient(to right, #02455F 0%, #02455F 56%, #1F879B 100%);
		min-height: 100vh;
	}

	/* 顶部栏 */
	.language-header {
		background:
			radial-gradient(circle at 100% 0%, #36BCCB 0%, #1F879B 34%, rgba(31, 135, 155, 0) 68%),
			linear-gradient(135deg, #02455F 0%, #02455F 56%, #1F879B 100%);
		background-size: 100% 552px;
		background-position: center top;
		padding: 40px 20px 20px 20px;
		display: flex;
		justify-content: space-between;
		align-items: center;
	}

	.header-back-icon, .header-placeholder {
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
	.language-content {
		padding: 30px 20px;
	}

	.language-item {
		background: #fff;
		border-radius: 12px;
		padding: 16px 20px;
		margin-bottom: 12px;
		display: flex;
		justify-content: space-between;
		align-items: center;
		box-shadow: 0 2px 6px rgba(0, 0, 0, 0.06);
	}

	.language-label {
		font-size: 16px;
		font-weight: 600;
		color: #1e3a5f;
	}

	.radio-circle {
		width: 24px;
		height: 24px;
		border-radius: 50%;
		border: 2px solid #ccc;
		display: flex;
		align-items: center;
		justify-content: center;
		transition: all 0.2s;
	}

	.radio-circle.radio-selected {
		border-color: #4fb3bf;
	}

	.radio-dot {
		width: 14px;
		height: 14px;
		border-radius: 50%;
		background: #4fb3bf;
	}

	.confirm-btn {
		background: #3d6877;
		border-radius: 12px;
		padding: 14px;
		text-align: center;
		margin-top: 30px;
	}

	.confirm-btn-text {
		font-size: 16px;
		font-weight: 600;
		color: #fff;
	}
</style>