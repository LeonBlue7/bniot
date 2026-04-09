/**
 * 安全工具函数测试
 */
import { describe, it, expect } from 'vitest'
import { sanitize, sanitizeText, isSafeUrl, getSafeUrl, escapeHtml, safeJsonParse } from '../utils/security'

describe('security utils', () => {
  describe('sanitize', () => {
    it('should sanitize XSS scripts', () => {
      const malicious = '<script>alert("XSS")</script>Hello'
      const result = sanitize(malicious)
      expect(result).toBe('Hello')
      expect(result).not.toContain('script')
    })

    it('should allow safe HTML tags', () => {
      const safe = '<b>Bold</b> and <i>italic</i>'
      const result = sanitize(safe)
      expect(result).toBe('<b>Bold</b> and <i>italic</i>')
    })

    it('should handle null and undefined', () => {
      expect(sanitize(null)).toBe('')
      expect(sanitize(undefined)).toBe('')
    })

    it('should remove dangerous attributes', () => {
      const malicious = '<a onclick="alert(1)" href="https://example.com">Link</a>'
      const result = sanitize(malicious)
      expect(result).not.toContain('onclick')
      expect(result).toContain('href')
    })
  })

  describe('sanitizeText', () => {
    it('should remove all HTML tags', () => {
      const html = '<p>Hello <strong>World</strong></p>'
      const result = sanitizeText(html)
      expect(result).toBe('Hello World')
    })

    it('should handle null and undefined', () => {
      expect(sanitizeText(null)).toBe('')
      expect(sanitizeText(undefined)).toBe('')
    })
  })

  describe('isSafeUrl', () => {
    it('should accept http and https URLs', () => {
      expect(isSafeUrl('https://example.com')).toBe(true)
      expect(isSafeUrl('http://example.com')).toBe(true)
    })

    it('should reject javascript URLs', () => {
      expect(isSafeUrl('javascript:alert(1)')).toBe(false)
      expect(isSafeUrl('JAVASCRIPT:alert(1)')).toBe(false)
    })

    it('should reject data URLs', () => {
      expect(isSafeUrl('data:text/html,<script>alert(1)</script>')).toBe(false)
    })

    it('should handle null and undefined', () => {
      expect(isSafeUrl(null)).toBe(false)
      expect(isSafeUrl(undefined)).toBe(false)
    })
  })

  describe('getSafeUrl', () => {
    it('should return safe URLs unchanged', () => {
      expect(getSafeUrl('https://example.com')).toBe('https://example.com')
    })

    it('should return empty string for unsafe URLs', () => {
      expect(getSafeUrl('javascript:alert(1)')).toBe('')
      expect(getSafeUrl(null)).toBe('')
    })
  })

  describe('escapeHtml', () => {
    it('should escape HTML special characters', () => {
      expect(escapeHtml('<script>')).toBe('&lt;script&gt;')
      expect(escapeHtml('a & b')).toBe('a &amp; b')
      expect(escapeHtml('"quoted"')).toBe('&quot;quoted&quot;')
    })

    it('should handle null and undefined', () => {
      expect(escapeHtml(null)).toBe('')
      expect(escapeHtml(undefined)).toBe('')
    })
  })

  describe('safeJsonParse', () => {
    it('should parse valid JSON', () => {
      expect(safeJsonParse('{"key": "value"}', {})).toEqual({ key: 'value' })
    })

    it('should return default value for invalid JSON', () => {
      expect(safeJsonParse('invalid json', { default: true })).toEqual({ default: true })
    })

    it('should return default value for null/undefined', () => {
      expect(safeJsonParse(null, 'default')).toBe('default')
      expect(safeJsonParse(undefined, 'default')).toBe('default')
    })
  })
})