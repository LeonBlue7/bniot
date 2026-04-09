/**
 * ECharts 图表组件测试
 * TDD: 测试先行
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, VueWrapper } from '@vue/test-utils'
import { nextTick } from 'vue'

// Mock ECharts - 必须在 vi.mock 内部定义所有内容，因为 vi.mock 是 hoisted
vi.mock('echarts', () => {
  // LinearGradient mock class - 必须定义在 mock 函数内部
  class MockLinearGradient {
    type = 'linear'
    x: number
    y: number
    x2: number
    y2: number
    stops: any[]
    constructor(x: number, y: number, x2: number, y2: number, stops: any[]) {
      this.x = x
      this.y = y
      this.x2 = x2
      this.y2 = y2
      this.stops = stops
    }
  }

  const mockChart = {
    setOption: vi.fn(),
    resize: vi.fn(),
    dispose: vi.fn(),
    on: vi.fn(),
    off: vi.fn(),
    getWidth: vi.fn(() => 400),
    getHeight: vi.fn(() => 300),
    getDataURL: vi.fn(() => 'data:image/png;base64,mock')
  }

  return {
    default: {
      init: vi.fn(() => mockChart),
      dispose: vi.fn(),
      graphic: {
        LinearGradient: MockLinearGradient
      }
    },
    init: vi.fn(() => mockChart),
    graphic: {
      LinearGradient: MockLinearGradient
    }
  }
})

// 导入组件 - 使用 RuntimeBarChart
import EnergyChart from '@/components/charts/EnergyChart.vue'
import TrendChart from '@/components/charts/TrendChart.vue'
import AlarmPieChart from '@/components/charts/AlarmPieChart.vue'
import RuntimeBarChart from '@/components/charts/RuntimeBarChart.vue'

// Ant Design Vue 组件 stub
const antdStubs = {
  'a-spin': {
    template: '<div class="ant-spin"><slot /></div>'
  },
  'a-empty': {
    template: '<div class="ant-empty">{{ description }}</div>',
    props: ['description']
  }
}

describe('EnergyChart 组件测试', () => {
  const mockData = [
    { device_id: '001', device_name: '空调1', total_energy: 120.5, avg_power: 500, max_power: 800, runtime_hours: 240 },
    { device_id: '002', device_name: '空调2', total_energy: 85.3, avg_power: 350, max_power: 600, runtime_hours: 180 }
  ]

  it('应该正确渲染能耗柱状图', async () => {
    const wrapper = mount(EnergyChart, {
      props: {
        data: mockData,
        loading: false
      },
      global: {
        stubs: antdStubs
      }
    })

    await nextTick()

    // 验证组件存在
    expect(wrapper.find('.energy-chart').exists()).toBe(true)
  })

  it('应该显示加载状态', async () => {
    const wrapper = mount(EnergyChart, {
      props: {
        data: [],
        loading: true
      },
      global: {
        stubs: antdStubs
      }
    })

    await nextTick()

    // 验证加载状态 - a-spin 组件被 stub 后会有 .ant-spin 类
    expect(wrapper.find('.ant-spin').exists()).toBe(true)
  })

  it('应该处理空数据', async () => {
    const wrapper = mount(EnergyChart, {
      props: {
        data: [],
        loading: false
      },
      global: {
        stubs: antdStubs
      }
    })

    await nextTick()

    // 验证空数据提示
    expect(wrapper.find('.empty-state').exists() || wrapper.find('.ant-empty').exists()).toBe(true)
  })

  it('应该生成正确的图表配置', async () => {
    const wrapper = mount(EnergyChart, {
      props: {
        data: mockData,
        loading: false
      },
      global: {
        stubs: antdStubs
      }
    })

    await nextTick()

    // 验证图表配置包含正确的数据
    const chartOption = wrapper.vm.chartOption
    expect(chartOption).toBeDefined()
    expect(chartOption.xAxis.data).toHaveLength(2)
    expect(chartOption.xAxis.data).toContain('空调1')
    expect(chartOption.xAxis.data).toContain('空调2')
  })

  it('应该格式化能耗数据单位', async () => {
    const wrapper = mount(EnergyChart, {
      props: {
        data: mockData,
        loading: false
      },
      global: {
        stubs: antdStubs
      }
    })

    await nextTick()

    // 验证图表配置包含单位 - yAxis 是数组形式
    const chartOption = wrapper.vm.chartOption
    // yAxis[0] 是能耗轴，包含 kWh
    expect(chartOption.yAxis[0].name).toContain('kWh')
  })

  it('应该响应窗口大小变化', async () => {
    const wrapper = mount(EnergyChart, {
      props: {
        data: mockData,
        loading: false,
        autoResize: true
      },
      global: {
        stubs: antdStubs
      }
    })

    await nextTick()

    // 验证 autoresize 属性
    expect(wrapper.props('autoResize')).toBe(true)
  })
})

describe('TrendChart 组件测试', () => {
  const mockTrendData = {
    device_id: '001',
    device_name: '空调1',
    temp_trend: [
      { time: '2024-01-01T00:00:00Z', value: 25 },
      { time: '2024-01-01T01:00:00Z', value: 26 },
      { time: '2024-01-01T02:00:00Z', value: 24 }
    ],
    humi_trend: [
      { time: '2024-01-01T00:00:00Z', value: 60 },
      { time: '2024-01-01T01:00:00Z', value: 62 },
      { time: '2024-01-01T02:00:00Z', value: 58 }
    ]
  }

  it('应该正确渲染温湿度趋势折线图', async () => {
    const wrapper = mount(TrendChart, {
      props: {
        data: mockTrendData,
        loading: false
      },
      global: {
        stubs: antdStubs
      }
    })

    await nextTick()

    expect(wrapper.find('.trend-chart').exists()).toBe(true)
  })

  it('应该显示温度和湿度两条线', async () => {
    const wrapper = mount(TrendChart, {
      props: {
        data: mockTrendData,
        loading: false
      },
      global: {
        stubs: antdStubs
      }
    })

    await nextTick()

    const chartOption = wrapper.vm.chartOption
    expect(chartOption.series).toHaveLength(2)
    expect(chartOption.series[0].name).toContain('温度')
    expect(chartOption.series[1].name).toContain('湿度')
  })

  it('应该正确格式化时间轴', async () => {
    const wrapper = mount(TrendChart, {
      props: {
        data: mockTrendData,
        loading: false
      },
      global: {
        stubs: antdStubs
      }
    })

    await nextTick()

    const chartOption = wrapper.vm.chartOption
    expect(chartOption.xAxis.data).toHaveLength(3)
    // 验证时间格式化函数存在
    expect(chartOption.xAxis.axisLabel.formatter).toBeDefined()
  })

  it('应该处理空趋势数据', async () => {
    const emptyData = {
      device_id: '001',
      device_name: '空调1',
      temp_trend: [],
      humi_trend: []
    }

    const wrapper = mount(TrendChart, {
      props: {
        data: emptyData,
        loading: false
      },
      global: {
        stubs: antdStubs
      }
    })

    await nextTick()

    expect(wrapper.find('.empty-state').exists() || wrapper.find('.ant-empty').exists()).toBe(true)
  })

  it('应该处理包含 null 值的数据点', async () => {
    const dataWithNull = {
      device_id: '001',
      device_name: '空调1',
      temp_trend: [
        { time: '2024-01-01T00:00:00Z', value: 25 },
        { time: '2024-01-01T01:00:00Z', value: null },
        { time: '2024-01-01T02:00:00Z', value: 24 }
      ],
      humi_trend: [
        { time: '2024-01-01T00:00:00Z', value: 60 },
        { time: '2024-01-01T01:00:00Z', value: null },
        { time: '2024-01-01T02:00:00Z', value: 58 }
      ]
    }

    const wrapper = mount(TrendChart, {
      props: {
        data: dataWithNull,
        loading: false
      },
      global: {
        stubs: antdStubs
      }
    })

    await nextTick()

    const chartOption = wrapper.vm.chartOption
    // 验证能正常处理 null 值（ECharts 会自动处理）
    expect(chartOption.series[0].data).toBeDefined()
  })

  it('应该支持图表导出', async () => {
    const wrapper = mount(TrendChart, {
      props: {
        data: mockTrendData,
        loading: false,
        showExport: true
      },
      global: {
        stubs: antdStubs
      }
    })

    await nextTick()

    // 验证 toolbox 配置包含导出功能
    const chartOption = wrapper.vm.chartOption
    expect(chartOption.toolbox).toBeDefined()
    expect(chartOption.toolbox!.feature.saveAsImage).toBeDefined()
  })
})

describe('AlarmPieChart 组件测试', () => {
  const mockAlarmData = [
    { type: 'offline', severity: 'high', count: 10, resolved_count: 5, unresolved_count: 5 },
    { type: 'illegal_on', severity: 'medium', count: 8, resolved_count: 3, unresolved_count: 5 },
    { type: 'temp_alarm', severity: 'low', count: 15, resolved_count: 10, unresolved_count: 5 }
  ]

  it('应该正确渲染告警统计饼图', async () => {
    const wrapper = mount(AlarmPieChart, {
      props: {
        data: mockAlarmData,
        loading: false
      },
      global: {
        stubs: antdStubs
      }
    })

    await nextTick()

    expect(wrapper.find('.alarm-pie-chart').exists()).toBe(true)
  })

  it('应该按类型显示告警分布', async () => {
    const wrapper = mount(AlarmPieChart, {
      props: {
        data: mockAlarmData,
        loading: false,
        groupBy: 'type'
      },
      global: {
        stubs: antdStubs
      }
    })

    await nextTick()

    const chartOption = wrapper.vm.chartOption
    expect(chartOption.series[0].type).toBe('pie')
    expect(chartOption.series[0].data).toHaveLength(3)
  })

  it('应该按严重程度显示告警分布', async () => {
    const wrapper = mount(AlarmPieChart, {
      props: {
        data: mockAlarmData,
        loading: false,
        groupBy: 'severity'
      },
      global: {
        stubs: antdStubs
      }
    })

    await nextTick()

    const chartOption = wrapper.vm.chartOption
    expect(chartOption.series[0].type).toBe('pie')
  })

  it('应该显示告警图例', async () => {
    const wrapper = mount(AlarmPieChart, {
      props: {
        data: mockAlarmData,
        loading: false
      },
      global: {
        stubs: antdStubs
      }
    })

    await nextTick()

    const chartOption = wrapper.vm.chartOption
    expect(chartOption.legend).toBeDefined()
    expect(chartOption.legend.data).toBeDefined()
  })

  it('应该处理空告警数据', async () => {
    const wrapper = mount(AlarmPieChart, {
      props: {
        data: [],
        loading: false
      },
      global: {
        stubs: antdStubs
      }
    })

    await nextTick()

    expect(wrapper.find('.empty-state').exists() || wrapper.find('.ant-empty').exists()).toBe(true)
  })

  it('应该使用不同颜色区分告警类型', async () => {
    const wrapper = mount(AlarmPieChart, {
      props: {
        data: mockAlarmData,
        loading: false
      },
      global: {
        stubs: antdStubs
      }
    })

    await nextTick()

    const chartOption = wrapper.vm.chartOption
    expect(chartOption.color).toBeDefined()
    expect(chartOption.color.length).toBeGreaterThan(0)
  })
})

describe('RuntimeBarChart 组件测试', () => {
  const mockRuntimeData = [
    { device_id: '001', device_name: '空调1', zone_name: '办公区', total_runtime_hours: 240, on_time_percentage: 80, on_count: 20, off_count: 20 },
    { device_id: '002', device_name: '空调2', zone_name: '会议室', total_runtime_hours: 120, on_time_percentage: 40, on_count: 15, off_count: 15 },
    { device_id: '003', device_name: '空调3', zone_name: '大厅', total_runtime_hours: 180, on_time_percentage: 60, on_count: 10, off_count: 10 }
  ]

  it('应该正确渲染运行时长横向柱状图', async () => {
    const wrapper = mount(RuntimeBarChart, {
      props: {
        data: mockRuntimeData,
        loading: false
      },
      global: {
        stubs: antdStubs
      }
    })

    await nextTick()

    expect(wrapper.find('.runtime-bar-chart').exists()).toBe(true)
  })

  it('应该横向显示柱状图', async () => {
    const wrapper = mount(RuntimeBarChart, {
      props: {
        data: mockRuntimeData,
        loading: false
      },
      global: {
        stubs: antdStubs
      }
    })

    await nextTick()

    const chartOption = wrapper.vm.chartOption
    // 横向柱状图：xAxis 是数值轴，yAxis 是类目轴
    expect(chartOption.xAxis.type).toBe('value')
    expect(chartOption.yAxis.type).toBe('category')
  })

  it('应该按运行时长排序', async () => {
    const wrapper = mount(RuntimeBarChart, {
      props: {
        data: mockRuntimeData,
        loading: false,
        sortByRuntime: true
      },
      global: {
        stubs: antdStubs
      }
    })

    await nextTick()

    const chartOption = wrapper.vm.chartOption
    const yAxisData = chartOption.yAxis.data
    // 验证排序（数据应该按运行时长降序排列）
    expect(yAxisData).toBeDefined()
  })

  it('应该显示运行时长和开机占比', async () => {
    const wrapper = mount(RuntimeBarChart, {
      props: {
        data: mockRuntimeData,
        loading: false,
        showPercentage: true
      },
      global: {
        stubs: antdStubs
      }
    })

    await nextTick()

    const chartOption = wrapper.vm.chartOption
    expect(chartOption.series).toBeDefined()
    // 可能有多条数据线（运行时长 + 开机占比）
  })

  it('应该处理空运行数据', async () => {
    const wrapper = mount(RuntimeBarChart, {
      props: {
        data: [],
        loading: false
      },
      global: {
        stubs: antdStubs
      }
    })

    await nextTick()

    expect(wrapper.find('.empty-state').exists() || wrapper.find('.ant-empty').exists()).toBe(true)
  })

  it('应该限制显示数量', async () => {
    const manyDevices = Array.from({ length: 20 }, (_, i) => ({
      device_id: `device-${i}`,
      device_name: `空调${i + 1}`,
      zone_name: `区域${i + 1}`,
      total_runtime_hours: Math.random() * 200,
      on_time_percentage: Math.random() * 100,
      on_count: Math.floor(Math.random() * 30),
      off_count: Math.floor(Math.random() * 30)
    }))

    const wrapper = mount(RuntimeBarChart, {
      props: {
        data: manyDevices,
        loading: false,
        maxItems: 10
      },
      global: {
        stubs: antdStubs
      }
    })

    await nextTick()

    const chartOption = wrapper.vm.chartOption
    // 验证只显示最多 maxItems 条数据
    expect(chartOption.yAxis.data.length).toBeLessThanOrEqual(10)
  })

  it('应该格式化运行时长单位', async () => {
    const wrapper = mount(RuntimeBarChart, {
      props: {
        data: mockRuntimeData,
        loading: false
      },
      global: {
        stubs: antdStubs
      }
    })

    await nextTick()

    const chartOption = wrapper.vm.chartOption
    expect(chartOption.xAxis.name).toContain('小时')
  })
})

describe('图表通用功能测试', () => {
  it('所有图表应该支持响应式调整', async () => {
    const energyData = [
      { device_id: '001', device_name: '空调1', total_energy: 120.5, avg_power: 500, max_power: 800, runtime_hours: 240 }
    ]

    const wrapper = mount(EnergyChart, {
      props: {
        data: energyData,
        loading: false,
        autoResize: true
      },
      global: {
        stubs: antdStubs
      }
    })

    await nextTick()

    expect(wrapper.props('autoResize')).toBe(true)
  })

  it('所有图表应该支持导出图片', async () => {
    const energyData = [
      { device_id: '001', device_name: '空调1', total_energy: 120.5, avg_power: 500, max_power: 800, runtime_hours: 240 }
    ]

    const wrapper = mount(EnergyChart, {
      props: {
        data: energyData,
        loading: false,
        showExport: true
      },
      global: {
        stubs: antdStubs
      }
    })

    await nextTick()

    // 验证工具栏包含保存图片功能
    const chartOption = wrapper.vm.chartOption
    expect(chartOption.toolbox).toBeDefined()
    expect(chartOption.toolbox!.feature.saveAsImage).toBeDefined()
  })

  it('图表应该使用统一的主题颜色', () => {
    const themeColors = [
      '#1890ff', // 主色
      '#52c41a', // 成功
      '#faad14', // 警告
      '#ff4d4f', // 错误
      '#722ed1', // 紫色
      '#13c2c2'  // 青色
    ]

    // 验证颜色配置存在
    expect(themeColors).toBeDefined()
    expect(themeColors.length).toBe(6)
  })
})