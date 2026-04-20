<template>
  <a-layout class="main-layout">
    <!-- 侧边栏 -->
    <a-layout-sider
      v-model:collapsed="collapsed"
      :trigger="null"
      collapsible
      :width="240"
      :collapsed-width="64"
      class="sidebar"
    >
      <!-- Logo 区域 -->
      <div class="sidebar-logo">
        <div class="logo-icon">
          <svg
            viewBox="0 0 32 32"
            fill="none"
          >
            <circle
              cx="16"
              cy="16"
              r="14"
              stroke="currentColor"
              stroke-width="2"
              opacity="0.3"
            />
            <circle
              cx="16"
              cy="16"
              r="10"
              stroke="currentColor"
              stroke-width="2"
            />
            <path
              d="M16 8v8l5 4"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
            />
            <circle
              cx="16"
              cy="16"
              r="3"
              fill="currentColor"
            />
          </svg>
        </div>
        <span
          v-show="!collapsed"
          class="logo-text"
        >BNIoT</span>
      </div>

      <!-- 导航菜单 -->
      <a-menu
        v-model:selected-keys="selectedKeys"
        mode="inline"
        :items="menuItems"
        class="sidebar-menu"
        @click="handleMenuClick"
      />

      <!-- 底部折叠按钮 -->
      <div class="sidebar-footer">
        <a-button
          type="text"
          class="collapse-btn"
          @click="collapsed = !collapsed"
        >
          <MenuFoldOutlined v-if="!collapsed" />
          <MenuUnfoldOutlined v-else />
        </a-button>
      </div>
    </a-layout-sider>

    <!-- 主内容区 -->
    <a-layout class="main-content">
      <!-- 顶部栏 -->
      <a-layout-header class="header">
        <div class="header-left">
          <h1 class="page-title-header">
            {{ pageTitle }}
          </h1>
        </div>

        <div class="header-right">
          <!-- 实时状态指示 -->
          <div class="system-status">
            <span class="status-label">系统</span>
            <span class="status-indicator online">
              <span class="pulse" />
              正常
            </span>
          </div>

          <!-- 用户信息 -->
          <a-dropdown>
            <div class="user-info">
              <a-avatar :style="{ backgroundColor: '#00d4ff', color: '#0a0e14' }">
                {{ userInitial }}
              </a-avatar>
              <span class="user-name">{{ user?.username }}</span>
              <DownOutlined class="dropdown-icon" />
            </div>
            <template #overlay>
              <a-menu class="user-menu">
                <a-menu-item
                  key="profile"
                  @click="handleProfile"
                >
                  <UserOutlined /> 个人中心
                </a-menu-item>
                <a-menu-divider />
                <a-menu-item
                  key="logout"
                  @click="handleLogout"
                >
                  <LogoutOutlined /> 退出登录
                </a-menu-item>
              </a-menu>
            </template>
          </a-dropdown>
        </div>
      </a-layout-header>

      <!-- 内容区域 -->
      <a-layout-content class="content">
        <router-view v-slot="{ Component }">
          <transition
            name="fade"
            mode="out-in"
          >
            <component :is="Component" />
          </transition>
        </router-view>
      </a-layout-content>
    </a-layout>
  </a-layout>
</template>

<script setup lang="ts">
import { ref, computed, watch, h } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { useAuthStore } from '@/stores/auth'
import {
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  UserOutlined,
  LogoutOutlined,
  DownOutlined,
  DashboardOutlined,
  DesktopOutlined,
  PartitionOutlined,
  TeamOutlined,
  AlertOutlined,
  SettingOutlined,
  BarChartOutlined
} from '@ant-design/icons-vue'
import type { MenuProps } from 'ant-design-vue'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const collapsed = ref(false)
const selectedKeys = ref<string[]>([])

const user = computed(() => authStore.user)
const userInitial = computed(() => user.value?.username?.charAt(0).toUpperCase() || 'U')

// 菜单项 - key 必须与路由 name 一致（PascalCase）
// 只有管理员才能看到：用户管理、分区管理
const menuItems = computed<MenuProps['items']>(() => {
  const items: MenuProps['items'] = [
    {
      key: 'Dashboard',
      icon: () => h(DashboardOutlined),
      label: '仪表盘',
      title: '仪表盘'
    },
    {
      key: 'Devices',
      icon: () => h(DesktopOutlined),
      label: '设备管理',
      title: '设备管理'
    },
    // 分区管理：只有管理员才能增删改，所以只有管理员显示此菜单
    ...(authStore.isAdmin ? [{
      key: 'Zones',
      icon: () => h(PartitionOutlined),
      label: '分区管理',
      title: '分区管理'
    }] : []),
    {
      key: 'Alarms',
      icon: () => h(AlertOutlined),
      label: '告警中心',
      title: '告警中心'
    },
    {
      key: 'Reports',
      icon: () => h(BarChartOutlined),
      label: '报表分析',
      title: '报表分析'
    },
    {
      key: 'Settings',
      icon: () => h(SettingOutlined),
      label: '系统设置',
      title: '系统设置'
    }
  ]

  // 管理员才能看到用户管理
  if (authStore.isAdmin) {
    items.splice(5, 0, {
      key: 'Users',
      icon: () => h(TeamOutlined),
      label: '用户管理',
      title: '用户管理'
    })
  }

  return items
})

// 页面标题
const pageTitle = computed(() => {
  const titles: Record<string, string> = {
    Dashboard: '控制中心',
    Devices: '设备管理',
    Zones: '分区管理',
    Alarms: '告警中心',
    Reports: '报表分析',
    Users: '用户管理',
    Settings: '系统设置'
  }
  return titles[route.name as string] || '控制中心'
})

// 监听路由变化更新选中菜单
watch(
  () => route.name,
  (name) => {
    if (name) {
      selectedKeys.value = [name as string]
    }
  },
  { immediate: true }
)

// 处理菜单点击 - 直接导航
function handleMenuClick(e: { key: string }) {
  if (e.key && route.name !== e.key) {
    router.push({ name: e.key })
  }
}

// 退出登录
function handleLogout() {
  authStore.logout()
  router.push({ name: 'Login' })
}

// 个人中心
function handleProfile() {
  router.push({ name: 'Profile' })
}
</script>

<style scoped>
.main-layout {
  min-height: 100vh;
  background: var(--color-bg-primary);
}

/* 侧边栏样式 */
.sidebar {
  background: var(--color-bg-secondary) !important;
  border-right: 1px solid var(--color-border-primary);
  position: relative;
}

.sidebar-logo {
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  border-bottom: 1px solid var(--color-border-primary);
  padding: 0 16px;
}

.logo-icon {
  width: 28px;
  height: 28px;
  color: var(--color-cool-primary);
  flex-shrink: 0;
  filter: drop-shadow(0 0 8px var(--color-cool-glow));
}

.logo-text {
  font-family: var(--font-mono);
  font-size: 18px;
  font-weight: 700;
  color: var(--color-text-primary);
  letter-spacing: 0.15em;
}

.sidebar-menu {
  border: none !important;
  background: transparent !important;
  padding: 8px 0;
}

/* 折叠状态下隐藏菜单文字 */
.sidebar.ant-layout-sider-collapsed .sidebar-menu {
  width: 64px;
}

.sidebar.ant-layout-sider-collapsed :deep(.ant-menu-item) {
  padding: 0 calc(50% - 16px / 2) !important;
}

.sidebar.ant-layout-sider-collapsed :deep(.ant-menu-item span:not(.anticon)) {
  display: none !important;
}

.sidebar.ant-layout-sider-collapsed :deep(.ant-menu-submenu-title span:not(.anticon)) {
  display: none !important;
}

.sidebar.ant-layout-sider-collapsed :deep(.ant-menu-item .anticon) {
  margin: 0 !important;
}

:deep(.ant-menu-item) {
  margin: 4px 8px !important;
  border-radius: var(--radius-md) !important;
  height: 40px !important;
  line-height: 40px !important;
  color: var(--color-text-secondary) !important;
  transition: all var(--transition-fast) !important;
}

:deep(.ant-menu-item:hover) {
  background: var(--color-bg-hover) !important;
  color: var(--color-text-primary) !important;
}

:deep(.ant-menu-item-selected) {
  background: var(--color-cool-glow) !important;
  color: var(--color-cool-primary) !important;
}

:deep(.ant-menu-item-selected::after) {
  display: none !important;
}

:deep(.ant-menu-item .anticon) {
  font-size: 16px !important;
}

.sidebar-footer {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 12px;
  border-top: 1px solid var(--color-border-primary);
}

.collapse-btn {
  width: 100%;
  color: var(--color-text-secondary) !important;
}

.collapse-btn:hover {
  background: var(--color-bg-hover) !important;
  color: var(--color-text-primary) !important;
}

/* 主内容区 */
.main-content {
  background: var(--color-bg-primary);
}

/* 顶部栏 */
.header {
  height: 64px;
  padding: 0 24px;
  background: var(--color-bg-secondary);
  border-bottom: 1px solid var(--color-border-primary);
  display: flex;
  align-items: center;
  justify-content: space-between;
  overflow: hidden; /* 防止内容溢出 */
  box-sizing: border-box; /* 边框计入尺寸 */
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.page-title-header {
  font-size: 20px;
  font-weight: 600;
  margin: 0;
  color: var(--color-text-primary);
}

.header-right {
  display: flex;
  align-items: center;
  gap: 24px;
}

.system-status {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 14px;
  background: var(--color-bg-tertiary);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border-primary);
}

.status-label {
  font-size: 11px;
  color: var(--color-text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.1em;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-family: var(--font-mono);
}

.status-indicator.online {
  color: var(--color-status-normal);
}

.pulse {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: currentColor;
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.user-info {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: var(--radius-md);
  transition: background var(--transition-fast);
}

.user-info:hover {
  background: var(--color-bg-hover);
}

.user-name {
  font-size: 14px;
  color: var(--color-text-primary);
}

.dropdown-icon {
  font-size: 10px;
  color: var(--color-text-tertiary);
}

.user-menu {
  background: var(--color-bg-secondary) !important;
  border: 1px solid var(--color-border-primary) !important;
}

:deep(.user-menu .ant-menu-item) {
  color: var(--color-text-primary) !important;
}

:deep(.user-menu .ant-menu-item:hover) {
  background: var(--color-bg-hover) !important;
}

/* 内容区域 */
.content {
  padding: 24px;
  min-height: calc(100vh - 64px);
  overflow: auto;
}

/* 过渡动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* 响应式 */
@media (max-width: 768px) {
  .header-right {
    gap: 12px;
  }

  .system-status {
    display: none;
  }

  .user-name {
    display: none;
  }

  .dropdown-icon {
    display: none;
  }
}
</style>