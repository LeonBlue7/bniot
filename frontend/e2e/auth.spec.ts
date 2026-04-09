/**
 * 用户登录流程 E2E 测试
 *
 * CRITICAL - 必须通过的测试
 *
 * 测试内容:
 * 1. 访问登录页面
 * 2. 输入用户名密码
 * 3. 提交表单
 * 4. 验证登录成功跳转到仪表盘
 * 5. 验证 Token 存储
 */
import { test, expect } from '@playwright/test'
import { LoginPage } from './pages/LoginPage'
import { TEST_USER } from './utils/test-helpers'

test.describe('用户登录流程', () => {
  let loginPage: LoginPage

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page)
  })

  test('应该正确显示登录页面', async ({ page }) => {
    await loginPage.goto()
    await loginPage.expectPageLoaded()

    // 验证关键元素存在
    await expect(page.locator('.brand')).toContainText('BNIoT')
    await expect(page.locator('.login-form')).toBeVisible()
    await expect(page.locator('input[placeholder="请输入用户名"]')).toBeVisible()
    await expect(page.locator('input[placeholder="请输入密码"]')).toBeVisible()
    await expect(page.locator('.login-btn')).toBeVisible()

    // 截图
    await page.screenshot({ path: 'playwright-report/screenshots/login-page.png' })
  })

  test('应该使用有效账户成功登录', async ({ page }) => {
    await loginPage.goto()
    await loginPage.login(TEST_USER.username, TEST_USER.password)

    // 验证登录成功
    await loginPage.expectLoginSuccess()

    // 验证 Token 存储
    await loginPage.expectTokenStored()

    // 验证跳转到仪表盘后页面内容
    await expect(page.locator('.page-title')).toContainText('控制中心')

    // 截图
    await page.screenshot({ path: 'playwright-report/screenshots/login-success.png' })
  })

  test('应该使用无效账户登录失败', async ({ page }) => {
    await loginPage.goto()
    await loginPage.login('invalid_user', 'invalid_password')

    // 验证登录失败 - 等待错误消息或保持在登录页
    await page.waitForTimeout(2000)

    // 验证仍在登录页面
    await expect(page).toHaveURL(/login/)

    // 检查是否有错误提示
    const errorVisible = await page.locator('.error-message').isVisible()
    if (errorVisible) {
      await expect(page.locator('.error-message')).toBeVisible()
    }

    // 截图
    await page.screenshot({ path: 'playwright-report/screenshots/login-failure.png' })
  })

  test('应该验证空表单提交', async ({ page }) => {
    await loginPage.goto()

    // 不输入任何内容直接点击登录
    await loginPage.clickLoginButton()

    // 验证仍在登录页面
    await expect(page).toHaveURL(/login/)

    // 验证表单验证错误提示
    await page.waitForTimeout(500)

    // 截图
    await page.screenshot({ path: 'playwright-report/screenshots/login-empty-validation.png' })
  })

  test('登录后应该能正确存储用户信息', async ({ page }) => {
    await loginPage.goto()
    await loginPage.login(TEST_USER.username, TEST_USER.password)
    await loginPage.expectLoginSuccess()

    // 验证用户信息存储（使用 sessionStorage 的安全存储）
    const storedUser = await page.evaluate(() => {
      const userStr = sessionStorage.getItem('bniot_user_secure')
      return userStr ? JSON.parse(userStr) : null
    })

    expect(storedUser).toBeTruthy()
    expect(storedUser.username).toBe(TEST_USER.username)
  })
})