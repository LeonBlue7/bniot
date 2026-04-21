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

// 批量操作响应接口
export interface BatchOperationResponse {
  success_count: number
  failed_count: number
  failed_details: Array<{ device_id: number; reason: string }>
}

// 分页响应接口
export interface DeviceListResponse {
  items: DeviceListItem[]
  total: number
  skip: number
  limit: number
}

// 参数信息接口
export interface ParamInfo {
  code: string
  name: string
  type: string
  range: string | null
  desc: string | null
  current_value: any | null
}

// 设备参数响应接口
export interface DeviceParamsResponse {
  version: string
  params: ParamInfo[]
  supported_codes: string[]
}

// 参数设置响应接口
export interface SetParamResponse {
  success: boolean
  message: string
  param_code: string | null
  validation_errors: string[] | null
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
   * 返回分页响应，包含总数
   */
  async list(params?: DeviceQueryParams): Promise<DeviceListResponse> {
    const response = await apiClient.get<DeviceListResponse>('/devices', { params })
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
  },

  /**
   * 批量触发设备版本检测
   * 发送 getparam 命令到在线设备，触发协议版本重新检测
   */
  async batchDetectVersion(deviceIds: number[]): Promise<BatchOperationResponse> {
    const response = await apiClient.post<BatchOperationResponse>('/devices/batch/detect-version', {
      device_ids: deviceIds
    })
    return response.data
  },

  /**
   * 批量移动设备到指定分区
   * @param deviceIds 设备ID列表
   * @param zoneId 目标分区ID（null表示移出分区）
   */
  async batchMoveZone(deviceIds: number[], zoneId: number | null): Promise<BatchOperationResponse> {
    const response = await apiClient.post<BatchOperationResponse>('/devices/batch/move-zone', {
      device_ids: deviceIds,
      zone_id: zoneId
    })
    return response.data
  },

  /**
   * 获取设备支持的参数列表
   */
  async getParams(id: number): Promise<DeviceParamsResponse> {
    const response = await apiClient.get<DeviceParamsResponse>(`/devices/${id}/params`)
    return response.data
  },

  /**
   * 设置单个设备参数
   */
  async setParam(id: number, paramCode: string, paramValue: any): Promise<SetParamResponse> {
    const response = await apiClient.post<SetParamResponse>(`/devices/${id}/set-param`, {
      param_code: paramCode,
      param_value: paramValue
    })
    return response.data
  },

  /**
   * 批量设置设备参数
   */
  async batchSetParam(deviceIds: number[], params: Record<string, any>): Promise<BatchOperationResponse> {
    const response = await apiClient.post<BatchOperationResponse>('/devices/batch/set-param', {
      device_ids: deviceIds,
      params
    })
    return response.data
  }
}