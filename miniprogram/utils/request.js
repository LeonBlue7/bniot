/**
 * HTTP 请求封装
 * 支持 Token 自动注入、错误统一处理
 */

const app = getApp()
const { ERROR_CODES, ERROR_MESSAGES, isAuthError } = require('./errorCodes')

/**
 * 发起 HTTP 请求
 * @param {string} url - 请求路径（不含 baseUrl）
 * @param {object} options - 请求选项
 * @returns {Promise} - 返回 Promise
 */
function request(url, options = {}) {
  const baseUrl = app.globalData.baseUrl
  const token = app.globalData.token

  // 默认请求头
  const header = {
    'Content-Type': 'application/json',
    ...options.header
  }

  // 添加 Token
  if (token) {
    header['Authorization'] = `Bearer ${token}`
  }

  return new Promise((resolve, reject) => {
    wx.request({
      url: `${baseUrl}${url}`,
      method: options.method || 'GET',
      data: options.data,
      header: header,
      timeout: options.timeout || 10000,
      success: (res) => {
        // HTTP 状态码检查
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res.data)
        } else if (res.statusCode === 401) {
          // Token 过期或无效，清除登录状态
          app.clearLoginState()

          const error = new Error(ERROR_MESSAGES[ERROR_CODES.TOKEN_EXPIRED])
          error.code = ERROR_CODES.TOKEN_EXPIRED
          reject(error)

          // 跳转到登录页
          wx.navigateTo({
            url: '/pages/login/login'
          })
        } else if (res.statusCode === 404) {
          const error = new Error(ERROR_MESSAGES[ERROR_CODES.NOT_FOUND])
          error.code = ERROR_CODES.NOT_FOUND
          reject(error)
        } else if (res.statusCode >= 500) {
          const error = new Error(ERROR_MESSAGES[ERROR_CODES.SERVER_ERROR])
          error.code = ERROR_CODES.SERVER_ERROR
          reject(error)
        } else {
          // 其他错误（如 400 验证错误）
          const errorMsg = res.data?.detail || res.data?.message || ERROR_MESSAGES[ERROR_CODES.VALIDATION_ERROR]
          const error = new Error(errorMsg)
          error.code = ERROR_CODES.VALIDATION_ERROR
          reject(error)
        }
      },
      fail: (err) => {
        // 网络错误
        const error = new Error(ERROR_MESSAGES[ERROR_CODES.NETWORK_ERROR])
        error.code = ERROR_CODES.NETWORK_ERROR
        reject(error)
      }
    })
  })
}

/**
 * GET 请求
 * @param {string} url - 请求路径
 * @param {object} params - 查询参数
 * @returns {Promise}
 */
function get(url, params = {}) {
  // 构建查询字符串
  const queryString = Object.keys(params)
    .filter(key => params[key] !== undefined && params[key] !== null)
    .map(key => `${encodeURIComponent(key)}=${encodeURIComponent(params[key])}`)
    .join('&')

  const fullUrl = queryString ? `${url}?${queryString}` : url
  return request(fullUrl, { method: 'GET' })
}

/**
 * POST 请求
 * @param {string} url - 请求路径
 * @param {object} data - 请求体数据
 * @returns {Promise}
 */
function post(url, data = {}) {
  return request(url, { method: 'POST', data })
}

/**
 * PUT 请求
 * @param {string} url - 请求路径
 * @param {object} data - 请求体数据
 * @returns {Promise}
 */
function put(url, data = {}) {
  return request(url, { method: 'PUT', data })
}

/**
 * DELETE 请求
 * @param {string} url - 请求路径
 * @param {object} params - 查询参数（可选）
 * @returns {Promise}
 */
function del(url, params = null) {
  const options = { method: 'DELETE' }
  if (params) {
    options.params = params
  }
  return request(url, options)
}

/**
 * PATCH 请求
 * @param {string} url - 请求路径
 * @param {object} data - 请求体数据
 * @returns {Promise}
 */
function patch(url, data = {}) {
  return request(url, { method: 'PATCH', data })
}

module.exports = {
  request,
  get,
  post,
  put,
  del,
  patch,
  ERROR_CODES,
  isAuthError
}