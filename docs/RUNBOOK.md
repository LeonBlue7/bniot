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

## 一键部署

### 快速部署脚本（推荐）

项目提供一键部署脚本，自动完成环境检查、前端构建、服务部署和健康验证：

```bash
# 克隆项目
git clone <repository-url>
cd bniot

# 执行一键部署脚本
./scripts/deploy.sh
```

部署脚本会自动：
1. ✅ 检查 Docker 环境
2. ✅ 检查并生成环境变量配置
3. ✅ 检查 SSL 证书
4. ✅ 构建前端生产版本
5. ✅ 部署 Docker 服务
6. ✅ 执行健康检查
7. ✅ 自动创建默认管理员用户

### 手动部署

```bash
# 1. 配置环境变量
cp .env.example .env
vi .env  # 编辑配置

# 2. 构建前端
cd frontend && npm install && npm run build && cd ..

# 3. 启动服务
docker-compose up -d --build

# 4. 检查服务状态
docker-compose ps
```

### 部署完成后访问

- 前端：https://www.jxbonner.cloud
- API 文档：https://www.jxbonner.cloud/api/docs
- EMQX Dashboard：http://服务器IP:18083

**默认登录凭据**：
- 用户名：`admin`
- 密码：`admin123`（可通过 `DEFAULT_ADMIN_PASSWORD` 环境变量自定义）

> ⚠️ **安全提示**: 请在生产环境修改默认密码！

---

## 常见部署问题与解决方案

### 问题 1: 登录 API 返回 500 错误

**症状**: 登录时显示 "Request failed with status code 500"

**原因**: passlib 1.7.4 与 bcrypt 4.x 版本不兼容

**解决方案**: 已在 `requirements.txt` 中锁定 bcrypt 版本为 3.x

```bash
# 重新构建后端镜像
docker-compose build backend
docker-compose up -d backend
```

### 问题 2: 数据库密码认证失败

**症状**: 后端日志显示 `password authentication failed for user "bniot"`

**原因**: 数据库用户密码与 `.env` 中的密码不一致

**解决方案**: 使用诊断脚本重置密码

```bash
./scripts/diagnose.sh password
```

或手动执行：

```bash
source .env
docker exec -it bniot-postgres psql -U bniot -d bniot -c \
  "ALTER USER bniot WITH PASSWORD '${POSTGRES_PASSWORD}';"
```

### 问题 3: 默认用户不存在

**症状**: 登录返回 401 "用户名或密码错误"，数据库用户表为空

**原因**: 数据库初始化脚本未执行（数据目录已存在）

**解决方案**: 使用诊断脚本创建用户

```bash
./scripts/diagnose.sh user
```

**自动修复**: 后端启动时会自动检查并创建默认用户

### 问题 4: 登录速率限制触发

**症状**: 登录返回 429 "登录尝试过于频繁"

**原因**: 多次登录失败触发 Redis 速率限制（5 次/5 分钟）

**解决方案**: 清除速率限制

```bash
./scripts/diagnose.sh rate-limit
```

或手动执行：

```bash
source .env
docker exec -it bniot-redis redis-cli -a "${REDIS_PASSWORD}" \
  KEYS "rate_limit:*" | xargs -I {} docker exec -i bniot-redis \
  redis-cli -a "${REDIS_PASSWORD}" DEL "{}"
```

---

## 诊断工具

### 使用诊断脚本

```bash
# 查看帮助
./scripts/diagnose.sh help

# 检查所有服务健康状态
./scripts/diagnose.sh health

# 清除登录速率限制
./scripts/diagnose.sh rate-limit

# 检查并创建默认用户
./scripts/diagnose.sh user

# 重置数据库密码
./scripts/diagnose.sh password

# 执行所有诊断和修复
./scripts/diagnose.sh all
```

### 手动健康检查

```bash
# 后端健康检查
curl https://jxbonner.cloud/health

# PostgreSQL 检查
docker exec bniot-postgres pg_isready -U bniot

# Redis 检查
source .env
docker exec bniot-redis redis-cli -a "${REDIS_PASSWORD}" ping

# EMQX 检查
docker exec bniot-emqx emqx ctl status
```

---

## 更新部署

```bash
# 拉取最新代码
git pull origin main

# 重新构建并部署
docker-compose build backend
docker-compose up -d backend

# 验证服务
docker-compose ps
docker logs bniot-backend --tail 20
```

---

## 备份与恢复

### 数据库备份

```bash
# 手动备份
docker exec bniot-postgres pg_dump -U bniot bniot > backup_$(date +%Y%m%d).sql

# 自动备份（cron）
0 2 * * * cd /opt/bniot && docker exec bniot-postgres pg_dump -U bniot bniot > /opt/bniot/backups/backup_$(date +\%Y\%m\%d).sql
```

### 数据库恢复

```bash
# 从备份恢复
cat backup_20260415.sql | docker exec -i bniot-postgres psql -U bniot bniot
```

---

## 服务管理

### 启动/停止/重启

```bash
# 启动所有服务
docker-compose up -d

# 停止所有服务
docker-compose down

# 重启所有服务
docker-compose restart

# 重启单个服务
docker-compose restart backend
docker-compose restart nginx
```

### 查看日志

```bash
# 查看所有日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f backend
docker-compose logs -f emqx

# 查看最近 50 行
docker logs bniot-backend --tail 50
```

---

## 安全配置清单

| 配置项 | 要求 | 检查方法 |
|--------|------|----------|
| POSTGRES_PASSWORD | 强密码，非示例值 | 检查 .env |
| REDIS_PASSWORD | 强密码，非示例值 | 检查 .env |
| JWT_SECRET | 随机字符串，至少 32 位 | 检查 .env |
| DEFAULT_ADMIN_PASSWORD | 生产环境修改默认值 | 部署后修改 |
| SSL 证书 | 有效证书文件 | 检查 ssl/ 目录 |

---

## 回滚流程

```bash
# 1. 查看最近提交
git log --oneline -5

# 2. 回滚到指定版本
git checkout <commit-hash>

# 3. 重新构建部署
docker-compose build backend
docker-compose up -d backend

# 4. 验证
docker-compose ps
docker logs bniot-backend --tail 20
```

---

## 监控端点

| 端点 | URL | 说明 |
|------|-----|------|
| 后端健康 | `/health` | 服务状态 |
| API 文档 | `/api/docs` | Swagger UI |
| EMQX Dashboard | `:18083` | MQTT 管理 |

---

## 联系支持

遇到问题请按以下顺序排查：
1. 使用诊断脚本 `./scripts/diagnose.sh all`
2. 查看服务日志 `docker logs bniot-backend --tail 50`
3. 检查环境变量配置
4. 联系技术支持