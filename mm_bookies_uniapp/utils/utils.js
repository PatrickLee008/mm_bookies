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
