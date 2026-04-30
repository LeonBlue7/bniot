/**
 * Profile 组件测试
 * TDD RED 阶段 - 测试编写在实现之前
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import Profile from '@/views/Profile.vue'
import { useAuthStore } from '@/stores/auth'

// Mock auth API
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
    confirm: vi.fn()
  }
}))

// 全局 stubs
const globalStubs = {
  'a-card': { template: '<div class="a-card"><slot /></div>' },
  'a-descriptions': { template: '<div class="a-descriptions"><slot /></div>' },
  'a-descriptions-item': { template: '<div class="a-descriptions-item"><slot /></div>' },
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
  'a-modal': { template: '<div class="a-modal"><slot /></div>' }
}

describe('Profile', () => {
  let pinia: ReturnType<typeof createPinia>

  beforeEach(() => {
    vi.clearAllMocks()
    pinia = createPinia()
    setActivePinia(pinia)

    // Mock auth store
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
  })

  describe('用户信息展示', () => {
    it('应该显示用户名', () => {
      const wrapper = mount(Profile, {
        global: {
          plugins: [pinia],
          stubs: globalStubs
        }
      })

      expect(wrapper.text()).toContain('testuser')
    })

    it('应该显示角色标签', () => {
      const wrapper = mount(Profile, {
        global: {
          plugins: [pinia],
          stubs: globalStubs
        }
      })

      // 角色应该显示为中文
      expect(wrapper.text()).toContain('管理员')
    })

    it('应该显示用户状态', () => {
      const wrapper = mount(Profile, {
        global: {
          plugins: [pinia],
          stubs: globalStubs
        }
      })

      expect(wrapper.text()).toContain('正常')
    })
  })

  describe('修改密码功能', () => {
    it('应该有密码表单字段', () => {
      const wrapper = mount(Profile, {
        global: {
          plugins: [pinia],
          stubs: globalStubs
        }
      })

      // 检查密码输入框
      const passwordInputs = wrapper.findAll('.a-input-password')
      expect(passwordInputs.length).toBe(3) // old_password, new_password, confirm_password
    })

    it('应该有修改密码按钮', () => {
      const wrapper = mount(Profile, {
        global: {
          plugins: [pinia],
          stubs: globalStubs
        }
      })

      // 找到修改密码按钮（注意：现在有多个按钮）
      const buttons = wrapper.findAll('.a-button')
      const passwordButton = buttons.find(b => b.text().includes('修改密码'))
      expect(passwordButton?.exists()).toBe(true)
    })
  })
})