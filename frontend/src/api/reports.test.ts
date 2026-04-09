/**
 * 测试报表 API
 * Phase 4 报表与分析功能 - TDD 开发
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { reportApi } from './reports'

// Mock apiClient
vi.mock('./client', () => ({
  default: {
    get: vi.fn(async () => ({ data: {} })),
    defaults: { baseURL: '/api' }
  }
}))

// Import after mock
import apiClient from './client'

describe('reportApi', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('getEnergyStats', () => {
    it('should call correct endpoint with params', async () => {
      const mockResponse = {
        data: [],
        total_energy: 0,
        start_time: '2024-01-01T00:00:00',
        end_time: '2024-01-02T00:00:00',
        granularity: 'day'
      }

      vi.mocked(apiClient.get).mockResolvedValueOnce({ data: mockResponse })

      const params = {
        start_time: '2024-01-01T00:00:00',
        end_time: '2024-01-02T00:00:00'
      }

      const result = await reportApi.getEnergyStats(params)

      expect(apiClient.get).toHaveBeenCalledWith('/reports/energy', { params })
      expect(result).toEqual(mockResponse)
    })

    it('should return energy stats data', async () => {
      const mockResponse = {
        data: [
          {
            device_id: 'device_001',
            device_name: '测试设备',
            total_energy: 10.5,
            avg_power: 220,
            max_power: 500,
            runtime_hours: 24
          }
        ],
        total_energy: 10.5,
        start_time: '2024-01-01T00:00:00',
        end_time: '2024-01-02T00:00:00',
        granularity: 'day'
      }

      vi.mocked(apiClient.get).mockResolvedValueOnce({ data: mockResponse })

      const result = await reportApi.getEnergyStats({
        start_time: '2024-01-01T00:00:00',
        end_time: '2024-01-02T00:00:00'
      })

      expect(result.data).toHaveLength(1)
      expect(result.data[0].total_energy).toBe(10.5)
    })
  })

  describe('getTrendData', () => {
    it('should call correct endpoint with params', async () => {
      const mockResponse = {
        data: [],
        start_time: '2024-01-01T00:00:00',
        end_time: '2024-01-02T00:00:00',
        interval: 60
      }

      vi.mocked(apiClient.get).mockResolvedValueOnce({ data: mockResponse })

      const params = {
        start_time: '2024-01-01T00:00:00',
        end_time: '2024-01-02T00:00:00',
        interval: 60
      }

      const result = await reportApi.getTrendData(params)

      expect(apiClient.get).toHaveBeenCalledWith('/reports/trend', { params })
      expect(result.interval).toBe(60)
    })
  })

  describe('getAlarmStats', () => {
    it('should call correct endpoint', async () => {
      const mockResponse = {
        data: [],
        total_alarms: 0,
        resolved_alarms: 0,
        unresolved_alarms: 0,
        start_time: '2024-01-01T00:00:00',
        end_time: '2024-01-02T00:00:00'
      }

      vi.mocked(apiClient.get).mockResolvedValueOnce({ data: mockResponse })

      const result = await reportApi.getAlarmStats({
        start_time: '2024-01-01T00:00:00',
        end_time: '2024-01-02T00:00:00'
      })

      expect(apiClient.get).toHaveBeenCalledWith('/reports/alarms', {
        params: {
          start_time: '2024-01-01T00:00:00',
          end_time: '2024-01-02T00:00:00'
        }
      })
      expect(result.total_alarms).toBe(0)
    })

    it('should support group_by parameter', async () => {
      const mockResponse = {
        data: [
          { type: 'offline', severity: 'high', count: 5, resolved_count: 2, unresolved_count: 3 }
        ],
        total_alarms: 5,
        resolved_alarms: 2,
        unresolved_alarms: 3,
        start_time: '2024-01-01T00:00:00',
        end_time: '2024-01-02T00:00:00'
      }

      vi.mocked(apiClient.get).mockResolvedValueOnce({ data: mockResponse })

      const result = await reportApi.getAlarmStats({
        start_time: '2024-01-01T00:00:00',
        end_time: '2024-01-02T00:00:00',
        group_by: 'type'
      })

      expect(result.data[0].type).toBe('offline')
      expect(result.data[0].count).toBe(5)
    })
  })

  describe('getRuntimeStats', () => {
    it('should call correct endpoint', async () => {
      const mockResponse = {
        data: [],
        total_devices: 0,
        avg_runtime_hours: 0,
        start_time: '2024-01-01T00:00:00',
        end_time: '2024-01-02T00:00:00'
      }

      vi.mocked(apiClient.get).mockResolvedValueOnce({ data: mockResponse })

      const result = await reportApi.getRuntimeStats({
        start_time: '2024-01-01T00:00:00',
        end_time: '2024-01-02T00:00:00'
      })

      expect(apiClient.get).toHaveBeenCalledWith('/reports/runtime', {
        params: {
          start_time: '2024-01-01T00:00:00',
          end_time: '2024-01-02T00:00:00'
        }
      })
      expect(result.total_devices).toBe(0)
    })

    it('should return runtime data', async () => {
      const mockResponse = {
        data: [
          {
            device_id: 'device_001',
            device_name: '测试设备',
            zone_name: '一楼',
            total_runtime_hours: 100,
            on_time_percentage: 80,
            on_count: 5,
            off_count: 5
          }
        ],
        total_devices: 1,
        avg_runtime_hours: 100,
        start_time: '2024-01-01T00:00:00',
        end_time: '2024-01-02T00:00:00'
      }

      vi.mocked(apiClient.get).mockResolvedValueOnce({ data: mockResponse })

      const result = await reportApi.getRuntimeStats({
        start_time: '2024-01-01T00:00:00',
        end_time: '2024-01-02T00:00:00'
      })

      expect(result.data[0].total_runtime_hours).toBe(100)
      expect(result.data[0].on_time_percentage).toBe(80)
    })
  })

  describe('exportReport', () => {
    it('should call export endpoint with blob response type', async () => {
      const mockBlob = new Blob(['test,csv\n1,2,3'], { type: 'text/csv' })

      vi.mocked(apiClient.get).mockResolvedValueOnce({ data: mockBlob })

      const result = await reportApi.exportReport({
        report_type: 'energy',
        start_time: '2024-01-01T00:00:00',
        end_time: '2024-01-02T00:00:00'
      })

      expect(apiClient.get).toHaveBeenCalledWith('/reports/export', {
        params: {
          report_type: 'energy',
          start_time: '2024-01-01T00:00:00',
          end_time: '2024-01-02T00:00:00'
        },
        responseType: 'blob'
      })
      expect(result).toBeInstanceOf(Blob)
    })
  })

  describe('downloadReport', () => {
    it('should create download link', () => {
      // Mock DOM methods
      const mockLink = {
        href: '',
        download: '',
        click: vi.fn()
      }

      const createElementSpy = vi.spyOn(document, 'createElement').mockReturnValue(mockLink as unknown as HTMLAnchorElement)
      const bodyAppendSpy = vi.spyOn(document.body, 'appendChild').mockImplementation(() => document.body)
      const bodyRemoveSpy = vi.spyOn(document.body, 'removeChild').mockImplementation(() => document.body)

      reportApi.downloadReport({
        report_type: 'energy',
        start_time: '2024-01-01T00:00:00',
        end_time: '2024-01-02T00:00:00'
      })

      expect(createElementSpy).toHaveBeenCalledWith('a')
      expect(mockLink.click).toHaveBeenCalled()

      createElementSpy.mockRestore()
      bodyAppendSpy.mockRestore()
      bodyRemoveSpy.mockRestore()
    })
  })
})