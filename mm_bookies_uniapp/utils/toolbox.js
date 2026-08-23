import my from './my.js'

export const tab_pages = []

let last_operate = null

export const toolbox = {
	/** 操作频繁警告，time_gap:操作间隔,提示信息:message
	 * @param {String} message 
	 * @param {Number} time_gap //列表索引
	 * @returns {Boolean}
	 */
	click_too_fast(time_gap = .1, message = 'click too fast') {
		var result = false;
		var now = new Date().getTime();
		if (last_operate !== null) {
			var second = (now - last_operate) / 1000;
			result = second < time_gap;
			if (message && result) {
				uni.showToast({
					title: message,
					icon: 'error',
				})
			}
		}
		last_operate = now
		return result;
	},
	/** 向下取整并格式化为带千位分隔符的字符串（用于余额显示）
	 * @param {String|Number} num
	 * @returns {String}
	 */
	floor_format(num) {
		let res = 0
		switch (typeof num) {
			case 'number':
				res = num
				break
			case 'string':
				res = parseFloat(num.replace(/,/g, '')) || 0
				break
			default:
				res = parseFloat(String(num)) || 0
		}
		if (isNaN(res)) res = 0
		res = Math.floor(res)
		let parts = String(res).split('.')
		parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ',')
		return parts.join('.')
	},
	/** 向下取整并返回整数（用于余额数值比较）
	 * @param {String|Number} num
	 * @returns {Number}
	 */
	floor_value(num) {
		let res = 0
		switch (typeof num) {
			case 'number':
				res = num
				break
			case 'string':
				res = parseFloat(num.replace(/,/g, '')) || 0
				break
			default:
				res = parseFloat(String(num)) || 0
		}
		if (isNaN(res)) res = 0
		return Math.floor(res)
	},
	/** 格式化数字，time_gap:操作间隔,提示信息:message
	 * @param {String || Number} message 
	 * @param {boolean} return_number //返回数字
	 */
	num_format(num, decimalPlaces = 0, return_number = false) {
		let res = ''
		switch (typeof num) {
			case 'number':
				res = parseFloat(num)
				break
			case 'string':
				res = parseFloat(num.replace(/\,/g, ''))
				break
		}
		return return_number ? res : res.toLocaleString('en-US', {
			minimumFractionDigits: decimalPlaces,
			maximumFractionDigits: decimalPlaces
		});
	},
	/** 删除对象的某个属性
	 * @param {Object} obj
	 * @param {Array}propertiesToRemove
	 * @returns {obj}
	 */
	remove_obj_prop(obj, propertiesToRemove) {
		let newObj = this.deep_clone(obj);
		propertiesToRemove.forEach(prop => {
			if (newObj.hasOwnProperty(prop)) {
				delete newObj[prop];
			}
		});
		return newObj;
	},
	/**
	 * @param {String} str //字符串传入
	 * @returns {Object}
	/*'yyyy-MM-dd HH:mm:ss'格式的字符串转日期*/
	string_to_date: function(str) {
		var tempStrs = str.split(" ");
		var dateStrs = tempStrs[0].split("-");
		console.log(tempStrs, dateStrs)
		var year = parseInt(dateStrs[0], 10);
		var month = parseInt(dateStrs[1], 10) - 1;
		var day = parseInt(dateStrs[2], 10);
		var timeStrs = tempStrs[1].split(":");
		var hour = parseInt(timeStrs[0], 10);
		var minute = parseInt(timeStrs[1], 10);
		var second = parseInt(timeStrs[2], 10);
		var date = new Date(year, month, day, hour, minute, second);
		return date;
	},
	/** 删除对象的多个属性
	 * @param {Object} obj
	 * @param {Array}propertiesToRemove
	 * @returns {Object}
	 */
	adjust_obj_prop(obj, propertiesToRemove) {
		let newObj = {};
		let newObj2 = this.deep_clone(obj);
		propertiesToRemove.forEach(prop => {
			if (newObj2.hasOwnProperty(prop)) {
				newObj[prop] = newObj2[prop];
			}
		});
		return newObj;
	},
	/** 利用JSON进行的深克隆，不能复制function
	 * @param {Object} obj
	 * @returns {Object}
	 */
	fake_deep_clone(obj) {
		return JSON.parse(JSON.stringify(obj))
	},
	/**深克隆
	 * @param {Object} source
	 * @returns {Object}
	 */
	deep_clone(source) {
		if (!source && typeof source !== 'object') {
			throw new Error('error arguments', ` source:`, source)
		}
		const targetObj = Array.isArray(source) ? [] : {}
		Object.keys(source).forEach(keys => {
			if (source[keys] && typeof source[keys] === 'object') {
				targetObj[keys] = this.deep_clone(source[keys])
			} else {
				targetObj[keys] = source[keys]
			}
		})
		return targetObj
	},
	/**
	 * 模糊搜索字符串
	 * @param {string} query - 搜索关键词
	 * @param {string[]} list - 待搜索的字符串列表
	 * @param {Object} [options] - 配置选项
	 * @param {boolean} [options.caseSensitive=false] - 是否区分大小写
	 * @param {string} [options.mode='normal'] - 搜索模式: 'normal' | 'strict' | 'loose'
	 * @param {boolean} [options.includeScore=false] - 是否包含匹配分数
	 * @param {number} [options.limit=Infinity] - 返回结果数量限制
	 * @return {Array} 匹配的字符串数组（包含匹配分数或原始字符串）
	 */
	fuzzy_search(query, list, options = {}) {
		// 合并默认选项
		const {
			caseSensitive = false,
				mode = 'normal',
				includeScore = false,
				limit = Infinity
		} = options;

		// 空查询返回全部结果
		if (!query) {
			return includeScore ?
				list.map(item => ({
					item,
					score: 0
				})) :
				list.slice(0, limit);
		}

		// 准备查询字符串
		const preparedQuery = caseSensitive ? query : query.toLowerCase();
		const queryLen = preparedQuery.length;

		// 存储匹配结果
		const results = [];

		// 遍历每个字符串
		for (const item of list) {
			// 准备搜索文本
			const text = caseSensitive ? item : item.toLowerCase();
			const textLen = text.length;

			// 三种匹配模式
			let match = false;
			let score = 0;

			if (mode === 'strict') {
				// 严格模式：完全匹配
				if (text === preparedQuery) {
					match = true;
					score = 1;
				}
			} else if (mode === 'loose') {
				// 宽松模式：任意部分包含
				if (text.includes(preparedQuery)) {
					match = true;
					score = preparedQuery.length / textLen;
				}
			} else {
				// 正常模式：模糊匹配（字符顺序一致）
				let queryIndex = 0;
				let textIndex = 0;
				let matchPositions = [];

				while (queryIndex < queryLen && textIndex < textLen) {
					if (preparedQuery[queryIndex] === text[textIndex]) {
						matchPositions.push(textIndex);
						queryIndex++;
					}
					textIndex++;
				}

				// 找到所有查询字符
				if (queryIndex === queryLen) {
					match = true;

					// 计算匹配分数（基于连续性和位置）
					const consecutiveBonus = calculateConsecutiveBonus(matchPositions);
					const positionBonus = 1 - (matchPositions[0] / textLen);
					score = 0.5 * (queryLen / textLen) +
						0.3 * consecutiveBonus +
						0.2 * positionBonus;
				}
			}

			// 添加到结果
			if (match) {
				results.push(includeScore ? {
					item,
					score
				} : item);

				// 达到数量限制时停止
				if (results.length >= limit && !includeScore) {
					break;
				}
			}
		}

		// 包含分数时排序
		if (includeScore) {
			results.sort((a, b) => b.score - a.score);
			return results.slice(0, limit);
		}

		return results.slice(0, limit);
	},

	/**
	 * 计算连续匹配的加分
	 * @param {number[]} positions - 匹配位置索引数组
	 * @return {number} 连续分数 (0-1)
	 */
	calculateConsecutiveBonus(positions) {
		if (positions.length < 2) return 0;

		let consecutiveCount = 1;
		let maxConsecutive = 1;

		for (let i = 1; i < positions.length; i++) {
			if (positions[i] === positions[i - 1] + 1) {
				consecutiveCount++;
				if (consecutiveCount > maxConsecutive) {
					maxConsecutive = consecutiveCount;
				}
			} else {
				consecutiveCount = 1;
			}
		}

		return maxConsecutive / positions.length;
	},

	/**
	 * 将服务器时间转换为本地时区时间（保持原始格式）
	 * @param {string|Date} serverTime - 服务器时间，可以是ISO字符串、日期字符串或Date对象
	 * @param {number} serverOffsetHours - 服务器时区与UTC的时差（小时），例如北京+8，纽约-5
	 * @returns {string|Date} 转换后的时间，保持与输入相同的格式
	 */
	convert_time(serverTime, serverOffsetHours = 8) {
		// 1. 确定原始输入类型和格式
		const isDateObject = serverTime instanceof Date;
		let originalFormat = 'date';
		let datetimeParts = null;
		let timeString = '';

		if (!isDateObject) {
			// 尝试解析字符串格式
			timeString = serverTime.toString();

			// 检查常见日期分隔符
			if (timeString.includes('-')) {
				originalFormat = 'YYYY-MM-DD';
			} else if (timeString.includes('/')) {
				originalFormat = 'YYYY/MM/DD';
			}

			// 检查时间部分是否存在
			const hasTime = /[0-9]{1,2}:[0-9]{1,2}(:[0-9]{1,2})?/.test(timeString);
			if (hasTime) {
				originalFormat += ' HH:mm:ss';
			}
		}

		// 2. 转换为Date对象（处理时区转换）
		const time = isDateObject ? serverTime : new Date(serverTime);

		if (isNaN(time.getTime())) {
			throw new Error('Invalid server time provided');
		}

		// 验证时差参数
		if (typeof serverOffsetHours !== 'number' || serverOffsetHours < -12 || serverOffsetHours > 14) {
			throw new Error('Invalid time offset. Expected value between -12 and +14');
		}

		// 3. 执行时区转换
		const utcTime = time.getTime();
		const serverOffsetMs = serverOffsetHours * 60 * 60 * 1000;
		const localOffsetMs = time.getTimezoneOffset() * 60 * 1000;
		const totalOffsetMs = localOffsetMs + serverOffsetMs;
		const localTime = new Date(utcTime + totalOffsetMs);

		// 4. 根据原始格式返回结果
		if (isDateObject) {
			return localTime;
		}

		// 从Date对象生成格式化字符串
		const pad = num => num.toString().padStart(2, '0');

		const year = localTime.getFullYear();
		const month = pad(localTime.getMonth() + 1);
		const day = pad(localTime.getDate());
		const hours = pad(localTime.getHours());
		const minutes = pad(localTime.getMinutes());
		const seconds = pad(localTime.getSeconds());

		// 根据原始格式重建字符串
		if (originalFormat.includes('-')) {
			if (originalFormat.includes('HH:mm:ss')) {
				return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
			}
			return `${year}-${month}-${day}`;
		} else if (originalFormat.includes('/')) {
			if (originalFormat.includes('HH:mm:ss')) {
				return `${year}/${month}/${day} ${hours}:${minutes}:${seconds}`;
			}
			return `${year}/${month}/${day}`;
		}

		// 默认返回ISO格式
		return localTime.toISOString();
	},
	/**
	 * 获取本地时区与UTC的时差（小时）
	 * @returns {number} 格式如 "8" 或 "-5"
	 */
	get_time_offset() {
		const offsetMinutes = new Date().getTimezoneOffset();
		const offsetHours = -offsetMinutes / 60;

		// 格式化输出
		const sign = offsetHours >= 0 ? '+' : '-';
		const absHours = Math.abs(offsetHours);

		return offsetHours;
	},
	formatCurrencyManual(number, currencySymbol = '$', decimalPlaces = 2) {
		if (typeof number !== 'number' || isNaN(number)) {
			return "Invalid input";
		}

		const fixedNumber = number.toFixed(decimalPlaces);
		// 分离整数部分和小数部分
		const parts = fixedNumber.split(".");
		const integerPart = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ",");
		const decimalPart = parts.length > 1 ? "." + parts[1] : "";

		return currencySymbol + integerPart + decimalPart;
	},
	/**
	 * 获取应用已注册的页面路径集合（兼容 H5 / App）
	 * 读取 uni-app 运行时路由表，无法获取时返回空 Set
	 * @returns {Set<String>} 形如 "pages/ucenter/message" 的路径集合（无前导斜杠、无参数）
	 */
	get_registered_pages() {
		const pages = new Set();
		const add = (p) => {
			if (!p) return;
			const path = String(p).replace(/^\//, '').split('?')[0].split('#')[0];
			if (path) pages.add(path);
		};
		try {
			// H5：vue-router 路由表
			// eslint-disable-next-line no-undef
			if (typeof __uniRoutes !== 'undefined' && Array.isArray(__uniRoutes)) {
				// eslint-disable-next-line no-undef
				__uniRoutes.forEach(r => {
					if (!r) return;
					add(r.path);
					if (r.meta && r.meta.pagePath) add(r.meta.pagePath);
				});
			}
		} catch (e) {}
		try {
			// App / 通用：__uniConfig.pages
			// eslint-disable-next-line no-undef
			if (typeof __uniConfig !== 'undefined' && __uniConfig && __uniConfig.pages) {
				const cfg_pages = __uniConfig.pages;
				if (Array.isArray(cfg_pages)) {
					cfg_pages.forEach(p => add(typeof p === 'string' ? p : (p && p.path)));
				} else {
					Object.keys(cfg_pages).forEach(add);
				}
			}
		} catch (e) {}
		return pages;
	},
	/**
	 * 检查页面（路由）是否已注册存在
	 * @param {String} url 页面路径，可带参数，如 "/pages/index/wallet?id=1"
	 * @returns {Boolean|null} true=存在，false=不存在，null=无法确定（路由表不可用）
	 */
	page_exists(url) {
		if (!url) return false;
		const path = String(url).replace(/^\//, '').split('?')[0].split('#')[0];
		if (!path) return false;
		const pages = this.get_registered_pages();
		if (!pages || pages.size === 0) return null;
		return pages.has(path);
	},
	/**
	 * 广告跳转
	 */
	openAdvertisementLink(linkUrl, linkTarget = 'Blank') {
		if (!linkUrl) return;
		const normalizedUrl = this.normalizeAdvertisementUrl(linkUrl);
		if (!normalizedUrl) return;
		if (normalizedUrl.startsWith('/pages/')) {
			this.navigateToPage(normalizedUrl);
			return;
		}
	
		const target = this.normalizeLinkTarget(linkTarget);
		const encodedUrl = encodeURIComponent(normalizedUrl);
		const webviewUrl = `/pages/webview/index?url=${encodedUrl}`;
	
		if (target === 'self') {
			// #ifdef APP-PLUS || MP-WEIXIN || MP-ALIPAY || MP-BAIDU || MP-TOUTIAO || MP-QQ
			uni.redirectTo({
				url: webviewUrl
			});
			// #endif
			// #ifdef H5
			window.location.href = normalizedUrl;
			// #endif
			return;
		}
	
		if (target === 'app') {
			uni.navigateTo({
				url: webviewUrl
			});
			return;
		}
	
		// #ifdef APP-PLUS
		plus.runtime.openURL(normalizedUrl);
		// #endif
		// #ifdef H5
		window.open(normalizedUrl, '_blank');
		// #endif
		// #ifdef MP-WEIXIN || MP-ALIPAY || MP-BAIDU || MP-TOUTIAO || MP-QQ
		uni.navigateTo({
			url: webviewUrl
		});
		// #endif
	},
	normalizeAdvertisementUrl(linkUrl) {
		if (!linkUrl) return '';
		const normalizedUrl = String(linkUrl).trim();
		if (!normalizedUrl) return '';
		if (normalizedUrl.startsWith('/pages/')) return normalizedUrl;
		if (/^https?:\/\//i.test(normalizedUrl)) return normalizedUrl;
		if (/^\/\//.test(normalizedUrl)) return `https:${normalizedUrl}`;
		if (/^[a-z0-9.-]+\.[a-z]{2,}(\/.*)?$/i.test(normalizedUrl)) return `https://${normalizedUrl}`;
		return '';
	},
	normalizeLinkTarget(linkTarget) {
		if (!linkTarget) return 'blank';
		return String(linkTarget).trim().toLowerCase();
	},
	/**
	 * 解析路由路径 - 将关键词路由转换为完整路径
	 * @param {String} route - 路由标识符（可以是关键词或完整路径）
	 * @returns {String} 完整的页面路径
	 */
	resolvePageRoute(route) {
		if (!route) return '/pages/match/home';
		
		// 如果已经是完整路径，直接返回
		if (route.startsWith('/')) {
			return route;
		}
		
		// 关键词路由映射 - 参考 launch 页面的 handleActionButton 实现
		const routeMap = {
			'home': '/pages/match/home',
			'promotions': '/pages/index/coupon?activity_type=promotion',
			'bet-history': '/pages/orders/home',
			'coupon': '/pages/index/coupon',
			'user-center': '/pages/ucenter/home',
			'wallet': '/pages/index/coupon',
			'invitation': '/pages/ucenter/invite/index',
			'deposit': '/pages/ucenter/charge',
			'withdraw': '/pages/ucenter/withdraw',
			'egame-list': '/pages/index/egame'
		};
		
		// 查找映射，找不到则默认跳转到首页
		const resolvedRoute = routeMap[route.toLowerCase()] || '/pages/match/home';
		
		console.log(`[RouteResolver] '${route}' resolved to '${resolvedRoute}'`);
		return resolvedRoute;
	},
	
	/**
	 * 判断是否为 TabBar 页面
	 * 从 uni-app 运行时 tabBar 配置读取，无配置时返回 false
	 * @param {String} url - 页面路径
	 * @returns {Boolean} 是否为 TabBar 页面
	 */
	isTabBarPage(url) {
		if (!url) return false;
		const path = String(url).replace(/^\//, '').split('?')[0].split('#')[0];
		if (!path) return false;
		try {
			// eslint-disable-next-line no-undef
			if (typeof __uniConfig === 'undefined' || !__uniConfig || !__uniConfig.tabBar || !__uniConfig.tabBar.list) {
				return false;
			}
			// eslint-disable-next-line no-undef
			return __uniConfig.tabBar.list.some(item => {
				const p = item && (item.pagePath || item.path);
				if (!p) return false;
				return String(p).replace(/^\//, '').split('?')[0].split('#')[0] === path;
			});
		} catch (e) {
			return false;
		}
	},
	
	/**
	 * 智能页面跳转 - 自动处理 TabBar 和普通页面
	 * @param {String} route - 路由标识符或完整路径
	 * @param {Object} options - 跳转选项
	 * @param {Function} options.success - 成功回调
	 * @param {Function} options.fail - 失败回调
	 */
	navigateToPage(route, options = {}) {
		try {
			const targetUrl = this.resolvePageRoute(route);
			const isTabBar = this.isTabBarPage(targetUrl);
			
			console.log(`[Navigator] Navigating to '${targetUrl}', isTabBar: ${isTabBar}`);
			
			const runNavigateTo = () => {
				uni.navigateTo({
					url: targetUrl,
					success: (res) => {
						console.log(`[Navigator] Successfully navigated to '${targetUrl}'`);
						if (options.success) options.success(res);
					},
					fail: (error) => {
						console.error(`[Navigator] Navigation failed to '${targetUrl}':`, error);
						if (options.fail) options.fail(error);
					}
				});
			};
			
			if (isTabBar) {
				uni.switchTab({
					url: targetUrl,
					success: (res) => {
						console.log(`[Navigator] Successfully switchTab to '${targetUrl}'`);
						if (options.success) options.success(res);
					},
					fail: (error) => {
						console.warn(`[Navigator] switchTab failed, fallback to navigateTo for '${targetUrl}':`, error);
						runNavigateTo();
					}
				});
			} else {
				runNavigateTo();
			}
		} catch (error) {
			console.error('[Navigator] Navigation error:', error);
			if (options.fail) options.fail(error);
		}
	}
}

export default toolbox;