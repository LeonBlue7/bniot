/**
 * Device Store 测试
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useDeviceStore } from '@/stores/devices'
import type { DeviceListItem, DeviceDetail, DashboardStats, DeviceData } from '@/types'

// Mock device API
vi.mock('@/api/devices', () => ({
  deviceApi: {
    getStats: vi.fn(),
    list: vi.fn(),
    get: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    delete: vi.fn(),
    control: vi.fn(),
    getData: vi.fn()
  }
}))

import { deviceApi } from '@/api/devices'

// Mock 数据 - DeviceListItem 包含实时数据和分区信息
const mockDevices: DeviceListItem[] = [
  {
    id: 1,
    tenant_id: 1,
    device_id: 'IMEI001',
    name: '空调1',
    zone_id: 1,
    protocol_version: 'V10',
    sim_card: null,
    is_online: true,
    last_seen_at: '2024-01-01',
    settings: {},
    created_at: '2024-01-01',
    temp: 25.5,
    humi: 60.2,
    alarmtemp: 0,
    zone_name: '办公区'
  },
  {
    id: 2,
    tenant_id: 1,
    device_id: 'IMEI002',
    name: '空调2',
    zone_id: 1,
    protocol_version: 'V20',
    sim_card: null,
    is_online: false,
    last_seen_at: '2024-01-01',
    settings: {},
    created_at: '2024-01-01',
    temp: null,
    humi: null,
    alarmtemp: null,
    zone_name: null
  }
]

// Mock 设备详情
const mockDeviceDetail: DeviceDetail = {
  id: 1,
  tenant_id: 1,
  device_id: 'IMEI001',
  name: '空调1',
  zone_id: 1,
  protocol_version: 'V10',
  sim_card: '13800138001',
  is_online: true,
  last_seen_at: '2024-01-01',
  settings: {},
  created_at: '2024-01-01',
  zone_name: '办公区',
  firmware_version: '1.0.0',
  temp: 25.5,
  humi: 60.2,
  csq: 25,
  alarmtemp: 0,
  alarmhumi: 0,
  air_err: null,
  airstate: 1,
  current: 5.2,
  supports_runtime: true,
  today_runtime: 8.0,
  month_runtime: 200.0
}

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
    time: '2024-01-01T00:00:00',
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

describe('Device Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  describe('初始状态', () => {
    it('应初始化 devices 为空数组', () => {
      const store = useDeviceStore()
      expect(store.devices).toEqual([])
    })

    it('应初始化 currentDevice 为 null', () => {
      const store = useDeviceStore()
      expect(store.currentDevice).toBeNull()
    })

    it('应初始化 stats 为 null', () => {
      const store = useDeviceStore()
      expect(store.stats).toBeNull()
    })

    it('应初始化 loading 为 false', () => {
      const store = useDeviceStore()
      expect(store.loading).toBe(false)
    })
  })

  describe('计算属性', () => {
    it('onlineDevices 应返回在线设备', () => {
      const store = useDeviceStore()
      store.devices = mockDevices

      expect(store.onlineDevices).toHaveLength(1)
      expect(store.onlineDevices[0].device_id).toBe('IMEI001')
    })

    it('offlineDevices 应返回离线设备', () => {
      const store = useDeviceStore()
      store.devices = mockDevices

      expect(store.offlineDevices).toHaveLength(1)
      expect(store.offlineDevices[0].device_id).toBe('IMEI002')
    })
  })

  describe('fetchStats 方法', () => {
    it('成功获取统计数据', async () => {
      vi.mocked(deviceApi.getStats).mockResolvedValue(mockStats)

      const store = useDeviceStore()
      await store.fetchStats()

      expect(store.stats).toEqual(mockStats)
      expect(store.loading).toBe(false)
    })

    it('获取失败应设置错误', async () => {
      vi.mocked(deviceApi.getStats).mockRejectedValue(new Error('获取失败'))

      const store = useDeviceStore()
      await store.fetchStats()

      expect(store.error).toBe('获取失败')
    })

    it('获取失败（非 Error 对象）应使用默认错误信息', async () => {
      vi.mocked(deviceApi.getStats).mockRejectedValue('string error')

      const store = useDeviceStore()
      await store.fetchStats()

      expect(store.error).toBe('获取统计失败')
    })
  })

  describe('fetchDevices 方法', () => {
    it('成功获取设备列表', async () => {
      const mockResponse = { items: mockDevices, total: 2, skip: 0, limit: 20 }
      vi.mocked(deviceApi.list).mockResolvedValue(mockResponse)

      const store = useDeviceStore()
      await store.fetchDevices()

      expect(store.devices).toEqual(mockDevices)
      expect(store.totalDevices).toBe(2)
    })

    it('支持查询参数', async () => {
      const mockResponse = { items: mockDevices, total: 2, skip: 0, limit: 20 }
      vi.mocked(deviceApi.list).mockResolvedValue(mockResponse)

      const store = useDeviceStore()
      await store.fetchDevices({ zone_id: 1, is_online: true })

      expect(deviceApi.list).toHaveBeenCalledWith({ zone_id: 1, is_online: true })
    })

    it('获取失败应设置错误', async () => {
      vi.mocked(deviceApi.list).mockRejectedValue(new Error('网络错误'))

      const store = useDeviceStore()
      await store.fetchDevices()

      expect(store.error).toBe('网络错误')
    })

    it('获取失败（非 Error 对象）应使用默认错误信息', async () => {
      vi.mocked(deviceApi.list).mockRejectedValue('unknown error')

      const store = useDeviceStore()
      await store.fetchDevices()

      expect(store.error).toBe('获取设备列表失败')
    })
  })

  describe('fetchDevice 方法', () => {
    it('成功获取设备详情', async () => {
      vi.mocked(deviceApi.get).mockResolvedValue(mockDeviceDetail)

      const store = useDeviceStore()
      await store.fetchDevice(1)

      expect(store.currentDevice).toEqual(mockDeviceDetail)
    })

    it('获取失败应设置错误', async () => {
      vi.mocked(deviceApi.get).mockRejectedValue(new Error('设备不存在'))

      const store = useDeviceStore()
      await store.fetchDevice(999)

      expect(store.error).toBe('设备不存在')
    })

    it('获取失败（非 Error 对象）应使用默认错误信息', async () => {
      vi.mocked(deviceApi.get).mockRejectedValue(null)

      const store = useDeviceStore()
      await store.fetchDevice(999)

      expect(store.error).toBe('获取设备详情失败')
    })
  })

  describe('createDevice 方法', () => {
    it('成功创建设备', async () => {
      vi.mocked(deviceApi.create).mockResolvedValue({
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
        created_at: '2024-01-01'
      })
      const newDeviceList = [...mockDevices, {
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
        created_at: '2024-01-01',
        temp: null,
        humi: null,
        alarmtemp: null,
        zone_name: null
      }]
      vi.mocked(deviceApi.list).mockResolvedValue({ items: newDeviceList, total: 3, skip: 0, limit: 20 })

      const store = useDeviceStore()
      const result = await store.createDevice({
        device_id: 'IMEI003',
        name: '新空调',
        tenant_id: 1
      })

      expect(result).toBeTruthy()
    })

    it('创建失败应返回 null', async () => {
      vi.mocked(deviceApi.create).mockRejectedValue(new Error('设备ID已存在'))

      const store = useDeviceStore()
      const result = await store.createDevice({
        device_id: 'IMEI001',
        name: '空调1',
        tenant_id: 1
      })

      expect(result).toBeNull()
      expect(store.error).toBe('设备ID已存在')
    })

    it('创建失败（非 Error 对象）应使用默认错误信息', async () => {
      vi.mocked(deviceApi.create).mockRejectedValue({})

      const store = useDeviceStore()
      const result = await store.createDevice({
        device_id: 'IMEI001',
        name: '空调1',
        tenant_id: 1
      })

      expect(result).toBeNull()
      expect(store.error).toBe('创建设备失败')
    })
  })

  describe('updateDevice 方法', () => {
    it('成功更新设备', async () => {
      const updatedDetail = { ...mockDeviceDetail, name: '更新名称' }
      vi.mocked(deviceApi.update).mockResolvedValue({
        id: 1,
        tenant_id: 1,
        device_id: 'IMEI001',
        name: '更新名称',
        zone_id: 1,
        protocol_version: 'V10',
        sim_card: '13800138001',
        is_online: true,
        last_seen_at: '2024-01-01',
        settings: {},
        created_at: '2024-01-01'
      })
      vi.mocked(deviceApi.get).mockResolvedValue(updatedDetail)

      const store = useDeviceStore()
      const result = await store.updateDevice(1, { name: '更新名称' })

      expect(result).toBeTruthy()
    })

    it('更新失败应返回 null', async () => {
      vi.mocked(deviceApi.update).mockRejectedValue(new Error('更新失败'))

      const store = useDeviceStore()
      const result = await store.updateDevice(1, { name: 'test' })

      expect(result).toBeNull()
      expect(store.error).toBe('更新失败')
    })

    it('更新失败（非 Error 对象）应使用默认错误信息', async () => {
      vi.mocked(deviceApi.update).mockRejectedValue(undefined)

      const store = useDeviceStore()
      const result = await store.updateDevice(1, { name: 'test' })

      expect(result).toBeNull()
      expect(store.error).toBe('更新设备失败')
    })
  })

  describe('deleteDevice 方法', () => {
    it('成功删除设备', async () => {
      vi.mocked(deviceApi.delete).mockResolvedValue({ message: '设备已删除' })

      const store = useDeviceStore()
      store.devices = mockDevices
      const result = await store.deleteDevice(1)

      expect(result).toBe(true)
      expect(store.devices).toHaveLength(1)
      expect(store.devices.find(d => d.id === 1)).toBeUndefined()
    })

    it('删除当前设备应清除', async () => {
      vi.mocked(deviceApi.delete).mockResolvedValue({ message: '设备已删除' })

      const store = useDeviceStore()
      store.devices = mockDevices
      store.currentDevice = mockDeviceDetail

      await store.deleteDevice(1)

      expect(store.currentDevice).toBeNull()
    })

    it('删除失败应返回 false', async () => {
      vi.mocked(deviceApi.delete).mockRejectedValue(new Error('删除失败'))

      const store = useDeviceStore()
      const result = await store.deleteDevice(1)

      expect(result).toBe(false)
      expect(store.error).toBe('删除失败')
    })

    it('删除失败（非 Error 对象）应使用默认错误信息', async () => {
      vi.mocked(deviceApi.delete).mockRejectedValue('')

      const store = useDeviceStore()
      const result = await store.deleteDevice(1)

      expect(result).toBe(false)
      expect(store.error).toBe('删除设备失败')
    })
  })

  describe('controlDevice 方法', () => {
    it('成功发送控制命令', async () => {
      vi.mocked(deviceApi.control).mockResolvedValue({ message: '控制命令已发送' })

      const store = useDeviceStore()
      const result = await store.controlDevice(1, 1)

      expect(result).toBe(true)
      expect(deviceApi.control).toHaveBeenCalledWith(1, 1)
    })

    it('控制失败应设置错误', async () => {
      vi.mocked(deviceApi.control).mockRejectedValue(new Error('设备离线'))

      const store = useDeviceStore()
      const result = await store.controlDevice(1, 1)

      expect(result).toBe(false)
      expect(store.error).toBe('设备离线')
    })

    it('控制失败（非 Error 对象）应使用默认错误信息', async () => {
      vi.mocked(deviceApi.control).mockRejectedValue(123)

      const store = useDeviceStore()
      const result = await store.controlDevice(1, 1)

      expect(result).toBe(false)
      expect(store.error).toBe('控制设备失败')
    })
  })

  describe('fetchDeviceData 方法', () => {
    it('成功获取设备数据', async () => {
      vi.mocked(deviceApi.getData).mockResolvedValue(mockDeviceData)

      const store = useDeviceStore()
      await store.fetchDeviceData(1, 24)

      expect(store.deviceData).toEqual(mockDeviceData)
      expect(deviceApi.getData).toHaveBeenCalledWith(1, { hours: 24 })
    })

    it('获取失败应设置错误', async () => {
      vi.mocked(deviceApi.getData).mockRejectedValue(new Error('获取失败'))

      const store = useDeviceStore()
      await store.fetchDeviceData(1)

      expect(store.error).toBe('获取失败')
    })

    it('获取失败（非 Error 对象）应使用默认错误信息', async () => {
      vi.mocked(deviceApi.getData).mockRejectedValue(false)

      const store = useDeviceStore()
      await store.fetchDeviceData(1)

      expect(store.error).toBe('获取设备数据失败')
    })
  })

  describe('clearCurrentDevice 方法', () => {
    it('应清除当前设备和数据', () => {
      const store = useDeviceStore()
      store.currentDevice = mockDeviceDetail
      store.deviceData = mockDeviceData

      store.clearCurrentDevice()

      expect(store.currentDevice).toBeNull()
      expect(store.deviceData).toEqual([])
    })
  })
})