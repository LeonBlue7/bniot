/**
 * 告警管理 API
 */
import apiClient from './client'
import type { Alarm } from '@/types'

export interface AlarmListParams {
  is_resolved?: boolean
  severity?: string
  type?: string
  device_id?: string
  skip?: number
  limit?: number
}

export interface BatchHandleRequest {
  alarm_ids: number[]
}

/**
 * 批量处理告警返回结果
 */
export interface BatchHandleResult {
  message: string
  handled_count: number
  invalid_ids?: number[]
  warning?: string
}

export const alarmApi = {
  /**
   * 获取告警列表
   */
  async list(params?: AlarmListParams): Promise<Alarm[]> {
    const response = await apiClient.get<Alarm[]>('/alarms', { params })
    return response.data
  },

  /**
   * 处理单个告警
   */
  async handle(alarmId: number): Promise<Alarm> {
    const response = await apiClient.patch<Alarm>(`/alarms/${alarmId}/handle`)
    return response.data
  },

  /**
   * 批量处理告警
   */
  async batchHandle(alarmIds: number[]): Promise<BatchHandleResult> {
    const response = await apiClient.patch<BatchHandleResult>(
      '/alarms/batch-handle',
      { alarm_ids: alarmIds }
    )
    return response.data
  },

  /**
   * 获取告警统计
   */
  async getStats(): Promise<{
    total_alarms: number
    unresolved_alarms: number
    resolved_alarms: number
  }> {
    const response = await apiClient.get<{
      total_alarms: number
      unresolved_alarms: number
      resolved_alarms: number
    }>('/alarms/stats')
    return response.data
  }
}