/**
 * 分区列表页面
 */

const api = require('../../utils/api')
const auth = require('../../utils/auth')
const util = require('../../utils/util')

Page({
  data: {
    zones: [],
    loading: true,
    errorMsg: ''
  },

  onLoad() {
    if (!auth.isLoggedIn()) {
      wx.navigateTo({ url: '/pages/login/login' })
      return
    }
    this.loadZones()
  },

  onShow() {
    if (auth.isLoggedIn() && this.data.zones.length === 0) {
      this.loadZones()
    }
  },

  onPullDownRefresh() {
    this.loadZones().then(() => wx.stopPullDownRefresh())
  },

  async loadZones() {
    this.setData({ loading: true, errorMsg: '' })

    try {
      const result = await api.getZones()
      this.setData({
        zones: result || [],
        loading: false
      })
    } catch (err) {
      if (err.message.includes('过期')) {
        wx.navigateTo({ url: '/pages/login/login' })
        return
      }
      this.setData({ loading: false, errorMsg: err.message })
    }
  },

  onZoneTap(e) {
    const zone = e.currentTarget.dataset.zone
    // 分区点击功能：后续版本可跳转分区详情页或筛选该分区设备
    util.showInfo(`分区: ${zone.name}`)
  }
})