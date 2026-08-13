<template>
	<view class="deposit-component">
		<global-notice ref="globalNotice"></global-notice>
		<scroll-view scroll-y class="deposit-scroll" @scroll="onScrollEmit" @scrolltoupper="onScrollTopEmit">
			<!-- from tangjq--- 银行卡列表界面（默认显示） -->
			<view class="bank-list-container" v-if="current_progress==0">
				<!-- 银行卡列表 -->
				<view class="bank-card-item" v-for="(card,index) in card_list" :key="index">
					<view class="bank-card-content" @click="openDepositModal(card)">
						<image class="bank-icon" :src="`/static/icon/register/${card.bank_code}.png`"></image>
						<text class="bank-name">{{card.bank_code}}</text>
						<text class="account-number">*****{{(card.acc_number || '').slice(-4)}}</text>
						<!-- 删除按钮 -->
						<view class="delete-btn" @click.stop="removeBank(card)" v-if="!card.is_default">
							<text class="cuIcon-delete delete-icon"></text>
						</view>
					</view>
				</view>

				<!-- 添加银行账户按钮 -->
				<view class="add-bank-btn" @click="show_add_modal('add')">
					<text class="add-bank-text">{{ $t('add bank account') }}</text>
				</view>
			</view>

			<!-- from tangjq--- 顶栏：AUTO/MANUAL 切换 -->
			<view class="title-tab justify-around" style="box-shadow: none;padding: 10px 0;" v-if="current_progress>0">
				<view class="register-btn" :style="`width: ${90/charge_way.length}%`"
					:class="item.checked?'mybg-lprimary':'mycolor-primary route-shadow'"
					@click="select_option(item,'charge_way')" v-for="(item,index) in charge_way" :key="index">
					{{item.label}}
				</view>
			</view>

			<!-- from tangjq--- Step 0: 银行选择和金额输入（隐藏，改为显示银行卡列表） -->
			<view v-if="false">
				<!-- 银行选择  -->
				<view class="flex-column justify-center padding-top-sm mycolor-primary">
					<view class="myfont-14px text-bold height-20px">{{'Available bank'}}</view>
					<view class="myfont-10px height-10px">{{'Select bank you would like to transfer to'}}</view>
				</view>
				<view class="flex-row1 justify-center margin-top-sm">
					<image :src="item.src" mode="heightFix" style="height: 60px;border-radius: 8px;margin: 0 10px;"
						:style="!item.checked?'opacity:50%':''" @click="select_option(item,'bank_list')"
						v-for="(item,index) in bank_list" :key="index">
					</image>
				</view>
				<!-- tips -->
				<view class="width-100 flex-column1 align-start margin-tb padding-lr-sm text-red myfont-13px"
					style="font-size: 1rem;line-height: 1.1;">
					<view class="text-bold">
						{{$t('important_notice')}}:
					</view>
					<view class="">
						{{$t('deposit_tips1')}}
					</view>
					<view class="">
						{{$t('deposit_tips2')}}
					</view>
				</view>
				<!-- 输入框 -->
				<view class="flex-column mybg-lprimary text-white width-100" style="position: relative">
					<input class="amount-input" style="" type="number" @input='inputNum' v-model="amount"
						placeholder-class="text-white" maxlength="7" placeholder="">
					<view class="limit">Minimum {{numberFormat(configs.deposit_min_limit || 3000)}} and Maximum
						{{numberFormat(configs.deposit_max_limit || 1000000)}} Ks
					</view>
				</view>
				<!-- 快速选择 -->
				<view
					style="display: flex;flex-direction: row;flex-wrap:wrap;justify-content:space-between;padding: 5px 40px;width: 100%;">
					<view class="amount-select" style="" v-for="(item,index) in amount_list" :key="index"
						@click="amount = item">{{numberFormat(item)}}
					</view>
				</view>

				<view class="width-100 flex-row1 justify-start margin-tb padding-lr-sm">
					<view class="mycolor-primary myfont-13px" style="font-size: 1rem;line-height: 1.1;">
						{{$t('deposit_tips3')}}
					</view>
				</view>
				<view class="width-100 flex-row justify-start margin-tb padding-lr-sm">
					<view class=" text-red myfont-13px" style="font-size: 1rem;line-height: 1.1;">
						<text class="text-bold">{{$t('note')}}</text>
						{{$t('deposit_tips4')}}
					</view>
				</view>
			</view>

			<!-- from tangjq--- Step 1 AUTO: 银行卡选择 -->
			<view class="" style="margin-left: 10%;width: 80%;" v-if="current_progress==1 && chargeForm.charge_way==0">
				<input class="search-rec" style="" :placeholder="$t('search')"
					placeholder-class="cuIcon-search mycolor-info" v-model="card_search" @input="clean_acc" />
				<view class="flex-row justify-between myfont-15px mycolor-primary margin-top-lg">
					<view class="myfont-19px">{{$t('Select_your_bank')}}</view>
					<view class="mybg-grey" style="padding: 0 6px;" v-if="card_list.length>0" @click="edit_card()">
						<text>{{language.edit}}</text>
						<text class="cuIcon-edit myfont-18px margin-left-xs"></text>
					</view>
				</view>

				<view class="flex-column radius-10px" :class="!editing?'round-border':'no-right-border'" style="">
					<view class="flex-row justify-between myfont-10px text-black height-70px"
						v-for="(card,index) in filtered_card_list" :key="index"
						@click="editing?'':select_option(card,'card_list',1)"
						style="line-height: 1.1;padding: 8px 0 8px 8px;border-radius: 4px;"
						:style="index+1<card_list.length?'border-bottom: solid darkgray 1px;':''">
						<view class="flex-row1">
							<view class="flex-column1 justify-center align-center">
								<image class="height-50px width-50px" style="border-radius: 8px;"
									:src="`/static/icon/register/${card.bank_code}.png`"></image>
							</view>
							<view class="flex-column1 justify-center align-start myfont-11px margin-left">
								<view class="myfont-12px text-bold text-black">{{ $t('account_number') }}</view>
								<view>{{card.acc_number}}</view>
								<view style="height: 2px;"></view>
								<view class="myfont-12px text-bold text-black">{{ $t('account_ame') }}</view>
								<view>{{card.acc_name}}</view>
							</view>
						</view>
						<view class="width-70px">
							<view
								class="height-70px flex-column text-white myfont-14px radius-right-6px account-remove-btn"
								:class="{ 'disabled-action': card.is_default }" v-if="editing"
								@click="card.is_default?'':removeBank(card)">
								{{ $t('remove') }}
							</view>
							<view class="flex-column1 align-center justify-center" v-else>
								<view class="myfont-10px margin-bottom-xs" :class="!index?'mycolor-primary':''">
									{{index?language.other:language['main account']}}
								</view>
								<radio :class="card.checkeds?'checked':''" :checked="card.checked">
								</radio>
							</view>
						</view>
					</view>
				</view>

				<view class="flex-row myfont-10px text-black height-70px radius-10px margin-top-lg"
					style="border: solid darkgray 1px;padding: 8px 20px;border-radius: 4px;"
					@click="show_add_modal('add')">
					<text class="cuIcon-roundadd myfont-28px mycolor-lprimary" style="">
					</text>
					<text class="myfont-17px margin-left-lg text-black">{{ $t('add_bank_manually') }}</text>
				</view>

				<view class="height-45px radius-10px margin-top flex-column mybg-lprimary"
					:class="{ 'disabled-action': !acc_checked }" @click="auto_submit()">
					{{$t('proceed_selected_account')}}
				</view>
				<view class="flex-row1 width-100vw margin-top-sm align-start height-20px"
					style="line-height: 1;position: absolute;left: 0;">
					<view class="width-45 height-50" style="border-bottom: dashed darkgray 1px;"></view>
					<text class="margin-lr-sm">{{language.or}}</text>
					<view class="width-45 height-50" style="border-bottom: dashed darkgray 1px;"></view>
				</view>
				<view class="mybg-lprimary height-45px radius-10px flex-column" style="margin-top: 40px;"
					@click="show_add_modal('one-time')">
					{{$t('proceed_one_time_payment')}}
				</view>
			</view>

			<!-- from tangjq--- Step 1 MANUAL: 手动充值 -->
			<view v-if="current_progress==1 && chargeForm.charge_way==1">
				<!-- 收款信息 -->
				<view class="padding">
					<view class="flex-row justify-start myfont-10px text-bold text-black"
						style="line-height: 1.5;box-shadow: rgba(0, 0, 0, 0.5) 0px 4px 8px;padding: 12px;border-radius: 4px;margin-bottom: 15px;">
						<view class="flex-column1 justify-center align-center margin-left-sm" @click="">
							<image class="title-icon" style="border-radius: 0;"
								:src="`/static/icon/register/${agent_bankcard.rc_bank_code}.png`"></image>
						</view>
						<view class="flex-column1 justify-center align-start width-45 margin-left-lg" @click="">
							<view class="bank-title">{{agent_bankcard.rc_bank_username}}</view>
							<view>{{ $t('account_ame') }}</view>
							<view class="bank-title">{{agent_bankcard.rc_bank_account}}<theme-icon name="copy"
									size="16px" color="rgb(161, 160, 161)" class="margin-left"
									style="display: inline-block; vertical-align: middle;"
									@click="copy(agent_bankcard.rc_bank_account)"></theme-icon>
							</view>
							<view>{{ $t('account_number') }}</view>
						</view>
					</view>
				</view>

				<!-- 金额显示 -->
				<view class="flex-row justify-center margin-bottom text-black padding-lr"
					style="margin: 0px 0px 16px;font-family: __Inter_7be8ac, __Inter_Fallback_7be8ac;font-weight: 600;font-size: 0.875rem;line-height: 1.13;text-align: center;">
					{{ $t('bank_change_notice') }}
				</view>
				<view class="width-100 flex-column padding-lr-lg" v-if="chargeForm.charge_way">
					<view class="text-center text-red myfont-13px" style="font-size: 1rem;line-height: 1.1;">
						{{ $t('enter_transaction_id') }}
					</view>
					<input class="width-100 margin-tb-sm height-30px radius-3px text-center"
						style="border: 2px solid #E0E0E0;" :style="transaction_disable?'background:rgb(241,241,241)':''"
						type="number" @input='' v-model="chargeForm.transaction_id" placeholder-class="text-white"
						maxlength="32" placeholder="" :disabled="transaction_disable">
				</view>
				<view class="padding-left-lg myfont-16px text-black text-bold">{{language.amount}}</view>
				<view class="flex-column mycolor-primary" style="position: relative">
					<view class="amount-input">{{numberFormat(amount)}}</view>
					<view class="ks" style="right: 110px;">Ks</view>
				</view>
				<view class="flex-column" v-if="chargeForm.charge_way">
					<!-- 提示 -->
					<view class="tips" style="">
						{{ $t('upload_slip_notice') }}
					</view>
					<view class="bg-img padding-sm" @tap="ViewImage" :data-url="picture"
						style="text-align: center;position: relative;">
						<image :src="picture" mode="aspectFill" style="width:80px;height:80px;border:1px dashed grey">
						</image>
					</view>
					<view
						class="mybg-lprimary height-25px myfont-13px padding-sm flex-row1 justify-center align-center radius-3px"
						@click="ChooseImage">
						<text
							class="cuIcon-upload margin-right-xs"></text>{{picture?language.upload_slip_new:language.upload}}
					</view>
				</view>
			</view>

			<!-- from tangjq--- 提交按钮 -->
			<!-- <button class="login-btn" style="width: 70%;margin: 20px 15% 10px 15%;" :disabled="confirmDisabled" v-if="(!chargeForm.charge_way&&current_progress!=1 ) || chargeForm.charge_way" @click="next_or_submit()">
				{{language.submit}}</button> -->
			<view class="padding-xs"></view>
		</scroll-view>

		<!-- from tangjq--- 添加/编辑银行卡 Modal（新设计） -->
		<view class="cu-modal" style="z-index: 9999;" :class="modalName=='add_modal'?'show':''">
			<view class="add-bank-dialog">
				<!-- 标题栏 -->
				<view class="dialog-header">
					<text class="dialog-title">{{ $t('bind_wallet_account') }}</text>
					<text class="dialog-close" @click="modalName = ''">✕</text>
				</view>

				<!-- 副标题 -->
				<view class="dialog-subtitle">
					<text>{{ $t('choose_account_type') }}</text>
				</view>

				<!-- 银行图标选择 -->
				<view class="bank-icon-selector">
					<view class="bank-icon-item" v-for="(bank,index) in bank_add_list" :key="index"
						@click="select_modal_bank(bank)" :class="card_conf.bank_code==bank.bank_code?'selected':''">
						<image class="bank-icon-img" :src="`/static/icon/register/${bank.bank_code}.png`"></image>
					</view>
				</view>

				<!-- 表单 -->
				<view class="dialog-form">
					<!-- Account No -->
					<view class="form-group">
						<text class="form-label">{{ $t('account_number') }}</text>
						<input class="form-input" type="number" maxlength="17" @input="set_add_disable()"
							:placeholder="$t('enter_account_number')" v-model="card_conf.acc_number" />
					</view>

					<!-- User Name -->
					<view class="form-group">
						<text class="form-label">{{ $t('account_ame') }}</text>
						<input class="form-input" type="text" @input="set_add_disable()"
							:placeholder="$t('account_ame')" v-model="card_conf.acc_name" />
					</view>
				</view>

				<!-- Confirm 按钮 -->
				<button class="confirm-btn" :class="add_disable?'disabled':''"
					@click="modal_type=='add'?add_card():auto_submit()" :disabled="add_disable">
					{{ $t('confirm') }}
				</button>
			</view>
		</view>

		<!-- from tangjq--- 充值弹窗（Auto Deposit） -->
		<view class="cu-modal" style="z-index: 9999;" :class="modalName=='deposit_modal'?'show':''">
			<view class="deposit-modal-dialog">
				<!-- 标题栏 -->
				<view class="deposit-modal-header">
					<text class="deposit-modal-title">{{ $t('auto_deposit') }}</text>
					<text class="deposit-modal-close" @click="closeDepositModal">✕</text>
				</view>

				<!-- 用户账户信息 -->
				<view class="user-account-section">
					<text class="section-title">{{ $t('user_account') }}</text>

					<!-- Bank Type -->
					<view class="info-row">
						<text class="info-label">{{ $t('bank type') }}</text>
						<view class="bank-type-value">
							<image class="bank-type-icon" :src="`/static/icon/register/${selectedCard.bank_code}.png`">
							</image>
							<text class="bank-type-text">{{selectedCard.bank_code}}</text>
						</view>
					</view>

					<!-- Account No -->
					<view class="info-row">
						<text class="info-label">{{ $t('account_number') }}</text>
						<view class="info-value-box">
							<text class="info-value-text">{{selectedCard.acc_number}}</text>
						</view>
					</view>

					<!-- User Name -->
					<view class="info-row">
						<text class="info-label">{{ $t('account_ame') }}</text>
						<view class="info-value-box">
							<text class="info-value-text">{{selectedCard.acc_name}}</text>
						</view>
					</view>
				</view>

				<!-- 金额输入 -->
				<view class="amount-section">
					<view class="amount-input-box">
						<input class="amount-input-field" placeholder-class="myfont-13px" type="number"
							@input='inputNum' v-model="amount" :placeholder="$t('enter_deposit_amount')" />
					</view>
					<text class="amount-hint">Minimum {{numberFormat(configs.deposit_min_limit || 3000)}} Ks, Maximum
						{{numberFormat(configs.deposit_max_limit || 1000000)}} Ks</text>

					<!-- 快速金额选择 -->
					<view class="quick-amount-grid">
						<view class="quick-amount-btn" v-for="(item,index) in amount_list" :key="index"
							@click="amount = item">
							{{numberFormat(item)}}
						</view>
					</view>
				</view>

				<!-- 支付渠道：仅支持 QR Pay -->
				<view class="payment-channel-section">
					<!-- <text class="section-title">{{ $t('payment_channel') }}</text> -->
					<view class="payment-channel-single">
						<text class="payment-channel-name">{{ $t('qr_pay') }}</text>
					</view>
				</view>

				<!-- Continue 按钮 -->
				<button class="continue-btn" :disabled="amount_error" @click="depositSubmit()">
					{{ $t('continue_btn') }}
				</button>
			</view>
		</view>

		<!-- from tangjq--- Transfer Tips弹窗 -->
		<view class="cu-modal" style="z-index: 9999;" :class="showTipsModal?'show':''">
			<view class="transfer-tips-dialog">
				<!-- 标题栏 -->
				<view class="transfer-modal-header">
					<text class="transfer-modal-title">{{ $t('deposit_with_kpay') }}</text>
					<text class="transfer-modal-close" @click="closeTipsModal">✕</text>
				</view>

				<!-- 金额信息 -->
				<view class="tips-content">
					<view class="tips-row">
						<text class="tips-label">{{ $t('transaction_amount') }} :</text>
						<text class="tips-value">{{numberFormat(amount)}} Ks</text>
					</view>
					<view class="tips-row">
						<text class="tips-label">{{ $t('handling_fees') }}</text>
						<text class="tips-value">0%</text>
					</view>
					<view class="tips-row highlight">
						<text class="tips-label">{{ $t('received_amount') }} :</text>
						<text class="tips-value">{{numberFormat(amount)}} Ks</text>
					</view>
				</view>

				<!-- Continue按钮 -->
				<button class="tips-continue-btn" @click="continueFromTips">
					{{ $t('continue_btn') }}
				</button>
			</view>
		</view>

		<!-- from tangjq--- Transfer Confirm弹窗 -->
		<view class="cu-modal" style="z-index: 9999;" :class="showConfirmModal?'show':''">
			<view class="transfer-confirm-dialog">
				<!-- 标题栏 -->
				<view class="transfer-modal-header">
					<text class="transfer-modal-title">{{ $t('deposit_with_kpay') }}</text>
					<text class="transfer-modal-close" @click="closeConfirmModal">✕</text>
				</view>

				<!-- User Account -->
				<view class="confirm-section">
					<text class="confirm-section-title">{{ $t('user_account') }}</text>

					<view class="confirm-row">
						<text class="confirm-label">{{ $t('bank type') }}</text>
						<view class="confirm-bank-value">
							<image class="confirm-bank-icon"
								:src="`/static/icon/register/${selectedCard.bank_code}.png`"></image>
							<text class="confirm-bank-text">Kpay</text>
						</view>
					</view>

					<view class="confirm-row">
						<text class="confirm-label">{{ $t('account_number') }}</text>
						<view class="confirm-value-box">
							<text class="confirm-value-text">{{selectedCard.acc_number || 'none'}}</text>
						</view>
					</view>

					<view class="confirm-row">
						<text class="confirm-label">{{ $t('account_ame') }}</text>
						<view class="confirm-value-box">
							<text class="confirm-value-text">{{selectedCard.acc_name || 'none'}}</text>
						</view>
					</view>
				</view>

				<!-- 箭头 -->
				<view class="transfer-arrows">
					<text class="arrow-icon">↓</text>
					<text class="arrow-icon">↓</text>
					<text class="arrow-icon">↓</text>
				</view>

				<!-- Payee Account -->
				<view class="confirm-section">
					<text class="confirm-section-title">{{ $t('payee_account') }}</text>

					<view class="confirm-row">
						<text class="confirm-label">{{ $t('bank type') }}</text>
						<view class="confirm-bank-value">
							<image class="confirm-bank-icon"
								:src="`/static/icon/register/${agent_bankcard.rc_bank_code || 'KBZ Pay'}.png`"></image>
							<text class="confirm-bank-text">Kpay</text>
						</view>
					</view>

					<view class="confirm-row">
						<text class="confirm-label">{{ $t('account_number') }}</text>
						<view class="confirm-copy-box">
							<text class="confirm-copy-text">{{agent_bankcard.rc_bank_account || 'none'}}</text>
							<view class="confirm-copy-btn"
								@click="copyPayeeInfo(agent_bankcard.rc_bank_account, 'Account')">
								<text class="copy-btn-text">{{ $t('copy') }}</text>
								<theme-icon name="copy" size="14px"
									color="var(--theme-icon-primary, var(--theme-primary))"></theme-icon>
							</view>
						</view>
					</view>

					<view class="confirm-row">
						<text class="confirm-label">{{ $t('account_ame') }}</text>
						<view class="confirm-copy-box">
							<text class="confirm-copy-text">{{agent_bankcard.rc_bank_username || 'Payee'}}</text>
							<view class="confirm-copy-btn"
								@click="copyPayeeInfo(agent_bankcard.rc_bank_username, 'Name')">
								<text class="copy-btn-text">{{ $t('copy') }}</text>
								<theme-icon name="copy" size="14px"
									color="var(--theme-icon-primary, var(--theme-primary))"></theme-icon>
							</view>
						</view>
					</view>
				</view>

				<!-- Transfer Amount & Valid Period -->
				<view class="transfer-info">
					<view class="transfer-info-row">
						<text class="transfer-info-label">{{ $t('transfer_amount') }} :</text>
						<text class="transfer-info-value">{{numberFormat(amount)}} Ks</text>
					</view>
					<view class="transfer-info-row">
						<text class="transfer-info-label">{{ $t('valid_period') }}</text>
						<text class="transfer-info-value">none</text>
					</view>
				</view>

				<!-- 倒计时 -->
				<view class="countdown-display">
					<text class="countdown-text">{{countdownDisplay}}</text>
				</view>

				<!-- 提示文字 -->
				<view class="transfer-notice" v-if="!showContinueBtn">
					<text class="transfer-notice-text">{{ $t('tap_copy_notice') }}</text>
				</view>

				<!-- Continue提示 -->
				<view class="transfer-notice" v-if="showContinueBtn">
					<text class="transfer-notice-text">{{ $t('press_continue_deposit') }}</text>
				</view>

				<!-- Continue按钮 -->
				<button class="transfer-final-btn" v-if="showContinueBtn" @click="transferContinue">
					{{ $t('continue_btn') }}
				</button>
			</view>
		</view>

		<!-- from tangjq--- QR Code弹窗 -->
		<view class="cu-modal" style="z-index: 9999;" :class="showQRCodeModal?'show':''">
			<view class="qrcode-dialog">
				<!-- 标题栏 -->
				<view class="qrcode-modal-header">
					<text class="qrcode-modal-title">{{ $t('deposit_with_kpay') }}</text>
					<text class="qrcode-modal-close" @click="closeQRCodeModal">✕</text>
				</view>

				<!-- 二维码 -->
				<view class="qrcode-section">
					<view class="qrcode-container">
						<tki-qrcode ref="qrcode" :val="qrCodeData" :size="300" v-if="qrCodeData" />
					</view>

					<!-- Save QR按钮 -->
					<button class="save-qr-btn" @click="$refs.qrcode._saveCode()">
						<text class="save-qr-icon">↓</text>
						<text class="save-qr-text">{{ $t('save_qr') }}</text>
					</button>
				</view>

				<!-- 提示文字 -->
				<view class="qrcode-tips">
					<text class="qrcode-tips-text">{{ $t('scan_qr_notice') }}</text>
					<text class="qrcode-tips-warning">{{ $t('same_account_payment') }}</text>
				</view>

				<!-- Transfer Amount & Valid Period -->
				<view class="qrcode-info">
					<view class="qrcode-info-row">
						<text class="qrcode-info-label">{{ $t('transfer_amount') }} :</text>
						<text class="qrcode-info-value">{{numberFormat(amount)}} Ks</text>
					</view>
					<view class="qrcode-info-row">
						<text class="qrcode-info-label">{{ $t('valid_period') }}</text>
						<text class="qrcode-info-value">none</text>
					</view>
				</view>

				<!-- 倒计时 -->
				<view class="qrcode-countdown">
					<text class="qrcode-countdown-text">{{countdownDisplay}}</text>
				</view>

				<!-- Continue按钮 -->
				<button class="qrcode-continue-btn" v-if="showContinueBtn" @click="qrPayContinue">
					{{ $t('continue_btn') }}
				</button>
			</view>
		</view>

		<!-- from tangjq--- Notice弹窗 -->
		<view class="cu-modal" style="z-index: 9999;" :class="showNoticeModal?'show':''">
			<view class="notice-dialog">
				<!-- 标题栏 -->
				<view class="notice-header">
					<text class="notice-title">{{ $t('notice_title') }}</text>
				</view>

				<!-- 内容 -->
				<view class="notice-content">
					<text class="notice-text">{{ $t('check_transaction_records') }}</text>
				</view>

				<!-- Confirm按钮 -->
				<button class="notice-confirm-btn" @click="closeNoticeModal">
					{{ $t('confirm') }}
				</button>
			</view>
		</view>

		<!-- delete bank confirm dialog -->
		<ConfirmDialog :visible="showDeleteConfirm" :title="$t('remove_bank_title') || 'Delete Bank Account'"
			:message="$t('remove_bank_confirm')" :confirmText="$t('Confirm')" :cancelText="$t('Cancel')"
			@confirm="confirmDeleteBank" @cancel="showDeleteConfirm = false" />
	</view>
</template>

<script>
	// from tangjq--- Deposit 组件,从 charge.vue 完整移植
	import config from '../../utils/config.js'
	import dateFormatUtils from "../../utils/utils.js"
	import tkiQrcode from '@/components/tki-qrcode/tki-qrcode.vue'
	import ConfirmDialog from '@/components/common/confirm-dialog.vue'

	export default {
		name: 'WalletDeposit',
		components: {
			tkiQrcode,
			ConfirmDialog
		},
		data() {
			return {
				userInfo: {},
				configs: {},
				language: config.language,
				picture: '',
				modalName: '',
				selectedCard: {},
				lang_select: uni.getStorageSync('lang_select') || config.language.lang,
				// Transfer支付相关
				showTipsModal: false,
				showConfirmModal: false,
				showNoticeModal: false,
				countdown: 600, // 10分钟倒计时（秒）
				countdownTimer: null,
				showContinueBtn: false,
				hasCopied: false,
				// QR Pay支付相关
				showQRCodeModal: false,
				qrCodeData: '',
				paymentType: '', // 当前支付类型：'transfer' 或 'qrpay'
				orderInfo: null, // 订单信息
				chargeForm: {
					charge_way: 0,
					bank_code: 'KBZ Pay',
					transaction_id: '',
					acc_name: '',
					acc_number: '',
				},
				acc_checked: false,
				card_search: '',
				bank_list: [{
					value: 'KBZ Pay',
					label: 'KBZPay',
					src: '/static/icon/register/KBZ Pay.png',
					checked: false
				}, {
					value: 'Wave Money',
					label: 'WavePay',
					src: '/static/icon/register/Wave Money.png',
					checked: true
				}],
				amount: '',
				amount_list: [3000, 5000, 10000, 100000, 500000, 1000000],
				amount_error: true,
				charge_way: [{
					label: 'AUTO',
					value: 0,
					checked: true
				}, {
					label: 'MANUAL',
					value: 1,
					checked: false
				}],
				card_list: [],
				current_progress: 0,
				token: uni.getStorageSync('Authorization') || '',
				bank_add_list: [],
				card_conf: {},
				show_bank_list: false,
				showDeleteConfirm: false,
				deleteTargetBank: null,
				add_disable: true,
				modal_type: '',
				editing: false,
				agent_bankcard: {},
				agent_no_bankcard: false,
				transaction_disable: false,
			}
		},
		watch: {
			amount(val) {
				const rawAmount = parseInt(this.amount)
				const minLimit = parseInt(this.configs.deposit_min_limit) || 3000;
				const maxLimit = parseInt(this.configs.deposit_max_limit) || 1000000;
				this.amount_error = !(rawAmount >= minLimit && rawAmount <= maxLimit)
			},
			// 监听系统配置变化，动态更新金额选择列表
			configs: {
				handler(val) {
					if (val && (val.deposit_min_limit || val.deposit_max_limit)) {
						this.amount_list = this.dynamicAmountList;
					}
				},
				deep: true,
				immediate: true
			},
		},
		computed: {
			confirmDisabled() {
				if (this.current_progress == 0 && this.amount_error) return true
				else if (this.current_progress == 1 && this.chargeForm.charge_way == 1 && (!this.picture || !this
						.chargeForm.transaction_id)) return true
				return false
			},
			filtered_card_list() {
				const keyword = this.card_search.trim().toLowerCase();
				if (!keyword) return this.card_list;
				return this.card_list.filter(item => {
					return (
						(item.acc_name && item.acc_name.toLowerCase().includes(keyword)) ||
						(item.acc_number && item.acc_number.toLowerCase().includes(keyword))
					);
				});
			},
			countdownDisplay() {
				const minutes = Math.floor(this.countdown / 60)
				const seconds = this.countdown % 60
				return `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}:00`
			},
			// 动态生成金额选择列表，基于系统配置的 min/max 限额
			dynamicAmountList() {
				const min = parseInt(this.configs.deposit_min_limit) || 3000;
				const max = parseInt(this.configs.deposit_max_limit) || 1000000;
				const fixedList = [3000, 5000, 10000, 50000, 100000, 200000, 300000, 500000, 1000000];

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
			// from tangjq--- 滚动事件冒泡给父页面，用于驱动 header 收起/展开
			onScrollEmit(e) {
				this.$emit('contentScroll', e)
			},
			// from tangjq--- 原生滚动到顶部事件冒泡给父页面，保证到达顶部时 header 一定展开还原
			onScrollTopEmit() {
				this.$emit('contentScrollTop')
			},
			select_option(selected, list, allow_false) {
				if (selected.checked && !allow_false) return
				selected.checked = !selected.checked
				this[list].forEach((item) => {
					if (item != selected) item.checked = false
				})
				this.set_charge_form()
			},
			set_charge_form() {
				this.chargeForm.bank_code = this.bank_list.find(item => item.checked).value

				// 如果存在charge_way，则设置charge_way
				if (this.charge_way && this.charge_way.length > 0) {
					this.chargeForm.charge_way = this.charge_way.find(item => item.checked).value
				}

				// 在充值弹窗中，账号信息由openDepositModal设置，不要清空
				// 只在非弹窗模式下处理card_list的选中逻辑
				if (this.modalName !== 'deposit_modal') {
					this.acc_checked = false
					let acc = this.card_list.find(item => item.checked)
					if (acc) {
						this.acc_checked = true
						this.chargeForm.acc_name = acc.acc_name
						this.chargeForm.acc_number = acc.acc_number
					} else {
						this.clean_acc()
					}
				}
			},
			clean_acc() {
				this.acc_checked = false
				this.chargeForm.acc_name = ''
				this.chargeForm.acc_number = ''
				let acc = this.card_list.find(item => item.checked)
				if (acc) acc.checked = false
			},
			inputNum: function(evt) {
				let amount = evt.detail.value.replace('.', '')
				amount = amount ? parseInt(amount) : '0'
				const maxLimit = parseInt(this.configs.deposit_max_limit) || 1000000;
				if (amount > maxLimit) {
					amount = maxLimit
				}
				this.$nextTick(function() {
					this.$set(this, 'amount', amount)
				})
			},
			numberFormat(number) {
				return dateFormatUtils.numFormat(number);
			},
			copy(account) {
				const _this = this
				uni.setClipboardData({
					data: account,
					success: function() {
						uni.showToast({
							title: _this.$t('copied_to_clipboard'),
							icon: 'success'
						});
					},
					fail: function() {}
				});
			},
			next_or_submit() {
				if (this.$toolbox.click_too_fast(1)) return
				if (!this.current_progress) {
					this.current_progress++
					this.charge_way = this.charge_way.filter(item => item.checked)
					let _this = this
					if (_this.chargeForm.charge_way == 1 && _this.agent_no_bankcard) {
						this.$notice.show({
							title: _this.$t('tips'),
							content: _this.$t('agent_no_bankcard'),
							showCancel: false,
							confirmText: _this.$t('back'),
							success: res => {
								if (res.confirm) {
									_this.current_progress = 0
									_this.charge_way = [{
										label: 'AUTO',
										value: 0,
										checked: true
									}, {
										label: 'MANUAL',
										value: 1,
										checked: false
									}]
								}
							}
						})
					}
					return
				}
				if (this.current_progress) {
					this.submit()
				}
			},
			show_add_modal(modal_type) {
				if (modal_type == 'add' && this.card_list.length >= 5) {
					this.$notice.show({
						title: this.$t('tips'),
						content: this.$t('max_five_banks'),
						showCancel: false,
						confirmText: this.$t('confirm'),
						success: res => {}
					})
					return
				}
				this.$set(this.card_conf, 'acc_name', '')
				this.$set(this.card_conf, 'acc_number', '')
				this.$set(this.card_conf, 'bank_code', this.bank_add_list[0].bank_code)
				this.modal_type = modal_type
				this.modalName = 'add_modal'
			},
			select_modal_bank(bank) {
				this.$set(this.card_conf, 'bank_code', bank.bank_code)
			},
			set_add_disable() {
				if (!this.card_conf.acc_name || !this.card_conf.acc_number) {
					this.add_disable = true
					return
				}
				this.add_disable = false
			},
			edit_card() {
				this.editing = !this.editing
				this.clean_acc()
			},
			add_card() {
				var _this = this;
				if (!_this.card_conf.acc_number || !_this.card_conf.bank_code || !_this.card_conf.acc_name) return
				var para = {
					acc_number: _this.card_conf.acc_number,
					bank_code: _this.card_conf.bank_code,
					acc_name: _this.card_conf.acc_name,
				}
				_this.$http.post('/bank_card/add', para, (res) => {
					if (res.statusCode == 200) {
						uni.showToast({
							title: _this.$t('saved_success'),
							icon: 'success',
							duration: 2000
						})
						_this.modalName = ''
						_this.get_bank_card_list();
					} else {
						uni.showToast({
							title: res.data.message,
							icon: 'none',
							duration: 2000
						})
					}
				})
			},
			removeBank(bank) {
				var _this = this;
				if (_this.$toolbox.click_too_fast(.5)) return
				_this.deleteTargetBank = bank
				_this.showDeleteConfirm = true
			},
			confirmDeleteBank() {
				var _this = this;
				_this.showDeleteConfirm = false
				var bank = _this.deleteTargetBank
				if (!bank) return
				var para = {
					id: bank.id,
				}
				_this.$http.post('/bank_card/delete', para, (res) => {
					if (res.statusCode == 200) {
						uni.showToast({
							title: _this.$t('removed_success'),
							icon: 'success',
							duration: 2000
						})
						_this.editing = false
						_this.get_bank_card_list()
					}
				})
				_this.deleteTargetBank = null
			},
			get_bank_card_list() {
				var _this = this;
				var para = {}
				_this.$http.get('/bank_card/get', {
					data: para
				}, (res) => {
					if (res.statusCode == 200) {
						_this.card_list = res.data.items.map((item, index) => ({
							...item,
							checked: false,
						}));
					} else {}
				})
			},
			get_agent_bank_card() {
				var _this = this;
				var para = {}
				_this.$http.get('/agent_bankcard', {
					data: para
				}, (res) => {
					if (res.statusCode == 200) {
						_this.agent_bankcard = res.data.item
						if (_this.agent_bankcard.rc_bank_code == 'CB') _this.agent_bankcard.rc_bank_code = 'CB Pay'
					}
					if (res.statusCode == 501) {
						_this.agent_no_bankcard = true
					} else {}
				})
			},
			uploadPic() {
				var _this = this;
				let url = '/charge/order_image'
				if (this.picture) {
					uni.showLoading({
						title: _this.$t('upload_pic')
					})
					var con = {
						url: url,
						filePath: _this.picture,
						formData: {
							MONEY: _this.amount,
							lang: _this.lang_select,
						},
						name: 'image',
						success: (res) => {
							if (res.statusCode == 200) {
								uni.hideLoading()
								let responseData;
								try {
									responseData = JSON.parse(res.data);
								} catch (e) {
									responseData = res.data;
								}
								let trades = responseData.trades;
								if (trades && trades[0]) {
									_this.chargeForm.transaction_id = trades[0].transaction_id;
									_this.transaction_disable = true;
								}
							} else {
								let tips = res.message
								if (_this.language[res.message]) {
									tips = _this.language[res.message]
								}
								uni.hideLoading()
								this.$notice.show({
									title: _this.$t('tips'),
									content: tips,
									showCancel: false,
									confirmText: _this.$t('ok')
								})
							}
						}
					}
					_this.$http.uploadFile(con)
				} else {
					uni.showToast({
						title: _this.$t('upload_charge_pic'),
						image: '../../static/icon/error.png',
						duration: 2000
					})
				}
			},
			ChooseImage() {
				var _this = this;
				uni.chooseImage({
					count: 1,
					sizeType: ['original', 'compressed'],
					sourceType: ['album'],
					success: (res) => {
						_this.picture = res.tempFilePaths[0];
						_this.uploadPic()
					},
					fail: (err) => {
						uni.showToast({
							title: '选择图片失败',
							icon: 'none'
						});
					}
				});
			},
			ViewImage() {
				if (!this.picture) {
					return;
				}
				uni.previewImage({
					urls: [this.picture],
					current: this.picture
				});
			},
			submit() {
				var _this = this;
				uni.showLoading({
					title: _this.$t('loading_dots')
				});
				// 手动充值（MANUAL mode with image）
				if (_this.chargeForm.charge_way && _this.picture) {
					uni.uploadFile({
						url: _this.$http.baseUrl + '/charge/recharge',
						filePath: _this.picture,
						name: 'image',
						formData: {
							transaction_id: _this.chargeForm.transaction_id,
							amount: _this.amount,
							charge_way: _this.chargeForm.charge_way,
							bank_code: _this.chargeForm.bank_code
						},
						header: {
							Authorization: _this.token
						},
						success: (uploadRes) => {
							uni.hideLoading();
							try {
								const data = JSON.parse(uploadRes.data);
								if (data.statusCode == 200) {
									setTimeout(() => {
										uni.reLaunch({
											url: '/pages/wallet/wallet'
										})
									}, 2000)
									uni.showToast({
										title: this.$t('deposit_success')
									});
								} else {
									this.$notice.show({
										confirmText: this.$t('ok'),
										showCancel: false,
										title: this.$t('error_title'),
										content: data.message
									});
								}
							} catch (e) {
								this.$notice.show({
									confirmText: this.$t('ok'),
									showCancel: false,
									title: this.$t('error_title'),
									content: this.$t('unknown_error')
								});
							}
						},
						fail: (err) => {
							uni.hideLoading();
							this.$notice.show({
								confirmText: this.$t('ok'),
								showCancel: false,
								title: this.$t('error_title'),
								content: this.$t('upload_fail')
							});
						}
					});
				} else {
					// 旧自动直接充值（MANUAL mode without proper data，shouldn't happen）
					let para = {
						transaction_id: _this.chargeForm.transaction_id,
						amount: _this.amount,
						charge_way: _this.chargeForm.charge_way,
						bank_code: _this.chargeForm.bank_code
					};

					_this.$http.post('/charge/recharge_apply', para, res => {
						uni.hideLoading();
						if (res.statusCode == 200) {
							setTimeout(() => {
								uni.reLaunch({
									url: '/pages/wallet/wallet'
								})
							}, 2000)
							uni.showToast({
								title: this.$t('deposit_success')
							});
						} else {
							this.$notice.show({
								confirmText: this.$t('ok'),
								showCancel: false,
								title: this.$t('error_title'),
								content: res.data.message
							});
						}
					});
				}
			},
			auto_submit() {
				var _this = this;
				if (_this.$toolbox.click_too_fast(.5)) return
				if (_this.modal_type == 'one-time') {
					_this.chargeForm.acc_name = _this.card_conf.acc_name
					_this.chargeForm.acc_number = _this.card_conf.acc_number
				}
				if (!_this.amount || !_this.chargeForm.acc_number)
					return

				let para = Object.assign({}, _this.chargeForm)
				para.amount = _this.amount
				para.memo = 'memo'
				para.subject = `charge ${para.amount}`
				delete para.transaction_id
				let acc = this.card_list.find(item => item.checked)
				para.card_id = acc.id

				_this.$http.post('/charge_apply/add', para, res => {
					let data = res.data
					if (data.code == 200) {
						let order = data.data;
						uni.showToast({
							title: _this.$t('success_excl')
						})
						_this.card_conf = {}
						_this.modalName = ''
						uni.navigateTo({
							url: `/pages/payment/payment?id=${order.tradeOrderId}`
						});
					} else if (data.code == 409) {
						let order = data.data;
						uni.navigateTo({
							url: `/pages/payment/payment?id=${order.out_order_id}`
						});
					} else {
						// from tangjq--- 先关闭当前弹窗，再显示错误提示，避免被遮挡
						_this.modalName = ''
						_this.$nextTick(() => {
							this.$notice.show({
								confirmText: this.$t('ok'),
								showCancel: false,
								title: this.$t('error_title'),
								content: res.data.message
							})
						})
					}
				})
			},
			set_info() {
				this.userInfo = Object.assign({}, this.$store.state.userInfo)
				this.configs = Object.assign({}, this.$store.state.configs)
				this.loadAvailableBanks()
			},
			// 通过接口获取 admin 配置的可用银行列表并过滤 bank_add_list
			loadAvailableBanks() {
				var _this = this
				_this.$http.get('/agent_bankcard/available_banks', {
					data: {}
				}, (res) => {
					if (res.statusCode == 200 && res.data) {
						const auto = res.data.auto || []
						const manual = res.data.manual || []
						// 合并 auto 和 manual 中的 bank_code，去重
						const codes = new Set()
						auto.forEach(b => codes.add(b.bank_code))
						manual.forEach(b => codes.add(b.bank_code))
						const availableCodes = Array.from(codes)

						const allBanks = [{
								bank_code: 'KBZ Pay',
								label: 'KBZPay',
								checked: true
							},
							{
								bank_code: 'Wave Money',
								label: 'WavePAY',
								checked: false
							},
							{
								bank_code: 'AYA',
								label: 'AYA PAY',
								checked: false
							},
							{
								bank_code: 'Citizen Pay',
								label: 'Citizen Pay',
								checked: false
							},
							{
								bank_code: 'UAB Pay',
								label: 'UAB Pay',
								checked: false
							},
						]
						_this.bank_add_list = allBanks.filter(bank => availableCodes.includes(bank.bank_code))
						if (_this.bank_add_list.length > 0) {
							_this.bank_add_list[0].checked = true
						}
					}
				})
			},
			openDepositModal(card) {
				this.selectedCard = card
				this.chargeForm.acc_name = card.acc_name
				this.chargeForm.acc_number = card.acc_number
				this.chargeForm.bank_code = card.bank_code
				this.modalName = 'deposit_modal'
				this.$nextTick(() => {
					this.amount = ''
				})
			},
			closeDepositModal() {
				this.modalName = ''
				this.selectedCard = {}
				this.amount = ''
			},
			depositSubmit() {
				if (this.$toolbox.click_too_fast(.5)) return

				// 验证金额（使用系统配置的动态限额）
				const amountNum = parseInt(this.amount)
				const minLimit = parseInt(this.configs.deposit_min_limit) || 3000;
				const maxLimit = parseInt(this.configs.deposit_max_limit) || 1000000;
				if (!amountNum || amountNum < minLimit || amountNum > maxLimit) {
					uni.showToast({
						title: this.$t('enter_valid_amount'),
						icon: 'none'
					})
					return
				}

				// 验证账号
				if (!this.chargeForm.acc_number) {
					uni.showToast({
						title: this.$t('account_number_missing'),
						icon: 'none'
					})
					return
				}

				// QR Pay 直接创建订单
				this.createQRPayOrder()
			},
			// Transfer支付相关方法
			showTransferTips() {
				this.paymentType = 'transfer'
				this.showTipsModal = true
			},
			closeTipsModal() {
				this.showTipsModal = false
			},
			continueFromTips() {
				this.closeTipsModal()
				if (this.paymentType === 'transfer') {
					this.showTransferConfirm()
				} else if (this.paymentType === 'qrpay') {
					this.createQRPayOrder()
				}
			},
			showTransferConfirm() {
				this.showConfirmModal = true
				this.showContinueBtn = false
				this.hasCopied = false
				this.countdown = 600
				this.startCountdown()
			},
			closeConfirmModal() {
				this.showConfirmModal = false
				this.stopCountdown()
				this.showContinueBtn = false
				this.hasCopied = false
			},
			startCountdown() {
				this.stopCountdown()
				this.countdownTimer = setInterval(() => {
					if (this.countdown > 0) {
						this.countdown--
					} else {
						this.closeConfirmModal()
					}
				}, 1000)
			},
			stopCountdown() {
				if (this.countdownTimer) {
					clearInterval(this.countdownTimer)
					this.countdownTimer = null
				}
			},
			copyPayeeInfo(text, type) {
				uni.setClipboardData({
					data: text,
					success: () => {
						uni.showToast({
							title: `${type} copied`,
							icon: 'success'
						})
						this.hasCopied = true
						this.showContinueBtn = true
					}
				})
			},
			transferContinue() {
				// 关闭确认弹窗
				this.closeConfirmModal()
				// 显示Notice弹窗
				this.showNoticeModal = true
			},
			closeNoticeModal() {
				this.showNoticeModal = false
				// 关闭充值弹窗
				this.closeDepositModal()
			},
			// QR Pay支付相关方法
			showQRPayTips() {
				this.paymentType = 'qrpay'
				this.showTipsModal = true
			},
			createQRPayOrder() {
				// 创建QR Pay订单
				let para = Object.assign({}, this.chargeForm)
				para.amount = this.amount
				para.memo = 'memo'
				para.subject = `charge ${para.amount}`
				delete para.transaction_id
				para.card_id = this.selectedCard.id

				uni.showLoading({
					title: this.$t('loading_dots')
				})

				this.$http.post('/charge_apply/add', para, res => {
					uni.hideLoading()
					let data = res.data
					if (data.code == 200) {
						let order = data.data
						this.closeDepositModal()
						uni.navigateTo({
							url: `/pages/payment/payment?id=${order.tradeOrderId}`
						})
					} else if (data.code == 409) {
						let order = data.data
						this.closeDepositModal()
						uni.navigateTo({
							url: `/pages/payment/payment?id=${order.out_order_id}`
						})
					} else {
						// from tangjq--- 先关闭当前弹窗，再显示错误提示，避免被遮挡
						this.closeDepositModal()
						this.$nextTick(() => {
							this.$notice.show({
								confirmText: this.$t('ok'),
								showCancel: false,
								title: this.$t('error_title'),
								content: res.data.message
							})
						})
					}
				})
			},
			closeQRCodeModal() {
				this.showQRCodeModal = false
				this.stopCountdown()
				this.qrCodeData = ''
				this.showContinueBtn = false
			},
			qrPayContinue() {
				// 关闭QR Code弹窗
				this.closeQRCodeModal()
				// 显示Notice弹窗
				this.showNoticeModal = true
			},
		},
		mounted() {
			// from tangjq--- 组件挂载时调用 API
			this.get_bank_card_list()
			this.get_agent_bank_card()
			this.set_info()
		},
	}
</script>

<style lang="scss" scoped>
	.account-remove-btn {
		background-color: #E02B2B;
	}

	.disabled-action {
		opacity: 0.5;
	}

	.deposit-component {
		width: 100%;
		height: 100%;
		display: flex;
		flex-direction: column;
	}

	.deposit-scroll {
		flex: 1;
		height: 0;
	}

	.title-tab {
		display: flex;
		flex-direction: row;
		align-items: center;
		width: 100%;
	}

	.register-btn {
		padding: 8px 0;
		border-radius: 8px;
		text-align: center;
		font-weight: 600;
		font-size: 14px;
	}

	.route-shadow {
		background-color: #fff;
		border: 1px solid;
	}

	.amount-input {
		font: inherit;
		letter-spacing: inherit;
		padding: 1px 0px 5px;
		border: 0px;
		box-sizing: content-box;
		background: none;
		height: 1.4375em;
		margin: 0px;
		display: block;
		min-width: 0px;
		width: 100%;
		font-size: 35px;
		font-weight: bold;
		text-align: center;
		height: 60px;
	}

	.limit {
		margin: 1px;
		font-family: __Inter_7be8ac, __Inter_Fallback_7be8ac;
		line-height: 1.5;
		color: rgb(255, 255, 255);
		font-size: 11px;
		font-weight: 600;
		text-align: center;
		opacity: 0.6;
	}

	.amount-select {
		width: 100px;
		height: 30px;
		margin-top: 5px;
		border-radius: 10px;
		color: rgb(12, 53, 106);
		font-weight: 600;
		display: flex;
		flex-direction: column;
		justify-content: center;
		text-align: center;
		background-color: rgb(255, 255, 255);
		box-shadow: rgba(60, 64, 67, 0.3) 0px 1px 2px 0px, rgba(60, 64, 67, 0.15) 0px 1px 3px 1px;
	}

	.search-rec {
		border-radius: 3px;
		border: #0074BE 1px solid;
		height: 37px;
		display: flex;
		flex-direction: row;
		align-items: center;
		padding: 0 12px;
		margin-top: 15px;
	}

	.bank-select {
		display: flex;
		flex-direction: column;
		background-color: white;
		border-radius: 20px;
		top: 76px;
		padding: 10px 0;
		border: solid 1px #C0BEBE;
		position: absolute;
		width: calc(680upx - 22px);
		z-index: 999;
	}

	.round-border {
		border: solid darkgray 1px;
	}

	.no-right-border {
		border: solid darkgray 1px;
		border-right: none;
		padding-right: 1px;
	}

	.tips {
		width: 100%;
		padding: 15px 30px;
		font-family: __Inter_7be8ac, __Inter_Fallback_7be8ac;
		font-weight: 600;
		line-height: 1.6;
		color: rgb(51, 51, 51);
		text-align: initial;
		font-size: 12px;
	}

	.ks {
		margin: 0px;
		font-family: __Inter_7be8ac, __Inter_Fallback_7be8ac;
		line-height: 1.5;
		font-size: 10px;
		font-weight: 600;
		position: absolute;
		right: 80px;
		top: 0px;
	}

	.title-icon {
		width: 50px;
		height: 50px;
	}

	.bank-title {
		font-size: 14px;
		font-weight: bold;
		margin-bottom: 4px;
	}

	/* from tangjq--- 银行卡列表样式 */
	.bank-list-container {
		padding: 20px 5px;
	}

	.bank-card-item {
		width: 100%;
		margin-bottom: 16px;
		border: 2px solid $color-border;
		border-radius: 16px;
		background-color: #fff;
		overflow: hidden;
	}

	.bank-card-content {
		display: flex;
		flex-direction: row;
		align-items: center;
		padding: 10px;
		gap: 16px;
	}

	.delete-btn {
		width: 32px;
		height: 32px;
		display: flex;
		align-items: center;
		justify-content: center;
		background-color: #FF4444;
		border-radius: 6px;
		margin-left: auto;
		flex-shrink: 0;
	}

	.delete-icon {
		font-size: 18px;
		color: #fff;
	}

	.bank-icon {
		width: 40px;
		height: 40px;
		border-radius: 8px;
		flex-shrink: 0;
	}

	.bank-name {
		flex: 1;
		font-size: 16px;
		font-weight: 700;
		color: #003D5B;
	}

	.account-number {
		font-size: 16px;
		font-weight: 400;
		color: #003D5B;
	}

	.add-bank-btn {
		width: 100%;
		height: 60px;
		border: 2px solid $color-primary;
		border-radius: 16px;
		background-color: #fff;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.add-bank-text {
		font-size: 18px;
		font-weight: 600;
		color: $color-primary;
	}

	/* from tangjq--- 添加银行卡弹窗样式 */
	.cu-modal {
		display: none;
		position: fixed;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		background-color: rgba(0, 0, 0, 0.6);
		align-items: center;
		justify-content: center;
		z-index: 9999;
	}

	.cu-modal.show {
		display: flex;
	}

	.add-bank-dialog {
		width: 90%;
		max-width: 600px;
		background-color: #fff;
		border-radius: 16px;
		padding: 24px 20px;
		position: relative;
	}

	.dialog-header {
		background-color: $color-primary;
		margin: -24px -20px 0;
		padding: 8px;
		border-radius: 16px 16px 0 0;
		display: flex;
		justify-content: center;
		align-items: center;
		position: relative;
	}

	.dialog-title {
		font-size: 16px;
		font-weight: 600;
		color: #fff;
		text-align: center;
	}

	.dialog-close {
		font-size: 20px;
		color: #fff;
		font-weight: 300;
		line-height: 1;
		cursor: pointer;
		position: absolute;
		right: 8px;
	}

	.dialog-subtitle {
		margin-top: 20px;
		margin-bottom: 16px;
		text-align: center;
	}

	.dialog-subtitle text {
		font-size: 12px;
		font-weight: 400;
		color: #333;
	}

	.bank-icon-selector {
		display: flex;
		flex-direction: row;
		justify-content: center;
		gap: 16px;
		margin-bottom: 24px;
	}

	.bank-icon-item {
		width: 40px;
		height: 40px;
		border-radius: 8px;
		overflow: hidden;
		border: 2px solid transparent;
	}

	.bank-icon-item.selected {
		border-color: $color-secondary;
	}

	.bank-icon-img {
		width: 100%;
		height: 100%;
	}

	.dialog-form {
		margin-bottom: 24px;
	}

	.form-group {
		margin-bottom: 16px;
		display: flex;
		flex-direction: row;
		align-items: center;
	}

	.form-label {
		font-size: 12px;
		font-weight: 600;
		color: #000;
		width: 120px;
		flex-shrink: 0;
	}

	.form-input {
		flex: 1;
		height: 24px;
		border: 2px solid $color-secondary;
		border-radius: 12px;
		font-size: 12px;
		color: #000;
		text-align: center;
	}

	.confirm-btn {
		width: 100%;
		height: 30px;
		background-color: $color-primary;
		border-radius: 12px;
		border: none;
		font-size: 15px;
		font-weight: 700;
		color: #fff;
		padding: 8px;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.confirm-btn.disabled {
		opacity: 0.5;
	}

	/* from tangjq--- 充值弹窗样式 */
	.deposit-modal-dialog {
		width: 90%;
		max-width: 650px;
		background-color: #fff;
		border-radius: 16px;
		padding: 0;
		position: relative;
		max-height: 90vh;
		overflow-y: auto;
	}

	.deposit-modal-header {
		background-color: $color-primary;
		padding: 8px;
		border-radius: 16px 16px 0 0;
		display: flex;
		justify-content: center;
		align-items: center;
		position: relative;
	}

	.deposit-modal-title {
		font-size: 16px;
		font-weight: 600;
		color: #fff;
		text-align: center;
	}

	.deposit-modal-close {
		font-size: 20px;
		color: #fff;
		font-weight: 300;
		line-height: 1;
		cursor: pointer;
		position: absolute;
		right: 8px;
	}

	.user-account-section {
		background-color: $bg-color-info;
		padding: 20px;
		margin: 0 10px;
	}

	.section-title {
		font-size: 18px;
		font-weight: 700;
		color: $color-primary;
		display: block;
		text-align: center;
		margin-bottom: 16px;
	}

	.info-row {
		display: flex;
		flex-direction: row;
		align-items: center;
		margin-bottom: 12px;
	}

	.info-label {
		font-size: 12px;
		font-weight: 600;
		color: #000;
		width: 120px;
		flex-shrink: 0;
	}

	.bank-type-value {
		display: flex;
		flex-direction: row;
		align-items: center;
		gap: 8px;
	}

	.bank-type-icon {
		width: 35px;
		height: 35px;
		border-radius: 6px;
	}

	.bank-type-text {
		font-size: 12px;
		font-weight: 600;
		color: $color-primary;
	}

	.info-value-box {
		flex: 1;
		height: 24px;
		border: 2px solid $color-secondary;
		border-radius: 12px;
		display: flex;
		align-items: center;
		justify-content: center;
		padding: 0 16px;
	}

	.info-value-text {
		font-size: 12px;
		color: $color-primary;
		font-weight: 600;
	}

	.amount-section {
		padding: 20px;
	}

	.amount-input-box {
		width: 100%;
		height: 40px;
		background-color: $bg-color-info;
		border: 1px solid $color-border-other;
		border-radius: 12px;
		display: flex;
		align-items: center;
		justify-content: center;
		margin-bottom: 8px;
	}

	.amount-input-field {
		font-size: 20px;
		font-weight: 600;
		color: $color-primary;
		text-align: center;
		border: none;
		background: transparent;
		width: 100%;
	}

	.amount-hint {
		font-size: 12px;
		color: #E02B2B;
		text-align: center;
		display: block;
		margin-bottom: 16px;
	}

	.quick-amount-grid {
		display: grid;
		grid-template-columns: repeat(3, 1fr);
		gap: 12px;
	}

	.quick-amount-btn {
		height: 30px;
		background-color: $color-primary;
		border-radius: 12px;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 12px;
		font-weight: 600;
		color: #fff;
		cursor: pointer;
	}

	.quick-amount-btn:active {
		background-color: $color-secondary;
	}

	.payment-channel-section {
		padding: 0 20px 20px;
	}

	.payment-channel-btns {
		display: flex;
		flex-direction: row;
		gap: 12px;
		margin-top: 12px;
	}

	.payment-channel-btn {
		flex: 1;
		height: 35px;
		background-color: $color-primary;
		border-radius: 12px;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 12px;
		font-weight: 600;
		color: #fff;
		cursor: pointer;
	}

	.payment-channel-btn.selected {
		background-color: $color-primary;
		border: 2px solid $color-secondary;
		box-sizing: border-box;
	}

	.payment-channel-single {
		display: flex;
		align-items: center;
		justify-content: center;
		margin-top: 12px;
	}

	/* 仅有一个支付渠道时，默认即为选中态：主色填充 + 亮色描边，明显区别于未选中 */
	.payment-channel-name {
		flex: 1;
		height: 35px;
		background-color: $color-secondary;
		border: 2px solid $color-secondary;
		box-sizing: border-box;
		border-radius: 12px;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 14px;
		font-weight: 700;
		color: white;
	}

	.continue-btn {
		width: calc(100% - 40px);
		height: 30px;
		background-color: $color-primary;
		border-radius: 12px;
		border: none;
		font-size: 16px;
		font-weight: 700;
		color: #fff;
		margin: 0 20px 20px;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.continue-btn:disabled {
		opacity: 0.5;
	}

	/* from tangjq--- Transfer Tips弹窗样式 */
	.transfer-tips-dialog {
		width: 90%;
		max-width: 600px;
		background-color: #fff;
		border-radius: 16px;
		overflow: hidden;
	}

	.transfer-modal-header {
		background-color: $color-primary;
		padding: 8px;
		display: flex;
		justify-content: center;
		align-items: center;
		position: relative;
	}

	.transfer-modal-title {
		font-size: 16px;
		font-weight: 600;
		color: #fff;
		text-align: center;
	}

	.transfer-modal-close {
		font-size: 20px;
		color: #fff;
		font-weight: 300;
		line-height: 1;
		cursor: pointer;
		position: absolute;
		right: 8px;
	}

	.tips-content {
		// background-color: $bg-color-info;
		padding: 20px;
	}

	.tips-row {
		background-color: $bg-color-info;
		display: flex;
		justify-content: space-between;
		align-items: center;
		font-size: 14px;
		padding: 5px 20px;

	}

	.tips-row.highlight {
		font-weight: 700;
		color: $color-primary;
		margin-bottom: 0;
	}

	.tips-label {
		color: $color-primary;
	}

	.tips-value {
		color: $color-primary;
	}

	.tips-continue-btn {
		width: calc(100% - 40px);
		height: 35px;
		background-color: $color-primary;
		border-radius: 12px;
		border: none;
		font-size: 16px;
		font-weight: 700;
		color: #fff;
		margin: 0 20px 20px;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	/* from tangjq--- Transfer Confirm弹窗样式 */
	.transfer-confirm-dialog {
		width: 90%;
		max-width: 650px;
		background-color: #fff;
		border-radius: 16px;
		overflow: hidden;
		max-height: 90vh;
		overflow-y: auto;
	}

	.confirm-section {
		background-color: $bg-color-info;
		padding: 20px;
		margin: 0;
	}

	.confirm-section-title {
		font-size: 12px;
		font-weight: 700;
		color: $color-primary;
		display: block;
		text-align: center;
		margin-bottom: 5px;
	}

	.confirm-row {
		display: flex;
		flex-direction: row;
		align-items: center;
		margin-bottom: 12px;
	}

	.confirm-label {
		font-size: 12px;
		font-weight: 600;
		color: #000;
		width: 120px;
		flex-shrink: 0;
	}

	.confirm-bank-value {
		display: flex;
		flex-direction: row;
		align-items: center;
		gap: 8px;
	}

	.confirm-bank-icon {
		width: 30px;
		height: 30px;
		border-radius: 6px;
	}

	.confirm-bank-text {
		font-size: 12px;
		font-weight: 600;
		color: $color-primary;
	}

	.confirm-value-box {
		flex: 1;
		height: 24px;
		border: 2px solid $color-secondary;
		border-radius: 12px;
		display: flex;
		align-items: center;
		justify-content: center;
		padding: 0 16px;
	}

	.confirm-value-text {
		font-size: 12px;
		color: $color-primary;
		font-weight: 500;
	}

	.confirm-copy-box {
		flex: 1;
		height: 24px;
		border: 2px solid $color-secondary;
		border-radius: 12px;
		display: flex;
		flex-direction: row;
		align-items: center;
		overflow: hidden;
	}

	.confirm-copy-text {
		flex: 1;
		font-size: 12px;
		color: $color-primary;
		font-weight: 500;
		padding-left: 16px;
	}

	.confirm-copy-btn {
		background-color: $color-secondary;
		height: 100%;
		padding: 0 5px;
		display: flex;
		flex-direction: row;
		align-items: center;
		justify-content: center;
		gap: 4px;
		flex-shrink: 0;
	}

	.copy-btn-text {
		font-size: 12px;
		font-weight: 600;
		color: #fff;
	}

	.transfer-arrows {
		display: flex;
		justify-content: center;
		gap: 20px;
		padding: 12px 0;
		background-color: #fff;
	}

	.arrow-icon {
		font-size: 18px;
		color: $color-primary;
		font-weight: bold;
	}

	.transfer-info {
		padding: 20px;
		background-color: #fff;
	}

	.transfer-info-row {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 8px;
	}

	.transfer-info-label {
		font-size: 14px;
		font-weight: 600;
		color: #000;
	}

	.transfer-info-value {
		font-size: 14px;
		font-weight: 700;
		color: $color-primary;
	}

	.countdown-display {
		text-align: center;
		padding: 16px 0;
		background-color: #fff;
	}

	.countdown-text {
		font-size: 20px;
		font-weight: 700;
		color: #E02B2B;
	}

	.transfer-notice {
		padding: 16px 20px;
		background-color: #fff;
	}

	.transfer-notice-text {
		font-size: 12px;
		color: #E02B2B;
		text-align: center;
		display: block;
		line-height: 1.5;
	}

	.transfer-final-btn {
		width: calc(100% - 40px);
		height: 35px;
		background-color: $color-primary;
		border-radius: 12px;
		border: none;
		font-size: 16px;
		font-weight: 700;
		color: #fff;
		margin: 0 20px 20px;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	/* from tangjq--- Notice弹窗样式 */
	.notice-dialog {
		width: 90%;
		max-width: 600px;
		background-color: #fff;
		border-radius: 16px;
		overflow: hidden;
	}

	.notice-header {
		background-color: $color-primary;
		padding: 8px;
		text-align: center;
	}

	.notice-title {
		font-size: 16px;
		font-weight: 700;
		color: #fff;
	}

	.notice-content {
		padding: 40px 30px;
	}

	.notice-text {
		font-size: 14px;
		color: #000;
		text-align: center;
		display: block;
		line-height: 1.6;
	}

	.notice-confirm-btn {
		width: calc(100% - 40px);
		height: 35px;
		background-color: $color-primary;
		border-radius: 12px;
		border: none;
		font-size: 14px;
		font-weight: 700;
		color: #fff;
		margin: 0 20px 20px;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	/* from tangjq--- QR Code弹窗样式 */
	.qrcode-dialog {
		width: 90%;
		max-width: 650px;
		background-color: #fff;
		border-radius: 16px;
		overflow: hidden;
		max-height: 90vh;
		overflow-y: auto;
	}

	.qrcode-modal-header {
		background-color: $color-primary;
		padding: 8px;
		display: flex;
		justify-content: center;
		align-items: center;
		position: relative;
	}

	.qrcode-modal-title {
		font-size: 16px;
		font-weight: 600;
		color: #fff;
		text-align: center;
	}

	.qrcode-modal-close {
		font-size: 20px;
		color: #fff;
		font-weight: 300;
		line-height: 1;
		cursor: pointer;
		position: absolute;
		right: 8px;
	}

	.qrcode-section {
		padding: 8px;
		background-color: #fff;
	}

	.qrcode-container {
		width: 300px;
		height: 300px;
		margin: 0 auto;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.save-qr-btn {
		width: 200px;
		height: 35px;
		background-color: $color-primary;
		border-radius: 12px;
		border: none;
		margin: 20px auto 0;
		display: flex;
		flex-direction: row;
		align-items: center;
		justify-content: center;
		gap: 8px;
	}

	.save-qr-icon {
		font-size: 20px;
		color: #fff;
		font-weight: bold;
	}

	.save-qr-text {
		font-size: 16px;
		font-weight: 600;
		color: #fff;
	}

	.qrcode-tips {
		background-color: $bg-color-info;
		padding: 20px;
		margin: 0;
		display: flex;
		flex-direction: column;
		gap: 12px;
	}

	.qrcode-tips-text {
		font-size: 14px;
		color: $color-primary;
		text-align: center;
		line-height: 1.5;
	}

	.qrcode-tips-warning {
		font-size: 13px;
		color: #E02B2B;
		text-align: center;
		line-height: 1.5;
	}

	.qrcode-info {
		padding: 20px;
		background-color: #fff;
	}

	.qrcode-info-row {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 8px;
	}

	.qrcode-info-label {
		font-size: 14px;
		font-weight: 600;
		color: #000;
	}

	.qrcode-info-value {
		font-size: 14px;
		font-weight: 700;
		color: $color-primary;
	}

	.qrcode-countdown {
		text-align: center;
		padding: 16px 0;
		background-color: #fff;
	}

	.qrcode-countdown-text {
		font-size: 16px;
		font-weight: 700;
		color: #E02B2B;
	}

	.qrcode-continue-btn {
		width: calc(100% - 40px);
		height: 35px;
		background-color: $color-primary;
		border-radius: 12px;
		border: none;
		font-size: 18px;
		font-weight: 700;
		color: #fff;
		margin: 0 20px 20px;
		display: flex;
		align-items: center;
		justify-content: center;
	}
</style>