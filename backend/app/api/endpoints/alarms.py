"""
告警管理 API 端点
"""
import logging
from datetime import UTC, datetime

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models import Alarm, User
from app.schemas import AlarmResponse
from app.services.auth import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)


class BatchHandleRequest(BaseModel):
    """批量处理请求"""
    alarm_ids: list[int]


@router.get("", response_model=list[AlarmResponse])
async def list_alarms(
    is_resolved: bool | None = Query(None, description="按处理状态过滤"),
    severity: str | None = Query(None, description="按严重程度过滤"),
    type: str | None = Query(None, description="按类型过滤"),
    device_id: str | None = Query(None, description="按设备ID过滤"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取告警列表"""
    query = select(Alarm).where(Alarm.tenant_id == current_user.tenant_id)

    if is_resolved is not None:
        query = query.where(Alarm.is_resolved == is_resolved)
    if severity:
        query = query.where(Alarm.severity == severity)
    if type:
        query = query.where(Alarm.type == type)
    if device_id:
        query = query.where(Alarm.device_id.ilike(f"%{device_id}%"))

    query = query.offset(skip).limit(limit).order_by(Alarm.occurred_at.desc())
    result = await db.execute(query)
    return result.scalars().all()


@router.patch("/{alarm_id}/handle", response_model=AlarmResponse)
async def handle_alarm(
    alarm_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """处理单个告警"""
    result = await db.execute(
        select(Alarm).where(
            Alarm.id == alarm_id,
            Alarm.tenant_id == current_user.tenant_id
        )
    )
    alarm = result.scalar_one_or_none()
    if not alarm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="告警不存在"
        )

    alarm.is_resolved = True
    alarm.resolved_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(alarm)

    logger.info(f"告警 {alarm_id} 由用户 {current_user.username} 处理，设备: {alarm.device_id}")
    return alarm


@router.patch("/batch-handle")
async def batch_handle_alarms(
    request: BatchHandleRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """批量处理告警"""
    if not request.alarm_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="告警ID列表不能为空"
        )

    # 查询属于当前租户且未处理的告警
    result = await db.execute(
        select(Alarm).where(
            Alarm.id.in_(request.alarm_ids),
            Alarm.tenant_id == current_user.tenant_id,
            Alarm.is_resolved == False
        )
    )
    alarms = result.scalars().all()

    # 检查是否有不属于当前租户或已处理的告警
    all_requested_ids = set(request.alarm_ids)
    handled_ids = set(a.id for a in alarms)
    invalid_ids = all_requested_ids - handled_ids

    # 处理告警
    handled_count = 0
    now = datetime.now(UTC)
    for alarm in alarms:
        alarm.is_resolved = True
        alarm.resolved_at = now
        handled_count += 1

    await db.commit()

    # 记录日志
    logger.info(
        f"用户 {current_user.username} 批量处理告警: "
        f"请求 {len(request.alarm_ids)} 个, 处理 {handled_count} 个, "
        f"无效 {len(invalid_ids)} 个"
    )

    response = {
        "message": f"已处理 {handled_count} 条告警",
        "handled_count": handled_count,
    }

    if invalid_ids:
        response["invalid_ids"] = list(invalid_ids)
        response["warning"] = f"{len(invalid_ids)} 个告警ID不属于当前租户或已处理，未能处理"

    return response


@router.get("/stats")
async def get_alarm_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取告警统计"""
    # 总告警数
    total_result = await db.execute(
        select(func.count(Alarm.id)).where(
            Alarm.tenant_id == current_user.tenant_id
        )
    )
    total_alarms = total_result.scalar() or 0

    # 未处理告警数
    unresolved_result = await db.execute(
        select(func.count(Alarm.id)).where(
            and_(
                Alarm.tenant_id == current_user.tenant_id,
                Alarm.is_resolved == False
            )
        )
    )
    unresolved_alarms = unresolved_result.scalar() or 0

    return {
        "total_alarms": total_alarms,
        "unresolved_alarms": unresolved_alarms,
        "resolved_alarms": total_alarms - unresolved_alarms
    }