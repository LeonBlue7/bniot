/**
 * 安全工具函数
 * 用于防止 XSS 攻击和其他安全相关功能
 */
import DOMPurify from 'dompurify'

// 类型定义
type DOMPurifyConfig = {
  ALLOWED_TAGS?: string[]
  ALLOWED_ATTR?: string[]
  ALLOW_DATA_ATTR?: boolean
}

/**
 * 消毒 HTML 内容，防止 XSS 攻击
 * @param dirty - 未消毒的 HTML 字符串
 * @param options - DOMPurify 配置选项
 * @returns 消毒后的安全 HTML 字符串
 */
export function sanitize(
  dirty: string | null | undefined,
  options?: DOMPurifyConfig
): string {
  if (dirty == null) {
    return ''
  }

  // 默认配置：允许安全的 HTML 标签
  const defaultOptions: DOMPurifyConfig = {
    ALLOWED_TAGS: ['b', 'i', 'em', 'strong', 'a', 'p', 'br', 'span'],
    ALLOWED_ATTR: ['href', 'title', 'class'],
    ALLOW_DATA_ATTR: false,
    ...options
  }

  return DOMPurify.sanitize(dirty, defaultOptions) as string
}

/**
 * 消毒纯文本内容（移除所有 HTML 标签）
 * @param text - 可能包含 HTML 的文本
 * @returns 纯文本
 */
export function sanitizeText(text: string | null | undefined): string {
  if (text == null) {
    return ''
  }

  // 先用 DOMPurify 移除危险内容
  const clean = DOMPurify.sanitize(text, { ALLOWED_TAGS: [] })

  // 再用 DOM 解析提取纯文本内容
  const div = document.createElement('div')
  div.innerHTML = clean
  return div.textContent || div.innerText || ''
}

/**
 * 验证 URL 是否为安全的链接
 * @param url - 要验证的 URL
 * @returns 是否为安全 URL
 */
export function isSafeUrl(url: string | null | undefined): boolean {
  if (url == null) {
    return false
  }

  try {
    const parsed = new URL(url, window.location.origin)
    // 只允许 http 和 https 协议
    return ['http:', 'https:'].includes(parsed.protocol)
  } catch {
    return false
  }
}

/**
 * 获取安全的 URL（防止 javascript: 协议攻击）
 * @param url - 原始 URL
 * @returns 安全的 URL 或空字符串
 */
export function getSafeUrl(url: string | null | undefined): string {
  if (!isSafeUrl(url)) {
    return ''
  }
  return url!
}

/**
 * 转义 HTML 特殊字符
 * @param text - 要转义的文本
 * @returns 转义后的文本
 */
export function escapeHtml(text: string | null | undefined): string {
  if (text == null) {
    return ''
  }

  const map: Record<string, string> = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#039;'
  }

  return text.replace(/[&<>"']/g, (char) => map[char])
}

/**
 * 安全的 JSON 解析
 * @param jsonString - JSON 字符串
 * @param defaultValue - 解析失败时的默认值
 * @returns 解析后的对象或默认值
 */
export function safeJsonParse<T>(jsonString: string | null | undefined, defaultValue: T): T {
  if (jsonString == null) {
    return defaultValue
  }

  try {
    return JSON.parse(jsonString) as T
  } catch {
    return defaultValue
  }
}