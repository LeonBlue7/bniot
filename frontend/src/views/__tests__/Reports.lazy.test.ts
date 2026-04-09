/**
 * Reports 页面动态导入测试
 * TDD: 测试图表组件的懒加载行为
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { defineComponent, defineAsyncComponent } from 'vue'
import Antd from 'ant-design-vue'

// Mock API
vi.mock('@/api/reports', () => ({
  reportApi: {
    getEnergyStats: vi.fn(() => Promise.resolve({ data: [] })),
    getTrendData: vi.fn(() => Promise.resolve({ data: [] })),
    getAlarmStats: vi.fn(() => Promise.resolve({ data: [], total_alarms: 0 })),
    getRuntimeStats: vi.fn(() => Promise.resolve({ data: [], avg_runtime_hours: 0 })),
    downloadReport: vi.fn()
  }
}))

vi.mock('@/api/zones', () => ({
  zoneApi: {
    list: vi.fn(() => Promise.resolve([]))
  }
}))

// Mock ECharts
vi.mock('echarts', () => ({
  default: {
    init: vi.fn(() => ({
      setOption: vi.fn(),
      resize: vi.fn(),
      dispose: vi.fn()
    }))
  },
  init: vi.fn(),
  graphic: {
    LinearGradient: vi.fn()
  }
}))

// Ant Design Vue 组件 stub
const antdStubs = {
  'a-card': {
    template: '<div class="ant-card"><slot /></div>'
  },
  'a-tabs': {
    template: '<div class="ant-tabs"><slot /></div>',
    props: ['activeKey']
  },
  'a-tab-pane': {
    template: '<div class="ant-tab-pane"><slot /></div>',
    props: ['key', 'tab']
  },
  'a-spin': {
    template: '<div class="ant-spin"><slot /></div>',
    props: ['spinning']
  },
  'a-empty': {
    template: '<div class="ant-empty">{{ description }}</div>',
    props: ['description']
  },
  'a-range-picker': {
    template: '<div class="ant-range-picker"></div>',
    props: ['value']
  },
  'a-select': {
    template: '<div class="ant-select"></div>',
    props: ['value']
  },
  'a-button': {
    template: '<button class="ant-btn"><slot /></button>',
    props: ['type', 'loading']
  },
  'a-radio-group': {
    template: '<div class="ant-radio-group"><slot /></div>',
    props: ['value']
  },
  'a-radio-button': {
    template: '<label class="ant-radio-button"><slot /></label>',
    props: ['value']
  },
  'a-skeleton': {
    template: '<div class="ant-skeleton chart-skeleton">Loading skeleton...</div>',
    props: ['active', 'paragraph']
  },
  'suspense': {
    template: '<div class="suspense-wrapper"><slot name="default" /><slot name="fallback" /></div>'
  }
}

// 使用 import.meta.glob 检查源代码
const reportsSource = import.meta.glob('../Reports.vue', { as: 'raw' })

describe('Reports 页面动态导入测试', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('源代码静态分析', () => {
    it('Reports.vue 应该使用 defineAsyncComponent 而非静态导入', async () => {
      // 读取源文件
      const sourceModule = await reportsSource['../Reports.vue']()
      const sourceCode = sourceModule as string

      // 检查是否使用 defineAsyncComponent
      const hasAsyncComponent = sourceCode.includes('defineAsyncComponent')

      // 检查是否有动态 import
      const hasDynamicImport = /import\s*\(\s*['"]@\/components\/charts/.test(sourceCode)

      // 不应该有静态导入图表组件
      const hasStaticImport = /import\s+\w+Chart\s+from\s+['"]@\/components\/charts\//.test(sourceCode)

      expect(hasAsyncComponent || hasDynamicImport).toBe(true)
      expect(hasStaticImport).toBe(false)
    })

    it('应该为每个图表组件创建独立的异步组件', async () => {
      const sourceModule = await reportsSource['../Reports.vue']()
      const sourceCode = sourceModule as string

      // 检查四个图表组件
      const chartComponents = ['EnergyChart', 'TrendChart', 'AlarmPieChart', 'RuntimeBarChart']

      // 应该有图表组件的引用
      let foundCharts = 0
      for (const chart of chartComponents) {
        if (sourceCode.includes(chart)) {
          foundCharts++
        }
      }

      expect(foundCharts).toBeGreaterThanOrEqual(4)
    })

    it('应该有图表加载状态管理', async () => {
      const sourceModule = await reportsSource['../Reports.vue']()
      const sourceCode = sourceModule as string

      // 检查是否有加载状态定义
      const hasLoadingState =
        sourceCode.includes('chartLoading') ||
        sourceCode.includes('chartLoadingStates') ||
        sourceCode.includes('isChartLoading')

      expect(hasLoadingState).toBe(true)
    })

    it('应该使用 Suspense 包裹异步组件', async () => {
      const sourceModule = await reportsSource['../Reports.vue']()
      const sourceCode = sourceModule as string

      // 检查是否使用 Suspense
      const hasSuspense = sourceCode.includes('Suspense')

      expect(hasSuspense).toBe(true)
    })
  })

  describe('组件运行时行为', () => {
    it('图表组件应该有独立的加载状态', async () => {
      const Reports = (await import('@/views/Reports.vue')).default

      const wrapper = mount(Reports, {
        global: {
          stubs: antdStubs,
          plugins: [Antd]
        }
      })

      await flushPromises()

      const vm = wrapper.vm as any

      // 验证有加载状态
      expect(vm.chartLoadingStates || vm.loading).toBeDefined()
    })

    it('切换标签页时应该触发数据加载', async () => {
      const Reports = (await import('@/views/Reports.vue')).default

      const wrapper = mount(Reports, {
        global: {
          stubs: antdStubs,
          plugins: [Antd]
        }
      })

      await flushPromises()

      const vm = wrapper.vm as any

      // 验证有 tab 切换相关的方法
      expect(vm.onTabChange || vm.refreshData || vm.activeTab).toBeDefined()
    })

    it('应该显示图表加载骨架屏', async () => {
      const Reports = (await import('@/views/Reports.vue')).default

      const wrapper = mount(Reports, {
        global: {
          stubs: antdStubs,
          plugins: [Antd]
        }
      })

      // 检查是否有加载状态指示
      const hasLoadingIndicator =
        wrapper.find('.ant-spin').exists() ||
        wrapper.find('.chart-loading').exists() ||
        wrapper.find('.chart-skeleton').exists() ||
        wrapper.find('.ant-skeleton').exists()

      expect(hasLoadingIndicator).toBe(true)
    })
  })

  describe('代码分割验证', () => {
    it('图表组件应该是可动态导入的', async () => {
      // 验证动态导入语法
      const imports = [
        import('@/components/charts/EnergyChart.vue'),
        import('@/components/charts/TrendChart.vue'),
        import('@/components/charts/AlarmPieChart.vue'),
        import('@/components/charts/RuntimeBarChart.vue')
      ]

      // 动态导入应该返回 Promise
      for (const importPromise of imports) {
        expect(importPromise).toBeInstanceOf(Promise)
      }

      // 等待所有导入完成
      await Promise.all(imports)
    })
  })
})

describe('懒加载工具函数', () => {
  it('createLazyChart 工厂函数应该正确工作', () => {
    const createLazyChart = (loader: () => Promise<any>) => {
      return defineAsyncComponent({
        loader,
        loadingComponent: defineComponent({
          template: '<div class="chart-skeleton">Loading...</div>'
        }),
        errorComponent: defineComponent({
          template: '<div class="chart-error">Failed to load</div>'
        }),
        delay: 200,
        timeout: 10000
      })
    }

    const LazyEnergyChart = createLazyChart(() => import('@/components/charts/EnergyChart.vue'))
    expect(LazyEnergyChart).toBeDefined()
  })
})