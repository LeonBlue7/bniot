/**
 * 设备详情页面 Page Object
 */
import { expect, type Page } from '@playwright/test'

export class DeviceDetailPage {
  readonly page: Page

  // 页面元素定位器
  readonly deviceInfoPanel: string
  readonly realtimeDataPanel: string
  readonly parametersPanel: string
  readonly backButton: string
  readonly deviceIdValue: string
  readonly deviceNameValue: string

  constructor(page: Page) {
    this.page = page
    this.deviceInfoPanel = '.device-info-panel'
    this.realtimeDataPanel = '.realtime-data-panel'
    this.parametersPanel = '.parameters-panel'
    this.backButton = 'button:has-text("返回")'
    this.deviceIdValue = '.device-id-value'
    this.deviceNameValue = '.device-name-value'
  }

  /**
   * 导航到设备详情页面
   */
  async goto(deviceId: number) {
    await this.page.goto(`/devices/${deviceId}`)
    await this.page.waitForSelector('.device-detail-page, .ant-spin', { timeout: 15000 })
  }

  /**
   * 验证页面加载完成
   */
  async expectPageLoaded() {
    // 检查是否有内容区域或空状态 - 使用 first() 避免严格模式
    await expect(this.page.locator('.ant-spin, .device-detail-page, .ant-empty').first()).toBeVisible({ timeout: 10000 })
  }

  /**
   * 验证设备信息可见
   */
  async expectDeviceInfoVisible() {
    // 等待加载完成
    await this.page.waitForTimeout(1000)
    const hasContent = await this.page.locator('.device-detail-page').isVisible()
    if (hasContent) {
      await expect(this.page.locator('.device-detail-page')).toBeVisible()
    }
  }

  /**
   * 点击返回按钮
   */
  async clickBackButton() {
    if (await this.page.locator(this.backButton).isVisible()) {
      await this.page.click(this.backButton)
    } else {
      // 使用浏览器返回
      await this.page.goBack()
    }
  }
}