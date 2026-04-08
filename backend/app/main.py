"""
BNIoT 空调节能管理系统 - FastAPI 后端
"""
import redis.asyncio as redis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from loguru import logger

from app.core.config import settings
from app.core.database import async_session_maker, init_db
from app.api import api_router
from app.services import init_version_detector
from app.mqtt import init_mqtt_client, init_message_handlers, get_mqtt_client


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

    # 初始化 MQTT 客户端
    init_mqtt_client()
    logger.info("MQTT 客户端初始化完成")

    # 初始化 MQTT 消息处理器
    init_message_handlers(async_session_maker)
    logger.info("MQTT 消息处理器初始化完成")

    logger.info("应用启动完成")

    yield

    # 关闭时清理
    logger.info("应用关闭中...")

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
    description="空调节能管理系统物联网平台 API",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan
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