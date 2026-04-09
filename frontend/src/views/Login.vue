<template>
  <div class="login-container">
    <!-- 背景网格效果 -->
    <div class="grid-bg"></div>

    <!-- 扫描线效果 -->
    <div class="scanline"></div>

    <!-- 登录卡片 -->
    <div class="login-wrapper">
      <div class="login-card">
        <!-- Logo 区域 -->
        <div class="login-header">
          <div class="logo-container">
            <div class="logo-icon">
              <svg viewBox="0 0 48 48" fill="none">
                <circle cx="24" cy="24" r="20" stroke="currentColor" stroke-width="2" opacity="0.3"/>
                <circle cx="24" cy="24" r="14" stroke="currentColor" stroke-width="2"/>
                <path d="M24 12v12l8 6" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                <circle cx="24" cy="24" r="4" fill="currentColor"/>
              </svg>
            </div>
            <div class="logo-text">
              <span class="brand">BNIoT</span>
              <span class="subtitle">工业物联网控制中心</span>
            </div>
          </div>
        </div>

        <!-- 系统状态指示 -->
        <div class="system-indicator">
          <span class="indicator-dot"></span>
          <span class="indicator-text">系统在线</span>
        </div>

        <!-- 登录表单 -->
        <a-form
          :model="formState"
          :rules="rules"
          @finish="handleLogin"
          layout="vertical"
          class="login-form"
        >
          <a-form-item name="username" class="form-item">
            <label class="input-label">
              <span class="label-icon">
                <UserOutlined />
              </span>
              <span>用户名</span>
            </label>
            <a-input
              v-model:value="formState.username"
              placeholder="请输入用户名"
              size="large"
              class="input-field"
            />
          </a-form-item>

          <a-form-item name="password" class="form-item">
            <label class="input-label">
              <span class="label-icon">
                <LockOutlined />
              </span>
              <span>密码</span>
            </label>
            <a-input-password
              v-model:value="formState.password"
              placeholder="请输入密码"
              size="large"
              class="input-field"
            />
          </a-form-item>

          <a-form-item class="form-item">
            <a-button
              type="primary"
              html-type="submit"
              size="large"
              block
              :loading="loading"
              class="login-btn"
            >
              <span v-if="!loading">登录系统</span>
              <span v-else>验证中...</span>
            </a-button>
          </a-form-item>
        </a-form>

        <!-- 错误提示 -->
        <transition name="fade">
          <div v-if="error" class="error-message">
            <span class="error-icon">
              <ExclamationCircleOutlined />
            </span>
            <span>{{ error }}</span>
          </div>
        </transition>

        <!-- 底部信息 -->
        <div class="login-footer">
          <div class="footer-line"></div>
          <span class="footer-text">空调节能管理系统 v1.0.0</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { UserOutlined, LockOutlined, ExclamationCircleOutlined } from '@ant-design/icons-vue'
import type { Rule } from 'ant-design-vue/es/form'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const formState = reactive({
  username: '',
  password: ''
})

const loading = computed(() => authStore.loading)
const error = computed(() => authStore.error)

// 表单验证规则
const rules: Record<string, Rule[]> = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' }
  ]
}

// 处理登录
async function handleLogin() {
  const success = await authStore.login({
    username: formState.username,
    password: formState.password
  })

  if (success) {
    const redirect = route.query.redirect as string
    router.push(redirect || { name: 'Dashboard' })
  }
}
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-bg-primary);
  position: relative;
  overflow: hidden;
}

/* 网格背景 */
.grid-bg {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(0, 212, 255, 0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(0, 212, 255, 0.03) 1px, transparent 1px);
  background-size: 40px 40px;
  pointer-events: none;
}

/* 扫描线效果 */
.scanline {
  position: absolute;
  inset: 0;
  background: repeating-linear-gradient(
    0deg,
    transparent,
    transparent 2px,
    rgba(0, 212, 255, 0.02) 2px,
    rgba(0, 212, 255, 0.02) 4px
  );
  pointer-events: none;
}

.login-wrapper {
  position: relative;
  z-index: 1;
}

.login-card {
  width: 420px;
  padding: 48px 40px;
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border-primary);
  border-radius: var(--radius-xl);
  box-shadow:
    0 0 60px rgba(0, 212, 255, 0.1),
    var(--shadow-lg);
  position: relative;
}

/* 顶部发光线 */
.login-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 40px;
  right: 40px;
  height: 2px;
  background: linear-gradient(90deg, transparent, var(--color-cool-primary), transparent);
}

/* Logo 区域 */
.login-header {
  text-align: center;
  margin-bottom: 32px;
}

.logo-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.logo-icon {
  width: 64px;
  height: 64px;
  color: var(--color-cool-primary);
  filter: drop-shadow(0 0 20px var(--color-cool-glow));
}

.logo-icon svg {
  width: 100%;
  height: 100%;
}

.logo-text {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.brand {
  font-family: var(--font-mono);
  font-size: 28px;
  font-weight: 700;
  color: var(--color-text-primary);
  letter-spacing: 0.15em;
}

.subtitle {
  font-size: 12px;
  color: var(--color-text-tertiary);
  letter-spacing: 0.1em;
  text-transform: uppercase;
}

/* 系统状态指示 */
.system-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin-bottom: 32px;
  padding: 8px 16px;
  background: var(--color-bg-tertiary);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border-secondary);
}

.indicator-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--color-status-normal);
  box-shadow: 0 0 8px var(--color-status-normal);
  animation: pulse 2s ease-in-out infinite;
}

.indicator-text {
  font-size: 12px;
  font-family: var(--font-mono);
  color: var(--color-status-normal);
  letter-spacing: 0.05em;
}

/* 表单样式 */
.login-form {
  margin-bottom: 16px;
}

.form-item {
  margin-bottom: 20px;
}

.input-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: var(--color-text-secondary);
  margin-bottom: 8px;
  text-transform: uppercase;
  letter-spacing: 0.1em;
}

.label-icon {
  color: var(--color-cool-primary);
}

.input-field {
  background: var(--color-bg-tertiary) !important;
  border-color: var(--color-border-primary) !important;
}

.input-field:focus,
.input-field:hover {
  border-color: var(--color-cool-primary) !important;
  box-shadow: 0 0 0 2px var(--color-cool-glow) !important;
}

/* 登录按钮 */
.login-btn {
  height: 48px;
  font-size: 16px;
  font-weight: 600;
  letter-spacing: 0.1em;
  background: var(--color-cool-primary) !important;
  border-color: var(--color-cool-primary) !important;
  transition: all var(--transition-base);
}

.login-btn:hover {
  background: var(--color-cool-secondary) !important;
  box-shadow: 0 0 30px var(--color-cool-glow);
}

.login-btn:active {
  transform: scale(0.98);
}

/* 错误消息 */
.error-message {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: rgba(255, 59, 59, 0.1);
  border: 1px solid var(--color-status-danger);
  border-radius: var(--radius-md);
  color: var(--color-status-danger);
  font-size: 14px;
}

.error-icon {
  font-size: 16px;
}

/* 底部 */
.login-footer {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  margin-top: 24px;
}

.footer-line {
  width: 60px;
  height: 1px;
  background: var(--color-border-primary);
}

.footer-text {
  font-size: 11px;
  font-family: var(--font-mono);
  color: var(--color-text-tertiary);
  letter-spacing: 0.05em;
}

/* 动画 */
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.fade-enter-active,
.fade-leave-active {
  transition: all 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

/* 响应式 */
@media (max-width: 480px) {
  .login-card {
    width: 100%;
    margin: 16px;
    padding: 32px 24px;
  }
}
</style>