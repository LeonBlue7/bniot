<template>
  <div class="users-page">
    <a-card title="用户管理">
      <template #extra>
        <a-button
          type="primary"
          @click="showCreateModal"
        >
          <plus-outlined />
          添加用户
        </a-button>
      </template>

      <a-table
        :columns="columns"
        :data-source="users"
        :loading="loading"
        :pagination="false"
        row-key="id"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'role'">
            <a-tag :color="getRoleColor(record.role)">
              {{ getRoleText(record.role) }}
            </a-tag>
          </template>
          <template v-else-if="column.key === 'is_active'">
            <a-tag :color="record.is_active ? 'green' : 'red'">
              {{ record.is_active ? '正常' : '禁用' }}
            </a-tag>
          </template>
          <template v-else-if="column.key === 'created_at'">
            {{ formatTime(record.created_at) }}
          </template>
          <template v-else-if="column.key === 'action'">
            <a-space>
              <a-button
                size="small"
                @click="showEditModal(record)"
              >
                编辑
              </a-button>
              <a-button
                size="small"
                :type="record.is_active ? 'default' : 'primary'"
                @click="handleToggleStatus(record)"
              >
                {{ record.is_active ? '禁用' : '启用' }}
              </a-button>
            </a-space>
          </template>
        </template>
      </a-table>
    </a-card>

    <!-- 创建用户弹窗 -->
    <a-modal
      v-model:open="createModalVisible"
      title="添加用户"
      :confirm-loading="createLoading"
      @ok="handleCreate"
    >
      <a-form layout="vertical">
        <a-form-item label="用户名">
          <a-input
            v-model:value="createForm.username"
            placeholder="请输入用户名"
          />
        </a-form-item>
        <a-form-item label="密码">
          <a-input-password
            v-model:value="createForm.password"
            placeholder="请输入密码"
          />
        </a-form-item>
        <a-form-item label="角色">
          <a-select v-model:value="createForm.role">
            <a-select-option value="admin">
              管理员
            </a-select-option>
            <a-select-option value="operator">
              操作员
            </a-select-option>
            <a-select-option value="viewer">
              观察员
            </a-select-option>
          </a-select>
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- 编辑用户弹窗 -->
    <a-modal
      v-model:open="editModalVisible"
      title="编辑用户"
      :confirm-loading="editLoading"
      @ok="handleEdit"
    >
      <a-form layout="vertical">
        <a-form-item label="用户名">
          <a-input
            v-model:value="editForm.username"
            disabled
          />
        </a-form-item>
        <a-form-item label="角色">
          <a-select v-model:value="editForm.role">
            <a-select-option value="admin">
              管理员
            </a-select-option>
            <a-select-option value="operator">
              操作员
            </a-select-option>
            <a-select-option value="viewer">
              观察员
            </a-select-option>
          </a-select>
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { PlusOutlined } from '@ant-design/icons-vue'
import dayjs from 'dayjs'
import { userApi } from '@/api'
import type { User } from '@/types'
import type { TableProps } from 'ant-design-vue'

const users = ref<User[]>([])
const loading = ref(false)
const createLoading = ref(false)
const editLoading = ref(false)

// 创建弹窗
const createModalVisible = ref(false)
const createForm = reactive({
  username: '',
  password: '',
  role: 'viewer' as 'admin' | 'operator' | 'viewer'
})

// 编辑弹窗
const editModalVisible = ref(false)
const editForm = reactive({
  username: '',
  role: 'viewer' as 'admin' | 'operator' | 'viewer'
})
const editUserId = ref<number>(0)

// 表格列
const columns: TableProps['columns'] = [
  { title: '用户名', dataIndex: 'username', key: 'username' },
  { title: '角色', dataIndex: 'role', key: 'role' },
  { title: '状态', dataIndex: 'is_active', key: 'is_active' },
  { title: '创建时间', dataIndex: 'created_at', key: 'created_at' },
  { title: '操作', key: 'action', width: 150 }
]

onMounted(() => {
  fetchUsers()
})

async function fetchUsers() {
  loading.value = true
  try {
    users.value = await userApi.list()
  } catch (err: unknown) {
    const error = err as { response?: { data?: { detail?: string } } }
    console.error('获取用户列表失败:', error)
    message.error(error.response?.data?.detail || '获取用户列表失败')
  } finally {
    loading.value = false
  }
}

function formatTime(time: string) {
  return dayjs(time).format('YYYY-MM-DD HH:mm')
}

function getRoleText(role: string) {
  const roles: Record<string, string> = {
    admin: '管理员',
    operator: '操作员',
    viewer: '观察员'
  }
  return roles[role] || role
}

function getRoleColor(role: string) {
  const colors: Record<string, string> = {
    admin: 'purple',
    operator: 'blue',
    viewer: 'default'
  }
  return colors[role] || 'default'
}

function showCreateModal() {
  createForm.username = ''
  createForm.password = ''
  createForm.role = 'viewer'
  createModalVisible.value = true
}

async function handleCreate() {
  if (!createForm.username || !createForm.password) {
    message.error('请填写用户名和密码')
    return
  }

  createLoading.value = true
  try {
    await userApi.create({
      username: createForm.username,
      password: createForm.password,
      role: createForm.role
    })
    message.success('用户创建成功')
    createModalVisible.value = false
    fetchUsers()
  } catch (err: unknown) {
    const error = err as { response?: { data?: { detail?: string } } }
    message.error(error.response?.data?.detail || '创建用户失败')
  } finally {
    createLoading.value = false
  }
}

function showEditModal(user: User) {
  editUserId.value = user.id
  editForm.username = user.username
  editForm.role = user.role
  editModalVisible.value = true
}

async function handleEdit() {
  editLoading.value = true
  try {
    await userApi.update(editUserId.value, { role: editForm.role })
    message.success('用户更新成功')
    editModalVisible.value = false
    fetchUsers()
  } catch (err: unknown) {
    const error = err as { response?: { data?: { detail?: string } } }
    message.error(error.response?.data?.detail || '更新用户失败')
  } finally {
    editLoading.value = false
  }
}

async function handleToggleStatus(user: User) {
  try {
    const newStatus = !user.is_active
    await userApi.updateStatus(user.id, { is_active: newStatus })
    message.success(newStatus ? '用户已启用' : '用户已禁用')
    fetchUsers()
  } catch (err: unknown) {
    const error = err as { response?: { data?: { detail?: string } } }
    message.error(error.response?.data?.detail || '操作失败')
  }
}
</script>

<style scoped>
.users-page {
  padding: 0;
}
</style>