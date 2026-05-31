import Vue from 'vue'
import VueI18n from 'vue-i18n'

Vue.use(VueI18n)

const i18n = new VueI18n({
  locale: 'mm', // 默认语言（缅甸语）
  fallbackLocale: 'en', // 回退语言（key 缺失时回退英文）
  messages: {
    en: require('./en.json'),
    mm: require('./mm.json'),
    cn: require('./cn.json'),
	th: require('./th.json'),
  }
})

export default i18n