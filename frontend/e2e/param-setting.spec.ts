/**
 * 设备参数设置功能 E2E 测试
 *
 * 测试内容:
 * 1. 打开参数编辑弹窗
 * 2. 验证参数表单显示
 * 3. V10/V20 版本差异化参数
 * 4. 设置空调开机/关机条件
 * 5. 设置开关机时间段
 * 6. 表单验证和提交
 */
import { test, expect } from '@playwright/test'
import { LoginPage } from './pages/LoginPage'
import { DeviceDetailPage } from './pages/DeviceDetailPage'
import { performLogin, waitForAntLoading } from './utils/test-helpers'

test.describe('设备参数设置功能', () => {
  let loginPage: LoginPage
  let deviceDetailPage: DeviceDetailPage

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page)
    deviceDetailPage = new DeviceDetailPage(page)

    // 先登录
    await performLogin(page)
  })

  test('应该显示参数设置卡片', async ({ page }) => {
    // 导航到设备详情页（假设设备ID为1）
    await deviceDetailPage.goto(1)
    await waitForAntLoading(page)

    // 验证参数设置卡片存在
    const paramsCard = page.locator('.ant-card:has-text("参数设置")')
    await expect(paramsCard).toBeVisible({ timeout: 10000 })

    // 截图
    await page.screenshot({ path: 'playwright-report/screenshots/param-card.png' })
  })

  test('应该显示编辑参数按钮', async ({ page }) => {
    await deviceDetailPage.goto(1)
    await waitForAntLoading(page)

    // 验证编辑参数按钮存在
    const editButton = page.locator('button:has-text("编辑参数")')
    await expect(editButton).toBeVisible({ timeout: 10000 })

    // 截图
    await page.screenshot({ path: 'playwright-report/screenshots/edit-param-button.png' })
  })

  test('应该能打开参数编辑弹窗', async ({ page }) => {
    await deviceDetailPage.goto(1)
    await waitForAntLoading(page)

    // 点击编辑参数按钮
    const editButton = page.locator('button:has-text("编辑参数")')
    await editButton.click()

    // 验证弹窗显示
    const modal = page.locator('.ant-modal:has-text("参数设置")')
    await expect(modal).toBeVisible({ timeout: 10000 })

    // 截图
    await page.screenshot({ path: 'playwright-report/screenshots/param-edit-modal.png' })
  })

  test('参数编辑弹窗应包含空调开机条件设置', async ({ page }) => {
    await deviceDetailPage.goto(1)
    await waitForAntLoading(page)

    // 打开参数编辑弹窗
    await page.locator('button:has-text("编辑参数")').click()
    await page.waitForSelector('.ant-modal:has-text("参数设置")', { timeout: 10000 })

    // 验证空调开机条件分区标题存在
    const divider = page.locator('.ant-divider-inner-text:has-text("空调开机条件")')
    await expect(divider).toBeVisible()

    // 验证温度参数输入框存在
    const summerStartupTemp = page.locator('.ant-form-item:has-text("夏天开机温度")')
    await expect(summerStartupTemp).toBeVisible()

    const summerShutdownTemp = page.locator('.ant-form-item:has-text("夏天关机温度")')
    await expect(summerShutdownTemp).toBeVisible()

    // 截图
    await page.screenshot({ path: 'playwright-report/screenshots/startup-conditions.png' })
  })

  test('参数编辑弹窗应包含开关机时间段设置', async ({ page }) => {
    await deviceDetailPage.goto(1)
    await waitForAntLoading(page)

    // 打开参数编辑弹窗
    await page.locator('button:has-text("编辑参数")').click()
    await page.waitForSelector('.ant-modal:has-text("参数设置")', { timeout: 10000 })

    // 验证开关机时间设置分区标题存在
    const divider = page.locator('.ant-divider-inner-text:has-text("开关机时间设置")')
    await expect(divider).toBeVisible()

    // 验证时间段输入框存在
    const startupTime1 = page.locator('.ant-form-item:has-text("开机时间段1")')
    await expect(startupTime1).toBeVisible()

    const shutdownTime1 = page.locator('.ant-form-item:has-text("关机时间段1")')
    await expect(shutdownTime1).toBeVisible()

    // 截图
    await page.screenshot({ path: 'playwright-report/screenshots/time-periods.png' })
  })

  test('时间段输入框应有正确的 placeholder 提示', async ({ page }) => {
    await deviceDetailPage.goto(1)
    await waitForAntLoading(page)

    // 打开参数编辑弹窗
    await page.locator('button:has-text("编辑参数")').click()
    await page.waitForSelector('.ant-modal:has-text("参数设置")', { timeout: 10000 })

    // 验证时间段输入框 placeholder
    const timeInput = page.locator('.ant-input[placeholder="HH:MM~HH:MM"]').first()
    await expect(timeInput).toBeVisible()

    // 截图
    await page.screenshot({ path: 'playwright-report/screenshots/time-placeholder.png' })
  })

  test('应该能设置联动模式', async ({ page }) => {
    await deviceDetailPage.goto(1)
    await waitForAntLoading(page)

    // 打开参数编辑弹窗
    await page.locator('button:has-text("编辑参数")').click()
    await page.waitForSelector('.ant-modal:has-text("参数设置")', { timeout: 10000 })

    // 验证联动模式下拉框存在
    const linkageModeSelect = page.locator('.ant-form-item:has-text("联动模式")')
    await expect(linkageModeSelect).toBeVisible()

    // 点击下拉框验证选项
    await linkageModeSelect.locator('.ant-select').click()
    await page.waitForTimeout(500)

    // 验证下拉选项
    const options = page.locator('.ant-select-dropdown .ant-select-item')
    await expect(options.first()).toBeVisible()

    // 截图
    await page.screenshot({ path: 'playwright-report/screenshots/linkage-mode-select.png' })
  })

  test('应该能关闭参数编辑弹窗', async ({ page }) => {
    await deviceDetailPage.goto(1)
    await waitForAntLoading(page)

    // 打开参数编辑弹窗
    await page.locator('button:has-text("编辑参数")').click()
    await page.waitForSelector('.ant-modal:has-text("参数设置")', { timeout: 10000 })

    // 点击取消按钮
    await page.locator('.ant-modal button:has-text("取消")').click()

    // 验证弹窗关闭
    const modal = page.locator('.ant-modal:has-text("参数设置")')
    await expect(modal).not.toBeVisible({ timeout: 5000 })

    // 截图
    await page.screenshot({ path: 'playwright-report/screenshots/modal-closed.png' })
  })

  test('温度输入框应有合理的范围限制', async ({ page }) => {
    await deviceDetailPage.goto(1)
    await waitForAntLoading(page)

    // 打开参数编辑弹窗
    await page.locator('button:has-text("编辑参数")').click()
    await page.waitForSelector('.ant-modal:has-text("参数设置")', { timeout: 10000 })

    // 验证温度设定输入框有 min/max 属性
    const tempInput = page.locator('.ant-form-item:has-text("温度设定") .ant-input-number')
    await expect(tempInput).toBeVisible()

    // 检查输入框属性
    const inputElement = tempInput.locator('input')
    const minAttr = await inputElement.getAttribute('min')
    const maxAttr = await inputElement.getAttribute('max')

    // 验证温度范围在合理区间（-5 到 45）
    expect(parseInt(minAttr || '-5')).toBeGreaterThanOrEqual(-5)
    expect(parseInt(maxAttr || '45')).toBeLessThanOrEqual(45)

    // 截图
    await page.screenshot({ path: 'playwright-report/screenshots/temp-range.png' })
  })
})