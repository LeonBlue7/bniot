"""租户 API 端点（仅管理员可用）"""
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models import Tenant, User
from app.schemas import Message
from app.services.auth import get_current_user
from app.services.permissions import Permission, require_permission

router = APIRouter()


@router.get("", response_model=list[dict])
async def list_tenants(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.USER_CREATE))
):
    """获取租户列表（仅系统管理员）"""
    result = await db.execute(select(Tenant).order_by(Tenant.id))
    tenants = result.scalars().all()
    return [
        {
            "id": t.id,
            "name": t.name,
            "code": t.code,
            "created_at": t.created_at
        }
        for t in tenants
    ]


@router.get("/me", response_model=dict)
async def get_current_tenant(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取当前用户所属租户信息"""
    result = await db.execute(
        select(Tenant).where(Tenant.id == current_user.tenant_id)
    )
    tenant = result.scalar_one_or_none()
    if not tenant:
        return {"id": 0, "name": "未知", "code": "unknown"}

    return {
        "id": tenant.id,
        "name": tenant.name,
        "code": tenant.code,
        "created_at": tenant.created_at
    }