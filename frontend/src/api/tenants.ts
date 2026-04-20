/**
 * 租户相关 API（仅管理员可用）
 */
import apiClient from './client'

export interface Tenant {
  id: number
  name: string
  code: string
  created_at: string
}

export const tenantApi = {
  /**
   * 获取租户列表（仅管理员）
   */
  async list(): Promise<Tenant[]> {
    const response = await apiClient.get<Tenant[]>('/tenants')
    return response.data
  },

  /**
   * 获取当前用户所属租户信息
   */
  async getCurrent(): Promise<Tenant> {
    const response = await apiClient.get<Tenant>('/tenants/me')
    return response.data
  }
}