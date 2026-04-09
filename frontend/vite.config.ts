import { defineConfig } from 'vitest/config'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  build: {
    // 代码分割配置
    rollupOptions: {
      output: {
        // 手动分割 chunks
        manualChunks(id) {
          // Vue 核心生态
          if (id.includes('node_modules/vue/') ||
              id.includes('node_modules/vue-router/') ||
              id.includes('node_modules/pinia/')) {
            return 'vue-vendor'
          }
          // ECharts 单独分割（大文件）
          if (id.includes('node_modules/echarts/') ||
              id.includes('node_modules/zrender/')) {
            return 'echarts'
          }
          // Ant Design Vue 单独分割
          if (id.includes('node_modules/ant-design-vue/') ||
              id.includes('node_modules/@ant-design/')) {
            return 'antd'
          }
          // Dayjs 单独分割
          if (id.includes('node_modules/dayjs/')) {
            return 'dayjs'
          }
        }
      }
    },
    // 提高 chunk 大小警告阈值
    chunkSizeWarningLimit: 600,
    // 启用 CSS 代码分割
    cssCodeSplit: true,
    // 生产环境关闭源码映射
    sourcemap: false
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true
      }
    }
  },
  test: {
    globals: true,
    environment: 'happy-dom',
    setupFiles: ['./src/test/setup.ts'],
    include: ['src/**/*.{test,spec}.{js,mjs,cjs,ts,mts,cts,jsx,tsx}'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: [
        'node_modules/',
        'src/**/*.d.ts',
        'src/**/*.test.ts',
        'src/**/*.spec.ts',
        'src/main.ts',
        'src/test/**',
        'src/views/**/*.vue',  // Vue 组件由 E2E 测试覆盖
        'src/components/**/*.vue',
        'src/layouts/**/*.vue',
        'src/App.vue',
        'src/router/**',  // 路由配置
        'src/api/index.ts'  // 仅导出模块
      ],
      thresholds: {
        statements: 80,
        branches: 80,
        functions: 80,
        lines: 80
      }
    }
  }
})