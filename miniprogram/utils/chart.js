/**
 * 简易图表工具
 * 基于小程序 Canvas API 绘制折线图
 * 用于设备历史数据趋势展示
 */

/**
 * 绘制折线图
 * @param {Object} options - 配置选项
 * @param {CanvasContext} options.ctx - Canvas 2D 上下文
 * @param {number} options.width - Canvas 宽度
 * @param {number} options.height - Canvas 高度
 * @param {Array} options.datasets - 数据集 [{data, label, color}]
 * @param {Array} options.labels - X 轴标签
 * @param {string} options.title - 图表标题
 * @param {number} options.padding - 内边距
 * @returns {boolean} - 绘制成功返回 true，失败返回 false
 */
function drawLineChart(options) {
  const {
    ctx,
    width,
    height,
    datasets = [],
    labels = [],
    title = '',
    padding = 40
  } = options

  // 参数验证
  if (!ctx || !datasets.length || !labels.length) {
    return false
  }

  // 验证数据有效性
  if (!hasValidData(datasets)) {
    return false
  }

  // 计算绘图区域
  const chartWidth = width - padding * 2
  const chartHeight = height - padding * 2
  const topPadding = title ? padding + 20 : padding

  // 清空画布
  ctx.clearRect(0, 0, width, height)

  // 绘制背景
  ctx.fillStyle = '#ffffff'
  ctx.fillRect(0, 0, width, height)

  // 绘制标题
  if (title) {
    ctx.fillStyle = '#333333'
    ctx.font = '14px sans-serif'
    ctx.textAlign = 'center'
    ctx.fillText(title, width / 2, 20)
  }

  // 计算所有数据的最小值和最大值
  let minVal = Infinity
  let maxVal = -Infinity

  datasets.forEach(dataset => {
    if (dataset.data && dataset.data.length) {
      const validData = dataset.data.filter(v => v !== null && v !== undefined)
      minVal = Math.min(minVal, ...validData)
      maxVal = Math.max(maxVal, ...validData)
    }
  })

  // 处理边界情况
  if (minVal === Infinity) minVal = 0
  if (maxVal === -Infinity) maxVal = 100
  if (minVal === maxVal) {
    minVal -= 1
    maxVal += 1
  }

  // 增加一点边距
  const range = maxVal - minVal
  minVal = Math.floor(minVal - range * 0.1)
  maxVal = Math.ceil(maxVal + range * 0.1)

  // 绘制 Y 轴刻度线和标签
  const ySteps = 5
  ctx.strokeStyle = '#e0e0e0'
  ctx.lineWidth = 1
  ctx.fillStyle = '#999999'
  ctx.font = '10px sans-serif'
  ctx.textAlign = 'right'

  for (let i = 0; i <= ySteps; i++) {
    const y = topPadding + (chartHeight / ySteps) * i
    const value = maxVal - ((maxVal - minVal) / ySteps) * i

    // 绘制刻度线
    ctx.beginPath()
    ctx.moveTo(padding, y)
    ctx.lineTo(width - padding, y)
    ctx.stroke()

    // 绘制刻度值
    ctx.fillText(value.toFixed(1), padding - 5, y + 3)
  }

  // 绘制 X 轴标签
  ctx.textAlign = 'center'
  const xStep = chartWidth / (labels.length - 1 || 1)

  labels.forEach((label, index) => {
    const x = padding + xStep * index

    // 只显示部分标签避免重叠
    if (labels.length <= 6 || index % Math.ceil(labels.length / 6) === 0) {
      ctx.fillText(label, x, height - padding + 15)
    }
  })

  // 绘制数据线
  datasets.forEach(dataset => {
    const { data = [], color = '#1890ff', label = '' } = dataset

    if (!data.length) return

    ctx.strokeStyle = color
    ctx.lineWidth = 2
    ctx.beginPath()

    let started = false

    data.forEach((value, index) => {
      if (value === null || value === undefined) return

      const x = padding + xStep * index
      const y = topPadding + chartHeight * (1 - (value - minVal) / (maxVal - minVal))

      if (!started) {
        ctx.moveTo(x, y)
        started = true
      } else {
        ctx.lineTo(x, y)
      }
    })

    ctx.stroke()

    // 绘制数据点
    ctx.fillStyle = color
    data.forEach((value, index) => {
      if (value === null || value === undefined) return

      const x = padding + xStep * index
      const y = topPadding + chartHeight * (1 - (value - minVal) / (maxVal - minVal))

      ctx.beginPath()
      ctx.arc(x, y, 3, 0, Math.PI * 2)
      ctx.fill()
    })

    // 绘制图例
    if (label) {
      const legendX = width - padding - 60
      const legendY = topPadding + datasets.indexOf(dataset) * 18

      ctx.fillStyle = color
      ctx.fillRect(legendX, legendY - 6, 12, 3)

      ctx.fillStyle = '#666666'
      ctx.font = '10px sans-serif'
      ctx.textAlign = 'left'
      ctx.fillText(label, legendX + 16, legendY)
    }
  })

  ctx.draw()
  return true
}

/**
 * 格式化图表数据
 * @param {Array} historyData - 历史数据数组
 * @param {string} field - 字段名（temp, humi）
 * @param {number} maxPoints - 最大数据点数
 * @returns {Object} {labels, data}
 */
function formatChartData(historyData, field = 'temp', maxPoints = 24) {
  if (!historyData || !historyData.length) {
    return { labels: [], data: [] }
  }

  // 按时间排序（旧 -> 新）
  const sorted = [...historyData].sort((a, b) => {
    const timeA = new Date(a.time).getTime()
    const timeB = new Date(b.time).getTime()
    return timeA - timeB
  })

  // 数据采样，避免点过多
  const step = Math.max(1, Math.floor(sorted.length / maxPoints))
  const sampled = sorted.filter((_, index) => index % step === 0)

  // 如果最后一点被跳过，加上
  if (sorted.length > 0 && sampled[sampled.length - 1] !== sorted[sorted.length - 1]) {
    sampled.push(sorted[sorted.length - 1])
  }

  // 提取标签和数据
  const labels = sampled.map(item => {
    const date = new Date(item.time)
    const hours = String(date.getHours()).padStart(2, '0')
    const minutes = String(date.getMinutes()).padStart(2, '0')
    return `${hours}:${minutes}`
  })

  const data = sampled.map(item => item[field])

  return { labels, data }
}

/**
 * 准备温度湿度双轴图表数据
 * @param {Array} historyData - 历史数据数组
 * @param {number} maxPoints - 最大数据点数
 * @returns {Object} {labels, datasets}
 */
function prepareTempHumiData(historyData, maxPoints = 24) {
  if (!historyData || !historyData.length) {
    return { labels: [], datasets: [] }
  }

  // 按时间排序（旧 -> 新）
  const sorted = [...historyData].sort((a, b) => {
    const timeA = new Date(a.time).getTime()
    const timeB = new Date(b.time).getTime()
    return timeA - timeB
  })

  // 数据采样
  const step = Math.max(1, Math.floor(sorted.length / maxPoints))
  const sampled = sorted.filter((_, index) => index % step === 0)

  if (sorted.length > 0 && sampled[sampled.length - 1] !== sorted[sorted.length - 1]) {
    sampled.push(sorted[sorted.length - 1])
  }

  // 提取标签
  const labels = sampled.map(item => {
    const date = new Date(item.time)
    const hours = String(date.getHours()).padStart(2, '0')
    const minutes = String(date.getMinutes()).padStart(2, '0')
    return `${hours}:${minutes}`
  })

  // 温度数据集
  const tempData = sampled.map(item => item.temp)
  // 湿度数据集
  const humiData = sampled.map(item => item.humi)

  return {
    labels,
    datasets: [
      { data: tempData, label: '温度(°C)', color: '#ff7875' },
      { data: humiData, label: '湿度(%)', color: '#36cfc9' }
    ]
  }
}

/**
 * 检查是否有有效数据
 * @param {Array} datasets - 数据集数组
 * @returns {boolean}
 */
function hasValidData(datasets) {
  if (!datasets || !datasets.length) return false

  return datasets.some(dataset => {
    if (!dataset.data || !dataset.data.length) return false
    return dataset.data.some(v => v !== null && v !== undefined)
  })
}

/**
 * 绘制柱状图
 * @param {Object} options - 配置选项
 * @param {CanvasContext} options.ctx - Canvas 2D 上下文
 * @param {number} options.width - Canvas 宽度
 * @param {number} options.height - Canvas 高度
 * @param {Array} options.labels - X 轴标签
 * @param {Array} options.values - 数值数组
 * @param {string} options.title - 图表标题
 * @param {string} options.color - 柱状图颜色
 * @param {number} options.padding - 内边距
 * @returns {boolean}
 */
function drawBarChart(options) {
  const {
    ctx,
    width,
    height,
    labels = [],
    values = [],
    title = '',
    color = '#1890ff',
    padding = 40
  } = options

  // 参数验证
  if (!ctx || !labels.length || !values.length) {
    return false
  }

  // 计算绘图区域
  const chartWidth = width - padding * 2
  const chartHeight = height - padding * 2
  const topPadding = title ? padding + 20 : padding

  // 清空画布
  ctx.clearRect(0, 0, width, height)

  // 绘制背景
  ctx.fillStyle = '#ffffff'
  ctx.fillRect(0, 0, width, height)

  // 绘制标题
  if (title) {
    ctx.fillStyle = '#333333'
    ctx.font = '14px sans-serif'
    ctx.textAlign = 'center'
    ctx.fillText(title, width / 2, 20)
  }

  // 计算最大值
  const maxVal = Math.max(...values) || 100

  // 计算柱宽
  const barWidth = (chartWidth / labels.length) * 0.6
  const barGap = (chartWidth / labels.length) * 0.4

  // 绘制柱状图
  ctx.fillStyle = color

  values.forEach((value, index) => {
    const barHeight = (value / maxVal) * chartHeight
    const x = padding + (chartWidth / labels.length) * index + barGap / 2
    const y = topPadding + chartHeight - barHeight

    // 绘制柱子
    ctx.fillRect(x, y, barWidth, barHeight)

    // 绘制数值
    ctx.fillStyle = '#666666'
    ctx.font = '10px sans-serif'
    ctx.textAlign = 'center'
    ctx.fillText(value.toFixed(1), x + barWidth / 2, y - 5)
    ctx.fillStyle = color
  })

  // 绘制 X 轴标签
  ctx.fillStyle = '#666666'
  ctx.font = '10px sans-serif'
  ctx.textAlign = 'center'

  labels.forEach((label, index) => {
    const x = padding + (chartWidth / labels.length) * index + (chartWidth / labels.length) / 2
    // 简化标签显示
    const shortLabel = label.length > 6 ? label.substring(0, 6) + '...' : label
    ctx.fillText(shortLabel, x, height - padding + 15)
  })

  ctx.draw()
  return true
}

/**
 * 绘制饼图
 * @param {Object} options - 配置选项
 * @param {CanvasContext} options.ctx - Canvas 2D 上下文
 * @param {number} options.width - Canvas 宽度
 * @param {number} options.height - Canvas 高度
 * @param {Array} options.labels - 标签数组
 * @param {Array} options.values - 数值数组
 * @param {string} options.title - 图表标题
 * @param {Array} options.colors - 颜色数组
 * @returns {boolean}
 */
function drawPieChart(options) {
  const {
    ctx,
    width,
    height,
    labels = [],
    values = [],
    title = '',
    colors = ['#1890ff', '#52c41a', '#faad14', '#ff4d4f', '#722ed1']
  } = options

  // 参数验证
  if (!ctx || !labels.length || !values.length) {
    return false
  }

  // 清空画布
  ctx.clearRect(0, 0, width, height)

  // 绘制背景
  ctx.fillStyle = '#ffffff'
  ctx.fillRect(0, 0, width, height)

  // 绘制标题
  if (title) {
    ctx.fillStyle = '#333333'
    ctx.font = '14px sans-serif'
    ctx.textAlign = 'center'
    ctx.fillText(title, width / 2, 20)
  }

  // 计算总值
  const total = values.reduce((sum, v) => sum + v, 0) || 100

  // 饼图中心和半径
  const centerX = width / 2
  const centerY = height / 2 - 20
  const radius = Math.min(width, height) / 3

  // 绘制饼图扇形
  let startAngle = -Math.PI / 2

  values.forEach((value, index) => {
    const sliceAngle = (value / total) * Math.PI * 2
    const endAngle = startAngle + sliceAngle

    ctx.beginPath()
    ctx.moveTo(centerX, centerY)
    ctx.arc(centerX, centerY, radius, startAngle, endAngle)
    ctx.closePath()

    ctx.fillStyle = colors[index % colors.length]
    ctx.fill()

    startAngle = endAngle
  })

  // 绘制图例
  const legendStartY = height - 40
  const legendItemWidth = width / labels.length

  labels.forEach((label, index) => {
    const x = legendItemWidth * index + legendItemWidth / 2
    const y = legendStartY

    // 绘制色块
    ctx.fillStyle = colors[index % colors.length]
    ctx.fillRect(x - 30, y - 6, 12, 12)

    // 绘制标签
    ctx.fillStyle = '#666666'
    ctx.font = '10px sans-serif'
    ctx.textAlign = 'left'
    const shortLabel = label.length > 4 ? label.substring(0, 4) : label
    ctx.fillText(`${shortLabel}: ${values[index]}`, x - 15, y)
  })

  ctx.draw()
  return true
}

module.exports = {
  drawLineChart,
  drawBarChart,
  drawPieChart,
  formatChartData,
  prepareTempHumiData,
  hasValidData
}