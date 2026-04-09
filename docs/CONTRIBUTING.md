# 贡献指南

<!-- AUTO-GENERATED sections are marked with comments -->

## 开发环境设置

### 前置要求

- Docker & Docker Compose
- Node.js 18+ (前端开发)
- Python 3.11+ (后端开发)

### 快速启动

```bash
# 克隆项目
git clone <repository-url>
cd bniot

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填写必填变量

# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps
```

---

<!-- AUTO-GENERATED: scripts table -->

## 前端脚本

| 命令 | 描述 |
|------|------|
| `npm run dev` | 启动开发服务器（热重载） |
| `npm run build` | 生产构建（含类型检查） |
| `npm run preview` | 预览生产构建 |
| `npm test` | 运行测试（Vitest） |
| `npm run test:run` | 运行测试（单次） |
| `npm run test:coverage` | 运行测试并生成覆盖率报告 |
| `npm run lint` | ESLint 检查并自动修复 |
| `npm run e2e` | 运行 E2E 测试（Playwright） |
| `npm run e2e:headed` | 运行 E2E 测试（可视化模式） |
| `npm run e2e:debug` | 运行 E2E 测试（调试模式） |
| `npm run e2e:report` | 显示 E2E 测试报告 |
| `npm run docs:check` | 检查文档同步状态 |
| `npm run docs:sync` | 同步更新文档 |

## 后端脚本

| 命令 | 描述 |
|------|------|
| `pytest` | 运行测试 |
| `pytest --cov=app` | 运行测试并生成覆盖率报告 |
| `pytest tests/unit/` | 运行单元测试 |
| `ruff check app/` | Ruff Lint 检查 |
| `ruff check --fix app/` | Ruff 自动修复 |

---

## 测试规范

### TDD 工作流

本项目严格遵循 TDD（测试驱动开发）：

1. **RED**: 先编写失败测试
2. **GREEN**: 实现最小代码使测试通过
3. **REFACTOR**: 重构优化，保持测试通过

### 测试覆盖率要求

- 前端: ≥ 80%
- 后端: ≥ 80%

### 运行测试

```bash
# 前端测试
cd frontend
npm test

# 后端测试
docker-compose exec backend pytest

# E2E 测试
cd frontend
npm run e2e
```

---

## 代码风格

### 前端（TypeScript/Vue）

- 使用 ESLint 10.x (flat config) 检查
- Vue 3 Composition API
- TypeScript 类型完整
- ESLint 配置文件：`eslint.config.js`

### 后端（Python）

- 使用 Ruff 检查
- 异步代码（async/await）
- FastAPI 规范

---

## PR 提交清单

提交 PR 前请确保：

- [ ] 所有测试通过
- [ ] 代码覆盖率达标
- [ ] Lint 检查无错误
- [ ] 无 console.log 调试语句
- [ ] TypeScript 类型完整
- [ ] 文档已更新（Git Hooks 会自动检查）

---

## 文档同步

项目使用三层机制确保代码与文档同步：

### 1. Git Hooks（自动）

```bash
# 安装 Git Hooks（首次配置）
./scripts/install-hooks.sh
```

每次 `git commit` 前自动检查文档同步状态。

### 2. 命令行检查

```bash
# 检查文档同步状态
./scripts/check-docs.sh

# 或通过 npm
npm run docs:check
```

### 3. 手动更新

```bash
# 更新文档
claude /everything-claude-code:update-docs
```

---

## 项目结构

```
bniot/
├── backend/          # FastAPI 后端
│   ├── app/
│   │   ├── api/      # API 端点
│   │   ├── core/     # 核心配置
│   │   ├── models/   # 数据模型
│   │   ├── mqtt/     # MQTT 处理
│   │   ├── schemas/  # Pydantic 模型
│   │   └── services/ # 业务服务
│   └── tests/        # 测试文件
├── frontend/         # Vue3 前端
│   ├── src/
│   │   ├── api/      # API 模块
│   │   ├── views/    # 页面组件
│   │   ├── router/   # 路由配置
│   │   └── styles/   # 样式文件
│   └── tests/        # 测试文件
├── docker/           # Docker 配置
├── docs/             # 文档
├── ssl/              # SSL 证书
└── volumes/          # 数据卷
```

---

## ECC 工作流

本项目使用 **everything-claude-code** 工作流：

| 命令 | 用途 |
|------|------|
| `/everything-claude-code:tdd` | 测试驱动开发 |
| `/everything-claude-code:plan` | 实现规划 |
| `/everything-claude-code:code-review` | 代码审查 |
| `/everything-claude-code:verify` | 验证检查 |
| `/everything-claude-code:e2e` | E2E 测试 |
| `/everything-claude-code:update-docs` | 文档更新 |