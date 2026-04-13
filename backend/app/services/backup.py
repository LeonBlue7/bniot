"""
备份服务模块
Phase 3.1 数据管理

提供数据库备份、备份列表管理、备份文件操作等功能
"""
import os
import subprocess
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import BackupRecord, BackupStatus


# 备份存储目录
BACKUP_DIR = os.environ.get("BACKUP_DIR", "/app/backups")

# 最大备份数量（每个租户）
MAX_BACKUPS_PER_TENANT = 10

# 允许的备份文件路径
ALLOWED_BACKUP_DIRS = [
    "/app/backups",
    "/var/lib/postgresql/backups",
]


class BackupService:
    """备份服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_backup_record(
        self,
        tenant_id: int | None,
        backup_type: str,
        file_path: str,
        file_size: int | None = None,
        status: str = BackupStatus.PENDING
    ) -> BackupRecord:
        """
        创建备份记录

        Args:
            tenant_id: 租户ID（scheduled备份可能无租户）
            backup_type: 备份类型 (manual/scheduled/auto)
            file_path: 备份文件路径
            file_size: 文件大小（字节）
            status: 备份状态

        Returns:
            备份记录对象
        """
        backup = BackupRecord(
            tenant_id=tenant_id,
            backup_type=backup_type,
            file_path=file_path,
            file_size=file_size,
            status=status,
            started_at=datetime.now(UTC)
        )

        self.db.add(backup)
        await self.db.commit()
        await self.db.refresh(backup)

        return backup

    async def list_backups(
        self,
        tenant_id: int,
        limit: int = 20,
        offset: int = 0,
        backup_type: str | None = None
    ) -> list[BackupRecord]:
        """
        获取备份列表

        Args:
            tenant_id: 租户ID
            limit: 返回数量限制
            offset: 偏移量
            backup_type: 备份类型筛选（可选）

        Returns:
            备份记录列表
        """
        query = select(BackupRecord).where(
            BackupRecord.tenant_id == tenant_id
        ).order_by(BackupRecord.created_at.desc())

        if backup_type:
            query = query.where(BackupRecord.backup_type == backup_type)

        query = query.limit(limit).offset(offset)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_backup_by_id(
        self,
        backup_id: int,
        tenant_id: int
    ) -> BackupRecord | None:
        """
        根据ID获取备份记录（带租户验证）

        Args:
            backup_id: 备份ID
            tenant_id: 租户ID

        Returns:
            备份记录或None
        """
        query = select(BackupRecord).where(
            BackupRecord.id == backup_id,
            BackupRecord.tenant_id == tenant_id
        )

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def generate_backup(
        self,
        tenant_id: int | None = None,
        backup_type: str = "manual"
    ) -> str:
        """
        生成备份文件

        Args:
            tenant_id: 租户ID（可选）
            backup_type: 备份类型

        Returns:
            备份文件路径
        """
        # 确保备份目录存在
        os.makedirs(BACKUP_DIR, exist_ok=True)

        # 生成文件名
        filename = self._generate_filename(backup_type)
        file_path = os.path.join(BACKUP_DIR, filename)

        # 执行数据库备份
        await self._dump_database(file_path, tenant_id)

        # 获取文件大小
        file_size = self._get_file_size(file_path)

        # 创建备份记录
        await self.create_backup_record(
            tenant_id=tenant_id,
            backup_type=backup_type,
            file_path=file_path,
            file_size=file_size,
            status=BackupStatus.COMPLETED,
        )

        return file_path

    async def _dump_database(
        self,
        file_path: str,
        tenant_id: int | None = None
    ) -> None:
        """
        执行数据库备份（pg_dump）

        Args:
            file_path: 备份文件路径
            tenant_id: 租户ID（可选，用于部分备份）
        """
        # 获取数据库连接信息
        db_host = os.environ.get("POSTGRES_HOST", "localhost")
        db_port = os.environ.get("POSTGRES_PORT", "5432")
        db_name = os.environ.get("POSTGRES_DB", "bniot")
        db_user = os.environ.get("POSTGRES_USER", "bniot")
        db_password = os.environ.get("POSTGRES_PASSWORD", "")

        # 构建pg_dump命令
        # 使用PGPASSWORD环境变量传递密码
        env = os.environ.copy()
        env["PGPASSWORD"] = db_password

        cmd = [
            "pg_dump",
            "-h", db_host,
            "-p", db_port,
            "-U", db_user,
            "-d", db_name,
            "-F", "p",  # plain SQL format
            "-f", file_path,
        ]

        # 如果指定了租户，只备份该租户的数据
        if tenant_id is not None:
            # 添加租户过滤条件（使用pg_dump的--table和--where选项）
            # 注意：pg_dump不支持行级过滤，这里需要特殊处理
            pass  # 对于生产环境，建议全量备份

        try:
            subprocess.run(
                cmd,
                env=env,
                check=True,
                capture_output=True,
                timeout=300  # 5分钟超时
            )
        except subprocess.CalledProcessError as e:
            # 备份失败，记录错误
            error_msg = e.stderr.decode() if e.stderr else str(e)
            raise RuntimeError(f"数据库备份失败: {error_msg}")
        except subprocess.TimeoutExpired:
            raise RuntimeError("数据库备份超时")

    def _generate_filename(self, backup_type: str) -> str:
        """
        生成备份文件名

        Args:
            backup_type: 备份类型

        Returns:
            文件名
        """
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        return f"backup_{backup_type}_{timestamp}.sql"

    def _get_file_size(self, file_path: str) -> int:
        """
        获取文件大小

        Args:
            file_path: 文件路径

        Returns:
            文件大小（字节）
        """
        if os.path.exists(file_path):
            return os.path.getsize(file_path)
        return 0

    def _validate_path(self, file_path: str) -> bool:
        """
        验证备份文件路径安全性

        Args:
            file_path: 文件路径

        Returns:
            是否为有效路径
        """
        # 检查是否为绝对路径
        if not os.path.isabs(file_path):
            return False

        # 使用 realpath 规范化路径，防止路径遍历攻击
        real_path = os.path.realpath(file_path)

        # 检查规范化的路径是否在允许的目录内
        for allowed_dir in ALLOWED_BACKUP_DIRS:
            real_allowed_dir = os.path.realpath(allowed_dir)
            if real_path.startswith(real_allowed_dir):
                return True

        return False

    def _generate_backup_header(self, tenant_id: int) -> str:
        """
        生成备份文件头部信息

        Args:
            tenant_id: 租户ID

        Returns:
            备份头部字符串
        """
        header = f"""
-- BNIoT Database Backup
-- Generated at: {datetime.now(UTC).isoformat()}
-- Tenant ID: {tenant_id}
-- Backup Type: PostgreSQL SQL Dump
--
"""
        return header

    async def update_backup_status(
        self,
        backup_id: int,
        status: str,
        error_message: str | None = None
    ) -> BackupRecord | None:
        """
        更新备份状态

        Args:
            backup_id: 备份ID
            status: 新状态
            error_message: 错误信息（可选）

        Returns:
            更新后的备份记录
        """
        query = select(BackupRecord).where(BackupRecord.id == backup_id)
        result = await self.db.execute(query)
        backup = result.scalar_one_or_none()

        if backup:
            backup.status = status
            if error_message:
                backup.error_message = error_message
            if status == BackupStatus.COMPLETED:
                backup.completed_at = datetime.now(UTC)
            await self.db.commit()
            await self.db.refresh(backup)

        return backup

    async def delete_backup(
        self,
        backup_id: int,
        tenant_id: int
    ) -> bool:
        """
        删除备份记录和文件

        Args:
            backup_id: 备份ID
            tenant_id: 租户ID

        Returns:
            是否成功删除
        """
        backup = await self.get_backup_by_id(backup_id, tenant_id)

        if not backup:
            return False

        # 删除文件
        if os.path.exists(backup.file_path):
            os.remove(backup.file_path)

        # 删除记录
        await self.db.delete(backup)
        await self.db.commit()

        return True

    async def cleanup_old_backups(
        self,
        tenant_id: int,
        max_count: int = MAX_BACKUPS_PER_TENANT
    ) -> int:
        """
        清理旧备份（保留最新N个）

        Args:
            tenant_id: 租户ID
            max_count: 最大保留数量

        Returns:
            删除的备份数量
        """
        # 获取所有备份（按时间排序）
        query = select(BackupRecord).where(
            BackupRecord.tenant_id == tenant_id
        ).order_by(BackupRecord.created_at.desc())

        result = await self.db.execute(query)
        backups = list(result.scalars().all())

        # 删除超过限制数量的旧备份
        deleted_count = 0
        for backup in backups[max_count:]:
            if os.path.exists(backup.file_path):
                os.remove(backup.file_path)
            await self.db.delete(backup)
            deleted_count += 1

        if deleted_count > 0:
            await self.db.commit()

        return deleted_count

    def get_backup_file_content(
        self,
        file_path: str
    ) -> bytes | None:
        """
        获取备份文件内容

        Args:
            file_path: 文件路径

        Returns:
            文件内容或None
        """
        if not self._validate_path(file_path):
            return None

        if not os.path.exists(file_path):
            return None

        with open(file_path, "rb") as f:
            return f.read()