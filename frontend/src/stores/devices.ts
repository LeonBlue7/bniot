/**
 * 设备状态管理
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { deviceApi } from '@/api'
import type { Device, DeviceCreate, DeviceUpdate, DashboardStats, DeviceData } from '@/types'

export const useDeviceStore = defineStore('device', () => {
  // 状态
  const devices = ref<Device[]>([])
  const currentDevice = ref<Device | null>(null)
  const deviceData = ref<DeviceData[]>([])
  const stats = ref<DashboardStats | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  // 计算属性
  const onlineDevices = computed(() =>
    devices.value.filter(d => d.is_online)
  )
  const offlineDevices = computed(() =>
    devices.value.filter(d => !d.is_online)
  )

  // 获取仪表盘统计
  async function fetchStats(): Promise<void> {
    loading.value = true
    error.value = null
    try {
      stats.value = await deviceApi.getStats()
    } catch (err) {
      error.value = err instanceof Error ? err.message : '获取统计失败'
    } finally {
      loading.value = false
    }
  }

  // 获取设备列表
  async function fetchDevices(params?: {
    zone_id?: number
    is_online?: boolean
    keyword?: string
    skip?: number
    limit?: number
  }): Promise<void> {
    loading.value = true
    error.value = null
    try {
      devices.value = await deviceApi.list(params)
    } catch (err) {
      error.value = err instanceof Error ? err.message : '获取设备列表失败'
    } finally {
      loading.value = false
    }
  }

  // 获取设备详情
  async function fetchDevice(id: number): Promise<void> {
    loading.value = true
    error.value = null
    try {
      currentDevice.value = await deviceApi.get(id)
    } catch (err) {
      error.value = err instanceof Error ? err.message : '获取设备详情失败'
    } finally {
      loading.value = false
    }
  }

  // 创建设备
  async function createDevice(data: DeviceCreate): Promise<Device | null> {
    loading.value = true
    error.value = null
    try {
      const device = await deviceApi.create(data)
      devices.value.unshift(device)
      return device
    } catch (err) {
      error.value = err instanceof Error ? err.message : '创建设备失败'
      return null
    } finally {
      loading.value = false
    }
  }

  // 更新设备
  async function updateDevice(id: number, data: DeviceUpdate): Promise<Device | null> {
    loading.value = true
    error.value = null
    try {
      const device = await deviceApi.update(id, data)
      const index = devices.value.findIndex(d => d.id === id)
      if (index !== -1) {
        devices.value[index] = device
      }
      if (currentDevice.value?.id === id) {
        currentDevice.value = device
      }
      return device
    } catch (err) {
      error.value = err instanceof Error ? err.message : '更新设备失败'
      return null
    } finally {
      loading.value = false
    }
  }

  // 删除设备
  async function deleteDevice(id: number): Promise<boolean> {
    loading.value = true
    error.value = null
    try {
      await deviceApi.delete(id)
      devices.value = devices.value.filter(d => d.id !== id)
      if (currentDevice.value?.id === id) {
        currentDevice.value = null
      }
      return true
    } catch (err) {
      error.value = err instanceof Error ? err.message : '删除设备失败'
      return false
    } finally {
      loading.value = false
    }
  }

  // 远程控制设备
  async function controlDevice(id: number, airstate: number): Promise<boolean> {
    loading.value = true
    error.value = null
    try {
      await deviceApi.control(id, airstate)
      return true
    } catch (err) {
      error.value = err instanceof Error ? err.message : '控制设备失败'
      return false
    } finally {
      loading.value = false
    }
  }

  // 获取设备历史数据
  async function fetchDeviceData(id: number, hours: number = 24): Promise<void> {
    loading.value = true
    error.value = null
    try {
      deviceData.value = await deviceApi.getData(id, { hours })
    } catch (err) {
      error.value = err instanceof Error ? err.message : '获取设备数据失败'
    } finally {
      loading.value = false
    }
  }

  // 清除当前设备
  function clearCurrentDevice(): void {
    currentDevice.value = null
    deviceData.value = []
  }

  return {
    // 状态
    devices,
    currentDevice,
    deviceData,
    stats,
    loading,
    error,
    // 计算属性
    onlineDevices,
    offlineDevices,
    // 方法
    fetchStats,
    fetchDevices,
    fetchDevice,
    createDevice,
    updateDevice,
    deleteDevice,
    controlDevice,
    fetchDeviceData,
    clearCurrentDevice
  }
})