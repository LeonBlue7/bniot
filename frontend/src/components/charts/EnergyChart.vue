<script setup lang="ts">
/**
 * 能耗统计柱状图组件
 * 显示设备的能耗统计数据
 */
import { computed, ref, watch, onMounted, onUnmounted } from 'vue'
import * as echarts from 'echarts'
import type { EnergyStats } from '@/types'

// Props
const props = defineProps<{
  data: EnergyStats[]
  loading?: boolean
  autoResize?: boolean
  showExport?: boolean
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
const chartInstance = ref<echarts.ECharts | null>(null)

// 是否为空数据
const isEmpty = computed(() => !props.data || props.data.length === 0)

// 图表配置
const chartOption = computed(() => {
  // 按 total_energy 降序排序，取前 10 个
  const sortedData = [...props.data]
    .sort((a, b) => b.total_energy - a.total_energy)
    .slice(0, 10)

  return {
    title: {
      text: '能耗统计',
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
        const item = params[0]
        const device = props.data.find(d => d.device_name === item.name)
        if (!device) return ''
        return `
          <div style="padding: 8px;">
            <div style="font-weight: bold; margin-bottom: 8px;">${device.device_name}</div>
            <div>设备ID: ${device.device_id}</div>
            <div>总能耗: ${device.total_energy.toFixed(2)} kWh</div>
            <div>平均功率: ${device.avg_power.toFixed(1)} W</div>
            <div>最大功率: ${device.max_power.toFixed(1)} W</div>
            <div>运行时长: ${device.runtime_hours.toFixed(1)} h</div>
          </div>
        `
      }
    },
    legend: {
      data: ['总能耗', '平均功率', '最大功率'],
      bottom: 10
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '15%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: sortedData.map(d => d.device_name),
      axisLabel: {
        rotate: 30,
        interval: 0
      }
    },
    yAxis: [
      {
        type: 'value',
        name: '能耗 (kWh)',
        position: 'left',
        axisLabel: {
          formatter: '{value}'
        }
      },
      {
        type: 'value',
        name: '功率 (W)',
        position: 'right',
        axisLabel: {
          formatter: '{value}'
        }
      }
    ],
    series: [
      {
        name: '总能耗',
        type: 'bar',
        data: sortedData.map(d => d.total_energy),
        itemStyle: {
          color: themeColors[0]
        },
        barWidth: '40%'
      },
      {
        name: '平均功率',
        type: 'line',
        yAxisIndex: 1,
        data: sortedData.map(d => d.avg_power),
        itemStyle: {
          color: themeColors[1]
        },
        symbol: 'circle',
        symbolSize: 8
      },
      {
        name: '最大功率',
        type: 'line',
        yAxisIndex: 1,
        data: sortedData.map(d => d.max_power),
        itemStyle: {
          color: themeColors[3]
        },
        symbol: 'triangle',
        symbolSize: 8
      }
    ],
    toolbox: props.showExport ? {
      feature: {
        saveAsImage: {
          name: '能耗统计',
          pixelRatio: 2
        },
        dataView: {
          readOnly: true
        }
      }
    } : undefined,
    color: themeColors
  }
})


// 更新图表
const updateChart = () => {
  if (chartInstance.value && !isEmpty.value) {
    chartInstance.value.setOption(chartOption.value, true)
  }
}

// 调整图表大小
const resizeChart = () => {
  if (chartInstance.value) {
    chartInstance.value.resize()
  }
}

// 导出图片
const exportImage = () => {
  if (chartInstance.value) {
    const url = chartInstance.value.getDataURL({
      type: 'png',
      pixelRatio: 2,
      backgroundColor: '#fff'
    })
    const link = document.createElement('a')
    link.download = `能耗统计_${new Date().toISOString().slice(0, 10)}.png`
    link.href = url
    link.click()
  }
}

// 初始化图表
const initChart = () => {
  if (chartRef.value) {
    chartInstance.value = echarts.init(chartRef.value)
    chartInstance.value.setOption(chartOption.value)
  }
}

// 监听数据变化
watch(() => props.data, () => {
  updateChart()
}, { deep: true })

// 组件挂载时初始化图表
onMounted(() => {
  initChart()
})

// 组件卸载时销毁图表
onUnmounted(() => {
  if (chartInstance.value) {
    chartInstance.value.dispose()
  }
  if (props.autoResize) {
    window.removeEventListener('resize', resizeChart)
  }
})

// 监听窗口大小变化
if (props.autoResize) {
  window.addEventListener('resize', resizeChart)
}

// 暴露方法给父组件
defineExpose({
  chartInstance,
  chartOption,
  resizeChart,
  exportImage
})
</script>

<template>
  <div class="energy-chart">
    <a-spin :spinning="loading">
      <div
        v-if="isEmpty && !loading"
        class="empty-state"
      >
        <a-empty description="暂无能耗数据" />
      </div>
      <div
        v-else
        ref="chartRef"
        class="chart-container"
      />
    </a-spin>
  </div>
</template>

<style scoped>
.energy-chart {
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