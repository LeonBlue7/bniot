/**
 * 告警中心页面 Page Object
 */
import { expect, type Page } from '@playwright/test'

export class AlarmsPage {
  readonly page: Page

  // 页面元素定位器
  readonly pageTitle: string
  readonly filterBar: string
  readonly statusFilter: string
  readonly severityFilter: string
  readonly alarmsTable: string
  readonly batchResolveButton: string

  constructor(page: Page) {
    this.page = page
    this.pageTitle = '.page-title'
    this.filterBar = '.filter-bar'
    this.statusFilter = '.ant-select'
    this.severityFilter = '.ant-select'
    this.alarmsTable = '.ant-table'
    this.batchResolveButton = 'button:has-text("批量处理")'
  }

  /**
   * 导航到告警中心页面
   */
  async goto() {
    await this.page.goto('/alarms')
    await this.page.waitForSelector('.alarms-page', { timeout: 15000 })
  }

  /**
   * 验证页面加载完成
   */
  async expectPageLoaded() {
    await expect(this.page.locator('.page-header-section')).toBeVisible()
    await expect(this.page.locator(this.pageTitle)).toContainText('告警中心')
  }

  /**
   * 验证过滤器栏可见
   */
  async expectFilterBarVisible() {
    await expect(this.page.locator(this.filterBar)).toBeVisible()
  }

  /**
   * 验证告警表格可见
   */
  async expectAlarmsTableVisible() {
    await expect(this.page.locator(this.alarmsTable)).toBeVisible()
  }

  /**
   * 选择状态过滤器
   */
  async selectStatusFilter(status: string) {
    // 点击状态过滤下拉框
    const filterGroup = this.page.locator('.filter-group').first()
    await filterGroup.locator('.ant-select-selector').click()
    // 选择选项
    await this.page.click(`.ant-select-dropdown .ant-select-item:has-text("${status}")`)
  }
}