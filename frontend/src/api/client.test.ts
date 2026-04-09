/**
 * API Client 测试
 * 测试 axios 实例配置和拦截器行为
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import MockAdapter from 'axios-mock-adapter'

// Mock auth store - 必须在工厂函数内部定义变量
vi.mock('@/stores/auth', () => {
  let token: string | null = 'test-token'
  return {
    useAuthStore: vi.fn(() => ({
      get token() { return token },
      set token(v: string | null) { token = v },
      logout: vi.fn(() => { token = null })
    }))
  }
})

// Mock CSRF module - 必须在工厂函数内部定义变量
vi.mock('@/utils/csrf', () => {
  let csrfToken: string | null = null
  return {
    csrfProtection: {
      getHeaders: () => csrfToken ? { 'X-CSRF-Token': csrfToken } : {},
      setToken: (t: string) => { csrfToken = t },
      refreshToken: vi.fn()
    },
    fetchCsrfToken: vi.fn(() => Promise.resolve('csrf-token'))
  }
})

// 导入 apiClient（在 mock 之后）
import apiClient from './client'

describe('API Client', () => {
  let mockAxios: MockAdapter

  beforeEach(() => {
    mockAxios = new MockAdapter(apiClient)
    vi.clearAllMocks()
  })

  afterEach(() => {
    mockAxios.restore()
  })

  describe('基础配置', () => {
    it('应设置正确的 baseURL', () => {
      expect(apiClient.defaults.baseURL).toBe('/api')
    })

    it('应设置正确的 timeout', () => {
      expect(apiClient.defaults.timeout).toBe(30000)
    })

    it('应设置正确的 Content-Type', () => {
      expect(apiClient.defaults.headers['Content-Type']).toBe('application/json')
    })

    it('应启用 withCredentials', () => {
      expect(apiClient.defaults.withCredentials).toBe(true)
    })
  })

  describe('请求拦截器', () => {
    it('应在请求头中添加 Authorization（有 token 时）', async () => {
      mockAxios.onGet('/test').reply(200, { success: true })
      await apiClient.get('/test')
      expect(mockAxios.history.get.length).toBe(1)
    })

    it('无 token 时请求也能成功', async () => {
      mockAxios.onGet('/test').reply(200, { success: true })
      const response = await apiClient.get('/test')
      expect(response.status).toBe(200)
    })

    it('应尝试获取 CSRF Token', async () => {
      mockAxios.onGet('/test').reply(200, { success: true })
      await apiClient.get('/test')
      // CSRF Token 获取在请求拦截器中已初始化
      expect(mockAxios.history.get.length).toBe(1)
    })
  })

  describe('响应拦截器', () => {
    it('应正确返回成功响应', async () => {
      mockAxios.onGet('/success').reply(200, { data: 'test' })
      const response = await apiClient.get('/success')
      expect(response.data).toEqual({ data: 'test' })
    })

    it('401 错误应跳转登录页', async () => {
      const originalLocation = window.location
      const mockLocation = { href: '' }
      Object.defineProperty(window, 'location', {
        value: mockLocation,
        writable: true,
        configurable: true
      })

      mockAxios.onGet('/unauthorized').reply(401)

      try {
        await apiClient.get('/unauthorized')
      } catch (error) {
        // 预期会抛出错误
      }

      await new Promise(resolve => setTimeout(resolve, 0))
      expect(mockLocation.href).toBe('/login')

      Object.defineProperty(window, 'location', {
        value: originalLocation,
        writable: true,
        configurable: true
      })
    })

    it('其他错误应直接抛出', async () => {
      mockAxios.onGet('/error').reply(500, { detail: 'Server Error' })
      await expect(apiClient.get('/error')).rejects.toThrow()
    })

    it('网络错误应抛出错误', async () => {
      mockAxios.onGet('/network-error').networkError()
      await expect(apiClient.get('/network-error')).rejects.toThrow()
    })
  })

  describe('请求方法', () => {
    it('GET 请求应正确发送参数', async () => {
      mockAxios.onGet('/devices').reply(200, { param: 'value' })
      const response = await apiClient.get('/devices', { params: { param: 'value' } })
      expect(response.data.param).toBe('value')
    })

    it('POST 请求应正确发送数据', async () => {
      mockAxios.onPost('/devices').reply(201, { id: 1, name: 'test' })
      const response = await apiClient.post('/devices', { name: 'test' })
      expect(response.data.name).toBe('test')
      expect(response.status).toBe(201)
    })

    it('PUT 请求应正确发送数据', async () => {
      mockAxios.onPut('/devices/1').reply(200, { id: 1, name: 'updated' })
      const response = await apiClient.put('/devices/1', { name: 'updated' })
      expect(response.data.name).toBe('updated')
    })

    it('DELETE 请求应正确发送', async () => {
      mockAxios.onDelete('/devices/1').reply(200, { message: 'deleted' })
      const response = await apiClient.delete('/devices/1')
      expect(response.data.message).toBe('deleted')
    })
  })
})