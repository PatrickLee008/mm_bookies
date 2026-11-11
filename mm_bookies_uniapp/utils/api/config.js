/**
 * 配置相关API
 */

/**
 * /config/get 并发去重：App.onLaunch、App.onShow、充值页 mounted 在同一次加载里都会取配置，
 * 共享同一个 in-flight 请求，避免一次刷新打多次后端。
 * 返回原始响应（skipFilter，启动时未登录拿到 401 也不触发会话过期跳转），失败 resolve null；
 * 请求结束后下一次调用重新发起，不影响"回到前台刷新页面配置版本"的设计。
 */
let configInflight = null
export function fetchConfigShared(http) {
	if (configInflight) return configInflight
	const p = new Promise((resolve) => {
		http.get('/config/get', {
			skipFilter: true,
			fail: () => resolve(null)
		}, (res) => resolve(res))
	})
	configInflight = p
	p.then(() => {
		if (configInflight === p) configInflight = null
	})
	return p
}

/**
 * 检查用户是否已登录
 * @returns {boolean} 是否已登录
 */
export function isUserLoggedIn() {
	const token = uni.getStorageSync('Authorization');
	const isLogin = uni.getStorageSync('isLogin');
	// console.log("check login",token)
	return !!(token);
}

/**
 * 获取系统配置
 * 需要用户登录后才能获取
 * 优先从本地缓存获取，缓存有效期5分钟
 * @param {Object} http - HTTP客户端实例 (this.$http)
 * @param {Object} store - Vuex store实例 (this.$store)
 * @param {Boolean} forceRefresh - 是否强制刷新，忽略缓存
 * @returns {Promise} Promise对象
 */
export function getConfigs(http, store, forceRefresh = false) {
	return new Promise((resolve, reject) => {
		// 检查用户是否登录
		if (!isUserLoggedIn()) {
			console.log('[Config] User not logged in, skipping config fetch');
			reject(new Error('User not logged in'));
			return;
		}

		// 如果不强制刷新，优先从缓存获取
		if (!forceRefresh) {
			const cachedConfig = uni.getStorageSync('config');
			const configTimestamp = uni.getStorageSync('config_timestamp');
			const now = Date.now();
			const cacheExpiry = 5 * 60 * 1000; // 5分钟（毫秒）

			// 检查缓存是否存在且未过期
			if (cachedConfig && configTimestamp && (now - configTimestamp < cacheExpiry)) {
				console.log('[Config] Using cached configuration');
				// 同时更新到Vuex store
				store.dispatch('saveConfigs', cachedConfig);
				resolve(cachedConfig);
				return;
			} else if (cachedConfig && configTimestamp) {
				console.log('[Config] Cache expired, fetching new configuration');
			} else {
				console.log('[Config] No cache found, fetching configuration');
			}
		} else {
			console.log('[Config] Force refresh, fetching new configuration');
		}

		// 从后台获取配置
		http.get('/config/get', {}, (res) => {
			if (res.statusCode == 200) {
				let config = res.data.items;
				// 保存到Vuex store
				store.dispatch('saveConfigs', config);
				// 保存到本地存储
				uni.setStorageSync('config', config);
				// 保存时间戳
				uni.setStorageSync('config_timestamp', Date.now());
				console.log('[Config] Configuration loaded and cached successfully');
				resolve(config);
			} else {
				console.error('[Config] Failed to load configuration:', res);
				reject(res);
			}
		});
	});
}

/**
 * 获取应用信息配置
 * 不需要登录即可获取
 * @param {Object} http - HTTP客户端实例 (this.$http)
 * @returns {Promise} Promise对象
 */
export function getAppInfo(http) {
	return new Promise((resolve, reject) => {
		http.get('/config/appinfo', {}, (res) => {
			if (res.statusCode == 200 && res.data.code == 200) {
				console.log('[Config] App info loaded successfully');
				resolve(res.data.data);
			} else {
				console.error('[Config] Failed to load app info:', res);
				reject(res);
			}
		});
	});
}

/**
 * 获取配置的Vue mixin
 * 可以在组件中直接使用 this.fetchConfigs()
 */
export const configMixin = {
	methods: {
		async fetchConfigs(forceRefresh = false) {
			try {
				await getConfigs(this.$http, this.$store, forceRefresh);
			} catch (error) {
				console.error('[Config] Error fetching configs:', error);
			}
		}
	}
};
