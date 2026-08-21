<template>
	<view class="full-page dark-teal-bg">
		<zw-header></zw-header>

		<scroll-view scroll-y class="page padding-lr-sm padding-bottom-55px text-bold" @scroll="handle_scroll"
			style="line-height: 1.5;height:calc(var(--app-viewport-height, 100vh) - 240upx)">
			<!-- 联赛 -->
			<view class="flex-column padding-tb-sm" v-for="(league,index) in league_list" :key="index"
				v-show='league.favor'>
				<view class="mybg-league flex-row justify-between radius-10px text-white myfont-9px"
					style="padding: 6px 10px;">
					<view class="flex-row ">
						<view class="cuIcon-favorfill margin-right-sm myfont-12px"
							:class="{'mycolor-active':league.favor,}" @click="favor_click(league)"></view>
						<view class="" @click="league.show_match = !league.show_match">{{league.name}}</view>
					</view>
					<view class="flex-row gap-5px width-25 justify-end" @click="league.show_match = !league.show_match">
						<view class="cu-tag round sm mybg-active mycolor-primary min-width-30px margin-right-sm">
							{{league.match_list.length}}
						</view>
						<view class="myfont-12px" :class="league.show_match?'cuIcon-unfold':'cuIcon-fold'"></view>
					</view>
				</view>

				<transition name="match-animation" class="width-100" @before-enter="beforeEnter" @enter="enter"
					@leave="leave">
					<view v-show="league.show_match" class="width-100">
						<view class="flex-column radius-10px myfont-12px margin-top-2px padding-tb-sm league-match"
							v-for="(match,_index) in league.match_list" :key="_index">
							<view class="flex-row padding-bottom-8px mycolor-primary myfont-10px ">
								<view class="flex-column width-33 padding-lr-sm"
									:class="{'text-red':match.LOSE_TEAM ==='1',}">
									{{match.HOST_TEAM}}
								</view>
								<view class="flex-row width-34 justify-between myfont-9px"
									:id='`match-${index}-${_index}`'>
									<image :src="match.show_image?match.home_logo:''" lazy-load
										class="width-25px height-25px" @error="error_pic(match,'home')" />
									<view class="flex-column align-center " style="width: calc(100% - 10vw);">
										<view>{{match.MD_HHMM}}</view>
										<view class="myfont-7px text-light">{{match.MD_NOON}}</view>
										<view>{{match.MD_DDMM}}</view>
									</view>
									<image :src="match.show_image?match.away_logo:''" lazy-load
										class="width-25px height-25px" @error="error_pic(match,'away')" />
								</view>
								<view class="flex-column width-33 padding-lr-sm"
									:class="{'text-red':match.LOSE_TEAM ==='2',}">
									{{match.GUEST_TEAM}}
								</view>
							</view>
						</view>
					</view>
				</transition>
			</view>
		</scroll-view>

	</view>
</template>

<script>
	import language from '../../utils/language.js'
	import config from '../../utils/config.js'
	import match_mixins from '../match/components/mixins.js'

	export default {
		mixins: [match_mixins],
		data() {
			return {
				language: config.language,
				userInfo: null,
				isLogin: uni.getStorageSync('Authorization') || false,

				league_list: [],
				match_ref: {
					mixed: false,
					num: 0,
					bet_match: {
						sa: {}
					},
					match_detail: {},
					league_list: [],
				},

			}
		},
		onLoad() {
			this.userInfo = Object.assign({}, this.$store.state.userInfo)
		},
		mounted() {
			this.get_list()
		},
		methods: {
			get_list() {
				var _this = this;
				uni.showLoading({
					title: _this.$t('loading')
				})
				var para = {
					page: _this.list_query.page,
					limit: _this.list_query.limit,
					odds_type: 'single',
				}
				_this.$http.get('/match/get_favor', {
					data: para
				}, (res) => {
					if (res.statusCode == 200) {
						_this.loaddingData(res.data);
						uni.hideLoading();
						if (res.data.items.length == 0) {
							uni.showToast({
								title: _this.$t('no_favorite_data'),
								icon: 'none'
							})
						}
					}
				})
			},
			loaddingData(data) {
				//获取联赛数组
				let _this = this;
				if (data.total) {
					let server_matches = data.items
					let favor_leagues = data.favor_leagues
					let server_leagues = [...new Set(server_matches.map(ele => ele.LEAGUE))]
					// leauges排序
					server_leagues = _this.sort_object(server_leagues, '', config.leagues)
					let league_list = server_leagues.map(ele => {
						return {
							name: ele,
							checked: true,
							show_match: true,
							favor: favor_leagues.includes(ele),
							match_list: [],
						}
					})
					server_matches.forEach(match => {
						let time = new Date(match.MATCH_MD_TIME)
						match.home_pic = _this.get_ha_pic(match, 'home')
						match.away_pic = _this.get_ha_pic(match, 'away')
						match.MATCH_MD_DATE = time
						match.MD_NOON = time.getHours() > 12 ? 'PM' : 'AM'
						match.MD_DAY = `${time.toDateString().split(" ")[0]}`
						match.MD_HHMM =
							`${String(time.getHours()%12).padStart(2,'0')}:${String(time.getMinutes()).padStart(2,'0')}`
						match.MD_DDMM =
							`${String(time.getDate()).padStart(2,'0')} ${time.toDateString().split(" ")[1]}`
						match.SLIP_DATE =
							`@ ${match.MD_DDMM} ${time.getFullYear()} ${String(time.getHours()%12).padStart(2,'0')}:${String(time.getMinutes()).padStart(2,'0')}`
						let match_index = server_leagues.indexOf(match.LEAGUE)
						if (match_index > -1) {
							league_list[match_index].match_list.push(match)
						}
					})
					_this.league_list = league_list
					_this.$nextTick(() => {
						_this.handle_scroll()
					})
				}
			},
		}
	}
</script>

<style lang="scss">
	@import '../match/components/match.css';

	.dark-teal-bg {
		min-height: var(--app-viewport-height, 100vh);
	}
</style>