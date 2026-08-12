<template>
	<scroll-view scroll-y class="dialog-wrapper" v-if="!hidden">
		<view style="background: none;">
			<view class="single-mask" @click="set_dialog_hide(true)"></view>
			<view class="text-bold flex-column" style="bottom: 0;position: fixed;">
				<view class=" flex-wrap padding-xs single-bottom dialig-bottom justify-start">
					<button class="button margin-tb-sm box-shadow" :class="{'mybg-primary':item.checked,}"
						@click="click(index)" v-for="(item,index) in date_arr" :key='index'>{{item.label}}</button>
				</view>
			</view>
		</view>
		</view>
	</scroll-view>
</template>

<script>
	export default {
		name: 'date-range-picker',
		props: {},
		data() {
			return {
				hidden: true,
				language:this.$config.language,
				date_arr: []

			}
		},
		methods: {
			set_dialog_hide(e) {
				this.hidden = e
				// this.$emit('update:hidden', e)
			},
			show() {
				this.hidden = false
			},
			click(index) {
				this.date_arr.forEach((ele, _index) => {
					ele.checked = index === _index
				})
				let result = this.date_arr[index]
				const {
					startDate,
					endDate
				} = this.getDateRange(result.value)
				// from tangjq--- 第三个参数传出预设 label（如 Today / Yesterday / Weekly 等），便于调用方直接显示
				this.$emit('click_option', [this.formatDate(startDate), this.formatDate(endDate)], result.label)
				this.set_dialog_hide(true)
			},
			formatDate(date) {
				const year = date.getFullYear();
				const month = String(date.getMonth() + 1).padStart(2, '0');
				const day = String(date.getDate()).padStart(2, '0');
				return {
					value:`${year}-${month}-${day}`,
					show:`${day}/${month}/${year}`,
				};
			},
			getDateRange(type) {
				const today = new Date();
				today.setHours(0, 0, 0, 0);
				let startDate, endDate;
				switch (type) {
					case 'today':
						startDate = new Date(today);
						endDate = new Date(today);
						break;
					case 'yesterday':
						startDate = new Date(today);
						startDate.setDate(today.getDate() - 1);
						endDate = new Date(startDate);
						break;
					case 'weekly':
						// 本周（周一为开始）
						startDate = new Date(today);
						startDate.setDate(today.getDate() - today.getDay() + (today.getDay() === 0 ? -6 : 1));
						endDate = new Date(today);
						break;
					case 'last_week':
						startDate = new Date(today);
						startDate.setDate(today.getDate() - today.getDay() - 6);
						endDate = new Date(startDate);
						endDate.setDate(startDate.getDate() + 6);
						break;
					case 'monthly':
						startDate = new Date(today.getFullYear(), today.getMonth(), 1);
						endDate = new Date(today);
						break;
					case 'last_month':
						startDate = new Date(today.getFullYear(), today.getMonth() - 1, 1);
						endDate = new Date(today.getFullYear(), today.getMonth(), 0);
						break;
					default:
						startDate = new Date(today);
						endDate = new Date(today);
				}

				return {
					startDate,
					endDate
				};
			},
		},
		created() {
			this.date_arr = ["today", "yesterday", "weekly", "last_week", "monthly", "last_month", ].map((ele, index) => {
				return {
					label: this.language[ele],
					checked: index === 0,
					value: ele,

				}
			})
		}
	}
</script>

<style lang="scss">
	.dialog-wrapper {
		z-index: 10000;
		// background-color: white;
		position: fixed;
		left: 0;
		bottom: 0;
		// height: calc(100vh - 55px);
		height: 100vh;
		width: 100vw;
		transform: none;
		transition: transform 225ms cubic-bezier(0, 0, 0.2, 1) 0ms;
	}

	.button {
		// width: 80%;    
		margin: 11px;
		padding: 5upx 16upx;
		border-radius: 25upx;
		font-size: 9px;
		width: calc(30% - 11px);
	}

	.box-shadow {
		box-shadow: rgba(60, 64, 67, 0.3) 0px 1px 2px 0px, rgba(60, 64, 67, 0.15) 0px 1px 3px 1px;
	}

	.dialig-bottom {
		background-color: white;
		display: flex;
		flex-direction: row;
		width: 100%;
	}


	.single-bottom {
		border-top-right-radius: 5vw;
		border-top-left-radius: 5vw;
	}

	.single-mask {
		background: none;
		height: 100vh;
		// filter: ;
		opacity: .5;
		background-color: black;
	}
</style>