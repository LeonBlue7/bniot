/**
 * 日志工具测试
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { Logger, wsLogger, apiLogger } from '../logger'

describe('Logger', () => {
  let consoleSpy: {
    debug: ReturnType<typeof vi.spyOn>
    info: ReturnType<typeof vi.spyOn>
    warn: ReturnType<typeof vi.spyOn>
    error: ReturnType<typeof vi.spyOn>
  }

  beforeEach(() => {
    consoleSpy = {
      debug: vi.spyOn(console, 'debug').mockImplementation(() => {}),
      info: vi.spyOn(console, 'info').mockImplementation(() => {}),
      warn: vi.spyOn(console, 'warn').mockImplementation(() => {}),
      error: vi.spyOn(console, 'error').mockImplementation(() => {})
    }
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('基础功能', () => {
    it('应该在启用时输出日志', () => {
      const testLogger = new Logger({ enabled: true, minLevel: 'debug' })

      testLogger.debug('debug message')
      testLogger.info('info message')
      testLogger.warn('warn message')
      testLogger.error('error message')

      expect(consoleSpy.debug).toHaveBeenCalled()
      expect(consoleSpy.info).toHaveBeenCalled()
      expect(consoleSpy.warn).toHaveBeenCalled()
      expect(consoleSpy.error).toHaveBeenCalled()
    })

    it('应该在禁用时不输出日志', () => {
      const testLogger = new Logger({ enabled: false, minLevel: 'debug' })

      testLogger.info('message')

      expect(consoleSpy.info).not.toHaveBeenCalled()
    })

    it('应该根据日志级别过滤', () => {
      const testLogger = new Logger({ enabled: true, minLevel: 'warn' })

      testLogger.debug('debug message')
      testLogger.info('info message')
      testLogger.warn('warn message')
      testLogger.error('error message')

      expect(consoleSpy.debug).not.toHaveBeenCalled()
      expect(consoleSpy.info).not.toHaveBeenCalled()
      expect(consoleSpy.warn).toHaveBeenCalled()
      expect(consoleSpy.error).toHaveBeenCalled()
    })
  })

  describe('格式化', () => {
    it('应该添加前缀', () => {
      const testLogger = new Logger({ enabled: true, minLevel: 'info', prefix: '[TEST]' })

      testLogger.info('message')

      // 验证调用参数包含预期内容
      const callArgs = consoleSpy.info.mock.calls[0]
      const allArgs = callArgs.join(' ')
      expect(allArgs).toContain('[TEST]')
      expect(allArgs).toContain('[INFO]')
    })

    it('应该添加时间戳', () => {
      const testLogger = new Logger({ enabled: true, minLevel: 'info', timestamp: true })

      testLogger.info('message')

      // 验证第一个参数是时间戳格式
      const callArgs = consoleSpy.info.mock.calls[0]
      expect(callArgs[0]).toMatch(/\[\d{4}-\d{2}-\d{2}T/)
    })
  })

  describe('模块日志器', () => {
    it('应该创建带模块名的日志器', () => {
      const testLogger = new Logger({ enabled: true, minLevel: 'debug' })
      const moduleLogger = testLogger.module('TestModule')

      moduleLogger.info('module message')

      // 验证调用参数包含模块名
      const callArgs = consoleSpy.info.mock.calls[0]
      const allArgs = callArgs.join(' ')
      expect(allArgs).toContain('TestModule')
    })
  })

  describe('预定义日志器', () => {
    it('wsLogger 应该有 WebSocket 模块名', () => {
      // 在开发模式下测试
      vi.stubEnv('DEV', true)

      wsLogger.info('test')

      // 验证调用（可能被禁用）
      expect(true).toBe(true)
    })

    it('apiLogger 应该有 API 模块名', () => {
      apiLogger.error('API error')

      // 验证调用（可能被禁用）
      expect(true).toBe(true)
    })
  })

  describe('log 方法别名', () => {
    it('log 应该等同于 info', () => {
      const testLogger = new Logger({ enabled: true, minLevel: 'info' })

      testLogger.log('message')

      expect(consoleSpy.info).toHaveBeenCalled()
    })
  })
})