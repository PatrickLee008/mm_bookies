<template>
	<view class="date-range-picker" :class="{ 'date-range-picker-inline': inline }">
		<view v-if="!hidden && !show_custom_panel" class="date-picker-dropdown-layer">
			<view class="date-picker-dropdown-mask" @click="close"></view>
			<view class="date-picker-dropdown" @click.stop>
				<!-- <view class="date-picker-header">
					<view class="date-picker-header-title">
						<theme-icon name="calendar" class="date-picker-header-icon"
							color="var(--theme-icon-on-primary, #fff)"></theme-icon>
						<text>{{ $t('Type') }}</text>
					</view>
					<text class="cuIcon-unfold date-picker-header-arrow"></text>
				</view> -->

				<view class="date-options">
					<view class="date-option" v-for="(item, index) in date_arr" :key="item.value" @click="click(index)">
						<text class="date-option-label">{{ getDateLabel(item) }}</text>
						<view class="date-radio" :class="{ 'date-radio-checked': item.checked }">
							<view v-if="item.checked" class="date-radio-dot"></view>
						</view>
					</view>
				</view>
			</view>
		</view>

		<view v-if="show_custom_panel" class="custom-modal-layer">
			<view class="custom-modal-mask" @click="cancel_custom_modal"></view>
			<view class="custom-date-modal" @click.stop>
				<view class="custom-modal-header">
					<text class="custom-modal-title">{{ $t('custom_date_title') }}</text>
					<text class="custom-modal-close" @click="cancel_custom_modal">×</text>
				</view>
				<view class="custom-date-panel">
					<view class="custom-date-row">
						<text class="custom-date-label">{{ $t('start_date') }}</text>
						<view class="custom-date-input" @click="toggle_calendar('start')">
							<text :class="custom_start_date ? 'custom-date-text' : 'custom-date-placeholder'">
								{{ custom_start_date ? custom_start_date : 'YYYY-MM-DD' }}
							</text>
							<theme-icon name="calendar" class="custom-date-icon"
								color="var(--theme-icon-primary, var(--theme-primary))"></theme-icon>
						</view>
						<view class="calendar-panel" v-if="calendar_target === 'start'">
							<view class="calendar-header">
								<view class="calendar-nav-btn" @click.stop="prev_month">‹</view>
								<text
									class="calendar-title">{{ calendar_year }}-{{ String(calendar_month).padStart(2, '0') }}</text>
								<view class="calendar-nav-btn" @click.stop="next_month">›</view>
							</view>
							<view class="calendar-weekdays">
								<text class="calendar-weekday" v-for="(weekday, weekdayIndex) in weekday_labels"
									:key="weekdayIndex">{{ weekday }}</text>
							</view>
							<view class="calendar-days">
								<view class="calendar-day" v-for="(day, dayIndex) in calendar_days" :key="dayIndex"
									:class="{
										'calendar-day-disabled': day.disabled,
										'calendar-day-other': !day.current_month,
										'calendar-day-selected': day.selected,
										'calendar-day-in-range': day.in_range
									}" @click.stop="select_calendar_day(day)">
									<text>{{ day.label }}</text>
								</view>
							</view>
						</view>
					</view>

					<view class="custom-date-row">
						<text class="custom-date-label">{{ $t('end_date') }}</text>
						<view class="custom-date-input" @click="toggle_calendar('end')">
							<text :class="custom_end_date ? 'custom-date-text' : 'custom-date-placeholder'">
								{{ custom_end_date ? custom_end_date : 'YYYY-MM-DD' }}
							</text>
							<theme-icon name="calendar" class="custom-date-icon"
								color="var(--theme-icon-primary, var(--theme-primary))"></theme-icon>
						</view>
						<view class="calendar-panel" v-if="calendar_target === 'end'">
							<view class="calendar-header">
								<view class="calendar-nav-btn" @click.stop="prev_month">‹</view>
								<text
									class="calendar-title">{{ calendar_year }}-{{ String(calendar_month).padStart(2, '0') }}</text>
								<view class="calendar-nav-btn" @click.stop="next_month">›</view>
							</view>
							<view class="calendar-weekdays">
								<text class="calendar-weekday" v-for="(weekday, weekdayIndex) in weekday_labels"
									:key="weekdayIndex">{{ weekday }}</text>
							</view>
							<view class="calendar-days">
								<view class="calendar-day" v-for="(day, dayIndex) in calendar_days" :key="dayIndex"
									:class="{
										'calendar-day-disabled': day.disabled,
										'calendar-day-other': !day.current_month,
										'calendar-day-selected': day.selected,
										'calendar-day-in-range': day.in_range
									}" @click.stop="select_calendar_day(day)">
									<text>{{ day.label }}</text>
								</view>
							</view>
						</view>
					</view>

					<view class="custom-date-actions">
						<view class="custom-btn custom-btn-cancel" @click="cancel_custom_modal">{{ $t('Cancel') }}
						</view>
						<view class="custom-btn custom-btn-confirm"
							:class="{ 'custom-btn-disabled': !can_confirm_custom }" @click="confirm_custom">
							{{ $t('Confirm') }}
						</view>
					</view>
				</view>
			</view>
		</view>
	</view>
</template>

<script>
	export default {
		name: 'date-range-picker',
		props: {
			inline: {
				type: Boolean,
				default: false,
			},
		},
		data() {
			const today = new Date()
			return {
				hidden: true,
				date_arr: [],
				show_custom_panel: false,
				custom_start_date: '',
				custom_end_date: '',
				saved_custom_start_date: '',
				saved_custom_end_date: '',
				selection_before_custom: '',
				calendar_target: '',
				calendar_year: today.getFullYear(),
				calendar_month: today.getMonth() + 1,
				weekday_labels: ['Su', 'Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa'],
			}
		},
		computed: {
			can_confirm_custom() {
				return Boolean(this.custom_start_date && this.custom_end_date)
			},
			calendar_days() {
				const year = this.calendar_year
				const month = this.calendar_month
				const first_day = new Date(year, month - 1, 1)
				const last_day = new Date(year, month, 0)
				const first_weekday = first_day.getDay()
				const days_in_month = last_day.getDate()
				const previous_month_last_day = new Date(year, month - 1, 0).getDate()
				const today = new Date()
				today.setHours(0, 0, 0, 0)
				const days = []

				for (let index = first_weekday - 1; index >= 0; index--) {
					const day = previous_month_last_day - index
					const date_obj = new Date(year, month - 2, day)
					days.push(this._build_day(day, date_obj, false, today))
				}
				for (let day = 1; day <= days_in_month; day++) {
					const date_obj = new Date(year, month - 1, day)
					days.push(this._build_day(day, date_obj, true, today))
				}
				for (let day = 1; days.length < 42; day++) {
					const date_obj = new Date(year, month, day)
					days.push(this._build_day(day, date_obj, false, today))
				}
				return days
			}
		},
		methods: {
			_build_day(day, date_obj, current_month, today) {
				const date_str = this._date_to_str(date_obj)
				let disabled = false
				if (this.calendar_target === 'start' && this.custom_end_date && date_str > this.custom_end_date) {
					disabled = true
				}
				if (this.calendar_target === 'end' && this.custom_start_date && date_str < this.custom_start_date) {
					disabled = true
				}
				const selected = (this.calendar_target === 'start' && date_str === this.custom_start_date) ||
					(this.calendar_target === 'end' && date_str === this.custom_end_date)
				const in_range = Boolean(
					this.custom_start_date &&
					this.custom_end_date &&
					date_str > this.custom_start_date &&
					date_str < this.custom_end_date
				)
				return {
					label: day,
					date_str,
					current_month,
					disabled,
					selected,
					in_range,
				}
			},
			_date_to_str(date) {
				const year = date.getFullYear()
				const month = String(date.getMonth() + 1).padStart(2, '0')
				const day = String(date.getDate()).padStart(2, '0')
				return `${year}-${month}-${day}`
			},
			getDateLabel(item) {
				const key = item.value === 'custom' ? 'custom_date' : item.value
				return this.$t(key)
			},
			toggle_calendar(target) {
				if (this.calendar_target === target) {
					this.calendar_target = ''
					return
				}

				this.calendar_target = target
				const reference_date = target === 'start' ? this.custom_start_date : this.custom_end_date
				if (reference_date) {
					const parts = reference_date.split('-')
					this.calendar_year = parseInt(parts[0], 10)
					this.calendar_month = parseInt(parts[1], 10)
				} else {
					const today = new Date()
					this.calendar_year = today.getFullYear()
					this.calendar_month = today.getMonth() + 1
				}
			},
			select_calendar_day(day) {
				if (day.disabled) return
				if (this.calendar_target === 'start') {
					this.custom_start_date = day.date_str
					if (this.custom_end_date && day.date_str > this.custom_end_date) {
						this.custom_end_date = day.date_str
					}
				} else if (this.calendar_target === 'end') {
					this.custom_end_date = day.date_str
					if (this.custom_start_date && day.date_str < this.custom_start_date) {
						this.custom_start_date = day.date_str
					}
				}
				this.calendar_target = ''
			},
			prev_month() {
				if (this.calendar_month === 1) {
					this.calendar_month = 12
					this.calendar_year--
				} else {
					this.calendar_month--
				}
			},
			next_month() {
				if (this.calendar_month === 12) {
					this.calendar_month = 1
					this.calendar_year++
				} else {
					this.calendar_month++
				}
			},
			set_dialog_hide(value) {
				if (value && this.show_custom_panel) {
					this.cancel_custom()
				}
				this.hidden = value
				this.calendar_target = ''
			},
			close() {
				this.set_dialog_hide(true)
			},
			cancel_custom_modal() {
				this.cancel_custom()
				this.hidden = true
			},
			show() {
				this.hidden = false
				this.show_custom_panel = false
				this.calendar_target = ''
			},
			begin_custom() {
				const today = this.formatDate(new Date()).value
				this.custom_start_date = this.saved_custom_start_date || today
				this.custom_end_date = this.saved_custom_end_date || today
				this.calendar_target = ''
			},
			click(index) {
				const result = this.date_arr[index]
				if (result.value === 'custom') {
					if (this.show_custom_panel) {
						this.cancel_custom()
						return
					}
					const selected = this.date_arr.find(item => item.checked)
					this.selection_before_custom = selected ? selected.value : ''
					this.date_arr.forEach((item, itemIndex) => {
						item.checked = index === itemIndex
					})
					this.show_custom_panel = true
					this.begin_custom()
					return
				}

				this.show_custom_panel = false
				this.calendar_target = ''
				this.date_arr.forEach((item, itemIndex) => {
					item.checked = index === itemIndex
				})
				const {
					startDate,
					endDate
				} = this.getDateRange(result.value)
				this.$emit('click_option', [this.formatDate(startDate), this.formatDate(endDate)],
					this.getDateLabel(result))
				this.set_dialog_hide(true)
			},
			confirm_custom() {
				if (!this.can_confirm_custom) {
					uni.showToast({
						title: this.$t('select_date_range'),
						icon: 'none'
					})
					return
				}

				const start = this.parseDate(this.custom_start_date)
				const end = this.parseDate(this.custom_end_date)
				this.saved_custom_start_date = this.custom_start_date
				this.saved_custom_end_date = this.custom_end_date
				this.selection_before_custom = 'custom'
				this.date_arr.forEach(item => {
					item.checked = item.value === 'custom'
				})
				this.show_custom_panel = false
				this.calendar_target = ''
				this.$emit('click_option', [this.formatDate(start), this.formatDate(end)])
				this.set_dialog_hide(true)
			},
			cancel_custom() {
				this.custom_start_date = this.saved_custom_start_date
				this.custom_end_date = this.saved_custom_end_date
				this.show_custom_panel = false
				this.calendar_target = ''
				const restoredSelection = this.saved_custom_start_date && this.saved_custom_end_date ?
					'custom' : this.selection_before_custom
				this.date_arr.forEach(item => {
					item.checked = item.value === restoredSelection
				})
			},
			parseDate(date_string) {
				const parts = date_string.split('-')
				return new Date(parseInt(parts[0], 10), parseInt(parts[1], 10) - 1, parseInt(parts[2], 10))
			},
			formatDate(date) {
				const year = date.getFullYear()
				const month = String(date.getMonth() + 1).padStart(2, '0')
				const day = String(date.getDate()).padStart(2, '0')
				return {
					value: `${year}-${month}-${day}`,
					show: `${day}/${month}/${year}`,
				}
			},
			getDateRange(type) {
				const today = new Date()
				today.setHours(0, 0, 0, 0)
				let startDate
				let endDate
				switch (type) {
					case 'today':
						startDate = new Date(today)
						endDate = new Date(today)
						break
					case 'yesterday':
						startDate = new Date(today)
						startDate.setDate(today.getDate() - 1)
						endDate = new Date(startDate)
						break
					case 'weekly':
						startDate = new Date(today)
						startDate.setDate(today.getDate() - today.getDay() + (today.getDay() === 0 ? -6 : 1))
						endDate = new Date(today)
						break
					case 'last_week':
						startDate = new Date(today)
						const days_since_monday = today.getDay() === 0 ? 6 : today.getDay() - 1
						startDate.setDate(today.getDate() - days_since_monday - 7)
						endDate = new Date(startDate)
						endDate.setDate(startDate.getDate() + 6)
						break
					case 'monthly':
						startDate = new Date(today.getFullYear(), today.getMonth(), 1)
						endDate = new Date(today)
						break
					case 'last_month':
						startDate = new Date(today.getFullYear(), today.getMonth() - 1, 1)
						endDate = new Date(today.getFullYear(), today.getMonth(), 0)
						break
					default:
						startDate = new Date(today)
						endDate = new Date(today)
				}
				return {
					startDate,
					endDate
				}
			},
		},
		created() {
			this.date_arr = ['today', 'yesterday', 'weekly', 'last_week', 'monthly', 'last_month', 'custom']
				.map((value, index) => ({
					checked: index === 0,
					value,
				}))
		}
	}
</script>

<style lang="scss">
	.date-picker-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		min-height: 56upx;
		padding: 15upx 10upx;
		background-color: $color-primary;
		color: #fff;
		box-sizing: border-box;
	}

	.date-picker-header-title {
		display: flex;
		align-items: center;
		font-size: 24upx;
		font-weight: 600;
		line-height: 32upx;
	}

	.date-picker-header-icon {
		width: 28upx;
		height: 28upx;
		margin-right: 8upx;
	}

	.date-picker-header-arrow {
		font-size: 22upx;
		line-height: 32upx;
	}

	.date-option {
		display: flex;
		align-items: center;
		justify-content: space-between;
		min-height: 0;
		padding: 15upx 10upx;
		border-bottom: none;
		background-color: transparent;
		box-sizing: border-box;
		color: $color-primary;
	}

	.date-option:active {
		background: var(--theme-primary-alpha-06, rgba(28, 102, 124, 0.06));
	}

	.date-options {
		display: flex;
		flex-direction: column;
		padding: 8upx 0;
	}

	.date-option-label {
		flex: 1;
		min-width: 0;
		overflow: hidden;
		color: $color-primary;
		font-size: 24upx;
		font-weight: 500;
		line-height: 32upx;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.date-radio {
		display: flex;
		align-items: center;
		justify-content: center;
		flex: 0 0 28upx;
		width: 28upx;
		height: 28upx;
		margin-left: 10upx;
		border: 2upx solid $color-primary;
		border-radius: 50%;
		background: transparent;
		box-sizing: border-box;
	}

	.date-radio-checked {
		border-color: $color-primary;
		background-color: transparent;
	}

	.date-radio-dot {
		width: 14upx;
		height: 14upx;
		border-radius: 50%;
		background-color: $color-primary;
	}

	.custom-date-panel {
		padding: 8upx 10upx 12upx;
		background-color: white;
		box-sizing: border-box;
	}

	.custom-date-row {
		margin-bottom: 0;
		padding: 15upx 10upx;
	}

	.custom-date-label {
		display: block;
		margin-bottom: 8upx;
		color: $color-primary;
		font-size: 24upx;
		font-weight: 500;
		line-height: 32upx;
	}

	.custom-date-input {
		display: flex;
		align-items: center;
		justify-content: space-between;
		min-height: 0;
		border: none;
		border-radius: 16upx;
		background-color: $bg-color-info;
		box-sizing: border-box;
	}

	.custom-date-text,
	.custom-date-placeholder {
		font-size: 24upx;
		line-height: 32upx;
		font-style: italic;
	}

	.custom-date-text {
		color: $color-primary;
	}

	.custom-date-placeholder {
		color: $text-color-secondary;
	}

	.custom-date-icon {
		width: 28upx;
		height: 28upx;
		margin-left: 10upx;
	}

	.custom-date-actions {
		display: flex;
		gap: 8upx;
		margin-top: 8upx;
	}

	.custom-btn {
		display: flex;
		align-items: center;
		justify-content: center;
		min-width: 0;
		min-height: 0;
		margin-left: 0;
		padding: 15upx 10upx;
		border-radius: 16upx;
		font-size: 24upx;
		font-weight: 500;
		line-height: 32upx;
		box-sizing: border-box;
	}

	.custom-btn-cancel {
		border: 2upx solid $color-primary;
		background-color: transparent;
		color: $color-primary;
	}

	.custom-btn-confirm {
		background-color: $color-primary;
		color: #fff;
	}

	.custom-btn-disabled {
		opacity: 0.5;
	}

	.calendar-panel {
		margin-top: 8upx;
		border: none;
		border-radius: 16upx;
		background-color: $bg-color-info;
		overflow: hidden;
	}

	.calendar-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		min-height: 40upx;
		padding: 0 10upx;
		background-color: $color-primary;
	}

	.calendar-title {
		color: #fff;
		font-size: 20upx;
		font-weight: 500;
		line-height: 28upx;
	}

	.calendar-nav-btn {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 28upx;
		height: 28upx;
		color: #fff;
		font-size: 22upx;
		line-height: 28upx;
	}

	.calendar-weekdays,
	.calendar-days {
		display: flex;
		flex-wrap: wrap;
	}

	.calendar-weekdays {
		padding: 8upx 4upx 2upx;
	}

	.calendar-weekday,
	.calendar-day {
		width: calc(100% / 7);
		text-align: center;
		box-sizing: border-box;
	}

	.calendar-weekday {
		color: $text-color-secondary;
		font-size: 20upx;
		line-height: 28upx;
	}

	.calendar-days {
		padding: 2upx 4upx 8upx;
	}

	.calendar-day {
		display: flex;
		align-items: center;
		justify-content: center;
		padding: 2upx 0;
		color: $color-primary;
		font-size: 20upx;
		line-height: 28upx;
	}

	.calendar-day text {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		width: 28upx;
		height: 28upx;
		border-radius: 50%;
	}

	.calendar-day-other {
		color: $text-color-secondary;
		opacity: 0.5;
	}

	.calendar-day-disabled {
		color: $text-color-secondary;
		opacity: 0.35;
	}

	.calendar-day-selected text {
		background-color: $color-primary;
		color: #fff;
	}

	.calendar-day-in-range text {
		background: var(--theme-primary-alpha-06, rgba(28, 102, 124, 0.06));
		color: $color-primary;
	}

	.date-range-picker {
		display: block;
	}

	.date-range-picker-inline {
		position: absolute;
		top: calc(100% + 8upx);
		left: 0;
		z-index: 30;
		width: 100%;
	}

	.date-picker-dropdown-layer {
		position: absolute;
		top: 0;
		left: 0;
		width: 100%;
	}

	.date-picker-dropdown-mask {
		position: fixed;
		top: 0;
		right: 0;
		bottom: 0;
		left: 0;
		z-index: 0;
	}

	.date-picker-dropdown {
		position: relative;
		z-index: 1;
		width: 100%;
		border-radius: 16upx;
		background-color: $bg-color-info;
		box-shadow: 0 6upx 20upx var(--theme-primary-alpha-18, rgba(28, 102, 124, 0.18));
		overflow: hidden;
	}

	.date-picker-dropdown .date-picker-header {
		min-height: 56upx;
		padding: 15upx 10upx;
		border-radius: 16upx 16upx 0 0;
	}

	.date-picker-dropdown .date-option {
		min-height: 0;
		padding: 15upx 10upx;
		border-bottom: none;
		background-color: transparent;
	}

	.date-picker-dropdown .date-option-label {
		color: $color-primary;
		font-size: 24upx;
		font-weight: bold;
		line-height: 32upx;
	}

	.date-picker-dropdown .date-radio {
		flex-basis: 28upx;
		width: 28upx;
		height: 28upx;
		margin-left: 10upx;
		border: 2upx solid $color-primary;
		background: transparent;
	}

	.date-picker-dropdown .date-radio-dot {
		width: 14upx;
		height: 14upx;
		background-color: $color-primary;
	}

	.date-picker-dropdown .date-radio.date-radio-checked {
		border-color: $color-primary;
		background-color: transparent;
	}

	.custom-modal-layer {
		position: fixed;
		top: 0;
		right: 0;
		bottom: 0;
		left: 0;
		z-index: 10000;
	}

	.custom-modal-mask {
		position: absolute;
		top: 0;
		right: 0;
		bottom: 0;
		left: 0;
		background-color: rgba(0, 0, 0, 0.5);
	}

	.custom-date-modal {
		position: absolute;
		top: 50%;
		left: 50%;
		width: calc(100% - 32upx);
		max-height: calc(100vh - 48upx);
		border-radius: $radius-large;
		background-color: none;
		transform: translate(-50%, -50%);
		overflow-y: auto;
	}

	.custom-modal-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		min-height: 56upx;
		padding: 15upx 30upx;
		background-color: $color-primary;
		color: #fff;
	}

	.custom-modal-title {
		font-size: 16px;
		font-weight: bold;
		line-height: 32upx;
	}

	.custom-modal-close {
		padding: 4upx;
		font-size: 22upx;
		font-weight: 400;
		line-height: 32upx;
	}

	.custom-date-modal .custom-date-panel {
		padding: 15px 15px;
	}

	.custom-date-modal .custom-date-row {
		margin-bottom: 0;
		padding: 15upx 10upx;
	}

	.custom-date-modal .custom-date-label {
		margin-bottom: 8upx;
		color: $color-primary;
		font-size: 24upx;
		font-weight: 500;
		line-height: 32upx;
	}

	.custom-date-modal .custom-date-input {
		min-height: 0;
		padding: 20upx 20upx;
		border: none;
		border-radius: 16upx;
		background-color: $bg-color-info;
	}

	.custom-date-modal .custom-date-text,
	.custom-date-modal .custom-date-placeholder {
		font-size: 24upx;
		font-weight: bold;
		line-height: 32upx;
	}

	.custom-date-modal .custom-date-text {
		color: $color-primary;
	}

	.custom-date-modal .custom-date-placeholder {
		color: $text-color-secondary;
	}

	.custom-date-modal .custom-date-icon {
		width: 28upx;
		height: 28upx;
		margin-left: 10upx;
	}

	.custom-date-modal .custom-date-actions {
		display: flex;
		gap: 8upx;
		margin-top: 8upx;
	}

	.custom-date-modal .custom-btn {
		flex: 1;
		min-width: 0;
		min-height: 0;
		margin-left: 0;
		padding: 15upx 10upx;
		border-radius: 16upx;
		font-size: 32upx;
		line-height: 32upx;
	}

	.custom-date-modal .custom-btn-cancel {
		border: 4upx solid $color-primary;
		background-color: transparent;
		color: #FF5341;
		font-weight: bold;
	}

	.custom-date-modal .custom-btn-confirm {
		background-color: $color-primary;
		color: #fff;
		font-weight: bold;
	}
</style>