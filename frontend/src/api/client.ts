/**
 * Axios 实例配置
 * 包含 CSRF 保护和安全认证
 */
import axios, { type AxiosInstance, type AxiosError, type InternalAxiosRequestConfig } from 'axios'
import { useAuthStore } from '@/stores/auth'
import { csrfProtection, fetchCsrfToken } from '@/utils/csrf'

// API 基础 URL
const BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'

// 创建 axios 实例
const apiClient: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  },
  withCredentials: true // 启用跨域请求携带 cookies
})

// 初始化 CSRF Token
let csrfInitialized = false

async function initCsrf(): Promise<void> {
  if (csrfInitialized) return
  try {
    await fetchCsrfToken()
    csrfInitialized = true
  } catch {
    // CSRF Token 获取失败，继续请求
  }
}

// 请求拦截器 - 添加 Token 和 CSRF 保护
apiClient.interceptors.request.use(
  async (config: InternalAxiosRequestConfig) => {
    // 初始化 CSRF Token（首次请求时）
    await initCsrf()

    // 添加认证 Token
    const authStore = useAuthStore()
    if (authStore.token) {
      config.headers.Authorization = `Bearer ${authStore.token}`
    }

    // 添加 CSRF Token
    const csrfHeaders = csrfProtection.getHeaders()
    for (const [key, value] of Object.entries(csrfHeaders)) {
      config.headers.set(key, value)
    }

    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器 - 处理错误和刷新 CSRF Token
apiClient.interceptors.response.use(
  (response) => {
    // 如果响应包含新的 CSRF Token，更新存储
    const newCsrfToken = response.headers['x-csrf-token']
    if (newCsrfToken) {
      csrfProtection.setToken(newCsrfToken)
    }
    return response
  },
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      // Token 过期或无效，清除登录状态
      const authStore = useAuthStore()
      authStore.logout()
      // 跳转到登录页
      window.location.href = '/login'
    } else if (error.response?.status === 403) {
      // CSRF 验证失败，尝试刷新 Token
      csrfProtection.refreshToken()
    }
    return Promise.reject(error)
  }
)

export default apiClient