/**
 * API 接口封装
 * 对应后端 RESTful API
 */

const { get, post, patch, del } = require('./request')

/**
 * 微信登录 API
 * @param {string} code - wx.login() 获取的 code
 * @returns {Promise<{access_token, token_type, is_new_user, user}>}
 */
function wechatLogin(code) {
  return post('/wechat/login', { code })
}

/**
 * 获取仪表盘统计数据
 * @returns {Promise<{total_devices, online_devices, offline_devices, total_alarms, unresolved_alarms}>}
 */
function getDashboardStats() {
  return get('/devices/stats')
}

/**
 * 获取设备列表
 * @param {object} params - 查询参数
 * @param {number} params.zone_id - 分区ID
 * @param {boolean} params.is_online - 是否在线
 * @param {string} params.keyword - 关键字搜索
 * @param {string} params.protocol_version - 协议版本
 * @param {number} params.skip - 跳过数量
 * @param {number} params.limit - 每页数量
 * @returns {Promise<{items: Array, total: number, skip: number, limit: number}>}
 */
function getDevices(params = {}) {
  return get('/devices', params)
}

/**
 * 获取设备详情
 * @param {number} deviceId - 设备ID
 * @returns {Promise<object>} - 设备详情
 */
function getDeviceDetail(deviceId) {
  return get(`/devices/${deviceId}`)
}

/**
 * 获取设备历史数据
 * @param {number} deviceId - 设备ID
 * @param {number} hours - 查询最近N小时数据
 * @returns {Promise<Array>}
 */
function getDeviceData(deviceId, hours = 24) {
  return get(`/devices/${deviceId}/data`, { hours })
}

/**
 * 获取设备开关机事件记录
 * @param {number} deviceId - 设备ID
 * @param {number} page - 页码
 * @param {number} pageSize - 每页数量
 * @returns {Promise<{supported, message, events, total, page, page_size}>}
 */
function getDeviceEvents(deviceId, page = 1, pageSize = 20) {
  return get(`/devices/${deviceId}/events`, { page, page_size: pageSize })
}

/**
 * 获取设备运行时间统计
 * @param {number} deviceId - 设备ID
 * @returns {Promise<{supported, message, today_runtime, month_runtime}>}
 */
function getDeviceRuntime(deviceId) {
  return get(`/devices/${deviceId}/runtime`)
}

/**
 * 获取设备参数列表
 * @param {number} deviceId - 设备ID
 * @returns {Promise<{version, params: Array, supported_codes: Array}>}
 */
function getDeviceParams(deviceId) {
  return get(`/devices/${deviceId}/params`)
}

/**
 * 设置单个设备参数
 * @param {number} deviceId - 设备ID
 * @param {string} paramCode - 参数编号
 * @param {any} paramValue - 参数值
 * @returns {Promise<{success, message, param_code, validation_errors}>}
 */
function setDeviceParam(deviceId, paramCode, paramValue) {
  return post(`/devices/${deviceId}/set-param`, {
    param_code: paramCode,
    param_value: paramValue
  })
}

/**
 * 控制设备（开机/关机）
 * @param {number} deviceId - 设备ID
 * @param {number} airstate - 0关机，1开机
 * @returns {Promise<{message}>}
 */
function controlDevice(deviceId, airstate) {
  return post(`/devices/${deviceId}/control`, { airstate })
}

/**
 * 获取分区列表
 * @returns {Promise<Array<{id, name, parent_id, description, sort_order, tenant_id, created_at}>>}
 */
function getZones() {
  return get('/zones')
}

/**
 * 获取单个告警详情
 * @param {number} alarmId - 告警ID
 * @returns {Promise<object>}
 */
function getAlarm(alarmId) {
  return get(`/alarms/${alarmId}`)
}

/**
 * 获取告警列表
 * @param {object} params - 查询参数
 * @param {boolean} params.is_resolved - 是否已处理
 * @param {string} params.severity - 严重程度
 * @param {string} params.type - 告警类型
 * @param {string} params.device_id - 设备ID
 * @param {number} params.skip - 跳过数量
 * @param {number} params.limit - 每页数量
 * @returns {Promise<Array>}
 */
function getAlarms(params = {}) {
  return get('/alarms', params)
}

/**
 * 处理单个告警
 * @param {number} alarmId - 告警ID
 * @returns {Promise<object>}
 */
function handleAlarm(alarmId) {
  return patch(`/alarms/${alarmId}/handle`)
}

/**
 * 批量处理告警
 * @param {Array<number>} alarmIds - 告警ID列表
 * @returns {Promise<{message, handled_count, invalid_ids}>}
 */
function batchHandleAlarms(alarmIds) {
  return patch('/alarms/batch-handle', { alarm_ids: alarmIds })
}

/**
 * 获取告警统计
 * @returns {Promise<{total_alarms, unresolved_alarms, resolved_alarms}>}
 */
function getAlarmStats() {
  return get('/alarms/stats')
}

/**
 * 获取分区授权列表（管理员）
 * @param {number} zoneId - 分区ID
 * @returns {Promise<Array<{id, zone_id, tenant_id, tenant_name, created_at}>>}
 */
function getZoneAuthorizations(zoneId) {
  return get(`/zones/${zoneId}/authorizations`)
}

/**
 * 授权分区给租户（管理员）
 * @param {number} zoneId - 分区ID
 * @param {number} tenantId - 租户ID
 * @returns {Promise<{id, zone_id, tenant_id, created_at}>}
 */
function authorizeZone(zoneId, tenantId) {
  return post(`/zones/${zoneId}/authorizations`, { tenant_id: tenantId })
}

/**
 * 移除分区授权（管理员）
 * @param {number} zoneId - 分区ID
 * @param {number} tenantId - 租户ID
 * @returns {Promise<{message}>}
 */
function removeZoneAuthorization(zoneId, tenantId) {
  return del(`/zones/${zoneId}/authorizations/${tenantId}`)
}

/**
 * 获取租户列表（管理员）
 * @returns {Promise<Array<{id, name, code, created_at}>>}
 */
function getTenants() {
  return get('/tenants')
}

/**
 * 获取当前用户信息
 * @returns {Promise<{id, username, role, tenant_id, tenant_name, is_active, created_at, wechat_openid}>}
 */
function getCurrentUser() {
  return get('/auth/me')
}

/**
 * 修改密码
 * @param {string} oldPassword - 旧密码
 * @param {string} newPassword - 新密码
 * @returns {Promise<{message}>}
 */
function changePassword(oldPassword, newPassword) {
  return post('/auth/change-password', {
    old_password: oldPassword,
    new_password: newPassword
  })
}

/**
 * 解绑微信
 * @returns {Promise<{message}>}
 */
function unbindWechat() {
  return post('/users/unbind-wechat')
}

// ========== 报表 API ==========

/**
 * 获取能耗统计报表
 * @param {object} params - 查询参数
 * @param {string} params.start_date - 开始日期 YYYY-MM-DD
 * @param {string} params.end_date - 结束日期 YYYY-MM-DD
 * @param {number} params.zone_id - 分区ID
 * @returns {Promise<Array<{device_id, device_name, total_runtime, energy_estimate}>>}
 */
function getEnergyStats(params = {}) {
  return get('/reports/energy', params)
}

/**
 * 获取温湿度趋势数据
 * @param {object} params - 查询参数
 * @param {string} params.start_date - 开始日期
 * @param {string} params.end_date - 结束日期
 * @param {number} params.device_id - 设备ID
 * @param {number} params.zone_id - 分区ID
 * @param {string} params.interval - 数据间隔 (1h, 6h, 1d)
 * @returns {Promise<{labels, temp_data, humi_data}>}
 */
function getTrendData(params = {}) {
  return get('/reports/trend', params)
}

/**
 * 获取告警统计报表
 * @param {object} params - 查询参数
 * @param {string} params.start_date - 开始日期
 * @param {string} params.end_date - 结束日期
 * @param {string} params.group_by - 分组方式 (type, severity, device)
 * @returns {Promise<{grouped_data, total_count, resolved_count, unresolved_count}>}
 */
function getAlarmReport(params = {}) {
  return get('/reports/alarms', params)
}

/**
 * 获取运行时长报表
 * @param {object} params - 查询参数
 * @param {string} params.start_date - 开始日期
 * @param {string} params.end_date - 结束日期
 * @param {number} params.zone_id - 分区ID
 * @param {number} params.limit - 返回数量限制
 * @returns {Promise<Array<{device_id, device_name, runtime_hours, percentage}>>}
 */
function getRuntimeStats(params = {}) {
  return get('/reports/runtime', params)
}

module.exports = {
  // 微信登录
  wechatLogin,

  // 仪表盘
  getDashboardStats,

  // 设备
  getDevices,
  getDeviceDetail,
  getDeviceData,
  getDeviceEvents,
  getDeviceRuntime,
  getDeviceParams,
  setDeviceParam,
  controlDevice,

  // 分区
  getZones,
  getZoneAuthorizations,
  authorizeZone,
  removeZoneAuthorization,

  // 租户
  getTenants,

  // 用户
  getCurrentUser,
  changePassword,
  unbindWechat,

  // 告警
  getAlarm,
  getAlarms,
  handleAlarm,
  batchHandleAlarms,
  getAlarmStats,

  // 报表
  getEnergyStats,
  getTrendData,
  getAlarmReport,
  getRuntimeStats
}