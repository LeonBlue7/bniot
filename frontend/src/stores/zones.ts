/**
 * 分区状态管理
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { zoneApi } from '@/api'
import type { Zone, ZoneCreate, ZoneUpdate } from '@/types'

export const useZoneStore = defineStore('zone', () => {
  // 状态
  const zones = ref<Zone[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  // 计算属性 - 构建树形结构
  const zoneTree = computed(() => {
    const buildTree = (parentId: number | null = null): Zone[] => {
      return zones.value
        .filter(z => z.parent_id === parentId)
        .sort((a, b) => a.sort_order - b.sort_order)
        .map(z => ({
          ...z,
          children: buildTree(z.id)
        }))
    }
    return buildTree(null)
  })

  // 获取分区列表
  async function fetchZones(): Promise<void> {
    loading.value = true
    error.value = null
    try {
      zones.value = await zoneApi.list()
    } catch (err) {
      error.value = err instanceof Error ? err.message : '获取分区列表失败'
    } finally {
      loading.value = false
    }
  }

  // 创建分区
  async function createZone(data: ZoneCreate): Promise<Zone | null> {
    loading.value = true
    error.value = null
    try {
      const zone = await zoneApi.create(data)
      zones.value.push(zone)
      return zone
    } catch (err) {
      error.value = err instanceof Error ? err.message : '创建分区失败'
      return null
    } finally {
      loading.value = false
    }
  }

  // 更新分区
  async function updateZone(id: number, data: ZoneUpdate): Promise<Zone | null> {
    loading.value = true
    error.value = null
    try {
      const zone = await zoneApi.update(id, data)
      const index = zones.value.findIndex(z => z.id === id)
      if (index !== -1) {
        zones.value[index] = zone
      }
      return zone
    } catch (err) {
      error.value = err instanceof Error ? err.message : '更新分区失败'
      return null
    } finally {
      loading.value = false
    }
  }

  // 删除分区
  async function deleteZone(id: number): Promise<boolean> {
    loading.value = true
    error.value = null
    try {
      await zoneApi.delete(id)
      zones.value = zones.value.filter(z => z.id !== id)
      return true
    } catch (err) {
      error.value = err instanceof Error ? err.message : '删除分区失败'
      return false
    } finally {
      loading.value = false
    }
  }

  return {
    // 状态
    zones,
    loading,
    error,
    // 计算属性
    zoneTree,
    // 方法
    fetchZones,
    createZone,
    updateZone,
    deleteZone
  }
})