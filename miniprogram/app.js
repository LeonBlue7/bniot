/**
 * BNIoT 空调管理小程序
 * 应用入口
 */

App({
  globalData: {
    // API 基础地址
    baseUrl: 'https://www.jxbonner.cloud:5000/api',
    // 用户信息
    userInfo: null,
    // Token
    token: null,
    // 是否已登录
    isLoggedIn: false
  },

  onLaunch() {
    // 检查登录状态
    this.checkLoginStatus()
  },

  onShow() {
    // App show
  },

  onHide() {
    // App hide
  },

  /**
   * 检查登录状态
   * 从本地存储读取 token，判断是否需要重新登录
   */
  checkLoginStatus() {
    const token = wx.getStorageSync('token')
    const userInfo = wx.getStorageSync('userInfo')

    if (token && userInfo) {
      this.globalData.token = token
      this.globalData.userInfo = userInfo
      this.globalData.isLoggedIn = true
    }
  },

  /**
   * 设置登录状态
   * @param {string} token - JWT token
   * @param {object} userInfo - 用户信息
   */
  setLoginState(token, userInfo) {
    this.globalData.token = token
    this.globalData.userInfo = userInfo
    this.globalData.isLoggedIn = true

    // 存储到本地
    wx.setStorageSync('token', token)
    wx.setStorageSync('userInfo', userInfo)
  },

  /**
   * 清除登录状态
   */
  clearLoginState() {
    this.globalData.token = null
    this.globalData.userInfo = null
    this.globalData.isLoggedIn = false

    // 清除本地存储
    wx.removeStorageSync('token')
    wx.removeStorageSync('userInfo')
  }
})