/**
 * 告警中心页面
 */

const api = require('../../utils/api')
const auth = require('../../utils/auth')
const util = require('../../utils/util')
const { isAuthError } = require('../../utils/request')

Page({
  data: {
    alarms: [],
    loading: true,
    loadingMore: false,
    total: 0,
    skip: 0,
    limit: 20,
    hasMore: true,
    // 筛选条件
    filter: {
      is_resolved: false  // 默认显示未处理告警
    },
    tabs: [
      { key: false, name: '未处理' },
      { key: true, name: '已处理' }
    ],
    activeTab: false,
    errorMsg: ''
  },

  onLoad() {
    if (!auth.isLoggedIn()) {
      wx.navigateTo({ url: '/pages/login/login' })
      return
    }
    this.loadAlarms()
  },

  onShow() {
    if (auth.isLoggedIn() && this.data.alarms.length === 0) {
      this.loadAlarms()
    }
  },

  onPullDownRefresh() {
    this.data.skip = 0
    this.data.hasMore = true
    this.loadAlarms().then(() => wx.stopPullDownRefresh())
  },

  onReachBottom() {
    if (this.data.hasMore && !this.data.loadingMore) {
      this.loadMoreAlarms()
    }
  },

  async loadAlarms() {
    this.setData({ loading: true, errorMsg: '' })

    try {
      const params = {
        is_resolved: this.data.filter.is_resolved,
        skip: 0,
        limit: this.data.limit
      }

      const result = await api.getAlarms(params)

      this.setData({
        alarms: result || [],
        loading: false,
        hasMore: (result || []).length >= this.data.limit
      })
    } catch (err) {
      if (isAuthError(err.code)) {
        wx.navigateTo({ url: '/pages/login/login' })
        return
      }
      this.setData({ loading: false, errorMsg: err.message })
    }
  },

  async loadMoreAlarms() {
    if (!this.data.hasMore) return

    this.setData({ loadingMore: true })

    try {
      const params = {
        is_resolved: this.data.filter.is_resolved,
        skip: this.data.skip + this.data.limit,
        limit: this.data.limit
      }

      const result = await api.getAlarms(params)

      this.setData({
        alarms: [...this.data.alarms, ...result || []],
        skip: params.skip,
        hasMore: (result || []).length >= this.data.limit,
        loadingMore: false
      })
    } catch (err) {
      this.setData({ loadingMore: false })
      util.showError(err.message)
    }
  },

  onTabChange(e) {
    const resolved = e.currentTarget.dataset.resolved
    this.setData({
      filter: { is_resolved: resolved },
      activeTab: resolved,
      skip: 0,
      hasMore: true
    })
    this.loadAlarms()
  },

  onAlarmTap(e) {
    const alarm = e.detail.alarm
    wx.navigateTo({
      url: `/pages/alarm-detail/alarm-detail?id=${alarm.id}`
    })
  },

  async onAlarmHandle(e) {
    const alarm = e.detail.alarm

    const confirmed = await util.showConfirm(`确认处理此告警？\n${alarm.message || alarm.type}`)
    if (!confirmed) return

    util.showLoading('处理中...')

    try {
      await api.handleAlarm(alarm.id)
      util.hideLoading()
      util.showSuccess('告警已处理')
      this.loadAlarms()
    } catch (err) {
      util.hideLoading()
      util.showError(err.message)
    }
  },

  async onBatchHandle() {
    const unresolvedAlarms = this.data.alarms.filter(a => !a.is_resolved)
    if (unresolvedAlarms.length === 0) {
      util.showInfo('没有未处理的告警')
      return
    }

    const confirmed = await util.showConfirm(`确认批量处理 ${unresolvedAlarms.length} 条告警？`)
    if (!confirmed) return

    util.showLoading('处理中...')

    try {
      const ids = unresolvedAlarms.map(a => a.id)
      await api.batchHandleAlarms(ids)
      util.hideLoading()
      util.showSuccess(`已处理 ${unresolvedAlarms.length} 条告警`)
      this.loadAlarms()
    } catch (err) {
      util.hideLoading()
      util.showError(err.message)
    }
  }
})