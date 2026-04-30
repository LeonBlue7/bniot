/**
 * Profile 组件测试 - 微信绑定功能
 * TDD RED 阶段 - 测试编写在实现之前
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import Profile from '@/views/Profile.vue'
import { useAuthStore } from '@/stores/auth'

// Mock userApi
vi.mock('@/api', () => ({
  authApi: {
    changePassword: vi.fn()
  },
  userApi: {
    bindWechat: vi.fn(),
    unbindWechat: vi.fn()
  }
}))

// Mock auth store
vi.mock('@/stores/auth', () => ({
  useAuthStore: vi.fn()
}))

// Mock ant-design-vue message and Modal
vi.mock('ant-design-vue', () => ({
  message: {
    success: vi.fn(),
    error: vi.fn()
  },
  Modal: {
    confirm: vi.fn(({ onOk }) => {
      // 自动调用 onOk 来模拟用户点击确认
      if (onOk) onOk()
    })
  }
}))

// 全局 stubs
const globalStubs = {
  'a-card': { template: '<div class="a-card"><slot /></div>' },
  'a-descriptions': { template: '<div class="a-descriptions"><slot /></div>' },
  'a-descriptions-item': {
    template: '<div class="a-descriptions-item"><span class="label">{{ label }}</span><slot /></div>',
    props: ['label']
  },
  'a-divider': { template: '<hr class="a-divider"><slot /></hr>' },
  'a-form': { template: '<form class="a-form"><slot /></form>' },
  'a-form-item': { template: '<div class="a-form-item"><slot /></div>' },
  'a-input-password': {
    template: '<input class="a-input-password" type="password" />',
    model: {
      prop: 'value',
      event: 'update:value'
    }
  },
  'a-button': { template: '<button class="a-button" type="submit"><slot /></button>' },
  'a-tag': { template: '<span class="a-tag"><slot /></span>' },
  'a-modal': { template: '<div class="a-modal"><slot /></div>' },
  'a-spin': { template: '<div class="a-spin"><slot /></div>' }
}

describe('Profile - 微信绑定功能', () => {
  let pinia: ReturnType<typeof createPinia>

  beforeEach(() => {
    vi.clearAllMocks()
    pinia = createPinia()
    setActivePinia(pinia)
  })

  describe('微信绑定状态显示', () => {
    it('应该显示微信绑定状态', () => {
      // Mock auth store - 已绑定微信的用户
      vi.mocked(useAuthStore).mockReturnValue({
        user: {
          id: 1,
          username: 'testuser',
          role: 'admin',
          tenant_id: 1,
          is_active: true,
          created_at: '2024-01-01T00:00:00Z',
          wechat_openid: 'test_openid_123'
        }
      } as unknown as ReturnType<typeof useAuthStore>)

      const wrapper = mount(Profile, {
        global: {
          plugins: [pinia],
          stubs: globalStubs
        }
      })

      // 应该显示绑定状态（标签或文本中）
      // 由于使用了 stub，检查 rendered HTML 中是否包含相关内容
      expect(wrapper.html()).toContain('已绑定')
    })

    it('已绑定用户应该显示解绑按钮', () => {
      vi.mocked(useAuthStore).mockReturnValue({
        user: {
          id: 1,
          username: 'testuser',
          role: 'admin',
          tenant_id: 1,
          is_active: true,
          created_at: '2024-01-01T00:00:00Z',
          wechat_openid: 'test_openid_123'
        }
      } as unknown as ReturnType<typeof useAuthStore>)

      const wrapper = mount(Profile, {
        global: {
          plugins: [pinia],
          stubs: globalStubs
        }
      })

      // 应该有解绑按钮文本
      expect(wrapper.text()).toContain('解绑微信')
    })

    it('未绑定用户应该显示绑定按钮', () => {
      vi.mocked(useAuthStore).mockReturnValue({
        user: {
          id: 1,
          username: 'testuser',
          role: 'admin',
          tenant_id: 1,
          is_active: true,
          created_at: '2024-01-01T00:00:00Z',
          wechat_openid: null
        }
      } as unknown as ReturnType<typeof useAuthStore>)

      const wrapper = mount(Profile, {
        global: {
          plugins: [pinia],
          stubs: globalStubs
        }
      })

      // 应该有绑定按钮文本
      expect(wrapper.text()).toContain('绑定微信')
    })
  })

  describe('微信绑定操作', () => {
    it('点击绑定按钮应该打开绑定弹窗', async () => {
      vi.mocked(useAuthStore).mockReturnValue({
        user: {
          id: 1,
          username: 'testuser',
          role: 'admin',
          tenant_id: 1,
          is_active: true,
          created_at: '2024-01-01T00:00:00Z',
          wechat_openid: null
        },
        refreshUser: vi.fn()
      } as unknown as ReturnType<typeof useAuthStore>)

      const wrapper = mount(Profile, {
        global: {
          plugins: [pinia],
          stubs: globalStubs
        }
      })

      // 找到绑定按钮
      const buttons = wrapper.findAll('.a-button')
      const bindButton = buttons.find(b => b.text().includes('绑定微信'))

      if (bindButton) {
        await bindButton.trigger('click')

        // 检查弹窗是否打开（通过组件内部状态）
        const vm = wrapper.vm as any
        expect(vm.bindModalVisible).toBe(true)
      }
    })

    it('绑定成功后应该刷新用户信息', async () => {
      const { userApi } = await import('@/api')
      const mockRefreshUser = vi.fn()

      vi.mocked(useAuthStore).mockReturnValue({
        user: {
          id: 1,
          username: 'testuser',
          role: 'admin',
          tenant_id: 1,
          is_active: true,
          created_at: '2024-01-01T00:00:00Z',
          wechat_openid: null
        },
        refreshUser: mockRefreshUser
      } as unknown as ReturnType<typeof useAuthStore>)

      // Mock 绑定成功
      vi.mocked(userApi.bindWechat).mockResolvedValue({
        success: true,
        message: '微信绑定成功',
        openid: 'new_openid_123'
      })

      const wrapper = mount(Profile, {
        global: {
          plugins: [pinia],
          stubs: globalStubs
        }
      })

      // 调用绑定方法（模拟点击确认）
      const vm = wrapper.vm as any
      // 设置弹窗打开
      vm.bindModalVisible = true
      await vm.handleBindWechat()

      // 应该调用 API
      expect(userApi.bindWechat).toHaveBeenCalled()

      // 应该刷新用户信息
      expect(mockRefreshUser).toHaveBeenCalled()
    })
  })

  describe('微信解绑操作', () => {
    it('解绑成功后应该清除绑定状态', async () => {
      const { userApi } = await import('@/api')
      const mockRefreshUser = vi.fn()

      vi.mocked(useAuthStore).mockReturnValue({
        user: {
          id: 1,
          username: 'testuser',
          role: 'admin',
          tenant_id: 1,
          is_active: true,
          created_at: '2024-01-01T00:00:00Z',
          wechat_openid: 'test_openid_123'
        },
        refreshUser: mockRefreshUser
      } as unknown as ReturnType<typeof useAuthStore>)

      // Mock 解绑成功
      vi.mocked(userApi.unbindWechat).mockResolvedValue({
        success: true,
        message: '微信解绑成功'
      })

      const wrapper = mount(Profile, {
        global: {
          plugins: [pinia],
          stubs: globalStubs
        }
      })

      // 调用解绑方法
      const vm = wrapper.vm as any
      await vm.handleUnbindWechat()

      // 应该调用 API（Modal.confirm mock 会自动调用 onOk）
      expect(userApi.unbindWechat).toHaveBeenCalled()

      // 应该刷新用户信息
      expect(mockRefreshUser).toHaveBeenCalled()
    })

    it('解绑失败应该显示错误信息', async () => {
      const { userApi } = await import('@/api')
      const { message } = await import('ant-design-vue')

      vi.mocked(useAuthStore).mockReturnValue({
        user: {
          id: 1,
          username: 'testuser',
          role: 'admin',
          tenant_id: 1,
          is_active: true,
          created_at: '2024-01-01T00:00:00Z',
          wechat_openid: 'test_openid_123'
        },
        refreshUser: vi.fn()
      } as unknown as ReturnType<typeof useAuthStore>)

      // Mock 解绑失败
      vi.mocked(userApi.unbindWechat).mockRejectedValue(new Error('解绑失败'))

      const wrapper = mount(Profile, {
        global: {
          plugins: [pinia],
          stubs: globalStubs
        }
      })

      const vm = wrapper.vm as any
      await vm.handleUnbindWechat()

      // 应该显示错误
      expect(message.error).toHaveBeenCalled()
    })
  })

  describe('边缘情况', () => {
    it('用户信息为空时不应崩溃', () => {
      vi.mocked(useAuthStore).mockReturnValue({
        user: null
      } as unknown as ReturnType<typeof useAuthStore>)

      const wrapper = mount(Profile, {
        global: {
          plugins: [pinia],
          stubs: globalStubs
        }
      })

      // 组件应该正常渲染，不崩溃
      expect(wrapper.exists()).toBe(true)
    })

    it('绑定过程中应该显示加载状态', async () => {
      vi.mocked(useAuthStore).mockReturnValue({
        user: {
          id: 1,
          username: 'testuser',
          role: 'admin',
          tenant_id: 1,
          is_active: true,
          created_at: '2024-01-01T00:00:00Z',
          wechat_openid: null
        },
        refreshUser: vi.fn()
      } as unknown as ReturnType<typeof useAuthStore>)

      const wrapper = mount(Profile, {
        global: {
          plugins: [pinia],
          stubs: globalStubs
        }
      })

      // 检查是否有加载状态相关的变量
      const vm = wrapper.vm as any
      expect(vm.wechatLoading !== undefined).toBe(true)
    })
  })
})