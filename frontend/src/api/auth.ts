/**
 * 认证相关 API
 */
import apiClient from './client'
import type { Token, User, LoginRequest, PasswordChangeRequest } from '@/types'

export const authApi = {
  /**
   * 用户登录
   */
  async login(data: LoginRequest): Promise<Token> {
    // 使用 OAuth2PasswordRequestForm 格式
    const formData = new URLSearchParams()
    formData.append('username', data.username)
    formData.append('password', data.password)

    const response = await apiClient.post<Token>('/auth/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      }
    })
    return response.data
  },

  /**
   * 获取当前用户信息
   */
  async getCurrentUser(): Promise<User> {
    const response = await apiClient.get<User>('/auth/me')
    return response.data
  },

  /**
   * 修改密码
   */
  async changePassword(data: PasswordChangeRequest): Promise<void> {
    await apiClient.post('/auth/change-password', data)
  }
}