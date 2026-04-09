/**
 * 仪表盘页面 Page Object
 */
import { expect, type Page } from '@playwright/test'

export class DashboardPage {
  readonly page: Page

  // 页面元素定位器
  readonly pageTitle: string
  readonly statsGrid: string
  readonly totalDevicesCard: string
  readonly onlineDevicesCard: string
  readonly offlineDevicesCard: string
  readonly alarmsCard: string
  readonly devicesPanel: string
  readonly alarmsPanel: string
  readonly refreshButton: string
  readonly deviceManagementButton: string
  readonly zoneManagementButton: string

  constructor(page: Page) {
    this.page = page
    this.pageTitle = '.page-title'
    this.statsGrid = '.stats-grid'
    this.totalDevicesCard = '.stat-card.cool'
    this.onlineDevicesCard = '.stat-card.normal'
    this.offlineDevicesCard = '.stat-card.warning'
    this.alarmsCard = '.stat-card.danger'
    this.devicesPanel = '.devices-panel'
    this.alarmsPanel = '.alarms-panel'
    this.refreshButton = '.refresh-btn'
    this.deviceManagementButton = '.action-btn'
    this.zoneManagementButton = '.action-btn'
  }

  /**
   * 导航到仪表盘
   */
  async goto() {
    await this.page.goto('/dashboard')
    await this.page.waitForSelector(this.pageTitle)
  }

  /**
   * 验证页面标题
   */
  async expectTitleVisible() {
    await expect(this.page.locator(this.pageTitle)).toContainText('控制中心')
  }

  /**
   * 验证统计卡片可见
   */
  async expectStatsCardsVisible() {
    await expect(this.page.locator(this.totalDevicesCard)).toBeVisible()
    await expect(this.page.locator(this.onlineDevicesCard)).toBeVisible()
    await expect(this.page.locator(this.offlineDevicesCard)).toBeVisible()
    await expect(this.page.locator(this.alarmsCard)).toBeVisible()
  }

  /**
   * 获取设备总数
   */
  async getTotalDevices() {
    const card = this.page.locator(this.totalDevicesCard)
    const value = card.locator('.stat-value')
    return await value.textContent() || '0'
  }

  /**
   * 获取在线设备数
   */
  async getOnlineDevices() {
    const card = this.page.locator(this.onlineDevicesCard)
    const value = card.locator('.stat-value')
    return await value.textContent() || '0'
  }

  /**
   * 获取告警数
   */
  async getAlarmsCount() {
    const card = this.page.locator(this.alarmsCard)
    const value = card.locator('.stat-value')
    return await value.textContent() || '0'
  }

  /**
   * 验证设备状态面板可见
   */
  async expectDevicesPanelVisible() {
    await expect(this.page.locator(this.devicesPanel)).toBeVisible()
  }

  /**
   * 验证告警面板可见
   */
  async expectAlarmsPanelVisible() {
    await expect(this.page.locator(this.alarmsPanel)).toBeVisible()
  }

  /**
   * 点击刷新按钮
   */
  async clickRefreshButton() {
    await this.page.click(this.refreshButton)
  }

  /**
   * 点击设备管理按钮
   */
  async clickDeviceManagement() {
    // 使用更精确的选择器
    await this.page.click('.quick-actions .action-btn:first-child')
  }

  /**
   * 点击分区管理按钮
   */
  async clickZoneManagement() {
    await this.page.click('.quick-actions .action-btn:last-child')
  }
}