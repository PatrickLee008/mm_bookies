<template>
	<view class="notification-overlay" v-if="visible" @click="handleOverlayClick">
		<view class="notification-container" @click.stop>
			<!-- 关闭按钮 -->
			<view class="close-btn" @click="handleClose">
				<text class="cuIcon-close"></text>
			</view>

			<!-- 消息指示器 -->
			<view class="message-indicator" v-if="messages.length > 1">
				<text class="indicator-text">{{ currentIndex + 1 }} / {{ messages.length }}</text>
			</view>

			<!-- 消息内容容器（支持滑动切换） -->
			<swiper class="message-swiper"
				:current="currentIndex"
				@change="onSwiperChange"
				:indicator-dots="false"
				:duration="300">
				<swiper-item v-for="(message, index) in messages" :key="index">
					<view class="message-content-wrapper">
						<!-- 消息图标 -->
						<view class="message-icon-wrapper">
							<view class="message-icon" :class="getIconClass(message.messageType)">
								<text :class="getIconText(message.messageType)"></text>
							</view>
						</view>

						<!-- 消息标题 -->
						<view class="message-title">{{ message.title || $t('msg_new_message') }}</view>

						<!-- 消息内容 -->
						<scroll-view class="message-body" scroll-y>
							<text class="message-text">{{ message.content }}</text>
						</scroll-view>

						<!-- 消息时间和来源 -->
						<view class="message-meta">
							<text class="meta-item">
								<text class="cuIcon-timefill"></text>
								{{ formatTime(message.timestamp) }}
							</text>
							<text class="meta-item" v-if="message.source">
								<text class="cuIcon-infofill"></text>
								{{ message.source }}
							</text>
						</view>
					</view>
				</swiper-item>
			</swiper>

			<!-- 操作按钮 -->
			<view class="action-buttons">
				<!-- 查看详情按钮 (只有targetType不为NONE时才显示) -->
				<view class="action-btn primary-btn"
					@click="handleViewDetail"
					v-if="currentMessage.targetType || currentMessage.payload">
					<text class="btn-icon cuIcon-read"></text>
					<text class="btn-text">{{ $t('msg_view_details') }}</text>
				</view>

				<!-- 关闭/下一条按钮 -->
				<view class="action-btn secondary-btn" @click="handleNext">
					<text class="btn-icon" :class="hasMore ? 'cuIcon-right' : 'cuIcon-close'"></text>
					<text class="btn-text">{{ hasMore ? $t('msg_next') : $t('msg_close') }}</text>
				</view>
			</view>

			<!-- 左右滑动提示 -->
			<view class="swipe-hint" v-if="messages.length > 1 && showSwipeHint">
				<text class="hint-icon cuIcon-back"></text>
				<text class="hint-text">{{ $t('msg_swipe_hint') }}</text>
				<text class="hint-icon cuIcon-right"></text>
			</view>
		</view>
	</view>
</template>

<script>
import { markAsRead } from '@/utils/api/message.js'

export default {
	name: 'MessageNotification',
	data() {
		return {
			visible: false,
			messages: [],
			currentIndex: 0,
			showSwipeHint: true,
			hintTimer: null,
			// 已标记为已读的消息ID集合，用于去重
			markedReadMessageIds: new Set(),
			// 用于触发相对时间自动刷新
			now: 0
		}
	},
	computed: {
		currentMessage() {
			return this.messages[this.currentIndex] || {}
		},
		hasMore() {
			return this.currentIndex < this.messages.length - 1
		}
	},
	methods: {
		// 显示通知
		show(messages) {
			if (!messages || messages.length === 0) {
				return
			}

			this.messages = Array.isArray(messages) ? messages : [messages]
			this.currentIndex = 0
			this.visible = true
			this.showSwipeHint = this.messages.length > 1

			// 3秒后隐藏滑动提示
			if (this.showSwipeHint) {
				this.hintTimer = setTimeout(() => {
					this.showSwipeHint = false
				}, 3000)
			}

			// 自动标记第一条消息为已读（1秒后）
			setTimeout(() => {
				if (this.messages.length > 0 && this.currentIndex === 0) {
					this.markMessageAsRead(this.messages[0])
				}
			}, 1000)
		},

		// 动态添加新消息到当前显示的列表中
		addMessages(newMessages) {
			if (!newMessages || newMessages.length === 0) {
				return
			}

			const messagesToAdd = Array.isArray(newMessages) ? newMessages : [newMessages]

			// 将新消息添加到列表末尾
			this.messages.push(...messagesToAdd)

			// 如果之前只有一条消息，现在有多条了，显示滑动提示
			if (this.messages.length > 1 && !this.showSwipeHint) {
				this.showSwipeHint = true

				if (this.hintTimer) {
					clearTimeout(this.hintTimer)
				}
				this.hintTimer = setTimeout(() => {
					this.showSwipeHint = false
				}, 3000)
			}
		},

		// 隐藏通知
		hide() {
			this.visible = false
			this.messages = []
			this.currentIndex = 0
			this.showSwipeHint = false

			// 清空已读消息 ID 集合，以便下次显示通知时能够重新标记
			this.markedReadMessageIds.clear()

			if (this.hintTimer) {
				clearTimeout(this.hintTimer)
				this.hintTimer = null
			}

			// 先触发全局关闭事件，通知 WebSocket Manager 等模块
			uni.$emit('messageNotification:closed')

			// 然后通知管理器更新状态
			if (typeof uni.$messageNotification !== 'undefined') {
				uni.$messageNotification.isShowing = false
			}
		},

		// 点击遮罩层（不关闭，只能通过按钮关闭）
		handleOverlayClick() {},

		// 关闭通知
		handleClose() {
			// 标记所有已查看的消息为已读（从第一条到当前消息）
			for (let i = 0; i <= this.currentIndex; i++) {
				this.markMessageAsRead(this.messages[i])
			}

			this.$emit('close', {
				readMessages: this.messages.slice(0, this.currentIndex + 1),
				unreadMessages: this.messages.slice(this.currentIndex + 1)
			})

			this.hide()
		},

		// 下一条/关闭
		handleNext() {
			// 标记当前消息为已读
			this.markCurrentAsRead()

			if (this.hasMore) {
				this.currentIndex++
				this.$emit('next', {
					current: this.currentMessage,
					index: this.currentIndex
				})

				// 切换到新消息后，延迟1秒标记新消息为已读
				setTimeout(() => {
					if (this.messages[this.currentIndex]) {
						this.markMessageAsRead(this.messages[this.currentIndex])
					}
				}, 1000)
			} else {
				this.$emit('close', {
					readMessages: this.messages,
					unreadMessages: []
				})
				this.hide()
			}
		},

		// 查看详情
		handleViewDetail() {
			const message = this.currentMessage

			// 标记当前消息为已读
			this.markCurrentAsRead()

			// 根据 targetType 进行不同的跳转处理
			if (message.targetType === 'PAGE' && message.targetUrl) {
				// 内部页面跳转
				try {
					uni.navigateTo({
						url: message.targetUrl,
						fail: () => {
							// navigateTo 失败回退到 switchTab / redirectTo
							uni.switchTab({
								url: message.targetUrl,
								fail: () => {
									uni.redirectTo({ url: message.targetUrl })
								}
							})
						}
					})
				} catch (error) {
					uni.showToast({ title: this.$t('msg_nav_failed'), icon: 'none' })
				}
			} else if (message.targetType === 'EXTERNAL' && message.targetUrl) {
				// 外部链接跳转
				try {
					// #ifdef APP-PLUS
					plus.runtime.openURL(message.targetUrl)
					// #endif

					// #ifdef H5
					window.open(message.targetUrl, '_blank')
					// #endif
				} catch (error) {
					uni.showToast({ title: this.$t('msg_nav_failed'), icon: 'none' })
				}
			} else {
				// 默认跳转到消息中心
				uni.navigateTo({ url: '/pages/ucenter/message' })
			}

			this.$emit('viewDetail', message)

			// 关闭通知
			this.hide()
		},

		// Swiper滑动事件
		onSwiperChange(e) {
			const newIndex = e.detail.current

			// 只标记滑动到的新消息为已读
			if (this.messages[newIndex]) {
				this.markMessageAsRead(this.messages[newIndex])
			}

			this.currentIndex = newIndex
			this.showSwipeHint = false

			this.$emit('swipe', {
				current: this.currentMessage,
				index: this.currentIndex
			})
		},

		// 标记当前消息为已读
		markCurrentAsRead() {
			this.markMessageAsRead(this.currentMessage)
		},

		// 标记消息为已读
		markMessageAsRead(message) {
			if (!message || !message.messageId) return

			// 检查消息是否已经被标记为已读，避免重复调用
			if (this.markedReadMessageIds.has(message.messageId)) {
				return
			}

			// 标记消息为已读，添加到已读集合
			this.markedReadMessageIds.add(message.messageId)

			// 触发标记已读事件（通知 header 组件）
			this.$emit('markRead', message)

			// 调用 API 标记消息为已读
			markAsRead([message.messageId]).then(() => {
				// 触发全局事件，通知更新未读数
				uni.$emit('message:unreadUpdate', null)
			}).catch(() => {
				// 如果 API 调用失败，从已读集合中移除，以便下次可以重试
				this.markedReadMessageIds.delete(message.messageId)
			})
		},

		// 获取图标类名
		getIconClass(type) {
			const classMap = {
				'SYSTEM': 'icon-system',
				'ORDER': 'icon-order',
				'NOTIFICATION': 'icon-notification',
				'BROADCAST': 'icon-broadcast',
				'MESSAGE': 'icon-message',
				'PROMOTION': 'icon-promotion'
			}
			return classMap[type] || 'icon-notification'
		},

		// 获取图标文本
		getIconText(type) {
			const iconMap = {
				'SYSTEM': 'cuIcon-settings',
				'ORDER': 'cuIcon-cart',
				'NOTIFICATION': 'cuIcon-notification',
				'BROADCAST': 'cuIcon-sound',
				'MESSAGE': 'cuIcon-message',
				'PROMOTION': 'cuIcon-tag'
			}
			return iconMap[type] || 'cuIcon-notification'
		},

		// 转换时间戳为缅甸标准时间 (UTC+6:30)
		toMMT(timestamp) {
			return new Date(timestamp + 390 * 60 * 1000)
		},

		// 触发时间标签重新渲染
		refreshTimes() {
			this.now++
		},

		// 格式化时间（自动刷新 + MMT 时区）
		formatTime(timestamp) {
			if (!timestamp) return ''

			void this.now // 依赖响应式 now，每分钟自动刷新
			const now = Date.now()
			const diff = now - timestamp
			const minutes = Math.floor(diff / 60000)
			const hours = Math.floor(diff / 3600000)
			const days = Math.floor(diff / 86400000)

			if (minutes < 1) return this.$t('msg_just_now')
			if (minutes < 60) return this.$t('msg_min_ago', { n: minutes })
			if (hours < 24) return this.$t('msg_hour_ago', { n: hours })
			if (days < 7) return this.$t('msg_day_ago', { n: days })

			// 超过7天显示完整日期（MMT 时区）
			const date = this.toMMT(timestamp)
			return `${date.getUTCFullYear()}/${date.getUTCMonth() + 1}/${date.getUTCDate()}`
		}
	},

	// 组件创建时设置实例
	mounted() {
		if (typeof uni.$messageNotification !== 'undefined') {
			uni.$messageNotification.setInstance(this)
		}
		// 每分钟刷新一次相对时间
		this._timesInterval = setInterval(this.refreshTimes, 60000)
	},

	// 组件销毁时清理
	beforeDestroy() {
		clearInterval(this._timesInterval)
		if (this.hintTimer) {
			clearTimeout(this.hintTimer)
		}

		// 清理实例引用
		if (typeof uni.$messageNotification !== 'undefined') {
			uni.$messageNotification.instance = null
		}
	}
}
</script>

<style lang="scss" scoped>
.notification-overlay {
	position: fixed;
	top: 0;
	left: 0;
	right: 0;
	bottom: 0;
	background: rgba(0, 0, 0, 0.6);
	backdrop-filter: blur(4px);
	display: flex;
	align-items: center;
	justify-content: center;
	z-index: 9999;
	animation: fadeIn 0.3s ease-out;
	padding: 20px;
}

@keyframes fadeIn {
	from {
		opacity: 0;
	}
	to {
		opacity: 1;
	}
}

.notification-container {
	width: 100%;
	max-width: 400px;
	background: linear-gradient(135deg, #2F5D62 0%, #5FB5BD 100%);
	border-radius: 24px;
	overflow: hidden;
	position: relative;
	box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
	animation: slideUp 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
}

@keyframes slideUp {
	from {
		transform: translateY(100px) scale(0.8);
		opacity: 0;
	}
	to {
		transform: translateY(0) scale(1);
		opacity: 1;
	}
}

.close-btn {
	position: absolute;
	top: 16px;
	right: 16px;
	width: 36px;
	height: 36px;
	border-radius: 50%;
	background: rgba(255, 255, 255, 0.2);
	backdrop-filter: blur(10px);
	display: flex;
	align-items: center;
	justify-content: center;
	z-index: 10;
	transition: all 0.2s;

	.cuIcon-close {
		color: white;
		font-size: 20px;
	}

	&:active {
		transform: scale(0.9);
		background: rgba(255, 255, 255, 0.3);
	}
}

.message-indicator {
	position: absolute;
	top: 16px;
	left: 16px;
	background: rgba(255, 255, 255, 0.2);
	backdrop-filter: blur(10px);
	padding: 6px 12px;
	border-radius: 20px;
	z-index: 10;

	.indicator-text {
		color: white;
		font-size: 12px;
		font-weight: 600;
	}
}

.message-swiper {
	height: 420px;
}

.message-content-wrapper {
	height: 100%;
	display: flex;
	flex-direction: column;
	padding: 60px 24px 24px;
}

.message-icon-wrapper {
	display: flex;
	justify-content: center;
	margin-bottom: 20px;
}

.message-icon {
	width: 64px;
	height: 64px;
	border-radius: 50%;
	display: flex;
	align-items: center;
	justify-content: center;
	font-size: 32px;
	color: white;
	animation: iconPulse 2s ease-in-out infinite;

	&.icon-system {
		background: linear-gradient(135deg, #667eea, #764ba2);
	}

	&.icon-order {
		background: linear-gradient(135deg, #f093fb, #f5576c);
	}

	&.icon-notification {
		background: linear-gradient(135deg, #4facfe, #00f2fe);
	}

	&.icon-broadcast {
		background: linear-gradient(135deg, #43e97b, #38f9d7);
	}

	&.icon-message {
		background: linear-gradient(135deg, #fa709a, #fee140);
	}

	&.icon-promotion {
		background: linear-gradient(135deg, #30cfd0, #330867);
	}
}

@keyframes iconPulse {
	0%, 100% {
		transform: scale(1);
		box-shadow: 0 0 0 0 rgba(255, 255, 255, 0.4);
	}
	50% {
		transform: scale(1.05);
		box-shadow: 0 0 0 10px rgba(255, 255, 255, 0);
	}
}

.message-title {
	font-size: 20px;
	font-weight: 700;
	color: white;
	text-align: center;
	margin-bottom: 16px;
	text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.message-body {
	flex: 1;
	background: rgba(255, 255, 255, 0.15);
	backdrop-filter: blur(10px);
	border-radius: 16px;
	padding: 16px;
	margin-bottom: 16px;
	max-height: 180px;
}

.message-text {
	color: white;
	font-size: 15px;
	line-height: 1.6;
	word-wrap: break-word;
	white-space: pre-wrap;
}

.message-meta {
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-bottom: 20px;
	padding: 0 4px;
}

.meta-item {
	display: flex;
	align-items: center;
	color: rgba(255, 255, 255, 0.8);
	font-size: 12px;

	.cuIcon-timefill,
	.cuIcon-infofill {
		margin-right: 4px;
		font-size: 14px;
	}
}

.action-buttons {
	display: flex;
	gap: 12px;
	padding: 0 20px 20px;
}

.action-btn {
	flex: 1;
	height: 48px;
	border-radius: 12px;
	display: flex;
	align-items: center;
	justify-content: center;
	gap: 8px;
	font-weight: 600;
	font-size: 15px;
	transition: all 0.2s;

	&:active {
		transform: scale(0.95);
	}
}

.primary-btn {
	background: white;
	color: #2F5D62;
	box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);

	.btn-icon {
		font-size: 18px;
	}
}

.secondary-btn {
	background: rgba(255, 255, 255, 0.2);
	backdrop-filter: blur(10px);
	color: white;
	border: 1px solid rgba(255, 255, 255, 0.3);

	.btn-icon {
		font-size: 18px;
	}
}

.swipe-hint {
	position: absolute;
	bottom: 90px;
	left: 50%;
	transform: translateX(-50%);
	display: flex;
	align-items: center;
	gap: 8px;
	padding: 8px 16px;
	background: rgba(0, 0, 0, 0.3);
	backdrop-filter: blur(10px);
	border-radius: 20px;
	animation: hintBounce 2s ease-in-out infinite;

	.hint-text {
		color: white;
		font-size: 12px;
		font-weight: 500;
	}

	.hint-icon {
		color: white;
		font-size: 14px;
	}
}

@keyframes hintBounce {
	0%, 100% {
		transform: translateX(-50%) translateY(0);
	}
	50% {
		transform: translateX(-50%) translateY(-4px);
	}
}
</style>
