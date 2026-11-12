// Case 19: 银行卡输入规则（与后端 utils/BankCardValidation.py 保持一致）
// 账号：纯数字 6~20 位；户名：英文/缅文字母 + 空格 2~50 位（缅文数字 ၀-၉ 属于数字，不允许）
const ACC_NUMBER_RE = /^[0-9]{6,20}$/
const ACC_NAME_RE = /^[A-Za-z\u1000-\u103F\u104A-\u109F ]{2,50}$/
const NAME_INVALID_RE = /[^A-Za-z\u1000-\u103F\u104A-\u109F ]/g

export function sanitizeAccNumber(value) {
	return String(value == null ? '' : value).replace(/\D/g, '').slice(0, 20)
}

export function sanitizeAccName(value) {
	return String(value == null ? '' : value).replace(NAME_INVALID_RE, '').slice(0, 50)
}

export function validateAccNumber(value) {
	const v = String(value == null ? '' : value).trim()
	if (!v) return 'Account number is required'
	if (!ACC_NUMBER_RE.test(v)) return 'Account number must be 6-20 digits (numbers only)'
	return ''
}

export function validateAccName(value) {
	const v = String(value == null ? '' : value).trim()
	if (!v) return 'User name is required'
	if (!ACC_NAME_RE.test(v)) return 'User name must be 2-50 letters (English or Myanmar) and spaces only'
	return ''
}