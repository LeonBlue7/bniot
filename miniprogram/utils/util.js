/**
 * 通用工具函数
 */

/**
 * 格式化日期时间
 * @param {Date|string|number} date - 日期对象、字符串或时间戳
 * @param {string} format - 格式模板（默认：YYYY-MM-DD HH:mm:ss）
 * @returns {string}
 */
function formatDate(date, format = 'YYYY-MM-DD HH:mm:ss') {
  if (!date) return ''

  let d = date
  if (typeof date === 'string' || typeof date === 'number') {
    d = new Date(date)
  }

  if (!(d instanceof Date) || isNaN(d.getTime())) {
    return ''
  }

  const year = d.getFullYear()
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  const hours = String(d.getHours()).padStart(2, '0')
  const minutes = String(d.getMinutes()).padStart(2, '0')
  const seconds = String(d.getSeconds()).padStart(2, '0')

  return format
    .replace('YYYY', year)
    .replace('MM', month)
    .replace('DD', day)
    .replace('HH', hours)
    .replace('mm', minutes)
    .replace('ss', seconds)
}

/**
 * 格式化相对时间（多久之前）
 * @param {Date|string|number} date - 日期
 * @returns {string}
 */
function formatRelativeTime(date) {
  if (!date) return ''

  let d = date
  if (typeof date === 'string' || typeof date === 'number') {
    d = new Date(date)
  }

  if (!(d instanceof Date) || isNaN(d.getTime())) {
    return ''
  }

  const now = new Date()
  const diff = now - d // 毫秒差

  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)
  const days = Math.floor(diff / 86400000)

  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes}分钟前`
  if (hours < 24) return `${hours}小时前`
  if (days < 7) return `${days}天前`

  return formatDate(date, 'YYYY-MM-DD')
}

/**
 * 格式化温度显示
 * @param {number|null} temp - 温度值
 * @param {number} precision - 精度（默认1位小数）
 * @returns {string}
 */
function formatTemperature(temp, precision = 1) {
  if (temp === null || temp === undefined) return '--'
  return `${Number(temp).toFixed(precision)}°C`
}

/**
 * 格式化湿度显示
 * @param {number|null} humi - 湿度值
 * @param {number} precision - 精度（默认1位小数）
 * @returns {string}
 */
function formatHumidity(humi, precision = 1) {
  if (humi === null || humi === undefined) return '--'
  return `${Number(humi).toFixed(precision)}%`
}

/**
 * 格式化电流显示
 * @param {number|null} current - 电流值（单位：A）
 * @param {number} precision - 精度（默认3位小数）
 * @returns {string}
 */
function formatCurrent(current, precision = 3) {
  if (current === null || current === undefined) return '--'
  return `${Number(current).toFixed(precision)}A`
}

/**
 * 格式化运行时间
 * @param {number|null} hours - 运行时间（小时）
 * @returns {string}
 */
function formatRuntime(hours) {
  if (hours === null || hours === undefined) return '--'

  if (hours < 1) {
    const minutes = Math.floor(hours * 60)
    return `${minutes}分钟`
  }

  if (hours < 24) {
    return `${hours.toFixed(1)}小时`
  }

  const days = Math.floor(hours / 24)
  const remainHours = hours % 24
  return `${days}天${remainHours.toFixed(0)}小时`
}

/**
 * 获取在线状态文本
 * @param {boolean} isOnline - 是否在线
 * @returns {string}
 */
function getOnlineStatusText(isOnline) {
  return isOnline ? '在线' : '离线'
}

/**
 * 获取在线状态样式类名
 * @param {boolean} isOnline - 是否在线
 * @returns {string}
 */
function getOnlineStatusClass(isOnline) {
  return isOnline ? 'status-online' : 'status-offline'
}

/**
 * 获取告警严重程度文本
 * @param {string} severity - 严重程度
 * @returns {string}
 */
function getSeverityText(severity) {
  const map = {
    'critical': '严重',
    'warning': '警告',
    'info': '提示'
  }
  return map[severity] || severity
}

/**
 * 获取告警严重程度样式类名
 * @param {string} severity - 严重程度
 * @returns {string}
 */
function getSeverityClass(severity) {
  const map = {
    'critical': 'status-error',
    'warning': 'status-warning',
    'info': 'status-info'
  }
  return map[severity] || ''
}

/**
 * 获取空调状态文本
 * @param {number|null} airstate - 空调状态（0关机，1开机）
 * @returns {string}
 */
function getAirstateText(airstate) {
  if (airstate === null || airstate === undefined) return '--'
  return airstate === 1 ? '开机' : '关机'
}

/**
 * 显示加载提示
 * @param {string} title - 提示文字
 */
function showLoading(title = '加载中...') {
  wx.showLoading({
    title: title,
    mask: true
  })
}

/**
 * 隐藏加载提示
 */
function hideLoading() {
  wx.hideLoading()
}

/**
 * 显示成功提示
 * @param {string} title - 提示文字
 * @param {number} duration - 持续时间（毫秒）
 */
function showSuccess(title, duration = 1500) {
  wx.showToast({
    title: title,
    icon: 'success',
    duration: duration
  })
}

/**
 * 显示错误提示
 * @param {string} title - 提示文字
 * @param {number} duration - 持续时间（毫秒）
 */
function showError(title, duration = 2000) {
  wx.showToast({
    title: title,
    icon: 'error',
    duration: duration
  })
}

/**
 * 显示普通提示
 * @param {string} title - 提示文字
 * @param {number} duration - 持续时间（毫秒）
 */
function showInfo(title, duration = 1500) {
  wx.showToast({
    title: title,
    icon: 'none',
    duration: duration
  })
}

/**
 * 确认对话框
 * @param {string} content - 对话框内容
 * @param {string} title - 对话框标题
 * @returns {Promise<boolean>}
 */
function showConfirm(content, title = '提示') {
  return new Promise((resolve) => {
    wx.showModal({
      title: title,
      content: content,
      success: (res) => {
        resolve(res.confirm)
      },
      fail: () => {
        resolve(false)
      }
    })
  })
}

module.exports = {
  formatDate,
  formatRelativeTime,
  formatTemperature,
  formatHumidity,
  formatCurrent,
  formatRuntime,
  getOnlineStatusText,
  getOnlineStatusClass,
  getSeverityText,
  getSeverityClass,
  getAirstateText,
  showLoading,
  hideLoading,
  showSuccess,
  showError,
  showInfo,
  showConfirm
}