/**
 * 测试辅助工具
 */

// 测试账户配置
export const TEST_USER = {
  username: 'admin',
  password: 'admin123'
}

// 等待网络空闲
export async function waitForNetworkIdle(page: import('@playwright/test').Page, timeout = 2000) {
  await page.waitForLoadState('networkidle', { timeout })
}

// 等待 Ant Design Vue 加载状态消失
export async function waitForAntLoading(page: import('@playwright/test').Page) {
  // 等待页面上所有 spin 组件消失
  try {
    // 使用更宽松的等待策略
    await page.waitForFunction(() => {
      const spins = document.querySelectorAll('.ant-spin-spinning')
      return spins.length === 0
    }, { timeout: 15000 })
  } catch {
    // 超时后继续，可能已经加载完成
  }
}

// 登录辅助函数
export async function performLogin(page: import('@playwright/test').Page) {
  await page.goto('/login')
  await page.waitForSelector('.login-container')
  await page.fill('input[placeholder="请输入用户名"]', TEST_USER.username)
  await page.fill('input[placeholder="请输入密码"]', TEST_USER.password)
  await page.click('.login-btn')
  await page.waitForURL(/dashboard/, { timeout: 15000 })
}

// 截图辅助函数
export async function takeScreenshot(page: import('@playwright/test').Page, name: string) {
  await page.screenshot({ path: `playwright-report/screenshots/${name}.png`, fullPage: true })
}