# 技术架构规划：空调节能管理系统物联网项目（BNIoT）

## 一、需求重述

### 核心目标
构建一个空调节能管理系统物联网平台，实现：
- 设备远程监控与数据采集（MQTT协议）
- 多租户数据隔离
- 设备分区管理
- 实时仪表盘与告警
- 远程控制与参数设置
- 报表统计分析

### 关键约束
- 设备端嵌入式程序已完成，协议不可修改
- MQTT认证硬编码（test1/test123）
- 两个协议版本（V10/V20）需兼容解析
- Docker 开发/生产环境统一
- 先后端+管理后台，小程序后续迭代

---

## 二、技术选型建议

### 方案对比

| 层级 | 方案A | 方案B | 推荐 |
|------|-------|-------|------|
| MQTT Broker | EMQX 5.5 | Mosquitto | **EMQX 5.5**（企业级、可视化管理、数据持久化） |
| 后端框架 | Python FastAPI | Go Gin | **FastAPI**（异步、快速开发） |
| 数据库 | PostgreSQL | MySQL | **PostgreSQL**（JSONB支持、物化视图） |
| 缓存 | Redis | 内存 | **Redis**（版本缓存、会话） |
| 前端框架 | Vue3 | React | **Vue3**（参考thingsboard-ui-vue3） |
| 前端UI库 | Ant Design Vue | Element Plus | **Ant Design Vue** |
| 时序数据 | TimescaleDB扩展 | 独立InfluxDB | **TimescaleDB**（PostgreSQL扩展） |

### 最终推荐技术栈

```
┌─────────────────────────────────────────────────────────┐
│                    前端管理后台                           │
│  Vue3 + Ant Design Vue + Vite + TypeScript              │
├─────────────────────────────────────────────────────────┤
│                    后端 API 服务                          │
│  Python 3.11 + FastAPI + SQLAlchemy + asyncio           │
├─────────────────────────────────────────────────────────┤
│                    MQTT Broker                           │
│  EMQX 5.5（支持设备认证、规则引擎、Webhook、数据持久化）   │
├─────────────────────────────────────────────────────────┤
│                    数据存储                               │
│  PostgreSQL 16 + TimescaleDB（时序数据）                 │
│  Redis 7.x（版本缓存、会话、实时状态）                    │
├─────────────────────────────────────────────────────────┤
│                    容器编排                               │
│  Docker + Docker Compose + 数据卷持久化                  │
└─────────────────────────────────────────────────────────┘
```

---

## 三、系统架构设计

### 整体架构图

```
                    ┌──────────────┐
                    │  管理后台     │
                    │  Vue3 SPA    │
                    └──────┬───────┘
                           │ HTTPS/WSS
                    ┌──────▼───────┐
                    │  API Gateway │
                    │  Nginx       │
                    └──────┬───────┘
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
    ┌────▼────┐      ┌────▼────┐      ┌────▼────┐
    │ FastAPI │      │  EMQX   │      │  Redis  │
    │ 后端服务 │◄────►│ Broker  │◄────►│  缓存   │
    └────┬────┘      └────┬────┘      └────┬────┘
         │                │                 │
         └────────────────┼─────────────────┘
                          │
                   ┌──────▼───────┐
                   │ PostgreSQL   │
                   │ + TimescaleDB│
                   └──────────────┘
                          │
                    ┌─────▼─────┐
                    │ 4G 设备端 │
                    │ MQTT客户端│
                    └───────────┘
```

### 数据流设计

```
设备上线流程:
设备 → MQTT(login) → EMQX → Webhook → FastAPI
                              ↓
                    主动发送 getparam
                              ↓
设备 → MQTT(getparam_reply) → EMQX → Webhook → FastAPI
                              ↓
                    版本检测 → Redis缓存 → PostgreSQL

数据上送流程:
设备 → MQTT(datas) → EMQX → 规则引擎 → PostgreSQL(TimescaleDB)
                              ↓
                    告警检测 → Redis → WebSocket推送前端

远程控制流程:
前端 → FastAPI → EMQX → 设备
              ↓
        日志记录 → PostgreSQL
```

---

## 四、数据持久化配置

### 数据卷挂载策略

为保证数据备份安全，所有关键服务数据必须挂载到容器外部：

```
项目目录结构：
bniot/
├── volumes/                    # 数据卷目录（容器外持久化）
│   ├── postgres/               # PostgreSQL 数据
│   │   ├── data/               # 数据库文件
│   │   └── backups/            # 备份文件
│   ├── redis/                  # Redis 数据
│   │   └── data/               # RDB/AOF 持久化文件
│   ├── emqx/                   # EMQX 数据
│   │   ├── data/               # EMQX 运行数据
│   │   ├── log/                # EMQX 日志
│   │   └── loaded_plugins/     # 插件配置
│   │   └── certs/              # SSL 证书
│   └── backend/                # 后端日志
│       └── logs/               # API 服务日志
├── backend/                    # FastAPI 后端源码
├── frontend/                   # Vue3 前端源码
├── docker/                     # Docker 配置
├── ssl/                        # SSL 证书（域名证书）
└── docs/                       # 文档
```

### Docker Compose 数据卷配置

```yaml
services:
  postgres:
    volumes:
      - ./volumes/postgres/data:/var/lib/postgresql/data
      - ./volumes/postgres/backups:/var/lib/postgresql/backups
      
  redis:
    volumes:
      - ./volumes/redis/data:/data
    command: ["redis-server", "--appendonly yes", "--save 60 1000"]
    
  emqx:
    image: emqx/emqx:5.5
    volumes:
      - ./volumes/emqx/data:/opt/emqx/data
      - ./volumes/emqx/log:/opt/emqx/log
      - ./volumes/emqx/loaded_plugins:/opt/emqx/loaded_plugins
      - ./ssl:/opt/emqx/etc/certs:ro
      
  backend:
    volumes:
      - ./backend:/app
      - ./volumes/backend/logs:/app/logs
```

### 备份策略

| 服务 | 备份方式 | 备份频率 | 存储位置 |
|------|----------|----------|----------|
| PostgreSQL | pg_dump + TimescaleDB备份 | 每日凌晨2点 | volumes/postgres/backups/ |
| Redis | RDB + AOF 双重持久化 | 实时+AOF | volumes/redis/data/ |
| EMQX | 内置持久化 + 配置导出 | 每周 | volumes/emqx/data/ |

### EMQX 5.5 数据持久化

EMQX 5.5 支持多种数据持久化方式：
- **内置数据库**：设备连接状态、订阅关系持久化
- **规则引擎**：消息持久化到 PostgreSQL/Redis
- **配置导出**：通过 API 导出配置备份

---

## 五、数据库设计

### 核心表结构

```sql
-- 多租户用户表
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    tenant_id INT REFERENCES tenants(id),
    username VARCHAR(50) UNIQUE,
    password_hash VARCHAR(255),
    role VARCHAR(20),  -- 'admin', 'operator', 'viewer'
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 租户表
CREATE TABLE tenants (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    code VARCHAR(20) UNIQUE,
    settings JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 分区表
CREATE TABLE zones (
    id SERIAL PRIMARY KEY,
    tenant_id INT REFERENCES tenants(id),
    name VARCHAR(100),
    parent_id INT REFERENCES zones(id),
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 设备表
CREATE TABLE devices (
    id SERIAL PRIMARY KEY,
    tenant_id INT REFERENCES tenants(id),
    zone_id INT REFERENCES zones(id),
    device_id VARCHAR(20) UNIQUE,  -- IMEI号
    name VARCHAR(100),
    protocol_version VARCHAR(10),  -- 'V10', 'V20'
    sim_card VARCHAR(30),
    is_online BOOLEAN DEFAULT false,
    last_seen_at TIMESTAMP,
    settings JSONB,  -- 当前参数配置
    created_at TIMESTAMP DEFAULT NOW()
);

-- 时序数据表（TimescaleDB）
CREATE TABLE device_data (
    time TIMESTAMPTZ NOT NULL,
    device_id VARCHAR(20),
    temp FLOAT,
    humi FLOAT,
    airstate INT,
    current FLOAT,
    csq FLOAT,
    air_err INT,
    alarmtemp INT,
    alarmhumi INT
);
SELECT create_hypertable('device_data', 'time');

-- 告警表
CREATE TABLE alarms (
    id SERIAL PRIMARY KEY,
    tenant_id INT REFERENCES tenants(id),
    device_id VARCHAR(20),
    type VARCHAR(20),  -- 'offline', 'illegal_on'
    severity VARCHAR(10),  -- 'high', 'medium', 'low'
    message TEXT,
    is_resolved BOOLEAN DEFAULT false,
    occurred_at TIMESTAMP,
    resolved_at TIMESTAMP
);

-- 协议版本注册表
CREATE TABLE protocol_versions (
    id SERIAL PRIMARY KEY,
    version_code VARCHAR(10),  -- 'V10', 'V20'
    version_number INT,        -- 10, 20
    feature_params JSONB,      -- 特征参数
    param_mappings JSONB,      -- 参数映射
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## 六、实施阶段规划

### Phase 1: 基础设施搭建（预计 2-3 天）

**目标**：搭建 Docker 开发环境，部署基础服务，配置数据持久化

1. 创建项目目录结构
   ```
   bniot/
   ├── volumes/           # 数据卷（容器外持久化）
   │   ├── postgres/
   │   ├── redis/
   │   ├── emqx/
   │   └── backend/
   ├── backend/           # FastAPI 后端源码
   ├── frontend/          # Vue3 前端源码
   ├── docker/            # Docker 配置
   ├── ssl/               # SSL证书
   └── docs/              # 文档
   ```

2. 编写 Docker Compose 配置（含数据卷挂载）
   - PostgreSQL 16 + TimescaleDB（数据卷挂载）
   - Redis 7.x（AOF持久化 + 数据卷挂载）
   - **EMQX 5.5**（数据卷挂载 + SSL证书）
   - FastAPI 后端（日志挂载）
   - Nginx 反向代理

3. 配置 EMQX 5.5
   - 设备认证（test1/test123）
   - Webhook 规则引擎
   - ACL 权限控制
   - 数据持久化配置

4. 初始化数据卷目录
   - 创建 volumes/ 目录结构
   - 设置目录权限
   - 配置自动备份脚本

**交付物**：
- docker-compose.yml（含完整数据卷配置）
- volumes/ 目录结构
- 基础服务可启动运行
- EMQX 5.5 管理控制台可访问

---

### Phase 2: 后端核心模块（预计 5-7 天）

**目标**：实现 MQTT 消息处理、版本检测、数据存储

1. MQTT 消息处理器
   - 设备上线处理（主动探测版本）
   - 数据上送处理（TimescaleDB 存储）
   - 参数解析器（策略模式）
   - 远程控制命令下发

2. 版本检测模块
   - VersionDetector 类
   - ProtocolParser 注册表
   - Redis 缓存管理

3. 设告警检测模块
   - 设备离线告警
   - 非法开启告警

4. REST API 接口
   - 用户认证（JWT）
   - 设备 CRUD
   - 分区管理
   - 数据查询

**交付物**：
- backend/app/ 目录结构
- API 文档（Swagger）
- 单元测试覆盖核心模块

---

### Phase 3: 前端管理后台（预计 7-10 天）

**目标**：实现管理后台界面与交互

1. 基础框架搭建
   - Vue3 + Vite + TypeScript
   - Ant Design Vue 组件库
   - 路由配置

2. 登录与认证
   - 登录页面
   - JWT Token 管理
   - 权限路由

3. 仪表盘页面
   - 设备统计卡片
   - 告警列表
   - 实时数据 WebSocket

4. 设备管理页面
   - 设备列表（表格）
   - 批量操作
   - 参数设置弹窗
   - 设备详情页

5. 分区管理页面
   - 树形分区结构
   - 分区 CRUD

6. 用户管理页面（管理员）

**交付物**：
- frontend/ 完整项目
- 可运行的管理后台
- E2E 测试覆盖核心流程

---

### Phase 4: 报表与分析（预计 3-5 天）

**目标**：实现数据统计与报表功能

1. 报表 API
   - 按时间范围查询
   - 按分区统计
   - 能耗分析计算

2. 前端报表页面
   - 图表组件（ECharts）
   - 时间范围选择
   - 数据导出

---

### Phase 5: 生产部署（预计 1-2 天）

**目标**：部署到腾讯云生产服务器

1. SSL 配置
2. Nginx 反向代理配置
3. 域名绑定
4. 数据库备份策略
5. 监控与日志

---

## 七、风险评估

| 风险 | 级别 | 影响 | 缓解措施 |
|------|------|------|----------|
| EMQX Webhook 性能瓶颈 | HIGH | 高并发设备数据丢失 | 使用消息队列缓冲 |
| 协议版本解析冲突 | MEDIUM | 数据错误显示 | 完善版本检测测试 |
| PostgreSQL 时序数据增长 | MEDIUM | 存储压力 | TimescaleDB 自动压缩 |
| WebSocket 连接稳定性 | LOW | 前端数据延迟 | 心跳机制 + 重连策略 |
| Docker 网络配置 | LOW | 服务互通问题 | 明确网络配置文档 |

---

## 八、复杂度估算

| 模块 | 后端 | 前端 | 测试 | 总计 |
|------|------|------|------|------|
| 基础设施 | 4h | - | 2h | 6h |
| MQTT处理 | 12h | - | 4h | 16h |
| REST API | 8h | - | 3h | 11h |
| 管理后台 | 4h | 20h | 4h | 28h |
| 报表分析 | 6h | 8h | 2h | 16h |
| 生产部署 | 4h | - | 2h | 6h |
| **总计** | **38h** | **28h** | **17h** | **83h** |

预计开发周期：**10-14 个工作日**

---

## 九、版本说明

| 组件 | 版本 | 说明 |
|------|------|------|
| EMQX | **5.5** | 企业级MQTT Broker，支持数据持久化 |
| PostgreSQL | 16 | 主数据库 |
| TimescaleDB | 2.x | PostgreSQL时序扩展 |
| Redis | 7.x | 缓存与持久化 |
| FastAPI | 0.100+ | Python异步框架 |
| Vue | 3.x | 前端框架 |
| Ant Design Vue | 4.x | UI组件库 |

---

**规划已确认，准备实施。**
