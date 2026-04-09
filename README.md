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
│   │   ├── core/          # 核心配置
│   │   ├── models/        # SQLAlchemy 模型
│   │   ├── mqtt/          # MQTT 处理
│   │   ├── schemas/       # Pydantic 模型
│   │   └── services/      # 业务服务
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
- 🏠 **多租户隔离** - 数据安全隔离
- 📊 **实时监控** - WebSocket 实时数据推送
- 📈 **数据报表** - 能耗统计、趋势分析
- ⚠️ **告警管理** - 设备离线、异常告警
- 🔐 **安全加固** - JWT 认证、CSRF 保护
- 🎨 **深色主题** - 深色/浅色主题切换

### 设备管理
- 设备列表与详情
- 批量操作
- 参数设置
- 远程控制

### 数据分析
- 能耗统计图表
- 温湿度趋势
- 运行时长统计
- 告警分布

## API 文档

启动服务后访问：
- Swagger UI: `https://localhost:5000/docs`
- ReDoc: `https://localhost:5000/redoc`

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

- ✅ JWT Token 认证
- ✅ CSRF 保护
- ✅ WebSocket 消息认证
- ✅ 设备订阅授权检查
- ✅ 生产环境密码强度验证
- ✅ XSS 防护

## 许可证

MIT License

## 作者

LeonBlue7