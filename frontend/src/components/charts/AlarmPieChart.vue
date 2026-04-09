<script setup lang="ts">
/**
 * 告警统计饼图组件
 * 显示告警按类型或严重程度的分布
 */
import { computed, ref, watch, onMounted, onUnmounted } from 'vue'
import * as echarts from 'echarts'
import type { AlarmStats } from '@/types'

// Props
const props = defineProps<{
  data: AlarmStats[]
  loading?: boolean
  autoResize?: boolean
  showExport?: boolean
  groupBy?: 'type' | 'severity' | 'device'
}>()

// 主题颜色配置
const severityColors = {
  high: '#ff4d4f',    // 红色 - 高
  medium: '#faad14',  // 橙色 - 中
  low: '#52c41a'      // 绿色 - 低
}

const typeColors = {
  offline: '#ff4d4f',      // 红色 - 离线
  illegal_on: '#faad14',   // 橙色 - 非法开启
  temp_alarm: '#1890ff'    // 蓝色 - 温度告警
}

const themeColors = ['#ff4d4f', '#faad14', '#52c41a', '#1890ff', '#722ed1', '#13c2c2']

// 告警类型名称映射
const typeNameMap: Record<string, string> = {
  offline: '设备离线',
  illegal_on: '非法开启',
  temp_alarm: '温度告警',
  humi_alarm: '湿度告警'
}

// 告警严重程度名称映射
const severityNameMap: Record<string, string> = {
  high: '高',
  medium: '中',
  low: '低'
}

// 图表实例引用
const chartRef = ref<HTMLElement | null>(null)
let chartInstance: echarts.ECharts | null = null

// 是否为空数据
const isEmpty = computed(() => !props.data || props.data.length === 0)

// 处理数据按分组方式
const processedData = computed(() => {
  const groupBy = props.groupBy || 'type'

  // 定义返回类型
  interface ProcessedItem {
    name: string
    value: number
    itemStyle?: { color: string }
    resolved: number
    unresolved: number
  }

  if (groupBy === 'type') {
    return props.data.map((item): ProcessedItem => ({
      name: typeNameMap[item.type || ''] || item.type || '未知',
      value: item.count,
      itemStyle: {
        color: (item.type && typeColors[item.type as keyof typeof typeColors]) || '#999'
      },
      resolved: item.resolved_count,
      unresolved: item.unresolved_count
    }))
  } else if (groupBy === 'severity') {
    // 按严重程度分组需要聚合数据
    const severityMap = new Map<string, { count: number; resolved: number; unresolved: number }>()
    props.data.forEach(item => {
      const severity = item.severity || 'unknown'
      const existing = severityMap.get(severity) || { count: 0, resolved: 0, unresolved: 0 }
      existing.count += item.count
      existing.resolved += item.resolved_count
      existing.unresolved += item.unresolved_count
      severityMap.set(severity, existing)
    })

    return Array.from(severityMap.entries()).map(([severity, stats]): ProcessedItem => ({
      name: severityNameMap[severity] || severity,
      value: stats.count,
      itemStyle: {
        color: severityColors[severity as keyof typeof severityColors] || '#999'
      },
      resolved: stats.resolved,
      unresolved: stats.unresolved
    }))
  }

  return props.data.map((item): ProcessedItem => ({
    name: item.type || item.severity || '未知',
    value: item.count,
    resolved: item.resolved_count,
    unresolved: item.unresolved_count
  }))
})

// 图表颜色
const chartColors = computed(() => {
  return processedData.value.map(d => d.itemStyle?.color || '#999')
})

// 图表配置
const chartOption = computed(() => {
  return {
    title: {
      text: '告警统计分布',
      left: 'center',
      textStyle: {
        fontSize: 14,
        fontWeight: 'normal'
      }
    },
    tooltip: {
      trigger: 'item',
      formatter: (params: any) => {
        const item = processedData.value.find(d => d.name === params.name)
        if (!item) return ''
        return `
          <div style="padding: 8px;">
            <div style="font-weight: bold; margin-bottom: 8px;">${params.name}</div>
            <div>总告警数: ${params.value} (${params.percent}%)</div>
            <div>已解决: ${item.resolved}</div>
            <div>未解决: ${item.unresolved}</div>
          </div>
        `
      }
    },
    legend: {
      orient: 'horizontal',
      bottom: 10,
      data: processedData.value.map(d => d.name)
    },
    series: [
      {
        type: 'pie',
        radius: ['40%', '70%'],
        center: ['50%', '45%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 10,
          borderColor: '#fff',
          borderWidth: 2
        },
        label: {
          show: true,
          formatter: '{b}: {d}%'
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 14,
            fontWeight: 'bold'
          },
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)'
          }
        },
        labelLine: {
          show: true
        },
        data: processedData.value.map(d => ({
          name: d.name,
          value: d.value,
          itemStyle: d.itemStyle
        }))
      }
    ],
    toolbox: props.showExport ? {
      feature: {
        saveAsImage: {
          name: '告警统计',
          pixelRatio: 2
        }
      }
    } : undefined,
    color: chartColors.value
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
    link.download = `告警统计_${new Date().toISOString().slice(0, 10)}.png`
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
  <div class="alarm-pie-chart">
    <a-spin :spinning="loading">
      <div v-if="isEmpty && !loading" class="empty-state">
        <a-empty description="暂无告警数据" />
      </div>
      <div v-else ref="chartRef" class="chart-container"></div>
    </a-spin>
  </div>
</template>

<style scoped>
.alarm-pie-chart {
  width: 100%;
  min-height: 300px;
}

.chart-container {
  width: 100%;
  height: 350px;
}

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 300px;
}
</style>