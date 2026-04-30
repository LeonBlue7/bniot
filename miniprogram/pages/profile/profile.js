/**
 * 个人中心页面
 * 包含：用户信息、修改密码、微信绑定状态、退出登录
 */

const api = require('../../utils/api')
const auth = require('../../utils/auth')
const util = require('../../utils/util')
const { isAuthError } = require('../../utils/request')

Page({
  data: {
    user: null,
    loading: true,
    errorMsg: '',

    // 修改密码弹窗
    showPasswordModal: false,
    oldPassword: '',
    newPassword: '',
    confirmPassword: '',
    passwordErrorMsg: '',

    // 微信绑定状态
    wechatBound: false,
    wechatOpenid: null
  },

  onLoad() {
    if (!auth.isLoggedIn()) {
      wx.navigateTo({ url: '/pages/login/login' })
      return
    }
    this.loadUserInfo()
  },

  onShow() {
    if (auth.isLoggedIn() && !this.data.user) {
      this.loadUserInfo()
    }
  },

  /**
   * 加载用户信息
   */
  async loadUserInfo() {
    this.setData({ loading: true, errorMsg: '' })

    try {
      const user = await api.getCurrentUser()

      this.setData({
        user: user,
        loading: false,
        wechatBound: !!user.wechat_openid,
        wechatOpenid: user.wechat_openid
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
   * 显示修改密码弹窗
   */
  onShowPasswordModal() {
    this.setData({
      showPasswordModal: true,
      oldPassword: '',
      newPassword: '',
      confirmPassword: '',
      passwordErrorMsg: ''
    })
  },

  /**
   * 隐藏修改密码弹窗
   */
  onHidePasswordModal() {
    this.setData({
      showPasswordModal: false,
      oldPassword: '',
      newPassword: '',
      confirmPassword: '',
      passwordErrorMsg: ''
    })
  },

  /**
   * 旧密码输入
   */
  onOldPasswordInput(e) {
    this.setData({ oldPassword: e.detail.value })
  },

  /**
   * 新密码输入
   */
  onNewPasswordInput(e) {
    this.setData({ newPassword: e.detail.value })
  },

  /**
   * 确认密码输入
   */
  onConfirmPasswordInput(e) {
    this.setData({ confirmPassword: e.detail.value })
  },

  /**
   * 提交修改密码
   */
  async onSubmitPassword() {
    const { oldPassword, newPassword, confirmPassword } = this.data

    // 验证输入
    if (!oldPassword) {
      this.setData({ passwordErrorMsg: '请输入旧密码' })
      return
    }
    if (!newPassword) {
      this.setData({ passwordErrorMsg: '请输入新密码' })
      return
    }
    if (newPassword.length < 6) {
      this.setData({ passwordErrorMsg: '新密码至少6位' })
      return
    }
    if (newPassword !== confirmPassword) {
      this.setData({ passwordErrorMsg: '两次密码不一致' })
      return
    }

    util.showLoading('修改中...')

    try {
      await api.changePassword(oldPassword, newPassword)
      util.hideLoading()
      util.showSuccess('密码修改成功')

      this.setData({
        showPasswordModal: false,
        oldPassword: '',
        newPassword: '',
        confirmPassword: '',
        passwordErrorMsg: ''
      })
    } catch (err) {
      util.hideLoading()
      this.setData({ passwordErrorMsg: err.message })
    }
  },

  /**
   * 解绑微信
   */
  async onUnbindWechat() {
    const confirmed = await util.showConfirm('确认解绑微信？解绑后小程序将无法登录此账号')
    if (!confirmed) return

    util.showLoading('解绑中...')

    try {
      await api.unbindWechat()
      util.hideLoading()
      util.showSuccess('微信已解绑')

      this.setData({
        wechatBound: false,
        wechatOpenid: null,
        user: { ...this.data.user, wechat_openid: null }
      })
    } catch (err) {
      util.hideLoading()
      util.showError(err.message)
    }
  },

  /**
   * 退出登录
   */
  async onLogout() {
    const confirmed = await util.showConfirm('确认退出登录？')
    if (!confirmed) return

    // 清除本地存储
    auth.logout()

    // 清除 WebSocket 连接
    const { wsManager } = require('../../utils/websocket')
    if (wsManager) {
      wsManager.close()
    }

    util.showSuccess('已退出登录')

    // 跳转到登录页
    wx.redirectTo({ url: '/pages/login/login' })
  },

  /**
   * 获取角色显示名称
   */
  getRoleName(role) {
    const roleMap = {
      admin: '系统管理员',
      operator: '操作员',
      viewer: '观察员'
    }
    return roleMap[role] || role
  }
})