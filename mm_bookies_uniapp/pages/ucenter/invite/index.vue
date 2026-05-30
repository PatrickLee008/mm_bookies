<template>
	<view class="bg-white full-page">
		<zw-header></zw-header>
		<scroll-view class="padding" scroll-y style="height: calc(100vh - 120px);">
			<view class="flex-row justify-start align-center" style="">
				<text class="cuIcon-back text-bold mycolor-primary margin-right-sm" @click="back_to()"></text>
				<image src="/static/icon/ucenter/invite.png" class="lblue2blue" style="height: 28px;" mode="heightFix">
				</image>
				<text class="title-text" style="">{{language.invite_friend}}</text>
			</view>
			<view class="flex-row justify-between text-black margin-top-sm" style="">
				<view class="dashboard-rec" style="background-color: #AECCF3;" @click="goto('./bonus_dashboard')">
					<text class="text-bold" style="">{{'Bonus Dashboard'}}</text>
					<view class="flex-row justify-between height-25px">
						<text class="text-bold" style="">{{summary.referrer_total_rewards}}</text>
						<text class="" style="">Ks</text>
					</view>
				</view>
				<view class="dashboard-rec" style="background-color: #FFEEC5;" @click="goto('./user_dashboard')">
					<text class="text-bold" style="">{{'User Dashboard'}}</text>
					<view class="flex-row justify-between height-22px">
						<text class="text-bold" style="">{{summary.total_invited_users}}</text>
						<text class="" style=""></text>
					</view>
				</view>
			</view>
			<view class="white-rec flex-column text-bold text-center" style="position: relative;">
				<text>{{ $t('invite_friend_rewarded') }}</text>
				<text class="cuIcon-infofill myfont-24px" style="position: absolute;top: 10px;right: 15px;"
					@click="modal_hidden=false"></text>
				<text
					class="myfont-10px line-height-13px">{{'Share your unique referral code with friends and earn rewards when they join and engage.'}}</text>
				<text class="myfont-10px margin-top-xs">{{'More benefits to come...'}}</text>
				<view class="flex-row justify-around margin-tb">
					<view class="rec-btn" style="border: dashed 3upx;" @click="copy">
						<view class="text-cut" style="max-width: 65%;"><text>{{userInfo.id}}</text></view>
						<view class="cuIcon-copy myfont-20px"></view>
					</view>
					<view class="rec-btn myfont-10px bg-black" style="" @click="goto('./share')">
						<text class="flex-column">{{'Invite Friends'}}</text>
					</view>
				</view>
			</view>
			<view v-for="(task,index) in task_list" :key="index">
				<view class="white-rec flex-row justify-between text-bold text-center"
					v-for="(progress,index_) in task.progress" :key="index_">
					<text class="myfont-12px line-height-13px text-left"
						style="max-width: 50%;">{{progress.activity_title}}</text>
					<view class="flex-row1 justify-between align-center" style="min-width: 50%;">
						<view></view>
						<view></view>
						<view class="flex-column1 align-center">
							<text
								class="myfont-10px line-height-13px mycolor-info">{{`${progress.rule_type=='invite_count'?progress.current_value:progress.current_value*progress.reward_amount}/${progress.threshold}`}}</text>
							<text
								class="myfont-17px line-height-17px margin-tb-xs">{{$toolbox.num_format(progress.reward_amount)}}</text>
						</view>
						<view class="flex-row1 justify-around">
							<!-- <text>{{`${progress.claimed_count}/${progress.max_claim_count?progress.max_claim_count:'-'}`}}</text> -->
							<view class="rec-btn myfont-10px" :class="progress.can_claim?'mybg-primary':'mybg-info'"
								style="border-color: rgba(0,0,0,0);width: 51px;height: 24px;"
								@click="progress.can_claim?get_bonus(progress,task):''">
								<text class="flex-column">{{'Claim'}}</text>
							</view>
						</view>
					</view>
				</view>
			</view>

		</scroll-view>
		<view class="cu-modal" style="z-index: 10;" :class="{'show':!modal_hidden,}" @click="modal_hidden=true">
			<view class="cu-dialog padding-lr-sm width-100"
				style="vertical-align: top;background: none;margin-top: 10vh;" @click.stop="">
				<!-- <view class="height-10vh"></view> -->
				<scroll-view scroll-y
					class="height-75vh bg-white radius-10px padding flex-column1 justify-start align-start text-black">
					<view class="flex-row justify-center myfont-24px text-bold">{{$t('Bonus Rules')}}</view>

					<view class="myfont-15px text-bold text-left">{{$t('Bonus Earnings for Invitation')}}</view>
					<view class="dashed-rec" style="">
						<view>{{$t('Inviters will be eligible to earn a bonus under the following conditions;')}}</view>
						<view class="margin-tb-sm">
							<text class="myfont-15px cuIcon-title margin-right-xs"></text>
							{{$t('The invitee must make their first deposit of at least 10,000 MMK')}}
						</view>
						<view class="margin-tb-xs">
							<text class="myfont-15px cuIcon-title margin-right-xs"></text>
							{{$t('The invitee must successfully deposit the minimum amount and place a bet of 1 MMK.')}}
						</view>
					</view>

					<view class="myfont-15px text-bold text-left">{{$t('Bonues Earnings for Turnover')}}</view>
					<view class="dashed-rec" style="">
						<view>{{$t("Inviters can earn bonuses based on the invitee's total turnover;")}}</view>
						<view class="margin-tb-sm">
							<text class="myfont-15px cuIcon-title margin-right-xs"></text>
							{{$t('10,000 MMK turnover -> 1,000 MMK Bonus')}}
						</view>
						<view class="margin-tb-sm">
							<text class="myfont-15px cuIcon-title margin-right-xs"></text>
							{{$t('25,000 MMK turnover -> 2,000 MMK Bonus')}}
						</view>
						<view class="margin-tb-sm">
							<text class="myfont-15px cuIcon-title margin-right-xs"></text>
							{{$t('50,000 MMK turnover -> 3,000 MMK Bonus')}}
						</view>
						<view class="margin-tb-sm">
							<text class="myfont-15px cuIcon-title margin-right-xs"></text>
							{{$t('100,000 MMK turnover-> 5,000 MMK Bonus')}}
						</view>
					</view>

					<view class="myfont-15px text-bold text-left">{{$t('Bonues Earnings for Turnover')}}</view>
					<view class="dashed-rec" style="">
						<view>{{$t("Inviters can earn bonuses based on the invitee's total turnover;")}}</view>
						<view class="margin-tb-sm">
							<text class="myfont-15px cuIcon-title margin-right-xs"></text>
							{{$t('1,000 MMK -> 10% (100MMK)')}}
						</view>
						<view class="margin-tb-sm">
							<text class="myfont-15px cuIcon-title margin-right-xs"></text>
							{{$t('10,000 MMK -> 15% (1,500MMK)')}}
						</view>
						<view class="margin-tb-sm">
							<text class="myfont-15px cuIcon-title margin-right-xs"></text>
							{{$t('100,000 MMK -> 20% (20,000MMK)')}}
						</view>
						<view class="margin-tb-sm">
							<text class="myfont-15px cuIcon-title margin-right-xs"></text>
							{{$t('500,000 MMK -> 15% (125,000MMK)')}}
						</view>
					</view>
				</scroll-view>
			</view>
		</view>

	</view>
</template>

<script>
	import language from '@/utils/language.js'
	import config from '@/utils/config.js'
	import uQRCode from '@/uni_modules/Sansnn-uQRCode/js_sdk/u-qrcode';

	export default {
		data() {
			return {
				language: config.language,
				userInfo: null,
				size: 165,
				share_url: '',
				modal_hidden: true,
				task_list: [{
					content: 'Invite first 10 friends',
					current_num: 1,
					max_num: 10,
					bonus: 5000,
					claim_disable: true,
					type: 'Invitation',
				}, {
					content: 'First Deposit of a user (min 5,000)',
					current_num: 0,
					max_num: '5,000',
					bonus: 5000,
					claim_disable: true,
					type: 'Deposit',
				}, {
					content: 'Turnover Commission for First 5,000 Bet Amount',
					current_num: 0,
					max_num: '5,000',
					bonus: 5000,
					claim_disable: true,
					type: 'Inviter Commission1',
				}, {
					content: 'Net Win Commission for First 5,000 Amount',
					current_num: 0,
					max_num: '5,000',
					bonus: 5000,
					claim_disable: true,
					type: 'Inviter Commission2',
				}, {
					content: 'Place 5,000 amount of bet and get 1,000 amount back',
					current_num: '5,000',
					max_num: '5,000',
					bonus: 5000,
					claim_disable: false,
					type: 'Invitee Bet Commission',
				}],
				summary: {
					total_invited_users: 0,
					total_claimable_reward: 0,
				}
			}
		},
		onLoad() {
			this.userInfo = Object.assign({}, this.$store.state.userInfo)
			this.get_activity()
			this.get_summary()
		},
		methods: {
			back_to() {
				uni.navigateBack({
					delta: 1,
				})
			},
			get_bonus(progress, task) {
				let _this = this
				console.log()
				_this.$http.post('/activity/rewards/claim', {
					"activity_id": task.id, // 活动ID (必填)
					"rule_id": progress.rule_id,
				}, res => {
					if (res.statusCode === 200 && res.data && res.data.code === 200) {
						_this.get_activity()
						_this.get_summary()
						uni.showModal({
							confirmText: 'OK',
							showCancel: false,
							title: this.$t('Congratulations'),
							content: `${this.$t('You have received a')} ${this.$toolbox.num_format(task.bonus)} ${this.$t('MMK reward for completing our task!')} \r\n ${this.$t('Keep up the good work!')}`
						})
					} else {
						uni.showModal({
							title: this.$t('tips'),
							content: res.data.message,
							confirmText: this.$t('ok'),
							showCancel: false
						})
					}
				});
			},
			copy() {
				const _this = this
				uni.setClipboardData({
					data: _this.userInfo.id,
					success: function() {
						uni.showToast({
							title: _this.$t('copied_to_clipboard'),
							icon: 'success'
						});
					},
					fail: function() {
						// uni.showToast({
						//   title: '复制失败',
						//   icon: 'none'
						// });
					}
				});

			},
			goto(url) {
				uni.navigateTo({
					url: url
				})
			},
			get_activity() {
				var _this = this;
				_this.$http.get('/activity/activities_with_progress', {}, (res) => {
					if (res.statusCode == 200) {
						_this.task_list = res.data.data.activities
						// console.log(_this.userInfo.money)

					}
				})
			},
			get_summary() {
				var _this = this;
				_this.$http.get('/activity/rewards/total-summary', {}, (res) => {
					if (res.statusCode == 200) {
						_this.summary = res.data.data.summary
						// console.log(_this.userInfo.money)

					}
				})
			},

		}
	}
</script>

<style lang="scss">
	.white-rec {
		display: flex;
		align-items: center;
		box-shadow: 0px 3px 4px 0px #00000040;
		border: 1px solid #00000040;
		padding: 10px 20px;
		width: 100%;
		border-radius: 10px;
		margin: 10px 0;
		color: black;
	}

	.copy-rec {
		width: 95%;
		margin-left: 2.5%;
		transition: box-shadow 300ms cubic-bezier(0.4, 0, 0.2, 1) 0ms;
		border-radius: 4px;
		box-shadow: 0px 2px 1px -1px rgba(0, 0, 0, 0.2), 0px 1px 1px 0px rgba(0, 0, 0, 0.14), 0px 1px 3px 0px rgba(0, 0, 0, 0.12);
		overflow: hidden;
		background-color: rgb(237, 236, 241);
		text-align: center;
		-webkit-box-align: center;
		align-items: center;
		box-shadow: rgba(0, 0, 0, 0.15) 0px 2px 3px 0px;
		padding: 15px 15px;
	}

	.dashboard-rec {
		display: flex;
		flex-direction: column;
		align-items: start;
		box-shadow: 0px 4px 4px 0px #00000040;
		padding: 10px 20px;
		width: 49%;
		border-radius: 10px;
	}

	.rec-btn {
		border: 1px solid black;
		height: 40px;
		width: 115px;
		border-radius: 20px;
		padding: 0 10px;
		display: flex;
		flex-direction: row;
		align-items: center;
		justify-content: space-between;
	}

	.dashed-rec {
		border: 1px dashed #00000080;
		width: 100%;
		text-align: start;
		font-size: 13px;
		padding: 10px 5px;
		line-height: 1.3;
	}
</style>