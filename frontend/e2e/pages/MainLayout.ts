/**
 * 主布局 Page Object（包含导航和登出功能）
 */
import { expect, type Page } from '@playwright/test'

export class MainLayout {
  readonly page: Page

  // 页面元素定位器
  readonly sidebar: string
  readonly header: string
  readonly userInfo: string
  readonly logoutButton: string
  readonly menuItems: string

  constructor(page: Page) {
    this.page = page
    this.sidebar = '.sidebar'
    this.header = '.header'
    this.userInfo = '.user-info'
    this.logoutButton = '.ant-dropdown-menu-item:has-text("退出登录")'
    this.menuItems = '.ant-menu-item'
  }

  /**
   * 验证侧边栏可见
   */
  async expectSidebarVisible() {
    await expect(this.page.locator(this.sidebar)).toBeVisible()
  }

  /**
   * 验证顶部栏可见
   */
  async expectHeaderVisible() {
    await expect(this.page.locator(this.header)).toBeVisible()
  }

  /**
   * 点击用户头像/信息区域
   */
  async clickUserInfo() {
    await this.page.click(this.userInfo)
  }

  /**
   * 执行登出操作
   */
  async logout() {
    // 点击用户信息区域
    await this.clickUserInfo()
    // 等待下拉菜单出现
    await this.page.waitForSelector('.ant-dropdown-menu', { timeout: 5000 })
    // 点击退出登录
    await this.page.click(this.logoutButton)
  }

  /**
   * 验证登出成功（跳转到登录页）
   */
  async expectLogoutSuccess() {
    await this.page.waitForURL(/login/, { timeout: 10000 })
    await expect(this.page).toHaveURL(/login/)
  }

  /**
   * 验证 Token 已清除
   */
  async expectTokenCleared() {
    const token = await this.page.evaluate(() => localStorage.getItem('bniot_token'))
    expect(token).toBeNull()
  }

  /**
   * 点击侧边栏菜单项
   */
  async clickMenuItem(itemName: string) {
    // 使用更精确的选择器匹配菜单项
    const menuItem = this.page.locator(`.ant-menu-item:has-text("${itemName}")`)
    await menuItem.click()
  }

  /**
   * 导航到仪表盘
   */
  async navigateToDashboard() {
    await this.clickMenuItem('仪表盘')
  }

  /**
   * 导航到设备管理
   */
  async navigateToDevices() {
    await this.clickMenuItem('设备管理')
  }

  /**
   * 导航到分区管理
   */
  async navigateToZones() {
    await this.clickMenuItem('分区管理')
  }

  /**
   * 导航到告警中心
   */
  async navigateToAlarms() {
    await this.clickMenuItem('告警中心')
  }
}