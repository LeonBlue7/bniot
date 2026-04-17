# 后端代码结构

<!-- AUTO-GENERATED -->
**Last Updated:** 2026-04-17

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
│   │       ├── users.py     # 用户管理 API（仅管理员）
│   │       ├── alarms.py    # 告警管理 API
│   │       ├── devices.py   # 设备 API
│   │       ├── zones.py     # 分区 API
│   │       ├── reports.py   # 报表 API
│   │       ├── websocket.py # WebSocket 端点
│   │       ├── logs.py      # 操作日志 API（Phase 1.2）
│   │       ├── notifications.py # 通知规则 API（Phase 2.2）
│   │       ├── health.py    # 系统健康监控 API（Phase 4.1）
│   │       ├── backups.py   # 备份管理 API（Phase 3.1）
│   │       ├── restores.py  # 恢复管理 API（Phase 3.2）
│   │       └── docs.py      # API 文档端点（Phase 4.2）
│   ├── core/                # 核心配置
│   │   ├── __init__.py
│   │   ├── config.py        # 配置管理（含安全检测）
│   │   ├── database.py      # 数据库连接
│   │   └── errors.py        # 错误码定义（Phase 4.2）
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
│   │   ├── reports.py       # 报表模型
│   │   ├── backup.py        # 备份请求/响应模型
│   │   └── restore.py       # 恢复请求/响应模型
│   └── services/            # 业务服务
│   │   ├── __init__.py
│   │   ├── auth.py          # 认证服务（含 tenant_id 验证）
│   │   ├── csrf.py          # CSRF Token 服务
│   │   ├── init_data.py     # 启动初始化（默认用户创建）
│   │   ├── websocket_manager.py # WebSocket 连接管理
│   │   ├── protocol_parser.py   # 协议解析器
│   │   ├── rate_limiter.py      # 速率限制
│   │   ├── reports.py           # 报表服务
│   │   ├── version_detector.py  # 版本检测
│   │   ├── permissions.py       # 权限系统（Phase 1.1）
│   │   ├── operation_log.py     # 操作日志（Phase 1.2）
│   │   ├── realtime_push.py     # 实时数据推送（Phase 2.3）
│   │   ├── backup.py            # 备份服务（Phase 3.1）
│   │   ├── restore.py           # 恢复服务（Phase 3.2）
│   │   ├── backup_scheduler.py  # 备份定时任务（Phase 3.1）
│   │   ├── excel_export.py      # Excel导出（Phase 3.3）
│   │   └── notification/        # 多渠道通知服务（Phase 2.2）
│   │       ├── __init__.py
│   │       ├── dispatch_service.py    # 通知分发
│   │       ├── rule_service.py        # 规则管理
│   │       ├── template_service.py    # 模板渲染
│   │       ├── email_service.py       # 邮件通知
│   │       └── wechat_service.py      # 微信通知
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
│       ├── test_users_api.py
│       ├── test_alarms_api.py
│       ├── test_dashboard_stats.py
│       ├── test_config_security.py
│       ├── test_models.py
│       ├── test_api.py
│       ├── test_rate_limiter.py
│       ├── test_protocol_parser.py
│       ├── test_version_detector.py
│       ├── test_security_fixes.py
│       └── test_permissions.py
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

### 用户管理 (`/api/users`)

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/` | 用户列表（仅管理员） |
| POST | `/` | 创建用户（仅管理员） |
| PUT | `/{user_id}` | 更新用户（仅管理员） |
| PATCH | `/{user_id}/status` | 启用/禁用用户（仅管理员） |
| DELETE | `/{user_id}` | 删除用户（仅管理员） |

### 告警管理 (`/api/alarms`)

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/` | 告警列表（支持过滤） |
| PATCH | `/{alarm_id}/handle` | 处理单个告警 |
| PATCH | `/batch-handle` | 批量处理告警 |
| GET | `/stats` | 告警统计 |

### 设备 (`/api/devices`)

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/` | 设备列表（分页响应：`DeviceListResponse`） |
| GET | `/stats` | 仪表盘统计 |
| GET | `/{device_id}` | 设备详情 |
| POST | `/` | 创建设备 |
| PUT | `/{device_id}` | 更新设备 |
| DELETE | `/{device_id}` | 删除设备 |
| POST | `/{device_id}/control` | 远程控制设备 |
| GET | `/{device_id}/data` | 设备历史数据 |
| GET | `/{device_id}/events` | 开关机事件记录 |
| GET | `/{device_id}/runtime` | 运行时间统计 |
| POST | `/batch/control` | 批量控制设备 |
| POST | `/batch/delete` | 批量删除设备 |
| POST | `/batch/move-zone` | 批量迁移分区 |

**新增响应格式（2026-04-16）**：

`GET /api/devices` 返回 `DeviceListResponse` 分页响应：
```json
{
  "items": [...],     // DeviceListItemResponse 数组
  "total": 76,        // 设备总数
  "skip": 0,          // 偏移量
  "limit": 20         // 每页数量
}
```

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

### 操作日志 (`/api/logs`) - Phase 1.2

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/` | 操作日志列表（需 admin/operator 权限） |
| GET | `/{log_id}` | 日志详情 |

### 通知管理 (`/api/notifications`) - Phase 2.2

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/rules` | 通知规则列表 |
| POST | `/rules` | 创建通知规则 |
| GET | `/rules/{rule_id}` | 获取规则详情 |
| PATCH | `/rules/{rule_id}` | 更新通知规则 |
| DELETE | `/rules/{rule_id}` | 删除通知规则 |
| GET | `/records` | 通知记录列表 |
| GET | `/stats` | 通知统计 |

### 健康监控 (`/api/health`) - Phase 4.1

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/health` | 系统健康检查（公开端点） |
| GET | `/metrics` | 系统性能指标（需认证） |
| GET | `/diagnostics/database` | 数据库诊断（需管理员权限） |
| GET | `/diagnostics/redis` | Redis 诊断（需管理员权限） |
| GET | `/diagnostics/devices` | 设备诊断（需管理员权限） |

### 备份管理 (`/api/backups`) - Phase 3.1

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/` | 备份列表 |
| POST | `/` | 创建手动备份（需管理员权限） |
| GET | `/{backup_id}` | 备份详情 |
| GET | `/{backup_id}/download` | 下载备份文件 |
| DELETE | `/{backup_id}` | 删除备份（需管理员权限） |
| GET | `/{backup_id}/validate` | 验证备份文件 |
| POST | `/{backup_id}/restore` | 从备份恢复（需管理员权限） |
| GET | `/scheduler/jobs` | 定时任务信息 |
| GET | `/restores` | 恢复记录列表 |

### 恢复管理 (`/api/restores`) - Phase 3.2

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/` | 恢复记录列表 |
| GET | `/{restore_id}` | 恢复详情 |

### API 文档 (`/api/docs`) - Phase 4.2

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/error-codes` | 错误码文档 |

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

### 启动初始化服务 (`services/init_data.py`)

自动检查并创建默认数据：
- `ensure_default_tenant()` - 确保默认租户存在
- `ensure_admin_user()` - 确保管理员用户存在
- `init_default_data()` - 初始化默认数据
- 支持环境变量自定义默认密码 (`DEFAULT_ADMIN_PASSWORD`)

### 权限系统 (`services/permissions.py`) - Phase 1.1

基于角色的访问控制（RBAC）：
- `Permission` - 权限枚举（设备、用户、分区、告警、报表、设置、日志、备份）
- `ROLE_PERMISSIONS` - 角色权限映射（admin/operator/viewer）
- `PermissionChecker` - 权限检查器
- `require_permission()` - 权限依赖装饰器
- `check_tenant_access()` - 租户隔离检查
- `can_manage_user()` - 用户管理权限检查

### 操作日志服务 (`services/operation_log.py`) - Phase 1.2

审计追踪功能：
- `ActionType` - 操作类型枚举（设备、用户、分区、告警、参数、登录）
- `ResourceType` - 资源类型枚举
- `OperationLogService` - 日志服务类
- `log()` - 记录操作日志
- `query()` - 查询日志（支持多条件过滤）
- `count()` - 统计日志数量
- `log_operation()` - 便捷函数

### WebSocket 管理器 (`services/websocket_manager.py`)

- `ConnectionManager` - 连接管理
- `connect()` - 建立连接
- `disconnect()` - 断开连接
- `broadcast_to_tenant()` - 租户广播
- `push_device_data()` - 推送设备数据

### 实时数据推送 (`services/realtime_push.py`) - Phase 2.3

集成 MQTT 和 WebSocket：
- `RealtimeDataPushService` - 实时推送服务
- `push_device_data()` - 推送设备数据（温湿度、状态等）
- `push_device_status()` - 推送设备在线/离线状态
- `push_alarm()` - 推送告警通知

### 多渠道通知服务 (`services/notification/`) - Phase 2.2

通知分发系统：
- `NotificationDispatchService` - 分发服务（规则匹配、渠道分发）
- `NotificationRuleService` - 规则管理（创建、更新、匹配）
- `NotificationTemplateService` - 模板渲染（邮件、微信）
- `EmailNotificationService` - 邮件通知（SMTP）
- `WeChatNotificationService` - 微信企业号通知

### 协议解析器 (`services/protocol_parser.py`)

- `ProtocolParser` - 策略模式解析器
- `V10Parser` - V10 协议解析
- `V20Parser` - V20 协议解析

### 版本检测 (`services/version_detector.py`)

- `VersionDetector` - 版本检测类
- 自动检测设备协议版本
- Redis 缓存管理
- **版本识别策略**（仅通过特征参数检测）：
  - V20 独有参数：108（冬天开始月份）、109（冬天结束月份）、110（空调关机间隔）
  - 若参数数据包含 108、109 或 110 任一参数 → V20
  - 否则 → V10
  - **注意**：Ver 字段是固件版本号，不能用于判断协议版本

### 备份服务 (`services/backup.py`) - Phase 3.1

数据库备份功能：
- `BackupService` - 备份服务类
- `create_backup_record()` - 创建备份记录
- `list_backups()` - 获取备份列表
- `generate_backup()` - 执行 pg_dump 备份
- `delete_backup()` - 删除备份文件和记录
- `cleanup_old_backups()` - 清理旧备份
- `get_backup_file_content()` - 获取备份内容
- `_validate_path()` - 路径安全验证

### 恢复服务 (`services/restore.py`) - Phase 3.2

数据恢复功能：
- `RestoreService` - 恢复服务类
- `validate_backup_file()` - 验证备份文件完整性
- `create_safety_backup()` - 创建恢复前安全备份
- `restore_from_backup()` - 执行恢复操作
- `_rollback_restore()` - 回滚恢复
- `update_restore_progress()` - 更新恢复进度
- `has_active_restore()` - 检查活跃恢复任务

### 备份调度器 (`services/backup_scheduler.py`) - Phase 3.1

定时备份任务：
- `BackupScheduler` - 调度器类（APScheduler）
- 每日凌晨2点自动备份
- 每周清理旧备份
- `execute_backup()` - 执行备份任务
- `cleanup_backups()` - 清理任务

### Excel 导出服务 (`services/excel_export.py`) - Phase 3.3

报表导出功能：
- `ExcelExportService` - Excel导出服务
- `export_data()` - 导出单工作表
- `export_multi_sheet()` - 导出多工作表
- `export_report_data()` - 按报表类型导出
- `_export_energy_report()` - 能耗报表
- `_export_trend_report()` - 温湿度趋势报表
- `_export_alarm_report()` - 告警报表
- `_export_runtime_report()` - 运行时长报表

### MQTT 处理 (`mqtt/handlers.py`)

- 设备上线处理
- 数据上送处理
- 主动版本探测
- **电流值转换**：设备上报电流单位 mA，存储/返回时转换为 A（除以 1000）

---

## 数据模型

### 核心表

| 表名 | 描述 | 索引 |
|------|------|------|
| `tenants` | 租户表 | - |
| `users` | 用户表 | `idx_users_tenant_id` |
| `zones` | 分区表 | `idx_zones_tenant_id` |
| `devices` | 设备表 | `idx_devices_tenant_id`, `idx_devices_is_online`, `idx_devices_last_seen` |
| `device_data` | 设备数据（时序） | Hypertable, `idx_device_data_time`, `idx_device_data_airstate` |
| `alarms` | 告警表 | `idx_alarms_tenant_id`, `idx_alarms_device_id`, `idx_alarms_occurred_at` |
| `operation_logs` | 操作日志 | `idx_operation_logs_tenant_id`, `idx_operation_logs_user_id`, `idx_operation_logs_action` |
| `protocol_versions` | 协议版本注册 | - |

### Phase 2.2 新增表

| 表名 | 描述 | 索引 |
|------|------|------|
| `notification_rules` | 通知规则表 | `idx_notification_rules_tenant_id`, `idx_notification_rules_enabled` |
| `notification_records` | 通知记录表 | `idx_notification_records_tenant_id`, `idx_notification_records_alarm_id`, `idx_notification_records_status` |

### Phase 3.1/3.2 新增表

| 表名 | 描述 | 索引 |
|------|------|------|
| `backup_records` | 备份记录表 | `idx_backup_records_tenant_id`, `idx_backup_records_status`, `idx_backup_records_backup_type` |
| `restore_records` | 恢复记录表 | `idx_restore_records_tenant_id`, `idx_restore_records_status`, `idx_restore_records_backup_id` |

### TimescaleDB 配置

- `device_data` 配置为 Hypertable
- 压缩策略：7 天后压缩
- 保留策略：365 天

---

## 数据库迁移

### 迁移文件列表

| 迁移文件 | 描述 | 创建日期 |
|----------|------|----------|
| `b9f4d3e6f2c5_add_airstate_index_for_runtime_queries.py` | 添加 airstate 索引优化运行时间查询 | 2026-04-15 |

### 索引说明

#### `idx_device_data_airstate` - 运行时间查询优化索引

**用途**：优化设备运行时间统计查询性能。

**索引字段**：`(device_id, tenant_id, airstate)`

**优化场景**：
- `/api/reports/runtime` 报表接口查询设备运行时长
- 统计空调开机/关机状态时长分布
- 按设备 ID 和租户 ID 过滤，同时筛选 airstate（空调运行状态）

**查询示例**：
```sql
-- 运行时间统计查询（使用此索引）
SELECT airstate, COUNT(*), SUM(duration)
FROM device_data
WHERE device_id = :device_id
  AND tenant_id = :tenant_id
  AND airstate IN (1, 2)  -- 1=制冷, 2=制热
GROUP BY airstate;
```

**性能提升**：对于百万级数据量的 device_data 表，该复合索引可将运行时间统计查询的响应时间从秒级降至毫秒级。

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

### 权限控制 (RBAC) - Phase 1.1

- 三级角色：admin/operator/viewer
- 权限细分：设备、用户、分区、告警、报表、设置、日志、备份
- 依赖装饰器：`require_permission(Permission.DEVICE_CREATE)`
- 租户隔离：`check_tenant_access()`

### 数据库安全

- Row Level Security (RLS)
- 租户隔离策略
- 外键级联删除

### 备份文件安全 - Phase 3.1

- 路径遍历攻击防护
- 允许目录白名单验证
- 规范化路径检查

---

## 错误码系统 (`core/errors.py`) - Phase 4.2

标准化错误码定义：

| 分类 | 范围 | 示例 |
|------|------|------|
| AUTH | 100-199 | AUTH_001（用户名或密码错误） |
| PERMISSION | 200-299 | PERMISSION_001（无权限访问） |
| VALIDATION | 300-399 | VALIDATION_001（参数验证失败） |
| RESOURCE | 400-499 | RESOURCE_001（资源不存在） |
| DEVICE | 500-599 | DEVICE_001（设备不存在） |
| SYSTEM | 600-699 | SYSTEM_001（服务器内部错误） |

错误响应格式：
```json
{
  "code": "DEVICE_001",
  "message": "设备不存在",
  "details": {"device_id": 12345},
  "http_status": 404
}
```

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
pytest tests/unit/test_users_api.py
pytest tests/unit/test_alarms_api.py
pytest tests/unit/test_permissions.py
```

### 测试统计

- 单元测试：200+ tests
- 跳过测试：23 (需项目根目录文件)