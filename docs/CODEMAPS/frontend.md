# 前端代码结构

<!-- AUTO-GENERATED -->
**Last Updated:** 2026-04-10

## 目录结构

```
frontend/
├── src/
│   ├── api/                 # API 模块
│   │   ├── client.ts        # Axios 客户端（含 CSRF 保护）
│   │   ├── auth.ts          # 认证 API
│   │   ├── devices.ts       # 设备 API
│   │   ├── zones.ts         # 分区 API
│   │   ├── reports.ts       # 报表 API
│   │   ├── users.ts         # 用户管理 API
│   │   ├── alarms.ts        # 告警管理 API
│   │   └── index.ts         # API 统一导出
│   ├── views/               # 页面组件
│   │   ├── Login.vue        # 登录页
│   │   ├── Dashboard.vue    # 仪表盘
│   │   ├── Devices.vue      # 设备管理
│   │   ├── DeviceDetail.vue # 设备详情
│   │   ├── Zones.vue        # 分区管理
│   │   ├── Alarms.vue       # 告警中心
│   │   ├── Reports.vue      # 报表分析（动态导入图表）
│   │   ├── Users.vue        # 用户管理（仅管理员）
│   │   └── Settings.vue     # 系统设置
│   ├── layouts/             # 布局组件
│   │   ├── MainLayout.vue   # 主布局
│   │   └── __tests__/       # 布局测试
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
│   │   ├── devices.ts       # 设备状态
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
│   └── reports.spec.ts      # 报表分析
├── index.html
├── vite.config.ts
├── tsconfig.json
├── package.json
└── playwright.config.ts
```

---

## 页面路由

| 路径 | 组件 | 描述 |
|------|------|------|
| `/login` | Login.vue | 登录页 |
| `/` | Dashboard.vue | 仪表盘 |
| `/devices` | Devices.vue | 设备列表 |
| `/devices/:id` | DeviceDetail.vue | 设备详情 |
| `/zones` | Zones.vue | 分区管理 |
| `/alarms` | Alarms.vue | 告警中心 |
| `/reports` | Reports.vue | 报表分析 |
| `/users` | Users.vue | 用户管理（仅管理员） |
| `/settings` | Settings.vue | 系统设置 |

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
deviceApi.list(params)              // 设备列表
deviceApi.get(deviceId)             // 设备详情
deviceApi.update(deviceId, data)    // 更新设备
deviceApi.delete(deviceId)          // 删除设备
deviceApi.getData(deviceId, params) // 设备数据
```

### 分区 API (`api/zones.ts`)

```typescript
zoneApi.list()                      // 分区列表
zoneApi.create(data)                // 创建分区
zoneApi.update(zoneId, data)        // 更新分区
zoneApi.delete(zoneId)              // 删除分区
```

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
}

// 设备
interface Device {
  id: number
  device_id: string
  name: string
  is_online: boolean
  zone_id?: number
}

// 分区
interface Zone {
  id: number
  name: string
  parent_id?: number
  children?: Zone[]
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

- 单元测试：371 tests
- E2E 测试：45 tests
- 覆盖率：93.05%

---

## 样式系统

### 主题配置 (`App.vue`)

使用 Ant Design Vue ConfigProvider 配置深色/浅色主题：

```vue
<a-config-provider :theme="themeConfig">
  <router-view />
</a-config-provider>
```

主题切换通过 `data-theme` 属性控制：

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