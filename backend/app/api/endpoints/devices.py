"""
设备 API 端点
使用新的权限系统进行访问控制

注意：批量操作路由必须在/{device_id}路由之前定义，否则batch会被当作device_id处理
"""
import json
import logging
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models import Alarm, Device, DeviceData, User, Zone
from app.mqtt import get_mqtt_client
from app.schemas import (
    BatchControlRequest,
    BatchDeleteRequest,
    BatchMoveZoneRequest,
    BatchOperationResponse,
    DashboardStats,
    DeviceCreate,
    DeviceResponse,
    DeviceUpdate,
    Message,
)
from app.services.auth import get_current_user
from app.services.permissions import Permission, require_permission
from app.services.operation_log import OperationLogService, ActionType, ResourceType

router = APIRouter()
logger = logging.getLogger(__name__)


# ============ 统计和列表（无路径参数） ============

@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.DEVICE_READ))
):
    """获取仪表盘统计数据"""
    # 设备统计
    total_result = await db.execute(
        select(func.count(Device.id)).where(Device.tenant_id == current_user.tenant_id)
    )
    total_devices = total_result.scalar() or 0

    online_result = await db.execute(
        select(func.count(Device.id)).where(
            and_(
                Device.tenant_id == current_user.tenant_id,
                Device.is_online
            )
        )
    )
    online_devices = online_result.scalar() or 0

    # 告警统计
    total_alarms_result = await db.execute(
        select(func.count(Alarm.id)).where(Alarm.tenant_id == current_user.tenant_id)
    )
    total_alarms = total_alarms_result.scalar() or 0

    unresolved_alarms_result = await db.execute(
        select(func.count(Alarm.id)).where(
            and_(
                Alarm.tenant_id == current_user.tenant_id,
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


@router.get("", response_model=list[DeviceResponse])
async def list_devices(
    zone_id: int | None = None,
    is_online: bool | None = None,
    keyword: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.DEVICE_READ))
):
    """获取设备列表"""
    query = select(Device).where(Device.tenant_id == current_user.tenant_id)

    if zone_id:
        query = query.where(Device.zone_id == zone_id)
    if is_online is not None:
        query = query.where(Device.is_online == is_online)
    if keyword:
        query = query.where(
            (Device.name.ilike(f"%{keyword}%")) |
            (Device.device_id.ilike(f"%{keyword}%"))
        )

    query = query.offset(skip).limit(limit).order_by(Device.id.desc())
    result = await db.execute(query)
    return result.scalars().all()


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


# ============ 单设备操作（带路径参数） ============

@router.get("/{device_id}", response_model=DeviceResponse)
async def get_device(
    device_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.DEVICE_READ))
):
    """获取设备详情"""
    result = await db.execute(
        select(Device).where(
            Device.id == device_id,
            Device.tenant_id == current_user.tenant_id
        )
    )
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")
    return device


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
            "current": d.current,
            "csq": d.csq,
            "air_err": d.air_err,
            "alarmtemp": d.alarmtemp,
            "alarmhumi": d.alarmhumi,
        }
        for d in data_result.scalars().all()
    ]