import { defineConfig, devices } from '@playwright/test'

/**
 * BNIoT E2E 测试配置
 * @see https://playwright.dev/docs/test-configuration
 */

// 生产环境 URL
const PRODUCTION_URL = 'https://www.jxbonner.cloud'

// 根据 BASE_URL 环境变量决定测试环境
const baseURL = process.env.BASE_URL || process.env.TEST_ENV === 'production'
  ? PRODUCTION_URL
  : 'http://localhost:3000'

export default defineConfig({
  // 测试目录
  testDir: './e2e',

  // 完全并行运行测试
  fullyParallel: true,

  // CI 上失败时禁止 test.only
  forbidOnly: !!process.env.CI,

  // CI 上失败时重试
  retries: process.env.CI ? 2 : 0,

  // CI 上限制并行 workers
  workers: process.env.CI ? 1 : undefined,

  // Reporter 配置
  reporter: [
    ['html', { outputFolder: 'playwright-report' }],
    ['json', { outputFile: 'test-results/results.json' }],
    ['list']
  ],

  // 全局配置
  use: {
    // 基础 URL（支持环境变量覆盖）
    baseURL,

    // 收集失败时的 trace
    trace: 'on-first-retry',

    // 失败时截图
    screenshot: 'only-on-failure',

    // 失败时录制视频
    video: 'retain-on-failure',

    // 测试超时
    actionTimeout: 10000,

    // 导航超时
    navigationTimeout: 30000,
  },

  // 测试项目配置
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],

  // 启动开发服务器（仅本地测试）
  webServer: baseURL.startsWith('http://localhost')
    ? {
        command: 'npm run dev',
        url: 'http://localhost:3000',
        reuseExistingServer: true,
        timeout: 120000,
        stdout: 'pipe',
      }
    : undefined, // 生产环境无需启动本地服务器
})