/**
 * 用户登出流程 E2E 测试
 *
 * IMPORTANT - 重要测试
 *
 * 测试内容:
 * 1. 点击用户头像
 * 2. 点击退出登录
 * 3. 验证跳转到登录页
 */
import { test, expect } from '@playwright/test'
import { LoginPage } from './pages/LoginPage'
import { MainLayout } from './pages/MainLayout'
import { TEST_USER, performLogin } from './utils/test-helpers'

test.describe('用户登出流程', () => {
  let loginPage: LoginPage
  let mainLayout: MainLayout

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page)
    mainLayout = new MainLayout(page)

    // 先登录
    await performLogin(page)
  })

  test('应该正确显示用户信息和下拉菜单', async ({ page }) => {
    // 验证顶部栏
    await mainLayout.expectHeaderVisible()

    // 验证用户信息区域
    await expect(page.locator('.user-info')).toBeVisible()

    // 点击用户信息
    await mainLayout.clickUserInfo()

    // 等待下拉菜单出现
    await page.waitForSelector('.ant-dropdown-menu', { timeout: 5000 })

    // 验证下拉菜单项
    await expect(page.locator('.ant-dropdown-menu-item:has-text("个人中心")')).toBeVisible()
    await expect(page.locator('.ant-dropdown-menu-item:has-text("退出登录")')).toBeVisible()

    // 截图
    await page.screenshot({ path: 'playwright-report/screenshots/user-dropdown-menu.png' })
  })

  test('应该能成功执行登出操作', async ({ page }) => {
    // 执行登出
    await mainLayout.logout()

    // 验证跳转到登录页
    await mainLayout.expectLogoutSuccess()

    // 截图
    await page.screenshot({ path: 'playwright-report/screenshots/logout-success.png' })
  })

  test('登出后应该清除 Token', async ({ page }) => {
    // 执行登出
    await mainLayout.logout()

    // 验证跳转到登录页
    await mainLayout.expectLogoutSuccess()

    // 验证 Token 清除
    await mainLayout.expectTokenCleared()
  })

  test('登出后应该清除用户信息', async ({ page }) => {
    // 执行登出
    await mainLayout.logout()

    // 验证跳转到登录页
    await mainLayout.expectLogoutSuccess()

    // 验证用户信息清除
    const storedUser = await page.evaluate(() => {
      return localStorage.getItem('bniot_user')
    })

    expect(storedUser).toBeNull()
  })

  test('登出后应该无法访问需要认证的页面', async ({ page }) => {
    // 执行登出
    await mainLayout.logout()

    // 验证跳转到登录页
    await mainLayout.expectLogoutSuccess()

    // 尝试直接访问仪表盘
    await page.goto('/dashboard')

    // 应该被重定向到登录页
    await page.waitForURL(/login/, { timeout: 5000 })
    await expect(page).toHaveURL(/login/)

    // 截图
    await page.screenshot({ path: 'playwright-report/screenshots/logout-redirect.png' })
  })
})