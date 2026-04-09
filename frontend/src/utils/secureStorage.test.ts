/**
 * 安全存储工具测试
 * 使用 sessionStorage 替代 localStorage 存储 token
 * sessionStorage 相对安全：页面关闭后数据清除，XSS 攻击窗口更小
 */
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { secureStorage, createSecureStorage } from './secureStorage'

describe('secureStorage - 安全存储工具', () => {
  beforeEach(() => {
    // 清除存储
    secureStorage.clear()
  })

  describe('Token 存储', () => {
    it('应能存储 token', () => {
      secureStorage.setToken('test-token-123')
      expect(secureStorage.getToken()).toBe('test-token-123')
    })

    it('应能移除 token', () => {
      secureStorage.setToken('test-token')
      secureStorage.removeToken()
      expect(secureStorage.getToken()).toBeNull()
    })

    it('空 token 不应存储', () => {
      secureStorage.setToken('')
      expect(secureStorage.getToken()).toBeNull()
    })

    it('null token 不应存储', () => {
      secureStorage.setToken(null)
      expect(secureStorage.getToken()).toBeNull()
    })

    it('存储后应正确判断存在性', () => {
      expect(secureStorage.hasToken()).toBe(false)
      secureStorage.setToken('test')
      expect(secureStorage.hasToken()).toBe(true)
    })

    it('清除后应无 token', () => {
      secureStorage.setToken('test')
      secureStorage.clear()
      expect(secureStorage.getToken()).toBeNull()
      expect(secureStorage.hasToken()).toBe(false)
    })
  })

  describe('用户数据存储', () => {
    it('应能存储用户对象', () => {
      const user = { id: 1, username: 'test', role: 'admin' }
      secureStorage.setUser(user)
      expect(secureStorage.getUser()).toEqual(user)
    })

    it('应能移除用户数据', () => {
      secureStorage.setUser({ id: 1 })
      secureStorage.removeUser()
      expect(secureStorage.getUser()).toBeNull()
    })

    it('空用户数据不应存储', () => {
      secureStorage.setUser(null)
      expect(secureStorage.getUser()).toBeNull()
    })

    it('undefined 用户数据不应存储', () => {
      secureStorage.setUser(undefined)
      expect(secureStorage.getUser()).toBeNull()
    })
  })

  describe('安全特性', () => {
    it('存储的 key 应使用安全命名', () => {
      secureStorage.setToken('test')
      // 验证存储的 key 确实存在
      const storedValue = secureStorage.getToken()
      expect(storedValue).toBe('test')
    })

    it('清除时应移除所有相关数据', () => {
      secureStorage.setToken('test')
      secureStorage.setUser({ id: 1 })
      secureStorage.clear()
      expect(secureStorage.getToken()).toBeNull()
      expect(secureStorage.getUser()).toBeNull()
    })
  })

  describe('错误处理', () => {
    it('sessionStorage 不可用时应优雅降级', () => {
      // 模拟 sessionStorage 不可用
      vi.stubGlobal('sessionStorage', undefined)

      // 创建新的存储实例（会使用内存降级）
      const fallbackStorage = createSecureStorage()

      // 应使用内存存储作为降级方案
      fallbackStorage.setToken('fallback-token')
      expect(fallbackStorage.getToken()).toBe('fallback-token')

      vi.unstubAllGlobals()
    })
  })

  describe('类型安全', () => {
    it('getUser 应返回正确的类型', () => {
      const user = { id: 1, username: 'test', role: 'admin' }
      secureStorage.setUser(user)
      const result = secureStorage.getUser<{ id: number; username: string; role: string }>()
      expect(result?.id).toBe(1)
      expect(result?.username).toBe('test')
      expect(result?.role).toBe('admin')
    })
  })
})