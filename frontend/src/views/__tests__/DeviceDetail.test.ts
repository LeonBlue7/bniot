/**
 * DeviceDetail 页面版本差异化渲染测试
 * TDD: 测试条件渲染逻辑
 *
 * 测试策略：
 * - 源代码静态分析：验证组件包含必要字段和条件渲染
 * - 运行时行为通过 E2E 测试覆盖（playwright）
 *
 * 测试目标：
 * - V10设备显示电流、空调状态、运行统计、开关机记录
 * - V20设备显示"协议不支持"提示
 * - null值时隐藏对应字段
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import Antd from 'ant-design-vue'

// Mock router
vi.mock('vue-router', () => ({
  useRouter: vi.fn(() => ({
    push: vi.fn()
  })),
  useRoute: vi.fn(() => ({
    params: { id: '1' }
  }))
}))

// Mock device store - 返回空状态
vi.mock('@/stores/devices', () => ({
  useDeviceStore: vi.fn(() => ({
    currentDevice: null,
    deviceData: [],
    loading: false,
    fetchDevice: vi.fn(() => Promise.resolve()),
    fetchDeviceData: vi.fn(() => Promise.resolve()),
    controlDevice: vi.fn(),
    clearCurrentDevice: vi.fn()
  }))
}))

// Mock device API
vi.mock('@/api/devices', () => ({
  deviceApi: {
    getEvents: vi.fn(() => Promise.resolve({
      supported: false,
      message: '',
      events: [],
      total: 0,
      page: 1,
      page_size: 20
    }))
  }
}))

// Mock dayjs
vi.mock('dayjs', () => ({
  default: vi.fn((date) => ({
    format: vi.fn(() => date ? String(date).slice(0, 19).replace('T', ' ') : '2024-01-01 00:00:00')
  }))
}))

// Ant Design Vue stubs - 简化版本
const antdStubs = {
  'a-page-header': {
    template: '<div class="ant-page-header"><slot /><slot name="extra" /></div>',
    props: ['title', 'sub-title']
  },
  'a-spin': {
    template: '<div class="ant-spin"><slot /></div>',
    props: ['spinning']
  },
  'a-row': {
    template: '<div class="ant-row"><slot /></div>',
    props: ['gutter']
  },
  'a-col': {
    template: '<div class="ant-col"><slot /></div>',
    props: ['span']
  },
  'a-card': {
    template: '<div class="ant-card"><div class="ant-card-head" v-if="title">{{ title }}</div><div class="ant-card-body"><slot /></div></div>',
    props: ['title', 'size', 'style']
  },
  'a-descriptions': {
    template: '<div class="ant-descriptions"><slot /></div>',
    props: ['column', 'size', 'bordered']
  },
  'a-descriptions-item': {
    template: '<div class="ant-descriptions-item"><span class="ant-descriptions-item-label">{{ label }}</span><span class="ant-descriptions-item-content"><slot /></span></div>',
    props: ['label']
  },
  'a-statistic': {
    template: '<div class="ant-statistic"><div class="ant-statistic-title">{{ title }}</div><div class="ant-statistic-content"><span class="ant-statistic-content-value">{{ value }}</span><span class="ant-statistic-content-suffix">{{ suffix }}</span><slot name="formatter" /></div></div>',
    props: ['title', 'value', 'suffix']
  },
  'a-tag': {
    template: '<span class="ant-tag" :class="[\'ant-tag-\' + color]"><slot /></span>',
    props: ['color']
  },
  'a-table': {
    template: '<div class="ant-table"><slot /></div>',
    props: ['columns', 'data-source', 'loading', 'pagination', 'row-key', 'size']
  },
  'a-empty': {
    template: '<div class="ant-empty">{{ description }}</div>',
    props: ['description']
  },
  'a-button': {
    template: '<button class="ant-btn"><slot /></button>',
    props: ['type', 'style']
  },
  'a-space': {
    template: '<div class="ant-space"><slot /></div>',
    props: []
  },
  'a-radio-group': {
    template: '<div class="ant-radio-group"><slot /></div>',
    props: ['value']
  },
  'a-radio-button': {
    template: '<label class="ant-radio-button"><slot /></label>',
    props: ['value']
  },
  'a-modal': {
    template: '<div class="ant-modal"><slot /></div>',
    props: ['open', 'title', 'width', 'footer']
  }
}

describe('DeviceDetail 页面版本差异化渲染', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('组件基础结构', () => {
    it('组件应该能够挂载', async () => {
      const DeviceDetailComponent = (await import('@/views/DeviceDetail.vue')).default

      const wrapper = mount(DeviceDetailComponent, {
        global: {
          stubs: antdStubs,
          plugins: [Antd]
        }
      })

      await flushPromises()

      // 组件应该成功挂载
      expect(wrapper.find('.device-detail').exists()).toBe(true)
      expect(wrapper.find('.ant-page-header').exists()).toBe(true)
    })

    it('应该包含基本信息卡片', async () => {
      const DeviceDetailComponent = (await import('@/views/DeviceDetail.vue')).default

      const wrapper = mount(DeviceDetailComponent, {
        global: {
          stubs: antdStubs,
          plugins: [Antd]
        }
      })

      await flushPromises()

      // 应该有基本信息卡片
      const cards = wrapper.findAll('.ant-card')
      const basicInfoCard = cards.find(card =>
        card.find('.ant-card-head').text().includes('基本信息')
      )

      expect(basicInfoCard?.exists()).toBe(true)
    })

    it('应该包含告警状态卡片', async () => {
      const DeviceDetailComponent = (await import('@/views/DeviceDetail.vue')).default

      const wrapper = mount(DeviceDetailComponent, {
        global: {
          stubs: antdStubs,
          plugins: [Antd]
        }
      })

      await flushPromises()

      // 应该有告警状态卡片
      const cards = wrapper.findAll('.ant-card')
      const alarmCard = cards.find(card =>
        card.find('.ant-card-head').text().includes('告警状态')
      )

      expect(alarmCard?.exists()).toBe(true)
    })

    it('应该包含开关机记录卡片', async () => {
      const DeviceDetailComponent = (await import('@/views/DeviceDetail.vue')).default

      const wrapper = mount(DeviceDetailComponent, {
        global: {
          stubs: antdStubs,
          plugins: [Antd]
        }
      })

      await flushPromises()

      // 应该有开关机记录卡片
      const cards = wrapper.findAll('.ant-card')
      const eventsCard = cards.find(card =>
        card.find('.ant-card-head').text().includes('开关机记录')
      )

      expect(eventsCard?.exists()).toBe(true)
    })
  })
})

// 源代码静态分析测试 - 验证组件包含必要字段和条件渲染
describe('DeviceDetail.vue 源代码静态分析', () => {
  const deviceDetailSource = import.meta.glob('../DeviceDetail.vue', { query: '?raw', import: 'default' })

  describe('通用数据卡片', () => {
    it('应该包含信号强度 (csq)', async () => {
      const sourceCode = await deviceDetailSource['../DeviceDetail.vue']() as string

      expect(sourceCode).toContain('csq')
    })

    it('应该包含 SIM 卡号 (sim_card)', async () => {
      const sourceCode = await deviceDetailSource['../DeviceDetail.vue']() as string

      expect(sourceCode).toContain('sim_card')
    })

    it('应该包含固件版本 (firmware_version)', async () => {
      const sourceCode = await deviceDetailSource['../DeviceDetail.vue']() as string

      expect(sourceCode).toContain('firmware_version')
    })

    it('应该包含所属分区 (zone_name)', async () => {
      const sourceCode = await deviceDetailSource['../DeviceDetail.vue']() as string

      expect(sourceCode).toContain('zone_name')
    })

    it('分区为空时应该显示"未分配"', async () => {
      const sourceCode = await deviceDetailSource['../DeviceDetail.vue']() as string

      expect(sourceCode).toContain('未分配')
    })
  })

  describe('告警状态卡片', () => {
    it('应该包含湿度告警 (alarmhumi)', async () => {
      const sourceCode = await deviceDetailSource['../DeviceDetail.vue']() as string

      expect(sourceCode).toContain('alarmhumi')
    })

    it('应该包含空调故障码 (air_err)', async () => {
      const sourceCode = await deviceDetailSource['../DeviceDetail.vue']() as string

      expect(sourceCode).toContain('air_err')
    })

    it('湿度告警应该使用橙色 Tag', async () => {
      const sourceCode = await deviceDetailSource['../DeviceDetail.vue']() as string

      expect(sourceCode).toContain('alarmhumi')
      expect(sourceCode).toContain('color="orange"')
    })

    it('空调故障应该使用红色 Tag', async () => {
      const sourceCode = await deviceDetailSource['../DeviceDetail.vue']() as string

      expect(sourceCode).toContain('air_err')
      expect(sourceCode).toContain('color="red"')
    })
  })

  describe('版本差异化数据条件渲染', () => {
    it('应该包含电流字段 (current)', async () => {
      const sourceCode = await deviceDetailSource['../DeviceDetail.vue']() as string

      expect(sourceCode).toContain('current')
    })

    it('应该包含空调状态字段 (airstate)', async () => {
      const sourceCode = await deviceDetailSource['../DeviceDetail.vue']() as string

      expect(sourceCode).toContain('airstate')
    })

    it('空调状态应该有条件渲染 v-if', async () => {
      const sourceCode = await deviceDetailSource['../DeviceDetail.vue']() as string

      // 检查 airstate 的条件渲染
      expect(sourceCode).toMatch(/v-if.*airstate/)
    })

    it('空调状态开机应该使用绿色 Tag', async () => {
      const sourceCode = await deviceDetailSource['../DeviceDetail.vue']() as string

      // 检查开机状态显示
      expect(sourceCode).toContain('airstate === 1')
      expect(sourceCode).toContain("'green'")
    })
  })

  describe('运行统计条件渲染', () => {
    it('应该包含运行统计卡片', async () => {
      const sourceCode = await deviceDetailSource['../DeviceDetail.vue']() as string

      expect(sourceCode).toContain('运行统计')
    })

    it('应该包含 supports_runtime 字段', async () => {
      const sourceCode = await deviceDetailSource['../DeviceDetail.vue']() as string

      expect(sourceCode).toContain('supports_runtime')
    })

    it('应该包含当天运行时间 (today_runtime)', async () => {
      const sourceCode = await deviceDetailSource['../DeviceDetail.vue']() as string

      expect(sourceCode).toContain('today_runtime')
    })

    it('应该包含当月运行时间 (month_runtime)', async () => {
      const sourceCode = await deviceDetailSource['../DeviceDetail.vue']() as string

      expect(sourceCode).toContain('month_runtime')
    })

    it('运行统计卡片应该有条件渲染', async () => {
      const sourceCode = await deviceDetailSource['../DeviceDetail.vue']() as string

      // 检查 supports_runtime 的条件渲染
      expect(sourceCode).toMatch(/v-if.*supports_runtime/)
    })
  })

  describe('开关机记录条件渲染', () => {
    it('应该包含开关机记录卡片', async () => {
      const sourceCode = await deviceDetailSource['../DeviceDetail.vue']() as string

      expect(sourceCode).toContain('开关机记录')
    })

    it('应该包含 events.supported 条件判断', async () => {
      const sourceCode = await deviceDetailSource['../DeviceDetail.vue']() as string

      expect(sourceCode).toContain('events?.supported')
    })

    it('应该包含"协议版本不支持"提示', async () => {
      const sourceCode = await deviceDetailSource['../DeviceDetail.vue']() as string

      expect(sourceCode).toContain('当前协议版本不支持空调状态监控')
    })

    it('不支持时应该显示 a-empty', async () => {
      const sourceCode = await deviceDetailSource['../DeviceDetail.vue']() as string

      // 检查条件渲染逻辑
      expect(sourceCode).toMatch(/v-else/)
      expect(sourceCode).toContain('a-empty')
    })
  })

  describe('API 调用', () => {
    it('应该导入 deviceApi', async () => {
      const sourceCode = await deviceDetailSource['../DeviceDetail.vue']() as string

      expect(sourceCode).toContain('deviceApi')
    })

    it('应该调用 getEvents API', async () => {
      const sourceCode = await deviceDetailSource['../DeviceDetail.vue']() as string

      expect(sourceCode).toContain('getEvents')
    })

    it('应该有 fetchEvents 函数', async () => {
      const sourceCode = await deviceDetailSource['../DeviceDetail.vue']() as string

      expect(sourceCode).toContain('fetchEvents')
    })
  })
})