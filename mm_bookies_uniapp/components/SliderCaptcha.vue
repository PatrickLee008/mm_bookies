<template>
	<view class="slider-captcha-container">
		<view class="captcha-canvas-area"
			:style="{ height: internalCaptchaData.backgroundImage ? canvasHeight + 'px' : '0px', overflow: internalCaptchaData.backgroundImage ? 'hidden' : 'visible' }"
			:triggerGenerate="triggerGenerate" :change:triggerGenerate="canvasCaptcha.generateCaptcha">
			<image v-if="internalCaptchaData.backgroundImage" class="background-image"
				:src="internalCaptchaData.backgroundImage" mode="widthFix"></image>
			<view v-if="internalCaptchaData.backgroundImage && internalCaptchaData.sliderWidth" class="captcha-gap"
				:style="gapStyle">
				<image class="captcha-gap-pattern" src="/static/icon/login/Icon.svg" mode="aspectFit"></image>
			</view>
			<view v-if="internalCaptchaData.backgroundImage && internalCaptchaData.sliderWidth" class="slider-image"
				:class="{ 'slider-animating': isResetting || isSnapping }" :style="sliderImageStyle">
				<image class="slider-puzzle-pattern" src="/static/icon/login/Icon.svg" mode="aspectFit"></image>
			</view>
			<view v-if="isSuccess" class="success-overlay">
				<text class="cuIcon-roundcheckfill success-icon"></text>
			</view>
		</view>

		<view class="slider-track" :class="trackClass">
			<view class="slider-progress" :class="{ 'progress-animating': isSnapping || isResetting }"
				:style="{ width: trackProgressWidth + 'px' }"></view>
			<view class="slider-button" :class="buttonClass" :style="{ left: trackSliderPosition + 'px' }"
				@touchstart="onTouchStart" @touchmove.stop.prevent="onTouchMove" @touchend="onTouchEnd"
				@mousedown="onMouseDown">
				<view v-if="!isSuccess" class="slider-grip">
					<view class="grip-bar"></view>
					<view class="grip-bar"></view>
					<view class="grip-bar"></view>
				</view>
				<text v-else class="cuIcon-check slider-success-check"></text>
			</view>
			<text v-if="!isDragging && !isSuccess" class="slider-text">{{ config.sliderText }}</text>
			<text v-if="isSuccess" class="success-text">{{ config.successText }}</text>
		</view>

		<view class="security-title">{{ config.title }}</view>
		<view class="security-description">{{ config.description }}</view>
	</view>
</template>

<script module="canvasCaptcha" lang="renderjs">
	export default {
		methods: {
			generateCaptcha(newValue, oldValue, ownerInstance) {
				if (!newValue) return

				const width = 300
				const height = 202
				const puzzleSize = 40
				const gapX = Math.floor(Math.random() * (width - puzzleSize - 50)) + 25
				const gapY = Math.floor(Math.random() * (height - puzzleSize - 30)) + 15
				const sourceImage = document.createElement('img')

				sourceImage.onload = function() {
					const backgroundCanvas = document.createElement('canvas')
					backgroundCanvas.width = width
					backgroundCanvas.height = height
					const backgroundContext = backgroundCanvas.getContext('2d')
					backgroundContext.drawImage(sourceImage, 0, 0, width, height)

					const result = {
						backgroundImage: backgroundCanvas.toDataURL('image/png'),
						sliderX: 0,
						sliderY: gapY,
						sliderWidth: puzzleSize,
						sliderHeight: puzzleSize,
						correctX: gapX,
					}

					if (ownerInstance && typeof ownerInstance.callMethod === 'function') {
						ownerInstance.callMethod('onCaptchaGenerated', result)
					}
				}
				sourceImage.onerror = function() {
					if (ownerInstance && typeof ownerInstance.callMethod === 'function') {
						ownerInstance.callMethod('onCaptchaError')
					}
				}
				sourceImage.src = '/static/icon/login/verify-bg.png'
			},
		},
	}
</script>

<script>
	export default {
		name: 'SliderCaptcha',
		props: {
			showClose: {
				type: Boolean,
				default: true,
			},
			config: {
				type: Object,
				default: () => ({
					title: 'Security Check',
					description: 'Prove you are human to continue.',
					sliderText: 'Slide to verify',
					successText: 'Verification successful',
					canvasWidth: 300,
					canvasHeight: 202,
					sliderSize: 40,
				}),
			},
			autoGenerate: {
				type: Boolean,
				default: false,
			},
			triggerGenerate: {
				type: [Number, String, Boolean],
				default: 0,
			},
		},
		data() {
			return {
				internalCaptchaData: {
					backgroundImage: '',
					sliderY: 0,
					sliderWidth: 0,
					sliderHeight: 0,
					correctX: 0,
				},
				isDragging: false,
				isSuccess: false,
				isResetting: false,
				isSnapping: false,
				containerWidth: 0,
				trackWidth: 0,
				canvasHeight: 202,
				trackScaleRatio: 1,
				canvasScaleRatio: 1,
				sliderPosition: 0,
				startX: 0,
				sliderButtonSize: 42,
			}
		},
		computed: {
			sliderImageStyle() {
				if (!this.internalCaptchaData.sliderWidth) return {}
				return {
					position: 'absolute',
					left: `${this.sliderPosition * this.canvasScaleRatio / this.trackScaleRatio}px`,
					top: `${this.internalCaptchaData.sliderY * this.canvasScaleRatio}px`,
					width: `${this.internalCaptchaData.sliderWidth * this.canvasScaleRatio}px`,
					height: `${(this.internalCaptchaData.sliderHeight || this.internalCaptchaData.sliderWidth) * this.canvasScaleRatio}px`,
				}
			},
			gapStyle() {
				if (!this.internalCaptchaData.sliderWidth) return {}
				return {
					position: 'absolute',
					left: `${this.internalCaptchaData.correctX * this.canvasScaleRatio}px`,
					top: `${this.internalCaptchaData.sliderY * this.canvasScaleRatio}px`,
					width: `${this.internalCaptchaData.sliderWidth * this.canvasScaleRatio}px`,
					height: `${(this.internalCaptchaData.sliderHeight || this.internalCaptchaData.sliderWidth) * this.canvasScaleRatio}px`,
				}
			},
			trackSliderPosition() {
				return this.sliderPosition
			},
			trackProgressWidth() {
				return Math.min(this.trackWidth, this.sliderPosition + this.sliderButtonSize)
			},
			trackClass() {
				return {
					'track-success': this.isSuccess,
					'track-error': this.isResetting && !this.isSuccess,
					'track-snapping': this.isSnapping,
				}
			},
			buttonClass() {
				return {
					'button-dragging': this.isDragging,
					'button-success': this.isSuccess,
					'button-animating': this.isResetting || this.isSnapping,
				}
			},
			isReady() {
				return !!this.internalCaptchaData.backgroundImage && this.trackWidth > 0
			},
		},
		mounted() {
			this.$nextTick(() => {
				setTimeout(() => {
					this.calculateDimensions()
					if (this.autoGenerate) this.$emit('init-generate')
				}, 100)
			})
		},
		methods: {
			onCaptchaGenerated(data) {
				this.internalCaptchaData = data
				this.resetState()
				this.$nextTick(() => this.calculateDimensions())
			},
			onCaptchaError() {
				this.$emit('error')
			},
			calculateDimensions() {
				const canvasQuery = uni.createSelectorQuery().in(this)
				canvasQuery.select('.captcha-canvas-area').boundingClientRect((rect) => {
					if (rect && rect.width) {
						this.canvasScaleRatio = rect.width / this.config.canvasWidth
						this.canvasHeight = this.config.canvasHeight * this.canvasScaleRatio
					}
				}).exec()
				const trackQuery = uni.createSelectorQuery().in(this)
				trackQuery.select('.slider-track').boundingClientRect((rect) => {
					if (rect && rect.width) {
						this.containerWidth = rect.width
						this.trackWidth = rect.width
						this.trackScaleRatio = rect.width / this.config.canvasWidth
					}
				}).exec()
			},
			resetState() {
				this.isDragging = false
				this.isSuccess = false
				this.isResetting = false
				this.isSnapping = false
				this.sliderPosition = 0
			},
			onTouchStart(e) {
				if (!this.isReady || this.isSuccess) return
				this.isDragging = true
				this.isSnapping = false
				this.startX = e.touches[0].clientX - this.sliderPosition
			},
			onTouchMove(e) {
				if (!this.isDragging) return
				let newPosition = e.touches[0].clientX - this.startX
				const maxPosition = this.trackWidth - this.sliderButtonSize
				newPosition = Math.max(0, Math.min(newPosition, maxPosition))
				this.sliderPosition = newPosition
			},
			onTouchEnd() {
				if (!this.isDragging) return
				this.isDragging = false
				this.verify()
			},
			// #ifdef H5
			onMouseDown(e) {
				if (!this.isReady || this.isSuccess) return
				this.isDragging = true
				this.isSnapping = false
				this.startX = e.clientX - this.sliderPosition
				const mouseMoveHandler = (event) => {
					if (!this.isDragging) return
					let newPosition = event.clientX - this.startX
					const maxPosition = this.trackWidth - this.sliderButtonSize
					newPosition = Math.max(0, Math.min(newPosition, maxPosition))
					this.sliderPosition = newPosition
				}
				const mouseUpHandler = () => {
					if (!this.isDragging) return
					this.isDragging = false
					this.verify()
					document.removeEventListener('mousemove', mouseMoveHandler)
					document.removeEventListener('mouseup', mouseUpHandler)
				}
				document.addEventListener('mousemove', mouseMoveHandler)
				document.addEventListener('mouseup', mouseUpHandler)
			},
			// #endif
			// #ifndef H5
			onMouseDown() {},
			// #endif
			verify() {
				const userX = Math.round(this.sliderPosition / this.trackScaleRatio)
				const isValid = Math.abs(userX - this.internalCaptchaData.correctX) <= 8
				if (isValid) {
					const targetPosition = Math.max(0, Math.min(
						this.trackWidth - this.sliderButtonSize,
						this.internalCaptchaData.correctX * this.trackScaleRatio
					))
					this.isSnapping = true
					this.sliderPosition = targetPosition
					this.isSuccess = true
					this.$emit('verify', {
						x: this.internalCaptchaData.correctX
					})
					setTimeout(() => {
						this.isSnapping = false
					}, 300)
					return
				}
				this.isSnapping = false
				this.isResetting = true
				setTimeout(() => {
					this.sliderPosition = 0
					setTimeout(() => {
						this.isResetting = false
					}, 300)
				}, 500)
				this.$emit('verify-fail')
			},
			handleRefresh() {
				this.$emit('refresh')
			},
		},
	}
</script>

<style lang="scss" scoped>
	.slider-captcha-container {
		width: 100%;
		padding: 0;
		background: transparent;
		box-sizing: border-box;
	}

	.captcha-canvas-area {
		position: relative;
		width: 100%;
		border-radius: 12px;
		overflow: hidden;
		background: rgba(0, 0, 0, 0.12);
		min-height: 0;
	}

	.background-image {
		width: 100%;
		display: block;
		border-radius: 12px;
		animation: captcha-fade-in 0.2s ease;
	}

	.captcha-gap {
		z-index: 1;
		display: flex;
		align-items: center;
		justify-content: center;
		width: 40px;
		height: 40px;
		box-sizing: border-box;
		border: 2px dashed #FFFFFF4D;
		background: rgba(0, 0, 0, 0.60);
		border-radius: 8px;
		pointer-events: none;
	}

	.captcha-gap-pattern {
		width: 29px;
		height: 30px;
		opacity: 0.4;
	}

	.slider-image {
		position: absolute;
		z-index: 2;
		display: flex;
		align-items: center;
		justify-content: center;
		width: 40px;
		height: 40px;
		box-sizing: border-box;
		overflow: hidden;
		border: 3px solid $color-secondary;
		border-radius: 8px;
		background: var(--theme-secondary-alpha-40, rgba(55, 189, 204, 0.4));
		backdrop-filter: blur(4px);
		-webkit-backdrop-filter: blur(4px);
		pointer-events: none;

		&.slider-animating {
			transition: left 0.5s cubic-bezier(0.34, 1.56, 0.64, 1);
		}
	}

	.slider-puzzle-pattern {
		position: relative;
		z-index: 1;
		width: 29px;
		height: 30px;
	}

	.success-overlay {
		position: absolute;
		top: 0;
		right: 0;
		bottom: 0;
		left: 0;
		display: flex;
		align-items: center;
		justify-content: center;
		background: rgba(53, 191, 208, 0.2);
	}

	.success-icon {
		color: $color-secondary;
		font-size: 60px;
	}

	.slider-track {
		position: relative;
		width: 100%;
		height: 44px;
		margin-top: 12px;
		background: rgba(3, 44, 45, 0.72);
		border: 1px solid rgba(136, 224, 229, 0.12);
		border-radius: 22px;
		overflow: hidden;
		box-sizing: border-box;

		&.track-success {
			border-color: rgba(136, 224, 229, 0.55);
		}

		&.track-error {
			border-color: rgba(255, 91, 104, 0.75);
		}

		&.track-snapping {
			border-color: rgba(255, 255, 255, 0.55);
		}
	}

	.slider-progress {
		position: absolute;
		top: 0;
		left: 0;
		height: 100%;
		border-radius: 22px;
		background: $color-secondary;

		&.progress-animating {
			transition: width 0.5s cubic-bezier(0.34, 1.56, 0.64, 1);
		}
	}

	.slider-button {
		position: absolute;
		top: 50%;
		left: 0;
		z-index: 10;
		display: flex;
		align-items: center;
		justify-content: center;
		width: 42px;
		height: 42px;
		background: $color-secondary-light;
		border: 0;
		border-radius: 50%;
		box-shadow: 0 2px 7px rgba(0, 0, 0, 0.2);
		transform: translateY(-50%);

		&.button-dragging {
			box-shadow: 0 3px 12px rgba(0, 0, 0, 0.32);
		}

		&.button-success {
			background: $color-secondary-light;
		}

		&.button-animating {
			transition: left 0.5s cubic-bezier(0.34, 1.56, 0.64, 1);
		}
	}

	.slider-grip {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 2px;
	}

	.grip-bar {
		width: 4px;
		height: 16px;
		border-radius: 2px;
		background: $color-secondary;
	}

	.slider-success-check {
		color: $color-secondary;
		font-size: 22px;
	}

	.slider-text,
	.success-text {
		position: absolute;
		top: 0;
		right: 0;
		left: 0;
		display: flex;
		align-items: center;
		justify-content: center;
		height: 44px;
		color: rgba(255, 255, 255, 0.28);
		font-size: 12px;
		font-weight: 500;
		letter-spacing: 2.5px;
		text-transform: uppercase;
		pointer-events: none;
	}

	.success-text {
		color: rgba(255, 255, 255, 0.86);
		font-weight: 600;
	}

	.security-title {
		margin-top: 17px;
		color: #ffffff;
		font-size: 15px;
		font-weight: 700;
		line-height: 1.3;
		text-align: center;
	}

	.security-description {
		margin-top: 8px;
		margin-bottom: 8px;
		color: rgba(255, 255, 255, 0.84);
		font-size: 11px;
		line-height: 1.4;
		text-align: center;
	}

	@keyframes captcha-fade-in {
		from {
			opacity: 0;
		}

		to {
			opacity: 1;
		}
	}
</style>