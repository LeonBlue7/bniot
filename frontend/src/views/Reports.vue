<script setup lang="ts">
/**
 * 报表分析页面
 * Phase 4 报表与分析功能
 * 集成 ECharts 图表组件
 * 使用 defineAsyncComponent 实现图表懒加载，优化初始打包体积
 */
import { ref, computed, onMounted, defineAsyncComponent } from 'vue'
import { message } from 'ant-design-vue'
import dayjs, { type Dayjs } from 'dayjs'
import { reportApi } from '@/api/reports'
import { zoneApi } from '@/api/zones'
import type {
  EnergyStats,
  TrendData,
  AlarmStats,
  RuntimeStats,
  Zone
} from '@/types'

// 图表组件懒加载配置
// 使用 defineAsyncComponent 实现代码分割，减少初始包体积
const EnergyChart = defineAsyncComponent(() =>
  import('@/components/charts/EnergyChart.vue')
)

const TrendChart = defineAsyncComponent(() =>
  import('@/components/charts/TrendChart.vue')
)

const AlarmPieChart = defineAsyncComponent(() =>
  import('@/components/charts/AlarmPieChart.vue')
)

const RuntimeBarChart = defineAsyncComponent(() =>
  import('@/components/charts/RuntimeBarChart.vue')
)

// 时间范围
const dateRange = ref<[Dayjs, Dayjs]>([
  dayjs().subtract(7, 'day'),
  dayjs()
])

// 分区列表
const zones = ref<Zone[]>([])
const selectedZoneId = ref<number | undefined>(undefined)

// 当前报表类型
const activeTab = ref('energy')

// 数据
const energyData = ref<EnergyStats[]>([])
const trendData = ref<TrendData[]>([])
const alarmData = ref<AlarmStats[]>([])
const runtimeData = ref<RuntimeStats[]>([])

// 加载状态 - 全局
const loading = ref(false)

// 图表独立加载状态 - 用于骨架屏显示
const chartLoadingStates = ref({
  energy: false,
  trend: false,
  alarm: false,
  runtime: false
})

// 图表加载错误状态
const chartErrors = ref<Record<string, string>>({})

// 汇总数据
const totalEnergy = computed(() => {
  return energyData.value.reduce((sum, item) => sum + item.total_energy, 0)
})

const totalAlarms = ref(0)
const avgRuntimeHours = ref(0)

// 告警分组方式
const alarmGroupBy = ref<'type' | 'severity' | 'device'>('type')

// 格式化日期参数
const formatParams = () => {
  return {
    start_time: dateRange.value[0].toISOString(),
    end_time: dateRange.value[1].toISOString(),
    zone_id: selectedZoneId.value
  }
}

// 加载分区列表
const loadZones = async () => {
  try {
    zones.value = await zoneApi.list()
  } catch {
    message.error('加载分区失败')
  }
}

// 加载能耗数据
const loadEnergyData = async () => {
  chartLoadingStates.value.energy = true
  delete chartErrors.value.energy

  try {
    const response = await reportApi.getEnergyStats(formatParams())
    energyData.value = response.data
  } catch {
    chartErrors.value.energy = '加载能耗数据失败'
    message.error(chartErrors.value.energy)
  } finally {
    chartLoadingStates.value.energy = false
  }
}

// 加载趋势数据
const loadTrendData = async () => {
  chartLoadingStates.value.trend = true
  delete chartErrors.value.trend

  try {
    const response = await reportApi.getTrendData(formatParams())
    trendData.value = response.data
  } catch {
    chartErrors.value.trend = '加载趋势数据失败'
    message.error(chartErrors.value.trend)
  } finally {
    chartLoadingStates.value.trend = false
  }
}

// 加载告警数据
const loadAlarmData = async () => {
  chartLoadingStates.value.alarm = true
  delete chartErrors.value.alarm

  try {
    const response = await reportApi.getAlarmStats({
      ...formatParams(),
      group_by: alarmGroupBy.value
    })
    alarmData.value = response.data
    totalAlarms.value = response.total_alarms
  } catch {
    chartErrors.value.alarm = '加载告警数据失败'
    message.error(chartErrors.value.alarm)
  } finally {
    chartLoadingStates.value.alarm = false
  }
}

// 加载运行时长数据
const loadRuntimeData = async () => {
  chartLoadingStates.value.runtime = true
  delete chartErrors.value.runtime

  try {
    const response = await reportApi.getRuntimeStats(formatParams())
    runtimeData.value = response.data
    avgRuntimeHours.value = response.avg_runtime_hours
  } catch {
    chartErrors.value.runtime = '加载运行时长数据失败'
    message.error(chartErrors.value.runtime)
  } finally {
    chartLoadingStates.value.runtime = false
  }
}

// 刷新数据
const refreshData = async () => {
  loading.value = true
  switch (activeTab.value) {
    case 'energy':
      await loadEnergyData()
      break
    case 'trend':
      await loadTrendData()
      break
    case 'alarm':
      await loadAlarmData()
      break
    case 'runtime':
      await loadRuntimeData()
      break
  }
  loading.value = false
}

// 导出报表
const exportReport = async () => {
  const reportType = activeTab.value
  const timestamp = dayjs().format('YYYYMMDD_HHmmss')

  try {
    reportApi.downloadReport({
      report_type: reportType,
      ...formatParams()
    }, `${reportType}_report_${timestamp}.csv`)
    message.success('导出成功')
  } catch {
    message.error('导出失败')
  }
}


// Tab 切换
const onTabChange = (key: string) => {
  activeTab.value = key
  refreshData()
}

// 时间范围变化
const onDateRangeChange = () => {
  refreshData()
}

// 分区变化
const onZoneChange = () => {
  refreshData()
}

// 告警分组方式变化
const onAlarmGroupByChange = () => {
  loadAlarmData()
}

// 图表加载状态
const isChartLoading = (chart: 'energy' | 'trend' | 'alarm' | 'runtime') => {
  return chartLoadingStates.value[chart]
}

// 初始化
onMounted(() => {
  loadZones()
  refreshData()
})
</script>

<template>
  <div class="reports-page">
    <!-- 页面标题 -->
    <div class="page-header">
      <h2>报表分析</h2>
    </div>

    <!-- 查询条件 -->
    <div class="query-panel">
      <a-space size="large">
        <!-- 时间范围 -->
        <a-range-picker
          v-model:value="dateRange"
          :placeholder="['开始时间', '结束时间']"
          @change="onDateRangeChange"
        />

        <!-- 分区筛选 -->
        <a-select
          v-model:value="selectedZoneId"
          placeholder="选择分区"
          allow-clear
          style="width: 200px"
          @change="onZoneChange"
        >
          <a-select-option
            v-for="zone in zones"
            :key="zone.id"
            :value="zone.id"
          >
            {{ zone.name }}
          </a-select-option>
        </a-select>

        <!-- 导出按钮 -->
        <a-button
          type="primary"
          @click="exportReport"
        >
          导出 CSV
        </a-button>
      </a-space>
    </div>

    <!-- 报表内容 -->
    <a-tabs
      v-model:active-key="activeTab"
      @change="onTabChange"
    >
      <!-- 能耗统计 -->
      <a-tab-pane
        key="energy"
        tab="能耗统计"
      >
        <a-spin :spinning="loading">
          <!-- 汇总卡片 -->
          <div class="summary-cards">
            <a-card>
              <a-statistic
                title="总能耗"
                :value="totalEnergy"
                suffix="kWh"
              />
            </a-card>
          </div>

          <!-- 能耗图表 - 懒加载 -->
          <div class="chart-section">
            <Suspense>
              <template #default>
                <EnergyChart
                  :data="energyData"
                  :loading="isChartLoading('energy')"
                  :auto-resize="true"
                  :show-export="true"
                />
              </template>
              <template #fallback>
                <div class="chart-skeleton">
                  <a-skeleton
                    active
                    :paragraph="{ rows: 6 }"
                  />
                </div>
              </template>
            </Suspense>
          </div>

          <!-- 数据表格 -->
          <a-table
            :data-source="energyData"
            :columns="[
              { title: '设备ID', dataIndex: 'device_id', key: 'device_id' },
              { title: '设备名称', dataIndex: 'device_name', key: 'device_name' },
              { title: '总能耗(kWh)', dataIndex: 'total_energy', key: 'total_energy' },
              { title: '平均功率(W)', dataIndex: 'avg_power', key: 'avg_power' },
              { title: '最大功率(W)', dataIndex: 'max_power', key: 'max_power' },
              { title: '运行时长(h)', dataIndex: 'runtime_hours', key: 'runtime_hours' }
            ]"
            :row-key="(record: EnergyStats) => record.device_id"
            :pagination="{ pageSize: 10 }"
          />
        </a-spin>
      </a-tab-pane>

      <!-- 温湿度趋势 -->
      <a-tab-pane
        key="trend"
        tab="温湿度趋势"
      >
        <a-spin :spinning="loading">
          <div
            v-for="device in trendData"
            :key="device.device_id"
            class="trend-section"
          >
            <Suspense>
              <template #default>
                <TrendChart
                  :data="device"
                  :loading="isChartLoading('trend')"
                  :auto-resize="true"
                  :show-export="true"
                />
              </template>
              <template #fallback>
                <div class="chart-skeleton">
                  <a-skeleton
                    active
                    :paragraph="{ rows: 6 }"
                  />
                </div>
              </template>
            </Suspense>
          </div>
          <a-empty
            v-if="trendData.length === 0 && !loading"
            description="暂无数据"
          />
        </a-spin>
      </a-tab-pane>

      <!-- 告警统计 -->
      <a-tab-pane
        key="alarm"
        tab="告警统计"
      >
        <a-spin :spinning="loading">
          <!-- 汇总卡片 -->
          <div class="summary-cards">
            <a-card>
              <a-statistic
                title="总告警数"
                :value="totalAlarms"
              />
            </a-card>
          </div>

          <!-- 分组方式选择 -->
          <div class="filter-bar">
            <a-radio-group
              v-model:value="alarmGroupBy"
              @change="onAlarmGroupByChange"
            >
              <a-radio-button value="type">
                按类型
              </a-radio-button>
              <a-radio-button value="severity">
                按严重程度
              </a-radio-button>
            </a-radio-group>
          </div>

          <!-- 告警饼图 - 懒加载 -->
          <div class="chart-section">
            <Suspense>
              <template #default>
                <AlarmPieChart
                  :data="alarmData"
                  :loading="isChartLoading('alarm')"
                  :auto-resize="true"
                  :show-export="true"
                  :group-by="alarmGroupBy"
                />
              </template>
              <template #fallback>
                <div class="chart-skeleton">
                  <a-skeleton
                    active
                    :paragraph="{ rows: 6 }"
                  />
                </div>
              </template>
            </Suspense>
          </div>

          <!-- 数据表格 -->
          <a-table
            :data-source="alarmData"
            :columns="[
              { title: '告警类型', dataIndex: 'type', key: 'type' },
              { title: '严重程度', dataIndex: 'severity', key: 'severity' },
              { title: '数量', dataIndex: 'count', key: 'count' },
              { title: '已解决', dataIndex: 'resolved_count', key: 'resolved_count' },
              { title: '未解决', dataIndex: 'unresolved_count', key: 'unresolved_count' }
            ]"
            :row-key="(record: AlarmStats) => record.type || record.severity || 'unknown'"
            :pagination="{ pageSize: 10 }"
          />
        </a-spin>
      </a-tab-pane>

      <!-- 运行时长 -->
      <a-tab-pane
        key="runtime"
        tab="运行时长"
      >
        <a-spin :spinning="loading">
          <!-- 汇总卡片 -->
          <div class="summary-cards">
            <a-card>
              <a-statistic
                title="平均运行时长"
                :value="avgRuntimeHours"
                suffix="小时"
              />
            </a-card>
          </div>

          <!-- 运行时长图表 - 懒加载 -->
          <div class="chart-section">
            <Suspense>
              <template #default>
                <RuntimeBarChart
                  :data="runtimeData"
                  :loading="isChartLoading('runtime')"
                  :auto-resize="true"
                  :show-export="true"
                  :sort-by-runtime="true"
                  :max-items="10"
                />
              </template>
              <template #fallback>
                <div class="chart-skeleton">
                  <a-skeleton
                    active
                    :paragraph="{ rows: 6 }"
                  />
                </div>
              </template>
            </Suspense>
          </div>

          <!-- 数据表格 -->
          <a-table
            :data-source="runtimeData"
            :columns="[
              { title: '设备ID', dataIndex: 'device_id', key: 'device_id' },
              { title: '设备名称', dataIndex: 'device_name', key: 'device_name' },
              { title: '分区', dataIndex: 'zone_name', key: 'zone_name' },
              { title: '运行时长(h)', dataIndex: 'total_runtime_hours', key: 'total_runtime_hours' },
              { title: '开机占比(%)', dataIndex: 'on_time_percentage', key: 'on_time_percentage' },
              { title: '开机次数', dataIndex: 'on_count', key: 'on_count' },
              { title: '关机次数', dataIndex: 'off_count', key: 'off_count' }
            ]"
            :row-key="(record: RuntimeStats) => record.device_id"
            :pagination="{ pageSize: 10 }"
          />
        </a-spin>
      </a-tab-pane>
    </a-tabs>
  </div>
</template>

<style scoped>
.reports-page {
  padding: 24px;
}

.page-header {
  margin-bottom: 24px;
}

.page-header h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
}

.query-panel {
  margin-bottom: 24px;
  padding: 16px;
  background: #fff;
  border-radius: 4px;
}

.summary-cards {
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
}

.summary-cards .ant-card {
  width: 200px;
}

.filter-bar {
  margin-bottom: 16px;
}

.chart-section {
  margin-bottom: 24px;
  padding: 16px;
  background: #fff;
  border-radius: 4px;
}

.trend-section {
  margin-bottom: 24px;
  padding: 16px;
  background: #fff;
  border-radius: 4px;
}

.chart-skeleton {
  min-height: 300px;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>