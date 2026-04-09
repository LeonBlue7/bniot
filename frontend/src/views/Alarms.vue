<template>
  <div class="alarms-page">
    <!-- 页面头部 -->
    <div class="page-header-section">
      <div class="header-content">
        <h1 class="page-title">告警中心</h1>
        <p class="page-subtitle">设备告警监控与处理</p>
      </div>
      <div class="header-actions">
        <a-button class="action-btn" @click="resolveSelected" :disabled="selectedAlarms.length === 0">
          <CheckOutlined /> 批量处理
        </a-button>
      </div>
    </div>

    <!-- 过滤器 -->
    <div class="filter-bar">
      <div class="filter-group">
        <label class="filter-label">状态</label>
        <a-select v-model:value="statusFilter" style="width: 120px" @change="fetchAlarms">
          <a-select-option value="">全部</a-select-option>
          <a-select-option value="unresolved">未处理</a-select-option>
          <a-select-option value="resolved">已处理</a-select-option>
        </a-select>
      </div>
      <div class="filter-group">
        <label class="filter-label">严重程度</label>
        <a-select v-model:value="severityFilter" style="width: 120px" @change="fetchAlarms">
          <a-select-option value="">全部</a-select-option>
          <a-select-option value="high">高</a-select-option>
          <a-select-option value="medium">中</a-select-option>
          <a-select-option value="low">低</a-select-option>
        </a-select>
      </div>
      <div class="filter-group">
        <label class="filter-label">设备ID</label>
        <a-input v-model:value="deviceIdFilter" placeholder="搜索设备" style="width: 180px" @pressEnter="fetchAlarms" />
      </div>
    </div>

    <!-- 告警列表 -->
    <div class="alarms-table-container">
      <a-table
        :columns="columns"
        :data-source="alarms"
        :loading="loading"
        :row-selection="{ selectedRowKeys: selectedAlarms, onChange: onSelectionChange }"
        row-key="id"
        :pagination="pagination"
        @change="handleTableChange"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'severity'">
            <span class="severity-badge" :class="record.severity">
              {{ severityText(record.severity) }}
            </span>
          </template>
          <template v-if="column.key === 'status'">
            <span class="status-badge" :class="record.is_resolved ? 'resolved' : 'unresolved'">
              {{ record.is_resolved ? '已处理' : '未处理' }}
            </span>
          </template>
          <template v-if="column.key === 'type'">
            {{ alarmTypeText(record.type) }}
          </template>
          <template v-if="column.key === 'occurred_at'">
            <span class="data-value">{{ formatTime(record.occurred_at) }}</span>
          </template>
          <template v-if="column.key === 'actions'">
            <a-button type="link" size="small" @click="resolveAlarm(record)" v-if="!record.is_resolved">
              处理
            </a-button>
            <a-button type="link" size="small" @click="viewDevice(record.device_id)">
              查看设备
            </a-button>
          </template>
        </template>
      </a-table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { CheckOutlined } from '@ant-design/icons-vue'
import type { TableProps } from 'ant-design-vue'

interface Alarm {
  id: number
  tenant_id: number
  device_id: string
  type: string
  severity: string
  message?: string
  details: Record<string, unknown>
  is_resolved: boolean
  occurred_at: string
  resolved_at?: string
}

const router = useRouter()

const loading = ref(false)
const alarms = ref<Alarm[]>([])
const selectedAlarms = ref<number[]>([])
const statusFilter = ref('')
const severityFilter = ref('')
const deviceIdFilter = ref('')

const pagination = reactive({
  current: 1,
  pageSize: 20,
  total: 0,
  showSizeChanger: true,
  showQuickJumper: true
})

const columns: TableProps['columns'] = [
  { title: '设备ID', dataIndex: 'device_id', key: 'device_id', width: 140 },
  { title: '类型', dataIndex: 'type', key: 'type', width: 120 },
  { title: '严重程度', dataIndex: 'severity', key: 'severity', width: 100 },
  { title: '消息', dataIndex: 'message', key: 'message', ellipsis: true },
  { title: '状态', dataIndex: 'status', key: 'status', width: 100 },
  { title: '发生时间', dataIndex: 'occurred_at', key: 'occurred_at', width: 160 },
  { title: '操作', key: 'actions', width: 140, fixed: 'right' }
]

// 获取告警列表
async function fetchAlarms() {
  loading.value = true
  try {
    // TODO: 实际 API 调用
    // const response = await api.getAlarms({
    //   status: statusFilter.value,
    //   severity: severityFilter.value,
    //   device_id: deviceIdFilter.value,
    //   page: pagination.current,
    //   page_size: pagination.pageSize
    // })
    // alarms.value = response.data.items
    // pagination.total = response.data.total

    // 模拟数据
    alarms.value = []
  } finally {
    loading.value = false
  }
}

// 选择变化
function onSelectionChange(keys: number[]) {
  selectedAlarms.value = keys
}

// 表格变化
function handleTableChange(pag: { current?: number; pageSize?: number }) {
  pagination.current = pag.current || 1
  pagination.pageSize = pag.pageSize || 20
  fetchAlarms()
}

// 处理告警
async function resolveAlarm(alarm: Alarm) {
  // TODO: 调用 API 处理告警
  message.info('告警处理功能待实现')
  fetchAlarms()
}

// 批量处理
async function resolveSelected() {
  // TODO: 调用 API 批量处理
  message.info('批量处理功能待实现')
  selectedAlarms.value = []
  fetchAlarms()
}

// 查看设备
function viewDevice(deviceId: string) {
  router.push({ name: 'DeviceDetail', params: { id: deviceId } })
}

// 格式化时间
function formatTime(time: string) {
  return new Date(time).toLocaleString('zh-CN')
}

// 严重程度文本
function severityText(severity: string) {
  const map: Record<string, string> = {
    high: '高',
    medium: '中',
    low: '低'
  }
  return map[severity] || severity
}

// 告警类型文本
function alarmTypeText(type: string) {
  const map: Record<string, string> = {
    offline: '设备离线',
    illegal_on: '非法开启',
    temp_alarm: '温度告警',
    humi_alarm: '湿度告警'
  }
  return map[type] || type
}

onMounted(() => {
  fetchAlarms()
})
</script>

<style scoped>
.alarms-page {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.page-header-section {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: var(--space-5);
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border-primary);
  border-radius: var(--radius-lg);
}

.header-content {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  margin: 0;
}

.page-subtitle {
  font-size: 14px;
  color: var(--color-text-secondary);
  margin: 0;
}

.action-btn {
  background: var(--color-bg-tertiary) !important;
  border-color: var(--color-border-primary) !important;
  color: var(--color-text-primary) !important;
}

.filter-bar {
  display: flex;
  gap: var(--space-4);
  padding: var(--space-4);
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border-primary);
  border-radius: var(--radius-lg);
}

.filter-group {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.filter-label {
  font-size: 12px;
  color: var(--color-text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.alarms-table-container {
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border-primary);
  border-radius: var(--radius-lg);
  padding: var(--space-4);
}

.severity-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: var(--radius-sm);
  font-size: 12px;
  font-weight: 500;
}

.severity-badge.high {
  background: rgba(255, 59, 59, 0.15);
  color: var(--color-status-danger);
}

.severity-badge.medium {
  background: rgba(255, 193, 7, 0.15);
  color: var(--color-status-warning);
}

.severity-badge.low {
  background: rgba(0, 255, 136, 0.15);
  color: var(--color-status-normal);
}

.status-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: var(--radius-sm);
  font-size: 12px;
}

.status-badge.unresolved {
  background: rgba(255, 59, 59, 0.1);
  color: var(--color-status-danger);
}

.status-badge.resolved {
  background: rgba(0, 255, 136, 0.1);
  color: var(--color-status-normal);
}
</style>