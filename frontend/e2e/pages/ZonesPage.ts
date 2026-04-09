/**
 * 分区管理页面 Page Object
 */
import { expect, type Page } from '@playwright/test'

export class ZonesPage {
  readonly page: Page

  // 页面元素定位器
  readonly zoneTree: string
  readonly zoneDetail: string
  readonly addButton: string
  readonly zoneNode: string

  constructor(page: Page) {
    this.page = page
    this.zoneTree = '.ant-tree'
    this.zoneDetail = '.ant-card:has-text("分区详情")'
    this.addButton = 'button:has-text("添加")'
    this.zoneNode = '.ant-tree-node-content-wrapper'
  }

  /**
   * 导航到分区管理页面
   */
  async goto() {
    await this.page.goto('/zones')
    await this.page.waitForSelector('.zones-page', { timeout: 15000 })
  }

  /**
   * 验证页面加载完成
   */
  async expectPageLoaded() {
    await expect(this.page.locator('.ant-card:has-text("分区结构")')).toBeVisible()
  }

  /**
   * 验证分区树可见
   */
  async expectZoneTreeVisible() {
    // 分区树可能不存在（无数据时显示空状态）
    const treeVisible = await this.page.locator(this.zoneTree).isVisible()
    const emptyVisible = await this.page.locator('.ant-empty').first().isVisible()
    expect(treeVisible || emptyVisible).toBeTruthy()
  }

  /**
   * 点击添加分区按钮
   */
  async clickAddButton() {
    await this.page.click(this.addButton)
  }

  /**
   * 验证添加分区弹窗显示
   */
  async expectAddZoneModalVisible() {
    await expect(this.page.locator('.ant-modal:has-text("添加分区")')).toBeVisible()
  }

  /**
   * 选择分区树中的第一个节点
   */
  async selectFirstZone() {
    const firstNode = this.page.locator('.ant-tree-treenode').first()
    await firstNode.click()
  }
}