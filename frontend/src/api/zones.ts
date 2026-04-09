/**
 * 分区相关 API
 */
import apiClient from './client'
import type { Zone, ZoneCreate, ZoneUpdate, Message } from '@/types'

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
  }
}