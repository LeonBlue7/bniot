/**
 * Zone Store 测试
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useZoneStore } from '@/stores/zones'
import type { Zone } from '@/types'

// Mock zone API
vi.mock('@/api/zones', () => ({
  zoneApi: {
    list: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    delete: vi.fn()
  }
}))

import { zoneApi } from '@/api/zones'

// Mock 数据
const mockZones: Zone[] = [
  {
    id: 1,
    tenant_id: 1,
    name: '一楼',
    parent_id: null,
    description: '一楼区域',
    sort_order: 1,
    created_at: '2024-01-01'
  },
  {
    id: 2,
    tenant_id: 1,
    name: '办公室A',
    parent_id: 1,
    description: '一楼办公室A',
    sort_order: 1,
    created_at: '2024-01-01'
  },
  {
    id: 3,
    tenant_id: 1,
    name: '办公室B',
    parent_id: 1,
    description: '一楼办公室B',
    sort_order: 2,
    created_at: '2024-01-01'
  },
  {
    id: 4,
    tenant_id: 1,
    name: '二楼',
    parent_id: null,
    description: '二楼区域',
    sort_order: 2,
    created_at: '2024-01-01'
  }
]

describe('Zone Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  describe('初始状态', () => {
    it('应初始化 zones 为空数组', () => {
      const store = useZoneStore()
      expect(store.zones).toEqual([])
    })

    it('应初始化 loading 为 false', () => {
      const store = useZoneStore()
      expect(store.loading).toBe(false)
    })

    it('应初始化 error 为 null', () => {
      const store = useZoneStore()
      expect(store.error).toBeNull()
    })
  })

  describe('zoneTree 计算属性', () => {
    it('应正确构建树形结构', () => {
      const store = useZoneStore()
      store.zones = mockZones

      const tree = store.zoneTree

      // 根节点有两个：一楼和二楼
      expect(tree).toHaveLength(2)
      expect(tree[0].name).toBe('一楼')
      expect(tree[1].name).toBe('二楼')
    })

    it('应正确处理嵌套结构', () => {
      const store = useZoneStore()
      store.zones = mockZones

      const tree = store.zoneTree

      // 一楼下面有两个子分区
      const firstFloor = tree[0]
      expect(firstFloor.children).toHaveLength(2)
      expect(firstFloor.children?.[0].name).toBe('办公室A')
      expect(firstFloor.children?.[1].name).toBe('办公室B')
    })

    it('应按 sort_order 排序', () => {
      const store = useZoneStore()
      store.zones = [
        { ...mockZones[0], sort_order: 3 },
        { ...mockZones[3], sort_order: 1 }
      ]

      const tree = store.zoneTree

      // 应按 sort_order 排序
      expect(tree[0].name).toBe('二楼')
      expect(tree[1].name).toBe('一楼')
    })

    it('空数组应返回空树', () => {
      const store = useZoneStore()
      store.zones = []

      expect(store.zoneTree).toEqual([])
    })

    it('无父节点时应返回根级别', () => {
      const store = useZoneStore()
      store.zones = [mockZones[0], mockZones[3]]

      const tree = store.zoneTree

      expect(tree).toHaveLength(2)
      expect(tree[0].children).toEqual([])
      expect(tree[1].children).toEqual([])
    })
  })

  describe('fetchZones 方法', () => {
    it('成功获取分区列表', async () => {
      vi.mocked(zoneApi.list).mockResolvedValue(mockZones)

      const store = useZoneStore()
      await store.fetchZones()

      expect(store.zones).toEqual(mockZones)
      expect(store.loading).toBe(false)
    })

    it('获取失败应设置错误', async () => {
      vi.mocked(zoneApi.list).mockRejectedValue(new Error('获取失败'))

      const store = useZoneStore()
      await store.fetchZones()

      expect(store.error).toBe('获取失败')
    })

    it('获取失败（非 Error 对象）应使用默认错误信息', async () => {
      vi.mocked(zoneApi.list).mockRejectedValue('unknown')

      const store = useZoneStore()
      await store.fetchZones()

      expect(store.error).toBe('获取分区列表失败')
    })

    it('获取过程中应设置 loading', async () => {
      vi.mocked(zoneApi.list).mockImplementation(() =>
        new Promise(resolve => setTimeout(() => resolve(mockZones), 100))
      )

      const store = useZoneStore()
      const promise = store.fetchZones()

      expect(store.loading).toBe(true)

      await promise
      expect(store.loading).toBe(false)
    })
  })

  describe('createZone 方法', () => {
    it('成功创建分区', async () => {
      const newZone: Zone = {
        id: 5,
        tenant_id: 1,
        name: '三楼',
        parent_id: null,
        description: '三楼区域',
        sort_order: 3,
        created_at: '2024-01-01'
      }
      vi.mocked(zoneApi.create).mockResolvedValue(newZone)

      const store = useZoneStore()
      const result = await store.createZone({
        name: '三楼',
        tenant_id: 1
      })

      expect(result).toEqual(newZone)
      expect(store.zones).toContainEqual(newZone)
    })

    it('创建失败应返回 null', async () => {
      vi.mocked(zoneApi.create).mockRejectedValue(new Error('创建失败'))

      const store = useZoneStore()
      const result = await store.createZone({
        name: '三楼',
        tenant_id: 1
      })

      expect(result).toBeNull()
      expect(store.error).toBe('创建失败')
    })

    it('创建失败（非 Error 对象）应使用默认错误信息', async () => {
      vi.mocked(zoneApi.create).mockRejectedValue(null)

      const store = useZoneStore()
      const result = await store.createZone({
        name: '三楼',
        tenant_id: 1
      })

      expect(result).toBeNull()
      expect(store.error).toBe('创建分区失败')
    })
  })

  describe('updateZone 方法', () => {
    it('成功更新分区', async () => {
      const updatedZone = { ...mockZones[0], name: '一楼更新' }
      vi.mocked(zoneApi.update).mockResolvedValue(updatedZone)

      const store = useZoneStore()
      store.zones = mockZones
      const result = await store.updateZone(1, { name: '一楼更新' })

      expect(result).toEqual(updatedZone)
      expect(store.zones[0].name).toBe('一楼更新')
    })

    it('更新不存在的分区应失败', async () => {
      vi.mocked(zoneApi.update).mockRejectedValue(new Error('分区不存在'))

      const store = useZoneStore()
      store.zones = mockZones
      const result = await store.updateZone(999, { name: '不存在' })

      expect(result).toBeNull()
      expect(store.error).toBe('分区不存在')
    })

    it('更新失败（非 Error 对象）应使用默认错误信息', async () => {
      vi.mocked(zoneApi.update).mockRejectedValue('')

      const store = useZoneStore()
      store.zones = mockZones
      const result = await store.updateZone(1, { name: 'test' })

      expect(result).toBeNull()
      expect(store.error).toBe('更新分区失败')
    })
  })

  describe('deleteZone 方法', () => {
    it('成功删除分区', async () => {
      vi.mocked(zoneApi.delete).mockResolvedValue({ message: '分区已删除' })

      const store = useZoneStore()
      store.zones = mockZones
      const result = await store.deleteZone(1)

      expect(result).toBe(true)
      expect(store.zones).toHaveLength(3)
      expect(store.zones.find(z => z.id === 1)).toBeUndefined()
    })

    it('删除失败应返回 false', async () => {
      vi.mocked(zoneApi.delete).mockRejectedValue(new Error('删除失败'))

      const store = useZoneStore()
      store.zones = mockZones
      const result = await store.deleteZone(1)

      expect(result).toBe(false)
      expect(store.zones).toHaveLength(4)
      expect(store.error).toBe('删除失败')
    })

    it('删除失败（非 Error 对象）应使用默认错误信息', async () => {
      vi.mocked(zoneApi.delete).mockRejectedValue(0)

      const store = useZoneStore()
      store.zones = mockZones
      const result = await store.deleteZone(1)

      expect(result).toBe(false)
      expect(store.error).toBe('删除分区失败')
    })
  })
})