const QR_CHANNELS = ['VIPPay']
// 走外部收银页的通道：有 PAYMENT_URL 时直接跳转，不弹二维码弹窗
const EXTERNAL_CHANNELS = ['TCPay', 'MCPay', 'KingPay']

function firstValue(order, keys) {
	if (!order) return ''
	for (let i = 0; i < keys.length; i++) {
		const value = order[keys[i]]
		if (value !== undefined && value !== null && value !== '') return value
	}
	return ''
}

export function getPaymentAction(order = {}) {
	const channel = firstValue(order, ['pay_channel', 'CHANNEL', 'channel'])
	const paymentUrl = firstValue(order, ['PAYMENT_URL', 'payment_url', 'pay_url', 'payUrl', 'paymentUrl'])
	const hasUrl = /^https?:\/\//i.test(String(paymentUrl || ''))

	// 外部收银页通道（TCPay / MCPay / KingPay）：有链接就直接跳，不弹窗。
	// TCPay 同时返回二维码和链接，但业务上要求直接跳第三方页，所以放在二维码判断之前。
	if (EXTERNAL_CHANNELS.indexOf(channel) !== -1 && hasUrl) {
		return { type: 'external', url: String(paymentUrl) }
	}

	const qrCode = firstValue(order, ['QRCODE', 'qrcode', 'qr_code'])
	if (String(qrCode || '').trim()) return { type: 'qr' }

	if (hasUrl) return { type: 'external', url: String(paymentUrl) }

	if (QR_CHANNELS.indexOf(channel) !== -1) return { type: 'qr' }
	return { type: 'transfer' }
}

export function getTransferPageUrl(order = {}) {
	const remark = String(firstValue(order, ['remark', 'REMARK']) || '')
	const cashCodeMatch = remark.match(/Cash Code\s*:?\s*(\d{1,8})/i)
	const params = {
		id: firstValue(order, ['id', 'ID', 'out_order_id', 'OUT_ORDER_ID']),
		channel: firstValue(order, ['pay_channel', 'CHANNEL', 'channel']),
		amount: firstValue(order, ['money', 'MONEY', 'amount']),
		bank_code: firstValue(order, ['receive_bank_code', 'bank_type', 'bank_code']),
		cash_code: firstValue(order, ['cash_code', 'CASH_CODE']) || (cashCodeMatch && cashCodeMatch[1]),
		expire_time: firstValue(order, ['expire_time', 'EXPIRE_TIME']),
		txn_last5: firstValue(order, ['txn_last5', 'TXN_LAST5'])
	}
	if (!params.id) return ''

	const query = Object.keys(params)
		.filter(key => params[key] !== undefined && params[key] !== null && params[key] !== '')
		.map(key => encodeURIComponent(key) + '=' + encodeURIComponent(String(params[key])))
	return '/pages/payment/transfer?' + query.join('&')
}

export function openPaymentUrl(url) {
	const paymentUrl = String(url || '')
	if (!/^https?:\/\//i.test(paymentUrl)) return false

	// #ifdef H5
	window.location.href = paymentUrl
	// #endif
	// #ifdef APP-PLUS
	plus.runtime.openURL(paymentUrl)
	// #endif
	// #ifdef MP-WEIXIN || MP-ALIPAY || MP-BAIDU || MP-TOUTIAO || MP-QQ
	uni.navigateTo({ url: '/pages/webview/index?url=' + encodeURIComponent(paymentUrl) })
	// #endif
	return true
}
