<template>
	<view>
		<!-- 顶栏 -->
		<view class="flex-row justify-around mybg-primary width-100" style="height: 55px;">
			<image src="/static/index_logo.png" style="width: 115px;height: 28.75px;margin-left: 20px;"
				@click="goto('/pages/match/home?mix=0',1)"></image>

			<view class="top-right" style="" v-if="isLogin">
				<view></view>
				<view class="wallet-bar" v-if="mounted" @click="goto('/pages/index/wallet',1)">
					<image src="/static/icon/bar/cash.svg" style="height: 18px;" mode="heightFix"></image>
					<view class="myfont-bold padding-lr-xs" style="font-size: 14px;">
						{{$toolbox.num_format(userInfo.money)}}
					</view>
				</view>
				<view class="wallet-bar" style="width: 49px;" v-else>
					<image src="/static/icon/bar/cash.svg" style="height: 18px;" mode="heightFix"></image>
					<view class="myfont-bold padding-lr-xs" style="font-size: 14px;">
					</view>
				</view>
				<!-- 消息按钮（优化后） -->
				<view class="message-btn" v-if="!pageType.indexPage" @click="goto('/pages/ucenter/message',1)">
					<view class="message-icon-wrapper">
						<image src="/static/icon/contact.png" class="yellow2dblue" style="height: 20px; width: 20px;" mode="aspectFit"></image>
						<view class="message-badge" v-if="unreadMessageCount > 0">
							{{ unreadMessageCount > 99 ? '99+' : unreadMessageCount }}
						</view>
					</view>
				</view>
				<!-- <view class="wallet-bar" v-if="!pageType.indexPage">
					<image src="/static/icon/bar/cash.svg" style="height: 18px;" mode="heightFix"></image>
				</view> -->
				<!-- <view style="width: 80px;"></view> -->
				<slot name="right"></slot>
			</view>

			<!-- <text class="cuIcon-filter" @tap="match_click" 
				style="display: flex;flex-direction: row;align-items:center;justify-content: center;width: 26px;height: 26px;border-radius: 50%;background-color: white;font-size: 22px;font-weight: bold;">
			</text>
			<view v-if="matchPage" style="width: 26px;"></view>
			<view v-else style="width: 26px;"></view>
			<text class="cuIcon-search" v-if="matchPage" @tap="match_click" 
				style="display: flex;flex-direction: row;align-items:center;justify-content: center;width: 26px;height: 26px;border-radius: 50%;background-color: white;font-size: 18px;font-weight: bold;">
			</text>
			<view v-if="matchPage" style="width: 26px;"></view>
			<view v-else style="width: 26px;"></view> -->

		</view>
		<!-- 未登录常驻登陆提示 -->
		<view class="flex-row justify-center align-center" style="width: 100vw;height: 60px;background-color: #F5F5F5;"
			v-if="!isLogin && !pageType.loginPage">
			<view class="mybg-primary register-btn" @click="goto('/pages/login/login')">
				{{$t('signin_button')}}
			</view>
			<view class="mybg-active register-btn" @click="goto('/pages/login/register')">
				{{$t('register_button')}}
			</view>
		</view>

		<!-- 顶部导航栏 -->
		<view class="top-navbar" v-if="pageType.indexPage">
			<view class="wrap">
				<view class="links os-links">
					<view class="link" :class="item.currentPage?'now-page':''" v-for="(item, index) in pageList"
						:key="index" @click="item.currentPage?'':goto(item)">
						<text :class="item.icon"
							:style="!item.currentPage?'filter: grayscale(1);opacity: 0.35;':''"></text>
						<text>{{$t(item.name)}}</text>
					</view>
				</view>
			</view>
		</view>

		<!-- 底部导航栏 -->
		<view class="box safe-area">
			<view class="cu-bar tabbar mybg-primary text-white" style="height: 65px;">
				<view class="action" v-for="(item,index) in bottomList" :key="index" @click="goto(item,1)">
					<view class="" :class="{
						[item.icon]: true,
						'yellow2white': !item.currentPage,
						}" style=""></view>
					<view class="myfont-10px flex-row1 align-center justify-center" style="height: 20px;"
						:class="{'mycolor-active': item.currentPage}">
						{{$t(item.name)}}
					</view>
				</view>
				<!-- <view class="action" @click="$relaunchPage('./elect')">
					<view class="icon-wallet grayscale"></view>
					<view class="margin-top-xs">钱包</view>
				</view>
				<view class="action" @click="$relaunchPage('./elect')">
					<view class="icon-coupon grayscale"></view>
					<view class="margin-top-xs">优惠券</view>
				</view>
				<view class="action" @click="$relaunchPage('./subject')">
					<view class="icon-contact grayscale"></view>
					<view class="margin-top-xs">客服</view>
				</view>
				<view class="action" @click="isLogin?$relaunchPage('../user/user_center'):to_page('../user/login')">
					<view class="icon-setting grayscale"></view>
					<view class="margin-top-xs">设置</view>
				</view> -->
			</view>
		</view>

	</view>
</template>

<script>
	import headerConfig from '@/common/config/common/header.config.js';
	import config from '../../utils/config.js'

	import {
		mapGetters
	} from 'vuex';

	export default {
		components: {},
		// props: {
		// 	searchKeyword: {
		// 		type: String,
		// 		default: ''
		// 	},
		// 	searchKeyword: {
		// 		type: String,
		// 		default: ''
		// 	}
		// },
		data() {
			return {
				pageList: [],
				bottomList: [],
				// keyword: this.searchKeyword,
				// keywordIndex: -1,
				// userInfo: uni.getStorageSync('userInfo') || {},
				isLogin: uni.getStorageSync('Authorization') || false,
				userInfo: {},
				pageType: {
					// matchPage: false,
					indexPage: false,
					loginPage: false,
				},
				mounted: false,
				unreadMessageCount: 0, // 未读消息数量

			}
		},
		computed: {
			currentRoute() {
				const pages = getCurrentPages();
				return pages.length ? pages[pages.length - 1].route : '';
			}
		},
		created() {
			// this.getUserInfo()
		},
		mounted() {
			this.updateTopPageList();
			this.getUserInfo();
			this.updateUnreadMessageCount(); // 启用初始化时的消息计数更新
			this.setupWebSocketMessageListener();
		},
		activated() {
			// 返回页面时触发
			// this.updateBottomList();
			this.updateTopPageList();
			// this.keyword = this.searchKeyword;
		},
		methods: {
			match_click() {
				this.$emit('match_click'); // 发出事件给父组件
			},
			showModal(e) {
				// this.music.play_dede();
				this.modalName = e.currentTarget.dataset.target
			},
			// 顶栏
			updateTopPageList() {
				let _this = this;
				// 获取当前路由
				const pages = getCurrentPages();
				const currentPage = pages[pages.length - 1];
				const currentRoute = currentPage.route;
				// 拼接带参数URL
				let routeParams = currentPage.options;
				let queryString = '';
				if (routeParams && Object.keys(routeParams).length > 0) {
					queryString = '?' + Object.entries(routeParams)
						.map(([key, value]) => `${key}=${value}`)
						.join('&');
				}
				// 拼接带参数URL
				let currentUrl = currentRoute + queryString;
				// 更新底部导航栏
				_this.updateBottomList(currentPage, currentRoute)
				// 初始化
				let navList = headerConfig.navList;
				currentUrl = currentUrl == 'pages/match/home' ? 'pages/match/home?mix=0' : currentUrl
				let matchedPage = ''
				navList.forEach((item) => {
					if (item.url.includes(currentUrl)) {
						matchedPage = item
						_this.pageType = matchedPage
						item.currentPage = true;
					} else {
						item.currentPage = false;
					}
				});
				// 匹配当前页面
				// console.log(currentUrl)
				// let matchedPage = navList.find(item => item.url.includes(currentUrl));
				if (matchedPage) {
					_this.pageType = matchedPage
					matchedPage.currentPage = true;
				} else {
					navList[0].currentPage = true;
				}
				this.pageList = navList;
			},
			// 底栏、其他页面
			updateBottomList(currentPage, currentRoute) {
				let _this = this;
				// 初始化
				let navList = headerConfig.bottomList;
				// if (!_this.isLogin) {
				// 	navList = headerConfig.bottomList.filter(item => !item.login_show);
				// }

				navList.forEach((item) => {
					item.currentPage = false;
				});
				// 匹配当前页面
				let matchedPage = navList.find(item => item.url.includes(currentRoute));
				if (!matchedPage) {
					// 将options对象转换为查询参数字符串
					let routeParams = currentPage.options;
					let queryString = '';

					if (routeParams && Object.keys(routeParams).length > 0) {
						queryString = '?' + Object.entries(routeParams)
							.map(([key, value]) => `${key}=${value}`)
							.join('&');
					}

					// 拼接带参数URL
					let currentUrl = currentRoute + queryString;
					// console.log('Current URL with params:', currentUrl);
					let ortherParaList = headerConfig.otherParaList;
					let parentPage = ortherParaList.find(item => item.url.includes(currentUrl));
					if (parentPage) {
						matchedPage = navList.find(item => item.url.includes(parentPage.parent_url));
					} else {
						// 带参数无匹配项再匹配无参数
						let ortherList = headerConfig.otherList;
						let sonPage = ortherList.find(item => item.url.includes(currentRoute));
						if (sonPage) {
							// this.pageType.matchPage = sonPage.matchPage
							_this.pageType.indexPage = sonPage.indexPage
							_this.pageType.loginPage = sonPage.login_page
						}
						if (sonPage && sonPage.parent_url) {
							matchedPage = navList.find(item => item.url.includes(sonPage.parent_url));
							if (!_this.isLogin && sonPage.need_login) {
								_this.goto('/pages/login/login')
							}
						}
					}
				}
				if (matchedPage) {
					matchedPage.currentPage = true;
					_this.pageType = matchedPage
				} else {
					navList[0].currentPage = true;
				}
				if (!_this.isLogin) {
					if (matchedPage && matchedPage.need_login) {
						_this.goto('/pages/login/login')
					}
					navList = navList.filter(item => !item.login_show);
				}
				_this.bottomList = navList;
			},
			getUserInfo() {
				var _this = this;
				_this.loading = true;
				if (uni.getStorageSync("Authorization")) {
					_this.$http.get('/app_user/user_info', {}, (res) => {
						_this.loading = false;
						if (res.statusCode == 200) {
							_this.$store.dispatch('saveUserInfo', res.data.data);
							_this.userInfo = res.data.data
							this.mounted = true
							// console.log(_this.userInfo.money)

						}
					})
				}
			},
			goto(item, limit_click) {
				let url = item
				if (item && item.url) {
					url = item.need_login && !this.isLogin ? '/pages/login/login' : item.url
				}
				if (limit_click) {
					if (url.includes(this.currentRoute) && this.$toolbox.click_too_fast(1)) return
				}

				// 特殊处理：消息页面使用 navigateTo 以显示返回按钮
				if (url === '/pages/ucenter/message') {
					uni.navigateTo({
						url: url
					})
					return
				}

				// 其他页面继续使用原有的 reLaunch 逻辑
				uni.reLaunch({
					url: url
				})

			},
			
			// 更新未读消息数量
			updateUnreadMessageCount() {
				try {
					// 从本地存储获取WebSocket消息，过滤掉SYSTEM消息
					const messages = uni.getStorageSync('websocket_messages') || []
					this.unreadMessageCount = messages
						.filter(m => m.messageType !== 'SYSTEM')  // 过滤掉SYSTEM消息
						.filter(m => !m.isRead)
						.length
					//console.log(`[Header] 更新未读消息数量: ${this.unreadMessageCount}`)
				} catch (error) {
					console.error('[Header] 获取未读消息数量失败:', error)
					this.unreadMessageCount = 0
				}
			},
			
			// 设置WebSocket消息监听器
			setupWebSocketMessageListener() {
				const _this = this
				
				// 监听新消息
				uni.$on('websocket:messageSaved', (message) => {
					//console.log('[Header] 收到新消息通知, 更新未读数量')
					_this.updateUnreadMessageCount()
				})
				
				// 监听消息已读状态变化
				uni.$on('message:read', () => {
					//console.log('[Header] 消息已读状态变化, 更新未读数量')
					_this.updateUnreadMessageCount()
				})
				
				// 监听消息列表更新
				uni.$on('message:update', () => {
					//console.log('[Header] 消息列表更新, 更新未读数量')
					_this.updateUnreadMessageCount()
				})
			}

		},
		
		// 组件销毁时清理监听器
		beforeDestroy() {
			uni.$off('websocket:messageSaved')
			uni.$off('message:read')
			uni.$off('message:update')
		}

	}
</script>

<style lang="scss">
	.register-btn {
		display: flex;
		flex-direction: column;
		justify-content: center;
		align-items: center;
		width: 175px;
		height: 38px;
		margin: 0 8px;
		border-radius: 8px;
		font-size: 10px;
		font-weight: bold;
	}

	.top-right {
		width: calc(100vw - 135px);
		display: flex;
		flex-direction: row;
		align-items: center;
		justify-content: space-between;
	}

	.wallet-bar {
		display: flex;
		flex-direction: row;
		align-items: center;
		justify-content: space-between;
		padding: 0 8px 0 2px;
		height: 25px;
		border-radius: 20px;
		background-color: white;
		margin: 0 auto;
		// width: 100px;
		max-width: 50vw;
		padding-left: 5px;
		color: $color-primary;
	}

	// 消息按钮样式
	.message-btn {
		padding: 4px 8px;
		border-radius: 20px;
		background-color: rgba(255, 255, 255, 0.9);
		backdrop-filter: blur(10px);
		transition: all 0.3s ease;
		margin-right: 12px; // 添加右边距，让按钮往左移
		
		&:active {
			transform: scale(0.95);
			background-color: rgba(255, 255, 255, 0.8);
		}
	}

	.message-icon-wrapper {
		position: relative;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.message-badge {
		position: absolute;
		top: -8px;
		right: -8px;
		min-width: 16px;
		height: 16px;
		border-radius: 8px;
		background: linear-gradient(135deg, #FF6B6B, #FF5252);
		color: white;
		font-size: 10px;
		font-weight: bold;
		display: flex;
		align-items: center;
		justify-content: center;
		padding: 0 4px;
		box-shadow: 0 2px 4px rgba(255, 107, 107, 0.3);
		border: 1px solid white;
		
		// 动画效果
		animation: pulse 2s infinite;
	}

	@keyframes pulse {
		0% {
			transform: scale(1);
		}
		50% {
			transform: scale(1.1);
		}
		100% {
			transform: scale(1);
		}
	}

	.top-navbar {
		width: 100%;
		position: relative;
		// height: 40px;
		font-size: 10px;
		background-color: white;


		.links {
			width: 100%;
			@extend %flex-align-center;

			.link {
				display: flex;
				flex-direction: column;
				justify-content: center;
				align-items: center;
				color: $color-linfo;
				cursor: pointer;
				height: 58px;
				// line-height: 58px;
				width: 25%;
				text-align: center;
				transition: all .2s;
				position: relative;
			}

			// .link:not(.now-page):hover {
			// 	color: $color-primary !important;
			// 	background-color: #FFFFFF !important;
			// 	background-size: contain;
			// 	background-repeat: no-repeat;
			// }

			// &:hover {
			// 	color: $color-primary !important;
			// 	background-color: #FFFFFF !important;
			// 	background-image: none;
			// }

			.now-page {
				font-weight: bold;
				// background: $color-primary;
				color: $color-primary;
				position: relative;
				/* 让 ::before 以 .now-page 为参照定位 */
				z-index: 1;
				/* 确保文本显示在最上层 */
			}

			/* 只给 .now-page 添加独立背景图片 */
			// .now-page::before {
			// 	content: "";
			// 	position: absolute;
			// 	top: 45%;
			// 	left: 50%;
			// 	width: 130px;
			// 	height: 48px;
			// 	background-image: url(/static/icon/tag.png);
			// 	background-size: contain;
			// 	background-repeat: no-repeat;
			// 	transform: translate(-50%, -50%);
			// 	z-index: -1;
			// }
		}
	}

	.box {
		margin: 0 0 0 0;
		position: fixed;
		bottom: 0px;
		width: 100vw;
		z-index: 10;

		.safe-area {
			padding-bottom: constant(safe-area-inset-bottom);
			padding-bottom: env(safe-area-inset-bottom);
		}
	}
</style>