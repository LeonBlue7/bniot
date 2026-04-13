/**
 * BNIoT JavaScript SDK 类型定义
 */

/**
 * BNIoT API 错误
 */
export class BNIoTError extends Error {
  code: string;
  message: string;
  httpStatus: number;
  details: Record<string, any> | null;
}

/**
 * SDK 配置选项
 */
export interface BNIoTClientOptions {
  baseUrl?: string;
  timeout?: number;
  retryCount?: number;
}

/**
 * 用户信息
 */
export interface User {
  id: number;
  username: string;
  role: string;
  tenant_id: number;
  is_active: boolean;
  created_at: string;
}

/**
 * 设备信息
 */
export interface Device {
  id: number;
  device_id: string;
  name: string;
  tenant_id: number;
  zone_id: number | null;
  protocol_version: string;
  sim_card: string | null;
  is_online: boolean;
  last_seen_at: string | null;
  settings: Record<string, any>;
  created_at: string;
}

/**
 * 设备数据
 */
export interface DeviceData {
  id: number;
  time: string;
  device_id: string;
  temp: number | null;
  humi: number | null;
  airstate: number | null;
  current: number | null;
  csq: number | null;
  air_err: number | null;
  alarmtemp: number | null;
  alarmhumi: number | null;
}

/**
 * 告警信息
 */
export interface Alarm {
  id: number;
  device_id: string;
  type: string;
  severity: string;
  message: string | null;
  details: Record<string, any>;
  is_resolved: boolean;
  occurred_at: string;
  resolved_at: string | null;
  created_at: string;
}

/**
 * 分区信息
 */
export interface Zone {
  id: number;
  name: string;
  parent_id: number | null;
  description: string | null;
  sort_order: number;
  tenant_id: number;
  created_at: string;
}

/**
 * 仪表盘统计
 */
export interface DashboardStats {
  total_devices: number;
  online_devices: number;
  offline_devices: number;
  total_alarms: number;
  unresolved_alarms: number;
}

/**
 * 批量操作结果
 */
export interface BatchOperationResult {
  success_count: number;
  failed_count: number;
  failed_details: Array<{
    device_id: number;
    reason: string;
  }>;
}

/**
 * Token 响应
 */
export interface TokenResponse {
  access_token: string;
  token_type: string;
}

/**
 * 设备查询选项
 */
export interface GetDevicesOptions {
  zoneId?: number;
  isOnline?: boolean;
  keyword?: string;
  skip?: number;
  limit?: number;
}

/**
 * 告警查询选项
 */
export interface GetAlarmsOptions {
  isResolved?: boolean;
  skip?: number;
  limit?: number;
}

/**
 * 设备控制选项
 */
export interface ControlOptions {
  airstate: number; // 0关机，1开机
}

/**
 * BNIoT SDK 客户端
 */
export class BNIoTClient {
  constructor(options?: BNIoTClientOptions);

  // 认证
  login(username: string, password: string): Promise<TokenResponse>;
  getCurrentUser(): Promise<User>;
  getCsrfToken(): Promise<{ csrf_token: string }>;

  // 设备管理
  getDevices(options?: GetDevicesOptions): Promise<Device[]>;
  getDevice(deviceId: number): Promise<Device>;
  getDeviceData(deviceId: number, hours?: number): Promise<DeviceData[]>;
  createDevice(data: Partial<Device>): Promise<Device>;
  updateDevice(deviceId: number, data: Partial<Device>): Promise<Device>;
  deleteDevice(deviceId: number): Promise<{ message: string }>;
  controlDevice(deviceId: number, options: ControlOptions): Promise<{ message: string }>;

  // 批量操作
  batchControl(deviceIds: number[], options: ControlOptions): Promise<BatchOperationResult>;
  batchDelete(deviceIds: number[]): Promise<BatchOperationResult>;
  batchMoveZone(deviceIds: number[], zoneId: number | null): Promise<BatchOperationResult>;

  // 告警管理
  getAlarms(options?: GetAlarmsOptions): Promise<Alarm[]>;
  resolveAlarm(alarmId: number): Promise<Alarm>;

  // 分区管理
  getZones(): Promise<Zone[]>;
  createZone(data: Partial<Zone>): Promise<Zone>;

  // 统计
  getDashboardStats(): Promise<DashboardStats>;

  // WebSocket
  connectWebSocket(): void;
  disconnectWebSocket(): void;
  onDeviceUpdate: ((data: any) => void) | null;
  onAlarm: ((data: any) => void) | null;
  onConnect: (() => void) | null;
  onDisconnect: (() => void) | null;
}