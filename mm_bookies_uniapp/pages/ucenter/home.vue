<template name="ucenter">
	<view class="bg-white full-page">
		<zw-header @doSomething=""></zw-header>

		<!-- from tangjq--- header占位元素，防止内容被遮挡 -->
		<view class="header-placeholder"></view>

		<scroll-view scroll-y style="height: calc(100vh - 250px);">
			<!-- <view class="title-bar">
				<view class="flex-row justify-between" style="">
					<view class="flex-row align-center" style="">
						<image class="yellow2dblue" style="height: 25px;" mode="heightFix" src="/static/icon/setting.png"></image>
						<text class="title-text" style="">{{$t('setting')}}</text>
					</view>
				</view>
			</view> -->

			<!-- 主列表区域 -->
			<view class="settings-list-container">
				<view class="setting-item" v-for="(bar,index) in bar_list" :key="index" @click="list_method(bar.method,bar.args)" v-if="!bar.para.need_login ||(isLogin&&bar.para.need_login)">
					<text class="setting-item-text">{{$t(bar.title)}}</text>
				</view>

				<!-- #ifdef APP-PLUS -->
				<view class="setting-item version-item">
					<text class="setting-item-text">Version: {{version}}</text>
				</view>
				<!-- #endif-->
			</view>

			<view class="padding"></view>
		</scroll-view>

		<!-- Profile 弹窗 -->
		<view class="modal-overlay" v-if="profileModalVisible" @click="hideProfileModal">
			<view class="modal-content profile-modal" @click.stop="">
				<view class="modal-header">
					<text class="modal-title">{{ $t('edit profile') }}</text>
					<text class="modal-close" @click="hideProfileModal">✕</text>
				</view>
				<view class="modal-body">
					<!-- 用户头像 -->
					<view class="profile-avatar-section">
						<view class="profile-avatar-circle">
							<image class="profile-avatar-img" src="/static/icon/nav/user_avatar.png" mode="aspectFill"></image>
						</view>
					</view>

					<!-- My ID -->
					<view class="profile-info-row">
						<text class="profile-info-label">{{ $t('my_id') }} : {{ $store.state.userInfo.id || userInfo.id || '00001' }}</text>
					</view>

					<!-- Phone No -->
					<view class="profile-phone-row">
						<text class="profile-phone-label">{{ $t('phone_no') }}: {{ $store.state.userInfo.phone || userInfo.phone || '0987654321' }}</text>
						<!-- <image class="profile-edit-icon" src="/static/icon/ucenter/edit.png" mode="aspectFit"></image> -->
					</view>

					<!-- Change Password 按钮 -->
					<view class="profile-change-pwd-btn" @click="showPasswordChangeModal">
						<text class="profile-change-pwd-text">{{ $t('Change password') }}</text>
					</view>

					<!-- Save 按钮 -->
					<view class="profile-save-btn" @click="hideProfileModal">
						<text class="profile-save-text">{{ $t('save') }}</text>
					</view>
				</view>
			</view>
		</view>

		<!-- Contact 弹窗 -->
		<view class="modal-overlay" v-if="contactModalVisible" @click="hideContactModal">
			<view class="modal-content contact-modal" @click.stop="">
				<view class="modal-header">
					<text class="modal-title" style="text-align: left;">{{ $t('contact us') }}</text>
					<text class="modal-close" @click="hideContactModal">✕</text>
				</view>
				<view class="modal-body">
					<!-- Live Chat 按钮 -->
					<view class="live-chat-btn" @click="openLiveChat">
						<text class="live-chat-text">{{ $t('welcome_to_live_chat') }}</text>
						<text class="live-chat-arrow">➤</text>
					</view>

					<text class="contact-section-title">{{ $t('Contact') }}</text>
					<!-- 隐藏 contact-description -->
					<text class="contact-description" v-if="false">{{ $t('explore_website') }}</text>

					<!-- 富文本显示 contact_us 内容 -->
					<view class="contact-rich-text" v-if="configs && configs.contact_us">
						<rich-text :nodes="contactUsRichText" @itemclick="handleRichTextClick"></rich-text>
					</view>

					<!-- 原来的联系方式列表，用 v-if="false" 隐藏 -->
					<view v-if="false">
					<view class="contact-row-item">
						<text class="contact-row-label">{{ $t('viber') }}</text>
						<view class="contact-input-wrapper">
							<text class="contact-input-value">09789456123</text>
							<view class="contact-copy-button" @click="copyToClipboard('09789456123')">
								<text class="copy-button-text">{{ $t('copy') }}</text>
								<image class="copy-button-icon" src="/static/icon/ucenter/copy.png" mode="aspectFit"></image>
							</view>
						</view>
					</view>

					<view class="contact-row-item">
						<text class="contact-row-label">{{ $t('telegram') }}</text>
						<view class="contact-input-wrapper">
							<text class="contact-input-value">09789456123</text>
							<view class="contact-copy-button" @click="copyToClipboard('09789456123')">
								<text class="copy-button-text">{{ $t('copy') }}</text>
								<image class="copy-button-icon" src="/static/icon/ucenter/copy.png" mode="aspectFit"></image>
							</view>
						</view>
					</view>

					<view class="contact-row-item">
						<text class="contact-row-label">{{ $t('email') }}</text>
						<view class="contact-input-wrapper">
							<text class="contact-input-value">mmbookies@test.com</text>
							<view class="contact-copy-button" @click="copyToClipboard('mmbookies@test.com')">
								<text class="copy-button-text">{{ $t('copy') }}</text>
								<image class="copy-button-icon" src="/static/icon/ucenter/copy.png" mode="aspectFit"></image>
							</view>
						</view>
					</view>
					</view>
				</view>
			</view>
		</view>

		<!-- About 弹窗 -->
		<view class="modal-overlay" v-if="aboutModalVisible" @click="hideAboutModal">
			<view class="modal-content about-modal" @click.stop="">
				<view class="modal-header">
					<text class="modal-title" style="text-align: left;">{{ $t('about') }}</text>
					<text class="modal-close" @click="hideAboutModal">✕</text>
				</view>
				<view class="modal-body">
					<!-- Rules 部分 -->
					<view class="about-section">
						<text class="about-section-title">{{ $t('rules') }}</text>
						<view class="about-rule-item">
							<text class="rule-number">1.</text>
							<text class="rule-text">Rules and regulation of mm bookies detail explained here</text>
						</view>
						<view class="about-rule-item">
							<text class="rule-number">2.</text>
							<text class="rule-text">Terms of service for online betting platforms outlined here</text>
						</view>
						<view class="about-rule-item">
							<text class="rule-number">3.</text>
							<text class="rule-text">Common betting strategies used by successful gamblers</text>
						</view>
						<view class="about-rule-item">
							<text class="rule-number">4.</text>
							<text class="rule-text">Legal age and identification requirements for placing bets</text>
						</view>
						<view class="about-rule-item">
							<text class="rule-number">5.</text>
							<text class="rule-text">How to recognize and report suspicious betting activities</text>
						</view>
					</view>

					<!-- Regulation 部分 -->
					<view class="about-section">
						<text class="about-section-title">{{ $t('regulation') }}</text>
						<view class="about-rule-item">
							<text class="rule-number">1.</text>
							<text class="rule-text">Rules and regulation of mm bookies detail explained here</text>
						</view>
						<view class="about-rule-item">
							<text class="rule-number">2.</text>
							<text class="rule-text">Terms of service for online betting platforms outlined here</text>
						</view>
						<view class="about-rule-item">
							<text class="rule-number">3.</text>
							<text class="rule-text">Common betting strategies used by successful gamblers</text>
						</view>
						<view class="about-rule-item">
							<text class="rule-number">4.</text>
							<text class="rule-text">Legal age and identification requirements for placing bets</text>
						</view>
						<view class="about-rule-item">
							<text class="rule-number">5.</text>
							<text class="rule-text">How to recognize and report suspicious betting activities</text>
						</view>
					</view>
				</view>
			</view>
		</view>

		<!-- Language 弹窗 -->
		<view class="modal-overlay" v-if="languageModalVisible" @click="hideLanguageModal">
			<view class="modal-content language-modal" @click.stop="">
				<view class="modal-header">
					<text class="modal-title">{{ $t('change_language') }}</text>
					<text class="modal-close" @click="hideLanguageModal">✕</text>
				</view>
				<view class="modal-body">
					<!-- 语言选项列表 -->
					<view class="language-item" @click="selectLanguage('mm')">
						<text class="language-label">မြန်မာ</text>
						<view class="radio-circle" :class="{ 'radio-selected': selectedLanguage === 'mm' }">
							<view class="radio-dot" v-if="selectedLanguage === 'mm'"></view>
						</view>
					</view>

					<view class="language-item" @click="selectLanguage('en')">
						<text class="language-label">{{ $t('English') }}</text>
						<view class="radio-circle" :class="{ 'radio-selected': selectedLanguage === 'en' }">
							<view class="radio-dot" v-if="selectedLanguage === 'en'"></view>
						</view>
					</view>

					<view class="language-item" @click="selectLanguage('th')">
						<text class="language-label">ภาษาไทย</text>
						<view class="radio-circle" :class="{ 'radio-selected': selectedLanguage === 'th' }">
							<view class="radio-dot" v-if="selectedLanguage === 'th'"></view>
						</view>
					</view>

					<view class="language-item" @click="selectLanguage('cn')">
						<text class="language-label">中文</text>
						<view class="radio-circle" :class="{ 'radio-selected': selectedLanguage === 'cn' }">
							<view class="radio-dot" v-if="selectedLanguage === 'cn'"></view>
						</view>
					</view>

					<!-- Confirm 按钮 -->
					<view class="language-confirm-btn" @click="confirmLanguage()">
						<text class="language-confirm-text">{{ $t('confirm') }}</text>
					</view>
				</view>
			</view>
		</view>

		<!-- Customer Support 弹窗 -->
		<view class="modal-overlay" v-if="customerSupportModalVisible" @click="hideCustomerSupportModal">
			<view class="modal-content support-modal" @click.stop="">
				<view class="modal-header">
					<text class="modal-title" style="text-align: left;">{{ $t('customer_support') }}</text>
					<text class="modal-close" @click="hideCustomerSupportModal">✕</text>
				</view>
				<view class="modal-body">
					<text class="support-main-title">{{ $t('contact us') }}</text>
					<text class="support-description">{{ $t('explore_website') }}</text>

					<!-- 支持渠道列表 -->
					<view class="support-channel-section">
						<text class="support-channel-title">KBZPay</text>
						<view class="support-link-item" @click="openSupportLink('https://contact.mmbookies/D1')">
							<text class="support-link-text">https://contact.mmbookies/D1</text>
						</view>
						<view class="support-link-item" @click="openSupportLink('https://contact.mmbookies/D1')">
							<text class="support-link-text">https://contact.mmbookies/D1</text>
						</view>
						<view class="support-link-item" @click="openSupportLink('https://contact.mmbookies/D1')">
							<text class="support-link-text">https://contact.mmbookies/D1</text>
						</view>
						<view class="support-link-item" @click="openSupportLink('https://contact.mmbookies/D1')">
							<text class="support-link-text">https://contact.mmbookies/D1</text>
						</view>
					</view>

					<view class="support-channel-section">
						<text class="support-channel-title">KBZPay</text>
						<view class="support-link-item" @click="openSupportLink('https://contact.mmbookies/D1')">
							<text class="support-link-text">https://contact.mmbookies/D1</text>
						</view>
						<view class="support-link-item" @click="openSupportLink('https://contact.mmbookies/D1')">
							<text class="support-link-text">https://contact.mmbookies/D1</text>
						</view>
						<view class="support-link-item" @click="openSupportLink('https://contact.mmbookies/D1')">
							<text class="support-link-text">https://contact.mmbookies/D1</text>
						</view>
						<view class="support-link-item" @click="openSupportLink('https://contact.mmbookies/D1')">
							<text class="support-link-text">https://contact.mmbookies/D1</text>
						</view>
					</view>
				</view>
			</view>
		</view>

		<!-- Change Password 弹窗 -->
		<view class="modal-overlay" v-if="passwordChangeModalVisible" @click="hidePasswordChangeModal">
			<view class="modal-content password-change-modal" @click.stop="">
				<view class="modal-header">
					<text class="modal-title">{{ $t('Change password') }}</text>
					<text class="modal-close" @click="hidePasswordChangeModal">✕</text>
				</view>
				<view class="modal-body">
					<!-- Old Password 输入框 -->
					<view class="pwd-input-wrapper" :class="{'input-focused': old_password_focused, 'input-error': old_password_error}">
						<input class="pwd-input" :type="show_old_password ? 'text' : 'password'" v-model="old_password" :placeholder="$t('enter_old_password')" @focus="old_password_focused = true" @blur="handleOldPasswordBlur" @input="clearPasswordErrors" />
						<view class="eye-icon" @click="show_old_password = !show_old_password">
							<text :class="show_old_password ? 'cuIcon-attentionfill' : 'cuIcon-attention'"></text>
						</view>
					</view>

					<!-- New Password 输入框 -->
					<view class="pwd-input-wrapper" :class="{'input-focused': new_password_focused, 'input-error': new_password_error}">
						<input class="pwd-input" :type="show_new_password ? 'text' : 'password'" v-model="new_password" :placeholder="$t('enter_new_password')" @focus="new_password_focused = true" @blur="handleNewPasswordBlur" @input="clearPasswordErrors" />
						<view class="eye-icon" @click="show_new_password = !show_new_password">
							<text :class="show_new_password ? 'cuIcon-attentionfill' : 'cuIcon-attention'"></text>
						</view>
					</view>

					<!-- Confirm Password 输入框 -->
					<view class="pwd-input-wrapper" :class="{'input-focused': confirm_password_focused, 'input-error': confirm_password_error}">
						<input class="pwd-input" :type="show_confirm_password ? 'text' : 'password'" v-model="confirm_password" :placeholder="$t('enter_confirm_new_password')" @focus="confirm_password_focused = true" @blur="handleConfirmPasswordBlur" @input="clearPasswordErrors" />
						<view class="eye-icon" @click="show_confirm_password = !show_confirm_password">
							<text :class="show_confirm_password ? 'cuIcon-attentionfill' : 'cuIcon-attention'"></text>
						</view>
					</view>

					<!-- 错误提示 -->
					<text class="pwd-error-message" v-if="password_error_message">{{ password_error_message }}</text>

					<!-- Cancel 按钮 -->
					<view class="pwd-cancel-btn" @click="hidePasswordChangeModal">
						<text class="pwd-cancel-text">{{ $t('cancel') }}</text>
					</view>

					<!-- Save 按钮 -->
					<view class="pwd-save-btn" @click="submitPasswordChange">
						<text class="pwd-save-text">{{ $t('save') }}</text>
					</view>
				</view>
			</view>
		</view>

		<!-- Logout 弹窗 -->
		<view class="logout-modal" v-if="showLogoutConfirm" @click="hideLogoutModal">
			<view class="logout-modal-content" @click.stop="">
				<view class="logout-modal-header">
					<text class="logout-modal-title">{{ $t('confirm_logout') }}</text>
				</view>
				<view class="logout-modal-body">
					<text class="logout-question">{{ $t('confirm_logout') }}</text>
				</view>
				<view class="logout-modal-buttons">
					<view class="logout-btn-confirm" @click="logout">
						<text class="logout-btn-text-red">{{ $t('logout') }}</text>
					</view>
					<view class="logout-btn-cancel" @click="hideLogoutModal">
						<text class="logout-btn-text-white">{{ $t('cancel') }}</text>
					</view>
				</view>
			</view>
		</view>
	</view>
</template>

<script>
	import config from '../../utils/config.js'
	import language from '../../utils/language.js'
	import dateFormatUtils from "../../utils/utils.js"

	export default {
		components: {},
		name: "ucenter",
		data() {
			return {
				isLogin: uni.getStorageSync('Authorization') || false,
				temp: {},
				about: '',
				currentLanguage: config.language,
				picker: '',
				contact2: '',
				contact: [],
				bar_list: [
					// from tangjq--- 按设计稿顺序排列的新列表项
					{
						title: "profile", // from tangjq--- 使用语言文件中的键名
						content: '',
						method: 'showProfileModal', // from tangjq--- 改为显示弹窗
						args: [],
						img: '../../static/icon/ucenter/profile.png',
						para: {
							need_login: true
						},
					},
					{
						title: "contact us", // from tangjq--- 使用语言文件中的键名
						content: '',
						method: 'showContactModal', // from tangjq--- 改为显示弹窗
						args: [],
						img: '../../static/icon/ucenter/contact_lblue.png',
						para: {},
					},
					{
						title: "about us", // from tangjq--- 使用语言文件中的键名
						content: '',
						method: 'showAboutModal', // from tangjq--- 改为显示弹窗
						args: [],
						img: '../../static/icon/ucenter/about.png',
						para: {},
					},
					{
						title: "language", // from tangjq--- 使用语言文件中的键名
						content: '',
						method: 'showLanguageModal', // from tangjq--- 改为显示弹窗
						args: [],
						img: '../../static/icon/ucenter/language.png',
						para: {},
					},
					{
						title: "logout", // from tangjq--- 使用语言文件中的键名
						content: '',
						method: 'showLogoutModal',
						args: [],
						img: '../../static/icon/ucenter/logout.png',
						para: {
							need_login: true
						},
					},
					// from tangjq--- 保留的原有列表项（不在设计稿中但保留）
					// {
					// 	title: 'account_information',
					// 	content: '',
					// 	method: 'goto',
					// 	args: ['/pages/ucenter/account'],
					// 	img: '../../static/icon/ucenter/account.png',
					// 	para: {
					// 		need_login: true
					// 	},
					// },
					// {
					// 	title: 'awc_game_lobby',
					// 	content: '',
					// 	method: 'enterAWCGameLobby',
					// 	args: [],
					// 	img: '../../static/icon/ucenter/logo-AWC-l-CGTOWzF4.webp',
					// 	para: {
					// 		need_login: true
					// 	},
					// },
					// {
					// 	title: 'invite',
					// 	content: '',
					// 	method: 'goto',
					// 	args: ['/pages/ucenter/invite/index'],
					// 	img: '../../static/icon/ucenter/invite.png',
					// 	para: {
					// 		need_login: true
					// 	},
					// },
					// {
					// 	title: 'bonus',
					// 	content: '',
					// 	method: 'goto',
					// 	args: ['/pages/ucenter/bonus'],
					// 	img: '../../static/icon/ucenter/bonus.png',
					// 	para: {
					// 		need_login: true
					// 	},
					// },
					// {
					// 	title: "downloadapp",
					// 	content: 'V 0.0.1',
					// 	method: 'goto',
					// 	args: ['/pages/ucenter/download'],
					// 	img: '../../static/icon/ucenter/download.png',
					// 	para: {},
					// },
				],
				contact: '',
				dislan: 0,
				dislan2: 0,
				version: uni.getStorageSync("version"),
				modal_name: '',

				// from tangjq--- Logout弹窗控制变量
				showLogoutConfirm: false,

				// from tangjq--- 各个弹窗的控制变量
				profileModalVisible: false,
				contactModalVisible: false,
				aboutModalVisible: false,
				languageModalVisible: false,
				customerSupportModalVisible: false,

				// from tangjq--- 语言选择器
				selectedLanguage: uni.getStorageSync('UNI_LOCALE') || 'mm',

				// from tangjq--- Change Password 弹窗相关变量
				passwordChangeModalVisible: false,
				old_password: '',
				new_password: '',
				confirm_password: '',
				old_password_focused: false,
				new_password_focused: false,
				confirm_password_focused: false,
				old_password_error: false,
				new_password_error: false,
				confirm_password_error: false,
				show_old_password: false,
				show_new_password: false,
				show_confirm_password: false,
				password_error_message: '',
			}
		},

		computed: {
			contactUsRichText() {
				if (this.configs && this.configs.contact_us) {
					let html = this.parseHtmlToNodes(this.configs.contact_us)
					return html;
				}
				return []
			}
		},

		methods: {
			// from tangjq--- 输入时清除密码错误信息
			clearPasswordErrors() {
				this.old_password_error = false
				this.new_password_error = false
				this.confirm_password_error = false
				this.password_error_message = ''
			},
			// from tangjq--- 显示Logout确认弹窗
			showLogoutModal() {
				this.showLogoutConfirm = true
			},
			// from tangjq--- 隐藏Logout确认弹窗
			hideLogoutModal() {
				this.showLogoutConfirm = false
			},

			// from tangjq--- Profile弹窗方法
			showProfileModal() {
				this.profileModalVisible = true
			},
			hideProfileModal() {
				this.profileModalVisible = false
			},

			// from tangjq--- Contact弹窗方法
			showContactModal() {
				this.contactModalVisible = true
			},
			hideContactModal() {
				this.contactModalVisible = false
			},
			// 富文本点击事件处理
			handleRichTextClick(e) {
				const node = e.detail.node
				if (node && node.name === 'a' && node.attrs) {
					const href = node.attrs.href
					if (href) {
						if (href.startsWith('http://') || href.startsWith('https://')) {
							// #ifdef H5
							window.open(href, '_blank')
							// #endif
							// #ifndef H5
							uni.navigateTo({
								url: `/pages/webview/index?url=${encodeURIComponent(href)}`
							})
							// #endif
						} else if (href.startsWith('tel:')) {
							const phoneNumber = href.replace('tel:', '')
							uni.makePhoneCall({
								phoneNumber: phoneNumber
							})
						}
					}
				}
			},
			// 解析 HTML 为 rich-text nodes 数组
			parseHtmlToNodes(html) {
				if (!html) return []
				const nodes = []
				// 匹配 HTML 标签：支持普通标签和自闭合标签
				const tagRegex = /<(\/?)(\w+)([^>]*?)(\/?)>/g
				let lastIndex = 0
				let match
				let currentParent = null // 当前打开的块级标签节点（如 p）

				while ((match = tagRegex.exec(html)) !== null) {
					// 处理标签之前的文本
					if (match.index > lastIndex) {
						const text = html.substring(lastIndex, match.index)
						const textParts = this._parseUrlsInText(text)
						if (currentParent && currentParent.children) {
							currentParent.children.push(...textParts)
						} else {
							nodes.push(...textParts)
						}
					}

					const isClosing = match[1] === '/'
					const tagName = match[2].toLowerCase()
					const attrsStr = match[3]
					const isSelfClosing = match[4] === '/'

					if (tagName === 'br' || (isSelfClosing && tagName === 'br')) {
						const brNode = { name: 'br', attrs: {} }
						if (currentParent && currentParent.children) {
							currentParent.children.push(brNode)
						} else {
							nodes.push(brNode)
						}
					} else if (isClosing) {
						if (tagName === 'p' || tagName === 'div') {
							currentParent = null
						}
					} else {
						// 开标签
						if (tagName === 'a') {
							const hrefMatch = attrsStr.match(/href=["']([^"']+)["']/)
							const href = hrefMatch ? hrefMatch[1] : ''
							const aNode = {
								name: 'a',
								attrs: {
									href: href,
									style: 'color: #4fb3bf; text-decoration: underline;'
								},
								children: []
							}
							if (currentParent && currentParent.children) {
								currentParent.children.push(aNode)
							} else {
								nodes.push(aNode)
							}
						} else if (tagName === 'p') {
							const pNode = { name: 'p', attrs: {}, children: [] }
							nodes.push(pNode)
							currentParent = pNode
						}
						// 其他标签按需扩展
					}

					lastIndex = match.index + match[0].length
				}

				// 处理剩余文本
				if (lastIndex < html.length) {
					const text = html.substring(lastIndex)
					const textParts = this._parseUrlsInText(text)
					if (currentParent && currentParent.children) {
						currentParent.children.push(...textParts)
					} else {
						nodes.push(...textParts)
					}
				}

				if (nodes.length === 0) {
					return [{
						name: 'div',
						attrs: {},
						children: [{
							type: 'text',
							text: html
						}]
					}]
				}
				return nodes
			},
			// 将文本中的裸 URL 转为 <a> 节点
			_parseUrlsInText(text) {
				if (!text) return []
				const parts = []
				// 匹配以 http:// 或 https:// 开头的 URL
				const urlRegex = /(https?:\/\/[^\s<>]+)/gi
				let lastIdx = 0
				let m

				while ((m = urlRegex.exec(text)) !== null) {
					if (m.index > lastIdx) {
						const before = text.substring(lastIdx, m.index)
						if (before) {
							parts.push({ type: 'text', text: before })
						}
					}
					parts.push({
						name: 'a',
						attrs: {
							href: m[0],
							style: 'color: #4fb3bf; text-decoration: underline;'
						},
						children: [{ type: 'text', text: m[0] }]
					})
					lastIdx = m.index + m[0].length
				}

				if (lastIdx < text.length) {
					const after = text.substring(lastIdx)
					if (after) {
						parts.push({ type: 'text', text: after })
					}
				}

				if (parts.length === 0 && text) {
					parts.push({ type: 'text', text })
				}
				return parts
			},
			openLiveChat() {
				// from tangjq--- 根据用户登录状态拼接客服链接
				const baseUrl = 'https://chat.wellytalk.com/MDE5ZDA1MDItYzU3MC03YjYyLThkMGItMjQ4YTJjMjQ0ODkwfGQzZjQwNTg3NzExOTAzMjFmOWU4MWM4ZDZmMGM4ZDQ4YjAyNDg5ZjQyM2EyZjgyZjc2NmJmMjI2ZTdlM2MxMzA='
				const params = []
				const userInfo = this.$store.state.userInfo || {}

				if (this.isLogin && userInfo.id) {
					params.push(`user_id=${userInfo.id}`)
					params.push(`user_name=${encodeURIComponent(userInfo.phone || userInfo.nick_name || '')}`)
				} else {
					// 游客模式：生成持久化的访客ID
					let guestIdentity = null
					try {
						guestIdentity = JSON.parse(uni.getStorageSync('guest_cs_identity') || 'null')
					} catch (e) {}
					if (!guestIdentity || !guestIdentity.id) {
						const rand = Math.random().toString(36).slice(2, 10).toUpperCase()
						const ts = Date.now().toString(36).toUpperCase()
						guestIdentity = {
							id: `G_${ts}${rand}`,
							name: `Guest_${Math.floor(Math.random() * 900000) + 100000}`
						}
						uni.setStorageSync('guest_cs_identity', JSON.stringify(guestIdentity))
					}
					params.push(`user_id=${guestIdentity.id}`)
					params.push(`user_name=${encodeURIComponent(guestIdentity.name)}`)
				}
				params.push('website_name=mmbookies')

				const url = `${baseUrl}?${params.join('&')}`
				uni.navigateTo({
					url: `/pages/webview/index?url=${encodeURIComponent(url)}`
				})
				this.hideContactModal()
			},
			copyToClipboard(text) {
				uni.setClipboardData({
					data: text,
					success: () => {
						uni.showToast({
							title: this.$t('copied'),
							icon: 'success',
							duration: 1500
						})
					}
				})
			},

			// from tangjq--- About弹窗方法
			showAboutModal() {
				this.aboutModalVisible = true
			},
			hideAboutModal() {
				this.aboutModalVisible = false
			},

			// from tangjq--- Language弹窗方法
			showLanguageModal() {
				this.languageModalVisible = true
			},
			hideLanguageModal() {
				this.languageModalVisible = false
			},
			selectLanguage(lang) {
				this.selectedLanguage = lang
			},
			confirmLanguage() {
				if (!this.selectedLanguage) this.selectedLanguage = 'mm'
				config.language = language[this.selectedLanguage]
				uni.setStorageSync('language', this.selectedLanguage)
				uni.setLocale(this.selectedLanguage)
				this.$i18n.locale = this.selectedLanguage
				this.hideLanguageModal()

				// 刷新页面
				setTimeout(() => {
					uni.reLaunch({
						url: '/pages/ucenter/home'
					})
				}, 300)
			},

			// from tangjq--- Customer Support弹窗方法
			showCustomerSupportModal() {
				this.customerSupportModalVisible = true
			},
			hideCustomerSupportModal() {
				this.customerSupportModalVisible = false
			},
			openSupportLink(url) {
				//#ifdef H5
				window.open(url, '_blank')
				//#endif

				//#ifdef APP-PLUS
				plus.runtime.openURL(url)
				//#endif

				//#ifdef MP
				uni.setClipboardData({
					data: url,
					success: () => {
						uni.showToast({
							title: this.$t('link_copied'),
							icon: 'success'
						})
					}
				})
				//#endif
			},
			show_modal(modal) {
				this.modal_name = modal
			},
			list_method(method, args) {
				// 传入方法名及参数
				if (typeof this[method] === 'function') {
					this[method](...args);
				} else {
					console.error(`${method}方法不存在`);
				}
			},
			// AWC游戏大厅入口
			enterAWCGameLobby() {
				var _this = this

				// 检查是否登录
				if (!_this.isLogin) {
					uni.showModal({
						title: _this.$t('tips'),
						content: _this.$t('please_sign_in_to_receive_the_coupon'),
						showCancel: false,
						confirmText: _this.$t('ok'),
						success: function(res) {
							if (res.confirm) {
								uni.navigateTo({
									url: '/pages/login/login'
								})
							}
						}
					})
					return
				}

				// 获取用户信息
				var userInfo = _this.$store.state.userInfo
				if (!userInfo || !userInfo.phone) {
					uni.showToast({
						title: _this.$t('unable_get_user_info'),
						icon: 'none'
					})
					return
				}

				// 显示加载中
				uni.showLoading({
					title: _this.$t('loading_dots')
				})

				// 准备请求参数
				var para = {
					userId: userInfo.phone,
					isMobileLogin: true
				}

				// 调用后端API
				_this.$http.post('/awc/enterGameLobby', para, (res) => {
					uni.hideLoading()

					if (res.statusCode == 200 && res.data.ok) {
						var gameUrl = res.data.data.url
						var isNewMember = res.data.data.isNewMember

						// 如果是新会员，提示用户
						if (isNewMember) {
							uni.showToast({
								title: _this.$t('account_created_success'),
								icon: 'success',
								duration: 2000
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
									title: _this.$t('tips'),
									content: _this.$t('allow_popups'),
									confirmText: _this.$t('open_now'),
									cancelText: _this.$t('cancel'),
									success: (modalRes) => {
										if (modalRes.confirm) {
											// 用户确认后，跳转到webview页面
											uni.navigateTo({
												url: '/pages/webview/index?url=' + encodeURIComponent(gameUrl)
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
							url: '/pages/webview/index?url=' + encodeURIComponent(gameUrl)
						})
						// #endif

					} else {
						uni.showModal({
							title: _this.$t('error_title'),
							content: res.data.message || _this.$t('unable_enter_lobby'),
							showCancel: false,
							confirmText: _this.$t('ok')
						})
					}
				})
			},
			download(url) {
				//#ifdef APP-PLUS
				plus.runtime.openURL(url)
				//#endif

				//#ifdef H5
				// debugger
				window.open(url);
				//#endif
				setTimeout(() => {
					goto('./home')
				}, 2000)
			},
			logout() {
				// this.music.play_dede();
				// from tangjq--- 隐藏确认弹窗
				this.hideLogoutModal()

				uni.removeStorageSync('splash_last_shown_time')
				uni.removeStorageSync('Authorization');
				uni.redirectTo({
					url: '../login/login'
				})
			},
			showContactDialogs() {
				// this.music.play_dede();
				this.$refs.contactDialogs.open()
			},
			goto(path) {
				uni.navigateTo({
					url: path,
					// url: '/pages/ucenter/' + path,
					animationType: 'slide-in-right',
					animationDuration: 100
				})

			},
			showDialogs(title) {
				// this.music.play_dede();
				this.temp = {
					title: this.currentLanguage[title],
					content: this.$data[title]
				}
				this.$refs.popup.open()
			},
			hideDialogs() {
				this.$refs.popup.close()
			},
			parseContact() {
				this.contact = []
				if (this.configs && this.configs.contact_us) {
					let arr = this.configs.contact_us.split('\n')
					arr.forEach((ele, index) => {
						if (ele.indexOf('https') > -1) {
							this.contact.push({
								'str': ele,
								'type': 'site',
							})
						} else {
							this.contact.push({
								'str': ele,
								'type': 'str',
							})
						}
					})
				}

			},

			// from tangjq--- Change Password 弹窗方法
			showPasswordChangeModal() {
				// from tangjq--- 先关闭 Profile 弹窗
				this.hideProfileModal()
				// from tangjq--- 打开密码修改弹窗
				this.passwordChangeModalVisible = true
				// from tangjq--- 重置表单
				this.old_password = ''
				this.new_password = ''
				this.confirm_password = ''
				this.old_password_error = false
				this.new_password_error = false
				this.confirm_password_error = false
				this.password_error_message = ''
			},
			hidePasswordChangeModal() {
				this.passwordChangeModalVisible = false
			},
			// from tangjq--- Old Password 输入框失焦处理
			handleOldPasswordBlur() {
				this.old_password_focused = false
				// from tangjq--- 不在输入时显示错误提示，仅在提交时验证
				this.old_password_error = false
				this.password_error_message = ''
			},
			// from tangjq--- New Password 输入框失焦处理
			handleNewPasswordBlur() {
				this.new_password_focused = false
				const pwd = this.new_password
				// from tangjq--- 密码验证：长度 ≥ 8，包含大小写字母和数字
				const isValid =
					pwd &&
					pwd.length >= 8 &&
					/[a-z]/.test(pwd) &&
					/[A-Z]/.test(pwd) &&
					/\d/.test(pwd)

				if (!isValid) {
					this.new_password_error = true
					this.password_error_message = this.$t('password_must_contain') || 'Password must be at least 8 characters with uppercase, lowercase and number'
				} else {
					this.new_password_error = false
					this.password_error_message = ''
				}

				// from tangjq--- 如果确认密码已输入，检查是否匹配
				if (this.confirm_password && this.new_password !== this.confirm_password) {
					this.confirm_password_error = true
					this.password_error_message = this.$t('those_passwords') || 'Passwords do not match'
				}
			},
			// from tangjq--- Confirm Password 输入框失焦处理
			handleConfirmPasswordBlur() {
				this.confirm_password_focused = false
				if (this.new_password !== this.confirm_password) {
					this.confirm_password_error = true
					this.password_error_message = this.$t('those_passwords') || 'Passwords do not match'
				} else {
					this.confirm_password_error = false
					this.password_error_message = ''
				}
			},
			// from tangjq--- 提交密码修改
			submitPasswordChange() {
				var _this = this

				// from tangjq--- 清除之前的错误信息
				_this.old_password_error = false
				_this.new_password_error = false
				_this.confirm_password_error = false
				_this.password_error_message = ''

				// from tangjq--- 表单验证
				if (!this.old_password) {
					this.old_password_error = true
					this.password_error_message = this.$t('old_password_required')
					return
				}

				if (!this.new_password) {
					this.new_password_error = true
					this.password_error_message = this.$t('new_password_required')
					return
				}

				if (!this.confirm_password) {
					this.confirm_password_error = true
					this.password_error_message = this.$t('confirm_password_required')
					return
				}

				if (this.new_password !== this.confirm_password) {
					this.confirm_password_error = true
					this.password_error_message = this.$t('those_passwords') || 'Passwords do not match'
					return
				}

				if (this.new_password === this.old_password) {
					// from tangjq--- 先关闭弹窗，再显示错误提示，避免被遮挡
					this.hidePasswordChangeModal()
					this.$nextTick(() => {
						uni.showModal({
							title: _this.$t('tips'),
							content: _this.$t('The new password is the same as the old one') || 'The new password cannot be the same as the old password',
							showCancel: false,
							confirmText: _this.$t('ok')
						})
					})
					return
				}

				// from tangjq--- 提交到后端
				var para = {
					USER_PWD: this.new_password,
					OLD_PASSWORD: this.old_password
				}

				uni.showLoading({
					title: this.$t('saving')
				})

				_this.$http.post('/app_user/edit', para, (res) => {
					uni.hideLoading()
					var tips = res.data.message
					if (_this.$t(tips)) {
						tips = _this.$t(tips)
					}

					if (res.statusCode == 200) {
						// from tangjq--- 先关闭弹窗，再显示成功提示，避免被遮挡
						_this.hidePasswordChangeModal()
						_this.$nextTick(() => {
							uni.showModal({
								title: _this.$t('success_word'),
								content: tips || _this.$t('password_changed_success'),
								showCancel: false,
								confirmText: _this.$t('ok')
							})
						})
					} else {
						_this.password_error_message = tips || _this.$t('failed_change_password')
						_this.old_password_error = true
					}
				}, (err) => {
					uni.hideLoading()
					_this.password_error_message = _this.$t('network_error')
					_this.old_password_error = true
				})
			},
		},
		onLoad() {
		},
		onShow() {
		},
		mounted() {
			this.configs = Object.assign({}, this.$store.state.configs)
			console.log(this.configs);
		},
		created() {}
	}
</script>

<style lang="scss">
	/* from tangjq--- header占位元素样式 */
	.header-placeholder {
		height: 240px;
		width: 100%;
	}

	.ucenter-page {
		background: #2F5D62;
		min-height: 100vh;
	}

	/* 顶部栏 */
	.ucenter-header {
		background: #2F5D62;
		padding: 40px 20px 20px 20px;
		text-align: center;
	}

	.header-title {
		font-size: 22px;
		font-weight: 700;
		color: #fff;
	}

	/* 用户信息卡片 */
	.user-info-card {
		background: #fff;
		border-radius: 16px;
		margin: 0 16px 20px 16px;
		padding: 16px;
		display: flex;
		justify-content: space-between;
		align-items: center;
		box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
	}

	.user-info-left {
		display: flex;
		align-items: center;
		flex: 1;
	}

	.user-avatar {
		width: 60px;
		height: 60px;
		border-radius: 50%;
		background: #2F5D62;
		display: flex;
		align-items: center;
		justify-content: center;
		overflow: hidden;
	}

	.avatar-image {
		width: 100%;
		height: 100%;
	}

	.user-info-text {
		margin-left: 12px;
		flex: 1;
	}

	.user-id {
		font-size: 16px;
		font-weight: 700;
		color: #1e3a5f;
		display: block;
		margin-bottom: 6px;
	}

	.user-balance-row {
		display: flex;
		align-items: center;
		gap: 6px;
	}

	.balance-icon {
		width: 18px;
		height: 18px;
	}

	.balance-label,
	.cashout-label {
		font-size: 13px;
		color: #1e3a5f;
		font-weight: 600;
	}

	.balance-value,
	.cashout-value {
		font-size: 13px;
		color: #1e3a5f;
		font-weight: 700;
		margin-right: 12px;
	}

	.user-settings-icon {
		width: 40px;
		height: 40px;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.settings-icon-img {
		width: 28px;
		height: 28px;
		tint-color: #2F5D62;
	}

	/* 快捷图标区域 */
	.quick-icons-container {
		background: #2F5D62;
		padding: 0 16px 24px 16px;
		display: flex;
		justify-content: space-between;
		align-items: center;
	}

	.quick-icon-item {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 8px;
	}

	.icon-circle {
		width: 48px;
		height: 48px;
		border-radius: 50%;
		background: rgba(255, 255, 255, 0.15);
		border: 2px solid rgba(255, 255, 255, 0.3);
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.icon-img {
		width: 28px;
		height: 28px;
	}

	.icon-label {
		font-size: 12px;
		color: #4fb3bf;
		font-weight: 500;
	}

	/* 设置列表区域 */
	.settings-list-container {
		background: #fff;
		border-radius: 24px 24px 0 0;
		padding: 20px;
		min-height: 400px;
	}

	.setting-item {
		background: #fff;
		border: 2px solid #2F5D62;
		border-radius: 12px;
		padding: 8px;
		margin-bottom: 20px;
		text-align: center;
	}

	.setting-item-text {
		font-size: 16px;
		font-weight: 600;
		color: #2F5D62;
	}

	.version-item {
		border: none;
		background: transparent;
	}

	.version-item .setting-item-text {
		color: #999;
		font-size: 14px;
		font-weight: 400;
	}

	/* Logout 弹窗 */
	.logout-modal {
		position: fixed;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		background: rgba(0, 0, 0, 0.6);
		display: flex;
		align-items: center;
		justify-content: center;
		z-index: 1001;
		padding: 20px;
	}

	.logout-modal-content {
		background: #fff;
		border-radius: 16px;
		width: 100%;
		max-width: 400px;
		overflow: hidden;
	}

	.logout-modal-header {
		background: #2F5D62;
		padding: 10px;
		text-align: center;
		border-radius: 16px 16px 0 0;
	}

	.logout-modal-title {
		font-size: 16px;
		font-weight: 600;
		color: #fff;
	}

	.logout-modal-body {
		padding: 30px 20px;
		text-align: center;
	}

	.logout-question {
		font-size: 16px;
		color: #2F5D62;
		font-weight: 500;
	}

	.logout-modal-buttons {
		padding: 0 20px 20px 20px;
		display: flex;
		flex-direction: column;
		gap: 12px;
	}

	.logout-btn-confirm {
		background: #2F5D62;
		border-radius: 12px;
		padding: 8px;
		text-align: center;
	}

	.logout-btn-text-red {
		font-size: 16px;
		font-weight: 600;
		color: #ff4444;
	}

	.logout-btn-cancel {
		background: #2F5D62;
		border-radius: 12px;
		padding: 8px;
		text-align: center;
	}

	.logout-btn-text-white {
		font-size: 16px;
		font-weight: 600;
		color: #fff;
	}

	/* from tangjq--- 弹窗通用样式 */
	.modal-overlay {
		position: fixed;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		background: rgba(0, 0, 0, 0.6);
		display: flex;
		align-items: center;
		justify-content: center;
		z-index: 1001;
		padding: 20px;
	}

	.modal-content {
		background: #fff;
		border-radius: 16px;
		width: 100%;
		max-width: 500px;
		max-height: 90vh;
		overflow-y: auto;
	}

	.modal-header {
		background: #2F5D62;
		padding: 10px;
		display: flex;
		justify-content: space-between;
		align-items: center;
		border-radius: 16px 16px 0 0;
	}

	.modal-title {
		font-size: 16px;
		font-weight: 600;
		color: #fff;
		flex: 1;
		text-align: center;
	}

	.modal-close {
		font-size: 20px;
		color: #fff;
		font-weight: 300;
		line-height: 1;
		position: absolute;
		right: 30px;
	}

	.modal-body {
		padding: 20px;
	}

	/* Profile 弹窗样式 */
	.profile-avatar-section {
		display: flex;
		justify-content: center;
		margin-bottom: 24px;
	}

	.profile-avatar-circle {
		width: 100px;
		height: 100px;
		border-radius: 50%;
		// background: #2F5D62;
		overflow: hidden;
	}

	.profile-avatar-img {
		width: 100%;
		height: 100%;
	}

	.profile-info-row {
		margin-bottom: 10px;
	}

	.profile-info-label {
		font-size: 16px;
		font-weight: 700;
		color: #1e3a5f;
	}

	.profile-phone-row {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 15px;
	}

	.profile-phone-label {
		font-size: 15px;
		font-weight: 600;
		color: #1e3a5f;
	}

	.profile-edit-icon {
		width: 20px;
		height: 20px;
	}

	.profile-change-pwd-btn {
		background: #fff;
		border: 2px solid #2F5D62;
		border-radius: 12px;
		padding: 8px;
		text-align: center;
		margin-bottom: 12px;
	}

	.profile-change-pwd-text {
		font-size: 16px;
		font-weight: 400;
		color: #2F5D62;
	}

	.profile-save-btn {
		background: #2F5D62;
		border-radius: 12px;
		padding: 8px;
		text-align: center;
	}

	.profile-save-text {
		font-size: 15px;
		font-weight: 600;
		color: #fff;
	}

	/* Contact 弹窗样式 */
	.live-chat-btn {
		background: linear-gradient(135deg, #2F5D62, #5FB5BD);
		border-radius: 12px;
		padding: 16px 20px;
		display: flex;
		align-items: center;
		justify-content: space-between;
		margin-bottom: 20px;
		cursor: pointer;
	}

	.live-chat-btn:active {
		opacity: 0.9;
	}

	.live-chat-text {
		font-size: 15px;
		font-weight: 600;
		color: #fff;
	}

	.live-chat-arrow {
		font-size: 20px;
		color: #fff;
	}

	.contact-section-title {
		font-size: 22px;
		font-weight: 700;
		color: #1e3a5f;
		display: block;
		margin-bottom: 12px;
	}

	.contact-description {
		font-size: 14px;
		color: #2F5D62;
		line-height: 1.5;
		display: block;
		margin-bottom: 24px;
	}

	.contact-rich-text {
		font-size: 14px;
		color: #1e3a5f;
		line-height: 1.8;
		margin-bottom: 16px;
		word-break: break-all;
	}

	.contact-row-item {
		display: flex;
		flex-direction: row;
		align-items: center;
		margin-bottom: 16px;
		gap: 12px;
	}

	.contact-row-label {
		font-size: 14px;
		font-weight: 700;
		color: #1e3a5f;
		min-width: 75px;
		flex-shrink: 0;
	}

	.contact-input-wrapper {
		flex: 1;
		display: flex;
		flex-direction: row;
		align-items: center;
		background: #fff;
		border: 2px solid #5FB5BD;
		border-radius: 20px;
		overflow: hidden;
		height: 38px;
	}

	.contact-input-value {
		flex: 1;
		font-size: 13px;
		color: #1e3a5f;
		padding: 0 12px;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.contact-copy-button {
		background: #5FB5BD;
		padding: 8px 14px;
		display: flex;
		flex-direction: row;
		align-items: center;
		gap: 4px;
		flex-shrink: 0;
		height: 100%;
	}

	.copy-button-text {
		font-size: 13px;
		font-weight: 600;
		color: #fff;
	}

	.copy-button-icon {
		width: 14px;
		height: 14px;
	}

	/* About 弹窗样式 */
	.about-section {
		margin-bottom: 24px;
	}

	.about-section-title {
		font-size: 18px;
		font-weight: 700;
		color: #1e3a5f;
		display: block;
		margin-bottom: 12px;
	}

	.about-rule-item {
		display: flex;
		margin-bottom: 12px;
		align-items: flex-start;
	}

	.rule-number {
		font-size: 14px;
		color: #2F5D62;
		font-weight: 600;
		margin-right: 8px;
		flex-shrink: 0;
	}

	.rule-text {
		font-size: 14px;
		color: #5a7a8f;
		line-height: 1.5;
		flex: 1;
	}

	/* Language 弹窗样式 */
	.language-item {
		background: #fff;
		border-radius: 12px;
		padding: 10px;
		display: flex;
		justify-content: space-between;
		align-items: center;
	}

	.language-label {
		font-size: 16px;
		font-weight: 600;
		color: #1e3a5f;
	}

	.radio-circle {
		width: 24px;
		height: 24px;
		border-radius: 50%;
		border: 2px solid #ccc;
		display: flex;
		align-items: center;
		justify-content: center;
		transition: all 0.2s;
	}

	.radio-circle.radio-selected {
		border-color: #4fb3bf;
	}

	.radio-dot {
		width: 14px;
		height: 14px;
		border-radius: 50%;
		background: #4fb3bf;
	}

	.language-confirm-btn {
		background: #2F5D62;
		border-radius: 12px;
		padding: 8px;
		text-align: center;
		margin-top: 30px;
	}

	.language-confirm-text {
		font-size: 16px;
		font-weight: 600;
		color: #fff;
	}

	/* Customer Support 弹窗样式 */
	.support-main-title {
		font-size: 16px;
		font-weight: 700;
		color: #1e3a5f;
		display: block;
		margin-bottom: 8px;
	}

	.support-description {
		font-size: 13px;
		color: #5a7a8f;
		line-height: 1.5;
		display: block;
		margin-bottom: 20px;
	}

	.support-channel-section {
		margin-bottom: 20px;
	}

	.support-channel-title {
		font-size: 15px;
		font-weight: 700;
		color: #1e3a5f;
		display: block;
		margin-bottom: 10px;
	}

	.support-link-item {
		background: #f7f9fb;
		border-radius: 8px;
		// padding: 12px;
		margin-bottom: 8px;
	}

	.support-link-text {
		font-size: 14px;
		color: #2F5D62;
		// text-decoration: underline;
	}

	/* from tangjq--- Change Password 弹窗样式 */
	.password-change-modal {
		max-width: 450px;
	}

	.pwd-input-wrapper {
		position: relative;
		background: #e8eff1;
		border-radius: 12px;
		margin-bottom: 16px;
		transition: all 0.3s;
	}

	.pwd-input-wrapper.input-focused {
		background: #d9e7ea;
	}

	// .pwd-input-wrapper.input-error {
	// 	border: 2px solid #e54d42;
	// }

	.pwd-input {
		width: 100%;
		height: 50px;
		font-size: 12px;
		color: #103C42;
		font-style: italic;
		background: transparent;
		border: 0;
		text-align: center;
		outline: none;
	}

	.pwd-input::placeholder {
		color: #7a9aaa;
		font-style: italic;
	}

	.eye-icon {
		position: absolute;
		right: 15px;
		top: 50%;
		transform: translateY(-50%);
		font-size: 20px;
		color: #5a7a8f;
		cursor: pointer;
	}

	.pwd-error-message {
		display: block;
		font-size: 13px;
		color: #e54d42;
		margin-top: -10px;
		margin-bottom: 10px;
		padding-left: 5px;
	}

	.pwd-cancel-btn {
		background: #fff;
		border: 2px solid #2F5D62;
		border-radius: 12px;
		padding: 8px;
		text-align: center;
		margin-bottom: 12px;
		margin-top: 20px;
	}

	.pwd-cancel-text {
		font-size: 16px;
		font-weight: 600;
		color: #2F5D62;
	}

	.pwd-save-btn {
		background: #2F5D62;
		border-radius: 12px;
		padding: 8px;
		text-align: center;
	}

	.pwd-save-text {
		font-size: 16px;
		font-weight: 600;
		color: #fff;
	}
</style>