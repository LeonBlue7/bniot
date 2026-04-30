/**
 * 用户管理 API
 */
import apiClient from './client'
import type { User } from '@/types'

export interface UserCreateAPI {
  username: string
  password: string
  role: 'admin' | 'operator' | 'viewer'
}

export interface UserUpdateAPI {
  role?: 'admin' | 'operator' | 'viewer'
}

export interface UserStatusUpdate {
  is_active: boolean
}

export const userApi = {
  /**
   * 获取用户列表
   */
  async list(): Promise<User[]> {
    const response = await apiClient.get<User[]>('/users')
    return response.data
  },

  /**
   * 创建用户
   */
  async create(data: UserCreateAPI): Promise<User> {
    const response = await apiClient.post<User>('/users', data)
    return response.data
  },

  /**
   * 更新用户
   */
  async update(id: number, data: UserUpdateAPI): Promise<User> {
    const response = await apiClient.put<User>(`/users/${id}`, data)
    return response.data
  },

  /**
   * 更新用户状态
   */
  async updateStatus(id: number, data: UserStatusUpdate): Promise<User> {
    const response = await apiClient.patch<User>(`/users/${id}/status`, data)
    return response.data
  },

  /**
   * 删除用户
   */
  async delete(id: number): Promise<{ message: string }> {
    const response = await apiClient.delete<{ message: string }>(`/users/${id}`)
    return response.data
  },

  /**
   * 绑定微信账号
   * @param code - wx.login() 获取的 code
   */
  async bindWechat(code: string): Promise<{ success: boolean; message: string; openid: string }> {
    const response = await apiClient.post<{ success: boolean; message: string; openid: string }>('/users/bind-wechat', { code })
    return response.data
  },

  /**
   * 解绑微信账号
   */
  async unbindWechat(): Promise<{ success: boolean; message: string }> {
    const response = await apiClient.delete<{ success: boolean; message: string }>('/users/unbind-wechat')
    return response.data
  }
}