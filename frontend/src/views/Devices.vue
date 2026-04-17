<template>
  <div class="devices-page">
    <!-- 搜索和操作栏 -->
    <a-card class="toolbar-card">
      <a-row
        :gutter="16"
        align="middle"
      >
        <a-col :span="6">
          <a-input-search
            v-model:value="searchKeyword"
            placeholder="搜索设备号、名称、SIM卡、固件版本、分区"
            allow-clear
            @search="handleSearch"
          />
        </a-col>
        <a-col :span="3">
          <a-select
            v-model:value="filterZone"
            placeholder="分区"
            allow-clear
            style="width: 100%"
            @change="handleSearch"
          >
            <a-select-option
              v-for="zone in zones"
              :key="zone.id"
              :value="zone.id"
            >
              {{ zone.name }}
            </a-select-option>
          </a-select>
        </a-col>
        <a-col :span="3">
          <a-select
            v-model:value="filterProtocol"
            placeholder="协议版本"
            allow-clear
            style="width: 100%"
            @change="handleSearch"
          >
            <a-select-option value="V10">
              V10
            </a-select-option>
            <a-select-option value="V20">
              V20
            </a-select-option>
          </a-select>
        </a-col>
        <a-col :span="3">
          <a-select
            v-model:value="filterOnline"
            placeholder="在线状态"
            allow-clear
            style="width: 100%"
            @change="handleSearch"
          >
            <a-select-option :value="true">
              在线
            </a-select-option>
            <a-select-option :value="false">
              离线
            </a-select-option>
          </a-select>
        </a-col>
        <a-col
          :span="9"
          style="text-align: right"
        >
          <a-space>
            <a-button
              type="primary"
              @click="showCreateModal"
            >
              <plus-outlined />
              添加设备
            </a-button>
          </a-space>
        </a-col>
      </a-row>
    </a-card>

    <!-- 设备列表 -->
    <a-card class="table-card">
      <a-table
        :columns="columns"
        :data-source="devices"
        :loading="loading"
        :pagination="pagination"
        row-key="id"
        @change="handleTableChange"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'device_id'">
            <span>{{ record.device_id }}</span>
          </template>
          <template v-else-if="column.key === 'name'">
            <a @click="goToDetail(record.id)">{{ record.name }}</a>
          </template>
          <template v-else-if="column.key === 'temp'">
            <span v-if="record.temp != null">{{ record.temp.toFixed(1) }}℃</span>
            <span v-else>--℃</span>
          </template>
          <template v-else-if="column.key === 'humi'">
            <span v-if="record.humi != null">{{ record.humi.toFixed(1) }}%</span>
            <span v-else>--%</span>
          </template>
          <template v-else-if="column.key === 'alarmtemp'">
            <a-tag
              v-if="record.alarmtemp"
              color="red"
            >
              告警
            </a-tag>
            <a-tag
              v-else
              color="default"
            >
              正常
            </a-tag>
          </template>
          <template v-else-if="column.key === 'protocol_version'">
            <a-tag :color="record.protocol_version === 'V10' ? 'blue' : 'green'">
              {{ record.protocol_version }}
            </a-tag>
          </template>
          <template v-else-if="column.key === 'zone_name'">
            <span v-if="record.zone_name">{{ record.zone_name }}</span>
            <span
              v-else
              style="color: #999"
            >未分配</span>
          </template>
          <template v-else-if="column.key === 'is_online'">
            <a-tag :color="record.is_online ? 'green' : 'default'">
              {{ record.is_online ? '在线' : '离线' }}
            </a-tag>
          </template>
          <template v-else-if="column.key === 'last_seen_at'">
            {{ formatTime(record.last_seen_at) }}
          </template>
          <template v-else-if="column.key === 'action'">
            <a-space>
              <a-button
                size="small"
                @click="goToDetail(record.id)"
              >
                详情
              </a-button>
              <a-dropdown>
                <a-button size="small">
                  更多
                  <down-outlined />
                </a-button>
                <template #overlay>
                  <a-menu>
                    <a-menu-item
                      key="edit"
                      @click="showEditModal(record)"
                    >
                      编辑
                    </a-menu-item>
                    <a-menu-item
                      key="control"
                      @click="showControlModal(record)"
                    >
                      远程控制
                    </a-menu-item>
                    <a-menu-divider />
                    <a-menu-item
                      key="delete"
                      danger
                      @click="handleDelete(record)"
                    >
                      删除
                    </a-menu-item>
                  </a-menu>
                </template>
              </a-dropdown>
            </a-space>
          </template>
        </template>
      </a-table>
    </a-card>

    <!-- 创建设备弹窗 -->
    <a-modal
      v-model:open="createModalVisible"
      title="添加设备"
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
          name="device_id"
          label="设备IMEI"
        >
          <a-input
            v-model:value="createForm.device_id"
            placeholder="请输入IMEI号"
          />
        </a-form-item>
        <a-form-item
          name="name"
          label="设备名称"
        >
          <a-input
            v-model:value="createForm.name"
            placeholder="请输入设备名称"
          />
        </a-form-item>
        <a-form-item
          name="zone_id"
          label="所属分区"
        >
          <a-select
            v-model:value="createForm.zone_id"
            placeholder="选择分区"
            allow-clear
          >
            <a-select-option
              v-for="zone in zones"
              :key="zone.id"
              :value="zone.id"
            >
              {{ zone.name }}
            </a-select-option>
          </a-select>
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- 编辑设备弹窗 -->
    <a-modal
      v-model:open="editModalVisible"
      title="编辑设备"
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
          label="设备名称"
        >
          <a-input
            v-model:value="editForm.name"
            placeholder="请输入设备名称"
          />
        </a-form-item>
        <a-form-item
          name="zone_id"
          label="所属分区"
        >
          <a-select
            v-model:value="editForm.zone_id"
            placeholder="选择分区"
            allow-clear
          >
            <a-select-option
              v-for="zone in zones"
              :key="zone.id"
              :value="zone.id"
            >
              {{ zone.name }}
            </a-select-option>
          </a-select>
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- 远程控制弹窗 -->
    <a-modal
      v-model:open="controlModalVisible"
      title="远程控制"
      :confirm-loading="controlLoading"
      @ok="handleControl"
    >
      <a-form layout="vertical">
        <a-form-item label="设备">
          <a-input
            :value="controlDevice?.name"
            disabled
          />
        </a-form-item>
        <a-form-item label="操作">
          <a-radio-group v-model:value="controlAction">
            <a-radio :value="1">
              开机
            </a-radio>
            <a-radio :value="0">
              关机
            </a-radio>
          </a-radio-group>
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { message, Modal } from 'ant-design-vue'
import { useDeviceStore } from '@/stores/devices'
import { useZoneStore } from '@/stores/zones'
import { useAuthStore } from '@/stores/auth'
import { PlusOutlined, DownOutlined } from '@ant-design/icons-vue'
import dayjs from 'dayjs'
import type { Device, DeviceCreate, DeviceUpdate } from '@/types'
import type { TableProps, FormInstance } from 'ant-design-vue'
import type { Rule } from 'ant-design-vue/es/form'

const router = useRouter()
const deviceStore = useDeviceStore()
const zoneStore = useZoneStore()
const authStore = useAuthStore()

// 状态
const searchKeyword = ref('')
const filterZone = ref<number | undefined>()
const filterOnline = ref<boolean | undefined>()
const filterProtocol = ref<string | undefined>()

// 数据
const devices = computed(() => deviceStore.devices)
const zones = computed(() => zoneStore.zones)
const loading = computed(() => deviceStore.loading)
const totalDevices = computed(() => deviceStore.totalDevices)

// 分页配置 - 初始化时从 store 获取 total
const pagination = reactive({
  current: deviceStore.currentPage,
  pageSize: deviceStore.pageSize,
  total: deviceStore.totalDevices,
  showSizeChanger: true,
  showTotal: (total: number) => `共 ${total} 条`
})

// 监听 store 中的总数变化，更新 pagination.total
watch(totalDevices, (newTotal) => {
  pagination.total = newTotal
}, { immediate: true })

// 表格列定义（10列）
const columns: TableProps['columns'] = [
  {
    title: '设备号',
    dataIndex: 'device_id',
    key: 'device_id',
    width: 130
  },
  {
    title: '设备名称',
    dataIndex: 'name',
    key: 'name',
    width: 130
  },
  {
    title: '温度',
    dataIndex: 'temp',
    key: 'temp',
    width: 90
  },
  {
    title: '湿度',
    dataIndex: 'humi',
    key: 'humi',
    width: 90
  },
  {
    title: '告警状态',
    dataIndex: 'alarmtemp',
    key: 'alarmtemp',
    width: 100
  },
  {
    title: '协议版本',
    dataIndex: 'protocol_version',
    key: 'protocol_version',
    width: 100
  },
  {
    title: '分区',
    dataIndex: 'zone_name',
    key: 'zone_name',
    width: 100
  },
  {
    title: '在线状态',
    dataIndex: 'is_online',
    key: 'is_online',
    width: 90
  },
  {
    title: '最后通信',
    dataIndex: 'last_seen_at',
    key: 'last_seen_at',
    width: 160
  },
  {
    title: '操作',
    key: 'action',
    width: 150,
    fixed: 'right'
  }
]

// 创建弹窗
const createModalVisible = ref(false)
const createLoading = ref(false)
const createFormRef = ref<FormInstance>()
const createForm = reactive<DeviceCreate>({
  device_id: '',
  name: '',
  tenant_id: authStore.user?.tenant_id || 0
})
const createRules: Record<string, Rule[]> = {
  device_id: [{ required: true, message: '请输入IMEI号', trigger: 'blur' }],
  name: [{ required: true, message: '请输入设备名称', trigger: 'blur' }]
}

// 编辑弹窗
const editModalVisible = ref(false)
const editLoading = ref(false)
const editFormRef = ref<FormInstance>()
const editForm = reactive<DeviceUpdate>({
  name: '',
  zone_id: undefined
})
const editRules: Record<string, Rule[]> = {
  name: [{ required: true, message: '请输入设备名称', trigger: 'blur' }]
}
const editDeviceId = ref<number>(0)

// 控制弹窗
const controlModalVisible = ref(false)
const controlLoading = ref(false)
const controlDevice = ref<Device | null>(null)
const controlAction = ref(1)

// 加载数据
onMounted(async () => {
  await zoneStore.fetchZones()
  await fetchDevices()
})

// 获取设备列表
async function fetchDevices() {
  await deviceStore.fetchDevices({
    keyword: searchKeyword.value,
    zone_id: filterZone.value,
    is_online: filterOnline.value,
    protocol_version: filterProtocol.value,
    skip: (pagination.current - 1) * pagination.pageSize,
    limit: pagination.pageSize
  })
}

// 搜索
function handleSearch() {
  pagination.current = 1
  fetchDevices()
}

// 表格变化
function handleTableChange(page: any) {
  pagination.current = page.current
  pagination.pageSize = page.pageSize
  fetchDevices()
}

// 格式化时间
function formatTime(time: string | null) {
  if (!time) return '-'
  return dayjs(time).format('YYYY-MM-DD HH:mm:ss')
}

// 导航到详情页
function goToDetail(id: number) {
  router.push({ name: 'DeviceDetail', params: { id } })
}

// 显示创建弹窗
function showCreateModal() {
  createForm.device_id = ''
  createForm.name = ''
  createForm.zone_id = undefined
  createForm.tenant_id = authStore.user?.tenant_id || 0
  createModalVisible.value = true
}

// 创建设备
async function handleCreate() {
  try {
    await createFormRef.value?.validateFields()
    createLoading.value = true
    const result = await deviceStore.createDevice(createForm)
    if (result) {
      message.success('设备创建成功')
      createModalVisible.value = false
      fetchDevices()
    }
  } catch {
    // 验证失败
  } finally {
    createLoading.value = false
  }
}

// 显示编辑弹窗
function showEditModal(device: Device) {
  editDeviceId.value = device.id
  editForm.name = device.name
  editForm.zone_id = device.zone_id
  editModalVisible.value = true
}

// 编辑设备
async function handleEdit() {
  try {
    await editFormRef.value?.validateFields()
    editLoading.value = true
    const result = await deviceStore.updateDevice(editDeviceId.value, editForm)
    if (result) {
      message.success('设备更新成功')
      editModalVisible.value = false
      fetchDevices()
    }
  } catch {
    // 验证失败
  } finally {
    editLoading.value = false
  }
}

// 显示控制弹窗
function showControlModal(device: Device) {
  controlDevice.value = device
  controlAction.value = 1
  controlModalVisible.value = true
}

// 远程控制
async function handleControl() {
  if (!controlDevice.value) return
  controlLoading.value = true
  const success = await deviceStore.controlDevice(controlDevice.value.id, controlAction.value)
  if (success) {
    message.success('控制命令已发送')
    controlModalVisible.value = false
  }
  controlLoading.value = false
}

// 删除设备
function handleDelete(device: Device) {
  Modal.confirm({
    title: '确认删除',
    content: `确定要删除设备 "${device.name}" 吗？`,
    okText: '删除',
    okType: 'danger',
    cancelText: '取消',
    async onOk() {
      const success = await deviceStore.deleteDevice(device.id)
      if (success) {
        message.success('设备已删除')
        fetchDevices()
      }
    }
  })
}
</script>

<style scoped>
.devices-page {
  padding: 0;
}

.toolbar-card {
  margin-bottom: 16px;
}

.table-card {
  min-height: 400px;
}
</style>