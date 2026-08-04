<template>
	<view class="full-page dark-teal-bg">
		<zw-header></zw-header>
		<scroll-view class="padding" scroll-y style="height: calc(100vh - 120px);">
			<!-- 返回头部 -->
			<view class="flex-row justify-start align-center margin-bottom-sm">
				<text class="cuIcon-back text-bold mycolor-primary margin-right-sm" @click="back_to()"></text>
				<!-- <image :src="messageData.icon || '/static/icon/messages.png'" class="lblue2blue" style="height: 28px;" mode="heightFix"></image> -->
				<text class="title-text">{{ $t('message_details') }}</text>
			</view>
			
			<!-- 消息详情内容 -->
			<view class="message-detail-card">
				<!-- 消息头部 -->
				<view class="detail-header">
					<view class="message-icon-large">
						<image :src="messageData.icon || '/static/icon/messages.png'" 
							   style="height: 50px; width: 50px;" 
							   mode="aspectFit"></image>
					</view>
					<text class="detail-title">{{ messageData.title || $t('push_message') }}</text>
					<text class="detail-time">{{ formatTime(messageData.timestamp) }}</text>
					<view class="message-type-tag" v-if="messageData.type">
						<text class="type-text">{{ getTypeLabel(messageData.type) }}</text>
					</view>
				</view>
				
				<!-- 消息内容 -->
				<view class="detail-content">
					<text class="content-text" v-if="messageData.content">{{ messageData.content }}</text>
					<text class="no-content-text" v-else>{{ $t('no_content_available') }}</text>
				</view>
				
				<!-- 消息元数据 -->
				<view class="detail-meta" v-if="showMetadata">
					<view class="meta-item">
						<text class="meta-label">{{ $t('message_id') }}:</text>
						<text class="meta-value">{{ messageData.messageId || messageData.id || 'N/A' }}</text>
					</view>
					<view class="meta-item" v-if="messageData.source">
						<text class="meta-label">{{ $t('source_label') }}:</text>
						<text class="meta-value">{{ messageData.source }}</text>
					</view>
					<view class="meta-item">
						<text class="meta-label">{{ $t('received') }}:</text>
						<text class="meta-value">{{ formatFullTime(messageData.timestamp) }}</text>
					</view>
				</view>
				
				<!-- 操作按钮 -->
				<view class="detail-actions">
					<view class="action-btn primary-btn" @click="markAsRead" v-if="!messageData.isRead">
						<text class="btn-text">{{ $t('mark_as_read') }}</text>
					</view>
					<view class="action-btn secondary-btn" @click="deleteMessage">
						<text class="btn-text">{{ $t('delete') }}</text>
					</view>
					<view class="action-btn secondary-btn" @click="toggleMetadata">
						<text class="btn-text">{{ showMetadata ? $t('hide') : $t('show') }} {{ $t('details') }}</text>
					</view>
				</view>
			</view>
		</scroll-view>
	</view>
</template>

<script>
	import config from '../../utils/config.js'
	import language from '../../utils/language.js'

	export default {
		name: "MessageDetail",
		data() {
			return {
				language: config.language,
				messageData: {},
				showMetadata: false,
				originalMessageData: null
			}
		},

		methods: {
			// 返回上一页
			back_to() {
				uni.navigateBack({
					delta: 1
				})
			},

			// 标记为已读
			markAsRead() {
				try {
					this.messageData.isRead = true
					
					// 更新本地存储中的已读状态
					this.updateMessageInStorage()
					
					// 通知其他组件消息状态已更新
					uni.$emit('message:read')
					
					uni.showToast({
						title: this.$t('marked_as_read'),
						icon: 'success',
						duration: 1500
					})
					
				} catch (error) {
					console.error('[MessageDetail] 标记已读失败:', error)
					uni.showToast({
						title: this.$t('operation_failed'),
						icon: 'none'
					})
				}
			},

			// 删除消息
			deleteMessage() {
				this.$notice.show({
					title: this.$t('delete_message'),
					content: this.$t('confirm_delete_message'),
					success: (res) => {
						if (res.confirm) {
							try {
								// 从本地存储中删除消息
								this.removeMessageFromStorage()
								
								// 通知其他组件消息已更新
								uni.$emit('message:update')
								
								uni.showToast({
									title: this.$t('message_deleted'),
									icon: 'success'
								})
								
								// 返回上一页
								setTimeout(() => {
									this.back_to()
								}, 1000)
								
							} catch (error) {
								console.error('[MessageDetail] 删除消息失败:', error)
								uni.showToast({
									title: this.$t('delete failed'),
									icon: 'none'
								})
							}
						}
					}
				})
			},

			// 切换元数据显示
			toggleMetadata() {
				this.showMetadata = !this.showMetadata
			},

			// 更新本地存储中的消息
			updateMessageInStorage() {
				try {
					const messages = uni.getStorageSync('websocket_messages') || []
					const targetMessageIndex = messages.findIndex(m => 
						(m.id && m.id === (this.messageData.id || this.messageData.messageId)) || 
						(m.messageId && m.messageId === (this.messageData.messageId || this.messageData.id)) ||
						(m.timestamp === this.messageData.timestamp && m.title === this.messageData.title)
					)
					
					if (targetMessageIndex !== -1) {
						messages[targetMessageIndex].isRead = true
						uni.setStorageSync('websocket_messages', messages)
						// console.log('[MessageDetail] Message read status updated')
					}
				} catch (error) {
					console.error('[MessageDetail] 更新消息存储失败:', error)
				}
			},

			// 从本地存储中删除消息
			removeMessageFromStorage() {
				try {
					const messages = uni.getStorageSync('websocket_messages') || []
					const filteredMessages = messages.filter(m => {
						const isSameMessage = 
							(m.id && m.id === (this.messageData.id || this.messageData.messageId)) || 
							(m.messageId && m.messageId === (this.messageData.messageId || this.messageData.id)) ||
							(m.timestamp === this.messageData.timestamp && m.title === this.messageData.title)
						return !isSameMessage
					})
					
					uni.setStorageSync('websocket_messages', filteredMessages)
					// console.log('[MessageDetail] Message deleted from storage')
				} catch (error) {
					console.error('[MessageDetail] 删除消息存储失败:', error)
				}
			},

			// 格式化时间（简短版）
			formatTime(timestamp) {
				if (!timestamp) return 'N/A'
				
				const date = new Date(timestamp);
				const now = new Date();
				const diffInDays = Math.floor((now - date) / (1000 * 60 * 60 * 24));

				if (diffInDays === 0) {
					// 今天，显示时分
					return `${this.padZero(date.getHours())}:${this.padZero(date.getMinutes())}`;
				} else if (diffInDays === 1) {
					return this.language.yesterday || 'Yesterday';
				} else if (diffInDays < 7) {
					// 一周内，显示星期几
					const weekdays = [
						this.language.sunday || 'Sunday', 
						this.language.monday || 'Monday', 
						this.language.tuesday || 'Tuesday', 
						this.language.wednesday || 'Wednesday', 
						this.language.thursday || 'Thursday', 
						this.language.friday || 'Friday', 
						this.language.saturday || 'Saturday'
					];
					return weekdays[date.getDay()];
				} else {
					// 超过一周，显示月日
					return `${date.getMonth() + 1}/${date.getDate()}`;
				}
			},

			// 格式化完整时间
			formatFullTime(timestamp) {
				if (!timestamp) return 'N/A'
				
				const date = new Date(timestamp);
				return `${date.getFullYear()}/${this.padZero(date.getMonth() + 1)}/${this.padZero(date.getDate())} ${this.padZero(date.getHours())}:${this.padZero(date.getMinutes())}:${this.padZero(date.getSeconds())}`;
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
					order: 'Order Update',
					promotion: 'Promotion',
					system: 'System'
				}
				return typeMap[type] || 'Push Message'
			}
		},

		onLoad(options) {
			// console.log('[MessageDetail] Page loaded, options:', options)
			
			try {
				// 从URL参数中获取消息数据
				if (options.messageData) {
					// 解析传递的消息数据
					this.messageData = JSON.parse(decodeURIComponent(options.messageData))
					// console.log('[MessageDetail] Got message data from params:', this.messageData)
				} else if (options.messageId) {
					// 通过消息ID从本地存储中查找
					const messages = uni.getStorageSync('websocket_messages') || []
					const targetMessage = messages.find(m => 
						m.id === options.messageId || 
						m.messageId === options.messageId
					)
					
					if (targetMessage) {
						this.messageData = {
							id: targetMessage.id || targetMessage.messageId,
							messageId: targetMessage.messageId || targetMessage.id,
							title: targetMessage.title || 'Push Message',
							content: targetMessage.content || targetMessage.message || '',
							timestamp: targetMessage.timestamp || Date.now(),
							isRead: targetMessage.isRead || false,
							type: targetMessage.type || targetMessage.messageType || 'notification',
							source: targetMessage.source || 'WEBSOCKET',
							icon: '/static/icon/messages.png'
						}
						// console.log('[MessageDetail] Got message data from storage:', this.messageData)
					} else {
						console.warn('[MessageDetail] 未找到对应的消息')
						this.messageData = {
							title: this.$t('message_not_found'),
							content: this.$t('message_not_found_content'),
							timestamp: Date.now(),
							type: 'error'
						}
					}
				} else {
					// 没有提供消息数据，显示错误信息
					console.warn('[MessageDetail] 未提供消息数据')
					this.messageData = {
						title: this.$t('no_message_data'),
						content: this.$t('no_message_data_content'),
						timestamp: Date.now(),
						type: 'error'
					}
				}
				
				// 自动标记为已读
				if (this.messageData && !this.messageData.isRead) {
					setTimeout(() => {
						this.markAsRead()
					}, 1000)
				}
				
			} catch (error) {
				console.error('[MessageDetail] 解析消息数据失败:', error)
				this.messageData = {
					title: this.$t('parse_error'),
					content: this.$t('parse_error_content'),
					timestamp: Date.now(),
					type: 'error'
				}
			}
		}
	}
</script>

<style lang="scss">
	.dark-teal-bg {
		background: linear-gradient(to right, #02455F 0%, #02455F 56%, #1F879B 100%);
		min-height: 100vh;
	}

	.message-detail-card {
		background-color: #FFFFFF;
		border-radius: 12px;
		margin: 8px 0;
		box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
		overflow: hidden;
	}

	.detail-header {
		text-align: center;
		padding: 24px 20px;
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		color: white;
		position: relative;
	}

	.message-icon-large {
		margin-bottom: 12px;
	}

	.detail-title {
		font-size: 20px;
		font-weight: bold;
		display: block;
		margin-bottom: 8px;
		line-height: 1.3;
	}

	.detail-time {
		font-size: 14px;
		opacity: 0.8;
		display: block;
		margin-bottom: 8px;
	}

	.message-type-tag {
		display: inline-block;
		background-color: rgba(255, 255, 255, 0.2);
		padding: 4px 12px;
		border-radius: 16px;
		margin-top: 8px;
	}

	.type-text {
		font-size: 12px;
		font-weight: 500;
	}

	.detail-content {
		padding: 24px 20px;
		min-height: 80px;
	}

	.content-text {
		font-size: 16px;
		line-height: 1.6;
		color: #333333;
		word-wrap: break-word;
		white-space: pre-wrap;
	}

	.no-content-text {
		font-size: 16px;
		color: #999999;
		font-style: italic;
	}

	.detail-meta {
		padding: 16px 20px;
		background-color: #F8F9FA;
		border-top: 1px solid #EDEDED;
	}

	.meta-item {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 8px;

		&:last-child {
			margin-bottom: 0;
		}
	}

	.meta-label {
		font-size: 14px;
		color: #666666;
		font-weight: 500;
	}

	.meta-value {
		font-size: 14px;
		color: #333333;
		font-family: monospace;
		flex: 1;
		text-align: right;
		word-break: break-all;
		margin-left: 12px;
	}

	.detail-actions {
		padding: 16px 20px;
		display: flex;
		flex-wrap: wrap;
		gap: 8px;
		border-top: 1px solid #EDEDED;
		background-color: #FAFBFC;
	}

	.action-btn {
		flex: 1;
		min-width: 100px;
		padding: 12px 16px;
		border-radius: 8px;
		text-align: center;
		cursor: pointer;
		transition: all 0.2s;

		&:active {
			transform: scale(0.98);
		}
	}

	.primary-btn {
		background-color: #007AFF;
		
		.btn-text {
			color: white;
			font-weight: 500;
		}

		&:active {
			background-color: #0056CC;
		}
	}

	.secondary-btn {
		background-color: #F2F3F5;
		
		.btn-text {
			color: #666666;
			font-weight: 500;
		}

		&:active {
			background-color: #E5E6EA;
		}
	}

	.btn-text {
		font-size: 14px;
		display: block;
	}

	.title-text {
		font-size: 18px;
		font-weight: bold;
		color: #333333;
		margin-left: 8px;
	}

	/* 响应式调整 */
	@media (max-width: 480px) {
		.detail-actions {
			flex-direction: column;
		}

		.action-btn {
			flex: none;
			width: 100%;
		}

		.meta-value {
			font-size: 12px;
		}
	}
</style>