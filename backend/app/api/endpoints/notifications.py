"""
通知规则 API 端点

提供通知规则的 CRUD 操作
"""
import logging
from datetime import UTC, datetime

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models import NotificationRule, NotificationRecord, User
from app.schemas import NotificationRuleResponse, NotificationRecordResponse
from app.services.auth import get_current_user
from app.services.notification import NotificationRuleService, NotificationDispatchService

router = APIRouter()
logger = logging.getLogger(__name__)


class NotificationRuleCreate(BaseModel):
    """创建通知规则请求"""
    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = None
    alarm_types: list[str] = Field(..., min_items=1)
    severities: list[str] = Field(..., min_items=1)
    channels: list[str] = Field(..., min_items=1)
    recipients: list[str] = Field(..., min_items=1)
    cooldown_minutes: int = Field(default=30, ge=1, le=1440)  # 1分钟到24小时
    is_enabled: bool = True


class NotificationRuleUpdate(BaseModel):
    """更新通知规则请求"""
    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = None
    alarm_types: list[str] | None = Field(None, min_items=1)
    severities: list[str] | None = Field(None, min_items=1)
    channels: list[str] | None = Field(None, min_items=1)
    recipients: list[str] | None = Field(None, min_items=1)
    cooldown_minutes: int | None = Field(None, ge=1, le=1440)
    is_enabled: bool | None = None


@router.get("/rules", response_model=list[NotificationRuleResponse])
async def list_notification_rules(
    is_enabled: bool | None = Query(None, description="按启用状态过滤"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取通知规则列表"""
    query = select(NotificationRule).where(
        NotificationRule.tenant_id == current_user.tenant_id
    )

    if is_enabled is not None:
        query = query.where(NotificationRule.is_enabled == is_enabled)

    query = query.offset(skip).limit(limit).order_by(NotificationRule.created_at.desc())
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/rules", response_model=NotificationRuleResponse, status_code=status.HTTP_201_CREATED)
async def create_notification_rule(
    request: NotificationRuleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建通知规则"""
    service = NotificationRuleService(db)

    rule = await service.create_rule(
        tenant_id=current_user.tenant_id,
        name=request.name,
        description=request.description,
        alarm_types=request.alarm_types,
        severities=request.severities,
        channels=request.channels,
        recipients=request.recipients,
        cooldown_minutes=request.cooldown_minutes,
        is_enabled=request.is_enabled
    )

    logger.info(f"用户 {current_user.username} 创建通知规则: {rule.id}")
    return rule


@router.get("/rules/{rule_id}", response_model=NotificationRuleResponse)
async def get_notification_rule(
    rule_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取单个通知规则"""
    result = await db.execute(
        select(NotificationRule).where(
            and_(
                NotificationRule.id == rule_id,
                NotificationRule.tenant_id == current_user.tenant_id
            )
        )
    )
    rule = result.scalar_one_or_none()

    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="通知规则不存在"
        )

    return rule


@router.patch("/rules/{rule_id}", response_model=NotificationRuleResponse)
async def update_notification_rule(
    rule_id: int,
    request: NotificationRuleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新通知规则"""
    service = NotificationRuleService(db)

    # 构建更新数据（只包含非 None 的字段）
    update_data = {}
    for key, value in request.model_dump().items():
        if value is not None:
            update_data[key] = value

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="没有需要更新的字段"
        )

    rule = await service.update_rule(
        rule_id=rule_id,
        tenant_id=current_user.tenant_id,
        **update_data
    )

    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="通知规则不存在"
        )

    logger.info(f"用户 {current_user.username} 更新通知规则: {rule_id}")
    return rule


@router.delete("/rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_notification_rule(
    rule_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除通知规则"""
    service = NotificationRuleService(db)

    success = await service.delete_rule(
        rule_id=rule_id,
        tenant_id=current_user.tenant_id
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="通知规则不存在"
        )

    logger.info(f"用户 {current_user.username} 删除通知规则: {rule_id}")


@router.get("/records", response_model=list[NotificationRecordResponse])
async def list_notification_records(
    alarm_id: int | None = Query(None, description="按告警ID过滤"),
    channel: str | None = Query(None, description="按渠道过滤"),
    status: str | None = Query(None, description="按状态过滤"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取通知记录列表"""
    query = select(NotificationRecord).where(
        NotificationRecord.tenant_id == current_user.tenant_id
    )

    if alarm_id is not None:
        query = query.where(NotificationRecord.alarm_id == alarm_id)
    if channel:
        query = query.where(NotificationRecord.channel == channel)
    if status:
        query = query.where(NotificationRecord.status == status)

    query = query.offset(skip).limit(limit).order_by(NotificationRecord.created_at.desc())
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/stats")
async def get_notification_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取通知统计"""
    # 总通知数
    total_result = await db.execute(
        select(func.count(NotificationRecord.id)).where(
            NotificationRecord.tenant_id == current_user.tenant_id
        )
    )
    total = total_result.scalar() or 0

    # 成功发送数
    sent_result = await db.execute(
        select(func.count(NotificationRecord.id)).where(
            and_(
                NotificationRecord.tenant_id == current_user.tenant_id,
                NotificationRecord.status == "sent"
            )
        )
    )
    sent_count = sent_result.scalar() or 0

    # 失败数
    failed_result = await db.execute(
        select(func.count(NotificationRecord.id)).where(
            and_(
                NotificationRecord.tenant_id == current_user.tenant_id,
                NotificationRecord.status == "failed"
            )
        )
    )
    failed_count = failed_result.scalar() or 0

    # 规则数
    rules_result = await db.execute(
        select(func.count(NotificationRule.id)).where(
            NotificationRule.tenant_id == current_user.tenant_id
        )
    )
    rules_count = rules_result.scalar() or 0

    return {
        "total_notifications": total,
        "sent_count": sent_count,
        "failed_count": failed_count,
        "success_rate": round(sent_count / total * 100, 2) if total > 0 else 0,
        "rules_count": rules_count
    }