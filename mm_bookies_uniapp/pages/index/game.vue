<template>
	<view class="match-page-container">
		<!-- from tangjq--- 使用新的统一header组件 -->
		<zw-header @headerHeightChange="onHeaderHeightChange"></zw-header>

		<!-- from tangjq--- header占位元素，防止内容被遮挡 -->
		<view class="header-placeholder" :style="{ height: headerHeight + 'px' }"></view>

		<!-- Search Bar and Filter Button -->
		<view class="search-container padding-lr-sm">
			<view class="search-wrapper">
				<view class="search-box">
					<theme-icon name="search" class="search-icon"
						color="var(--theme-icon-primary, var(--theme-primary))"></theme-icon>
					<input class="search-input" type="text" :placeholder="$t('search')" v-model="searchKeyword" />
					<theme-icon name="close" class="clear-icon"
						color="var(--theme-icon-secondary, var(--theme-secondary))" v-show="searchKeyword"
						@tap="clearSearch"></theme-icon>
				</view>
				<view class="filter-button" @click="openFilterPopup">
					<view class="filter-icon">
						<view class="filter-line"></view>
						<view class="filter-line"></view>
						<view class="filter-line"></view>
					</view>
				</view>
			</view>
		</view>

		<!-- Game Categories and Game Cards -->
		<scroll-view scroll-y class="page padding-lr-sm padding-bottom-1px scroll-container"
			@scroll="handleHeaderScroll"
			:style="{height:isLogin?`calc(${calc_page_height} - 55px - 70px - 65px)`:`calc(${calc_page_height} - 55px - 60px - 70px - 65px)`,}">

			<!-- Loop through game categories -->
			<view class="flex-column padding-tb-sm" v-for="(category, catIndex) in game_categories" :key="catIndex">
				<!-- Category Header -->
				<view class="category-header" @click="category.expanded = !category.expanded">
					<text class="category-text text-white">{{category.name}}</text>
					<view class="cuIcon-unfold category-arrow text-white"></view>
				</view>

				<!-- Game Grid -->
				<view v-show="category.expanded" class="game-grid margin-top-sm">
					<view class="game-card" v-for="(game, gameIndex) in category.games" :key="gameIndex"
						@click="openGame(game)">
						<!-- Game Image -->
						<view class="game-image-wrapper">
							<image :src="game.image" mode="aspectFill" class="game-image" lazy-load></image>
						</view>

						<!-- Game Info Section -->
						<view class="game-info">
							<view class="game-info-content">
								<text class="game-name text-white text-bold">{{game.name}}</text>
								<text class="game-desc">{{game.description}}</text>
							</view>
							<view class="game-favorite" @click.stop="toggleFavorite(game)">
								<view class="favorite-icon"
									:class="[game.favorite ? 'cuIcon-favorfill' : 'cuIcon-favor', 'text-white']"></view>
							</view>
						</view>
					</view>
				</view>
			</view>
		</scroll-view>

		<!-- Filter Popup -->
		<view class="filter-popup-overlay" v-if="showFilterPopup" @click="closeFilterPopup">
			<view class="filter-popup" @click.stop>
				<!-- Filter Header -->
				<view class="filter-header">
					<text class="filter-title">{{ $t('filter') }}</text>
				</view>

				<!-- Filter Options -->
				<view class="filter-options">
					<view class="filter-option" v-for="(option, index) in filterOptions" :key="index"
						@click="selectFilterOption(option)">
						<text class="filter-option-text">{{option}}</text>
						<view class="filter-radio" :class="{'active': filterOption === option}">
							<view class="filter-radio-inner" v-if="filterOption === option"></view>
						</view>
					</view>
				</view>

				<!-- Confirm Button -->
				<view class="filter-confirm">
					<view class="filter-confirm-btn" @click="confirmFilter">
						<text class="filter-confirm-text">{{ $t('confirm') }}</text>
					</view>
				</view>
			</view>
		</view>

		<login-modal ref='login_modal' :hidden.sync="hide_login_modal"></login-modal>
	</view>
</template>

<script>
	import siteinfo from '../../siteinfo.js'
	import headerCollapse from '@/mixins/headerCollapse.js'

	export default {
		components: {},
		mixins: [headerCollapse],
		data() {
			return {
				siteinfo: siteinfo,
				isLogin: uni.getStorageSync('Authorization') || false,
				filter_type: 'hot', // hot, new, all
				hide_login_modal: true,
				game_categories: [],
				loading: false,
				pageNo: 1,
				pageSize: 100,
				// from tangjq--- 新增搜索和筛选相关变量
				searchKeyword: '', // 搜索关键词
				showFilterPopup: false, // 控制筛选弹窗显示
				filterOption: 'All', // 当前选中的筛选选项
				filterOptions: ['All'], // 筛选选项列表（将动态填充游戏类型）
				allGames: [], // 存储所有原始游戏数据
				pendingPlatform: null // 从外部页面跳转传入的厂商平台参数
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
			// from tangjq--- 计算过滤后的游戏列表
			filteredGames() {
				let games = this.allGames

				// 根据搜索关键词过滤
				if (this.searchKeyword && this.searchKeyword.trim()) {
					const keyword = this.searchKeyword.toLowerCase().trim()
					games = games.filter(game => {
						const name = (game.name || '').toLowerCase()
						return name.includes(keyword)
					})
				}

				// 根据游戏类型过滤
				if (this.filterOption && this.filterOption !== 'All') {
					games = games.filter(game => game.gameType === this.filterOption)
				}

				return games
			}
		},
		watch: {
			filter_type() {
				this.loadGames()
			},
			// from tangjq--- 监听搜索关键词和筛选选项变化，重新分组游戏
			searchKeyword() {
				this.groupGamesByPlatform(this.filteredGames)
			},
			filterOption() {
				this.groupGamesByPlatform(this.filteredGames)
			}
		},
		methods: {
			// 加载游戏列表
			loadGames() {
				if (this.loading) return

				const _this = this
				_this.loading = true

				uni.showLoading({
					title: _this.$t('loading_dots')
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
						// from tangjq--- 保存原始游戏数据并转换格式
						_this.allGames = games.map(game => ({
							id: game.id,
							platform: game.platform,
							gameType: game.gameType,
							gameCode: game.gameCode,
							name: game.nameZh || game.nameEn || 'Unknown',
							description: `RTP: ${game.rtp || 'N/A'}%`,
							image: game.iconUrl ? `${_this.siteinfo.awcImgUrl}${game.iconUrl}` : (game
								.thumbnailUrl || '/static/image/game/default-game.png'),
							favorite: game.isFavourite === 1,
							isHot: game.isHot === 1,
							isNew: game.isNew === 1
						}))
						// from tangjq--- 提取所有游戏类型并添加到筛选选项
						_this.extractGameTypes()
						// from tangjq--- 使用过滤后的游戏数据进行分组
						_this.groupGamesByPlatform(_this.filteredGames)
						// 如果有外部传入的厂商平台参数，过滤只显示该平台
						if (_this.pendingPlatform) {
							_this.game_categories = _this.game_categories.filter(cat => cat.name === _this
								.pendingPlatform)
							_this.pendingPlatform = null
						}
					} else {
						uni.showToast({
							title: res.data.message || _this.$t('failed_load_games'),
							icon: 'none'
						})
					}
				}, (err) => {
					_this.loading = false
					uni.hideLoading()
					uni.showToast({
						title: _this.$t('network_error'),
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

					platformMap[platform].games.push(game)
				})

				this.game_categories = Object.values(platformMap)
			},

			// from tangjq--- 提取所有游戏类型并添加到筛选选项
			extractGameTypes() {
				const gameTypes = new Set()
				this.allGames.forEach(game => {
					if (game.gameType) {
						gameTypes.add(game.gameType)
					}
				})
				this.filterOptions = ['All', ...Array.from(gameTypes).sort()]
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
						title: _this.$t('unable_get_user_info'),
						icon: 'none'
					})
					return
				}

				// 显示加载中
				uni.showLoading({
					title: _this.$t('loading_game'),
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
								title: _this.$t('account_created_success'),
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
								this.$notice.show({
									title: _this.$t('tips'),
									content: _this.$t('allow_popups'),
									confirmText: _this.$t('open_now'),
									cancelText: _this.$t('cancel'),
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
						this.$notice.show({
							title: _this.$t('error_title'),
							content: res.data.message || _this.$t('failed_launch_game'),
							showCancel: false,
							confirmText: _this.$t('ok')
						})
					}
				}, (err) => {
					uni.hideLoading()
					console.error('launchGame error:', err)
					uni.showToast({
						title: _this.$t('network_error'),
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
							title: isFavorite ? _this.$t('removed_from_favorites') : _this.$t(
								'added_to_favorites'),
							icon: 'success'
						})
					} else {
						uni.showToast({
							title: res.data.message || _this.$t('operation_failed'),
							icon: 'none'
						})
					}
				}, (err) => {
					uni.showToast({
						title: _this.$t('network_error'),
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
			},

			// from tangjq--- 打开筛选弹窗
			openFilterPopup() {
				this.showFilterPopup = true
			},

			// from tangjq--- 关闭筛选弹窗
			closeFilterPopup() {
				this.showFilterPopup = false
			},

			// from tangjq--- 选择筛选选项
			selectFilterOption(option) {
				this.filterOption = option
			},

			// from tangjq--- 确认筛选
			confirmFilter() {
				// 关闭弹窗，筛选会通过watch自动触发
				this.showFilterPopup = false
			},
			// from tangjq--- 清空搜索关键字
			clearSearch() {
				this.searchKeyword = ''
			}
		},
		onLoad(options) {
			// 检查是否从外部页面传入厂商平台参数
			if (options && options.platform) {
				this.pendingPlatform = options.platform
			}
			// 加载游戏列表
			this.loadGames()
		},
		mounted() {}
	}
</script>

<style lang="scss">
	/* from tangjq--- header占位元素样式 */
	.header-placeholder {
		height: 255px;
		width: 100%;
		flex-shrink: 0;
		transition: height 0.3s ease;
	}

	/* Search Container */
	.search-container {
		padding: 10px;
		background-color: #f5f5f5;
	}

	.search-wrapper {
		display: flex;
		flex-direction: row;
		align-items: center;
		gap: 10px;
	}

	.search-box {
		flex: 1;
		display: flex;
		flex-direction: row;
		align-items: center;
		background-color: #ffffff;
		border-radius: 25px;
		padding: 6px 15px;
		border: 1px solid $color-primary;
	}

	.search-icon {
		width: 20px;
		height: 20px;
		margin-right: 10px;
	}

	.search-input {
		flex: 1;
		font-size: 14px;
		color: #333;
		border: none;
	}

	.search-input::placeholder {
		color: #999;
	}

	.clear-icon {
		width: 16px;
		height: 16px;
		margin-left: 8px;
		cursor: pointer;
	}

	.filter-button {
		width: 35px;
		height: 35px;
		background-color: $color-primary;
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
		cursor: pointer;
		transition: background-color 0.3s;
	}

	.filter-button:active {
		background-color: #2d5d5d;
	}

	.filter-icon {
		display: flex;
		flex-direction: column;
		gap: 4px;
		align-items: center;
	}

	.filter-line {
		height: 2px;
		background-color: #ffffff;
		border-radius: 1px;
	}

	.filter-line:nth-child(1) {
		width: 18px;
	}

	.filter-line:nth-child(2) {
		width: 10px;
	}

	.filter-line:nth-child(3) {
		width: 4px;
	}

	.scroll-container {
		margin-top: 10px;
		background-color: #ffffff;
	}

	/* Category Header */
	.category-header {
		display: flex;
		flex-direction: row;
		align-items: center;
		justify-content: space-between;
		background-color: $color-primary;
		border-radius: 25px;
		padding: 8px 20px;
		cursor: pointer;
		margin-bottom: 10px;
		width: 100%;
	}

	.category-text {
		color: #ffffff;
		font-size: 14px;
		font-weight: 500;
	}

	.category-arrow {
		color: #ffffff;
		font-size: 16px;
	}

	.game-grid {
		display: flex;
		flex-direction: row;
		flex-wrap: wrap;
		justify-content: space-between;
		width: 100%;
	}

	.game-card {
		display: flex;
		flex-direction: column;
		border-radius: 15px;
		overflow: hidden;
		box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
		width: 48%;
		background: $color-primary;
		margin-bottom: 12px;
		transition: transform 0.2s;
	}

	.game-card:active {
		transform: scale(0.98);
	}

	.game-image-wrapper {
		width: 100%;
		height: 200px;
		overflow: hidden;
		background: #333;
	}

	.game-image {
		width: 100%;
		height: 100%;
		object-fit: cover;
	}

	.game-info {
		display: flex;
		flex-direction: row;
		align-items: center;
		justify-content: space-between;
		background-color: $color-primary;
		padding: 0 12px;
		min-height: 50px;
	}

	.game-info-content {
		flex: 1;
		display: flex;
		flex-direction: column;
		gap: 4px;
		overflow: hidden;
		text-align: left;
	}

	.game-name {
		font-size: 12px;
		font-weight: 600;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
		line-height: 1;
	}

	.game-desc {
		color: rgba(255, 255, 255, 0.85);
		font-size: 11px;
		line-height: 1.3;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.game-favorite {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 32px;
		height: 32px;
		flex-shrink: 0;
		margin-left: 8px;
	}

	.favorite-icon {
		font-size: 20px;
	}

	/* Filter Popup */
	.filter-popup-overlay {
		position: fixed;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		background-color: rgba(0, 0, 0, 0.5);
		z-index: 9999;
		display: flex;
		justify-content: flex-end;
	}

	.filter-popup {
		width: 260px;
		height: 100%;
		background-color: #ffffff;
		display: flex;
		flex-direction: column;
		animation: slideInRight 0.3s ease-out;
		border-radius: 10px 0 0 10px;
	}

	@keyframes slideInRight {
		from {
			transform: translateX(100%);
		}

		to {
			transform: translateX(0);
		}
	}

	.filter-header {
		background-color: $color-primary;
		padding: 15px 20px;
		display: flex;
		align-items: center;
		justify-content: center;
		border-radius: 10px 0 0 0;
	}

	.filter-title {
		color: #ffffff;
		font-size: 18px;
		font-weight: 600;
	}

	.filter-options {
		flex: 1;
		padding: 20px 0;
		background-color: #f8f9fa;
	}

	.filter-option {
		display: flex;
		flex-direction: row;
		align-items: center;
		justify-content: space-between;
		padding: 8px 25px;
		background-color: #ffffff;
		margin-bottom: 1px;
		cursor: pointer;
		transition: background-color 0.2s;
		background-color: $color-secondary-light;
	}

	.filter-option:active {
		background-color: #f5f5f5;
	}

	.filter-option-text {
		color: $color-primary;
		font-size: 14px;
		font-weight: 500;
	}

	.filter-radio {
		width: 22px;
		height: 22px;
		border: 2px solid $color-secondary;
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
		transition: all 0.2s;
	}

	.filter-radio.active {
		border-color: $color-secondary;
	}

	.filter-radio-inner {
		width: 12px;
		height: 12px;
		background-color: $color-secondary;
		border-radius: 50%;
	}

	.filter-confirm {
		padding: 20px;
		background-color: #ffffff;
		box-shadow: 0 -2px 8px rgba(0, 0, 0, 0.05);
		border-radius: 0 0 0 10px;
	}

	.filter-confirm-btn {
		background-color: $color-primary;
		border-radius: 25px;
		padding: 8px;
		display: flex;
		align-items: center;
		justify-content: center;
		cursor: pointer;
		transition: background-color 0.3s;
	}

	.filter-confirm-btn:active {
		background-color: #2d5d5d;
	}

	.filter-confirm-text {
		color: #ffffff;
		font-size: 16px;
		font-weight: 600;
	}

	.page {
		display: block;
		flex: 1;
	}
</style>