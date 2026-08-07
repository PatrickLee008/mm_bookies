<template>
	<view class="selector-wrapper">
		<view class="cu-tag round sm selector-tag" :style="tag_style" @click="set_dialog_status(!hidden)">
			<text>{{language[current_tag.label]?language[current_tag.label]:current_tag.label}}</text>
			<text class="" :class="hidden?'cuIcon-unfold':'cuIcon-fold'"></text>
		</view>
		<view class="selector-bg" v-if="!hidden" :style="{'top':top,'left':left}">
			<!-- 顶部青绿标题栏：当前选中项 + 收起箭头 -->
			<view class="selector-header" @click="set_dialog_status(true)">
				<text class="selector-header-text">{{language[current_tag.label]?language[current_tag.label]:current_tag.label}}</text>
				<text class="cuIcon-fold selector-header-arrow"></text>
			</view>
			<!-- 选项列表 -->
			<view class="selector-options">
				<view class="option-bg" v-for="(i,_index) in option_list" :key="_index"
					:class="{'option-active':i.checked}" @click="clickOption(_index)">
					<text class="option-text">{{language[i.label]?language[i.label]:i.label}}</text>
					<view class="option-radio" :class="{'radio-checked':i.checked}"></view>
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
			// from tangjq--- 当选中项 value 为 'All'（不区分大小写）时，触发器显示该 prop 代替 'All'
			default_label: {
				type: String,
				default: ''
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
				// from tangjq--- 当选中项是 'All'（默认初始值）时，用 default_label 替代显示
				if (res && typeof res.value === 'string' && res.value.toLowerCase() === 'all' && this.default_label) {
					res = Object.assign({}, res, { label: this.default_label })
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
	.selector-wrapper {
		position: relative;
		margin: 0;
		padding: 0;
	}

	/* 触发器（tag）：统一使用订单筛选栏的青绿色样式，页面可按容器覆盖 */
	.selector-tag {
		background-color: #1C667C;
		color: white;
		gap: 6upx;
		position: relative;
		overflow: visible;
	}

	/* 下拉面板：顶部青绿标题栏 + 浅蓝白选项列表 */
	.selector-bg {
		position: absolute;
		top: calc(100% + 8upx);
		left: 0;
		z-index: 15;
		min-width: 220upx;
		background-color: #F0F9FB;
		border-radius: 16upx;
		box-shadow: 0 6upx 20upx rgba(28, 102, 124, 0.18);
		overflow: hidden;
	}

	/* 顶部青绿标题栏（与触发器同宽，含当前选中项 + 收起箭头） */
	.selector-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 16upx;
		padding: 18upx 24upx;
		background: #1C667C;
		cursor: pointer;
	}

	.selector-header-text {
		color: #FFFFFF;
		font-size: 24upx;
		font-weight: 600;
		line-height: 32upx;
		white-space: nowrap;
	}

	.selector-header-arrow {
		color: #FFFFFF;
		font-size: 22upx;
		flex-shrink: 0;
	}

	/* 选项列表 */
	.selector-options {
		display: flex;
		flex-direction: column;
		padding: 8upx 0;
	}

	.option-bg {
		display: flex;
		justify-content: space-between;
		align-items: center;
		gap: 16upx;
		padding: 18upx 24upx;
		background: transparent;
		white-space: nowrap;
		cursor: pointer;
		transition: background 0.15s ease;
	}

	.option-bg:active {
		background: rgba(28, 102, 124, 0.06);
	}

	.option-text {
		color: #1C667C;
		font-size: 24upx;
		font-weight: 500;
		line-height: 32upx;
		flex: 1;
	}

	/* radio 圆圈：青绿描边，选中带实心内点 */
	.option-radio {
		width: 28upx;
		height: 28upx;
		border: 2upx solid #4fb3bf;
		border-radius: 50%;
		background: transparent;
		flex-shrink: 0;
		position: relative;
		box-sizing: border-box;
	}

	.option-radio.radio-checked::after {
		content: '';
		position: absolute;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		width: 14upx;
		height: 14upx;
		border-radius: 50%;
		background: #4fb3bf;
	}

	/* 旧 option-active 不再使用浅色背景，由 radio-checked 表达选中态 */
	.option-active {
		background: transparent;
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