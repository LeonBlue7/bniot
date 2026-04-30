/**
 * 分区列表页面
 * 包含：分区列表、分区授权管理（管理员）
 */

const api = require('../../utils/api')
const auth = require('../../utils/auth')
const util = require('../../utils/util')

Page({
  data: {
    zones: [],
    loading: true,
    errorMsg: '',
    isAdmin: false,

    // 授权管理弹窗
    showAuthModal: false,
    currentZone: null,
    authorizations: [],
    authLoading: false,

    // 租户列表（用于授权）
    tenants: [],
    showTenantPicker: false
  },

  onLoad() {
    if (!auth.isLoggedIn()) {
      wx.navigateTo({ url: '/pages/login/login' })
      return
    }

    // 判断用户角色
    const user = auth.getUserInfo()
    const isAdmin = user && user.role === 'admin'
    this.setData({ isAdmin })

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

  /**
   * 加载分区列表
   */
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

  /**
   * 分区点击
   */
  onZoneTap(e) {
    const zone = e.currentTarget.dataset.zone

    // 管理员：显示授权管理
    if (this.data.isAdmin) {
      this.showAuthorizationModal(zone)
    } else {
      // 普通用户：显示分区信息
      util.showInfo(`分区: ${zone.name}`)
    }
  },

  /**
   * 显示授权管理弹窗
   */
  async showAuthorizationModal(zone) {
    this.setData({
      showAuthModal: true,
      currentZone: zone,
      authorizations: [],
      authLoading: true
    })

    try {
      // 加载授权列表
      const authList = await api.getZoneAuthorizations(zone.id)
      this.setData({
        authorizations: authList || [],
        authLoading: false
      })
    } catch (err) {
      this.setData({ authLoading: false })
      util.showError(err.message)
    }
  },

  /**
   * 隐藏授权管理弹窗
   */
  onHideAuthModal() {
    this.setData({
      showAuthModal: false,
      currentZone: null,
      authorizations: [],
      showTenantPicker: false
    })
  },

  /**
   * 加载租户列表
   */
  async loadTenants() {
    try {
      const tenants = await api.getTenants()
      this.setData({ tenants: tenants || [] })
    } catch (err) {
      util.showError('加载租户列表失败')
    }
  },

  /**
   * 显示租户选择器
   */
  onShowTenantPicker() {
    if (this.data.tenants.length === 0) {
      this.loadTenants()
    }
    this.setData({ showTenantPicker: true })
  },

  /**
   * 隐藏租户选择器
   */
  onHideTenantPicker() {
    this.setData({ showTenantPicker: false })
  },

  /**
   * 选择租户进行授权
   */
  async onTenantSelect(e) {
    const tenantId = e.currentTarget.dataset.tenantId
    const tenant = this.data.tenants.find(t => t.id === tenantId)

    // 检查是否已授权
    const existing = this.data.authorizations.find(a => a.tenant_id === tenantId)
    if (existing) {
      util.showInfo('该租户已授权此分区')
      this.setData({ showTenantPicker: false })
      return
    }

    const confirmed = await util.showConfirm(`确认授权分区给 ${tenant.name}？`)
    if (!confirmed) return

    util.showLoading('授权中...')

    try {
      await api.authorizeZone(this.data.currentZone.id, tenantId)
      util.hideLoading()
      util.showSuccess('授权成功')

      // 刷新授权列表
      const authList = await api.getZoneAuthorizations(this.data.currentZone.id)
      this.setData({
        authorizations: authList || [],
        showTenantPicker: false
      })
    } catch (err) {
      util.hideLoading()
      util.showError(err.message)
    }
  },

  /**
   * 移除授权
   */
  async onRemoveAuth(e) {
    const tenantId = e.currentTarget.dataset.tenantId
    const auth = this.data.authorizations.find(a => a.tenant_id === tenantId)

    const confirmed = await util.showConfirm(`确认移除 ${auth.tenant_name} 的授权？`)
    if (!confirmed) return

    util.showLoading('移除中...')

    try {
      await api.removeZoneAuthorization(this.data.currentZone.id, tenantId)
      util.hideLoading()
      util.showSuccess('授权已移除')

      // 刷新授权列表
      const authList = await api.getZoneAuthorizations(this.data.currentZone.id)
      this.setData({ authorizations: authList || [] })
    } catch (err) {
      util.hideLoading()
      util.showError(err.message)
    }
  }
})