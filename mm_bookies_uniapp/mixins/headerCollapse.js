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
			_headerTransitioning: false, // 收缩动画期间忽略布局变化触发的滚动事件
			_headerTransitionTimer: null,
			_lastScrollTop: null,
		}
	},
	methods: {
		/**
		 * scroll-view 滚动事件处理
		 * 滚动超过阈值时收起 header，回到顶部附近时展开
		 */
		handleHeaderScroll(e) {
			if (!e || !e.detail) return
			const scrollTop = Math.max(0, Number(e.detail.scrollTop) || 0)
			const rawDeltaY = Number(e.detail.deltaY)
			const deltaY = Number.isFinite(rawDeltaY) ? rawDeltaY : null
			const previousScrollTop = this._lastScrollTop
			this._lastScrollTop = scrollTop

			if (this._headerTransitioning) {
				const reachedTopByUser = scrollTop < 30 && (
					(deltaY !== null && deltaY < 0) ||
					(deltaY === null && previousScrollTop !== null && scrollTop < previousScrollTop &&
						previousScrollTop - scrollTop < 40)
				)
				if (!reachedTopByUser) return
				this._headerTransitioning = false
				clearTimeout(this._headerTransitionTimer)
			}

			// 收起阈值 80px，展开阈值 30px，避免在阈值附近反复切换。
			let shouldCollapse = this._headerCollapsed
			if (shouldCollapse === null) {
				shouldCollapse = scrollTop > 80
			} else if (!shouldCollapse && scrollTop > 80) {
				shouldCollapse = true
			} else if (shouldCollapse && scrollTop < 30) {
				shouldCollapse = false
			} else {
				return
			}

			this.setHeaderCollapsed(shouldCollapse)
		},

		handleHeaderTop() {
			this._lastScrollTop = 0
			if (this._headerTransitioning || this._headerCollapsed !== true) return
			this.setHeaderCollapsed(false)
		},

		setHeaderCollapsed(collapsed) {
			if (collapsed === this._headerCollapsed) return
			this._headerCollapsed = collapsed
			this._headerTransitioning = true
			uni.$emit('header:setCollapsed', collapsed)
			clearTimeout(this._headerTransitionTimer)
			this._headerTransitionTimer = setTimeout(() => {
				this._headerTransitioning = false
			}, 450)
		},

		/**
		 * header 高度变化回调，更新占位元素高度
		 */
		onHeaderHeightChange(height) {
			if (this.headerHeight === height) return
			this.headerHeight = height
		},
	},
	onUnload() {
		// 页面卸载时重置 header 状态
		uni.$emit('header:setCollapsed', false)
		clearTimeout(this._headerTransitionTimer)
		this._headerCollapsed = null
		this._headerTransitioning = false
		this._lastScrollTop = null
	},
}
