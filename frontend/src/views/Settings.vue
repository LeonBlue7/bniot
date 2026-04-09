<template>
  <div class="settings-page">
    <!-- 页面头部 -->
    <div class="page-header-section">
      <div class="header-content">
        <h1 class="page-title">系统设置</h1>
        <p class="page-subtitle">配置系统参数与偏好</p>
      </div>
    </div>

    <!-- 设置内容 -->
    <div class="settings-content">
      <!-- 外观设置 -->
      <div class="settings-section">
        <h3 class="section-title">外观设置</h3>
        <div class="settings-card">
          <div class="setting-item">
            <div class="setting-info">
              <span class="setting-label">主题模式</span>
              <span class="setting-desc">选择深色或浅色主题</span>
            </div>
            <a-radio-group v-model:value="settings.theme" @change="saveSettings">
              <a-radio value="dark">深色</a-radio>
              <a-radio value="light">浅色</a-radio>
            </a-radio-group>
          </div>
          <div class="setting-item">
            <div class="setting-info">
              <span class="setting-label">显示动画效果</span>
              <span class="setting-desc">开启界面过渡动画</span>
            </div>
            <a-switch v-model:checked="settings.animations" @change="saveSettings" />
          </div>
        </div>
      </div>

      <!-- 通知设置 -->
      <div class="settings-section">
        <h3 class="section-title">通知设置</h3>
        <div class="settings-card">
          <div class="setting-item">
            <div class="setting-info">
              <span class="setting-label">设备离线告警</span>
              <span class="setting-desc">设备离线时发送通知</span>
            </div>
            <a-switch v-model:checked="settings.notifyOffline" @change="saveSettings" />
          </div>
          <div class="setting-item">
            <div class="setting-info">
              <span class="setting-label">温度告警</span>
              <span class="setting-desc">温度超出阈值时通知</span>
            </div>
            <a-switch v-model:checked="settings.notifyTempAlarm" @change="saveSettings" />
          </div>
          <div class="setting-item">
            <div class="setting-info">
              <span class="setting-label">声音提醒</span>
              <span class="setting-desc">告警时播放提示音</span>
            </div>
            <a-switch v-model:checked="settings.soundEnabled" @change="saveSettings" />
          </div>
        </div>
      </div>

      <!-- 数据刷新 -->
      <div class="settings-section">
        <h3 class="section-title">数据刷新</h3>
        <div class="settings-card">
          <div class="setting-item">
            <div class="setting-info">
              <span class="setting-label">自动刷新间隔</span>
              <span class="setting-desc">仪表盘数据自动刷新频率</span>
            </div>
            <a-select v-model:value="settings.refreshInterval" style="width: 120px" @change="saveSettings">
              <a-select-option :value="0">关闭</a-select-option>
              <a-select-option :value="30">30秒</a-select-option>
              <a-select-option :value="60">1分钟</a-select-option>
              <a-select-option :value="300">5分钟</a-select-option>
            </a-select>
          </div>
        </div>
      </div>

      <!-- 系统信息 -->
      <div class="settings-section">
        <h3 class="section-title">系统信息</h3>
        <div class="settings-card">
          <div class="info-grid">
            <div class="info-item">
              <span class="info-label">系统版本</span>
              <span class="info-value data-value">v1.0.0</span>
            </div>
            <div class="info-item">
              <span class="info-label">前端框架</span>
              <span class="info-value">Vue 3.5</span>
            </div>
            <div class="info-item">
              <span class="info-label">UI 组件</span>
              <span class="info-value">Ant Design Vue 4.x</span>
            </div>
            <div class="info-item">
              <span class="info-label">构建工具</span>
              <span class="info-value">Vite 6.x</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, onMounted } from 'vue'
import { message } from 'ant-design-vue'

interface Settings {
  theme: 'dark' | 'light'
  animations: boolean
  notifyOffline: boolean
  notifyTempAlarm: boolean
  soundEnabled: boolean
  refreshInterval: number
}

const settings = reactive<Settings>({
  theme: 'dark',
  animations: true,
  notifyOffline: true,
  notifyTempAlarm: true,
  soundEnabled: false,
  refreshInterval: 60
})

// 加载设置
function loadSettings() {
  const saved = localStorage.getItem('bniot_settings')
  if (saved) {
    try {
      const parsed = JSON.parse(saved)
      Object.assign(settings, parsed)
    } catch {
      // localStorage 数据损坏时使用默认设置
    }
  }
}

// 保存设置
function saveSettings() {
  localStorage.setItem('bniot_settings', JSON.stringify(settings))
  message.success('设置已保存')
}

onMounted(() => {
  loadSettings()
})
</script>

<style scoped>
.settings-page {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  max-width: 800px;
}

.page-header-section {
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

.settings-content {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.settings-section {
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border-primary);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.section-title {
  margin: 0;
  padding: var(--space-4) var(--space-5);
  font-size: 16px;
  font-weight: 600;
  background: var(--color-bg-tertiary);
  border-bottom: 1px solid var(--color-border-primary);
}

.settings-card {
  padding: var(--space-4);
}

.setting-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-3) 0;
  border-bottom: 1px solid var(--color-border-secondary);
}

.setting-item:last-child {
  border-bottom: none;
}

.setting-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.setting-label {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-primary);
}

.setting-desc {
  font-size: 12px;
  color: var(--color-text-tertiary);
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--space-4);
  padding: var(--space-4);
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.info-label {
  font-size: 12px;
  color: var(--color-text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.info-value {
  font-size: 14px;
  color: var(--color-text-primary);
}

/* Ant Design 样式覆盖 */
:deep(.ant-radio-wrapper) {
  color: var(--color-text-primary) !important;
}

:deep(.ant-select-selector) {
  background: var(--color-bg-tertiary) !important;
  border-color: var(--color-border-primary) !important;
}
</style>