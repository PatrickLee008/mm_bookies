<template>
	<view class="invite-page">
		<zw-header @headerHeightChange="onHeaderHeightChange"></zw-header>
		<view class="invite-header-placeholder" :style="{ height: headerHeight + 'px', transition: 'height 0.3s ease' }"></view>
		<scroll-view scroll-y class="padding-bottom invite-scroll" @scroll="handleHeaderScroll" @scrolltoupper="handleHeaderTop">
			<view class="title-bar" style="height: auto;">
				<view class="flex-row justify-between" style="">
					<!-- <text class="cuIcon-back text-bold mycolor-primary margin-right-sm" @click="back_to()"></text> -->
					<view class="flex-row align-center" style="">
						<theme-icon name="referral" size="28px"
							color="var(--theme-icon-primary, var(--theme-primary))"></theme-icon>
						<text class="title-text" style="">{{ language.invite_friend }}</text>
					</view>
				</view>
			</view>

			<!-- 加载中 -->
			<view v-if="loading" class="flex-column align-center" style="padding: 60px 0;">
				<view class="cu-load loading"></view>
			</view>

			<!-- 加载完成 -->
			<view v-else>
				<view class="qr-rec">
					<view style="position: relative; display: inline-block;">
						<canvas id="qrcode" canvas-id="qrcode"
							:style="{ width: `${size}px`, height: `${size}px` }"></canvas>
						<view v-if="!canInvite" class="qr-overlay">
							<text class="qr-overlay-text">{{ $t('Limit Reached') }}</text>
						</view>
					</view>
				</view>

				<view class="qr-rec" style="padding: 10px 25px;">
					<text class="flex-column mycolor-primary myfont-14px text-bold">{{ language.share_invite }}</text>
					<view class="flex-row justify-around margin-top-sm">
						<view class="flex-column1 align-center" :class="{ grayscale: !canInvite }" @click="shareSystem()">
							<view class="mybg-primary flex-column radius-50" style="width: 38px;height: 38px;">
								<theme-icon name="share" size="24px"
									color="var(--theme-icon-on-primary, #fff)"></theme-icon>
							</view>
							<text class="myfont-12px">{{ language.share }}</text>
						</view>
						<view class="flex-column1 align-center" :class="{ grayscale: !canInvite }" @click="shareFacebook()">
							<image mode="widthFix" class="width-39px" src="/static/icon/share/facebook.svg" />
							<text class="myfont-12px">{{ language.facebook }}</text>
						</view>
						<view class="flex-column1 align-center" :class="{ grayscale: !canInvite }" @click="shareTelegram()">
							<image mode="widthFix" class="width-39px" src="/static/icon/share/telegram.svg" />
							<text class="myfont-12px">{{ language.telegram }}</text>
						</view>
						<view class="flex-column1 align-center" :class="{ grayscale: !canInvite }" @click="shareLine()">
							<image mode="widthFix" class="width-39px" src="/static/icon/share/line.svg" />
							<text class="myfont-12px">{{ language.line }}</text>
						</view>
					</view>
				</view>

				<view class="flex-column padding-lr">
					<text class="myfont-12px mycolor-primary text-bold">{{ language.copy_link }}</text>
					<text class="myfont-10px" style="color: #999; margin-top: 5px;">
						{{ $t('Invites') }}: {{ downlineCount }}/{{ maxInvites }}
					</text>
				</view>
				<view class="copy-rec flex-row1 justify-between mycolor-dgray" :style="{ opacity: canInvite ? 1 : 0.5 }">
					<text class="width-90 text-cut" v-if="canInvite">{{ share_url }}</text>
					<text class="width-100 text-cut" v-else>{{ $t("You've reached the maximum invites") }}</text>
					<theme-icon name="copy" size="20px"
						color="var(--theme-icon-primary, var(--theme-primary))" @click="copy"
						v-if="canInvite"></theme-icon>
				</view>
			</view>

			<view style="height: 30px; width: 100%;"></view>
		</scroll-view>
	</view>
</template>

<script>
	import config from '@/utils/config.js'
	import uQRCode from '@/uni_modules/Sansnn-uQRCode/js_sdk/u-qrcode';
	import siteinfo from '@/siteinfo.js';
	import headerCollapse from '@/mixins/headerCollapse.js'

	export default {
		mixins: [headerCollapse],
		data() {
			return {
				language: config.language,
				r_code: '',
				size: 165,
				share_url: '',
				loading: true,
				canInvite: true,
				downlineCount: 0,
				maxInvites: 10
			}
		},
		onLoad(option) {
			this.r_code = (option && option.r_code) || ''
			if (!this.r_code) {
				const uinfo = this.$store.state.userInfo || {}
				this.r_code = uinfo.r_code || ''
			}
			this.checkInviteLimit()
		},
		methods: {
			back_to() {
				uni.navigateTo({ url: './index' })
			},
			checkInviteLimit() {
				let _this = this
				_this.loading = true
				_this.$http.get('/invitation_v2/downline-count', {}, (res) => {
					let response = res.data
					if (response && response.code === 200) {
						_this.downlineCount = response.data.downline_count
						_this.maxInvites = response.data.max_invites
						_this.canInvite = response.data.can_invite
					}
					_this.generate_qr_code()
					_this.loading = false
				}, () => {
					_this.generate_qr_code()
					_this.loading = false
				})
			},
			getSiteOrigin() {
				// #ifdef H5
				if (typeof window !== 'undefined' && window.location && window.location.origin) {
					return window.location.origin
				}
				// #endif
				try {
					return siteinfo.apiUrl.replace('/api', '')
				} catch (e) {
					return 'https://m.mmbookies.com'
				}
			},
			openUrl(url) {
				// #ifdef H5
				if (typeof window !== 'undefined') {
					window.open(url);
					return;
				}
				// #endif
				// #ifdef APP-PLUS
				plus.runtime.openURL(url);
				// #endif
			},
			generate_qr_code() {
				let _this = this
				let origin = _this.getSiteOrigin();
				let url = `${origin}/#/pages/login/register?iv=${_this.r_code}`
				_this.share_url = url
				setTimeout(() => {
					const ctx = uni.createCanvasContext('qrcode');
					const uqrcode = new uQRCode({ text: url, size: _this.size }, ctx);
					uqrcode.make();
					uqrcode.draw();
				}, 100)
			},
			limitToast() {
				uni.showToast({
					title: this.$t("You've reached the maximum invites"),
					icon: 'none',
					duration: 3000
				});
			},
			shareSystem() {
				if (!this.canInvite) return this.limitToast();
				// #ifdef H5
				if (typeof navigator !== 'undefined' && navigator.share) {
					navigator.share({
						title: 'MM Bookies',
						text: 'Click the link to get started!',
						url: this.share_url
					});
					return;
				}
				// #endif
				uni.setClipboardData({
					data: this.share_url,
					success: () => uni.showToast({ title: this.$t('copied_to_clipboard'), icon: 'success' })
				});
			},
			shareFacebook() {
				if (!this.canInvite) return this.limitToast();
				this.openUrl(`https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(this.share_url)}`);
			},
			shareTelegram() {
				if (!this.canInvite) return this.limitToast();
				this.openUrl(`https://t.me/share/url?url=${encodeURIComponent(this.share_url)}&text=MM Bookies`);
			},
			shareLine() {
				if (!this.canInvite) return this.limitToast();
				this.openUrl(`https://social-plugins.line.me/lineit/share?url=${encodeURIComponent(this.share_url)}`);
			},
			copy() {
				if (!this.canInvite) return this.limitToast();
				uni.setClipboardData({
					data: this.share_url,
					success: () => uni.showToast({ title: this.$t('copied_to_clipboard'), icon: 'success' })
				});
			}
		}
	}
</script>

<style lang="scss">
	.invite-page {
		height: var(--app-viewport-height, 100vh);
		display: flex;
		flex-direction: column;
		overflow: hidden;
	}

	.invite-header-placeholder {
		width: 100%;
		height: 255px;
		flex-shrink: 0;
		transition: height 0.3s ease;
	}

	.invite-scroll {
		flex: 1;
		height: 0;
		border-radius: 20px 20px 0 0;
		background: #ffffff;
		position: relative;
		z-index: 1;
	}

	.qr-rec {
		width: 95%;
		margin-left: 2.5%;
		display: flex;
		flex-direction: column;
		padding: 25px;
		margin-top: 10px;
		color: rgba(0, 0, 0, 0.87);
		border-radius: 8px;
		overflow: hidden;
		text-align: center;
		align-items: center;
		margin-bottom: 10px;
		background-color: #ffffff;
		box-shadow: 0px 2px 1px -1px rgba(0, 0, 0, 0.2), 0px 1px 1px 0px rgba(0, 0, 0, 0.14), 0px 1px 3px 0px rgba(0, 0, 0, 0.12);
	}

	.copy-rec {
		width: 95%;
		margin-left: 2.5%;
		border-radius: 8px;
		overflow: hidden;
		background-color: #eef5f6;
		text-align: center;
		align-items: center;
		box-shadow: rgba(0, 0, 0, 0.15) 0px 2px 3px 0px;
		padding: 15px 15px;
		margin-top: 6px;
	}

	.qr-overlay {
		position: absolute;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
		background: rgba(0, 0, 0, 0.6);
		display: flex;
		align-items: center;
		justify-content: center;
		border-radius: 4px;
	}

	.qr-overlay-text {
		color: white;
		font-size: 14px;
		font-weight: bold;
	}

	.grayscale {
		filter: grayscale(100%);
		opacity: 0.5;
	}
</style>
