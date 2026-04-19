/**
 * 简化版全面功能测试 - 专注于截图和功能验证
 */
import { test, expect } from '@playwright/test'

// 测试账户
const TEST_USER = {
  username: 'admin',
  password: 'admin123'
}

// 登录辅助函数
async function login(page: any) {
  await page.goto('/login')
  await page.waitForSelector('.login-container')
  await page.fill('input[placeholder="请输入用户名"]', TEST_USER.username)
  await page.fill('input[placeholder="请输入密码"]', TEST_USER.password)
  await page.click('.login-btn')
  await page.waitForURL(/dashboard/, { timeout: 15000 })
}

test.describe('全面功能测试', () => {

  // ==========================================
  // 1. 登录页面测试
  // ==========================================
  test('01-登录页面显示', async ({ page }) => {
    await page.goto('/login')
    await page.waitForSelector('.login-container')

    // 验证关键元素
    await expect(page.locator('.brand')).toContainText('BNIoT')
    await expect(page.locator('.login-form')).toBeVisible()

    await page.screenshot({ path: '/home/leon/projects/bniot/e2e-screenshots/01-login-page.png', fullPage: true })
  })

  test('02-成功登录', async ({ page }) => {
    await login(page)
    await expect(page).toHaveURL(/dashboard/)
    await page.screenshot({ path: '/home/leon/projects/bniot/e2e-screenshots/02-login-success.png', fullPage: true })
  })

  // ==========================================
  // 2. 仪表盘测试
  // ==========================================
  test('03-仪表盘页面', async ({ page }) => {
    await login(page)

    await page.waitForSelector('.dashboard', { timeout: 10000 })

    // 验证统计卡片
    const statCards = page.locator('.stat-card')
    const count = await statCards.count()
    expect(count).toBeGreaterThanOrEqual(4)

    // 验证刷新按钮
    await expect(page.locator('.refresh-btn')).toBeVisible()

    await page.screenshot({ path: '/home/leon/projects/bniot/e2e-screenshots/03-dashboard.png', fullPage: true })
  })

  // ==========================================
  // 3. 设备管理测试
  // ==========================================
  test('04-设备管理页面', async ({ page }) => {
    await login(page)
    await page.goto('/devices')
    await page.waitForSelector('.devices-page', { timeout: 10000 })

    // 验证工具栏
    await expect(page.locator('.toolbar-card')).toBeVisible()
    await expect(page.locator('.table-card')).toBeVisible()

    // 验证添加设备按钮
    await expect(page.locator('button:has-text("添加设备")')).toBeVisible()

    await page.screenshot({ path: '/home/leon/projects/bniot/e2e-screenshots/04-devices.png', fullPage: true })
  })

  test('05-添加设备弹窗', async ({ page }) => {
    await login(page)
    await page.goto('/devices')
    await page.waitForSelector('.devices-page', { timeout: 10000 })

    await page.click('button:has-text("添加设备")')
    await page.waitForSelector('.ant-modal-content', { timeout: 5000 })

    await expect(page.locator('.ant-modal-title')).toContainText('添加设备')

    await page.screenshot({ path: '/home/leon/projects/bniot/e2e-screenshots/05-add-device-modal.png', fullPage: true })

    // 关闭弹窗
    await page.click('.ant-modal-close')
  })

  // ==========================================
  // 4. 设备详情测试
  // ==========================================
  test('06-设备详情页面', async ({ page }) => {
    await login(page)
    await page.goto('/devices')
    await page.waitForSelector('.devices-page', { timeout: 10000 })

    // 查看是否有设备可以点击
    const detailButtons = page.locator('button:has-text("详情")')
    const count = await detailButtons.count()

    if (count > 0) {
      await detailButtons.first().click()
      await page.waitForSelector('.device-detail', { timeout: 10000 })

      // 验证控制按钮
      await expect(page.locator('button:has-text("开机")')).toBeVisible()
      await expect(page.locator('button:has-text("关机")')).toBeVisible()

      await page.screenshot({ path: '/home/leon/projects/bniot/e2e-screenshots/06-device-detail.png', fullPage: true })
    } else {
      // 没有设备时，截图空表格状态
      await page.screenshot({ path: '/home/leon/projects/bniot/e2e-screenshots/06-no-devices.png', fullPage: true })
    }
  })

  // ==========================================
  // 5. 分区管理测试
  // ==========================================
  test('07-分区管理页面', async ({ page }) => {
    await login(page)
    await page.goto('/zones')
    await page.waitForSelector('.zones-page', { timeout: 10000 })

    // 验证分区结构和详情卡片
    await expect(page.locator('.ant-card:has-text("分区结构")')).toBeVisible()
    await expect(page.locator('.ant-card:has-text("分区详情")')).toBeVisible()

    await page.screenshot({ path: '/home/leon/projects/bniot/e2e-screenshots/07-zones.png', fullPage: true })
  })

  test('08-添加分区弹窗', async ({ page }) => {
    await login(page)
    await page.goto('/zones')
    await page.waitForSelector('.zones-page', { timeout: 10000 })

    await page.click('button:has-text("添加")')
    await page.waitForSelector('.ant-modal-content', { timeout: 5000 })

    await expect(page.locator('.ant-modal-title')).toContainText('添加分区')

    await page.screenshot({ path: '/home/leon/projects/bniot/e2e-screenshots/08-add-zone-modal.png', fullPage: true })

    // 关闭弹窗
    await page.click('.ant-modal-close')
  })

  // ==========================================
  // 6. 告警中心测试
  // ==========================================
  test('09-告警中心页面', async ({ page }) => {
    await login(page)
    await page.goto('/alarms')
    await page.waitForSelector('.alarms-page', { timeout: 10000 })

    // 验证过滤器
    await expect(page.locator('.filter-bar')).toBeVisible()

    // 验证批量处理按钮
    await expect(page.locator('button:has-text("批量处理")')).toBeVisible()

    await page.screenshot({ path: '/home/leon/projects/bniot/e2e-screenshots/09-alarms.png', fullPage: true })
  })

  // ==========================================
  // 7. 报表分析测试
  // ==========================================
  test('10-报表分析页面', async ({ page }) => {
    await login(page)
    await page.goto('/reports')
    await page.waitForSelector('.reports-page', { timeout: 10000 })

    // 验证查询面板存在
    const queryPanel = page.locator('.query-panel')
    await expect(queryPanel).toBeVisible()

    // 验证Tab页
    const tabs = ['能耗统计', '温湿度趋势', '告警统计', '运行时长']
    for (const tab of tabs) {
      await expect(page.locator(`.ant-tabs-tab:has-text("${tab}")`)).toBeVisible()
    }

    await page.screenshot({ path: '/home/leon/projects/bniot/e2e-screenshots/10-reports.png', fullPage: true })
  })

  test('11-报表Tab切换', async ({ page }) => {
    await login(page)
    await page.goto('/reports')
    await page.waitForSelector('.reports-page', { timeout: 10000 })

    // 切换到温湿度趋势
    await page.click('.ant-tabs-tab:has-text("温湿度趋势")')
    await page.waitForTimeout(500)
    await page.screenshot({ path: '/home/leon/projects/bniot/e2e-screenshots/11-reports-trend.png', fullPage: true })

    // 切换到告警统计
    await page.click('.ant-tabs-tab:has-text("告警统计")')
    await page.waitForTimeout(500)
    await page.screenshot({ path: '/home/leon/projects/bniot/e2e-screenshots/12-reports-alarm.png', fullPage: true })
  })

  // ==========================================
  // 8. 用户管理测试
  // ==========================================
  test('12-用户管理页面', async ({ page }) => {
    await login(page)
    await page.goto('/users')
    await page.waitForSelector('.users-page', { timeout: 10000 })

    // 验证用户管理卡片
    await expect(page.locator('.ant-card:has-text("用户管理")')).toBeVisible()

    // 验证添加用户按钮
    await expect(page.locator('button:has-text("添加用户")')).toBeVisible()

    await page.screenshot({ path: '/home/leon/projects/bniot/e2e-screenshots/13-users.png', fullPage: true })
  })

  test('13-添加用户弹窗', async ({ page }) => {
    await login(page)
    await page.goto('/users')
    await page.waitForSelector('.users-page', { timeout: 10000 })

    await page.click('button:has-text("添加用户")')
    await page.waitForSelector('.ant-modal-content', { timeout: 5000 })

    await expect(page.locator('.ant-modal-title')).toContainText('添加用户')

    await page.screenshot({ path: '/home/leon/projects/bniot/e2e-screenshots/14-add-user-modal.png', fullPage: true })

    // 关闭弹窗
    await page.click('.ant-modal-close')
  })

  // ==========================================
  // 9. 系统设置测试
  // ==========================================
  test('14-系统设置页面', async ({ page }) => {
    await login(page)
    await page.goto('/settings')
    await page.waitForSelector('.settings-page', { timeout: 10000 })

    // 验证设置区块
    await expect(page.locator('.section-title:has-text("外观设置")')).toBeVisible()
    await expect(page.locator('.section-title:has-text("通知设置")')).toBeVisible()
    await expect(page.locator('.section-title:has-text("数据刷新")')).toBeVisible()
    await expect(page.locator('.section-title:has-text("系统信息")')).toBeVisible()

    await page.screenshot({ path: '/home/leon/projects/bniot/e2e-screenshots/15-settings.png', fullPage: true })
  })

  test('15-主题切换测试', async ({ page }) => {
    await login(page)
    await page.goto('/settings')
    await page.waitForSelector('.settings-page', { timeout: 10000 })

    // 使用 radio-group 中的 radio input
    const radioGroup = page.locator('.ant-radio-group')
    await expect(radioGroup).toBeVisible()

    // 点击"浅色"选项（第二个 radio）
    await radioGroup.locator('input[type="radio"]').nth(1).click({ force: true })
    await page.waitForTimeout(300)
    await page.screenshot({ path: '/home/leon/projects/bniot/e2e-screenshots/16-settings-light-theme.png', fullPage: true })

    // 点击"深色"选项（第一个 radio）
    await radioGroup.locator('input[type="radio"]').first().click({ force: true })
    await page.waitForTimeout(300)
    await page.screenshot({ path: '/home/leon/projects/bniot/e2e-screenshots/17-settings-dark-theme.png', fullPage: true })
  })

  // ==========================================
  // 10. 用户下拉菜单和登出测试
  // ==========================================
  test('16-用户下拉菜单', async ({ page }) => {
    await login(page)
    await page.waitForSelector('.user-info', { timeout: 10000 })

    // 点击用户信息打开下拉菜单
    await page.click('.user-info')
    await page.waitForTimeout(500)

    // 验证下拉菜单可见
    const dropdown = page.locator('.ant-dropdown')
    await expect(dropdown).toBeVisible()

    await page.screenshot({ path: '/home/leon/projects/bniot/e2e-screenshots/18-user-dropdown.png', fullPage: true })
  })

  test('17-登出功能', async ({ page }) => {
    await login(page)
    await page.waitForSelector('.user-info', { timeout: 10000 })

    // 打开下拉菜单
    await page.click('.user-info')
    await page.waitForTimeout(500)

    // 点击退出登录
    await page.locator('.ant-dropdown-menu-item:has-text("退出登录")').click()
    await page.waitForURL(/login/, { timeout: 10000 })

    await expect(page).toHaveURL(/login/)
    await page.screenshot({ path: '/home/leon/projects/bniot/e2e-screenshots/19-logout-success.png', fullPage: true })
  })

  // ==========================================
  // 11. 侧边栏导航测试
  // ==========================================
  test('18-侧边栏折叠', async ({ page }) => {
    await login(page)
    await page.waitForSelector('.sidebar', { timeout: 10000 })

    // 点击折叠按钮
    await page.click('.collapse-btn')
    await page.waitForTimeout(500)
    await page.screenshot({ path: '/home/leon/projects/bniot/e2e-screenshots/20-sidebar-collapsed.png', fullPage: true })

    // 再次展开
    await page.click('.collapse-btn')
    await page.waitForTimeout(500)
    await page.screenshot({ path: '/home/leon/projects/bniot/e2e-screenshots/21-sidebar-expanded.png', fullPage: true })
  })

  test('19-侧边栏导航到各页面', async ({ page }) => {
    await login(page)
    await page.waitForSelector('.sidebar-menu', { timeout: 10000 })

    // 导航到设备管理
    await page.locator('.ant-menu-item:has-text("设备管理")').click()
    await page.waitForURL(/devices/)
    await page.screenshot({ path: '/home/leon/projects/bniot/e2e-screenshots/22-nav-devices.png', fullPage: true })

    // 导航到分区管理
    await page.locator('.ant-menu-item:has-text("分区管理")').click()
    await page.waitForURL(/zones/)
    await page.screenshot({ path: '/home/leon/projects/bniot/e2e-screenshots/23-nav-zones.png', fullPage: true })

    // 导航到告警中心
    await page.locator('.ant-menu-item:has-text("告警中心")').click()
    await page.waitForURL(/alarms/)
    await page.screenshot({ path: '/home/leon/projects/bniot/e2e-screenshots/24-nav-alarms.png', fullPage: true })

    // 导航到报表分析
    await page.locator('.ant-menu-item:has-text("报表分析")').click()
    await page.waitForURL(/reports/)
    await page.screenshot({ path: '/home/leon/projects/bniot/e2e-screenshots/25-nav-reports.png', fullPage: true })

    // 导航到用户管理
    await page.locator('.ant-menu-item:has-text("用户管理")').click()
    await page.waitForURL(/users/)
    await page.screenshot({ path: '/home/leon/projects/bniot/e2e-screenshots/26-nav-users.png', fullPage: true })

    // 导航到系统设置
    await page.locator('.ant-menu-item:has-text("系统设置")').click()
    await page.waitForURL(/settings/)
    await page.screenshot({ path: '/home/leon/projects/bniot/e2e-screenshots/27-nav-settings.png', fullPage: true })
  })
})