/**
 * CSRF 保护工具测试
 * 测试 CSRF Token 获取和验证逻辑
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { csrfProtection, fetchCsrfToken, getCsrfToken, clearCsrfToken, createCsrfProtectedFetch } from './csrf'

describe('csrf - CSRF 保护工具', () => {
  beforeEach(() => {
    clearCsrfToken()
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  describe('CSRF Token 管理', () => {
    it('初始状态应无 token', () => {
      expect(getCsrfToken()).toBeNull()
    })

    it('应能设置 CSRF Token', () => {
      csrfProtection.setToken('csrf-token-123')
      expect(getCsrfToken()).toBe('csrf-token-123')
    })

    it('应能清除 CSRF Token', () => {
      csrfProtection.setToken('test-token')
      clearCsrfToken()
      expect(getCsrfToken()).toBeNull()
    })
  })

  describe('fetchCsrfToken 函数', () => {
    it('应从 API 获取 CSRF Token', async () => {
      const mockFetch = vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ csrf_token: 'new-csrf-token' })
      })
      vi.stubGlobal('fetch', mockFetch)

      const token = await fetchCsrfToken()

      expect(mockFetch).toHaveBeenCalledWith('/api/auth/csrf-token', {
        method: 'GET',
        credentials: 'same-origin'
      })
      expect(token).toBe('new-csrf-token')
    })

    it('API 失败应返回 null', async () => {
      const mockFetch = vi.fn().mockResolvedValue({
        ok: false,
        status: 500
      })
      vi.stubGlobal('fetch', mockFetch)

      const token = await fetchCsrfToken()

      expect(token).toBeNull()
    })

    it('网络错误应返回 null', async () => {
      const mockFetch = vi.fn().mockRejectedValue(new Error('Network error'))
      vi.stubGlobal('fetch', mockFetch)

      const token = await fetchCsrfToken()

      expect(token).toBeNull()
    })

    it('响应缺少 csrf_token 字段应返回 null', async () => {
      const mockFetch = vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ message: 'success' })
      })
      vi.stubGlobal('fetch', mockFetch)

      const token = await fetchCsrfToken()

      expect(token).toBeNull()
    })
  })

  describe('请求拦截', () => {
    it('应为请求添加 CSRF Token 头', async () => {
      csrfProtection.setToken('test-csrf-token')

      const headers = csrfProtection.getHeaders()

      expect(headers['X-CSRF-Token']).toBe('test-csrf-token')
    })

    it('无 token 时头应为空', () => {
      clearCsrfToken()

      const headers = csrfProtection.getHeaders()

      expect(headers['X-CSRF-Token']).toBeUndefined()
    })
  })

  describe('Token 刷新', () => {
    it('应能刷新 CSRF Token', async () => {
      const mockFetch = vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ csrf_token: 'refreshed-token' })
      })
      vi.stubGlobal('fetch', mockFetch)

      const success = await csrfProtection.refreshToken()

      expect(success).toBe(true)
      expect(getCsrfToken()).toBe('refreshed-token')
    })

    it('刷新失败应保持原 token', async () => {
      csrfProtection.setToken('original-token')
      const mockFetch = vi.fn().mockRejectedValue(new Error('Network error'))
      vi.stubGlobal('fetch', mockFetch)

      const success = await csrfProtection.refreshToken()

      expect(success).toBe(false)
      expect(getCsrfToken()).toBe('original-token')
    })
  })

  describe('安全验证', () => {
    it('应验证 CSRF Token 格式', () => {
      expect(csrfProtection.isValidToken('valid-token-123')).toBe(true)
      expect(csrfProtection.isValidToken('')).toBe(false)
      expect(csrfProtection.isValidToken(null)).toBe(false)
      expect(csrfProtection.isValidToken(undefined)).toBe(false)
    })

    it('Token 长度应合理', () => {
      // Token 应至少有一定长度（防止简单攻击）
      expect(csrfProtection.isValidToken('short')).toBe(false)
      expect(csrfProtection.isValidToken('a-very-long-secure-token-12345')).toBe(true)
    })
  })

  describe('clearToken 方法', () => {
    it('应能通过 clearToken 清除 token', () => {
      csrfProtection.setToken('test-token')
      expect(getCsrfToken()).toBe('test-token')
      csrfProtection.clearToken()
      expect(getCsrfToken()).toBeNull()
    })
  })

  describe('createCsrfProtectedFetch', () => {
    it('应创建带有 CSRF 保护的 fetch 函数', async () => {
      const mockFetch = vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ csrf_token: 'new-token' })
      })
      vi.stubGlobal('fetch', mockFetch)

      csrfProtection.setToken('existing-token')
      const protectedFetch = createCsrfProtectedFetch()

      await protectedFetch('/api/test', { method: 'POST' })

      // 验证请求包含 CSRF 头
      expect(mockFetch).toHaveBeenCalled()
      const callArgs = mockFetch.mock.calls[0]
      expect(callArgs[1].headers).toBeDefined()

      vi.unstubAllGlobals()
    })

    it('无 token 时应先获取 CSRF Token', async () => {
      clearCsrfToken()

      const mockFetch = vi.fn()
      // 第一次调用获取 CSRF Token
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ csrf_token: 'new-csrf-token' })
      })
      // 第二次调用是实际请求
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ data: 'test' })
      })

      vi.stubGlobal('fetch', mockFetch)

      const protectedFetch = createCsrfProtectedFetch()
      await protectedFetch('/api/test')

      // 应先获取 CSRF Token
      expect(mockFetch).toHaveBeenCalledTimes(2)
      expect(mockFetch.mock.calls[0][0]).toBe('/api/auth/csrf-token')

      vi.unstubAllGlobals()
    })

    it('应合并现有请求头', async () => {
      const mockFetch = vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ csrf_token: 'token' })
      })
      vi.stubGlobal('fetch', mockFetch)

      csrfProtection.setToken('test-csrf-token')
      const protectedFetch = createCsrfProtectedFetch()

      const existingHeaders = new Headers()
      existingHeaders.set('Content-Type', 'application/json')

      await protectedFetch('/api/test', { headers: existingHeaders })

      const callArgs = mockFetch.mock.calls[0]
      const headers = callArgs[1].headers as Headers
      expect(headers.get('Content-Type')).toBe('application/json')
      expect(headers.get('X-CSRF-Token')).toBe('test-csrf-token')

      vi.unstubAllGlobals()
    })
  })
})