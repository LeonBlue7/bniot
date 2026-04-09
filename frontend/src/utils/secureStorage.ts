/**
 * 安全存储工具
 * 使用 sessionStorage 替代 localStorage 存储 token
 * sessionStorage 特点：
 * 1. 页面关闭后数据自动清除，减少 XSS 攻击窗口
 * 2. 数据不会持久化到磁盘，减少数据泄露风险
 * 3. 仅在当前标签页可用，避免跨标签页数据共享
 */

// 存储键名（不包含敏感信息提示）
const TOKEN_KEY = 'bniot_token_secure'
const USER_KEY = 'bniot_user_secure'

/**
 * 内存存储降级方案
 * 当 sessionStorage 不可用时使用
 */
class MemoryStorage {
  private store: Map<string, string> = new Map()

  getItem(key: string): string | null {
    return this.store.get(key) || null
  }

  setItem(key: string, value: string): void {
    this.store.set(key, value)
  }

  removeItem(key: string): void {
    this.store.delete(key)
  }

  clear(): void {
    this.store.clear()
  }
}

/**
 * 检查 sessionStorage 是否可用
 */
function isSessionStorageAvailable(): boolean {
  try {
    if (typeof window === 'undefined' || !window.sessionStorage) {
      return false
    }
    // 测试读写能力
    const testKey = '__storage_test__'
    window.sessionStorage.setItem(testKey, 'test')
    window.sessionStorage.removeItem(testKey)
    return true
  } catch {
    return false
  }
}

/**
 * 获取可用存储实例
 */
function getStorage(): Storage | MemoryStorage {
  return isSessionStorageAvailable() ? window.sessionStorage : new MemoryStorage()
}

/**
 * 安全存储接口
 */
interface SecureStorageInterface {
  getToken(): string | null
   
  setToken(token: string | null): void
  removeToken(): void
  hasToken(): boolean
  getUser<T = unknown>(): T | null
   
  setUser<T>(user: T | null): void
  removeUser(): void
  clear(): void
}

/**
 * 创建安全存储实例
 */
export function createSecureStorage(): SecureStorageInterface {
  const storage = getStorage()

  return {
    getToken(): string | null {
      try {
        return storage.getItem(TOKEN_KEY)
      } catch {
        return null
      }
    },

    setToken(token: string | null): void {
      if (!token || token === '') {
        this.removeToken()
        return
      }
      try {
        storage.setItem(TOKEN_KEY, token)
      } catch {
        // 存储失败，忽略（内存存储不会失败）
      }
    },

    removeToken(): void {
      try {
        storage.removeItem(TOKEN_KEY)
      } catch {
        // 移除失败，忽略
      }
    },

    hasToken(): boolean {
      return this.getToken() !== null && this.getToken() !== ''
    },

    getUser<T = unknown>(): T | null {
      try {
        const data = storage.getItem(USER_KEY)
        if (!data) return null
        return JSON.parse(data) as T
      } catch {
        // JSON 解析失败
        return null
      }
    },

    setUser<T>(user: T | null): void {
      if (!user) {
        this.removeUser()
        return
      }
      try {
        storage.setItem(USER_KEY, JSON.stringify(user))
      } catch {
        // 存储失败，忽略
      }
    },

    removeUser(): void {
      try {
        storage.removeItem(USER_KEY)
      } catch {
        // 移除失败，忽略
      }
    },

    clear(): void {
      this.removeToken()
      this.removeUser()
    }
  }
}

/**
 * 默认安全存储实例
 */
export const secureStorage = createSecureStorage()