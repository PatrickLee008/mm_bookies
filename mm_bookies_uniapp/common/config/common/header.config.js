export default {
	/**
	@matchPage 比赛页面显示筛选、搜索
	@indexPage 首页页面显示顶部导航栏
	@need_login 未登录跳转
	@login_show 未登录隐藏
	@login_page 登陆注册页面不显示未登录顶部按钮
	**/
	navList: [{
			name: 'single',
			url: '/pages/match/home?mix=0',
			icon: 'icon-single',
			matchPage: true,
			indexPage: true,
			need_login: true,
		},
		{
			name: 'mixparlay',
			url: '/pages/match/home?mix=1',
			icon: 'icon-mix',
			matchPage: true,
			indexPage: true,
		},
		{
			name: 'Game',
			url: '/pages/index/game',
			icon: 'icon-game',
			para: 'login',
			indexPage: true,
			// need_login: true,
		},
		{
			name: 'Bet History',
			url: '/pages/orders/home',
			icon: 'icon-history',
			para: 'login',
			indexPage: true,
			need_login: true,
		},
		// {
		// 	name: 'favorite',
		// 	url: '/pages/index/favor',
		// 	icon: 'icon-favor',
		// 	para: 'login',
		// 	indexPage: true,
		// 	need_login: true,
		// },
	],

	bottomList: [{
			name: 'home',
			url: '/pages/match/home',
			icon: 'icon-home',
		},
		{
			name: 'wallet',
			url: '/pages/index/wallet',
			icon: 'icon-wallet',
			need_login: true,
			login_show: true,
		},
		{
			name: 'coupon',
			url: '/pages/index/coupon',
			icon: 'icon-coupon',
		},
		{
			name: 'contact',
			url: '/pages/index/contact',
			icon: 'icon-contact',
		},
		{
			name: 'setting',
			url: '/pages/ucenter/home',
			icon: 'icon-setting',
		},
	],

	otherParaList: [{
			parent_url: '#/pages/index/elect',
			url: '#/pages/subject/college_detail?type=0',
		},
		// 专业选科目
		{
			parent_url: '#/pages/index/subject',
			url: '#/pages/subject/college_detail?type=1',
		},
		// 院校选科目
		{
			parent_url: '#/pages/index/college',
			url: '#/pages/subject/college_detail?type=1&college=1',
		},
	],

	// 底部导航栏子页面
	otherList: [
		// 登录注册の仔
		{
			parent_url: '',
			url: '/pages/login/login',
			login_page: true,
		},
		{
			parent_url: '',
			url: '/pages/login/register',
			login_page: true,
		},
		// 个人中心の仔
		{
			parent_url: '/pages/ucenter/home',
			url: '/pages/ucenter/account',
		},
		{
			parent_url: '/pages/ucenter/home',
			url: '/pages/ucenter/invite/index',
			need_login: true,
		},
		{
			parent_url: '/pages/ucenter/home',
			url: '/pages/ucenter/invite/share',
			need_login: true,
		},
		{
			parent_url: '/pages/ucenter/home',
			url: '/pages/ucenter/language',
		},
		{
			parent_url: '/pages/ucenter/home',
			url: '/pages/ucenter/bonus',
			need_login: true,
		},
		{
			parent_url: '/pages/ucenter/home',
			url: '/pages/ucenter/download',
		},
		{
			parent_url: '/pages/ucenter/home',
			url: '/pages/ucenter/message',
			need_login: true,
		},
		{
			parent_url: '/pages/ucenter/home',
			url: '/pages/ucenter/invite/bonus_dashboard',
			need_login: true,
		},
		{
			parent_url: '/pages/ucenter/home',
			url: '/pages/ucenter/invite/user_dashboard',
			need_login: true,
		},
		// 钱包の仔
		{
			parent_url: '/pages/index/wallet',
			url: '/pages/ucenter/withdraw',
			need_login: true,
		},
		{
			parent_url: '/pages/index/wallet',
			url: '/pages/ucenter/charge',
			need_login: true,
		},
		{
			parent_url: '/pages/index/wallet',
			url: '/pages/payment/payment',
			need_login: true,
		},
	]
}