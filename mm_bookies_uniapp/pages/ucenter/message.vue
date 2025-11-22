<template name="messageCenter">
	<view class="bg-white full-page">
		<zw-header></zw-header>
		<scroll-view class="padding" scroll-y style="height: calc(100vh - 120px);">
			<!-- 消息列表视图 -->
			<view class="message-list-container">
				<view class="flex-row justify-start align-center margin-bottom-sm">
					<text class="cuIcon-back text-bold mycolor-primary margin-right-sm" @click="back_to()"></text>
					<!-- 	<image src="/static/icon/messages.png" class="lblue2blue" style="height: 28px;" mode="heightFix">
					</image> -->
					<text class="title-text" style="">Messages</text>
				</view>
				<!-- 操作栏 -->
				<view class="action-bar" v-if="messages.length > 0">
					<view class="flex-row justify-between align-center">
						<view class="message-stats">
							<text class="stats-text">Total {{messages.length}} messages</text>
							<text class="stats-text" v-if="unreadCount > 0"> · {{unreadCount}} unread</text>
						</view>
						<view class="action-buttons">
							<text class="action-btn" @click="onRefresh">Refresh</text>
							<text class="action-btn mark-read-btn" @click="markAllAsRead" v-if="hasUnreadMessages">Mark
								All Read</text>
							<text class="action-btn clear-btn" @click="clearAllMessages"
								v-if="messages.length > 0">Clear</text>
						</view>
					</view>
				</view>

				<!-- 加载状态 -->
				<view class="loading-container" v-if="loading && !refreshing">
					<view class="loading-spinner"></view>
					<text class="loading-text">Loading...</text>
				</view>

				<!-- 下拉刷新容器 -->
				<scroll-view class="message-scroll" scroll-y="true" refresher-enabled="true"
					:refresher-triggered="refreshing" @refresherrefresh="onRefresh" style="height: 400px;">

					<view class="message-list">
						<view v-for="(message, index) in messages" :key="message.id || index"
							class="message-item flex-row align-center" :class="{ 'unread': !message.read }"
							@click="viewMessageDetails(message)">

							<view class="message-icon">
								<image :src="message.icon" style="height: 40px; width: 40px;" mode="aspectFit"></image>
								<view class="unread-badge" v-if="!message.read"></view>
							</view>

							<view class="message-content flex-1">
								<view class="flex-row justify-between">
									<text class="message-title"
										:class="{ 'unread-title': !message.read }">{{message.title}}</text>
								</view>
								<text class="message-preview">{{message.preview}}</text>
								<view class="message-meta flex-row justify-between align-center">
									<view class="flex-row align-center" v-if="message.type">
										<text class="message-type">{{getTypeLabel(message.type)}}</text>
									</view>
									<view class="message-time-wrapper">
										<text class="message-time">{{formatTime(message.timestamp)}}</text>
									</view>
								</view>
							</view>
						</view>
					</view>
				</scroll-view>

				<!-- 空状态 -->
				<view class="no-messages" v-if="messages.length === 0 && !loading">
					<image src="/static/icon/messages.png"
						style="height: 80px; width: 80px; margin-bottom: 16px; opacity: 0.3;" mode="aspectFit"></image>
					<text class="no-messages-text">No Messages</text>
					<text class="no-messages-tip">Real-time messages will appear after WebSocket connection</text>
				</view>
			</view>
		</scroll-view>
	</view>
</template>

<script>
	import config from '../../utils/config.js'
	import language from '../../utils/language.js'

	export default {
		components: {},
		name: "messageCenter",
		data() {
			return {
				isLogin: uni.getStorageSync('Authorization') || false,
				language: config.language,
				messages: [],
				loading: false,
				refreshing: false
			}
		},

		computed: {
			hasUnreadMessages() {
				return this.messages.some(msg => !msg.read)
			},
			unreadCount() {
				return this.messages.filter(msg => !msg.read).length
			}
		},

		methods: {
			// 加载消息列表
			loadMessages() {
				try {
					this.loading = true
					// console.log('[MessageList] Starting to load message list')

					// 从本地存储获取WebSocket消息
					const websocketMessages = uni.getStorageSync('websocket_messages') || []
					// console.log(`[MessageList] Retrieved ${websocketMessages.length} messages from storage`)

					// 过滤掉SYSTEM类型的消息（双重保险，虽然存储时已过滤）
					const filteredMessages = websocketMessages.filter(msg => {
						const messageType = (msg.messageType || msg.type || '').toUpperCase()
						return messageType !== 'SYSTEM'
					})
					// console.log(`[MessageList] ${filteredMessages.length} non-system messages after filtering`)

					// 转换消息格式以适配UI
					const formattedMessages = filteredMessages.map(msg => {
						return {
							id: msg.id || Date.now() + Math.random(),
							title: msg.title || 'Push Message',
							preview: this.truncateContent(msg.content || msg.message || '', 50),
							content: msg.content || msg.message || '',
							timestamp: msg.timestamp || Date.now(),
							read: msg.isRead || false,
							icon: this.getMessageIcon(msg.type || 'notification'),
							type: msg.type || 'notification',
							originalMessage: msg
						}
					})

					// 按时间倒序排列（最新消息在前）
					this.messages = formattedMessages.sort((a, b) => b.timestamp - a.timestamp)
					// console.log(`[MessageList] Formatting completed, ${this.messages.length} messages total`)

				} catch (error) {
					console.error('[MessageList] Load messages failed:', error)
					uni.showToast({
						title: 'Failed to load messages',
						icon: 'none'
					})
				} finally {
					this.loading = false
					this.refreshing = false
				}
			},

			// 截取内容用作预览
			truncateContent(content, maxLength) {
				if (!content) return ''
				return content.length > maxLength ? content.substring(0, maxLength) + '...' : content
			},

			// 根据消息类型获取图标
			getMessageIcon(type) {
				const iconMap = {
					notification: '/static/icon/messages.png',
					broadcast: '/static/icon/messages.png',
					order: '/static/icon/messages.png',
					promotion: '/static/icon/messages.png'
				}
				return iconMap[type] || '/static/icon/messages.png'
			},

			// 查看消息详情
			viewMessageDetails(message) {
				// console.log('[MessageList] Viewing message details:', message.title)

				// 标记为已读
				if (!message.read) {
					message.read = true

					// 更新本地存储中的已读状态
					this.updateMessageReadStatus(message)
				}

				try {
					// 构建消息数据用于传递
					const messageData = {
						id: message.id || message.originalMessage?.id,
						messageId: message.originalMessage?.messageId || message.id,
						title: message.title || 'Push Message',
						content: message.content || '',
						timestamp: message.timestamp || Date.now(),
						isRead: message.read || false,
						type: message.type || 'notification',
						source: message.originalMessage?.source || 'WEBSOCKET',
						icon: message.icon || '/static/icon/messages.png'
					}

					// 跳转到消息详情页面
					uni.navigateTo({
						url: `/pages/ucenter/messageDetail?messageData=${encodeURIComponent(JSON.stringify(messageData))}`,
						success: () => {
							// Navigation successful
						},
						fail: (error) => {
							console.error('[MessageList] Navigation failed:', error)
							uni.showToast({
								title: 'Page navigation failed',
								icon: 'none'
							})
						}
					})
				} catch (error) {
					console.error('[MessageList] Navigation error:', error)
					uni.showToast({
						title: 'Navigation error',
						icon: 'none'
					})
				}
			},

			// 更新消息已读状态
			updateMessageReadStatus(message) {
				try {
					const messages = uni.getStorageSync('websocket_messages') || []
					const targetMessage = messages.find(m =>
						(m.id && m.id === message.originalMessage?.id) ||
						(m.timestamp === message.originalMessage?.timestamp)
					)

					if (targetMessage) {
						targetMessage.isRead = true
						uni.setStorageSync('websocket_messages', messages)
						// console.log('[MessageList] Message read status updated')

						// 通知其他组件消息状态已更新
						uni.$emit('message:read')
					}
				} catch (error) {
					console.error('[MessageList] Update message read status failed:', error)
				}
			},

			// 主页面返回（和invite/index一样的实现）
			back_to() {
				uni.navigateBack({
					delta: 1
				})
			},

			// 标记所有消息为已读
			markAllAsRead() {
				// console.log('[MessageList] Marking all messages as read')

				try {
					// 更新UI中的消息状态
					this.messages.forEach(msg => {
						msg.read = true
					})

					// 更新本地存储中的所有非SYSTEM消息状态
					const messages = uni.getStorageSync('websocket_messages') || []
					messages.forEach(msg => {
						// 只标记非SYSTEM消息为已读
						if (msg.messageType !== 'SYSTEM') {
							msg.isRead = true
						}
					})
					uni.setStorageSync('websocket_messages', messages)

					// 通知其他组件消息状态已更新
					uni.$emit('message:read')

					uni.showToast({
						title: 'All messages marked as read',
						icon: 'success'
					})

				} catch (error) {
					console.error('[MessageList] Mark all messages as read failed:', error)
					uni.showToast({
						title: 'Operation failed',
						icon: 'none'
					})
				}
			},

			// 下拉刷新
			onRefresh() {
				// console.log('[MessageList] Starting to refresh message list')
				this.refreshing = true
				this.loadMessages()
			},

			// 清空所有消息
			clearAllMessages() {
				uni.showModal({
					title: 'Confirm Clear',
					content: 'Are you sure you want to clear all messages? This action cannot be undone.',
					success: (res) => {
						if (res.confirm) {
							try {
								// 清空本地存储中的非SYSTEM消息，保留SYSTEM消息
								const messages = uni.getStorageSync('websocket_messages') || []
								const systemMessages = messages.filter(msg => msg.messageType === 'SYSTEM')
								uni.setStorageSync('websocket_messages', systemMessages)

								// 清空UI
								this.messages = []
								// 通知其他组件消息已更新
								uni.$emit('message:update')

								uni.showToast({
									title: 'All messages cleared',
									icon: 'success'
								})
								// console.log('[MessageList] All messages cleared')
							} catch (error) {
								console.error('[MessageList] Clear messages failed:', error)
								uni.showToast({
									title: 'Clear failed',
									icon: 'none'
								})
							}
						}
					}
				})
			},

			// 设置消息监听器
			setupMessageListeners() {
				const _this = this

				// 监听新消息
				uni.$on('websocket:messageSaved', (message) => {
					// console.log('[MessageList] New message notification received, refreshing list')
					_this.loadMessages()
				})

				// 监听消息更新
				uni.$on('message:update', () => {
					// console.log('[MessageList] Message update notification received, refreshing list')
					_this.loadMessages()
				})
			},

			// 格式化时间
			formatTime(timestamp) {
				const date = new Date(timestamp);
				const now = new Date();
				const diffInDays = Math.floor((now - date) / (1000 * 60 * 60 * 24));

				if (diffInDays === 0) {
					// 今天，显示时分
					return `${this.padZero(date.getHours())}:${this.padZero(date.getMinutes())}`;
				} else if (diffInDays === 1) {
					return this.language.yesterday;
				} else if (diffInDays < 7) {
					// 一周内，显示星期几
					const weekdays = [this.language.sunday, this.language.monday, this.language.tuesday,
						this.language.wednesday, this.language.thursday, this.language.friday,
						this.language.saturday
					];
					return weekdays[date.getDay()];
				} else {
					// 超过一周，显示月日
					return `${date.getMonth() + 1}/${date.getDate()}`;
				}
			},

			// 补零函数
			padZero(num) {
				return num < 10 ? `0${num}` : num;
			},

			// 获取消息类型标签
			getTypeLabel(type) {
				const typeMap = {
					notification: 'Notification',
					broadcast: 'Broadcast',
					order: 'Order',
					promotion: 'Promotion'
				}
				return typeMap[type] || 'Push Message'
			}
		},

		created() {
			// console.log('[MessageList] Component created, starting initialization')
			// 加载消息列表
			this.loadMessages()
			// 设置消息监听器
			this.setupMessageListeners()
		},

		// 组件销毁时清理监听器
		beforeDestroy() {
			uni.$off('websocket:messageSaved')
			uni.$off('message:update')
		}
	}
</script>

<style lang="scss">
	.message-list-container {
		padding: 0;
	}

	.title-bar {
		padding: 16px 0;
		border-bottom: 1px solid #EDEDED;
		margin-bottom: 16px;
	}

	.title-text {
		font-size: 18px;
		font-weight: bold;
		margin-left: 8px;
	}

	.mark-all-read {
		color: #007AFF;
		font-size: 14px;
	}

	.message-list {
		display: flex;
		flex-direction: column;
	}

	.message-item {
		padding: 12px 0;
		border-bottom: 1px solid #F5F5F5;
		transition: background-color 0.2s;

		&:last-child {
			border-bottom: none;
		}

		&:active {
			background-color: #F5F5F5;
		}

		&.unread {
			background-color: #FFF8E6;
		}
	}

	.message-icon {
		position: relative;
		margin-right: 12px;
	}

	.unread-badge {
		position: absolute;
		top: -2px;
		right: -2px;
		width: 10px;
		height: 10px;
		border-radius: 50%;
		background-color: #FF3B30;
	}

	.message-content {
		overflow: hidden;
	}

	.message-title {
		font-size: 16px;
		color: #333333;
		font-weight: 500;
	}

	.message-time {
		font-size: 12px;
		color: #999999;
	}

	.message-preview {
		font-size: 14px;
		color: #666666;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
		margin-top: 4px;
		display: block;
	}

	.no-messages {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		padding: 60px 0;
		color: #999999;
		font-size: 16px;
	}


	/* 新增样式 */
	.action-bar {
		padding: 12px 10px;
		background-color: #F8F9FA;
		border-bottom: 1px solid #EDEDED;
		margin-bottom: 8px;
		border-radius: 5px;
		box-shadow: 0px 1px 1px 0px #00000040;

	}

	.message-stats .stats-text {
		font-size: 12px;
		color: #666666;
	}

	.action-buttons .action-btn {
		font-size: 14px;
		color: #007AFF;
		margin-left: 16px;
		padding: 4px 8px;
		border-radius: 4px;
		background-color: transparent;
		transition: background-color 0.2s;
	}

	.action-buttons .action-btn:active {
		background-color: rgba(0, 122, 255, 0.1);
	}

	.mark-read-btn {
		color: #34C759 !important;
	}

	.clear-btn {
		color: #FF3B30 !important;
	}

	.loading-container {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		padding: 40px 0;
	}

	.loading-spinner {
		width: 20px;
		height: 20px;
		border: 2px solid #EDEDED;
		border-top: 2px solid #007AFF;
		border-radius: 50%;
		animation: spin 1s linear infinite;
		margin-bottom: 8px;
	}

	@keyframes spin {
		0% {
			transform: rotate(0deg);
		}

		100% {
			transform: rotate(360deg);
		}
	}

	.loading-text {
		font-size: 14px;
		color: #999999;
	}

	.message-scroll {
		flex: 1;
	}

	.unread-title {
		font-weight: bold;
		color: #333333;
	}

	.message-meta {
		margin-top: 4px;
	}

	.message-type {
		font-size: 11px;
		color: #007AFF;
		background-color: rgba(0, 122, 255, 0.1);
		padding: 2px 6px;
		border-radius: 8px;
		margin-right: 8px;
	}

	.no-messages-text {
		font-size: 16px;
		color: #666666;
		margin-bottom: 8px;
	}

	.no-messages-tip {
		font-size: 14px;
		color: #999999;
	}

	.title-text {
		font-size: 18px;
		font-weight: bold;
		color: #333333;
		margin-left: 8px;
	}
</style>