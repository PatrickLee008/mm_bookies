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
				if (!this.count_time) {
					console.warn('count_down: count_time is empty', this.count_time);
					return new Date(Date.now() + 24 * 60 * 60 * 1000); // 默认24小时后
				}

				// 如果已经是 Date 对象，直接返回
				if (this.count_time instanceof Date) {
					return this.count_time;
				}

				// 处理字符串格式
				let timeStr = String(this.count_time).trim();

				// 检查是否已包含时区信息
				const hasTimezone = timeStr.includes('+') || timeStr.includes('-') ||
					timeStr.endsWith('Z') || /[+-]\d{2}:?\d{2}$/.test(timeStr);

				// 如果已包含时区信息，直接解析
				if (hasTimezone) {
					timeStr = timeStr.replace(' ', 'T');
					let dateObj = new Date(timeStr);
					if (!isNaN(dateObj.getTime())) {
						return dateObj;
					}
				}

				// 没有时区信息时，将 "YYYY-MM-DD HH:MM:SS" 规范化后按本地时间解析
				// 与列表页 new Date(match.LOCAL_MATCH_TIME) 保持一致
				timeStr = timeStr.replace(' ', 'T');

				// 尝试标准解析（作为本地时间）
				let dateObj = new Date(timeStr);

				// 验证日期是否有效
				if (isNaN(dateObj.getTime())) {
					// 尝试替换分隔符
					timeStr = timeStr.replace(/\//g, '-');
					dateObj = new Date(timeStr);

					if (isNaN(dateObj.getTime())) {
						console.error('count_down: Invalid date format', this.count_time);
						return new Date(Date.now() + 24 * 60 * 60 * 1000);
					}
				}

				return dateObj;
			}
		},
		watch: {
			count_time(newVal, oldVal) {
				// 当 count_time 改变时，重启倒计时
				if (newVal !== oldVal) {
					console.log('count_down: count_time changed from', oldVal, 'to', newVal);
					this.clearCountdown();
					this.startCountdown();
				}
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
				const endTime = this.endTime
				const remaining = endTime - now

				// 详细调试信息 - 每次都打印以便追踪问题
				// console.log('count_down: updateCountdown', {
				// 	count_time_raw: this.count_time,
				// 	count_time_type: typeof this.count_time,
				// 	endTime: endTime.toString(),
				// 	endTime_iso: endTime.toISOString(),
				// 	now: now.toString(),
				// 	now_iso: now.toISOString(),
				// 	remaining_ms: remaining,
				// 	remaining_hours: (remaining / (1000 * 60 * 60)).toFixed(2)
				// });

				// 检查 remaining 是否为 NaN
				if (isNaN(remaining)) {
					console.error('count_down: remaining is NaN', {
						count_time: this.count_time,
						endTime: endTime,
						endTimeValid: !isNaN(endTime.getTime())
					});
					this.countdown = '-- : -- : --'
					return
				}

				// 如果时间已过去
				if (remaining <= 0) {
					console.warn('count_down: time has passed', {
						count_time: this.count_time,
						endTime: endTime.toString(),
						now: now.toString(),
						remaining_ms: remaining,
						passed_hours: Math.abs(remaining / (1000 * 60 * 60)).toFixed(2)
					});

					// 如果时间刚刚过去（1小时内），可能是数据错误
					if (remaining > -3600000) { // -1小时
						this.countdown = 'STARTING'
					} else {
						this.countdown = '00 : 00 : 00'
					}

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