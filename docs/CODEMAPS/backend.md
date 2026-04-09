# 后端代码结构

<!-- AUTO-GENERATED -->

## 目录结构

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI 应用入口
│   ├── api/                 # API 路由
│   │   ├── __init__.py      # 路由注册
│   │   └── endpoints/       # API 端点
│   │       ├── __init__.py
│   │       ├── auth.py      # 认证 API（含 CSRF）
│   │       ├── devices.py   # 设备 API
│   │       ├── zones.py     # 分区 API
│   │       ├── reports.py   # 报表 API
│   │       └── websocket.py # WebSocket 端点
│   ├── core/                # 核心配置
│   │   ├── __init__.py
│   │   ├── config.py        # 配置管理（含安全检测）
│   │   └── database.py      # 数据库连接
│   ├── models/              # SQLAlchemy 模型
│   │   ├── __init__.py
│   │   └── models.py        # 数据表定义
│   ├── mqtt/                # MQTT 模块
│   │   ├── __init__.py
│   │   ├── client.py        # MQTT 客户端
│   │   └── handlers.py      # 消息处理器
│   ├── schemas/             # Pydantic 模型
│   │   ├── __init__.py
│   │   ├── schemas.py       # 通用模型
│   │   └── reports.py       # 报表模型
│   └── services/            # 业务服务
│       ├── __init__.py
│       ├── auth.py          # 认证服务（含 tenant_id 验证）
│       ├── csrf.py          # CSRF Token 服务
│       ├── websocket_manager.py # WebSocket 连接管理
│       ├── protocol_parser.py   # 协议解析器
│       ├── rate_limiter.py      # 速率限制
│       ├── reports.py           # 报表服务
│       └── version_detector.py  # 版本检测
├── migrations/              # Alembic 数据库迁移
│   ├── env.py
│   └── versions/
├── tests/
│   ├── conftest.py          # 测试配置
│   └── unit/                # 单元测试
│       ├── test_auth.py
│       ├── test_csrf.py
│       ├── test_websocket.py
│       ├── test_reports_api.py
│       └── test_config_security.py
├── Dockerfile
├── alembic.ini              # Alembic 配置
├── requirements.txt
└── pyproject.toml           # Ruff 配置
```

---

## API 端点

### 认证 (`/api/auth`)

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/login` | 用户登录 |
| POST | `/register` | 用户注册 |
| GET | `/csrf-token` | 获取 CSRF Token |

### 设备 (`/api/devices`)

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/` | 设备列表 |
| GET | `/{device_id}` | 设备详情 |
| PUT | `/{device_id}` | 更新设备 |
| DELETE | `/{device_id}` | 删除设备 |
| GET | `/{device_id}/data` | 设备数据 |

### 分区 (`/api/zones`)

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/` | 分区列表 |
| POST | `/` | 创建分区 |
| PUT | `/{zone_id}` | 更新分区 |
| DELETE | `/{zone_id}` | 删除分区 |

### 报表 (`/api/reports`)

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/energy` | 能耗统计 |
| GET | `/trend` | 温湿度趋势 |
| GET | `/alarms` | 告警统计 |
| GET | `/runtime` | 运行时长 |
| GET | `/export` | 报表导出 |

### WebSocket (`/api/ws`)

| 端点 | 描述 |
|------|------|
| `ws://host/api/ws?token=JWT` | WebSocket 连接 |

消息类型：
- `ping/pong` - 心跳
- `subscribe/unsubscribe` - 订阅管理
- `device_data/alarm/device_status` - 数据推送

---

## 核心模块

### 认证服务 (`services/auth.py`)

- `get_password_hash()` - 密码哈希
- `verify_password()` - 密码验证
- `create_access_token()` - JWT 生成（含 tenant_id）
- `get_current_user()` - 获取当前用户

### CSRF 服务 (`services/csrf.py`)

- `generate_csrf_token()` - 生成 Token
- `verify_csrf_token()` - 验证 Token
- `CsrfMiddleware` - CSRF 中间件

### WebSocket 管理器 (`services/websocket_manager.py`)

- `ConnectionManager` - 连接管理
- `connect()` - 建立连接
- `disconnect()` - 断开连接
- `broadcast_to_tenant()` - 租户广播
- `push_device_data()` - 推送设备数据

### 协议解析器 (`services/protocol_parser.py`)

- `ProtocolParser` - 策略模式解析器
- `V10Parser` - V10 协议解析
- `V20Parser` - V20 协议解析

### 版本检测 (`services/version_detector.py`)

- `VersionDetector` - 版本检测类
- 自动检测设备协议版本
- Redis 缓存管理

### MQTT 处理 (`mqtt/handlers.py`)

- 设备上线处理
- 数据上送处理
- 主动版本探测

---

## 数据模型

### 核心表

| 表名 | 描述 | 索引 |
|------|------|------|
| `tenants` | 租户表 | - |
| `users` | 用户表 | `idx_users_tenant_id` |
| `zones` | 分区表 | `idx_zones_tenant_id` |
| `devices` | 设备表 | `idx_devices_tenant_id` |
| `device_data` | 设备数据（时序） | Hypertable |
| `alarms` | 告警表 | `idx_alarms_tenant_id` |
| `operation_logs` | 操作日志 | `idx_operation_logs_tenant_id` |
| `protocol_versions` | 协议版本注册 | - |

### TimescaleDB 配置

- `device_data` 配置为 Hypertable
- 压缩策略：7 天后压缩
- 保留策略：365 天

---

## 安全特性

### JWT 增强

- Token 包含 `tenant_id`
- 验证用户租户归属
- 不安全密钥检测

### CSRF 保护

- Token 存储在 Redis
- 1 小时过期
- 一次性使用

### 数据库安全

- Row Level Security (RLS)
- 租户隔离策略
- 外键级联删除

---

## 测试

```bash
# 运行所有测试
pytest

# 运行单元测试
pytest tests/unit/

# 运行带覆盖率
pytest --cov=app

# 运行特定测试文件
pytest tests/unit/test_csrf.py
pytest tests/unit/test_websocket.py
```

### 测试统计

- 单元测试：170 tests
- 跳过测试：23 (需项目根目录文件)