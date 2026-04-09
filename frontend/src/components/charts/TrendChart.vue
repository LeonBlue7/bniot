<script setup lang="ts">
/**
 * 温湿度趋势折线图组件
 * 显示设备的温度和湿度变化趋势
 */
import { computed, ref, watch, onMounted, onUnmounted } from 'vue'
import * as echarts from 'echarts'
import dayjs from 'dayjs'
import type { TrendData } from '@/types'

// Props
const props = defineProps<{
  data: TrendData
  loading?: boolean
  autoResize?: boolean
  showExport?: boolean
}>()

// 主题颜色配置
const themeColors = {
  temp: '#ff4d4f',  // 红色 - 温度
  humi: '#1890ff'   // 蓝色 - 湿度
}

// 图表实例引用
const chartRef = ref<HTMLElement | null>(null)
let chartInstance: echarts.ECharts | null = null

// 是否为空数据
const isEmpty = computed(() => {
  return !props.data ||
    (!props.data.temp_trend || props.data.temp_trend.length === 0) &&
    (!props.data.humi_trend || props.data.humi_trend.length === 0)
})

// 格式化时间
const formatTime = (time: string) => {
  return dayjs(time).format('MM-DD HH:mm')
}

// 图表配置
const chartOption = computed(() => {
  const tempData = props.data?.temp_trend || []
  const humiData = props.data?.humi_trend || []

  // 时间轴数据
  const xAxisData = tempData.map(d => d.time)

  // 温度数据
  const tempValues = tempData.map(d => d.value)

  // 湿度数据
  const humiValues = humiData.map(d => d.value)

  return {
    title: {
      text: `${props.data?.device_name || '设备'} - 温湿度趋势`,
      left: 'center',
      textStyle: {
        fontSize: 14,
        fontWeight: 'normal'
      }
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      },
      formatter: (params: any) => {
        if (!params || params.length === 0) return ''
        const time = params[0].axisValue
        let html = `<div style="padding: 8px;">
          <div style="font-weight: bold; margin-bottom: 8px;">${formatTime(time)}</div>`
        params.forEach((item: any) => {
          if (item.value !== null && item.value !== undefined) {
            const unit = item.seriesName === '温度' ? '°C' : '%'
            html += `<div style="display: flex; justify-content: space-between;">
              <span>${item.marker} ${item.seriesName}:</span>
              <span style="font-weight: bold; margin-left: 16px;">${item.value}${unit}</span>
            </div>`
          }
        })
        html += '</div>'
        return html
      }
    },
    legend: {
      data: ['温度', '湿度'],
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
      data: xAxisData,
      axisLabel: {
        formatter: formatTime,
        rotate: 30,
        interval: 'auto'
      },
      boundaryGap: false
    },
    yAxis: [
      {
        type: 'value',
        name: '温度 (°C)',
        position: 'left',
        axisLabel: {
          formatter: '{value}'
        },
        splitLine: {
          show: true,
          lineStyle: {
            type: 'dashed'
          }
        }
      },
      {
        type: 'value',
        name: '湿度 (%)',
        position: 'right',
        min: 0,
        max: 100,
        axisLabel: {
          formatter: '{value}'
        },
        splitLine: {
          show: false
        }
      }
    ],
    series: [
      {
        name: '温度',
        type: 'line',
        data: tempValues,
        smooth: true,
        symbol: 'circle',
        symbolSize: 6,
        itemStyle: {
          color: themeColors.temp
        },
        lineStyle: {
          width: 2
        },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(255, 77, 79, 0.3)' },
            { offset: 1, color: 'rgba(255, 77, 79, 0.05)' }
          ])
        },
        connectNulls: false
      },
      {
        name: '湿度',
        type: 'line',
        yAxisIndex: 1,
        data: humiValues,
        smooth: true,
        symbol: 'circle',
        symbolSize: 6,
        itemStyle: {
          color: themeColors.humi
        },
        lineStyle: {
          width: 2
        },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(24, 144, 255, 0.3)' },
            { offset: 1, color: 'rgba(24, 144, 255, 0.05)' }
          ])
        },
        connectNulls: false
      }
    ],
    toolbox: props.showExport ? {
      feature: {
        saveAsImage: {
          name: `温湿度趋势_${props.data?.device_name || ''}_${new Date().toISOString().slice(0, 10)}`,
          pixelRatio: 2
        },
        dataZoom: {
          yAxisIndex: 'none'
        },
        restore: {}
      }
    } : undefined,
    dataZoom: [
      {
        type: 'inside',
        start: 0,
        end: 100
      },
      {
        type: 'slider',
        start: 0,
        end: 100,
        bottom: 50
      }
    ]
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
    link.download = `温湿度趋势_${props.data?.device_name || ''}_${new Date().toISOString().slice(0, 10)}.png`
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
  <div class="trend-chart">
    <a-spin :spinning="loading">
      <div v-if="isEmpty && !loading" class="empty-state">
        <a-empty description="暂无趋势数据" />
      </div>
      <div v-else ref="chartRef" class="chart-container"></div>
    </a-spin>
  </div>
</template>

<style scoped>
.trend-chart {
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