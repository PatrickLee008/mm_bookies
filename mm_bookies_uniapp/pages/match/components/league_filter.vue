<template>
	<scroll-view scroll-y class="dialog-wrapper bg-white" v-show="!hidden">
		<view style="" class="">
			<view class="flex-row box-shadow padding mybg-primary" @click="set_dialog_hide(true)"
				style="position: sticky;top: 0;">
				<view class="margin-left width-100 text-bold">{{'LEAGUE FILTER'}}</view>
				<view class="cuIcon-close"></view>
			</view>
			<view class="myfont-12px text-left">
				<checkbox-group class="block" @change="CheckboxChange">
					<view class="league-row">
						<checkbox class="blue" style="scale: .65;" :class="all_status?'checked':''"
							:checked="all_status?true:false" value="All"></checkbox>

						<text class="margin-left-sm" style="">
							All
						</text>
					</view>
					<view class="league-row" v-for="(league,index) in league_list" :key="index" v-show='league[`include_${tomorrow?"tomorrow":"today"}`]'>
						<checkbox class="blue" style="scale: .65;" :class="league.checked?'checked':''"
							:checked="league.checked?true:false" :value="String(index)"></checkbox>
						<text class="margin-left-sm" style="">
							{{league.name}}
						</text>
					</view>

				</checkbox-group>
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
			league_list: {
				type: Array,
				default: function() {
					return []
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
			tomorrow: {
				type: Boolean,
				default: false
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
				all_status: true,
			}
		},
		methods: {
			set_dialog_hide(e) {
				this.$emit('update:hidden', e)
			},
			show_dialog(...args) {

			},
			CheckboxChange(evt) {
				let check_list = evt.detail.value
				let origin_all = this.all_status
				this.all_status = check_list.includes('All')
				let list = this.$toolbox.deep_clone(this.league_list)
				if (origin_all !== this.all_status) {
					list.forEach((league, index) => {
						league.checked = this.all_status
					})
				} else {
					list.forEach((league, index) => {
						league.checked = check_list.includes(String(index))
					})
				}
				list.forEach(ele=>{
					ele.match_list.forEach(match=>{
						match.checked = true
					})
				})
				this.$emit('update:league_list', list)
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
	}

	.box-shadow {
		box-shadow: rgba(60, 64, 67, 0.3) 0px 1px 2px 0px, rgba(60, 64, 67, 0.15) 0px 1px 3px 1px;
	}

	.league-row {
		padding: 5px;
		display: flex;
		flex-direction: row;
		justify-content: flex-start;
		align-items: center;
	}

	.league-row image {
		width: 25px;
		height: 25px;
	}

	/deep/ uni-checkbox .uni-checkbox-input.uni-checkbox-input-checked:before {
		font: normal normal normal 14px/1 uni;
		content: "EA08";
		font-size: 0;
		/* 重点使用这一步取消的默认样式 */
		position: absolute;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -48%) scale(1);
		-webkit-transform: translate(-50%, -48%) scale(1);
	}

	/* 重新定义复选框选中后的样式*/
	/deep/ .uni-checkbox-input-checked::before {
		width: 19px;
		height: 19px;
		background: #ff0000;
		border-radius: 50%;
		/* background: url(../../static/img/seal.png) no-repeat center; */
		//选中图标
	}
</style>