import Vue from 'vue'
import VueI18n from 'vue-i18n'

Vue.use(VueI18n)

const i18n = new VueI18n({
  locale: 'mm', // 默认语言
  fallbackLocale: 'mm', // 回退语言
  messages: {
    en: require('./en.json'),
    mm: require('./mm.json'),
    cn: require('./cn.json'),
	th: require('./th.json'),
  }
})

export default i18n