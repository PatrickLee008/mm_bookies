export default {
	levels: ['低', '中', '高'],
	colors: ['#e53935', '#ffac13', '#33CC00'],
	securityTips: ['请设置密码', '请绑定邮箱以进一步降低风险', '太棒了，风险已降至最低'],
	buttons: [{
			iconUrl: 'https://s01.mifile.cn/i/user/portal-icon-1.png',
			title: '待支付的订单',
			tip: '查看待支付订单',
			linkUrl: '/pages/order/index?status=1'
		},
		{
			iconUrl: 'https://s01.mifile.cn/i/user/portal-icon-2.png',
			title: '待收货的订单',
			tip: '查看待收货订单',
			linkUrl: '/pages/order/index?status=2'
		},
		{
			iconUrl: 'https://s01.mifile.cn/i/user/portal-icon-3.png',
			title: '待评价商品数',
			tip: '查看待评价商品',
			linkUrl: '/pages/order/comment/index'
		},
		{
			iconUrl: 'https://s01.mifile.cn/i/user/portal-icon-4.png',
			title: '喜欢的商品数',
			tip: '查看喜欢的商品',
			linkUrl: '/pages/user/favorite/index'
		}
	]
}
