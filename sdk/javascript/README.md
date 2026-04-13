# BNIoT JavaScript SDK

空调节能管理系统物联网平台的 JavaScript/TypeScript 客户端 SDK。

## 安装

```bash
npm install bniot-sdk
```

或使用 yarn：

```bash
yarn add bniot-sdk
```

## 快速开始

### 认证登录

```javascript
import { BNIoTClient } from 'bniot-sdk';

// 创建客户端
const client = new BNIoTClient({
  baseUrl: 'https://www.jxbonner.cloud/api'
});

// 登录
await client.login('username', 'password');

// 登录成功后，token 会自动保存，后续请求自动携带认证
```

### 设备管理

```javascript
// 获取设备列表
const devices = await client.getDevices();
console.log(`共有 ${devices.length} 台设备`);

// 获取单个设备详情
const device = await client.getDevice(1);
console.log(`设备名称: ${device.name}`);

// 创建新设备
const newDevice = await client.createDevice({
  device_id: 'IMEI12345678',
  name: '空调-会议室'
});

// 更新设备
await client.updateDevice(1, { name: '空调-新名称' });

// 删除设备
await client.deleteDevice(1);
```

### 设备控制

```javascript
// 远程开机
await client.controlDevice(1, { airstate: 1 });

// 远程关机
await client.controlDevice(1, { airstate: 0 });
```

### 批量操作

```javascript
// 批量开机
const result = await client.batchControl([1, 2, 3], { airstate: 1 });
console.log(`成功: ${result.success_count}, 失败: ${result.failed_count}`);

// 批量删除
const result = await client.batchDelete([1, 2, 3]);
```

### 告警管理

```javascript
// 获取告警列表
const alarms = await client.getAlarms({ is_resolved: false });

// 处理告警
await client.resolveAlarm(1);
```

### WebSocket 实时推送

```javascript
// 连接 WebSocket
client.connectWebSocket();

// 设置消息回调
client.onDeviceUpdate = (data) => console.log('设备更新:', data);
client.onAlarm = (data) => console.log('新告警:', data);

// 断开连接
client.disconnectWebSocket();
```

## 错误处理

```javascript
import { BNIoTClient, BNIoTError } from 'bniot-sdk';

try {
  const device = await client.getDevice(999);
} catch (error) {
  if (error instanceof BNIoTError) {
    console.log(`错误码: ${error.code}`);
    console.log(`错误消息: ${error.message}`);
    console.log(`HTTP 状态码: ${error.httpStatus}`);
  }
}
```

## 配置选项

```javascript
const client = new BNIoTClient({
  baseUrl: 'https://www.jxbonner.cloud/api',
  timeout: 30000,  // 请求超时时间（毫秒）
  retryCount: 3,   // 失败重试次数
});
```

## TypeScript 类型

SDK 提供完整的 TypeScript 类型定义：

```typescript
import { BNIoTClient, Device, Alarm, DashboardStats } from 'bniot-sdk';

const client: BNIoTClient = new BNIoTClient({ baseUrl: '...' });
const devices: Device[] = await client.getDevices();
const stats: DashboardStats = await client.getDashboardStats();
```

## API 文档

完整 API 文档请访问：https://www.jxbonner.cloud/api/docs

## 许可证

MIT License