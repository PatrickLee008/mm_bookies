<template>
	<scroll-view scroll-y class="dialog-wrapper" v-if="!hidden">
		<view style="background: none;">
			<view class="single-mask" @click="set_dialog_hide(true)"></view>
			<view class="text-bold flex-column" style="bottom: 0;" :style="{'position':mixed?'sticky':'fixed'}">
				<view class="flex-column padding-xs single-bottom dialig-bottom">
					<view class=" mybg-primary row-line"></view>
					<view class="text-light myfont-13px padding-tb-xs">Please login to get more features !</view>
					<button class="button mybg-primary margin-tb-sm" @click="redirect_to('login')">SIGN IN</button>
					<button class="button mybg-active margin-tb-sm" @click="redirect_to()">REGISTER</button>
				</view>
			</view>
		</view>
		</view>
	</scroll-view>
</template>

<script>
	export default {
		props: {
			hidden: true,
			title: String,
			match: {
				type: Object,
				default: function() {
					return {}
				}
			},
			width: {
				type: String,
				default: '880px'
			},
			height: {
				type: String,
				default: '500px'
			},
			showConfrim: {
				type: Boolean,
				default: true
			},
			showCancel: {
				type: Boolean,
				default: true
			},
			confirmText: {
				type: String,
				default: '确定'
			},
			cancelText: {
				type: String,
				default: '取消'
			},
		},
		computed: {
			mask_style() {

			}
		},
		data() {
			return {
				mixed: false,
				willclose: false,
			}
		},
		methods: {
			set_dialog_hide(e) {
				this.$emit('update:hidden', e)
			},
			show() {
				this.$emit('update:hidden', false)
			},
			redirect_to(navi) {
				let url = navi === 'login' ? '../login/login' : '../login/register'
				console.log(url)
				uni.redirectTo({
					url: url,
				})
			},
		}
	}
</script>

<style lang="scss">
	.dialog-wrapper {
		z-index: 10000;
		// background-color: white;
		position: fixed;
		left: 0;
		bottom: 0;
		// height: calc(100vh - 55px);
		height: 100vh;
		width: 100vw;
		transform: none;
		transition: transform 225ms cubic-bezier(0, 0, 0.2, 1) 0ms;
	}

	.button {
		width: 80%;
		padding: 5upx 6upx;
		font-size: .6rem;
	}

	.box-shadow {
		box-shadow: rgba(60, 64, 67, 0.3) 0px 1px 2px 0px, rgba(60, 64, 67, 0.15) 0px 1px 3px 1px;
	}

	.dialig-bottom {
		display: flex;
		flex-direction: column;
		background-color: white;
	}

	.row-line {
		height: 2vw;
		width: 12vw;
		border-radius: 100px;
	}

	.single-bottom {
		border-top-right-radius: 5vw;
		border-top-left-radius: 5vw;
	}

	.single-mask {
		background: none;
		height: 100vh;
		// filter: ;
		opacity: .5;
		background-color: black;
	}
</style>