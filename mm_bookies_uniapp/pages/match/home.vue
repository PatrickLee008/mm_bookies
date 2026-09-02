<template>
	<view class="match-page-container">
		<!-- from tangjq--- 使用新的统一header组件 -->
		<zw-header @headerHeightChange="onHeaderHeightChange"></zw-header>

		<!-- 实时消息弹窗提醒（全局挂载点） -->
		<message-notification></message-notification>

		<!-- from tangjq--- header占位元素，防止内容被遮挡 -->
		<view class="header-placeholder" :style="{ height: headerHeight + 'px', transition: 'height 0.3s ease' }">
		</view>

		<!-- <view class="flex-row mybg-lprimary justify-around padding-tb-sm ">
			<button class="cu-btn sm width-40 myfont-10px" :class="{'mybg-active':!tomorrow,}" @click="select_date(false)">{{$t('today')}}</button>
			<button class="cu-btn sm width-40 myfont-10px" :class="{'mybg-active':tomorrow,}" @click="select_date(true)">{{$t('tomorrow')}}</button>
		</view> -->
		<!-- <view class="ticket-wrapper cu-avatar" v-show="bet_list.length > 0 && match_ref.mixed" @click="show_bet_slip">
			<view class='ticket-tag'>{{bet_list.length}}</view>
			<view class="ticket width-30px height-30px "></view>
		</view> -->

		<!-- from tangjq--- 新的搜索框和筛选按钮布局 -->
		<view class="new-header-wrapper">
			<view class="new-search-bar">
				<theme-icon name="search" class="search-icon"
					color="var(--theme-icon-primary, var(--theme-primary))"></theme-icon>
				<input class="search-input" placeholder-style="font-style:italic;color:var(--theme-primary)" type="text"
					:placeholder="$t('search_by_team')" v-model="searchKeyword" @input="handleSearchInput" />
				<theme-icon name="close" class="clear-icon" color="var(--theme-icon-secondary, var(--theme-secondary))"
					v-show="searchKeyword" @tap="clearSearch"></theme-icon>
			</view>
			<view class="filter-btn" @tap="hide_league_filter = false">
				<view>{{$t('league')}}</view>
				<view class="filter-icon">
					<view class="filter-line"></view>
					<view class="filter-line"></view>
					<view class="filter-line"></view>
				</view>
				<view class='filter-badge' v-if="league_checked_count > 0">
					{{ league_checked_count > 99 ? '99+' : league_checked_count }}
				</view>
			</view>
		</view>

		<!-- from tangjq--- 调整scroll-view高度，移除today/tomorrow tab高度，为mix模式底部栏预留空间 -->
		<scroll-view scroll-y class="page padding-lr padding-bottom-1px text-bold"
			:class="{ 'page-mixed': match_ref.mixed }" style="line-height: 1.5;"
			@scroll="onScrollHandler" @scrolltoupper="handleHeaderTop">
			<!-- from tangjq--- 重构联赛和比赛卡片布局，严格按照设计稿 -->
			<view class="flex-column" v-for="(league,index) in league_list" :key="index"
				v-show='league.checked  && league[`include_${tomorrow?"tomorrow":"today"}`] && isLeagueMatchSearch(league)'>
				<!-- 联赛标题栏 -->
				<view class="new-league-header" @click="league.show_match = !league.show_match">
					<view class="league-left">
						<image class="league-icon" :src="league.league_icon || defaultLeagueIcon" mode="aspectFit">
						</image>
						<text class="league-name">{{league.name}}</text>
					</view>
					<view class="league-right">
						<image class="league-toggle-icon" :class="{ 'league-fold-icon': league.show_match }"
							src="/static/image/single/leage_unfold.svg" mode="aspectFit"></image>
					</view>
				</view>

				<view v-show="league.show_match" class="width-100">
						<!-- 比赛卡片 -->
						<view class="new-match-card" v-for="(match,_index) in league.match_list" :key="_index"
							v-show="match.checked && match.MATCH_DAY ===(!tomorrow?'today':'tomorrow') && isMatchSearch(match)">
							<view class="match-summary">
								<view class="match-teams">
									<view class="match-logo-row">
										<view class="team-logo-frame"
											:class="{ 'team-logo-frame-expanded': match.expanded }">
											<image :src="match.show_image?match.home_logo:''" lazy-load
												class="team-logo" :class="{ 'team-logo-expanded': match.expanded }"
												@error="error_pic(match,'home')" />
										</view>
										<view class="match-datetime">
											{{match.MD_DATE_TIME}}
										</view>
										<view class="team-logo-frame"
											:class="{ 'team-logo-frame-expanded': match.expanded }">
											<image :src="match.show_image?match.away_logo:''" lazy-load
												class="team-logo" :class="{ 'team-logo-expanded': match.expanded }"
												@error="error_pic(match,'away')" />
										</view>
									</view>

									<view class="match-name-row">
										<view class="team-name" :class="{'text-red':match.LOSE_TEAM ==='1',}">
											{{match.HOST_TEAM}}
										</view>
										<text class="vs-text">vs</text>
										<view class="team-name" :class="{'text-red':match.LOSE_TEAM ==='2',}">
											{{match.GUEST_TEAM}}
										</view>
									</view>
								</view>
							</view>

							<!-- from tangjq--- 投注选项区域：循环显示所有投注选项 -->
							<view class="new-bet-options">
								<!-- 循环显示所有投注选项，前2个始终显示，其余根据expanded状态显示 -->
								<template v-for="(attr, attr_index) in match.ATTR">
									<view class="bet-row" v-if="!attr.disabled && (attr_index < 2 || match.expanded)"
										:key="attr_index">
										<!-- HDP类型 -->
										<template
											v-if="attr.MATCH_ATTR_TYPE == bet_type.SINGLE_BODY || attr.MATCH_ATTR_TYPE == bet_type.MIX_BODY">
											<view class="bet-type-label">
												<text>H</text>
												<text>D</text>
												<text>P</text>
											</view>
											<view class="bet-buttons">
												<view class="bet-btn bet-btn-small"
													:class="{'bet-btn-selected':attr.host_selected,}"
													@click="betClick('host',index,_index,attr_index,attr)">
													<text class="bet-text-small">Home</text>
													<!-- <text class="bet-odds-small"
														v-if="!match_ref.mixed">{{formatOdds(attr.ODDS)}}</text> -->
												</view>
												<view class="bet-odds">
													<text>{{calc_real_odds(attr)}}</text>
												</view>
												<view class="bet-btn bet-btn-small"
													:class="{'bet-btn-selected':attr.guest_selected,}"
													@click="betClick('guest',index,_index,attr_index,attr)">
													<text class="bet-text-small">Away</text>
													<!-- <text class="bet-odds-small"
														v-if="!match_ref.mixed">{{formatOdds(attr.ODDS)}}</text> -->
												</view>
											</view>
										</template>

										<!-- O/U类型 -->
										<template
											v-else-if="attr.MATCH_ATTR_TYPE == bet_type.SINGLE_GOAL || attr.MATCH_ATTR_TYPE == bet_type.MIX_GOAL">
											<view class="bet-type-label">
												<text>O</text>
												<text>U</text>
											</view>
											<view class="bet-buttons">
												<view class="bet-btn bet-btn-small"
													:class="{'bet-btn-selected':attr.host_selected,}"
													@click="betClick('host',index,_index,attr_index,attr)">
													<text class="bet-text-small">Over</text>
													<!-- <text class="bet-odds-small"
														v-if="!match_ref.mixed">{{formatOdds(attr.ODDS)}}</text> -->
												</view>
												<view class="bet-odds">
													<text>{{attr.LOSE_BALL_NUM}}+{{attr.DRAW_ODDS}}</text>
												</view>
												<view class="bet-btn bet-btn-small"
													:class="{'bet-btn-selected':attr.guest_selected,}"
													@click="betClick('guest',index,_index,attr_index,attr)">
													<text class="bet-text-small">Under</text>
													<!-- <text class="bet-odds-small"
														v-if="!match_ref.mixed">{{formatOdds(attr.ODDS)}}</text> -->
												</view>
											</view>
										</template>

										<!-- 1X2类型 -->
										<template v-else-if="attr.MATCH_ATTR_TYPE == bet_type.SINGLE_WDL">
											<view class="bet-type-label">
												<text>1</text>
												<text>X</text>
												<text>2</text>
											</view>
											<view class="bet-buttons bet-buttons-three">
												<view class="bet-btn bet-btn-small"
													:class="{'bet-btn-selected':attr.host_selected,}"
													@click="betClick('host',index,_index,attr_index,attr)">
													<text class="bet-text-small">Home</text>
													<text class="bet-odds-small"
														v-if="!match_ref.mixed">{{formatOdds(attr.ODDS)}}</text>
												</view>
												<view class="bet-btn bet-btn-small"
													:class="{'bet-btn-selected':attr.draw_selected,}"
													@click="betClick('draw',index,_index,attr_index,attr)">
													<text class="bet-text-small">Draw</text>
													<text class="bet-odds-small"
														v-if="!match_ref.mixed">{{formatOdds(attr.DRAW_ODDS)}}</text>
												</view>
												<view class="bet-btn bet-btn-small"
													:class="{'bet-btn-selected':attr.guest_selected,}"
													@click="betClick('guest',index,_index,attr_index,attr)">
													<text class="bet-text-small">Away</text>
													<text class="bet-odds-small"
														v-if="!match_ref.mixed">{{formatOdds(attr.ODDS_GUEST)}}</text>
												</view>
											</view>
										</template>
									</view>
								</template>
							</view>

							<!-- from tangjq--- 展开/收起按钮，仅当有超过2个投注选项时显示 -->
							<view class="match-expand-btn" v-if="get_available_bet_count(match) > 2"
								@click.stop="toggle_match_expand(match)">
								<image class="match-toggle-icon"
									:class="{ 'match-toggle-icon-expanded': match.expanded }"
									src="/static/image/single/unfold.svg" mode="aspectFit"></image>
							</view>
						</view>
					</view>

				<!-- from tangjq--- 广告图显示在第一个可见联赛和第二个联赛之间 -->
				<template v-if="index === firstVisibleLeagueIndex && advertisements.length > 0">
					<view class="ad-banner-wrapper" v-for="(ad, adIndex) in advertisements" :key="`ad-${adIndex}`"
						@click="handleAdClick(ad)">
						<image class="ad-banner-image"
							:src="ad.image_urls && ad.image_urls.length > 0 ? ad.image_urls[0] : ''" mode="scaleToFill">
						</image>
					</view>
				</template>
			</view>
			<view class="match-list-bottom-spacer"
				:class="{ 'match-list-bottom-spacer-mixed': match_ref.mixed }"></view>
		</scroll-view>

		<!-- from tangjq--- 混合投注模式的底部栏 -->
		<view class="mix-bottom-bar" v-if="match_ref.mixed">
			<view class="total-matches-btn">
				<text class="total-text">Total Matches</text>
				<text class="total-count">{{bet_list.length}}</text>
			</view>
			<view class="confirm-btn" @click="show_bet_slip">
				<text class="confirm-text">Confirm</text>
			</view>
		</view>

		<!-- from tangjq--- 单注详情弹窗，按照设计稿重构 -->
		<view class="new-detail-popup" v-show="!hide_match_detail">
			<!-- from tangjq--- 遮罩层 -->
			<view class="detail-popup-mask" @click="hide_match_detail = true"></view>

			<!-- from tangjq--- 弹窗内容容器 -->
			<view class="detail-popup-container">
				<!-- 标题栏 -->
				<view class="detail-header">
					<text class="detail-title">Details</text>
				</view>

				<!-- 内容区域 -->
				<view class="detail-content">
					<!-- 比赛信息卡片 -->
					<view class="detail-match-card">
						<view class="detail-datetime">
							{{match_ref.match_detail.MD_DATE_TIME}}
						</view>
						<view class="detail-teams">
							<view class="detail-team">
								<image :src="match_ref.match_detail.home_logo" lazy-load class="detail-team-logo"
									@error="error_pic(match_ref.match_detail,'home')"></image>
								<text class="detail-team-name"
									:class="{'text-red':match_ref.match_detail.LOSE_TEAM ==='1',}">
									{{match_ref.match_detail.HOST_TEAM}}
								</text>
							</view>
							<text class="detail-vs">vs</text>
							<view class="detail-team">
								<image :src="match_ref.match_detail.away_logo" lazy-load class="detail-team-logo"
									@error="error_pic(match_ref.match_detail,'away')"></image>
								<text class="detail-team-name"
									:class="{'text-red':match_ref.match_detail.LOSE_TEAM ==='2',}">
									{{match_ref.match_detail.GUEST_TEAM}}
								</text>
							</view>
						</view>
					</view>

					<!-- 其他内容保持原样，继续向下滚动 -->
				</view>
			</view>
		</view>

		<!-- from tangjq--- 重构下单详情弹窗 -->
		<view class="new-bet-slip-popup" v-show="!hide_bets_slip">
			<!-- from tangjq--- 遮罩层（单注和混合模式都有） -->
			<view class="bet-slip-mask" @click="hide_bets_slip = true"></view>

			<!-- from tangjq--- 弹窗内容 -->
			<view class="bet-slip-container" :class="{'mix-mode': match_ref.mixed}">
				<!-- 标题栏 -->
				<view class="bet-slip-header">
					<text class="bet-slip-title">Details</text>
				</view>

				<!-- from tangjq--- 混合投注：可滚动的比赛列表区域 -->
				<scroll-view scroll-y class="bet-slip-scroll" v-if="match_ref.mixed">
					<view class="mix-matches-list">
						<view class="mix-match-item" v-for="(match,index) in bet_list" :key='index'>
							<!-- from tangjq--- 比赛时间 -->
							<view class="mix-match-datetime">
								<text>{{match.SLIP_DATE && match.SLIP_DATE.includes('@') ? match.SLIP_DATE.split('@')[0] : match.SLIP_DATE}}
									{{match.SLIP_DATE && match.SLIP_DATE.includes('@') ? match.SLIP_DATE.split('@')[1] : ''}}</text>
							</view>

							<view class="mix-match-info">
								<!-- from tangjq--- 队伍对阵 -->
								<view class="mix-match-row mix-teams-row">
									<text class="mix-team-name"
										:class="{'text-red':match.LOSE_TEAM=='1',}">{{match.HOST_TEAM}}</text>
									<text class="mix-vs">vs</text>
									<text class="mix-team-name"
										:class="{'text-red':match.LOSE_TEAM=='2',}">{{match.GUEST_TEAM}}</text>
								</view>

								<!-- from tangjq--- 投注类型 + 赔率（2列） -->
								<view class="mix-match-row">
									<text
										class="mix-row-label">{{bet_type.MIX_BODY == match.sa.MATCH_ATTR_TYPE ?'HDP':'O/U'}}</text>
									<text class="mix-row-value">{{calc_real_odds(match.sa)}}</text>
								</view>

								<!-- from tangjq--- Bet: + 选中的队伍名（2列） -->
								<view class="mix-match-row">
									<text class="mix-row-label">Bet :</text>
									<text class="mix-row-value mix-bet-choice">{{bet_content(match)}}</text>
								</view>
							</view>
						</view>
					</view>
				</scroll-view>

				<!-- from tangjq--- 单注：比赛信息（完整版，参考设计稿） -->
				<view class="single-match-info" v-if="!match_ref.mixed && match_ref.bet_match">
					<!-- from tangjq--- 比赛时间 -->
					<view class="match-time-row">
						<text
							class="match-time">{{match_ref.bet_match.SLIP_DATE && match_ref.bet_match.SLIP_DATE.includes('@') ? match_ref.bet_match.SLIP_DATE.split('@')[1] : ''}}</text>
					</view>

					<!-- from tangjq--- 队伍图标和名称 -->
					<view class="teams-row">
						<view class="team-section">
							<image class="team-logo"
								:src="match_ref.bet_match.show_image ? match_ref.bet_match.home_logo : ''" lazy-load
								mode="aspectFit" @error="error_pic(match_ref.bet_match,'home')"></image>
							<text class="team-name"
								:class="{'text-red':match_ref.bet_match.LOSE_TEAM=='1'}">{{match_ref.bet_match.HOST_TEAM}}</text>
						</view>
						<text class="vs-text">VS</text>
						<view class="team-section">
							<image class="team-logo"
								:src="match_ref.bet_match.show_image ? match_ref.bet_match.away_logo : ''" lazy-load
								mode="aspectFit" @error="error_pic(match_ref.bet_match,'away')"></image>
							<text class="team-name"
								:class="{'text-red':match_ref.bet_match.LOSE_TEAM=='2'}">{{match_ref.bet_match.GUEST_TEAM}}</text>
						</view>
					</view>

					<!-- from tangjq--- 投注类型详情 -->
					<view class="bet-detail-row">
						<text
							class="bet-type">{{match_ref.bet_match.sa && (bet_type.SINGLE_BODY == match_ref.bet_match.sa.MATCH_ATTR_TYPE || bet_type.MIX_BODY == match_ref.bet_match.sa.MATCH_ATTR_TYPE) ? 'HDP' : (bet_type.SINGLE_WDL == match_ref.bet_match.sa.MATCH_ATTR_TYPE ? '1X2' : 'O/U')}}</text>
						<text
							class="bet-odds">{{match_ref.bet_match.sa ? (bet_type.SINGLE_WDL == match_ref.bet_match.sa.MATCH_ATTR_TYPE ? (match_ref.bet_match.sa.draw_selected ? match_ref.bet_match.sa.DRAW_ODDS : (match_ref.bet_match.sa.guest_selected ? match_ref.bet_match.sa.ODDS_GUEST : match_ref.bet_match.sa.ODDS)) : calc_real_odds(match_ref.bet_match.sa)) : ''}}</text>
						<!-- <text
							class="bet-time">{{match_ref.bet_match.SLIP_DATE && match_ref.bet_match.SLIP_DATE.includes('@') ? match_ref.bet_match.SLIP_DATE.split('@')[1] : ''}}</text> -->
					</view>

					<!-- from tangjq--- 投注选项 -->
					<view class="bet-choice-row">
						<text class="mix-row-label">Bet :</text>
						<text class="choice-team">{{bet_content(match_ref.bet_match)}}</text>
						<!-- <text class="choice-type"></text> -->
					</view>
				</view>

				<!-- from tangjq--- 投注信息和输入区域（固定在底部，不滚动） -->
				<view class="bet-input-section">
					<!-- Bet Time 和 Potential Winnings -->
					<view class="bet-info-rows">
						<view class="bet-info-row">
							<text class="info-label">{{$t('Bet Time')}}</text>
							<text class="info-value">{{bet_time}}</text>
						</view>
						<view class="bet-info-row">
							<text class="info-label">{{$t('Potential Winnings')}}</text>
							<text class="info-value">{{$toolbox.num_format(calc_benefit(match_ref.bet_match))}}</text>
						</view>
					</view>

					<!-- from tangjq--- Main Wallet / Promo Wallet 并排按钮，参考 MPL_Detial_Overlay.png -->
					<view class="wallet-buttons">
						<view class="wallet-btn wallet-btn-main" :class="{'wallet-btn-active': !use_promotion_wallet}"
							@click="use_promotion_wallet && togglePromotionWallet()">
							<text class="wallet-btn-label">{{$t('main_wallet')}}</text>
							<text class="wallet-btn-value">{{$toolbox.floor_format($store.state.userInfo.money)}}</text>
						</view>
						<view class="wallet-btn wallet-btn-promo"
							:class="{'wallet-btn-active': use_promotion_wallet, 'wallet-btn-disabled': !canUsePromotionWallet}"
							@click="canUsePromotionWallet && !use_promotion_wallet && togglePromotionWallet()">
							<text class="wallet-btn-label">{{$t('promotion_wallet')}}</text>
							<text
								class="wallet-btn-value">{{$toolbox.floor_format($store.state.userInfo.money_promotion || 0)}}</text>
						</view>
					</view>

					<!-- 输入框 -->
					<view class="bet-amount-input">
						<input type="number" placeholder="Please enter bet amount" v-model="amount" @input="inputNum"
							class="amount-input" />
					</view>

					<!-- from tangjq--- Min/Max Bet Amount：一行左右两侧，参考 MPL_Detial_Overlay.png -->
					<view class="min-max-bet-row">
						<text class="min-bet-label">Min Bet Amount :
							{{$toolbox.num_format(match_ref.mixed?mix_min:single_min)}}</text>
						<text class="min-bet-label">Max Bet Amount :
							{{$toolbox.num_format(match_ref.mixed?mix_max:single_max)}}</text>
					</view>

					<!-- Cancel 和 Confirm 按钮 -->
					<view class="action-buttons">
						<view class="cancel-btn" @click="hide_bets_slip = true">
							<text class="cancel-text">{{$t('Cancel')}}</text>
						</view>
						<view class="confirm-btn-action"
							:class="{'confirm-active': amount >= (match_ref.mixed?mix_min:single_min)}"
							@click="submit()">
							<text class="confirm-text">{{$t('Confirm')}}</text>
						</view>
					</view>
				</view>
			</view>
		</view>

		<!-- from tangjq--- 保留原有复杂逻辑的下单详情（隐藏，用于保持逻辑） -->
		<scroll-view scroll-y class="dialog-wrapper mycolor-primary slip" v-show="false" @tap.prevent=""
			style="height: 100%; display: none;">
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
					style="bottom: 0;overflow-y: overlay;z-index: 17;display:none;"
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
						<view
							class="flex-row justify-between detail-box-shadow radius-6px margin-bottom-xs myfont-12px gap-5px padding-sm">
								<view class="flex-row justify-start">

									<view class="mybg-active round width-75upx height-65upx align-center flex-column"
										style="">
										<theme-icon name="wallet" class="width-20px"
											color="var(--theme-icon-primary, var(--theme-primary))"></theme-icon>
									</view>
									<view class="flex-column margin-left-sm align-start gap-5px"
										style="align-items: start;">
										<view class="text-light">{{$t('balance')}} ({{$t('main_wallet')}})</view>
										<view>{{$toolbox.floor_format($store.state.userInfo.money)}}</view>
									</view>
								</view>
								<button class="deposit-btn mybg-active mycolor-primary myfont-12px width-30vw"
									@click="to_deposit()">
									<theme-icon name="deposit" class="width-20px margin-right-xs"
										color="var(--theme-icon-secondary, var(--theme-secondary))"></theme-icon>
									<view>{{$t('deposit')}}</view>
								</button>
							</view>
							<!-- Promotion Wallet 显示 -->
							<view
								class="flex-row justify-between detail-box-shadow radius-6px margin-bottom-xs myfont-12px gap-5px padding-sm">
								<view class="flex-row justify-start align-center">
									<view class="mybg-active round width-33px height-65upx align-center flex-column">
										<theme-icon name="wallet" class="width-20px"
											color="var(--theme-icon-primary, var(--theme-primary))"></theme-icon>
									</view>
									<view class="flex-column1 margin-left-sm align-start gap-5px">
										<view class="text-light">{{$t('promotion_wallet')}}</view>
										<view>{{$toolbox.floor_format($store.state.userInfo.money_promotion || 0)}}
										</view>
									</view>
								</view>
								<view class="flex-row1 align-center justify-end" @click="togglePromotionWallet">
									<view class="flex-row align-center gap-5px" style="cursor: pointer;">
										<text class="myfont-10px text-light width-100px" style="line-height: 1.2;">
											{{$t('use_promotion_wallet')}}
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


										<theme-icon name="close" class="width-20px height-20px"
											color="var(--theme-icon-secondary, var(--theme-secondary))"
											@click="clearAmount()">
											<!-- @click="amount=match_ref.mixed?mix_min:single_min"> -->
										</theme-icon>
									</view>
									<button class="deposit-btn mybg-active mycolor-primary myfont-12px width-35vw"
										@click="submit()">
										<image mode="widthFix" class="width-20px margin-right-xs"
											src="/static/image/single/ball.svg"></image>
										<view class="">{{$t('betting')}}</view>
									</button>
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
				</view>
			</view>
		</scroll-view>

		<login-modal ref='login_modal' :hidden.sync="hide_login_modal"></login-modal>
		<league-filter ref='league_filter' :hidden.sync="hide_league_filter" :tomorrow='tomorrow'
			:league_list.sync='league_list'></league-filter>
		<fuzzy-search ref='fuzzy_search' :hidden.sync="hide_fuzzy_search"
			:league_list.sync='league_list'></fuzzy-search>

		<!-- from tangjq--- 投注成功提示弹窗 -->
		<view class="success-popup-wrapper" v-show="!hide_success_popup" @click="hide_success_popup = true">
			<view class="success-popup-container" @click.stop="">
				<!-- 标题栏 -->
				<view class="success-popup-header">
					<text class="success-popup-title">Notice</text>
				</view>

				<!-- 成功提示内容 -->
				<view class="success-popup-content">
					<image class="success-popup-image"
						src="https://images.unsplash.com/photo-1579952363873-27f3bade9f55?w=800" mode="aspectFill">
					</image>
					<text class="success-popup-subtitle">Betting Success</text>
				</view>

				<!-- OK按钮 -->
				<view class="success-popup-footer">
					<view class="success-ok-btn" @click="hide_success_popup = true">
						<text class="success-ok-text">OK</text>
					</view>
				</view>
			</view>
		</view>

		<!-- from tangjq--- 投注失败提示弹窗 -->
		<view class="fail-popup-wrapper" v-show="!hide_fail_popup" @click="hide_fail_popup = true">
			<view class="fail-popup-container" @click.stop="">
				<text class="fail-popup-text">{{ fail_message }}</text>
			</view>
		</view>
	</view>
</template>

<script>
	import config from '../../utils/config.js'
	import Vue from "vue";
	import match_mixins from './components/mixins.js'
	import headerCollapse from '@/mixins/headerCollapse.js'
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
		mixins: [match_mixins, headerCollapse],
		data() {
			return {
				amount_list: [1000, 5000, 10000],
				isLogin: uni.getStorageSync('Authorization') || false,
				animation: '',
				amount: 0,
				hide_league_filter: true,
				hide_match_detail: true,
				hide_bets_slip: true,
				bet_time: '',
				hide_login_modal: true,
				hide_fuzzy_search: true,
				hide_success_popup: true, // from tangjq--- 控制投注成功提示弹窗显示
				hide_fail_popup: true, // from tangjq--- 控制投注失败提示弹窗显示
				fail_message: '', // from tangjq--- 存储失败提示的错误信息
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
				defaultLeagueIcon: 'https://ssl.gstatic.com/onebox/media/sports/logos/udQ6ns69PctCvXqqCPnItA_48x48.png',
				match_ref: {
					mixed: false,
					num: 0,
					bet_match: {
						sa: {}
					},
					match_detail: {},
					league_list: [],
				},
				use_promotion_wallet: false, // 是否优先使用Promotion Wallet
				searchKeyword: '', // from tangjq--- 搜索关键字
				advertisements: [], // from tangjq--- 广告列表
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
					const promotionBalance = this.$toolbox.floor_value(
						this.$store.state.userInfo.money_promotion || 0);

					let message = 'Promotion wallet balance is insufficient for this bet amount';
					let min_limit = this.match_ref.mixed ? this.mix_min : this.single_min
					if (promotionBalance < min_limit) {
						message = `Promotion wallet balance must be at least ${min_limit} MMK`;
					}

					uni.showToast({
						title: message,
						icon: 'none',
						// duration: 2000
					});
				}
			},
			// 监听系统配置变化，动态更新金额选择列表
			configs: {
				handler(val) {
					if (val && (val.single_min || val.single_max)) {
						this.amount_list = this.dynamicAmountList;
					}
				},
				deep: true,
				immediate: true
			},
		},
		computed: {
			// 计算实际支付金额
			actualPaymentAmount() {
				return this.amount;
			},
			// 判断是否可以使用优惠钱包
			canUsePromotionWallet() {
				const promotionBalance = this.$toolbox.floor_value(
					this.$store.state.userInfo.money_promotion || 0);

				// 条件1: 优惠钱包余额必须大于0
				if (promotionBalance <= 0) {
					return false;
				}

				// 条件2: 优惠钱包余额必须大于等于最小下单金额（参考onex2_test，区分single/mix模式）
				let min_limit = this.match_ref.mixed ? this.mix_min : this.single_min
				if (promotionBalance < min_limit) {
					return false;
				}

				// 条件3: 优惠钱包余额必须大于等于当前下单金额
				let requiredAmount = this.amount;

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
			mix_min_count() {
				if (!this.configs.hasOwnProperty('mix_min_count')) {
					this.configs = this.$store.state.configs || uni.getStorageSync('config')
				}
				return parseInt(this.configs.mix_min_count) || 2
			},
			mix_max_count() {
				if (!this.configs.hasOwnProperty('mix_max_count')) {
					this.configs = this.$store.state.configs || uni.getStorageSync('config')
				}
				return parseInt(this.configs.mix_max_count) || 12
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
			firstVisibleLeagueIndex() {
				const dayKey = `include_${this.tomorrow ? 'tomorrow' : 'today'}`
				return this.league_list.findIndex(league =>
					league.checked && league[dayKey] && this.isLeagueMatchSearch(league)
				)
			},
			calc_slip_height() {
				let info = uni.getDeviceInfo()
				if (info.platform == 'ios') {
					return `calc(var(--app-viewport-height, 100vh) - 85px)`
				}
				return 'var(--app-viewport-height, 100vh)'
			},
			// 动态生成金额选择列表，基于系统配置的 min/max 限额
			dynamicAmountList() {
				let min = parseInt(this.configs.single_min) || 3000;
				let max = parseInt(this.configs.single_max) || 10000;
				if (this.match_ref.mixed) {
					min = parseInt(this.configs.mix_min) || 3000;
					max = parseInt(this.configs.mix_max) || 10000;
				}
				const fixedList = [3000, 5000, 10000];

				if (!min || !max || min >= max) {
					return fixedList;
				}

				// 从固定列表中筛选出在 min 和 max 之间的值（不包括两端）
				const middleValues = fixedList.filter((value) => value > min && value < max);

				// 从中间值中选择最多4个
				let selectedMiddle = [];
				if (middleValues.length <= 4) {
					selectedMiddle = middleValues;
				} else {
					const step = middleValues.length / 4;
					for (let i = 0; i < 4; i++) {
						const index = Math.floor(i * step);
						selectedMiddle.push(middleValues[index]);
					}
				}

				// 组合：[最小值, 中间值, 最大值]
				return [min, ...selectedMiddle, max];
			},
		},
		methods: {
			onScrollHandler(e) {
				this.handleHeaderScroll(e)
			},
			// 格式化赔率，保留两位小数
			formatOdds(odds) {
				if (odds == null || odds == undefined) return '0.00';
				const num = parseFloat(odds);
				return num.toFixed(2);
			},
			// 清零金额
			clearAmount() {
				this.amount = 0
			},

			// 切换Promotion Wallet优先使用状态
			togglePromotionWallet() {
				// 使用computed属性检查是否可以使用优惠钱包
				if (!this.canUsePromotionWallet) {
					let message = this.$t('Promotion wallet balance is insufficient');
					const promotionBalance = this.$toolbox.floor_value(
						this.$store.state.userInfo.money_promotion || 0);

					// 计算所需金额
					let requiredAmount = this.amount;

					let min_limit = this.match_ref.mixed ? this.mix_min : this.single_min
					if (promotionBalance < min_limit) {
						message = `Promotion wallet balance must be at least ${min_limit} MMK`;
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
				if (!str) return 0
				return str
			},
			set_amount(amount) {
				this.amount = amount
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

				// mix模式：选择时检查是否超出最大比赛数量限制
				if (_this.match_ref.mixed && select_restult) {
					let match_was_selected = match.ATTR.some(a => a.host_selected || a.guest_selected || a.draw_selected)
					if (!match_was_selected && _this.bet_list.length >= _this.mix_max_count) {
						_this.show_fail_popup(_this.$t('at_most_count').replace('xxx', _this.mix_max_count))
						return
					}
				}

				// 取消本场赛事其他attr已选项
				match.ATTR.forEach(_attr => {
					_this.reset_attr_select(_attr)
				})
				attr[`${type}_selected`] = select_restult

				if (_this.match_ref.mixed) {
					// 混合显示
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
				// 点击赔率时不再自动预填最小投注金额，保持输入框为空，显示占位提示
				_this.amount = ''
				_this.bet_time = _this.formatMatchDateTime(new Date())
				_this.hide_bets_slip = false
			},
			getAdvertisements() {
				var _this = this;
				_this.$http.post('/advertisement/get_by_page', {
					platform: 'mobile',
					page: 'match',
					position: 'banner'
				}, (res) => {
					if (res.statusCode == 200 && res.data.code == 200) {
						_this.advertisements = res.data.data.items || []
					}
				})
			},
			handleAdClick(ad) {
				if (!ad.link_url) return
				this.$toolbox.openAdvertisementLink(ad.link_url, ad.link_target)
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
						if (res.data.items.length == 0) {
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
						// 赔率无变化的项直接跳过，避免整列表无谓的重渲染
						_this.league_list.forEach((league) => {
							league.match_list.forEach((match) => {
								match.ATTR.forEach((attr) => {
									let new_odds = odds_map.get(attr.MATCH_ATTR_ID)
									if (!new_odds) return
									if (attr.ODDS == new_odds.ODDS &&
										attr.ODDS_GUEST == new_odds.ODDS_GUEST &&
										attr.DRAW_ODDS == new_odds.DRAW_ODDS &&
										attr.REAL_ODDS == new_odds.REAL_ODDS) return
									attr.REAL_ODDS = new_odds.REAL_ODDS;
									attr.ODDS = new_odds.ODDS;
									attr.ODDS_GUEST = new_odds.ODDS_GUEST;
									attr.DRAW_ODDS = new_odds.DRAW_ODDS;
								})
							})
						})
					}
				})
			},
			loadding_data(data) {
				//获取联赛数组
				let _this = this;
				if (data.total) {
					let favor_leagues = data.favor_leagues
					let server_matches = data.items
					let league_icons = {}
					server_matches.forEach(match => {
						if (match.LEAGUE && !league_icons[match.LEAGUE]) {
							league_icons[match.LEAGUE] = match.league_logo || ''
						}
					})
					//使用set给leauges去重
					let server_leagues = [...new Set(server_matches.map(ele => ele.LEAGUE))]
					// leauges排序
					server_leagues = _this.sort_object(server_leagues, '', config.leagues)
					let league_list = server_leagues.map(ele => {
						return {
							name: ele,
							league_icon: league_icons[ele] || '',
							checked: true,
							show_match: true,
							include_today: false,
							include_tomorrow: false,
							favor: favor_leagues.includes(ele),
							match_list: [],
						}
					})

					let all_attr_type_list = _this.match_ref.mixed ? [_this.bet_type.MIX_BODY, _this.bet_type.MIX_GOAL, ] :
						[_this.bet_type.SINGLE_BODY, _this.bet_type.SINGLE_GOAL, _this.bet_type.SINGLE_WDL, ]
					server_matches.forEach(match => {
						match.click_arr = []
						match.show_image = true
						match.checked = true
						let time = new Date(match.LOCAL_MATCH_TIME)
						match.MATCH_MD_DATE = time
						match.MD_DATE_TIME = _this.formatMatchDateTime(time)
						match.MD_NOON = time.getHours() >= 12 ? 'PM' : 'AM'
						match.MD_DAY = `${time.toDateString().split(" ")[0]}`
						match.MD_HHMM =
							`${String(time.getHours()%12 || 12).padStart(2,'0')}:${String(time.getMinutes()).padStart(2,'0')}`
						match.MD_DDMM =
							`${String(time.getDate()).padStart(2,'0')} ${time.toDateString().split(" ")[1]}`
						match.SLIP_DATE =
							`@ ${match.MD_DDMM} ${time.getFullYear()} ${String(time.getHours()%12 || 12).padStart(2,'0')}:${String(time.getMinutes()).padStart(2,'0')}`
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
					// from tangjq--- 使用Vue.set确保expanded属性是响应式的
					_this.league_list.forEach((league, league_index) => {
						league.match_list.forEach((match, match_index) => {
							Vue.set(_this.league_list[league_index].match_list[match_index], 'expanded',
								false)
						})
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
				const betAmount = parseInt(_this.amount) || 0
				const userInfo = _this.$store.state.userInfo || {}
				const mainBalance = _this.$toolbox.floor_value(userInfo.money || 0)
				const promotionBalance = _this.$toolbox.floor_value(userInfo.money_promotion || 0)
				const requiredBalance = _this.use_promotion_wallet ? promotionBalance : mainBalance
				if (betAmount > requiredBalance) {
					content = _this.use_promotion_wallet ?
						`Promotion wallet balance (${_this.$toolbox.num_format(promotionBalance)}) is less than required amount (${_this.$toolbox.num_format(betAmount)})` :
						_this.$t('Sorry, your current balance is not enough for this bet')
				}
				if (_this.amount > max) {
					content = (_this.match_ref.mixed ? _this.$t('mix_max') : _this.$t('single_max')) +
						` ( ${max} )`;
				}
				if (_this.amount < min) {
					content = (_this.match_ref.mixed ? _this.$t('mix_min') : _this.$t('single_min')).replace('xxx', min);
				}
				if (_this.match_ref.mixed && _this.bet_list.length < _this.mix_min_count) {
					content = _this.$t('at_least_count').replace('xxx', _this.mix_min_count)
				}
				if (_this.match_ref.mixed && _this.bet_list.length > _this.mix_max_count) {
					content = _this.$t('at_most_count').replace('xxx', _this.mix_max_count)
				}
				if (content) {
					// from tangjq--- 使用投注失败提示弹窗代替原来的 this.$notice.show
					_this.show_fail_popup(content);
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
							this.$notice.show({
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

							// 如果勾选了使用优惠钱包，添加use_promotion_wallet标记
							if (_this.use_promotion_wallet) {
								requestParams.use_promotion_wallet = true;
							}

							_this.$http.post(url, requestParams, (res) => {
								uni.hideLoading();
								if (res.statusCode == 200) {
									var userInfo = _this.$store.state.userInfo

									// 实际扣除金额
									let actualDeduction = parseInt(_this.amount);

									// 根据是否使用优惠钱包，从不同的余额扣除
									if (_this.use_promotion_wallet) {
										// 从优惠钱包扣除
										userInfo.money_promotion = _this.$toolbox.floor_format(
											_this.$toolbox.floor_value(userInfo.money_promotion) -
											actualDeduction);
									} else {
										// 从主钱包扣除
										userInfo.money = _this.$toolbox.floor_format(
											_this.$toolbox.floor_value(userInfo.money) -
											actualDeduction);
									}

									_this.reset();
									_this.$store.dispatch('saveUserInfo',
										userInfo);
									// from tangjq--- 投注成功后显示成功提示弹窗
									_this.hide_bets_slip = true
									_this.show_success_popup();
								} else {
									// from tangjq--- 服务器返回错误，显示投注失败提示
									var errorMsg = (res.data && res.data.message) ? _this.$t(res.data
										.message) : 'Betting failed, please try again'
									_this.show_fail_popup(errorMsg);
								}
							}, (err) => {
								// from tangjq--- 网络请求失败，显示投注失败提示
								uni.hideLoading();
								_this.show_fail_popup(_this.$t('Network error, please try again'));
							})
						}
					} else {
						// from tangjq--- 赔率检查失败，显示错误提示
						uni.hideLoading();
						var errorMsg = (res.data && res.data.message) ? _this.$t(res.data.message) :
							'Failed to check odds, please try again'
						_this.show_fail_popup(errorMsg);
					}
				}, (err) => {
					// from tangjq--- 网络错误导致赔率检查失败
					uni.hideLoading();
					_this.show_fail_popup(_this.$t('Network error, please try again'));
				})
			},

			to_deposit() {
				uni.navigateTo({
					url: '/pages/ucenter/charge',
					complete(res) {}
				})
			},
			// from tangjq--- 显示投注成功提示弹窗
			show_success_popup() {
				this.hide_success_popup = false
			},
			// from tangjq--- 显示投注失败提示弹窗，接收错误信息参数，2秒后自动消失
			show_fail_popup(message) {
				this.fail_message = message || 'Betting failed, please try again'
				this.hide_fail_popup = false
				setTimeout(() => {
					this.hide_fail_popup = true
				}, 3000)
			},
			// from tangjq--- 获取比赛可用的投注选项数量
			get_available_bet_count(match) {
				if (!match || !match.ATTR) return 0
				const count = match.ATTR.filter(attr => !attr.disabled).length
				// console.log('get_available_bet_count:', count, 'for match:', match.MATCH_ID)
				return count
			},
			// from tangjq--- 切换比赛投注选项的展开/收起状态
			toggle_match_expand(match) {
				this.$set(match, 'expanded', !match.expanded)
			},
			// from tangjq--- 处理搜索输入
			handleSearchInput() {
				// 输入时自动过滤，无需额外处理
			},
			// from tangjq--- 清空搜索关键字
			clearSearch() {
				this.searchKeyword = ''
			},
			formatMatchDateTime(time) {
				const month = String(time.getMonth() + 1).padStart(2, '0')
				const day = String(time.getDate()).padStart(2, '0')
				const hours24 = time.getHours()
				const hours12 = String(hours24 % 12 || 12).padStart(2, '0')
				const minutes = String(time.getMinutes()).padStart(2, '0')
				const period = hours24 >= 12 ? 'PM' : 'AM'
				return `${day}.${month}.${time.getFullYear()} ${hours12}:${minutes} ${period}`
			},
			// from tangjq--- 判断比赛是否匹配搜索关键字
			isMatchSearch(match) {
				if (!this.searchKeyword || this.searchKeyword.trim() === '') {
					return true; // 没有搜索关键字时显示所有
				}
				const keyword = this.searchKeyword.toLowerCase().trim();
				const hostTeam = (match.HOST_TEAM || '').toLowerCase();
				const guestTeam = (match.GUEST_TEAM || '').toLowerCase();
				const leagueName = (match.LEAGUE || '').toLowerCase();
				return hostTeam.includes(keyword) || guestTeam.includes(keyword) || leagueName.includes(keyword);
			},
			// from tangjq--- 判断联赛是否有匹配搜索的比赛
			isLeagueMatchSearch(league) {
				if (!this.searchKeyword || this.searchKeyword.trim() === '') {
					return true; // 没有搜索关键字时显示所有
				}
				// 如果联赛下有任何比赛匹配，显示该联赛
				if (league.match_list && league.match_list.length > 0) {
					const dayKey = !this.tomorrow ? 'today' : 'tomorrow';
					return league.match_list.some(match => {
						if (!match.checked || match.MATCH_DAY !== dayKey) {
							return false;
						}
						return this.isMatchSearch(match);
					});
				}
				return false;
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
			this.getAdvertisements() // from tangjq--- 获取广告列表
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
			this.hide_success_popup = true // from tangjq--- 关闭投注成功提示弹窗
			this.hide_fail_popup = true // from tangjq--- 关闭投注失败提示弹窗
			return true;
		},
		//离开当前页面后执行
		destroyed: function() {
			clearInterval(this.intervalId);
		},
	}
</script>

<style lang="scss">
	@import './components/match.css';

	/* from tangjq--- header占位元素样式 */
	.header-placeholder {
		width: 100%;
		flex-shrink: 0;
	}

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
		height: var(--app-viewport-height, 100vh);
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

	/* from tangjq--- 新的页面容器样式，修复滚动问题 */
	.match-page-container {
		height: var(--app-viewport-height, 100vh);
		min-height: var(--app-viewport-height, 100vh);
		overflow: hidden;
		display: flex;
		flex-direction: column;
	}

	.page {
		flex: 1;
		height: 0;
		min-height: 0;
		background: #ffffff;
		box-sizing: border-box;
		// padding-bottom: 24px !important;
		// padding-bottom: calc(24px + env(safe-area-inset-bottom)) !important;
	}

	.page.page-mixed {
		// padding-bottom: 70px !important;
		// padding-bottom: calc(70px + env(safe-area-inset-bottom)) !important;
	}

	.match-list-bottom-spacer {
		height: 48px;
		flex-shrink: 0;
	}

	.match-list-bottom-spacer-mixed {
		height: 90px;
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

	/* from tangjq--- 新的搜索栏和筛选按钮样式 */
	.new-header-wrapper {
		display: flex;
		flex-direction: row;
		align-items: center;
		padding: 10px 15px 5px;
		gap: 10px;
		background-color: #ffffff;
		border-radius: 20px 20px 0 0;
		flex-shrink: 0;
	}

	.new-search-bar {
		flex: 1;
		display: flex;
		flex-direction: row;
		align-items: center;
		background-color: white;
		border-radius: $radius-large;
		padding: 0 5px;
		border: 2px solid $color-primary;
	}

	.search-icon {
		width: 22px;
		height: 22px;
		margin: 4px 10px 4px 0;
	}

	.search-input {
		flex: 1;
		font-size: 14px;
		color: $color-primary;
	}

	/* from tangjq--- 清空按钮样式 */
	.clear-icon {
		width: 16px;
		height: 16px;
		margin-left: 8px;
		cursor: pointer;
		opacity: 0.6;
	}

	.filter-btn {
		position: relative;
		height: 30px;
		background-color: $color-primary;
		color: white;
		font-weight: bold;
		gap: 5px;
		padding: 0 15px;
		border-radius: $radius-large;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 12px;
	}

	.filter-icon {
		display: flex;
		flex-direction: column;
		gap: 3px;
		align-items: center;
	}

	.filter-line {
		height: 2px;
		background-color: #ffffff;
		border-radius: 1px;
	}

	.filter-line:nth-child(1) {
		width: 18px;
	}

	.filter-line:nth-child(2) {
		width: 10px;
	}

	.filter-line:nth-child(3) {
		width: 4px;
	}

	.filter-badge {
		position: absolute;
		top: -5px;
		right: -5px;
		background-color: #ff4444;
		color: white;
		width: 18px;
		height: 18px;
		min-width: 18px;
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 8px;
		line-height: 1;
		padding: 0;
		white-space: nowrap;
		box-sizing: border-box;
	}

	/* from tangjq--- 新的联赛标题栏样式 */
	.new-league-header {
		font-size: 12px;
		display: flex;
		flex-direction: row;
		justify-content: space-between;
		align-items: center;
		background-color: var(--theme-league-bg, $color-primary);
		border-radius: $radius-medium;
		padding: 7px 12px;
		margin-bottom: 10px;
		width: 100%;
	}

	.league-left {
		display: flex;
		flex-direction: row;
		align-items: center;
		gap: 10px;
	}

	.league-icon {
		width: 20px;
		height: 20px;
		border-radius: 50%;
		background-color: white;
	}

	.league-name {
		color: white;
		font-size: 14px;
		font-weight: bold;
	}

	.league-right {
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.league-toggle-icon {
		width: 8px;
		height: 7px;
	}

	.league-fold-icon {
		transform: rotate(180deg);
	}

	/* from tangjq--- 新的比赛卡片样式 */
	.new-match-card {
		background-color: white;
		border-radius: $radius-large;
		margin-bottom: 10px;
		overflow: hidden;
		border: 1px solid $color-border;
		box-shadow: 0 1px 3px rgba(47, 93, 98, 0.16);
		padding-bottom: 12px;
		--match-center-column-width: 128px;
	}

	.match-summary {
		padding: 8px 14px 10px;
		min-width: 0;
	}

	.match-teams {
		min-width: 0;
	}

	.match-logo-row,
	.match-name-row {
		display: grid;
		grid-template-columns: minmax(0, 1fr) var(--match-center-column-width) minmax(0, 1fr);
		min-width: 0;
	}

	.match-logo-row {
		align-items: center;
		min-height: 0;
		padding: 5px 0;
	}

	.match-logo-row .team-logo-frame {
		justify-self: center;
	}

	.match-name-row {
		align-items: stretch;
		margin-top: 3px;
	}

	.match-datetime {
		width: 100%;
		min-width: 0;
		max-width: 100%;
		box-sizing: border-box;
		overflow: visible;
		background-color: transparent;
		text-align: center;
		font-size: 11px;
		color: $color-primary;
		font-weight: 500;
		line-height: 1.25;
		white-space: nowrap;
		padding-top: 8px;
	}

	.new-match-card .team-logo-frame {
		width: 20px;
		height: 20px;
		display: flex;
		align-items: center;
		justify-content: center;
		flex-shrink: 0;
		transition: width 180ms ease-out, height 180ms ease-out;
	}

	.new-match-card .team-logo-frame.team-logo-frame-expanded {
		width: 35px;
		height: 35px;
	}

	.new-match-card .team-logo {
		width: 20px;
		height: 20px;
		transform: scale(1);
		transform-origin: center;
		transition: transform 180ms ease-out;
	}

	.new-match-card .team-logo.team-logo-expanded {
		transform: scale(1.75);
	}

	.new-match-card .team-name {
		display: flex;
		align-self: stretch;
		align-items: center;
		justify-content: center;
		font-size: 12px;
		color: $color-primary;
		font-weight: 600;
		text-align: center;
		min-width: 0;
		max-width: 100%;
		min-height: 30px;
		padding: 0 2px;
		box-sizing: border-box;
		line-height: 1.25;
		white-space: normal;
		overflow-wrap: break-word;
		word-break: break-word;
	}

	.new-match-card .vs-text {
		display: block;
		width: 100%;
		font-size: 14px;
		color: $color-primary;
		font-weight: bold;
		line-height: 1;
		text-align: center;
		padding-top: 1px;
		margin: 0;
	}

	/* from tangjq--- 新的投注选项样式 */
	.new-bet-options {
		padding: 0 20px 0;
	}

	.bet-row {
		display: flex;
		flex-direction: row;
		align-items: center;
		background-color: $color-primary;
		border-radius: $radius-medium;
		padding: 9px 9px 9px 0;
		margin-bottom: 4px;
	}

	.bet-row:last-child {
		margin-bottom: 0;
	}

	.bet-type-label {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		/* margin-right: 15px; */
		min-width: 25px;
	}

	.bet-type-label text {
		color: white;
		font-size: 12px;
		font-weight: bold;
		line-height: 1.2;
	}

	.bet-buttons {
		flex: 1;
		display: flex;
		flex-direction: row;
		align-items: center;
		justify-content: space-between;
		gap: 10px;
	}

	.bet-btn {
		flex: 1;
		background-color: white;
		border-radius: $radius-small;
		padding: 10px;
		display: flex;
		align-items: center;
		justify-content: center;
		min-height: 46px;
	}

	.bet-btn-selected {
		background-color: $color-active !important;
	}

	.bet-text {
		color: $color-primary;
		font-size: 14px;
		font-weight: 600;
	}

	/* from tangjq--- 1X2类型的三列布局样式 */
	.bet-buttons-three {
		gap: 8px;
	}

	.bet-btn-small {
		flex: 1;
		flex-direction: column;
		padding: 3px 5px;
	}

	.bet-text-small {
		color: $color-primary;
		font-size: 14px;
		font-weight: bold;
	}

	.bet-odds-small {
		color: $color-primary;
		font-size: 14px;
		font-weight: bold;
		font-style: italic;
	}

	.bet-odds {
		flex: 0 0 auto;
		min-width: 80px;
		text-align: center;
	}

	.bet-odds text {
		color: white;
		font-size: 13px;
		font-weight: bold;
	}

	.match-expand-btn {
		background-color: $color-primary;
		height: 28px;
		margin: 4px 20px 0;
		display: flex;
		align-items: center;
		justify-content: center;
		color: white;
		border-radius: $radius-medium;
		cursor: pointer;
	}

	.match-toggle-icon {
		width: 13px;
		height: 14px;
		display: block;
		transform: rotate(0deg);
		transition: transform 180ms ease-out;
	}

	.match-toggle-icon.match-toggle-icon-expanded {
		transform: rotate(180deg);
	}

	/* from tangjq--- 确保展开按钮可点击 */
	.match-expand-btn:active {
		opacity: 0.8;
	}

	/* from tangjq--- 混合投注底部栏样式 */
	.mix-bottom-bar {
		position: fixed;
		bottom: 0;
		left: 0;
		right: 0;
		display: flex;
		flex-direction: row;
		padding: 15px;
		gap: 15px;
		background-color: white;
		border-radius: 15px 15px 0 0;
		/* from tangjq--- 上方两个角圆角 */
		box-shadow: 0 -6px 20px rgba(0, 0, 0, 0.25);
		/* from tangjq--- 增强上边框阴影效果 */
		z-index: 100;
	}

	.total-matches-btn {
		flex: 1;
		// background-color: #E0E0E0;
		border-radius: $radius-medium;
		padding: 5px;
		display: flex;
		flex-direction: row;
		align-items: center;
		justify-content: space-between;
	}

	.total-text {
		color: $color-primary;
		font-size: 16px;
		font-weight: bold;
	}

	.total-count {
		color: $color-secondary;
		font-size: 18px;
		font-weight: bold;
	}

	.confirm-btn {
		flex: 1;
		background-color: $color-primary;
		border-radius: $radius-medium;
		padding: 5px;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.confirm-text {
		color: white;
		font-size: 16px;
		font-weight: bold;
	}

	/* from tangjq--- 单注详情弹窗样式 - 居中显示 */
	.new-detail-popup {
		position: fixed;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		z-index: 1000;
		display: flex;
		align-items: center;
		justify-content: center;
		padding: 20px;
	}

	/* from tangjq--- 单注详情弹窗遮罩层 */
	.detail-popup-mask {
		position: absolute;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		background-color: rgba(0, 0, 0, 0.6);
		z-index: 1;
	}

	/* from tangjq--- 单注详情弹窗内容容器 */
	.detail-popup-container {
		position: relative;
		z-index: 2;
		background-color: white;
		border-radius: 15px;
		width: 90%;
		max-width: 500px;
		max-height: 80vh;
		display: flex;
		flex-direction: column;
		overflow: hidden;
		box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
	}

	.detail-header {
		background-color: $color-primary;
		padding: 20px;
		text-align: center;
		flex-shrink: 0;
	}

	.detail-title {
		color: white;
		font-size: 20px;
		font-weight: bold;
	}

	/* from tangjq--- 单注详情内容区域，flex布局自适应 */
	.detail-content {
		flex: 1;
		padding: 20px;
		overflow-y: auto;
		min-height: 0;
	}

	.detail-match-card {
		background-color: $bg-color-info;
		border-radius: 15px;
		padding: 15px;
		margin-bottom: 20px;
	}

	.detail-datetime {
		text-align: center;
		font-size: 14px;
		color: $color-primary;
		font-weight: 500;
		margin-bottom: 15px;
	}

	.detail-teams {
		display: flex;
		flex-direction: row;
		justify-content: space-around;
		align-items: center;
	}

	.detail-team {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 10px;
	}

	.detail-team-logo {
		width: 35px;
		height: 35px;
	}

	.detail-team-name {
		font-size: 13px;
		color: $color-primary;
		font-weight: 600;
		text-align: center;
	}

	.detail-vs {
		font-size: 16px;
		color: #666;
		font-weight: bold;
	}

	/* from tangjq--- 下单详情弹窗样式 - 居中显示 */
	.new-bet-slip-popup {
		position: fixed;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		z-index: 2000;
		display: flex;
		align-items: center;
		justify-content: center;
		padding: 5px;
	}

	.bet-slip-mask {
		position: absolute;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		background-color: rgba(0, 0, 0, 0.6);
		z-index: 1;
	}

	/* from tangjq--- 下单详情内容容器 - 居中弹窗 */
	.bet-slip-container {
		position: relative;
		z-index: 2;
		background-color: white;
		border-radius: 15px;
		width: 90%;
		max-width: 500px;
		max-height: 80vh;
		display: flex;
		flex-direction: column;
		overflow: hidden;
		box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
	}

	/* from tangjq--- 混合投注模式也使用相同的居中样式 */
	.bet-slip-container.mix-mode {
		/* 移除之前的全屏样式，使用与单注相同的居中样式 */
	}

	.bet-slip-header {
		background-color: $color-primary;
		padding: 8px;
		text-align: center;
		flex-shrink: 0;
		border-radius: 15px 15px 0 0;
	}

	.bet-slip-title {
		color: white;
		font-size: 16px;
		font-weight: bold;
	}

	/* from tangjq--- 滚动区域样式，只包含比赛列表，限制高度，使其可滚动 */
	.bet-slip-scroll {
		flex: 1;
		max-height: 35vh;
		overflow-y: auto;
		min-height: 150px;
		padding: 0;
	}

	/* from tangjq--- 混合投注已选比赛列表样式 */
	.mix-matches-list {
		padding: 15px 0 5px 0;
	}

	/* from tangjq--- 混合投注列表项，与左右边框有距离 */
	.mix-match-item {
		background-color: $bg-color-info;
		border: 1px solid $color-border-other;
		border-radius: $radius-small;
		padding: 12px 15px;
		margin: 0 15px 12px 15px;
	}

	/* from tangjq--- 最后一个列表项底部留出更多间距 */
	.mix-match-item:last-child {
		margin-bottom: 15px;
	}

	/* from tangjq--- 比赛时间 */
	.mix-match-datetime {
		text-align: center;
		margin-bottom: 10px;
	}

	.mix-match-datetime text {
		font-size: 12px;
		color: $color-primary;
		font-weight: 500;
	}

	.mix-match-info {
		display: flex;
		flex-direction: column;
		gap: 8px;
	}

	/* from tangjq--- 队伍对阵行特殊样式 */
	.mix-teams-row {
		padding-bottom: 10px;
		border-bottom: 1px solid $color-border-other;
		margin-bottom: 2px;
		align-items: flex-start;
		/* from tangjq--- 改为顶部对齐，支持换行后的布局 */
	}

	.mix-team-name {
		font-size: 13px;
		font-weight: 600;
		max-width: 45%;
		/* from tangjq--- 限制最大宽度为行的38%，确保两个队名和vs都能显示 */
		word-wrap: break-word;
		/* from tangjq--- 允许单词内换行 */
		word-break: break-word;
		/* from tangjq--- 在必要时断词换行 */
		overflow-wrap: break-word;
		/* from tangjq--- 确保长单词换行 */
		line-height: 1.3;
		/* from tangjq--- 设置行高，让多行文字更易读 */
		text-align: center;
		/* from tangjq--- 居中对齐 */
	}

	.mix-vs {
		font-size: 14px;
		font-weight: bold;
		color: $color-primary;
		flex-shrink: 0;
		/* from tangjq--- 防止vs文字被压缩 */
		padding: 0 5px;
		/* from tangjq--- 左右留出间距 */
	}

	.mix-match-row {
		display: flex;
		flex-direction: row;
		justify-content: space-between;
		align-items: center;
		font-size: 12px;
		color: $color-primary;
	}

	/* from tangjq--- mix-match-item 卡片内的字段行：左 label / 右 value */
	.mix-row-label {
		color: $color-primary;
		font-weight: 500;
	}

	.mix-row-value {
		color: $color-primary;
		font-weight: 600;
		text-align: right;
	}

	.mix-bet-choice {
		color: #4A90A4;
		font-weight: 600;
	}

	/* from tangjq--- 单注比赛信息样式 */
	.single-match-info {
		background-color: $bg-color-info;
		border-radius: $radius-small;
		padding: 10px;
		margin: 15px;
		margin-bottom: 15px;
	}

	/* from tangjq--- 比赛时间行 */
	.match-time-row {
		text-align: center;
		margin-bottom: 15px;
	}

	.match-time {
		font-size: 12px;
		color: $color-primary;
		font-weight: 500;
	}

	/* from tangjq--- 队伍行 */
	.teams-row {
		display: flex;
		flex-direction: row;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 10px;
		padding-bottom: 10px;
		border-bottom: 1px solid $color-border-other;
	}

	.team-section {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 5px;
		flex: 1;
	}

	.team-logo {
		width: 35px;
		height: 35px;
	}

	.team-name {
		font-size: 12px;
		font-weight: 600;
		text-align: center;
	}

	.vs-text {
		font-size: 16px;
		color: $color-primary;
		font-weight: bold;
		margin: 0 10px;
	}

	/* from tangjq--- 投注详情行 */
	.bet-detail-row {
		display: flex;
		flex-direction: row;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 12px;
		font-size: 12px;
		color: $color-primary;
	}

	.bet-type {
		font-weight: 600;
	}

	.bet-odds {
		font-weight: 600;
	}

	.bet-time {
		font-weight: 500;
	}

	/* from tangjq--- 投注选项行 */
	.bet-choice-row {
		display: flex;
		flex-direction: row;
		justify-content: space-between;
		align-items: center;
		font-size: 12px;
	}

	.choice-team {
		color: $color-primary;
		font-weight: 600;
	}

	.choice-type {
		color: $color-primary;
		font-weight: 600;
	}

	/* from tangjq--- 投注输入区域样式（固定在底部，不滚动） */
	.bet-input-section {
		display: flex;
		flex-direction: column;
		padding: 0 15px 15px;
		flex-shrink: 0;
		background-color: white;
	}

	.bet-info-rows {
		background-color: $bg-color-info;
		border-radius: $radius-small;
		padding: 12px 15px;
		margin-bottom: 15px;
	}

	.bet-info-row {
		display: flex;
		flex-direction: row;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 8px;
		font-size: 12px;
	}

	.bet-info-row:last-child {
		margin-bottom: 0;
	}

	.bet-info-row .info-label {
		color: $color-primary;
		font-weight: 500;
	}

	.info-value {
		font-weight: 600;
		color: $color-primary;
	}

	/* from tangjq--- Main/Promo Wallet 并排按钮，参考 MPL_Detial_Overlay.png */
	.wallet-buttons {
		display: flex;
		flex-direction: row;
		gap: 10px;
		margin-bottom: 10px;
	}

	.wallet-btn {
		flex: 1;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 2px;
		padding: 4px;
		border-radius: $radius-small;
		border: 1.5px solid $color-primary;
		background: $bg-color-info;
		cursor: pointer;
		transition: background 0.2s ease;
	}

	.wallet-btn-label {
		font-size: 12px;
		color: $color-primary;
		font-weight: 500;
		line-height: 16px;
	}

	.wallet-btn-value {
		font-size: 14px;
		color: $color-primary;
		font-weight: 700;
		line-height: 18px;
	}

	/* Main Wallet 默认（未选中态）：白底 + 青绿边框 + 青绿文字 */
	.wallet-btn-main.wallet-btn-active,
	.wallet-btn-promo.wallet-btn-active {
		background: $color-primary;
	}

	.wallet-btn-main.wallet-btn-active .wallet-btn-label,
	.wallet-btn-main.wallet-btn-active .wallet-btn-value,
	.wallet-btn-promo.wallet-btn-active .wallet-btn-label,
	.wallet-btn-promo.wallet-btn-active .wallet-btn-value {
		color: #FFFFFF;
	}

	.wallet-btn-disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	.wallet-label {
		font-size: 12px;
		color: $color-primary;
		font-weight: 600;
	}

	.wallet-value {
		font-size: 12px;
		color: $color-primary;
		font-weight: bold;
	}

	.bet-amount-input {
		background-color: #BDD4D6;
		border-radius: $radius-small;
		padding: 8px;
		margin-bottom: 5px;
	}

	.amount-input {
		width: 100%;
		font-size: 13px;
		color: $color-primary;
		font-weight: 500;
		text-align: center;
		font-style: italic;
	}

	/* from tangjq--- 输入框placeholder样式 */
	.amount-input::placeholder {
		font-size: 12px;
		font-style: italic;
		color: #7FA5A8;
	}

	/* from tangjq--- Min/Max Bet Amount：一行左右两侧，参考 MPL_Detial_Overlay.png */
	.min-max-bet-row {
		display: flex;
		flex-direction: row;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 15px;
		gap: 10px;
	}

	.min-bet-label {
		color: #890006;
		font-size: 11px;
		font-weight: 500;
		white-space: nowrap;
	}

	.action-buttons {
		display: flex;
		flex-direction: row;
		gap: 15px;
	}

	/* from tangjq--- Cancel 按钮：白底 + 红边 + 红字，参考 MPL_Detial_Overlay.png */
	.cancel-btn {
		flex: 1;
		background-color: white;
		border: 2px solid $color-primary;
		border-radius: $radius-medium;
		padding: 5px;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.cancel-text {
		color: #C8434C;
		font-size: 16px;
		font-weight: bold;
	}

	.confirm-btn-action {
		flex: 1;
		background-color: #BDD4D6;
		border-radius: $radius-medium;
		padding: 5px;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.confirm-btn-action.confirm-active {
		background-color: $color-primary;
	}

	.confirm-btn-action .confirm-text {
		color: white;
		font-size: 16px;
		font-weight: bold;
	}

	/* from tangjq--- 广告图区域样式 */
	.ad-banner-wrapper {
		width: 100%;
		height: 36.8vw;
		border-radius: 15px;
		overflow: hidden;
		/* margin: 15px 0; */
		box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
	}

	.ad-banner-image {
		width: 100%;
		height: 100%;
	}

	/* from tangjq--- 投注成功提示弹窗样式 */
	.success-popup-wrapper {
		position: fixed;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		background-color: rgba(0, 0, 0, 0.6);
		z-index: 3000;
		display: flex;
		align-items: center;
		justify-content: center;
		padding: 30px;
	}

	.success-popup-container {
		background-color: white;
		border-radius: 20px;
		width: 100%;
		max-width: 500px;
		overflow: hidden;
		box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
	}

	.success-popup-header {
		background-color: $color-primary;
		padding: 8px;
		text-align: center;
	}

	.success-popup-title {
		color: white;
		font-size: 12px;
		font-weight: bold;
	}

	.success-popup-content {
		padding: 20px;
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 20px;
	}

	.success-popup-image {
		width: 100%;
		height: 200px;
		border-radius: 15px;
	}

	.success-popup-subtitle {
		color: $color-primary;
		font-size: 20px;
		font-weight: bold;
		text-align: center;
	}

	.success-popup-footer {
		padding: 20px;
		display: flex;
		justify-content: center;
	}

	.success-ok-btn {
		background-color: $color-primary;
		border-radius: 12px;
		padding: 8px;
		min-width: 100px;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.success-ok-text {
		color: white;
		font-size: 18px;
		font-weight: bold;
	}

	/* from tangjq--- 投注失败提示弹窗样式 */
	.fail-popup-wrapper {
		position: fixed;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		background-color: rgba(0, 0, 0, 0.5);
		z-index: 9999;
		display: flex;
		align-items: center;
		justify-content: center;
		padding: 40px;
	}

	.fail-popup-container {
		background-color: white;
		border-radius: 20px;
		padding: 30px 40px;
		box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
		max-width: 80%;
		word-break: break-word;
	}

	.fail-popup-text {
		color: #D44131;
		font-size: 16px;
		font-weight: 600;
		text-align: center;
		line-height: 1.5;
	}
</style>
