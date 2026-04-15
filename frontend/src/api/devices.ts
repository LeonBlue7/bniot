/**
 * 设备相关 API
 */
import apiClient from './client'
import type {
  Device,
  DeviceListItem,
  DeviceDetail,
  DeviceCreate,
  DeviceUpdate,
  DeviceData,
  DashboardStats,
  Message,
  DeviceQueryParams,
  DeviceDataQueryParams
} from '@/types'

// 开关机事件接口
export interface DeviceEvent {
  time: string
  action: string
  duration: number | null
}

export interface DeviceEventsResponse {
  supported: boolean
  message: string
  events: DeviceEvent[]
  total: number
  page: number
  page_size: number
}

export interface DeviceRuntimeResponse {
  supported: boolean
  message: string
  today_runtime: number | null
  month_runtime: number | null
}

export const deviceApi = {
  /**
   * 获取仪表盘统计
   */
  async getStats(): Promise<DashboardStats> {
    const response = await apiClient.get<DashboardStats>('/devices/stats')
    return response.data
  },

  /**
   * 获取设备列表（包含实时数据和分区信息）
   */
  async list(params?: DeviceQueryParams): Promise<DeviceListItem[]> {
    const response = await apiClient.get<DeviceListItem[]>('/devices', { params })
    return response.data
  },

  /**
   * 获取设备详情（包含完整信息）
   */
  async get(id: number): Promise<DeviceDetail> {
    const response = await apiClient.get<DeviceDetail>(`/devices/${id}`)
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
  },

  /**
   * 获取设备开关机事件记录
   */
  async getEvents(id: number, params?: { page?: number; page_size?: number }): Promise<DeviceEventsResponse> {
    const response = await apiClient.get<DeviceEventsResponse>(`/devices/${id}/events`, { params })
    return response.data
  },

  /**
   * 获取设备运行时间统计
   */
  async getRuntime(id: number): Promise<DeviceRuntimeResponse> {
    const response = await apiClient.get<DeviceRuntimeResponse>(`/devices/${id}/runtime`)
    return response.data
  }
}