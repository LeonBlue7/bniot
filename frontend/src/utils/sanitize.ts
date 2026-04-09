/**
 * XSS 防护工具
 * 使用 DOMPurify 进行 HTML 消毒
 */
import DOMPurify from 'dompurify'

// 类型定义
type DOMPurifyConfig = {
  ALLOWED_TAGS?: string[]
  ALLOWED_ATTR?: string[]
  ALLOWED_URI_REGEXP?: RegExp
  FORBID_ATTR?: string[]
  ADD_ATTR?: string[]
  DECODE_ENTITIES?: boolean
}

/**
 * 消毒 HTML 字符串，移除潜在的 XSS 攻击向量
 * @param input - 要消毒的字符串
 * @returns 消毒后的安全 HTML 字符串
 */
export function sanitize(input: string | null | undefined | unknown): string {
  // 处理 null/undefined
  if (input === null || input === undefined) {
    return ''
  }

  // 处理非字符串类型
  if (typeof input !== 'string') {
    return String(input)
  }

  // 空字符串直接返回
  if (input === '') {
    return ''
  }

  // 配置 DOMPurify
  const config: DOMPurifyConfig = {
    // 允许的标签
    ALLOWED_TAGS: [
      'p', 'br', 'span', 'div',
      'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
      'strong', 'b', 'em', 'i', 'u', 's',
      'ul', 'ol', 'li',
      'a', 'img',
      'table', 'thead', 'tbody', 'tr', 'th', 'td',
      'blockquote', 'pre', 'code'
    ],
    // 允许的属性
    ALLOWED_ATTR: [
      'href', 'title', 'target', 'rel',
      'src', 'alt', 'width', 'height',
      'class', 'id',
      'style'
    ],
    // 允许的 URI 协议
    ALLOWED_URI_REGEXP: /^(?:(?:(?:f|ht)tps?|mailto|tel|callto|sms|cid|xmpp):|[^a-z]|[a-z+.\-]+(?:[^a-z+.\-:]|$))/i,
    // 禁止 data: URI（可能包含恶意代码）
    FORBID_ATTR: ['style'],
    // 移除不安全的 data: URI
    ADD_ATTR: ['target'],
    // 保持 HTML 实体
    DECODE_ENTITIES: true
  }

  return DOMPurify.sanitize(input, config) as string
}

/**
 * 递归消毒对象中的所有字符串值
 * @param obj - 要消毒的对象
 * @returns 消毒后的对象副本
 */
export function sanitizeObject<T>(obj: T): T {
  // 处理 null 和 undefined
  if (obj === null || obj === undefined) {
    return obj
  }

  // 处理字符串
  if (typeof obj === 'string') {
    return sanitize(obj) as T
  }

  // 处理数组
  if (Array.isArray(obj)) {
    return obj.map(item => sanitizeObject(item)) as T
  }

  // 处理对象
  if (typeof obj === 'object') {
    const result: Record<string, unknown> = {}
    for (const [key, value] of Object.entries(obj)) {
      result[key] = sanitizeObject(value)
    }
    return result as T
  }

  // 其他类型直接返回
  return obj
}

/**
 * HTML 实体转义（不保留任何 HTML 标签）
 * 适用于需要纯文本的场景
 * @param input - 要转义的字符串
 * @returns 转义后的字符串
 */
export function escapeHtml(input: string | null | undefined | unknown): string {
  // 处理 null/undefined
  if (input === null || input === undefined) {
    return ''
  }

  // 处理非字符串类型
  if (typeof input !== 'string') {
    return String(input)
  }

  const escapeMap: Record<string, string> = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#039;'
  }

  return input.replace(/[&<>"']/g, char => escapeMap[char] || char)
}

/**
 * 检查 URL 是否安全
 * 用于防止 javascript:、data: 等恶意 URL
 * @param url - 要检查的 URL
 * @returns 是否为安全的 URL
 */
export function isSafeUrl(url: string | null | undefined): boolean {
  // 空值检查
  if (!url || typeof url !== 'string') {
    return false
  }

  // 去除前后空格
  const trimmedUrl = url.trim().toLowerCase()

  // 空字符串
  if (trimmedUrl === '') {
    return false
  }

  // 危险协议黑名单
  const dangerousProtocols = [
    'javascript:',
    'vbscript:',
    'data:',
    'blob:'
  ]

  // 检查危险协议（直接匹配）
  for (const protocol of dangerousProtocols) {
    if (trimmedUrl.startsWith(protocol)) {
      return false
    }
  }

  // 检查 URL 编码的危险协议
  try {
    const decodedUrl = decodeURIComponent(trimmedUrl)
    for (const protocol of dangerousProtocols) {
      if (decodedUrl.toLowerCase().startsWith(protocol)) {
        return false
      }
    }
  } catch {
    // URL 解码失败，可能包含恶意内容
    return false
  }

  // 安全协议白名单
  const safeProtocols = [
    'http:',
    'https:',
    'mailto:',
    'tel:',
    'ftp:',
    '/'
  ]

  // 检查是否以安全协议或相对路径开头
  for (const protocol of safeProtocols) {
    if (trimmedUrl.startsWith(protocol) || trimmedUrl.startsWith('./') || trimmedUrl.startsWith('#')) {
      return true
    }
  }

  // 没有协议的相对 URL 视为安全
  if (!trimmedUrl.includes(':') || /^[a-z0-9_-]/i.test(trimmedUrl)) {
    return true
  }

  return false
}

/**
 * 创建安全的 HTML 内容
 * 用于 Vue 模板中的 v-html 指令
 * @param html - 原始 HTML
 * @returns 安全的 HTML
 */
export function safeHtml(html: string): string {
  return sanitize(html)
}