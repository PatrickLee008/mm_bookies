var dateFormatUtils = {
	numFormat: function(n) {
		if(!n){n =0} ;
		n = parseInt(n);
		let num = n.toString()
		let decimals = ''
		// 判断是否有小数
		num.indexOf('.') > -1 ? decimals = num.split('.')[1] : decimals
		let len = num.length
		if (len <= 3) {
			return num
		} else {
			let temp = ''
			let remainder = len % 3
			decimals ? temp = '.' + decimals : temp
			if (remainder > 0) { // 不是3的整数倍
				return num.slice(0, remainder) + ',' + num.slice(remainder, len).match(/\d{3}/g).join(',') + temp
			} else { // 是3的整数倍
				return num.slice(0, len).match(/\d{3}/g).join(',') + temp
			}
		}
	},
	formatNumber: function(n) {
		n = n.toString()
		return n[1] ? n : '0' + n;
	},
	/*'yyyy-MM-dd'格式的字符串转日期*/
	stringToDate2: function(str) {
		var dateStrs = str.split("-");
		var year = parseInt(dateStrs[0], 10);
		var month = parseInt(dateStrs[1], 10) - 1;
		var day = parseInt(dateStrs[2], 10);
		var date = new Date(year, month, day, 0, 0, 0);
		return date;
	},
	formatDate: function(number, format) {
		let time = new Date(number)
		let newArr = []
		let formatArr = ['Y', 'M', 'D']
		newArr.push(time.getFullYear())
		newArr.push(this.formatNumber(time.getMonth() + 1))
		newArr.push(this.formatNumber(time.getDate()))
		for (let i in newArr) {
			format = format.replace(formatArr[i], newArr[i])
		}
		return format;
	},
	getCurrentDate2: function(n) {
		var dd = new Date();
		if (n) {
			dd.setDate(dd.getDate() - n);
		}
		var year = dd.getFullYear();
		var month =
			dd.getMonth() + 1 < 10 ? "0" + (dd.getMonth() + 1) : dd.getMonth() + 1;
		var day = dd.getDate() < 10 ? "0" + dd.getDate() : dd.getDate();
		var date = month + "-" + day
		var date2 = year + '-' + month + "-" + day
		var day2 = dd.getDay()
		return [date,day2,date2] ;
	},
	formatTime: function (date) {
	    var y = date.getFullYear();
	    var m = date.getMonth() + 1;
	    m = m < 10 ? ('0' + m) : m;
	    var d = date.getDate();
	    d = d < 10 ? ('0' + d) : d;
	    var h = date.getHours();
	    var minute = date.getMinutes();
	    minute = minute < 10 ? ('0' + minute) : minute;
	    var second= date.getSeconds();
	    second = minute < 10 ? ('0' + second) : second;
	    return y + '-' + m + '-' + d+' '+h+':'+minute+':'+ second;
	},
	/*'yyyy-MM-dd HH:mm:ss'格式的字符串转日期*/
	stringToDate: function(str) {
		var tempStrs = str.split(" ");
		var dateStrs = tempStrs[0].split("-");
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
	getCurrentDate: function(n) {
		var dd = new Date();
		if (n) {
			dd.setDate(dd.getDate() - n);
		}
		var year = dd.getFullYear();
		var month =
			dd.getMonth() + 1 < 10 ? "0" + (dd.getMonth() + 1) : dd.getMonth() + 1;
		var day = dd.getDate() < 10 ? "0" + dd.getDate() : dd.getDate();
		return year + "-" + month + "-" + day;
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

	// ========== 时区日期转换 ==========

	// 系统默认时区偏移（小时），服务器时间基于 UTC+8
	SYSTEM_TZ_OFFSET: 8,

	// 常见时区 UTC 偏移映射表（小时），小数表示半小时时区
	TIMEZONE_OFFSETS: {
		'Asia/Shanghai': 8,
		'Asia/Singapore': 8,
		'Asia/Kuala_Lumpur': 8,
		'Asia/Manila': 8,
		'Asia/Taipei': 8,
		'Asia/Hong_Kong': 8,
		'Asia/Macau': 8,
		'Asia/Ulaanbaatar': 8,
		'Asia/Brunei': 8,
		'Asia/Makassar': 8,
		'Asia/Choibalsan': 8,
		'Asia/Irkutsk': 8,
		'Asia/Bangkok': 7,
		'Asia/Jakarta': 7,
		'Asia/Pontianak': 7,
		'Asia/Ho_Chi_Minh': 7,
		'Asia/Phnom_Penh': 7,
		'Asia/Vientiane': 7,
		'Asia/Novosibirsk': 7,
		'Asia/Yangon': 6.5,
		'Asia/Dhaka': 6,
		'Asia/Almaty': 6,
		'Asia/Bishkek': 6,
		'Asia/Omsk': 6,
		'Asia/Thimphu': 6,
		'Asia/Kolkata': 5.5,
		'Asia/Colombo': 5.5,
		'Asia/Kathmandu': 5.75,
		'Asia/Karachi': 5,
		'Asia/Tashkent': 5,
		'Asia/Ashgabat': 5,
		'Asia/Dushanbe': 5,
		'Asia/Aqtobe': 5,
		'Asia/Yekaterinburg': 5,
		'Asia/Dubai': 4,
		'Asia/Muscat': 4,
		'Asia/Baku': 4,
		'Asia/Tbilisi': 4,
		'Asia/Tehran': 3.5,
		'Asia/Baghdad': 3,
		'Asia/Riyadh': 3,
		'Asia/Kuwait': 3,
		'Asia/Qatar': 3,
		'Asia/Bahrain': 3,
		'Asia/Aden': 3,
		'Asia/Jerusalem': 3,
		'Asia/Amman': 3,
		'Asia/Damascus': 3,
		'Asia/Beirut': 3,
		'Asia/Nicosia': 3,
		'Asia/Tokyo': 9,
		'Asia/Seoul': 9,
		'Asia/Pyongyang': 9,
		'Asia/Yakutsk': 9,
		'Asia/Vladivostok': 10,
		'Asia/Magadan': 11,
		'Asia/Kamchatka': 12,
		'Pacific/Auckland': 12,
		'Pacific/Fiji': 12,
		'Australia/Sydney': 10,
		'Australia/Melbourne': 10,
		'Australia/Brisbane': 10,
		'Australia/Perth': 8,
		'Australia/Darwin': 9.5,
		'Australia/Adelaide': 9.5,
		'Europe/London': 1,
		'Europe/Paris': 2,
		'Europe/Berlin': 2,
		'Europe/Moscow': 3,
		'Europe/Istanbul': 3,
		'Africa/Cairo': 3,
		'Africa/Lagos': 1,
		'Africa/Nairobi': 3,
		'Africa/Johannesburg': 2,
		'America/New_York': -4,
		'America/Chicago': -5,
		'America/Denver': -6,
		'America/Los_Angeles': -7,
		'America/Anchorage': -8,
		'America/Sao_Paulo': -3,
		'America/Argentina/Buenos_Aires': -3,
		'America/Mexico_City': -5,
		'America/Toronto': -4,
		'America/Vancouver': -7,
		'Pacific/Honolulu': -10
	},

	/**
	 * 从本地缓存获取用户时区
	 * @returns {string|null} IANA 时区字符串或 null
	 */
	getUserTimezone: function() {
		try {
			const userInfo = uni.getStorageSync('user_info');
			if (userInfo && userInfo.timezone) {
				return userInfo.timezone;
			}
		} catch (e) {}
		// 也尝试从独立 key 读取
		try {
			const tz = uni.getStorageSync('timezone');
			if (tz) return tz;
		} catch (e) {}
		return null;
	},

	/**
	 * 获取指定时区的 UTC 偏移（小时）
	 * @param {string} timezone - IANA 时区名称，如 'Asia/Yangon'
	 * @returns {number|null} UTC 偏移小时数，或 null
	 */
	getTimezoneOffset: function(timezone) {
		if (!timezone) return null;
		// 优先从映射表查找
		if (this.TIMEZONE_OFFSETS.hasOwnProperty(timezone)) {
			return this.TIMEZONE_OFFSETS[timezone];
		}
		// 尝试用 Intl 计算偏移（兼容现代浏览器/WebView）
		try {
			var testDate = new Date();
			var utcStr = testDate.toLocaleString('en-US', { timeZone: 'UTC' });
			var tzStr = testDate.toLocaleString('en-US', { timeZone: timezone });
			var utcDate = new Date(utcStr);
			var tzDate = new Date(tzStr);
			if (!isNaN(utcDate.getTime()) && !isNaN(tzDate.getTime())) {
				return (tzDate.getTime() - utcDate.getTime()) / 3600000;
			}
		} catch (e) {}
		return null;
	},

	/**
	 * 将日期字符串从系统时区 (UTC+8) 转换到用户时区
	 * @param {string} dateStr - 日期字符串，如 "2026-06-04 09:27:15"（服务器 UTC+8 时间）
	 * @param {string} userTimezone - IANA 时区名称（可选，不传则从缓存读取 user_info.timezone）
	 * @returns {string} 用户时区下的日期字符串，格式 "YYYY-MM-DD HH:MM:SS"
	 */
	convertTimezone: function(dateStr, userTimezone) {
		if (!dateStr) return dateStr;

		// 未传入时区则从缓存获取
		if (!userTimezone) {
			userTimezone = this.getUserTimezone();
		}
		if (!userTimezone) return dateStr;

		// 获取用户时区偏移
		var userOffset = this.getTimezoneOffset(userTimezone);
		if (userOffset === null || userOffset === undefined) return dateStr;

		// 如果用户时区与系统时区相同，确保格式后返回
		if (userOffset === this.SYSTEM_TZ_OFFSET) {
			// 确保输出格式为 YYYY-MM-DD HH:MM:SS
			var matchSame = String(dateStr).match(/(\d{4})-(\d{2})-(\d{2})\s+(\d{2}):(\d{2}):(\d{2})/);
			if (matchSame) return dateStr;
			// 尝试补全时间部分
			var matchDateOnly3 = String(dateStr).match(/(\d{4})-(\d{2})-(\d{2})/);
			if (matchDateOnly3) return dateStr + ' 00:00:00';
			return dateStr;
		}

		// 解析输入日期字符串（服务器 UTC+8 时间）
		var match = String(dateStr).match(/(\d{4})-(\d{2})-(\d{2})\s+(\d{2}):(\d{2}):(\d{2})/);
		if (!match) {
			// 尝试仅日期格式，不包含时间则直接返回
			var matchDateOnly4 = String(dateStr).match(/(\d{4})-(\d{2})-(\d{2})/);
			if (matchDateOnly4) return dateStr;
			return dateStr;
		}

		var y = +match[1];
		var m = +match[2];
		var d = +match[3];
		var h = +match[4];
		var min = +match[5];
		var s = +match[6];

		// 步骤1: 将服务器时间（UTC+8 的钟面时间）转为 UTC 时间戳
		// Date.UTC 把钟面数字当作 UTC 解释 → 减去8小时得到真正的 UTC 时间戳
		var realUtc = Date.UTC(y, m - 1, d, h, min, s) - this.SYSTEM_TZ_OFFSET * 3600000;

		// 步骤2: 加上用户时区偏移，得到用户本地时间戳
		var userLocal = realUtc + userOffset * 3600000;

		// 步骤3: 使用 UTC 方法格式化，避免本地时区干扰
		var resultDate = new Date(userLocal);
		var year = resultDate.getUTCFullYear();
		var month = String(resultDate.getUTCMonth() + 1).padStart(2, '0');
		var day = String(resultDate.getUTCDate()).padStart(2, '0');
		var hours = String(resultDate.getUTCHours()).padStart(2, '0');
		var minutes = String(resultDate.getUTCMinutes()).padStart(2, '0');
		var seconds = String(resultDate.getUTCSeconds()).padStart(2, '0');

		return year + '-' + month + '-' + day + ' ' + hours + ':' + minutes + ':' + seconds;
	}

}
export default dateFormatUtils;

export function deepClone(source) {
  if (!source && typeof source !== 'object') {
    throw new Error('error arguments', 'deepClone')
  }
  const targetObj = source.constructor === Array ? [] : {}
  Object.keys(source).forEach(keys => {
    if (source[keys] && typeof source[keys] === 'object') {
      targetObj[keys] = deepClone(source[keys])
    } else {
      targetObj[keys] = source[keys]
    }
  })
  return targetObj
}
