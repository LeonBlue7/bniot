/**
 * 认证管理模块
 * 处理 Token 存储、登录状态管理
 */

const app = getApp()

/**
 * 检查是否已登录
 * @returns {boolean}
 */
function isLoggedIn() {
  return app.globalData.isLoggedIn && app.globalData.token
}

/**
 * 获取 Token
 * @returns {string|null}
 */
function getToken() {
  return app.globalData.token || wx.getStorageSync('token')
}

/**
 * 获取用户信息
 * @returns {object|null}
 */
function getUserInfo() {
  return app.globalData.userInfo || wx.getStorageSync('userInfo')
}

/**
 * 保存登录状态
 * @param {string} token - JWT Token
 * @param {object} userInfo - 用户信息
 */
function saveLoginState(token, userInfo) {
  app.setLoginState(token, userInfo)
}

/**
 * 清除登录状态
 */
function clearLoginState() {
  app.clearLoginState()
}

/**
 * 微信登录流程
 * 1. 调用 wx.login() 获取 code
 * 2. 调用后端 /wechat/login 换取 token
 * 3. 保存登录状态
 * @returns {Promise<{success, isNewUser}>}
 */
function doWechatLogin() {
  return new Promise((resolve, reject) => {
    // 第一步：获取微信 code
    wx.login({
      success: (loginRes) => {
        if (loginRes.code) {
          // 第二步：调用后端 API
          const api = require('./api')
          api.wechatLogin(loginRes.code)
            .then((data) => {
              // 第三步：保存登录状态
              saveLoginState(data.access_token, data.user)

              resolve({
                success: true,
                isNewUser: data.is_new_user,
                user: data.user
              })
            })
            .catch((err) => {
              reject(new Error(`登录失败: ${err.message}`))
            })
        } else {
          reject(new Error('wx.login 获取 code 失败'))
        }
      },
      fail: (err) => {
        reject(new Error('微信登录失败'))
      }
    })
  })
}

/**
 * 检查登录状态，未登录则跳转登录页
 * @param {object} page - 页面实例（用于跳转）
 * @returns {boolean} - 是否已登录
 */
function checkLogin(page) {
  if (!isLoggedIn()) {
    wx.navigateTo({
      url: '/pages/login/login'
    })
    return false
  }
  return true
}

/**
 * 退出登录
 */
function logout() {
  clearLoginState()
  wx.navigateTo({
    url: '/pages/login/login'
  })
}

module.exports = {
  isLoggedIn,
  getToken,
  getUserInfo,
  saveLoginState,
  clearLoginState,
  doWechatLogin,
  checkLogin,
  logout
}