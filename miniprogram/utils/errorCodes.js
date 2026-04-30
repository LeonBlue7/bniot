/**
 * 错误码常量定义
 * 用于统一前后端错误判断
 */

const ERROR_CODES = {
  // 认证相关
  TOKEN_EXPIRED: 'TOKEN_EXPIRED',
  UNAUTHORIZED: 'UNAUTHORIZED',
  INVALID_TOKEN: 'INVALID_TOKEN',

  // 网络相关
  NETWORK_ERROR: 'NETWORK_ERROR',
  TIMEOUT: 'TIMEOUT',

  // 业务相关
  NOT_FOUND: 'NOT_FOUND',
  VALIDATION_ERROR: 'VALIDATION_ERROR',
  SERVER_ERROR: 'SERVER_ERROR'
}

/**
 * 错误消息映射
 */
const ERROR_MESSAGES = {
  [ERROR_CODES.TOKEN_EXPIRED]: '登录已过期，请重新登录',
  [ERROR_CODES.UNAUTHORIZED]: '未授权，请先登录',
  [ERROR_CODES.INVALID_TOKEN]: '无效的登录凭证',
  [ERROR_CODES.NETWORK_ERROR]: '网络请求失败，请检查网络连接',
  [ERROR_CODES.TIMEOUT]: '请求超时，请重试',
  [ERROR_CODES.NOT_FOUND]: '资源不存在',
  [ERROR_CODES.VALIDATION_ERROR]: '数据验证失败',
  [ERROR_CODES.SERVER_ERROR]: '服务器错误，请稍后重试'
}

/**
 * 判断是否为认证错误
 * @param {string} errorCode - 错误码
 * @returns {boolean}
 */
function isAuthError(errorCode) {
  return [
    ERROR_CODES.TOKEN_EXPIRED,
    ERROR_CODES.UNAUTHORIZED,
    ERROR_CODES.INVALID_TOKEN
  ].includes(errorCode)
}

/**
 * 获取错误消息
 * @param {string} errorCode - 错误码
 * @returns {string}
 */
function getErrorMessage(errorCode) {
  return ERROR_MESSAGES[errorCode] || '未知错误'
}

module.exports = {
  ERROR_CODES,
  ERROR_MESSAGES,
  isAuthError,
  getErrorMessage
}