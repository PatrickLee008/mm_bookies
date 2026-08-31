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
	const updateAppViewportHeight = () => {
		const visualViewport = window.visualViewport
		const height = visualViewport && visualViewport.height
			? visualViewport.height
			: window.innerHeight

		if (height > 0) {
			document.documentElement.style.setProperty('--app-viewport-height', `${height}px`)
		}
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



 
