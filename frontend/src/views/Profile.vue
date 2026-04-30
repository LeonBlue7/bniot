<template>
  <div class="profile-page">
    <a-card
      title="个人中心"
      class="profile-card"
    >
      <!-- 用户信息展示 -->
      <a-descriptions
        :column="1"
        bordered
        class="user-info"
      >
        <a-descriptions-item label="用户名">
          {{ user?.username }}
        </a-descriptions-item>
        <a-descriptions-item label="角色">
          {{ roleLabel }}
        </a-descriptions-item>
        <a-descriptions-item label="状态">
          <a-tag :color="user?.is_active ? 'success' : 'error'">
            {{ user?.is_active ? '正常' : '已禁用' }}
          </a-tag>
        </a-descriptions-item>
        <a-descriptions-item label="微信绑定">
          <a-tag :color="user?.wechat_openid ? 'success' : 'default'">
            {{ user?.wechat_openid ? '已绑定' : '未绑定' }}
          </a-tag>
          <a-button
            v-if="user?.wechat_openid"
            type="link"
            size="small"
            danger
            :loading="wechatLoading"
            @click="handleUnbindWechat"
          >
            解绑微信
          </a-button>
          <a-button
            v-else
            type="link"
            size="small"
            :loading="wechatLoading"
            @click="showBindModal"
          >
            绑定微信
          </a-button>
        </a-descriptions-item>
        <a-descriptions-item label="创建时间">
          {{ formatDate(user?.created_at) }}
        </a-descriptions-item>
      </a-descriptions>

      <!-- 微信绑定弹窗 -->
      <a-modal
        v-model:open="bindModalVisible"
        title="绑定微信"
        :confirm-loading="wechatLoading"
        @ok="handleBindWechat"
        @cancel="bindModalVisible = false"
      >
        <p>绑定微信后，您可以使用微信小程序登录管理后台。</p>
        <p>请在微信小程序中登录，然后点击确认绑定。</p>
        <p class="bind-tip">
          提示：绑定需要小程序授权，请确保已打开小程序。
        </p>
      </a-modal>

      <!-- 修改密码表单 -->
      <a-divider>修改密码</a-divider>
      <a-form
        :model="passwordForm"
        :rules="passwordRules"
        layout="vertical"
        @finish="handlePasswordChange"
      >
        <a-form-item
          label="当前密码"
          name="old_password"
        >
          <a-input-password
            v-model:value="passwordForm.old_password"
            placeholder="请输入当前密码"
          />
        </a-form-item>
        <a-form-item
          label="新密码"
          name="new_password"
        >
          <a-input-password
            v-model:value="passwordForm.new_password"
            placeholder="请输入新密码（至少6位）"
          />
        </a-form-item>
        <a-form-item
          label="确认新密码"
          name="confirm_password"
        >
          <a-input-password
            v-model:value="passwordForm.confirm_password"
            placeholder="请再次输入新密码"
          />
        </a-form-item>
        <a-form-item>
          <a-button
            type="primary"
            html-type="submit"
            :loading="loading"
          >
            修改密码
          </a-button>
        </a-form-item>
      </a-form>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, reactive } from 'vue'
import { message, Modal } from 'ant-design-vue'
import { useAuthStore } from '@/stores/auth'
import { authApi, userApi } from '@/api'
import type { PasswordChangeRequest } from '@/types'
import type { Rule } from 'ant-design-vue/es/form'

const authStore = useAuthStore()

// 用户信息
const user = computed(() => authStore.user)
const roleLabel = computed(() => {
  const roleMap: Record<string, string> = {
    admin: '管理员',
    operator: '操作员',
    viewer: '查看者'
  }
  return roleMap[user.value?.role || 'viewer'] || '未知'
})

// 密码表单
const passwordForm = reactive({
  old_password: '',
  new_password: '',
  confirm_password: ''
})

const loading = ref(false)

// 微信绑定状态
const wechatLoading = ref(false)
const bindModalVisible = ref(false)
const bindCode = ref('')

// 密码验证规则
const passwordRules: Record<string, Rule[]> = {
  old_password: [
    { required: true, message: '请输入当前密码', trigger: 'blur' }
  ],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码至少6位', trigger: 'blur' }
  ],
  confirm_password: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    {
      validator: (_rule: Rule, value: string) => {
        if (value !== passwordForm.new_password) {
          return Promise.reject('两次输入的密码不一致')
        }
        return Promise.resolve()
      },
      trigger: 'blur'
    }
  ]
}

// 格式化日期
function formatDate(dateStr: string | undefined): string {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 显示绑定弹窗
function showBindModal() {
  bindModalVisible.value = true
  bindCode.value = ''
}

// 绑定微信
async function handleBindWechat() {
  wechatLoading.value = true
  try {
    // 生成一个临时 code（实际场景需要从小程序获取）
    // 这里使用模拟方式，实际应该通过小程序扫码授权获取
    const tempCode = `bind_${Date.now()}_${Math.random().toString(36).slice(2)}`

    const result = await userApi.bindWechat(tempCode)
    if (result.success) {
      message.success(result.message || '微信绑定成功')
      bindModalVisible.value = false
      // 刷新用户信息
      await authStore.refreshUser()
    }
  } catch (error) {
    const err = error as { response?: { data?: { detail?: string } } }
    message.error(err.response?.data?.detail || '微信绑定失败')
  } finally {
    wechatLoading.value = false
  }
}

// 解绑微信
async function handleUnbindWechat() {
  Modal.confirm({
    title: '确认解绑',
    content: '解绑后将无法使用微信小程序登录，确定要解绑吗？',
    okText: '确定',
    cancelText: '取消',
    onOk: async () => {
      wechatLoading.value = true
      try {
        const result = await userApi.unbindWechat()
        if (result.success) {
          message.success(result.message || '微信解绑成功')
          // 刷新用户信息
          await authStore.refreshUser()
        }
      } catch (error) {
        const err = error as { response?: { data?: { detail?: string } } }
        message.error(err.response?.data?.detail || '微信解绑失败')
      } finally {
        wechatLoading.value = false
      }
    }
  })
}

// 修改密码
async function handlePasswordChange() {
  loading.value = true
  try {
    const data: PasswordChangeRequest = {
      old_password: passwordForm.old_password,
      new_password: passwordForm.new_password
    }
    await authApi.changePassword(data)
    message.success('密码修改成功')
    // 清空表单
    passwordForm.old_password = ''
    passwordForm.new_password = ''
    passwordForm.confirm_password = ''
  } catch (error) {
    const err = error as { response?: { data?: { detail?: string } } }
    message.error(err.response?.data?.detail || '密码修改失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.profile-page {
  max-width: 600px;
  margin: 0 auto;
}

.profile-card {
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border-primary);
}

.profile-card :deep(.ant-card-head) {
  border-bottom: 1px solid var(--color-border-primary);
}

.profile-card :deep(.ant-card-head-title) {
  color: var(--color-text-primary);
}

.user-info :deep(.ant-descriptions-item-label) {
  background: var(--color-bg-tertiary);
  color: var(--color-text-secondary);
}

.user-info :deep(.ant-descriptions-item-content) {
  color: var(--color-text-primary);
}

:deep(.ant-divider-inner-text) {
  color: var(--color-text-secondary);
}

:deep(.ant-form-item-label > label) {
  color: var(--color-text-primary);
}

:deep(.ant-input-password) {
  background: var(--color-bg-tertiary);
  border-color: var(--color-border-primary);
  color: var(--color-text-primary);
}

:deep(.ant-input-password:hover),
:deep(.ant-input-password:focus) {
  border-color: var(--color-cool-primary);
}

.bind-tip {
  color: var(--color-text-secondary);
  font-size: 12px;
  margin-top: 8px;
}

/* 微信绑定按钮样式 */
:deep(.ant-btn-link) {
  padding-left: 8px;
}
</style>