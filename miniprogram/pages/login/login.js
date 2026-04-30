/**
 * 登录页面
 * 微信小程序登录流程
 */

const auth = require('../../utils/auth')
const util = require('../../utils/util')

Page({
  /**
   * 页面数据
   */
  data: {
    loading: false,
    errorMsg: ''
  },

  /**
   * 页面加载
   * 检查是否已登录
   */
  onLoad(options) {
    // 如果已登录，直接跳转首页
    if (auth.isLoggedIn()) {
      this.navigateToIndex()
    }
  },

  /**
   * 微信登录
   */
  async onWechatLogin() {
    if (this.data.loading) return

    this.setData({
      loading: true,
      errorMsg: ''
    })

    util.showLoading('登录中...')

    try {
      const result = await auth.doWechatLogin()

      util.hideLoading()

      if (result.success) {
        if (result.isNewUser) {
          util.showSuccess('欢迎加入！')
        } else {
          util.showSuccess('登录成功')
        }

        // 跳转首页
        this.navigateToIndex()
      }
    } catch (err) {
      util.hideLoading()
      util.showError(err.message || '登录失败')

      this.setData({
        loading: false,
        errorMsg: err.message || '登录失败，请重试'
      })
    }
  },

  /**
   * 跳转首页
   */
  navigateToIndex() {
    // 使用 switchTab 跳转 tabBar 页面
    wx.switchTab({
      url: '/pages/index/index'
    })
  },

  /**
   * 页面显示
   */
  onShow() {
    // 页面显示时再次检查登录状态
    if (auth.isLoggedIn()) {
      this.navigateToIndex()
    }
  }
})