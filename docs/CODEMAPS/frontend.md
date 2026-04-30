# 前端代码结构

<!-- AUTO-GENERATED -->
**Last Updated:** 2026-04-30 (微信小程序绑定功能)

## 目录结构

```
frontend/
├── src/
│   ├── api/                 # API 模块
│   │   ├── client.ts        # Axios 客户端（含 CSRF 保护）
│   │   ├── auth.ts          # 认证 API（login、getCurrentUser、changePassword）
│   │   ├── devices.ts       # 设备 API（含批量移动分区、参数设置）
│   │   ├── zones.ts         # 分区 API（含授权管理）
│   │   ├── tenants.ts       # 租户 API（租户列表、当前租户）
│   │   ├── reports.ts       # 报表 API
│   │   ├── users.ts         # 用户管理 API
│   │   ├── alarms.ts        # 告警管理 API
│   │   └── index.ts         # API 统一导出
│   ├── views/               # 页面组件
│   │   ├── Login.vue        # 登录页
│   │   ├── Dashboard.vue    # 仪表盘
│   │   ├── Devices.vue      # 设备管理（含深色主题标签、批量移动分区）
│   │   ├── DeviceDetail.vue # 设备详情（含参数设置功能）
│   │   ├── Zones.vue        # 分区管理（含授权管理界面）
│   │   ├── Alarms.vue       # 告警中心
│   │   ├── Reports.vue      # 报表分析（动态导入图表、数据显示优化）
│   │   ├── Users.vue        # 用户管理（仅管理员）
│   │   ├── Settings.vue     # 系统设置
│   │   ├── Profile.vue      # 个人中心（用户信息、修改密码）
│   │   └── __tests__/       # 页面测试
│   ├── layouts/             # 布局组件
│   │   ├── MainLayout.vue   # 主布局（含菜单权限控制、个人中心导航）
│   │   └── __tests__/       # 布局测试（含菜单权限测试）
│   ├── components/          # 通用组件
│   │   └── charts/          # 图表组件（懒加载）
│   │       ├── EnergyChart.vue    # 能耗柱状图
│   │       ├── TrendChart.vue     # 温湿度趋势图
│   │       ├── AlarmPieChart.vue  # 告警饼图
│   │       └── RuntimeBarChart.vue # 运行时长图
│   ├── router/              # 路由配置
│   │   └── index.ts
│   ├── stores/              # Pinia 状态
│   │   ├── auth.ts          # 认证状态
│   │   ├── devices.ts       # 设备状态（含分页状态）
│   │   └── zones.ts         # 分区状态
│   ├── utils/               # 工具函数
│   │   ├── logger.ts        # 统一日志工具
│   │   ├── websocket.ts     # WebSocket 管理器
│   │   ├── csrf.ts          # CSRF 保护
│   │   ├── security.ts      # XSS 防护（DOMPurify）
│   │   ├── sanitize.ts      # 数据清洗
│   │   └── secureStorage.ts # 安全存储（sessionStorage）
│   ├── styles/              # 样式文件
│   │   ├── industrial.css   # 工业风格主题（CSS 变量）
│   │   └── style.css        # Chrome autofill 样式覆盖
│   ├── types/               # TypeScript 类型
│   │   └── index.ts
│   ├── App.vue              # 根组件（含主题配置）
│   └── main.ts              # 入口文件
├── eslint.config.js         # ESLint flat config（ESLint 10.x+）
├── tests/                   # 单元测试
│   ├── api/                 # API 测试
│   ├── utils/               # 工具测试
│   └── views/               # 组件测试
├── e2e/                     # E2E 测试
│   ├── auth.spec.ts         # 认证流程
│   ├── devices.spec.ts      # 设备管理
│   ├── zones.spec.ts        # 分区管理
│   ├── alarms.spec.ts       # 告警中心
│   ├── reports.spec.ts      # 报表分析
│   ├── param-setting.spec.ts # 参数设置功能
│   ├── comprehensive-test.spec.ts # 全面功能测试
│   └── full-test.spec.ts    # 全流程测试
├── index.html
├── vite.config.ts
├── tsconfig.json
├── package.json
└── playwright.config.ts     # E2E 测试配置（支持生产环境）
```

---

## E2E 测试配置

### playwright.config.ts

支持本地和生产环境 E2E 测试：

```typescript
// 根据 BASE_URL 或 TEST_ENV 环境变量决定测试环境
const baseURL = process.env.BASE_URL || process.env.TEST_ENV === 'production'
  ? 'https://www.jxbonner.cloud'
  : 'http://localhost:3000'
```

### 使用方法

```bash
# 本地测试（默认，启动开发服务器）
npx playwright test

# 生产环境测试（不启动本地服务器）
TEST_ENV=production npx playwright test

# 或指定自定义 URL
BASE_URL=https://www.jxbonner.cloud npx playwright test
```

### 测试项目配置

- **chromium**：Desktop Chrome 测试
- **测试目录**：./e2e
- **Reporter**：HTML + JSON + List
- **失败处理**：自动截图、录屏、Trace

---

## 页面路由

| 路径 | 组件 | 描述 |
|------|------|------|
| `/login` | Login.vue | 登录页 |
| `/` | Dashboard.vue | 仪表盘 |
| `/devices` | Devices.vue | 设备列表 |
| `/devices/:id` | DeviceDetail.vue | 设备详情 |
| `/zones` | Zones.vue | 分区管理（含授权管理） |
| `/alarms` | Alarms.vue | 告警中心 |
| `/reports` | Reports.vue | 报表分析 |
| `/users` | Users.vue | 用户管理（仅管理员） |
| `/settings` | Settings.vue | 系统设置 |

---

## 新增页面功能

### 参数设置功能 (`DeviceDetail.vue`) - 2026-04-21

系统管理员和操作员可远程设置设备参数：
- **空调开机条件**：夏天/冬天开机温度
- **空调关机条件**：夏天/冬天关机温度
- **开关机时间**：开机时间段1/2、关机时间段1/2（格式：HH:MM~HH:MM）
- **联动模式**：关闭/温度联动/时间段联动/温度+时间联动
- **其他参数**：上送周期、温度告警阈值、湿度告警阈值
- **V20 独有参数**：冬天开始月份、冬天结束月份、空调关机间隔

**版本差异化处理**：
- V10 设备显示 V10 参数集（冬天开机温度 105、冬天关机温度 106）
- V20 设备显示 V20 参数集（夏天关机温度 104、冬天关机温度 107、月份参数 108/109）

### 微信绑定功能 (`Profile.vue`) - 2026-04-30

用户可在个人中心绑定/解绑微信小程序：
- **绑定微信**：显示微信 openid，允许小程序登录
- **解绑微信**：清除 openid，小程序登录将创建新用户
- **状态显示**：已绑定/未绑定状态可视化

**API**：
- `bindWechat()` - 绑定微信（生成 openid）
- `unbindWechat()` - 解绑微信（清除 openid）

### 分区授权管理 (`Zones.vue`) - 2026-04-20

管理员可以在分区列表中管理授权：
- 查看每个分区的授权列表
- 将分区授权给其他租户
- 移除对租户的授权
- 创建分区时自动授权给当前租户

### 批量移动设备 (`Devices.vue`)

支持批量将设备移动到指定分区：
- 选择多个设备后可批量操作
- 移动到已有分区或移出分区（变为未分区）
- 操作后自动刷新列表显示最新分区

---

## API 模块

### 认证 API (`api/auth.ts`)

```typescript
authApi.login(username, password)  // 登录
authApi.register(userData)          // 注册
authApi.getCurrentUser()            // 获取当前用户
```

### 设备 API (`api/devices.ts`)

```typescript
deviceApi.list(params)              // 设备列表（返回 DeviceListResponse 分页响应）
deviceApi.get(deviceId)             // 设备详情（含运行统计）
deviceApi.update(deviceId, data)    // 更新设备
deviceApi.delete(deviceId)          // 删除设备
deviceApi.getData(deviceId, params) // 设备历史数据
deviceApi.getEvents(deviceId, params) // 开关机记录（仅V10）
deviceApi.getRuntime(deviceId)      // 运行时间统计（仅V10）
deviceApi.batchMoveZone(deviceIds, zoneId) // 批量移动设备分区
deviceApi.getParams(deviceId)       // 获取设备参数列表（V10/V20差异化）
deviceApi.setParam(deviceId, paramCode, paramValue) // 设置单个参数
deviceApi.batchSetParam(deviceIds, params) // 批量设置参数
```

**批量移动分区**（2026-04-20 新增）：
- `batchMoveZone(deviceIds, zoneId)` - 将多个设备移动到指定分区
- `zoneId` 为 `null` 时表示移出分区（设备变为未分区状态）
- 返回 `{ success_count, failed_count, failed_details }`

**新增返回格式（2026-04-16）**：

`deviceApi.list()` 返回 `DeviceListResponse`：
```typescript
interface DeviceListResponse {
  items: DeviceListItem[]   // 设备数组
  total: number            // 设备总数
  skip: number             // 偏移量
  limit: number            // 每页数量
}
```

| API | 新增字段 | 说明 |
|-----|---------|------|
| `list()` | `temp`, `humi`, `alarmtemp`, `zone_name` | 实时数据、告警状态、分区名称 |
| `get()` | `firmware_version`, `csq`, `air_err`, `alarmhumi`, `current`, `airstate`, `supports_runtime`, `today_runtime`, `month_runtime` | 设备详情完整数据、版本差异化字段 |

### 分区 API (`api/zones.ts`)

```typescript
zoneApi.list()                      // 分区列表
zoneApi.create(data)                // 创建分区
zoneApi.update(zoneId, data)        // 更新分区
zoneApi.delete(zoneId)              // 删除分区
zoneApi.listAuthorizations(zoneId)  // 分区授权列表
zoneApi.authorize(zoneId, tenantId) // 授权分区给租户
zoneApi.removeAuthorization(zoneId, tenantId) // 移除分区授权
```

**分区授权管理**（2026-04-20 新增）：
- `listAuthorizations(zoneId)` - 获取分区的授权列表
- `authorize(zoneId, tenantId)` - 将分区授权给指定租户
- `removeAuthorization(zoneId, tenantId)` - 移除对指定租户的授权

### 租户 API (`api/tenants.ts`)

```typescript
tenantApi.list()                    // 租户列表（仅管理员）
tenantApi.getCurrent()              // 当前用户所属租户信息
```

**用途**：用于分区授权管理界面，获取可选的租户列表进行授权操作。

### 报表 API (`api/reports.ts`)

```typescript
reportApi.getEnergyStats(params)    // 能耗统计
reportApi.getTrendData(params)      // 温湿度趋势
reportApi.getAlarmStats(params)     // 告警统计
reportApi.getRuntimeStats(params)   // 运行时长
reportApi.exportReport(params)      // 导出报表
```

### 用户管理 API (`api/users.ts`)

```typescript
userApi.list()                       // 用户列表
userApi.create(data)                 // 创建用户
userApi.update(id, data)             // 更新用户
userApi.updateStatus(id, data)      // 启用/禁用用户
userApi.delete(id)                   // 删除用户
userApi.bindWechat()                 // 绑定微信小程序（2026-04-30）
userApi.unbindWechat()               // 解绑微信小程序（2026-04-30）
```

### 告警管理 API (`api/alarms.ts`)

```typescript
alarmApi.list(params)               // 告警列表（支持过滤）
alarmApi.handle(alarmId)            // 处理单个告警
alarmApi.batchHandle(alarmIds)      // 批量处理告警
alarmApi.getStats()                 // 获取告警统计
```

---

## 图表组件

### 懒加载优化

所有图表组件使用 `defineAsyncComponent` 实现懒加载：

```typescript
const EnergyChart = defineAsyncComponent(() =>
  import('@/components/charts/EnergyChart.vue')
)
```

### 组件列表

| 组件 | 功能 | Props |
|------|------|-------|
| `EnergyChart` | 能耗柱状图 | `data`, `loading`, `autoResize`, `showExport` |
| `TrendChart` | 温湿度趋势图 | `data`, `loading`, `showExport` |
| `AlarmPieChart` | 告警饼图 | `data`, `loading`, `groupBy` |
| `RuntimeBarChart` | 运行时长图 | `data`, `loading`, `sortByRuntime`, `maxItems` |

---

## 工具模块

### 日志工具 (`utils/logger.ts`)

```typescript
import { logger, wsLogger, apiLogger } from '@/utils/logger'

logger.info('message')      // 通用日志
wsLogger.debug('connected') // WebSocket 模块日志
apiLogger.error('failed')   // API 模块日志
```

特性：
- 开发环境启用，生产环境禁用
- 支持模块化日志器
- 可配置日志级别

### WebSocket 管理器 (`utils/websocket.ts`)

```typescript
const ws = new WebSocketManager({
  url: 'wss://host/ws',
  token: 'jwt-token',
  onMessage: (msg) => console.log(msg)
})

ws.connect()
ws.send({ type: 'subscribe', topic: 'device' })
```

特性：
- 自动重连
- 心跳保活
- 订阅管理
- 多租户隔离

### CSRF 保护 (`utils/csrf.ts`)

```typescript
import { csrfProtection } from '@/utils/csrf'

// 获取 CSRF Token
await csrfProtection.refreshToken()

// 获取请求头
const headers = csrfProtection.getHeaders()
// { 'X-CSRF-Token': 'token-value' }
```

### 安全存储 (`utils/secureStorage.ts`)

```typescript
import { secureStorage } from '@/utils/secureStorage'

secureStorage.setToken('jwt-token')  // 存储到 sessionStorage
secureStorage.getToken()              // 获取 Token
secureStorage.setUser(userData)       // 存储用户信息
```

### XSS 防护 (`utils/security.ts`)

```typescript
import { sanitize, sanitizeText, isSafeUrl } from '@/utils/security'

sanitize('<script>alert(1)</script>')  // 清理 HTML
sanitizeText(userInput)                // 清理纯文本
isSafeUrl(url)                         // 检查 URL 安全性
```

---

## TypeScript 类型

### 核心类型

```typescript
// 用户
interface User {
  id: number
  username: string
  role: 'admin' | 'operator' | 'viewer'
  tenant_id: number
  is_active: boolean
  created_at: string
  wechat_openid?: string            // 微信小程序 openid（2026-04-30）
}

// 设备
interface Device {
  id: number
  device_id: string
  name: string
  is_online: boolean
  zone_id?: number
}

// 设备列表项（含实时数据）
interface DeviceListItem extends Device {
  temp: number | null           // 实时温度
  humi: number | null           // 实时湿度
  alarmtemp: number | null      // 温度告警状态
  zone_name: string | null      // 分区名称
}

// 设备列表分页响应（2026-04-16 新增）
interface DeviceListResponse {
  items: DeviceListItem[]       // 设备数组
  total: number                 // 设备总数
  skip: number                  // 偏移量
  limit: number                 // 每页数量
}

// 设备详情（含完整信息）
interface DeviceDetail extends Device {
  zone_name: string | null
  firmware_version: string | null
  temp: number | null
  humi: number | null
  csq: number | null            // 信号强度
  alarmtemp: number | null      // 温度告警
  alarmhumi: number | null      // 湿度告警
  air_err: number | null        // 空调故障码
  airstate: number | null       // 空调状态（V10专属）
  current: number | null        // 电流（V10专属，单位：A，后端已从mA转换）
  supports_runtime: boolean     // 是否支持运行统计
  today_runtime: number | null  // 当天运行时间（小时）
  month_runtime: number | null  // 当月运行时间（小时）
}

// 分区
interface Zone {
  id: number
  name: string
  parent_id?: number
  children?: Zone[]
}

// 分区授权（2026-04-20 新增）
interface ZoneAuthorization {
  id: number
  zone_id: number
  tenant_id: number
  created_at: string
}

// 租户（2026-04-20 新增）
interface Tenant {
  id: number
  name: string
  code: string
  created_at: string
}

// 批量操作响应（2026-04-20 新增）
interface BatchOperationResponse {
  success_count: number
  failed_count: number
  failed_details: Array<{ device_id: number; reason: string }>
}

// 参数信息（2026-04-21 新增）
interface ParamInfo {
  code: string              // 参数编号（如 101, 102）
  name: string              // 参数名称
  type: string              // 参数类型（int/float/string）
  range: string | null      // 参数范围
  desc: string | null       // 参数描述
  current_value: any | null // 当前值
}

// 设备参数响应（2026-04-21 新增）
interface DeviceParamsResponse {
  version: string           // 协议版本（V10/V20）
  params: ParamInfo[]       // 参数列表
  supported_codes: string[] // 支持的参数编号列表
}

// 参数设置响应（2026-04-21 新增）
interface SetParamResponse {
  success: boolean
  message: string
  param_code: string | null
  validation_errors: string[] | null
}

// 告警
interface Alarm {
  id: number
  device_id: string
  type: string
  severity: 'high' | 'medium' | 'low'
  message?: string
  is_resolved: boolean
  occurred_at: string
  resolved_at?: string
}

// 报表
interface EnergyStats { ... }
interface TrendData { ... }
interface AlarmStats { ... }
interface RuntimeStats { ... }
```

---

## 测试

```bash
# 运行单元测试
npm test

# 运行单次测试
npm run test:run

# 运行覆盖率测试
npm run test:coverage

# 运行 E2E 测试
npm run e2e

# 运行 E2E 测试（可视化）
npm run e2e:headed
```

### 测试覆盖率

- 单元测试：399 tests
- E2E 测试：54 tests（含参数设置功能 9 tests）
- 覆盖率：90%+

---

## 样式系统

### 主题配置 (`App.vue`)

使用 Ant Design Vue ConfigProvider 配置深色/浅色主题和中文国际化：

```vue
<a-config-provider :theme="themeConfig" :locale="zhCN">
  <router-view />
</a-config-provider>
```

特性：
- 深色/浅色主题切换
- 中文 locale 配置（zhCN）
- 主题切换通过 `data-theme` 属性控制

```typescript
document.documentElement.setAttribute('data-theme', 'dark' | 'light')
```

### 工业风格主题 (`styles/industrial.css`)

- 支持深色/浅色双主题
- 公共设计令牌在 `:root` 定义（字体、间距等）
- 主题颜色在 `[data-theme='dark']` 和 `[data-theme='light']` 定义
- 等宽字体用于数据显示
- 状态颜色语义化
- CSS 变量驱动

### Chrome Autofill 样式 (`style.css`)

覆盖 Chrome 自动填充样式，确保深色主题下输入框样式一致：

```css
input:-webkit-autofill {
  -webkit-box-shadow: 0 0 0 1000px var(--color-bg-tertiary) inset;
  -webkit-text-fill-color: var(--color-text-primary);
}
```

### 主要变量

```css
--color-bg-primary
--color-text-primary
--color-status-success
--color-status-danger
--font-mono
```