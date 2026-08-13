import Vue from 'vue'
import App from './App'
import i18n from './locale/i18n.js'


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

import themeManager from './utils/theme/manager.js'
themeManager.initPreset()

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
Vue.component('message-notification', () => import('@/components/message-notification/message-notification.vue'));
import DateRangePicker from './components/common/date-range-picker.vue'
Vue.component('date-range-picker',DateRangePicker)

import LoginModal from './components/common/login_modal.vue'
Vue.component('login-modal',LoginModal)

import cuCustom from './colorui/components/cu-custom.vue'
Vue.component('cu-custom',cuCustom)

// 顶栏底栏
Vue.component('zw-header', () => import('@/components/common/header.vue'));
Vue.component('zw-footer', () => import('@/components/common/footer.vue'));
Vue.component('global-notice', () => import('@/components/common/global-notice.vue'));
Vue.component('theme-icon', () => import('@/components/common/theme-icon.vue'));
Vue.component('theme-logo', () => import('@/components/common/theme-logo.vue'));

Vue.config.productionTip = false

App.mpType = 'app'



const app = new Vue({
	i18n,
    ...App
})
app.$mount()



 
