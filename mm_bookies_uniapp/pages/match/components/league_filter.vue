<template>
	<!-- from tangjq--- 改造为右侧弹出的过滤器弹窗 -->
	<view class="filter-popup-wrapper" v-show="!hidden">
		<!-- from tangjq--- 遮罩层 -->
		<view class="filter-mask" @click="set_dialog_hide(true)"></view>

		<!-- from tangjq--- 右侧弹出的内容容器 -->
		<view class="filter-container" :class="{'filter-show': !hidden}">
			<!-- from tangjq--- 标题栏 -->
			<view class="filter-header">
				<text class="filter-title">{{ $t('filter') }}</text>
			</view>

			<!-- from tangjq--- 滚动列表区域 -->
			<scroll-view scroll-y class="filter-scroll">
				<view class="filter-list">
					<checkbox-group @change="CheckboxChange">
						<!-- from tangjq--- All选项 -->
						<view class="filter-item" @click="toggleAll">
							<text class="filter-item-text">All</text>
							<view class="filter-radio" :class="{'filter-radio-checked': all_status}">
								<view class="filter-radio-inner" v-if="all_status"></view>
							</view>
						</view>

						<!-- from tangjq--- 联赛列表 -->
						<view class="filter-item" v-for="(league,index) in league_list" :key="index"
							v-show='league[`include_${tomorrow?"tomorrow":"today"}`]' @click="toggleLeague(index)">
							<text class="filter-item-text">{{league.name}}</text>
							<view class="filter-radio" :class="{'filter-radio-checked': league.checked}">
								<view class="filter-radio-inner" v-if="league.checked"></view>
							</view>
							<!-- from tangjq--- 隐藏的checkbox用于保持原有逻辑 -->
							<checkbox style="display: none;" :checked="league.checked" :value="String(index)">
							</checkbox>
						</view>

						<!-- from tangjq--- 隐藏的All checkbox用于保持原有逻辑 -->
						<checkbox style="display: none;" :checked="all_status" value="All"></checkbox>
					</checkbox-group>
				</view>
			</scroll-view>

			<!-- from tangjq--- 底部确认按钮 -->
			<view class="filter-footer">
				<view class="filter-confirm-btn" @click="set_dialog_hide(true)">
					<text class="filter-confirm-text">{{ $t('confirm') }}</text>
				</view>
			</view>
		</view>
	</view>
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
			// from tangjq--- 切换All选项
			toggleAll() {
				this.all_status = !this.all_status
				let list = this.$toolbox.deep_clone(this.league_list)
				list.forEach((league, index) => {
					league.checked = this.all_status
				})
				list.forEach(ele => {
					ele.match_list.forEach(match => {
						match.checked = true
					})
				})
				this.$emit('update:league_list', list)
			},
			// from tangjq--- 切换单个联赛选项
			toggleLeague(index) {
				let list = this.$toolbox.deep_clone(this.league_list)
				list[index].checked = !list[index].checked
				// 检查是否所有联赛都被选中
				this.all_status = list.every(league => league.checked)
				list.forEach(ele => {
					ele.match_list.forEach(match => {
						match.checked = true
					})
				})
				this.$emit('update:league_list', list)
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
				list.forEach(ele => {
					ele.match_list.forEach(match => {
						match.checked = true
					})
				})
				this.$emit('update:league_list', list)
			},
		}
	}
</script>

<style lang="scss">
	/* from tangjq--- 右侧弹出过滤器样式 */
	.filter-popup-wrapper {
		position: fixed;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		z-index: 10000;
	}

	/* from tangjq--- 遮罩层 */
	.filter-mask {
		position: absolute;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		background-color: rgba(0, 0, 0, 0.5);
		z-index: 1;
	}

	/* from tangjq--- 右侧弹出容器 */
	.filter-container {
		position: absolute;
		top: 0;
		right: 0;
		bottom: 0;
		width: 260px;
		background-color: white;
		z-index: 2;
		display: flex;
		flex-direction: column;
		transform: translateX(100%);
		transition: transform 0.3s ease;
		box-shadow: -2px 0 8px rgba(0, 0, 0, 0.15);
		border-radius: 10px 0 0 10px;
	}

	/* from tangjq--- 显示时滑入 */
	.filter-container.filter-show {
		transform: translateX(0);
	}

	/* from tangjq--- 标题栏 */
	.filter-header {
		background-color: $color-secondary;
		padding: 15px 20px;
		display: flex;
		align-items: center;
		justify-content: center;
		flex-shrink: 0;
		border-radius: 10px 0 0 0;
	}

	.filter-title {
		color: white;
		font-size: 18px;
		font-weight: 600;
	}

	/* from tangjq--- 滚动区域 */
	.filter-scroll {
		flex: 1;
		overflow-y: auto;
		min-height: 0;
		background-color: #f8f9fa;
		padding: 20px 12px;
	}

	.filter-list {
		padding: 0;
		background-color: $bg-color-info;
		border-radius: $radius-medium;
		overflow: hidden;
	}

	/* from tangjq--- 过滤项样式 */
	.filter-item {
		background-color: $bg-color-info;
		margin-bottom: 1px;
		padding: 8px 25px;
		display: flex;
		flex-direction: row;
		justify-content: space-between;
		align-items: center;
		cursor: pointer;
		transition: background-color 0.2s;
		border-bottom: 1px solid var(--theme-primary-alpha-20, rgba(28, 102, 124, .2));
	}

	.filter-item:active {
		background-color: #f5f5f5;
	}

	.filter-item-text {
		color: $color-primary;
		font-size: 14px;
		font-weight: 500;
		flex: 1;
	}

	/* from tangjq--- 自定义单选按钮样式 */
	.filter-radio {
		width: 22px;
		height: 22px;
		border: 2px solid $color-secondary;
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
		flex-shrink: 0;
		transition: all 0.2s;
	}

	.filter-radio-checked {
		background-color: white;
		border-color: $color-secondary;
	}

	.filter-radio-inner {
		width: 12px;
		height: 12px;
		background-color: $color-secondary;
		border-radius: 50%;
	}

	/* from tangjq--- 底部按钮区域 */
	.filter-footer {
		padding: 20px;
		flex-shrink: 0;
		background-color: white;
		box-shadow: 0 -2px 8px rgba(0, 0, 0, 0.05);
		border-radius: 0 0 0 10px;
	}

	.filter-confirm-btn {
		background-color: $color-secondary;
		border-radius: $radius-medium;
		padding: 8px;
		text-align: center;
		cursor: pointer;
		transition: background-color 0.3s;
	}

	.filter-confirm-btn:active {
		background-color: #2d5d5d;
	}

	.filter-confirm-text {
		color: white;
		font-size: 16px;
		font-weight: 600;
	}
</style>