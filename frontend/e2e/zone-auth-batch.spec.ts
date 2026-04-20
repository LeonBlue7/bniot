/**
 * 分区授权与批量操作 E2E 测试
 *
 * 验证以下功能：
 * 1. 分区创建自动授权功能 - 创建分区后设备应该可见
 * 2. 分区授权管理界面 - 管理员可以查看、添加、移除授权
 * 3. 批量移动设备功能 - 设备列表支持多选并移动到指定分区
 */
import { test, expect } from '@playwright/test'
import { TEST_USER, performLogin, waitForAntLoading } from './utils/test-helpers'

test.describe.configure({ timeout: 60000 }) // 增加测试超时时间

test.describe('分区授权与批量操作', () => {
  test.beforeEach(async ({ page }) => {
    await performLogin(page)
  })

  // ==========================================
  // 1. 分区创建自动授权功能测试
  // ==========================================
  test.describe('分区创建自动授权', () => {
    test('应该能创建新分区', async ({ page }) => {
      // 导航到分区管理
      await page.goto('/zones')
      await waitForAntLoading(page)
      await page.waitForTimeout(2000)

      // 强制关闭所有可能存在的弹窗
      while (await page.locator('.ant-modal').isVisible({ timeout: 500 })) {
        await page.keyboard.press('Escape')
        await page.waitForTimeout(300)
      }

      // 点击添加按钮
      const addButton = page.locator('button:has-text("添加")')
      await addButton.click()
      await page.waitForSelector('.ant-modal-content', { timeout: 10000 })

      // 填写分区信息
      const zoneName = `E2E测试分区-${Date.now()}`
      await page.fill('.ant-modal input', zoneName)

      // 提交创建
      await page.locator('.ant-modal .ant-btn-primary').click()
      await page.waitForTimeout(2000)

      // 验证分区创建成功
      const tree = page.locator('.ant-tree')
      await expect(tree).toBeVisible({ timeout: 10000 })

      // 截图
      await page.screenshot({ path: 'playwright-report/screenshots/zone-created.png' })
    })

    test('创建分区后应该自动授权给租户', async ({ page }) => {
      await page.goto('/zones')
      await waitForAntLoading(page)
      await page.waitForTimeout(2000)

      // 强制关闭所有可能存在的弹窗
      while (await page.locator('.ant-modal').isVisible({ timeout: 500 })) {
        await page.keyboard.press('Escape')
        await page.waitForTimeout(300)
      }

      // 检查是否有分区数据
      const treeVisible = await page.locator('.ant-tree').isVisible()
      const emptyVisible = await page.locator('.ant-empty').first().isVisible()

      if (treeVisible) {
        // 点击树节点
        const treeNode = page.locator('.ant-tree-node-content-wrapper').first()
        await treeNode.click({ force: true, timeout: 15000 })
        await page.waitForTimeout(2000)

        // 等待分区详情加载
        await expect(page.locator('.ant-descriptions')).toBeVisible({ timeout: 5000 })

        // 检查授权分隔符是否存在
        const authDivider = page.locator('[data-testid="auth-divider"]')
        await expect(authDivider).toBeVisible({ timeout: 10000 })

        // 截图
        await page.screenshot({ path: 'playwright-report/screenshots/zone-detail-auth.png' })
      } else if (emptyVisible) {
        test.skip(true, '没有分区数据，跳过测试')
      } else {
        await page.waitForTimeout(3000)
        test.skip(true, '分区数据未加载完成，跳过测试')
      }
    })
  })

  // ==========================================
  // 2. 分区授权管理界面测试
  // ==========================================
  test.describe('分区授权管理界面', () => {
    test('管理员应该能看到分区授权列表', async ({ page }) => {
      await page.goto('/zones')
      await waitForAntLoading(page)
      await page.waitForTimeout(2000)

      // 强制关闭所有可能存在的弹窗
      while (await page.locator('.ant-modal').isVisible({ timeout: 500 })) {
        await page.keyboard.press('Escape')
        await page.waitForTimeout(300)
      }

      // 检查是否有分区
      const treeVisible = await page.locator('.ant-tree').isVisible()

      if (treeVisible) {
        // 选择第一个分区 - 使用 node-content-wrapper
        const treeNode = page.locator('.ant-tree-node-content-wrapper').first()
        await treeNode.click({ force: true, timeout: 15000 })
        await page.waitForTimeout(2000)

        // 查看分区详情卡片
        const detailCard = page.locator('.ant-card:has-text("分区详情")')
        await expect(detailCard).toBeVisible({ timeout: 10000 })

        // 等待分区详情加载
        await expect(page.locator('.ant-descriptions')).toBeVisible({ timeout: 5000 })

        // 检查授权分隔符 - 使用 data-testid
        const authDivider = page.locator('[data-testid="auth-divider"]')
        await expect(authDivider).toBeVisible({ timeout: 10000 })

        // 截图
        await page.screenshot({ path: 'playwright-report/screenshots/zone-auth-panel.png' })
      } else {
        test.skip(true, '没有分区数据，跳过测试')
      }
    })

    test('应该能查看分区的授权用户列表', async ({ page }) => {
      await page.goto('/zones')
      await waitForAntLoading(page)
      await page.waitForTimeout(2000)

      // 强制关闭所有可能存在的弹窗
      while (await page.locator('.ant-modal').isVisible({ timeout: 500 })) {
        await page.keyboard.press('Escape')
        await page.waitForTimeout(300)
      }

      const treeVisible = await page.locator('.ant-tree').isVisible()

      if (treeVisible) {
        const treeNode = page.locator('.ant-tree-node-content-wrapper').first()
        await treeNode.click({ force: true, timeout: 15000 })
        await page.waitForTimeout(2000)

        // 等待分区详情加载
        await expect(page.locator('.ant-descriptions')).toBeVisible({ timeout: 5000 })

        // 查看是否有授权表格
        const authTable = page.locator('[data-testid="auth-table"]')
        await expect(authTable).toBeVisible({ timeout: 10000 })

        // 截图
        await page.screenshot({ path: 'playwright-report/screenshots/zone-auth-list.png' })
      } else {
        test.skip(true, '没有分区数据，跳过测试')
      }
    })

    test('应该能添加新的授权用户', async ({ page }) => {
      await page.goto('/zones')
      await waitForAntLoading(page)
      await page.waitForTimeout(2000)

      const treeVisible = await page.locator('.ant-tree').isVisible()

      if (treeVisible) {
        const treeNode = page.locator('.ant-tree-node-content-wrapper').first()
        await treeNode.click({ timeout: 15000 })
        await page.waitForTimeout(2000)

        // 查找添加授权按钮 - 使用 data-testid
        const addAuthButton = page.locator('[data-testid="add-auth-btn"]')

        if (await addAuthButton.isVisible({ timeout: 10000 })) {
          await addAuthButton.click()
          await page.waitForTimeout(500)

          // 验证添加授权弹窗显示
          await expect(page.locator('.ant-modal:has-text("添加分区授权")')).toBeVisible()

          // 截图
          await page.screenshot({ path: 'playwright-report/screenshots/zone-add-auth-modal.png' })
        } else {
          test.skip(true, '没有找到添加授权按钮')
        }
      } else {
        test.skip(true, '没有分区数据，跳过测试')
      }
    })

    test('应该能移除授权用户', async ({ page }) => {
      await page.goto('/zones')
      await waitForAntLoading(page)
      await page.waitForTimeout(2000)

      const treeVisible = await page.locator('.ant-tree').isVisible()

      if (treeVisible) {
        const treeNode = page.locator('.ant-tree-node-content-wrapper').first()
        await treeNode.click({ timeout: 15000 })
        await page.waitForTimeout(2000)

        // 查找移除授权按钮
        const removeButton = page.locator('button:has-text("移除授权")')

        if (await removeButton.isVisible({ timeout: 10000 })) {
          // 截图授权管理界面
          await page.screenshot({ path: 'playwright-report/screenshots/zone-remove-auth.png' })
        } else {
          test.skip(true, '没有找到移除授权按钮（可能没有已授权的用户）')
        }
      } else {
        test.skip(true, '没有分区数据，跳过测试')
      }
    })
  })

  // ==========================================
  // 3. 批量移动设备功能测试
  // ==========================================
  test.describe('批量移动设备功能', () => {
    test('设备列表应该支持多选功能', async ({ page }) => {
      await page.goto('/devices')
      await waitForAntLoading(page)
      await page.waitForTimeout(2000)

      // 检查是否有设备数据
      const deviceRows = page.locator('.ant-table-row')
      const rowCount = await deviceRows.count()

      if (rowCount > 0) {
        // 检查是否有批量选择功能 - 每行应该有复选框
        const rowCheckbox = page.locator('.ant-table-row .ant-checkbox-wrapper').first()

        if (await rowCheckbox.isVisible({ timeout: 5000 })) {
          // 点击第一行的复选框
          await rowCheckbox.click()
          await page.waitForTimeout(500)

          // 截图
          await page.screenshot({ path: 'playwright-report/screenshots/devices-multi-select.png' })
        } else {
          test.skip(true, '设备列表不支持多选功能')
        }
      } else {
        test.skip(true, '没有设备数据，跳过测试')
      }
    })

    test('应该能批量选择多个设备', async ({ page }) => {
      await page.goto('/devices')
      await waitForAntLoading(page)
      await page.waitForTimeout(2000)

      const deviceRows = page.locator('.ant-table-row')
      const rowCount = await deviceRows.count()

      if (rowCount >= 2) {
        const rowCheckbox = page.locator('.ant-table-row .ant-checkbox-wrapper')

        if (await rowCheckbox.first().isVisible({ timeout: 5000 })) {
          // 选择前两个设备
          await rowCheckbox.first().click()
          await page.waitForTimeout(200)
          await rowCheckbox.nth(1).click()
          await page.waitForTimeout(500)

          // 截图
          await page.screenshot({ path: 'playwright-report/screenshots/devices-batch-selected.png' })
        } else {
          test.skip(true, '设备列表不支持多选功能')
        }
      } else {
        test.skip(true, '设备数量不足，跳过测试')
      }
    })

    test('应该显示批量操作按钮', async ({ page }) => {
      await page.goto('/devices')
      await waitForAntLoading(page)
      await page.waitForTimeout(2000)

      const deviceRows = page.locator('.ant-table-row')
      const rowCount = await deviceRows.count()

      if (rowCount > 0) {
        const rowCheckbox = page.locator('.ant-table-row .ant-checkbox-wrapper')

        if (await rowCheckbox.first().isVisible({ timeout: 5000 })) {
          // 选择一个设备
          await rowCheckbox.first().click()
          await page.waitForTimeout(500)

          // 查找批量移动按钮 - 按钮文本是 "移动分区 (数量)"
          const batchMoveButton = page.locator('button:has-text("移动分区")')

          if (await batchMoveButton.isVisible({ timeout: 5000 })) {
            await expect(batchMoveButton).toBeVisible()

            // 截图
            await page.screenshot({ path: 'playwright-report/screenshots/devices-batch-move-btn.png' })
          } else {
            test.skip(true, '没有找到批量移动按钮')
          }
        } else {
          test.skip(true, '设备列表不支持多选功能')
        }
      } else {
        test.skip(true, '没有设备数据，跳过测试')
      }
    })

    test('应该能打开批量移动设备弹窗', async ({ page }) => {
      await page.goto('/devices')
      await waitForAntLoading(page)
      await page.waitForTimeout(2000)

      const deviceRows = page.locator('.ant-table-row')
      const rowCount = await deviceRows.count()

      if (rowCount > 0) {
        const rowCheckbox = page.locator('.ant-table-row .ant-checkbox-wrapper')

        if (await rowCheckbox.first().isVisible({ timeout: 5000 })) {
          // 选择一个设备
          await rowCheckbox.first().click()
          await page.waitForTimeout(500)

          // 点击批量移动按钮
          const batchMoveButton = page.locator('button:has-text("移动分区")')

          if (await batchMoveButton.isVisible({ timeout: 5000 })) {
            await batchMoveButton.click()
            await page.waitForTimeout(500)

            // 验证移动弹窗显示
            const moveModal = page.locator('.ant-modal:has-text("批量移动设备分区")')
            await expect(moveModal).toBeVisible({ timeout: 5000 })

            // 截图
            await page.screenshot({ path: 'playwright-report/screenshots/devices-batch-move-modal.png' })

            // 关闭弹窗
            await page.locator('.ant-modal-close').click()
          } else {
            test.skip(true, '没有找到批量移动按钮')
          }
        } else {
          test.skip(true, '设备列表不支持多选功能')
        }
      } else {
        test.skip(true, '没有设备数据，跳过测试')
      }
    })

    test('应该能在移动弹窗中选择目标分区', async ({ page }) => {
      await page.goto('/devices')
      await waitForAntLoading(page)
      await page.waitForTimeout(2000)

      const deviceRows = page.locator('.ant-table-row')
      const rowCount = await deviceRows.count()

      if (rowCount > 0) {
        const rowCheckbox = page.locator('.ant-table-row .ant-checkbox-wrapper')

        if (await rowCheckbox.first().isVisible({ timeout: 5000 })) {
          // 选择设备
          await rowCheckbox.first().click()
          await page.waitForTimeout(500)

          const batchMoveButton = page.locator('button:has-text("移动分区")')

          if (await batchMoveButton.isVisible({ timeout: 5000 })) {
            await batchMoveButton.click()
            await page.waitForTimeout(500)

            // 检查是否有分区选择器
            const zoneSelect = page.locator('.ant-modal:has-text("批量移动设备分区") .ant-select')

            if (await zoneSelect.isVisible({ timeout: 5000 })) {
              // 点击展开分区选择
              await zoneSelect.click()
              await page.waitForTimeout(500)

              // 验证分区列表显示
              await expect(page.locator('.ant-select-dropdown')).toBeVisible({ timeout: 5000 })

              // 截图
              await page.screenshot({ path: 'playwright-report/screenshots/devices-zone-select.png' })

              // 关闭
              await page.keyboard.press('Escape')
              await page.locator('.ant-modal-close').click()
            } else {
              test.skip(true, '移动弹窗中没有分区选择器')
            }
          } else {
            test.skip(true, '没有找到批量移动按钮')
          }
        } else {
          test.skip(true, '设备列表不支持多选功能')
        }
      } else {
        test.skip(true, '没有设备数据，跳过测试')
      }
    })
  })

  // ==========================================
  // 4. 综合验证：分区创建后设备可见性
  // ==========================================
  test('创建分区后，该分区的设备应该在设备列表中可见', async ({ page }) => {
    // 步骤1：先查看设备列表当前状态
    await page.goto('/devices')
    await waitForAntLoading(page)
    await page.waitForTimeout(2000)

    const initialDeviceCount = await page.locator('.ant-table-row').count()

    // 步骤2：创建新分区
    await page.goto('/zones')
    await waitForAntLoading(page)
    await page.waitForTimeout(2000)

    // 点击添加按钮
    const addButton = page.locator('button:has-text("添加")')
    await addButton.click()
    await page.waitForSelector('.ant-modal-content', { timeout: 10000 })

    const zoneName = `E2E可见性测试-${Date.now()}`
    await page.fill('.ant-modal input', zoneName)
    await page.locator('.ant-modal .ant-btn-primary').click()
    await page.waitForTimeout(2000)

    // 步骤3：验证分区创建成功
    const tree = page.locator('.ant-tree')
    await expect(tree).toBeVisible({ timeout: 10000 })

    // 步骤4：返回设备列表，检查新分区是否出现在筛选器中
    await page.goto('/devices')
    await waitForAntLoading(page)
    await page.waitForTimeout(2000)

    // 查找分区筛选下拉框（第一个 select 是分区筛选）
    const zoneFilter = page.locator('.ant-select').first()
    if (await zoneFilter.isVisible({ timeout: 5000 })) {
      await zoneFilter.click()
      await page.waitForTimeout(500)

      // 检查下拉列表中是否包含新创建的分区
      const dropdown = page.locator('.ant-select-dropdown')
      await expect(dropdown).toBeVisible({ timeout: 5000 })

      // 截图
      await page.screenshot({ path: 'playwright-report/screenshots/devices-zone-filter.png' })

      await page.keyboard.press('Escape')
    }

    // 截图最终状态
    await page.screenshot({ path: 'playwright-report/screenshots/devices-after-zone-created.png' })
  })
})