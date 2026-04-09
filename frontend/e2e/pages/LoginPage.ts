/**
 * 登录页面 Page Object
 */
import { expect, type Page } from '@playwright/test'

export class LoginPage {
  readonly page: Page

  // 页面元素定位器
  readonly loginContainer: string
  readonly usernameInput: string
  readonly passwordInput: string
  readonly loginButton: string
  readonly errorMessage: string

  constructor(page: Page) {
    this.page = page
    this.loginContainer = '.login-container'
    this.usernameInput = 'input[placeholder="请输入用户名"]'
    this.passwordInput = 'input[placeholder="请输入密码"]'
    this.loginButton = '.login-btn'
    this.errorMessage = '.error-message'
  }

  /**
   * 导航到登录页面
   */
  async goto() {
    await this.page.goto('/login')
    await this.page.waitForSelector(this.loginContainer)
  }

  /**
   * 输入用户名
   */
  async fillUsername(username: string) {
    await this.page.fill(this.usernameInput, username)
  }

  /**
   * 输入密码
   */
  async fillPassword(password: string) {
    await this.page.fill(this.passwordInput, password)
  }

  /**
   * 点击登录按钮
   */
  async clickLoginButton() {
    await this.page.click(this.loginButton)
  }

  /**
   * 执行完整登录流程
   */
  async login(username: string, password: string) {
    await this.fillUsername(username)
    await this.fillPassword(password)
    await this.clickLoginButton()
  }

  /**
   * 验证登录成功（跳转到仪表盘）
   */
  async expectLoginSuccess() {
    await this.page.waitForURL(/dashboard/, { timeout: 15000 })
    await expect(this.page).toHaveURL(/dashboard/)
  }

  /**
   * 验证登录失败（显示错误消息）
   */
  async expectLoginFailure() {
    await this.page.waitForSelector(this.errorMessage, { timeout: 5000 })
    await expect(this.page.locator(this.errorMessage)).toBeVisible()
  }

  /**
   * 验证页面加载完成
   */
  async expectPageLoaded() {
    await expect(this.page.locator(this.loginContainer)).toBeVisible()
    await expect(this.page.locator('.brand')).toContainText('BNIoT')
  }

  /**
   * 验证 Token 存储在 sessionStorage（使用安全存储）
   */
  async expectTokenStored() {
    // 前端使用 sessionStorage 存储 token（key: bniot_token_secure）
    const token = await this.page.evaluate(() => sessionStorage.getItem('bniot_token_secure'))
    expect(token).toBeTruthy()
    expect(token?.length).toBeGreaterThan(10)
  }
}