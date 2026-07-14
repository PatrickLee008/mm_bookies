<template>
	<view class="bg-white full-page">
		<zw-header></zw-header>
		<scroll-view class="padding" scroll-y style="height: calc(100vh - 120px);">
			<!-- 标题 -->
			<view class="flex-row justify-start align-center" style="">
				<text class="cuIcon-back text-bold mycolor-primary margin-right-sm" @click="back_to()"></text>
				<image src="/static/icon/ucenter/invite.png" class="lblue2blue" style="height: 28px;" mode="heightFix">
				</image>
				<text class="title-text" style="">{{ language.invite_friend }}</text>
			</view>

			<!-- 两个仪表盘入口 -->
			<view class="flex-row justify-between text-black margin-top-sm" style="">
				<view class="dashboard-rec dashboard-bonus" @click="goto('./bonus_dashboard')">
					<text class="text-bold myfont-12px">{{ $t('Bonus Dashboard') }}</text>
					<view class="flex-row justify-between align-center height-22px">
						<text class="text-bold myfont-16px">{{ $toolbox.num_format(summary.referrer_total_rewards || 0) }}</text>
						<text class="myfont-10px">Ks</text>
					</view>
				</view>
				<view class="dashboard-rec dashboard-user" @click="goto('./user_dashboard')">
					<text class="text-bold myfont-12px">{{ $t('User Dashboard') }}</text>
					<view class="flex-row justify-between align-center height-22px">
						<text class="text-bold myfont-16px">{{ summary.total_invited_users || 0 }}</text>
						<text class="myfont-10px"></text>
					</view>
				</view>
			</view>

			<!-- 推荐码卡片 -->
			<view class="white-rec flex-column text-bold text-center" style="position: relative;">
				<text>{{ $t('Invite a friend and get rewarded') }}</text>
				<text class="myfont-10px line-height-13px mycolor-info">{{ $t('Share your unique referral code') }}</text>
				<view class="flex-row justify-around margin-tb">
					<view class="rec-btn" style="border: dashed 3upx;" @click="copy">
						<view class="text-cut" style="max-width: 70%;"><text>{{ userInfo ? userInfo.r_code : '' }}</text></view>
						<view class="cuIcon-copy myfont-20px mycolor-primary"></view>
					</view>
					<view class="rec-btn myfont-12px mybg-primary text-white"
						@click="goto(`./share?r_code=${userInfo ? userInfo.r_code : ''}`)">
						<text class="flex-column">{{ $t('Invite Friends') }}</text>
					</view>
				</view>
			</view>

			<!-- 活动列表 -->
			<view v-for="(activity, activityIndex) in task_list" :key="activityIndex">
				<!-- 活动标题卡片 -->
				<view class="activity-title-card" style="position: relative;">
					<text class="cuIcon-infofill myfont-20px mycolor-primary"
						style="position: absolute;right: 12px;top:12px" @click="openRulesModal(activity.id)"></text>
					<view class="flex-row1 align-center" style="padding-right: 30px;">
						<text class="cuIcon-rankfill myfont-20px mycolor-primary margin-right-sm"></text>
						<text class="myfont-16px text-bold" style="line-height: 1.6;">{{ activity.title }}</text>
					</view>
					<view class="flex-row justify-between align-center margin-top-xs">
						<text class="myfont-10px mycolor-info">
							{{ formatDate(activity.start_date) }} - {{ formatDate(activity.end_date) }}
						</text>
						<view class="activity-status-badge" :class="activity.is_valid ? 'status-active' : 'status-inactive'">
							<text class="myfont-10px">{{ activity.is_valid ? $t('Active') : $t('Ended') }}</text>
						</view>
					</view>

					<view class="flex-row justify-around margin-top-sm" v-if="activity.summary">
						<view class="flex-column1 align-center">
							<text class="myfont-10px mycolor-info">{{ $t('Total Claimable') }}</text>
							<text class="myfont-14px text-bold mycolor-warning">
								{{ $toolbox.num_format(activity.summary.total_claimable || 0) }} Ks
							</text>
						</view>
						<view class="flex-column1 align-center">
							<text class="myfont-10px mycolor-info">{{ $t('Total Claimed') }}</text>
							<text class="myfont-14px text-bold mycolor-success">
								{{ $toolbox.num_format(activity.summary.total_rewards_claimed || 0) }} Ks
							</text>
						</view>
					</view>

					<view class="flex-row justify-center margin-top-sm">
						<view v-if="activity.has_joined" class="participate-badge participated">
							<text class="cuIcon-check myfont-14px margin-right-xs"></text>
							<text class="myfont-12px">{{ $t('Participated') }}</text>
						</view>
						<view v-else-if="activity.is_valid" class="participate-btn" @click="joinActivity(activity)">
							<text class="cuIcon-add myfont-14px margin-right-xs"></text>
							<text class="myfont-12px text-bold">{{ $t('Join Activity') }}</text>
						</view>
					</view>
				</view>

				<!-- Method 1.1: 成就规则奖励 -->
				<view v-if="activity.method1 && activity.method1.achievement_rules && activity.method1.achievement_rules.length > 0">
					<view class="white-rec flex-column1" style="padding: 8px;align-items: start;">
						<view class="method-title">
							<text class="cuIcon-friend margin-right-xs"></text>
							<text>{{ $t('Invitation Achievement') }}</text>
						</view>
						<view class="inner-rec flex-row justify-between text-bold text-center"
							v-for="(rule, ruleIndex) in activity.method1.achievement_rules" :key="rule.rule_id">
							<text class="myfont-12px line-height-13px text-left" style="max-width: 50%;">
								{{ rule.description || rule.rule_type }}
							</text>
							<view class="flex-row1 justify-between align-center" style="min-width: 50%;">
								<view class="flex-column1 align-center">
									<text class="myfont-10px line-height-13px mycolor-info">
										{{ `${rule.current_value}/${rule.threshold}` }}
									</text>
									<text class="myfont-17px line-height-17px margin-top-xs mycolor-primary">
										{{ $toolbox.num_format(rule.reward_amount) }}
									</text>
									<text class="myfont-9px mycolor-info" v-if="rule.max_claim_count">
										{{ `${rule.claimed_count}/${rule.max_claim_count} ${$t('claimed')}` }}
									</text>
								</view>
								<view class="flex-row1 justify-around margin-left-sm">
									<view class="rec-btn-sm" :class="rule.can_claim ? 'mybg-primary text-white' : 'mybg-info'"
										@click="rule.can_claim ? claimAchievementReward(activity, rule) : ''">
										<text>{{ $t('Claim') }}</text>
									</view>
								</view>
							</view>
						</view>
					</view>
				</view>

				<!-- Method 1.2: 一次性邀请奖励 -->
				<view v-if="activity.method1 && activity.method1.invitation_share">
					<view class="white-rec flex-column1" style="padding: 8px;align-items: start;">
						<view class="method-title">
							<text class="cuIcon-share myfont-16px margin-right-xs"></text>
							<text>{{ $t('Invitation Share') }}</text>
						</view>
						<view class="inner-rec flex-row justify-between text-bold text-center">
							<view class="flex-column1 text-left" style="max-width: 60%;">
								<text class="myfont-12px line-height-13px">{{ $t('One-time Invitation Reward') }}</text>
								<view class="flex-row1 align-center margin-top-xs" style="font-size: 11px;">
									<text class="mycolor-info">{{ $t('Qualified Invitees') }}: </text>
									<text :class="activity.method1.invitation_share.qualified_invitees > 0 ? 'mycolor-success' : 'mycolor-info'">
										{{ activity.method1.invitation_share.qualified_invitees || 0 }}
									</text>
									<text class="margin-left-xs mycolor-info"
										v-if="activity.method1.invitation_share.qualified_invitees > 0">
										× {{ $toolbox.num_format(activity.method1.invitation_share.one_time_bonus) }} Ks
									</text>
								</view>
							</view>
							<view class="flex-row1 justify-end align-center" style="min-width: 40%;">
								<view class="flex-column1 align-center">
									<text class="myfont-17px line-height-17px mycolor-primary">
										{{ $toolbox.num_format(activity.method1.invitation_share.potential_rewards || 0) }}
									</text>
									<text class="myfont-9px mycolor-info" style="margin-top: 2px;">Ks</text>
								</view>
								<view class="flex-row1 justify-around margin-left-sm">
									<view class="rec-btn-sm"
										:class="activity.method1.invitation_share.can_claim ? 'mybg-primary text-white' : 'mybg-info'"
										@click="activity.method1.invitation_share.can_claim ? claimOneTimeReward(activity) : ''">
										<text>{{ $t('Claim') }}</text>
									</view>
								</view>
							</view>
						</view>
						<view class="requirement-hint">
							<text class="myfont-9px">
								{{ $t('Requirements') }}: {{ $t('Deposit') }}
								≥{{ $toolbox.num_format(activity.method1.invitation_share.min_deposit) }} Ks,
								{{ $t('Turnover') }}
								≥{{ $toolbox.num_format(activity.method1.invitation_share.min_turnover) }} Ks
							</text>
						</view>
					</view>
				</view>

				<!-- Method 2: 存款分享 -->
				<view v-if="activity.method2 && activity.method2.deposit_share_tiers && activity.method2.deposit_share_tiers.length > 0">
					<view class="white-rec flex-column1" style="padding: 8px;align-items: start;">
						<view class="method-title">
							<text class="cuIcon-moneybag myfont-16px margin-right-xs"></text>
							<text>{{ $t('Deposit Share') }}</text>
						</view>
						<view class="inner-rec flex-row justify-between text-bold text-center"
							v-for="(tier, tierIndex) in activity.method2.deposit_share_tiers" :key="tierIndex">
							<view class="flex-column1 text-left" style="max-width: 60%;">
								<text class="myfont-12px line-height-13px">{{ tier.description }}</text>
								<text class="myfont-9px mycolor-info">
									{{ $t('Claimed') }}:
									{{ tier.triggered_count }}{{ tier.max_claims > 0 ? ' / ' + tier.max_claims : '' }}
									{{ $t('times') }}
								</text>
								<text class="myfont-9px mycolor-warning margin-top-xs" v-if="tier.claimable_count > 0">
									{{ $t('Claimable') }}: {{ tier.claimable_count }} {{ $t('times') }}
								</text>
							</view>
							<view class="flex-row1 justify-end align-center" style="min-width: 40%;">
								<view class="flex-column1 align-center">
									<text class="myfont-10px line-height-13px mycolor-info">{{ tier.bonus_rate }}%</text>
									<text class="myfont-17px line-height-17px margin-tb-xs mycolor-primary">
										{{ $toolbox.num_format(tier.claimable_amount || 0) }}
									</text>
								</view>
							</view>
						</view>
						<view class="summary-rec flex-row justify-between align-center">
							<view class="flex-column1 align-start">
								<text>{{ $t('Total Deposit Share Rewards') }}: </text>
								<text class="text-bold">{{ $toolbox.num_format(activity.method2.total_rewards) }} Ks</text>
								<text class="myfont-9px margin-top-xs" style="color:#FFD98A;" v-if="activity.method2.can_claim">
									{{ $t('Claimable') }}: {{ $toolbox.num_format(activity.method2.total_claimable_amount) }} Ks
								</text>
							</view>
							<view class="rec-btn-sm"
								:class="activity.method2.can_claim ? 'bg-white mycolor-primary text-bold' : 'mybg-info'"
								@click="activity.method2.can_claim ? claimDepositShareReward(activity) : ''">
								<text>{{ $t('Claim') }}</text>
							</view>
						</view>
					</view>
				</view>

				<!-- Method 3: 邀请人佣金 -->
				<view v-if="activity.method3 && activity.method3.commission_stats">
					<view class="method-title">
						<text class="cuIcon-fork myfont-16px margin-right-xs"></text>
						<text>{{ $t('Inviter Commission') }}</text>
					</view>
					<view class="white-rec flex-column text-bold" style="align-items: flex-start;">
						<view class="flex-row justify-between align-center" style="width: 100%;">
							<text class="myfont-12px">{{ $t('Commission from Invitee Deposits/Turnover') }}</text>
							<text class="myfont-17px mycolor-primary">
								{{ $toolbox.num_format(activity.method3.commission_stats.total) }} Ks
							</text>
						</view>
						<view class="flex-row justify-between margin-top-sm" style="width: 100%; font-size: 11px;">
							<view class="flex-column1 align-center">
								<text class="mycolor-info">{{ $t('Pending') }}</text>
								<text class="mycolor-warning text-bold">{{ $toolbox.num_format(activity.method3.commission_stats.pending) }} Ks</text>
							</view>
							<view class="flex-column1 align-center">
								<text class="mycolor-info">{{ $t('Paid') }}</text>
								<text class="mycolor-success text-bold">{{ $toolbox.num_format(activity.method3.commission_stats.paid) }} Ks</text>
							</view>
							<view class="flex-column1 align-center">
								<text class="mycolor-info">{{ $t('Rate') }}</text>
								<text class="text-bold">{{ activity.method3.config.commission_rate }}%</text>
							</view>
						</view>
					</view>
				</view>

				<!-- Method 4: 被邀请人投注佣金 -->
				<view v-if="activity.method4 && activity.method4.commission_stats">
					<view class="method-title">
						<text class="cuIcon-redpacket myfont-16px margin-right-xs"></text>
						<text>{{ $t('Invitee Bet Commission') }}</text>
					</view>
					<view class="white-rec flex-column text-bold" style="align-items: flex-start;">
						<view class="flex-row justify-between align-center" style="width: 100%;">
							<text class="myfont-12px">{{ $t('Commission from Invitee Betting') }}</text>
							<text class="myfont-17px mycolor-primary">
								{{ $toolbox.num_format(activity.method4.commission_stats.total) }} Ks
							</text>
						</view>
						<view class="flex-row justify-between margin-top-sm" style="width: 100%; font-size: 11px;">
							<view class="flex-column1 align-center">
								<text class="mycolor-info">{{ $t('Pending') }}</text>
								<text class="mycolor-warning text-bold">{{ $toolbox.num_format(activity.method4.commission_stats.pending) }} Ks</text>
							</view>
							<view class="flex-column1 align-center">
								<text class="mycolor-info">{{ $t('Paid') }}</text>
								<text class="mycolor-success text-bold">{{ $toolbox.num_format(activity.method4.commission_stats.paid) }} Ks</text>
							</view>
							<view class="flex-column1 align-center">
								<text class="mycolor-info">{{ $t('Rate') }}</text>
								<text class="text-bold">{{ activity.method4.config.commission_rate }}%</text>
							</view>
						</view>
					</view>
				</view>
			</view>

			<view style="height: 30px; width: 100%;"></view>
		</scroll-view>

		<!-- 规则弹窗 -->
		<view class="cu-modal" style="z-index: 10;" :class="{ 'show': !modal_hidden }" @click="modal_hidden = true">
			<view class="cu-dialog padding-lr-sm width-100" style="vertical-align: top;background: none;margin-top: 10vh;"
				@click.stop="">
				<scroll-view scroll-y
					class="height-75vh bg-white radius-10px padding flex-column1 justify-start align-start text-black">
					<view v-if="loadingRules" class="flex-column justify-center align-center" style="width:100%;margin-top: 50px;">
						<text class="cuIcon-loading2 cuIconfont-spin mycolor-primary" style="font-size: 40px;"></text>
						<text class="myfont-14px mycolor-info margin-top-sm">{{ $t('Loading') }}...</text>
					</view>

					<view v-else-if="rulesData" style="width:100%;">
						<view class="flex-row justify-center myfont-20px text-bold margin-bottom">
							{{ rulesData.activity_title || $t('Activity Rules') }}
						</view>
						<view class="info-section margin-bottom">
							<text class="myfont-12px mycolor-info">{{ rulesData.activity_description }}</text>
							<view class="flex-row justify-between margin-top-xs myfont-10px mycolor-info">
								<text>{{ formatDate(rulesData.start_date) }} - {{ formatDate(rulesData.end_date) }}</text>
							</view>
						</view>

						<view v-if="rulesData.method1 && rulesData.method1.enabled" class="margin-bottom-sm">
							<view class="myfont-15px text-bold text-left mycolor-primary">
								<text class="cuIcon-friendfill margin-right-xs"></text>
								{{ $t('Invitation & Achievement Share') }}
							</view>
							<view class="dashed-rec">
								<view class="margin-bottom-sm">
									<text class="text-bold">{{ $t('One-Time Bonus') }}:</text>
									<text class="mycolor-warning"> {{ $toolbox.num_format(rulesData.method1.one_time_bonus) }} Ks</text>
								</view>
								<view class="margin-bottom-xs myfont-12px">
									<text class="cuIcon-title margin-right-xs"></text>
									{{ $t('Min Deposit') }}: {{ $toolbox.num_format(rulesData.method1.min_deposit) }} Ks
								</view>
								<view class="margin-bottom-xs myfont-12px">
									<text class="cuIcon-title margin-right-xs"></text>
									{{ $t('Min Turnover') }}: {{ $toolbox.num_format(rulesData.method1.min_turnover) }} Ks
								</view>
								<view v-if="rulesData.method1.achievement_rules && rulesData.method1.achievement_rules.length > 0"
									class="margin-top-sm">
									<text class="text-bold">{{ $t('Achievement Rewards') }}:</text>
									<view v-for="(rule, index) in rulesData.method1.achievement_rules" :key="index"
										class="margin-tb-xs myfont-12px">
										<text class="cuIcon-rankfill margin-right-xs mycolor-warning"></text>
										{{ $t('Invite') }} {{ rule.threshold_value }} {{ $t('people') }} →
										{{ $toolbox.num_format(rule.reward_amount) }} Ks
										<text v-if="rule.max_claim_count > 0" class="mycolor-info"> ({{ $t('Max') }} {{ rule.max_claim_count }}x)</text>
									</view>
								</view>
							</view>
						</view>

						<view v-if="rulesData.method2 && rulesData.method2.enabled" class="margin-bottom-sm">
							<view class="myfont-15px text-bold text-left mycolor-primary">
								<text class="cuIcon-moneybag margin-right-xs"></text>
								{{ $t('Deposit Share') }}
							</view>
							<view class="dashed-rec">
								<view class="margin-bottom-xs myfont-12px">
									{{ $t('Earn a percentage of your invitees deposits based on tier ranges') }}
								</view>
								<view v-for="(tier, index) in rulesData.method2.deposit_tiers" :key="index" class="margin-tb-xs myfont-12px">
									<text class="cuIcon-title margin-right-xs"></text>
									{{ $toolbox.num_format(tier.min_deposit) }} -
									{{ tier.max_deposit ? $toolbox.num_format(tier.max_deposit) : '∞' }} Ks
									→ <text class="text-bold mycolor-success">{{ tier.bonus_rate }}%</text>
									<text v-if="tier.max_claims > 0" class="mycolor-info"> ({{ $t('Max') }} {{ tier.max_claims }}x)</text>
								</view>
							</view>
						</view>

						<view v-if="rulesData.method3 && rulesData.method3.enabled" class="margin-bottom-sm">
							<view class="myfont-15px text-bold text-left mycolor-primary">
								<text class="cuIcon-fork margin-right-xs"></text>
								{{ $t('Inviter Commission') }}
							</view>
							<view class="dashed-rec">
								<view class="margin-bottom-xs myfont-12px">
									<text class="cuIcon-title margin-right-xs"></text>
									{{ $t('Type') }}:
									{{ rulesData.method3.commission_type === 'turnover' ? $t('Based on Turnover') : $t('Based on Win/Loss') }}
								</view>
								<view class="margin-bottom-xs myfont-12px">
									<text class="cuIcon-title margin-right-xs"></text>
									{{ $t('Rate') }}: <text class="text-bold mycolor-warning">{{ rulesData.method3.commission_rate }}%</text>
								</view>
								<view class="myfont-12px">
									<text class="cuIcon-title margin-right-xs"></text>
									{{ $t('Settlement') }}: {{ formatFrequency(rulesData.method3.settlement_frequency) }}
								</view>
							</view>
						</view>

						<view v-if="rulesData.method4 && rulesData.method4.enabled" class="margin-bottom-sm">
							<view class="myfont-15px text-bold text-left mycolor-primary">
								<text class="cuIcon-redpacket margin-right-xs"></text>
								{{ $t('Invitee Bet Commission') }}
							</view>
							<view class="dashed-rec">
								<view class="margin-bottom-xs myfont-12px mycolor-warning">
									⚠️ {{ $t('This commission goes to INVITEE (not inviter)!') }}
								</view>
								<view class="myfont-12px">
									<text class="cuIcon-title margin-right-xs"></text>
									{{ $t('Commission Rate') }}: <text class="text-bold mycolor-warning">{{ rulesData.method4.rebate_rate }}%</text>
								</view>
							</view>
						</view>
					</view>

					<view v-else class="flex-column justify-center align-center" style="width:100%;margin-top: 50px;">
						<text class="cuIcon-roundclosefill myfont-40px mycolor-warning"></text>
						<text class="myfont-14px mycolor-info margin-top-sm">{{ $t('Failed to load rules') }}</text>
					</view>
				</scroll-view>
			</view>
		</view>
	</view>
</template>

<script>
	import config from '@/utils/config.js'

	export default {
		data() {
			return {
				language: config.language,
				userInfo: null,
				modal_hidden: true,
				task_list: [],
				summary: {
					referrer_total_rewards: 0,
					total_invited_users: 0,
					total_claimable_reward: 0,
				},
				loadingRules: false,
				rulesData: null,
			}
		},
		onLoad() {
			this.userInfo = Object.assign({}, this.$store.state.userInfo)
			this.getUserInfo()
			this.get_activity()
			this.get_summary()
		},
		methods: {
			back_to() {
				uni.navigateBack({ delta: 1 })
			},
			goto(url) {
				uni.navigateTo({ url })
			},
			// 本地日期格式化（本项目 $toolbox 无 formatDateTime）
			formatDate(dateStr, sep = '/') {
				if (!dateStr) return '--'
				let d = String(dateStr).split(' ')[0].split('-')
				if (d.length < 3) return String(dateStr)
				return `${d[0]}${sep}${d[1]}${sep}${d[2]}`
			},
			formatFrequency(freq) {
				const map = {
					'weekly': this.$t('Weekly'),
					'monthly': this.$t('Monthly'),
					'manual': this.$t('Manual')
				}
				return map[freq] || freq
			},
			getUserInfo() {
				let _this = this
				if (!uni.getStorageSync('Authorization')) return
				_this.$http.get('/app_user/user_info', {}, (res) => {
					if (res.statusCode === 200 && res.data && res.data.data) {
						_this.$store.dispatch('saveUserInfo', res.data.data)
						_this.userInfo = res.data.data
					}
				})
			},
			get_activity() {
				let _this = this
				_this.$http.get('/invitation_v2/list', {}, (res) => {
					if (res.statusCode === 200 && res.data.code === 200) {
						_this.task_list = res.data.data.activities || []
					}
				})
			},
			get_summary() {
				let _this = this
				_this.$http.get('/invitation_v2/total-summary', {}, (res) => {
					if (res.statusCode === 200 && res.data.code === 200) {
						_this.summary = res.data.data.summary || _this.summary
					}
				})
			},
			copy() {
				let _this = this
				let code = _this.userInfo && _this.userInfo.r_code
				if (!code) return
				uni.setClipboardData({
					data: code,
					success: () => uni.showToast({ title: _this.$t('copied_to_clipboard'), icon: 'success' })
				})
			},
			openRulesModal(activityId) {
				if (!activityId) return
				this.loadRulesData(activityId)
			},
			loadRulesData(activityId) {
				let _this = this
				_this.loadingRules = true
				_this.rulesData = null
				_this.modal_hidden = false
				_this.$http.get(`/invitation_v2/rules-detail/${activityId}`, {}, (res) => {
					_this.loadingRules = false
					if (res.statusCode === 200 && res.data.code === 200) {
						_this.rulesData = res.data.data
					} else {
						_this.rulesData = null
						uni.showToast({ title: res.data.message || _this.$t('Failed to load rules'), icon: 'none' })
					}
				}, () => {
					_this.loadingRules = false
					_this.rulesData = null
				})
			},
			// 参与活动
			joinActivity(activity) {
				let _this = this
				if (!activity.is_valid) {
					uni.showToast({ title: _this.$t('Activity has ended'), icon: 'none' })
					return
				}
				if (activity.has_joined) {
					uni.showToast({ title: _this.$t('Already participated'), icon: 'none' })
					return
				}
				uni.showModal({
					title: _this.$t('Join Activity'),
					content: _this.$t('Do you want to participate in this invitation activity.'),
					confirmText: _this.$t('Confirm'),
					cancelText: _this.$t('Cancel'),
					success: (r) => {
						if (!r.confirm) return
						_this.$http.post('/invitation_v2/join-activity', { activity_id: activity.id }, (res) => {
							if (res.statusCode === 200 && res.data.code === 200) {
								uni.showModal({
									title: _this.$t('Success'),
									content: _this.$t('Successfully joined the invitation activity!'),
									showCancel: false,
									confirmText: _this.$t('ok')
								})
								_this.get_activity()
							} else {
								_this.alertMsg(res.data.message || _this.$t('Failed to join activity'))
							}
						})
					}
				})
			},
			// 统一失败提示（尝试 i18n）
			alertMsg(content) {
				let translated = this.$t(content)
				uni.showModal({
					title: this.$t('tips'),
					content: translated || content,
					showCancel: false,
					confirmText: this.$t('ok')
				})
			},
			// 领取前需已参与
			ensureJoined(activity) {
				if (!activity.has_joined) {
					this.alertMsg(this.$t('Please join this activity first before claiming rewards.'))
					return false
				}
				return true
			},
			refreshAfterClaim() {
				this.get_activity()
				this.get_summary()
				this.getUserInfo()
			},
			// Method 1.1
			claimAchievementReward(activity, rule) {
				let _this = this
				if (!_this.ensureJoined(activity)) return
				_this.$http.post('/invitation_v2/claim-achievement-reward', {
					activity_id: activity.id,
					rule_id: rule.rule_id,
				}, (res) => {
					if (res.statusCode === 200 && res.data && res.data.code === 200) {
						_this.refreshAfterClaim()
						uni.showModal({
							title: _this.$t('Congratulations'),
							content: `${_this.$t('You have received a')} ${_this.$toolbox.num_format(rule.reward_amount)} ${_this.$t('MMK reward for completing our task!')}`,
							showCancel: false,
							confirmText: _this.$t('Confirm')
						})
					} else {
						_this.alertMsg(res.data.message)
					}
				})
			},
			// Method 1.2
			claimOneTimeReward(activity) {
				let _this = this
				if (!_this.ensureJoined(activity)) return
				_this.$http.post('/invitation_v2/claim-one-time-reward', {
					activity_id: activity.id
				}, (res) => {
					if (res.statusCode === 200 && res.data && res.data.code === 200) {
						_this.refreshAfterClaim()
						const data = res.data.data || {}
						uni.showModal({
							title: _this.$t('Congratulations'),
							content: `${_this.$t('You have received a')} ${_this.$toolbox.num_format(data.total_reward_amount)} Ks`,
							showCancel: false,
							confirmText: _this.$t('Confirm')
						})
					} else {
						_this.alertMsg(res.data.message)
					}
				})
			},
			// Method 2
			claimDepositShareReward(activity) {
				let _this = this
				if (!_this.ensureJoined(activity)) return
				_this.$http.post('/invitation_v2/claim-deposit-share-reward', {
					activity_id: activity.id
				}, (res) => {
					if (res.statusCode === 200 && res.data && res.data.code === 200) {
						_this.refreshAfterClaim()
						const data = res.data.data || {}
						uni.showModal({
							title: _this.$t('Congratulations'),
							content: `${_this.$t('You have received a')} ${_this.$toolbox.num_format(data.total_reward_amount)} Ks`,
							showCancel: false,
							confirmText: _this.$t('Confirm')
						})
					} else {
						_this.alertMsg(res.data.message)
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

	.inner-rec {
		display: flex;
		align-items: center;
		border: 1px solid #0000001A;
		padding: 8px 20px;
		width: 100%;
		border-radius: 8px;
		margin: 10px 0 0;
		color: black;
	}

	.dashboard-rec {
		display: flex;
		flex-direction: column;
		align-items: start;
		box-shadow: 0px 4px 4px 0px #00000040;
		padding: 10px 4vw;
		width: 49%;
		border-radius: 10px;
		color: #1e3a3f;
	}

	.dashboard-bonus {
		background-color: #cfe6e8;
	}

	.dashboard-user {
		background-color: #e8f4f8;
	}

	.rec-btn {
		border: 1px solid $color-primary;
		height: 40px;
		width: 115px;
		border-radius: 20px;
		padding: 0 10px;
		display: flex;
		flex-direction: row;
		align-items: center;
		justify-content: space-between;
	}

	.rec-btn-sm {
		width: 56px;
		height: 26px;
		border-radius: 13px;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 11px;
		font-weight: bold;
	}

	.dashed-rec {
		border: 1px dashed #00000080;
		width: 100%;
		text-align: start;
		font-size: 13px;
		padding: 10px 5px;
		line-height: 1.3;
	}

	.method-title {
		display: flex;
		align-items: center;
		font-weight: bold;
		font-size: 16px;
		color: $color-primary;
		padding-left: 5px;
		margin: 5px;
	}

	.requirement-hint {
		width: 100%;
		background: #fff3cd;
		padding: 8px;
		border-radius: 5px;
		margin-top: 6px;
		color: #856404;
	}

	.summary-rec {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 8px 20px;
		margin: 12px 0 0;
		background: #2F5D62;
		border-radius: 8px;
		color: white;
		font-size: 13px;
		width: 100%;
	}

	.activity-title-card {
		box-shadow: 0px 3px 4px 0px #00000040;
		border: 1px solid #00000040;
		padding: 10px 20px;
		width: 100%;
		border-radius: 10px;
		margin: 10px 0;
		color: #2F5D62;
	}

	.activity-status-badge {
		padding: 2px 12px;
		border-radius: 8px;
		font-size: 11px;
		font-weight: bold;
	}

	.status-active {
		background-color: #d4edda;
		color: #155724;
	}

	.status-inactive {
		background-color: #f8d7da;
		color: #721c24;
	}

	.info-section {
		padding: 10px;
		background: #f0f6f7;
		border-radius: 8px;
	}

	.participate-btn {
		display: flex;
		flex-direction: row;
		align-items: center;
		justify-content: center;
		background: #2F5D62;
		color: white;
		padding: 8px 20px;
		margin-bottom: 5px;
		border-radius: 20px;
		box-shadow: 0px 3px 6px rgba(47, 93, 98, 0.4);
	}

	.participate-badge {
		display: flex;
		flex-direction: row;
		align-items: center;
		justify-content: center;
		padding: 6px 16px;
		border-radius: 20px;
		font-size: 12px;
	}

	.participate-badge.participated {
		background-color: #d4edda;
		color: #155724;
		border: 1px solid #c3e6cb;
	}
</style>
