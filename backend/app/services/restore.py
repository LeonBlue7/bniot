"""
数据恢复服务模块
Phase 3.2 数据管理

提供备份文件验证、恢复执行、进度跟踪、恢复日志等功能
"""
import hashlib
import logging
import os
import subprocess
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import BackupRecord, BackupStatus, RestoreRecord
from app.services.backup import BACKUP_DIR, BackupService

logger = logging.getLogger(__name__)


# 恢复状态枚举
class RestoreStatus:
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class RestoreService:
    """数据恢复服务"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.backup_service = BackupService(db)

    async def validate_backup_file(self, file_path: str) -> dict[str, Any]:
        """
        验证备份文件

        Args:
            file_path: 备份文件路径

        Returns:
            验证结果字典
        """
        result = {
            'valid': False,
            'file_path': file_path,
            'error': None,
            'file_size': 0,
            'checksum': None
        }

        # 检查文件存在
        if not os.path.exists(file_path):
            result['error'] = '备份文件不存在'
            return result

        # 获取文件大小
        result['file_size'] = os.path.getsize(file_path)

        # 读取并验证文件内容
        try:
            with open(file_path, 'rb') as f:
                content = f.read()

            # 计算校验和
            result['checksum'] = self._calculate_checksum(content)

            # 验证文件格式（检查是否包含基本的SQL结构）
            content_str = content.decode('utf-8', errors='ignore')

            # 检查是否包含有效的SQL语句
            valid_indicators = ['BEGIN', 'COMMIT', 'CREATE', 'INSERT', '--']
            if any(indicator in content_str for indicator in valid_indicators):
                result['valid'] = True
            else:
                result['error'] = '备份文件格式无效或损坏'

        except Exception as e:
            result['error'] = f'读取备份文件失败: {str(e)}'

        return result

    async def validate_backup_integrity(self, backup: BackupRecord) -> dict[str, Any]:
        """
        验证备份完整性

        Args:
            backup: 备份记录对象

        Returns:
            验证结果字典
        """
        result = await self.validate_backup_file(backup.file_path)

        # 添加额外信息
        result['backup_id'] = backup.id
        result['backup_status'] = backup.status

        return result

    def _calculate_checksum(self, content: bytes) -> str:
        """
        计算文件校验和

        Args:
            content: 文件内容

        Returns:
            SHA256校验和
        """
        return hashlib.sha256(content).hexdigest()

    async def create_safety_backup(self, tenant_id: int) -> dict[str, Any]:
        """
        创建恢复前的安全备份

        Args:
            tenant_id: 租户ID

        Returns:
            安全备份信息
        """
        # 生成安全备份文件名
        filename = self._generate_safety_backup_filename()
        file_path = os.path.join(BACKUP_DIR, filename)

        # 执行备份
        await self.backup_service._dump_database(file_path, tenant_id)

        # 获取文件大小
        file_size = self.backup_service._get_file_size(file_path)

        # 创建备份记录
        safety_backup = await self.backup_service.create_backup_record(
            tenant_id=tenant_id,
            backup_type="pre_restore",
            file_path=file_path,
            file_size=file_size,
            status=BackupStatus.COMPLETED
        )

        return {
            'backup_id': safety_backup.id,
            'file_path': file_path,
            'backup_type': 'pre_restore'
        }

    def _generate_safety_backup_filename(self) -> str:
        """
        生成安全备份文件名

        Returns:
            文件名
        """
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        return f"pre_restore_backup_{timestamp}.sql"

    async def create_restore_record(
        self,
        tenant_id: int,
        backup_id: int,
        status: str = RestoreStatus.PENDING,
        safety_backup_id: int | None = None
    ) -> RestoreRecord:
        """
        创建恢复记录

        Args:
            tenant_id: 租户ID
            backup_id: 备份ID
            status: 恢复状态
            safety_backup_id: 安全备份ID

        Returns:
            恢复记录对象
        """
        restore = RestoreRecord(
            tenant_id=tenant_id,
            backup_id=backup_id,
            status=status,
            safety_backup_id=safety_backup_id,
            started_at=datetime.now(UTC) if status == RestoreStatus.IN_PROGRESS else None
        )

        self.db.add(restore)
        await self.db.commit()
        await self.db.refresh(restore)

        return restore

    async def restore_from_backup(
        self,
        backup_id: int,
        tenant_id: int,
        backup_record: BackupRecord | None = None
    ) -> dict[str, Any]:
        """
        从备份文件恢复数据

        Args:
            backup_id: 备份ID
            tenant_id: 租户ID
            backup_record: 备份记录对象（可选，用于验证状态）

        Returns:
            恢复结果字典
        """
        result = {
            'success': False,
            'restore_id': None,
            'error': None
        }

        # 获取备份记录
        if backup_record is None:
            backup_record = await self._get_backup_record(backup_id, tenant_id)

        if backup_record is None:
            result['error'] = '备份不存在'
            return result

        # 验证备份状态
        if backup_record.status != BackupStatus.COMPLETED:
            result['error'] = '备份未完成或状态无效'
            return result

        # 验证备份文件
        validation = await self.validate_backup_file(backup_record.file_path)
        if not validation['valid']:
            result['error'] = validation['error']
            return result

        # 检查是否有正在进行的恢复
        if await self.has_active_restore(tenant_id):
            result['error'] = '已有恢复任务正在进行中'
            return result

        try:
            # 创建安全备份
            safety_backup = await self.create_safety_backup(tenant_id)

            # 创建恢复记录
            restore_record = await self.create_restore_record(
                tenant_id=tenant_id,
                backup_id=backup_id,
                status=RestoreStatus.IN_PROGRESS,
                safety_backup_id=safety_backup['backup_id']
            )

            result['restore_id'] = restore_record.id

            # 执行恢复
            success = await self._execute_restore(backup_record.file_path, tenant_id)

            if success:
                # 更新恢复状态为完成
                await self.update_restore_progress(
                    restore_id=restore_record.id,
                    progress=100,
                    status=RestoreStatus.COMPLETED
                )
                result['success'] = True

                # 记录操作日志
                await self._log_restore_operation(
                    tenant_id=tenant_id,
                    user_id=None,  # API层会传入
                    backup_id=backup_id,
                    action="restore_completed"
                )
            else:
                # 回滚恢复
                await self._rollback_restore(safety_backup['file_path'], tenant_id)

                await self.update_restore_progress(
                    restore_id=restore_record.id,
                    progress=0,
                    status=RestoreStatus.ROLLED_BACK,
                    error_message="恢复失败，已回滚"
                )
                result['error'] = '恢复执行失败'

        except Exception as e:
            result['error'] = f'恢复过程出错: {str(e)}'

            # 记录失败日志
            await self._log_restore_operation(
                tenant_id=tenant_id,
                user_id=None,
                backup_id=backup_id,
                action="restore_failed"
            )

        return result

    async def _get_backup_record(
        self,
        backup_id: int,
        tenant_id: int
    ) -> BackupRecord | None:
        """
        获取备份记录

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

    async def _execute_restore(
        self,
        file_path: str,
        tenant_id: int
    ) -> bool:
        """
        执行恢复（pg_restore）

        Args:
            file_path: 备份文件路径
            tenant_id: 租户ID

        Returns:
            是否成功
        """
        # 获取数据库连接信息
        db_host = os.environ.get("POSTGRES_HOST", "localhost")
        db_port = os.environ.get("POSTGRES_PORT", "5432")
        db_name = os.environ.get("POSTGRES_DB", "bniot")
        db_user = os.environ.get("POSTGRES_USER", "bniot")
        db_password = os.environ.get("POSTGRES_PASSWORD", "")

        # 构建psql命令（恢复SQL文件）
        env = os.environ.copy()
        env["PGPASSWORD"] = db_password

        cmd = [
            "psql",
            "-h", db_host,
            "-p", db_port,
            "-U", db_user,
            "-d", db_name,
            "-f", file_path,
            "-v", "ON_ERROR_STOP=1",  # 遇到错误立即停止
            "--single-transaction"  # 单事务执行
        ]

        try:
            subprocess.run(
                cmd,
                env=env,
                check=True,
                capture_output=True,
                timeout=600  # 10分钟超时
            )
            return True
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.decode() if e.stderr else str(e)
            logger.error("恢复失败: %s", error_msg)
            return False
        except subprocess.TimeoutExpired:
            logger.error("恢复超时")
            return False

    async def _rollback_restore(
        self,
        safety_backup_path: str,
        tenant_id: int
    ) -> bool:
        """
        回滚恢复（使用安全备份）

        Args:
            safety_backup_path: 安全备份文件路径
            tenant_id: 租户ID

        Returns:
            是否成功
        """
        # 使用安全备份重新恢复
        return await self._execute_restore(safety_backup_path, tenant_id)

    async def update_restore_progress(
        self,
        restore_id: int,
        progress: int,
        status: str,
        error_message: str | None = None
    ) -> RestoreRecord | None:
        """
        更新恢复进度

        Args:
            restore_id: 恢复ID
            progress: 进度（0-100）
            status: 状态
            error_message: 错误信息

        Returns:
            更新后的恢复记录
        """
        query = select(RestoreRecord).where(RestoreRecord.id == restore_id)
        result = await self.db.execute(query)
        restore = result.scalar_one_or_none()

        if restore:
            restore.progress = progress
            restore.status = status
            if error_message:
                restore.error_message = error_message
            if status == RestoreStatus.COMPLETED:
                restore.completed_at = datetime.now(UTC)
            await self.db.commit()
            await self.db.refresh(restore)

        return restore

    async def list_restore_records(
        self,
        tenant_id: int,
        limit: int = 20,
        offset: int = 0
    ) -> list[RestoreRecord]:
        """
        获取恢复记录列表

        Args:
            tenant_id: 租户ID
            limit: 返回数量限制
            offset: 偏移量

        Returns:
            恢复记录列表
        """
        query = select(RestoreRecord).where(
            RestoreRecord.tenant_id == tenant_id
        ).order_by(RestoreRecord.created_at.desc()).limit(limit).offset(offset)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def has_active_restore(self, tenant_id: int) -> bool:
        """
        检查是否有正在进行的恢复

        Args:
            tenant_id: 租户ID

        Returns:
            是否有活跃恢复
        """
        query = select(RestoreRecord).where(
            RestoreRecord.tenant_id == tenant_id,
            RestoreRecord.status == RestoreStatus.IN_PROGRESS
        )

        result = await self.db.execute(query)
        return result.scalar_one_or_none() is not None

    async def get_restore_record(
        self,
        restore_id: int,
        tenant_id: int
    ) -> RestoreRecord | None:
        """
        获取恢复记录

        Args:
            restore_id: 恢复ID
            tenant_id: 租户ID

        Returns:
            恢复记录或None
        """
        query = select(RestoreRecord).where(
            RestoreRecord.id == restore_id,
            RestoreRecord.tenant_id == tenant_id
        )

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def _log_restore_operation(
        self,
        tenant_id: int,
        user_id: int | None,
        backup_id: int,
        action: str
    ) -> None:
        """
        记录恢复操作日志

        Args:
            tenant_id: 租户ID
            user_id: 用户ID
            backup_id: 备份ID
            action: 操作类型
        """
        try:
            from app.services.operation_log import log_operation

            await log_operation(
                db=self.db,
                tenant_id=tenant_id,
                user_id=user_id,
                action=action,
                resource_type="backup",
                resource_id=str(backup_id),
                details=self._create_restore_log_details(backup_id, None, action)
            )
        except Exception as e:
            logger.error("记录操作日志失败: %s", e)

    def _create_restore_log_details(
        self,
        backup_id: int,
        restore_id: int | None,
        status: str
    ) -> dict[str, Any]:
        """
        创建恢复日志详情

        Args:
            backup_id: 备份ID
            restore_id: 恢复ID
            status: 状态

        Returns:
            日志详情字典
        """
        return {
            'backup_id': backup_id,
            'restore_id': restore_id,
            'status': status,
            'timestamp': datetime.now(UTC).isoformat()
        }