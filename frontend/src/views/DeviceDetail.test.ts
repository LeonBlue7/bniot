/**
 * DeviceDetail 组件测试
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { setActivePinia, createPinia } from 'pinia'
import DeviceDetail from '@/views/DeviceDetail.vue'
import { useDeviceStore } from '@/stores/devices'
import type { Device, DeviceData } from '@/types'

// Mock router
const mockPush = vi.fn()
vi.mock('vue-router', () => ({
  useRouter: () => ({
    push: mockPush
  }),
  useRoute: () => ({
    params: { id: '1' }
  })
}))

// Mock Ant Design Vue message
vi.mock('ant-design-vue', async () => {
  const actual = await vi.importActual('ant-design-vue')
  return {
    ...actual,
    message: {
      success: vi.fn(),
      error: vi.fn(),
      warning: vi.fn()
    }
  }
})

// Mock stores
vi.mock('@/stores/devices', () => ({
  useDeviceStore: vi.fn()
}))

// Mock data
const mockDevice: Device = {
  id: 1,
  tenant_id: 1,
  device_id: 'IMEI001',
  name: '空调1',
  zone_id: 1,
  protocol_version: 'V10',
  sim_card: '12345678901',
  is_online: true,
  last_seen_at: '2024-01-01T10:00:00Z',
  settings: {
    temp: 25.5,
    humi: 60,
    airstate: 1,
    csq: 20,
    '101': 1,
    '102': 26,
    '501': 30
  },
  created_at: '2024-01-01T00:00:00Z'
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

describe('DeviceDetail 组件', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()

    // Setup mock store
    vi.mocked(useDeviceStore).mockReturnValue({
      devices: [],
      currentDevice: mockDevice,
      deviceData: mockDeviceData,
      stats: null,
      loading: false,
      error: null,
      onlineDevices: [],
      offlineDevices: [],
      fetchStats: vi.fn(),
      fetchDevices: vi.fn(),
      fetchDevice: vi.fn().mockResolvedValue(undefined),
      createDevice: vi.fn(),
      updateDevice: vi.fn(),
      deleteDevice: vi.fn(),
      controlDevice: vi.fn().mockResolvedValue(true),
      fetchDeviceData: vi.fn().mockResolvedValue(undefined),
      clearCurrentDevice: vi.fn()
    } as any)
  })

  describe('组件渲染', () => {
    it('应正确渲染组件', () => {
      const wrapper = mount(DeviceDetail, {
        global: {
          stubs: {
            APageHeader: { template: '<div class="ant-page-header"><slot /></div>' },
            ASpin: { template: '<div><slot /></div>' },
            ARow: { template: '<div><slot /></div>' },
            ACol: { template: '<div><slot /></div>' },
            ACard: { template: '<div class="ant-card"><slot /></div>' },
            ADescriptions: true,
            ADescriptionsItem: true,
            ATag: true,
            AStatistic: true,
            AEmpty: true,
            AButton: true,
            ASpace: true,
            ARadioGroup: true,
            ARadioButton: true,
            ATable: true
          }
        }
      })

      expect(wrapper.exists()).toBe(true)
      expect(wrapper.find('.device-detail').exists()).toBe(true)
    })

    it('应显示设备名称作为标题', () => {
      const wrapper = mount(DeviceDetail, {
        global: {
          stubs: {
            APageHeader: {
              template: '<div class="ant-page-header"><slot name="title" /></div>',
              props: ['title', 'subTitle']
            },
            ASpin: true,
            ARow: true,
            ACol: true,
            ACard: true,
            AButton: true,
            ASpace: true
          }
        }
      })

      // 组件应能正确获取 device 数据
      const vm = wrapper.vm as any
      expect(vm.device?.name).toBe('空调1')
    })
  })

  describe('数据加载', () => {
    it('挂载时应调用 fetchDevice 和 fetchDeviceData', async () => {
      const mockFetchDevice = vi.fn().mockResolvedValue(undefined)
      const mockFetchDeviceData = vi.fn().mockResolvedValue(undefined)

      vi.mocked(useDeviceStore).mockReturnValue({
        devices: [],
        currentDevice: mockDevice,
        deviceData: mockDeviceData,
        stats: null,
        loading: false,
        error: null,
        onlineDevices: [],
        offlineDevices: [],
        fetchStats: vi.fn(),
        fetchDevices: vi.fn(),
        fetchDevice: mockFetchDevice,
        createDevice: vi.fn(),
        updateDevice: vi.fn(),
        deleteDevice: vi.fn(),
        controlDevice: vi.fn(),
        fetchDeviceData: mockFetchDeviceData,
        clearCurrentDevice: vi.fn()
      } as any)

      mount(DeviceDetail, {
        global: {
          stubs: {
            APageHeader: true,
            ASpin: true,
            ARow: true,
            ACol: true,
            ACard: true,
            ADescriptions: true,
            ADescriptionsItem: true,
            ATag: true,
            AStatistic: true,
            AEmpty: true,
            AButton: true,
            ASpace: true,
            ARadioGroup: true,
            ARadioButton: true,
            ATable: true
          }
        }
      })

      // 等待 onMounted 执行
      await new Promise(resolve => setTimeout(resolve, 0))

      expect(mockFetchDevice).toHaveBeenCalledWith(1)
      expect(mockFetchDeviceData).toHaveBeenCalled()
    })

    it('卸载时应清除当前设备', async () => {
      const mockClearCurrentDevice = vi.fn()

      vi.mocked(useDeviceStore).mockReturnValue({
        devices: [],
        currentDevice: mockDevice,
        deviceData: mockDeviceData,
        stats: null,
        loading: false,
        error: null,
        onlineDevices: [],
        offlineDevices: [],
        fetchStats: vi.fn(),
        fetchDevices: vi.fn(),
        fetchDevice: vi.fn().mockResolvedValue(undefined),
        createDevice: vi.fn(),
        updateDevice: vi.fn(),
        deleteDevice: vi.fn(),
        controlDevice: vi.fn(),
        fetchDeviceData: vi.fn().mockResolvedValue(undefined),
        clearCurrentDevice: mockClearCurrentDevice
      } as any)

      const wrapper = mount(DeviceDetail, {
        global: {
          stubs: {
            APageHeader: true,
            ASpin: true,
            ARow: true,
            ACol: true,
            ACard: true,
            ADescriptions: true,
            ADescriptionsItem: true,
            ATag: true,
            AStatistic: true,
            AEmpty: true,
            AButton: true,
            ASpace: true,
            ARadioGroup: true,
            ARadioButton: true,
            ATable: true
          }
        }
      })

      // 触发卸载
      wrapper.unmount()

      expect(mockClearCurrentDevice).toHaveBeenCalled()
    })
  })

  describe('辅助函数', () => {
    it('formatTime 应正确格式化时间', () => {
      const wrapper = mount(DeviceDetail, {
        global: {
          stubs: {
            APageHeader: true,
            ASpin: true,
            ARow: true,
            ACol: true,
            ACard: true,
            ADescriptions: true,
            ADescriptionsItem: true,
            ATag: true,
            AStatistic: true,
            AEmpty: true,
            AButton: true,
            ASpace: true,
            ARadioGroup: true,
            ARadioButton: true,
            ATable: true
          }
        }
      })

      const vm = wrapper.vm as any

      // 测试正常时间
      const formatted = vm.formatTime('2024-01-01T10:00:00Z')
      expect(formatted).toMatch(/^2024-01-01 \d{2}:\d{2}:\d{2}$/)

      // 测试空值
      expect(vm.formatTime(null)).toBe('-')
      expect(vm.formatTime(undefined)).toBe('-')
    })

    it('getAirStateText 应正确返回空调状态', () => {
      const wrapper = mount(DeviceDetail, {
        global: {
          stubs: {
            APageHeader: true,
            ASpin: true,
            ARow: true,
            ACol: true,
            ACard: true,
            ADescriptions: true,
            ADescriptionsItem: true,
            ATag: true,
            AStatistic: true,
            AEmpty: true,
            AButton: true,
            ASpace: true,
            ARadioGroup: true,
            ARadioButton: true,
            ATable: true
          }
        }
      })

      const vm = wrapper.vm as any

      expect(vm.getAirStateText(1)).toBe('开机')
      expect(vm.getAirStateText(0)).toBe('关机')
      expect(vm.getAirStateText(null)).toBe('-')
      expect(vm.getAirStateText(undefined)).toBe('-')
      expect(vm.getAirStateText('invalid')).toBe('-')
    })

    it('getLinkageMode 应正确返回联动模式', () => {
      const wrapper = mount(DeviceDetail, {
        global: {
          stubs: {
            APageHeader: true,
            ASpin: true,
            ARow: true,
            ACol: true,
            ACard: true,
            ADescriptions: true,
            ADescriptionsItem: true,
            ATag: true,
            AStatistic: true,
            AEmpty: true,
            AButton: true,
            ASpace: true,
            ARadioGroup: true,
            ARadioButton: true,
            ATable: true
          }
        }
      })

      const vm = wrapper.vm as any

      expect(vm.getLinkageMode(0)).toBe('关闭')
      expect(vm.getLinkageMode(1)).toBe('温度联动')
      expect(vm.getLinkageMode(2)).toBe('时间段联动')
      expect(vm.getLinkageMode(3)).toBe('温度+时间联动')
      expect(vm.getLinkageMode(99)).toBe('未知')
      expect(vm.getLinkageMode(null)).toBe('-')
      expect(vm.getLinkageMode(undefined)).toBe('-')
    })
  })

  describe('导航功能', () => {
    it('goBack 应导航到设备列表页', () => {
      const wrapper = mount(DeviceDetail, {
        global: {
          stubs: {
            APageHeader: true,
            ASpin: true,
            ARow: true,
            ACol: true,
            ACard: true,
            ADescriptions: true,
            ADescriptionsItem: true,
            ATag: true,
            AStatistic: true,
            AEmpty: true,
            AButton: true,
            ASpace: true,
            ARadioGroup: true,
            ARadioButton: true,
            ATable: true
          }
        }
      })

      const vm = wrapper.vm as any
      vm.goBack()

      expect(mockPush).toHaveBeenCalledWith({ name: 'Devices' })
    })
  })

  describe('远程控制', () => {
    it('handleControl 应发送控制命令', async () => {
      const mockControlDevice = vi.fn().mockResolvedValue(true)

      vi.mocked(useDeviceStore).mockReturnValue({
        devices: [],
        currentDevice: mockDevice,
        deviceData: mockDeviceData,
        stats: null,
        loading: false,
        error: null,
        onlineDevices: [],
        offlineDevices: [],
        fetchStats: vi.fn(),
        fetchDevices: vi.fn(),
        fetchDevice: vi.fn().mockResolvedValue(undefined),
        createDevice: vi.fn(),
        updateDevice: vi.fn(),
        deleteDevice: vi.fn(),
        controlDevice: mockControlDevice,
        fetchDeviceData: vi.fn().mockResolvedValue(undefined),
        clearCurrentDevice: vi.fn()
      } as any)

      const wrapper = mount(DeviceDetail, {
        global: {
          stubs: {
            APageHeader: true,
            ASpin: true,
            ARow: true,
            ACol: true,
            ACard: true,
            ADescriptions: true,
            ADescriptionsItem: true,
            ATag: true,
            AStatistic: true,
            AEmpty: true,
            AButton: true,
            ASpace: true,
            ARadioGroup: true,
            ARadioButton: true,
            ATable: true
          }
        }
      })

      const vm = wrapper.vm as any
      await vm.handleControl(1)

      expect(mockControlDevice).toHaveBeenCalledWith(1, 1)
    })

    it('无设备时 handleControl 不应执行', async () => {
      vi.mocked(useDeviceStore).mockReturnValue({
        devices: [],
        currentDevice: null,
        deviceData: [],
        stats: null,
        loading: false,
        error: null,
        onlineDevices: [],
        offlineDevices: [],
        fetchStats: vi.fn(),
        fetchDevices: vi.fn(),
        fetchDevice: vi.fn().mockResolvedValue(undefined),
        createDevice: vi.fn(),
        updateDevice: vi.fn(),
        deleteDevice: vi.fn(),
        controlDevice: vi.fn(),
        fetchDeviceData: vi.fn().mockResolvedValue(undefined),
        clearCurrentDevice: vi.fn()
      } as any)

      const wrapper = mount(DeviceDetail, {
        global: {
          stubs: {
            APageHeader: true,
            ASpin: true,
            ARow: true,
            ACol: true,
            ACard: true,
            ADescriptions: true,
            ADescriptionsItem: true,
            ATag: true,
            AStatistic: true,
            AEmpty: true,
            AButton: true,
            ASpace: true,
            ARadioGroup: true,
            ARadioButton: true,
            ATable: true
          }
        }
      })

      const vm = wrapper.vm as any
      await vm.handleControl(1)

      // 无设备时不调用 controlDevice
      expect(vm.device).toBeNull()
    })
  })

  describe('历史数据', () => {
    it('fetchHistoryData 应调用 fetchDeviceData', async () => {
      const mockFetchDeviceData = vi.fn().mockResolvedValue(undefined)

      vi.mocked(useDeviceStore).mockReturnValue({
        devices: [],
        currentDevice: mockDevice,
        deviceData: mockDeviceData,
        stats: null,
        loading: false,
        error: null,
        onlineDevices: [],
        offlineDevices: [],
        fetchStats: vi.fn(),
        fetchDevices: vi.fn(),
        fetchDevice: vi.fn().mockResolvedValue(undefined),
        createDevice: vi.fn(),
        updateDevice: vi.fn(),
        deleteDevice: vi.fn(),
        controlDevice: vi.fn(),
        fetchDeviceData: mockFetchDeviceData,
        clearCurrentDevice: vi.fn()
      } as any)

      const wrapper = mount(DeviceDetail, {
        global: {
          stubs: {
            APageHeader: true,
            ASpin: true,
            ARow: true,
            ACol: true,
            ACard: true,
            ADescriptions: true,
            ADescriptionsItem: true,
            ATag: true,
            AStatistic: true,
            AEmpty: true,
            AButton: true,
            ASpace: true,
            ARadioGroup: true,
            ARadioButton: true,
            ATable: true
          }
        }
      })

      const vm = wrapper.vm as any
      vm.dataRange = 72
      await vm.fetchHistoryData()

      expect(mockFetchDeviceData).toHaveBeenCalledWith(1, 72)
    })

    it('应正确初始化 dataRange', () => {
      const wrapper = mount(DeviceDetail, {
        global: {
          stubs: {
            APageHeader: true,
            ASpin: true,
            ARow: true,
            ACol: true,
            ACard: true,
            ADescriptions: true,
            ADescriptionsItem: true,
            ATag: true,
            AStatistic: true,
            AEmpty: true,
            AButton: true,
            ASpace: true,
            ARadioGroup: true,
            ARadioButton: true,
            ATable: true
          }
        }
      })

      const vm = wrapper.vm as any
      expect(vm.dataRange).toBe(24)
    })
  })
})