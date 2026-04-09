/**
 * WebSocket 连接管理器
 * 用于实时数据推送
 *
 * 安全认证：使用初始消息认证而非 URL 参数，避免 token 泄露到日志
 */
import { ref, type Ref } from 'vue'
import { wsLogger } from './logger'

export interface WebSocketMessage {
  type: string
  topic?: string
  device_id?: string
  data?: unknown
  timestamp?: string
  token?: string // 仅用于认证消息
}

export interface WebSocketOptions {
  url: string
  token: string
   
  onMessage?: (message: WebSocketMessage) => void
  onConnect?: () => void
  onDisconnect?: () => void
   
  onError?: (error: Event) => void
   
  onAuthError?: (message: string) => void
  reconnectAttempts?: number
  reconnectInterval?: number
  heartbeatInterval?: number
  authTimeout?: number
}

const DEFAULT_OPTIONS = {
  reconnectAttempts: 5,
  reconnectInterval: 3000,
  heartbeatInterval: 30000,
  authTimeout: 10000 // 10秒认证超时
}

export class WebSocketManager {
  private ws: WebSocket | null = null
  private options: Required<WebSocketOptions>
  private reconnectCount = 0
  private heartbeatTimer: number | null = null
  private isConnecting = false
  private authResolved = false

  public isConnected: Ref<boolean> = ref(false)
  public connectionError: Ref<string | null> = ref(null)

  constructor(options: WebSocketOptions) {
    this.options = { ...DEFAULT_OPTIONS, ...options } as Required<WebSocketOptions>
  }

  /**
   * 建立 WebSocket 连接（使用消息认证）
   */
  connect(): void {
    if (this.ws?.readyState === WebSocket.OPEN || this.isConnecting) {
      return
    }

    this.isConnecting = true
    this.connectionError.value = null
    this.authResolved = false

    try {
      // 连接 WebSocket（不带 token 参数）
      this.ws = new WebSocket(this.options.url)

      // 设置认证超时
      const authTimeoutId = window.setTimeout(() => {
        if (!this.authResolved) {
          wsLogger.error('认证超时')
          this.connectionError.value = '认证超时'
          this.isConnecting = false
          this.options.onAuthError?.('认证超时')
          this.ws?.close(4002, '认证超时')
        }
      }, this.options.authTimeout)

      this.ws.onopen = () => {
        wsLogger.debug('WebSocket 连接已打开，发送认证消息')

        // 发送认证消息
        this.send({
          type: 'auth',
          token: this.options.token
        })
      }

      this.ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data)

          // 处理认证成功消息
          if (message.type === 'connected') {
            clearTimeout(authTimeoutId)
            this.authResolved = true
            this.isConnecting = false
            this.reconnectCount = 0
            this.isConnected.value = true
            this.connectionError.value = null
            this.startHeartbeat()
            wsLogger.debug('认证成功，user_id:', message.data)
            this.options.onConnect?.()
            return
          }

          // 处理认证失败消息
          if (message.type === 'error' && !this.authResolved) {
            clearTimeout(authTimeoutId)
            wsLogger.error('认证失败:', message.data)
            this.connectionError.value = typeof message.data === 'string' ? message.data : '认证失败'
            this.isConnecting = false
            this.options.onAuthError?.(this.connectionError.value)
            this.ws?.close(4001, '认证失败')
            return
          }

          // 处理 pong 响应
          if (message.type === 'pong') {
            return
          }

          // 处理订阅成功消息
          if (message.type === 'subscribed') {
            wsLogger.debug('Subscribed to:', message.topic, message.device_id)
            return
          }

          // 处理取消订阅成功消息
          if (message.type === 'unsubscribed') {
            wsLogger.debug('Unsubscribed from:', message.topic, message.device_id)
            return
          }

          // 处理错误消息
          if (message.type === 'error') {
            wsLogger.error('WebSocket error:', message.data)
            return
          }

          this.options.onMessage?.(message)
        } catch {
          wsLogger.error('Failed to parse message:', event.data)
        }
      }

      this.ws.onclose = (event) => {
        clearTimeout(authTimeoutId)
        this.isConnecting = false
        this.isConnected.value = false
        this.authResolved = false
        this.stopHeartbeat()
        this.options.onDisconnect?.()

        // 非正常关闭时尝试重连（排除认证失败导致的关闭）
        if (event.code !== 1000 && event.code !== 4001 && this.reconnectCount < this.options.reconnectAttempts) {
          this.scheduleReconnect()
        }
      }

      this.ws.onerror = (error) => {
        clearTimeout(authTimeoutId)
        this.isConnecting = false
        this.connectionError.value = 'WebSocket 连接错误'
        this.options.onError?.(error)
      }
    } catch (error) {
      this.isConnecting = false
      this.connectionError.value = 'WebSocket 连接失败'
      wsLogger.error('Connection error:', error)
    }
  }

  /**
   * 断开连接
   */
  disconnect(): void {
    this.stopHeartbeat()
    if (this.ws) {
      this.ws.close(1000, 'User disconnect')
      this.ws = null
    }
    this.isConnected.value = false
  }

  /**
   * 发送消息
   */
  send(message: WebSocketMessage): boolean {
    if (this.ws?.readyState !== WebSocket.OPEN) {
      wsLogger.warn('WebSocket is not connected')
      return false
    }

    try {
      this.ws.send(JSON.stringify(message))
      return true
    } catch (error) {
      wsLogger.error('Failed to send message:', error)
      return false
    }
  }

  /**
   * 发送心跳 (ping)
   */
  sendPing(): void {
    this.send({ type: 'ping' })
  }

  /**
   * 订阅设备数据
   */
  subscribeDevice(deviceId: string): void {
    this.send({
      type: 'subscribe',
      topic: 'device',
      device_id: deviceId
    })
  }

  /**
   * 取消订阅设备数据
   */
  unsubscribeDevice(deviceId: string): void {
    this.send({
      type: 'unsubscribe',
      topic: 'device',
      device_id: deviceId
    })
  }

  /**
   * 订阅多个设备数据
   */
  subscribeDevices(deviceIds: string[]): void {
    deviceIds.forEach(id => this.subscribeDevice(id))
  }

  /**
   * 取消订阅多个设备数据
   */
  unsubscribeDevices(deviceIds: string[]): void {
    deviceIds.forEach(id => this.unsubscribeDevice(id))
  }

  /**
   * 订阅告警
   */
  subscribeAlarms(): void {
    this.send({
      type: 'subscribe',
      topic: 'alarm'
    })
  }

  /**
   * 取消订阅告警
   */
  unsubscribeAlarms(): void {
    this.send({
      type: 'unsubscribe',
      topic: 'alarm'
    })
  }

  /**
   * 订阅设备状态变化
   */
  subscribeDeviceStatus(deviceId: string): void {
    this.send({
      type: 'subscribe',
      topic: 'device_status',
      device_id: deviceId
    })
  }

  /**
   * 取消订阅设备状态变化
   */
  unsubscribeDeviceStatus(deviceId: string): void {
    this.send({
      type: 'unsubscribe',
      topic: 'device_status',
      device_id: deviceId
    })
  }

  /**
   * 开始心跳
   */
  private startHeartbeat(): void {
    this.stopHeartbeat()
    this.heartbeatTimer = window.setInterval(() => {
      this.sendPing()
    }, this.options.heartbeatInterval)
  }

  /**
   * 停止心跳
   */
  private stopHeartbeat(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer)
      this.heartbeatTimer = null
    }
  }

  /**
   * 计划重连
   */
  private scheduleReconnect(): void {
    this.reconnectCount++
    wsLogger.debug(`Reconnecting... (${this.reconnectCount}/${this.options.reconnectAttempts})`)

    setTimeout(() => {
      this.connect()
    }, this.options.reconnectInterval)
  }
}

// 全局 WebSocket 实例
let wsInstance: WebSocketManager | null = null

/**
 * 获取或创建 WebSocket 实例
 */
export function useWebSocket(options?: WebSocketOptions): WebSocketManager {
  if (!wsInstance && options) {
    wsInstance = new WebSocketManager(options)
  }
  return wsInstance!
}

/**
 * 断开 WebSocket 连接
 */
export function disconnectWebSocket(): void {
  wsInstance?.disconnect()
  wsInstance = null
}