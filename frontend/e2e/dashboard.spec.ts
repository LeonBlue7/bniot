/**
 * 仪表盘数据流程 E2E 测试
 *
 * CRITICAL - 必须通过的测试
 *
 * 测试内容:
 * 1. 登录后访问仪表盘
 * 2. 验证统计卡片数据展示
 * 3. 验证设备状态面板
 * 4. 验证快速操作按钮
 */
import { test, expect } from '@playwright/test'
import { LoginPage } from './pages/LoginPage'
import { DashboardPage } from './pages/DashboardPage'
import { MainLayout } from './pages/MainLayout'
import { TEST_USER, performLogin } from './utils/test-helpers'

test.describe('仪表盘数据流程', () => {
  let loginPage: LoginPage
  let dashboardPage: DashboardPage
  let mainLayout: MainLayout

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page)
    dashboardPage = new DashboardPage(page)
    mainLayout = new MainLayout(page)

    // 先登录
    await performLogin(page)
  })

  test('应该正确显示仪表盘页面', async ({ page }) => {
    await dashboardPage.goto()

    // 验证页面标题
    await dashboardPage.expectTitleVisible()

    // 截图
    await page.screenshot({ path: 'playwright-report/screenshots/dashboard-page.png' })
  })

  test('应该正确显示统计卡片数据', async ({ page }) => {
    await dashboardPage.goto()

    // 验证统计卡片可见
    await dashboardPage.expectStatsCardsVisible()

    // 验证各卡片包含数值
    const totalDevices = await dashboardPage.getTotalDevices()
    expect(totalDevices).toBeTruthy()

    const onlineDevices = await dashboardPage.getOnlineDevices()
    expect(onlineDevices).toBeTruthy()

    // 截图
    await page.screenshot({ path: 'playwright-report/screenshots/dashboard-stats.png' })
  })

  test('应该正确显示设备状态面板', async ({ page }) => {
    await dashboardPage.goto()

    // 验证设备状态面板
    await dashboardPage.expectDevicesPanelVisible()

    // 验证设备状态环形图
    await expect(page.locator('.status-ring.online')).toBeVisible()
    await expect(page.locator('.status-ring.offline')).toBeVisible()
    await expect(page.locator('.status-ring.online-rate')).toBeVisible()

    // 截图
    await page.screenshot({ path: 'playwright-report/screenshots/dashboard-devices-panel.png' })
  })

  test('应该正确显示告警面板', async ({ page }) => {
    await dashboardPage.goto()

    // 验证告警面板
    await dashboardPage.expectAlarmsPanelVisible()

    // 截图
    await page.screenshot({ path: 'playwright-report/screenshots/dashboard-alarms-panel.png' })
  })

  test('应该能刷新仪表盘数据', async ({ page }) => {
    await dashboardPage.goto()

    // 点击刷新按钮
    await dashboardPage.clickRefreshButton()

    // 等待加载完成
    await page.waitForTimeout(1000)

    // 验证页面仍然正常显示
    await dashboardPage.expectTitleVisible()

    // 截图
    await page.screenshot({ path: 'playwright-report/screenshots/dashboard-refresh.png' })
  })

  test('应该能通过快速操作按钮导航到设备管理', async ({ page }) => {
    await dashboardPage.goto()

    // 点击设备管理按钮
    await dashboardPage.clickDeviceManagement()

    // 验证跳转到设备管理页面
    await page.waitForURL(/devices/, { timeout: 10000 })
    await expect(page).toHaveURL(/devices/)

    // 截图
    await page.screenshot({ path: 'playwright-report/screenshots/dashboard-nav-devices.png' })
  })

  test('应该能通过快速操作按钮导航到分区管理', async ({ page }) => {
    await dashboardPage.goto()

    // 点击分区管理按钮
    await dashboardPage.clickZoneManagement()

    // 验证跳转到分区管理页面
    await page.waitForURL(/zones/, { timeout: 10000 })
    await expect(page).toHaveURL(/zones/)

    // 截图
    await page.screenshot({ path: 'playwright-report/screenshots/dashboard-nav-zones.png' })
  })

  test('应该显示系统状态信息栏', async ({ page }) => {
    await dashboardPage.goto()

    // 验证系统信息栏
    await expect(page.locator('.system-bar')).toBeVisible()

    // 验证系统版本
    await expect(page.locator('.system-bar')).toContainText('系统版本')
    await expect(page.locator('.system-bar')).toContainText('v1.0.0')

    // 截图
    await page.screenshot({ path: 'playwright-report/screenshots/dashboard-system-bar.png' })
  })
})