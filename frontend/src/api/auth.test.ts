/**
 * Auth API 测试
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import MockAdapter from 'axios-mock-adapter'
import apiClient from './client'
import { authApi } from './auth'
import type { Token, User } from '@/types'

// Mock auth store
const mockLogout = vi.fn()
let mockToken: string | null = null

vi.mock('@/stores/auth', () => ({
  useAuthStore: vi.fn(() => ({
    get token() { return mockToken },
    logout: mockLogout
  }))
}))

describe('Auth API', () => {
  let mockAxios: MockAdapter

  beforeEach(() => {
    setActivePinia(createPinia())
    mockAxios = new MockAdapter(apiClient)
    vi.clearAllMocks()
    mockToken = null
  })

  afterEach(() => {
    mockAxios.restore()
  })

  describe('login', () => {
    it('应使用 form-urlencoded 格式发送登录请求', async () => {
      const mockToken: Token = {
        access_token: 'test-access-token',
        token_type: 'bearer'
      }

      mockAxios.onPost('/auth/login').reply((config) => {
        // 验证 Content-Type
        expect(config.headers?.['Content-Type']).toContain('application/x-www-form-urlencoded')
        // 验证数据格式
        expect(config.data).toContain('username=testuser')
        expect(config.data).toContain('password=testpass')
        return [200, mockToken]
      })

      const result = await authApi.login({
        username: 'testuser',
        password: 'testpass'
      })

      expect(result.access_token).toBe('test-access-token')
      expect(result.token_type).toBe('bearer')
    })

    it('登录成功应返回 token', async () => {
      const mockToken: Token = {
        access_token: 'valid-token',
        token_type: 'bearer'
      }

      mockAxios.onPost('/auth/login').reply(200, mockToken)

      const result = await authApi.login({
        username: 'admin',
        password: 'password123'
      })

      expect(result).toEqual(mockToken)
    })

    it('登录失败应抛出错误', async () => {
      mockAxios.onPost('/auth/login').reply(401, { detail: 'Incorrect username or password' })

      await expect(authApi.login({
        username: 'wrong',
        password: 'wrong'
      })).rejects.toThrow()
    })

    it('网络错误应抛出错误', async () => {
      mockAxios.onPost('/auth/login').networkError()

      await expect(authApi.login({
        username: 'test',
        password: 'test'
      })).rejects.toThrow()
    })

    it('服务器错误应抛出错误', async () => {
      mockAxios.onPost('/auth/login').reply(500, { detail: 'Internal Server Error' })

      await expect(authApi.login({
        username: 'test',
        password: 'test'
      })).rejects.toThrow()
    })

    it('特殊字符用户名应正确编码', async () => {
      const mockToken: Token = {
        access_token: 'token',
        token_type: 'bearer'
      }

      mockAxios.onPost('/auth/login').reply((config) => {
        // 验证特殊字符被 URL 编码
        expect(config.data).toContain('username=user%40test')
        return [200, mockToken]
      })

      await authApi.login({
        username: 'user@test',
        password: 'pass'
      })
    })

    it('密码包含特殊字符应正确编码', async () => {
      const mockToken: Token = {
        access_token: 'token',
        token_type: 'bearer'
      }

      mockAxios.onPost('/auth/login').reply((config) => {
        expect(config.data).toContain('password=pass%40word')
        return [200, mockToken]
      })

      await authApi.login({
        username: 'user',
        password: 'pass@word'
      })
    })
  })

  describe('getCurrentUser', () => {
    it('应返回当前用户信息', async () => {
      const mockUser: User = {
        id: 1,
        username: 'admin',
        role: 'admin',
        tenant_id: 1,
        is_active: true,
        created_at: '2024-01-01T00:00:00Z'
      }

      mockAxios.onGet('/auth/me').reply(200, mockUser)

      const result = await authApi.getCurrentUser()

      expect(result).toEqual(mockUser)
    })

    it('未认证应抛出 401 错误', async () => {
      mockAxios.onGet('/auth/me').reply(401, { detail: 'Not authenticated' })

      await expect(authApi.getCurrentUser()).rejects.toThrow()
    })

    it('token 过期应抛出错误', async () => {
      mockAxios.onGet('/auth/me').reply(401, { detail: 'Token expired' })

      await expect(authApi.getCurrentUser()).rejects.toThrow()
    })

    it('服务器错误应抛出错误', async () => {
      mockAxios.onGet('/auth/me').reply(500)

      await expect(authApi.getCurrentUser()).rejects.toThrow()
    })

    it('网络错误应抛出错误', async () => {
      mockAxios.onGet('/auth/me').networkError()

      await expect(authApi.getCurrentUser()).rejects.toThrow()
    })
  })
})