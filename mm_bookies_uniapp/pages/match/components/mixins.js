import config from '../../../utils/config.js'
import dateFormatUtils from "../../../utils/utils.js"
export default {
	data() {
		return {
			hide_match_detail: true,
			config: config,
			language: config.language,
			modalName: null,
			commission: 0,
			bet_type: {
				'SINGLE_BODY': '1',
				'SINGLE_GOAL': '2',
				'SINGLE_CORRECT': '3',
				'SINGLE_EVEN': '6',
				'SINGLE_Digit': '8',
				'SINGLE_WDL': '10',
				'MIX_BODY': '4',
				'MIX_GOAL': '5',
				'MIX_EVEN': '7',
				'SINGLE_Digit3D': '9',
				'MIX_WDL': '11',
				'SINGLE_BTTS': '18',
				'MIX_BTTS': '19',
			},
			list_query: {
				limit: 200,
				page: 1,
			},
		}
	},
	methods: {
		error_pic(match, ha) {
			match[`${ha}_pic`] = `https://storage.googleapis.com/onextwomm/football/shirt/${ha}.png?w=64&q=75`
		},
		beforeEnter(el) {
			el.style.opacity = 0
		},
		enter(el, done) {
			el.offsetWidth
			el.style.opacity = 1
			setTimeout(done, 500)
		},
		leave(el, done) {
			el.style.opacity = 0
			setTimeout(done, 500)
		},
		numberFormat(num) {
			return dateFormatUtils.numFormat(num)
		},
		favor_click(league) {
			if (this.$toolbox.click_too_fast(1)) return
			if (!this.isLogin) {
				this.hide_login_modal = false
				return
			}
			let _this = this
			let para = {
				league: league.name,
			}
			let url = 'favourite/add'
			let fail_content = _this.$t('add_favor_failed')
			if (league.favor) {
				fail_content = _this.$t('delete_favor_failed')
				url = 'favourite/delete'
			}
			_this.$http.post(url, para, (res) => {
				if (res.statusCode == 200) {
					let toast = _this.$t('add_favor_success')
					if (league.favor) {
						toast = _this.$t('remove_favor_success')
					}
					uni.showToast({
						title: toast,
						icon: 'none',
					})
					league.favor = !league.favor
					// _this.get_list()
				} else {
					this.$notice.show({
						content: fail_content,
						title: _this.$t('tips'),
						showCancel: false,
						confirmText: _this.$t('ok')
					})
				}
			})
		},
		handle_scroll(event) {
			const scrollTop = event ? event.detail.scrollTop : 0;

			const query = uni.createSelectorQuery().in(this);
			let windowHeight = 0;
			uni.getSystemInfo({
				success: (res) => {
					windowHeight = res.windowHeight;
				}
			});
			this.league_list.forEach((league, index) => {
				league.match_list.forEach((match, _index) => {
					query.select(`#match-${index}-${_index}`).boundingClientRect(data => {
						if (data && data.top < windowHeight + scrollTop) {
							this.$set(this.league_list[index].match_list[_index],
								'show_image', true);
						}
					}).exec();
				})
			})
		},
		sort_object(list, attr = '', sort_list = []) {
			// 对象列表根据attr参数进行排序,字符串列表直接排序,优先根据sort_list字符串列表进行排序,再根据字母排序
			return list.sort((a, b) => {
				// console.log(a[attr])
				const cp_a = typeof a === 'string' ? a : a[attr]
				const cp_b = typeof b === 'string' ? b : b[attr]
				const indexA = sort_list.indexOf(cp_a);
				const indexB = sort_list.indexOf(cp_b);
				if (indexA !== -1 && indexB !== -1) return indexA - indexB;
				if (indexA !== -1) return -1;
				if (indexB !== -1) return 1;
				return cp_a.localeCompare(cp_b);
			});
		},
		calc_detail_odds(attr) {
			if (!attr.hasOwnProperty('MATCH_ATTR_TYPE')) return ''
			if ([this.bet_type.SINGLE_WDL].includes(attr.MATCH_ATTR_TYPE)) {
				return ''
			}
			let str = ''
			switch (true) {
				case attr.host_selected:
					str = attr.ODDS
					break
				case attr.guest_selected:
					str = attr.ODDS_GUEST
					break
				case attr.draw_selected:
					str = attr.DRAW_ODDS
					break
			}
			return str
		},
		bet_type_2_str(attr, typ = 'MATCH_ATTR_TYPE') {
			if (!attr.hasOwnProperty(typ)) return ''
			let str = ''
			switch (true) {
				case [this.bet_type.SINGLE_BODY, this.bet_type.MIX_BODY].includes(attr[typ]):
					str = 'HANDICAP'
					break
				case [this.bet_type.SINGLE_GOAL, this.bet_type.MIX_GOAL].includes(attr[typ]):
					str = 'TOTAL'
					break
				case [this.bet_type.SINGLE_EVEN, this.bet_type.MIX_EVEN].includes(attr[typ]):
					str = 'EVEN'
					break
				case [this.bet_type.SINGLE_WDL].includes(attr[typ]):
					str = '1X2'
					break
			}
			return str
		},
		bet_content(match) {
			if (!match.hasOwnProperty('sa')) return ''
			let attr = match.sa
			let str = ''
			switch (true) {
				case [this.bet_type.SINGLE_BODY, this.bet_type.MIX_BODY].includes(attr.MATCH_ATTR_TYPE):
					if (attr.host_selected) {
						str = match.HOST_TEAM
						// str = this.match_ref.mixed ? this.$t('home') : match.HOST_TEAM
					} else {
						str = match.GUEST_TEAM
						// str = this.match_ref.mixed ? this.$t('away') : match.GUEST_TEAM
					}
					break
				case [this.bet_type.SINGLE_GOAL, this.bet_type.MIX_GOAL].includes(attr.MATCH_ATTR_TYPE):
					if (attr.host_selected) {
						str = this.$t('over')
					} else {
						str = this.$t('under')
					}
					break
				case [this.bet_type.SINGLE_EVEN, this.bet_type.MIX_EVEN].includes(attr.MATCH_ATTR_TYPE):
					if (attr.host_selected) {
						str = this.$t('odd')
					} else {
						str = this.$t('even')
					}
					break
				case [this.bet_type.SINGLE_WDL].includes(attr.MATCH_ATTR_TYPE):
					if (attr.host_selected) {
						str = 'HOME'
						// return this.$t('wdl_home')
					} else if (attr.guest_selected) {
						str = 'AWAY'
						// return this.$t('wdl_away')
					} else {
						str = 'DRAW'
						// return this.$t('wdl_draw')
					}
					break
			}
			return str
		},
		attr_content(attr, odd_type) {
			let str = ''
			switch (true) {
				case [this.bet_type.SINGLE_BODY, this.bet_type.MIX_BODY].includes(attr.MATCH_ATTR_TYPE):
					if (odd_type == 1) {
						str = this.$t('home')
					} else {
						str = this.$t('away')
					}
					break
				case [this.bet_type.SINGLE_GOAL, this.bet_type.MIX_GOAL].includes(attr.MATCH_ATTR_TYPE):
					if (odd_type == 1) {
						str = this.$t('over')
					} else {
						str = this.$t('under')
					}
					break
				case [this.bet_type.SINGLE_EVEN, this.bet_type.MIX_EVEN].includes(attr.MATCH_ATTR_TYPE):
					if (odd_type == 1) {
						str = this.$t('odd')
					} else {
						str = this.$t('even')
					}
					break
				case [this.bet_type.SINGLE_WDL].includes(attr.MATCH_ATTR_TYPE):
					if (odd_type == 1) {
						str = 'HOME'
					} else if (odd_type == 2) {
						str = 'AWAY'
					} else {
						str = 'DRAW'
					}
					break
			}
			return str
		},

	},
	computed: {
		calc_page_height() {
			let info = uni.getDeviceInfo()
			if (info.platform == 'ios') {
				return `calc(var(--app-viewport-height, 100vh) - 85px)`
			}
			return 'var(--app-viewport-height, 100vh)'
		},

	},
	mounted() {},
	onLoad(option) {}
}