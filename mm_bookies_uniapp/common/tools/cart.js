import store from '@/store/index.js';
import util from './util.js';

export default {
	initCart() {
		if (store.getters.isLogin) {
			uni.showLoading({
				title: '加载中...',
				mask: true
			});
			util.request('/cart', {}, (res) => {
				uni.hideLoading();

				store.commit('initCart', res.map(e => {
					e.checked = e.checked == 0;
					return e;
				}));
			}, true);
		} else {
			uni.getStorage({
				key: 'cart',
				success: (e) => {
					e = e.data;
					if (e && e.length > 0) {
						store.commit('initCart', e);
					}
				}
			});
		}
	},
	removeGoods(id) {
		return new Promise((resolve, reject) => {
			if (store.getters.isLogin) {
				uni.showLoading({
					title: '处理中...',
					mask: true
				});
				util.request('/cart/remove', {
					id
				}, (res) => {
					uni.hideLoading();

					if (res.state == 'ok') {
						store.commit('removeGoods', id);
						resolve();
					} else {
						reject(res.msg);
					}
				});
			} else {
				store.commit('removeGoods', id);
				resolve();
			}
		});
	},
	syncCart() {
		// 如果购物车中有商品，则自动同步到数据库
		const cart = store.state.cart;
		if (cart.length > 0) {
			util.request('/cart/sync', {
				cartJson: JSON.stringify(cart)
			}, (res) => {
				this.initCart();
			});
		} else {
			this.initCart();
		}
	},
	update(id, payload) {
		const {
			count,
			checked
		} = payload;

		return new Promise((resolve, reject) => {
			if (store.getters.isLogin) {
				uni.showLoading({
					title: '处理中...',
					mask: true
				});
				util.request('/cart/' + (count ? 'updateCount' : 'updateCheck'), {
					id,
					count,
					checked
				}, (res) => {
					uni.hideLoading();

					if (res.state == 'ok') {
						store.commit('updateGoods', {
							id,
							count,
							checked
						});
						resolve();
					} else {
						reject(res.msg);
					}
				});
			} else {
				store.commit('updateGoods', {
					id,
					count,
					checked
				});
				resolve();
			}
		});
	}
}
