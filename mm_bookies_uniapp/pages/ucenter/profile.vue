<template>
	<view class="profile-page full-page">
		<!-- 顶部栏 -->
		<view class="profile-header">
			<text class="header-back-icon" @click="goBack">←</text>
			<text class="header-title">Edit Profile</text>
			<text class="header-placeholder"></text>
		</view>

		<scroll-view scroll-y style="height: calc(100vh - 88px);">
			<view class="profile-content">
				<!-- 用户头像 -->
				<view class="avatar-section">
					<view class="avatar-circle">
						<image class="avatar-img" src="/static/icon/ucenter/default-avatar.png" mode="aspectFill"></image>
					</view>
				</view>

				<!-- My ID -->
				<view class="info-row">
					<text class="info-label">My ID : {{ userInfo.id || '00001' }}</text>
				</view>

				<!-- Phone No -->
				<view class="phone-row">
					<text class="phone-label">Phone No: {{ userInfo.phone || '0987654321' }}</text>
					<image class="edit-icon" src="/static/icon/edit.png" mode="aspectFit" @click="editPhone"></image>
				</view>

				<!-- Change Password 按钮 -->
				<view class="change-pwd-btn" @click="showChangePasswordModal">
					<text class="change-pwd-text">Change Password</text>
				</view>

				<!-- Save 按钮 -->
				<view class="save-btn">
					<text class="save-btn-text">Save</text>
				</view>
			</view>
		</scroll-view>

		<!-- Change Password 弹窗 -->
		<view class="change-pwd-modal" v-if="showPwdModal" @click="hidePwdModal">
			<view class="pwd-modal-content" @click.stop="">
				<!-- 弹窗标题栏 -->
				<view class="pwd-modal-header">
					<text class="pwd-modal-title">Change Password</text>
				</view>

				<!-- 输入表单 -->
				<view class="pwd-form">
					<input
						class="pwd-input"
						type="password"
						placeholder="Please enter your old password"
						placeholder-class="pwd-placeholder"
						v-model="oldPassword" />
					<input
						class="pwd-input"
						type="password"
						placeholder="Please enter your new password"
						placeholder-class="pwd-placeholder"
						v-model="newPassword" />
					<input
						class="pwd-input"
						type="password"
						placeholder="Please enter your new password"
						placeholder-class="pwd-placeholder"
						v-model="confirmPassword" />
				</view>

				<!-- 按钮组 -->
				<view class="pwd-buttons">
					<view class="pwd-cancel-btn" @click="hidePwdModal">
						<text class="pwd-cancel-text">Cancel</text>
					</view>
					<view class="pwd-save-btn" @click="savePassword">
						<text class="pwd-save-text">Save</text>
					</view>
				</view>
			</view>
		</view>
	</view>
</template>

<script>
	export default {
		name: "Profile",
		data() {
			return {
				userInfo: {},
				showPwdModal: false,
				oldPassword: '',
				newPassword: '',
				confirmPassword: ''
			}
		},
		onLoad() {
			this.userInfo = Object.assign({}, this.$store.state.userInfo)
		},
		methods: {
			goBack() {
				uni.navigateBack()
			},
			editPhone() {
				uni.showToast({
					icon: 'none',
					title: 'Phone editing feature coming soon'
				})
			},
			// from tangjq--- 显示修改密码弹窗
			showChangePasswordModal() {
				this.showPwdModal = true
			},
			// from tangjq--- 隐藏修改密码弹窗
			hidePwdModal() {
				this.showPwdModal = false
				this.oldPassword = ''
				this.newPassword = ''
				this.confirmPassword = ''
			},
			// from tangjq--- 保存密码
			savePassword() {
				let _this = this

				if (!_this.oldPassword || !_this.newPassword || !_this.confirmPassword) {
					uni.showToast({
						icon: 'none',
						title: 'Please fill in all fields'
					})
					return
				}

				if (_this.newPassword !== _this.confirmPassword) {
					uni.showToast({
						icon: 'none',
						title: 'New passwords do not match'
					})
					return
				}

				uni.showLoading({
					title: 'Saving...',
					mask: true
				})

				_this.$http.post('/user/changePassword', {
					old_password: _this.oldPassword,
					new_password: _this.newPassword
				}, (res) => {
					uni.hideLoading()
					if (res.statusCode === 200 && res.data.code === 200) {
						uni.showToast({
							icon: 'success',
							title: 'Password changed successfully',
							duration: 2000
						})
						_this.hidePwdModal()
					} else {
						uni.showToast({
							icon: 'none',
							title: res.data.message || 'Failed to change password',
							duration: 2000
						})
					}
				}, (err) => {
					uni.hideLoading()
					uni.showToast({
						icon: 'none',
						title: 'Network error',
						duration: 2000
					})
				})
			}
		}
	}
</script>

<style lang="scss" scoped>
	.profile-page {
		background: #f5f5f5;
		min-height: 100vh;
	}

	/* 顶部栏 */
	.profile-header {
		background: #3d6877;
		padding: 40px 20px 20px 20px;
		display: flex;
		justify-content: space-between;
		align-items: center;
	}

	.header-back-icon, .header-placeholder {
		width: 40px;
		font-size: 24px;
		color: #fff;
		font-weight: 300;
	}

	.header-title {
		font-size: 20px;
		font-weight: 700;
		color: #fff;
		flex: 1;
		text-align: center;
	}

	/* 内容区域 */
	.profile-content {
		padding: 30px 20px;
	}

	.avatar-section {
		display: flex;
		justify-content: center;
		margin-bottom: 30px;
	}

	.avatar-circle {
		width: 120px;
		height: 120px;
		border-radius: 50%;
		background: #3d6877;
		display: flex;
		align-items: center;
		justify-content: center;
		overflow: hidden;
	}

	.avatar-img {
		width: 100%;
		height: 100%;
	}

	.info-row {
		margin-bottom: 20px;
	}

	.info-label {
		font-size: 18px;
		font-weight: 700;
		color: #1e3a5f;
	}

	.phone-row {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 30px;
	}

	.phone-label {
		font-size: 16px;
		font-weight: 600;
		color: #1e3a5f;
	}

	.edit-icon {
		width: 24px;
		height: 24px;
		tint-color: #3d6877;
	}

	.change-pwd-btn {
		background: #fff;
		border: 2px solid #3d6877;
		border-radius: 12px;
		padding: 14px;
		text-align: center;
		margin-bottom: 16px;
	}

	.change-pwd-text {
		font-size: 16px;
		font-weight: 600;
		color: #3d6877;
	}

	.save-btn {
		background: #3d6877;
		border-radius: 12px;
		padding: 14px;
		text-align: center;
	}

	.save-btn-text {
		font-size: 16px;
		font-weight: 600;
		color: #fff;
	}

	/* Change Password 弹窗 */
	.change-pwd-modal {
		position: fixed;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		background: rgba(0, 0, 0, 0.6);
		display: flex;
		align-items: center;
		justify-content: center;
		z-index: 999;
		padding: 20px;
	}

	.pwd-modal-content {
		background: #fff;
		border-radius: 16px;
		width: 100%;
		max-width: 400px;
		overflow: hidden;
	}

	.pwd-modal-header {
		background: #3d6877;
		padding: 20px;
		text-align: center;
	}

	.pwd-modal-title {
		font-size: 20px;
		font-weight: 700;
		color: #fff;
	}

	.pwd-form {
		padding: 20px;
	}

	.pwd-input {
		background: #d9e4e8;
		border-radius: 12px;
		padding: 16px;
		margin-bottom: 12px;
		font-size: 14px;
		color: #1e3a5f;
	}

	.pwd-placeholder {
		color: #5a7a8f;
		font-style: italic;
	}

	.pwd-buttons {
		padding: 0 20px 20px 20px;
		display: flex;
		flex-direction: column;
		gap: 12px;
	}

	.pwd-cancel-btn {
		background: #fff;
		border: 2px solid #3d6877;
		border-radius: 12px;
		padding: 14px;
		text-align: center;
	}

	.pwd-cancel-text {
		font-size: 16px;
		font-weight: 600;
		color: #3d6877;
	}

	.pwd-save-btn {
		background: #3d6877;
		border-radius: 12px;
		padding: 14px;
		text-align: center;
	}

	.pwd-save-text {
		font-size: 16px;
		font-weight: 600;
		color: #fff;
	}
</style>
