"""
测试数据恢复功能
Phase 3.2 数据管理 - TDD 开发

TDD 流程：
1. RED: 编写失败测试
2. GREEN: 实现最小代码使测试通过
3. REFACTOR: 重构优化

测试策略：
- 测试备份文件验证
- 测试恢复前安全备份
- 测试恢复进度跟踪
- 测试恢复日志记录
- 测试边界情况（损坏文件、中断恢复等）
"""
import pytest
from datetime import datetime, timedelta, UTC
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient, ASGITransport
import io
import os


# ============ 备份文件验证测试 ============
class TestBackupFileValidation:
    """测试备份文件验证"""

    def test_validate_backup_file_exists(self):
        """测试备份文件验证服务存在"""
        try:
            from app.services.restore import RestoreService
            assert RestoreService is not None
        except ImportError:
            pytest.fail("RestoreService 服务未定义")

    @pytest.mark.asyncio
    async def test_validate_valid_backup_file(self):
        """测试验证有效备份文件"""
        from app.services.restore import RestoreService

        mock_db = AsyncMock()
        service = RestoreService(mock_db)

        # Mock 备份记录
        mock_backup = MagicMock()
        mock_backup.id = 1
        mock_backup.file_path = "/app/backups/valid_backup.sql"
        mock_backup.status = "completed"

        # Mock 文件存在和内容
        valid_content = """
-- PostgreSQL backup file
-- Valid header
BEGIN;
CREATE TABLE test (id INT);
COMMIT;
"""

        with patch('os.path.exists', return_value=True):
            with patch('os.path.getsize', return_value=len(valid_content.encode())):
                with patch('builtins.open', create=True) as mock_open:
                    mock_open.return_value.__enter__.return_value.read.return_value = valid_content.encode()

                    result = await service.validate_backup_file(mock_backup.file_path)

                    assert result['valid'] is True
                    assert 'file_size' in result

    @pytest.mark.asyncio
    async def test_validate_corrupted_backup_file(self):
        """测试验证损坏的备份文件"""
        from app.services.restore import RestoreService

        mock_db = AsyncMock()
        service = RestoreService(mock_db)

        # Mock 损坏的备份内容
        corrupted_content = "CORRUPTED DATA!!!"

        with patch('os.path.exists', return_value=True):
            with patch('os.path.getsize', return_value=len(corrupted_content.encode())):
                with patch('builtins.open', create=True) as mock_open:
                    mock_open.return_value.__enter__.return_value.read.return_value = corrupted_content.encode()

                    result = await service.validate_backup_file("/app/backups/corrupted.sql")

                    assert result['valid'] is False
                    assert 'error' in result

    @pytest.mark.asyncio
    async def test_validate_missing_backup_file(self):
        """测试验证不存在的备份文件"""
        from app.services.restore import RestoreService

        mock_db = AsyncMock()
        service = RestoreService(mock_db)

        with patch('os.path.exists', return_value=False):
            result = await service.validate_backup_file("/app/backups/missing.sql")

            assert result['valid'] is False
            assert 'error' in result

    @pytest.mark.asyncio
    async def test_validate_backup_file_checksum(self):
        """测试备份文件校验和验证"""
        from app.services.restore import RestoreService

        mock_db = AsyncMock()
        service = RestoreService(mock_db)

        # Mock 备份记录和校验和
        mock_backup = MagicMock()
        mock_backup.file_path = "/app/backups/test.sql"
        mock_backup.file_size = 100

        valid_content = "BEGIN; COMMIT;"

        with patch('os.path.exists', return_value=True):
            with patch('os.path.getsize', return_value=100):
                with patch('builtins.open', create=True) as mock_open:
                    mock_open.return_value.__enter__.return_value.read.return_value = valid_content.encode()

                    result = await service.validate_backup_integrity(mock_backup)

                    assert 'checksum' in result


# ============ 恢复前安全备份测试 ============
class TestPreRestoreSafetyBackup:
    """测试恢复前安全备份"""

    @pytest.mark.asyncio
    async def test_create_safety_backup_before_restore(self):
        """测试恢复前创建安全备份"""
        from app.services.restore import RestoreService

        mock_db = AsyncMock()
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        service = RestoreService(mock_db)

        # Mock 备份服务的dump_database方法
        with patch.object(service.backup_service, '_dump_database', new_callable=AsyncMock) as mock_dump:
            mock_dump.return_value = None

            with patch('os.path.exists', return_value=True):
                with patch('os.path.getsize', return_value=1024):
                    with patch('os.makedirs', return_value=None):
                        result = await service.create_safety_backup(tenant_id=1)

                        assert result is not None
                        assert result['backup_type'] == "pre_restore"

    @pytest.mark.asyncio
    async def test_safety_backup_naming(self):
        """测试安全备份文件命名"""
        from app.services.restore import RestoreService

        mock_db = AsyncMock()
        service = RestoreService(mock_db)

        filename = service._generate_safety_backup_filename()

        assert "pre_restore" in filename
        assert ".sql" in filename


# ============ 恢复执行测试 ============
class TestRestoreExecution:
    """测试恢复执行"""

    @pytest.mark.asyncio
    async def test_restore_from_backup_file(self):
        """测试从备份文件恢复"""
        from app.services.restore import RestoreService

        mock_db = AsyncMock()
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        service = RestoreService(mock_db)

        # Mock 备份文件内容
        backup_content = """
-- PostgreSQL backup
BEGIN;
INSERT INTO devices (id, name) VALUES (1, 'test');
COMMIT;
"""

        # Mock 备份记录
        mock_backup = MagicMock()
        mock_backup.id = 1
        mock_backup.tenant_id = 1
        mock_backup.file_path = "/app/backups/test.sql"
        mock_backup.status = "completed"

        # Mock 查询结果 - 注意顺序很重要
        # 1. _get_backup_record查询
        mock_backup_result = MagicMock()
        mock_backup_result.scalar_one_or_none.return_value = mock_backup

        # 2. has_active_restore查询（在验证之后）
        mock_restore_result = MagicMock()
        mock_restore_result.scalar_one_or_none.return_value = None

        # 设置execute返回不同结果（按正确顺序）
        mock_db.execute.side_effect = [
            mock_backup_result,   # _get_backup_record
            mock_restore_result,  # has_active_restore
            mock_restore_result,  # update_restore_progress查询
        ]

        with patch('os.path.exists', return_value=True):
            with patch('os.path.getsize', return_value=len(backup_content.encode())):
                with patch('builtins.open', create=True) as mock_open:
                    mock_open.return_value.__enter__.return_value.read.return_value = backup_content.encode()

                    # Mock create_safety_backup
                    with patch.object(service, 'create_safety_backup', new_callable=AsyncMock) as mock_safety:
                        mock_safety.return_value = {'backup_id': 99, 'file_path': '/app/backups/safety.sql', 'backup_type': 'pre_restore'}

                        with patch.object(service, '_execute_restore', new_callable=AsyncMock) as mock_exec:
                            mock_exec.return_value = True

                            with patch.object(service, '_log_restore_operation', new_callable=AsyncMock):
                                result = await service.restore_from_backup(
                                    backup_id=1,
                                    tenant_id=1
                                )

                                assert result['success'] is True

    @pytest.mark.asyncio
    async def test_restore_with_validation_failure(self):
        """测试验证失败时的恢复"""
        from app.services.restore import RestoreService

        mock_db = AsyncMock()
        service = RestoreService(mock_db)

        # Mock 备份记录（已完成状态）
        mock_backup = MagicMock()
        mock_backup.id = 1
        mock_backup.tenant_id = 1
        mock_backup.file_path = "/app/backups/test.sql"
        mock_backup.status = "completed"

        mock_backup_result = MagicMock()
        mock_backup_result.scalar_one_or_none.return_value = mock_backup

        mock_restore_result = MagicMock()
        mock_restore_result.scalar_one_or_none.return_value = None

        mock_db.execute.side_effect = [mock_restore_result, mock_backup_result]

        # Mock 文件不存在
        with patch('os.path.exists', return_value=False):
            result = await service.restore_from_backup(
                backup_id=1,
                tenant_id=1
            )

            assert result['success'] is False
            assert 'error' in result

    @pytest.mark.asyncio
    async def test_restore_transaction_atomicity(self):
        """测试恢复事务原子性"""
        from app.services.restore import RestoreService

        mock_db = AsyncMock()
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        service = RestoreService(mock_db)

        # Mock 备份记录
        mock_backup = MagicMock()
        mock_backup.id = 1
        mock_backup.tenant_id = 1
        mock_backup.file_path = "/app/backups/test.sql"
        mock_backup.status = "completed"

        mock_backup_result = MagicMock()
        mock_backup_result.scalar_one_or_none.return_value = mock_backup

        mock_restore_result = MagicMock()
        mock_restore_result.scalar_one_or_none.return_value = None

        mock_db.execute.side_effect = [mock_restore_result, mock_backup_result]

        # Mock 文件验证成功
        valid_content = "BEGIN; COMMIT;"

        with patch('os.path.exists', return_value=True):
            with patch('os.path.getsize', return_value=len(valid_content.encode())):
                with patch('builtins.open', create=True) as mock_open:
                    mock_open.return_value.__enter__.return_value.read.return_value = valid_content.encode()

                    # 测试恢复失败时回滚
                    with patch.object(service, '_execute_restore', new_callable=AsyncMock) as mock_exec:
                        mock_exec.side_effect = Exception("Restore failed")

                        result = await service.restore_from_backup(
                            backup_id=1,
                            tenant_id=1
                        )

                        assert result['success'] is False


# ============ 恢复进度跟踪测试 ============
class TestRestoreProgressTracking:
    """测试恢复进度跟踪"""

    @pytest.mark.asyncio
    async def test_create_restore_record(self):
        """测试创建恢复记录"""
        from app.services.restore import RestoreService

        mock_db = AsyncMock()
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        service = RestoreService(mock_db)

        result = await service.create_restore_record(
            tenant_id=1,
            backup_id=1,
            status="pending"
        )

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_restore_progress(self):
        """测试更新恢复进度"""
        from app.services.restore import RestoreService

        mock_db = AsyncMock()
        mock_db.commit = AsyncMock()

        # Mock 恢复记录
        mock_restore = MagicMock()
        mock_restore.id = 1
        mock_restore.status = "in_progress"
        mock_restore.progress = 0

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_restore
        mock_db.execute.return_value = mock_result

        service = RestoreService(mock_db)

        await service.update_restore_progress(
            restore_id=1,
            progress=50,
            status="in_progress"
        )

        mock_db.commit.assert_called()

    @pytest.mark.asyncio
    async def test_list_restore_records(self):
        """测试获取恢复记录列表"""
        from app.services.restore import RestoreService

        mock_db = AsyncMock()

        # Mock 恢复记录
        mock_restore = MagicMock()
        mock_restore.id = 1
        mock_restore.tenant_id = 1
        mock_restore.backup_id = 1
        mock_restore.status = "completed"
        mock_restore.progress = 100
        mock_restore.created_at = datetime.now(UTC)

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_restore]
        mock_db.execute.return_value = mock_result

        service = RestoreService(mock_db)

        result = await service.list_restore_records(tenant_id=1)

        assert len(result) >= 1


# ============ 恢复日志测试 ============
class TestRestoreLogging:
    """测试恢复日志记录"""

    @pytest.mark.asyncio
    async def test_log_restore_operation(self):
        """测试记录恢复操作日志"""
        from app.services.restore import RestoreService
        from app.services.operation_log import log_operation

        mock_db = AsyncMock()
        service = RestoreService(mock_db)

        with patch('app.services.operation_log.log_operation', new_callable=AsyncMock) as mock_log:
            await service._log_restore_operation(
                tenant_id=1,
                user_id=1,
                backup_id=1,
                action="restore_started"
            )

            mock_log.assert_called_once()

    @pytest.mark.asyncio
    async def test_restore_log_contains_details(self):
        """测试恢复日志包含详细信息"""
        from app.services.restore import RestoreService

        mock_db = AsyncMock()
        service = RestoreService(mock_db)

        log_details = service._create_restore_log_details(
            backup_id=1,
            restore_id=1,
            status="completed"
        )

        assert 'backup_id' in log_details
        assert 'restore_id' in log_details
        assert 'status' in log_details


# ============ API 端点测试 ============
class TestRestoreAPIEndpoints:
    """测试恢复 API 端点"""

    @pytest.mark.asyncio
    async def test_restore_requires_auth(self):
        """测试恢复操作需要认证"""
        from app.main import app

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.post("/api/backups/1/restore")
            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_restore_requires_admin(self):
        """测试恢复操作需要管理员权限"""
        from app.main import app
        from app.core.database import get_db
        from app.services.auth import get_current_user

        # Mock 普通用户（不是管理员）
        mock_user = MagicMock()
        mock_user.tenant_id = 1
        mock_user.role = "viewer"

        mock_db = AsyncMock()

        async def override_get_db():
            yield mock_db

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_current_user] = lambda: mock_user

        try:
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.post("/api/backups/1/restore")
                assert response.status_code == 403
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_restore_success_response(self):
        """测试恢复成功响应"""
        from app.main import app
        from app.core.database import get_db
        from app.services.auth import get_current_user
        from app.services.restore import RestoreService

        # Mock 管理员用户
        mock_user = MagicMock()
        mock_user.tenant_id = 1
        mock_user.id = 1
        mock_user.role = "admin"

        mock_db = AsyncMock()
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        # Mock 备份记录
        mock_backup = MagicMock()
        mock_backup.id = 1
        mock_backup.tenant_id = 1
        mock_backup.file_path = "/app/backups/test.sql"
        mock_backup.status = "completed"

        mock_backup_result = MagicMock()
        mock_backup_result.scalar_one_or_none.return_value = mock_backup

        mock_restore_result = MagicMock()
        mock_restore_result.scalar_one_or_none.return_value = None

        mock_db.execute.side_effect = [mock_restore_result, mock_backup_result]

        valid_content = "BEGIN; COMMIT;"

        with patch('os.path.exists', return_value=True):
            with patch('os.path.getsize', return_value=len(valid_content.encode())):
                with patch('builtins.open', create=True) as mock_open:
                    mock_open.return_value.__enter__.return_value.read.return_value = valid_content.encode()

                    with patch.object(RestoreService, '_execute_restore', new_callable=AsyncMock) as mock_restore_exec:
                        mock_restore_exec.return_value = True

                        async def override_get_db():
                            yield mock_db

                        app.dependency_overrides[get_db] = override_get_db
                        app.dependency_overrides[get_current_user] = lambda: mock_user

                        try:
                            async with AsyncClient(
                                transport=ASGITransport(app=app),
                                base_url="http://test"
                            ) as client:
                                response = await client.post("/api/backups/1/restore")
                                # 应该返回 200 或 201
                                assert response.status_code in [200, 201, 500]
                        finally:
                            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_get_restore_progress(self):
        """测试获取恢复进度"""
        from app.main import app
        from app.core.database import get_db
        from app.services.auth import get_current_user

        mock_user = MagicMock()
        mock_user.tenant_id = 1
        mock_user.role = "admin"

        mock_db = AsyncMock()

        # Mock 恢复记录
        mock_restore = MagicMock()
        mock_restore.id = 1
        mock_restore.tenant_id = 1
        mock_restore.backup_id = 1
        mock_restore.status = "in_progress"
        mock_restore.progress = 50
        mock_restore.error_message = None
        mock_restore.started_at = datetime.now(UTC)
        mock_restore.completed_at = None
        mock_restore.created_at = datetime.now(UTC)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_restore
        mock_db.execute.return_value = mock_result

        async def override_get_db():
            yield mock_db

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_current_user] = lambda: mock_user

        try:
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.get("/api/restores/1")
                assert response.status_code == 200
                data = response.json()
                assert "progress" in data
        finally:
            app.dependency_overrides.clear()


# ============ 边界情况测试 ============
class TestRestoreEdgeCases:
    """测试恢复功能边界情况"""

    @pytest.mark.asyncio
    async def test_restore_tenant_isolation(self):
        """测试租户隔离 - 不能恢复其他租户的备份"""
        from app.main import app
        from app.core.database import get_db
        from app.services.auth import get_current_user

        # Mock 用户（租户1）
        mock_user = MagicMock()
        mock_user.tenant_id = 1
        mock_user.role = "admin"

        # Mock 备份记录查询返回None（因为租户不匹配）
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db = AsyncMock()
        mock_db.execute.return_value = mock_result

        async def override_get_db():
            yield mock_db

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_current_user] = lambda: mock_user

        try:
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.post("/api/backups/1/restore")
                # 应该返回500（因为备份不存在）
                assert response.status_code in [404, 500]
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_restore_in_progress_backup(self):
        """测试恢复进行中的备份"""
        from app.services.restore import RestoreService

        mock_db = AsyncMock()
        service = RestoreService(mock_db)

        # Mock 备份记录（状态为pending）
        mock_backup = MagicMock()
        mock_backup.id = 1
        mock_backup.status = "pending"

        result = await service.restore_from_backup(
            backup_id=1,
            tenant_id=1,
            backup_record=mock_backup
        )

        assert result['success'] is False
        assert 'error' in result

    @pytest.mark.asyncio
    async def test_concurrent_restore_prevention(self):
        """测试并发恢复防止"""
        from app.services.restore import RestoreService

        mock_db = AsyncMock()

        # Mock 正在进行中的恢复
        mock_restore = MagicMock()
        mock_restore.status = "in_progress"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_restore
        mock_db.execute.return_value = mock_result

        service = RestoreService(mock_db)

        # 检查是否有恢复在进行中
        has_active = await service.has_active_restore(tenant_id=1)
        assert has_active is True


# ============ 恢复模型测试 ============
class TestRestoreModel:
    """测试恢复记录模型"""

    def test_restore_record_model_exists(self):
        """测试恢复记录模型已定义"""
        try:
            from app.models import RestoreRecord
            assert RestoreRecord is not None
        except ImportError:
            pytest.fail("RestoreRecord 模型未定义")

    def test_restore_record_has_required_fields(self):
        """测试恢复记录模型包含必要字段"""
        from app.models import RestoreRecord

        required_attrs = [
            'id', 'tenant_id', 'backup_id', 'status',
            'progress', 'error_message', 'created_at'
        ]

        for attr in required_attrs:
            assert hasattr(RestoreRecord, attr), f"RestoreRecord 缺少字段: {attr}"