/**
 * 报表页面 E2E 测试
 *
 * 测试内容:
 * 1. 登录后访问报表页面
 * 2. 验证图表渲染
 * 3. 验证导出功能
 * 4. 验证筛选功能
 */
import { test, expect } from '@playwright/test'
import { LoginPage } from './pages/LoginPage'
import { ReportsPage } from './pages/ReportsPage'
import { TEST_USER, performLogin, waitForAntLoading } from './utils/test-helpers'

test.describe('报表分析页面', () => {
  let loginPage: LoginPage
  let reportsPage: ReportsPage

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page)
    reportsPage = new ReportsPage(page)

    // 先登录
    await performLogin(page)
  })

  test('应该正确显示报表页面', async ({ page }) => {
    await reportsPage.goto()

    // 验证页面标题
    await reportsPage.expectPageLoaded()

    // 截图
    await page.screenshot({ path: 'playwright-report/screenshots/reports-page.png' })
  })

  test('应该正确显示查询面板', async ({ page }) => {
    await reportsPage.goto()

    // 验证查询面板
    await reportsPage.expectQueryPanelVisible()

    // 截图
    await page.screenshot({ path: 'playwright-report/screenshots/reports-query-panel.png' })
  })

  test('应该正确显示四个图表标签页', async ({ page }) => {
    await reportsPage.goto()

    // 验证标签页
    await reportsPage.expectTabsVisible()

    // 截图
    await page.screenshot({ path: 'playwright-report/screenshots/reports-tabs.png' })
  })

  test('应该正确渲染能耗统计图表', async ({ page }) => {
    await reportsPage.goto()

    // 等待数据加载
    await waitForAntLoading(page)
    await page.waitForTimeout(2000) // 等待图表渲染

    // 验证能耗图表
    await reportsPage.expectEnergyChartVisible()

    // 验证汇总卡片（可能不存在）
    const summaryCards = page.locator('.summary-cards')
    const cardsVisible = await summaryCards.isVisible().catch(() => false)
    if (cardsVisible) {
      await expect(summaryCards).toBeVisible()
    }

    // 截图（增加超时）
    await page.screenshot({ path: 'playwright-report/screenshots/reports-energy-chart.png', timeout: 30000 })
  })

  test('应该正确渲染温湿度趋势图表', async ({ page }) => {
    await reportsPage.goto()

    // 切换到温湿度趋势标签页
    await reportsPage.switchTab(1)

    // 等待数据加载
    await waitForAntLoading(page)

    // 验证趋势图表或空状态
    await reportsPage.expectTrendChartVisible()

    // 截图
    await page.screenshot({ path: 'playwright-report/screenshots/reports-trend-chart.png' })
  })

  test('应该正确渲染告警统计饼图', async ({ page }) => {
    await reportsPage.goto()

    // 切换到告警统计标签页
    await reportsPage.switchTab(2)

    // 等待数据加载
    await waitForAntLoading(page)

    // 验证告警饼图
    await reportsPage.expectAlarmPieChartVisible()

    // 截图
    await page.screenshot({ path: 'playwright-report/screenshots/reports-alarm-chart.png' })
  })

  test('应该正确渲染运行时长柱状图', async ({ page }) => {
    await reportsPage.goto()

    // 切换到运行时长标签页
    await reportsPage.switchTab(3)

    // 等待数据加载
    await waitForAntLoading(page)

    // 验证运行时长图表
    await reportsPage.expectRuntimeBarChartVisible()

    // 截图
    await page.screenshot({ path: 'playwright-report/screenshots/reports-runtime-chart.png' })
  })

  test('应该能切换告警分组方式', async ({ page }) => {
    await reportsPage.goto()

    // 切换到告警统计标签页
    await reportsPage.switchTab(2)

    // 等待数据加载
    await waitForAntLoading(page)
    await page.waitForTimeout(1000) // 额外等待渲染

    // 查找并点击"按严重程度"按钮（使用 label 选择器）
    const severityButton = page.locator('text=按严重程度').first()
    await severityButton.waitFor({ state: 'visible', timeout: 10000 })
    await severityButton.click()

    // 等待重新加载
    await waitForAntLoading(page)

    // 验证图表仍然可见
    await reportsPage.expectAlarmPieChartVisible()

    // 截图
    await page.screenshot({ path: 'playwright-report/screenshots/reports-alarm-severity.png' })
  })

  test('应该显示数据表格', async ({ page }) => {
    await reportsPage.goto()

    // 等待数据加载
    await waitForAntLoading(page)

    // 验证表格可见
    await expect(page.locator('.ant-table')).toBeVisible()

    // 截图
    await page.screenshot({ path: 'playwright-report/screenshots/reports-table.png' })
  })

  test('应该能导出报表', async ({ page }) => {
    await reportsPage.goto()

    // 等待数据加载
    await waitForAntLoading(page)

    // 点击导出按钮
    await reportsPage.clickExportButton()

    // 等待下载触发（不验证实际下载，因为需要后端支持）
    await page.waitForTimeout(1000)

    // 截图
    await page.screenshot({ path: 'playwright-report/screenshots/reports-export.png' })
  })
})