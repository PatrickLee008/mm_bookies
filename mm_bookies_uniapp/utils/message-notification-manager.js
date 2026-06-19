/**
 * 消息通知管理器
 * 用于控制全局消息通知组件的显示
 */

class MessageNotificationManager {
	constructor() {
		this.instance = null
		this.messageQueue = []
		this.isShowing = false
	}

	/**
	 * 设置组件实例
	 * @param {Object} instance 组件实例
	 */
	setInstance(instance) {
		this.instance = instance

		// 如果有待显示的消息，立即显示
		if (this.messageQueue.length > 0) {
			// 重置显示状态，确保能够正常显示
			this.isShowing = false
			// 延迟一小段时间，确保组件完全准备好
			setTimeout(() => {
				this.showNext()
			}, 100)
		}
	}

	/**
	 * 显示消息通知
	 * @param {Array|Object} messages 消息或消息数组
	 */
	show(messages) {
		const messageArray = Array.isArray(messages) ? messages : [messages]

		// 如果当前正在显示通知且实例存在，动态添加到当前显示的消息列表
		if (this.isShowing && this.instance) {
			this.instance.addMessages(messageArray)
		} else {
			// 将消息添加到队列
			this.messageQueue.push(...messageArray)

			// 如果当前没有显示通知，则尝试显示
			if (!this.isShowing) {
				this.showNext()
			}
		}
	}

	/**
	 * 显示队列中的下一批消息
	 * @param {Number} retryCount 重试次数（内部使用）
	 */
	showNext(retryCount = 0) {
		if (this.messageQueue.length === 0) {
			this.isShowing = false
			return
		}

		if (!this.instance) {
			// 如果重试次数未超过限制，延迟重试
			if (retryCount < 3) {
				setTimeout(() => {
					this.showNext(retryCount + 1)
				}, 500)
			} else {
				this.isShowing = false
			}
			return
		}

		// 取出队列中的所有消息（一次性显示）
		const messagesToShow = this.messageQueue.splice(0, this.messageQueue.length)

		this.isShowing = true
		this.instance.show(messagesToShow)
	}

	/**
	 * 隐藏消息通知
	 */
	hide() {
		if (this.instance) {
			this.instance.hide()
		}
		this.isShowing = false
	}

	/**
	 * 清空消息队列
	 */
	clearQueue() {
		this.messageQueue = []
	}

	/**
	 * 获取队列长度
	 */
	getQueueLength() {
		return this.messageQueue.length
	}
}

// 创建全局单例
const messageNotificationManager = new MessageNotificationManager()

export default messageNotificationManager
