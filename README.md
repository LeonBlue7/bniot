# BNIoT - 空调节能管理系统

空调节能管理系统物联网项目，用于智能空调设备的远程监控、能耗管理和节能控制。

## 技术栈

### 后端
- **FastAPI** - Python 异步 Web 框架
- **SQLAlchemy** - 异步 ORM
- **TimescaleDB** - PostgreSQL 时序数据库扩展
- **Redis** - 缓存、Session、CSRF Token 存储
- **EMQX** - MQTT 消息代理
- **Alembic** - 数据库迁移工具
- **APScheduler** - 定时任务调度器

### 前端
- **Vue 3** - 渐进式 JavaScript 框架
- **TypeScript** - 类型安全
- **Ant Design Vue** - UI 组件库
- **ECharts** - 数据可视化图表
- **Pinia** - 状态管理
- **Vite** - 构建工具

### 基础设施
- **Docker & Docker Compose** - 容器化部署
- **Nginx** - 反向代理
- **SSL/TLS** - HTTPS 加密

## 项目结构

```
bniot/
├── backend/                # FastAPI 后端
│   ├── app/
│   │   ├── api/           # API 端点
│   │   │   └── endpoints/ # 认证、用户、设备、告警、报表、通知、备份、健康监控等
│   │   ├── core/          # 核心配置、错误码定义
│   │   ├── models/        # SQLAlchemy 模型
│   │   ├── mqtt/          # MQTT 处理
│   │   ├── schemas/       # Pydantic 模型
│   │   └── services/      # 业务服务
│   │       ├── notification/  # 多渠道通知服务
│   │       ├── permissions.py # RBAC 权限系统
│   │       ├── operation_log.py # 操作日志
│   │       ├── realtime_push.py # 实时推送
│   │       ├── backup.py  # 备份服务
│   │       ├── restore.py # 恢复服务
│   │       ├── excel_export.py # Excel 导出
│   │       └── backup_scheduler.py # 定时备份
│   ├── migrations/        # Alembic 迁移
│   └── tests/             # 测试文件
├── frontend/              # Vue 3 前端
│   ├── src/
│   │   ├── api/           # API 模块
│   │   ├── views/         # 页面组件
│   │   ├── components/    # 通用组件
│   │   ├── stores/        # Pinia 状态
│   │   └── utils/         # 工具函数
│   └── e2e/               # E2E 测试
├── docs/                  # 文档
│   ├── CODEMAPS/          # 代码结构文档
│   ├── CONTRIBUTING.md    # 贡献指南
│   ├── ENV.md             # 环境变量文档
│   └── RUNBOOK.md         # 运行手册
├── docker/                # Docker 配置
├── scripts/               # 脚本工具
└── ssl/                   # SSL 证书
```

## 快速开始

### 前置要求

- Docker & Docker Compose
- Git

### 安装部署

```bash
# 克隆项目
git clone https://github.com/LeonBlue7/bniot.git
cd bniot

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填写必填变量（见 docs/ENV.md）

# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps
```

### 开发环境

```bash
# 安装 Git Hooks
./scripts/install-hooks.sh

# 后端开发
docker-compose exec backend bash

# 前端开发
cd frontend
npm install
npm run dev
```

## 功能特性

### 核心功能
- **多租户隔离** - 数据安全隔离，租户级别权限控制
- **实时监控** - WebSocket 实时数据推送，设备状态实时更新
- **数据报表** - 能耗统计、趋势分析、运行时长统计
- **告警管理** - 设备离线、异常告警，批量处理支持
- **安全加固** - JWT 认证、CSRF 保护、RBAC 权限控制
- **深色主题** - 深色/浅色主题切换

### Phase 1-4 新增功能

#### Phase 1.1 - 权限系统增强
- **RBAC 权限控制** - 三级角色（admin/operator/viewer）
- **权限细分** - 设备、用户、分区、告警、报表、设置、日志、备份
- **租户隔离** - 严格的租户数据隔离检查

#### Phase 1.2 - 操作日志系统
- **审计追踪** - 所有关键操作记录日志
- **日志查询** - 支持多条件过滤（操作类型、资源、时间范围）
- **自动记录** - 设备操作、用户管理、告警处理等自动记录

#### Phase 2.2 - 多渠道通知
- **通知规则** - 自定义告警触发条件和通知渠道
- **邮件通知** - SMTP 邮件发送
- **微信通知** - 企业微信机器人推送
- **冷却时间** - 防止通知风暴
- **通知记录** - 完整的通知发送记录

#### Phase 2.3 - 实时数据推送
- **设备数据推送** - 温湿度、状态实时推送
- **设备状态推送** - 在线/离线状态实时通知
- **告警推送** - 告警实时推送通知

#### Phase 3.1-3.3 - 数据管理
- **数据库备份** - 手动备份、定时自动备份（凌晨2点）
- **数据恢复** - 从备份恢复数据，支持回滚
- **备份验证** - 备份文件完整性验证
- **Excel 导出** - 报表数据导出为 Excel 格式
- **安全备份** - 恢复前自动创建安全备份

#### Phase 4.1-4.2 - 系统增强
- **健康监控** - 数据库、Redis、MQTT、WebSocket 状态检查
- **性能指标** - 连接数、内存使用、运行时间等
- **诊断工具** - 数据库诊断、Redis 诊断、设备诊断
- **错误码文档** - 标准化错误码定义和 API 文档

### 设备管理
- 设备列表与详情
- 批量操作支持
- 参数设置
- 远程控制

### 数据分析
- 能耗统计图表
- 温湿度趋势
- 运行时长统计
- 告警分布
- Excel 导出

## API 文档

启动服务后访问：
- Swagger UI: `https://localhost:5000/docs`
- ReDoc: `https://localhost:5000/redoc`
- 错误码文档: `https://localhost:5000/api/docs/error-codes`

## 测试

```bash
# 后端测试
docker-compose exec backend pytest

# 前端测试
cd frontend
npm test

# E2E 测试
npm run e2e
```

### 测试覆盖率
- 后端：178 tests
- 前端：371 tests（93.05% 覆盖率）
- E2E：45 tests

## 文档

- [贡献指南](docs/CONTRIBUTING.md)
- [环境变量配置](docs/ENV.md)
- [运行手册](docs/RUNBOOK.md)
- [后端代码结构](docs/CODEMAPS/backend.md)
- [前端代码结构](docs/CODEMAPS/frontend.md)

## 开发工作流

本项目使用 **everything-claude-code** 工作流：

| 命令 | 用途 |
|------|------|
| `/everything-claude-code:plan` | 实现规划 |
| `/everything-claude-code:tdd` | 测试驱动开发 |
| `/everything-claude-code:code-review` | 代码审查 |
| `/everything-claude-code:verify` | 验证检查 |
| `/everything-claude-code:e2e` | E2E 测试 |
| `/everything-claude-code:update-docs` | 文档更新 |

## 安全特性

- JWT Token 认证（含 tenant_id）
- CSRF 保护
- WebSocket 消息认证
- 设备订阅授权检查
- 生产环境密码强度验证
- XSS 防护
- RBAC 权限控制
- 租户数据隔离
- 备份文件路径安全验证

## 许可证

MIT License

## 作者

LeonBlue7