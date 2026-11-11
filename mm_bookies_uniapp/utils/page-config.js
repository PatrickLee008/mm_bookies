/**
 * 页面配置（后台 Setting → Other，平台 MMBookies，类型为页面路由，如 wallet/deposit）（2026-11-11）
 *
 * 版本号缓存：
 *   - /config/get 返回 page_config_versions: { 页面: 版本 }（App 启动、回到前台、进页面时都会调用）；
 *   - 本地缓存 page_cfg:<页面> = { v: 版本, items: [全部语言的配置] }；
 *   - 页面先用缓存显示；版本与服务端一致时不发请求，不一致才拉取 /setting/get_all 并更新缓存；
 *   - 本地存储不可用时退回每次请求。
 *
 * 显示规则（同《页面自定义参数配置》方案 §7）：配置什么显示什么（保留换行，不编号、不渲染 HTML）；
 * 当前语言没配置时用页面内置文案。
 */
const CACHE_PREFIX = 'page_cfg:'

function cacheKey(page) {
	return CACHE_PREFIX + page
}

/** 读本地缓存：{ v, items } 或 null */
export function getCachedPageConfig(page) {
	try {
		const c = uni.getStorageSync(cacheKey(page))
		if (c && Array.isArray(c.items)) return c
	} catch (e) {}
	return null
}

function saveCache(page, v, items) {
	try {
		uni.setStorageSync(cacheKey(page), { v: v || '', items: items || [] })
	} catch (e) {}
}

/**
 * 从 /config/get 的结果里取某个页面的最新版本。
 * versions 不可用（请求失败、老版本后端）时返回 null；版本表里没有这个页面 = 没有任何配置，返回 'empty'
 * （与后端 PageConfig.page_version 一致），这样后台删光配置后缓存也会被清掉。
 */
export function latestVersionOf(config, page) {
	const versions = config && config.page_config_versions
	if (!versions || typeof versions !== 'object') return null
	return versions[page] || 'empty'
}

/**
 * 按版本同步页面配置。
 * @param http       this.$http
 * @param page       页面标识，如 'wallet/deposit'
 * @param latest     latestVersionOf(...) 的结果；null 表示版本未知
 * @param callback   (items) => void，只有拿到新数据时才调用（缓存命中不调用，调用方先用 getCachedPageConfig 显示）
 */
export function syncPageConfig(http, page, latest, callback) {
	const cached = getCachedPageConfig(page)
	// 版本一致：不请求
	if (cached && latest && cached.v === latest) return
	// 版本未知且已有缓存：先用缓存，等下次拿到版本再比对
	if (cached && !latest) return
	// 版本为 empty（后台没有配置）：直接清成空，不必请求
	if (latest === 'empty') {
		if (!cached || cached.items.length) {
			saveCache(page, 'empty', [])
			callback && callback([])
		}
		return
	}
	http.get('/setting/get_all', {
		data: { setting_type: page, status: 1 },
		fail: () => {}
	}, (res) => {
		const d = (res && res.data) || {}
		if (d.code !== 20000 || !d.data) return
		const items = Array.isArray(d.data.items) ? d.data.items : []
		saveCache(page, d.data.version || latest || '', items)
		callback && callback(items)
	})
}

/**
 * 取某个参数在当前语言下的文本；没有配置返回 ''（调用方回退内置文案）。
 * 只取通用配置（aid 为空），同一参数有多条时取 sort 最小的一条（后端已按 sort 排序）。
 */
export function pickText(items, key, lang) {
	if (!Array.isArray(items)) return ''
	const hit = items.find(it => it && it.setting_key === key && it.language_type === lang &&
		Number(it.status) === 1 && !it.aid)
	const text = hit && hit.setting_value != null ? String(hit.setting_value) : ''
	return text.trim() ? text : ''
}

/** 移动端语言 → 页面配置语言：缅文 mm，其他一律 en */
export function pageConfigLang(lang) {
	return lang === 'mm' ? 'mm' : 'en'
}
