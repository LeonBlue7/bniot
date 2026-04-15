# 运行手册

## 服务概述

| 服务 | 端口 | 描述 |
|------|------|------|
| Nginx | 80/443 | 反向代理 |
| Backend | 5000 | FastAPI 服务 |
| PostgreSQL (TimescaleDB) | 5432 | 时序数据库 |
| Redis | 6379 | 缓存/Session |
| EMQX | 1883/8883/8083/8084/18083 | MQTT Broker |

---

## 部署流程

### 一键部署（推荐）

项目已预配置所有必要文件（前端构建产物、SSL证书、生产环境配置），实现一键部署：

```bash
# 克隆项目
git clone git@github.com:LeonBlue7/bniot.git
cd bniot

# 一键启动
docker-compose up -d --build

# 验证服务状态
docker-compose ps
```

部署完成后访问：
- 前端：https://jxbonner.cloud
- API：https://jxbonner.cloud:5000/docs
- EMQX Dashboard：http://服务器IP:18083

> **国内部署优化**: Dockerfile 已配置阿里云镜像源（Debian apt + pip PyPI），国内服务器构建速度更快。

<!-- AUTO-GENERATED: backend/Dockerfile -->
### Dockerfile 镜像源配置

| 配置项 | 镜像源 |
|--------|--------|
| Debian apt | mirrors.aliyun.com |
| pip PyPI | mirrors.aliyun.com/pypi/simple/ |

### 已预提交文件

以下文件已提交到仓库，无需额外配置：

| 文件 | 说明 |
|------|------|
| `.env` | 生产环境配置（数据库密码、JWT密钥等） |
| `ssl/*.pem`, `ssl/*.key` | SSL证书 |
| `frontend/dist/` | 前端构建产物 |

### 首次部署（完整流程）

如果需要全新部署到其他服务器：

```bash
# 1. 拉取代码
git clone <repository-url>
cd bniot

# 2. 构建并启动（一键部署）
docker-compose up -d --build
```

> **安全提示**: `.env` 文件包含敏感密码，已提交到私有仓库。如部署到其他环境，请修改密码。

### 更新部署

```bash
# 拉取最新代码并重启
git pull && docker-compose up -d --build

# 验证服务
docker-compose ps
docker-compose logs -f backend
```

---

## 健康检查

### 服务健康检查

```bash
# 检查所有服务状态
docker-compose ps

# 后端健康检查
curl https://jxbonner.cloud:5000/health

# PostgreSQL 检查
docker-compose exec postgres pg_isready -U bniot

# Redis 检查
docker-compose exec redis redis-cli -a <password> ping

# EMQX 检查
docker-compose exec emqx emqx ctl status
```

### 监控端点

- EMQX Dashboard: `https://jxbonner.cloud:18083`
- API Docs: `https://jxbonner.cloud:5000/docs`

---

## 常见问题

### 1. 后端服务无法启动

**症状**: backend 容器反复重启

**排查**:
```bash
docker-compose logs backend
```

**常见原因**:
- 数据库连接失败 → 检查 PostgreSQL 状态
- Redis 连接失败 → 检查 Redis 状态
- 环境变量未设置 → 检查 .env 文件

### 2. 设备无法连接 MQTT

**症状**: 设备离线，无法收发消息

**排查**:
```bash
# 检查 EMQX 状态
docker-compose logs emqx

# 检查端口监听
docker-compose exec emqx netstat -tlnp | grep 1883

# 检查认证配置
# 登录 EMQX Dashboard 查看认证规则
```

### 3. 前端页面空白

**症状**: 访问页面显示空白

**排查**:
```bash
# 检查前端构建
ls -la frontend/dist/

# 检查 Nginx 配置
docker-compose exec nginx nginx -t
```

### 4. 数据库连接超时

**症状**: API 请求超时或报错

**排查**:
```bash
# 检查数据库连接数
docker-compose exec postgres psql -U bniot -c "SELECT count(*) FROM pg_stat_activity;"

# 检查数据库磁盘空间
docker-compose exec postgres df -h /var/lib/postgresql/data
```

---

## 备份与恢复

### 数据库备份

```bash
# 手动备份
docker-compose exec postgres pg_dump -U bniot bniot > backup_$(date +%Y%m%d).sql

# 自动备份（cron）
0 2 * * * cd /home/leon/projects/bniot && ./docker/backup.sh
```

### 数据库恢复

```bash
# 从备份恢复
cat backup_20260409.sql | docker-compose exec -T postgres psql -U bniot bniot
```

### Redis 备份

```bash
# Redis 自动持久化（RDB + AOF）
# 数据文件: volumes/redis/data/
```

---

## 回滚流程

### 快速回滚

```bash
# 1. 查看最近提交
git log --oneline -5

# 2. 回滚到指定版本
git checkout <commit-hash>

# 3. 重新构建部署
docker-compose up -d --build

# 4. 验证
docker-compose ps
```

### 数据库回滚

```bash
# 1. 停止服务
docker-compose stop backend

# 2. 恢复数据库
cat backup.sql | docker-compose exec -T postgres psql -U bniot bniot

# 3. 重启服务
docker-compose start backend
```

---

## 告警配置

### 告警类型

| 告警 | 级别 | 触发条件 | 处理方式 |
|------|------|----------|----------|
| 设备离线 | HIGH | 设备 5 分钟无心跳 | 检查设备网络/EMQX 状态 |
| 数据库连接失败 | CRITICAL | 无法连接 PostgreSQL | 检查数据库状态/重启服务 |
| Redis 连接失败 | HIGH | 无法连接 Redis | 检查 Redis 状态/重启服务 |
| 磁盘空间不足 | HIGH | 使用率 > 90% | 清理日志/备份数据 |

### 告警通知

- 邮件通知（配置 SMTP）
- Webhook 通知（配置 URL）

---

## 日志查看

```bash
# 查看所有日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f backend
docker-compose logs -f emqx

# 查看最近 100 行
docker-compose logs --tail=100 backend
```

---

## 服务重启

```bash
# 重启所有服务
docker-compose restart

# 重启特定服务
docker-compose restart backend
docker-compose restart emqx

# 完全重建
docker-compose down && docker-compose up -d --build
```