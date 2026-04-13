"""
操作日志 API 端点
Phase 1.2 操作日志系统
"""
from datetime import datetime, UTC
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models import OperationLog, User
from app.schemas import PaginatedResponse
from app.services.permissions import Permission, require_permission
from app.services.operation_log import OperationLogService

router = APIRouter()


class OperationLogResponse:
    """操作日志响应模型"""
    id: int
    tenant_id: int
    user_id: int | None
    action: str
    resource_type: str
    resource_id: str | None
    details: dict[str, Any]
    ip_address: str | None
    user_agent: str | None
    created_at: datetime

    class Config:
        from_attributes = True


@router.get("", response_model=PaginatedResponse)
async def list_logs(
    action: str | None = Query(None, description="操作类型过滤"),
    resource_type: str | None = Query(None, description="资源类型过滤"),
    resource_id: str | None = Query(None, description="资源ID过滤"),
    user_id: int | None = Query(None, description="用户ID过滤"),
    start_date: datetime | None = Query(None, description="开始日期"),
    end_date: datetime | None = Query(None, description="结束日期"),
    skip: int = Query(0, ge=0, description="跳过条数"),
    limit: int = Query(20, ge=1, le=100, description="返回条数"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.LOG_READ))
):
    """
    获取操作日志列表

    仅管理员和操作员可以访问。
    """
    # 查询日志
    log_service = OperationLogService()
    logs = await log_service.query(
        db,
        tenant_id=current_user.tenant_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        user_id=user_id,
        start_date=start_date,
        end_date=end_date,
        skip=skip,
        limit=limit
    )

    # 统计总数
    total = await log_service.count(
        db,
        tenant_id=current_user.tenant_id,
        action=action,
        resource_type=resource_type,
        start_date=start_date,
        end_date=end_date
    )

    # 构建响应
    items = [
        {
            "id": log.id,
            "tenant_id": log.tenant_id,
            "user_id": log.user_id,
            "action": log.action,
            "resource_type": log.resource_type,
            "resource_id": log.resource_id,
            "details": log.details,
            "ip_address": log.ip_address,
            "user_agent": log.user_agent,
            "created_at": log.created_at
        }
        for log in logs
    ]

    return PaginatedResponse(
        items=items,
        total=total,
        page=skip // limit + 1,
        page_size=limit,
        total_pages=(total + limit - 1) // limit
    )


@router.get("/{log_id}")
async def get_log_detail(
    log_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.LOG_READ))
):
    """
    获取操作日志详情
    """
    result = await db.execute(
        select(OperationLog).where(
            OperationLog.id == log_id,
            OperationLog.tenant_id == current_user.tenant_id
        )
    )
    log = result.scalar_one_or_none()

    if not log:
        raise HTTPException(status_code=404, detail="日志不存在")

    return {
        "id": log.id,
        "tenant_id": log.tenant_id,
        "user_id": log.user_id,
        "action": log.action,
        "resource_type": log.resource_type,
        "resource_id": log.resource_id,
        "details": log.details,
        "ip_address": log.ip_address,
        "user_agent": log.user_agent,
        "created_at": log.created_at
    }