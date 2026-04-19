/**
 * 全面功能测试 - 覆盖所有页面
 * 用于测试管理后台所有功能并截图记录
 */
import { test, expect } from '@playwright/test'
import { TEST_USER, performLogin, waitForAntLoading, takeScreenshot } from './utils/test-helpers'

test.describe('全面功能测试', () => {

  // ==========================================
  // 1. 登录页面测试
  // ==========================================
  test.describe('登录页面', () => {
    test('应该显示登录页面并截图', async ({ page }) => {
      await page.goto('/login')
      await page.waitForSelector('.login-container')

      // 验证关键元素
      await expect(page.locator('.brand')).toContainText('BNIoT')
      await expect(page.locator('.login-form')).toBeVisible()
      await expect(page.locator('input[placeholder="请输入用户名"]')).toBeVisible()
      await expect(page.locator('input[placeholder="请输入密码"]')).toBeVisible()

      await takeScreenshot(page, '01-login-page')
    })

    test('应该成功登录并跳转到仪表盘', async ({ page }) => {
      await performLogin(page)
      await expect(page).toHaveURL(/dashboard/)
      await takeScreenshot(page, '02-login-success-dashboard')
    })

    test('应该显示登录表单验证错误', async ({ page }) => {
      await page.goto('/login')
      await page.waitForSelector('.login-container')
      await page.click('.login-btn')
      await page.waitForTimeout(500)
      await takeScreenshot(page, '03-login-validation-error')
    })

    test('应该显示登录失败错误提示', async ({ page }) => {
      await page.goto('/login')
      await page.waitForSelector('.login-container')
      await page.fill('input[placeholder="请输入用户名"]', 'wronguser')
      await page.fill('input[placeholder="请输入密码"]', 'wrongpass')
      await page.click('.login-btn')
      await page.waitForTimeout(2000)
      await takeScreenshot(page, '04-login-failure')
    })
  })

  // ==========================================
  // 2. 仪表盘/Dashboard 测试
  // ==========================================
  test.describe('仪表盘', () => {
    test.beforeEach(async ({ page }) => {
      await performLogin(page)
    })

    test('应该显示仪表盘所有统计卡片', async ({ page }) => {
      await page.waitForSelector('.dashboard')
      await waitForAntLoading(page)

      // 验证统计卡片
      const statCards = page.locator('.stat-card')
      await expect(statCards).toHaveCount(4)

      // 验证卡片内容
      await expect(page.locator('.stat-label').first()).toContainText('设备总数')
      await takeScreenshot(page, '05-dashboard-stats')
    })

    test('应该显示设备状态面板', async ({ page }) => {
      await page.waitForSelector('.devices-panel')
      await expect(page.locator('.panel-title').first()).toContainText('设备状态')
      await takeScreenshot(page, '06-dashboard-devices-panel')
    })

    test('应该显示告警面板', async ({ page }) => {
      await page.waitForSelector('.alarms-panel')
      await expect(page.locator('.panel-title').nth(1)).toContainText('最新告警')
      await takeScreenshot(page, '07-dashboard-alarms-panel')
    })

    test('应该显示系统信息栏', async ({ page }) => {
      await page.waitForSelector('.system-bar')
      await expect(page.locator('.bar-item').first()).toContainText('系统版本')
      await takeScreenshot(page, '08-dashboard-system-bar')
    })

    test('应该能刷新数据', async ({ page }) => {
      await page.waitForSelector('.refresh-btn')
      await page.click('.refresh-btn')
      await page.waitForTimeout(1000)
      await takeScreenshot(page, '09-dashboard-refresh')
    })

    test('应该能通过快速操作按钮导航', async ({ page }) => {
      // 点击设备管理按钮
      await page.waitForSelector('.action-btn')
      await page.click('.action-btn:first-child')
      await page.waitForURL(/devices/)
      await expect(page).toHaveURL(/devices/)
      await takeScreenshot(page, '10-dashboard-quick-action-devices')
    })
  })

  // ==========================================
  // 3. 设备管理页面测试
  // ==========================================
  test.describe('设备管理', () => {
    test.beforeEach(async ({ page }) => {
      await performLogin(page)
      await page.goto('/devices')
      await waitForAntLoading(page)
    })

    test('应该显示设备管理页面', async ({ page }) => {
      await expect(page.locator('.toolbar-card')).toBeVisible()
      await expect(page.locator('.table-card')).toBeVisible()
      await takeScreenshot(page, '11-devices-page')
    })

    test('应该显示搜索和过滤功能', async ({ page }) => {
      await expect(page.locator('input[placeholder="搜索设备号、名称、SIM卡、固件版本、分区"]')).toBeVisible()
      await expect(page.locator('.ant-select')).toHaveCount(3) // 分区、协议版本、在线状态筛选
      await takeScreenshot(page, '12-devices-toolbar')
    })

    test('应该显示添加设备按钮', async ({ page }) => {
      await expect(page.locator('button:has-text("添加设备")')).toBeVisible()
      await takeScreenshot(page, '13-devices-add-button')
    })

    test('应该能打开添加设备弹窗', async ({ page }) => {
      await page.click('button:has-text("添加设备")')
      await page.waitForSelector('.ant-modal-content')
      await expect(page.locator('.ant-modal-title')).toContainText('添加设备')
      await takeScreenshot(page, '14-devices-add-modal')
      await page.click('.ant-modal-close')
    })

    test('应该显示设备表格列', async ({ page }) => {
      const columns = ['设备号', '设备名称', '温度', '湿度', '告警状态', '协议版本', '分区', '在线状态', '最后通信', '操作']
      for (const col of columns) {
        await expect(page.locator(`th:has-text("${col}")`)).toBeVisible()
      }
      await takeScreenshot(page, '15-devices-table-columns')
    })

    test('应该能搜索设备', async ({ page }) => {
      await page.fill('input[placeholder="搜索设备号、名称、SIM卡、固件版本、分区"]', 'test')
      // 按 Enter 键触发搜索
      await page.press('input[placeholder="搜索设备号、名称、SIM卡、固件版本、分区"]', 'Enter')
      await page.waitForTimeout(500)
      await takeScreenshot(page, '16-devices-search')
    })

    test('应该能点击设备查看详情', async ({ page }) => {
      // 等待表格加载
      await waitForAntLoading(page)

      // 尝试点击第一个设备名称链接（如果有）
      const deviceLink = page.locator('a:has-text("详情")').first()
      if (await deviceLink.isVisible()) {
        await deviceLink.click()
        await page.waitForURL(/devices\/\d+/)
        await takeScreenshot(page, '17-device-detail-page')
      } else {
        // 如果没有设备，截图空表格状态
        await takeScreenshot(page, '17-devices-empty-table')
      }
    })

    test('应该能打开设备更多操作菜单', async ({ page }) => {
      await waitForAntLoading(page)
      const moreButton = page.locator('button:has-text("更多")').first()
      if (await moreButton.isVisible()) {
        await moreButton.click()
        await page.waitForSelector('.ant-dropdown-menu')
        await takeScreenshot(page, '18-devices-more-menu')
        await page.keyboard.press('Escape')
      } else {
        await takeScreenshot(page, '18-devices-no-more-menu')
      }
    })
  })

  // ==========================================
  // 4. 设备详情页测试
  // ==========================================
  test.describe('设备详情', () => {
    test.beforeEach(async ({ page }) => {
      await performLogin(page)
      await page.goto('/devices')
      await waitForAntLoading(page)
    })

    test('应该显示设备详情页面结构', async ({ page }) => {
      // 先查看是否有设备
      const deviceLink = page.locator('a').filter({ hasText: /[^\s]+/ }).first()
      if (await deviceLink.isVisible()) {
        await deviceLink.click()
        await page.waitForURL(/devices\/\d+/)

        // 验证页面结构
        await expect(page.locator('.device-detail')).toBeVisible()
        await expect(page.locator('.ant-page-header')).toBeVisible()
        await expect(page.locator('button:has-text("开机")')).toBeVisible()
        await expect(page.locator('button:has-text("关机")')).toBeVisible()

        await takeScreenshot(page, '19-device-detail-full')
      } else {
        // 没有设备时截图设备列表空状态
        await takeScreenshot(page, '19-no-devices-for-detail')
      }
    })
  })

  // ==========================================
  // 5. 分区管理测试
  // ==========================================
  test.describe('分区管理', () => {
    test.beforeEach(async ({ page }) => {
      await performLogin(page)
      await page.goto('/zones')
      await waitForAntLoading(page)
    })

    test('应该显示分区管理页面', async ({ page }) => {
      await expect(page.locator('.zones-page')).toBeVisible()
      await expect(page.locator('.ant-card:has-text("分区结构")')).toBeVisible()
      await expect(page.locator('.ant-card:has-text("分区详情")')).toBeVisible()
      await takeScreenshot(page, '20-zones-page')
    })

    test('应该显示添加分区按钮', async ({ page }) => {
      await expect(page.locator('button:has-text("添加")')).toBeVisible()
      await takeScreenshot(page, '21-zones-add-button')
    })

    test('应该能打开添加分区弹窗', async ({ page }) => {
      await page.click('button:has-text("添加")')
      await page.waitForSelector('.ant-modal-content')
      await expect(page.locator('.ant-modal-title')).toContainText('添加分区')
      await takeScreenshot(page, '22-zones-add-modal')
      await page.click('.ant-modal-close')
    })

    test('应该显示分区树结构', async ({ page }) => {
      await waitForAntLoading(page)
      const treeVisible = await page.locator('.ant-tree').isVisible()
      if (treeVisible) {
        await expect(page.locator('.ant-tree')).toBeVisible()
        await takeScreenshot(page, '23-zones-tree')
      } else {
        // 使用 first() 避免 strict mode violation
        await expect(page.locator('.ant-empty').first()).toBeVisible()
        await takeScreenshot(page, '23-zones-empty')
      }
    })
  })

  // ==========================================
  // 6. 告警中心测试
  // ==========================================
  test.describe('告警中心', () => {
    test.beforeEach(async ({ page }) => {
      await performLogin(page)
      await page.goto('/alarms')
      await waitForAntLoading(page)
    })

    test('应该显示告警中心页面', async ({ page }) => {
      await expect(page.locator('.alarms-page')).toBeVisible()
      await expect(page.locator('.page-title')).toContainText('告警中心')
      await takeScreenshot(page, '24-alarms-page')
    })

    test('应该显示过滤器栏', async ({ page }) => {
      await expect(page.locator('.filter-bar')).toBeVisible()
      await expect(page.locator('.filter-label').first()).toContainText('状态')
      await takeScreenshot(page, '25-alarms-filters')
    })

    test('应该显示批量处理按钮', async ({ page }) => {
      await expect(page.locator('button:has-text("批量处理")')).toBeVisible()
      await takeScreenshot(page, '26-alarms-batch-button')
    })

    test('应该显示告警表格', async ({ page }) => {
      await expect(page.locator('.alarms-table-container')).toBeVisible()
      await takeScreenshot(page, '27-alarms-table')
    })

    test('应该能筛选告警状态', async ({ page }) => {
      const statusSelect = page.locator('.filter-group .ant-select').first()
      await statusSelect.click()
      await page.waitForSelector('.ant-select-dropdown')
      await takeScreenshot(page, '28-alarms-status-filter-dropdown')
      await page.keyboard.press('Escape')
    })
  })

  // ==========================================
  // 7. 报表分析测试
  // ==========================================
  test.describe('报表分析', () => {
    test.beforeEach(async ({ page }) => {
      await performLogin(page)
      await page.goto('/reports')
      await waitForAntLoading(page)
    })

    test('应该显示报表页面', async ({ page }) => {
      await expect(page.locator('.reports-page')).toBeVisible()
      await expect(page.locator('.page-header h2')).toContainText('报表分析')
      await takeScreenshot(page, '29-reports-page')
    })

    test('应该显示查询面板', async ({ page }) => {
      await expect(page.locator('.query-panel')).toBeVisible()
      // 检查日期范围选择器（使用更通用的选择器）
      const datePicker = page.locator('.ant-picker-range')
      if (await datePicker.isVisible()) {
        await expect(datePicker).toBeVisible()
      }
      await takeScreenshot(page, '30-reports-query-panel')
    })

    test('应该显示四个Tab页', async ({ page }) => {
      const tabs = ['能耗统计', '温湿度趋势', '告警统计', '运行时长']
      for (const tab of tabs) {
        await expect(page.locator(`.ant-tabs-tab:has-text("${tab}")`)).toBeVisible()
      }
      await takeScreenshot(page, '31-reports-tabs')
    })

    test('应该能切换Tab页', async ({ page }) => {
      // 切换到温湿度趋势
      await page.click('.ant-tabs-tab:has-text("温湿度趋势")')
      await page.waitForTimeout(500)
      await takeScreenshot(page, '32-reports-trend-tab')

      // 切换到告警统计
      await page.click('.ant-tabs-tab:has-text("告警统计")')
      await page.waitForTimeout(500)
      await takeScreenshot(page, '33-reports-alarm-tab')

      // 切换到运行时长
      await page.click('.ant-tabs-tab:has-text("运行时长")')
      await page.waitForTimeout(500)
      await takeScreenshot(page, '34-reports-runtime-tab')
    })

    test('应该显示数据表格', async ({ page }) => {
      await page.waitForSelector('.ant-table')
      await takeScreenshot(page, '35-reports-data-table')
    })
  })

  // ==========================================
  // 8. 用户管理测试 (仅管理员可见)
  // ==========================================
  test.describe('用户管理', () => {
    test.beforeEach(async ({ page }) => {
      await performLogin(page)
      // 使用 admin 用户登录应该能看到用户管理
    })

    test('管理员应该能看到用户管理菜单', async ({ page }) => {
      await page.waitForSelector('.sidebar-menu')
      const userMenuItem = page.locator('.ant-menu-item:has-text("用户管理")')
      // admin 用户应该能看到用户管理
      await expect(userMenuItem).toBeVisible()
      await takeScreenshot(page, '36-users-menu-visible')
    })

    test('应该显示用户管理页面', async ({ page }) => {
      await page.goto('/users')
      await waitForAntLoading(page)
      await expect(page.locator('.users-page')).toBeVisible()
      await expect(page.locator('.ant-card:has-text("用户管理")')).toBeVisible()
      await takeScreenshot(page, '37-users-page')
    })

    test('应该显示添加用户按钮', async ({ page }) => {
      await page.goto('/users')
      await waitForAntLoading(page)
      await expect(page.locator('button:has-text("添加用户")')).toBeVisible()
      await takeScreenshot(page, '38-users-add-button')
    })

    test('应该能打开添加用户弹窗', async ({ page }) => {
      await page.goto('/users')
      await waitForAntLoading(page)
      await page.click('button:has-text("添加用户")')
      await page.waitForSelector('.ant-modal-content')
      await expect(page.locator('.ant-modal-title')).toContainText('添加用户')
      await takeScreenshot(page, '39-users-add-modal')
      await page.click('.ant-modal-close')
    })
  })

  // ==========================================
  // 9. 系统设置测试
  // ==========================================
  test.describe('系统设置', () => {
    test.beforeEach(async ({ page }) => {
      await performLogin(page)
      await page.goto('/settings')
      await waitForAntLoading(page)
    })

    test('应该显示设置页面', async ({ page }) => {
      await expect(page.locator('.settings-page')).toBeVisible()
      await expect(page.locator('.page-title')).toContainText('系统设置')
      await takeScreenshot(page, '40-settings-page')
    })

    test('应该显示外观设置', async ({ page }) => {
      await expect(page.locator('.section-title:has-text("外观设置")')).toBeVisible()
      await expect(page.locator('.setting-label:has-text("主题模式")')).toBeVisible()
      await expect(page.locator('.setting-label:has-text("显示动画效果")')).toBeVisible()
      await takeScreenshot(page, '41-settings-appearance')
    })

    test('应该显示通知设置', async ({ page }) => {
      await expect(page.locator('.section-title:has-text("通知设置")')).toBeVisible()
      await takeScreenshot(page, '42-settings-notification')
    })

    test('应该显示数据刷新设置', async ({ page }) => {
      await expect(page.locator('.section-title:has-text("数据刷新")')).toBeVisible()
      await takeScreenshot(page, '43-settings-refresh')
    })

    test('应该显示系统信息', async ({ page }) => {
      await expect(page.locator('.section-title:has-text("系统信息")')).toBeVisible()
      await takeScreenshot(page, '44-settings-system-info')
    })

    test('应该能切换主题', async ({ page }) => {
      // 使用更精确的选择器点击主题选项
      const lightThemeRadio = page.locator('.ant-radio-group').locator('input[type="radio"]').nth(1)
      await lightThemeRadio.click({ force: true })
      await page.waitForTimeout(500)
      await takeScreenshot(page, '45-settings-light-theme')

      // 点击深色主题
      const darkThemeRadio = page.locator('.ant-radio-group').locator('input[type="radio"]').first()
      await darkThemeRadio.click({ force: true })
      await page.waitForTimeout(500)
      await takeScreenshot(page, '46-settings-dark-theme')
    })
  })

  // ==========================================
  // 10. 用户下拉菜单测试
  // ==========================================
  test.describe('用户下拉菜单', () => {
    test.beforeEach(async ({ page }) => {
      await performLogin(page)
    })

    test('应该显示用户信息', async ({ page }) => {
      await page.waitForSelector('.user-info')
      await expect(page.locator('.user-name')).toContainText('admin')
      await expect(page.locator('.user-info .ant-avatar')).toBeVisible()
      await takeScreenshot(page, '47-user-info')
    })

    test('应该能打开用户下拉菜单', async ({ page }) => {
      await page.waitForSelector('.user-info')
      await page.click('.user-info')
      await page.waitForSelector('.user-menu')
      // 使用 role="menuitem" 选择器匹配实际结构
      await expect(page.locator('[role="menuitem"]:has-text("个人中心")')).toBeVisible()
      await expect(page.locator('[role="menuitem"]:has-text("退出登录")')).toBeVisible()
      await takeScreenshot(page, '48-user-dropdown-menu')
    })
  })

  // ==========================================
  // 11. 登出测试
  // ==========================================
  test.describe('登出流程', () => {
    test('应该能成功登出', async ({ page }) => {
      await performLogin(page)

      // 点击用户下拉菜单
      await page.waitForSelector('.user-info')
      await page.click('.user-info')
      await page.waitForSelector('.user-menu')

      // 使用 role="menuitem" 选择器
      await page.click('[role="menuitem"]:has-text("退出登录")')
      await page.waitForURL(/login/)
      await expect(page).toHaveURL(/login/)
      await takeScreenshot(page, '49-logout-success')
    })

    test('登出后应该清除认证状态', async ({ page }) => {
      await performLogin(page)

      // 登出
      await page.waitForSelector('.user-info')
      await page.click('.user-info')
      await page.waitForSelector('.user-menu')
      await page.click('[role="menuitem"]:has-text("退出登录")')
      await page.waitForURL(/login/)

      // 尝试访问需要认证的页面
      await page.goto('/dashboard')
      await page.waitForURL(/login/)
      await expect(page).toHaveURL(/login/)
      await takeScreenshot(page, '50-logout-redirect-to-login')
    })
  })

  // ==========================================
  // 12. 侧边栏导航测试
  // ==========================================
  test.describe('侧边栏导航', () => {
    test.beforeEach(async ({ page }) => {
      await performLogin(page)
    })

    test('应该显示侧边栏菜单项', async ({ page }) => {
      await page.waitForSelector('.sidebar-menu')
      const menuItems = ['仪表盘', '设备管理', '分区管理', '告警中心', '报表分析', '用户管理', '系统设置']
      for (const item of menuItems) {
        await expect(page.locator(`.ant-menu-item:has-text("${item}")`)).toBeVisible()
      }
      await takeScreenshot(page, '51-sidebar-menu')
    })

    test('应该能折叠侧边栏', async ({ page }) => {
      await page.waitForSelector('.collapse-btn')
      await page.click('.collapse-btn')
      await page.waitForTimeout(500)
      await takeScreenshot(page, '52-sidebar-collapsed')

      // 再次展开
      await page.click('.collapse-btn')
      await page.waitForTimeout(500)
      await takeScreenshot(page, '53-sidebar-expanded')
    })

    test('应该能通过侧边栏导航到各个页面', async ({ page }) => {
      // 导航到设备管理
      await page.click('.ant-menu-item:has-text("设备管理")')
      await page.waitForURL(/devices/)
      await takeScreenshot(page, '54-nav-to-devices')

      // 导航到分区管理
      await page.click('.ant-menu-item:has-text("分区管理")')
      await page.waitForURL(/zones/)
      await takeScreenshot(page, '55-nav-to-zones')

      // 导航到告警中心
      await page.click('.ant-menu-item:has-text("告警中心")')
      await page.waitForURL(/alarms/)
      await takeScreenshot(page, '56-nav-to-alarms')

      // 导航到报表分析
      await page.click('.ant-menu-item:has-text("报表分析")')
      await page.waitForURL(/reports/)
      await takeScreenshot(page, '57-nav-to-reports')

      // 导航到系统设置
      await page.click('.ant-menu-item:has-text("系统设置")')
      await page.waitForURL(/settings/)
      await takeScreenshot(page, '58-nav-to-settings')
    })
  })
})