"""分区 API 端点
包含分区管理和分区授权管理
""" 
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models import User, Zone
from app.models.models import ZoneTenant
from app.schemas import Message, ZoneCreate, ZoneResponse, ZoneUpdate
from app.services.auth import get_current_user
from app.services.permissions import Permission, require_permission

router = APIRouter()


# ============ 分区基础管理 ============

@router.get("", response_model=list[ZoneResponse])
async def list_zones(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.ZONE_READ))
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
    current_user: User = Depends(require_permission(Permission.ZONE_CREATE))
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
    current_user: User = Depends(require_permission(Permission.ZONE_UPDATE))
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
        raise HTTPException(status_code=404, detail="分区不存在" )

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
    current_user: User = Depends(require_permission(Permission.ZONE_DELETE))
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
        raise HTTPException(status_code=404, detail="分区不存在" )

    await db.delete(zone)
    await db.commit()
    return Message(message="分区已删除" )


# ============ 分区授权管理（仅管理员） ============

@router.get("/{zone_id}/authorizations", response_model=list[dict])
async def list_zone_authorizations(
    zone_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.ZONE_READ))
):
    """获取分区的授权列表""" 
    # 检查分区是否存在且属于当前租户
    result = await db.execute(
        select(Zone).where(
            Zone.id == zone_id,
            Zone.tenant_id == current_user.tenant_id
        )
    )
    zone = result.scalar_one_or_none()
    if not zone:
        raise HTTPException(status_code=404, detail="分区不存在" )

    # 查询授权列表
    result = await db.execute(
        select(ZoneTenant).where(ZoneTenant.zone_id == zone_id)
    )
    authorizations = result.scalars().all()

    return [
        {
            "id": auth.id,
            "zone_id": auth.zone_id,
            "tenant_id": auth.tenant_id,
            "created_at": auth.created_at
        }
        for auth in authorizations
    ]


@router.post("/{zone_id}/authorizations", response_model=dict, status_code=status.HTTP_201_CREATED)
async def authorize_zone_to_tenant(
    zone_id: int,
    tenant_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.ZONE_UPDATE))
):
    """将分区授权给指定租户""" 
    from app.models import Tenant

    # 检查分区是否存在且属于当前租户
    result = await db.execute(
        select(Zone).where(
            Zone.id == zone_id,
            Zone.tenant_id == current_user.tenant_id
        )
    )
    zone = result.scalar_one_or_none()
    if not zone:
        raise HTTPException(status_code=404, detail="分区不存在" )

    # 检查目标租户是否存在
    result = await db.execute(
        select(Tenant).where(Tenant.id == tenant_id)
    )
    target_tenant = result.scalar_one_or_none()
    if not target_tenant:
        raise HTTPException(status_code=404, detail="目标租户不存在" )

    # 检查是否已授权
    result = await db.execute(
        select(ZoneTenant).where(
            and_(
                ZoneTenant.zone_id == zone_id,
                ZoneTenant.tenant_id == tenant_id
            )
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="分区已授权给该租户" )

    # 创建授权关系
    zone_tenant = ZoneTenant(
        zone_id=zone_id,
        tenant_id=tenant_id
    )
    db.add(zone_tenant)
    await db.commit()
    await db.refresh(zone_tenant)

    return {
        "id": zone_tenant.id,
        "zone_id": zone_tenant.zone_id,
        "tenant_id": zone_tenant.tenant_id,
        "created_at": zone_tenant.created_at
    }


@router.delete("/{zone_id}/authorizations/{tenant_id}", response_model=Message)
async def remove_zone_authorization(
    zone_id: int,
    tenant_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.ZONE_UPDATE))
):
    """移除分区对指定租户的授权""" 
    # 检查分区是否存在且属于当前租户
    result = await db.execute(
        select(Zone).where(
            Zone.id == zone_id,
            Zone.tenant_id == current_user.tenant_id
        )
    )
    zone = result.scalar_one_or_none()
    if not zone:
        raise HTTPException(status_code=404, detail="分区不存在" )

    # 查找授权关系
    result = await db.execute(
        select(ZoneTenant).where(
            and_(
                ZoneTenant.zone_id == zone_id,
                ZoneTenant.tenant_id == tenant_id
            )
        )
    )
    zone_tenant = result.scalar_one_or_none()
    if not zone_tenant:
        raise HTTPException(status_code=404, detail="授权关系不存在" )

    # 删除授权关系
    await db.delete(zone_tenant)
    await db.commit()

    return Message(message="授权已移除" )
