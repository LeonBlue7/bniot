/**
 * 报表分析页面
 * 包含：能耗统计、温湿度趋势、告警统计、运行时长
 */

const api = require('../../utils/api')
const auth = require('../../utils/auth')
const util = require('../../utils/util')
const chart = require('../../utils/chart')
const { isAuthError } = require('../../utils/request')

Page({
  data: {
    // 当前选中的报表类型
    activeTab: 'energy',
    tabs: [
      { key: 'energy', name: '能耗统计' },
      { key: 'trend', name: '温湿度趋势' },
      { key: 'alarm', name: '告警统计' },
      { key: 'runtime', name: '运行时长' }
    ],

    // 时间范围选择
    dateRange: 7,
    dateRangeOptions: [
      { value: 1, label: '今天' },
      { value: 7, label: '近7天' },
      { value: 30, label: '近30天' }
    ],

    // 分区选择
    zones: [],
    selectedZoneId: null,
    showZonePicker: false,

    // 设备选择（温湿度趋势）
    devices: [],
    selectedDeviceId: null,
    showDevicePicker: false,

    // 数据加载状态
    loading: false,
    errorMsg: '',

    // 能耗数据
    energyData: [],
    energyTotal: 0,

    // 温湿度趋势数据
    trendData: null,
    trendLabels: [],
    trendTempData: [],
    trendHumiData: [],

    // 告警统计数据
    alarmReportData: null,
    alarmGroupBy: 'type',
    alarmGroupOptions: [
      { value: 'type', label: '按类型' },
      { value: 'severity', label: '按严重程度' },
      { value: 'device', label: '按设备' }
    ],

    // 运行时长数据
    runtimeData: [],
    runtimeTotal: 0,

    // Canvas 尺寸
    canvasWidth: 300,
    canvasHeight: 200
  },

  onLoad() {
    if (!auth.isLoggedIn()) {
      wx.navigateTo({ url: '/pages/login/login' })
      return
    }

    // 获取屏幕宽度，计算 Canvas 尺寸
    const systemInfo = wx.getSystemInfoSync()
    const canvasWidth = systemInfo.windowWidth - 32
    const canvasHeight = 200

    this.setData({ canvasWidth, canvasHeight })

    // 加载分区列表
    this.loadZones()

    // 加载默认报表
    this.loadReport()
  },

  onShow() {
    if (auth.isLoggedIn() && this.data.energyData.length === 0) {
      this.loadReport()
    }
  },

  onPullDownRefresh() {
    this.loadReport().then(() => wx.stopPullDownRefresh())
  },

  /**
   * 加载分区列表
   */
  async loadZones() {
    try {
      const zones = await api.getZones()
      const formattedZones = [
        { id: null, name: '全部分区' },
        ...(zones || []).map(z => ({ id: z.id, name: z.name }))
      ]
      this.setData({ zones: formattedZones })
    } catch (err) {
      // 分区加载失败不影响报表加载
    }
  },

  /**
   * 加载设备列表（用于温湿度趋势）
   */
  async loadDevices() {
    try {
      const result = await api.getDevices({ limit: 50 })
      const formattedDevices = [
        { id: null, name: '全部设备' },
        ...(result.items || []).map(d => ({ id: d.id, name: d.name || d.device_id }))
      ]
      this.setData({ devices: formattedDevices })
    } catch (err) {
      // 设备加载失败
    }
  },

  /**
   * 切换报表类型
   */
  onTabChange(e) {
    const tab = e.currentTarget.dataset.tab
    this.setData({ activeTab: tab, loading: false, errorMsg: '' })
    this.loadReport()
  },

  /**
   * 切换时间范围
   */
  onDateRangeChange(e) {
    const range = parseInt(e.currentTarget.dataset.range)
    this.setData({ dateRange: range })
    this.loadReport()
  },

  /**
   * 显示分区选择器
   */
  onShowZonePicker() {
    this.setData({ showZonePicker: true })
  },

  /**
   * 隐藏分区选择器
   */
  onHideZonePicker() {
    this.setData({ showZonePicker: false })
  },

  /**
   * 选择分区
   */
  onZoneSelect(e) {
    const zoneId = e.currentTarget.dataset.zoneId
    this.setData({
      selectedZoneId: zoneId,
      showZonePicker: false
    })
    this.loadReport()
  },

  /**
   * 显示设备选择器
   */
  onShowDevicePicker() {
    if (this.data.devices.length === 0) {
      this.loadDevices()
    }
    this.setData({ showDevicePicker: true })
  },

  /**
   * 隐藏设备选择器
   */
  onHideDevicePicker() {
    this.setData({ showDevicePicker: false })
  },

  /**
   * 选择设备
   */
  onDeviceSelect(e) {
    const deviceId = e.currentTarget.dataset.deviceId
    this.setData({
      selectedDeviceId: deviceId,
      showDevicePicker: false
    })
    this.loadReport()
  },

  /**
   * 切换告警分组方式
   */
  onAlarmGroupChange(e) {
    const groupBy = e.currentTarget.dataset.group
    this.setData({ alarmGroupBy: groupBy })
    this.loadReport()
  },

  /**
   * 加载报表数据
   */
  async loadReport() {
    this.setData({ loading: true, errorMsg: '' })

    try {
      const { activeTab, dateRange, selectedZoneId, selectedDeviceId, alarmGroupBy } = this.data

      // 计算日期范围
      const endDate = util.formatDate(new Date())
      const startDate = util.formatDate(new Date(Date.now() - dateRange * 24 * 60 * 60 * 1000))

      const params = {
        start_date: startDate,
        end_date: endDate
      }
      if (selectedZoneId) params.zone_id = selectedZoneId

      switch (activeTab) {
        case 'energy':
          await this.loadEnergyReport(params)
          break
        case 'trend':
          await this.loadTrendReport(params, selectedDeviceId)
          break
        case 'alarm':
          await this.loadAlarmReport(params, alarmGroupBy)
          break
        case 'runtime':
          await this.loadRuntimeReport(params)
          break
      }

      this.setData({ loading: false })
    } catch (err) {
      if (isAuthError(err.code)) {
        wx.navigateTo({ url: '/pages/login/login' })
        return
      }
      this.setData({ loading: false, errorMsg: err.message })
    }
  },

  /**
   * 加载能耗报表
   */
  async loadEnergyReport(params) {
    const data = await api.getEnergyStats(params)
    const energyData = data || []
    const energyTotal = energyData.reduce((sum, item) => sum + (item.runtime_hours || 0), 0)

    this.setData({ energyData, energyTotal })

    // 绘制图表
    this.drawEnergyChart()
  },

  /**
   * 加载温湿度趋势报表
   */
  async loadTrendReport(params, deviceId) {
    if (deviceId) params.device_id = deviceId
    params.interval = this.data.dateRange <= 7 ? '1h' : '6h'

    const data = await api.getTrendData(params)

    this.setData({
      trendData: data,
      trendLabels: data?.labels || [],
      trendTempData: data?.temp_data || [],
      trendHumiData: data?.humi_data || []
    })

    // 绘制图表
    this.drawTrendChart()
  },

  /**
   * 加载告警报表
   */
  async loadAlarmReport(params, groupBy) {
    params.group_by = groupBy

    const data = await api.getAlarmReport(params)
    this.setData({ alarmReportData: data })

    // 绘制图表
    this.drawAlarmChart()
  },

  /**
   * 加载运行时长报表
   */
  async loadRuntimeReport(params) {
    params.limit = 10

    const data = await api.getRuntimeStats(params)
    const runtimeData = data || []
    const runtimeTotal = runtimeData.reduce((sum, item) => sum + (item.runtime_hours || 0), 0)

    this.setData({ runtimeData, runtimeTotal })

    // 绘制图表
    this.drawRuntimeChart()
  },

  /**
   * 绘制能耗图表
   */
  drawEnergyChart() {
    const { energyData, canvasWidth, canvasHeight } = this.data
    if (!energyData.length) return

    const query = wx.createSelectorQuery()
    query.select('#energyChart')
      .fields({ node: true, size: true })
      .exec((res) => {
        if (!res[0] || !res[0].node) return

        const canvas = res[0].node
        const ctx = canvas.getContext('2d')
        canvas.width = canvasWidth
        canvas.height = canvasHeight

        // 准备数据
        const labels = energyData.map(d => d.device_name || `设备${d.device_id}`)
        const values = energyData.map(d => d.runtime_hours || 0)

        chart.drawBarChart({
          ctx,
          width: canvasWidth,
          height: canvasHeight,
          labels,
          values,
          title: '运行时长分布',
          color: '#1890ff',
          padding: 40
        })
      })
  },

  /**
   * 绘制温湿度趋势图表
   */
  drawTrendChart() {
    const { trendLabels, trendTempData, trendHumiData, canvasWidth, canvasHeight } = this.data
    if (!trendLabels.length) return

    const query = wx.createSelectorQuery()
    query.select('#trendChart')
      .fields({ node: true, size: true })
      .exec((res) => {
        if (!res[0] || !res[0].node) return

        const canvas = res[0].node
        const ctx = canvas.getContext('2d')
        canvas.width = canvasWidth
        canvas.height = canvasHeight

        chart.drawLineChart({
          ctx,
          width: canvasWidth,
          height: canvasHeight,
          datasets: [
            { label: '温度', data: trendTempData, color: '#ff4d4f' },
            { label: '湿度', data: trendHumiData, color: '#52c41a' }
          ],
          labels: trendLabels,
          title: '温湿度趋势',
          padding: 40
        })
      })
  },

  /**
   * 绘制告警图表
   */
  drawAlarmChart() {
    const { alarmReportData, alarmGroupBy, canvasWidth, canvasHeight } = this.data
    if (!alarmReportData || !alarmReportData.grouped_data) return

    const query = wx.createSelectorQuery()
    query.select('#alarmChart')
      .fields({ node: true, size: true })
      .exec((res) => {
        if (!res[0] || !res[0].node) return

        const canvas = res[0].node
        const ctx = canvas.getContext('2d')
        canvas.width = canvasWidth
        canvas.height = canvasHeight

        const groupedData = alarmReportData.grouped_data
        const labels = groupedData.map(d => d.label || d.key)
        const values = groupedData.map(d => d.count)

        chart.drawPieChart({
          ctx,
          width: canvasWidth,
          height: canvasHeight,
          labels,
          values,
          title: `告警分布 (${alarmGroupBy})`,
          colors: ['#ff4d4f', '#faad14', '#52c41a', '#1890ff', '#722ed1']
        })
      })
  },

  /**
   * 绘制运行时长图表
   */
  drawRuntimeChart() {
    const { runtimeData, canvasWidth, canvasHeight } = this.data
    if (!runtimeData.length) return

    const query = wx.createSelectorQuery()
    query.select('#runtimeChart')
      .fields({ node: true, size: true })
      .exec((res) => {
        if (!res[0] || !res[0].node) return

        const canvas = res[0].node
        const ctx = canvas.getContext('2d')
        canvas.width = canvasWidth
        canvas.height = canvasHeight

        const labels = runtimeData.map(d => d.device_name || `设备${d.device_id}`)
        const values = runtimeData.map(d => d.runtime_hours || 0)

        chart.drawBarChart({
          ctx,
          width: canvasWidth,
          height: canvasHeight,
          labels,
          values,
          title: '设备运行时长排行',
          color: '#52c41a',
          padding: 40
        })
      })
  },

  /**
   * 格式化运行时长
   */
  formatRuntime(hours) {
    if (!hours) return '--'
    if (hours < 1) return `${Math.floor(hours * 60)}分钟`
    return `${hours.toFixed(1)}小时`
  }
})