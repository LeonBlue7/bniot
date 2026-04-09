/**
 * MainLayout 组件测试
 * 测试菜单导航功能
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createRouter, createWebHistory, type Router } from 'vue-router'
import { createPinia, setActivePinia } from 'pinia'
import MainLayout from '@/layouts/MainLayout.vue'
import { useAuthStore } from '@/stores/auth'

// Mock 组件
const DashboardView = { template: '<div>Dashboard</div>' }
const DevicesView = { template: '<div>Devices</div>' }
const ZonesView = { template: '<div>Zones</div>' }

// 创建测试路由 - 使用 PascalCase 名称匹配实际路由
function createTestRouter(): Router {
  return createRouter({
    history: createWebHistory(),
    routes: [
      { path: '/', redirect: '/dashboard' },
      { path: '/dashboard', name: 'Dashboard', component: DashboardView },
      { path: '/devices', name: 'Devices', component: DevicesView },
      { path: '/zones', name: 'Zones', component: ZonesView }
    ]
  })
}

// Mock auth store
vi.mock('@/stores/auth', () => ({
  useAuthStore: vi.fn()
}))

// 全局 stubs
const globalStubs = {
  'router-view': true,
  'a-layout': { template: '<div class="a-layout"><slot /></div>' },
  'a-layout-sider': { template: '<div class="a-layout-sider"><slot /></div>' },
  'a-layout-header': { template: '<div class="a-layout-header"><slot /></div>' },
  'a-layout-content': { template: '<div class="a-layout-content"><slot /></div>' },
  'a-button': { template: '<button class="a-button"><slot /></button>' },
  'a-avatar': { template: '<div class="a-avatar"><slot /></div>' },
  'a-dropdown': { template: '<div class="a-dropdown"><slot /></div>' },
  'a-menu': { template: '<div class="a-menu"><slot /></div>' },
  'a-menu-divider': { template: '<hr class="a-menu-divider" />' },
  'a-menu-item': { template: '<div class="a-menu-item"><slot /></div>' }
}

describe('MainLayout', () => {
  let router: Router
  let pinia: ReturnType<typeof createPinia>

  beforeEach(() => {
    vi.clearAllMocks()
    pinia = createPinia()
    setActivePinia(pinia)

    vi.mocked(useAuthStore).mockReturnValue({
      user: { username: 'admin', role: 'admin' },
      isAdmin: true,
      logout: vi.fn()
    } as unknown as ReturnType<typeof useAuthStore>)

    router = createTestRouter()
  })

  describe('菜单导航功能', () => {
    it('selectedKeys 应该随路由变化而更新', async () => {
      await router.push('/dashboard')
      await router.isReady()

      const wrapper = mount(MainLayout, {
        global: {
          plugins: [router, pinia],
          stubs: globalStubs
        }
      })

      // 验证初始选中状态 - 使用 PascalCase 路由名称
      const vm = wrapper.vm as unknown as { selectedKeys: string[] }
      expect(vm.selectedKeys).toContain('Dashboard')

      // 改变路由
      await router.push('/devices')
      await wrapper.vm.$nextTick()

      // 验证选中状态更新
      expect(vm.selectedKeys).toContain('Devices')
    })

    it('点击菜单项应该触发路由导航', async () => {
      await router.push('/dashboard')
      await router.isReady()

      const pushSpy = vi.spyOn(router, 'push')

      const wrapper = mount(MainLayout, {
        global: {
          plugins: [router, pinia],
          stubs: globalStubs
        }
      })

      // 模拟点击菜单 - 直接调用 handleMenuClick
      const vm = wrapper.vm as unknown as {
         
        handleMenuClick?: (e: { key: string }) => void
      }

      // 检查是否有 handleMenuClick 方法（待实现）
      if (vm.handleMenuClick) {
        await vm.handleMenuClick({ key: 'Devices' })
        await wrapper.vm.$nextTick()
        expect(pushSpy).toHaveBeenCalledWith({ name: 'Devices' })
      } else {
        // 如果方法不存在，测试应该失败（RED 阶段）
        expect(vm.handleMenuClick).toBeDefined()
      }
    })

    it('菜单项数据应该包含正确的 key', async () => {
      await router.push('/dashboard')
      await router.isReady()

      const wrapper = mount(MainLayout, {
        global: {
          plugins: [router, pinia],
          stubs: globalStubs
        }
      })

      const vm = wrapper.vm as unknown as { menuItems: Array<{ key: string }> }
      const items = vm.menuItems || []

      // 验证菜单项存在
      expect(items.length).toBeGreaterThan(0)

      // 验证菜单项包含必要的 key（PascalCase 匹配路由名称）
      const keys = items.map(item => item.key)
      expect(keys).toContain('Dashboard')
      expect(keys).toContain('Devices')
      expect(keys).toContain('Zones')
    })
  })
})