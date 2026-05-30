<template>
	<view class="cu-modal " :class="{'show':!hidden,}" @click="set_dialog_hide(true)">
		<view class="cu-dialog padding-sm width-100" style="vertical-align: top;background: none;" @click.stop="">
			<view class="min-height-30vw bg-white radius-10px padding-sm">
				<view class="flex-row mycolor-primary margin-tb-sm" style="">
					<view class="cuIcon-back mycolor-info" @click="set_dialog_hide(true)"></view>
					<view class="flex-row justify-between margin-right radius-6px padding-tb-xs padding-lr-sm">
						<input class="width-100 text-left padding-right-sm myfont-12px" :placeholder="$t('search')"
							placeholder-class="holder-class" v-model="search_query" @input="handle_search" />
						<view
							class="cuIcon-close round width-17px height-16px line-height-16px myfont-8px round mybg-info text-white"
							v-if="search_query" style="" @click="clear_search_query"></view>
					</view>
				</view>
				<view class="flex-column myfont-10px">
					<view class="flex-row gap-5px line-height-25px">
						<view class="mybg-lprimary round padding-lr " @click="check_filter(index)"
							:class="{'mybg-active text-black':item.checked,}" v-for="(item,index) in filter_list" :key='index'>
							{{item.label}}
						</view>
					</view>
					<view class="flex-column" v-show="recent_search.length">
						<view class="margin-tb-sm mybg-linfo width-100 height-3upx" />
						<view class="text-bold mycolor-primary text-left width-100 myfont-12px">
							Recent Search
						</view>
						<view class="flex-row flex-wrap gap-5px min-height-10vw">
							<view class="mybg-lprimary radius-6px padding-lr-sm" v-for="(h,index) in recent_search"
								:key="index" @click="select_item(h,true)">
								{{h.name}}
							</view>
						</view>
					</view>
					<view class="margin-tb-sm mybg-linfo width-100 height-3upx" />
					<view class="text-bold mycolor-primary text-left width-100 myfont-12px">
						Result ({{current_type}})
					</view>
					<scroll-view v-show="search_results.length" :show-scrollbar="true" scroll-y
						class="flex-column height-40vh gap-5px myfont-10px text-bold mycolor-primary">
						<view class="mybg-linfo padding-sm text-left radius-6px margin-bottom-xs"
							v-for="(item,index) in search_results" @click="select_item(item)" :key="index">
							{{item.name}}
						</view>
					</scroll-view>
				</view>
			</view>
		</view>
	</view>

</template>

<script>
	export default {
		props: {
			hidden: true,
			league_list: {
				type: Array,
				default: function() {
					return []
				}
			},
		},
		computed: {},
		mounted() {
			this.filter_list = ['All', 'Team', 'League'].map((ele, index) => {
				return {
					label: ele,
					checked: index === 0,
				}
			})
		},
		data() {
			return {
				all_status: true,
				recent_search: uni.getStorageSync('recent_search') || [],
				search_query: '',
				search_results: [],
				selected_items: [],
				filter_list: [],
				current_type: 'All',
			}
		},
		methods: {
			check_filter(index) {
				this.filter_list.forEach((ele, _index) => {
					ele.checked = index === _index
				})
				this.current_type = this.filter_list[index].label
				this.handle_search()
			},
			set_dialog_hide(e) {
				this.$emit('update:hidden', e)
			},
			handle_search() {
				if (!this.search_query.trim()) {
					this.search_results = [];
					return;
				}
				const query = this.search_query.toLowerCase();
				const results = [];
				let matches = []
				this.league_list.forEach(league => {
					matches = matches.concat(league.match_list)
					if (this.current_type !== 'Team' && league.name.toLowerCase().includes(query)) {
						results.push({
							name: league.name,
							type: 'league'
						});
					}

				});
				// 搜索比赛
				if (this.current_type !== 'League') {
					matches.forEach(match => {
						if (match.HOST_TEAM.toLowerCase().includes(query) || match.GUEST_TEAM.toLowerCase()
							.includes(
								query)) {
							results.push({
								name: match.HOST_TEAM.toLowerCase().includes(query) ? match.HOST_TEAM :
									match
									.GUEST_TEAM,
								league: match.LEAGUE,
								type: 'match'
							});
						}
					});
				}
				this.search_results = results;
			},
			// 处理点击结果
			select_item(item, history) {
				let query = item.name.toLowerCase()
				this.reset_league_list()
				let list = this.$toolbox.deep_clone(this.league_list)
				if (item.type === 'league') {
					list.forEach(league => {
						let check = league.name.toLowerCase() === query
						league.checked = check
					})
				} else {
					list.forEach(league => {
						league.checked = league.name.toLowerCase() === item.league.toLowerCase()
						league.match_list.forEach(match => {
							// 主队或客队包含关键字
							let check = match.HOST_TEAM.toLowerCase().includes(query) || match
								.GUEST_TEAM
								.toLowerCase().includes(query)
							match.checked = check
						})
					});
				}
				this.search_query = item.name;
				this.save_storage(item)
				this.handle_search()
				this.$emit('update:league_list', list)
				this.$emit('update:hidden', true)
			},
			clear_search_query() {
				this.search_query = '';
				this.handle_search()
				this.reset_league_list()
			},
			reset_league_list() {
				this.league_list.forEach(league => {
					league.checked = true
					league.match_list.forEach(match => {
						match.checked = true
					})
				})
			},
			save_storage(item) {
				let map = this.recent_search.map(ele => ele.name)
				
				// 如果已有则删除，重新插入变为第一位
				let index = map.indexOf(item.name)
				if(index > -1){
					this.recent_search.splice(index, 1)
				}
				// 超长删除
				if (this.recent_search.length > 9) {
					this.recent_search.splice(this.recent_search.length - 1, 1)
				}
				
				this.recent_search = [item].concat(this.recent_search)
				uni.setStorageSync('recent_search', this.recent_search)
			},
		}
	}
</script>

<style lang="scss">
	.dialog-wrapper {
		z-index: 10000;
		// background-color: white;
		position: fixed;
		left: 0;
		bottom: 0;
		// height: calc(100vh - 55px);
		height: 100vh;
		width: 100vw;
	}

	.box-shadow {
		box-shadow: rgba(60, 64, 67, 0.3) 0px 1px 2px 0px, rgba(60, 64, 67, 0.15) 0px 1px 3px 1px;
	}

	.text-black {
		color: #000 !important;
	}
</style>