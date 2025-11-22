<template>
	<view class="bg-white full-page">
		<zw-header></zw-header>

		<view class="title-bar" style="height: auto;">
			<view class="flex-row justify-between" style="">
				<text class="cuIcon-back text-bold mycolor-primary margin-right-sm" @click="back_to()"></text>
				<view class="flex-row align-center" style="">
					<image src="/static/icon/ucenter/invite.png" class="lblue2blue" style="height: 28px;"
						mode="heightFix"></image>
					<text class="title-text" style="">{{language.invite_friend}}</text>
				</view>
			</view>
		</view>
		<view class="qr-rec">
			<canvas id="qrcode" canvas-id="qrcode" :style="{ width: `${size}px`, height: `${size}px` }"></canvas>
		</view>
		<view class="qr-rec" style="padding: 10px 25px;">
			<text class="flex-column mycolor-primary myfont-14px text-bold">{{language.share_invite}}</text>
			<view class="flex-row justify-around margin-top-sm">
				<view class="flex-column1 align-center" @click="shareSystem()">
					<view class="mybg-primary flex-column radius-50" style="width: 38px;height: 38px;">
						<image mode="widthFix" class="width-38upx " src="/static/icon/share/share.svg" />
					</view>
					<text class="myfont-12px">{{language.share}}</text>
				</view>
				<view class="flex-column1 align-center" @click="shareFacebook()">
					<image mode="widthFix" class="width-39px " src="/static/icon/share/facebook.svg" />
					<text class="myfont-12px">{{language.facebook}}</text>
				</view>
				<view class="flex-column1 align-center" @click="shareTelegram()">
					<image mode="widthFix" class="width-39px " src="/static/icon/share/telegram.svg" />
					<text class="myfont-12px">{{language.telegram}}</text>
				</view>
				<view class="flex-column1 align-center" @click="shareLine()">
					<image mode="widthFix" class="width-39px " src="/static/icon/share/line.svg" />
					<text class="myfont-12px">{{language.line}}</text>
				</view>
			</view>
		</view>
		<view class="flex-column">
			<text class="myfont-12px mycolor-primary text-bold">{{language.copy_link}}</text>
			<text class="myfont-10px" style="color: #999; margin-top: 5px;">Invites: {{downlineCount}}/{{maxInvites}}</text>
		</view>
		<view class="copy-rec flex-row1 justify-between mycolor-dgray" :style="{ opacity: canInvite ? 1 : 0.5 }">
			<text class="width-90 text-cut">{{share_url}}</text>
			<view class="cuIcon-copy myfont-18px" :style="{ color: canInvite ? '#007aff' : '#ccc' }" @click="copy"></view>
		</view>
		<!-- <view class="flex-column justify-center" style="position: fixed;top: 45vh;">
			<view class="flex-row align-center justify-center" style="">
				<view class="myfont-20px mycolor-primary">{{language.is_coming_soon}}</view>
			</view>
		</view> -->

	</view>
</template>

<script>
	import language from '@/utils/language.js'
	import config from '@/utils/config.js'
	import uQRCode from '@/uni_modules/Sansnn-uQRCode/js_sdk/u-qrcode';

	export default {
		data() {
			return {
				language: config.language,
				userInfo: null,
				size: 165,
				share_url: '',
				canInvite: true,
				downlineCount: 0,
				maxInvites: 10
			}
		},
		onLoad() {
			this.userInfo = Object.assign({}, this.$store.state.userInfo)
			this.checkInviteLimit()
		},
		methods: {
			back_to() {
				uni.navigateBack({
					delta: 1,
				})
			},
			checkInviteLimit() {
				// 调用API检查邀请限制
				this.$http.get('/activity/downline-count', {}, (res) => {
					if (res.data.code === 200) {
						this.downlineCount = res.data.downline_count
						this.maxInvites = res.data.max_invites
						this.canInvite = res.data.can_invite

						// 如果可以邀请，生成二维码
						if (this.canInvite) {
							this.generate_qr_code()
						}
					} else {
						console.error('Failed to check invite limit:', res.message)
						// 默认允许邀请，避免阻塞用户
						this.generate_qr_code()
					}
				})
			},
			generate_qr_code() {
				// let url = `${this.$http.baseUrl}/#/pages/login/register?iv=${this.userInfo.id}`
				let url = `${window.location.origin}/#/pages/login/register?iv=${this.userInfo.id}`
				let _this = this
				_this.share_url = url
				const ctx = uni.createCanvasContext('qrcode');
				const uqrcode = new uQRCode({
					text: url,
					size: _this.size,
				}, ctx);
				uqrcode.make();
				uqrcode.draw();
			},
			shareSystem() {
				if (!this.canInvite) {
					uni.showToast({
						title: "You've reached the maximum invites",
						icon: 'none',
						duration: 3000
					});
					return;
				}

				if (navigator.share) {
					navigator.share({
						title: 'Join me on ONE X2!',
						text: 'Click the link to get started!',
						url: this.share_url
					});
				} else {
					uni.showToast({
						title: 'System share not supported',
						icon: 'none'
					});
				}
			},
			shareFacebook() {
				if (!this.canInvite) {
					uni.showToast({
						title: "You've reached the maximum invites",
						icon: 'none',
						duration: 3000
					});
					return;
				}
				window.open(`https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(this.share_url)}`);
			},
			shareTelegram() {
				if (!this.canInvite) {
					uni.showToast({
						title: "You've reached the maximum invites",
						icon: 'none',
						duration: 3000
					});
					return;
				}
				window.open(`https://t.me/share/url?url=${encodeURIComponent(this.share_url)}&text=Join me on ONE X2!`);
			},
			shareLine() {
				if (!this.canInvite) {
					uni.showToast({
						title: "You've reached the maximum invites",
						icon: 'none',
						duration: 3000
					});
					return;
				}
				window.open(`https://social-plugins.line.me/lineit/share?url=${encodeURIComponent(this.share_url)}`);
			},
			copy() {
				// 检查是否可以邀请
				if (!this.canInvite) {
					uni.showToast({
						title: "You've reached the maximum invites",
						icon: 'none',
						duration: 3000
					});
					return;
				}

				uni.setClipboardData({
					data: this.share_url,
					success: function() {
						uni.showToast({
							title: 'Copied to clipboard',
							icon: 'success'
						});
					},
					fail: function() {
						// uni.showToast({
						//   title: '复制失败',
						//   icon: 'none'
						// });
					}
				});
			}

		}
	}
</script>

<style lang="scss">
	.qr-rec {
		width: 95%;
		margin-left: 2.5%;
		display: flex;
		flex-direction: column;
		padding: 25px;
		margin-top: 10px;
		color: rgba(0, 0, 0, 0.87);
		transition: box-shadow 300ms cubic-bezier(0.4, 0, 0.2, 1) 0ms;
		border-radius: 4px;
		box-shadow: var(--Paper-shadow);
		background-image: var(--Paper-overlay);
		overflow: hidden;

		text-align: center;
		-webkit-box-align: center;
		align-items: center;
		margin-bottom: 10px;
		background-color: rgb(255, 255, 255);
		box-shadow: 0px 2px 1px -1px rgba(0, 0, 0, 0.2), 0px 1px 1px 0px rgba(0, 0, 0, 0.14), 0px 1px 3px 0px rgba(0, 0, 0, 0.12);
	}

	.copy-rec {
		width: 95%;
		margin-left: 2.5%;
		transition: box-shadow 300ms cubic-bezier(0.4, 0, 0.2, 1) 0ms;
		border-radius: 4px;
		box-shadow: 0px 2px 1px -1px rgba(0, 0, 0, 0.2), 0px 1px 1px 0px rgba(0, 0, 0, 0.14), 0px 1px 3px 0px rgba(0, 0, 0, 0.12);
		overflow: hidden;
		background-color: rgb(237, 236, 241);
		text-align: center;
		-webkit-box-align: center;
		align-items: center;
		box-shadow: rgba(0, 0, 0, 0.15) 0px 2px 3px 0px;
		padding: 15px 15px;
	}
</style>