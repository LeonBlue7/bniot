/**
 * WebSocket 工具测试
 * 测试消息认证流程
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { WebSocketManager, type WebSocketMessage } from '../utils/websocket'

// Mock WebSocket
class MockWebSocket {
  static CONNECTING = 0
  static OPEN = 1
  static CLOSING = 2
  static CLOSED = 3

  readyState = MockWebSocket.OPEN
  onopen: ((event: Event) => void) | null = null
  onmessage: ((event: MessageEvent) => void) | null = null
  onclose: ((event: CloseEvent) => void) | null = null
  onerror: ((event: Event) => void) | null = null

  constructor(public url: string) {
    // URL should NOT contain token (security check)
    expect(url).not.toContain('token')
    expect(url).not.toContain('test-token')

    setTimeout(() => {
      this.onopen?.(new Event('open'))
    }, 0)
  }

  send(data: string): void {
    // Verify auth message format
    const parsed = JSON.parse(data)
    if (parsed.type === 'auth') {
      // Simulate auth success response
      setTimeout(() => {
        this.onmessage?.(new MessageEvent('message', {
          data: JSON.stringify({
            type: 'connected',
            user_id: 1,
            tenant_id: 1
          })
        }))
      }, 5)
    }
  }

  close(code?: number, reason?: string): void {
    this.readyState = MockWebSocket.CLOSED
    this.onclose?.(new CloseEvent('close', { code, reason }))
  }
}

// Replace global WebSocket and timers
vi.stubGlobal('WebSocket', MockWebSocket)
vi.stubGlobal('setInterval', vi.fn(() => 1))
vi.stubGlobal('clearInterval', vi.fn())

describe('WebSocketManager', () => {
  let manager: WebSocketManager

  beforeEach(() => {
    vi.useFakeTimers()
    manager = new WebSocketManager({
      url: 'wss://example.com/api/ws',
      token: 'test-token',
      reconnectAttempts: 3,
      reconnectInterval: 100,
      heartbeatInterval: 1000,
      authTimeout: 10000
    })
  })

  afterEach(() => {
    manager.disconnect()
    vi.useRealTimers()
    vi.clearAllMocks()
  })

  describe('安全认证流程', () => {
    it('连接 URL 不应包含 token 参数', async () => {
      manager.connect()

      // 等待连接和认证完成
      await vi.runOnlyPendingTimersAsync()

      expect(manager.isConnected.value).toBe(true)
    })

    it('应在连接后发送 auth 消息', async () => {
      const mockSend = vi.fn()
      const originalSend = MockWebSocket.prototype.send
      MockWebSocket.prototype.send = mockSend

      manager.connect()
      await vi.runOnlyPendingTimersAsync()

      // 验证发送了认证消息
      const authCall = mockSend.mock.calls.find(call => {
        try {
          const data = JSON.parse(call[0])
          return data.type === 'auth' && data.token === 'test-token'
        } catch {
          return false
        }
      })
      expect(authCall).toBeDefined()

      MockWebSocket.prototype.send = originalSend
    })

    it('应在收到 connected 消息后完成认证', async () => {
      const onConnect = vi.fn()
      manager = new WebSocketManager({
        url: 'wss://example.com/api/ws',
        token: 'test-token',
        onConnect,
        authTimeout: 10000
      })

      manager.connect()
      await vi.runOnlyPendingTimersAsync()

      expect(manager.isConnected.value).toBe(true)
      expect(onConnect).toHaveBeenCalled()
    })

    it('应处理认证失败', async () => {
      vi.useRealTimers()

      // 创建自定义 MockWebSocket 返回认证失败
      class AuthFailMockWebSocket extends MockWebSocket {
        send(data: string): void {
          const parsed = JSON.parse(data)
          if (parsed.type === 'auth') {
            setTimeout(() => {
              this.onmessage?.(new MessageEvent('message', {
                data: JSON.stringify({
                  type: 'error',
                  data: '无效的认证令牌'
                })
              }))
              // 然后关闭连接
              setTimeout(() => {
                this.readyState = MockWebSocket.CLOSED
                this.onclose?.(new CloseEvent('close', { code: 4001, reason: '认证失败' }))
              }, 5)
            }, 5)
          }
        }
      }

      vi.stubGlobal('WebSocket', AuthFailMockWebSocket)

      const onAuthError = vi.fn()
      manager = new WebSocketManager({
        url: 'wss://example.com/api/ws',
        token: 'invalid-token',
        onAuthError,
        authTimeout: 10000
      })

      manager.connect()

      // 等待认证失败
      await new Promise(resolve => setTimeout(resolve, 20))

      expect(manager.isConnected.value).toBe(false)
      expect(onAuthError).toHaveBeenCalledWith('无效的认证令牌')

      vi.stubGlobal('WebSocket', MockWebSocket)
    })

    it('应处理认证超时', async () => {
      vi.useRealTimers()

      // 创建不响应认证的 MockWebSocket
      class NoResponseMockWebSocket extends MockWebSocket {
        send(data: string): void {
          // 不发送任何响应
        }
      }

      vi.stubGlobal('WebSocket', NoResponseMockWebSocket)

      const onAuthError = vi.fn()
      manager = new WebSocketManager({
        url: 'wss://example.com/api/ws',
        token: 'test-token',
        onAuthError,
        authTimeout: 100 // 100ms 超时
      })

      manager.connect()

      // 等待超时
      await new Promise(resolve => setTimeout(resolve, 150))

      expect(manager.isConnected.value).toBe(false)
      expect(onAuthError).toHaveBeenCalledWith('认证超时')

      vi.stubGlobal('WebSocket', MockWebSocket)
    })
  })

  describe('消息处理', () => {
    beforeEach(async () => {
      vi.useFakeTimers()
      manager.connect()
      await vi.runOnlyPendingTimersAsync()
    })

    afterEach(() => {
      manager.disconnect()
      vi.useRealTimers()
    })

    it('应处理 device_data 消息', async () => {
      const onMessage = vi.fn()
      manager = new WebSocketManager({
        url: 'wss://example.com/api/ws',
        token: 'test-token',
        onMessage
      })

      manager.connect()
      await vi.runOnlyPendingTimersAsync()

      const message: WebSocketMessage = {
        type: 'device_data',
        device_id: 'device_001',
        data: { temp: 25.5 }
      }
      manager['ws']?.onmessage?.(new MessageEvent('message', {
        data: JSON.stringify(message)
      }))

      expect(onMessage).toHaveBeenCalledWith(message)
    })

    it('应处理 alarm 消息', async () => {
      const onMessage = vi.fn()
      manager = new WebSocketManager({
        url: 'wss://example.com/api/ws',
        token: 'test-token',
        onMessage
      })

      manager.connect()
      await vi.runOnlyPendingTimersAsync()

      const message: WebSocketMessage = {
        type: 'alarm',
        data: { type: 'offline', device_id: 'alarm_device_001' }
      }
      manager['ws']?.onmessage?.(new MessageEvent('message', {
        data: JSON.stringify(message)
      }))

      expect(onMessage).toHaveBeenCalledWith(message)
    })

    it('应发送 ping 消息', async () => {
      const sendSpy = vi.spyOn(manager, 'send')
      manager.sendPing()
      expect(sendSpy).toHaveBeenCalledWith({ type: 'ping' })
    })

    it('应发送 subscribe device 消息', async () => {
      const sendSpy = vi.spyOn(manager, 'send')
      manager.subscribeDevice('device_001')
      expect(sendSpy).toHaveBeenCalledWith({
        type: 'subscribe',
        topic: 'device',
        device_id: 'device_001'
      })
    })

    it('应发送 unsubscribe device 消息', async () => {
      const sendSpy = vi.spyOn(manager, 'send')
      manager.unsubscribeDevice('device_001')
      expect(sendSpy).toHaveBeenCalledWith({
        type: 'unsubscribe',
        topic: 'device',
        device_id: 'device_001'
      })
    })

    it('应发送 subscribe alarms 消息', async () => {
      const sendSpy = vi.spyOn(manager, 'send')
      manager.subscribeAlarms()
      expect(sendSpy).toHaveBeenCalledWith({
        type: 'subscribe',
        topic: 'alarm'
      })
    })

    it('应发送 subscribe device_status 消息', async () => {
      const sendSpy = vi.spyOn(manager, 'send')
      manager.subscribeDeviceStatus('device_001')
      expect(sendSpy).toHaveBeenCalledWith({
        type: 'subscribe',
        topic: 'device_status',
        device_id: 'device_001'
      })
    })

    it('未连接时发送消息应失败', async () => {
      manager.disconnect()
      const result = manager.send({ type: 'ping' })
      expect(result).toBe(false)
    })

    it('应正确断开连接', async () => {
      vi.useFakeTimers()
      const onDisconnect = vi.fn()
      manager = new WebSocketManager({
        url: 'wss://example.com/api/ws',
        token: 'test-token',
        onDisconnect
      })

      manager.connect()
      await vi.runOnlyPendingTimersAsync()

      manager.disconnect()

      expect(manager.isConnected.value).toBe(false)
      expect(onDisconnect).toHaveBeenCalled()
    })

    it('应忽略 pong 消息', async () => {
      vi.useFakeTimers()
      const onMessage = vi.fn()
      manager = new WebSocketManager({
        url: 'wss://example.com/api/ws',
        token: 'test-token',
        onMessage
      })

      manager.connect()
      await vi.runOnlyPendingTimersAsync()

      manager['ws']?.onmessage?.(new MessageEvent('message', {
        data: JSON.stringify({ type: 'pong' })
      }))

      expect(onMessage).not.toHaveBeenCalled()
    })

    it('应忽略 subscribed 消息', async () => {
      vi.useFakeTimers()
      const onMessage = vi.fn()
      manager = new WebSocketManager({
        url: 'wss://example.com/api/ws',
        token: 'test-token',
        onMessage
      })

      manager.connect()
      await vi.runOnlyPendingTimersAsync()

      manager['ws']?.onmessage?.(new MessageEvent('message', {
        data: JSON.stringify({ type: 'subscribed', topic: 'device', device_id: 'device_001' })
      }))

      expect(onMessage).not.toHaveBeenCalled()
    })

    it('应处理 error 消息（仅记录日志，不设置 connectionError）', async () => {
      vi.useFakeTimers()
      manager.connect()
      await vi.runOnlyPendingTimersAsync()

      // 认证后的 error 消息只记录日志，不设置 connectionError
      // connectionError 只用于认证失败和连接错误
      manager['ws']?.onmessage?.(new MessageEvent('message', {
        data: JSON.stringify({ type: 'error', data: 'Test error' })
      }))

      // connectionError 应保持 null（因为这是认证后的错误，不是连接错误）
      expect(manager.connectionError.value).toBe(null)
    })

    it('应订阅多个设备', async () => {
      vi.useFakeTimers()
      manager.connect()
      await vi.runOnlyPendingTimersAsync()

      const sendSpy = vi.spyOn(manager, 'send')
      manager.subscribeDevices(['device_001', 'device_002'])

      expect(sendSpy).toHaveBeenCalledTimes(2)
      expect(sendSpy).toHaveBeenCalledWith({
        type: 'subscribe',
        topic: 'device',
        device_id: 'device_001'
      })
      expect(sendSpy).toHaveBeenCalledWith({
        type: 'subscribe',
        topic: 'device',
        device_id: 'device_002'
      })
    })
  })
})