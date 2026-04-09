/**
 * 设备相关 API
 */
import apiClient from './client'
import type {
  Device,
  DeviceCreate,
  DeviceUpdate,
  DeviceData,
  DashboardStats,
  Message,
  DeviceQueryParams,
  DeviceDataQueryParams
} from '@/types'

export const deviceApi = {
  /**
   * 获取仪表盘统计
   */
  async getStats(): Promise<DashboardStats> {
    const response = await apiClient.get<DashboardStats>('/devices/stats')
    return response.data
  },

  /**
   * 获取设备列表
   */
  async list(params?: DeviceQueryParams): Promise<Device[]> {
    const response = await apiClient.get<Device[]>('/devices', { params })
    return response.data
  },

  /**
   * 获取设备详情
   */
  async get(id: number): Promise<Device> {
    const response = await apiClient.get<Device>(`/devices/${id}`)
    return response.data
  },

  /**
   * 创建设备
   */
  async create(data: DeviceCreate): Promise<Device> {
    const response = await apiClient.post<Device>('/devices', data)
    return response.data
  },

  /**
   * 更新设备
   */
  async update(id: number, data: DeviceUpdate): Promise<Device> {
    const response = await apiClient.put<Device>(`/devices/${id}`, data)
    return response.data
  },

  /**
   * 删除设备
   */
  async delete(id: number): Promise<Message> {
    const response = await apiClient.delete<Message>(`/devices/${id}`)
    return response.data
  },

  /**
   * 远程控制设备
   */
  async control(id: number, airstate: number): Promise<Message> {
    const response = await apiClient.post<Message>(`/devices/${id}/control`, null, {
      params: { airstate }
    })
    return response.data
  },

  /**
   * 获取设备历史数据
   */
  async getData(id: number, params?: DeviceDataQueryParams): Promise<DeviceData[]> {
    const response = await apiClient.get<DeviceData[]>(`/devices/${id}/data`, { params })
    return response.data
  }
}