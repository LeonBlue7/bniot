<template>
  <div class="device-detail">
    <a-page-header
      :title="device?.name || '设备详情'"
      :sub-title="device?.device_id"
      @back="goBack"
    >
      <template #extra>
        <a-space>
          <a-button
            :type="device?.is_online ? 'primary' : 'default'"
            @click="handleControl(1)"
          >
            开机
          </a-button>
          <a-button
            :type="!device?.is_online ? 'primary' : 'default'"
            @click="handleControl(0)"
          >
            关机
          </a-button>
        </a-space>
      </template>
    </a-page-header>

    <a-spin :spinning="loading">
      <a-row :gutter="16">
        <!-- 基本信息 -->
        <a-col :span="8">
          <a-card
            title="基本信息"
            size="small"
          >
            <a-descriptions
              :column="1"
              size="small"
            >
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
              <a-descriptions-item label="固件版本">
                {{ device?.firmware_version || '-' }}
              </a-descriptions-item>
              <a-descriptions-item label="所属分区">
                {{ device?.zone_name || '未分配' }}
              </a-descriptions-item>
              <a-descriptions-item label="创建时间">
                {{ formatTime(device?.created_at) }}
              </a-descriptions-item>
            </a-descriptions>
          </a-card>
        </a-col>

        <!-- 实时数据 -->
        <a-col :span="8">
          <a-card
            title="实时数据"
            size="small"
          >
            <a-row :gutter="16">
              <a-col :span="12">
                <a-statistic
                  title="温度"
                  :value="device?.is_online && device?.temp != null ? device.temp.toFixed(1) : '-'"
                  suffix="C"
                />
              </a-col>
              <a-col :span="12">
                <a-statistic
                  title="湿度"
                  :value="device?.is_online && device?.humi != null ? device.humi.toFixed(1) : '-'"
                  suffix="%"
                />
              </a-col>
            </a-row>
            <a-row
              :gutter="16"
              style="margin-top: 16px"
            >
              <a-col :span="12">
                <a-statistic
                  title="信号强度"
                  :value="device?.is_online ? (device?.csq ?? '-') : '-'"
                  suffix="dB"
                />
              </a-col>
              <a-col :span="12">
                <a-statistic
                  v-if="device?.is_online && device?.current != null"
                  title="电流"
                  :value="device.current.toFixed(2)"
                  suffix="A"
                />
                <a-statistic
                  v-else
                  title="电流"
                  value="-"
                  suffix="A"
                />
              </a-col>
            </a-row>
            <!-- 空调状态（版本差异化） -->
            <a-row
              v-if="device?.is_online && device?.airstate != null"
              :gutter="16"
              style="margin-top: 16px"
            >
              <a-col :span="12">
                <a-statistic title="空调状态">
                  <template #formatter>
                    <a-tag :color="device.airstate === 1 ? 'green' : 'default'">
                      {{ device.airstate === 1 ? '开机' : '关机' }}
                    </a-tag>
                  </template>
                </a-statistic>
              </a-col>
            </a-row>
          </a-card>
        </a-col>

        <!-- 告警状态 -->
        <a-col :span="8">
          <a-card
            title="告警状态"
            size="small"
          >
            <a-descriptions
              :column="1"
              size="small"
            >
              <a-descriptions-item label="温度告警">
                <a-tag
                  v-if="device?.alarmtemp"
                  color="red"
                >
                  告警
                </a-tag>
                <span v-else>正常</span>
              </a-descriptions-item>
              <a-descriptions-item label="湿度告警">
                <a-tag
                  v-if="device?.alarmhumi"
                  color="orange"
                >
                  告警
                </a-tag>
                <span v-else>正常</span>
              </a-descriptions-item>
              <a-descriptions-item label="空调故障">
                <a-tag
                  v-if="device?.air_err"
                  color="red"
                >
                  故障({{ device.air_err }})
                </a-tag>
                <span v-else>正常</span>
              </a-descriptions-item>
            </a-descriptions>
          </a-card>
        </a-col>
      </a-row>

      <!-- 运行统计（版本差异化 - 仅支持 airstate 的设备显示） -->
      <a-card
        v-if="device?.supports_runtime"
        title="运行统计"
        style="margin-top: 16px"
      >
        <a-row :gutter="16">
          <a-col :span="12">
            <a-statistic
              title="当天运行"
              :value="device?.today_runtime != null ? device.today_runtime.toFixed(1) : 0"
              suffix="小时"
            />
          </a-col>
          <a-col :span="12">
            <a-statistic
              title="当月运行"
              :value="device?.month_runtime != null ? device.month_runtime.toFixed(1) : 0"
              suffix="小时"
            />
          </a-col>
        </a-row>
      </a-card>

      <!-- 开关机记录（版本差异化） -->
      <a-card
        title="开关机记录"
        style="margin-top: 16px"
      >
        <a-table
          v-if="events?.supported"
          :columns="eventColumns"
          :data-source="events?.events"
          :loading="eventsLoading"
          :pagination="{
            current: events?.page || 1,
            pageSize: events?.page_size || 20,
            total: events?.total || 0,
            onChange: handleEventsPageChange
          }"
          row-key="time"
          size="small"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'time'">
              {{ formatTime(record.time) }}
            </template>
            <template v-else-if="column.key === 'action'">
              <a-tag :color="record.action === '开机' ? 'green' : 'default'">
                {{ record.action }}
              </a-tag>
            </template>
            <template v-else-if="column.key === 'duration'">
              {{ record.duration != null ? `${record.duration} 小时` : '-' }}
            </template>
          </template>
        </a-table>
        <a-empty
          v-else
          description="当前协议版本不支持空调状态监控"
        />
      </a-card>

      <!-- 参数设置 -->
      <a-card
        title="参数设置"
        style="margin-top: 16px"
        size="small"
      >
        <template #extra>
          <a-button
            type="primary"
            size="small"
            @click="showParamEditModal"
          >
            编辑参数
          </a-button>
        </template>
        <a-empty
          v-if="!device?.settings"
          description="暂无参数数据"
        />
        <a-descriptions
          v-else
          :column="2"
          size="small"
        >
          <a-descriptions-item label="联动模式">
            {{ getLinkageMode(device?.settings?.['101']) }}
          </a-descriptions-item>
          <a-descriptions-item label="温度设定">
            {{ device?.settings?.['102'] ?? '-' }} C
          </a-descriptions-item>
          <a-descriptions-item label="上送周期">
            {{ device?.settings?.['501'] ?? '-' }} 分钟
          </a-descriptions-item>
          <a-descriptions-item label="温度告警阈值">
            {{ device?.settings?.['401'] ?? '-' }} C
          </a-descriptions-item>
        </a-descriptions>
        <a-button
          type="link"
          style="margin-top: 8px"
          @click="showFullParams"
        >
          查看完整参数
        </a-button>
      </a-card>

      <!-- 历史数据图表 -->
      <a-card
        title="历史数据"
        style="margin-top: 16px"
      >
        <a-radio-group
          v-model:value="dataRange"
          @change="fetchHistoryData"
        >
          <a-radio-button value="24">
            24小时
          </a-radio-button>
          <a-radio-button value="72">
            3天
          </a-radio-button>
          <a-radio-button value="168">
            7天
          </a-radio-button>
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

    <!-- 完整参数弹窗 -->
    <a-modal
      v-model:open="paramsModalVisible"
      title="完整参数"
      width="800px"
      :footer="null"
    >
      <a-descriptions
        v-if="device?.settings"
        :column="2"
        bordered
        size="small"
      >
        <a-descriptions-item label="联动模式(101)">
          {{ getLinkageMode(device?.settings?.['101']) }}
        </a-descriptions-item>
        <a-descriptions-item label="温度设定(102)">
          {{ device?.settings?.['102'] ?? '-' }} C
        </a-descriptions-item>
        <a-descriptions-item label="夏天开机温度(103)">
          {{ device?.settings?.['103'] ?? '-' }} C
        </a-descriptions-item>
        <a-descriptions-item label="夏天关机温度(104)">
          {{ device?.settings?.['104'] ?? '-' }} C
        </a-descriptions-item>
        <a-descriptions-item label="上送周期(501)">
          {{ device?.settings?.['501'] ?? '-' }} 分钟
        </a-descriptions-item>
        <a-descriptions-item label="温度告警阈值(401)">
          {{ device?.settings?.['401'] ?? '-' }} C
        </a-descriptions-item>
        <a-descriptions-item label="湿度告警阈值(402)">
          {{ device?.settings?.['402'] ?? '-' }} %
        </a-descriptions-item>
        <a-descriptions-item label="空调故障码">
          {{ device?.air_err ?? '正常' }}
        </a-descriptions-item>
      </a-descriptions>
    </a-modal>

    <!-- 参数编辑弹窗 -->
    <a-modal
      v-model:open="paramEditModalVisible"
      title="参数设置"
      width="600px"
      :confirm-loading="paramEditLoading"
      @ok="handleParamEditSubmit"
      @cancel="resetParamEditForm"
    >
      <a-spin :spinning="paramsLoading">
        <a-form
          ref="paramEditFormRef"
          :model="paramEditForm"
          :label-col="{ span: 6 }"
          :wrapper-col="{ span: 18 }"
        >
          <a-alert
            v-if="device?.protocol_version === 'V10'"
            message="当前设备为 V10 版本，部分参数不可设置"
            type="info"
            show-icon
            style="margin-bottom: 16px"
          />

          <!-- 联动模式 -->
          <a-form-item
            label="联动模式"
            name="101"
          >
            <a-select v-model:value="paramEditForm['101']">
              <a-select-option :value="0">
                关闭
              </a-select-option>
              <a-select-option :value="1">
                温度联动
              </a-select-option>
              <a-select-option :value="2">
                时间段联动
              </a-select-option>
              <a-select-option :value="3">
                温度+时间联动
              </a-select-option>
            </a-select>
          </a-form-item>

          <!-- 温度设定 -->
          <a-form-item
            label="温度设定"
            name="102"
          >
            <a-input-number
              v-model:value="paramEditForm['102']"
              :min="-5"
              :max="45"
              :precision="1"
              addon-after="C"
            />
          </a-form-item>

          <!-- 空调开机条件 -->
          <a-divider>空调开机条件</a-divider>

          <!-- 夏天开机温度 -->
          <a-form-item
            label="夏天开机温度"
            name="103"
          >
            <a-input-number
              v-model:value="paramEditForm['103']"
              :min="-5"
              :max="45"
              :precision="1"
              addon-after="C"
            />
          </a-form-item>

          <!-- 夏天关机温度 -->
          <a-form-item
            label="夏天关机温度"
            name="104"
          >
            <a-input-number
              v-model:value="paramEditForm['104']"
              :min="-5"
              :max="45"
              :precision="1"
              addon-after="C"
            />
          </a-form-item>

          <!-- 冬天开机温度 (V10) -->
          <a-form-item
            v-if="device?.protocol_version === 'V10'"
            label="冬天开机温度"
            name="105"
          >
            <a-input-number
              v-model:value="paramEditForm['105']"
              :min="-5"
              :max="45"
              :precision="1"
              addon-after="C"
            />
          </a-form-item>

          <!-- 冬天关机温度 (V10:106, V20:107) -->
          <a-form-item
            label="冬天关机温度"
            :name="device?.protocol_version === 'V20' ? '107' : '106'"
          >
            <a-input-number
              v-model:value="paramEditForm[device?.protocol_version === 'V20' ? '107' : '106']"
              :min="-5"
              :max="45"
              :precision="1"
              addon-after="C"
            />
          </a-form-item>

          <!-- V20 独有参数 -->
          <template v-if="device?.protocol_version === 'V20'">
            <a-divider>V20 独有参数</a-divider>

            <!-- 冬天开始月份 -->
            <a-form-item
              label="冬天开始月份"
              name="108"
            >
              <a-input-number
                v-model:value="paramEditForm['108']"
                :min="1"
                :max="12"
              />
            </a-form-item>

            <!-- 冬天结束月份 -->
            <a-form-item
              label="冬天结束月份"
              name="109"
            >
              <a-input-number
                v-model:value="paramEditForm['109']"
                :min="1"
                :max="12"
              />
            </a-form-item>

            <!-- 空调关机间隔 -->
            <a-form-item
              label="空调关机间隔"
              name="110"
            >
              <a-input-number
                v-model:value="paramEditForm['110']"
                :min="1"
                :max="60"
                addon-after="分钟"
              />
            </a-form-item>
          </template>

          <!-- 开关机时间设置 -->
          <a-divider>开关机时间设置</a-divider>

          <!-- 开机时间段1 -->
          <a-form-item
            label="开机时间段1"
            name="201"
          >
            <a-input
              v-model:value="paramEditForm['201']"
              placeholder="HH:MM~HH:MM"
            />
          </a-form-item>

          <!-- 关机时间段1 -->
          <a-form-item
            label="关机时间段1"
            name="202"
          >
            <a-input
              v-model:value="paramEditForm['202']"
              placeholder="HH:MM~HH:MM"
            />
          </a-form-item>

          <!-- 开机时间段2 -->
          <a-form-item
            label="开机时间段2"
            name="203"
          >
            <a-input
              v-model:value="paramEditForm['203']"
              placeholder="HH:MM~HH:MM"
            />
          </a-form-item>

          <!-- 关机时间段2 -->
          <a-form-item
            label="关机时间段2"
            name="204"
          >
            <a-input
              v-model:value="paramEditForm['204']"
              placeholder="HH:MM~HH:MM"
            />
          </a-form-item>

          <!-- 其他参数 -->
          <a-divider>其他参数</a-divider>

          <!-- 上送周期 -->
          <a-form-item
            label="上送周期"
            name="501"
          >
            <a-input-number
              v-model:value="paramEditForm['501']"
              :min="1"
              :max="1440"
              addon-after="分钟"
            />
          </a-form-item>

          <!-- 温度告警阈值 -->
          <a-form-item
            label="温度告警阈值"
            name="401"
          >
            <a-input-number
              v-model:value="paramEditForm['401']"
              :min="-5"
              :max="45"
              :precision="1"
              addon-after="C"
            />
          </a-form-item>

          <!-- 湿度告警阈值 -->
          <a-form-item
            label="湿度告警阈值"
            name="402"
          >
            <a-input-number
              v-model:value="paramEditForm['402']"
              :min="0"
              :max="100"
              :precision="1"
              addon-after="%"
            />
          </a-form-item>
        </a-form>
      </a-spin>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { message } from 'ant-design-vue'
import { useDeviceStore } from '@/stores/devices'
import { deviceApi } from '@/api/devices'
import type { DeviceParamsResponse } from '@/api/devices'
import dayjs from 'dayjs'
import type { TableProps, FormInstance } from 'ant-design-vue'
import type { DeviceEventsResponse } from '@/api/devices'

const router = useRouter()
const route = useRoute()
const deviceStore = useDeviceStore()

const deviceId = computed(() => Number(route.params.id))
const device = computed(() => deviceStore.currentDevice)
const deviceData = computed(() => deviceStore.deviceData)
const loading = computed(() => deviceStore.loading)

const dataRange = ref(24)
const dataLoading = ref(false)
const eventsLoading = ref(false)
const events = ref<DeviceEventsResponse | null>(null)
const paramsModalVisible = ref(false)

// 参数编辑弹窗相关
const paramEditModalVisible = ref(false)
const paramEditLoading = ref(false)
const paramsLoading = ref(false)
const paramEditFormRef = ref<FormInstance>()
const paramEditForm = ref<Record<string, any>>({})
const deviceParams = ref<DeviceParamsResponse | null>(null)

// 开关机事件表格列
const eventColumns: TableProps['columns'] = [
  { title: '时间', dataIndex: 'time', key: 'time', width: 180 },
  { title: '动作', dataIndex: 'action', key: 'action', width: 100 },
  { title: '持续时间', dataIndex: 'duration', key: 'duration', width: 120 }
]

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
  await fetchEvents()
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

// 获取开关机事件
async function fetchEvents(page: number = 1) {
  eventsLoading.value = true
  try {
    events.value = await deviceApi.getEvents(deviceId.value, {
      page,
      page_size: 20
    })
  } catch (err) {
    // 显示错误提示给用户
    message.warning('获取开关机记录失败，请稍后重试')
    events.value = {
      supported: false,
      message: '获取开关机记录失败',
      events: [],
      total: 0,
      page: 1,
      page_size: 20
    }
  } finally {
    eventsLoading.value = false
  }
}

// 开关机事件分页变化
function handleEventsPageChange(page: number) {
  fetchEvents(page)
}

// 显示完整参数弹窗
function showFullParams() {
  paramsModalVisible.value = true
}

// 显示参数编辑弹窗
async function showParamEditModal() {
  paramEditModalVisible.value = true
  paramsLoading.value = true

  try {
    // 获取设备参数信息
    deviceParams.value = await deviceApi.getParams(deviceId.value)

    // 用当前值初始化表单
    const settings = device.value?.settings || {}
    paramEditForm.value = {}

    // 填充表单默认值
    for (const param of deviceParams.value.params) {
      if (param.current_value != null) {
        paramEditForm.value[param.code] = param.current_value
      }
    }
  } catch (err) {
    message.error('获取参数信息失败')
    paramEditModalVisible.value = false
  } finally {
    paramsLoading.value = false
  }
}

// 提交参数编辑
async function handleParamEditSubmit() {
  paramEditLoading.value = true

  try {
    // 验证时间段格式
    const timeParams = ['201', '202', '203', '204']
    for (const code of timeParams) {
      const value = paramEditForm.value[code]
      if (value && !isValidTimePeriod(value)) {
        message.error(`时间段格式错误，应为 HH:MM~HH:MM`)
        paramEditLoading.value = false
        return
      }
    }

    // 过滤出有变化的参数
    const changedParams: Record<string, any> = {}
    const settings = device.value?.settings || {}

    for (const [code, value] of Object.entries(paramEditForm.value)) {
      // 只发送有变化且不为空的参数
      if (value != null && value !== '' && settings[code] !== value) {
        changedParams[code] = value
      }
    }

    if (Object.keys(changedParams).length === 0) {
      message.info('没有参数需要修改')
      paramEditModalVisible.value = false
      paramEditLoading.value = false
      return
    }

    // 使用批量参数设置 API（支持多参数单设备）
    const result = await deviceApi.batchSetParam([deviceId.value], changedParams)

    if (result.success_count > 0) {
      message.success('参数设置命令已发送')
      paramEditModalVisible.value = false

      // 刷新设备信息
      await deviceStore.fetchDevice(deviceId.value)
    } else {
      const failedReason = result.failed_details[0]?.reason || '参数设置失败'
      message.error(failedReason)
    }
  } catch (err: any) {
    message.error(err.response?.data?.detail || '参数设置失败')
  } finally {
    paramEditLoading.value = false
  }
}

// 重置参数编辑表单
function resetParamEditForm() {
  paramEditForm.value = {}
  deviceParams.value = null
}

// 验证时间段格式
function isValidTimePeriod(value: string): boolean {
  const pattern = /^\d{2}:\d{2}~\d{2}:\d{2}$/
  if (!pattern.test(value)) return false

  const parts = value.split('~')
  for (const part of parts) {
    const [hour, minute] = part.split(':').map(Number)
    if (hour < 0 || hour > 23 || minute < 0 || minute > 59) {
      return false
    }
  }
  return true
}

// 监听设备 ID 变化
watch(deviceId, (newId) => {
  if (newId) {
    deviceStore.fetchDevice(newId)
    fetchHistoryData()
    fetchEvents()
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