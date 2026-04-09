/**
 * Auth Store 测试
 * 使用 sessionStorage 进行安全存储
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import type { User } from '@/types'

// Mock secureStorage - 必须在工厂函数内部定义变量
vi.mock('@/utils/secureStorage', () => {
  const storage = {
    token: null as string | null,
    user: null as unknown,
    getToken: () => storage.token,
    setToken: (t: string | null) => { storage.token = t },
    setUser: (u: unknown) => { storage.user = u },
    getUser: () => storage.user,
    clear: () => { storage.token = null; storage.user = null },
    removeToken: () => { storage.token = null },
    removeUser: () => { storage.user = null },
    hasToken: () => storage.token !== null
  }
  return {
    secureStorage: storage
  }
})

// Mock auth API
vi.mock('@/api/auth', () => ({
  authApi: {
    login: vi.fn(),
    getCurrentUser: vi.fn()
  }
}))

import { useAuthStore } from '@/stores/auth'
import { authApi } from '@/api/auth'
import { secureStorage } from '@/utils/secureStorage'

describe('Auth Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
    secureStorage.clear()
  })

  describe('初始状态', () => {
    it('应初始化为未认证状态', () => {
      const store = useAuthStore()
      expect(store.isAuthenticated).toBe(false)
      expect(store.token).toBeNull()
      expect(store.user).toBeNull()
    })

    it('应初始化 loading 为 false', () => {
      const store = useAuthStore()
      expect(store.loading).toBe(false)
    })

    it('应初始化 error 为 null', () => {
      const store = useAuthStore()
      expect(store.error).toBeNull()
    })
  })

  describe('从 secureStorage 恢复状态', () => {
    it('有 token 时应恢复认证状态', () => {
      secureStorage.setToken('stored-token')
      const store = useAuthStore()
      expect(store.token).toBe('stored-token')
      expect(store.isAuthenticated).toBe(true)
    })

    it('有用户数据时应恢复用户信息', () => {
      const mockUser: User = {
        id: 1,
        username: 'testuser',
        role: 'admin',
        tenant_id: 1,
        is_active: true,
        created_at: '2024-01-01'
      }
      secureStorage.setUser(mockUser)
      const store = useAuthStore()
      expect(store.user).toEqual(mockUser)
    })
  })

  describe('计算属性', () => {
    it('isAuthenticated 应正确反映 token 状态', () => {
      const store = useAuthStore()
      expect(store.isAuthenticated).toBe(false)
      store.token = 'test-token'
      expect(store.isAuthenticated).toBe(true)
    })

    it('userRole 应返回用户角色', () => {
      const store = useAuthStore()
      expect(store.userRole).toBeNull()
      store.user = {
        id: 1,
        username: 'test',
        role: 'admin',
        tenant_id: 1,
        is_active: true,
        created_at: '2024-01-01'
      } as User
      expect(store.userRole).toBe('admin')
    })

    it('isAdmin 应正确判断管理员', () => {
      const store = useAuthStore()
      expect(store.isAdmin).toBe(false)
      store.user = {
        id: 1,
        username: 'test',
        role: 'admin',
        tenant_id: 1,
        is_active: true,
        created_at: '2024-01-01'
      } as User
      expect(store.isAdmin).toBe(true)
      store.user = {
        id: 1,
        username: 'test',
        role: 'viewer',
        tenant_id: 1,
        is_active: true,
        created_at: '2024-01-01'
      } as User
      expect(store.isAdmin).toBe(false)
    })
  })

  describe('login 方法', () => {
    it('登录成功应设置 token 和用户信息', async () => {
      const mockToken = { access_token: 'test-token', token_type: 'bearer' }
      const mockUser: User = {
        id: 1,
        username: 'testuser',
        role: 'admin',
        tenant_id: 1,
        is_active: true,
        created_at: '2024-01-01'
      }
      vi.mocked(authApi.login).mockResolvedValue(mockToken)
      vi.mocked(authApi.getCurrentUser).mockResolvedValue(mockUser)
      const store = useAuthStore()
      const result = await store.login({ username: 'testuser', password: 'password' })
      expect(result).toBe(true)
      expect(store.token).toBe('test-token')
      expect(store.user).toEqual(mockUser)
      expect(store.isAuthenticated).toBe(true)
      expect(store.loading).toBe(false)
      expect(store.error).toBeNull()
    })

    it('登录失败应设置错误信息', async () => {
      vi.mocked(authApi.login).mockRejectedValue(new Error('登录失败'))
      const store = useAuthStore()
      const result = await store.login({ username: 'testuser', password: 'wrong' })
      expect(result).toBe(false)
      expect(store.token).toBeNull()
      expect(store.user).toBeNull()
      expect(store.error).toBe('登录失败')
    })

    it('登录失败（非 Error 对象）应使用默认错误信息', async () => {
      vi.mocked(authApi.login).mockRejectedValue('some string error')
      const store = useAuthStore()
      const result = await store.login({ username: 'testuser', password: 'wrong' })
      expect(result).toBe(false)
      expect(store.error).toBe('登录失败')
    })

    it('登录过程中应设置 loading 状态', async () => {
      vi.mocked(authApi.login).mockImplementation(() =>
        new Promise(resolve => setTimeout(() => resolve({ access_token: 'test', token_type: 'bearer' }), 100))
      )
      const store = useAuthStore()
      const loginPromise = store.login({ username: 'test', password: 'pass' })
      expect(store.loading).toBe(true)
      await loginPromise
      expect(store.loading).toBe(false)
    })

    it('登录成功应保存到 secureStorage', async () => {
      const mockToken = { access_token: 'test-token', token_type: 'bearer' }
      const mockUser: User = {
        id: 1,
        username: 'testuser',
        role: 'admin',
        tenant_id: 1,
        is_active: true,
        created_at: '2024-01-01'
      }
      vi.mocked(authApi.login).mockResolvedValue(mockToken)
      vi.mocked(authApi.getCurrentUser).mockResolvedValue(mockUser)
      const store = useAuthStore()
      await store.login({ username: 'testuser', password: 'password' })
      expect(secureStorage.getToken()).toBe('test-token')
      expect(secureStorage.getUser()).toEqual(mockUser)
    })
  })

  describe('logout 方法', () => {
    it('登出应清除所有状态', () => {
      const store = useAuthStore()
      store.token = 'test-token'
      store.user = {
        id: 1,
        username: 'test',
        role: 'admin',
        tenant_id: 1,
        is_active: true,
        created_at: '2024-01-01'
      } as User
      store.logout()
      expect(store.token).toBeNull()
      expect(store.user).toBeNull()
      expect(store.isAuthenticated).toBe(false)
      expect(secureStorage.getToken()).toBeNull()
    })
  })

  describe('refreshUser 方法', () => {
    it('无 token 时不应刷新', async () => {
      const store = useAuthStore()
      store.token = null
      await store.refreshUser()
      expect(authApi.getCurrentUser).not.toHaveBeenCalled()
    })

    it('刷新成功应更新用户信息', async () => {
      const mockUser: User = {
        id: 1,
        username: 'testuser',
        role: 'admin',
        tenant_id: 1,
        is_active: true,
        created_at: '2024-01-01'
      }
      vi.mocked(authApi.getCurrentUser).mockResolvedValue(mockUser)
      const store = useAuthStore()
      store.token = 'test-token'
      await store.refreshUser()
      expect(store.user).toEqual(mockUser)
      expect(secureStorage.getUser()).toEqual(mockUser)
    })

    it('刷新失败应登出', async () => {
      vi.mocked(authApi.getCurrentUser).mockRejectedValue(new Error('Unauthorized'))
      const store = useAuthStore()
      store.token = 'test-token'
      store.user = {
        id: 1,
        username: 'test',
        role: 'admin',
        tenant_id: 1,
        is_active: true,
        created_at: '2024-01-01'
      } as User
      await store.refreshUser()
      expect(store.token).toBeNull()
      expect(store.user).toBeNull()
      expect(secureStorage.getToken()).toBeNull()
    })

    it('刷新失败（非 Error 对象）应登出', async () => {
      vi.mocked(authApi.getCurrentUser).mockRejectedValue('string error')
      const store = useAuthStore()
      store.token = 'test-token'
      await store.refreshUser()
      expect(store.token).toBeNull()
      expect(store.user).toBeNull()
    })
  })
})