/**
 * TypeScript 类型定义
 * 与后端 Pydantic schemas 对应
 */

// ============ 用户认证 ============
export interface Token {
  access_token: string
  token_type: string
}

export interface TokenData {
  username: string | null
  tenant_id: number | null
}

export interface LoginRequest {
  username: string
  password: string
}

export interface PasswordChangeRequest {
  old_password: string
  new_password: string
}

// ============ 用户 ============
export interface User {
  id: number
  username: string
  role: 'admin' | 'operator' | 'viewer'
  tenant_id: number
  is_active: boolean
  created_at: string
  wechat_openid?: string | null
}

// ============ 租户 ============
export interface Tenant {
  id: number
  name: string
  code: string
  settings: Record<string, unknown>
  created_at: string
}

// ============ 分区 ============
export interface Zone {
  id: number
  tenant_id: number
  name: string
  parent_id: number | null
  description: string | null
  sort_order: number
  created_at: string
  children?: Zone[]
}

export interface ZoneCreate {
  name: string
  parent_id?: number | null
  description?: string | null
  sort_order?: number
  tenant_id: number
}

export interface ZoneUpdate {
  name?: string
  parent_id?: number | null
  description?: string | null
  sort_order?: number
}

// ============ 设备 ============
export interface Device {
  id: number
  tenant_id: number
  device_id: string
  name: string
  zone_id: number | null
  protocol_version: string
  sim_card: string | null
  is_online: boolean
  last_seen_at: string | null
  settings: Record<string, unknown>
  created_at: string
}

// 设备列表项（包含实时数据和分区信息）
export interface DeviceListItem extends Device {
  temp: number | null
  humi: number | null
  alarmtemp: number | null
  zone_name: string | null
}

// 设备详情（包含完整信息）
export interface DeviceDetail extends Device {
  zone_name: string | null
  firmware_version: string | null
  temp: number | null
  humi: number | null
  csq: number | null
  alarmtemp: number | null
  alarmhumi: number | null
  air_err: number | null
  airstate: number | null
  current: number | null
  supports_runtime: boolean
  today_runtime: number | null
  month_runtime: number | null
}

export interface DeviceCreate {
  device_id: string
  name: string
  zone_id?: number | null
  tenant_id: number
  sim_card?: string | null
}

export interface DeviceUpdate {
  name?: string
  zone_id?: number | null
  sim_card?: string | null
}

export interface DeviceWithData extends Device {
  temp: number | null
  humi: number | null
  airstate: number | null
  current: number | null
}

// ============ 设备数据 ============
export interface DeviceData {
  id: number
  time: string
  device_id: string
  tenant_id: number
  temp: number | null
  humi: number | null
  airstate: number | null
  current: number | null
  csq: number | null
  air_err: number | null
  alarmtemp: number | null
  alarmhumi: number | null
}

// ============ 告警 ============
export type AlarmType = 'offline' | 'illegal_on' | 'temp_alarm'
export type AlarmSeverity = 'high' | 'medium' | 'low'

export interface Alarm {
  id: number
  tenant_id: number
  device_id: string
  type: AlarmType
  severity: AlarmSeverity
  message: string | null
  details: Record<string, unknown>
  is_resolved: boolean
  occurred_at: string
  resolved_at: string | null
  created_at: string
}

export interface AlarmCreate {
  device_id: string
  type: AlarmType
  severity: AlarmSeverity
  message?: string | null
  details?: Record<string, unknown>
  tenant_id: number
  occurred_at: string
}

export interface AlarmUpdate {
  is_resolved?: boolean
}

// ============ 仪表盘统计 ============
export interface DashboardStats {
  total_devices: number
  online_devices: number
  offline_devices: number
  total_alarms: number
  unresolved_alarms: number
}

// ============ 通用响应 ============
export interface Message {
  message: string
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

// ============ API 错误响应 ============
export interface ApiError {
  detail: string
}

// ============ 查询参数 ============
export interface DeviceQueryParams {
  zone_id?: number
  is_online?: boolean
  keyword?: string
  protocol_version?: string
  skip?: number
  limit?: number
}

export interface DeviceDataQueryParams {
  hours?: number
}

// ============ 路由元信息 ============
export interface RouteMeta {
  title?: string
  requiresAuth?: boolean
  roles?: string[]
  [key: string]: unknown
}

// ============ 报表相关类型 ============
// 能耗统计
export interface EnergyStats {
  device_id: string
  device_name: string
  total_energy: number
  avg_power: number
  max_power: number
  runtime_hours: number
}

export interface EnergyStatsResponse {
  data: EnergyStats[]
  total_energy: number
  start_time: string
  end_time: string
  granularity: string
}

// 温湿度趋势
export interface TrendPoint {
  time: string
  value: number | null
}

export interface TrendData {
  device_id: string
  device_name: string
  temp_trend: TrendPoint[]
  humi_trend: TrendPoint[]
}

export interface TrendResponse {
  data: TrendData[]
  start_time: string
  end_time: string
  interval: number
}

// 告警统计
export interface AlarmStats {
  type?: string
  severity?: string
  count: number
  resolved_count: number
  unresolved_count: number
}

export interface AlarmStatsResponse {
  data: AlarmStats[]
  total_alarms: number
  resolved_alarms: number
  unresolved_alarms: number
  start_time: string
  end_time: string
}

// 运行时长统计
export interface RuntimeStats {
  device_id: string
  device_name: string
  zone_name: string | null
  total_runtime_hours: number
  on_time_percentage: number
  on_count: number
  off_count: number
}

export interface RuntimeResponse {
  data: RuntimeStats[]
  total_devices: number
  avg_runtime_hours: number
  start_time: string
  end_time: string
}

// 报表查询参数
export interface ReportQueryParams {
  start_time: string
  end_time: string
  device_ids?: string
  zone_id?: number
  granularity?: string // hour/day/month
  interval?: number // 分钟
  group_by?: string // type/severity/device
}