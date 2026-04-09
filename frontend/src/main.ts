/**
 * BNIoT 空调节能管理系统前端入口
 * 工业控制中心美学
 */
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import Antd from 'ant-design-vue'
import App from './App.vue'
import router from './router'

// Ant Design Vue 样式
import 'ant-design-vue/dist/reset.css'

// 工业设计系统
import './styles/industrial.css'

// Ant Design Vue 深色主题覆盖
import './style.css'

// 创建应用
const app = createApp(App)

// 使用 Pinia 状态管理
const pinia = createPinia()
app.use(pinia)

// 使用 Vue Router
app.use(router)

// 使用 Ant Design Vue
app.use(Antd)

app.mount('#app')