/**
 * 设备列表页面
 * 支持搜索、分区筛选、扫码绑定设备
 */

const api = require('../../utils/api')
const auth = require('../../utils/auth')
const util = require('../../utils/util')
const { isAuthError } = require('../../utils/request')

Page({
  data: {
    devices: [],
    loading: true,
    loadingMore: false,
    total: 0,
    skip: 0,
    limit: 20,
    hasMore: true,

    // 筛选条件
    filter: {
      keyword: '',
      is_online: null,
      zone_id: null
    },

    // 分区列表
    zones: [],
    zonesLoading: false,
    showZoneFilter: false,

    // 状态筛选
    statusOptions: [
      { value: null, label: '全部' },
      { value: true, label: '在线' },
      { value: false, label: '离线' }
    ],
    selectedStatus: null,

    errorMsg: ''
  },

  onLoad() {
    if (!auth.isLoggedIn()) {
      wx.navigateTo({ url: '/pages/login/login' })
      return
    }

    // 加载分区列表（用于筛选）
    this.loadZones()
    this.loadDevices()
  },

  onShow() {
    if (auth.isLoggedIn() && this.data.devices.length === 0) {
      this.loadDevices()
    }
  },

  onPullDownRefresh() {
    this.data.skip = 0
    this.data.hasMore = true
    Promise.all([
      this.loadZones(),
      this.loadDevices()
    ]).then(() => wx.stopPullDownRefresh())
  },

  onReachBottom() {
    if (this.data.hasMore && !this.data.loadingMore) {
      this.loadMoreDevices()
    }
  },

  /**
   * 加载分区列表
   */
  async loadZones() {
    this.setData({ zonesLoading: true })

    try {
      const zones = await api.getZones()

      // 格式化分区列表，添加"全部"选项
      const formattedZones = [
        { id: null, name: '全部分区' },
        ...(zones || []).map(z => ({ id: z.id, name: z.name }))
      ]

      this.setData({
        zones: formattedZones,
        zonesLoading: false
      })
    } catch (err) {
      this.setData({ zonesLoading: false })
    }
  },

  /**
   * 加载设备列表
   */
  async loadDevices() {
    this.setData({ loading: true, errorMsg: '' })

    try {
      const params = {
        skip: 0,
        limit: this.data.limit
      }
      if (this.data.filter.keyword) params.keyword = this.data.filter.keyword
      if (this.data.filter.is_online !== null) params.is_online = this.data.filter.is_online
      if (this.data.filter.zone_id) params.zone_id = this.data.filter.zone_id

      const result = await api.getDevices(params)

      this.setData({
        devices: result.items || [],
        total: result.total || 0,
        skip: result.skip || 0,
        hasMore: (result.items || []).length < result.total,
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
   * 加载更多设备
   */
  async loadMoreDevices() {
    if (!this.data.hasMore) return

    this.setData({ loadingMore: true })

    try {
      const params = {
        skip: this.data.skip + this.data.limit,
        limit: this.data.limit
      }
      if (this.data.filter.keyword) params.keyword = this.data.filter.keyword
      if (this.data.filter.is_online !== null) params.is_online = this.data.filter.is_online
      if (this.data.filter.zone_id) params.zone_id = this.data.filter.zone_id

      const result = await api.getDevices(params)

      this.setData({
        devices: [...this.data.devices, ...result.items || []],
        total: result.total,
        skip: params.skip,
        hasMore: (result.items || []).length >= this.data.limit,
        loadingMore: false
      })
    } catch (err) {
      this.setData({ loadingMore: false })
      util.showError(err.message)
    }
  },

  /**
   * 点击设备卡片
   */
  onDeviceTap(e) {
    const device = e.detail.device
    wx.navigateTo({ url: `/pages/device-detail/device-detail?id=${device.id}` })
  },

  /**
   * 查看设备详情
   */
  onDeviceDetail(e) {
    const device = e.detail.device
    wx.navigateTo({ url: `/pages/device-detail/device-detail?id=${device.id}` })
  },

  /**
   * 搜索输入
   */
  onSearchInput(e) {
    this.setData({ 'filter.keyword': e.detail.value })
  },

  /**
   * 确认搜索
   */
  onSearchConfirm() {
    this.setData({ skip: 0, hasMore: true })
    this.loadDevices()
  },

  /**
   * 清除搜索
   */
  onClearSearch() {
    this.setData({ 'filter.keyword': '', skip: 0, hasMore: true })
    this.loadDevices()
  },

  /**
   * 状态筛选
   */
  onStatusFilter(e) {
    const status = e.currentTarget.dataset.status

    this.setData({
      'filter.is_online': status,
      selectedStatus: status,
      skip: 0,
      hasMore: true
    })

    this.loadDevices()
  },

  /**
   * 显示分区筛选
   */
  onShowZoneFilter() {
    this.setData({ showZoneFilter: true })
  },

  /**
   * 隐藏分区筛选
   */
  onHideZoneFilter() {
    this.setData({ showZoneFilter: false })
  },

  /**
   * 选择分区
   */
  onZoneSelect(e) {
    const zoneId = e.currentTarget.dataset.zoneId

    this.setData({
      'filter.zone_id': zoneId,
      skip: 0,
      hasMore: true,
      showZoneFilter: false
    })

    this.loadDevices()
  },

  /**
   * 扫码绑定设备
   */
  async onScanDevice() {
    try {
      const res = await wx.scanCode({
        scanType: ['barCode', 'qrCode'],
        onlyFromCamera: false
      })

      // 解析扫码结果（假设二维码/条码内容为设备ID）
      let deviceId = res.result

      // 如果是二维码URL格式，尝试提取设备ID
      if (deviceId.startsWith('http') || deviceId.startsWith('https')) {
        // 尝试从URL中提取设备ID
        const match = deviceId.match(/device[_-]?id=([^&]+)/i)
        if (match) {
          deviceId = match[1]
        } else {
          // 尝试从URL路径中提取
          const pathMatch = deviceId.match(/\/devices\/(\d+)/)
          if (pathMatch) {
            deviceId = pathMatch[1]
          }
        }
      }

      util.showLoading('查找设备...')

      // 查找设备
      const result = await api.getDevices({ keyword: deviceId, limit: 10 })
      const device = (result?.items || []).find(d =>
        d.device_id === deviceId ||
        String(d.id) === deviceId ||
        d.device_id.includes(deviceId)
      )

      util.hideLoading()

      if (device) {
        // 找到设备，跳转到详情页
        util.showSuccess('找到设备')
        wx.navigateTo({
          url: `/pages/device-detail/device-detail?id=${device.id}`
        })
      } else {
        // 未找到设备
        util.showInfo('未找到对应设备，请检查扫码结果')
      }
    } catch (err) {
      if (err.errMsg && err.errMsg.includes('cancel')) {
        // 用户取消扫码
        return
      }
      util.showError('扫码失败: ' + (err.errMsg || err.message))
    }
  }
})