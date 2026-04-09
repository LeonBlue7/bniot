# 环境变量配置文档

<!-- AUTO-GENERATED from .env.example and frontend/.env.example -->

## 后端环境变量

### 数据库配置

| 变量 | 必填 | 描述 | 默认值 | 示例 |
|------|------|------|--------|------|
| `POSTGRES_HOST` | Yes | PostgreSQL 主机地址 | `postgres` | `postgres` |
| `POSTGRES_PORT` | Yes | PostgreSQL 端口 | `5432` | `5432` |
| `POSTGRES_DB` | Yes | 数据库名称 | `bniot` | `bniot` |
| `POSTGRES_USER` | Yes | 数据库用户名 | `bniot` | `bniot` |
| `POSTGRES_PASSWORD` | Yes | 数据库密码 | - | `your_secure_password_here` |

### Redis 配置

| 变量 | 必填 | 描述 | 默认值 | 示例 |
|------|------|------|--------|------|
| `REDIS_HOST` | Yes | Redis 主机地址 | `redis` | `redis` |
| `REDIS_PORT` | Yes | Redis 端口 | `6379` | `6379` |
| `REDIS_PASSWORD` | Yes | Redis 密码 | - | `your_redis_password_here` |

### EMQX 配置

| 变量 | 必填 | 描述 | 默认值 | 示例 |
|------|------|------|--------|------|
| `EMQX_HOST` | Yes | EMQX 主机地址 | `emqx` | `emqx` |
| `EMQX_MQTT_PORT` | No | MQTT TCP 端口 | `1883` | `1883` |
| `EMQX_MQTT_SSL_PORT` | No | MQTT SSL 端口 | `8883` | `8883` |
| `EMQX_WS_PORT` | No | WebSocket 端口 | `8083` | `8083` |
| `EMQX_WSS_PORT` | No | WebSocket SSL 端口 | `8084` | `8084` |
| `EMQX_DASHBOARD_PORT` | No | Dashboard 端口 | `18083` | `18083` |
| `EMQX_DASHBOARD_USER` | No | Dashboard 用户名 | `admin` | `admin` |
| `EMQX_DASHBOARD_PASSWORD` | No | Dashboard 密码 | `public` | `public` |

### MQTT 设备认证

> ⚠️ **注意**: 设备端嵌入式程序已硬编码认证信息，无法修改。

| 变量 | 必填 | 描述 | 默认值 |
|------|------|------|--------|
| `MQTT_USERNAME` | Yes | 设备 MQTT 用户名 | `test1` |
| `MQTT_PASSWORD` | Yes | 设备 MQTT 密码 | `test123` |

### 后端服务配置

| 变量 | 必填 | 描述 | 默认值 | 示例 |
|------|------|------|--------|------|
| `BACKEND_HOST` | No | 后端服务主机 | `0.0.0.0` | `0.0.0.0` |
| `BACKEND_PORT` | No | 后端服务端口 | `5000` | `5000` |
| `BACKEND_DEBUG` | No | 调试模式开关 | `false` | `true`/`false` |
| `JWT_SECRET` | Yes | JWT 签名密钥 | - | `your_jwt_secret_here` |
| `JWT_EXPIRE_HOURS` | No | JWT 过期时间(小时) | `24` | `24` |

### 小程序配置（后续迭代）

| 变量 | 必填 | 描述 | 默认值 |
|------|------|------|--------|
| `WECHAT_APPID` | No | 微信小程序 AppID | `wx9fcb70ddbcf43ecd` |
| `WECHAT_SECRET` | No | 微信小程序 Secret | - |

### 域名配置

| 变量 | 必填 | 描述 | 示例 |
|------|------|------|------|
| `DOMAIN` | Yes | 生产域名 | `jxbonner.cloud` |
| `SSL_CERT_PATH` | Yes | SSL 证书路径 | `./ssl/fullchain.pem` |
| `SSL_KEY_PATH` | Yes | SSL 私钥路径 | `./ssl/privkey.pem` |

---

## 前端环境变量

> 位置: `frontend/.env.example`

### API 配置

| 变量 | 必填 | 描述 | 示例 |
|------|------|------|------|
| `VITE_API_BASE_URL` | Yes | API 基础 URL | `/api`（开发）/ `https://host/api`（生产） |

### WebSocket 配置

| 变量 | 必填 | 描述 | 示例 |
|------|------|------|------|
| `VITE_WS_URL` | Yes | WebSocket URL | `wss://www.jxbonner.cloud:8084` |

### 应用信息

| 变量 | 必填 | 描述 | 默认值 |
|------|------|------|--------|
| `VITE_APP_TITLE` | No | 应用标题 | `BNIoT - 空调节能管理系统` |
| `VITE_APP_VERSION` | No | 应用版本 | `1.0.0` |

### 开发配置

| 变量 | 必填 | 描述 | 默认值 |
|------|------|------|--------|
| `VITE_DEBUG` | No | 调试模式 | `false` |
| `VITE_ENABLE_MOCK` | No | 启用 Mock 数据 | `false` |

### 用户界面

| 变量 | 必填 | 描述 | 默认值 |
|------|------|------|--------|
| `VITE_LOCALE` | No | 界面语言 | `zh-CN` |
| `VITE_THEME_PRIMARY` | No | 主题主色 | `#1890ff` |
| `VITE_THEME_MODE` | No | 主题模式 | `light` |

---

## 配置步骤

### 1. 后端配置

```bash
# 复制示例文件
cp .env.example .env

# 编辑必填变量（标记为 Yes 的项）
nano .env
```

### 2. 前端配置

```bash
# 复制示例文件
cd frontend
cp .env.example .env.local

# 编辑配置
nano .env.local
```

### 3. 启动服务

```bash
# 启动所有服务
docker-compose up -d

# 验证服务状态
docker-compose ps
```

---

## 安全注意事项

1. **必填变量**: 所有标记为 `Yes` 的变量必须在生产环境中配置
2. **密码强度**: 使用强密码（至少 16 位，包含大小写字母、数字、特殊字符）
3. **JWT 密钥**: 使用随机生成的强密钥（至少 32 位）
4. **敏感信息**: 不要将 `.env` 文件提交到版本控制
5. **前端变量**: 所有 `VITE_` 前缀变量会打包到前端代码，不要存储敏感信息