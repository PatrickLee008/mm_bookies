<template name="messageCenter">
	<view class="full-page">
		<zw-header @headerHeightChange="onHeaderHeightChange"></zw-header>
		<!-- header 占位，防止内容被固定头部遮挡 -->
		<view class="header-placeholder" :style="{ height: headerHeight + 'px' }"></view>

		<!-- 页面头部 -->
		<view class="page-header">
			<view class="header-left">
				<text class="cuIcon-back" @click="back_to()"></text>
				<text class="header-title">{{ $t('messages_title') }}</text>
			</view>
			<view class="header-right" v-if="unreadCount > 0">
				<text class="mark-all-read-btn" @click="markAllAsRead">
					<text class="cuIcon-check"></text> {{ $t('mark_all_read') }}
				</text>
			</view>
		</view>

		<!-- 消息过滤标签 -->
		<view class="filter-tabs">
			<view class="tab-item" :class="{'active': activeTab === 'all'}" @click="switchTab('all')">
				<text class="tab-text">{{ $t('msg_tab_all') }}</text>
				<view class="tab-underline" v-if="activeTab === 'all'"></view>
			</view>
			<view class="tab-item" :class="{'active': activeTab === 'unread'}" @click="switchTab('unread')">
				<text class="tab-text">{{ $t('msg_tab_unread') }}</text>
				<view class="tab-badge" v-if="unreadCount > 0">{{ unreadCount > 99 ? '99+' : unreadCount }}</view>
				<view class="tab-underline" v-if="activeTab === 'unread'"></view>
			</view>
			<view class="tab-item" :class="{'active': activeTab === 'read'}" @click="switchTab('read')">
				<text class="tab-text">{{ $t('msg_tab_read') }}</text>
				<view class="tab-underline" v-if="activeTab === 'read'"></view>
			</view>
		</view>

		<!-- 加载状态 -->
		<view class="loading-container" v-if="loading && !refreshing">
			<view class="loading-spinner"></view>
			<text class="loading-text">{{ $t('msg_loading') }}</text>
		</view>

		<!-- 下拉刷新容器 -->
		<scroll-view class="message-scroll" scroll-y="true" refresher-enabled="true" :refresher-triggered="refreshing"
			@refresherrefresh="onRefresh" @scroll="handleHeaderScroll" @scrolltoupper="handleHeaderTop">

			<!-- 消息列表 -->
			<view class="message-list">
				<view v-for="(message, index) in messages" :key="message.id || index" class="message-card"
					:class="{'unread-card': !message.read}" @click="viewMessageDetails(message)">
					<!-- 未读指示条 -->
					<view class="unread-indicator" v-if="!message.read"></view>

					<!-- 卡片头部 -->
					<view class="card-header">
						<text class="header-text">{{ getMessageSource(message) }}</text>
						<text class="message-time">{{ formatMessageTime(message.timestamp) }}</text>
					</view>

					<!-- 卡片内容 -->
					<view class="card-body">
						<text class="message-title">{{ message.title }}</text>
						<text class="message-description">{{ message.preview }}</text>
					</view>
				</view>
			</view>
			<!-- 空状态 -->
			<view class="no-messages" v-if="messages.length === 0 && !loading">
				<image src="/static/icon/messages.png"
					style="height: 80px; width: 80px; margin-bottom: 16px; opacity: 0.3;" mode="aspectFit"></image>
				<text class="no-messages-text">{{ $t('no_messages') }}</text>
				<text class="no-messages-tip">{{ $t('realtime_msg_tip') }}</text>
			</view>
			<!-- 底部安全区域占位 -->
			<view style="height: 30px; width: 100%;"></view>
		</scroll-view>

		<!-- 消息详情弹窗 -->
		<view class="modal-overlay" v-if="showDetailModal" @click="closeModal">
			<view class="modal-content" @click.stop>
				<!-- 弹窗头部 -->
				<view class="modal-header">
					<text class="modal-title">{{ $t('msg_details') }}</text>
					<text class="cuIcon-close" @click="closeModal"></text>
				</view>

				<!-- 弹窗内容 -->
				<scroll-view class="modal-body" scroll-y>
					<view class="detail-section">
						<text class="detail-label">{{ $t('msg_title_label') }}:</text>
						<text class="detail-title-text">{{ selectedMessage.title }}</text>
					</view>
					<view class="detail-divider"></view>

					<view class="detail-section">
						<text class="detail-label">{{ $t('msg_content_label') }}:</text>
						<text class="detail-content-text">{{ selectedMessage.content || $t('msg_no_content') }}</text>
					</view>
					<view class="detail-divider"></view>

					<view class="detail-section">
						<view class="detail-item">
							<text class="detail-label">{{ $t('msg_from') }}:</text>
							<text class="detail-value">{{ selectedMessage.source || 'System' }}</text>
						</view>
						<view class="detail-item">
							<text class="detail-label">{{ $t('msg_type_label') }}:</text>
							<text class="detail-value">{{ getTypeLabel(selectedMessage.type) }}</text>
						</view>
						<view class="detail-item">
							<text class="detail-label">{{ $t('msg_time_label') }}:</text>
							<text class="detail-value">{{ formatFullTime(selectedMessage.timestamp) }}</text>
						</view>
					</view>
				</scroll-view>

				<!-- 弹窗底部操作 -->
				<view class="modal-footer">
					<!-- 跳转按钮 - 根据target_type和target_url显示 -->
					<view class="modal-btn primary-btn" @click="handleMessageJump" v-if="shouldShowJumpButton()">
						<text class="btn-text">{{ $t('msg_view_details') }}</text>
					</view>

					<view class="modal-btn primary-btn" @click="markAsRead" v-if="!selectedMessage.read">
						<text class="btn-text">{{ $t('msg_mark_as_read') }}</text>
					</view>
					<view class="modal-btn primary-btn" @click="closeModal" v-else>
						<text class="btn-text">{{ $t('msg_close') }}</text>
					</view>
				</view>
			</view>
		</view>

		<!-- Mark All Read 自定义确认弹窗（替代框架自带 this.$notice.show，避免英文单词换行问题） -->
		<view class="modal-overlay" v-if="showMarkAllModal" @click="showMarkAllModal = false">
			<view class="confirm-modal" @click.stop>
				<view class="confirm-header">
					<text class="confirm-title">{{ $t('mark_all_read') }}</text>
				</view>
				<view class="confirm-body">
					<text class="confirm-message">{{ $t('msg_mark_all_confirm', { n: unreadCount }) }}</text>
				</view>
				<view class="confirm-footer">
					<view class="confirm-btn cancel-btn" @click="showMarkAllModal = false">
						<text class="confirm-btn-text cancel-text">{{ $t('Cancel') }}</text>
					</view>
					<view class="confirm-btn ok-btn" @click="confirmMarkAllAsRead">
						<text class="confirm-btn-text ok-text">{{ $t('Confirm') }}</text>
					</view>
				</view>
			</view>
		</view>
	</view>
</template>

<script>
	import config from '../../utils/config.js'
	import language from '../../utils/language.js'
	import {
		getMessageList,
		getUnreadCount,
		markAsRead as apiMarkAsRead,
		markAllAsRead as apiMarkAllAsRead,
		deleteMessage as apiDeleteMessage
	} from '../../utils/api/message.js'
	import headerCollapse from '@/mixins/headerCollapse.js'

	export default {
		name: "messageCenter",
		mixins: [headerCollapse],
		data() {
			return {
				isLogin: uni.getStorageSync('Authorization') || false,
				language: config.language,
				messages: [],
				loading: false,
				refreshing: false,
				showDetailModal: false,
				showMarkAllModal: false, // 控制 Mark All Read 自定义确认弹窗
				selectedMessage: {},
				currentPage: 1,
				pageSize: 20,
				hasMore: true,
				activeTab: 'all', // 当前激活的标签：all, unread, read
				unreadCount: 0 // 未读消息数量
			}
		},

		computed: {
			hasUnreadMessages() {
				return this.messages.some(msg => !msg.read)
			}
		},

		methods: {
			// 从后端API加载消息列表
			async loadMessages() {
				this.messages = [];
				try {
					this.loading = true
					// 检查用户是否已登录
					if (!this.isLogin) {
						this.messages = []
						return
					}

					// 构建查询参数，根据当前激活的标签过滤
					const params = {
						current: this.currentPage,
						size: this.pageSize
					}

					// 根据标签添加 isRead 过滤条件
					if (this.activeTab === 'unread') {
						params.isRead = 0 // 未读
					} else if (this.activeTab === 'read') {
						params.isRead = 1 // 已读
					}
					// activeTab === 'all' 时不传 isRead，获取全部消息

					// 从后端API获取消息列表
					const response = await getMessageList(params)
					if (response && response.records) {
						// 转换后端消息格式为前端显示格式
						this.messages = response.records.map(msg => ({
							id: msg.id,
							messageId: msg.messageId,
							title: msg.title,
							preview: this.truncateContent(msg.content, 50),
							content: msg.content,
							timestamp: new Date(msg.createTime).getTime(),
							read: msg.isRead === 1,
							icon: this.getMessageIcon(msg.messageType || 'NOTIFICATION'),
							type: msg.messageType || 'NOTIFICATION',
							source: msg.source || 'SYSTEM',
							targetUrl: msg.targetUrl,
							targetType: msg.targetType,
							priority: msg.priority,
							createTime: msg.createTime,
							updateTime: msg.updateTime,
							originalMessage: msg // 保留原始数据
						}))

						// 按时间倒序排列
						this.messages.sort((a, b) => b.timestamp - a.timestamp)
					} else {
						this.messages = []
					}

					// 更新未读消息数量（用于标签角标显示）
					await this.updateUnreadCount()

				} catch (error) {
					console.error('[MessageList] Failed to load messages from backend:', error)
					uni.showToast({
						title: this.$t('failed_load_messages'),
						icon: 'none',
						duration: 2000
					})
					this.messages = []
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

			// 获取消息来源
			getMessageSource(message) {
				return message.source || 'System'
			},

			// 查看消息详情（弹窗）
			viewMessageDetails(message) {
				this.selectedMessage = message
				this.showDetailModal = true

				// 标记为已读
				if (!message.read) {
					message.read = true
					this.updateMessageReadStatus(message)
				}
			},

			// 关闭弹窗
			closeModal() {
				this.showDetailModal = false
				this.selectedMessage = {}
			},

			// 标记为已读
			async markAsRead() {
				if (this.selectedMessage && !this.selectedMessage.read) {
					this.selectedMessage.read = true
					await this.updateMessageReadStatus(this.selectedMessage)

					uni.showToast({
						title: this.$t('msg_marked_read'),
						icon: 'success',
						duration: 1500
					})
				}
			},

			// 判断是否应该显示跳转按钮
			shouldShowJumpButton() {
				const message = this.selectedMessage
				if (!message) return false

				// 只有当target_type不是NONE且target_url存在时才显示跳转按钮
				return message.targetType &&
					message.targetType !== 'NONE' &&
					message.targetUrl &&
					message.targetUrl.trim() !== ''
			},

			// 处理消息跳转
			handleMessageJump() {
				const message = this.selectedMessage
				if (!message || !message.targetType || !message.targetUrl) {
					return
				}

				try {
					switch (message.targetType) {
						case 'PAGE':
							this.handlePageJump(message.targetUrl)
							break

						case 'EXTERNAL':
							this.handleExternalJump(message.targetUrl)
							break

						case 'NONE':
						default:
							uni.showToast({
								title: this.$t('msg_no_action'),
								icon: 'none'
							})
							break
					}
				} catch (error) {
					uni.showToast({
						title: this.$t('msg_nav_failed'),
						icon: 'none'
					})
				}
			},

			// 处理页面内部跳转（mm-bookies 无 $toolbox.navigateToPage，使用 uni 原生跳转 + 回退）
			handlePageJump(route) {
				uni.navigateTo({
					url: route,
					success: () => {
						this.closeModal()
					},
					fail: () => {
						// navigateTo 失败回退 switchTab / redirectTo
						uni.switchTab({
							url: route,
							success: () => {
								this.closeModal()
							},
							fail: () => {
								uni.redirectTo({
									url: route,
									success: () => {
										this.closeModal()
									},
									fail: () => {
										uni.showToast({
											title: this.$t('msg_nav_failed'),
											icon: 'none'
										})
									}
								})
							}
						})
					}
				})
			},

			// 处理外部链接跳转
			handleExternalJump(targetUrl) {
				try {
					// #ifdef APP-PLUS
					plus.runtime.openURL(targetUrl)
					this.closeModal()
					// #endif

					// #ifdef H5
					window.open(targetUrl, '_blank')
					this.closeModal()
					// #endif
				} catch (error) {
					uni.showToast({
						title: this.$t('msg_nav_failed'),
						icon: 'none'
					})
				}
			},

			// 删除消息（onex2 中此入口默认隐藏，保留实现以备启用）
			deleteMessage() {
				this.$notice.show({
					title: this.$t('confirm_clear'),
					content: this.$t('confirm_clear_content'),
					confirmText: this.$t('clear'),
					success: async (res) => {
						if (!res.confirm) return
						try {
							if (!this.isLogin || !this.selectedMessage.id) {
								return
							}

							// 调用后端API删除消息
							await apiDeleteMessage(this.selectedMessage.id)

							// 从UI列表中移除
							const index = this.messages.findIndex(m => m.id === this.selectedMessage.id)
							if (index !== -1) {
								this.messages.splice(index, 1)
							}

							this.closeModal()

							// 通知其他组件消息已更新
							uni.$emit('message:update')
							uni.$emit('message:unreadUpdate', null)

							this.updateUnreadCount()

							uni.showToast({
								title: this.$t('all_messages_cleared'),
								icon: 'success'
							})
						} catch (error) {
							uni.showToast({
								title: this.$t('clear_failed'),
								icon: 'none'
							})
						}
					}
				})
			},

			// 更新消息已读状态（调用后端API）
			async updateMessageReadStatus(message) {
				try {
					if (!this.isLogin || !message.id) {
						return
					}

					// 调用后端API标记消息为已读
					await apiMarkAsRead(message.id)

					// 触发全局事件，通知其他组件更新角标
					uni.$emit('message:read')
					uni.$emit('message:unreadUpdate', null)

					// 更新本页未读数
					this.updateUnreadCount()

				} catch (error) {
					console.error('[MessageList] Failed to mark message as read:', error)
					uni.showToast({
						title: this.$t('msg_failed_mark'),
						icon: 'none',
						duration: 2000
					})
				}
			},

			// 返回上一页
			back_to() {
				uni.navigateBack({
					delta: 1
				})
			},

			// 切换标签
			switchTab(tab) {
				if (this.activeTab === tab) return // 避免重复点击

				this.activeTab = tab
				this.currentPage = 1 // 重置页码
				this.loadMessages() // 重新加载消息
			},

			// 更新未读消息数量
			async updateUnreadCount() {
				try {
					if (!this.isLogin) {
						this.unreadCount = 0
						return
					}

					// 从后端API获取未读消息数
					const count = await getUnreadCount()
					this.unreadCount = count || 0

					// 同步应用角标
					// #ifdef APP-PLUS
					plus.runtime.setBadgeNumber(this.unreadCount)
					// #endif

				} catch (error) {
					this.unreadCount = 0
				}
			},

			// 标记全部消息为已读：打开自定义确认弹窗（替代框架自带 this.$notice.show）
			markAllAsRead() {
				if (!this.isLogin || this.unreadCount === 0) {
					return
				}
				this.showMarkAllModal = true
			},

			// 确认标记全部消息为已读
			async confirmMarkAllAsRead() {
				this.showMarkAllModal = false

				if (!this.isLogin || this.unreadCount === 0) {
					return
				}

				uni.showLoading({
					title: this.$t('msg_processing'),
					mask: true
				})

				try {
					// 调用后端API标记全部为已读
					await apiMarkAllAsRead()

					// 刷新消息列表和未读数
					await this.loadMessages()

					// 触发全局事件，通知其他组件更新
					uni.$emit('message:read')
					uni.$emit('message:unreadUpdate', null)

					uni.hideLoading()
					uni.showToast({
						title: this.$t('all_marked_read'),
						icon: 'success',
						duration: 2000
					})
				} catch (error) {
					uni.hideLoading()
					uni.showToast({
						title: this.$t('msg_failed_mark'),
						icon: 'none',
						duration: 2000
					})
				}
			},

			// 下拉刷新
			onRefresh() {
				this.refreshing = true
				setTimeout(() => {
					this.loadMessages()
				}, 300)
			},

			// 设置消息监听器
			setupMessageListeners() {
				const _this = this

				// 收到实时推送消息时，重新从后端API加载完整列表
				uni.$on('websocket:messageSaved', () => {
					_this.loadMessages()
				})

				// 监听消息更新（已读、删除等操作）
				uni.$on('message:update', () => {
					_this.loadMessages()
				})

				// 监听未读数更新
				uni.$on('message:unreadUpdate', () => {
					_this.updateUnreadCount()
				})
			},

			// 格式化完整时间
			formatFullTime(timestamp) {
				if (!timestamp) return 'N/A'

				const date = new Date(timestamp);
				return `${date.getFullYear()}/${this.padZero(date.getMonth() + 1)}/${this.padZero(date.getDate())} ${this.padZero(date.getHours())}:${this.padZero(date.getMinutes())}`;
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
				return typeMap[(type || '').toLowerCase()] || this.$t('push_message')
			},

			// 格式化消息时间（列表显示）
			formatMessageTime(timestamp) {
				if (!timestamp) return ''

				const now = Date.now()
				const diff = now - timestamp
				const minutes = Math.floor(diff / 60000)
				const hours = Math.floor(diff / 3600000)
				const days = Math.floor(diff / 86400000)

				if (minutes < 1) return this.$t('msg_just_now')
				if (minutes < 60) return this.$t('msg_min_ago', {
					n: minutes
				})
				if (hours < 24) return this.$t('msg_hour_ago', {
					n: hours
				})
				if (days < 7) return this.$t('msg_day_ago', {
					n: days
				})

				const date = new Date(timestamp)
				return `${date.getMonth() + 1}/${date.getDate()} ${this.padZero(date.getHours())}:${this.padZero(date.getMinutes())}`
			}
		},

		created() {
			// 加载消息列表
			this.loadMessages()
			// 设置消息监听器
			this.setupMessageListeners()
		},

		// 组件销毁时清理监听器
		beforeDestroy() {
			uni.$off('websocket:messageSaved')
			uni.$off('message:update')
			uni.$off('message:unreadUpdate')
		}
	}
</script>

<style lang="scss" scoped>
	.full-page {
		height: 100vh;
		overflow: hidden;
		display: flex;
		flex-direction: column;
	}

	/* header 占位 */
	.header-placeholder {
		height: 255px;
		width: 100%;
		flex-shrink: 0;
		transition: height 0.3s ease;
	}

	.page-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 12px 10px;
		font-weight: bold;
		color: $color-primary;
		background-color: white;
		flex-shrink: 0;
	}

	.header-left {
		display: flex;
		align-items: center;
	}

	.header-right {
		display: flex;
		align-items: center;
	}

	.cuIcon-back {
		font-size: 16px;
		margin-right: 5px;
	}

	.header-title {
		font-weight: 600;
		font-size: 15px;
		line-height: 22px;
		letter-spacing: 0.5px;
	}

	.mark-all-read-btn {
		display: flex;
		align-items: center;
		font-weight: 500;
		font-size: 13px;
		color: $color-primary;
		padding: 6px 12px;
		background: $bg-color-info;
		border-radius: 6px;

		.cuIcon-check {
			font-size: 14px;
			margin-right: 4px;
		}

		&:active {
			opacity: 0.7;
			transform: scale(0.98);
		}
	}

	/* 消息过滤标签 */
	.filter-tabs {
		display: flex;
		background-color: white;
		padding: 0 20px;
		border-top: 1px solid #E5E7EB;
		border-bottom: 1px solid #E5E7EB;
		box-shadow: 0px 2px 4px rgba(0, 0, 0, 0.05);
		flex-shrink: 0;
	}

	.tab-item {
		flex: 1;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		padding: 12px 0;
		position: relative;

		&:active {
			opacity: 0.7;
		}
	}

	.tab-text {
		font-weight: 500;
		font-size: 14px;
		color: #8B8891;

		.tab-item.active & {
			color: $color-primary;
			font-weight: 700;
		}
	}

	.tab-underline {
		position: absolute;
		bottom: 0;
		left: 50%;
		transform: translateX(-50%);
		width: 40px;
		height: 3px;
		background: $color-primary;
		border-radius: 2px 2px 0 0;
		animation: slideIn 0.2s ease-out;
	}

	@keyframes slideIn {
		from {
			width: 0;
		}

		to {
			width: 40px;
		}
	}

	.tab-badge {
		position: absolute;
		top: 5px;
		right: calc(50% - 45px);
		background: #E52626;
		color: white;
		width: 18px;
		height: 18px;
		min-width: 18px;
		font-size: 8px;
		font-weight: 600;
		padding: 0;
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
		text-align: center;
		line-height: 1;
		white-space: nowrap;
		box-sizing: border-box;
	}

	.message-scroll {
		flex: 1;
		height: 0;
		min-height: 0;
		background-color: #E1E1E1;
	}

	.message-list {
		display: flex;
		flex-direction: column;
		gap: 12px;
		padding: 12px 14px;
	}

	.message-card {
		background: #FFFFFF;
		border-radius: 12px;
		overflow: visible;
		box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
		transition: all 0.3s ease;
		position: relative;

		&.unread-card {
			background: linear-gradient(135deg, #E8F0FE 0%, #F5F9FF 50%, #FFFFFF 100%);
			box-shadow: 0 2px 16px rgba(47, 93, 98, 0.25);
			border: 1px solid rgba(47, 93, 98, 0.1);

			.card-header {
				background: $color-primary;
				font-weight: 700;
			}

			.message-title {
				font-weight: 700;
				color: $color-primary;
			}

			.message-description {
				color: #4B5563;
				font-weight: 500;
			}
		}

		&:active {
			transform: translateY(-2px) scale(0.98);
			box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
		}
	}

	.unread-indicator {
		position: absolute;
		left: 0;
		top: 0;
		bottom: 0;
		width: 6px;
		background: $color-secondary;
		border-radius: 12px 0 0 12px;
		animation: pulse 2s ease-in-out infinite;
		box-shadow: 2px 0 8px rgba(95, 181, 189, 0.5);
	}

	@keyframes pulse {

		0%,
		100% {
			opacity: 1;
			width: 6px;
		}

		50% {
			opacity: 0.9;
			width: 8px;
		}
	}

	.card-header {
		background: $color-primary;
		padding: 8px 16px;
		display: flex;
		justify-content: space-between;
		align-items: center;
		position: relative;
		border-start-start-radius: 8px;
		border-start-end-radius: 8px;
	}

	.header-text {
		color: #FFFFFF;
		font-size: 11px;
		font-weight: 600;
		opacity: 0.9;
		letter-spacing: 0.3px;
	}

	.message-time {
		color: rgba(255, 255, 255, 0.7);
		font-size: 10px;
		font-weight: 500;
	}

	.card-body {
		padding: 12px 16px;
		background: transparent;
	}

	.message-title {
		font-weight: 600;
		font-size: 13px;
		line-height: 1.4;
		color: $color-primary;
		display: block;
		margin-bottom: 6px;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.message-description {
		font-weight: 400;
		font-size: 12px;
		line-height: 1.5;
		color: #6B7280;
		display: -webkit-box;
		-webkit-line-clamp: 2;
		-webkit-box-orient: vertical;
		overflow: hidden;
		text-overflow: ellipsis;
	}

	.loading-container {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		padding: 40px 0;
		background-color: #E1E1E1;
	}

	.loading-spinner {
		width: 20px;
		height: 20px;
		border: 2px solid #EDEDED;
		border-top: 2px solid $color-primary;
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

	.no-messages {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		padding: 60px 0;
		color: #999999;
	}

	.no-messages-text {
		font-size: 16px;
		color: #666666;
		margin-bottom: 8px;
	}

	.no-messages-tip {
		font-size: 14px;
		color: #999999;
		text-align: center;
	}

	/* 弹窗样式 */
	.modal-overlay {
		position: fixed;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		background: rgba(0, 0, 0, 0.5);
		display: flex;
		align-items: center;
		justify-content: center;
		z-index: 9999;
		padding: 20px;
	}

	.modal-content {
		background: #FFFFFF;
		border-radius: 16px;
		width: 100%;
		max-width: 500px;
		max-height: 80vh;
		display: flex;
		flex-direction: column;
		overflow: hidden;
	}

	.modal-header {
		padding: 10px 20px;
		border-bottom: 1px solid #E5E7EB;
		display: flex;
		justify-content: space-between;
		align-items: center;
	}

	.modal-title {
		font-size: 18px;
		font-weight: 600;
		color: #1F2937;
	}

	.cuIcon-close {
		font-size: 24px;
		color: #6B7280;
	}

	.modal-body {
		flex: 1;
		padding: 20px;
		overflow-y: auto;
	}

	.detail-section {
		margin-bottom: 20px;

		&:last-child {
			margin-bottom: 0;
		}
	}

	.detail-item {
		display: flex;
		justify-content: space-between;

		&:last-child {
			margin-bottom: 0;
		}
	}

	.detail-label {
		font-size: 14px;
		font-weight: 600;
		color: #6B7280;
		display: block;
	}

	.detail-value {
		font-size: 12px;
		color: #1F2937;
		text-align: right;
	}

	.detail-title-text {
		font-size: 16px;
		font-weight: 600;
		color: $color-primary;
		line-height: 1.5;
		display: block;
		margin-top: 8px;
	}

	.detail-content-text {
		font-size: 15px;
		color: $color-primary;
		line-height: 1.6;
		display: block;
		margin-top: 8px;
		white-space: pre-wrap;
		word-wrap: break-word;
	}

	.detail-divider {
		height: 1px;
		background: #E5E7EB;
		margin: 16px 0;
	}

	.modal-footer {
		padding: 16px 20px;
		border-top: 1px solid #E5E7EB;
		display: flex;
		gap: 12px;
	}

	.modal-btn {
		flex: 1;
		padding: 8px 16px;
		border-radius: 8px;
		text-align: center;
		transition: all 0.2s;

		&:active {
			transform: scale(0.98);
		}
	}

	.primary-btn {
		background: $color-primary;

		.btn-text {
			color: #FFFFFF;
			font-weight: 600;
			font-size: 14px;
		}

		&:active {
			background: #244a4e;
		}
	}

	.btn-text {
		display: block;
	}

	/* Mark All Read 自定义确认弹窗 */
	.confirm-modal {
		background: #FFFFFF;
		border-radius: 16px;
		width: 100%;
		max-width: 340px;
		display: flex;
		flex-direction: column;
		overflow: hidden;
	}

	.confirm-header {
		padding: 18px 20px 6px;
		text-align: center;
	}

	.confirm-title {
		font-size: 17px;
		font-weight: 700;
		color: $color-primary;
		line-height: 1.5;
		word-break: break-word;
		white-space: normal;
	}

	.confirm-body {
		padding: 8px 20px 20px;
	}

	.confirm-message {
		display: block;
		font-size: 15px;
		font-weight: 400;
		color: #4B5563;
		line-height: 1.6;
		text-align: center;
		word-break: break-word;
		white-space: normal;
	}

	.confirm-footer {
		display: flex;
		flex-direction: row;
		gap: 12px;
		padding: 0 20px 20px;
	}

	.confirm-btn {
		flex: 1;
		padding: 10px 12px;
		border-radius: 10px;
		text-align: center;
		transition: all 0.2s;

		&:active {
			transform: scale(0.98);
		}
	}

	.cancel-btn {
		background: #FFFFFF;
		border: 1px solid $color-primary;
	}

	.ok-btn {
		background: $color-primary;

		&:active {
			background: #244a4e;
		}
	}

	.confirm-btn-text {
		display: block;
		font-size: 15px;
		font-weight: 600;
	}

	.cancel-text {
		color: #C8434C;
	}

	.ok-text {
		color: #FFFFFF;
	}
</style>