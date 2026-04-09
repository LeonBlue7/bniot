/**
 * 报表相关 API
 * Phase 4 报表与分析功能
 */
import apiClient from './client'
import type {
  EnergyStatsResponse,
  TrendResponse,
  AlarmStatsResponse,
  RuntimeResponse,
  ReportQueryParams
} from '@/types'

export const reportApi = {
  /**
   * 获取能耗统计数据
   */
  async getEnergyStats(params: ReportQueryParams): Promise<EnergyStatsResponse> {
    const response = await apiClient.get<EnergyStatsResponse>('/reports/energy', { params })
    return response.data
  },

  /**
   * 获取温湿度趋势数据
   */
  async getTrendData(params: ReportQueryParams): Promise<TrendResponse> {
    const response = await apiClient.get<TrendResponse>('/reports/trend', { params })
    return response.data
  },

  /**
   * 获取告警统计数据
   */
  async getAlarmStats(params: ReportQueryParams): Promise<AlarmStatsResponse> {
    const response = await apiClient.get<AlarmStatsResponse>('/reports/alarms', { params })
    return response.data
  },

  /**
   * 获取运行时长统计数据
   */
  async getRuntimeStats(params: ReportQueryParams): Promise<RuntimeResponse> {
    const response = await apiClient.get<RuntimeResponse>('/reports/runtime', { params })
    return response.data
  },

  /**
   * 导出报表
   * @returns CSV 文件下载
   */
  async exportReport(params: ReportQueryParams & { report_type: string; format?: string }): Promise<Blob> {
    const response = await apiClient.get('/reports/export', {
      params,
      responseType: 'blob'
    })
    return response.data
  },

  /**
   * 下载导出的报表文件
   */
  downloadReport(params: ReportQueryParams & { report_type: string; format?: string }, filename?: string): void {
    // 构建带参数的 URL，过滤 undefined 值
    const baseUrl = apiClient.defaults.baseURL || '/api'
    const queryString = new URLSearchParams(
      Object.entries(params)
        .filter(([, value]) => value !== undefined && value !== null)
        .map(([key, value]) => [key, String(value)])
    ).toString()
    const url = `${baseUrl}/reports/export?${queryString}`

    // 创建下载链接
    const link = document.createElement('a')
    link.href = url
    link.download = filename || `${params.report_type}_report.csv`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }
}