"""
设备 API 端点
使用新的权限系统进行访问控制
包含基于分区授权的设备访问过滤

注意：批量操作路由必须在/{device_id}路由之前定义，否则batch会被当作device_id处理
"""
import json
import logging
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import outerjoin, selectinload

from app.core.database import get_db
from app.models import Alarm, Device, DeviceData, User, Zone
from app.models.models import ZoneTenant
from app.mqtt import get_mqtt_client
from app.schemas import (
    BatchControlRequest,
    BatchDeleteRequest,
    BatchMoveZoneRequest,
    BatchOperationResponse,
    DashboardStats,
    DeviceCreate,
    DeviceDetailResponse,
    DeviceEventsResponse,
    DeviceListItemResponse,
    DeviceListResponse,
    DeviceResponse,
    DeviceRuntimeResponse,
    DeviceUpdate,
    Message,
)
from app.services.auth import get_current_user
from app.services.permissions import Permission, require_permission
from app.services.operation_log import OperationLogService, ActionType, ResourceType
from app.services.runtime import RuntimeService

router = APIRouter()
logger = logging.getLogger(__name__)


# ============ 统计和列表（无路径参数） ============

@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.DEVICE_READ))
):
    """获取仪表盘统计数据

    权限规则：
    - 系统管理员（admin）：可以看到租户内所有设备统计
    - 观察员/操作员：只能看到授权分区内的设备统计
    - 无授权分区：返回所有统计为0

    跨租户授权场景：
    - 分区可以授权给其他租户查看
    - 授权分区内的设备对被授权租户可见
    """
    # 分区权限过滤：非管理员只能看到已授权分区内的设备
    authorized_zone_ids = None
    if current_user.role != "admin":
        # 查询用户租户被授权的分区ID列表
        authorized_zones_result = await db.execute(
            select(ZoneTenant.zone_id).where(
                ZoneTenant.tenant_id == current_user.tenant_id
            )
        )
        authorized_zone_ids = [row[0] for row in authorized_zones_result.all()]

        # 如果没有授权分区，返回所有统计为0
        if not authorized_zone_ids:
            return DashboardStats(
                total_devices=0,
                online_devices=0,
                offline_devices=0,
                total_alarms=0,
                unresolved_alarms=0
            )

    # 构建设备查询条件
    if authorized_zone_ids is not None:
        # 非管理员：只统计授权分区内的设备（跨租户可见）
        # 设备可能属于分区创建者的租户，但被授权给其他租户查看
        device_conditions = [Device.zone_id.in_(authorized_zone_ids)]
    else:
        # 管理员：统计自己租户内所有设备
        device_conditions = [Device.tenant_id == current_user.tenant_id]

    # 设备统计
    total_result = await db.execute(
        select(func.count(Device.id)).where(and_(*device_conditions))
    )
    total_devices = total_result.scalar() or 0

    online_result = await db.execute(
        select(func.count(Device.id)).where(
            and_(
                *device_conditions,
                Device.is_online
            )
        )
    )
    online_devices = online_result.scalar() or 0

    # 告警统计 - 需要根据设备所属分区过滤
    if authorized_zone_ids is not None:
        # 非管理员：先获取授权分区内的设备ID列表
        devices_in_zones_result = await db.execute(
            select(Device.device_id).where(and_(*device_conditions))
        )
        device_ids_in_zones = [row[0] for row in devices_in_zones_result.all()]

        if device_ids_in_zones:
            # 告警过滤条件：只统计这些设备的告警
            alarm_conditions = [Alarm.device_id.in_(device_ids_in_zones)]
        else:
            # 无设备时返回0告警
            return DashboardStats(
                total_devices=total_devices,
                online_devices=online_devices,
                offline_devices=total_devices - online_devices,
                total_alarms=0,
                unresolved_alarms=0
            )
    else:
        # 管理员：统计租户内所有告警（不依赖设备过滤）
        alarm_conditions = [Alarm.tenant_id == current_user.tenant_id]

    total_alarms_result = await db.execute(
        select(func.count(Alarm.id)).where(and_(*alarm_conditions))
    )
    total_alarms = total_alarms_result.scalar() or 0

    unresolved_alarms_result = await db.execute(
        select(func.count(Alarm.id)).where(
            and_(
                *alarm_conditions,
                Alarm.is_resolved == False
            )
        )
    )
    unresolved_alarms = unresolved_alarms_result.scalar() or 0

    return DashboardStats(
        total_devices=total_devices,
        online_devices=online_devices,
        offline_devices=total_devices - online_devices,
        total_alarms=total_alarms,
        unresolved_alarms=unresolved_alarms
    )


@router.get("", response_model=DeviceListResponse)
async def list_devices(
    zone_id: int | None = None,
    is_online: bool | None = None,
    keyword: str | None = None,
    protocol_version: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.DEVICE_READ))
):
    """获取设备列表，包含实时数据和分区信息

    权限规则：
    - 系统管理员（admin）：可以看到租户内所有设备
    - 观察员/操作员：只能看到所属租户授权分区内的设备
    - 未分区的设备：仅管理员可见
    """
    # 处理空字符串 keyword（前端可能传递 keyword=""）
    if keyword == "":
        keyword = None

    # 分区权限过滤：非管理员只能看到已授权分区内的设备
    authorized_zone_ids = None
    if current_user.role != "admin":
        # 查询用户租户被授权的分区ID列表
        authorized_zones_result = await db.execute(
            select(ZoneTenant.zone_id).where(
                ZoneTenant.tenant_id == current_user.tenant_id
            )
        )
        authorized_zone_ids = [row[0] for row in authorized_zones_result.all()]

        # 如果没有授权分区，返回空列表
        if not authorized_zone_ids:
            return DeviceListResponse(items=[], total=0, skip=skip, limit=limit)

    # 使用 DISTINCT ON 获取每个设备的最新数据（PostgreSQL 特有）
    # 先按 device_id 分组，取时间最新的那条记录
    latest_data_query = (
        select(
            DeviceData.device_id,
            DeviceData.temp,
            DeviceData.humi,
            DeviceData.alarmtemp,
            DeviceData.time
        )
        .where(DeviceData.tenant_id == current_user.tenant_id)
        .distinct(DeviceData.device_id)
        .order_by(DeviceData.device_id, DeviceData.time.desc())
        .subquery()
    )

    # 基础查询条件（用于计数和查询）
    base_conditions = [Device.tenant_id == current_user.tenant_id]

    # 分区权限过滤
    if authorized_zone_ids is not None:
        # 非管理员：只能看到授权分区内的设备
        base_conditions.append(Device.zone_id.in_(authorized_zone_ids))
    elif zone_id:
        # 管理员可以按指定分区过滤
        base_conditions.append(Device.zone_id == zone_id)

    if is_online is not None:
        base_conditions.append(Device.is_online == is_online)
    if protocol_version:
        base_conditions.append(Device.protocol_version == protocol_version)

    # 查询总数
    if keyword:
        # 关键字搜索需要 JOIN Zone
        count_query = (
            select(func.count(Device.id))
            .join(Zone, Device.zone_id == Zone.id, isouter=True)
            .where(and_(*base_conditions))
            .where(
                (Device.name.ilike(f"%{keyword}%")) |
                (Device.device_id.ilike(f"%{keyword}%")) |
                (Device.sim_card.ilike(f"%{keyword}%")) |
                (Device.firmware_version.ilike(f"%{keyword}%")) |
                (Zone.name.ilike(f"%{keyword}%"))
            )
        )
    else:
        count_query = select(func.count(Device.id)).where(and_(*base_conditions))
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # 数据查询 - 使用 join() 方法 + isouter=True 构建 LEFT JOIN
    query = (
        select(
            Device.id,
            Device.tenant_id,
            Device.device_id,
            Device.name,
            Device.zone_id,
            Device.protocol_version,
            Device.is_online,
            Device.last_seen_at,
            Device.created_at,
            Zone.name.label("zone_name"),
            latest_data_query.c.temp,
            latest_data_query.c.humi,
            latest_data_query.c.alarmtemp,
        )
        .join(Zone, Device.zone_id == Zone.id, isouter=True)
        .join(latest_data_query, Device.device_id == latest_data_query.c.device_id, isouter=True)
        .where(and_(*base_conditions))
    )

    if keyword:
        query = query.where(
            (Device.name.ilike(f"%{keyword}%")) |
            (Device.device_id.ilike(f"%{keyword}%")) |
            (Device.sim_card.ilike(f"%{keyword}%")) |
            (Device.firmware_version.ilike(f"%{keyword}%")) |
            (Zone.name.ilike(f"%{keyword}%"))
        )

    query = query.offset(skip).limit(limit).order_by(Device.id.desc())
    result = await db.execute(query)

    # 将结果转换为DeviceListItemResponse格式
    rows = result.all()
    devices = []
    for row in rows:
        devices.append({
            "id": row.id,
            "tenant_id": row.tenant_id,
            "device_id": row.device_id,
            "name": row.name,
            "zone_id": row.zone_id,
            "protocol_version": row.protocol_version,
            "temp": row.temp,
            "humi": row.humi,
            "alarmtemp": row.alarmtemp,
            "zone_name": row.zone_name,
            "is_online": row.is_online,
            "last_seen_at": row.last_seen_at,
            "created_at": row.created_at,
        })
    return DeviceListResponse(
        items=devices,
        total=total,
        skip=skip,
        limit=limit
    )


@router.post("", response_model=DeviceResponse, status_code=status.HTTP_201_CREATED)
async def create_device(
    device_in: DeviceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.DEVICE_CREATE))
):
    """创建设备"""
    # 检查 device_id 是否已存在（跨租户检查）
    result = await db.execute(
        select(Device).where(Device.device_id == device_in.device_id)
    )
    existing_device = result.scalar_one_or_none()
    if existing_device:
        # 区分错误信息：同一租户 vs 其他租户
        if existing_device.tenant_id == current_user.tenant_id:
            raise HTTPException(status_code=400, detail="设备ID已存在")
        else:
            raise HTTPException(
                status_code=400,
                detail="设备ID已被其他租户使用，请联系管理员处理"
            )

    device = Device(
        tenant_id=current_user.tenant_id,
        device_id=device_in.device_id,
        name=device_in.name,
        zone_id=device_in.zone_id,
    )
    db.add(device)
    await db.commit()
    await db.refresh(device)
    return device


# ============ 批量操作（必须在/{device_id}之前） ============

@router.post("/batch/control", response_model=BatchOperationResponse)
async def batch_control_devices(
    request: Request,
    batch_req: BatchControlRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.DEVICE_CONTROL))
):
    """
    批量控制设备（开机/关机）
    """
    log_service = OperationLogService()
    success_count = 0
    failed_details = []

    for device_id in batch_req.device_ids:
        result = await db.execute(
            select(Device).where(
                Device.id == device_id,
                Device.tenant_id == current_user.tenant_id
            )
        )
        device = result.scalar_one_or_none()

        if not device:
            failed_details.append({
                "device_id": device_id,
                "reason": "设备不存在或无权访问"
            })
            continue

        topic = f"/down/{device.device_id}/ctr"
        payload = json.dumps({
            "airstate": batch_req.airstate,
            "timestamp": str(int(datetime.now().timestamp()))
        })

        mqtt = get_mqtt_client()
        if mqtt.publish(topic, payload):
            success_count += 1
        else:
            failed_details.append({
                "device_id": device_id,
                "reason": "MQTT发送失败"
            })

    await log_service.log(
        db,
        user=current_user,
        action=ActionType.DEVICE_BATCH_CONTROL,
        resource_type=ResourceType.DEVICE,
        details={
            "device_ids": batch_req.device_ids,
            "airstate": batch_req.airstate,
            "success_count": success_count,
            "failed_count": len(failed_details)
        },
        ip_address=request.client.host if request.client else None
    )
    await db.commit()

    return BatchOperationResponse(
        success_count=success_count,
        failed_count=len(failed_details),
        failed_details=failed_details
    )


@router.post("/batch/delete", response_model=BatchOperationResponse)
async def batch_delete_devices(
    request: Request,
    batch_req: BatchDeleteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.DEVICE_DELETE))
):
    """批量删除设备"""
    log_service = OperationLogService()
    deleted_count = 0
    failed_details = []

    for device_id in batch_req.device_ids:
        result = await db.execute(
            select(Device).where(
                Device.id == device_id,
                Device.tenant_id == current_user.tenant_id
            )
        )
        device = result.scalar_one_or_none()

        if not device:
            failed_details.append({
                "device_id": device_id,
                "reason": "设备不存在或无权访问"
            })
            continue

        await log_service.log(
            db,
            user=current_user,
            action=ActionType.DEVICE_DELETE,
            resource_type=ResourceType.DEVICE,
            resource_id=device.device_id,
            details={"name": device.name, "device_id": device.device_id},
            ip_address=request.client.host if request.client else None
        )

        await db.delete(device)
        deleted_count += 1

    await log_service.log(
        db,
        user=current_user,
        action=ActionType.DEVICE_BATCH_DELETE,
        resource_type=ResourceType.DEVICE,
        details={
            "device_ids": batch_req.device_ids,
            "deleted_count": deleted_count,
            "failed_count": len(failed_details)
        },
        ip_address=request.client.host if request.client else None
    )
    await db.commit()

    return BatchOperationResponse(
        success_count=deleted_count,
        failed_count=len(failed_details),
        failed_details=failed_details
    )


@router.post("/batch/move-zone", response_model=BatchOperationResponse)
async def batch_move_zone(
    request: Request,
    batch_req: BatchMoveZoneRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.DEVICE_UPDATE))
):
    """批量迁移设备分区"""
    log_service = OperationLogService()
    moved_count = 0
    failed_details = []

    if batch_req.zone_id is not None:
        zone_result = await db.execute(
            select(Zone).where(
                Zone.id == batch_req.zone_id,
                Zone.tenant_id == current_user.tenant_id
            )
        )
        target_zone = zone_result.scalar_one_or_none()
        if not target_zone:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="目标分区不存在或无权访问"
            )

    for device_id in batch_req.device_ids:
        result = await db.execute(
            select(Device).where(
                Device.id == device_id,
                Device.tenant_id == current_user.tenant_id
            )
        )
        device = result.scalar_one_or_none()

        if not device:
            failed_details.append({
                "device_id": device_id,
                "reason": "设备不存在或无权访问"
            })
            continue

        old_zone_id = device.zone_id
        device.zone_id = batch_req.zone_id
        moved_count += 1

        await log_service.log(
            db,
            user=current_user,
            action="move_zone",
            resource_type=ResourceType.DEVICE,
            resource_id=device.device_id,
            details={
                "name": device.name,
                "old_zone_id": old_zone_id,
                "new_zone_id": batch_req.zone_id
            },
            ip_address=request.client.host if request.client else None
        )

    await db.commit()

    return BatchOperationResponse(
        success_count=moved_count,
        failed_count=len(failed_details),
        failed_details=failed_details
    )


@router.post("/batch/detect-version", response_model=BatchOperationResponse)
async def batch_detect_version(
    request: Request,
    batch_req: BatchDeleteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.DEVICE_CONTROL))
):
    """
    批量触发设备版本检测

    发送 getparam 命令到指定在线设备，触发协议版本重新检测
    离线设备无法触发检测
    """
    log_service = OperationLogService()
    success_count = 0
    failed_details = []

    mqtt = get_mqtt_client()

    for device_id in batch_req.device_ids:
        result = await db.execute(
            select(Device).where(
                Device.id == device_id,
                Device.tenant_id == current_user.tenant_id
            )
        )
        device = result.scalar_one_or_none()

        if not device:
            failed_details.append({
                "device_id": device_id,
                "reason": "设备不存在或无权访问"
            })
            continue

        if not device.is_online:
            failed_details.append({
                "device_id": device_id,
                "reason": "设备离线，无法触发检测"
            })
            continue

        # 发送 getparam 命令触发版本检测
        topic = f"/down/{device.device_id}/getparam"
        payload = json.dumps({"timestamp": str(int(datetime.now(UTC).timestamp()))})

        if mqtt.publish(topic, payload):
            success_count += 1
        else:
            failed_details.append({
                "device_id": device_id,
                "reason": "MQTT发送失败"
            })

    await log_service.log(
        db,
        user=current_user,
        action=ActionType.DEVICE_BATCH_CONTROL,
        resource_type=ResourceType.DEVICE,
        details={
            "device_ids": batch_req.device_ids,
            "operation": "detect_version",
            "success_count": success_count,
            "failed_count": len(failed_details)
        },
        ip_address=request.client.host if request.client else None
    )
    await db.commit()

    return BatchOperationResponse(
        success_count=success_count,
        failed_count=len(failed_details),
        failed_details=failed_details
    )


# ============ 单设备操作（带路径参数） ============

@router.get("/{device_id}", response_model=DeviceDetailResponse)
async def get_device(
    device_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.DEVICE_READ))
):
    """获取设备详情（包含实时数据、分区信息、运行统计）"""
    # 查询设备基础信息，LEFT JOIN Zone
    query = (
        select(
            Device.id,
            Device.tenant_id,
            Device.device_id,
            Device.name,
            Device.zone_id,
            Device.protocol_version,
            Device.sim_card,
            Device.is_online,
            Device.last_seen_at,
            Device.settings,
            Device.created_at,
            Device.firmware_version,
            Zone.name.label("zone_name"),
        )
        .outerjoin(Zone, Device.zone_id == Zone.id)
        .where(
            Device.id == device_id,
            Device.tenant_id == current_user.tenant_id
        )
    )
    result = await db.execute(query)
    row = result.one_or_none()

    if not row:
        raise HTTPException(status_code=404, detail="设备不存在")

    # 获取最新设备数据
    latest_data_query = (
        select(DeviceData)
        .where(DeviceData.device_id == row.device_id)
        .order_by(DeviceData.time.desc())
        .limit(1)
    )
    latest_data_result = await db.execute(latest_data_query)
    latest_data = latest_data_result.scalar_one_or_none()

    # 获取运行时间统计（传入 tenant_id 确保租户隔离）
    runtime_service = RuntimeService(db, tenant_id=current_user.tenant_id)
    supports_runtime = await runtime_service.supports_runtime(row.device_id)

    if supports_runtime:
        today_runtime = await runtime_service.get_today_runtime(
            row.device_id, last_seen_at=row.last_seen_at
        )
        month_runtime = await runtime_service.get_month_runtime(
            row.device_id, last_seen_at=row.last_seen_at
        )
    else:
        today_runtime = None
        month_runtime = None

    # 构建响应
    response = {
        "id": row.id,
        "tenant_id": row.tenant_id,
        "device_id": row.device_id,
        "name": row.name,
        "zone_id": row.zone_id,
        "protocol_version": row.protocol_version,
        "sim_card": row.sim_card,
        "is_online": row.is_online,
        "last_seen_at": row.last_seen_at,
        "settings": row.settings,
        "created_at": row.created_at,
        "zone_name": row.zone_name,
        "firmware_version": row.firmware_version,
        # 从最新数据获取
        "temp": latest_data.temp if latest_data else None,
        "humi": latest_data.humi if latest_data else None,
        "csq": latest_data.csq if latest_data else None,
        "alarmtemp": latest_data.alarmtemp if latest_data else None,
        "alarmhumi": latest_data.alarmhumi if latest_data else None,
        "air_err": latest_data.air_err if latest_data else None,
        "airstate": latest_data.airstate if latest_data else None,
        "current": latest_data.current / 1000.0 if latest_data and latest_data.current else None,
        # 运行时间统计
        "supports_runtime": supports_runtime,
        "today_runtime": today_runtime,
        "month_runtime": month_runtime,
    }

    return response


@router.put("/{device_id}", response_model=DeviceResponse)
async def update_device(
    device_id: int,
    device_in: DeviceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.DEVICE_UPDATE))
):
    """更新设备"""
    result = await db.execute(
        select(Device).where(
            Device.id == device_id,
            Device.tenant_id == current_user.tenant_id
        )
    )
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")

    update_data = device_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(device, field, value)

    await db.commit()
    await db.refresh(device)
    return device


@router.delete("/{device_id}", response_model=Message)
async def delete_device(
    device_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.DEVICE_DELETE))
):
    """删除设备"""
    result = await db.execute(
        select(Device).where(
            Device.id == device_id,
            Device.tenant_id == current_user.tenant_id
        )
    )
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")

    await db.delete(device)
    await db.commit()
    return Message(message="设备已删除")


@router.post("/{device_id}/control", response_model=Message)
async def control_device(
    device_id: int,
    airstate: int = Query(..., ge=0, le=1, description="0关机，1开机"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.DEVICE_CONTROL))
):
    """远程控制设备"""
    result = await db.execute(
        select(Device).where(
            Device.id == device_id,
            Device.tenant_id == current_user.tenant_id
        )
    )
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")

    topic = f"/down/{device.device_id}/ctr"
    payload = json.dumps({
        "airstate": airstate,
        "timestamp": str(int(datetime.now().timestamp()))
    })

    mqtt = get_mqtt_client()
    if mqtt.publish(topic, payload):
        return Message(message="控制命令已发送")
    else:
        raise HTTPException(status_code=500, detail="发送控制命令失败")


@router.get("/{device_id}/data", response_model=list[dict])
async def get_device_data(
    device_id: int,
    hours: int = Query(24, ge=1, le=168, description="查询最近N小时数据"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.DEVICE_READ))
):
    """获取设备历史数据"""
    result = await db.execute(
        select(Device).where(
            Device.id == device_id,
            Device.tenant_id == current_user.tenant_id
        )
    )
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")

    start_time = datetime.now(UTC) - timedelta(hours=hours)

    data_result = await db.execute(
        select(DeviceData)
        .where(DeviceData.device_id == device.device_id)
        .where(DeviceData.time >= start_time)
        .order_by(DeviceData.time.desc())
        .limit(1000)
    )
    return [
        {
            "id": d.id,
            "time": d.time,
            "device_id": d.device_id,
            "tenant_id": d.tenant_id,
            "temp": d.temp,
            "humi": d.humi,
            "airstate": d.airstate,
            "current": d.current / 1000.0 if d.current else None,
            "csq": d.csq,
            "air_err": d.air_err,
            "alarmtemp": d.alarmtemp,
            "alarmhumi": d.alarmhumi,
        }
        for d in data_result.scalars().all()
    ]


@router.get("/{device_id}/events", response_model=DeviceEventsResponse)
async def get_device_events(
    device_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.DEVICE_READ))
):
    """
    获取设备开关机事件记录

    返回:
    - supported: 是否支持空调状态监控
    - message: 不支持时的提示消息
    - events: 事件列表 [{time, action, duration}]
    - total: 总数量
    - page: 当前页
    - page_size: 每页数量
    """
    result = await db.execute(
        select(Device).where(
            Device.id == device_id,
            Device.tenant_id == current_user.tenant_id
        )
    )
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")

    # 使用运行时间服务获取事件记录（传入 tenant_id 确保租户隔离）
    service = RuntimeService(db, tenant_id=current_user.tenant_id)
    events_data = await service.get_runtime_events(
        device.device_id,
        page=page,
        page_size=page_size
    )

    return events_data


@router.get("/{device_id}/runtime", response_model=DeviceRuntimeResponse)
async def get_device_runtime(
    device_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.DEVICE_READ))
):
    """
    获取设备运行时间统计

    返回:
    - supported: 是否支持运行时间统计
    - today_runtime: 当天运行时间（小时）
    - month_runtime: 当月运行时间（小时）
    """
    result = await db.execute(
        select(Device).where(
            Device.id == device_id,
            Device.tenant_id == current_user.tenant_id
        )
    )
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")

    # 使用运行时间服务（传入 tenant_id 确保租户隔离）
    service = RuntimeService(db, tenant_id=current_user.tenant_id)

    # 检查是否支持
    supported = await service.supports_runtime(device.device_id)

    if not supported:
        return {
            "supported": False,
            "message": "当前协议版本不支持空调状态监控",
            "today_runtime": None,
            "month_runtime": None
        }

    # 计算运行时间（传入 last_seen_at 处理边界条件）
    today_runtime = await service.get_today_runtime(
        device.device_id, last_seen_at=device.last_seen_at
    )
    month_runtime = await service.get_month_runtime(
        device.device_id, last_seen_at=device.last_seen_at
    )

    return {
        "supported": True,
        "message": "",
        "today_runtime": today_runtime,
        "month_runtime": month_runtime
    }