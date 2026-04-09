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
          <a-descriptions
            v-else
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

          <a-divider v-if="selectedZone" />

          <div
            v-if="selectedZone"
            style="text-align: right"
          >
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
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { message, Modal } from 'ant-design-vue'
import { useZoneStore } from '@/stores/zones'
import { useAuthStore } from '@/stores/auth'
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons-vue'
import dayjs from 'dayjs'
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
})

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