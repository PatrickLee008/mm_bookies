/**
 * 公共API模块
 * 包含不需要登录的公共接口
 */

/**
 * 添加用户行为日志
 * @param {Object} http - HTTP客户端实例 (this.$http)
 * @param {Object} params - 行为日志参数
 * @param {String} params.event_type - 事件类型(visit/register/login/deposit/bet/withdraw) - 必填
 * @param {String} params.business_type - 业务类型(adlink/promotion/coupon/general) - 可选，默认general
 * @param {String} params.business_id - 业务ID - 可选
 * @param {String} params.member_id - 会员ID - 可选
 * @param {Object} params.event_params - 事件参数 - 可选
 * @param {String} params.remark - 备注 - 可选
 * @returns {Promise} Promise对象
 */
export function addBehaviorLog(http, params) {
	return new Promise((resolve, reject) => {
		if (!params || !params.event_type) {
			console.error('[BehaviorLog] event_type is required');
			reject(new Error('event_type is required'));
			return;
		}

		const data = {
			event_type: params.event_type,
		};

		if (params.business_type) data.business_type = params.business_type;
		if (params.business_id) data.business_id = params.business_id;
		if (params.member_id) data.member_id = params.member_id;
		if (params.event_params) data.event_params = params.event_params;
		if (params.remark) data.remark = params.remark;

		console.log('[BehaviorLog] Adding behavior log:', data);

		http.post('/public/behavior/log', data, (res) => {
			if (res.statusCode == 200) {
				console.log('[BehaviorLog] Behavior log added successfully');
				resolve(res.data);
			} else {
				console.error('[BehaviorLog] Failed to add behavior log:', res);
				reject(res);
			}
		}, (err) => {
			console.error('[BehaviorLog] Error adding behavior log:', err);
			reject(err);
		});
	});
}

/**
 * 记录广告链接访问日志
 * @param {Object} http - HTTP客户端实例 (this.$http)
 * @param {String} adlId - 广告链接ID
 * @param {String} memberId - 会员ID（可选）
 * @returns {Promise} Promise对象
 */
export function logAdlinkVisit(http, adlId, memberId = null) {
	const params = {
		event_type: 'visit',
		business_type: 'adlink',
		business_id: adlId,
	};

	if (memberId) {
		params.member_id = memberId;
	}

	return addBehaviorLog(http, params);
}
