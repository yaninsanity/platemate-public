// src/main.ts
import { createApp } from 'vue'
import App from './App.vue'

import router from './router'       // <-- now this is the Router instance
import { createPinia } from 'pinia'

// Vuetify
import 'vuetify/styles'
import '@mdi/font/css/materialdesignicons.css'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import '@/assets/styles/variables.scss'
import '@/assets/styles/global.scss';
import '/src/assets/_layout.css';

const vuetify = createVuetify({
  components,
  directives,
  theme: { defaultTheme: 'light' },
})

const app = createApp(App)
app.use(createPinia())
app.use(router)                    
app.use(vuetify)
app.mount('#app')

// 🎯 performance tuning：移除全局fetchProfile调用
// 原因：
// 1. components call fetchProfile as needed (BaseHeader, ProfileView, CoupleSetupView)
// 2. fetchProfile有2分钟缓存，不会重复调用API
// 3. 在这里调用会导致和组件mount时的调用重复
// 4. Token验证由router守卫和axios拦截器处理

// preloading belongs in a router guard, not here
