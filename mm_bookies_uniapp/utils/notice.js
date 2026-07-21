// 全局通知管理器
class NoticeManager {
	constructor() {
		this.noticeInstance = null
		this.pendingNotices = []
	}

	// 设置通知组件实例
	setInstance(instance) {
		this.noticeInstance = instance
		if (this.noticeInstance && typeof this.noticeInstance.show === 'function') {
			const pendingNotices = this.pendingNotices.splice(0)
			pendingNotices.forEach((options) => this.noticeInstance.show(options))
		}
	}

	clearInstance(instance) {
		if (this.noticeInstance === instance) {
			this.noticeInstance = null
		}
	}

	// 显示通知
	show(options) {
		// console.log('[NoticeManager] Show called, instance exists:', !!this.noticeInstance)
		if (this.noticeInstance && typeof this.noticeInstance.show === 'function') {
			// console.log('[NoticeManager] Using custom notice component')
			this.noticeInstance.show(options)
		} else {
			this.pendingNotices.push(options)
		}
	}

	// 成功提示
	// 支持两种调用方式:
	//   success(content, options)           -- 旧式, options 包含 success/cancel 回调
	//   success(content, onConfirm, options) -- 新式, onConfirm 为函数
	success(content, onConfirmOrOptions = {}, extraOptions = {}) {
		const isNewStyle = typeof onConfirmOrOptions === 'function' || onConfirmOrOptions === null
		const options = isNewStyle ? { success: onConfirmOrOptions || undefined, ...extraOptions } : onConfirmOrOptions
		this.show({
			type: 'success',
			content,
			showCancel: false,
			...options
		})
	}

	// 错误提示
	error(content, onConfirmOrOptions = {}, extraOptions = {}) {
		const isNewStyle = typeof onConfirmOrOptions === 'function' || onConfirmOrOptions === null
		const options = isNewStyle ? { success: onConfirmOrOptions || undefined, ...extraOptions } : onConfirmOrOptions
		this.show({
			type: 'error',
			content,
			showCancel: false,
			...options
		})
	}

	// 普通通知
	notice(content, onConfirmOrOptions = {}, extraOptions = {}) {
		const isNewStyle = typeof onConfirmOrOptions === 'function' || onConfirmOrOptions === null
		const options = isNewStyle ? { success: onConfirmOrOptions || undefined, ...extraOptions } : onConfirmOrOptions
		this.show({
			type: 'notice',
			content,
			showCancel: false,
			...options
		})
	}

	// 警告提示
	// 支持两种调用方式:
	//   alert(content, options)                    -- 旧式
	//   alert(content, onConfirm, options)          -- 新式
	alert(content, onConfirmOrOptions = {}, extraOptions = {}) {
		const isNewStyle = typeof onConfirmOrOptions === 'function' || onConfirmOrOptions === null
		const options = isNewStyle ? { success: onConfirmOrOptions || undefined, ...extraOptions } : onConfirmOrOptions
		this.show({
			type: 'alert',
			content,
			showCancel: false,
			...options
		})
	}

	// 确认对话框
	// 支持两种调用方式:
	//   confirm(content, options)                       -- 旧式, options 包含 success/cancel 回调
	//   confirm(content, onConfirm, onCancel, options)  -- 新式, 回调为独立参数
	confirm(content, onConfirmOrOptions = {}, onCancel, extraOptions = {}) {
		const isNewStyle = typeof onConfirmOrOptions === 'function' || onConfirmOrOptions === null
		const options = isNewStyle
			? { success: onConfirmOrOptions || undefined, cancel: onCancel || undefined, ...extraOptions }
			: onConfirmOrOptions
		this.show({
			type: 'notice',
			content,
			showCancel: true,
			...options
		})
	}
}

export default new NoticeManager()
