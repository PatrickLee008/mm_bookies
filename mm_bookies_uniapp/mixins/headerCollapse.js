/**
 * Header 收起/展开 Mixin
 *
 * 使用方法：
 * 1. 在页面中引入：import headerCollapse from '@/mixins/headerCollapse.js'
 * 2. mixins: [headerCollapse]
 * 3. scroll-view 添加：@scroll="handleHeaderScroll" @scrolltoupper="handleHeaderTop"
 *    （@scrolltoupper 是原生「滚动到顶部」事件，不依赖 deltaY 推算，展开更可靠）
 * 4. zw-header 添加：@headerHeightChange="onHeaderHeightChange"
 * 5. header-placeholder 改为：:style="{ height: headerHeight + 'px' }"
 *
 * 判定逻辑只依赖 scrollTop 的双阈值（滞回区间），不再依赖 deltaY 等启发式规则，
 * 避免出现「回到顶部却无法展开」「需要多滑一点才能展开」等不符合直觉的问题。
 *
 * 注意：header 收起/展开会改变 header-placeholder 的高度，从而改变 scroll-view 的
 * 可视高度/可滚动范围。当页面内容较短、可滚动空间有限时，这个布局变化本身会触发新的
 * scroll 事件并再次越过阈值，形成「收起->布局变化->展开->布局变化->收起」的反馈循环、
 * 出现反复抖动。因此每次切换状态后设置一个与 CSS 过渡时长匹配的短暂锁定期，锁定期内
 * 忽略由布局变化连带触发的 scroll 阈值判定和 scrolltoupper 事件，等布局稳定后再继续
 * 响应真实的用户滚动，从而避免「收起后又被布局变化本身弹回展开」的抖动。
 */
const COLLAPSE_THRESHOLD = 80 // 超过该值收起 header
const EXPAND_THRESHOLD = 20 // 低于该值展开 header（与收起阈值留出间隔，避免临界抖动）
const TRANSITION_LOCK_MS = 350 // 与 header/placeholder 的 0.3s 过渡时长匹配，略留余量

export default {
	data() {
		return {
			headerHeight: uni.getStorageSync('Authorization') ? 270 : 201, // 默认占位高度，等待 header 组件计算后更新
			_headerCollapsed: false, // 当前收起状态（防止重复触发）
			_headerScrollTicking: false, // rAF 节流标记，避免 scroll 事件密集触发造成卡顿
			_headerTransitionLockTimer: null, // 过渡期锁定计时器，防止布局变化引发的滚动反馈循环
			_headerTransitionLocked: false,
		}
	},
	methods: {
		/**
		 * scroll-view 滚动事件处理
		 * 滚动超过阈值时收起 header，回到顶部附近时展开
		 * 用 requestAnimationFrame 节流，一帧内只处理一次，减少计算与视图更新次数
		 */
		handleHeaderScroll(e) {
			if (!e || !e.detail) return
			const scrollTop = Math.max(0, Number(e.detail.scrollTop) || 0)
			if (this._headerScrollTicking) return
			this._headerScrollTicking = true
			const schedule = typeof requestAnimationFrame === 'function' ?
				requestAnimationFrame :
				(fn) => setTimeout(fn, 16)
			schedule(() => {
				this._headerScrollTicking = false
				if (this._headerTransitionLocked) return
				this.updateHeaderCollapsedByScrollTop(scrollTop)
			})
		},

		updateHeaderCollapsedByScrollTop(scrollTop) {
			if (!this._headerCollapsed && scrollTop > COLLAPSE_THRESHOLD) {
				this.setHeaderCollapsed(true)
			} else if (this._headerCollapsed && scrollTop <= EXPAND_THRESHOLD) {
				this.setHeaderCollapsed(false)
			}
		},

		/**
		 * scroll-view 原生 scrolltoupper 事件，滚动到顶部时触发。
		 * 注意：header 收起会让 placeholder 变矮、scroll-view 可视区域变大，
		 * 若页面内容本身不长，收起后内容可能刚好被撑满而不再需要滚动，
		 * 此时平台会将 scrollTop 强制归 0 并连带触发一次「假的」scrolltoupper，
		 * 从而出现「刚收起就自动展开」的抖动。因此这里同样遵守过渡期锁定，
		 * 忽略布局变化期间的 scrolltoupper，锁定结束后的真实到顶事件仍会正常展开。
		 */
		handleHeaderTop() {
			if (this._headerTransitionLocked) return
			this.setHeaderCollapsed(false)
		},

		setHeaderCollapsed(collapsed) {
			if (collapsed === this._headerCollapsed) return
			this._headerCollapsed = collapsed
			uni.$emit('header:setCollapsed', collapsed)

			// 状态切换会触发 placeholder 高度过渡，进而改变 scroll-view 可滚动范围，
			// 锁定期内不再响应 scrollTop 阈值判定，避免布局变化引发的连锁触发。
			this._headerTransitionLocked = true
			clearTimeout(this._headerTransitionLockTimer)
			this._headerTransitionLockTimer = setTimeout(() => {
				this._headerTransitionLocked = false
			}, TRANSITION_LOCK_MS)
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
		this._headerCollapsed = false
		this._headerScrollTicking = false
		clearTimeout(this._headerTransitionLockTimer)
		this._headerTransitionLocked = false
	},
}
