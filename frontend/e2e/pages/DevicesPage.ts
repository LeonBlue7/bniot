/**
 * 设备管理页面 Page Object
 */
import { expect, type Page } from '@playwright/test'

export class DevicesPage {
  readonly page: Page

  // 页面元素定位器
  readonly toolbarCard: string
  readonly searchInput: string
  readonly zoneFilter: string
  readonly onlineFilter: string
  readonly addButton: string
  readonly deviceTable: string
  readonly deviceRow: string
  readonly deviceDetailLink: string

  constructor(page: Page) {
    this.page = page
    this.toolbarCard = '.toolbar-card'
    this.searchInput = 'input[placeholder="搜索设备号、名称、SIM卡、固件版本、分区"]'
    this.zoneFilter = '.ant-select-selector'
    this.addButton = 'button:has-text("添加设备")'
    this.deviceTable = '.ant-table'
    this.deviceRow = '.ant-table-row'
    this.deviceDetailLink = 'a:has-text("详情")'
  }

  /**
   * 导航到设备管理页面
   */
  async goto() {
    await this.page.goto('/devices')
    await this.page.waitForSelector(this.toolbarCard, { timeout: 15000 })
  }

  /**
   * 验证页面加载完成
   */
  async expectPageLoaded() {
    await expect(this.page.locator(this.toolbarCard)).toBeVisible()
    await expect(this.page.locator(this.searchInput)).toBeVisible()
  }

  /**
   * 搜索设备
   */
  async searchDevice(keyword: string) {
    await this.page.fill(this.searchInput, keyword)
    await this.page.press(this.searchInput, 'Enter')
    // 等待搜索结果
    await this.page.waitForTimeout(500)
  }

  /**
   * 获取设备列表行数
   */
  async getDeviceRowsCount() {
    const rows = this.page.locator(this.deviceRow)
    return await rows.count()
  }

  /**
   * 点击设备详情链接（第一行）
   */
  async clickFirstDeviceDetail() {
    // 点击表格第一行的设备名称链接
    const firstRow = this.page.locator('.ant-table-row').first()
    const deviceLink = firstRow.locator('a')
    await deviceLink.click()
  }

  /**
   * 点击第一行的详情按钮
   */
  async clickFirstRowDetailButton() {
    const firstRow = this.page.locator('.ant-table-row').first()
    // 按钮文本可能是 "详 情" 或 "详情"，使用更灵活的选择器
    const detailButton = firstRow.locator('button').filter({ hasText: '详' }).first()
    await detailButton.click()
  }

  /**
   * 验证设备表格可见
   */
  async expectTableVisible() {
    await expect(this.page.locator(this.deviceTable)).toBeVisible()
  }

  /**
   * 点击添加设备按钮
   */
  async clickAddDeviceButton() {
    await this.page.click(this.addButton)
  }

  /**
   * 验证添加设备弹窗显示
   */
  async expectAddDeviceModalVisible() {
    await expect(this.page.locator('.ant-modal:has-text("添加设备")')).toBeVisible()
  }
}