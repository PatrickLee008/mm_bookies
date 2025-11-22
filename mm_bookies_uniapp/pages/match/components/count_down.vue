<template>
	<view>
		<view>{{ countdown }}</view>
	</view>
</template>

<script>
	export default {
		props: {
			count_time: {
				type: [String, Date],
			},
			duration: { // 倒计时总时长（毫秒）
				type: Number,
				default: 24 * 60 * 60 * 1000 // 默认24小时
			}
		},
		data() {
			return {
				countdown: '00 : 00 : 00',
				timer: null
			}
		},
		computed: {
			endTime() {
				// const createTime = new Date(this.count_time)
				
				// function beijingToUTC(beijingTimeStr) {
				  // 创建Date对象(会被解析为本地时区)
				  // const beijingTime = new Date(this.count_time);
				  // const localOffset = beijingTime.getTimezoneOffset();
				  // const beijingOffset = -480;
				  // const diff = beijingOffset - localOffset;
				  // const utcTime = new Date(beijingTime.getTime() + diff * 60000);
				  return new Date(this.count_time);
				// }
				// return new Date(createTime.getTime())
				// return new Date(createTime.getTime() + this.duration)
			}
		},
		mounted() {
			this.startCountdown()
		},
		beforeDestroy() {
			this.clearCountdown()
		},
		methods: {
			startCountdown() {
				this.updateCountdown()
				this.timer = setInterval(this.updateCountdown, 1000)
			},
			clearCountdown() {
				if (this.timer) {
					clearInterval(this.timer)
					this.timer = null
				}
			},
			updateCountdown() {
				const now = new Date()
				const remaining = this.endTime - now

				if (remaining <= 0) {
					this.countdown = '00 : 00 : 00'
					this.clearCountdown()
					this.$emit('countdown-end')
					return
				}

				const hours = Math.floor(remaining / (1000 * 60 * 60))
				const minutes = Math.floor((remaining % (1000 * 60 * 60)) / (1000 * 60))
				const seconds = Math.floor((remaining % (1000 * 60)) / 1000)

				this.countdown = [
					hours.toString().padStart(2, '0'),
					minutes.toString().padStart(2, '0'),
					seconds.toString().padStart(2, '0')
				].join(' : ')
			}
		}
	}
</script>