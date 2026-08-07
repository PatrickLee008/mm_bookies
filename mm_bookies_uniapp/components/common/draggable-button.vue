<template>
	<view 
		ref="dragBtn"
		class="draggable-button"
		:style="buttonStyle"
		@touchstart="handleTouchStart"
		@touchmove="handleTouchMove"
		@touchend="handleTouchEnd"
		@mousedown="handleMouseDown"
		@click="handleClick"
	>
		<slot></slot>
	</view>
</template>

<script>
export default {
	name: 'DraggableButton',
	props: {
		initialRight: {
			type: Number,
			default: 20
		},
		initialBottom: {
			type: Number,
			default: 100
		},
		storageKey: {
			type: String,
			default: 'draggable_btn_position'
		},
		btnSize: {
			type: Number,
			default: 50
		},
		safeAreaBottom: {
			type: Number,
			default: 10
		},
		safeAreaRight: {
			type: Number,
			default: 10
		}
	},
	data() {
		// 在data初始化时就从storage读取位置，避免先渲染默认位置再闪现到存储位置
		let savedRight = this.initialRight
		let savedBottom = this.initialBottom
		try {
			const saved = uni.getStorageSync(this.storageKey)
			if (saved) {
				const pos = JSON.parse(saved)
				if (typeof pos.right === 'number' && typeof pos.bottom === 'number') {
					savedRight = pos.right
					savedBottom = pos.bottom
				}
			}
		} catch (e) {}
		
		return {
			position: { right: savedRight, bottom: savedBottom },
			startPos: { x: 0, y: 0 },
			isDragging: false,
			hasMoved: false,
			isMouseDragging: false,
			currentDragRight: savedRight,
			currentDragBottom: savedBottom,
			buttonStyle: {
				right: savedRight + 'px',
				bottom: savedBottom + 'px',
				transition: 'none'
			}
		}
	},
	mounted() {
		// 位置已在data初始化时加载，无需再loadPosition
	},
	methods: {
		loadPosition() {
			try {
				const saved = uni.getStorageSync(this.storageKey)
				if (saved) {
					const pos = JSON.parse(saved)
					this.position = pos
					// console.log('[DraggableButton] Loaded position:', pos)
				}
			} catch (e) {
				console.error('Load position error:', e)
			}
			
			// 初始化拖动位置
			this.currentDragRight = this.position.right
			this.currentDragBottom = this.position.bottom
			
			// 使用响应式数据更新位置
			this.$set(this.buttonStyle, 'right', this.position.right + 'px')
			this.$set(this.buttonStyle, 'bottom', this.position.bottom + 'px')
			this.$set(this.buttonStyle, 'transition', 'none')
			this.$set(this.buttonStyle, 'transform', '')
			
			// console.log('[DraggableButton] Initial position set:', this.position)
		},
		savePosition() {
			try {
				uni.setStorageSync(this.storageKey, JSON.stringify(this.position))
			} catch (e) {
				console.error('Save position error:', e)
			}
		},
		handleTouchStart(e) {
			// console.log('[DraggableButton] touchstart triggered')
			this.isDragging = true
			this.hasMoved = false
			this.startPos = {
				x: e.touches[0].clientX,
				y: e.touches[0].clientY
			}
			
			// 记录当前实际位置
			this.currentDragRight = this.position.right
			this.currentDragBottom = this.position.bottom
			this.$set(this.buttonStyle, 'transition', 'none')
		},
		handleTouchMove(e) {
			if (!this.isDragging) return
			
			// 阻止默认行为，防止页面滚动
			if (e.preventDefault) {
				e.preventDefault()
			}
			
			const currentX = e.touches[0].clientX
			const currentY = e.touches[0].clientY
			const deltaX = currentX - this.startPos.x
			const deltaY = currentY - this.startPos.y
			
			if (Math.abs(deltaX) > 5 || Math.abs(deltaY) > 5) {
				this.hasMoved = true
			}
			
			// 使用响应式数据更新位置
			let newRight = this.currentDragRight - deltaX
			let newBottom = this.currentDragBottom - deltaY
			
			// 限制边界
			const systemInfo = uni.getSystemInfoSync()
			const screenWidth = systemInfo.windowWidth
			const screenHeight = systemInfo.windowHeight
			
			newRight = Math.max(this.safeAreaRight, Math.min(newRight, screenWidth - this.btnSize - this.safeAreaRight))
			newBottom = Math.max(this.safeAreaBottom, Math.min(newBottom, screenHeight - this.btnSize))
			
			this.$set(this.buttonStyle, 'right', newRight + 'px')
			this.$set(this.buttonStyle, 'bottom', newBottom + 'px')
			
			// console.log('[DraggableButton] Moving:', { newRight, newBottom, deltaX, deltaY })
		},
		handleTouchEnd() {
			if (!this.isDragging) return
			
			this.isDragging = false
			
			if (this.hasMoved) {
				// 从 buttonStyle 中获取当前位置
				const currentRight = parseFloat(this.buttonStyle.right) || this.position.right
				const currentBottom = parseFloat(this.buttonStyle.bottom) || this.position.bottom
				
				// 限制边界
				const systemInfo = uni.getSystemInfoSync()
				const screenWidth = systemInfo.windowWidth
				const screenHeight = systemInfo.windowHeight
				
				let finalRight = Math.max(this.safeAreaRight, Math.min(currentRight, screenWidth - this.btnSize - this.safeAreaRight))
				let finalBottom = Math.max(this.safeAreaBottom, Math.min(currentBottom, screenHeight - this.btnSize))
				
				// 如果需要回弹，使用平滑动画
				if (finalRight !== currentRight || finalBottom !== currentBottom) {
					this.$set(this.buttonStyle, 'transition', 'right 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94), bottom 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94)')
					this.$set(this.buttonStyle, 'right', finalRight + 'px')
					this.$set(this.buttonStyle, 'bottom', finalBottom + 'px')
					
					// 动画结束后清理
					setTimeout(() => {
						this.$set(this.buttonStyle, 'transition', 'none')
					}, 300)
				}
				
				this.position = { right: finalRight, bottom: finalBottom }
				this.savePosition()
			}
		},
		// 鼠标按下
		handleMouseDown(e) {
			// APP 环境不支持 document，直接返回
			if (typeof document === 'undefined') return
			
			this.isMouseDragging = true
			this.isDragging = true
			this.hasMoved = false
			this.startPos = {
				x: e.clientX,
				y: e.clientY
			}
			
			// 记录当前实际位置
			this.currentDragRight = this.position.right
			this.currentDragBottom = this.position.bottom
			this.$set(this.buttonStyle, 'transition', 'none')
			
			// 监听鼠标移动和释放
			document.addEventListener('mousemove', this.handleMouseMove)
			document.addEventListener('mouseup', this.handleMouseUp)
		},
		// 鼠标移动
		handleMouseMove(e) {
			if (!this.isMouseDragging || typeof document === 'undefined') return
			
			const currentX = e.clientX
			const currentY = e.clientY
			const deltaX = currentX - this.startPos.x
			const deltaY = currentY - this.startPos.y
			
			if (Math.abs(deltaX) > 5 || Math.abs(deltaY) > 5) {
				this.hasMoved = true
			}
			
			let newRight = this.currentDragRight - deltaX
			let newBottom = this.currentDragBottom - deltaY
			
			// 限制边界
			const systemInfo = uni.getSystemInfoSync()
			const screenWidth = systemInfo.windowWidth
			const screenHeight = systemInfo.windowHeight
			
			newRight = Math.max(this.safeAreaRight, Math.min(newRight, screenWidth - this.btnSize - this.safeAreaRight))
			newBottom = Math.max(this.safeAreaBottom, Math.min(newBottom, screenHeight - this.btnSize))
			
			this.$set(this.buttonStyle, 'right', newRight + 'px')
			this.$set(this.buttonStyle, 'bottom', newBottom + 'px')
		},
		// 鼠标释放
		handleMouseUp() {
			if (!this.isMouseDragging || typeof document === 'undefined') return
			
			this.isMouseDragging = false
			this.isDragging = false
			
			// 移除监听
			document.removeEventListener('mousemove', this.handleMouseMove)
			document.removeEventListener('mouseup', this.handleMouseUp)
			
			// 复用 touchEnd 的逻辑
			this.handleTouchEnd()
		},
		handleClick() {
			if (!this.hasMoved) {
				this.$emit('click')
			}
		}
	}
}
</script>

<style scoped>
.draggable-button {
	position: fixed;
	z-index: 1001;
	cursor: pointer;
}
</style>
