/**
 * 分区相关 API
 */
import apiClient from './client'
import type { Zone, ZoneCreate, ZoneUpdate, Message } from '@/types'

// 分区授权接口
export interface ZoneAuthorization {
  id: number
  zone_id: number
  tenant_id: number
  created_at: string
}

export const zoneApi = {
  /**
   * 获取分区列表
   */
  async list(): Promise<Zone[]> {
    const response = await apiClient.get<Zone[]>('/zones')
    return response.data
  },

  /**
   * 创建分区
   */
  async create(data: ZoneCreate): Promise<Zone> {
    const response = await apiClient.post<Zone>('/zones', data)
    return response.data
  },

  /**
   * 更新分区
   */
  async update(id: number, data: ZoneUpdate): Promise<Zone> {
    const response = await apiClient.put<Zone>(`/zones/${id}`, data)
    return response.data
  },

  /**
   * 删除分区
   */
  async delete(id: number): Promise<Message> {
    const response = await apiClient.delete<Message>(`/zones/${id}`)
    return response.data
  },

  /**
   * 获取分区授权列表
   */
  async listAuthorizations(zoneId: number): Promise<ZoneAuthorization[]> {
    const response = await apiClient.get<ZoneAuthorization[]>(`/zones/${zoneId}/authorizations`)
    return response.data
  },

  /**
   * 将分区授权给租户
   */
  async authorize(zoneId: number, tenantId: number): Promise<ZoneAuthorization> {
    const response = await apiClient.post<ZoneAuthorization>(
      `/zones/${zoneId}/authorizations`,
      null,
      { params: { tenant_id: tenantId } }
    )
    return response.data
  },

  /**
   * 移除分区授权
   */
  async removeAuthorization(zoneId: number, tenantId: number): Promise<Message> {
    const response = await apiClient.delete<Message>(
      `/zones/${zoneId}/authorizations/${tenantId}`
    )
    return response.data
  }
}