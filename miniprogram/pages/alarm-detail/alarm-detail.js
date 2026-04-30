/**
 * 告警详情页面
 * 显示告警完整信息，支持处理操作
 */

const api = require('../../utils/api')
const auth = require('../../utils/auth')
const util = require('../../utils/util')
const { isAuthError } = require('../../utils/request')

Page({
  data: {
    alarmId: null,
    alarm: null,
    device: null,
    loading: true,
    errorMsg: '',
    handling: false
  },

  onLoad(options) {
    if (!auth.isLoggedIn()) {
      wx.navigateTo({ url: '/pages/login/login' })
      return
    }

    const alarmId = parseInt(options.id)
    if (!alarmId) {
      this.setData({ errorMsg: '告警ID无效' })
      return
    }

    this.setData({ alarmId })
    this.loadAlarmDetail()
  },

  onPullDownRefresh() {
    this.loadAlarmDetail().then(() => wx.stopPullDownRefresh())
  },

  /**
   * 加载告警详情
   */
  async loadAlarmDetail() {
    this.setData({ loading: true, errorMsg: '' })

    try {
      // 使用新的告警详情 API
      const alarm = await api.getAlarm(this.data.alarmId)

      // 格式化告警数据
      const formattedAlarm = this.formatAlarm(alarm)

      this.setData({
        alarm: formattedAlarm,
        loading: false
      })

      // 如果告警关联了设备，加载设备信息
      if (alarm.device_id) {
        this.loadDeviceInfo(alarm.device_id)
      }
    } catch (err) {
      // 如果新 API 不支持，尝试备用方案（从列表查找）
      if (err.message === '资源不存在' || err.code === 'NOT_FOUND') {
        const alarm = await this.findAlarmFromList()

        if (!alarm) {
          if (isAuthError(err.code)) {
            wx.navigateTo({ url: '/pages/login/login' })
            return
          }
          this.setData({ loading: false, errorMsg: '告警不存在或已删除' })
          return
        }

        const formattedAlarm = this.formatAlarm(alarm)
        this.setData({
          alarm: formattedAlarm,
          loading: false
        })

        if (alarm.device_id) {
          this.loadDeviceInfo(alarm.device_id)
        }
        return
      }

      if (isAuthError(err.code)) {
        wx.navigateTo({ url: '/pages/login/login' })
        return
      }
      this.setData({ loading: false, errorMsg: err.message })
    }
  },

  /**
   * 从告警列表中查找告警（备用方案）
   * @returns {Promise<object|null>}
   */
  async findAlarmFromList() {
    try {
      // 先从未处理告警列表查找
      const alarms = await api.getAlarms({ limit: 100 })
      const alarm = (alarms || []).find(a => a.id === this.data.alarmId)

      if (alarm) return alarm

      // 再从已处理告警列表查找
      const resolvedAlarms = await api.getAlarms({ is_resolved: true, limit: 100 })
      return (resolvedAlarms || []).find(a => a.id === this.data.alarmId)
    } catch (err) {
      return null
    }
  },

  /**
   * 加载关联设备信息
   */
  async loadDeviceInfo(deviceId) {
    try {
      // 从设备列表中查找设备名称
      const devices = await api.getDevices({ keyword: deviceId, limit: 10 })
      const device = (devices?.items || []).find(d => d.device_id === deviceId)

      if (device) {
        this.setData({ device })
      }
    } catch (err) {
      // 设备信息加载失败不影响告警详情显示
    }
  },

  /**
   * 格式化告警数据
   */
  formatAlarm(alarm) {
    return {
      id: alarm.id,
      type: alarm.type || '未知类型',
      typeText: this.getAlarmTypeText(alarm.type),
      message: alarm.message || alarm.type || '无详细信息',
      severity: alarm.severity || 'warning',
      severityText: this.getSeverityText(alarm.severity),
      severityClass: this.getSeverityClass(alarm.severity),
      device_id: alarm.device_id,
      is_resolved: alarm.is_resolved,
      resolvedText: alarm.is_resolved ? '已处理' : '未处理',
      resolvedClass: alarm.is_resolved ? 'resolved' : 'unresolved',
      occurred_at: alarm.occurred_at,
      occurredTime: this.formatTime(alarm.occurred_at),
      resolved_at: alarm.resolved_at,
      resolvedTime: alarm.resolved_at ? this.formatTime(alarm.resolved_at) : null,
      handled_by: alarm.handled_by,
      tenant_id: alarm.tenant_id
    }
  },

  /**
   * 获取告警类型文本
   */
  getAlarmTypeText(type) {
    const typeMap = {
      'offline': '设备离线',
      'temp_alarm': '温度告警',
      'humi_alarm': '湿度告警',
      'illegal_on': '非法开启',
      'illegal_off': '非法关闭',
      'device_error': '设备异常',
      'air_error': '空调异常'
    }
    return typeMap[type] || type || '未知类型'
  },

  /**
   * 获取严重程度文本
   */
  getSeverityText(severity) {
    const severityMap = {
      'critical': '严重',
      'warning': '警告',
      'info': '提示'
    }
    return severityMap[severity] || severity || '警告'
  },

  /**
   * 获取严重程度样式类名
   */
  getSeverityClass(severity) {
    const classMap = {
      'critical': 'severity-critical',
      'warning': 'severity-warning',
      'info': 'severity-info'
    }
    return classMap[severity] || 'severity-warning'
  },

  /**
   * 格式化时间
   */
  formatTime(timestamp) {
    if (!timestamp) return '--'

    const date = new Date(timestamp)
    const year = date.getFullYear()
    const month = String(date.getMonth() + 1).padStart(2, '0')
    const day = String(date.getDate()).padStart(2, '0')
    const hours = String(date.getHours()).padStart(2, '0')
    const minutes = String(date.getMinutes()).padStart(2, '0')
    const seconds = String(date.getSeconds()).padStart(2, '0')

    return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`
  },

  /**
   * 处理告警
   */
  async onHandleAlarm() {
    if (this.data.alarm.is_resolved) {
      util.showInfo('此告警已处理')
      return
    }

    const confirmed = await util.showConfirm(
      `确认处理此告警？\n类型: ${this.data.alarm.typeText}`
    )
    if (!confirmed) return

    this.setData({ handling: true })
    util.showLoading('处理中...')

    try {
      await api.handleAlarm(this.data.alarmId)

      util.hideLoading()
      util.showSuccess('告警已处理')

      // 更新本地状态
      this.setData({
        handling: false,
        alarm: {
          ...this.data.alarm,
          is_resolved: true,
          resolvedText: '已处理',
          resolvedClass: 'resolved',
          resolved_at: new Date().toISOString(),
          resolvedTime: this.formatTime(new Date())
        }
      })
    } catch (err) {
      util.hideLoading()
      this.setData({ handling: false })
      util.showError(err.message)
    }
  },

  /**
   * 跳转到设备详情
   */
  onDeviceTap() {
    if (!this.data.device) {
      util.showInfo('无法找到关联设备')
      return
    }

    wx.navigateTo({
      url: `/pages/device-detail/device-detail?id=${this.data.device.id}`
    })
  },

  /**
   * 返回告警列表
   */
  onBackToList() {
    wx.navigateBack()
  }
})