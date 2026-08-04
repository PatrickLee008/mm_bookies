/**
 * Header 收起/展开 Mixin
 *
 * 使用方法：
 * 1. 在页面中引入：import headerCollapse from '@/mixins/headerCollapse.js'
 * 2. mixins: [headerCollapse]
 * 3. scroll-view 添加：@scroll="handleHeaderScroll"
 * 4. zw-header 添加：@headerHeightChange="onHeaderHeightChange"
 * 5. header-placeholder 改为：:style="{ height: headerHeight + 'px' }"
 */
export default {
	data() {
		return {
			headerHeight: 255, // 默认占位高度，等待 header 组件计算后更新
			_headerCollapsed: null, // 当前收起状态（防止重复触发）
		}
	},
	methods: {
		/**
		 * scroll-view 滚动事件处理
		 * 滚动超过阈值时收起 header，回到顶部附近时展开
		 */
		handleHeaderScroll(e) {
			if (!e || !e.detail) return
			const scrollTop = e.detail.scrollTop
			// 收起阈值 80px，展开阈值 30px（滞后避免抖动）
			const shouldCollapse = scrollTop > 80
			if (shouldCollapse !== this._headerCollapsed) {
				this._headerCollapsed = shouldCollapse
				uni.$emit('header:setCollapsed', shouldCollapse)
			}
		},

		/**
		 * header 高度变化回调，更新占位元素高度
		 */
		onHeaderHeightChange(height) {
			this.headerHeight = height
		},
	},
	onUnload() {
		// 页面卸载时重置 header 状态
		uni.$emit('header:setCollapsed', false)
		this._headerCollapsed = null
	},
}
