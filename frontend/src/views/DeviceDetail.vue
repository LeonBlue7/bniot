<template>
  <div class="device-detail">
    <a-page-header
      :title="device?.name || '设备详情'"
      :sub-title="device?.device_id"
      @back="goBack"
    >
      <template #extra>
        <a-space>
          <a-button :type="device?.is_online ? 'primary' : 'default'" @click="handleControl(1)">
            开机
          </a-button>
          <a-button :type="!device?.is_online ? 'primary' : 'default'" @click="handleControl(0)">
            关机
          </a-button>
        </a-space>
      </template>
    </a-page-header>

    <a-spin :spinning="loading">
      <a-row :gutter="16">
        <!-- 基本信息 -->
        <a-col :span="8">
          <a-card title="基本信息" size="small">
            <a-descriptions :column="1" size="small">
              <a-descriptions-item label="IMEI号">
                {{ device?.device_id }}
              </a-descriptions-item>
              <a-descriptions-item label="协议版本">
                {{ device?.protocol_version }}
              </a-descriptions-item>
              <a-descriptions-item label="在线状态">
                <a-tag :color="device?.is_online ? 'green' : 'red'">
                  {{ device?.is_online ? '在线' : '离线' }}
                </a-tag>
              </a-descriptions-item>
              <a-descriptions-item label="最后通信">
                {{ formatTime(device?.last_seen_at) }}
              </a-descriptions-item>
              <a-descriptions-item label="SIM卡号">
                {{ device?.sim_card || '-' }}
              </a-descriptions-item>
              <a-descriptions-item label="创建时间">
                {{ formatTime(device?.created_at) }}
              </a-descriptions-item>
            </a-descriptions>
          </a-card>
        </a-col>

        <!-- 实时数据 -->
        <a-col :span="8">
          <a-card title="实时数据" size="small">
            <a-row :gutter="16">
              <a-col :span="12">
                <a-statistic
                  title="温度"
                  :value="device?.settings?.temp ?? '-'"
                  suffix="C"
                />
              </a-col>
              <a-col :span="12">
                <a-statistic
                  title="湿度"
                  :value="device?.settings?.humi ?? '-'"
                  suffix="%"
                />
              </a-col>
            </a-row>
            <a-row :gutter="16" style="margin-top: 16px">
              <a-col :span="12">
                <a-statistic
                  title="空调状态"
                  :value="getAirStateText(device?.settings?.airstate)"
                />
              </a-col>
              <a-col :span="12">
                <a-statistic
                  title="信号强度"
                  :value="device?.settings?.csq ?? '-'"
                  suffix="dB"
                />
              </a-col>
            </a-row>
          </a-card>
        </a-col>

        <!-- 参数设置 -->
        <a-col :span="8">
          <a-card title="参数设置" size="small">
            <a-empty v-if="!device?.settings" description="暂无参数数据" />
            <a-descriptions v-else :column="1" size="small">
              <a-descriptions-item label="联动模式">
                {{ getLinkageMode(device?.settings?.['101']) }}
              </a-descriptions-item>
              <a-descriptions-item label="温度设定">
                {{ device?.settings?.['102'] ?? '-' }} C
              </a-descriptions-item>
              <a-descriptions-item label="上送周期">
                {{ device?.settings?.['501'] ?? '-' }} 分钟
              </a-descriptions-item>
            </a-descriptions>
            <a-button type="link" style="margin-top: 8px">
              查看完整参数
            </a-button>
          </a-card>
        </a-col>
      </a-row>

      <!-- 历史数据图表 -->
      <a-card title="历史数据" style="margin-top: 16px">
        <a-radio-group v-model:value="dataRange" @change="fetchHistoryData">
          <a-radio-button value="24">24小时</a-radio-button>
          <a-radio-button value="72">3天</a-radio-button>
          <a-radio-button value="168">7天</a-radio-button>
        </a-radio-group>
        <a-table
          :columns="dataColumns"
          :data-source="deviceData"
          :loading="dataLoading"
          :pagination="{ pageSize: 20 }"
          row-key="id"
          style="margin-top: 16px"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'time'">
              {{ formatTime(record.time) }}
            </template>
            <template v-else-if="column.key === 'airstate'">
              <a-tag :color="record.airstate ? 'green' : 'default'">
                {{ record.airstate ? '开机' : '关机' }}
              </a-tag>
            </template>
          </template>
        </a-table>
      </a-card>
    </a-spin>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { message } from 'ant-design-vue'
import { useDeviceStore } from '@/stores/devices'
import dayjs from 'dayjs'
import type { TableProps } from 'ant-design-vue'

const router = useRouter()
const route = useRoute()
const deviceStore = useDeviceStore()

const deviceId = computed(() => Number(route.params.id))
const device = computed(() => deviceStore.currentDevice)
const deviceData = computed(() => deviceStore.deviceData)
const loading = computed(() => deviceStore.loading)

const dataRange = ref(24)
const dataLoading = ref(false)

// 数据表格列
const dataColumns: TableProps['columns'] = [
  { title: '时间', dataIndex: 'time', key: 'time', width: 180 },
  { title: '温度', dataIndex: 'temp', key: 'temp', width: 100 },
  { title: '湿度', dataIndex: 'humi', key: 'humi', width: 100 },
  { title: '空调状态', dataIndex: 'airstate', key: 'airstate', width: 100 },
  { title: '电流', dataIndex: 'current', key: 'current', width: 100 },
  { title: '信号', dataIndex: 'csq', key: 'csq', width: 80 }
]

// 加载设备详情
onMounted(async () => {
  await deviceStore.fetchDevice(deviceId.value)
  await fetchHistoryData()
})

onUnmounted(() => {
  deviceStore.clearCurrentDevice()
})

// 格式化时间
function formatTime(time: string | null | undefined) {
  if (!time) return '-'
  return dayjs(time).format('YYYY-MM-DD HH:mm:ss')
}

// 获取空调状态文本
function getAirStateText(state: unknown) {
  if (state === undefined || state === null) return '-'
  const numState = Number(state)
  return isNaN(numState) ? '-' : (numState === 1 ? '开机' : '关机')
}

// 获取联动模式文本
function getLinkageMode(mode: unknown) {
  if (mode === undefined || mode === null) return '-'
  const numMode = Number(mode)
  if (isNaN(numMode)) return '-'
  const modes: Record<number, string> = {
    0: '关闭',
    1: '温度联动',
    2: '时间段联动',
    3: '温度+时间联动'
  }
  return modes[numMode] || '未知'
}

// 返回上一页
function goBack() {
  router.push({ name: 'Devices' })
}

// 远程控制
async function handleControl(airstate: number) {
  if (!device.value) return
  const success = await deviceStore.controlDevice(device.value.id, airstate)
  if (success) {
    message.success('控制命令已发送')
  }
}

// 获取历史数据
async function fetchHistoryData() {
  dataLoading.value = true
  await deviceStore.fetchDeviceData(deviceId.value, dataRange.value)
  dataLoading.value = false
}

// 监听设备 ID 变化
watch(deviceId, (newId) => {
  if (newId) {
    deviceStore.fetchDevice(newId)
    fetchHistoryData()
  }
})
</script>

<style scoped>
.device-detail {
  padding: 0;
}

:deep(.ant-page-header) {
  padding: 0 0 16px 0;
}
</style>