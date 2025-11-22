import config from '../../utils/config.js';
import uniPopup from "@/components/uni-popup/uni-popup.vue";
import uniLoadMore from "@/components/uni-load-more/uni-load-more.vue";
import dateFormatUtils from "../../utils/utils.js";
export default {
	data() {
		return {
			url_suffix_list: ['get', 'get_history'],
			url_prefix: '/order',
			btn_options:[],
			bet_time_options: ['all', 'one_week', 'one_month', ],
			bettype_options: ['all', 'single_bet', 'mix_bet', ],
			popup_str_2_int:{
				'bettype':0,
				'bet_time':1,
			},
			popup_type: 'bet_time',
			bet_type: {
				'MIX_BODY': '4',
				'MIX_GOAL': '5',
				'MIX_EVEN': '7',
				'MIX_WDL': '11',
				'SINGLE_BODY': '1',
				'SINGLE_GOAL': '2',
				'SINGLE_EVEN': '6',
				'SINGLE_WDL': '10',
			},
			list: [],
			modalName: '',
			listQuery: {
				date: '',
				time: 0,
				type: 0,
				is_mix: '',
				page: 1,
				limit: 100,
				end: false,
			},
			month_2_str: [
				"January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
				"November", "December"
			],
			extra_para: {},
			activeTab: 1,
			orderDetails: {
				detail: {},
				benefit: 0,
				orders: []
			},
			language: config.language
		};
	},
	methods: {
		calParlay(order) {
			let a = ''
			if (this.language.lang == 'mm') {
				a = `${order.REMARK.slice(0, order.REMARK.indexOf('x'))} ${this.language.parlay}`
			} else {
				a = `${this.language.parlay} ${order.REMARK}`
			}
			return a
		},
		cal_bet_content_class(order) {
			let a = ''
			if(order.ORDER_TYPE ==4){
				if((order.LOSE_TEAM == '1' && order.BET_CONTENT==order.HOME)||(order.LOSE_TEAM == '2' && order.BET_CONTENT==order.AWAY)){
					a = 'my-font-blue'
				}
			}
			return  'my-font-blue'
		},
		getCurrentDate(n) {
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
		popupOpen(typ) {
			this.popup_type = typ
			this.btn_options = this[`${typ}_options`]
			this.$refs.popup1.open()
		},
		buttonPress(typ, val) {
			typ == this.popup_str_2_int.bet_time ? this.$set(this.listQuery, 'time', val) : this.$set(this.listQuery, 'type', val)
			this.$refs.popup1.close()
			this.handleTabChange(null, true)
		},
		numberFormat(num) {
			return dateFormatUtils.numFormat(num)
		},
		handleTabChange(typ, force) {
			let list = [0, 1]
			if (this.activeTab === typ && !force) {
				return
			}
			list.includes(typ) ? this.activeTab = typ : ''
			this.listQuery.page = 1
			this.listQuery.end = false
			this.list = []
			this.getOrderList();
		},
		getOrderList() {
			var _this = this;
			uni.showLoading({
				title: 'Loading!'
			})
			let url = `/${_this.url_prefix}/${_this.url_suffix_list[_this.activeTab]}`
			var para = {
				page: _this.listQuery.page,
				limit: _this.listQuery.limit,
				start_time: _this.listQuery.time == 0 ? '' : _this.listQuery.time == 1 ? _this.getCurrentDate(7) :
					_this.getCurrentDate(30),
				end_time: _this.listQuery.time == 0 ? '' : _this.getCurrentDate(0),
				order_type: _this.listQuery.type == 3 ? 3 : '',
				is_mix: _this.listQuery.type == 2 ? 1 : _this.listQuery.type == 0 ? '' : 0,
			};
			para = Object.assign(para, _this.extra_para)
			_this.$http.get(url, {
				data: para
			}, (res) => {
				uni.hideLoading()
				if (res.statusCode == 200) {
					let results = res.data.items
					results.forEach(ele => {
						_this.list.push(_this.parseBetContent(ele));
					})

					if (results.length == 0) {
						_this.listQuery.end = true
					}
				}
			})
		},
		parseBetContent(_order) {
			let _this = this
			let ele = Object.assign({}, _order)
			let order_type = String(ele.ORDER_TYPE)
			if (ele.ORDER_DESC.indexOf('||') > -1) {
				var temp = ele.ORDER_DESC.split('||');
				ele.HOME = temp[0];
				ele.AWAY = temp[1];
			}
			if (ele.BET_HOST_TEAM_RESULT != null && ele.BET_GUEST_TEAM_RESULT != null) {
				ele.RESULT = ele.BET_HOST_TEAM_RESULT + '-' + ele.BET_GUEST_TEAM_RESULT;
			}
			if (ele.BET_HOST_TEAM_RESULT == '100') {
				ele.RESULT = _this.language.matchCancel;
			}
			ele.REMARK = ele.REMARK.replace('��', 'x')
			let time = new Date(new Date(ele.CREATE_TIME).valueOf() - 5400 * 1000)
			ele.CREATE_TIME = time
			ele.SHOW_CREATE_TIME = `${String(time.getDate()).padStart(2,'0')} ${_this.month_2_str[time.getMonth()]} ${String(time.getFullYear()).slice(2,4)} (${String(time.getHours()).padStart(2,'0')}:${String(time.getMinutes()).padStart(2,'0')})`
			ele.HMS =
				`${String(time.getHours()).padStart(2,'0')}:${String(time.getMinutes()).padStart(2,'0')}:${String(time.getSeconds()).padStart(2,'0')}`
			ele.YMD =
				`${time.getFullYear()}-${String(time.getMonth() + 1).padStart(2,'0')}-${String(time.getDate()).padStart(2,'0')}`
			ele.HM = `${String(time.getHours()).padStart(2,'0')}:${String(time.getMinutes()).padStart(2,'0')}`
			ele.MD = `${String(time.getMonth() + 1).padStart(2,'0')}-${String(time.getDate()).padStart(2,'0')}`
			ele.SHOW_CREATE_TIME2 = dateFormatUtils.formatTime(time).substring(5, 19);
			ele.MATCH_TIME = ele.MATCH_TIME.substring(5, 16);
			ele.DRAW_BUNKO = ele.DRAW_BUNKO == '0' ? '+' : '-';
			switch (true) {
				case ['1', '4'].includes(order_type):
					ele.ORDER_TYPE_SHOW = _this.language.body
					ele.BET_CONTENT = ele.BET_TYPE == '1' ?ele.HOME :ele.AWAY;
					ele.ODDS_DESC = '(' + ele.LOSE_BALL_NUM + ele.DRAW_BUNKO + ele.DRAW_ODDS + ')'
					break
				case ['2', '5'].includes(order_type):
					ele.ORDER_TYPE_SHOW = _this.language.goal
					ele.BET_CONTENT = ele.BALL_TYPE == '1' ? _this.language.over : _this.language.under;
					ele.ODDS_DESC = '(' + ele.LOSE_BALL_NUM + ele.DRAW_BUNKO + ele.DRAW_ODDS + ')'
					break
				case ['3', ].includes(order_type):
					ele.ORDER_TYPE_SHOW = 'Correct'
					ele.BET_CONTENT = ele.REMARK
					ele.ODDS_DESC = ele.BET_ODDS;
					break
				case ['6', '7'].includes(order_type):
					ele.ORDER_TYPE_SHOW = _this.language.odd_even
					ele.BET_CONTENT = ele.BET_TYPE == '1' ? _this.language.odd : _this.language.even;
					ele.ODDS_DESC = ele.BET_ODDS;
					break
				case ['10', '11'].includes(order_type):
					ele.ORDER_TYPE_SHOW = '1X2'
					ele.BET_CONTENT = (ele.BET_TYPE == '3' ? _this.language.wdl_draw :
							ele.BET_TYPE == '1' ?
							_this.language.wdl_home : _this.language.wdl_away) + ' ' + '@' +
						ele.BET_ODDS
					ele.ODDS_DESC = '';
					break
				case ['9'].includes(order_type):
					ele.ORDER_TYPE_SHOW = '3D'
					break
				case ['9'].includes(order_type):
					// ele.ORDER_TYPE = '3D'
					// ele.ODDS_DESC = '';
					break

			}
			return ele
		},
		showOrderDetails(row, type) {
			if (row.IS_MIX != '1') return;
			let _this = this;
			let url = `/${_this.url_prefix}/${_this.url_suffix_list[_this.activeTab]}`
			_this.orderDetails.detail = Object.assign({}, row);
			_this.orderDetails.orders = []
			let para = {
				order_id: row.ORDER_ID.replace(/\s*/g, ""),
				is_detail: true,
				limit:999,
			};
			para = Object.assign(para, _this.extra_para)
			_this.$http.get(url, {
				data: para
			}, (res) => {
				if (res.statusCode == 200) {
					let benefit_list = []
					let items = res.data.items
					items.sort((a,b)=>{
						return a.BET_TYPE - b.BET_TYPE
						// return b.BET_TYPE - a.BET_TYPE
					})
					items.sort((a,b)=>{
						return b.BONUS - a.BONUS
					})
					items.forEach(ele => {
						_this.orderDetails.orders.push(_this.parseBetContent(ele))
						benefit_list.push(parseFloat(ele.BET_MONEY) * parseFloat(ele.BET_ODDS))
					})
					if(_this.orderDetails.detail.ORDER_TYPE==='9'){
						_this.orderDetails.benefit = Math.max.apply(null,benefit_list)
					}else{
						_this.orderDetails.benefit = _this.orderDetails.detail.BET_MONEY * Math.pow(2,items.length)
					}
					
					// console.log(_this.orderDetails)
				}
			})
			_this.modalName = 'order_modal'
			// this.$refs.popup.open()
		},
		clickLoadMore() {
			if (this.listQuery.end) return
			this.listQuery.page++
			this.getOrderList()
		},
	},
	mounted() {
		this.listQuery.date = dateFormatUtils.formatDate(new Date().getTime(), 'Y-M-D');
		this.getOrderList()
	},
	created() {}
}