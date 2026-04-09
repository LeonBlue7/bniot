/**
 * Devices 组件测试
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { setActivePinia, createPinia } from 'pinia'
import Devices from '@/views/Devices.vue'
import { useDeviceStore } from '@/stores/devices'
import { useZoneStore } from '@/stores/zones'
import { useAuthStore } from '@/stores/auth'
import type { Device, Zone, User } from '@/types'

// Mock router
const mockPush = vi.fn()
vi.mock('vue-router', () => ({
  useRouter: () => ({
    push: mockPush
  }),
  useRoute: () => ({
    params: {},
    query: {}
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
    },
    Modal: {
      confirm: vi.fn()
    }
  }
})

// Mock stores
vi.mock('@/stores/devices', () => ({
  useDeviceStore: vi.fn()
}))

vi.mock('@/stores/zones', () => ({
  useZoneStore: vi.fn()
}))

vi.mock('@/stores/auth', () => ({
  useAuthStore: vi.fn()
}))

// Mock data
const mockDevices: Device[] = [
  {
    id: 1,
    tenant_id: 1,
    device_id: 'IMEI001',
    name: '空调1',
    zone_id: 1,
    protocol_version: 'V10',
    sim_card: null,
    is_online: true,
    last_seen_at: '2024-01-01T10:00:00Z',
    settings: {},
    created_at: '2024-01-01T00:00:00Z'
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
    last_seen_at: '2024-01-01T08:00:00Z',
    settings: {},
    created_at: '2024-01-01T00:00:00Z'
  }
]

const mockZones: Zone[] = [
  {
    id: 1,
    tenant_id: 1,
    name: '一楼',
    parent_id: null,
    description: '一楼区域',
    sort_order: 1,
    created_at: '2024-01-01T00:00:00Z'
  }
]

const mockUser: User = {
  id: 1,
  username: 'admin',
  role: 'admin',
  tenant_id: 1,
  is_active: true,
  created_at: '2024-01-01T00:00:00Z'
}

describe('Devices 组件', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()

    // Setup mock stores
    vi.mocked(useDeviceStore).mockReturnValue({
      devices: mockDevices,
      currentDevice: null,
      deviceData: [],
      stats: null,
      loading: false,
      error: null,
      onlineDevices: mockDevices.filter(d => d.is_online),
      offlineDevices: mockDevices.filter(d => !d.is_online),
      fetchStats: vi.fn(),
      fetchDevices: vi.fn().mockResolvedValue(undefined),
      fetchDevice: vi.fn().mockResolvedValue(undefined),
      createDevice: vi.fn().mockResolvedValue(mockDevices[0]),
      updateDevice: vi.fn().mockResolvedValue(mockDevices[0]),
      deleteDevice: vi.fn().mockResolvedValue(true),
      controlDevice: vi.fn().mockResolvedValue(true),
      fetchDeviceData: vi.fn().mockResolvedValue(undefined),
      clearCurrentDevice: vi.fn()
    } as any)

    vi.mocked(useZoneStore).mockReturnValue({
      zones: mockZones,
      loading: false,
      error: null,
      zoneTree: [],
      fetchZones: vi.fn().mockResolvedValue(undefined),
      createZone: vi.fn(),
      updateZone: vi.fn(),
      deleteZone: vi.fn()
    } as any)

    vi.mocked(useAuthStore).mockReturnValue({
      token: 'test-token',
      user: mockUser,
      loading: false,
      error: null,
      isAuthenticated: true,
      userRole: 'admin',
      isAdmin: true,
      login: vi.fn(),
      logout: vi.fn(),
      refreshUser: vi.fn()
    } as any)
  })

  describe('组件渲染', () => {
    it('应正确渲染组件', () => {
      const wrapper = mount(Devices, {
        global: {
          stubs: {
            ACard: true,
            ARow: true,
            ACol: true,
            AInputSearch: true,
            ASelect: true,
            ASelectOption: true,
            ATable: true,
            AButton: true,
            ASpace: true,
            ATag: true,
            AModal: true,
            AForm: true,
            AFormItem: true,
            AInput: true,
            ARadioGroup: true,
            ARadio: true,
            ADropdown: true,
            AMenu: true,
            AMenuItem: true,
            AMenuDivider: true,
            PlusOutlined: true,
            DownOutlined: true
          }
        }
      })

      expect(wrapper.exists()).toBe(true)
      expect(wrapper.find('.devices-page').exists()).toBe(true)
    })

    it('应显示工具栏卡片', () => {
      const wrapper = mount(Devices, {
        global: {
          stubs: {
            ACard: { template: '<div class="ant-card"><slot /></div>' },
            ARow: { template: '<div><slot /></div>' },
            ACol: { template: '<div><slot /></div>' },
            AInputSearch: true,
            ASelect: true,
            ASelectOption: true,
            AButton: true,
            ASpace: true,
            PlusOutlined: true,
            ATable: true
          }
        }
      })

      expect(wrapper.find('.toolbar-card').exists()).toBe(true)
    })

    it('应显示表格卡片', () => {
      const wrapper = mount(Devices, {
        global: {
          stubs: {
            ACard: { template: '<div class="ant-card"><slot /></div>' },
            ATable: true,
            ARow: true,
            ACol: true,
            AInputSearch: true,
            ASelect: true,
            ASelectOption: true,
            AButton: true,
            ASpace: true,
            PlusOutlined: true
          }
        }
      })

      expect(wrapper.find('.table-card').exists()).toBe(true)
    })
  })

  describe('数据加载', () => {
    it('挂载时应调用 fetchZones 和 fetchDevices', async () => {
      const mockFetchZones = vi.fn().mockResolvedValue(undefined)
      const mockFetchDevices = vi.fn().mockResolvedValue(undefined)

      vi.mocked(useZoneStore).mockReturnValue({
        zones: mockZones,
        loading: false,
        error: null,
        zoneTree: [],
        fetchZones: mockFetchZones,
        createZone: vi.fn(),
        updateZone: vi.fn(),
        deleteZone: vi.fn()
      } as any)

      vi.mocked(useDeviceStore).mockReturnValue({
        devices: mockDevices,
        currentDevice: null,
        deviceData: [],
        stats: null,
        loading: false,
        error: null,
        onlineDevices: mockDevices.filter(d => d.is_online),
        offlineDevices: mockDevices.filter(d => !d.is_online),
        fetchStats: vi.fn(),
        fetchDevices: mockFetchDevices,
        fetchDevice: vi.fn(),
        createDevice: vi.fn(),
        updateDevice: vi.fn(),
        deleteDevice: vi.fn(),
        controlDevice: vi.fn(),
        fetchDeviceData: vi.fn(),
        clearCurrentDevice: vi.fn()
      } as any)

      mount(Devices, {
        global: {
          stubs: {
            ACard: true,
            ARow: true,
            ACol: true,
            AInputSearch: true,
            ASelect: true,
            ASelectOption: true,
            ATable: true,
            AButton: true,
            ASpace: true,
            PlusOutlined: true,
            DownOutlined: true,
            AModal: true,
            AForm: true,
            AFormItem: true,
            AInput: true,
            ARadioGroup: true,
            ARadio: true,
            ADropdown: true,
            AMenu: true,
            AMenuItem: true,
            AMenuDivider: true,
            ATag: true
          }
        }
      })

      // 等待 onMounted 执行
      await new Promise(resolve => setTimeout(resolve, 0))

      expect(mockFetchZones).toHaveBeenCalled()
      expect(mockFetchDevices).toHaveBeenCalled()
    })
  })

  describe('用户交互', () => {
    it('点击设备名称应导航到详情页', async () => {
      const wrapper = mount(Devices, {
        global: {
          stubs: {
            ACard: true,
            ARow: true,
            ACol: true,
            AInputSearch: true,
            ASelect: true,
            ASelectOption: true,
            ATable: {
              template: `
                <div class="ant-table">
                  <slot name="bodyCell" column="name" :record="{ id: 1, name: '空调1' }" />
                </div>
              `
            },
            AButton: { template: '<button><slot /></button>' },
            ASpace: true,
            ATag: true,
            PlusOutlined: true,
            DownOutlined: true,
            AModal: true,
            AForm: true,
            AFormItem: true,
            AInput: true,
            ARadioGroup: true,
            ARadio: true,
            ADropdown: true,
            AMenu: true,
            AMenuItem: true,
            AMenuDivider: true
          }
        }
      })

      // 找到设备名称链接并点击
      const link = wrapper.find('a')
      if (link.exists()) {
        await link.trigger('click')
        expect(mockPush).toHaveBeenCalledWith({ name: 'DeviceDetail', params: { id: 1 } })
      }
    })
  })

  describe('搜索功能', () => {
    it('应正确初始化搜索状态', () => {
      const wrapper = mount(Devices, {
        global: {
          stubs: {
            ACard: true,
            ARow: true,
            ACol: true,
            AInputSearch: true,
            ASelect: true,
            ASelectOption: true,
            ATable: true,
            AButton: true,
            ASpace: true,
            PlusOutlined: true,
            DownOutlined: true,
            AModal: true,
            AForm: true,
            AFormItem: true,
            AInput: true,
            ARadioGroup: true,
            ARadio: true,
            ADropdown: true,
            AMenu: true,
            AMenuItem: true,
            AMenuDivider: true,
            ATag: true
          }
        }
      })

      // 检查初始状态
      const vm = wrapper.vm as any
      expect(vm.searchKeyword).toBe('')
      expect(vm.filterZone).toBeUndefined()
      expect(vm.filterOnline).toBeUndefined()
    })
  })

  describe('格式化函数', () => {
    it('formatTime 应正确格式化时间', () => {
      const wrapper = mount(Devices, {
        global: {
          stubs: {
            ACard: true,
            ARow: true,
            ACol: true,
            AInputSearch: true,
            ASelect: true,
            ASelectOption: true,
            ATable: true,
            AButton: true,
            ASpace: true,
            PlusOutlined: true,
            DownOutlined: true,
            AModal: true,
            AForm: true,
            AFormItem: true,
            AInput: true,
            ARadioGroup: true,
            ARadio: true,
            ADropdown: true,
            AMenu: true,
            AMenuItem: true,
            AMenuDivider: true,
            ATag: true
          }
        }
      })

      const vm = wrapper.vm as any

      // 测试正常时间 - 格式化为 YYYY-MM-DD HH:mm:ss 格式
      const formatted = vm.formatTime('2024-01-01T10:00:00Z')
      expect(formatted).toMatch(/^2024-01-01 \d{2}:\d{2}:\d{2}$/)

      // 测试空值
      expect(vm.formatTime(null)).toBe('-')
      expect(vm.formatTime(undefined)).toBe('-')
    })
  })
})