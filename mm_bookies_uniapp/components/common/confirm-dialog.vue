<template>
	<view class="confirm-dialog-overlay" v-if="visible" @click="handleCancel">
		<view class="confirm-dialog-content" @click.stop="">
			<!-- 标题栏 -->
			<view class="confirm-dialog-header">
				<text class="confirm-dialog-title">{{ title }}</text>
			</view>
			<!-- 内容区域 -->
			<view class="confirm-dialog-body">
				<text class="confirm-dialog-message">{{ message }}</text>
			</view>
			<!-- 按钮区域 -->
			<view class="confirm-dialog-buttons">
				<view class="confirm-dialog-btn-cancel" @click="handleCancel">
					<text class="btn-cancel-text">{{ cancelText }}</text>
				</view>
				<view class="confirm-dialog-btn-confirm" @click="handleConfirm">
					<text class="btn-confirm-text">{{ confirmText }}</text>
				</view>
			</view>
		</view>
	</view>
</template>

<script>
	export default {
		name: 'ConfirmDialog',
		props: {
			visible: {
				type: Boolean,
				default: false
			},
			title: {
				type: String,
				default: ''
			},
			message: {
				type: String,
				default: ''
			},
			confirmText: {
				type: String,
				default: 'Confirm'
			},
			cancelText: {
				type: String,
				default: 'Cancel'
			}
		},
		methods: {
			handleConfirm() {
				this.$emit('confirm')
			},
			handleCancel() {
				this.$emit('cancel')
			}
		}
	}
</script>

<style lang="scss" scoped>
	.confirm-dialog-overlay {
		position: fixed;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		background: rgba(0, 0, 0, 0.6);
		display: flex;
		align-items: center;
		justify-content: center;
		z-index: 10001;
		padding: 40px;
	}

	.confirm-dialog-content {
		background: #fff;
		border-radius: 16px;
		width: 100%;
		max-width: 400px;
		overflow: hidden;
	}

	.confirm-dialog-header {
		background: #2F5D62;
		padding: 12px 16px;
		text-align: center;
	}

	.confirm-dialog-title {
		font-size: 16px;
		font-weight: 600;
		color: #fff;
	}

	.confirm-dialog-body {
		padding: 24px 20px;
		text-align: center;
	}

	.confirm-dialog-message {
		font-size: 15px;
		color: #2F5D62;
		font-weight: 500;
		line-height: 1.6;
		word-break: normal;
		white-space: normal;
	}

	.confirm-dialog-buttons {
		padding: 0 20px 20px 20px;
		display: flex;
		flex-direction: row;
		gap: 12px;
	}

	.confirm-dialog-btn-cancel {
		flex: 1;
		background: #fff;
		border: 2px solid #2F5D62;
		border-radius: 12px;
		padding: 10px;
		text-align: center;
	}

	.btn-cancel-text {
		font-size: 15px;
		font-weight: 600;
		color: #2F5D62;
	}

	.confirm-dialog-btn-confirm {
		flex: 1;
		background: #E02B2B;
		border-radius: 12px;
		padding: 10px;
		text-align: center;
	}

	.btn-confirm-text {
		font-size: 15px;
		font-weight: 600;
		color: #fff;
	}
</style>
