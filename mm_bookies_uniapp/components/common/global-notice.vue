<template>
	<view v-if="visible" class="notice-overlay" :class="{'notice-overlay-closing': closing}"
		@click="handleOverlayClick">
		<view class="notice-container" :class="[containerClass, {'notice-container-closing': closing}]" @click.stop="">
			<!-- 头部 - 仅在Notice和Alert类型显示 -->
			<view v-if="hasHeader" class="notice-header" :class="headerClass">
				<text class="notice-header-text">{{headerText}}</text>
			</view>

			<!-- 内容区域 -->
			<view class="notice-body" :class="hasHeader ? 'notice-body-with-header' : 'notice-body-simple'">
				<!-- 图片显示 -->
				<theme-icon v-if="themeIcon" :name="themeIcon" class="notice-image"
					color="var(--theme-icon-primary, var(--theme-primary))"></theme-icon>
				<image v-else-if="image" :src="image" class="notice-image" mode="aspectFit"></image>
				<text class="notice-content" :class="{'notice-content-error': type === 'error'}">{{content}}</text>
			</view>

			<!-- 按钮区域 - 无头部样式（圆角按钮） -->
			<view v-if="!hasHeader" class="notice-footer-simple">
				<view v-if="showCancel" class="notice-btn-simple notice-btn-cancel-simple" @click="handleCancel">
					<text class="notice-btn-simple-text">{{cancelText}}</text>
				</view>
				<view class="notice-btn-simple notice-btn-confirm-simple" @click="handleConfirm">
					<text class="notice-btn-simple-text-white">{{confirmText}}</text>
				</view>
			</view>

			<!-- 按钮区域 - 有头部样式（占满底部，带分割线） -->
			<view v-else class="notice-footer-normal">
				<view v-if="showCancel" class="notice-btn-normal" @click="handleCancel">
					<text class="notice-btn-normal-text">{{cancelText}}</text>
				</view>
				<view class="notice-btn-normal notice-btn-confirm-border" @click="handleConfirm">
					<text class="notice-btn-normal-text notice-btn-confirm-color">{{confirmText}}</text>
				</view>
			</view>
		</view>
	</view>
</template>

<script>
	export default {
		name: 'GlobalNotice',
		data() {
			return {
				visible: false,
				closing: false, // 关闭动画状态
				type: 'success', // success, error, notice, alert
				title: '',
				content: '',
				showCancel: false,
				confirmText: this.$t('OK'),
				cancelText: this.$t('Cancel'),
				onConfirm: null,
				onCancel: null,
				onComplete: null,
				onFail: null,
				duration: 0, // 自动消失时间（毫秒），0则不消失
				image: '', // 图片路径
				themeIcon: '', // 内联主题图标名称
				autoCloseTimer: null, // 自动关闭定时器
				noticeQueue: [], // 通知队列
				isShowing: false // 是否正在显示通知（包括关闭动画期间）
			}
		},
		mounted() {
			this.$notice.setInstance(this)
		},
		beforeDestroy() {
			this.$notice.clearInstance(this)
		},
		// onLoad() {
		// 	// 测试所有通知样式 - 调试用，调试完成后可以删除
		// 	setTimeout(() => {
		// 		// 测试1: 成功样式
		// 		this.$notice.success('Your bet has been successfully placed', {
		// 			confirmText: 'OK',
		// 			cancelText: 'Cancel',
		// 			showCancel: true,
		// 		})
		// 	}, 1000)

		// 	setTimeout(() => {
		// 		// 测试2: 错误样式
		// 		this.$notice.error('Betting failed', {
		// 			confirmText: 'OK'
		// 		})
		// 	}, 3000)

		// 	setTimeout(() => {
		// 		// 测试3: 普通通知样式 (蓝色头部)
		// 		this.$notice.notice('Your bet has been successfully placed', {
		// 			title: 'Notice',
		// 			confirmText: 'OK'
		// 		})
		// 	}, 5000)

		// 	setTimeout(() => {
		// 		// 测试4: 警告样式 (红色头部)
		// 		this.$notice.alert('Your bet has been successfully placed', {
		// 			title: 'Alert',
		// 			confirmText: 'OK'
		// 		})
		// 	}, 7000)

		// 	setTimeout(() => {
		// 		// 测试5: 确认对话框 (带取消按钮)
		// 		this.$notice.confirm('Are you sure to delete this item?', {
		// 			title: 'Confirm',
		// 			confirmText: 'OK',
		// 			cancelText: 'Cancel',
		// 			success: (res) => {
		// 				console.log('User confirmed:', res)
		// 			},
		// 			cancel: (res) => {
		// 				console.log('User cancelled:', res)
		// 			}
		// 		})
		// 	}, 9000)

		// 	// 测试6: 实际的赔率变化提示
		// 	setTimeout(() => {
		// 		this.$notice.notice(this.$t('odds_change'), {
		// 			title: 'Tips',
		// 			confirmText: 'အတည်ပြုမည်'
		// 		})
		// 	}, 11000)
		// },
		computed: {
			containerClass() {
				return this.hasHeader ? 'notice-container-normal' : 'notice-container-simple'
			},
			hasHeader() {
				return this.type === 'notice' || this.type === 'alert'
			},
			headerClass() {
				return {
					'notice-header-notice': this.type === 'notice',
					'notice-header-alert': this.type === 'alert'
				}
			},
			headerText() {
				if (this.title) return this.title
				return this.type === 'notice' ? this.$t('Notice') : this.$t('Alert')
			}
		},

		methods: {
			show(options = {}) {
				// 如果当前正在显示通知（包括关闭动画期间），将新通知加入队列
				if (this.isShowing) {
					this.noticeQueue.push(options)
					return
				}

				// 显示通知
				this.showNotice(options)
			},

			showNotice(options) {
				this.isShowing = true
				this.type = options.type || 'success'
				this.title = options.title || ''
				this.content = options.content || ''
				this.showCancel = options.showCancel !== undefined ? options.showCancel : true
				this.confirmText = options.confirmText || this.$t('OK')
				this.cancelText = options.cancelText || this.$t('Cancel')
				this.onConfirm = options.success || null
				this.onCancel = options.cancel || null
				this.onComplete = options.complete || null
				this.onFail = options.fail || null
				this.duration = options.duration || 0
				this.image = options.image || ''
				this.themeIcon = options.themeIcon || ''
				this.closing = false
				this.visible = true

				// 如果设置了 duration，自动关闭
				if (this.duration > 0) {
					this.clearAutoCloseTimer()
					this.autoCloseTimer = setTimeout(() => {
						this.hide()
					}, this.duration)
				}
			},
			hide() {
				this.clearAutoCloseTimer()
				// 先触发关闭动画
				this.closing = true
				// 等待动画完成后再隐藏
				setTimeout(() => {
					this.visible = false
					this.closing = false
					// 重置数据
					setTimeout(() => {
						this.type = 'success'
						this.title = ''
						this.content = ''
						this.showCancel = false
						this.confirmText = this.$t('OK')
						this.cancelText = this.$t('Cancel')
						this.onConfirm = null
						this.onCancel = null
						this.onComplete = null
						this.onFail = null
						this.duration = 0
						this.image = ''
						this.themeIcon = ''
						this.isShowing = false

						// 检查队列中是否有等待显示的通知
						if (this.noticeQueue.length > 0) {
							const nextNotice = this.noticeQueue.shift()
							// 稍微延迟一下再显示下一个通知，避免过快
							setTimeout(() => {
								this.showNotice(nextNotice)
							}, 100)
						}
					}, 50)
				}, 300)
			},
			handleConfirm() {
				const result = {
					confirm: true,
					cancel: false
				}
				if (this.onConfirm && typeof this.onConfirm === 'function') {
					this.onConfirm(result)
				}
				if (this.onComplete && typeof this.onComplete === 'function') {
					this.onComplete(result)
				}
				this.hide()
			},
			handleCancel() {
				const result = {
					confirm: false,
					cancel: true
				}
				if (this.onCancel && typeof this.onCancel === 'function') {
					this.onCancel(result)
				}
				if (this.onComplete && typeof this.onComplete === 'function') {
					this.onComplete(result)
				}
				this.hide()
			},
			handleOverlayClick() {
				// 点击遮罩层不关闭
			},
			clearAutoCloseTimer() {
				if (this.autoCloseTimer) {
					clearTimeout(this.autoCloseTimer)
					this.autoCloseTimer = null
				}
			}
		}
	}
</script>

<style lang="scss" scoped>
	.notice-overlay {
		position: fixed;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		background-color: rgba(0, 0, 0, 0.5);
		display: flex;
		align-items: center;
		justify-content: center;
		z-index: 999999;
		padding: 0 40upx;
		animation: overlay-fade-in 0.3s ease-out;
	}

	.notice-overlay-closing {
		animation: overlay-fade-out 0.3s ease-out;
	}

	.notice-container {
		background-color: #FFFFFF;
		width: 100%;
		max-width: 560upx;
		overflow: hidden;
		box-shadow: 0 8upx 32upx rgba(0, 0, 0, 0.2);
		animation: notice-slide-in 0.3s ease-out;
	}

	.notice-container-closing {
		animation: notice-slide-out 0.3s ease-out;
	}

	/* 简单样式容器(success/error) - 圆角更大 */
	.notice-container-simple {
		border-radius: 24upx;
	}

	/* 带头部的容器(notice/alert) - 圆角稍小 */
	.notice-container-normal {
		border-radius: 16upx;
	}

	/* ============ 头部样式 ============ */
	.notice-header {
		padding: 12upx 40upx;
		text-align: center;
		color: #FFFFFF;
		font-weight: bold;
		font-size: 32upx;
	}

	.notice-header-notice {
		background: linear-gradient(135deg, $color-primary 0%, $color-primary 100%);
	}

	.notice-header-alert {
		background: linear-gradient(135deg, #D8372B 0%, #D8372B 100%);
	}

	.notice-header-text {
		color: #FFFFFF;
	}

	/* ============ 内容区域 ============ */
	.notice-body {
		text-align: center;
		min-height: 100upx;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
	}

	.notice-body-simple {
		padding: 20upx 40upx 40upx 40upx;
	}

	.notice-body-with-header {
		padding: 20upx 40upx;
	}

	.notice-image {
		width: 80upx;
		height: 80upx;
		margin: 20upx 0;
	}

	.notice-content {
		font-size: 28upx;
		line-height: 1.6;
		color: $color-primary;
		word-wrap: break-word;
		white-space: pre-wrap;
	}

	.notice-content-error {
		color: #D8372B;
	}

	/* ============ 按钮区域 - 无头部样式 ============ */
	.notice-footer-simple {
		padding: 0 40upx 20upx 40upx;
		display: flex;
		gap: 20upx;
		justify-content: center;
	}

	.notice-btn-simple {
		flex: 1;
		height: 60upx;
		border-radius: 16upx;
		display: flex;
		align-items: center;
		justify-content: center;
		cursor: pointer;
		transition: all 0.2s;
		font-weight: 500;
		max-width: 300upx;
	}

	.notice-btn-simple:active {
		opacity: 0.8;
		transform: scale(0.98);
	}

	.notice-btn-cancel-simple {
		background-color: transparent;
		border: 2px solid $color-primary;
		max-width: 300upx;
	}

	.notice-btn-confirm-simple {
		background: linear-gradient(135deg, $color-primary 0%, $color-primary 100%);
	}

	.notice-btn-simple-text {
		font-size: 28upx;
		color: #FF5341;
	}

	.notice-btn-simple-text-white {
		font-size: 28upx;
		color: #FFFFFF;
	}

	/* ============ 按钮区域 - 有头部样式（带边距的并排按钮） ============ */
	.notice-footer-normal {
		display: flex;
		gap: 20upx;
		padding: 0 40upx 24upx 40upx;
	}

	.notice-btn-normal {
		flex: 1;
		height: 60upx;
		border-radius: 16upx;
		display: flex;
		align-items: center;
		justify-content: center;
		cursor: pointer;
		transition: all 0.2s;
		background-color: transparent;
		border: 2px solid $color-primary;
	}

	.notice-btn-normal:active {
		opacity: 0.8;
		transform: scale(0.98);
	}

	.notice-btn-confirm-border {
		background: linear-gradient(135deg, $color-primary 0%, $color-primary 100%);
		border: none;
	}

	.notice-btn-normal-text {
		font-size: 28upx;
		color: #FF5341;
		font-weight: 500;
	}

	.notice-btn-confirm-color {
		color: #FFFFFF;
		font-weight: 500;
	}

	/* ============ 动画 ============ */
	/* 遮罩层淡入 */
	@keyframes overlay-fade-in {
		from {
			opacity: 0;
		}

		to {
			opacity: 1;
		}
	}

	/* 遮罩层淡出 */
	@keyframes overlay-fade-out {
		from {
			opacity: 1;
		}

		to {
			opacity: 0;
		}
	}

	/* 弹窗滑入 */
	@keyframes notice-slide-in {
		from {
			opacity: 0;
			transform: translateY(-50upx) scale(0.9);
		}

		to {
			opacity: 1;
			transform: translateY(0) scale(1);
		}
	}

	/* 弹窗滑出 */
	@keyframes notice-slide-out {
		from {
			opacity: 1;
			transform: translateY(0) scale(1);
		}

		to {
			opacity: 0;
			transform: translateY(-30upx) scale(0.95);
		}
	}
</style>