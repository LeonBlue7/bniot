/**
 * 设备详情页面
 * 包含：设备信息、实时数据、运行统计、参数设置、历史数据图表、远程控制
 * 支持 WebSocket 实时数据更新
 */

const api = require('../../utils/api')
const auth = require('../../utils/auth')
const util = require('../../utils/util')
const chart = require('../../utils/chart')
const { isAuthError } = require('../../utils/request')
const { wsManager, WS_STATE } = require('../../utils/websocket')

// 参数定义映射（用于显示名称）
const PARAM_DEFINITIONS = {
  '101': { name: '联动模式', type: 'number', range: [0, 2], desc: '0-自动,1-夏天模式,2-冬天模式' },
  '102': { name: '夏天空调开机温度', type: 'number', range: [16, 35], unit: '°C' },
  '103': { name: '夏天空调关机温度', type: 'number', range: [16, 35], unit: '°C' },
  '104': { name: '夏天空调关机温度', type: 'number', range: [16, 35], unit: '°C' },
  '105': { name: '冬天空调开机温度', type: 'number', range: [5, 30], unit: '°C' },
  '106': { name: '冬天空调关机温度', type: 'number', range: [5, 30], unit: '°C' },
  '201': { name: '时间段1开始', type: 'time', format: 'HH:mm' },
  '202': { name: '时间段1结束', type: 'time', format: 'HH:mm' },
  '203': { name: '时间段2开始', type: 'time', format: 'HH:mm' },
  '204': { name: '时间段2结束', type: 'time', format: 'HH:mm' },
  '301': { name: '空调开机最小温度差', type: 'number', range: [0, 10], unit: '°C' },
  '302': { name: '空调关机最小温度差', type: 'number', range: [0, 10], unit: '°C' },
  '401': { name: '告警温度上限', type: 'number', range: [0, 50], unit: '°C' },
  '402': { name: '告警温度下限', type: 'number', range: [0, 50], unit: '°C' },
  '403': { name: '告警湿度上限', type: 'number', range: [0, 100], unit: '%' },
  '404': { name: '告警湿度下限', type: 'number', range: [0, 100], unit: '%' },
  '501': { name: '数据上送周期', type: 'number', range: [1, 60], unit: '分钟' },
  // V20 新增参数
  '107': { name: '冬天空调关机温度', type: 'number', range: [5, 30], unit: '°C' },
  '108': { name: '冬天开始月份', type: 'number', range: [1, 12], unit: '月' },
  '109': { name: '冬天结束月份', type: 'number', range: [1, 12], unit: '月' },
  '110': { name: '空调关机间隔', type: 'number', range: [0, 30], unit: '分钟' }
}

Page({
  data: {
    deviceId: null,
    device: null,
    loading: true,
    errorMsg: '',

    // 参数设置相关
    params: [],
    paramsLoading: false,
    showParamModal: false,
    currentParam: null,
    paramValue: '',
    paramErrorMsg: '',

    // 历史数据图表相关
    historyData: [],
    historyLoading: false,
    selectedHours: 24,
    hoursOptions: [
      { value: 24, label: '24小时' },
      { value: 72, label: '3天' },
      { value: 168, label: '7天' }
    ],

    // Canvas 图表
    canvasWidth: 300,
    canvasHeight: 200,

    // WebSocket 状态
    wsConnected: false,
    realtimeData: null,
    // WebSocket 监听器 ID
    wsListenerIds: {}
  },

  onLoad(options) {
    if (!auth.isLoggedIn()) {
      wx.navigateTo({ url: '/pages/login/login' })
      return
    }

    const deviceId = parseInt(options.id)
    if (!deviceId) {
      this.setData({ errorMsg: '设备ID无效' })
      return
    }

    this.setData({ deviceId })

    // 获取屏幕宽度，计算 Canvas 尺寸
    const systemInfo = wx.getSystemInfoSync()
    const canvasWidth = systemInfo.windowWidth - 32  // 减去左右 padding
    const canvasHeight = 180

    this.setData({ canvasWidth, canvasHeight })

    // 加载所有数据
    this.loadAllData()

    // 初始化 WebSocket
    this.initWebSocket()
  },

  onShow() {
    // 页面显示时刷新数据
    if (this.data.deviceId && auth.isLoggedIn()) {
      this.loadDeviceDetail()
    }
  },

  onHide() {
    // 页面隐藏时取消订阅
    if (this.data.deviceId) {
      wsManager.unsubscribeDevice(String(this.data.deviceId))
    }
  },

  onUnload() {
    // 页面卸载时取消订阅并移除监听器
    if (this.data.deviceId) {
      wsManager.unsubscribeDevice(String(this.data.deviceId))
    }
    this.removeWsListeners()
  },

  onPullDownRefresh() {
    this.loadAllData().then(() => wx.stopPullDownRefresh())
  },

  /**
   * 初始化 WebSocket 连接
   */
  initWebSocket() {
    const token = wx.getStorageSync('token')
    if (!token) return

    // 注册 WebSocket 事件监听
    this.setupWsListeners()

    // 如果未连接，尝试连接
    if (!wsManager.isConnected()) {
      wsManager.connect(token)
        .then(() => {
          this.setData({ wsConnected: true })
          // 订阅当前设备数据
          this.subscribeToDevice()
        })
        .catch(() => {
          // WebSocket 连接失败，不影响页面正常使用
          this.setData({ wsConnected: false })
        })
    } else {
      this.setData({ wsConnected: true })
      this.subscribeToDevice()
    }
  },

  /**
   * 订阅当前设备数据
   */
  subscribeToDevice() {
    if (this.data.deviceId && wsManager.isConnected()) {
      wsManager.subscribeDevice(String(this.data.deviceId))
    }
  },

  /**
   * 设置 WebSocket 事件监听
   */
  setupWsListeners() {
    // 监听设备数据推送
    this.data.wsListenerIds.deviceData = wsManager.on('device_data', this.onDeviceDataReceived.bind(this))

    // 监听设备状态变化
    this.data.wsListenerIds.deviceStatus = wsManager.on('device_status', this.onDeviceStatusChanged.bind(this))

    // 监听连接状态变化
    this.data.wsListenerIds.connected = wsManager.on('connected', () => {
      this.setData({ wsConnected: true })
      this.subscribeToDevice()
    })

    this.data.wsListenerIds.disconnected = wsManager.on('disconnected', () => {
      this.setData({ wsConnected: false })
    })
  },

  /**
   * 移除 WebSocket 事件监听
   */
  removeWsListeners() {
    const ids = this.data.wsListenerIds
    if (ids.deviceData) wsManager.off('device_data', ids.deviceData)
    if (ids.deviceStatus) wsManager.off('device_status', ids.deviceStatus)
    if (ids.connected) wsManager.off('connected', ids.connected)
    if (ids.disconnected) wsManager.off('disconnected', ids.disconnected)
    this.data.wsListenerIds = {}
  },

  /**
   * 接收到设备数据推送
   * @param {object} data - 设备数据
   */
  onDeviceDataReceived(data) {
    // 检查是否是当前设备的数据
    if (data.device_id != this.data.deviceId) return

    // 更新实时数据
    this.setData({ realtimeData: data })

    // 更新设备信息中的实时数据
    if (this.data.device) {
      const device = { ...this.data.device }
      if (data.temp !== undefined) device.temp = data.temp
      if (data.humi !== undefined) device.humidity = data.humi
      if (data.current !== undefined) device.current = data.current
      if (data.airstate !== undefined) device.airstate = data.airstate

      this.setData({ device })
    }
  },

  /**
   * 设备状态变化
   * @param {object} data - 设备状态数据
   */
  onDeviceStatusChanged(data) {
    // 检查是否是当前设备
    if (data.device_id != this.data.deviceId) return

    // 更新设备状态
    if (this.data.device) {
      const device = { ...this.data.device }
      if (data.is_online !== undefined) device.is_online = data.is_online
      if (data.airstate !== undefined) device.airstate = data.airstate

      this.setData({ device })
    }

    // 显示状态变化提示
    if (data.is_online !== undefined) {
      wx.showToast({
        title: data.is_online ? '设备已上线' : '设备已离线',
        icon: 'none',
        duration: 2000
      })
    }
  },

  /**
   * 加载所有数据
   */
  async loadAllData() {
    await Promise.all([
      this.loadDeviceDetail(),
      this.loadDeviceParams(),
      this.loadHistoryData()
    ])
  },

  /**
   * 加载设备详情
   */
  async loadDeviceDetail() {
    this.setData({ loading: true, errorMsg: '' })

    try {
      const device = await api.getDeviceDetail(this.data.deviceId)
      this.setData({
        device: device,
        loading: false
      })
    } catch (err) {
      if (isAuthError(err.code)) {
        wx.navigateTo({ url: '/pages/login/login' })
        return
      }
      this.setData({ loading: false, errorMsg: err.message })
    }
  },

  /**
   * 加载设备参数列表
   */
  async loadDeviceParams() {
    this.setData({ paramsLoading: true })

    try {
      const result = await api.getDeviceParams(this.data.deviceId)

      // 格式化参数列表
      const params = (result.params || []).map(p => {
        const def = PARAM_DEFINITIONS[p.code] || {}
        return {
          code: p.code,
          name: def.name || p.name || p.code,
          type: def.type || p.type || 'number',
          range: def.range || p.range,
          unit: def.unit || '',
          desc: def.desc || p.desc || '',
          currentValue: p.current_value
        }
      })

      this.setData({
        params: params,
        paramsLoading: false,
        protocolVersion: result.version
      })
    } catch (err) {
      this.setData({ paramsLoading: false })
    }
  },

  /**
   * 加载历史数据
   */
  async loadHistoryData() {
    this.setData({ historyLoading: true })

    try {
      const data = await api.getDeviceData(this.data.deviceId, this.data.selectedHours)

      this.setData({
        historyData: data || [],
        historyLoading: false
      })

      // 绘制图表
      this.drawChart()
    } catch (err) {
      this.setData({ historyLoading: false })
    }
  },

  /**
   * 绘制历史数据图表
   */
  drawChart() {
    const { historyData, canvasWidth, canvasHeight } = this.data

    if (!historyData.length) return

    // 使用 Canvas 2D API
    const query = wx.createSelectorQuery()
    query.select('#historyChart')
      .fields({ node: true, size: true })
      .exec((res) => {
        if (!res[0] || !res[0].node) return

        const canvas = res[0].node
        const ctx = canvas.getContext('2d')

        // 设置 Canvas 尺寸
        canvas.width = canvasWidth
        canvas.height = canvasHeight

        // 准备图表数据
        const { labels, datasets } = chart.prepareTempHumiData(historyData, 24)

        // 绘制图表
        chart.drawLineChart({
          ctx: ctx,
          width: canvasWidth,
          height: canvasHeight,
          datasets: datasets,
          labels: labels,
          title: '温度/湿度趋势',
          padding: 35
        })
      })
  },

  /**
   * 切换历史数据时间范围
   */
  onHoursChange(e) {
    const hours = parseInt(e.currentTarget.dataset.hours)
    this.setData({ selectedHours: hours })
    this.loadHistoryData()
  },

  /**
   * 打开参数设置弹窗
   */
  onParamTap(e) {
    const param = e.currentTarget.dataset.param

    this.setData({
      showParamModal: true,
      currentParam: param,
      paramValue: param.currentValue !== null ? String(param.currentValue) : '',
      paramErrorMsg: ''
    })
  },

  /**
   * 关闭参数设置弹窗
   */
  onModalClose() {
    this.setData({
      showParamModal: false,
      currentParam: null,
      paramValue: '',
      paramErrorMsg: ''
    })
  },

  /**
   * 参数值输入
   */
  onParamInput(e) {
    this.setData({ paramValue: e.detail.value })
  },

  /**
   * 确认设置参数
   */
  async onParamSubmit() {
    const { currentParam, paramValue } = this.data

    if (!currentParam) return

    // 验证输入
    const value = parseFloat(paramValue)
    if (isNaN(value)) {
      this.setData({ paramErrorMsg: '请输入有效的数值' })
      return
    }

    // 范围验证
    if (currentParam.range) {
      const [min, max] = currentParam.range
      if (value < min || value > max) {
        this.setData({ paramErrorMsg: `值范围: ${min} - ${max}${currentParam.unit}` })
        return
      }
    }

    util.showLoading('设置中...')

    try {
      const result = await api.setDeviceParam(this.data.deviceId, currentParam.code, value)

      util.hideLoading()

      if (result.success) {
        util.showSuccess('参数设置命令已发送')

        // 更新本地参数显示
        const params = this.data.params.map(p => {
          if (p.code === currentParam.code) {
            return { ...p, currentValue: value }
          }
          return p
        })

        this.setData({
          params: params,
          showParamModal: false,
          currentParam: null,
          paramValue: ''
        })
      } else {
        const errorMsg = result.message || '设置失败'
        if (result.validation_errors && result.validation_errors.length) {
          errorMsg = result.validation_errors[0]
        }
        this.setData({ paramErrorMsg: errorMsg })
      }
    } catch (err) {
      util.hideLoading()
      this.setData({ paramErrorMsg: err.message })
    }
  },

  /**
   * 远程控制
   */
  async onControl(e) {
    const airstate = e.currentTarget.dataset.airstate
    const actionText = airstate === 1 ? '开机' : '关机'

    const confirmed = await util.showConfirm(`确认${actionText}此设备？`)
    if (!confirmed) return

    util.showLoading(`${actionText}中...`)

    try {
      await api.controlDevice(this.data.deviceId, airstate)
      util.hideLoading()
      util.showSuccess(`${actionText}命令已发送`)
      // 刷新设备状态
      this.loadDeviceDetail()
    } catch (err) {
      util.hideLoading()
      util.showError(err.message)
    }
  },

  /**
   * 跳转到告警详情
   */
  onAlarmTap(e) {
    const alarmId = e.currentTarget.dataset.alarmId
    wx.navigateTo({
      url: `/pages/alarm-detail/alarm-detail?id=${alarmId}`
    })
  },

  /**
   * 格式化温度
   */
  formatTemp(temp) {
    if (temp === null || temp === undefined) return '--'
    return Number(temp).toFixed(1) + '°C'
  },

  /**
   * 格式化湿度
   */
  formatHumi(humi) {
    if (humi === null || humi === undefined) return '--'
    return Number(humi).toFixed(1) + '%'
  },

  /**
   * 格式化运行时间
   */
  formatRuntime(hours) {
    if (hours === null || hours === undefined) return '--'
    if (hours < 1) return Math.floor(hours * 60) + '分钟'
    return hours.toFixed(1) + '小时'
  }
})