/**
 * XSS 防护工具测试
 * 使用 TDD 方法：先写失败的测试，再实现功能
 */
import { describe, it, expect } from 'vitest'
import { sanitize, sanitizeObject, escapeHtml, isSafeUrl } from './sanitize'

describe('sanitize - XSS 防护工具', () => {
  describe('sanitize 函数', () => {
    describe('基础 HTML 消毒', () => {
      it('应移除 script 标签', () => {
        const input = '<script>alert("XSS")</script>Hello World'
        const result = sanitize(input)
        expect(result).not.toContain('<script>')
        expect(result).toContain('Hello World')
      })

      it('应移除 onclick 事件处理器', () => {
        const input = '<div onclick="alert(\'XSS\')">Click me</div>'
        const result = sanitize(input)
        expect(result).not.toContain('onclick')
        expect(result).toContain('Click me')
      })

      it('应移除 onerror 事件处理器', () => {
        const input = '<img src="x" onerror="alert(\'XSS\')">'
        const result = sanitize(input)
        expect(result).not.toContain('onerror')
      })

      it('应移除 onload 事件处理器', () => {
        const input = '<body onload="alert(\'XSS\')">'
        const result = sanitize(input)
        expect(result).not.toContain('onload')
      })

      it('应移除 javascript: URL', () => {
        const input = '<a href="javascript:alert(\'XSS\')">Click</a>'
        const result = sanitize(input)
        expect(result).not.toContain('javascript:')
      })

      it('应保留安全的 HTML 标签', () => {
        const input = '<p><strong>Bold</strong> and <em>italic</em></p>'
        const result = sanitize(input)
        expect(result).toContain('<p>')
        expect(result).toContain('<strong>')
        expect(result).toContain('<em>')
      })

      it('应保留安全的属性', () => {
        const input = '<a href="https://example.com" title="Link">Link</a>'
        const result = sanitize(input)
        expect(result).toContain('href="https://example.com"')
        expect(result).toContain('title="Link"')
      })
    })

    describe('边界情况', () => {
      it('空字符串应返回空字符串', () => {
        expect(sanitize('')).toBe('')
      })

      it('null 应返回空字符串', () => {
        expect(sanitize(null as unknown as string)).toBe('')
      })

      it('undefined 应返回空字符串', () => {
        expect(sanitize(undefined as unknown as string)).toBe('')
      })

      it('纯文本应原样返回', () => {
        const input = 'Hello World, this is plain text.'
        expect(sanitize(input)).toBe(input)
      })

      it('数字类型应转为字符串', () => {
        expect(sanitize(123 as unknown as string)).toBe('123')
      })

      it('应处理嵌套的恶意标签', () => {
        const input = '<div><script><script>alert("XSS")</script></script></div>'
        const result = sanitize(input)
        expect(result).not.toContain('<script>')
      })
    })

    describe('复杂攻击模式', () => {
      it('应处理大小写混合的恶意标签', () => {
        const input = '<ScRiPt>alert("XSS")</ScRiPt>'
        const result = sanitize(input)
        expect(result.toLowerCase()).not.toContain('<script>')
      })

      it('应处理带空格的恶意标签', () => {
        const input = '<script >alert("XSS")</script>'
        const result = sanitize(input)
        expect(result).not.toContain('alert')
      })

      it('应处理 HTML 实体编码的攻击', () => {
        const input = '&#60;script&#62;alert("XSS")&#60;/script&#62;'
        const result = sanitize(input)
        // DOMPurify 会解码实体并消毒
        expect(result.toLowerCase()).not.toContain('<script>')
      })

      it('应处理 data URI 攻击', () => {
        const input = '<a href="data:text/html,<script>alert(\'XSS\')</script>">Click</a>'
        const result = sanitize(input)
        // DOMPurify 默认会移除危险的 data URI
        expect(result).not.toContain('data:text/html')
      })

      it('应处理 SVG 中的恶意脚本', () => {
        const input = '<svg onload="alert(\'XSS\')"><circle r="10"/></svg>'
        const result = sanitize(input)
        expect(result).not.toContain('onload')
      })

      it('应处理 iframe 注入', () => {
        const input = '<iframe src="https://malicious.com"></iframe>'
        const result = sanitize(input)
        expect(result).not.toContain('<iframe')
      })
    })
  })

  describe('sanitizeObject 函数', () => {
    it('应消毒对象中的所有字符串值', () => {
      const input = {
        name: '<script>alert("XSS")</script>John',
        description: '<p>Safe HTML</p>'
      }
      const result = sanitizeObject(input)
      expect(result.name).not.toContain('<script>')
      expect(result.description).toContain('<p>')
    })

    it('应处理嵌套对象', () => {
      const input = {
        user: {
          name: '<script>XSS</script>Alice',
          bio: 'Normal bio'
        }
      }
      const result = sanitizeObject(input)
      expect(result.user.name).not.toContain('<script>')
      expect(result.user.bio).toBe('Normal bio')
      expect(result.user.name).toContain('Alice')
    })

    it('应处理数组', () => {
      const input = {
        items: ['<script>XSS</script>Item1', 'Item2']
      }
      const result = sanitizeObject(input)
      expect(result.items[0]).not.toContain('<script>')
      expect(result.items[1]).toBe('Item2')
    })

    it('应保留非字符串值', () => {
      const input = {
        count: 42,
        active: true,
        data: null,
        value: undefined
      }
      const result = sanitizeObject(input)
      expect(result.count).toBe(42)
      expect(result.active).toBe(true)
      expect(result.data).toBeNull()
      expect(result.value).toBeUndefined()
    })

    it('null 和 undefined 应原样返回', () => {
      expect(sanitizeObject(null)).toBeNull()
      expect(sanitizeObject(undefined)).toBeUndefined()
    })

    it('数组应正确处理', () => {
      const input = ['<script>XSS</script>Item', 'Safe']
      const result = sanitizeObject(input)
      expect(Array.isArray(result)).toBe(true)
      expect(result[0]).not.toContain('<script>')
    })
  })

  describe('escapeHtml 函数', () => {
    it('应转义 HTML 特殊字符', () => {
      expect(escapeHtml('<div>')).toBe('&lt;div&gt;')
      expect(escapeHtml('a & b')).toBe('a &amp; b')
      expect(escapeHtml('"quoted"')).toBe('&quot;quoted&quot;')
      expect(escapeHtml("'single'")).toBe('&#039;single&#039;')
    })

    it('空字符串应返回空字符串', () => {
      expect(escapeHtml('')).toBe('')
    })

    it('null 应返回空字符串', () => {
      expect(escapeHtml(null as unknown as string)).toBe('')
    })

    it('纯文本应原样返回', () => {
      expect(escapeHtml('Hello World')).toBe('Hello World')
    })

    it('应处理组合攻击向量', () => {
      const input = '<script>alert("XSS")</script>'
      const result = escapeHtml(input)
      expect(result).toBe('&lt;script&gt;alert(&quot;XSS&quot;)&lt;/script&gt;')
      expect(result).not.toContain('<')
      expect(result).not.toContain('>')
    })
  })

  describe('isSafeUrl 函数', () => {
    it('应接受安全的 HTTP URL', () => {
      expect(isSafeUrl('http://example.com')).toBe(true)
      expect(isSafeUrl('https://example.com')).toBe(true)
    })

    it('应拒绝 javascript: URL', () => {
      expect(isSafeUrl('javascript:alert(1)')).toBe(false)
      expect(isSafeUrl('JAVASCRIPT:alert(1)')).toBe(false)
      expect(isSafeUrl('  javascript:alert(1)')).toBe(false)
    })

    it('应拒绝 data: URL（可能包含恶意代码）', () => {
      expect(isSafeUrl('data:text/html,<script>alert(1)</script>')).toBe(false)
    })

    it('应拒绝 vbscript: URL', () => {
      expect(isSafeUrl('vbscript:msgbox(1)')).toBe(false)
    })

    it('应接受相对 URL', () => {
      expect(isSafeUrl('/path/to/page')).toBe(true)
      expect(isSafeUrl('./relative')).toBe(true)
      expect(isSafeUrl('#anchor')).toBe(true)
    })

    it('应接受 mailto: URL', () => {
      expect(isSafeUrl('mailto:test@example.com')).toBe(true)
    })

    it('应接受 tel: URL', () => {
      expect(isSafeUrl('tel:+1234567890')).toBe(true)
    })

    it('空字符串应返回 false', () => {
      expect(isSafeUrl('')).toBe(false)
    })

    it('null 应返回 false', () => {
      expect(isSafeUrl(null as unknown as string)).toBe(false)
    })

    it('应处理 URL 编码的恶意代码', () => {
      expect(isSafeUrl('%6A%61%76%61%73%63%72%69%70%74%3Aalert(1)')).toBe(false)
    })
  })
})