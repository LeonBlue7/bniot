<script setup lang="ts">
/**
 * 设备运行时长横向柱状图组件
 * 显示设备运行时长统计，支持排序和限制显示数量
 */
import { computed, ref, watch, onMounted, onUnmounted } from 'vue'
import * as echarts from 'echarts'
import type { RuntimeStats } from '@/types'

// Props
const props = defineProps<{
  data: RuntimeStats[]
  loading?: boolean
  autoResize?: boolean
  showExport?: boolean
  sortByRuntime?: boolean
  showPercentage?: boolean
  maxItems?: number
}>()

// 主题颜色配置
const themeColors = [
  '#1890ff', // 主色
  '#52c41a', // 成功
  '#faad14', // 警告
  '#ff4d4f', // 错误
  '#722ed1', // 紫色
  '#13c2c2'  // 青色
]

// 图表实例引用
const chartRef = ref<HTMLElement | null>(null)
let chartInstance: echarts.ECharts | null = null

// 是否为空数据
const isEmpty = computed(() => !props.data || props.data.length === 0)

// 处理数据：排序和限制数量
const processedData = computed(() => {
  let result = [...props.data]

  // 按运行时长排序
  if (props.sortByRuntime) {
    result.sort((a, b) => b.total_runtime_hours - a.total_runtime_hours)
  }

  // 限制显示数量
  if (props.maxItems && result.length > props.maxItems) {
    result = result.slice(0, props.maxItems)
  }

  // 横向柱状图数据需要倒序排列（最长的在上面）
  return result.reverse()
})

// 图表配置
const chartOption = computed(() => {
  const deviceNames = processedData.value.map(d => d.device_name)
  const runtimeValues = processedData.value.map(d => d.total_runtime_hours)

  const series: any[] = [
    {
      name: '运行时长',
      type: 'bar',
      data: runtimeValues.map((value, index) => ({
        value,
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
            { offset: 0, color: themeColors[index % themeColors.length] },
            { offset: 1, color: themeColors[(index + 1) % themeColors.length] + '80' }
          ])
        }
      })),
      label: {
        show: true,
        position: 'right',
        formatter: (params: any) => `${params.value.toFixed(1)}h`
      },
      barWidth: '60%'
    }
  ]

  // 如果显示开机占比，添加第二条系列
  if (props.showPercentage) {
    series.push({
      name: '开机占比',
      type: 'bar',
      data: processedData.value.map(d => d.on_time_percentage),
      label: {
        show: true,
        position: 'right',
        formatter: (params: any) => `${params.value.toFixed(1)}%`
      },
      barWidth: '40%',
      itemStyle: {
        color: '#52c41a'
      }
    })
  }

  return {
    title: {
      text: '设备运行时长统计',
      left: 'center',
      textStyle: {
        fontSize: 14,
        fontWeight: 'normal'
      }
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      },
      formatter: (params: any) => {
        const device = processedData.value.find(d => d.device_name === params[0].name)
        if (!device) return ''
        return `
          <div style="padding: 8px;">
            <div style="font-weight: bold; margin-bottom: 8px;">${device.device_name}</div>
            <div>设备ID: ${device.device_id}</div>
            <div>分区: ${device.zone_name || '未分配'}</div>
            <div>运行时长: ${device.total_runtime_hours.toFixed(1)} 小时</div>
            <div>开机占比: ${device.on_time_percentage.toFixed(1)}%</div>
            <div>开机次数: ${device.on_count}</div>
            <div>关机次数: ${device.off_count}</div>
          </div>
        `
      }
    },
    legend: props.showPercentage ? {
      data: ['运行时长', '开机占比'],
      bottom: 10
    } : undefined,
    grid: {
      left: '3%',
      right: '15%',
      bottom: props.showPercentage ? '15%' : '3%',
      top: '15%',
      containLabel: true
    },
    xAxis: {
      type: 'value',
      name: '运行时长 (小时)',
      axisLabel: {
        formatter: '{value}'
      }
    },
    yAxis: {
      type: 'category',
      data: deviceNames,
      axisLabel: {
        width: 100,
        overflow: 'truncate',
        ellipsis: '...'
      }
    },
    series,
    toolbox: props.showExport ? {
      feature: {
        saveAsImage: {
          name: '设备运行时长统计',
          pixelRatio: 2
        }
      }
    } : undefined
  }
})

// 初始化图表
const initChart = () => {
  if (!chartRef.value || isEmpty.value) return

  if (chartInstance) {
    chartInstance.dispose()
  }

  chartInstance = echarts.init(chartRef.value)
  chartInstance.setOption(chartOption.value)
}

// 更新图表
const updateChart = () => {
  if (chartInstance && !isEmpty.value) {
    chartInstance.setOption(chartOption.value, true)
  }
}

// 调整图表大小
const resizeChart = () => {
  if (chartInstance) {
    chartInstance.resize()
  }
}

// 导出图片
const exportImage = () => {
  if (chartInstance) {
    const url = chartInstance.getDataURL({
      type: 'png',
      pixelRatio: 2,
      backgroundColor: '#fff'
    })
    const link = document.createElement('a')
    link.download = `设备运行时长统计_${new Date().toISOString().slice(0, 10)}.png`
    link.href = url
    link.click()
  }
}

// 监听数据变化
watch(() => props.data, () => {
  updateChart()
}, { deep: true })

// 组件挂载
onMounted(() => {
  initChart()
  if (props.autoResize) {
    window.addEventListener('resize', resizeChart)
  }
})

// 组件卸载
onUnmounted(() => {
  if (chartInstance) {
    chartInstance.dispose()
  }
  if (props.autoResize) {
    window.removeEventListener('resize', resizeChart)
  }
})

// 暴露方法给父组件
defineExpose({
  chartInstance,
  chartOption,
  resizeChart,
  exportImage
})
</script>

<template>
  <div class="runtime-bar-chart">
    <a-spin :spinning="loading">
      <div v-if="isEmpty && !loading" class="empty-state">
        <a-empty description="暂无运行时长数据" />
      </div>
      <div v-else ref="chartRef" class="chart-container"></div>
    </a-spin>
  </div>
</template>

<style scoped>
.runtime-bar-chart {
  width: 100%;
  min-height: 300px;
}

.chart-container {
  width: 100%;
  height: 400px;
}

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 300px;
}
</style>