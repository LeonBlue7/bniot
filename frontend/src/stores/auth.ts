/**
 * 认证状态管理
 * 使用 sessionStorage 存储敏感信息，减少 XSS 风险
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '@/api'
import { secureStorage } from '@/utils/secureStorage'
import type { User, LoginRequest, Token } from '@/types'

export const useAuthStore = defineStore('auth', () => {
  // 状态
  const token = ref<string | null>(secureStorage.getToken())
  const user = ref<User | null>(secureStorage.getUser<User>())
  const loading = ref(false)
  const error = ref<string | null>(null)

  // 计算属性
  const isAuthenticated = computed(() => !!token.value)
  const userRole = computed(() => user.value?.role || null)
  const isAdmin = computed(() => user.value?.role === 'admin')

  // 登录
  async function login(credentials: LoginRequest): Promise<boolean> {
    loading.value = true
    error.value = null

    try {
      const tokenData: Token = await authApi.login(credentials)
      token.value = tokenData.access_token
      secureStorage.setToken(tokenData.access_token)

      // 获取用户信息
      const userData = await authApi.getCurrentUser()
      user.value = userData
      secureStorage.setUser(userData)

      return true
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '登录失败'
      error.value = errorMessage
      return false
    } finally {
      loading.value = false
    }
  }

  // 登出
  function logout(): void {
    token.value = null
    user.value = null
    secureStorage.clear()
  }

  // 刷新用户信息
  async function refreshUser(): Promise<void> {
    if (!token.value) return

    try {
      const userData = await authApi.getCurrentUser()
      user.value = userData
      secureStorage.setUser(userData)
    } catch {
      logout()
    }
  }

  return {
    // 状态
    token,
    user,
    loading,
    error,
    // 计算属性
    isAuthenticated,
    userRole,
    isAdmin,
    // 方法
    login,
    logout,
    refreshUser
  }
})