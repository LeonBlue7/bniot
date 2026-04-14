<template>
  <a-config-provider
    :theme="themeConfig"
    :locale="zhCN"
  >
    <router-view />
  </a-config-provider>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import zhCN from 'ant-design-vue/es/locale/zh_CN'

// 深色主题配置
const themeConfig = computed(() => ({
  token: {
    // 输入框颜色 - 深色背景 + 浅色文字
    colorBgContainer: '#1a222d',
    colorText: '#e8edf3',
    colorTextPlaceholder: '#64748b',
    colorBorder: '#2a3644',
    colorPrimary: '#00d4ff',
    // 下拉框
    colorBgElevated: '#212b38',
    // 按钮文字
    colorPrimaryText: '#0a0e14',
    colorPrimaryTextHover: '#0a0e14',
    colorPrimaryTextActive: '#0a0e14',
  },
  components: {
    Input: {
      colorBgContainer: '#1a222d',
      colorText: '#e8edf3',
      colorTextPlaceholder: '#64748b',
      colorBorder: '#2a3644',
      colorBgContainerDisabled: '#1a222d',
    },
    InputNumber: {
      colorBgContainer: '#1a222d',
      colorText: '#e8edf3',
      colorTextPlaceholder: '#64748b',
      colorBorder: '#2a3644',
    },
    Select: {
      colorBgContainer: '#1a222d',
      colorText: '#e8edf3',
      colorTextPlaceholder: '#64748b',
      colorBorder: '#2a3644',
      colorBgElevated: '#212b38',
      optionSelectedBg: 'rgba(0, 212, 255, 0.15)',
      optionSelectedColor: '#00d4ff',
    },
    DatePicker: {
      colorBgContainer: '#1a222d',
      colorText: '#e8edf3',
      colorTextPlaceholder: '#64748b',
      colorBorder: '#2a3644',
      colorBgElevated: '#212b38',
    },
    Table: {
      colorBgContainer: '#111820',
      headerBg: '#1a222d',
      headerColor: '#94a3b8',
      rowHoverBg: '#2a3644',
      colorText: '#e8edf3',
      borderColor: '#2a3644',
    },
    Card: {
      colorBgContainer: '#111820',
      colorText: '#e8edf3',
      colorBorderSecondary: '#2a3644',
    },
    Modal: {
      colorBgElevated: '#111820',
      colorText: '#e8edf3',
      contentBg: '#111820',
      headerBg: '#111820',
    },
    Menu: {
      colorItemText: '#94a3b8',
      colorItemTextHover: '#e8edf3',
      colorItemTextSelected: '#00d4ff',
      colorItemBgSelected: 'rgba(0, 212, 255, 0.15)',
      colorItemBgHover: '#2a3644',
      colorBgContainer: '#111820',
    },
    Button: {
      primaryColor: '#0a0e14',
      colorBgContainer: '#1a222d',
      colorBorder: '#2a3644',
      colorText: '#e8edf3',
    },
    Radio: {
      colorBgContainer: '#1a222d',
      colorBorder: '#2a3644',
      buttonSolidCheckedBg: '#00d4ff',
      buttonSolidCheckedColor: '#0a0e14',
    },
    Switch: {
      colorBgContainer: '#64748b',
      colorPrimary: '#00d4ff',
    },
    Dropdown: {
      colorBgElevated: '#212b38',
      colorText: '#e8edf3',
      controlItemBgHover: '#2a3644',
    },
    Form: {
      labelColor: '#94a3b8',
      colorText: '#e8edf3',
    },
    Descriptions: {
      labelBg: '#1a222d',
      labelColor: '#94a3b8',
      contentColor: '#e8edf3',
    },
    Tabs: {
      itemColor: '#94a3b8',
      itemHoverColor: '#00d4ff',
      itemSelectedColor: '#00d4ff',
      inkBarColor: '#00d4ff',
    },
    Pagination: {
      colorBgContainer: '#1a222d',
      colorBorder: '#2a3644',
      colorText: '#e8edf3',
      itemActiveBg: '#00d4ff',
    },
    Tooltip: {
      colorBgElevated: '#212b38',
      colorText: '#e8edf3',
    },
    Popover: {
      colorBgElevated: '#212b38',
      colorText: '#e8edf3',
    },
    Tag: {
      colorText: '#e8edf3',
    },
    Badge: {
      colorText: '#e8edf3',
    },
    Message: {
      contentBg: '#111820',
      contentColor: '#e8edf3',
    },
    Spin: {
      colorText: '#94a3b8',
    },
    Empty: {
      colorText: '#64748b',
    },
  },
}))
</script>

<style>
#app {
  min-height: 100vh;
}
</style>