export default [{
		title: '订单中心',
		list: [{
				name: '我的订单',
				linkUrl: '/pages/order/index'
			},
			{
				name: '评价晒单',
				linkUrl: '/pages/order/comment/index'
			}
		]
	},
	{
		title: '个人中心',
		list: [{
				name: '我的个人中心',
				linkUrl: '/pages/user/index'
			},
			{
				name: '喜欢的商品',
				linkUrl: '/pages/user/favorite/index'
			},
			{
				name: '收货地址',
				linkUrl: '/pages/user/profile/shipping-address'
			}
		]
	},
	{
		title: '账户管理',
		list: [{
				name: '个人信息',
				linkUrl: '/pages/user/profile/index'
			},
			{
				name: '账号安全',
				linkUrl: '/pages/user/security/index'
			},
			{
				name: '修改密码',
				linkUrl: '/pages/user/security/index?service=Pwd'
			}
		]
	}
]
