<template>
	<view>

		<!-- 上半部分 -->
		<view class="up-half-wrapper">
			<view class="wrap">
				<!-- 主要服务 -->
				<view class="service-wrap">
					<block v-for="(item, index) in services" :key="index">
						<a class="service" :href="item.linkUrl" target="_blank">
							<i :class="['icon', item.icon]"></i>
							<view class="name">{{item.name}}</view>
						</a>
					</block>
				</view>
				<!-- 更多服务 -->
				<view class="service-more">
					<!-- 服务链接 -->
					<view class="links">
						<view class="item" v-for="(item, index) in links" :key="index">
							<view class="title">{{item.title}}</view>
							<view class="list">
								<block v-for="(link, linkIndex) in item.list" :key="linkIndex">
									<a class="link" :href="link.linkUrl" target="_blank" @click.stop.prevent="hiddenWechatInfo = false;">{{link.name}}</a>
								</block>
							</view>
						</view>
					</view>
					<!-- 联系我们 -->
					<view class="contact">
						<view class="telphone-number">{{contact.telphoneNumber}}</view>
						<view class="service-range">
							<view class="detail">{{contact.serviceDayRange}} {{contact.serviceTimeRange}}</view>
							<view class="tip">（仅收市话费）</view>
						</view>
						<view class="btn-message" @click="openOnlineService">
							<i class="icon i-message"></i>
							<text class="name">人工客服</text>
						</view>
					</view>
				</view>
			</view>
		</view>

		<!-- 下半部分 -->
		<view class="down-half-wrapper">
			<view class="wrap">
				<!-- 声明信息 -->
				<view class="site-info-wrap">
					<img class="logo" src="/static/image/common/logo.png" />
					<view class="site-info">
						<view class="links">
							<block v-for="(item, index) in siteLinks" :key="index">
								<a class="link" href="https://www.mi.com" target="_blank">{{item}}</a>
							</block>
						</view>
						<view class="info-text">
							© mi.com 京ICP证110507号 京ICP备10046444号 京公网安备11010802020134号 京网文[2020]0276-042号
						</view>
						<view class="info-text">
							（京）网械平台备字（2018）第00005号 互联网药品信息服务资格证 (京)-非经营性-2014-0090 营业执照 医疗器械质量公告
						</view>
						<view class="info-text">
							增值电信业务许可证 网络食品经营备案（京）【2018】WLSPJYBAHF-12 食品经营许可证
						</view>
						<view class="info-text">
							违法和不良信息举报电话：185-0130-1238 知识产权侵权投诉 本网站所列数据，除特殊说明，所有数据均出自我司实验室测试
						</view>
						<view class="info-images">
							<block v-for="(item, index) in siteLinkImages" :key="index">
								<a href="https://www.mi.com" target="_blank">
									<img class="link-image" :src="item" />
								</a>
							</block>
						</view>
					</view>
				</view>
				<!-- 口号 -->
				<img class="slogan" src="https://cnbj1.fds.api.xiaomi.com/staticsfile/global/slogan2020.png" />
			</view>
		</view>

		<!-- 官方微信弹窗 -->
		<zw-dialog :hidden="hiddenWechatInfo" title="小米手机官方微信二维码" :width="680" :height="340" @close="closeDialog">
			<img class="qrcode" src="https://i1.mifile.cn/f/i/17/site/weixin.jpg" />
		</zw-dialog>

	</view>
</template>

<script>
	import footerConfig from '@/common/config/common/footer.config.js';

	export default {
		data() {
			return {
				...footerConfig,
				hiddenWechatInfo: true
			}
		},
		methods: {
			closeDialog() {
				this.hiddenWechatInfo = true;
			},
			openOnlineService() {
				window.open('https://support.kefu.mi.com', 'smallwin', 'width=500, height=750, statue=yes');
			}
		}
	}
</script>

<style lang="scss">
	.up-half-wrapper {
		background-color: $bg-color;

		.wrap {
			width: $page-width;
			margin: 0 auto;

			.service-wrap {
				padding: 27px 0;
				border-bottom: 1px solid #e0e0e0;
				@extend %flex-align-center;
				justify-content: space-between;

				.service {
					width: 19.8%;
					height: 25px;
					border-left: 1px solid #e0e0e0;
					@extend %flex-align-center;
					justify-content: center;
					color: #616161;
					transition: color .2s;

					&:first-child {
						border-left: none;
					}

					&:hover {
						color: $color-primary;
					}

					.icon {
						margin-right: 6px;
						font-size: 24px;
					}

					.name {
						font-size: 16px;
					}
				}
			}

			.service-more {
				@extend %flex-align-center;
				justify-content: space-between;

				.links {
					display: flex;

					.item {
						width: 160px;
						text-align: center;

						.title {
							margin: 26px auto;
							line-height: 1.25;
							color: #424242;
						}

						.link {
							margin-bottom: 10px;
							color: #757575;
							font-size: 12px;
							display: block;

							&:hover {
								color: $color-primary;
							}
						}
					}
				}

				.contact {
					width: 242px;
					height: 112px;
					border-left: 1px solid #e0e0e0;
					text-align: center;

					.telphone-number {
						margin-bottom: 5px;
						font-size: 22px;
						line-height: 1;
						color: $color-primary;
					}

					.service-range {
						margin-bottom: 16px;
						font-size: 12px;
						color: #616161;
					}

					.btn-message {
						margin: 0 auto;
						@extend %flex-align-center;
						justify-content: center;
						width: 118px;
						height: 28px;
						border: 1px solid $color-primary;
						cursor: pointer;
						transition: all .4s;

						&:hover {
							background-color: $color-primary;

							.icon {
								color: $bg-color;
							}

							.name {
								color: $bg-color;
							}
						}

						.icon {
							display: inline-block;
							font-size: 16px;
							color: $color-primary;
							margin-right: 2px;
						}

						.name {
							font-size: 12px;
							color: $color-primary;
						}
					}
				}
			}
		}
	}

	.down-half-wrapper {
		background-color: $bg-color-grey;

		.wrap {
			width: $page-width;
			margin: 0 auto;

			.site-info-wrap {
				display: flex;
				padding-top: 30px;

				.logo {
					width: 57px;
					height: 57px;
					margin-right: 10px;
				}

				.site-info {

					.links a {
						color: #757575;
						line-height: 18px;
						font-size: 12px;
						padding: 0 5px;
						border-left: 1px solid #b0b0b0;

						&:first-child {
							padding-left: 0;
							border-left: none;
						}

						&:hover {
							color: $color-primary;
						}
					}

					.info-text {
						color: #b0b0b0;
						line-height: 18px;
						font-size: 12px;
					}

					.info-images {
						display: flex;
						margin-top: 5px;

						.link-image {
							width: 100px;
							height: 28px;
							object-fit: contain;
							margin-bottom: 5px;

							&:first-child {
								margin-left: -8px;
							}
						}
					}
				}
			}

			.slogan {
				margin: 20px 0;
				width: 100%;
				height: 21px;
				object-fit: contain;
			}
		}
	}

	.qrcode {
		width: 680px;
		height: 340px;
	}
</style>
