<template>
	<view class="mybg-grey page" :style="{'height':calc_page_height,}">
		<zw-header>
			<block slot="right">
				<view class="flex-row justify-center width-20vw gap-10px mycolor-primary">
					<view class="margin-top-20upx" style="position: relative;">
						<image mode="widthFix"
							class="width-50upx height-50upx margin-right-xs bg-white round padding-4upx"
							src="/static/image/single/filter.svg" @tap="hide_league_filter = false">
							<view class='ticket-tag' style="top: -10px;left: 15px;" v-if="league_checked_count > 0">
								{{league_checked_count}}
							</view>
						</image>
						<image mode="widthFix"
							class="width-50upx height-50upx margin-right-xs bg-white round padding-4upx margin-left-sm"
							src="/static/image/single/search.svg" @tap="hide_fuzzy_search = false" />
					</view>
				</view>
			</block>
		</zw-header>

		<view class="flex-row mybg-lprimary justify-around padding-tb-sm ">
			<button class="cu-btn sm width-40 myfont-10px" :class="{'mybg-active':!tomorrow,}"
				@click="select_date(false)">{{$t('today')}}</button>
			<button class="cu-btn sm width-40 myfont-10px" :class="{'mybg-active':tomorrow,}"
				@click="select_date(true)">{{$t('tomorrow')}}</button>
		</view>
		<view class="ticket-wrapper cu-avatar" v-show="bet_list.length > 0 && match_ref.mixed" @click="show_bet_slip">
			<view class='ticket-tag'>{{bet_list.length}}</view>
			<view class="ticket width-30px height-30px "></view>
		</view>

		<!-- <scroll-view scroll-y class="page" style="height:calc(100vh - 123px);" @scrolltolower="clickLoadMore"> -->
		<scroll-view scroll-y class="page padding-lr-sm padding-bottom-1px text-bold" style="line-height: 1.5;"
			@scroll="handle_scroll"
			:style="{height:isLogin?`calc(${calc_page_height} - 55px - 58px - 46px - 65px)`:`calc(${calc_page_height} - 55px - 60px - 58px - 46px - 65px)`,}">
			<!-- 联赛 -->
			<view class="flex-column padding-tb-sm" v-for="(league,index) in league_list" :key="index"
				v-show='league.checked  && league[`include_${tomorrow?"tomorrow":"today"}`]'>
				<view class="mybg-league flex-row justify-between radius-10px text-white myfont-9px"
					style="padding: 6px 10px;">
					<view class="flex-row ">
						<view class="cuIcon-favorfill margin-right-sm myfont-12px"
							:class="{'mycolor-active':league.favor,}" @click="favor_click(league)"></view>
						<view class="" @click="league.show_match = !league.show_match">{{league.name}}</view>
					</view>
					<view class="flex-row gap-5px width-25 justify-end" @click="league.show_match = !league.show_match">
						<view class="cu-tag round sm mybg-active mycolor-primary min-width-30px margin-right-sm">
							{{league.match_list.length}}
						</view>
						<view class="myfont-12px" :class="league.show_match?'cuIcon-unfold':'cuIcon-fold'"></view>
					</view>
				</view>

				<transition name="match-animation" class="width-100" @before-enter="beforeEnter" @enter="enter"
					@leave="leave">
					<view v-show="league.show_match" class="width-100">
						<view class="flex-column radius-10px myfont-12px margin-top-2px padding-tb-sm league-match"
							v-for="(match,_index) in league.match_list" :key="_index"
							v-show="match.checked && match.MATCH_DAY ===(!tomorrow?'today':'tomorrow')">
							<view class="flex-row padding-bottom-8px mycolor-primary myfont-10px "
								@click="show_match_detail(match,index,_index)">
								<view class="flex-column width-33 padding-lr-sm"
									:class="{'text-red':match.LOSE_TEAM ==='1',}">
									{{match.HOST_TEAM}}
								</view>
								<view class="flex-row width-34 justify-between myfont-9px"
									:id='`match-${index}-${_index}`'>
									<image :src="match.show_image?match.home_logo:''" lazy-load
										class="width-25px height-25px" @error="error_pic(match,'home')" />
									<view class="flex-column align-center " style="width: calc(100% - 10vw);">
										<view>{{match.MD_HHMM}}</view>
										<view class="myfont-7px text-light">{{match.MD_NOON}}</view>
										<view>{{match.MD_DDMM}}</view>
									</view>
									<image :src="match.show_image?match.away_logo:''" lazy-load
										class="width-25px height-25px" @error="error_pic(match,'away')" />
								</view>
								<view class="flex-column width-33 padding-lr-sm"
									:class="{'text-red':match.LOSE_TEAM ==='2',}">
									{{match.GUEST_TEAM}}
								</view>
							</view>

							<view class="league-match-attr-row width-100" style="justify-content: space-around;"
								@click="">
								<view class="league-match-attr" v-for="(attr,__index) in match.ATTR" :key="__index"
									:class="attr.MATCH_ATTR_TYPE==bet_type.SINGLE_WDL?'width-40':'width-30'">
									<view class="league-match-attr-type" :class="{'text-grey':attr.disabled,}">
										{{[,'HDP','OU',,'HDP','OU',,,,,'1X2'][parseInt(attr.MATCH_ATTR_TYPE)]}}
									</view>
									<view class="league-match-attr-detail"
										@click="betClick('host',index,_index,__index,attr)"
										:class="{'mybg-active':attr.host_selected,}">
										<view class="league-match-attr-detail-up" :class="{'text-red':( match_ref.mixed || 
											(bet_type.SINGLE_BODY ==attr.MATCH_ATTR_TYPE && attr.LOSE_TEAM==='1') ||
											(bet_type.SINGLE_GOAL ==attr.MATCH_ATTR_TYPE)),
											'mybg-active':attr.host_selected,}">
											{{cal_odds(attr,1)}}
										</view>
										<view class="league-match-attr-detail-down "
											:class="{'disable':attr.disabled,}">
											{{cal_mix_under_odds(attr,1)||attr.ODDS}}
										</view>
									</view>
									<view class="league-match-attr-detail"
										@click="betClick('draw',index,_index,__index,attr)"
										:class="{'mybg-active':attr.draw_selected,}"
										v-if="attr.MATCH_ATTR_TYPE==bet_type.SINGLE_WDL">
										<view class="league-match-attr-detail-up"
											:class="{'mybg-active':attr.draw_selected,}">{{attr.disabled?'':'DRAW'}}
										</view>
										<view class="league-match-attr-detail-down" :class="{'disable':attr.disabled,}">
											{{cal_mix_under_odds(attr,3)||attr.DRAW_ODDS}}
										</view>
									</view>
									<view class="league-match-attr-detail"
										@click="betClick('guest',index,_index,__index,attr)"
										:class="{'mybg-active':attr.guest_selected,}">
										<view class="league-match-attr-detail-up" :class="{'text-red':( match_ref.mixed || (bet_type.SINGLE_BODY==attr.MATCH_ATTR_TYPE && attr.LOSE_TEAM==='2')),
											'mybg-active':attr.guest_selected,}">
											{{cal_odds(attr,2)}}
										</view>
										<view class="league-match-attr-detail-down "
											:class="{'disable':attr.disabled,}">
											{{cal_mix_under_odds(attr,2)||attr.ODDS_GUEST}}
										</view>
									</view>
								</view>
							</view>
						</view>
					</view>
				</transition>
			</view>
		</scroll-view>


		<!-- 比赛详情 -->
		<view class="dialog-wrapper bg-white" v-show="!hide_match_detail">
			<view class="flex-row text-bold box-shadow padding" @click="hide_match_detail = true"
				style="line-height: 1.2;">
				<view class="cuIcon-back mycolor-info"></view>
				<view class="mycolor-primary">{{match_ref.match_detail.REMARK ||match_ref.match_detail.LEAGUE}}</view>
			</view>
			<view class="flex-row justify-center padding-tb-xl mycolor-primary text-bold width-100 padding-lr"
				style="line-height: 1.5;">
				<view class="flex-column gap-5px myfont-11px">
					<image :src="match_ref.match_detail.home_logo" lazy-load class="height-10vw width-10vw"
						@error="error_pic(match_ref.match_detail,'home')"></image>
					<view :class="{'text-red':match_ref.match_detail.LOSE_TEAM ==='1',}">
						{{match_ref.match_detail.HOST_TEAM}}
					</view>
				</view>

				<view class="flex-column myfont-10px" v-if="!tomorrow">
					<view>{{'TODAY'}}</view>
					<view>{{'MATCH START IN'}}</view>
					<view class="myfont-18px">
						<count-down :count_time="match_ref.match_detail.LOCAL_MATCH_TIME"></count-down>
						<!-- <text>{{'14'}}</text>：<text>{{'38'}}</text>：<text>{{'59'}}</text> -->
					</view>
					<view class="myfont-7px">
						<text>{{'HOUR'}}</text>：<text>{{'MINUTE'}}</text>：<text>{{'SECOND'}}</text>
					</view>
				</view>
				<view class="flex-column myfont-10px" v-else>
					<view>{{match_ref.match_detail.MD_DAY}} {{match_ref.match_detail.MD_DDMM}}</view>
					<view>{{'MATCH START TIME'}}</view>
					<view class="myfont-18px">
						<text>{{match_ref.match_detail.MD_HHMM}}</text>
					</view>
					<view class="myfont-7px">
						<text>{{match_ref.match_detail.MD_NOON}}</text>
					</view>
				</view>

				<view class="flex-column gap-5px myfont-11px">
					<image :src="match_ref.match_detail.away_logo" lazy-load class="height-10vw width-10vw"
						@error="error_pic(match_ref.match_detail,'away')"></image>
					<view :class="{'text-red':match_ref.match_detail.LOSE_TEAM ==='2',}">
						{{match_ref.match_detail.GUEST_TEAM}}
					</view>
				</view>
			</view>
			<view class="flex-column width-100 gap-10vh padding-lr" style="white-space: pre-wrap;">
				<view class="league-match-attr detail" v-for="(attr,__index) in match_ref.match_detail.ATTR"
					:key="__index">
					<view class="league-match-attr-type" :class="{'text-grey':attr.disabled,}">
						{{[,'HDP','OU',,'HDP','OU',,,,,'1X2'][parseInt(attr.MATCH_ATTR_TYPE)]}}
					</view>
					<view class="league-match-attr-detail detail"
						@click="betClick('host',match_ref.match_detail.index,match_ref.match_detail._index,__index,attr)"
						:class="{'mybg-active':attr.host_selected,}">
						<view class="league-match-attr-detail-up detail"
							:class="{'text-red':( match_ref.mixed || ([bet_type.SINGLE_GOAL,bet_type.SINGLE_BODY].includes(attr.MATCH_ATTR_TYPE) && attr.LOSE_TEAM==='1')),'mybg-active':attr.host_selected,}">
							{{cal_odds(attr,1)}}
						</view>
						<view class="league-match-attr-detail-down detail " :class="{'text-grey':attr.disabled,}">
							{{cal_mix_under_odds(attr,1)||attr.ODDS}}
						</view>
					</view>
					<view class="league-match-attr-detail detail"
						@click="betClick('draw',match_ref.match_detail.index,match_ref.match_detail._index,__index,attr)"
						:class="{'mybg-active':attr.draw_selected,}" v-if="attr.MATCH_ATTR_TYPE==bet_type.SINGLE_WDL">
						<view class="league-match-attr-detail-up detail" :class="{'mybg-active':attr.draw_selected,}">
							DRAW</view>
						<view class="league-match-attr-detail-down detail">{{attr.DRAW_ODDS}}</view>
					</view>
					<view class="league-match-attr-detail detail"
						@click="betClick('guest',match_ref.match_detail.index,match_ref.match_detail._index,__index,attr)"
						:class="{'mybg-active':attr.guest_selected,}">
						<view class="league-match-attr-detail-up detail"
							:class="{'text-red':( match_ref.mixed || ([bet_type.SINGLE_GOAL,bet_type.SINGLE_BODY].includes(attr.MATCH_ATTR_TYPE) && attr.LOSE_TEAM==='2')),'mybg-active':attr.guest_selected,}">
							{{cal_odds(attr,2)}}
						</view>
						<view class="league-match-attr-detail-down detail "
							:class="{'text-grey myfont-12px':attr.disabled,}">
							{{cal_mix_under_odds(attr,2)||attr.ODDS_GUEST}}
						</view>
					</view>
				</view>
			</view>
		</view>

		<!-- 下单详情 -->
		<scroll-view scroll-y class="dialog-wrapper mycolor-primary slip" v-show="!hide_bets_slip" @tap.prevent=""
			style="height: 100%;">
			<view style="background: none;line-height: 1.2;">
				<view class="flex-row text-bold box-shadow padding bg-white mycolor-primary"
					@click="hide_bets_slip = true" style="position: sticky;top: 0;overflow-y: overlay;z-index: 16;"
					v-if="match_ref.mixed">
					<view class="cuIcon-back mycolor-info"></view>
					<view class="width-100">{{'Bets Slip'}}</view>
				</view>
				<!-- 混合 -->
				<view class="flex-column padding-xs text-bold bg-white mycolor-primary" v-show="match_ref.mixed"
					style="min-height: calc(100vh - 750upx - 62px - 42.5px);justify-content: start;">
					<view class="flex-column detail-box-shadow radius-6px margin-bottom-xs" style="height: auto;"
						v-for="(match,index) in bet_list" :key='index'>
						<view class="padding-sm flex-column myfont-12px gap-5px">
							<view class="flex-row justify-between">
								<view :class="{'text-red':match.LOSE_TEAM=='1',}">{{match.HOST_TEAM}}</view>
								<view>{{bet_type.MIX_BODY == match.sa.MATCH_ATTR_TYPE ?'HANDICAP':'OU'}}</view>
							</view>
							<view class="flex-row justify-between">
								<view :class="{'text-red':match.LOSE_TEAM=='2',}">{{match.GUEST_TEAM}}</view>
								<view class="">{{calc_real_odds(match.sa,'bn')}}<text
										class="text-red">{{calc_real_odds(match.sa,'bo')}}</text>{{calc_real_odds(match.sa,'ha')}}
								</view>
							</view>
							<view class="flex-row justify-between">
								<view>{{match.SLIP_DATE}}</view>
								<view></view>
							</view>
						</view>
						<view class="flex-row justify-between mybg-primary padding-sm radius-6px">
							<view
								class="cuIcon-deletefill round bg-white mycolor-primary myfont-10px width-20px height-18px line-height-18px"
								@click="remove_select(match)">
							</view>
							<view class="flex-row  justify-end">
								<text class="mycolor-active">{{bet_content(match)}}</text>
								<text class="text-white padding-left-sm">@2.00</text>
							</view>
						</view>
					</view>
				</view>
				<!-- 单笔 -->
				<view v-if="!match_ref.mixed" class="single-mask" @click="hide_bets_slip = true"></view>
				<view class="text-bold flex-column bg-white padding-lr-sm"
					style="bottom: 0;overflow-y: overlay;z-index: 17;"
					:style="{'position':match_ref.mixed?'sticky':'fixed'}">
					<view class="flex-column padding-xs single-bottom dialig-bottom" v-if="!match_ref.mixed">
						<view class="margin-top-sm mybg-primary row-line"></view>
						<view class="flex-row gap-5px justify-center margin-tb-xs myfont-11px">
							<text class=""
								:class="{'text-red':match_ref.bet_match.LOSE_TEAM=='1',}">{{match_ref.bet_match.HOST_TEAM}}</text>
							<text class="text-light">vs</text>
							<text
								:class="{'text-red':match_ref.bet_match.LOSE_TEAM=='2',}">{{match_ref.bet_match.GUEST_TEAM}}</text>
						</view>
					</view>
					<view v-if="!match_ref.mixed" class="width-100">
						<view
							class="flex-column detail-box-shadow radius-6px margin-bottom-xs myfont-12px gap-5px padding-sm">
							<view class="flex-row justify-between">
								<view class="flex-column" style="align-items: start;">
									<view class="">{{bet_content(match_ref.bet_match)}}</view>
									<view class="">@ {{bet_type_2_str(match_ref.bet_match.sa)}}</view>
								</view>
								<view class="flex-column" style="align-items: end;">
									<view class="">{{calc_detail_odds(match_ref.bet_match.sa)}}</view>
									<view class="">{{calc_real_odds(match_ref.bet_match.sa,'bn')}}<text
											class="text-red">{{calc_real_odds(match_ref.bet_match.sa,'bo')}}</text>{{calc_real_odds(match_ref.bet_match.sa,'ha')}}
									</view>
								</view>
							</view>
						</view>
						<!-- 注释掉兑换码tab，只保留bets tab -->
						<!-- <view
							class="flex-row justify-between detail-box-shadow radius-6px margin-bottom-xs myfont-12px gap-5px padding-2px">
							<button class="cu-btn mycolor-primary myfont-12px basis-df"
								:class="!bet_main?'bg-white':'mybg-active'" @click="bet_main = !bet_main">
								<view>{{$t('bets')}}</view>
							</button>
							<button class="cu-btn mycolor-primary myfont-12px basis-df"
								:class="bet_main?'bg-white':'mybg-active'" @click="bet_main = !bet_main">
								<view>{{$t('promotion_code')}}</view>
							</button>
						</view> -->
					</view>
					<view class="flex-column padding-tb-xs dialig-bottom">
						<view
							class="flex-column detail-box-shadow radius-6px margin-bottom-xs myfont-12px gap-5px padding-sm"
							v-if="match_ref.mixed">
							<view class="flex-row justify-between">
								<view class="">Total Bet</view>
								<view class="">{{bet_list.length}}</view>
							</view>
							<view class="flex-row justify-between">
								<view class="">Odds</view>
								<view class="">{{Math.pow(2,bet_list.length)}}</view>
							</view>
						</view>
						<view v-show="bet_main">
							<view
								class="flex-row justify-between detail-box-shadow radius-6px margin-bottom-xs myfont-12px gap-5px padding-sm">
								<view class="flex-row justify-start">

									<view class="mybg-active round width-75upx height-65upx align-center flex-column"
										style="">
										<image mode="widthFix" class="width-20px "
											src="/static/image/single/wallet-bet.svg"></image>
									</view>
									<view class="flex-column margin-left-sm align-start gap-5px"
										style="align-items: start;">
										<view class="text-light">{{$t('balance')}} ({{$t('main_wallet')}})</view>
										<view>{{$toolbox.num_format($store.state.userInfo.money)}}</view>
									</view>
								</view>
								<button class="deposit-btn mybg-active mycolor-primary myfont-12px width-30vw"
									@click="to_deposit()">
									<image mode="widthFix" class="width-20px margin-right-xs"
										src="/static/image/single/deposit.svg"></image>
									<view>{{$t('deposit')}}</view>
								</button>
							</view>
							<!-- Promotion Wallet 显示 -->
							<view
								class="flex-row justify-between detail-box-shadow radius-6px margin-bottom-xs myfont-12px gap-5px padding-sm">
								<view class="flex-row justify-start align-center">
									<view class="mybg-active round width-33px height-65upx align-center flex-column">
										<image mode="widthFix" class="width-20px"
											src="/static/image/single/wallet-bet.svg"></image>
									</view>
									<view class="flex-column1 margin-left-sm align-start gap-5px">
										<view class="text-light">Promotion Wallet</view>
										<view>{{$toolbox.num_format($store.state.userInfo.money_promotion || 0)}}</view>
									</view>
								</view>
								<view class="flex-row1 align-center justify-end" @click="togglePromotionWallet">
									<view class="flex-row align-center gap-5px" style="cursor: pointer;">
										<text class="myfont-10px text-light width-100px" style="line-height: 1.2;">
											Use Promotion Wallet
										</text>
										<!-- 自定义checkbox -->
										<view class="custom-checkbox" :class="{
												'custom-checkbox-checked': use_promotion_wallet,
												'custom-checkbox-disabled': !canUsePromotionWallet
											}">
											<view v-if="use_promotion_wallet" class="custom-checkbox-icon cuIcon-check">
											</view>
										</view>

									</view>
								</view>
							</view>
							<view
								class="flex-column detail-box-shadow radius-6px margin-bottom-xs myfont-12px gap-5px padding-sm">
								<view class="flex-row justify-between">
									<view
										class="flex-row justify-between margin-right radius-6px padding-tb-xs padding-lr-sm"
										style="border: 1px grey solid;">
										<input class="width-100 text-left padding-right-sm" type="number"
											@input="inputNum" v-model="amount" />


										<image class="width-20px height-20px" src="/static/image/single/close.svg"
											@click="clearAmount()">
											<!-- @click="amount=match_ref.mixed?mix_min:single_min"> -->
										</image>
									</view>
									<button class="deposit-btn mybg-active mycolor-primary myfont-12px width-35vw"
										@click="submit()">
										<image mode="widthFix" class="width-20px margin-right-xs"
											src="/static/image/single/ball.svg"></image>
										<view class="">{{$t('betting')}}</view>
									</button>
								</view>

								<!-- 优惠券下拉选择框 (单笔和混合都显示) -->
								<view class="flex-column margin-top-sm gap-5px" style="position: relative;">
									<!-- <view class="text-light myfont-10px">{{$t('Available Coupons')}}</view> -->

									<!-- 下拉选择框主体 -->
									<view class="coupon-select-wrapper" @click="toggleCouponDropdown">
										<view class="coupon-select-input padding-sm radius-6px"
											:class="show_coupon_dropdown ? 'mybg-active text-black' : 'mybg-primary'"
											style="border: 1px solid rgba(255,255,255,0.2); display: flex; flex-direction: row; justify-content: space-between; align-items: center; width: 100%;">
											<!-- 左侧内容区 -->
											<view class="flex-row1 align-center" style="flex: 1; min-width: 0;">
												<view v-if="selected_coupon"
													style="display: flex; flex-direction: row; align-items: center;">
													<text class="text-bold myfont-12px"
														style="white-space: nowrap;">{{selected_coupon.coupon_name}}</text>
													<text class="myfont-10px text-light margin-left-sm flex-row1"
														style="white-space: nowrap;">
														(-{{$toolbox.num_format(selected_coupon.bonus_amount)}} MMK)
													</text>
												</view>
												<view v-else class="text-light myfont-12px flex-row1">
													<text v-if="loading_coupons">{{$t('Loading Coupons')}}...</text>
													<text
														v-else-if="available_coupons.length > 0">{{`${$t('Select Coupon')}(${available_coupons.length})`}}
													</text>
													<text v-else>{{$t('No Available Coupons')}}</text>
												</view>
											</view>
											<!-- 右侧图标区 -->
											<view
												style="display: flex; flex-direction: row; align-items: center; flex-shrink: 0; margin-left: 10px;">
												<view v-if="selected_coupon" class="cuIcon-close myfont-12px"
													@click.stop="clearCouponSelection" style="padding: 2px 5px;"></view>
												<view class="cuIcon-unfold myfont-12px"
													:class="show_coupon_dropdown ? 'rotate-180' : ''"
													style="padding: 2px 5px;"></view>
											</view>
										</view>
									</view>

									<!-- 下拉选项列表 -->
									<view v-if="show_coupon_dropdown" class="coupon-dropdown-list mybg-grey radius-6px"
										style="position: absolute; top: 100%; left: 0; right: 0; z-index: 100;
											   max-height: 150px; overflow-y: auto; margin-top: 5px;
											   box-shadow: 0 2px 8px rgba(0,0,0,0.3);">
										<view v-for="(coupon, index) in available_coupons" :key="index"
											@click="selectCoupon(coupon)"
											class="coupon-dropdown-item flex-row justify-between padding-sm"
											:class="selected_coupon && selected_coupon.member_coupon_id === coupon.member_coupon_id ? 'mybg-active text-black' : ''"
											style="border-bottom: 1px solid rgba(255,255,255,0.1);">
											<view class="flex-column align-start gap-2px" style="flex: 1;">
												<text class="text-bold myfont-12px">{{coupon.coupon_name}}</text>
												<text class="myfont-10px text-light">
													{{$t('bonus')}}: {{$toolbox.num_format(coupon.bonus_amount)}} MMK
												</text>
												<text v-if="coupon.min_bet_required > 0"
													class="myfont-9px text-light">{{`${$t('Min Bet')}: ${$toolbox.num_format(coupon.min_bet_required)}MMK`}}
												</text>
												<!-- <text v-if="coupon.min_bet_required > 0" class="myfont-9px text-light">
													{{$t('min_bet')}}: {{$toolbox.num_format(coupon.min_bet_required)}} MMK
												</text> -->
											</view>
											<view
												v-if="selected_coupon && selected_coupon.member_coupon_id === coupon.member_coupon_id"
												class="cuIcon-check mycolor-active myfont-14px"></view>
										</view>
									</view>
								</view>

								<view class="flex-row justify-start text-light text-black text-left" style="">
									<view>
										<text>{{$t('minimum_bet')}}</text>
										<text
											class="padding-lr-xs text-bold mycolor-primary">{{match_ref.mixed?mix_min:single_min}}</text>
										<text>{{$t('to')}}</text>
										<text
											class="padding-lr-xs text-bold mycolor-primary">{{match_ref.mixed?mix_max:single_max}}</text>
										<text>MMK{{$t('until')}}.</text>
									</view>
								</view>
								<view class="flex-row justify-between align-center ">
									<view>{{$t('potential')}}<text
											class="margin-left-sm myfont-20px ">{{$toolbox.num_format(calc_benefit(match_ref.bet_match))}}</text>
									</view>
									<!-- 实际支付金额显示 -->
									<view class="myfont-10px">Actual Payment<text
											class="margin-left-sm myfont-20px ">{{$toolbox.num_format(actualPaymentAmount)}}</text>
									</view>
									<!-- <view class="flex-column align-end">
										<text class="text-light myfont-10px">Actual Payment</text>
										<text class="myfont-16px text-bold mycolor-primary">{{$toolbox.num_format(actualPaymentAmount)}}</text>
									</view> -->
								</view>
								<view class="flex-row justify-start text-light">
									<view>{{$t('non_maximum_wining_limit')}}</view>
								</view>
							</view>
							<view
								class="flex-column detail-box-shadow radius-6px margin-bottom-xs myfont-12px gap-5px padding-sm">
								<view class="flex-row justify-start text-light">
									<view>{{$t('quick_bets')}}</view>
								</view>
								<view class="flex-row justify-start text-light">
									<view>{{$t('select_bet')}}</view>
								</view>
								<view class="flex-row justify-between text-light">
									<button class="cu-btn mybg-primary width-31" @click="set_amount(i)"
										v-for="(i,index) in amount_list" :key='index'>{{i}}</button>
								</view>
							</view>
						</view>
						<!-- 注释掉兑换码内容部分 -->
						<!-- <view class="width-100" v-show='!bet_main'>
							<view
								class="flex-column justify-between detail-box-shadow radius-6px margin-bottom-xs myfont-12px gap-5px padding-sm mycolor-primary"
								style="align-items: start;">
								<view>{{$t('promo_code')}}</view>
								<view
									class="flex-row justify-between margin-right radius-6px padding-tb-xs padding-lr-sm"
									style="border: 1px grey solid;">
									<input class="width-100 text-left padding-right-sm" v-model="promotion_code" />
									<view class="cuIcon-close round width-20px height-18px line-height-16px myfont-10px"
										style="border: 4upx #0c356a solid;" @click="promotion_code = ''"></view>
								</view>
								<button class="cu-btn mybg-active mycolor-primary myfont-12px width-100"
									@click="submitWithPromotion()">{{$t('redeem')}}</button>
							</view>
						</view> -->
					</view>
				</view>
			</view>
		</scroll-view>

		<login-modal ref='login_modal' :hidden.sync="hide_login_modal"></login-modal>
		<league-filter ref='league_filter' :hidden.sync="hide_league_filter" :tomorrow='tomorrow'
			:league_list.sync='league_list'></league-filter>
		<fuzzy-search ref='fuzzy_search' :hidden.sync="hide_fuzzy_search"
			:league_list.sync='league_list'></fuzzy-search>
	</view>
</template>

<script>
	import config from '../../utils/config.js'
	import Vue from "vue";
	import './components/match.css'
	import match_mixins from './components/mixins.js'
	import LeagueFilter from './components/league_filter.vue'
	import FuzzySearch from './components/fuzzy_search.vue'
	import CountDown from './components/count_down.vue'
	import Selector from '../../components/common/selector.vue'
	// import MatchDetail from './components/match_detail.vue'
	// import BetsSlip from './components/bets_slip.vue'

	export default {
		components: {
			LeagueFilter,
			CountDown,
			FuzzySearch,
			// MatchDetail,
			// BetsSlip,
		},
		mixins: [match_mixins],
		data() {
			return {
				amount_list: [1000, 5000, 10000],
				isLogin: uni.getStorageSync('Authorization') || false,
				animation: '',
				promotion_code: '',
				amount: 0,
				hide_league_filter: true,
				hide_match_detail: true,
				hide_bets_slip: true,
				hide_login_modal: true,
				hide_fuzzy_search: true,
				bet_main: true,
				tomorrow: false,
				orders: [],
				num: 0,
				league_list: [],
				allStatus: true,
				intervalId: '',
				all_matches_data: null, // Store all matches data for filtering
				confirmIntervalId: '',
				configs: {},
				mix_slip: uni.getStorageSync('mix_slip') || [],
				match_ref: {
					mixed: false,
					num: 0,
					bet_match: {
						sa: {}
					},
					match_detail: {},
					league_list: [],
				},
				login_success: uni.getStorageSync('login_success') || false,
				// 优惠券相关
				available_coupons: [],
				selected_coupon: null,
				loading_coupons: false,
				show_coupon_dropdown: false, // 控制下拉框显示
				use_promotion_wallet: false, // 是否优先使用Promotion Wallet
			}
		},
		watch: {
			'$store.state.configs.single_min': function() {
				this.amount = parseInt(this.$store.state.configs.single_min);
			},
			'$store.state.userInfo.id': function() {},
			// 监听金额变化，自动取消不符合条件的优惠钱包勾选
			'amount': function(newAmount, oldAmount) {
				// 如果已勾选优惠钱包，检查新金额是否仍然符合条件
				if (this.use_promotion_wallet && !this.canUsePromotionWallet) {
					// 自动取消勾选
					this.use_promotion_wallet = false;

					// 提示用户
					const promotionBalance = parseFloat(this.$toolbox.num_format(
						this.$store.state.userInfo.money_promotion || 0, 0, true));

					let message = 'Promotion wallet balance is insufficient for this bet amount';
					if (promotionBalance < this.single_min) {
						message = `Promotion wallet balance must be at least ${this.single_min} MMK`;
					}

					uni.showToast({
						title: message,
						icon: 'none',
						// duration: 2000
					});
				}
			},
			// 监听优惠券变化，也检查优惠钱包状态
			'selected_coupon': function(newCoupon, oldCoupon) {
				// 如果已勾选优惠钱包，检查优惠券变化后是否仍然符合条件
				if (this.use_promotion_wallet && !this.canUsePromotionWallet) {
					this.use_promotion_wallet = false;

					uni.showToast({
						title: 'Promotion wallet balance is insufficient after applying coupon',
						icon: 'none',
						// duration: 2000
					});
				}
			}
		},
		computed: {
			// 计算实际支付金额（考虑优惠券折扣）
			actualPaymentAmount() {
				let paymentAmount = this.amount;

				// 如果选择了优惠券，减去优惠金额
				if (this.selected_coupon && this.selected_coupon.bonus_amount) {
					const couponAmount = parseFloat(this.$toolbox.num_format(
						this.selected_coupon.bonus_amount, 0, true));
					paymentAmount = this.amount - couponAmount;
					// 确保不会是负数
					if (paymentAmount < 0) {
						paymentAmount = 0;
					}
				}

				return paymentAmount;
			},
			// 判断是否可以使用优惠钱包
			canUsePromotionWallet() {
				// 使用num_format的第三个参数true来去除格式化，获取纯数字
				const promotionBalance = parseFloat(this.$toolbox.num_format(
					this.$store.state.userInfo.money_promotion || 0, 0, true));

				// 条件1: 优惠钱包余额必须大于0
				if (promotionBalance <= 0) {
					return false;
				}

				// 条件2: 优惠钱包余额必须大于等于single最小下单金额
				if (promotionBalance < this.single_min) {
					return false;
				}

				// 条件3: 优惠钱包余额必须大于等于当前下单金额（考虑优惠券折扣后的金额）
				let requiredAmount = this.amount;
				if (this.selected_coupon && this.selected_coupon.bonus_amount) {
					// 如果有优惠券，计算优惠后的金额
					const couponAmount = parseFloat(this.$toolbox.num_format(
						this.selected_coupon.bonus_amount, 0, true));
					requiredAmount = this.amount - couponAmount;
					if (requiredAmount < 0) {
						requiredAmount = 0;
					}
				}

				if (promotionBalance < requiredAmount) {
					return false;
				}

				return true;
			},
			bet_list() {
				let match_list = []
				let leagues = this.league_list
				leagues.forEach(league => {
					match_list = match_list.concat(league.match_list)
				})
				let selected = []
				match_list.forEach(match => {
					match.ATTR.some(attr => {
						if (attr.host_selected || attr.guest_selected || attr.draw_selected) {
							selected.push(match)
							match.sa = attr
							return
						}
					})
				})
				return selected
			},
			mix_min() {
				if (!this.configs.hasOwnProperty('mix_min')) {
					this.configs = this.$store.state.configs || uni.getStorageSync('config')
				}
				return parseInt(this.configs.mix_min)
			},
			mix_max() {
				return parseInt(this.configs.mix_max)
			},
			single_min() {
				if (!this.configs.hasOwnProperty('single_min')) {
					this.configs = this.$store.state.configs || uni.getStorageSync('config')
				}
				return parseInt(this.configs.single_min)
			},
			single_max() {
				return parseInt(this.configs.single_max)
			},
			league_checked_count() {
				let leagues = this.league_list.filter(league => league[`include_${this.tomorrow?"tomorrow":"today"}`])

				return leagues.filter(ele => ele.checked).length
			},
			calc_slip_height() {
				let info = uni.getDeviceInfo()
				if (info.platform == 'ios') {
					return `calc(100vh - 85px)`
				}
				return '100vh'
			},
		},
		methods: {
			// 获取可用优惠券
			fetchAvailableCoupons() {
				// 检查用户登录状态
				if (!this.isLogin) {
					this.available_coupons = []
					this.selected_coupon = null
					return
				}

				// 确定最小金额（根据是否mix）
				const minAmount = this.match_ref.mixed ? this.mix_min : this.single_min

				// 只有当金额大于等于最小投注额时才获取优惠券
				if (this.amount < minAmount) {
					console.log('Amount is less than minimum bet, clearing coupons')
					this.available_coupons = []
					this.selected_coupon = null
					this.loading_coupons = false
					return
				}

				this.loading_coupons = true
				this.$http.post('/coupon/available_for_bet', {
					bet_amount: this.amount
				}, (res) => {
					this.loading_coupons = false
					// 如果金额已被清零，忽略此响应（防止竞态条件）
					if (this.amount === 0) {
						console.log('Amount is 0, ignoring coupon response')
						return
					}
					if (res.statusCode == 200) {
						// 修正数据路径: res.data 是后端返回的完整响应对象
						// 后端返回: {code: 200, data: {coupons: [...], total_count: 3}, message: "success"}
						// 所以需要访问 res.data.data.coupons
						const responseData = res.data && res.data.data ? res.data.data : res.data
						this.available_coupons = responseData.coupons || []
						console.log('Available coupons loaded:', this.available_coupons.length)
						// 如果之前选择的优惠券不在新列表中，清除选择
						if (this.selected_coupon) {
							const stillAvailable = this.available_coupons.find(
								c => c.member_coupon_id === this.selected_coupon.member_coupon_id
							)
							if (!stillAvailable) {
								this.selected_coupon = null
							}
						}
					} else {
						this.available_coupons = []
						this.selected_coupon = null
					}
				}, (err) => {
					this.loading_coupons = false
					// 如果金额已被清零，忽略此错误响应
					if (this.amount === 0) {
						return
					}
					this.available_coupons = []
					this.selected_coupon = null
					console.error('Failed to load coupons:', err)
				})
			},

			// 选择优惠券
			selectCoupon(coupon) {
				if (this.selected_coupon && this.selected_coupon.member_coupon_id === coupon.member_coupon_id) {
					// 取消选择
					this.selected_coupon = null
				} else {
					this.selected_coupon = coupon
				}
				// 选择后关闭下拉框
				this.show_coupon_dropdown = false
			},

			// 切换下拉框显示状态
			toggleCouponDropdown() {
				// 只有在有优惠券时才允许展开下拉框
				if (this.available_coupons.length > 0 && !this.loading_coupons) {
					this.show_coupon_dropdown = !this.show_coupon_dropdown
				}
			},

			// 清除优惠券选择
			clearCouponSelection() {
				this.selected_coupon = null
				this.show_coupon_dropdown = false
			},

			// 清零金额并清除优惠券
			clearAmount() {
				this.amount = 0
				// 清零时清除优惠券列表和选择
				this.available_coupons = []
				this.selected_coupon = null
				this.show_coupon_dropdown = false
			},

			// 切换Promotion Wallet优先使用状态
			togglePromotionWallet() {
				// 使用computed属性检查是否可以使用优惠钱包
				if (!this.canUsePromotionWallet) {
					let message = this.$t('Promotion wallet balance is insufficient');
					// 使用num_format的第三个参数true来去除格式化，获取纯数字
					const promotionBalance = parseFloat(this.$toolbox.num_format(
						this.$store.state.userInfo.money_promotion || 0, 0, true));

					// 计算所需金额（考虑优惠券）
					let requiredAmount = this.amount;
					if (this.selected_coupon && this.selected_coupon.bonus_amount) {
						requiredAmount = this.amount - parseFloat(this.selected_coupon.bonus_amount);
						if (requiredAmount < 0) requiredAmount = 0;
					}

					if (promotionBalance < this.single_min) {
						message = `Promotion wallet balance must be at least ${this.single_min} MMK`;
					} else if (promotionBalance < requiredAmount) {
						message =
							`Promotion wallet balance (${this.$toolbox.num_format(promotionBalance)}) is less than required amount (${this.$toolbox.num_format(requiredAmount)})`;
					}

					uni.showToast({
						title: message,
						icon: 'none',
						// duration: 2000
					})
					return
				}
				this.use_promotion_wallet = !this.use_promotion_wallet
				console.log('Promotion wallet:', this.use_promotion_wallet)
			},

			inputNum: function(evt) {
				let min = this.match_ref.mixed ? this.mix_min : this.single_min
				let max = this.match_ref.mixed ? this.mix_max : this.single_max
				let amount = evt.detail.value.replace('.', '')
				amount = amount ? parseInt(amount) : '0'
				if (amount > max) {
					amount = max
				}
				// if (amount <= min) {
				// 	amount = min
				// }
				this.$nextTick(function() {
					this.$set(this, 'amount', amount)
					// 当金额改变时，自动获取可用优惠券（支持single和mix）
					if (this.amount > 0 && this.isLogin) {
						this.fetchAvailableCoupons()
					}
					// if (10000 < parseInt(this.amount) && parseInt(this.amount) < 5000000) {
					// 	this.amount_error = false
					// }
				})
			},
			show_match_detail(match, index, _index) {
				match.index = index
				match._index = _index
				this.match_ref.match_detail = match
				this.hide_match_detail = false
			},
			toggle(e) {
				this.animation = e;
				setTimeout(() => {
					this.animation = '';
				}, 1000)
			},
			select_date(tomorrow) {
				this.tomorrow = tomorrow
				if (!this.match_ref.mixed) {
					this.reset()
				}
				// this.filter_matches_by_date()
			},
			remove_select(match) {
				match.ATTR.forEach(attr => {
					this.reset_attr_select(attr)
				})
				this.calc_match_num()
				if (this.bet_list.length === 0) {
					this.hide_bets_slip = true
				}
			},
			cal_odds(attr, odd_type, typ = 'MATCH_ATTR_TYPE') {
				if (attr.disabled) return ''
				let type_2_str = [this.bet_type.MIX_GOAL, this.bet_type.SINGLE_GOAL].includes(attr.MATCH_ATTR_TYPE) ? [,
					'OVER', 'UNDER'
				] : [, 'HOME', 'AWAY', 'DRAW']
				if (!attr.hasOwnProperty(typ)) return ''
				let str = ''
				switch (true) {
					// BODY让球方显示赔率 attr.LOSE_TEAM == odd_type
					case [this.bet_type.SINGLE_BODY, this.bet_type.MIX_BODY, ].includes(attr[typ]) && attr.LOSE_TEAM ==
					odd_type:
						str = this.calc_real_odds(attr)
						break
						// GOAL左边显示文字 odd_type == 1
					case [this.bet_type.SINGLE_GOAL, this.bet_type.MIX_GOAL, ].includes(attr[typ]) && odd_type == 1:
						str = this.calc_real_odds(attr)
						break
						// 混合上面除了赔率其他不显示文字
					case this.match_ref.mixed:
						str = ''
						break
					default:
						str = type_2_str[odd_type]
				}
				return str
			},
			cal_mix_under_odds(attr, odd_type) {
				if (attr.disabled) {
					return this.attr_content(attr, odd_type)
				}
				if (!this.match_ref.mixed) {
					return ''
				}
				let res = ''
				let type_2_str = this.bet_type.MIX_GOAL == attr.MATCH_ATTR_TYPE ? [, 'OVER', 'UNDER'] : [, 'HOME', 'AWAY',
					'DRAW'
				]
				return type_2_str[odd_type]
			},
			calc_real_odds(attr, rt) {
				if (!attr.hasOwnProperty('MATCH_ATTR_TYPE')) return ''
				var DRAW_BUNKO = attr.DRAW_BUNKO == '0' ? '+' : '-';
				if (attr.DRAW_ODDS == '0') {
					if (['bo', 'ha'].includes(rt)) {
						return ''
					}
					return attr.LOSE_BALL_NUM + '=';
				} else {
					let body_attr = [this.bet_type.SINGLE_BODY, this.bet_type.MIX_BODY].includes(attr.MATCH_ATTR_TYPE) ||
						''
					if (body_attr) {
						body_attr = attr.LOSE_TEAM === '1' ? 'H' : 'A'
					}
					if (rt === 'bn') return `${attr.LOSE_BALL_NUM}`;
					if (rt === 'ha') return `${body_attr}`;
					if (rt === 'bo') {
						if ([this.bet_type.SINGLE_WDL].includes(attr.MATCH_ATTR_TYPE)) {
							return attr.draw_selected ? `${attr.DRAW_ODDS}` : attr.guest_selected ? `${attr.ODDS_GUEST}` :
								`${attr.ODDS}`
						}
						return `(${DRAW_BUNKO}${attr.DRAW_ODDS})`
					};
					return `${attr.LOSE_BALL_NUM}(${DRAW_BUNKO}${attr.DRAW_ODDS})${body_attr}`;
				}
			},
			calc_benefit(match) {
				let str = ''
				// 赔率设置在match_mixins中
				if (this.match_ref.mixed) {
					str = Math.pow(2, this.bet_list.length) * this.amount * (1 - this.commission)
				} else {
					let sa = match.sa
					let odds = 2
					switch (true) {
						case sa.host_selected:
							odds = sa.ODDS
							break
						case sa.guest_selected:
							odds = sa.ODDS_GUEST
							break
						case sa.draw_selected:
							odds = sa.DRAW_ODDS
							break
					}
					let own = sa.MATCH_ATTR_TYPE == '10' ? 0 : 1
					str = (parseFloat(odds) + own) * parseInt(this.amount)
				}
				return str
			},
			set_amount(amount) {
				this.amount = amount
				// 快捷金额选择后也需要获取可用优惠券（支持single和mix）
				if (this.amount > 0 && this.isLogin) {
					this.fetchAvailableCoupons()
				}
			},
			betClick(type, index, _index, __index, attr) {
				if (!this.isLogin) {
					this.hide_login_modal = false
					return
				}
				if (attr.disabled) return
				let _this = this;
				let league = _this.league_list[index]
				let match = league.match_list[_index];
				match.click_arr = [type, index, _index, __index, attr]
				_this.match_ref.num = 0

				let select_restult = _this.match_ref.mixed ? !attr[`${type}_selected`] : true

				// 取消本场赛事其他attr已选项
				match.ATTR.forEach(_attr => {
					_this.reset_attr_select(_attr)
				})
				attr[`${type}_selected`] = select_restult

				if (_this.match_ref.mixed) {
					// 混合显示
					match.ATTR[__index] = attr;
					this.calc_match_num()
				} else {
					//single的其他赛事取消高亮
					_this.league_list.forEach(_league => {
						_league.match_list.forEach(_match => {
							_match.ATTR.forEach(_attr => {
								if (attr.MATCH_ATTR_ID != _attr.MATCH_ATTR_ID) {
									_this.reset_attr_select(_attr)
								}
							})
						})
					})
					// 单笔显示下单界面
					match.sa = attr
					_this.match_ref.bet_match = match
					_this.bet_main = true
					_this.show_bet_slip()
				}
			},
			calc_match_num() {
				this.mix_slip = []
				this.match_ref.num = 0 // Reset counter before counting
				this.league_list.forEach(league => {
					league.match_list.forEach(match => {
						match.ATTR.forEach(attr => {
							if (attr.host_selected || attr.guest_selected || attr
								.draw_selected) {
								this.match_ref.num++;
								let _type = 'host'
								if (attr.guest_selected) {
									_type = 'guest'
								}
								if (attr.draw_selected) {
									_type = 'draw'
								}
								this.mix_slip.push(`${attr.MATCH_ATTR_ID}_${_type}`)
							}
						})
					})
				});
				uni.setStorageSync('mix_slip', this.mix_slip)
			},
			get_selected_attr(match, _type = 'had') {

			},
			show_bet_slip() {
				let _this = this
				_this.amount = _this.match_ref.mixed ? _this.mix_min : _this.single_min
				_this.promotion_code = ''
				_this.hide_bets_slip = false
				// 弹出下单框时也需要获取优惠券,因为有的优惠券可能初始金额就能用（支持single和mix）
				if (_this.amount > 0 && _this.isLogin) {
					_this.fetchAvailableCoupons()
				}
			},
			get_list() {
				var _this = this;
				uni.showLoading({
					title: 'loading'
				})
				var para = {
					// Remove match_date parameter - backend now returns both today and tomorrow
					page: _this.list_query.page,
					limit: _this.list_query.limit,
					odds_type: _this.match_ref.mixed ? 'mix' : 'single',
					time_zone_hours: 6.5,
					// time_zone_hours: _this.$toolbox.get_time_offset(),
				}
				_this.league_list = []
				_this.$http.get('/match/get', {
					data: para
				}, (res) => {
					if (res.statusCode == 200) {
						// Store raw data for filtering
						_this.all_matches_data = res.data;
						_this.loadding_data(res.data);
						uni.hideLoading();
						if (res.data.items.length == 0 && !_this.login_success) {
							uni.showToast({
								title: _this.$t('no_more_data'),
								icon: 'none'
							})
						}
					}
				})
			},
			updateOdds() {
				var _this = this;
				_this.$http.get('/match/get_odds', {}, (res) => {
					if (res.statusCode == 200) {
						let odds = res.data.items
						const odds_map = new Map(odds.map(odd => [odd.MATCH_ATTR_ID, odd]));
						_this.league_list.forEach((league, index) => {
							league.match_list.forEach((match, _index) => {
								match.ATTR.forEach((attr, __index) => {
									let new_odds = odds_map.get(attr.MATCH_ATTR_ID)
									if (new_odds) {
										attr.REAL_ODDS = new_odds.REAL_ODDS;
										attr.ODDS = new_odds.ODDS;
										attr.ODDS_GUEST = new_odds.ODDS_GUEST;
										attr.DRAW_ODDS = new_odds.DRAW_ODDS;
										attr.change = true;
										Vue.set(_this.league_list[index]
											.match_list[_index]
											.ATTR, __index, attr);
										setTimeout(function() {
											attr.change = false;
											Vue.set(_this.league_list[
													index]
												.match_list[_index]
												.ATTR,
												__index, attr);
										}, 5000)
									}
								})
							})
						})
						// })
					}
				})
			},
			loadding_data(data) {
				//获取联赛数组
				let _this = this;
				if (data.total) {
					let favor_leagues = data.favor_leagues
					let server_matches = data.items
					//使用set给leauges去重
					let server_leagues = [...new Set(server_matches.map(ele => ele.LEAGUE))]
					// leauges排序
					server_leagues = _this.sort_object(server_leagues, '', config.leagues)
					let league_list = server_leagues.map(ele => {
						return {
							name: ele,
							checked: true,
							show_match: true,
							include_today: false,
							include_tomorrow: false,
							favor: favor_leagues.includes(ele),
							match_list: [],
						}
					})

					let all_attr_type_list = _this.match_ref.mixed ? [_this.bet_type.MIX_BODY, _this.bet_type.MIX_GOAL, ] :
						[_this.bet_type.SINGLE_WDL, _this.bet_type.SINGLE_BODY, _this.bet_type.SINGLE_GOAL, ]
					server_matches.forEach(match => {
						match.click_arr = []
						match.show_image = true
						match.checked = true
						let time = new Date(match.LOCAL_MATCH_TIME)
						match.MATCH_MD_DATE = time
						match.MD_NOON = time.getHours() > 12 ? 'PM' : 'AM'
						match.MD_DAY = `${time.toDateString().split(" ")[0]}`
						match.MD_HHMM =
							`${String(time.getHours()%12).padStart(2,'0')}:${String(time.getMinutes()).padStart(2,'0')}`
						match.MD_DDMM =
							`${String(time.getDate()).padStart(2,'0')} ${time.toDateString().split(" ")[1]}`
						match.SLIP_DATE =
							`@ ${match.MD_DDMM} ${time.getFullYear()} ${String(time.getHours()%12).padStart(2,'0')}:${String(time.getMinutes()).padStart(2,'0')}`
						let match_attr = _this.$toolbox.fake_deep_clone(match.ATTR)
						let show_attr = []
						let attr_type_list = match_attr.map(attr => {
							return attr.MATCH_ATTR_TYPE
						})
						all_attr_type_list.forEach(attr_type => {
							let index = attr_type_list.indexOf(attr_type)
							if (index > -1) {
								let attr = match_attr[index]
								attr.host_selected = _this.mix_slip.includes(
										`${attr.MATCH_ATTR_ID}_host`) &&
									_this.isLogin;
								attr.guest_selected = _this.mix_slip.includes(
										`${attr.MATCH_ATTR_ID}_guest`) &&
									_this.isLogin;
								attr.draw_selected = _this.mix_slip.includes(
										`${attr.MATCH_ATTR_ID}_draw`) &&
									_this.isLogin;
								if ([_this.bet_type.SINGLE_BODY, _this.bet_type.MIX_BODY].includes(attr
										.MATCH_ATTR_TYPE)) {
									match.LOSE_TEAM = attr.LOSE_TEAM
								}
								show_attr.push(attr)
							} else {
								// 添加不存在的赔率
								show_attr.push({
									disabled: true,
									MATCH_ATTR_TYPE: attr_type,
								})
							}
						})
						match.ATTR = show_attr
						let match_index = server_leagues.indexOf(match.LEAGUE)
						if (match_index > -1) {
							league_list[match_index][`include_${match.MATCH_DAY}`] = true
							league_list[match_index].match_list.push(match)
						}
					})
					_this.league_list = league_list
					_this.$nextTick(() => {
						_this.handle_scroll()
						// _this.scroll_top = 1
					})
					// console.log(league_list)
				}
			},
			filter_matches_by_date() {
				// Filter existing data based on selected date
				if (this.all_matches_data) {
					// this.loadding_data(this.all_matches_data);
				}
			},
			reset_attr_select(attr) {
				attr.host_selected = false;
				attr.guest_selected = false;
				attr.draw_selected = false;
			},
			reset() {
				let _this = this;
				_this.league_list.forEach((league, index) => {
					league.match_list.forEach((match, _index) => {
						match.ATTR.forEach(attr => {
							_this.reset_attr_select(attr)
						})
						Vue.set(_this.league_list[index].match_list, _index, match);
					})
				})
				_this.mix_slip = []
				uni.removeStorageSync('mix_slip')
				_this.hide_bets_slip = true
				_this.match_ref.num = 0;
				_this.amount = _this.$store.state.configs[`${_this.match_ref.mixed?'mix':'single'}_min`]
				// 重置优惠券相关状态
				_this.available_coupons = []
				_this.selected_coupon = null
				_this.show_coupon_dropdown = false
				// 重置优惠钱包优先使用状态
				_this.use_promotion_wallet = false
			},
			submit() {
				if (this.$toolbox.click_too_fast(2)) return
				var _this = this;
				let url = `/order/${_this.match_ref.mixed?'mix':'single'}_bet`

				//校验是否超出限额
				let min = _this.match_ref.mixed ? _this.mix_min : _this.single_min
				let max = _this.match_ref.mixed ? _this.mix_max : _this.single_max
				let content = ''
				if (_this.amount > parseFloat(_this.$store.state.userInfo.money.replaceAll(',', ''))) {
					content = _this.$t('Sorry, your current balance is not enough for this bet')
				}
				if (_this.amount > max) {
					content = (_this.match_ref.mixed ? _this.$t('mix_max') : _this.$t('single_max')) +
						` ( ${max} )`;
				}
				if (_this.amount < min) {
					content = (_this.match_ref.mixed ? _this.$t('mix_min') : _this.$t('single_min')).replace('xxx', min);
				}
				if (_this.match_ref.mixed && _this.bet_list.length < 2) {
					content = _this.$t('at_least_2_game')
				}
				if (_this.match_ref.mixed && _this.bet_list.length > 12) {
					content = _this.$t('at_most_12_game')
				}
				if (content) {
					uni.showModal({
						title: 'Tips',
						content: content,
						showCancel: false,
						confirmText: 'ok',
						success: function(res) {}
					});
					return
				}
				uni.showLoading({
					title: 'loading',
				})

				clearInterval(this.confirmIntervalId)
				var paras = [];
				var checkAttrs = {}
				_this.bet_list.forEach(element => {
					var temp = {
						matchId: element.MATCH_ID,
						attrType: element.sa.MATCH_ATTR_TYPE,
						betType: element.sa.draw_selected ? 3 : element.sa.host_selected || element.sa
							.over_selected ? 1 : 2,
						amount: parseInt(_this.amount)
					}
					checkAttrs[element.sa.MATCH_ATTR_ID] = element.sa;
					checkAttrs[element.sa.MATCH_ATTR_ID].BET_TYPE = element.sa.draw_selected ? 3 : element
						.sa
						.host_selected || element.sa.over_selected ? 1 : 2
					paras.push(temp)
				})
				var changeList = [];
				_this.$http.post('/order/check_odds', {
					attrs: checkAttrs
				}, (res) => {
					if (res.statusCode == 200) {
						changeList = res.data.items;
						if (changeList.length > 0) {
							uni.showModal({
								title: 'tips',
								content: _this.$t('odds_change'),
								showCancel: false,
								confirmText: 'အတည်ပြုမည်',
								success: function(res) {
									_this.bet_list.forEach((element, index, ) => {
										changeList.forEach(ele => {
											if (ele.MATCH_ATTR_ID == element.sa
												.MATCH_ATTR_ID) {
												var DRAW_BUNKO = ele
													.DRAW_BUNKO ==
													'0' ? '+' : '-';

												element.sa.ODDS_DESC = '(' +
													ele
													.LOSE_BALL_NUM +
													DRAW_BUNKO + ele
													.DRAW_ODDS +
													')' //(2-50)

												element.sa.LOSE_BALL_NUM = ele
													.LOSE_BALL_NUM;
												element.sa.DRAW_BUNKO = ele
													.DRAW_BUNKO;
												element.sa.DRAW_ODDS = ele
													.DRAW_ODDS;
												element.sa.ODDS = ele.ODDS;
												element.sa.ODDS_GUEST = ele
													.ODDS_GUEST;
												Vue.set(_this.bet_list,
													index,
													element)
											}
										})
									})
									uni.hideLoading()
									return;
								}
							})
						} else {
							// 准备请求参数
							const requestParams = {
								bets: paras,
								totalAmount: parseInt(_this.amount)
							};

							// 如果选择了优惠券，添加coupon_id到请求参数
							if (_this.selected_coupon && _this.selected_coupon.member_coupon_id) {
								requestParams.coupon_id = _this.selected_coupon.member_coupon_id;
							}

							// 如果勾选了使用优惠钱包，添加use_promotion_wallet标记
							if (_this.use_promotion_wallet) {
								requestParams.use_promotion_wallet = true;
							}

							_this.$http.post(url, requestParams, (res) => {
								uni.hideLoading();
								if (res.statusCode == 200) {
									var userInfo = _this.$store.state.userInfo

									// 计算实际扣除金额（考虑优惠券折扣）
									let actualDeduction = parseInt(_this.amount);
									if (_this.selected_coupon && _this.selected_coupon.bonus_amount) {
										// 实际扣除 = 下注金额 - 优惠券金额
										actualDeduction = parseInt(_this.amount) - parseInt(_this
											.selected_coupon.bonus_amount);
										// 确保不会扣除负数
										if (actualDeduction < 0) {
											actualDeduction = 0;
										}
									}

									// 根据是否使用优惠钱包，从不同的余额扣除
									if (_this.use_promotion_wallet) {
										// 从优惠钱包扣除
										let promotionMoney = _this.$toolbox.num_format(
											userInfo.money_promotion, 0, true);
										userInfo.money_promotion = _this.$toolbox.num_format(
											parseInt(promotionMoney) - actualDeduction);
									} else {
										// 从主钱包扣除
										let money = _this.$toolbox.num_format(
											userInfo.money, 0, true);
										userInfo.money = _this.$toolbox.num_format(
											parseInt(money) - actualDeduction);
									}

									_this.reset();
									_this.$store.dispatch('saveUserInfo',
										userInfo);
									uni.showModal({
										content: _this.$t('bettingSuccess'),
										title: tips,
										showCancel: false,
										confirmText: 'OK',
										success: function() {
											//把选过的比赛刷掉
											_this.hide_bets_slip = true
										}
									});
								} else {
									var tips = _this.$t(res.data.message);
									uni.showModal({
										title: 'Tips',
										content: tips,
										showCancel: false,
										confirmText: 'ok',
										success: function(res) {}
									});
								}
							})
						}
					}
				})
			},

			// 使用优惠券下单
			submitWithPromotion() {
				if (this.$toolbox.click_too_fast(2)) return
				var _this = this;

				// 验证优惠券代码
				if (!_this.promotion_code || _this.promotion_code.trim() === '') {
					uni.showModal({
						title: 'Tips',
						content: _this.$t('Please enter promotion code'),
						showCancel: false,
						confirmText: 'OK'
					});
					return
				}

				// 只支持单笔下单
				if (_this.match_ref.mixed) {
					uni.showModal({
						title: 'Tips',
						content: 'Promotion code can only be used for single bets',
						showCancel: false,
						confirmText: 'OK'
					});
					return
				}

				// 校验至少选择一场比赛
				if (_this.bet_list.length === 0) {
					uni.showModal({
						title: 'Tips',
						content: _this.$t('Please select at least one match'),
						showCancel: false,
						confirmText: 'OK'
					});
					return
				}

				uni.showLoading({
					title: 'Processing...',
				})

				clearInterval(this.confirmIntervalId)
				var paras = [];
				var checkAttrs = {}
				_this.bet_list.forEach(element => {
					var temp = {
						matchId: element.MATCH_ID,
						attrType: element.sa.MATCH_ATTR_TYPE,
						betType: element.sa.draw_selected ? 3 : element.sa.host_selected || element.sa
							.over_selected ? 1 : 2,
					}
					checkAttrs[element.sa.MATCH_ATTR_ID] = element.sa;
					paras.push(temp);
				})

				_this.$http.post('/order/promo_bet', {
					bets: paras,
					promotion_code: _this.promotion_code.trim()
				}, (res) => {
					uni.hideLoading();
					if (res.statusCode == 200) {
						var userInfo = _this.$store.state.userInfo
						// 更新促销余额
						if (res.data.new_promotion_balance !== undefined) {
							userInfo.money_promotion = res.data.new_promotion_balance
						}
						_this.reset();
						_this.$store.dispatch('saveUserInfo', userInfo);
						uni.showModal({
							content: _this.$t('bettingSuccess') + '\n' + _this.$t(
								'Using promotion code: ') + _this.promotion_code,
							title: 'Success',
							showCancel: false,
							confirmText: 'OK',
							success: function() {
								_this.hide_bets_slip = true
							}
						});
					} else {
						var tips = _this.$t(res.data.message);
						uni.showModal({
							title: 'Tips',
							content: tips,
							showCancel: false,
							confirmText: 'OK'
						});
					}
				}, (err) => {
					uni.hideLoading();
					uni.showModal({
						title: 'Tips',
						content: _this.$t('Network error, please try again'),
						showCancel: false,
						confirmText: 'OK'
					});
				})
			},

			to_deposit() {
				uni.navigateTo({
					url: '/pages/ucenter/charge',
					complete(res) {}
				})
			},
			show_login_toast() {
				let _this = this
				if (!this.login_success) return
				let title = `${this.$t('Congratulations')}!\r\n${this.$t('login_success')}`
				if (this.register_success) {
					title = `${this.$t('Congratulations')}!\r\n${this.$t('register_success')}`
				}
				uni.showToast({
					title: title,
					icon: 'none'
				})
				uni.removeStorageSync('login_success')
			},
		},
		onLoad(options) {
			this.match_ref.mixed = options.mix === '1'
			if (this.match_ref.mixed) {
				this.amount_list = [500, 50000, 100000]
			}

		},
		created() {},
		mounted() {
			if (this.match_ref.mixed) {
				this.mix_slip = uni.getStorageSync('mix_slip') || []
			}
			this.get_list()
			this.show_login_toast()
			let _this = this
			if (_this.isLogin) {
				_this.intervalId = setInterval(function() {
					let page_list = getCurrentPages()
					if (page_list[page_list.length - 1].route.indexOf('pages/match/home') < 0) {
						clearInterval(_this.intervalId);
						_this.intervalId = null
					} else if (_this.league_list.length > 0) {
						_this.updateOdds()
					}
				}, 60 * 1000);
			}
		},
		onBackPress() {
			this.hide_league_filter = true
			this.hide_match_detail = true
			this.hide_bets_slip = true
			this.hide_login_modal = true
			this.hide_fuzzy_search = true
			return true;
		},
		//离开当前页面后执行
		destroyed: function() {
			clearInterval(this.intervalId);
		},
	}
</script>

<style>
	.detail-box-shadow {
		box-shadow: rgba(60, 64, 67, 0.3) 0px 1px 2px 0px, rgba(60, 64, 67, 0.15) 0px 1px 3px 1px;
	}


	.row-line {
		height: 2vw;
		width: 12vw;
		border-radius: 100px;
	}

	.single-bottom {
		border-top-right-radius: 5vw;
		border-top-left-radius: 5vw;
	}

	.single-mask {
		background: none;
		height: 100vh;
		opacity: .5;
		background-color: black;
	}

	.deposit-btn {
		position: relative;
		display: inline-flex;
		align-items: center;
		justify-content: center;
		box-sizing: border-box;
		padding: 0 8upx;
		height: 35px;
		line-height: 1;
		text-align: center;
		text-decoration: none;
		overflow: visible;
		margin-left: initial;
		transform: translate(0px, 0px);
		margin-right: initial;
	}

	.match-animation-enter-active,
	.match-animation-leave-active {
		transition: all .5s ease;
	}

	.match-animation-enter-from,
	.match-animation-leave-to {
		opacity: 0;
		/* transform: translateY(-30px); */
	}

	.page {
		/* height: calc(100vh - env(safe-area-inset-bottom)); */
		display: block;
		flex: 1;
	}

	.dialog-wrapper {
		z-index: 10;
		position: fixed;
		left: 0;
		bottom: 0;
		height: 100%;
		/* height: calc(100vh - 55px - env(safe-area-inset-bottom) ); */
		width: 100vw;
	}

	.dialog-wrapper.slip {
		z-index: 15 !important;
		/* height: calc(100vh - 55px ); */
		/* background-color: white; */
	}


	.league-match-attr.detail {
		font-weight: 400;
		line-height: 1.5;
		height: 75px;
		width: 100%;
		max-width: 100%;
	}

	.league-match-attr-type.detail {
		font-size: 16px;
		font-weight: 700;
		line-height: 100%;
		transform: scale(1);
	}

	.league-match-attr-type.text-grey {
		color: rgba(0, 0, 0, 0.38) !important;
	}

	.league-match-attr-detail.detail {
		height: 65px;
		width: 50%;
		margin: 0px 10px;
		padding: 0px;
		border-radius: 5px;
		max-width: 100%;
	}

	.league-match-attr-detail-up.detail {
		font-weight: 700;
		font-size: 10px;
		transform: scale(1);
		padding: 2px;
		height: 25px;
	}

	.league-match-attr-detail-down.detail {
		transform: scale(1);
		font-size: 0.875rem;
		width: 100%;
		border-radius: 0px 0px 5px 5px;
		height: calc(100% - 25px);
		display: grid;
		place-items: center;
	}

	.league-match-attr-detail-down.disable {
		color: rgba(0, 0, 0, 0.38) !important;
		font-size: 8px;
	}

	.league-match-attr-detail-down.text-grey {
		color: rgba(0, 0, 0, 0.38) !important;
	}


	.cu-avatar {
		background-color: none;
	}

	/* 优惠券下拉选择框样式 */
	.coupon-select-wrapper {
		position: relative;
		width: 100%;
	}

	.coupon-select-input {
		cursor: pointer;
		transition: all 0.3s;
		min-height: 40px;
	}

	.coupon-select-input:active {
		opacity: 0.8;
	}

	.coupon-dropdown-list {
		animation: dropdown-slide 0.2s ease-out;
	}

	.coupon-dropdown-item {
		cursor: pointer;
		transition: background-color 0.2s;
	}

	.coupon-dropdown-item:hover {
		opacity: 0.9;
	}

	.coupon-dropdown-item:last-child {
		border-bottom: none !important;
	}

	.rotate-180 {
		transform: rotate(180deg);
		transition: transform 0.3s;
	}

	@keyframes dropdown-slide {
		from {
			opacity: 0;
			transform: translateY(-10px);
		}

		to {
			opacity: 1;
			transform: translateY(0);
		}
	}

	/* 自定义Checkbox样式 */
	.custom-checkbox {
		width: 18px;
		height: 18px;
		border: 2px solid #999;
		border-radius: 3px;
		background-color: transparent;
		display: flex;
		align-items: center;
		justify-content: center;
		transition: all 0.2s;
		flex-shrink: 0;
	}

	.custom-checkbox-checked {
		background-color: #0C356A;
		border-color: #0C356A;
	}

	.custom-checkbox-icon {
		color: #fff;
		font-size: 14px;
		font-weight: bold;
		line-height: 1;
	}

	.custom-checkbox-disabled {
		opacity: 0.4;
		cursor: not-allowed !important;
		border-color: #ccc;
	}
</style>