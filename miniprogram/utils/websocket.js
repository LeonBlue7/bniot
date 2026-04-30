/**
 * WebSocket 连接管理模块
 * 用于实时数据推送
 *
 * 功能：
 * 1. WebSocket 连接建立与认证
 * 2. 心跳机制保持连接
 * 3. 断线自动重连
 * 4. 设备数据订阅与接收
 * 5. 告警实时推送
 *
 * 使用方法：
 * const ws = new WebSocketManager()
 * ws.connect(token)
 * ws.subscribeDevice(deviceId)
 * ws.on('device_data', callback)
 * ws.on('alarm', callback)
 */

// 获取 app 实例（延迟获取避免循环引用）
let app = null
function getAppInstance() {
  if (!app) {
    try {
      app = getApp()
    } catch (e) {
      // 非 App 环境使用默认配置
    }
  }
  return app
}

// WebSocket 配置
const WS_CONFIG = {
  // WebSocket 服务器地址（从 app.globalData 获取或使用默认）
  baseUrl: 'wss://www.jxbonner.cloud:5000/api/ws',
  // 心跳间隔（秒）
  heartbeatInterval: 30,
  // 重连间隔（秒）
  reconnectInterval: 5,
  // 最大重连次数
  maxReconnectAttempts: 5,
  // 认证超时（秒）
  authTimeout: 10,
  // 连接超时（秒）
  connectionTimeout: 15,
  // 调试模式
  debug: false
}

// 动态获取 WebSocket URL
function getWebSocketUrl() {
  const appInstance = getAppInstance()
  if (appInstance && appInstance.globalData && appInstance.globalData.wsUrl) {
    return appInstance.globalData.wsUrl
  }
  return WS_CONFIG.baseUrl
}

// 条件化日志
function log(message, ...args) {
  if (WS_CONFIG.debug) {
    console.log('[WebSocket]', message, ...args)
  }
}

function logError(message, ...args) {
  if (WS_CONFIG.debug) {
    console.error('[WebSocket]', message, ...args)
  }
}

function logWarn(message, ...args) {
  if (WS_CONFIG.debug) {
    console.warn('[WebSocket]', message, ...args)
  }
}

// WebSocket 状态
const WS_STATE = {
  DISCONNECTED: 'disconnected',
  CONNECTING: 'connecting',
  AUTHENTICATING: 'authenticating',
  CONNECTED: 'connected',
  RECONNECTING: 'reconnecting'
}

class WebSocketManager {
  constructor() {
    // WebSocket 连接实例
    this.ws = null
    // 当前状态
    this.state = WS_STATE.DISCONNECTED
    // 用户 token
    this.token = null
    // 订阅列表
    this.subscriptions = {
      devices: new Set(),
      alarms: false
    }
    // 事件监听器（使用 ID 管理）
    this.listeners = {}
    this.listenerId = 0
    // 心跳定时器
    this.heartbeatTimer = null
    // 重连定时器
    this.reconnectTimer = null
    // 重连次数
    this.reconnectAttempts = 0
    // 是否手动关闭
    this.manualClose = false
  }

  /**
   * 建立 WebSocket 连接
   * @param {string} token - JWT 认证令牌
   * @returns {Promise<boolean>} - 连接是否成功
   */
  connect(token) {
    return new Promise((resolve, reject) => {
      if (this.state === WS_STATE.CONNECTED) {
        resolve(true)
        return
      }

      this.token = token
      this.manualClose = false
      this.state = WS_STATE.CONNECTING

      // 连接超时定时器
      const connectionTimeoutTimer = setTimeout(() => {
        if (this.state === WS_STATE.CONNECTING) {
          logError('连接超时')
          this.close()
          reject(new Error('WebSocket 连接超时'))
        }
      }, WS_CONFIG.connectionTimeout * 1000)

      // 获取动态 WebSocket URL
      const wsUrl = getWebSocketUrl()

      // 创建 WebSocket 连接
      this.ws = wx.connectSocket({
        url: wsUrl,
        success: () => {
          log('连接建立成功')
        },
        fail: (err) => {
          clearTimeout(connectionTimeoutTimer)
          logError('连接建立失败:', err)
          this.state = WS_STATE.DISCONNECTED
          reject(new Error('WebSocket 连接失败'))
        }
      })

      // 监听 WebSocket 事件
      this.setupListeners(resolve, reject, connectionTimeoutTimer)
    })
  }

  /**
   * 设置 WebSocket 事件监听
   */
  setupListeners(resolve, reject, connectionTimeoutTimer) {
    // 连接打开
    wx.onSocketOpen(() => {
      clearTimeout(connectionTimeoutTimer)
      log('连接已打开')
      this.state = WS_STATE.AUTHENTICATING

      // 发送认证消息
      this.sendAuthMessage()
        .then(() => resolve(true))
        .catch((err) => reject(err))
    })

    // 接收消息
    wx.onSocketMessage((res) => {
      this.handleMessage(res.data)
    })

    // 连接错误
    wx.onSocketError((err) => {
      clearTimeout(connectionTimeoutTimer)
      logError('连接错误:', err)
      this.handleDisconnect()
    })

    // 连接关闭
    wx.onSocketClose((res) => {
      clearTimeout(connectionTimeoutTimer)
      log('连接关闭:', res)
      this.handleDisconnect()
    })
  }

  /**
   * 发送认证消息
   */
  async sendAuthMessage() {
    // 发送认证消息
    this.send({
      type: 'auth',
      token: this.token
    })

    // 设置认证超时
    return new Promise((resolve, reject) => {
      const timeout = setTimeout(() => {
        reject(new Error('认证超时'))
        this.close()
      }, WS_CONFIG.authTimeout * 1000)

      // 监听认证结果（通过 once 事件）
      this.once('connected', () => {
        clearTimeout(timeout)
        this.state = WS_STATE.CONNECTED
        this.reconnectAttempts = 0
        this.startHeartbeat()
        this.restoreSubscriptions()
        resolve(true)
      })

      this.once('error', (err) => {
        clearTimeout(timeout)
        reject(new Error(err.message || '认证失败'))
        this.close()
      })
    })
  }

  /**
   * 处理接收的消息
   * @param {string} data - 接收的消息数据
   */
  handleMessage(data) {
    try {
      const message = JSON.parse(data)
      log('收到消息:', message.type)

      switch (message.type) {
        case 'connected':
          // 认证成功
          this.emit('connected', message)
          break

        case 'error':
          // 错误消息
          logError('服务端错误:', message.message)
          this.emit('error', message)
          break

        case 'pong':
          // 心跳响应
          this.handlePong()
          break

        case 'subscribed':
          // 订阅成功
          log('订阅成功:', message.topic, message.device_id)
          break

        case 'unsubscribed':
          // 取消订阅成功
          log('取消订阅:', message.topic, message.device_id)
          break

        case 'device_data':
          // 设备数据推送
          this.emit('device_data', message.data)
          break

        case 'alarm':
          // 告警推送
          this.emit('alarm', message.data)
          break

        case 'device_status':
          // 设备状态变化
          this.emit('device_status', message.data)
          break

        default:
          logWarn('未知的消息类型:', message.type)
      }
    } catch (e) {
      logError('消息解析失败:', e)
    }
  }

  /**
   * 处理断开连接
   */
  handleDisconnect() {
    // 停止心跳
    this.stopHeartbeat()

    // 清理重连定时器
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }

    // 如果不是手动关闭，尝试重连
    if (!this.manualClose && this.reconnectAttempts < WS_CONFIG.maxReconnectAttempts) {
      this.state = WS_STATE.RECONNECTING
      this.reconnectAttempts++
      log(`尝试重连 (${this.reconnectAttempts}/${WS_CONFIG.maxReconnectAttempts})`)

      this.reconnectTimer = setTimeout(() => {
        this.connect(this.token)
          .then(() => {
            log('重连成功')
          })
          .catch((err) => {
            logError('重连失败:', err)
          })
      }, WS_CONFIG.reconnectInterval * 1000)
    } else {
      this.state = WS_STATE.DISCONNECTED
      this.emit('disconnected')
    }
  }

  /**
   * 发送心跳消息
   */
  startHeartbeat() {
    this.stopHeartbeat()

    this.heartbeatTimer = setInterval(() => {
      if (this.state === WS_STATE.CONNECTED) {
        this.send({ type: 'ping' })
      }
    }, WS_CONFIG.heartbeatInterval * 1000)
  }

  /**
   * 停止心跳
   */
  stopHeartbeat() {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer)
      this.heartbeatTimer = null
    }
  }

  /**
   * 处理心跳响应
   */
  handlePong() {
    // 心跳响应，连接正常
  }

  /**
   * 发送消息
   * @param {object} message - 要发送的消息
   */
  send(message) {
    if (this.ws && this.state !== WS_STATE.DISCONNECTED) {
      wx.sendSocketMessage({
        data: JSON.stringify(message),
        success: () => {
          log('发送消息成功:', message.type)
        },
        fail: (err) => {
          logError('发送消息失败:', err)
        }
      })
    } else {
      logWarn('未连接，无法发送消息')
    }
  }

  /**
   * 订阅设备数据
   * @param {string} deviceId - 设备 ID
   */
  subscribeDevice(deviceId) {
    if (this.state !== WS_STATE.CONNECTED) {
      logWarn('未连接，无法订阅')
      return
    }

    if (!this.subscriptions.devices.has(deviceId)) {
      this.subscriptions.devices.add(deviceId)
      this.send({
        type: 'subscribe',
        topic: 'device',
        device_id: deviceId
      })
    }
  }

  /**
   * 取消订阅设备数据
   * @param {string} deviceId - 设备 ID
   */
  unsubscribeDevice(deviceId) {
    if (this.state !== WS_STATE.CONNECTED) {
      return
    }

    if (this.subscriptions.devices.has(deviceId)) {
      this.subscriptions.devices.delete(deviceId)
      this.send({
        type: 'unsubscribe',
        topic: 'device',
        device_id: deviceId
      })
    }
  }

  /**
   * 订阅告警推送
   */
  subscribeAlarms() {
    if (this.state !== WS_STATE.CONNECTED) {
      logWarn('未连接，无法订阅')
      return
    }

    if (!this.subscriptions.alarms) {
      this.subscriptions.alarms = true
      this.send({
        type: 'subscribe',
        topic: 'alarm'
      })
    }
  }

  /**
   * 取消订阅告警
   */
  unsubscribeAlarms() {
    if (this.state !== WS_STATE.CONNECTED) {
      return
    }

    if (this.subscriptions.alarms) {
      this.subscriptions.alarms = false
      this.send({
        type: 'unsubscribe',
        topic: 'alarm'
      })
    }
  }

  /**
   * 重连后恢复订阅
   */
  restoreSubscriptions() {
    // 恢复设备订阅
    this.subscriptions.devices.forEach((deviceId) => {
      this.send({
        type: 'subscribe',
        topic: 'device',
        device_id: deviceId
      })
    })

    // 恢复告警订阅
    if (this.subscriptions.alarms) {
      this.send({
        type: 'subscribe',
        topic: 'alarm'
      })
    }
  }

  /**
   * 关闭 WebSocket 连接
   */
  close() {
    this.manualClose = true
    this.stopHeartbeat()

    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }

    if (this.ws) {
      wx.closeSocket()
      this.ws = null
    }

    this.state = WS_STATE.DISCONNECTED
    this.subscriptions.devices.clear()
    this.subscriptions.alarms = false
  }

  /**
   * 获取当前状态
   */
  getState() {
    return this.state
  }

  /**
   * 是否已连接
   */
  isConnected() {
    return this.state === WS_STATE.CONNECTED
  }

  // ========== 事件系统 ==========

  /**
   * 注册事件监听
   * @param {string} event - 事件名称
   * @param {function} callback - 回调函数
   * @returns {number} - 监听器 ID（用于移除监听）
   */
  on(event, callback) {
    if (!this.listeners[event]) {
      this.listeners[event] = {}
    }
    const id = ++this.listenerId
    this.listeners[event][id] = callback
    return id
  }

  /**
   * 移除事件监听
   * @param {string} event - 事件名称
   * @param {number} listenerId - 监听器 ID
   */
  off(event, listenerId) {
    if (this.listeners[event] && listenerId) {
      delete this.listeners[event][listenerId]
    }
  }

  /**
   * 注册一次性事件监听
   * @param {string} event - 事件名称
   * @param {function} callback - 回调函数
   * @returns {number} - 监听器 ID
   */
  once(event, callback) {
    const id = this.on(event, (data) => {
      callback(data)
      this.off(event, id)
    })
    return id
  }

  /**
   * 触发事件
   * @param {string} event - 事件名称
   * @param {*} data - 事件数据
   */
  emit(event, data) {
    if (this.listeners[event]) {
      Object.values(this.listeners[event]).forEach(callback => {
        try {
          callback(data)
        } catch (e) {
          logError(`事件回调错误 (${event}):`, e)
        }
      })
    }
  }

  /**
   * 移除所有事件监听器
   */
  removeAllListeners() {
    this.listeners = {}
  }
}

// 创建单例实例
const wsManager = new WebSocketManager()

module.exports = {
  WebSocketManager,
  wsManager,
  WS_STATE,
  WS_CONFIG,
  getWebSocketUrl,
  // 条件化日志函数
  setDebug: (debug) => { WS_CONFIG.debug = debug }
}