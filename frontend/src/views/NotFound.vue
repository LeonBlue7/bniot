<template>
  <div class="not-found">
    <a-result
      status="404"
      title="404"
      sub-title="页面不存在"
    >
      <template #extra>
        <a-button
          type="primary"
          @click="goHome"
        >
          返回首页
        </a-button>
      </template>
    </a-result>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()

function goHome() {
  router.push({ name: 'Dashboard' })
}
</script>

<style scoped>
.not-found {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>