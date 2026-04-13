"""
备份管理 API 端点
Phase 3.1 数据管理

提供手动备份、备份列表、下载备份、删除备份、数据恢复等接口
"""
import logging
import os
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
import io

from app.core.database import get_db
from app.models import BackupRecord, RestoreRecord, User
from app.schemas.backup import (
    BackupCreateRequest,
    BackupResponse,
    BackupListResponse,
)
from app.schemas.restore import (
    RestoreResponse,
    RestoreListResponse,
    RestoreRequest,
    BackupValidationResponse,
)
from app.services.auth import get_current_user
from app.services.backup import BackupService, BackupStatus
from app.services.restore import RestoreService, RestoreStatus
from app.services.permissions import Permission, require_permission

router = APIRouter()
logger = logging.getLogger(__name__)


# ============ 备份相关接口 ============

@router.get("", response_model=BackupListResponse)
async def list_backups(
    limit: int = Query(20, ge=1, le=100, description="返回数量限制"),
    offset: int = Query(0, ge=0, description="偏移量"),
    backup_type: str | None = Query(None, description="备份类型筛选: manual/scheduled/auto"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取备份列表

    - 支持分页查询
    - 支持按备份类型筛选
    - 只显示当前租户的备份
    """
    service = BackupService(db)

    backups = await service.list_backups(
        tenant_id=current_user.tenant_id,
        limit=limit,
        offset=offset,
        backup_type=backup_type
    )

    return BackupListResponse(
        data=[BackupResponse.model_validate(b) for b in backups],
        total=len(backups),
        limit=limit,
        offset=offset
    )


@router.post("", response_model=BackupResponse, status_code=201)
async def create_backup(
    request: BackupCreateRequest = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.BACKUP_CREATE))
):
    """
    创建手动备份

    - 需要管理员权限
    - 支持全量备份和租户级备份
    - 返回备份记录和下载链接
    """
    service = BackupService(db)

    try:
        # 生成备份文件
        file_path = await service.generate_backup(
            tenant_id=current_user.tenant_id,
            backup_type="manual"
        )

        # 获取最新备份记录
        backups = await service.list_backups(current_user.tenant_id, limit=1)
        if backups:
            return BackupResponse.model_validate(backups[0])

        raise HTTPException(status_code=500, detail="备份创建失败")

    except Exception as e:
        logger.error("备份创建失败: %s", e)
        raise HTTPException(status_code=500, detail="备份创建失败，请稍后重试")


@router.get("/{backup_id}", response_model=BackupResponse)
async def get_backup(
    backup_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取单个备份详情

    - 验证租户权限
    - 返回备份详细信息
    """
    service = BackupService(db)

    backup = await service.get_backup_by_id(backup_id, current_user.tenant_id)

    if not backup:
        raise HTTPException(status_code=404, detail="备份不存在")

    return BackupResponse.model_validate(backup)


@router.get("/{backup_id}/download")
async def download_backup(
    backup_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    下载备份文件

    - 验证租户权限
    - 验证备份状态（已完成）
    - 返回文件流
    """
    service = BackupService(db)

    # 获取备份记录
    backup = await service.get_backup_by_id(backup_id, current_user.tenant_id)

    if not backup:
        raise HTTPException(status_code=404, detail="备份不存在")

    # 验证备份状态
    if backup.status != BackupStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="备份未完成，无法下载")

    # 验证文件存在
    if not os.path.exists(backup.file_path):
        raise HTTPException(status_code=404, detail="备份文件不存在")

    # 读取文件内容
    content = service.get_backup_file_content(backup.file_path)

    if content is None:
        raise HTTPException(status_code=500, detail="无法读取备份文件")

    # 生成文件名
    filename = os.path.basename(backup.file_path)

    # 返回文件流
    return StreamingResponse(
        io.BytesIO(content),
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )


@router.delete("/{backup_id}", status_code=204)
async def delete_backup(
    backup_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.BACKUP_DELETE))
):
    """
    删除备份

    - 需要管理员权限
    - 同时删除记录和文件
    """
    service = BackupService(db)

    success = await service.delete_backup(backup_id, current_user.tenant_id)

    if not success:
        raise HTTPException(status_code=404, detail="备份不存在")

    return None


@router.get("/{backup_id}/validate", response_model=BackupValidationResponse)
async def validate_backup(
    backup_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.BACKUP_VIEW))
):
    """
    验证备份文件

    - 验证租户权限
    - 检查备份文件完整性和有效性
    """
    backup_service = BackupService(db)
    restore_service = RestoreService(db)

    # 获取备份记录
    backup = await backup_service.get_backup_by_id(backup_id, current_user.tenant_id)

    if not backup:
        raise HTTPException(status_code=404, detail="备份不存在")

    # 验证备份文件
    result = await restore_service.validate_backup_file(backup.file_path)

    return BackupValidationResponse(**result)


@router.post("/{backup_id}/restore", response_model=RestoreResponse, status_code=200)
async def restore_from_backup(
    backup_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.BACKUP_CREATE))
):
    """
    从备份恢复数据

    - 需要管理员权限
    - 验证备份文件有效性
    - 创建恢复前安全备份
    - 执行恢复操作
    - 记录恢复日志
    """
    restore_service = RestoreService(db)

    try:
        result = await restore_service.restore_from_backup(
            backup_id=backup_id,
            tenant_id=current_user.tenant_id
        )

        if not result['success']:
            logger.error("恢复失败: %s", result['error'])
            raise HTTPException(status_code=500, detail="恢复失败，请稍后重试")

        # 获取恢复记录
        restore = await restore_service.get_restore_record(
            restore_id=result['restore_id'],
            tenant_id=current_user.tenant_id
        )

        if restore:
            return RestoreResponse.model_validate(restore)

        raise HTTPException(status_code=500, detail="恢复记录获取失败")

    except HTTPException:
        raise
    except Exception as e:
        logger.error("恢复过程异常: %s", e)
        raise HTTPException(status_code=500, detail="恢复失败，请稍后重试")


@router.get("/scheduler/jobs")
async def get_scheduler_jobs(
    current_user: User = Depends(require_permission(Permission.BACKUP_VIEW))
):
    """
    获取定时任务信息

    - 需要管理员权限
    - 显示每日备份任务配置
    """
    from app.services.backup_scheduler import get_scheduler

    scheduler = get_scheduler()
    jobs = scheduler.get_jobs()

    return {
        "jobs": jobs,
        "scheduler_running": scheduler.scheduler.running
    }


# ============ 恢复记录接口 ============

@router.get("/restores", response_model=RestoreListResponse)
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
    restore_service = RestoreService(db)

    restores = await restore_service.list_restore_records(
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