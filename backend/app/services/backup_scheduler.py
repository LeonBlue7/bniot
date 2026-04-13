"""
备份定时任务调度器
Phase 3.1 数据管理

提供每日自动备份功能（凌晨2点执行）
使用 APScheduler 实现定时任务
"""
import logging
import os
from datetime import UTC, datetime
from typing import Any

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.database import async_session_maker
from app.services.backup import BackupService, BackupStatus

logger = logging.getLogger(__name__)


# 定时任务配置
DAILY_BACKUP_HOUR = int(os.environ.get("BACKUP_HOUR", "2"))  # 凌晨2点
DAILY_BACKUP_MINUTE = int(os.environ.get("BACKUP_MINUTE", "0"))


class BackupScheduler:
    """备份定时任务调度器"""

    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.jobs: dict[str, Any] = {}

    def setup_jobs(self) -> None:
        """
        设置定时任务
        """
        # 每日凌晨2点执行全量备份
        self.scheduler.add_job(
            self.execute_backup,
            trigger=CronTrigger(
                hour=DAILY_BACKUP_HOUR,
                minute=DAILY_BACKUP_MINUTE
            ),
            id="daily_backup",
            name="每日自动备份",
            replace_existing=True
        )

        # 每周清理旧备份（周日凌晨3点）
        self.scheduler.add_job(
            self.cleanup_backups,
            trigger=CronTrigger(
                day_of_week="sun",
                hour=3,
                minute=0
            ),
            id="weekly_cleanup",
            name="每周清理旧备份",
            replace_existing=True
        )

    def start(self) -> None:
        """
        启动调度器
        """
        if not self.scheduler.running:
            self.scheduler.start()

    def stop(self) -> None:
        """
        停止调度器
        """
        if self.scheduler.running:
            self.scheduler.shutdown()

    def get_jobs(self) -> list[dict[str, Any]]:
        """
        获取所有定时任务信息

        Returns:
            任务列表
        """
        jobs = []
        for job in self.scheduler.get_jobs():
            # 获取next_run_time（可能不存在如果调度器未启动）
            next_run = getattr(job, 'next_run_time', None)
            jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run_time": next_run.isoformat() if next_run else None,
                "trigger": str(job.trigger)
            })
        return jobs

    async def execute_backup(self) -> bool:
        """
        执行备份任务

        Returns:
            是否成功
        """
        try:
            async with async_session_maker() as db:
                service = BackupService(db)

                # 执行全量备份（无租户限制）
                file_path = await service.generate_backup(
                    tenant_id=None,
                    backup_type="scheduled"
                )

                return file_path is not None

        except Exception as e:
            # 记录错误日志
            logger.error("备份任务执行失败: %s", e)
            return False

    async def cleanup_backups(self) -> int:
        """
        清理旧备份任务

        Returns:
            清理的备份数量
        """
        try:
            async with async_session_maker() as db:
                service = BackupService(db)

                # 清理所有租户的旧备份
                from sqlalchemy import select
                from app.models import Tenant

                query = select(Tenant)
                result = await db.execute(query)
                tenants = result.scalars().all()

                total_deleted = 0
                for tenant in tenants:
                    deleted = await service.cleanup_old_backups(tenant.id)
                    total_deleted += deleted

                return total_deleted

        except Exception as e:
            logger.error("清理备份任务执行失败: %s", e)
            return 0


# 全局调度器实例
_scheduler: BackupScheduler | None = None


def get_scheduler() -> BackupScheduler:
    """
    获取调度器实例

    Returns:
        调度器实例
    """
    global _scheduler

    if _scheduler is None:
        _scheduler = BackupScheduler()
        _scheduler.setup_jobs()

    return _scheduler


def start_scheduler() -> None:
    """
    启动调度器
    """
    scheduler = get_scheduler()
    scheduler.start()


def stop_scheduler() -> None:
    """
    停止调度器
    """
    global _scheduler

    if _scheduler is not None:
        _scheduler.stop()
        _scheduler = None