<template>
  <div class="zones-page">
    <a-row :gutter="16">
      <!-- 分区树 -->
      <a-col :span="6">
        <a-card
          title="分区结构"
          size="small"
        >
          <template #extra>
            <a-button
              type="primary"
              size="small"
              @click="showCreateModal(null)"
            >
              <plus-outlined />
              添加
            </a-button>
          </template>
          <a-spin :spinning="loading">
            <a-tree
              v-if="zoneTree.length > 0"
              :tree-data="zoneTree"
              :selected-keys="selectedKeys"
              :expanded-keys="expandedKeys"
              :field-names="{ title: 'name', key: 'id', children: 'children' }"
              @select="handleSelect"
              @expand="handleExpand"
            >
              <template #title="node">
                <span>{{ node.name }}</span>
                <a-space class="tree-actions">
                  <a-button
                    size="small"
                    type="text"
                    @click.stop="showCreateModal(node)"
                  >
                    <plus-outlined />
                  </a-button>
                  <a-button
                    size="small"
                    type="text"
                    @click.stop="showEditModal(node)"
                  >
                    <edit-outlined />
                  </a-button>
                  <a-button
                    size="small"
                    type="text"
                    danger
                    @click.stop="handleDelete(node)"
                  >
                    <delete-outlined />
                  </a-button>
                </a-space>
              </template>
            </a-tree>
            <a-empty
              v-else
              description="暂无分区数据"
            />
          </a-spin>
        </a-card>
      </a-col>

      <!-- 分区详情 -->
      <a-col :span="18">
        <a-card
          title="分区详情"
          size="small"
        >
          <a-empty
            v-if="!selectedZone"
            description="请选择分区查看详情"
          />
          <template v-else>
            <a-descriptions
              :column="2"
              bordered
            >
              <a-descriptions-item label="分区ID">
                {{ selectedZone.id }}
              </a-descriptions-item>
              <a-descriptions-item label="分区名称">
                {{ selectedZone.name }}
              </a-descriptions-item>
              <a-descriptions-item label="上级分区">
                {{ getParentName(selectedZone.parent_id) || '根分区' }}
              </a-descriptions-item>
              <a-descriptions-item label="排序">
                {{ selectedZone.sort_order }}
              </a-descriptions-item>
              <a-descriptions-item
                label="描述"
                :span="2"
              >
                {{ selectedZone.description || '-' }}
              </a-descriptions-item>
              <a-descriptions-item
                label="创建时间"
                :span="2"
              >
                {{ formatTime(selectedZone.created_at) }}
              </a-descriptions-item>
            </a-descriptions>

            <!-- 分区授权列表 -->
            <a-divider data-testid="auth-divider">
              分区授权
            </a-divider>
            <a-spin :spinning="authLoading">
              <a-table
                data-testid="auth-table"
                :columns="authColumns"
                :data-source="authorizations"
                :pagination="false"
                size="small"
                row-key="id"
              >
                <template #bodyCell="{ column, record }">
                  <template v-if="column.key === 'tenant_name'">
                    {{ getTenantName(record.tenant_id) }}
                  </template>
                  <template v-if="column.key === 'created_at'">
                    {{ formatTime(record.created_at) }}
                  </template>
                  <template v-if="column.key === 'actions'">
                    <a-button
                      size="small"
                      type="text"
                      danger
                      @click="handleRemoveAuth(record)"
                    >
                      移除授权
                    </a-button>
                  </template>
                </template>
              </a-table>
              <div style="margin-top: 16px; text-align: right">
                <a-button
                  type="primary"
                  data-testid="add-auth-btn"
                  @click="showAddAuthModal"
                >
                  <plus-outlined />
                  添加授权
                </a-button>
              </div>
            </a-spin>

            <a-divider />

            <div style="text-align: right">
              <a-space>
                <a-button @click="showEditModal(selectedZone)">
                  编辑
                </a-button>
                <a-button
                  type="primary"
                  @click="showCreateModal(selectedZone)"
                >
                  添加子分区
                </a-button>
              </a-space>
            </div>
          </template>
        </a-card>
      </a-col>
    </a-row>

    <!-- 创建分区弹窗 -->
    <a-modal
      v-model:open="createModalVisible"
      title="添加分区"
      :confirm-loading="createLoading"
      @ok="handleCreate"
    >
      <a-form
        ref="createFormRef"
        :model="createForm"
        :rules="createRules"
        layout="vertical"
      >
        <a-form-item
          name="name"
          label="分区名称"
        >
          <a-input
            v-model:value="createForm.name"
            placeholder="请输入分区名称"
          />
        </a-form-item>
        <a-form-item
          name="description"
          label="描述"
        >
          <a-textarea
            v-model:value="createForm.description"
            placeholder="请输入描述"
            :rows="3"
          />
        </a-form-item>
        <a-form-item
          name="sort_order"
          label="排序"
        >
          <a-input-number
            v-model:value="createForm.sort_order"
            :min="0"
          />
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- 编辑分区弹窗 -->
    <a-modal
      v-model:open="editModalVisible"
      title="编辑分区"
      :confirm-loading="editLoading"
      @ok="handleEdit"
    >
      <a-form
        ref="editFormRef"
        :model="editForm"
        :rules="editRules"
        layout="vertical"
      >
        <a-form-item
          name="name"
          label="分区名称"
        >
          <a-input
            v-model:value="editForm.name"
            placeholder="请输入分区名称"
          />
        </a-form-item>
        <a-form-item
          name="description"
          label="描述"
        >
          <a-textarea
            v-model:value="editForm.description"
            placeholder="请输入描述"
            :rows="3"
          />
        </a-form-item>
        <a-form-item
          name="sort_order"
          label="排序"
        >
          <a-input-number
            v-model:value="editForm.sort_order"
            :min="0"
          />
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- 添加授权弹窗 -->
    <a-modal
      v-model:open="addAuthModalVisible"
      title="添加分区授权"
      :confirm-loading="addAuthLoading"
      @ok="handleAddAuth"
    >
      <a-form layout="vertical">
        <a-form-item label="选择租户">
          <a-select
            v-model:value="selectedTenantId"
            placeholder="请选择要授权的租户"
            :loading="tenantLoading"
            style="width: 100%"
          >
            <a-select-option
              v-for="tenant in tenants"
              :key="tenant.id"
              :value="tenant.id"
            >
              {{ tenant.name }} ({{ tenant.code }})
            </a-select-option>
          </a-select>
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { message, Modal } from 'ant-design-vue'
import { useZoneStore } from '@/stores/zones'
import { useAuthStore } from '@/stores/auth'
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons-vue'
import dayjs from 'dayjs'
import { zoneApi, type ZoneAuthorization } from '@/api/zones'
import { tenantApi, type Tenant } from '@/api/tenants'
import type { Zone, ZoneCreate, ZoneUpdate } from '@/types'
import type { FormInstance } from 'ant-design-vue'
import type { Rule } from 'ant-design-vue/es/form'

const zoneStore = useZoneStore()
const authStore = useAuthStore()

// 状态
const selectedKeys = ref<number[]>([])
const expandedKeys = ref<number[]>([])
const selectedZone = ref<Zone | null>(null)

// 数据
const zoneTree = computed(() => zoneStore.zoneTree)
const zones = computed(() => zoneStore.zones)
const loading = computed(() => zoneStore.loading)

// 分区授权
const authorizations = ref<ZoneAuthorization[]>([])
const authLoading = ref(false)
const authColumns = [
  { title: '授权ID', dataIndex: 'id', key: 'id', width: 80 },
  { title: '租户', dataIndex: 'tenant_id', key: 'tenant_name' },
  { title: '授权时间', dataIndex: 'created_at', key: 'created_at' },
  { title: '操作', key: 'actions', width: 120 }
]

// 租户列表
const tenants = ref<Tenant[]>([])
const tenantLoading = ref(false)

// 添加授权弹窗
const addAuthModalVisible = ref(false)
const addAuthLoading = ref(false)
const selectedTenantId = ref<number | null>(null)

// 创建弹窗
const createModalVisible = ref(false)
const createLoading = ref(false)
const createFormRef = ref<FormInstance>()
const createParentId = ref<number | null>(null)
const createForm = reactive<ZoneCreate>({
  name: '',
  parent_id: null,
  description: null,
  sort_order: 0,
  tenant_id: authStore.user?.tenant_id || 0
})
const createRules: Record<string, Rule[]> = {
  name: [{ required: true, message: '请输入分区名称', trigger: 'blur' }]
}

// 编辑弹窗
const editModalVisible = ref(false)
const editLoading = ref(false)
const editFormRef = ref<FormInstance>()
const editForm = reactive<ZoneUpdate>({
  name: '',
  description: null,
  sort_order: 0
})
const editRules: Record<string, Rule[]> = {
  name: [{ required: true, message: '请输入分区名称', trigger: 'blur' }]
}
const editZoneId = ref<number>(0)

// 加载分区数据
onMounted(async () => {
  await zoneStore.fetchZones()
  // 默认展开第一层
  expandedKeys.value = zones.value.filter(z => z.parent_id === null).map(z => z.id)
  // 加载租户列表（管理员才有权限）
  if (authStore.user?.role === 'admin') {
    await loadTenants()
  }
})

// 监听选中分区，加载授权列表
watch(selectedZone, async (zone) => {
  if (zone) {
    await loadAuthorizations(zone.id)
  } else {
    authorizations.value = []
  }
})

// 加载授权列表
async function loadAuthorizations(zoneId: number) {
  authLoading.value = true
  try {
    authorizations.value = await zoneApi.listAuthorizations(zoneId)
  } catch (error) {
    console.error('加载授权列表失败:', error)
    authorizations.value = []
  } finally {
    authLoading.value = false
  }
}

// 加载租户列表
async function loadTenants() {
  tenantLoading.value = true
  try {
    tenants.value = await tenantApi.list()
  } catch (error) {
    console.error('加载租户列表失败:', error)
    tenants.value = []
  } finally {
    tenantLoading.value = false
  }
}

// 获取租户名称
function getTenantName(tenantId: number): string {
  const tenant = tenants.value.find(t => t.id === tenantId)
  return tenant?.name || `租户 ${tenantId}`
}

// 选择分区
function handleSelect(keys: number[]) {
  selectedKeys.value = keys
  if (keys.length > 0) {
    selectedZone.value = zones.value.find(z => z.id === keys[0]) || null
  } else {
    selectedZone.value = null
  }
}

// 展开/收起
function handleExpand(keys: number[]) {
  expandedKeys.value = keys
}

// 获取父分区名称
function getParentName(parentId: number | null) {
  if (!parentId) return null
  const parent = zones.value.find(z => z.id === parentId)
  return parent?.name
}

// 格式化时间
function formatTime(time: string) {
  return dayjs(time).format('YYYY-MM-DD HH:mm:ss')
}

// 显示创建弹窗
function showCreateModal(parent: Zone | null) {
  createParentId.value = parent?.id || null
  createForm.name = ''
  createForm.parent_id = parent?.id || null
  createForm.description = null
  createForm.sort_order = 0
  createForm.tenant_id = authStore.user?.tenant_id || 0
  createModalVisible.value = true
}

// 创建分区
async function handleCreate() {
  try {
    await createFormRef.value?.validateFields()
    createLoading.value = true
    const result = await zoneStore.createZone(createForm)
    if (result) {
      message.success('分区创建成功')
      createModalVisible.value = false
      // 展开新分区
      expandedKeys.value = [...expandedKeys.value, result.id]
      // 自动刷新授权列表（分区创建时已自动授权）
      if (selectedZone.value?.id === result.id) {
        await loadAuthorizations(result.id)
      }
    }
  } catch {
    // 验证失败
  } finally {
    createLoading.value = false
  }
}

// 显示编辑弹窗
function showEditModal(zone: Zone) {
  editZoneId.value = zone.id
  editForm.name = zone.name
  editForm.description = zone.description
  editForm.sort_order = zone.sort_order
  editModalVisible.value = true
}

// 编辑分区
async function handleEdit() {
  try {
    await editFormRef.value?.validateFields()
    editLoading.value = true
    const result = await zoneStore.updateZone(editZoneId.value, editForm)
    if (result) {
      message.success('分区更新成功')
      editModalVisible.value = false
      if (selectedZone.value?.id === editZoneId.value) {
        selectedZone.value = result
      }
    }
  } catch {
    // 验证失败
  } finally {
    editLoading.value = false
  }
}

// 删除分区
function handleDelete(zone: Zone) {
  const hasChildren = zones.value.some(z => z.parent_id === zone.id)
  if (hasChildren) {
    message.warning('该分区有子分区，请先删除子分区')
    return
  }

  Modal.confirm({
    title: '确认删除',
    content: `确定要删除分区 "${zone.name}" 吗？`,
    okText: '删除',
    okType: 'danger',
    cancelText: '取消',
    async onOk() {
      const success = await zoneStore.deleteZone(zone.id)
      if (success) {
        message.success('分区已删除')
        selectedKeys.value = []
        selectedZone.value = null
        expandedKeys.value = expandedKeys.value.filter(k => k !== zone.id)
      }
    }
  })
}

// 显示添加授权弹窗
function showAddAuthModal() {
  selectedTenantId.value = null
  addAuthModalVisible.value = true
}

// 添加授权
async function handleAddAuth() {
  if (!selectedZone.value || !selectedTenantId.value) {
    message.warning('请选择要授权的租户')
    return
  }

  addAuthLoading.value = true
  try {
    await zoneApi.authorize(selectedZone.value.id, selectedTenantId.value)
    message.success('授权添加成功')
    addAuthModalVisible.value = false
    await loadAuthorizations(selectedZone.value.id)
  } catch (error: any) {
    const detail = error.response?.data?.detail || '添加授权失败'
    message.error(detail)
  } finally {
    addAuthLoading.value = false
  }
}

// 移除授权
function handleRemoveAuth(auth: ZoneAuthorization) {
  if (!selectedZone.value) return

  Modal.confirm({
    title: '确认移除授权',
    content: `确定要移除对租户 "${getTenantName(auth.tenant_id)}" 的授权吗？`,
    okText: '移除',
    okType: 'danger',
    cancelText: '取消',
    async onOk() {
      try {
        await zoneApi.removeAuthorization(selectedZone.value!.id, auth.tenant_id)
        message.success('授权已移除')
        await loadAuthorizations(selectedZone.value!.id)
      } catch (error: any) {
        const detail = error.response?.data?.detail || '移除授权失败'
        message.error(detail)
      }
    }
  })
}
</script>

<style scoped>
.zones-page {
  padding: 0;
}

.tree-actions {
  float: right;
  opacity: 0;
  transition: opacity 0.3s;
}

.tree-actions:hover {
  opacity: 1;
}

:deep(.ant-tree-node-content-wrapper:hover) .tree-actions {
  opacity: 1;
}
</style>