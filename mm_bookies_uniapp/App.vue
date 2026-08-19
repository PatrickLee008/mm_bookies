<script>
	import Vue from 'vue'
	import config from './utils/config.js'
	import language from './utils/language.js'
	import websocketManager from './utils/websocket.js'
	import { logAdlinkVisit } from './utils/api/public.js'

	//#ifdef APP-PLUS
	// let main = plus.android.runtimeMainActivity();
	//为了防止快速点按返回键导致程序退出重写quit方法改为隐藏至后台
	// plus.runtime.quit = function() {
	// 	main.moveTaskToBack(false);
	// };
	//应用全屏，不显示状态栏
	plus.navigator.setFullscreen(true);

	//重写toast方法如果内容为 ‘再按一次退出应用’ 就隐藏应用，其他正常toast
	plus.nativeUI.toast = (function(str) {
		if (str == 'Press again to exit the application') {
			plus.runtime.quit();
			return false;
		} else {
			uni.showToast({
				title: 'Press again to exit the application',
				icon: 'none',
			})
		}
	});
	//#endif

	export default {
		methods: {
			// WebSocket 相关方法
			initWebSocket() {
				console.log('[App] 初始化 WebSocket 连接...')

				// 检查登录状态，只要有token就尝试连接
				const token = uni.getStorageSync('Authorization')

				if (token) {
					// 从store获取真实用户ID
					const userId = this.getUserIdFromStore()
					if (userId) {
						console.log('[App] 开始连接 WebSocket, userId:', userId)
						websocketManager.connect(userId, token)
					} else {
						console.warn('[App] 未找到用户ID，跳过 WebSocket 连接（用户信息可能尚未加载）')
					}

					// 注册全局消息监听器
					this.setupWebSocketListeners()
				} else {
					console.log('[App] 未登录（无 token），跳过 WebSocket 连接')
				}
			},

			// 从store获取用户ID
			getUserIdFromStore() {
				try {
					const userInfo = this.$store.state.userInfo
					if (userInfo && userInfo.id) {
						return userInfo.id
					}

					// 如果store中没有，尝试从本地存储获取
					// 注意：登录与 store 均保存到 'user_info'（带下划线），优先读取它
					const storedUserInfo = uni.getStorageSync('user_info') || uni.getStorageSync('userInfo')
					if (storedUserInfo && storedUserInfo.id) {
						return storedUserInfo.id
					}

					return null
				} catch (error) {
					console.error('[App] 获取用户ID失败:', error)
					return null
				}
			},

			// 监听登录事件：登录成功后立即建立连接并刷新未读数
			setupLoginListener() {
				uni.$on('user:login', () => {
					console.log('[App] 收到登录事件，准备建立 WebSocket 连接')
					// 延迟一点等待 token / user_info 写入完成
					setTimeout(() => {
						this.initWebSocket()
						// 通知 header 等刷新未读数
						uni.$emit('message:unreadUpdate', null)
					}, 1000)
				})
			},
			
			setupWebSocketListeners() {
				// 只监听应用级别需要处理的关键事件
				uni.$on('websocket:connected', () => {
					 // console.log('[App] WebSocket connection successful')
					// 连接成功后可以做一些应用级别的初始化
					this.onWebSocketConnected()
				})
				
				uni.$on('websocket:disconnected', () => {
					// console.log('[App] WebSocket connection disconnected')
					// 连接断开时的应用级别处理
					this.onWebSocketDisconnected()
				})
				
				uni.$on('websocket:error', (error) => {
					// console.error('[App] WebSocket connection error:', error)
					// 可以在这里处理连接错误的应用级别逻辑
				})
			},
			
			// WebSocket连接成功的应用级别处理
			onWebSocketConnected() {
				// 可以在这里做一些连接成功后的初始化工作
				// 比如同步未读消息状态等
			},
			
			// WebSocket连接断开的应用级别处理
			onWebSocketDisconnected() {
				// 可以在这里处理断开连接的UI状态更新等
			},
			
			checkWebSocketConnection() {
				const token = uni.getStorageSync('Authorization')

				if (token) {
					const status = websocketManager.getStatus()
					console.log('[App] 检查 WebSocket 连接状态:', status)
					if (!status.isConnected && !status.isConnecting) {
						const userId = this.getUserIdFromStore()
						if (userId) {
							console.log('[App] WebSocket 未连接，尝试重连, userId:', userId)
							websocketManager.connect(userId, token)
						} else {
							console.warn('[App] 重连时未找到 userId')
						}
					}
				}
			},
			
			cleanupWebSocketListeners() {
				// 清理事件监听器
				uni.$off('websocket:connected')
				uni.$off('websocket:disconnected')
				uni.$off('websocket:error')
			},

			//#ifdef APP-PLUS
			checkUpdate() {
				//检查更新
				var _this = this;
				plus.runtime.getProperty(plus.runtime.appid, function(widgetInfo) {

					// if(widgetInfo.version == '0.0.6'){
					// 	plus.nativeUI.alert("The version is error, please download again !", function(){
					// 	       plus.runtime.quit(); 
					// 	}, "nativeUI", "OK");
					// };

					var paras = {
						version: widgetInfo.version
					}

					uni.setStorageSync("version", widgetInfo.version);
					_this.$http.get("/config/updates", {
						data: paras
					}, (res) => {
						var data = res.data;
						if (data.update && data.wgtUrl) {
							plus.nativeUI.showWaiting(
								"Check the new version, start downloading the update file...");
							uni.downloadFile({
								url: data.wgtUrl,
								success: (downloadResult) => {
									plus.nativeUI.closeWaiting();
									if (downloadResult.statusCode === 200) {
										plus.nativeUI.showWaiting(
											"The download is complete, start to install the update file..."
										);
										plus.runtime.install(downloadResult.tempFilePath, {
											force: true
										}, function() {
											plus.nativeUI.closeWaiting();
											plus.nativeUI.alert("Update Completed！",
												function() {
													plus.runtime.restart();
												});
										}, function(e) {
											plus.nativeUI.closeWaiting();
											plus.nativeUI.alert("Update Failed[" + e
												.code + "]：" + e.message);
										});
									}
								}
							});
						}
					})
				});
			},
			//#endif
			getConfigs() {
				var _this = this;
				_this.$http.get('/config/get', { skipFilter: true }, (res) => {
					if (res.statusCode == 200 && res.data) {
						let config = res.data.items
						if (config) {
							_this.$store.dispatch('saveConfigs', config);
							uni.setStorageSync('config', config)
						}
					}
				}, (err) => {
					// 忽略错误，不处理
				})
			},
			
			handleLaunchParams(option) {
				let params = {}
				
				if (option && option.query) {
					params = option.query
				} else {
					try {
						const launchOptions = uni.getLaunchOptionsSync()
						if (launchOptions && launchOptions.query) {
							params = launchOptions.query
						}
					} catch (e) {
						console.log('[App] getLaunchOptionsSync not available')
					}
				}
				
				if (typeof window !== 'undefined' && window.location && !params._aid) {
					const urlParams = new URLSearchParams(window.location.search)
					if (urlParams.has('_aid')) {
						params._aid = urlParams.get('_aid')
					}
					if (urlParams.has('_adl')) {
						params._adl = urlParams.get('_adl')
					}
				}
				
				if (params._aid) {
					uni.setStorageSync('default_r_aid', params._aid)
					console.log('[App] Saved default_r_aid:', params._aid)
				}
				if (params._adl) {
					uni.setStorageSync('default_adl', params._adl)
					console.log('[App] Saved default_adl:', params._adl)
					this.trackFlow(params._adl, params._aid)
				}
			},
			
			trackFlow(adl, aid) {
				if (!adl) return
				
				let memberId = null
				try {
					const userInfo = this.$store.state.userInfo
					if (userInfo && userInfo.id) {
						memberId = userInfo.id
					} else {
						const storedUserInfo = uni.getStorageSync('userInfo')
						if (storedUserInfo && storedUserInfo.id) {
							memberId = storedUserInfo.id
						}
					}
				} catch (e) {
					console.log('[App] Failed to get memberId:', e)
				}
				
				logAdlinkVisit(this.$http, adl, memberId).then((res) => {
					console.log('[App] Adlink visit logged successfully', res)
				}).catch((err) => {
					console.error('[App] Failed to log adlink visit:', err)
				})
			},
		},
		onLaunch: function(option) {

			var _this = this;

			_this.handleLaunchParams(option)

			// 注册登录事件监听，登录后立即连接 WebSocket
			_this.setupLoginListener()

			// 读取用户已存的语种偏好；首次启动无偏好时默认缅甸语（不跟随系统语言）
			var lang = uni.getStorageSync('UNI_LOCALE') || uni.getStorageSync('language') || 'mm';
			let langs = ['cn', 'en', 'mm', 'th']
			lang = langs.includes(lang) ? lang : 'mm'
			uni.removeStorageSync('noticed');
			if (lang) {
				config.language = language[lang]
				uni.setLocale(lang)
				this.$i18n.locale = lang;
			}

			//#ifdef APP-PLUS
			_this.checkUpdate();

			//每分钟检测一次更新
			var intervalID = setInterval(function() {
				_this.checkUpdate();
			}, 1000 * 60);
			//#endif
			
			// 获取配置信息
			_this.getConfigs()
			
			// 延迟初始化WebSocket，等待配置加载完成
			setTimeout(() => {
				_this.initWebSocket()
			}, 2000)
			
			uni.getSystemInfo({
				success: function(e) {
					// #ifndef MP
					Vue.prototype.StatusBar = e.statusBarHeight;
					if (e.platform == 'android') {
						Vue.prototype.CustomBar = e.statusBarHeight + 50;
					} else {
						Vue.prototype.CustomBar = e.statusBarHeight + 45;
					};
					// #endif

					// #ifdef MP-WEIXIN
					Vue.prototype.StatusBar = e.statusBarHeight;
					let custom = wx.getMenuButtonBoundingClientRect();
					Vue.prototype.Custom = custom;
					Vue.prototype.CustomBar = custom.bottom + custom.top - e.statusBarHeight;
					// #endif		

					// #ifdef MP-ALIPAY
					Vue.prototype.StatusBar = e.statusBarHeight;
					Vue.prototype.CustomBar = e.statusBarHeight + e.titleBarHeight;
					// #endif
				}
			})

			Vue.prototype.ColorList = [{
					title: '嫣红',
					name: 'red',
					color: '#D0342C'
				},
				{
					title: '桔橙',
					name: 'orange',
					color: '#f37b1d'
				},
				{
					title: '明黄',
					name: 'yellow',
					color: '#fbbd08'
				},
				{
					title: '橄榄',
					name: 'olive',
					color: '#8dc63f'
				},
				{
					title: '森绿',
					name: 'green',
					color: '#39b54a'
				},
				{
					title: '天青',
					name: 'cyan',
					color: '#1cbbb4'
				},
				{
					title: '海蓝',
					name: 'blue',
					color: '#0081ff'
				},
				{
					title: '姹紫',
					name: 'purple',
					color: '#6739b6'
				},
				{
					title: '木槿',
					name: 'mauve',
					color: '#9c26b0'
				},
				{
					title: '桃粉',
					name: 'pink',
					color: '#e03997'
				},
				{
					title: '棕褐',
					name: 'brown',
					color: '#a5673f'
				},
				{
					title: '玄灰',
					name: 'grey',
					color: '#8799a3'
				},
				{
					title: '草灰',
					name: 'gray',
					color: '#aaaaaa'
				},
				{
					title: '墨黑',
					name: 'black',
					color: '#333333'
				},
				{
					title: '雅白',
					name: 'white',
					color: '#ffffff'
				},
			]

		},
		onShow: function() {
			// console.log('[App] App Show - Application returned to foreground')
			
			// 刷新配置信息
			this.getConfigs()

			// 检查并恢复WebSocket连接
			this.checkWebSocketConnection()

			// 回到前台时刷新未读消息数（角标/铃铛）
			uni.$emit('message:unreadUpdate', null)
		},
		onHide: function() {
			// console.log('[App] App Hide - Application entered background')
			
			// 应用进入后台时保持WebSocket连接，以便接收推送消息
			// 如果需要节省资源，可以选择断开连接
		},
		
		onUnload: function() {
			// console.log('[App] App Unload - Application unloading')
			
			// 清理WebSocket连接和监听器
			websocketManager.close()
			this.cleanupWebSocketListeners()
			uni.$off('user:login')
		}

	}
</script>

<style lang="scss">
	@import "colorui/main.css";
	@import "colorui/icon.css";
	@import "colorui/my.css";
	@import "colorui/my.scss";

	@font-face {
		font-family: regular;
		src: url('~@/static/font/default.woff2');
	}


	body {
		font-family: 'regular';
	}

	:root {
		--app-viewport-height: 100vh;
	}

	// Keep H5 page overscroll inside the page scroll-view instead of moving
	// the document behind the fixed header.
	html,
	body {
		width: 100%;
		height: var(--app-viewport-height);
		margin: 0;
		overflow: hidden;
		overscroll-behavior: none;
	}

	#app,
	uni-app,
	uni-page,
	uni-page-wrapper,
	uni-page-body,
	page {
		width: 100%;
		height: var(--app-viewport-height);
		min-height: var(--app-viewport-height);
		overflow: hidden;
	}

	scroll-view,
	uni-scroll-view,
	.uni-scroll-view {
		overscroll-behavior-y: contain;
		-webkit-overflow-scrolling: touch;
	}

	// Keep the app shell background behind transparent page containers and
	// rounded header edges. Individual no-header pages opt into their own theme.
	page,
	body,
	#app {
		background-color: var(--theme-app-background-color, #{$theme-app-background-color});
		background-image: var(--theme-app-background-image, #{$theme-app-background});
		background-position: var(--theme-app-background-position, center);
		background-size: var(--theme-app-background-size, cover);
		background-repeat: var(--theme-app-background-repeat, no-repeat);
	}

	.nav-list {
		display: flex;
		flex-wrap: wrap;
		padding: 0px 40upx 0px;
		justify-content: space-between;
	}

	.nav-li {
		padding: 30upx;
		border-radius: 12upx;
		width: 45%;
		margin: 0 2.5% 40upx;
		//background-image: url(https://cdn.nlark.com/yuque/0/2019/png/280374/1552996358352-assets/web-upload/cc3b1807-c684-4b83-8f80-80e5b8a6b975.png);
		background-size: cover;
		background-position: center;
		position: relative;
		z-index: 1;
	}

	.nav-li::after {
		content: "";
		position: absolute;
		z-index: -1;
		background-color: inherit;
		width: 100%;
		height: 100%;
		left: 0;
		bottom: -10%;
		border-radius: 10upx;
		opacity: 0.2;
		transform: scale(0.9, 0.9);
	}

	.nav-li.cur {
		color: #fff;
		background: rgb(94, 185, 94);
		box-shadow: 4upx 4upx 6upx rgba(94, 185, 94, 0.4);
	}

	.nav-title {
		font-size: 32upx;
		font-weight: 300;
	}

	.nav-title::first-letter {
		font-size: 40upx;
		margin-right: 4upx;
	}

	.nav-name {
		font-size: 28upx;
		text-transform: Capitalize;
		margin-top: 20upx;
		position: relative;
	}

	.nav-name::before {
		content: "";
		position: absolute;
		display: block;
		width: 40upx;
		height: 6upx;
		background: #fff;
		bottom: 0;
		right: 0;
		opacity: 0.5;
	}

	.nav-name::after {
		content: "";
		position: absolute;
		display: block;
		width: 100upx;
		height: 1px;
		background: #fff;
		bottom: 0;
		right: 40upx;
		opacity: 0.3;
	}

	.nav-name::first-letter {
		font-weight: bold;
		font-size: 36upx;
		margin-right: 1px;
	}

	.nav-li text {
		position: absolute;
		right: 30upx;
		top: 30upx;
		font-size: 52upx;
		width: 60upx;
		height: 60upx;
		text-align: center;
		line-height: 60upx;
	}

	.text-light {
		font-weight: 300;
	}

	uni-toast {
		z-index: 999999 !important;
	}

	@keyframes show {
		0% {
			transform: translateY(-50px);
		}

		60% {
			transform: translateY(40upx);
		}

		100% {
			transform: translateY(0px);
		}
	}

	@-webkit-keyframes show {
		0% {
			transform: translateY(-50px);
		}

		60% {
			transform: translateY(40upx);
		}

		100% {
			transform: translateY(0px);
		}
	}
	.blank{
		padding:10px;
	}
</style>