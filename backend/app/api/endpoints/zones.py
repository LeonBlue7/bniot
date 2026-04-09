"""
分区 API 端点
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models import User, Zone
from app.schemas import Message, ZoneCreate, ZoneResponse, ZoneUpdate
from app.services.auth import get_current_user

router = APIRouter()


@router.get("", response_model=list[ZoneResponse])
async def list_zones(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取分区列表"""
    result = await db.execute(
        select(Zone)
        .where(Zone.tenant_id == current_user.tenant_id)
        .order_by(Zone.sort_order)
    )
    return result.scalars().all()


@router.post("", response_model=ZoneResponse, status_code=status.HTTP_201_CREATED)
async def create_zone(
    zone_in: ZoneCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建分区"""
    zone = Zone(
        tenant_id=current_user.tenant_id,
        name=zone_in.name,
        parent_id=zone_in.parent_id,
        description=zone_in.description,
        sort_order=zone_in.sort_order
    )
    db.add(zone)
    await db.commit()
    await db.refresh(zone)
    return zone


@router.put("/{zone_id}", response_model=ZoneResponse)
async def update_zone(
    zone_id: int,
    zone_in: ZoneUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新分区"""
    result = await db.execute(
        select(Zone).where(
            Zone.id == zone_id,
            Zone.tenant_id == current_user.tenant_id
        )
    )
    zone = result.scalar_one_or_none()
    if not zone:
        raise HTTPException(status_code=404, detail="分区不存在")

    update_data = zone_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(zone, field, value)

    await db.commit()
    await db.refresh(zone)
    return zone


@router.delete("/{zone_id}", response_model=Message)
async def delete_zone(
    zone_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除分区"""
    result = await db.execute(
        select(Zone).where(
            Zone.id == zone_id,
            Zone.tenant_id == current_user.tenant_id
        )
    )
    zone = result.scalar_one_or_none()
    if not zone:
        raise HTTPException(status_code=404, detail="分区不存在")

    await db.delete(zone)
    await db.commit()
    return Message(message="分区已删除")
