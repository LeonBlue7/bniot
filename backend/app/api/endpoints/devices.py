"""
设备 API 端点
"""
import json
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models import Device, DeviceData, User
from app.mqtt import get_mqtt_client
from app.schemas import DashboardStats, DeviceCreate, DeviceResponse, DeviceUpdate, Message
from app.services.auth import get_current_user

router = APIRouter()


@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
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
    # TODO: 实现告警统计

    return DashboardStats(
        total_devices=total_devices,
        online_devices=online_devices,
        offline_devices=total_devices - online_devices,
        total_alarms=0,
        unresolved_alarms=0
    )


@router.get("", response_model=list[DeviceResponse])
async def list_devices(
    zone_id: int | None = None,
    is_online: bool | None = None,
    keyword: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
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


@router.get("/{device_id}", response_model=DeviceResponse)
async def get_device(
    device_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
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


@router.post("", response_model=DeviceResponse, status_code=status.HTTP_201_CREATED)
async def create_device(
    device_in: DeviceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
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


@router.put("/{device_id}", response_model=DeviceResponse)
async def update_device(
    device_id: int,
    device_in: DeviceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
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
    current_user: User = Depends(get_current_user)
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
    current_user: User = Depends(get_current_user)
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

    # 发送 MQTT 控制命令
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
    current_user: User = Depends(get_current_user)
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

    # 查询历史数据
    start_time = datetime.now(UTC) - timedelta(hours=hours)

    data_result = await db.execute(
        select(DeviceData)
        .where(DeviceData.device_id == device.device_id)
        .where(DeviceData.time >= start_time)
        .order_by(DeviceData.time.desc())
        .limit(1000)
    )
    # 手动构建字典，避免暴露 SQLAlchemy 内部属性
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
