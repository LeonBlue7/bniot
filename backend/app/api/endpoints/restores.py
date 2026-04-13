"""
恢复管理 API 端点
Phase 3.2 数据管理

提供恢复记录查询、恢复进度跟踪等接口
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models import User
from app.schemas.restore import (
    RestoreResponse,
    RestoreListResponse,
)
from app.services.auth import get_current_user
from app.services.restore import RestoreService
from app.services.permissions import check_permission


router = APIRouter()


@router.get("", response_model=RestoreListResponse)
async def list_restores(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取恢复记录列表

    - 支持分页查询
    - 只显示当前租户的恢复记录
    """
    service = RestoreService(db)

    restores = await service.list_restore_records(
        tenant_id=current_user.tenant_id,
        limit=limit,
        offset=offset
    )

    return RestoreListResponse(
        data=[RestoreResponse.model_validate(r) for r in restores],
        total=len(restores),
        limit=limit,
        offset=offset
    )


@router.get("/{restore_id}", response_model=RestoreResponse)
async def get_restore(
    restore_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取单个恢复记录详情

    - 验证租户权限
    - 返回恢复详细信息和进度
    """
    service = RestoreService(db)

    restore = await service.get_restore_record(restore_id, current_user.tenant_id)

    if not restore:
        raise HTTPException(status_code=404, detail="恢复记录不存在")

    return RestoreResponse.model_validate(restore)