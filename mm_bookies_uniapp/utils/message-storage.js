/**
 * 消息存储管理工具
 * 对应Java后端MAppMessage实体类
 */
class MessageStorage {
  constructor() {
    this.storageKey = 'websocket_messages'
    this.maxMessages = 1000
    this.syncUrl = 'http://localhost:5000/api/websocket/messages'
  }

  /**
   * 保存消息到本地存储
   * @param {Object} message 消息对象
   */
  saveMessage(message) {
    try {
      const messages = this.getMessages()
      
      // 检查消息是否已存在
      const exists = messages.find(m => 
        m.messageId === message.messageId || 
        (m.timestamp === message.timestamp && m.title === message.title)
      )
      
      if (exists) {
        return false
      }
      
      // 添加到列表开头
      messages.unshift(message)
      
      // 限制消息数量
      if (messages.length > this.maxMessages) {
        messages.splice(this.maxMessages)
      }
      
      // 保存到本地存储
      uni.setStorageSync(this.storageKey, messages)
      
      // 更新未读计数
      this.updateUnreadCount()
      
      return true
      
    } catch (error) {
      console.error('[MessageStorage] 保存消息失败:', error)
      return false
    }
  }

  /**
   * 获取消息列表
   * @param {Object} options 查询选项
   */
  getMessages(options = {}) {
    try {
      let messages = uni.getStorageSync(this.storageKey) || []
      
      // 过滤选项
      if (options.userId) {
        messages = messages.filter(m => m.userId === options.userId)
      }
      
      if (options.isRead !== undefined) {
        messages = messages.filter(m => m.isRead === options.isRead)
      }
      
      if (options.pushType) {
        messages = messages.filter(m => m.pushType === options.pushType)
      }
      
      if (options.messageType) {
        messages = messages.filter(m => m.messageType === options.messageType)
      }
      
      if (options.keyword) {
        const keyword = options.keyword.toLowerCase()
        messages = messages.filter(m => 
          (m.title && m.title.toLowerCase().includes(keyword)) ||
          (m.content && m.content.toLowerCase().includes(keyword))
        )
      }
      
      // 时间范围筛选
      if (options.startDate) {
        messages = messages.filter(m => m.timestamp >= options.startDate)
      }
      
      if (options.endDate) {
        messages = messages.filter(m => m.timestamp <= options.endDate)
      }
      
      // 分页
      if (options.page && options.pageSize) {
        const start = (options.page - 1) * options.pageSize
        const end = start + options.pageSize
        messages = messages.slice(start, end)
      }
      
      // 排序（默认按时间倒序）
      messages.sort((a, b) => b.timestamp - a.timestamp)
      
      return messages
    } catch (error) {
      console.error('[MessageStorage] 获取消息失败:', error)
      return []
    }
  }

  /**
   * 根据ID获取单个消息
   * @param {String} messageId 消息ID
   */
  getMessageById(messageId) {
    try {
      const messages = this.getMessages()
      return messages.find(m => m.messageId === messageId) || null
    } catch (error) {
      return null
    }
  }

  /**
   * 标记消息为已读
   * @param {String|Array} messageIds 消息ID或ID数组
   */
  markAsRead(messageIds) {
    try {
      const messages = this.getMessages()
      const ids = Array.isArray(messageIds) ? messageIds : [messageIds]
      let updated = false
      
      messages.forEach(message => {
        if (ids.includes(message.messageId) && !message.isRead) {
          message.isRead = true
          message.readAt = Date.now()
          updated = true
        }
      })
      
      if (updated) {
        uni.setStorageSync(this.storageKey, messages)
        this.updateUnreadCount()
      }
      
      return updated
    } catch (error) {
      return false
    }
  }

  /**
   * 标记所有消息为已读
   */
  markAllAsRead() {
    try {
      const messages = this.getMessages()
      let updated = false
      
      messages.forEach(message => {
        if (!message.isRead) {
          message.isRead = true
          message.readAt = Date.now()
          updated = true
        }
      })
      
      if (updated) {
        uni.setStorageSync(this.storageKey, messages)
        this.updateUnreadCount()
      }
      
      return updated
    } catch (error) {
      return false
    }
  }

  /**
   * 删除消息
   * @param {String|Array} messageIds 消息ID或ID数组
   */
  deleteMessages(messageIds) {
    try {
      const messages = this.getMessages()
      const ids = Array.isArray(messageIds) ? messageIds : [messageIds]
      
      const filteredMessages = messages.filter(m => !ids.includes(m.messageId))
      
      if (filteredMessages.length !== messages.length) {
        uni.setStorageSync(this.storageKey, filteredMessages)
        this.updateUnreadCount()
        return true
      }
      
      return false
    } catch (error) {
      return false
    }
  }

  /**
   * 清空所有消息
   */
  clearAllMessages() {
    try {
      uni.removeStorageSync(this.storageKey)
      uni.removeStorageSync('unread_message_count')
      return true
    } catch (error) {
      return false
    }
  }

  /**
   * 获取消息统计信息
   * @param {String} userId 用户ID（可选）
   */
  getStatistics(userId = null) {
    try {
      let messages = this.getMessages()
      
      if (userId) {
        messages = messages.filter(m => m.userId === userId)
      }
      
      const now = new Date()
      const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())
      const week = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000)
      
      const stats = {
        totalCount: messages.length,
        unreadCount: messages.filter(m => !m.isRead).length,
        readCount: messages.filter(m => m.isRead).length,
        
        // 按推送类型统计
        notificationCount: messages.filter(m => m.pushType === 1).length,  // 通知类型
        messageCount: messages.filter(m => m.pushType === 2).length,       // 消息类型
        
        // 按消息类型统计
        systemCount: messages.filter(m => m.messageType === 'SYSTEM').length,
        broadcastCount: messages.filter(m => m.messageType === 'BROADCAST').length,
        
        // 时间统计
        todayCount: messages.filter(m => m.timestamp >= today.getTime()).length,
        weekCount: messages.filter(m => m.timestamp >= week.getTime()).length,
        
        // 计算阅读率
        readRate: messages.length > 0 ? ((messages.filter(m => m.isRead).length / messages.length) * 100).toFixed(2) : 0
      }
      
      return stats
    } catch (error) {
      return {
        totalCount: 0,
        unreadCount: 0,
        readCount: 0,
        notificationCount: 0,
        messageCount: 0,
        systemCount: 0,
        broadcastCount: 0,
        todayCount: 0,
        weekCount: 0,
        readRate: 0
      }
    }
  }

  /**
   * 更新未读消息数量
   */
  updateUnreadCount() {
    try {
      const unreadCount = this.getStatistics().unreadCount
      uni.setStorageSync('unread_message_count', unreadCount)
      
      // 发送未读数量变更事件
      uni.$emit('unreadCountChanged', unreadCount)
      
    } catch (error) {
    }
  }

  /**
   * 获取未读消息数量
   */
  getUnreadCount() {
    try {
      return uni.getStorageSync('unread_message_count') || 0
    } catch (error) {
      return 0
    }
  }

  /**
   * 搜索消息
   * @param {String} keyword 搜索关键词
   * @param {Object} options 搜索选项
   */
  searchMessages(keyword, options = {}) {
    return this.getMessages({
      ...options,
      keyword
    })
  }

  /**
   * 清理过期消息
   * @param {Number} daysToKeep 保留天数，默认30天
   */
  cleanupExpiredMessages(daysToKeep = 30) {
    try {
      const messages = this.getMessages()
      const expiredTime = Date.now() - (daysToKeep * 24 * 60 * 60 * 1000)
      
      const validMessages = messages.filter(m => m.timestamp > expiredTime)
      
      if (validMessages.length !== messages.length) {
        uni.setStorageSync(this.storageKey, validMessages)
        this.updateUnreadCount()
        
        const deletedCount = messages.length - validMessages.length        
        return deletedCount
      }
      
      return 0
    } catch (error) {
      return 0
    }
  }

  /**
   * 导出消息数据
   */
  exportMessages() {
    try {
      const messages = this.getMessages()
      const stats = this.getStatistics()
      
      return {
        exportTime: new Date().toISOString(),
        statistics: stats,
        messages: messages.map(msg => ({
          messageId: msg.messageId,
          title: msg.title,
          content: msg.content,
          pushType: msg.pushType,
          messageType: msg.messageType,
          timestamp: msg.timestamp,
          isRead: msg.isRead,
          receivedAt: new Date(msg.receivedAt).toISOString()
        }))
      }
    } catch (error) {
      return null
    }
  }

  /**
   * 同步消息到Python服务器
   * @param {Object} message 消息对象
   */
  async syncToServer(message) {
    try {
      const response = await uni.request({
        url: this.syncUrl,
        method: 'POST',
        header: { 'Content-Type': 'application/json' },
        data: {
          message_id: message.messageId,
          user_id: message.userId,
          title: message.title,
          content: message.content,
          push_type: message.pushType,
          device_token: message.deviceToken,
          status: message.status || 1,  // 已推送状态
          push_time: new Date(message.timestamp).toISOString(),
          remarks: message.payload ? JSON.stringify(message.payload) : null
        }
      })

      if (response.statusCode === 200 && response.data.code === 20000) {
        return true
      } else {
        return false
      }
    } catch (error) {
      return false
    }
  }
}

// 创建全局消息存储实例
const messageStorage = new MessageStorage()

export default messageStorage