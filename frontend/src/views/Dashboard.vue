<template>
  <div class="dashboard">
    <!-- 页面头部 -->
    <div class="page-header-section">
      <div class="header-content">
        <h1 class="page-title">
          控制中心
        </h1>
        <p class="page-subtitle">
          实时监控与系统概览
        </p>
      </div>
      <div class="header-actions">
        <div class="last-update">
          <span class="update-label">最后更新</span>
          <span class="update-time">{{ lastUpdateTime }}</span>
        </div>
        <a-button
          type="primary"
          class="refresh-btn"
          :loading="loading"
          @click="refreshData"
        >
          <template #icon>
            <ReloadOutlined />
          </template>
          刷新数据
        </a-button>
      </div>
    </div>

    <!-- 统计卡片区域 -->
    <div class="stats-grid">
      <!-- 设备总数 -->
      <div class="stat-card cool fade-in stagger-1">
        <div class="stat-icon">
          <DesktopOutlined />
        </div>
        <div class="stat-content">
          <span class="stat-label">设备总数</span>
          <div class="stat-value-container">
            <span class="stat-value data-value-lg">{{ stats?.total_devices ?? 0 }}</span>
            <span class="stat-unit">台</span>
          </div>
        </div>
        <div class="stat-gauge">
          <svg
            viewBox="0 0 100 100"
            class="gauge-svg"
          >
            <circle
              cx="50"
              cy="50"
              r="40"
              class="gauge-bg"
            />
            <circle
              cx="50"
              cy="50"
              r="40"
              class="gauge-fill"
              :style="totalDevicesStyle"
            />
          </svg>
        </div>
      </div>

      <!-- 在线设备 -->
      <div class="stat-card normal fade-in stagger-2">
        <div class="stat-icon online">
          <CheckCircleOutlined />
        </div>
        <div class="stat-content">
          <span class="stat-label">在线设备</span>
          <div class="stat-value-container">
            <span class="stat-value data-value-lg">{{ stats?.online_devices ?? 0 }}</span>
            <span class="stat-unit">台</span>
          </div>
          <span class="stat-change up">+{{ onlineRate }}%</span>
        </div>
        <div class="stat-progress">
          <div
            class="progress-bar"
            :style="{ width: onlineRate + '%' }"
          />
        </div>
      </div>

      <!-- 离线设备 -->
      <div class="stat-card warning fade-in stagger-3">
        <div class="stat-icon warning">
          <CloseCircleOutlined />
        </div>
        <div class="stat-content">
          <span class="stat-label">离线设备</span>
          <div class="stat-value-container">
            <span class="stat-value data-value-lg">{{ stats?.offline_devices ?? 0 }}</span>
            <span class="stat-unit">台</span>
          </div>
        </div>
      </div>

      <!-- 告警数量 -->
      <div class="stat-card danger fade-in stagger-4">
        <div class="stat-icon danger">
          <WarningOutlined />
        </div>
        <div class="stat-content">
          <span class="stat-label">未处理告警</span>
          <div class="stat-value-container">
            <span class="stat-value data-value-lg">{{ stats?.unresolved_alarms ?? 0 }}</span>
            <span class="stat-unit">条</span>
          </div>
        </div>
        <div
          v-if="stats?.unresolved_alarms && stats.unresolved_alarms > 0"
          class="stat-badge"
        >
          <span class="badge-pulse" />
          <span>需要处理</span>
        </div>
      </div>
    </div>

    <!-- 主内容区域 -->
    <div class="main-content-grid">
      <!-- 左侧：设备状态面板 -->
      <div class="panel devices-panel fade-in">
        <div class="panel-header">
          <h3 class="panel-title">
            <span class="title-icon"><AppstoreOutlined /></span>
            设备状态
          </h3>
          <a-button
            type="link"
            class="view-all-btn"
            @click="goToDevices"
          >
            查看全部 <RightOutlined />
          </a-button>
        </div>
        <div class="panel-content">
          <div class="device-status-grid">
            <div class="status-block">
              <div class="status-ring online">
                <span class="ring-value">{{ stats?.online_devices ?? 0 }}</span>
              </div>
              <span class="status-label">在线</span>
            </div>
            <div class="status-block">
              <div class="status-ring offline">
                <span class="ring-value">{{ stats?.offline_devices ?? 0 }}</span>
              </div>
              <span class="status-label">离线</span>
            </div>
            <div class="status-block">
              <div class="status-ring online-rate">
                <span class="ring-value">{{ onlineRate }}%</span>
              </div>
              <span class="status-label">在线率</span>
            </div>
          </div>

          <!-- 快速操作 -->
          <div class="quick-actions">
            <a-button
              class="action-btn"
              @click="goToDevices"
            >
              <ControlOutlined />
              设备管理
            </a-button>
            <a-button
              class="action-btn"
              @click="goToZones"
            >
              <ApartmentOutlined />
              分区管理
            </a-button>
          </div>
        </div>
      </div>

      <!-- 右侧：告警面板 -->
      <div class="panel alarms-panel fade-in">
        <div class="panel-header">
          <h3 class="panel-title">
            <span class="title-icon"><AlertOutlined /></span>
            最新告警
          </h3>
          <a-button
            type="link"
            class="view-all-btn"
            @click="goToAlarms"
          >
            查看全部 <RightOutlined />
          </a-button>
        </div>
        <div class="panel-content">
          <div
            v-if="recentAlarms.length === 0"
            class="empty-state"
          >
            <CheckCircleOutlined class="empty-icon" />
            <span>暂无告警</span>
          </div>
          <div
            v-else
            class="alarms-list"
          >
            <div
              v-for="alarm in recentAlarms"
              :key="alarm.id"
              class="alert-item"
              :class="alarm.severity"
            >
              <div class="alert-icon">
                <WarningOutlined v-if="alarm.severity === 'high'" />
                <InfoCircleOutlined v-else />
              </div>
              <div class="alert-content">
                <span class="alert-title">{{ alarm.message || '设备告警' }}</span>
                <div class="alert-meta">
                  <span class="device-id">{{ alarm.device_id }}</span>
                  <span class="alert-time">{{ formatTime(alarm.occurred_at) }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 系统信息栏 -->
    <div class="system-bar fade-in">
      <div class="bar-item">
        <span class="bar-label">系统版本</span>
        <span class="bar-value data-value">v1.0.0</span>
      </div>
      <div class="bar-divider" />
      <div class="bar-item">
        <span class="bar-label">MQTT状态</span>
        <span class="bar-value status-dot online">已连接</span>
      </div>
      <div class="bar-divider" />
      <div class="bar-item">
        <span class="bar-label">数据库状态</span>
        <span class="bar-value status-dot online">正常</span>
      </div>
      <div class="bar-divider" />
      <div class="bar-item">
        <span class="bar-label">告警处理率</span>
        <span class="bar-value data-value">{{ alarmResolveRate }}%</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useDeviceStore } from '@/stores/devices'
import {
  DesktopOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  WarningOutlined,
  ReloadOutlined,
  AppstoreOutlined,
  ControlOutlined,
  ApartmentOutlined,
  AlertOutlined,
  RightOutlined,
  InfoCircleOutlined
} from '@ant-design/icons-vue'

interface Alarm {
  id: number
  device_id: string
  severity: string
  message?: string
  occurred_at: string
}

const router = useRouter()
const deviceStore = useDeviceStore()

const stats = computed(() => deviceStore.stats)
const loading = computed(() => deviceStore.loading)
const lastUpdateTime = ref(formatTime(new Date().toISOString()))

// 模拟告警数据（实际应从 API 获取）
const recentAlarms = ref<Alarm[]>([])

// 在线率
const onlineRate = computed(() => {
  if (!stats.value || stats.value.total_devices === 0) return 0
  return Math.round((stats.value.online_devices / stats.value.total_devices) * 100)
})

// 告警处理率
const alarmResolveRate = computed(() => {
  if (!stats.value || stats.value.total_alarms === 0) return 100
  return Math.round(((stats.value.total_alarms - stats.value.unresolved_alarms) / stats.value.total_alarms) * 100)
})

// 设备总数仪表盘样式
const totalDevicesStyle = computed(() => {
  const maxDevices = 100
  const percentage = stats.value ? Math.min(stats.value.total_devices / maxDevices, 1) : 0
  const circumference = 2 * Math.PI * 40
  const offset = circumference * (1 - percentage)
  return {
    strokeDasharray: `${circumference}`,
    strokeDashoffset: `${offset}`,
    stroke: 'var(--color-cool-primary)'
  }
})

// 格式化时间
function formatTime(time: string) {
  const date = new Date(time)
  return date.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 刷新数据
async function refreshData() {
  await deviceStore.fetchStats()
  lastUpdateTime.value = formatTime(new Date().toISOString())
}

// 导航
function goToDevices() {
  router.push({ name: 'Devices' })
}

function goToZones() {
  router.push({ name: 'Zones' })
}

function goToAlarms() {
  router.push({ name: 'Alarms' })
}

// 页面加载时获取数据
onMounted(() => {
  deviceStore.fetchStats()
})
</script>

<style scoped>
.dashboard {
  display: flex;
  flex-direction: column;
  gap: var(--space-6);
}

/* 页面头部 */
.page-header-section {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: var(--space-6);
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
  font-size: 28px;
  font-weight: 600;
  margin: 0;
  color: var(--color-text-primary);
}

.page-subtitle {
  font-size: 14px;
  color: var(--color-text-secondary);
  margin: 0;
}

.header-actions {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: var(--space-3);
}

.last-update {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 2px;
}

.update-label {
  font-size: 11px;
  color: var(--color-text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.1em;
}

.update-time {
  font-family: var(--font-mono);
  font-size: 13px;
  color: var(--color-text-secondary);
}

.refresh-btn {
  background: var(--color-cool-primary) !important;
  border-color: var(--color-cool-primary) !important;
}

.refresh-btn:hover {
  box-shadow: 0 0 20px var(--color-cool-glow);
}

/* 统计卡片网格 */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--space-4);
}

.stat-card {
  position: relative;
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border-primary);
  border-radius: var(--radius-lg);
  padding: var(--space-5);
  overflow: hidden;
  transition: all var(--transition-base);
}

.stat-card:hover {
  border-color: var(--color-border-focus);
  box-shadow: var(--shadow-glow-cool);
}

.stat-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 4px;
  height: 100%;
}

.stat-card.cool::before { background: var(--color-cool-primary); }
.stat-card.normal::before { background: var(--color-status-normal); }
.stat-card.warning::before { background: var(--color-status-warning); }
.stat-card.danger::before { background: var(--color-status-danger); }

.stat-icon {
  position: absolute;
  top: var(--space-4);
  right: var(--space-4);
  font-size: 32px;
  opacity: 0.2;
  color: var(--color-text-tertiary);
}

.stat-icon.online { color: var(--color-status-normal); opacity: 0.3; }
.stat-icon.warning { color: var(--color-status-warning); opacity: 0.3; }
.stat-icon.danger { color: var(--color-status-danger); opacity: 0.3; }

.stat-content {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.stat-label {
  font-size: 12px;
  color: var(--color-text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.1em;
}

.stat-value-container {
  display: flex;
  align-items: baseline;
  gap: var(--space-1);
}

.stat-value {
  color: var(--color-text-primary);
}

.stat-unit {
  font-size: 14px;
  color: var(--color-text-tertiary);
}

.stat-change {
  font-size: 12px;
  font-family: var(--font-mono);
}

.stat-change.up { color: var(--color-status-normal); }
.stat-change.down { color: var(--color-status-danger); }

.stat-progress {
  margin-top: var(--space-3);
  height: 4px;
  background: var(--color-bg-tertiary);
  border-radius: 2px;
  overflow: hidden;
}

.progress-bar {
  height: 100%;
  background: var(--color-status-normal);
  border-radius: 2px;
  transition: width 0.5s ease;
}

.stat-badge {
  position: absolute;
  bottom: var(--space-3);
  right: var(--space-3);
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  background: rgba(255, 59, 59, 0.15);
  border-radius: var(--radius-md);
  font-size: 11px;
  color: var(--color-status-danger);
}

.badge-pulse {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--color-status-danger);
  animation: pulse 1.5s ease-in-out infinite;
}

.stat-gauge {
  position: absolute;
  top: var(--space-3);
  right: var(--space-3);
  width: 60px;
  height: 60px;
}

.gauge-svg {
  transform: rotate(-90deg);
}

.gauge-bg {
  fill: none;
  stroke: var(--color-bg-tertiary);
  stroke-width: 8;
}

.gauge-fill {
  fill: none;
  stroke-width: 8;
  stroke-linecap: round;
  transition: stroke-dashoffset 1s ease;
}

/* 主内容区域 */
.main-content-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-4);
}

.panel {
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border-primary);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-4) var(--space-5);
  border-bottom: 1px solid var(--color-border-primary);
  background: var(--color-bg-tertiary);
}

.panel-title {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: 16px;
  font-weight: 600;
  margin: 0;
  color: var(--color-text-primary);
}

.title-icon {
  color: var(--color-cool-primary);
}

.view-all-btn {
  font-size: 13px;
  color: var(--color-text-secondary) !important;
}

.view-all-btn:hover {
  color: var(--color-cool-primary) !important;
}

.panel-content {
  padding: var(--space-5);
}

/* 设备状态网格 */
.device-status-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-4);
  margin-bottom: var(--space-5);
}

.status-block {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-2);
}

.status-ring {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 4px solid;
  position: relative;
}

.status-ring.online {
  border-color: var(--color-status-normal);
  background: rgba(0, 255, 136, 0.1);
}

.status-ring.offline {
  border-color: var(--color-status-warning);
  background: rgba(255, 193, 7, 0.1);
}

.status-ring.online-rate {
  border-color: var(--color-cool-primary);
  background: var(--color-cool-glow);
}

.ring-value {
  font-family: var(--font-mono);
  font-size: 20px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.status-label {
  font-size: 12px;
  color: var(--color-text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

/* 快速操作 */
.quick-actions {
  display: flex;
  gap: var(--space-3);
}

.action-btn {
  flex: 1;
  height: 44px;
  background: var(--color-bg-tertiary) !important;
  border-color: var(--color-border-primary) !important;
  color: var(--color-text-primary) !important;
}

.action-btn:hover {
  background: var(--color-bg-hover) !important;
  border-color: var(--color-cool-primary) !important;
}

/* 告警列表 */
.alarms-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.alert-item {
  display: flex;
  align-items: flex-start;
  gap: var(--space-3);
  padding: var(--space-3);
  background: var(--color-bg-tertiary);
  border-radius: var(--radius-md);
  border-left: 3px solid;
  transition: background var(--transition-fast);
}

.alert-item:hover {
  background: var(--color-bg-hover);
}

.alert-item.high { border-left-color: var(--color-status-danger); }
.alert-item.medium { border-left-color: var(--color-status-warning); }
.alert-item.low { border-left-color: var(--color-status-normal); }

.alert-icon {
  color: var(--color-status-warning);
  font-size: 16px;
  margin-top: 2px;
}

.alert-content {
  flex: 1;
  min-width: 0;
}

.alert-title {
  font-size: 14px;
  color: var(--color-text-primary);
  display: block;
}

.alert-meta {
  display: flex;
  gap: var(--space-2);
  margin-top: 4px;
  font-size: 12px;
  font-family: var(--font-mono);
  color: var(--color-text-tertiary);
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--space-8);
  color: var(--color-text-tertiary);
}

.empty-icon {
  font-size: 32px;
  color: var(--color-status-normal);
  margin-bottom: var(--space-2);
}

/* 系统信息栏 */
.system-bar {
  display: flex;
  align-items: center;
  padding: var(--space-3) var(--space-5);
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border-primary);
  border-radius: var(--radius-lg);
}

.bar-item {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.bar-label {
  font-size: 12px;
  color: var(--color-text-tertiary);
}

.bar-value {
  font-size: 13px;
  color: var(--color-text-primary);
}

.bar-divider {
  width: 1px;
  height: 24px;
  background: var(--color-border-primary);
  margin: 0 var(--space-4);
}

/* 动画 */
@keyframes pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.5; transform: scale(1.1); }
}

/* 响应式 */
@media (max-width: 1200px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .main-content-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }

  .page-header-section {
    flex-direction: column;
    gap: var(--space-4);
  }

  .header-actions {
    align-items: flex-start;
  }

  .device-status-grid {
    grid-template-columns: 1fr;
  }

  .system-bar {
    flex-wrap: wrap;
    gap: var(--space-2);
  }

  .bar-divider {
    display: none;
  }
}
</style>