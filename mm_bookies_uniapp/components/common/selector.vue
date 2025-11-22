<template>
	<view class="" style="position: relative;margin: 0;padding: 0;">
		<view class="cu-tag round sm selector-tag" :style="{'style':tag_style}" @click="set_dialog_status(!hidden)">
			<text>{{language[current_tag.label]?language[current_tag.label]:current_tag.label}}</text>
			<text class="" :class="hidden?'cuIcon-unfold':'cuIcon-fold'"></text>
		</view>
		<view class="selector-bg" style="" v-if="!hidden" :style="{'top':top,'left':left}">
			<view class="flex-column" style="align-items: flex-start;">
				<view class="option-bg" v-for="(i,_index) in option_list" :key="_index" style=""
					:class="{'option-active width-100':i.checked}" @click="clickOption(_index)">
					{{language[i.label]?language[i.label]:i.label}}
				</view>
			</view>
		</view>

		<view v-if="!hidden" class="mask" @click="hidden = true"></view>
	</view>

</template>

<script>
	export default {
		props: {
			// hidden: {
			// 	type: Boolean,
			// 	default: true,
			// },
			index: {
				type: Number,
				default: 1,
			},
			tag_style: {
				type: Object,
				default: function() {
					return {}
				}
			},
			option_list: {
				type: Array,
				default: function() {
					return []
				}
			},
			top: {
				type: String,
				default: ''
			},
			left: {
				type: String,
				default: '0'
			},
		},
		data() {
			return {
				hidden: true,
				language: this.$config.language,
			}
		},
		computed: {
			current_tag() {
				let res = {}
				let checked = this.option_list.filter(ele => {
					return ele.checked
				})
				if (checked.length > 0) {
					res = checked[0]
				}
				return res
			}
		},
		methods: {
			set_dialog_status(e) {
				// this.$emit('update:hidden', e)
				this.hidden = e
			},
			show() {
				this.set_dialog_status(false)
			},
			show_dialog(...args) {

			},
			clickOption(index) {
				let option_list = this.$toolbox.deep_clone(this.option_list)
				option_list.forEach((ele, _index) => {
					ele.checked = index === _index
				})
				this.$emit('update:option_list', option_list)
				this.$emit('click_option', option_list[index])
				this.set_dialog_status(true)
			},
		}
	}
</script>

<style lang="scss">
	.selector-bg {
		clear: both;
		top: calc(100% - 10upx);
		left: 0;
		position: absolute;
		z-index: 15;
		box-shadow: rgba(99, 99, 99, 0.2) 0px 2px 8px 0px;
		font-style: normal;
		font-family: '__Inter_7be8ac', '__Inter_Fallback_7be8ac';
		color: rgb(12, 53, 106);
		position: absolute;
		font-weight: 400;
		line-height: 1.5;
		min-width: 16px;
		min-height: 16px;
		outline: 0px;
		border-radius: 10px;
		padding: 5px;
		transform-origin: 0px 0px;
		margin-top: 0;
		background-color: rgb(255, 255, 255);

	}

	.option-bg {
		font-weight: 400;
		line-height: 1.5;
		display: flex;
		justify-content: flex-start;
		align-items: center;
		padding: 5px;
		border-radius: 5px;
		font-size: 10px;
		height: 25px;
		min-height: 25px;
		min-width: 15vw;
		white-space: nowrap;
	}

	.option-active {
		background-color: rgba(12, 53, 106, 0.08);
	}

	.selector-tag {
		// padding: 0px 6px;
		background-color: #bdbdbd !important;
		color: white;
		gap: 15rpx;
		position: relative;
		overflow: visible;
	}

	.mask {
		position: fixed;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		z-index: 14;
		/* 低于下拉面板 */
	}
</style>