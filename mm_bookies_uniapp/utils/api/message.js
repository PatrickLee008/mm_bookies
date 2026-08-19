/**
 * APP消息API模块
 * 对接Java后端 /message 接口
 */
import my from '@/utils/my.js'
var http = my.http;

/**
 * 获取消息列表（分页）
 * @param {Object} params - 查询参数
 * @param {Number} params.current - 当前页码，默认1
 * @param {Number} params.size - 每页数量，默认10
 * @param {String} params.messageType - 消息类型（可选）：SYSTEM/ORDER/PROMOTION/NOTICE/NOTIFICATION/RECHARGE/WITHDRAW/GAME
 * @param {String} params.category - 消息分类（可选）
 * @param {Number} params.isRead - 是否已读（可选）：0-未读, 1-已读
 * @returns {Promise} Promise对象
 */
export function getMessageList(params = {}) {
	return new Promise((resolve, reject) => {
		const queryParams = {
			current: params.current || 1,
			size: params.size || 10,
		};

		// 添加可选参数（使用下划线命名匹配后端）
		if (params.messageType) queryParams.message_type = params.messageType;
		if (params.category) queryParams.category = params.category;
		if (params.isRead !== undefined) queryParams.is_read = params.isRead;

		http.post('/message/list', queryParams, (res) => {
			if (res.statusCode == 200 && res.data.code == 200) {
				resolve(res.data);
			} else {
				reject(res);
			}
		}, (err) => {
			reject(err);
		});
	});
}

/**
 * 获取未读消息数量
 * @param {String} memberId - 会员ID（可选，不传则获取当前登录会员）
 * @returns {Promise} Promise对象
 */
export function getUnreadCount(memberId = null) {
	return new Promise((resolve, reject) => {
		const params = memberId ? { memberId } : {};

		http.get('/message/unread_count', params, (res) => {
			if (res.statusCode == 200 && res.data.code == 200) {
				// 接口返回格式: { code: 200, count: 1, message: "Success" }
				const unreadCount = res.data.count || 0;
				resolve(unreadCount);
			} else {
				reject(res);
			}
		}, (err) => {
			reject(err);
		});
	});
}

/**
 * 获取消息详情（自动标记已读）
 * @param {String} id - 消息ID
 * @returns {Promise} Promise对象
 */
export function getMessageDetail(id) {
	return new Promise((resolve, reject) => {
		if (!id) {
			reject(new Error('Message ID is required'));
			return;
		}

		http.get(`/message/detail/${id}`, {}, (res) => {
			if (res.statusCode == 200 && res.data.code == 200) {
				resolve(res.data.data);
			} else {
				reject(res);
			}
		}, (err) => {
			reject(err);
		});
	});
}

/**
 * 标记消息为已读
 * @param {String|Array} ids - 消息ID（单个或多个）
 * @returns {Promise} Promise对象
 */
export function markAsRead(ids) {
	return new Promise((resolve, reject) => {
		if (!ids || (Array.isArray(ids) && ids.length === 0)) {
			reject(new Error('Message IDs are required'));
			return;
		}

		// 转换为字符串格式
		const idStr = Array.isArray(ids) ? ids.join(',') : ids;

		http.post('/message/mark_read', { message_id: idStr }, (res) => {
			if (res.statusCode == 200 && res.data.code == 200) {
				resolve(res.data.data);
			} else {
				reject(res);
			}
		}, (err) => {
			reject(err);
		});
	});
}

/**
 * 标记全部消息为已读
 * @returns {Promise} Promise对象
 */
export function markAllAsRead() {
	return new Promise((resolve, reject) => {
		http.post('/message/mark_all_read', {}, (res) => {
			if (res.statusCode == 200 && res.data.code == 200) {
				resolve(res.data.data);
			} else {
				reject(res);
			}
		}, (err) => {
			reject(err);
		});
	});
}

/**
 * 删除消息
 * @param {String|Array} ids - 消息ID（单个或多个）
 * @returns {Promise} Promise对象
 */
export function deleteMessage(ids) {
	return new Promise((resolve, reject) => {
		if (!ids || (Array.isArray(ids) && ids.length === 0)) {
			reject(new Error('Message IDs are required'));
			return;
		}

		// 转换为字符串格式
		const idStr = Array.isArray(ids) ? ids.join(',') : ids;

		// mm-bookies 的 http 工具未提供 delete 快捷方法，使用 request 指定 method
		http.request({
			url: '/message/delete',
			method: 'DELETE',
			data: { ids: idStr },
			success: (res) => {
				if (res.statusCode == 200 && res.data.code == 200) {
					resolve(res.data.data);
				} else {
					reject(res);
				}
			},
			fail: (err) => {
				reject(err);
			}
		});
	});
}

/**
 * 获取消息统计信息
 * @returns {Promise} Promise对象
 */
export function getStatistics() {
	return new Promise((resolve, reject) => {
		http.get('/message/statistics', {}, (res) => {
			if (res.statusCode == 200 && res.data.code == 200) {
				resolve(res.data.data);
			} else {
				reject(res);
			}
		}, (err) => {
			reject(err);
		});
	});
}

/**
 * 按分类获取消息列表
 * @param {String} messageType - 消息类型
 * @param {Object} page - 分页参数
 * @returns {Promise} Promise对象
 */
export function getByType(messageType, page = { current: 1, size: 10 }) {
	return getMessageList({
		...page,
		messageType: messageType
	});
}

/**
 * 获取未读消息列表
 * @param {Object} page - 分页参数
 * @returns {Promise} Promise对象
 */
export function getUnreadList(page = { current: 1, size: 10 }) {
	return getMessageList({
		...page,
		isRead: 0
	});
}

/**
 * 获取已读消息列表
 * @param {Object} page - 分页参数
 * @returns {Promise} Promise对象
 */
export function getReadList(page = { current: 1, size: 10 }) {
	return getMessageList({
		...page,
		isRead: 1
	});
}
