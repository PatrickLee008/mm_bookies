<template>
	<view class="mybg-grey page" :style="{'height':calc_page_height,}">
		<zw-header>
			<block slot="center">
				<view class="text-white text-bold myfont-16px">eGames</view>
			</block>
		</zw-header>

		<!-- Filter Tabs: Hot / New / All -->
		<view class="flex-row mybg-lprimary justify-around padding-tb-sm">
			<button class="cu-btn sm width-30 myfont-10px" :class="{'mybg-active': filter_type === 'hot'}"
				@click="filter_type = 'hot'">Hot</button>
			<button class="cu-btn sm width-30 myfont-10px" :class="{'mybg-active': filter_type === 'new'}"
				@click="filter_type = 'new'">New</button>
			<button class="cu-btn sm width-30 myfont-10px" :class="{'mybg-active': filter_type === 'all'}"
				@click="filter_type = 'all'">All</button>
		</view>

		<!-- Game Categories and Game Cards -->
		<scroll-view scroll-y class="page padding-lr-sm padding-bottom-1px" style="line-height: 1.5;"
			:style="{height:isLogin?`calc(${calc_page_height} - 55px - 58px - 46px - 65px)`:`calc(${calc_page_height} - 55px - 60px - 58px - 46px - 65px)`,}">

			<!-- Loop through game categories -->
			<view class="flex-column padding-tb-sm" v-for="(category, catIndex) in game_categories" :key="catIndex">
				<!-- Category Header -->
				<view
					class="category-header flex-row justify-between align-center radius-10px text-white padding-lr-sm padding-tb-xs mybg-lprimary">
					<view class="flex-row1 align-center">
						<view class="cuIcon-favorfill margin-right-sm myfont-14px"
							:class="category.favorite ? 'text-yellow' : 'text-white'"
							@click.stop="toggleCategoryFavorite(category)"></view>
						<text class="myfont-12px text-bold">{{category.name}}</text>
					</view>
					<view class="flex-row1 align-center gap-5px" @click="category.expanded = !category.expanded">
						<view class="cu-tag round sm mybg-active mycolor-primary min-width-30px">
							{{category.games.length}}
						</view>
						<view class="myfont-12px" :class="category.expanded ? 'cuIcon-unfold' : 'cuIcon-fold'"></view>
					</view>
				</view>

				<!-- Game Grid -->
				<view v-show="category.expanded" class="game-grid margin-top-sm">
					<view class="game-card" v-for="(game, gameIndex) in category.games" :key="gameIndex"
						@click="openGame(game)">
						<!-- Game Image -->
						<image :src="game.image" mode="aspectFill" class="game-image" lazy-load></image>

						<!-- Game Info Overlay -->
						<view class="game-info">
							<view class="flex-row1 justify-between align-center">
								<text class="game-name text-white text-bold myfont-12px">{{game.name}}</text>
								<view class="cuIcon-favorfill myfont-16px"
									:class="game.favorite ? 'text-yellow' : 'text-white'"
									@click.stop="toggleFavorite(game)"></view>
							</view>
							<text class="game-desc myfont-10px">{{game.description}}</text>
						</view>
					</view>
				</view>
			</view>
		</scroll-view>

		<login-modal ref='login_modal' :hidden.sync="hide_login_modal"></login-modal>
	</view>
</template>

<script>
	import siteinfo from '../../siteinfo.js'

	export default {
		components: {},
		data() {
			return {
				siteinfo: siteinfo,
				isLogin: uni.getStorageSync('Authorization') || false,
				filter_type: 'hot', // hot, new, all
				hide_login_modal: true,
				game_categories: [],
				loading: false,
				pageNo: 1,
				pageSize: 100
			}
		},
		computed: {
			calc_page_height() {
				let info = uni.getDeviceInfo()
				if (info.platform == 'ios') {
					return `calc(100vh - 85px)`
				}
				return '100vh'
			},
		},
		watch: {
			filter_type() {
				this.loadGames()
			}
		},
		methods: {
			// 加载游戏列表
			loadGames() {
				if (this.loading) return

				const _this = this
				_this.loading = true

				uni.showLoading({
					title: 'Loading...'
				})

				const para = {
					filter: _this.filter_type,
					pageNo: _this.pageNo,
					pageSize: _this.pageSize
				}

				_this.$http.get('/awc/getAwcGameList', {
					data: para
				}, (res) => {
					_this.loading = false
					uni.hideLoading()

					if (res.statusCode == 200 && res.data.code == 200) {
						const games = res.data.data.records || []
						_this.groupGamesByPlatform(games)
					} else {
						uni.showToast({
							title: res.data.message || 'Failed to load games',
							icon: 'none'
						})
					}
				}, (err) => {
					_this.loading = false
					uni.hideLoading()
					uni.showToast({
						title: 'Network error',
						icon: 'none'
					})
				})
			},

			// 按平台分组游戏
			groupGamesByPlatform(games) {
				const platformMap = {}

				games.forEach(game => {
					const platform = game.platform || 'Other'
					if (!platformMap[platform]) {
						platformMap[platform] = {
							name: platform,
							expanded: true,
							favorite: false,
							games: []
						}
					}

					platformMap[platform].games.push({
						id: game.id,
						platform: game.platform,
						gameType: game.gameType,
						gameCode: game.gameCode,
						name: game.nameZh || game.nameEn || 'Unknown',
						description: `RTP: ${game.rtp || 'N/A'}%`,
						image: game.iconUrl ? `${this.siteinfo.awcImgUrl}${game.iconUrl}` : (game.thumbnailUrl || '/static/image/game/default-game.png'),
						favorite: game.isFavourite === 1,
						isHot: game.isHot === 1,
						isNew: game.isNew === 1
					})
				})

				this.game_categories = Object.values(platformMap)
			},

			// 打开游戏
			openGame(game) {
				const _this = this

				// 检查登录状态
				if (!_this.isLogin) {
					_this.hide_login_modal = false
					return
				}

				// 获取用户信息
				const userInfo = _this.$store.state.userInfo
				if (!userInfo || !userInfo.phone) {
					uni.showToast({
						title: 'Unable to get user information',
						icon: 'none'
					})
					return
				}

				// 显示加载中
				uni.showLoading({
					title: 'Loading game...',
					mask: true
				})

				// 准备请求参数 - 后端会自动处理注册逻辑
				const para = {
					userId: userInfo.phone,
					platform: game.platform,
					gameType: game.gameType,
					gameCode: game.gameCode,
					isMobileLogin: true
				}

				// 调用后端API进入指定游戏（后端自动处理注册逻辑）
				_this.$http.post('/awc/launchGame', para, (res) => {
					uni.hideLoading()

					if (res.statusCode == 200 && res.data.ok) {
						const gameUrl = res.data.data.url
						const isNewMember = res.data.data.isNewMember

						// 如果是新会员（首次注册AWC），提示用户
						if (isNewMember) {
							uni.showToast({
								title: 'Account created successfully',
								icon: 'success',
								duration: 1500
							})
						}

						// 根据不同平台采用不同的打开方式
						// #ifdef H5
						// H5环境下检测是否为iOS Safari
						const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent)
						const isSafari = /Safari/.test(navigator.userAgent) && !/Chrome/.test(navigator.userAgent)

						if (isIOS && isSafari) {
							// iOS Safari直接在当前窗口打开，避免弹窗拦截
							console.log('iOS Safari detected, opening in current window')
							window.location.href = gameUrl
						} else {
							// PC或其他移动浏览器使用新窗口打开
							const newWindow = window.open(gameUrl, '_blank')
							if (!newWindow) {
								// 如果被拦截，提示用户或使用备用方案
								uni.showModal({
									title: 'Tips',
									content: 'Please allow pop-ups for this site',
									confirmText: 'Open Now',
									cancelText: 'Cancel',
									success: (modalRes) => {
										if (modalRes.confirm) {
											// 用户确认后，跳转到webview页面
											uni.navigateTo({
												url: `/pages/webview/index?url=${encodeURIComponent(gameUrl)}&title=${encodeURIComponent(game.name)}`
											})
										}
									}
								})
							}
						}
						// #endif

						// #ifdef APP-PLUS || MP
						// APP和小程序环境使用内嵌webview
						uni.navigateTo({
							url: `/pages/webview/index?url=${encodeURIComponent(gameUrl)}&title=${encodeURIComponent(game.name)}`
						})
						// #endif

					} else {
						uni.showModal({
							title: 'Error',
							content: res.data.message || 'Failed to launch game',
							showCancel: false,
							confirmText: 'OK'
						})
					}
				}, (err) => {
					uni.hideLoading()
					console.error('launchGame error:', err)
					uni.showToast({
						title: 'Network error',
						icon: 'none'
					})
				})
			},

			// 切换游戏收藏状态
			toggleFavorite(game) {
				// 参考 /pages/match/home 的实现，未登录时弹出登录弹窗
				if (!this.isLogin) {
					this.hide_login_modal = false
					return
				}

				const _this = this
				const isFavorite = game.favorite
				const action = isFavorite ? 'removeGameFavourite' : 'addGameFavourite'

				const postData = {
					gameCode: game.gameCode
				}

				_this.$http.post(`/awc/${action}`, postData, (res) => {
					if (res.statusCode == 200 && res.data.code == 200) {
						game.favorite = !isFavorite
						uni.showToast({
							title: isFavorite ? 'Removed from favorites' : 'Added to favorites',
							icon: 'success'
						})
					} else {
						uni.showToast({
							title: res.data.message || 'Operation failed',
							icon: 'none'
						})
					}
				}, (err) => {
					uni.showToast({
						title: 'Network error',
						icon: 'none'
					})
				})
			},

			// 切换分类收藏状态
			toggleCategoryFavorite(category) {
				category.favorite = !category.favorite
				uni.showToast({
					title: category.favorite ? 'Category favorited' : 'Category unfavorited',
					icon: 'none'
				})
			}
		},
		onLoad(options) {
			// 加载游戏列表
			this.loadGames()
		},
		mounted() {}
	}
</script>

<style>
	.category-header {
		box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
		cursor: pointer;
	}

	.game-grid {
		display: flex;
		flex-direction: row;
		flex-wrap: wrap;
		justify-content: space-between;
		width: 100%;
	}

	.game-card {
		position: relative;
		border-radius: 10px;
		overflow: hidden;
		box-shadow: rgba(60, 64, 67, 0.3) 0px 1px 2px 0px, rgba(60, 64, 67, 0.15) 0px 1px 3px 1px;
		width: 48%;
		height: 200px;
		background: #333;
		margin-bottom: 10px;
	}

	.game-image {
		width: 100%;
		height: 100%;
		object-fit: cover;
	}

	.game-info {
		position: absolute;
		bottom: 0;
		left: 0;
		right: 0;
		background: linear-gradient(to top, rgba(0, 0, 0, 0.9) 0%, rgba(0, 0, 0, 0.6) 50%, transparent 100%);
		min-height: 70px;
		padding: 10px;
	}

	.game-name {
		flex: 1;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.game-desc {
		color: rgba(255, 255, 255, 0.8);
		font-size: 10px;
		margin-top: 4px;
		display: block;
	}

	.page {
		display: block;
		flex: 1;
	}
</style>
