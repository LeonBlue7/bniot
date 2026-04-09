/**
 * Devices API 测试
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import MockAdapter from 'axios-mock-adapter'
import apiClient from './client'
import { deviceApi } from './devices'
import type { Device, DeviceCreate, DeviceUpdate, DeviceData, DashboardStats } from '@/types'

// Mock auth store
vi.mock('@/stores/auth', () => ({
  useAuthStore: vi.fn(() => ({
    token: 'test-token',
    logout: vi.fn()
  }))
}))

describe('Devices API', () => {
  let mockAxios: MockAdapter

  // Mock 数据
  const mockDevice: Device = {
    id: 1,
    tenant_id: 1,
    device_id: 'IMEI001',
    name: '空调1',
    zone_id: 1,
    protocol_version: 'V10',
    sim_card: null,
    is_online: true,
    last_seen_at: '2024-01-01T00:00:00Z',
    settings: {},
    created_at: '2024-01-01T00:00:00Z'
  }

  const mockDevices: Device[] = [
    mockDevice,
    {
      id: 2,
      tenant_id: 1,
      device_id: 'IMEI002',
      name: '空调2',
      zone_id: 1,
      protocol_version: 'V20',
      sim_card: null,
      is_online: false,
      last_seen_at: '2024-01-01T00:00:00Z',
      settings: {},
      created_at: '2024-01-01T00:00:00Z'
    }
  ]

  const mockStats: DashboardStats = {
    total_devices: 100,
    online_devices: 80,
    offline_devices: 20,
    total_alarms: 5,
    unresolved_alarms: 3
  }

  const mockDeviceData: DeviceData[] = [
    {
      id: 1,
      time: '2024-01-01T00:00:00Z',
      device_id: 'IMEI001',
      tenant_id: 1,
      temp: 25.5,
      humi: 60,
      airstate: 1,
      current: 2.5,
      csq: 20,
      air_err: 0,
      alarmtemp: 0,
      alarmhumi: 0
    }
  ]

  beforeEach(() => {
    setActivePinia(createPinia())
    mockAxios = new MockAdapter(apiClient)
    vi.clearAllMocks()
  })

  afterEach(() => {
    mockAxios.restore()
  })

  describe('getStats', () => {
    it('应返回仪表盘统计数据', async () => {
      mockAxios.onGet('/devices/stats').reply(200, mockStats)

      const result = await deviceApi.getStats()

      expect(result).toEqual(mockStats)
      expect(result.total_devices).toBe(100)
      expect(result.online_devices).toBe(80)
    })

    it('服务器错误应抛出异常', async () => {
      mockAxios.onGet('/devices/stats').reply(500)

      await expect(deviceApi.getStats()).rejects.toThrow()
    })

    it('网络错误应抛出异常', async () => {
      mockAxios.onGet('/devices/stats').networkError()

      await expect(deviceApi.getStats()).rejects.toThrow()
    })
  })

  describe('list', () => {
    it('应返回设备列表', async () => {
      mockAxios.onGet('/devices').reply(200, mockDevices)

      const result = await deviceApi.list()

      expect(result).toEqual(mockDevices)
      expect(result.length).toBe(2)
    })

    it('支持 zone_id 查询参数', async () => {
      mockAxios.onGet('/devices', { params: { zone_id: 1 } }).reply(200, mockDevices)

      const result = await deviceApi.list({ zone_id: 1 })

      expect(result).toEqual(mockDevices)
    })

    it('支持 is_online 查询参数', async () => {
      mockAxios.onGet('/devices', { params: { is_online: true } }).reply(200, [mockDevice])

      const result = await deviceApi.list({ is_online: true })

      expect(result.length).toBe(1)
      expect(result[0].is_online).toBe(true)
    })

    it('支持 keyword 搜索参数', async () => {
      mockAxios.onGet('/devices', { params: { keyword: '空调1' } }).reply(200, [mockDevice])

      const result = await deviceApi.list({ keyword: '空调1' })

      expect(result.length).toBe(1)
    })

    it('支持分页参数', async () => {
      mockAxios.onGet('/devices', { params: { skip: 0, limit: 10 } }).reply(200, mockDevices)

      await deviceApi.list({ skip: 0, limit: 10 })

      expect(mockAxios.history.get.length).toBe(1)
    })

    it('组合查询参数', async () => {
      mockAxios.onGet('/devices').reply(200, mockDevices)

      await deviceApi.list({
        zone_id: 1,
        is_online: true,
        keyword: '空调',
        skip: 0,
        limit: 10
      })

      const request = mockAxios.history.get[0]
      expect(request.params).toEqual({
        zone_id: 1,
        is_online: true,
        keyword: '空调',
        skip: 0,
        limit: 10
      })
    })

    it('空列表应返回空数组', async () => {
      mockAxios.onGet('/devices').reply(200, [])

      const result = await deviceApi.list()

      expect(result).toEqual([])
    })

    it('无参数调用应成功', async () => {
      mockAxios.onGet('/devices').reply(200, mockDevices)

      const result = await deviceApi.list()

      expect(result).toEqual(mockDevices)
    })
  })

  describe('get', () => {
    it('应返回单个设备详情', async () => {
      mockAxios.onGet('/devices/1').reply(200, mockDevice)

      const result = await deviceApi.get(1)

      expect(result).toEqual(mockDevice)
      expect(result.id).toBe(1)
      expect(result.device_id).toBe('IMEI001')
    })

    it('设备不存在应抛出 404 错误', async () => {
      mockAxios.onGet('/devices/999').reply(404, { detail: 'Device not found' })

      await expect(deviceApi.get(999)).rejects.toThrow()
    })

    it('无权限应抛出 403 错误', async () => {
      mockAxios.onGet('/devices/1').reply(403, { detail: 'Forbidden' })

      await expect(deviceApi.get(1)).rejects.toThrow()
    })

    it('网络错误应抛出异常', async () => {
      mockAxios.onGet('/devices/1').networkError()

      await expect(deviceApi.get(1)).rejects.toThrow()
    })
  })

  describe('create', () => {
    it('应成功创建设备', async () => {
      const createData: DeviceCreate = {
        device_id: 'IMEI003',
        name: '新空调',
        tenant_id: 1
      }
      const newDevice: Device = {
        id: 3,
        tenant_id: 1,
        device_id: 'IMEI003',
        name: '新空调',
        zone_id: null,
        protocol_version: 'V10',
        sim_card: null,
        is_online: false,
        last_seen_at: null,
        settings: {},
        created_at: '2024-01-02T00:00:00Z'
      }

      mockAxios.onPost('/devices').reply(201, newDevice)

      const result = await deviceApi.create(createData)

      expect(result).toEqual(newDevice)
      expect(result.id).toBe(3)
    })

    it('创建带分区 ID 的设备', async () => {
      const createData: DeviceCreate = {
        device_id: 'IMEI004',
        name: '分区空调',
        tenant_id: 1,
        zone_id: 2
      }
      const newDevice: Device = {
        ...mockDevice,
        id: 4,
        device_id: 'IMEI004',
        name: '分区空调',
        zone_id: 2
      }

      mockAxios.onPost('/devices', createData).reply(201, newDevice)

      const result = await deviceApi.create(createData)

      expect(result.zone_id).toBe(2)
    })

    it('设备 ID 已存在应抛出错误', async () => {
      mockAxios.onPost('/devices').reply(400, { detail: 'Device ID already exists' })

      await expect(deviceApi.create({
        device_id: 'IMEI001',
        name: '重复空调',
        tenant_id: 1
      })).rejects.toThrow()
    })

    it('验证失败应抛出错误', async () => {
      mockAxios.onPost('/devices').reply(422, { detail: 'Validation error' })

      await expect(deviceApi.create({
        device_id: '',
        name: '',
        tenant_id: 1
      })).rejects.toThrow()
    })
  })

  describe('update', () => {
    it('应成功更新设备名称', async () => {
      const updateData: DeviceUpdate = { name: '更新后的空调' }
      const updatedDevice: Device = { ...mockDevice, name: '更新后的空调' }

      mockAxios.onPut('/devices/1').reply(200, updatedDevice)

      const result = await deviceApi.update(1, updateData)

      expect(result.name).toBe('更新后的空调')
    })

    it('应成功更新设备分区', async () => {
      const updateData: DeviceUpdate = { zone_id: 3 }
      const updatedDevice: Device = { ...mockDevice, zone_id: 3 }

      mockAxios.onPut('/devices/1').reply(200, updatedDevice)

      const result = await deviceApi.update(1, updateData)

      expect(result.zone_id).toBe(3)
    })

    it('应成功更新多个字段', async () => {
      const updateData: DeviceUpdate = {
        name: '新名称',
        zone_id: 5,
        sim_card: '12345678901'
      }
      const updatedDevice: Device = {
        ...mockDevice,
        name: '新名称',
        zone_id: 5,
        sim_card: '12345678901'
      }

      mockAxios.onPut('/devices/1').reply(200, updatedDevice)

      const result = await deviceApi.update(1, updateData)

      expect(result.name).toBe('新名称')
      expect(result.zone_id).toBe(5)
      expect(result.sim_card).toBe('12345678901')
    })

    it('设备不存在应抛出错误', async () => {
      mockAxios.onPut('/devices/999').reply(404, { detail: 'Device not found' })

      await expect(deviceApi.update(999, { name: 'test' })).rejects.toThrow()
    })

    it('空更新数据应成功', async () => {
      mockAxios.onPut('/devices/1').reply(200, mockDevice)

      const result = await deviceApi.update(1, {})

      expect(result).toEqual(mockDevice)
    })

    it('清除分区（设为 null）', async () => {
      const updateData: DeviceUpdate = { zone_id: null }
      const updatedDevice: Device = { ...mockDevice, zone_id: null }

      mockAxios.onPut('/devices/1').reply(200, updatedDevice)

      const result = await deviceApi.update(1, updateData)

      expect(result.zone_id).toBeNull()
    })
  })

  describe('delete', () => {
    it('应成功删除设备', async () => {
      mockAxios.onDelete('/devices/1').reply(200, { message: 'Device deleted' })

      const result = await deviceApi.delete(1)

      expect(result.message).toBe('Device deleted')
    })

    it('设备不存在应抛出错误', async () => {
      mockAxios.onDelete('/devices/999').reply(404, { detail: 'Device not found' })

      await expect(deviceApi.delete(999)).rejects.toThrow()
    })

    it('设备有告警时可能无法删除', async () => {
      mockAxios.onDelete('/devices/1').reply(400, { detail: 'Device has active alarms' })

      await expect(deviceApi.delete(1)).rejects.toThrow()
    })
  })

  describe('control', () => {
    it('应成功发送开机命令 (airstate=1)', async () => {
      mockAxios.onPost('/devices/1/control').reply(200, { message: 'Control command sent' })

      const result = await deviceApi.control(1, 1)

      expect(result.message).toBe('Control command sent')
      // 验证请求参数
      const request = mockAxios.history.post[0]
      expect(request.params).toEqual({ airstate: 1 })
    })

    it('应成功发送关机命令 (airstate=0)', async () => {
      mockAxios.onPost('/devices/1/control').reply(200, { message: 'Control command sent' })

      await deviceApi.control(1, 0)

      const request = mockAxios.history.post[0]
      expect(request.params).toEqual({ airstate: 0 })
    })

    it('应成功发送复位命令', async () => {
      mockAxios.onPost('/devices/1/control').reply(200, { message: 'Reset command sent' })

      await deviceApi.control(1, 2)

      const request = mockAxios.history.post[0]
      expect(request.params).toEqual({ airstate: 2 })
    })

    it('设备离线应返回错误', async () => {
      mockAxios.onPost('/devices/1/control').reply(400, { detail: 'Device is offline' })

      await expect(deviceApi.control(1, 1)).rejects.toThrow()
    })

    it('设备不存在应抛出错误', async () => {
      mockAxios.onPost('/devices/999/control').reply(404)

      await expect(deviceApi.control(999, 1)).rejects.toThrow()
    })

    it('无效 airstate 值应抛出错误', async () => {
      mockAxios.onPost('/devices/1/control').reply(400, { detail: 'Invalid airstate value' })

      await expect(deviceApi.control(1, 999)).rejects.toThrow()
    })
  })

  describe('getData', () => {
    it('应返回设备历史数据', async () => {
      mockAxios.onGet('/devices/1/data').reply(200, mockDeviceData)

      const result = await deviceApi.getData(1)

      expect(result).toEqual(mockDeviceData)
      expect(result.length).toBe(1)
    })

    it('支持 hours 参数', async () => {
      mockAxios.onGet('/devices/1/data', { params: { hours: 24 } }).reply(200, mockDeviceData)

      await deviceApi.getData(1, { hours: 24 })

      const request = mockAxios.history.get[0]
      expect(request.params).toEqual({ hours: 24 })
    })

    it('支持不同时间范围', async () => {
      mockAxios.onGet('/devices/1/data', { params: { hours: 48 } }).reply(200, mockDeviceData)

      await deviceApi.getData(1, { hours: 48 })

      const request = mockAxios.history.get[0]
      expect(request.params).toEqual({ hours: 48 })
    })

    it('无数据应返回空数组', async () => {
      mockAxios.onGet('/devices/1/data').reply(200, [])

      const result = await deviceApi.getData(1)

      expect(result).toEqual([])
    })

    it('设备不存在应抛出错误', async () => {
      mockAxios.onGet('/devices/999/data').reply(404)

      await expect(deviceApi.getData(999)).rejects.toThrow()
    })

    it('大量数据应正确返回', async () => {
      const largeData: DeviceData[] = Array.from({ length: 1000 }, (_, i) => ({
        id: i + 1,
        time: `2024-01-01T${String(i).padStart(2, '0')}:00:00Z`,
        device_id: 'IMEI001',
        tenant_id: 1,
        temp: 25 + i * 0.1,
        humi: 60,
        airstate: 1,
        current: 2.5,
        csq: 20,
        air_err: 0,
        alarmtemp: 0,
        alarmhumi: 0
      }))

      mockAxios.onGet('/devices/1/data').reply(200, largeData)

      const result = await deviceApi.getData(1)

      expect(result.length).toBe(1000)
    })
  })
})