/**
 * TypeScript 类型定义测试
 */
import { describe, it, expect } from 'vitest'
import type {
  User,
  Device,
  Zone,
  Alarm,
  DashboardStats,
  Token,
  LoginRequest,
  DeviceCreate,
  DeviceUpdate,
  ZoneCreate,
  ZoneUpdate,
  AlarmType,
  AlarmSeverity
} from '@/types'

describe('类型定义', () => {
  describe('User 类型', () => {
    it('应正确定义 User 类型', () => {
      const user: User = {
        id: 1,
        username: 'testuser',
        role: 'admin',
        tenant_id: 1,
        is_active: true,
        created_at: '2024-01-01T00:00:00Z'
      }
      expect(user.id).toBe(1)
      expect(user.username).toBe('testuser')
      expect(user.role).toBe('admin')
    })

    it('应支持所有角色类型', () => {
      const roles: User['role'][] = ['admin', 'operator', 'viewer']
      expect(roles).toContain('admin')
      expect(roles).toContain('operator')
      expect(roles).toContain('viewer')
    })
  })

  describe('Device 类型', () => {
    it('应正确定义 Device 类型', () => {
      const device: Device = {
        id: 1,
        tenant_id: 1,
        device_id: 'IMEI123456',
        name: '空调1',
        zone_id: 1,
        protocol_version: 'V10',
        sim_card: '12345678901',
        is_online: true,
        last_seen_at: '2024-01-01T00:00:00Z',
        settings: {},
        created_at: '2024-01-01T00:00:00Z'
      }
      expect(device.device_id).toBe('IMEI123456')
      expect(device.is_online).toBe(true)
    })

    it('应支持可选字段为 null', () => {
      const device: Device = {
        id: 1,
        tenant_id: 1,
        device_id: 'IMEI123456',
        name: '空调1',
        zone_id: null,
        protocol_version: 'V10',
        sim_card: null,
        is_online: false,
        last_seen_at: null,
        settings: {},
        created_at: '2024-01-01T00:00:00Z'
      }
      expect(device.zone_id).toBeNull()
      expect(device.last_seen_at).toBeNull()
    })
  })

  describe('Zone 类型', () => {
    it('应正确定义 Zone 类型', () => {
      const zone: Zone = {
        id: 1,
        tenant_id: 1,
        name: '一楼办公区',
        parent_id: null,
        description: '一楼所有办公室',
        sort_order: 1,
        created_at: '2024-01-01T00:00:00Z'
      }
      expect(zone.name).toBe('一楼办公区')
      expect(zone.parent_id).toBeNull()
    })

    it('应支持嵌套分区', () => {
      const childZone: Zone = {
        id: 2,
        tenant_id: 1,
        name: '办公室A',
        parent_id: 1,
        description: null,
        sort_order: 1,
        created_at: '2024-01-01T00:00:00Z'
      }
      expect(childZone.parent_id).toBe(1)
    })
  })

  describe('Alarm 类型', () => {
    it('应正确定义 Alarm 类型', () => {
      const alarm: Alarm = {
        id: 1,
        tenant_id: 1,
        device_id: 'IMEI123456',
        type: 'offline',
        severity: 'high',
        message: '设备离线',
        details: {},
        is_resolved: false,
        occurred_at: '2024-01-01T00:00:00Z',
        resolved_at: null,
        created_at: '2024-01-01T00:00:00Z'
      }
      expect(alarm.type).toBe('offline')
      expect(alarm.severity).toBe('high')
      expect(alarm.is_resolved).toBe(false)
    })

    it('应支持所有告警类型', () => {
      const types: AlarmType[] = ['offline', 'illegal_on', 'temp_alarm']
      expect(types).toHaveLength(3)
    })

    it('应支持所有严重级别', () => {
      const severities: AlarmSeverity[] = ['high', 'medium', 'low']
      expect(severities).toHaveLength(3)
    })
  })

  describe('DashboardStats 类型', () => {
    it('应正确定义 DashboardStats 类型', () => {
      const stats: DashboardStats = {
        total_devices: 100,
        online_devices: 80,
        offline_devices: 20,
        total_alarms: 5,
        unresolved_alarms: 3
      }
      expect(stats.total_devices).toBe(100)
      expect(stats.online_devices).toBe(80)
      expect(stats.offline_devices).toBe(20)
    })
  })

  describe('Token 类型', () => {
    it('应正确定义 Token 类型', () => {
      const token: Token = {
        access_token: 'eyJhbGciOiJIUzI1NiIs...',
        token_type: 'bearer'
      }
      expect(token.access_token).toBeTruthy()
      expect(token.token_type).toBe('bearer')
    })
  })

  describe('LoginRequest 类型', () => {
    it('应正确定义 LoginRequest 类型', () => {
      const request: LoginRequest = {
        username: 'testuser',
        password: 'password123'
      }
      expect(request.username).toBe('testuser')
      expect(request.password).toBe('password123')
    })
  })

  describe('DeviceCreate 类型', () => {
    it('应正确定义 DeviceCreate 类型', () => {
      const create: DeviceCreate = {
        device_id: 'IMEI123456',
        name: '新空调',
        tenant_id: 1
      }
      expect(create.device_id).toBe('IMEI123456')
    })

    it('应支持可选字段', () => {
      const create: DeviceCreate = {
        device_id: 'IMEI123456',
        name: '新空调',
        tenant_id: 1,
        zone_id: 1,
        sim_card: '12345678901'
      }
      expect(create.zone_id).toBe(1)
    })
  })

  describe('DeviceUpdate 类型', () => {
    it('应正确定义 DeviceUpdate 类型', () => {
      const update: DeviceUpdate = {
        name: '更新名称'
      }
      expect(update.name).toBe('更新名称')
    })

    it('应允许部分字段更新', () => {
      const update: DeviceUpdate = {
        zone_id: 2
      }
      expect(update.zone_id).toBe(2)
      expect(update.name).toBeUndefined()
    })
  })

  describe('ZoneCreate 类型', () => {
    it('应正确定义 ZoneCreate 类型', () => {
      const create: ZoneCreate = {
        name: '新分区',
        tenant_id: 1
      }
      expect(create.name).toBe('新分区')
    })
  })

  describe('ZoneUpdate 类型', () => {
    it('应正确定义 ZoneUpdate 类型', () => {
      const update: ZoneUpdate = {
        name: '更新分区名',
        sort_order: 2
      }
      expect(update.name).toBe('更新分区名')
      expect(update.sort_order).toBe(2)
    })
  })
})