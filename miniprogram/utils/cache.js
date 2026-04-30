/**
 * 数据缓存工具
 * 用于缓存设备数据、告警数据等，减少网络请求
 */

const CACHE_PREFIX = 'bniot_cache_'
const DEFAULT_EXPIRE = 5 * 60 * 1000  // 默认缓存 5 分钟

// 开发模式下输出日志
const DEBUG = false

function logError(msg, err) {
  if (DEBUG) {
    console.error(msg, err)
  }
}

/**
 * 设置缓存
 * @param {string} key - 缓存键
 * @param {any} data - 缓存数据
 * @param {number} expire - 过期时间（毫秒），默认 5 分钟
 */
function setCache(key, data, expire = DEFAULT_EXPIRE) {
  try {
    const cacheData = {
      data: data,
      timestamp: Date.now(),
      expire: expire
    }
    wx.setStorageSync(CACHE_PREFIX + key, cacheData)
  } catch (err) {
    logError('缓存设置失败:', err)
  }
}

/**
 * 获取缓存
 * @param {string} key - 缓存键
 * @returns {any|null} - 缓存数据，过期或不存在返回 null
 */
function getCache(key) {
  try {
    const cacheData = wx.getStorageSync(CACHE_PREFIX + key)

    if (!cacheData) return null

    // 检查是否过期
    const now = Date.now()
    if (now - cacheData.timestamp > cacheData.expire) {
      // 过期，删除缓存
      wx.removeStorageSync(CACHE_PREFIX + key)
      return null
    }

    return cacheData.data
  } catch (err) {
    logError('缓存读取失败:', err)
    return null
  }
}

/**
 * 删除缓存
 * @param {string} key - 缓存键
 */
function removeCache(key) {
  try {
    wx.removeStorageSync(CACHE_PREFIX + key)
  } catch (err) {
    logError('缓存删除失败:', err)
  }
}

/**
 * 清除所有缓存
 */
function clearAllCache() {
  try {
    const info = wx.getStorageInfoSync()
    const keys = info.keys || []

    keys.forEach(key => {
      if (key.startsWith(CACHE_PREFIX)) {
        wx.removeStorageSync(key)
      }
    })
  } catch (err) {
    logError('清除缓存失败:', err)
  }
}

/**
 * 获取缓存状态
 * @returns {object} - 缓存统计信息
 */
function getCacheStatus() {
  try {
    const info = wx.getStorageInfoSync()
    const keys = (info.keys || []).filter(k => k.startsWith(CACHE_PREFIX))

    return {
      count: keys.length,
      totalKeys: info.keys?.length || 0,
      totalSize: info.currentSize || 0,
      limitSize: info.limitSize || 0
    }
  } catch (err) {
    logError('获取缓存状态失败:', err)
    return { count: 0 }
  }
}

/**
 * 带缓存的 API 请求包装器
 * @param {Function} apiFunc - API 函数
 * @param {string} cacheKey - 缓存键
 * @param {Object} options - 配置选项
 * @param {number} options.expire - 过期时间
 * @param {boolean} options.forceRefresh - 强制刷新（忽略缓存）
 * @returns {Promise<any>}
 */
async function withCache(apiFunc, cacheKey, options = {}) {
  const { expire = DEFAULT_EXPIRE, forceRefresh = false } = options

  // 如果不是强制刷新，先尝试从缓存获取
  if (!forceRefresh) {
    const cachedData = getCache(cacheKey)
    if (cachedData !== null) {
      return cachedData
    }
  }

  // 调用 API 获取数据
  const data = await apiFunc()

  // 设置缓存
  if (data !== null && data !== undefined) {
    setCache(cacheKey, data, expire)
  }

  return data
}

/**
 * 缓存键生成器
 */
const CacheKeys = {
  // 设备相关
  deviceList: (params) => `devices_${JSON.stringify(params)}`,
  deviceDetail: (id) => `device_${id}`,
  deviceParams: (id) => `device_params_${id}`,
  deviceData: (id, hours) => `device_data_${id}_${hours}`,

  // 告警相关
  alarmList: (params) => `alarms_${JSON.stringify(params)}`,
  alarmStats: () => 'alarm_stats',

  // 分区相关
  zoneList: () => 'zones',

  // 仪表盘
  dashboardStats: () => 'dashboard_stats'
}

module.exports = {
  setCache,
  getCache,
  removeCache,
  clearAllCache,
  getCacheStatus,
  withCache,
  CacheKeys,
  DEFAULT_EXPIRE
}