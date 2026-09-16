import Vue from 'vue'
import App from './App'
import i18n from './locale/i18n.js'
import MessageNotification from './components/message-notification/message-notification.vue'
import ZwHeader from './components/common/header.vue'
import ZwFooter from './components/common/footer.vue'
import GlobalNotice from './components/common/global-notice.vue'
import ThemeIcon from './components/common/theme-icon.vue'
import ThemeLogo from './components/common/theme-logo.vue'

// Use the visible H5 viewport so fixed-height page shells do not extend
// behind the browser toolbar.
if (typeof window !== 'undefined' && typeof document !== 'undefined') {
	// 最近一次成功写入的视口尺寸。判断键盘弹出时不能比较 innerHeight 与
	// visualViewport.height 的差值 —— iOS 上两者的更新时机不同步（window 的
	// resize 可能晚于 innerHeight 已变小时触发），差值时有时无导致守卫不稳定。
	// 只与上次写入值比较则与事件触发顺序无关。
	let lastViewportWidth = window.innerWidth
	let lastViewportHeight = window.innerHeight

	const updateAppViewportHeight = () => {
		const visualViewport = window.visualViewport
		const width = visualViewport && visualViewport.width
			? visualViewport.width
			: window.innerWidth
		const height = visualViewport && visualViewport.height
			? visualViewport.height
			: window.innerHeight

		if (height <= 0) return

		// 高度骤降（>180px）且宽度不变 = 软键盘弹出。跳过更新，保持
		// --app-viewport-height 为全高：App.vue 的全局壳层（固定 height +
		// overflow:hidden）若塌缩，iOS 顶起 WebView 内容后键盘上方会露出
		// html 之外的画布主题色块盖住表单。宽度显著变化（>50px）说明是
		// 旋转/分屏，正常写入；键盘收起时高度回升，同样正常写入恢复全高。
		if (lastViewportHeight - height > 180 && Math.abs(width - lastViewportWidth) <= 50) {
			return
		}

		lastViewportWidth = width
		lastViewportHeight = height
		document.documentElement.style.setProperty('--app-viewport-height', `${height}px`)
	}

	updateAppViewportHeight()
	window.addEventListener('resize', updateAppViewportHeight)
	window.addEventListener('orientationchange', updateAppViewportHeight)
	if (window.visualViewport) {
		window.visualViewport.addEventListener('resize', updateAppViewportHeight)
	}
}


import toolbox from './utils/toolbox.js';
Vue.prototype.$toolbox = toolbox;

import my from './utils/my.js'
var http = my.http;
var getUserInfo = my.getUserInfo;
var getConfigs = my.getConfigs;
Vue.prototype.$http =http;

import httpPay from './utils/httpPay.js'
Vue.prototype.$httpPay =httpPay.httpPay;

import config from './utils/config.js'
Vue.prototype.$config =config;

import noticeManager from './utils/notice.js'
Vue.prototype.$notice = noticeManager;

import store from './store/index.js';
Vue.prototype.$store =store;
// WebSocket服务
import websocketManager from './utils/websocket.js'
import messageStorage from './utils/message-storage.js'
Vue.prototype.$websocket = websocketManager;
Vue.prototype.$messageStorage = messageStorage;

// 消息实时弹窗提醒
import messageNotificationManager from './utils/message-notification-manager.js'
uni.$messageNotification = messageNotificationManager;
Vue.prototype.$messageNotification = messageNotificationManager;
Vue.component('message-notification', MessageNotification)
import DateRangePicker from './components/common/date-range-picker.vue'
Vue.component('date-range-picker',DateRangePicker)

import LoginModal from './components/common/login_modal.vue'
Vue.component('login-modal',LoginModal)

import cuCustom from './colorui/components/cu-custom.vue'
Vue.component('cu-custom',cuCustom)

// 顶栏底栏
Vue.component('zw-header', ZwHeader)
Vue.component('zw-footer', ZwFooter)
Vue.component('global-notice', GlobalNotice)
Vue.component('theme-icon', ThemeIcon)
Vue.component('theme-logo', ThemeLogo)

Vue.config.productionTip = false

App.mpType = 'app'



const app = new Vue({
	i18n,
    ...App
})
app.$mount()



 
