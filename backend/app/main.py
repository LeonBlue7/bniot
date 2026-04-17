"""
BNIoT 空调节能管理系统 - FastAPI 后端
"""
from contextlib import asynccontextmanager

import redis.asyncio as redis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.api import api_router
from app.core.config import settings
from app.core.database import async_session_maker
from app.mqtt import get_mqtt_client, init_message_handlers, init_mqtt_client
from app.services import init_version_detector
from app.services.device_monitor import start_device_monitor, stop_device_monitor
from app.services.init_data import init_default_data

# 全局 Redis 客户端引用
_redis_client: redis.Redis = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global _redis_client

    # 启动时初始化
    logger.info("应用启动中...")

    # 初始化 Redis
    _redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    # 将 Redis 客户端存储到应用状态
    app.state.redis_client = _redis_client
    logger.info("Redis 连接成功")

    # 初始化版本检测器
    await init_version_detector(_redis_client)
    logger.info("版本检测器初始化完成")

    # 初始化默认数据（租户和管理员用户）
    await init_default_data()
    logger.info("默认数据初始化完成")

    # 初始化 MQTT 客户端
    init_mqtt_client()
    logger.info("MQTT 客户端初始化完成")

    # 初始化 MQTT 消息处理器
    init_message_handlers(async_session_maker)
    logger.info("MQTT 消息处理器初始化完成")

    # 启动设备在线状态监控
    await start_device_monitor()
    logger.info("设备在线状态监控服务启动完成")

    logger.info("应用启动完成")

    yield

    # 关闭时清理
    logger.info("应用关闭中...")

    # 停止设备在线状态监控
    await stop_device_monitor()
    logger.info("设备在线状态监控服务已停止")

    # 关闭 Redis 连接
    if _redis_client:
        await _redis_client.close()
        logger.info("Redis 连接已关闭")

    # 关闭 MQTT 连接
    mqtt_client = get_mqtt_client()
    if mqtt_client:
        mqtt_client.disconnect()
        logger.info("MQTT 连接已关闭")

    logger.info("应用已关闭")


app = FastAPI(
    title="BNIoT API",
    description="""
空调节能管理系统物联网平台 API

## 功能概述

本 API 提供以下核心功能：

- **认证管理**: 用户登录、JWT 令牌获取、CSRF Token
- **设备管理**: 设备 CRUD、远程控制、历史数据查询
- **分区管理**: 分区 CRUD、层级结构
- **告警管理**: 告警列表、告警处理
- **报表分析**: 数据统计、趋势分析
- **用户管理**: 用户 CRUD、权限控制（仅管理员）
- **操作日志**: 操作审计追踪
- **通知管理**: 通知规则配置、通知记录
- **健康监控**: 系统健康状态检查
- **备份恢复**: 数据备份、数据恢复
- **WebSocket**: 实时数据推送

## 认证方式

使用 JWT Bearer Token 认证：

1. 通过 `/api/auth/login` 获取 Token
2. 在请求头添加 `Authorization: Bearer <token>`
3. Token 有效期 24 小时

## 错误处理

所有错误响应遵循标准格式：

```json
{
  "code": "DEVICE_001",
  "message": "设备不存在",
  "details": {"device_id": 12345},
  "http_status": 404
}
```

## 版本信息

- API 版本: v1.0.0
- 协议版本支持: V10, V20

## 联系方式

如有问题请联系技术支持团队。
""",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
    contact={
        "name": "BNIoT 技术支持",
        "email": "support@jxbonner.cloud",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    servers=[
        {
            "url": "https://www.jxbonner.cloud/api",
            "description": "生产环境"
        },
        {
            "url": "http://localhost:5000/api",
            "description": "开发环境"
        }
    ],
    openapi_tags=[
        {
            "name": "认证",
            "description": "用户认证相关操作，包括登录、获取用户信息、CSRF Token 等。"
        },
        {
            "name": "用户",
            "description": "用户管理操作，包括用户 CRUD、权限控制等。仅系统管理员可访问。"
        },
        {
            "name": "设备",
            "description": "设备管理操作，包括设备 CRUD、远程控制、历史数据查询、批量操作等。"
        },
        {
            "name": "分区",
            "description": "分区管理操作，用于按物理位置组织空调设备。"
        },
        {
            "name": "告警",
            "description": "告警管理操作，包括告警列表查询、告警处理等。"
        },
        {
            "name": "报表",
            "description": "数据报表与分析，包括设备统计、能耗趋势等。"
        },
        {
            "name": "操作日志",
            "description": "操作审计日志，记录用户的操作历史。"
        },
        {
            "name": "通知",
            "description": "通知规则配置与通知记录管理。"
        },
        {
            "name": "健康监控",
            "description": "系统健康状态检查，包括服务状态、数据库连接等。"
        },
        {
            "name": "备份管理",
            "description": "数据库备份操作，支持手动和自动备份。"
        },
        {
            "name": "恢复管理",
            "description": "数据库恢复操作，从备份文件恢复数据。"
        },
        {
            "name": "WebSocket",
            "description": "实时数据推送，包括设备数据更新、告警通知等。"
        },
    ]
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(api_router, prefix="/api")


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "version": "1.0.0"}
