/**
 * CSRF 保护工具
 * 用于防止跨站请求伪造攻击
 */

import { apiLogger } from './logger'


// 最小 Token 长度（防止简单攻击）
const MIN_TOKEN_LENGTH = 8

/**
 * CSRF Token 存储（内存中）
 * 不使用 sessionStorage，因为 CSRF Token 需要跨页面共享
 */
let csrfToken: string | null = null

/**
 * 获取当前 CSRF Token
 */
export function getCsrfToken(): string | null {
  return csrfToken
}

/**
 * 设置 CSRF Token
 */
function setCsrfToken(token: string | null): void {
  csrfToken = token
}

/**
 * 清除 CSRF Token
 */
export function clearCsrfToken(): void {
  csrfToken = null
}

/**
 * 从 API 获取 CSRF Token
 * 需要后端配合提供 /api/auth/csrf-token 接口
 */
export async function fetchCsrfToken(): Promise<string | null> {
  try {
    const response = await fetch('/api/auth/csrf-token', {
      method: 'GET',
      credentials: 'same-origin' // 包含 cookies
    })

    if (!response.ok) {
      return null
    }

    const data = await response.json()

    if (data.csrf_token) {
      setCsrfToken(data.csrf_token)
      return data.csrf_token
    }

    return null
  } catch (error) {
    // 网络错误或其他异常
    apiLogger.error('Failed to fetch CSRF token:', error)
    return null
  }
}

/**
 * 验证 CSRF Token 格式
 */
function isValidToken(token: string | null | undefined): boolean {
  if (!token || typeof token !== 'string') {
    return false
  }

  // Token 应至少有一定长度
  if (token.length < MIN_TOKEN_LENGTH) {
    return false
  }

  return true
}

/**
 * CSRF 保护对象
 */
export const csrfProtection = {
  /**
   * 设置 Token
   */
  setToken(token: string): void {
    if (isValidToken(token)) {
      setCsrfToken(token)
    }
  },

  /**
   * 获取 Token
   */
  getToken(): string | null {
    return getCsrfToken()
  },

  /**
   * 清除 Token
   */
  clearToken(): void {
    clearCsrfToken()
  },

  /**
   * 获取请求头（包含 CSRF Token）
   */
  getHeaders(): Record<string, string> {
    const headers: Record<string, string> = {}

    const token = getCsrfToken()
    if (token) {
      headers['X-CSRF-Token'] = token
    }

    return headers
  },

  /**
   * 刷新 Token
   */
  async refreshToken(): Promise<boolean> {
    const newToken = await fetchCsrfToken()
    return newToken !== null
  },

  /**
   * 验证 Token 格式
   */
  isValidToken(token: string | null | undefined): boolean {
    return isValidToken(token)
  }
}

/**
 * 为 fetch 请求自动添加 CSRF 保护
 */
export function createCsrfProtectedFetch(): (
   
  url: string,
   
  options?: RequestInit
) => Promise<Response> {
  return async (url: string, options: RequestInit = {}) => {
    // 确保有 CSRF Token
    if (!getCsrfToken()) {
      await fetchCsrfToken()
    }

    // 合并 CSRF 头
    const headers = new Headers(options.headers)
    const csrfHeaders = csrfProtection.getHeaders()

    for (const [key, value] of Object.entries(csrfHeaders)) {
      headers.set(key, value)
    }

    return fetch(url, {
      ...options,
      headers,
      credentials: 'same-origin'
    })
  }
}