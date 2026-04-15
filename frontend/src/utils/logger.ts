/**
 * 统一日志工具
 * 支持开发/生产环境切换，避免生产环境输出敏感日志
 */

type LogLevel = 'debug' | 'info' | 'warn' | 'error'

interface LoggerOptions {
  /** 是否启用日志（生产环境应设为 false） */
  enabled: boolean
  /** 最低日志级别 */
  minLevel: LogLevel
  /** 是否包含时间戳 */
  timestamp: boolean
  /** 前缀 */
  prefix?: string
}

const LOG_LEVELS: Record<LogLevel, number> = {
  debug: 0,
  info: 1,
  warn: 2,
  error: 3
}

class Logger {
  private options: LoggerOptions

  constructor(options?: Partial<LoggerOptions>) {
    // 从环境变量读取配置
    const isDev = import.meta.env.DEV
    const isDebugEnabled = import.meta.env.VITE_DEBUG === 'true'

    this.options = {
      enabled: isDev || isDebugEnabled,
      minLevel: isDev ? 'debug' : 'error',
      timestamp: isDev,
      prefix: '[BNIoT]',
      ...options
    }
  }

  private shouldLog(level: LogLevel): boolean {
    if (!this.options.enabled) return false
    return LOG_LEVELS[level] >= LOG_LEVELS[this.options.minLevel]
  }

  private formatMessage(level: LogLevel, ...args: unknown[]): unknown[] {
    const parts: unknown[] = []

    if (this.options.timestamp) {
      parts.push(`[${new Date().toISOString()}]`)
    }

    if (this.options.prefix) {
      parts.push(this.options.prefix)
    }

    parts.push(`[${level.toUpperCase()}]`)

    return [...parts, ...args]
  }

  debug(...args: unknown[]): void {
    if (this.shouldLog('debug')) {
      console.debug(...this.formatMessage('debug', ...args))
    }
  }

  info(...args: unknown[]): void {
    if (this.shouldLog('info')) {
      console.info(...this.formatMessage('info', ...args))
    }
  }

  log(...args: unknown[]): void {
    this.info(...args)
  }

  warn(...args: unknown[]): void {
    if (this.shouldLog('warn')) {
      console.warn(...this.formatMessage('warn', ...args))
    }
  }

  error(...args: unknown[]): void {
    if (this.shouldLog('error')) {
      console.error(...this.formatMessage('error', ...args))
    }
  }

  /** 创建带模块前缀的子日志器 */
  module(name: string): ModuleLogger {
    return new ModuleLogger(this, name)
  }
}

class ModuleLogger {
  private parent: Logger
  private moduleName: string

  constructor(parent: Logger, moduleName: string) {
    this.parent = parent
    this.moduleName = moduleName
  }

  private prefix(): string {
    return `[${this.moduleName}]`
  }

  debug(...args: unknown[]): void {
    this.parent.debug(this.prefix(), ...args)
  }

  info(...args: unknown[]): void {
    this.parent.info(this.prefix(), ...args)
  }

  log(...args: unknown[]): void {
    this.info(...args)
  }

  warn(...args: unknown[]): void {
    this.parent.warn(this.prefix(), ...args)
  }

  error(...args: unknown[]): void {
    this.parent.error(this.prefix(), ...args)
  }
}

// 创建默认日志器实例
const logger = new Logger()

// 创建常用模块日志器（仅导出实际使用的）
export const wsLogger = logger.module('WebSocket')
export const apiLogger = logger.module('API')

// 导出类型和类
export type { LoggerOptions, LogLevel }
export { Logger }