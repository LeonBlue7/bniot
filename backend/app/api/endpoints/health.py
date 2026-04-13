"""
系统健康监控 API 端点

提供系统健康检查、性能监控、诊断工具
"""
import logging
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.auth import get_current_user
from app.models import User

router = APIRouter()
logger = logging.getLogger(__name__)


class HealthStatus(BaseModel):
    """健康状态响应"""
    status: str  # healthy, degraded, unhealthy
    timestamp: str
    components: dict[str, dict]


class SystemMetrics(BaseModel):
    """系统指标响应"""
    database: dict
    redis: dict
    mqtt: dict
    websocket: dict
    uptime: float


@router.get("/health", response_model=HealthStatus)
async def health_check():
    """
    系统健康检查（公开端点）

    检查各组件状态：
    - 数据库连接
    - Redis 连接
    - MQTT 连接
    - WebSocket 连接数
    """
    from app.core.config import settings
    import redis.asyncio as redis
    from app.mqtt.client import get_mqtt_client
    from app.services.websocket_manager import get_connection_manager

    components = {}
    overall_status = "healthy"

    # 检查数据库
    try:
        from app.core.database import async_session_maker
        async with async_session_maker() as db:
            await db.execute(text("SELECT 1"))
        components["database"] = {"status": "healthy", "message": "连接正常"}
    except Exception as e:
        components["database"] = {"status": "unhealthy", "message": str(e)}
        overall_status = "unhealthy"

    # 检查 Redis
    try:
        redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
        await redis_client.ping()
        await redis_client.close()
        components["redis"] = {"status": "healthy", "message": "连接正常"}
    except Exception as e:
        components["redis"] = {"status": "unhealthy", "message": str(e)}
        overall_status = "degraded"

    # 检查 MQTT
    try:
        mqtt_client = get_mqtt_client()
        if mqtt_client and mqtt_client.is_connected():
            components["mqtt"] = {"status": "healthy", "message": "连接正常"}
        else:
            components["mqtt"] = {"status": "degraded", "message": "未连接"}
            if overall_status == "healthy":
                overall_status = "degraded"
    except Exception as e:
        components["mqtt"] = {"status": "unhealthy", "message": str(e)}

    # 检查 WebSocket
    try:
        manager = get_connection_manager()
        connection_count = len(manager.active_connections)
        components["websocket"] = {
            "status": "healthy",
            "message": f"{connection_count} 个活跃连接"
        }
    except Exception as e:
        components["websocket"] = {"status": "degraded", "message": str(e)}

    return HealthStatus(
        status=overall_status,
        timestamp=datetime.now(UTC).isoformat(),
        components=components
    )


@router.get("/metrics", response_model=SystemMetrics)
async def get_system_metrics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    系统性能指标（需认证）

    返回各组件的性能指标：
    - 数据库连接池状态
    - Redis 内存使用
    - MQTT 消息统计
    - WebSocket 连接统计
    """
    from app.core.config import settings
    import redis.asyncio as redis
    from app.mqtt.client import get_mqtt_client
    from app.services.websocket_manager import get_connection_manager

    # 数据库指标
    db_metrics = {}
    try:
        # 查询活跃连接数
        result = await db.execute(
            text("SELECT count(*) FROM pg_stat_activity WHERE datname = current_database()")
        )
        active_connections = result.scalar() or 0
        db_metrics = {
            "active_connections": active_connections,
            "status": "healthy"
        }
    except Exception as e:
        db_metrics = {"status": "error", "message": str(e)}

    # Redis 指标
    redis_metrics = {}
    try:
        redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
        info = await redis_client.info("memory")
        redis_metrics = {
            "used_memory": info.get("used_memory_human", "unknown"),
            "connected_clients": info.get("connected_clients", 0),
            "status": "healthy"
        }
        await redis_client.close()
    except Exception as e:
        redis_metrics = {"status": "error", "message": str(e)}

    # MQTT 指标
    mqtt_metrics = {}
    try:
        mqtt_client = get_mqtt_client()
        mqtt_metrics = {
            "is_connected": mqtt_client.is_connected() if mqtt_client else False,
            "status": "healthy"
        }
    except Exception as e:
        mqtt_metrics = {"status": "error", "message": str(e)}

    # WebSocket 指标
    ws_metrics = {}
    try:
        manager = get_connection_manager()
        ws_metrics = {
            "active_connections": len(manager.active_connections),
            "tenant_count": len(manager.tenant_connections),
            "status": "healthy"
        }
    except Exception as e:
        ws_metrics = {"status": "error", "message": str(e)}

    # 系统运行时间（从应用启动开始）
    from app.main import app
    uptime = 0.0
    if hasattr(app.state, "start_time"):
        uptime = (datetime.now(UTC) - app.state.start_time).total_seconds()

    return SystemMetrics(
        database=db_metrics,
        redis=redis_metrics,
        mqtt=mqtt_metrics,
        websocket=ws_metrics,
        uptime=uptime
    )


@router.get("/diagnostics/database")
async def diagnose_database(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    数据库诊断（需管理员权限）
    """
    if current_user.role != "admin":
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )

    diagnostics = {}

    try:
        # 表大小
        result = await db.execute(
            text("""
                SELECT relname as table_name,
                       pg_size_pretty(pg_total_relation_size(relid)) as total_size
                FROM pg_catalog.pg_statio_user_tables
                ORDER BY pg_total_relation_size(relid) DESC
                LIMIT 10
            """)
        )
        table_sizes = [{"table": row[0], "size": row[1]} for row in result.fetchall()]
        diagnostics["table_sizes"] = table_sizes

        # 索引使用情况
        result = await db.execute(
            text("""
                SELECT indexrelname as index_name,
                       relname as table_name,
                       idx_scan as scans
                FROM pg_catalog.pg_stat_user_indexes
                ORDER BY idx_scan DESC
                LIMIT 10
            """)
        )
        index_usage = [{"index": row[0], "table": row[1], "scans": row[2]} for row in result.fetchall()]
        diagnostics["index_usage"] = index_usage

        # 活跃查询
        result = await db.execute(
            text("""
                SELECT pid, state, query_start
                FROM pg_stat_activity
                WHERE datname = current_database() AND state = 'active'
            """)
        )
        active_queries = [{"pid": row[0], "state": row[1], "query_start": str(row[2])} for row in result.fetchall()]
        diagnostics["active_queries"] = active_queries

    except Exception as e:
        diagnostics["error"] = str(e)

    return diagnostics


@router.get("/diagnostics/redis")
async def diagnose_redis(
    current_user: User = Depends(get_current_user)
):
    """
    Redis 诊断（需管理员权限）
    """
    if current_user.role != "admin":
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )

    from app.core.config import settings
    import redis.asyncio as redis

    diagnostics = {}

    try:
        redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)

        # 基本信息
        info = await redis_client.info()
        diagnostics["server_info"] = {
            "version": info.get("redis_version", "unknown"),
            "uptime_seconds": info.get("uptime_in_seconds", 0),
            "connected_clients": info.get("connected_clients", 0),
        }

        # 内存信息
        memory_info = await redis_client.info("memory")
        diagnostics["memory"] = {
            "used_memory": memory_info.get("used_memory_human", "unknown"),
            "used_memory_peak": memory_info.get("used_memory_peak_human", "unknown"),
            "mem_fragmentation_ratio": memory_info.get("mem_fragmentation_ratio", 0),
        }

        # 统计信息
        stats = await redis_client.info("stats")
        diagnostics["stats"] = {
            "total_commands_processed": stats.get("total_commands_processed", 0),
            "instantaneous_ops_per_sec": stats.get("instantaneous_ops_per_sec", 0),
            "keyspace_hits": stats.get("keyspace_hits", 0),
            "keyspace_misses": stats.get("keyspace_misses", 0),
        }

        # Key 数量
        db_size = await redis_client.dbsize()
        diagnostics["key_count"] = db_size

        await redis_client.close()

    except Exception as e:
        diagnostics["error"] = str(e)

    return diagnostics


@router.get("/diagnostics/devices")
async def diagnose_devices(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    设备诊断（需管理员权限）
    """
    if current_user.role != "admin":
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )

    from sqlalchemy import func, select
    from app.models import Device, Alarm

    diagnostics = {}

    try:
        # 设备统计
        result = await db.execute(
            select(
                func.count(Device.id).label("total"),
                func.count(Device.id).filter(Device.is_online == True).label("online"),
                func.count(Device.id).filter(Device.is_online == False).label("offline"),
            )
        )
        stats = result.one()
        diagnostics["device_stats"] = {
            "total": stats.total,
            "online": stats.online,
            "offline": stats.offline,
            "online_rate": round(stats.online / stats.total * 100, 2) if stats.total > 0 else 0
        }

        # 告警统计
        result = await db.execute(
            select(
                func.count(Alarm.id).label("total"),
                func.count(Alarm.id).filter(Alarm.is_resolved == False).label("unresolved"),
            )
        )
        alarm_stats = result.one()
        diagnostics["alarm_stats"] = {
            "total": alarm_stats.total,
            "unresolved": alarm_stats.unresolved
        }

        # 离线设备列表
        result = await db.execute(
            select(Device.device_id, Device.name, Device.last_seen_at)
            .where(Device.is_online == False)
            .order_by(Device.last_seen_at.desc())
            .limit(10)
        )
        offline_devices = [
            {
                "device_id": row[0],
                "name": row[1],
                "last_seen": row[2].isoformat() if row[2] else None
            }
            for row in result.fetchall()
        ]
        diagnostics["offline_devices"] = offline_devices

    except Exception as e:
        diagnostics["error"] = str(e)

    return diagnostics