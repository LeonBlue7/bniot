/**
 * 首页仪表盘
 * 显示统计信息、快速入口
 * 支持 WebSocket 实时告警推送
 */

const api = require('../../utils/api')
const auth = require('../../utils/auth')
const util = require('../../utils/util')
const { isAuthError } = require('../../utils/request')
const { wsManager, WS_STATE } = require('../../utils/websocket')

Page({
  /**
   * 页面数据
   */
  data: {
    // 统计数据
    stats: {
      total_devices: 0,
      online_devices: 0,
      offline_devices: 0,
      total_alarms: 0,
      unresolved_alarms: 0
    },
    // 最近设备列表
    recentDevices: [],
    // 未处理告警列表
    recentAlarms: [],
    // 加载状态
    loading: true,
    loadingDevices: true,
    loadingAlarms: true,
    // 错误信息
    errorMsg: '',
    // WebSocket 连接状态
    wsConnected: false,
    // WebSocket 监听器 ID
    wsListenerIds: {}
  },

  /**
   * 页面加载
   */
  onLoad() {
    // 检查登录状态
    if (!auth.isLoggedIn()) {
      wx.navigateTo({
        url: '/pages/login/login'
      })
      return
    }

    // 加载数据
    this.loadDashboardData()

    // 初始化 WebSocket
    this.initWebSocket()
  },

  /**
   * 页面显示
   */
  onShow() {
    // tabBar 页面每次显示时刷新数据
    if (auth.isLoggedIn()) {
      this.loadDashboardData()
    }
  },

  /**
   * 页面隐藏
   */
  onHide() {
    // 页面隐藏时保持 WebSocket 连接（用于后台接收告警）
  },

  /**
   * 页面卸载
   */
  onUnload() {
    // 移除 WebSocket 监听器
    this.removeWsListeners()
  },

  /**
   * 下拉刷新
   */
  onPullDownRefresh() {
    this.loadDashboardData().then(() => {
      wx.stopPullDownRefresh()
    })
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
          // 订阅告警推送
          wsManager.subscribeAlarms()
        })
        .catch(() => {
          // WebSocket 连接失败，不影响页面正常使用
          this.setData({ wsConnected: false })
        })
    } else {
      this.setData({ wsConnected: true })
      wsManager.subscribeAlarms()
    }
  },

  /**
   * 设置 WebSocket 事件监听
   */
  setupWsListeners() {
    // 监听告警推送
    this.data.wsListenerIds.alarm = wsManager.on('alarm', this.onAlarmReceived.bind(this))

    // 监听连接状态变化
    this.data.wsListenerIds.connected = wsManager.on('connected', () => {
      this.setData({ wsConnected: true })
      wsManager.subscribeAlarms()
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
    if (ids.alarm) wsManager.off('alarm', ids.alarm)
    if (ids.connected) wsManager.off('connected', ids.connected)
    if (ids.disconnected) wsManager.off('disconnected', ids.disconnected)
    this.data.wsListenerIds = {}
  },

  /**
   * 接收到告警推送
   * @param {object} alarm - 告警数据
   */
  onAlarmReceived(alarm) {
    // 更新统计数据（未处理告警数量+1）
    const stats = this.data.stats
    this.setData({
      stats: {
        ...stats,
        total_alarms: stats.total_alarms + 1,
        unresolved_alarms: stats.unresolved_alarms + 1
      }
    })

    // 将告警添加到列表顶部
    const recentAlarms = this.data.recentAlarms
    recentAlarms.unshift(alarm)
    // 保持最多 5 条
    if (recentAlarms.length > 5) {
      recentAlarms.pop()
    }
    this.setData({ recentAlarms })

    // 显示告警提示
    wx.showModal({
      title: '新告警',
      content: alarm.message || alarm.type || '收到新告警',
      showCancel: true,
      cancelText: '忽略',
      confirmText: '查看',
      success: (res) => {
        if (res.confirm) {
          // 跳转到告警详情
          wx.navigateTo({
            url: `/pages/alarm-detail/alarm-detail?id=${alarm.id}`
          })
        }
      }
    })
  },

  /**
   * 加载仪表盘数据
   */
  async loadDashboardData() {
    this.setData({
      loading: true,
      errorMsg: ''
    })

    try {
      // 并行请求统计数据、设备列表、告警列表
      const [stats, devices, alarms] = await Promise.all([
        api.getDashboardStats(),
        api.getDevices({ limit: 5 }),
        api.getAlarms({ is_resolved: false, limit: 5 })
      ])

      this.setData({
        stats: stats,
        recentDevices: devices.items || [],
        recentAlarms: alarms || [],
        loading: false,
        loadingDevices: false,
        loadingAlarms: false
      })
    } catch (err) {
      // 检查是否是认证错误
      if (isAuthError(err.code)) {
        wx.navigateTo({
          url: '/pages/login/login'
        })
        return
      }

      this.setData({
        loading: false,
        errorMsg: err.message || '加载失败，请下拉刷新重试'
      })
    }
  },

  /**
   * 点击统计卡片 - 设备
   */
  onStatsDeviceTap() {
    wx.switchTab({
      url: '/pages/devices/devices'
    })
  },

  /**
   * 点击统计卡片 - 告警
   */
  onStatsAlarmTap() {
    wx.switchTab({
      url: '/pages/alarms/alarms'
    })
  },

  /**
   * 点击设备卡片
   */
  onDeviceTap(e) {
    const device = e.detail.device
    wx.navigateTo({
      url: `/pages/device-detail/device-detail?id=${device.id}`
    })
  },

  /**
   * 点击设备详情
   */
  onDeviceDetail(e) {
    const device = e.detail.device
    wx.navigateTo({
      url: `/pages/device-detail/device-detail?id=${device.id}`
    })
  },

  /**
   * 点击告警条目
   */
  onAlarmTap(e) {
    const alarm = e.detail.alarm
    wx.navigateTo({
      url: `/pages/alarm-detail/alarm-detail?id=${alarm.id}`
    })
  },

  /**
   * 处理告警
   */
  async onAlarmHandle(e) {
    const alarm = e.detail.alarm

    const confirmed = await util.showConfirm(`确认处理此告警？\n${alarm.message || alarm.type}`)
    if (!confirmed) return

    util.showLoading('处理中...')

    try {
      await api.handleAlarm(alarm.id)
      util.hideLoading()
      util.showSuccess('告警已处理')

      // 重新加载数据
      this.loadDashboardData()
    } catch (err) {
      util.hideLoading()
      util.showError(err.message || '处理失败')
    }
  },

  /**
   * 查看更多设备
   */
  onViewMoreDevices() {
    wx.switchTab({
      url: '/pages/devices/devices'
    })
  },

  /**
   * 查看更多告警
   */
  onViewMoreAlarms() {
    wx.switchTab({
      url: '/pages/alarms/alarms'
    })
  }
})