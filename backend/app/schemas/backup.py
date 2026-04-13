"""
备份相关 Pydantic Schemas
Phase 3.1 数据管理
"""
from datetime import datetime

from pydantic import BaseModel, Field


class BackupResponse(BaseModel):
    """备份响应"""
    id: int
    tenant_id: int | None = None
    backup_type: str = Field(..., description="备份类型: manual/scheduled/auto")
    file_path: str
    file_size: int | None = Field(None, description="文件大小(字节)")
    status: str = Field(..., description="状态: pending/in_progress/completed/failed")
    error_message: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class BackupListResponse(BaseModel):
    """备份列表响应"""
    data: list[BackupResponse]
    total: int = Field(..., description="总数")
    limit: int = Field(..., description="限制数量")
    offset: int = Field(..., description="偏移量")


class BackupCreateRequest(BaseModel):
    """创建备份请求"""
    backup_type: str = Field(default="manual", description="备份类型")
    description: str | None = Field(None, description="备份描述")


class BackupSchedulerJobResponse(BaseModel):
    """定时任务响应"""
    id: str
    name: str
    next_run_time: datetime | None
    trigger: str


class BackupSchedulerStatusResponse(BaseModel):
    """调度器状态响应"""
    jobs: list[BackupSchedulerJobResponse]
    scheduler_running: bool