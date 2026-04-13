"""
恢复相关 Pydantic Schemas
Phase 3.2 数据管理
"""
from datetime import datetime

from pydantic import BaseModel, Field


class RestoreResponse(BaseModel):
    """恢复响应"""
    id: int
    tenant_id: int
    backup_id: int | None = None
    status: str = Field(..., description="状态: pending/in_progress/completed/failed/rolled_back")
    progress: int = Field(default=0, ge=0, le=100, description="进度百分比")
    error_message: str | None = None
    safety_backup_id: int | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class RestoreListResponse(BaseModel):
    """恢复记录列表响应"""
    data: list[RestoreResponse]
    total: int
    limit: int
    offset: int


class RestoreRequest(BaseModel):
    """恢复请求"""
    backup_id: int = Field(..., description="备份ID")
    force: bool = Field(default=False, description="强制恢复（跳过某些验证）")


class RestoreProgressResponse(BaseModel):
    """恢复进度响应"""
    restore_id: int
    status: str
    progress: int
    error_message: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None


class BackupValidationResponse(BaseModel):
    """备份验证响应"""
    valid: bool
    file_path: str
    file_size: int | None = None
    checksum: str | None = None
    error: str | None = None