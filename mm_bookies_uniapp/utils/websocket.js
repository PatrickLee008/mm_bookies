/**
 * UniApp WebSocket Manager
 * Maps to Java backend PushWebSocket: /ws/push/{userId}
 */
import siteinfo from '../siteinfo.js'
class WebSocketManager {
  constructor() {
    this.socketTask = null
    this.url = ''
    this.isConnected = false
    this.reconnectTimer = null
    this.reconnectCount = 0
    this.maxReconnectCount = 5
    this.reconnectInterval = 3000
    this.heartbeatTimer = null
    this.heartbeatInterval = 30000
    this.userId = null
    this.messageHandlers = []
    this.connectionStartTime = null
  }

  /**
   * Connect to WebSocket
   * @param {String} userId User ID
   * @param {String} token Authentication token
   */
  connect(userId, token) {
    if (this.isConnected) {
      return
    }

    if (!userId) {
      // console.error('[WebSocket] User ID is required')
      return
    }

    this.userId = userId
    this.url = `${siteinfo.wsUrl}/ws/push/${userId}?token=${token || ''}`
    
     // console.log(`[WebSocket] Connecting user: ${userId}`)

    try {
      this.socketTask = uni.connectSocket({
        url: this.url,
        success: () => {
          // Connection request sent successfully
        },
        fail: (err) => {
          // console.error('[WebSocket] Connection request failed:', err)
          this.handleReconnect()
        }
      })

      this.setupEventListeners()
    } catch (error) {
      // console.error('[WebSocket] Connection exception:', error)
      this.handleReconnect()
    }
  }

  /**
   * 设置事件监听器
   */
  setupEventListeners() {
    if (!this.socketTask) return

    // 连接打开事件
    this.socketTask.onOpen((res) => {
      // console.log('[WebSocket] Connection opened for user:', this.userId)
      this.isConnected = true
      this.reconnectCount = 0
      this.connectionStartTime = Date.now()
      this.startHeartbeat()
      
      // 通知连接成功
      uni.$emit('websocket:connected', { userId: this.userId })
      this.triggerHandlers('connected', res)
    })

    // 接收消息事件
    this.socketTask.onMessage((res) => {
      this.handleMessage(res.data)
    })

    // 连接关闭事件
    this.socketTask.onClose((res) => {
      // console.log('[WebSocket] Connection closed:', res)
      this.isConnected = false
      this.connectionStartTime = null
      this.stopHeartbeat()
      
      // 通知连接关闭
      uni.$emit('websocket:disconnected', res)
      this.triggerHandlers('disconnected', res)
      
      // 非主动关闭时重连
      if (res.code !== 1000 && res.code !== 1001) {
        this.handleReconnect()
      }
    })

    // 连接错误事件
    this.socketTask.onError((res) => {
      // console.error('[WebSocket] Connection error:', res)
      this.isConnected = false
      this.connectionStartTime = null
      
      // 通知连接错误
      uni.$emit('websocket:error', res)
      this.triggerHandlers('error', res)
      
      this.handleReconnect()
    })
  }

  /**
   * 处理接收到的消息
   * @param {String} data 消息数据
   */
  handleMessage(data) {
    try {
      const message = typeof data === 'string' ? JSON.parse(data) : data
      
      // 处理心跳响应
      if (message.type === 'heartbeat' || message.title === 'Heartbeat') {
        return
      }
      
      // 处理Java后端消息格式
      if (message.title && message.content) {
        this.processServerMessage(message)
      }
      
      // 触发消息处理器
      this.triggerHandlers('message', message)
      
    } catch (error) {
      // console.error('[WebSocket] Message parsing failed:', error)
    }
  }

  /**
   * 处理服务器推送的消息
   * @param {Object} message 服务器消息 
   */
  processServerMessage(message) {
    const { title, content, payload, data, timestamp, type, action } = message
    
    // 处理payload数据，优先使用data字段（广播消息），然后使用payload字段
    const actualPayload = data || payload
    
    // 智能判断消息类型
    let messageType = 'NOTIFICATION' // 默认为通知类型，确保显示弹窗
    
    // 从多个字段推断消息类型
    if (type) {
      // 根据Java后端的type字段判断
      if (type === 'MESSAGE' && action === 'BROADCAST') {
        messageType = 'BROADCAST'
      } else if (type === 'NOTIFICATION') {
        messageType = 'NOTIFICATION'
      } else if (type === 'MESSAGE') {
        // MESSAGE类型也显示为NOTIFICATION，确保用户看到弹窗
        messageType = 'NOTIFICATION'
      } else {
        messageType = type.toUpperCase()
      }
    } else if (actualPayload?.messageType) {
      // 从payload获取消息类型
      if (actualPayload.messageType === 'NOTIFICATION') {
        messageType = 'NOTIFICATION'
      } else if (actualPayload.messageType === 'MESSAGE') {
        // MESSAGE类型也显示为NOTIFICATION，确保用户看到弹窗
        messageType = 'NOTIFICATION'
      } else {
        messageType = actualPayload.messageType
      }
    } else if (title || content) {
      // 如果有标题或内容，默认为通知类型，确保会显示弹窗
      messageType = 'NOTIFICATION'
    }
    
    // 构建标准化消息对象
    const standardMessage = {
      id: this.generateMessageId(),
      messageId: actualPayload?.messageId || this.generateMessageId(),
      userId: this.userId,
      title,
      content,
      pushType: this.getPushTypeFromPayload(actualPayload),
      messageType: messageType,
      payload: actualPayload,
      timestamp: timestamp || Date.now(),
      isRead: false,
      receivedAt: Date.now(),
      deviceToken: this.getDeviceInfo().deviceId,
      source: 'JAVA_BACKEND',
      status: 1 // 已推送
    }
    
    // console.log('[WebSocket] Processing message:', messageType, title)
    
    // 保存到本地存储
    this.saveMessageToLocal(standardMessage)
    
    // 根据推送类型分发消息
    this.dispatchMessageByType(standardMessage)
  }

  /**
   * 根据payload获取推送类型
   */
  getPushTypeFromPayload(payload) {
    if (!payload) return 2 // 默认消息类型
    
    switch (payload.messageType) {
      case 'SYSTEM':
      case 'NOTIFICATION':
        return 1 // 通知类型
      case 'BROADCAST':
        return 2 // 广播消息类型
      default:
        return 2 // 消息类型
    }
  }

  /**
   * 根据类型分发消息
   * @param {Object} message 消息对象
   */
  dispatchMessageByType(message) {
    const { pushType, messageType, payload } = message
    
    // 根据消息类型进行不同的UI处理
    switch (messageType) {
      case 'SYSTEM':
        // 系统消息：静默处理，不显示UI提示
        // System message processed silently
        break
        
      case 'BROADCAST':
        // 广播消息：显示Toast提示
        this.showBroadcastMessage(message)
        break
        
      case 'NOTIFICATION':
        // 通知消息：显示通知并更新角标
        this.showNotification(message)
        
        // 处理跳转逻辑
        if (payload?.targetPage) {
          this.handlePageNavigation(payload.targetPage, message)
        }
        break
        
      case 'MESSAGE':
        // 普通消息：显示通知弹窗和更新角标
        this.showNotification(message)
        break
        
      default:
        // 其他类型消息：更新角标即可
        this.updateBadge()
    }
    
    // 发出事件供其他组件监听（保持向后兼容）
    uni.$emit(`websocket:${messageType.toLowerCase()}`, message)
  }

  /**
   * 显示通知消息
   * @param {Object} message 消息对象
   */
  showNotification(message) {
    // console.log('[WebSocket] Showing notification:', message.title)
    
    // 先显示Toast提示
    uni.showToast({
      title: message.title || 'New message',
      icon: 'none',
      duration: 3000
    })

    // 更新应用角标
    this.updateBadge()
    
    // 如果有内容，延迟显示Modal弹窗，让用户看到详细信息
    if (message.content && message.content.trim()) {
      setTimeout(() => {
        uni.showModal({
          title: message.title || 'New message',
          content: message.content,
          showCancel: true,
          cancelText: 'Cancel',
          confirmText: 'View detail',
          success: (res) => {
            if (res.confirm) {
              // 用户选择查看详情，可以跳转到消息页面
              this.navigateToMessagePage(message)
            }
            // 无论如何都标记为已读
            this.markMessageAsRead(message.messageId)
          }
        })
      }, 1500) // 延迟1.5秒显示，让Toast先显示完
    }
  }

  /**
   * 显示广播消息
   * @param {Object} message 消息对象
   */
  showBroadcastMessage(message) {
    if (message.title && message.content) {
      uni.showToast({
        title: message.title,
        icon: 'none',
        duration: 3000
      })
    }
  }

  /**
   * 处理页面跳转
   * @param {String} targetPage 目标页面
   * @param {Object} message 消息对象
   */
  handlePageNavigation(targetPage, message) {
    setTimeout(() => {
      uni.showModal({
        title: 'Message',
        content: `New message: ${message.title}. View now?`,
        success: (res) => {
          if (res.confirm) {
            try {
              uni.navigateTo({
                url: targetPage,
                fail: () => {
                  uni.switchTab({ url: targetPage })
                }
              })
            } catch (error) {
              console.warn('[WebSocket] 页面跳转失败:', error)
            }
          }
        }
      })
    }, 1000)
  }

  /**
   * 跳转到消息页面
   * @param {Object} message 消息对象
   */
  navigateToMessagePage(message) {
    try {
      // console.log('[WebSocket] Navigating to message detail page:', message.title)
      
      // 构建消息数据用于传递
      const messageData = {
        id: message.messageId || message.id,
        messageId: message.messageId || message.id,
        title: message.title || 'Push Message',
        content: message.content || '',
        timestamp: message.timestamp || Date.now(),
        isRead: message.isRead || false,
        type: message.messageType || message.type || 'notification',
        source: message.source || 'JAVA_BACKEND',
        icon: '/static/icon/messages.png'
      }
      
      // 跳转到消息详情页面
      uni.navigateTo({
        url: `/pages/ucenter/messageDetail?messageData=${encodeURIComponent(JSON.stringify(messageData))}`,
        success: () => {
          // Navigation successful
        },
        fail: (error) => {
          // console.error('[WebSocket] Failed to navigate to message detail:', error)
          
          // 如果跳转失败，尝试跳转到消息列表页面
          uni.navigateTo({
            url: '/pages/ucenter/message',
            fail: (error2) => {
              // console.error('[WebSocket] Failed to navigate to message list:', error2)
              
              // 显示错误提示
              // uni.showToast({
              //   title: 'Page navigation failed',
              //   icon: 'none'
              // })
            }
          })
        }
      })
    } catch (error) {
      // console.error('[WebSocket] Navigation to message page error:', error)
      
      // 显示错误提示
      // uni.showToast({
      //   title: 'Navigation error',
      //   icon: 'none'
      // })
    }
  }

  /**
   * 更新应用角标
   */
  updateBadge() {
    try {
      const unreadCount = this.getUnreadMessageCount()
      
      // 设置TabBar角标
      if (unreadCount > 0) {
        uni.setTabBarBadge({
          index: 3, // 假设消息在第4个tab
          text: unreadCount > 99 ? '99+' : unreadCount.toString()
        })
      } else {
        uni.removeTabBarBadge({ index: 3 })
      }

      // APP端设置应用角标
      // #ifdef APP-PLUS
      if (unreadCount > 0) {
        plus.runtime.setBadgeNumber(unreadCount)
      } else {
        plus.runtime.setBadgeNumber(0)
      }
      // #endif
    } catch (error) {
      console.warn('[WebSocket] Update badge failed:', error)
    }
  }

  /**
   * 保存消息到本地存储
   * @param {Object} message 消息对象
   */
  saveMessageToLocal(message) {
    try {
      // 过滤SYSTEM类型的消息，不保存到本地存储
      if (message.messageType === 'SYSTEM') {
        return
      }
      
      const storageKey = 'websocket_messages'
      const existingMessages = uni.getStorageSync(storageKey) || []
      
      // 检查消息是否已存在
      const exists = existingMessages.find(m => 
        m.messageId === message.messageId || 
        (m.timestamp === message.timestamp && m.title === message.title)
      )
      
      if (exists) {
        return
      }
      
      // 添加到列表开头
      existingMessages.unshift(message)
      
      // 限制消息数量
      if (existingMessages.length > 1000) {
        existingMessages.splice(1000)
      }
      
      // 保存到本地存储
      uni.setStorageSync(storageKey, existingMessages)
      uni.setStorageSync('last_message_time', Date.now())
      
      // Message saved to local storage
      
      // 广播消息保存事件（仅非SYSTEM消息）
      uni.$emit('websocket:messageSaved', message)
      
    } catch (error) {
      // console.error('[WebSocket] Save message failed:', error)
    }
  }


  /**
   * 发送消息到服务器
   * @param {Object|String} message 消息内容
   */
  send(message) {
    if (!this.isConnected || !this.socketTask) {
      console.warn('[WebSocket] Not connected, cannot send message')
      return false
    }

    try {
      const messageData = typeof message === 'object' ? JSON.stringify(message) : message
      
      this.socketTask.send({
        data: messageData,
        success: () => {
          // Message sent successfully
        },
        fail: (err) => {
          // console.error('[WebSocket] Message send failed:', err)
        }
      })
      
      return true
    } catch (error) {
      // console.error('[WebSocket] Send message exception:', error)
      return false
    }
  }

  /**
   * 开始心跳检测
   */
  startHeartbeat() {
    this.stopHeartbeat()
    this.heartbeatTimer = setInterval(() => {
      if (this.isConnected) {
        this.send({
          type: 'heartbeat',
          userId: this.userId,
          timestamp: Date.now()
        })
      }
    }, this.heartbeatInterval)
  }

  /**
   * 停止心跳检测
   */
  stopHeartbeat() {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer)
      this.heartbeatTimer = null
    }
  }

  /**
   * 处理重连
   */
  handleReconnect() {
    if (this.reconnectCount >= this.maxReconnectCount) {
      // console.log('[WebSocket] Max reconnection attempts reached, stopping')
      // uni.showToast({
      //   title: 'Network connection failed',
      //   icon: 'none'
      // })
      return
    }

    this.reconnectCount++
    // console.log(`[WebSocket] Reconnecting attempt ${this.reconnectCount}...`)

    this.reconnectTimer = setTimeout(() => {
      if (this.userId) {
        const websocketToken = uni.getStorageSync('websocketToken') || ''
        this.connect(this.userId, websocketToken)
      }
    }, this.reconnectInterval)
  }

  /**
   * 关闭连接
   */
  close() {
    // console.log('[WebSocket] Manually closing connection')
    
    if (this.socketTask) {
      this.socketTask.close({
        code: 1000,
        reason: 'Manual close'
      })
    }
    
    this.cleanup()
  }

  /**
   * 清理资源
   */
  cleanup() {
    this.isConnected = false
    this.connectionStartTime = null
    this.userId = null
    this.stopHeartbeat()
    
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }
    
    this.messageHandlers = []
  }

  /**
   * 注册事件处理器
   * @param {String} event 事件名称
   * @param {Function} handler 处理函数
   */
  on(event, handler) {
    this.messageHandlers.push({ event, handler })
  }

  /**
   * 触发事件处理器
   * @param {String} event 事件名称
   * @param {*} data 事件数据
   */
  triggerHandlers(event, data) {
    this.messageHandlers
      .filter(h => h.event === event)
      .forEach(h => {
        try {
          h.handler(data)
        } catch (error) {
          // console.error(`[WebSocket] 事件处理器错误 [${event}]:`, error)
        }
      })
  }

  /**
   * 获取未读消息数量（排除SYSTEM消息）
   */
  getUnreadMessageCount() {
    try {
      const messages = uni.getStorageSync('websocket_messages') || []
      // 过滤掉SYSTEM消息，只统计非系统消息的未读数量
      return messages
        .filter(m => m.messageType !== 'SYSTEM')
        .filter(m => !m.isRead)
        .length
    } catch (error) {
      return 0
    }
  }

  /**
   * 生成消息ID
   */
  generateMessageId() {
    return Date.now() + '_' + Math.random().toString(36).substr(2, 9)
  }

  /**
   * 获取设备信息
   */
  getDeviceInfo() {
    try {
      const systemInfo = uni.getSystemInfoSync()
      return {
        deviceId: systemInfo.deviceId || this.generateMessageId(),
        platform: systemInfo.platform,
        system: systemInfo.system,
        version: systemInfo.version,
        model: systemInfo.model
      }
    } catch (error) {
      return {
        deviceId: this.generateMessageId(),
        platform: 'unknown'
      }
    }
  }

  /**
   * 获取连接状态
   */
  getStatus() {
    return {
      isConnected: this.isConnected,
      userId: this.userId,
      reconnectCount: this.reconnectCount,
      connectionDuration: this.connectionStartTime ? Date.now() - this.connectionStartTime : 0
    }
  }

  /**
   * 手动更新消息角标（供外部调用）
   */
  refreshBadge() {
    this.updateBadge()
  }

  /**
   * 标记消息为已读
   * @param {String} messageId 消息ID
   */
  markMessageAsRead(messageId) {
    try {
      const messages = uni.getStorageSync('websocket_messages') || []
      const messageIndex = messages.findIndex(m => m.messageId === messageId)
      
      if (messageIndex !== -1) {
        messages[messageIndex].isRead = true
        uni.setStorageSync('websocket_messages', messages)
        
        // 更新角标
        this.updateBadge()
        
        // console.log('[WebSocket] Message marked as read:', messageId)
        return true
      }
      
      return false
    } catch (error) {
      // console.error('[WebSocket] Mark message as read failed:', error)
      return false
    }
  }

  /**
   * 批量标记消息为已读
   * @param {Array} messageIds 消息ID数组
   */
  markMessagesAsRead(messageIds) {
    try {
      const messages = uni.getStorageSync('websocket_messages') || []
      let updatedCount = 0
      
      messages.forEach(message => {
        if (messageIds.includes(message.messageId) && !message.isRead) {
          message.isRead = true
          updatedCount++
        }
      })
      
      if (updatedCount > 0) {
        uni.setStorageSync('websocket_messages', messages)
        this.updateBadge()
        // console.log(`[WebSocket] Marked ${updatedCount} messages as read`)
      }
      
      return updatedCount
    } catch (error) {
      // console.error('[WebSocket] Bulk mark messages as read failed:', error)
      return 0
    }
  }

  /**
   * 获取消息列表
   * @param {Object} options 查询选项
   */
  getMessages(options = {}) {
    try {
      const messages = uni.getStorageSync('websocket_messages') || []
      let filteredMessages = messages
      
      // 按消息类型过滤
      if (options.messageType) {
        filteredMessages = filteredMessages.filter(m => m.messageType === options.messageType)
      }
      
      // 按已读状态过滤
      if (typeof options.isRead === 'boolean') {
        filteredMessages = filteredMessages.filter(m => m.isRead === options.isRead)
      }
      
      // 分页
      if (options.page && options.pageSize) {
        const start = (options.page - 1) * options.pageSize
        filteredMessages = filteredMessages.slice(start, start + options.pageSize)
      }
      
      return {
        messages: filteredMessages,
        totalCount: messages.length,
        unreadCount: this.getUnreadMessageCount()
      }
    } catch (error) {
      // console.error('[WebSocket] 获取消息列表失败:', error)
      return {
        messages: [],
        totalCount: 0,
        unreadCount: 0
      }
    }
  }
}

// 创建全局WebSocket实例
const websocketManager = new WebSocketManager()

export default websocketManager