<template>
	<view class="mybg-grey full-page">
		<cu-custom isBack backUrl="/pages/index/index">
			<block slot="content">{{$t('score')}}
			</block>
			<block slot="right">
				<view style="width: 30vw;" @tap="showModal" class="padding-xs" data-target="Modal">
					<!-- <image style="width:25px;height: 25px;float: right;margin-right: 10px;" :style="filterScale"
						src="../../static/image/shaixuan.png"></image> -->
				</view>
			</block>
		</cu-custom>


		<view class="flex-row" style="justify-content: space-around;">
			<view class="text-center padding radius" style="width: 15%;"
				:style="live ? 'background-color: #0081ff;color:white;':''" @click="live = !live">Live</view>
			<view class="flex-row" style="width: 85%;margin: 1px;justify-content: space-around;">
				<view class="myrect flex-column" :class="index == selectDay ? 'bg-blue':'mybg-dgrey'"
					@click="dayClick(index)" style="width: 17%;margin: 1px;" v-for="(day,index) in days">
					<text>{{day.day}}</text>
					<text>{{day.date}}</text>
				</view>
			</view>
		</view>

		<view class="cu-modal drawer-modal justify-start" :class="modalName=='Modal'?'show':''" @tap="hideModal">
			<view class="cu-dialog basis-lg">
				<scroll-view scroll-y @tap.stop="" style="margin-top: 50px;"
					:style="[{top:CustomBar+'px',height:'calc(100vh - 50px - ' + CustomBar + 'px)'}]">
					<view class="cu-list menu text-left">
						<view class="league-row">
							<image style="height: 16px;width: 16px;" v-show="allStatus"
								src="../../static/icon/checked.png" @click="selectAll"></image>
							<image style="height: 16px;width: 16px;" v-show="!allStatus"
								src="../../static/icon/unchecked.png" @click="selectAll"></image>
							<text class="margin-left text-bold" style="width: 160px;">
								{{'&nbsp&nbsp&nbsp&nbsp&nbspAll'}}
							</text>
						</view>
						<view class="league-row" @tap="ChooseCheckbox" :data-value="item.name"
							v-for="(item,index) in leagueObjs" :key="index">
							<image style="height: 16px;width: 20px;" v-show="item.checked"
								src="../../static/icon/checked.png"></image>
							<image style="height: 16px;width: 20px;" v-show="!item.checked"
								src="../../static/icon/unchecked.png"></image>
							<image style="height: 15px;width: 26px;margin: 0 3px 0 8px;"
								:src="imgPreUrl2 + item.region.toLowerCase().replaceAll(' ','-') + '.jpg'"></image>
							<view class="flex-column ">
								<text class="text-bold" style="width: 150px;">
									{{item.region}}
								</text>
								<text class="" style="width: 150px">
									{{item.name}}
								</text>
							</view>
							<!-- <view class="flex-column ">
								<text class="text-bold" style="width: 150px">
									{{item.region + ' '}}{{item.name}}
								</text>
								<text class="" style="width: 150px;">
									
								</text>
							</view> -->
						</view>
					</view>
				</scroll-view>
				<view class="padding-sm flex flex-direction">
					<button class="cu-btn mybg-red lh" @click="setLeagueFilter"> Ok </button>
				</view>
			</view>
		</view>
		<scroll-view class="flex-column" scroll-y style="height: calc(100vh - 45px - 66px);"
			@scrolltolower="clickLoadMore">
			<view v-for="league in filterList" v-if="live ? league.live : true">
				<view class="flex-row padding">
					<image style="height: 25px;width: 35px;margin: 0 3vw 0 3vw;" :lazy-load='true' class="padding"
						:src="imgPreUrl2 + league.region.toLowerCase().replaceAll(' ','-') + '.jpg'"></image>
					<view class="flex-column" style="width: 70%;align-items: flex-start;">
						<view class="myfont-bold">{{league.name}}</view>
						<view>{{league.region}}</view>
					</view>
				</view>
				<view v-for="(result,index) in league.results" v-if="live ? result.status == 1 : true"
					@click="getMatchResultDetail(result)" class="myrect bg-white flex-row"
					style="width: 96vw;margin: 1vw 2vw;min-height: 50px;border-radius: 10px;">
					<view style="width: 18%;" :class="result.status == 1 ? 'text-orange':''">
						{{result.status == 0 ? result.begin_time.slice(-8,-3) : result.sta_desc }}
					</view>
					<view class="flex-column" style="width: 70%;align-items: flex-start;">
						<view class="flex-row padding">
							<image class="team-icon" :lazy-load='true' :src="imgPreUrl + result.host_team_icon" />
							<text>{{result.host_team}}</text>
						</view>
						<view class="flex-row padding">
							<image class="team-icon" :lazy-load='true' :src="imgPreUrl + result.guest_team_icon" />
							<text>{{result.guest_team}}</text>
						</view>
					</view>
					<view class="flex-column" style="width: 10%;font-size: 15px;" v-if="result.status == 2">
						<view class="padding myfont-bold">{{result.full_host_score}}</view>
						<view class="padding myfont-bold">{{result.full_guest_score}}</view>
					</view>
					<view class="flex-column" style="width: 10%;font-size: 15px;" v-else>
						<view class="padding myfont-bold">{{result.half_host_score}}</view>
						<view class="padding myfont-bold">{{result.half_guest_score}}</view>
					</view>
				</view>
			</view>


		</scroll-view>

		<uni-popup ref="popup" type="center">
			<view class="popup">
				<view class="text-center text-bold mybg-red border"
					style="border-radius:13px 13px 0 0;height: 46px;line-height: 46px;">{{$t('detail')}}</view>
				<view class="mybg-grey" style="padding-top: 10px;">
					<scroll-view scroll-y style="height: 70vh;">
						<view class="myrect flex-row bg-white"
							style="justify-content: space-around;width: 96%;margin: 0 2% 0 2%;">
							<view class="flex-column padding">
								<image class="team-icon2" :src="imgPreUrl + resultDetail.host_team_icon"></image>
								<text>{{resultDetail.host_team}}</text>
							</view>
							<view class="flex-column">
								<text v-if="resultDetail.end_time"
									class="myfont-bold">{{resultDetail.full_host_score + ' - ' + resultDetail.full_guest_score}}</text>
								<text v-else
									class="myfont-bold">{{resultDetail.half_host_score + ' - ' + resultDetail.half_guest_score}}</text>
								<text v-if="resultDetail.end_time">Full Time</text>
								<text v-else>{{resultDetail.begin_time}}</text>
							</view>
							<view class="flex-column padding">
								<image class="team-icon2" :src="imgPreUrl + resultDetail.guest_team_icon"></image>
								<text>{{resultDetail.guest_team}}</text>
							</view>
						</view>
						<!-- 上半场 -->
						<view class="flex-column" style="justify-content: flex-start;margin-top: 15px;">
							<view v-for="(detail,index) in resultDetail.details" v-if="detail.phase == 1"
								class="myrect bg-white flex-row"
								style="min-height: 50px;width: 96%;margin: 0px 2% 10px 2%;border-radius: 10px;">
								<view style="width: 20%;">
									{{detail.minute + (detail.min_ex > 0 ? '+' + detail.min_ex : '')}}'
								</view>
								<view class="flex-row" style="width: 80%;">
									<view class="flex-column padding" style="width: 40%;font-size: 11px;">
										<span class="text-bold flex-row"
											v-if="detail.belong_team == 1">{{detail.results[0].player_name}}
											<view>
												<view style="height: 15px;width: 15px;" :style="detail.bg?detail.bg:''">
												</view>
												<view v-if="detail.og">OG</view>
											</view>
										</span>
										<text class="flex-row"
											v-if="detail.belong_team == 1 && detail.doubleLine">{{detail.results[1].player_name}}</text>
									</view>
									<view class="flex-row padding text-bold"
										style="width: 20%;justify-content: center;">
										<text
											v-if="detail.host_score || detail.guest_score">{{detail.host_score + ' - ' + detail.guest_score}}</text>
									</view>
									<view class="flex-column padding" style="width: 40%;font-size: 11px;">
										<span class="text-bold flex-row" v-if="detail.belong_team == 2">
											<view>
												<view style="height: 15px;width: 15px;" :style="detail.bg?detail.bg:''">
												</view>
												<view v-if="detail.og">OG</view>
											</view>
											{{detail.results[0].player_name}}
										</span>
										<text class="flex-row" style="margin-left: 33px;"
											v-if="detail.belong_team == 2 && detail.doubleLine">{{detail.results[1].player_name}}</text>
									</view>
								</view>
							</view>
							<!-- 半场比分 -->
							<view class="myrect bg-white flex-row" v-if="resultDetail.end_time"
								style="min-height: 50px;width: 96%;margin: 0px 2% 10px 2%;border-radius: 10px;">
								<view style="width: 20%;">
									HT
								</view>
								<view class="flex-row" style="width: 80%;">
									<view class="flex-column padding" style="width: 35%;">
									</view>
									<view class="flex-row padding text-bold"
										style="width: 30%;justify-content: center;">
										<text>{{resultDetail.half_host_score + ' - ' + resultDetail.half_guest_score}}</text>
									</view>
									<view class="flex-column padding" style="width: 35%;">
									</view>
								</view>
							</view>
							<!-- 下半场 -->
							<view v-for="(detail,index) in resultDetail.details" v-if="detail.phase == 2"
								class="myrect bg-white flex-row"
								style="min-height: 50px;width: 96%;margin: 0px 2% 10px 2%;border-radius: 10px;">
								<view style="width: 20%;">
									{{detail.minute + (detail.min_ex > 0 ? '+' + detail.min_ex : '')}}'
								</view>
								<view class="flex-row" style="width: 80%;">
									<view class="flex-column padding" style="width: 40%;font-size: 11px;">
										<span class="text-bold flex-row"
											v-if="detail.belong_team == 1">{{detail.results[0].player_name}}
											<view>
												<view style="height: 15px;width: 15px;" :style="detail.bg?detail.bg:''">
												</view>
												<view v-if="detail.og">OG</view>
											</view>
										</span>
										<text class="flex-row"
											v-if="detail.belong_team == 1 && detail.doubleLine">{{detail.results[1].player_name}}</text>
									</view>
									<view class="flex-row padding text-bold"
										style="width: 20%;justify-content: center;">
										<text
											v-if="detail.host_score || detail.guest_score">{{detail.host_score + ' - ' + detail.guest_score}}</text>
									</view>
									<view class="flex-column padding" style="width: 40%;font-size: 11px;">
										<span class="text-bold flex-row" v-if="detail.belong_team == 2">
											<view>
												<view style="height: 15px;width: 15px;" :style="detail.bg?detail.bg:''">
												</view>
												<view v-if="detail.og">OG</view>
											</view>
											{{detail.results[0].player_name}}
										</span>
										<text class="flex-row" style="margin-left: 33px;"
											v-if="detail.belong_team == 2 && detail.doubleLine">{{detail.results[1].player_name}}</text>
									</view>
								</view>
							</view>
							<!-- 全场比分 -->
							<view class="myrect bg-white flex-row" v-if="resultDetail.end_time"
								style="min-height: 50px;width: 96%;margin: 0px 2% 10px 2%;border-radius: 10px;">
								<view style="width: 20%;">
									FT
								</view>
								<view class="flex-row" style="width: 80%;">
									<view class="flex-column padding" style="width: 35%;">
									</view>
									<view class="flex-row padding text-bold"
										style="width: 30%;justify-content: center;">
										<text>{{resultDetail.full_host_score + ' - ' + resultDetail.full_guest_score}}</text>
									</view>
									<view class="flex-column padding" style="width: 35%;">
									</view>
								</view>
							</view>
							<!-- 加时 -->
							<view v-for="(detail,index) in resultDetail.details" v-if="detail.phase == 3"
								class="myrect bg-white flex-row"
								style="min-height: 50px;width: 96%;margin: 0px 2% 10px 2%;border-radius: 10px;">
								<view style="width: 20%;">
									{{detail.minute + (detail.min_ex > 0 ? '+' + detail.min_ex : '')}}'
								</view>
								<view class="flex-row" style="width: 80%;">
									<view class="flex-column padding" style="width: 40%;font-size: 11px;">
										<span class="text-bold flex-row"
											v-if="detail.belong_team == 1">{{detail.results[0].player_name}}
											<view>
												<view style="height: 15px;width: 15px;" :style="detail.bg?detail.bg:''">
												</view>
												<view v-if="detail.og">OG</view>
											</view>
										</span>
										<text class="flex-row"
											v-if="detail.belong_team == 1 && detail.doubleLine">{{detail.results[1].player_name}}</text>
									</view>
									<view class="flex-row padding text-bold"
										style="width: 20%;justify-content: center;">
										<text
											v-if="detail.host_score || detail.guest_score">{{detail.host_score + ' - ' + detail.guest_score}}</text>
									</view>
									<view class="flex-column padding" style="width: 40%;font-size: 11px;">
										<span class="text-bold flex-row" v-if="detail.belong_team == 2">
											<view>
												<view style="height: 15px;width: 15px;" :style="detail.bg?detail.bg:''">
												</view>
												<view v-if="detail.og">OG</view>
											</view>
											{{detail.results[0].player_name}}
										</span>
										<text class="flex-row" style="margin-left: 33px;"
											v-if="detail.belong_team == 2 && detail.doubleLine">{{detail.results[1].player_name}}</text>
									</view>
								</view>
							</view>
						</view>
					</scroll-view>

				</view>


				<view class="mybg-pink text-center basis-df flex-column"
					style="border-radius: 0 0  13px 13px ;height: 46px;">
					<button class="cu-btn mybg-orange" style="width: 60%;" @click="$refs.popup.close()">OK</button>
				</view>
			</view>
		</uni-popup>

	</view>
</template>

<script>
	import dateFormatUtils from '../../utils/utils.js'
	import Vue from "vue";
	export default {
		components: {
		},
		data() {
			return {
				months: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sept', 'Oct', 'Nov', 'Dec', ],
				days: ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', ],
				selectDay: null,
				results: [],
				leagueObjs: [],
				leagueArr: [],
				list: [],
				imgPreUrl: 'https://lsm-static-prod.livescore.com/medium/',
				imgPreUrl2: 'https://static.livescore.com/i2/fh/',
				matches: [],
				red_car: '',
				live: false,
				resultDetail: {},
				allStatus: false,
				filterScale: '',
				modalName: null,
				listQuery: {
					limit: 200,
					page: 1,
				},

				filterList: [],
				config: config
			}
		},
		methods: {
			toHome() {
				uni.reLaunch({
					url: '/pages/index/index'
				})
			},
			handleDateChange(filter) {
				this.listQuery.page = 1; //重置页数
				this.results.length = 0; //重置缓存数据
				this.filterList.length = 0;
				this.listQuery.start_time = filter.start_time.slice(0, 10);
				this.listQuery.end_time = filter.start_time.slice(0, 10);
				this.getMatchResult();
			},
			getMatchResult() {
				var _this = this;

				uni.showLoading({
					title: 'loading'
				})
				_this.$http.get('/tech_result', {
					data: _this.listQuery
				}, (res) => {
					if (res.statusCode == 200) {

						uni.hideLoading();
						if (res.data.items.length == 0) {
							uni.showToast({
								title: 'no more',
								icon: 'none'
							})
						} else {
							res.data.items.forEach(match => {
								// match.MATCH_TIME = match.MATCH_TIME.substring(10, 16);
								if(match.status == 0){
									match.half_host_score = '-'
									match.half_guest_score = '-'
								}
							})
							_this.results = _this.results.concat(res.data.items);
							_this.loadingData(_this.results);
						}
					} else {
						uni.showToast({
							title: 'Error!' + res.data.message,
							icon: 'none'
						})
					}
				})
			},
			getMatchResultDetail(row) {
				if (row.status == 0) {
					return
				}
				let _this = this;

				uni.showLoading({
					title: 'loading'
				})
				_this.$http.get('/tech_result/' + row.id, {}, (res) => {
					uni.hideLoading()
					if (res.statusCode == 200) {
						_this.resultDetail = res.data.item
						_this.resultDetail.details = _this.parseResultDetail(res.data.item)
						_this.showPopup()
					}
				})
			},
			parseResultDetail(item) {
				let minuts = []
				let minuts_result = []
				// let 
				item.details.forEach((ele, index) => {
					let min_add = String(ele.minute) + '-' + String(ele.min_ex)
					if (minuts.indexOf(min_add) < 0) {
						minuts.push(min_add)
					}
				})
				// 按时间排序
				// minuts.sort(function(a, b) {
				// 	return a - b
				// })
				// minuts.forEach((el, inde) => {
				// 	let min_split = el.split('-')
				// 	var temp = {
				// 		minute: min_split[0],
				// 		min_ex: min_split[1],
				// 		results: []
				// 	}
				// 	item.details.forEach(detail => {
				// 		// 球员名字过长处理
				// 		if (detail.player_name.length > 10) {
				// 			let player_name_split = detail.player_name.split(' ')
				// 			let new_name = ''
				// 			player_name_split.forEach((e, i) => {
				// 				if (i + 1 < player_name_split.length) {
				// 					new_name += e.slice(0, 1) + '. '
				// 				} else if (e.length > 9) {
				// 					new_name += e.slice(0, 1) + '. '
				// 				} else {
				// 					new_name += e
				// 				}
				// 			})
				// 			detail.player_name = new_name
				// 		}
				// 		if (detail.minute == min_split[0] && detail.min_ex == min_split[1]) {
				// 			let pic = this.parseDetailPic(detail)
				// 			pic.bg ? temp.bg = pic.bg : '',
				// 				pic.og ? temp.og = pic.og : '',
				// 				// console.log(pic)
				// 				temp.belong_team = detail.belong_team
				// 			temp.guest_score = detail.guest_score
				// 			temp.host_score = detail.host_score
				// 			temp.phase = detail.phase
				// 			temp.results.push(detail);
				// 		}
				// 	})
				// 	temp.doubleLine = temp.results.length >= 2
				// 	if (temp.doubleLine) {
				// 		temp.bg = temp.bg + 'margin-top:15px;'
				// 	}
				// 	temp.results.sort(function(a, b) {
				// 		return a.tech_type - b.tech_type
				// 	})
				// 	minuts_result.push(temp)
				// })


				item.details.forEach((detail, index) => {
					var temp = {
						minute: detail.minute,
						min_ex: detail.min_ex,
						results: []
					}
					if (detail.player_name.length > 10) {
						let player_name_split = detail.player_name.split(' ')
						let new_name = ''
						player_name_split.forEach((e, i) => {
							if (i + 1 < player_name_split.length) {
								new_name += e.slice(0, 1) + '. '
							} else if (e.length > 9) {
								new_name += e.slice(0, 1) + '. '
							} else {
								new_name += e
							}
						})
						detail.player_name = new_name
					}
					let pic = this.parseDetailPic(detail)
					pic.bg ? temp.bg = pic.bg : '';
					pic.og ? temp.og = pic.og : '';
					temp.belong_team = detail.belong_team
					temp.guest_score = detail.guest_score
					temp.host_score = detail.host_score
					temp.phase = detail.phase
					if (detail.tech_type == 36) {
						temp.results.push(detail);
						item.details.forEach((_detail, _index) => {
							if (_detail.tech_type == 63 && detail.minute == _detail.minute && detail
								.min_ex == _detail.min_ex) {
								temp.results.push(_detail);
								temp.doubleLine = true
							}
						})
						if (temp.doubleLine) {
							temp.bg = temp.bg + 'margin-top:15px;'
						}
						minuts_result.push(temp)
					} else if (detail.tech_type != 63) {
						temp.results.push(detail);
						minuts_result.push(temp)
					}
				})
				console.log(minuts_result)
				return minuts_result
			},
			parseDetailPic(detail) {
				let pic = {
					bg: null,
					og: false
				}
				switch (detail.tech_type) {
					// 进球
					case 36:
						pic.bg = 'background-image: url(../../static/image/FootballGoal.svg);'
						break
						// 
					case 37:
						pic.bg = 'background-image: url(../../static/image/FootballGoalPen.svg);'
						break
						// 乌龙球
					case 39:
						pic.bg = 'background-image: url(../../static/image/FootballOwnGoal.svg);'
						pic.og = true
						break
						// 黄牌
					case 43:
						pic.bg =
							'background-image: url(../../static/image/FootballYellowCard.svg);height: 15px;width: 11px;'
						break
						// 黄红牌
					case 44:
						pic.bg = 'background-image: url(../../static/image/FootballRedYellowCard.svg);'
						break
						// 红牌
					case 45:
						pic.bg = 'background-image: url(../../static/image/FootballRedCard.svg);height: 15px;width: 11px;'
						break
						// 助攻
					case 63:
						pic.bg = 'background-image: url(../../static/image/FootballGoal.svg);margin-top:15px;'
						break
				}
				if (pic.bg) {
					pic.bg = detail.belong_team == 1 ? pic.bg + 'margin-left:3px;' : pic.bg + 'margin-right:3px;'
				}
				return pic
			},
			hidePopup() {
				this.$refs.popup.close()
			},
			showPopup() {
				this.$refs.popup.open()
			},
			clickLoadMore() {
				this.listQuery.page++;
				this.getMatchResult();
			},
			selectAll() {
				if (!this.allStatus) {
					this.allStatus = true;
					this.leagueObjs.forEach(element => {
						element.checked = true;
					})
				} else {
					this.allStatus = false;
					this.leagueObjs.forEach(element => {
						element.checked = false;
					})
				}
			},
			loadingData(arr) {
				this.list.length = 0;
				this.leagueObjs.length = 0;
				var leagueArr = [];
				var regionArr = [];
				arr.forEach(element => {
					if (leagueArr.indexOf(element.league) < 0) {
						leagueArr.push(element.league);
						regionArr.push(element.region)
					}
				})
				leagueArr.forEach((league, index) => {
					var leagueObj = {
						name: league,
						region: regionArr[index],
						checked: false,
					}
					this.leagueObjs.push(leagueObj);
					var temp = {
						name: league,
						region: regionArr[index],
						results: []
					}
					arr.forEach(match => {
						if (match.league == league) {
							if (match.status == 1) {
								leagueObj.live = true
								temp.live = true
							}
							// if(match.region  == 'Mexico'){
							// 	console.log(match)
							// }
							temp.results.push(match);
						}
					})
					this.list.push(temp);
				})

				this.list.sort(function(a, b) {
					return a.name.charCodeAt(0) - b.name.charCodeAt(0);
				})

				config.leagues2.forEach(leagueOfConfig => {
					this.list.forEach((leagueOfList, index) => {
						if (leagueOfConfig.toUpperCase() == leagueOfList.name.toUpperCase()) {
							//将该元素 置顶
							this.list.unshift(this.list.splice(index, 1)[0]);
						}
					})
				})

				this.filterList = [].concat(this.list);


				this.leagueObjs.sort(function(a, b) {
					return a.name.localeCompare(b.name)
					// return a.name.charCodeAt(0) - b.name.charCodeAt(0);
				})

				this.leagueObjs.sort(function(a, b) {
					return a.region.localeCompare(b.region)
					// return a.region.charCodeAt(0) - b.region.charCodeAt(0);
				})

				//读取config中的联赛并置顶
				var config_leagues = [];
				config.leagues2.forEach(league => {
					this.leagueObjs.forEach((_league, index) => {
						if (league.toUpperCase() == _league.name.toUpperCase()) {
							this.leagueObjs.unshift(this.leagueObjs.splice(index, 1)[0]);
						}
					})
				})

			},
			ChooseCheckbox(e) {
				let items = this.leagueObjs;
				let values = e.currentTarget.dataset.value;
				for (let i = 0, lenI = items.length; i < lenI; ++i) {
					if (items[i].name == values) {
						items[i].checked = !items[i].checked;
						break
					}
				}
			},
			setLeagueFilter() {
				//全不选
				let noSelect = true;
				this.leagueObjs.forEach(league => {
					if (league.checked) {
						noSelect = false;
					}
				})
				if (!noSelect) {
					this.filterList = [];
					this.leagueObjs.forEach(league => {
						if (league.checked) {
							this.list.forEach(_league => {
								if (_league.name == league.name) {
									this.filterList.push(_league);
								}
							})
						}
					})
				}
				this.hideModal();
			},
			dayClick(index) {
				this.selectDay = index
				this.listQuery.start_time = this.days[index].date2;
				this.listQuery.end_time = this.days[index].date2;
				this.listQuery.page = 1; //重置页数
				this.results.length = 0; //重置缓存数据
				this.filterList.length = 0;
				this.getMatchResult()
			},
			getDays() {
				let day = new Date()
				// let today = day.getDay() - 1
				let days = []
				for (let i = 0; i < 5; i++) {
					let dates = dateFormatUtils.getCurrentDate2(2 - i)
					let date_split = dates[0].split('-')
					let date = this.months[parseInt(date_split[0] - 1)] + ' ' + date_split[1]
					let tmp = {
						date: date,
						date2: dates[2],
						day: 2 - i == 0 ? 'Today' : this.days[dates[1]],
					}
					days.push(tmp)
				}
				// console.log(days)
				this.days = days
				this.dayClick(2)
				// this.selectDay = 2
			},
			showModal(e) {
				this.filterScale = 'filter: grayscale(100%)'
				this.modalName = e.currentTarget.dataset.target
			},
			hideModal(e) {
				this.filterScale = ''
				this.modalName = null
			}
		},
		mounted() {
			this.getDays()
		}
	}
</script>

<style>
	.team-icon {
		width: 20px;
		height: 20px;
		margin-right: 5px;
	}

	.team-icon2 {
		width: 30px;
		height: 30px;
	}

	.padding {
		padding: 5px;
	}

	.league-row {
		padding: 5px;
		display: flex;
		flex-direction: row;
		justify-content: flex-start;
		align-items: center;
	}

	.league-row image {
		width: 25px;
		height: 25px;
	}

	.bg-gray {
		background-color: #8a8a8a;
	}

	.page {
		width: 100vw;
		margin-bottom: 80px;
	}

	.line-grey {
		height: 1px;
		width: 100%;
		background-color: #E2E2E2;
		margin-top: 5px;
	}

	.bg-lightgrey {
		background-color: #E2E2E2;
	}

	.text-score :first-child {
		float: left;
		width: 44%;
	}

	.bg-green {
		background-color: rgb(41, 150, 56)
	}

	.popup {
		width: 96vw;
	}

	.text-score :nth-child(2) {
		float: left;
		width: 12%;
	}

	.bg-orange {
		background-color: rgb(246, 156, 87);
	}

	.text-orange {
		color: rgb(246, 156, 87);
	}

	.text-score :nth-child(3) {
		float: left;
		width: 44%;
	}

	.content {
		left: 10px !important;
	}
</style>
