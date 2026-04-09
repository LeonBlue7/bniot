/**
 * Zones API 测试
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import MockAdapter from 'axios-mock-adapter'
import apiClient from './client'
import { zoneApi } from './zones'
import type { Zone, ZoneCreate, ZoneUpdate, Message } from '@/types'

// Mock auth store
vi.mock('@/stores/auth', () => ({
  useAuthStore: vi.fn(() => ({
    token: 'test-token',
    logout: vi.fn()
  }))
}))

describe('Zones API', () => {
  let mockAxios: MockAdapter

  // Mock 数据
  const mockZone: Zone = {
    id: 1,
    tenant_id: 1,
    name: '一楼',
    parent_id: null,
    description: '一楼办公区',
    sort_order: 1,
    created_at: '2024-01-01T00:00:00Z'
  }

  const mockZones: Zone[] = [
    mockZone,
    {
      id: 2,
      tenant_id: 1,
      name: '二楼',
      parent_id: null,
      description: '二楼办公区',
      sort_order: 2,
      created_at: '2024-01-01T00:00:00Z'
    },
    {
      id: 3,
      tenant_id: 1,
      name: '101室',
      parent_id: 1,
      description: '一楼101会议室',
      sort_order: 1,
      created_at: '2024-01-01T00:00:00Z'
    },
    {
      id: 4,
      tenant_id: 1,
      name: '102室',
      parent_id: 1,
      description: '一楼102办公室',
      sort_order: 2,
      created_at: '2024-01-01T00:00:00Z'
    }
  ]

  beforeEach(() => {
    setActivePinia(createPinia())
    mockAxios = new MockAdapter(apiClient)
    vi.clearAllMocks()
  })

  afterEach(() => {
    mockAxios.restore()
  })

  describe('list', () => {
    it('应返回分区列表', async () => {
      mockAxios.onGet('/zones').reply(200, mockZones)

      const result = await zoneApi.list()

      expect(result).toEqual(mockZones)
      expect(result.length).toBe(4)
    })

    it('空列表应返回空数组', async () => {
      mockAxios.onGet('/zones').reply(200, [])

      const result = await zoneApi.list()

      expect(result).toEqual([])
    })

    it('服务器错误应抛出异常', async () => {
      mockAxios.onGet('/zones').reply(500)

      await expect(zoneApi.list()).rejects.toThrow()
    })

    it('网络错误应抛出异常', async () => {
      mockAxios.onGet('/zones').networkError()

      await expect(zoneApi.list()).rejects.toThrow()
    })

    it('未认证应抛出 401 错误', async () => {
      mockAxios.onGet('/zones').reply(401)

      await expect(zoneApi.list()).rejects.toThrow()
    })
  })

  describe('create', () => {
    it('应成功创建根分区', async () => {
      const createData: ZoneCreate = {
        name: '三楼',
        tenant_id: 1
      }
      const newZone: Zone = {
        id: 5,
        tenant_id: 1,
        name: '三楼',
        parent_id: null,
        description: null,
        sort_order: 3,
        created_at: '2024-01-02T00:00:00Z'
      }

      mockAxios.onPost('/zones').reply(201, newZone)

      const result = await zoneApi.create(createData)

      expect(result).toEqual(newZone)
      expect(result.parent_id).toBeNull()
    })

    it('应成功创建子分区', async () => {
      const createData: ZoneCreate = {
        name: '103室',
        parent_id: 1,
        tenant_id: 1
      }
      const newZone: Zone = {
        id: 5,
        tenant_id: 1,
        name: '103室',
        parent_id: 1,
        description: null,
        sort_order: 0,
        created_at: '2024-01-02T00:00:00Z'
      }

      mockAxios.onPost('/zones').reply(201, newZone)

      const result = await zoneApi.create(createData)

      expect(result.parent_id).toBe(1)
    })

    it('创建带描述的分区', async () => {
      const createData: ZoneCreate = {
        name: '新分区',
        description: '这是新分区描述',
        tenant_id: 1
      }
      const newZone: Zone = {
        id: 5,
        tenant_id: 1,
        name: '新分区',
        parent_id: null,
        description: '这是新分区描述',
        sort_order: 0,
        created_at: '2024-01-02T00:00:00Z'
      }

      mockAxios.onPost('/zones').reply(201, newZone)

      const result = await zoneApi.create(createData)

      expect(result.description).toBe('这是新分区描述')
    })

    it('创建带排序的分区', async () => {
      const createData: ZoneCreate = {
        name: '新分区',
        sort_order: 5,
        tenant_id: 1
      }
      const newZone: Zone = {
        id: 5,
        tenant_id: 1,
        name: '新分区',
        parent_id: null,
        description: null,
        sort_order: 5,
        created_at: '2024-01-02T00:00:00Z'
      }

      mockAxios.onPost('/zones').reply(201, newZone)

      const result = await zoneApi.create(createData)

      expect(result.sort_order).toBe(5)
    })

    it('分区名称已存在应抛出错误', async () => {
      mockAxios.onPost('/zones').reply(400, { detail: 'Zone name already exists' })

      await expect(zoneApi.create({
        name: '一楼',
        tenant_id: 1
      })).rejects.toThrow()
    })

    it('父分区不存在应抛出错误', async () => {
      mockAxios.onPost('/zones').reply(404, { detail: 'Parent zone not found' })

      await expect(zoneApi.create({
        name: '子分区',
        parent_id: 999,
        tenant_id: 1
      })).rejects.toThrow()
    })

    it('验证失败应抛出错误', async () => {
      mockAxios.onPost('/zones').reply(422, { detail: 'Validation error' })

      await expect(zoneApi.create({
        name: '',
        tenant_id: 1
      })).rejects.toThrow()
    })

    it('名称包含特殊字符应正确处理', async () => {
      const createData: ZoneCreate = {
        name: '分区-A/B',
        tenant_id: 1
      }
      const newZone: Zone = {
        id: 5,
        ...createData,
        parent_id: null,
        description: null,
        sort_order: 0,
        created_at: '2024-01-02T00:00:00Z'
      }

      mockAxios.onPost('/zones').reply(201, newZone)

      const result = await zoneApi.create(createData)

      expect(result.name).toBe('分区-A/B')
    })

    it('名称包含 Unicode 字符应正确处理', async () => {
      const createData: ZoneCreate = {
        name: '会议室 🏢',
        tenant_id: 1
      }
      const newZone: Zone = {
        id: 5,
        ...createData,
        parent_id: null,
        description: null,
        sort_order: 0,
        created_at: '2024-01-02T00:00:00Z'
      }

      mockAxios.onPost('/zones').reply(201, newZone)

      const result = await zoneApi.create(createData)

      expect(result.name).toBe('会议室 🏢')
    })
  })

  describe('update', () => {
    it('应成功更新分区名称', async () => {
      const updateData: ZoneUpdate = { name: '更新后的分区' }
      const updatedZone: Zone = { ...mockZone, name: '更新后的分区' }

      mockAxios.onPut('/zones/1').reply(200, updatedZone)

      const result = await zoneApi.update(1, updateData)

      expect(result.name).toBe('更新后的分区')
    })

    it('应成功更新分区描述', async () => {
      const updateData: ZoneUpdate = { description: '新描述' }
      const updatedZone: Zone = { ...mockZone, description: '新描述' }

      mockAxios.onPut('/zones/1').reply(200, updatedZone)

      const result = await zoneApi.update(1, updateData)

      expect(result.description).toBe('新描述')
    })

    it('应成功更新分区排序', async () => {
      const updateData: ZoneUpdate = { sort_order: 10 }
      const updatedZone: Zone = { ...mockZone, sort_order: 10 }

      mockAxios.onPut('/zones/1').reply(200, updatedZone)

      const result = await zoneApi.update(1, updateData)

      expect(result.sort_order).toBe(10)
    })

    it('应成功移动分区到新父分区', async () => {
      const updateData: ZoneUpdate = { parent_id: 2 }
      const updatedZone: Zone = { ...mockZone, parent_id: 2 }

      mockAxios.onPut('/zones/1').reply(200, updatedZone)

      const result = await zoneApi.update(1, updateData)

      expect(result.parent_id).toBe(2)
    })

    it('应成功将分区设为根分区', async () => {
      const updateData: ZoneUpdate = { parent_id: null }
      const childZone: Zone = { ...mockZones[2], parent_id: null }

      mockAxios.onPut('/zones/3').reply(200, childZone)

      const result = await zoneApi.update(3, updateData)

      expect(result.parent_id).toBeNull()
    })

    it('应成功更新多个字段', async () => {
      const updateData: ZoneUpdate = {
        name: '新名称',
        description: '新描述',
        sort_order: 5
      }
      const updatedZone: Zone = { ...mockZone, ...updateData }

      mockAxios.onPut('/zones/1').reply(200, updatedZone)

      const result = await zoneApi.update(1, updateData)

      expect(result.name).toBe('新名称')
      expect(result.description).toBe('新描述')
      expect(result.sort_order).toBe(5)
    })

    it('分区不存在应抛出错误', async () => {
      mockAxios.onPut('/zones/999').reply(404, { detail: 'Zone not found' })

      await expect(zoneApi.update(999, { name: 'test' })).rejects.toThrow()
    })

    it('移动到非存在的父分区应抛出错误', async () => {
      mockAxios.onPut('/zones/1').reply(404, { detail: 'Parent zone not found' })

      await expect(zoneApi.update(1, { parent_id: 999 })).rejects.toThrow()
    })

    it('空更新数据应成功', async () => {
      mockAxios.onPut('/zones/1').reply(200, mockZone)

      const result = await zoneApi.update(1, {})

      expect(result).toEqual(mockZone)
    })

    it('不能将分区设为自己的子分区', async () => {
      mockAxios.onPut('/zones/1').reply(400, { detail: 'Cannot set parent to self' })

      await expect(zoneApi.update(1, { parent_id: 1 })).rejects.toThrow()
    })
  })

  describe('delete', () => {
    it('应成功删除分区', async () => {
      mockAxios.onDelete('/zones/1').reply(200, { message: 'Zone deleted' })

      const result = await zoneApi.delete(1)

      expect(result.message).toBe('Zone deleted')
    })

    it('分区不存在应抛出错误', async () => {
      mockAxios.onDelete('/zones/999').reply(404, { detail: 'Zone not found' })

      await expect(zoneApi.delete(999)).rejects.toThrow()
    })

    it('分区有子分区时应抛出错误', async () => {
      mockAxios.onDelete('/zones/1').reply(400, { detail: 'Zone has child zones' })

      await expect(zoneApi.delete(1)).rejects.toThrow()
    })

    it('分区有设备时应抛出错误', async () => {
      mockAxios.onDelete('/zones/1').reply(400, { detail: 'Zone has devices' })

      await expect(zoneApi.delete(1)).rejects.toThrow()
    })

    it('无权限应抛出错误', async () => {
      mockAxios.onDelete('/zones/1').reply(403, { detail: 'Forbidden' })

      await expect(zoneApi.delete(1)).rejects.toThrow()
    })

    it('删除叶子分区应成功', async () => {
      // 叶子分区（无子分区）
      mockAxios.onDelete('/zones/4').reply(200, { message: 'Zone deleted' })

      const result = await zoneApi.delete(4)

      expect(result.message).toBe('Zone deleted')
    })
  })
})