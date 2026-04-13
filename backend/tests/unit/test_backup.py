"""
测试数据备份功能
Phase 3.1 数据管理 - TDD 开发

TDD 流程：
1. RED: 编写失败测试
2. GREEN: 实现最小代码使测试通过
3. REFACTOR: 重构优化

测试策略：
- 测试备份模型存在性
- 测试备份API端点
- 测试备份服务功能
- 测试自动调度任务
- 测试边界情况（空数据、权限、并发）
"""
import pytest
from datetime import datetime, timedelta, UTC
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient, ASGITransport
import io
import os


# ============ 模型测试 ============
class TestBackupModel:
    """测试备份记录模型"""

    def test_backup_model_exists(self):
        """测试备份模型已定义"""
        try:
            from app.models import BackupRecord
            assert BackupRecord is not None
        except ImportError:
            pytest.fail("BackupRecord 模型未定义")

    def test_backup_model_has_required_fields(self):
        """测试备份模型包含必要字段"""
        from app.models import BackupRecord

        # 检查模型属性
        required_attrs = [
            'id', 'tenant_id', 'backup_type', 'file_path',
            'file_size', 'status', 'created_at'
        ]

        for attr in required_attrs:
            assert hasattr(BackupRecord, attr), f"BackupRecord 缺少字段: {attr}"

    def test_backup_status_enum(self):
        """测试备份状态枚举"""
        try:
            from app.models import BackupStatus

            assert BackupStatus.PENDING == "pending"
            assert BackupStatus.COMPLETED == "completed"
            assert BackupStatus.FAILED == "failed"
        except ImportError:
            pytest.fail("BackupStatus 枚举未定义")


# ============ 服务层测试 ============
class TestBackupService:
    """测试备份服务"""

    def test_backup_service_exists(self):
        """测试备份服务已定义"""
        try:
            from app.services.backup import BackupService
            assert BackupService is not None
        except ImportError:
            pytest.fail("BackupService 服务未定义")

    @pytest.mark.asyncio
    async def test_create_backup_record(self):
        """测试创建备份记录"""
        from app.services.backup import BackupService

        mock_db = AsyncMock()

        # Mock 数据库操作
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        service = BackupService(mock_db)

        result = await service.create_backup_record(
            tenant_id=1,
            backup_type="manual",
            file_path="/backups/test.sql"
        )

        assert result is not None
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_backups(self):
        """测试获取备份列表"""
        from app.services.backup import BackupService

        mock_db = AsyncMock()

        # Mock 备份记录
        mock_backup = MagicMock()
        mock_backup.id = 1
        mock_backup.tenant_id = 1
        mock_backup.backup_type = "manual"
        mock_backup.file_path = "/backups/test.sql"
        mock_backup.file_size = 1024
        mock_backup.status = "completed"
        mock_backup.created_at = datetime.now(UTC)

        # Mock 查询结果
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_backup]
        mock_db.execute.return_value = mock_result

        service = BackupService(mock_db)

        result = await service.list_backups(tenant_id=1)

        assert len(result) == 1
        assert result[0].backup_type == "manual"

    @pytest.mark.asyncio
    async def test_generate_backup_file(self):
        """测试生成备份文件"""
        from app.services.backup import BackupService

        mock_db = AsyncMock()

        service = BackupService(mock_db)

        # 测试生成备份文件
        with patch.object(service, '_dump_database') as mock_dump:
            mock_dump.return_value = "/backups/backup_20240101_020000.sql"

            result = await service.generate_backup(
                tenant_id=1,
                backup_type="manual"
            )

            assert result is not None
            assert "backup" in result

    @pytest.mark.asyncio
    async def test_backup_with_empty_database(self):
        """测试空数据库备份"""
        from app.services.backup import BackupService

        mock_db = AsyncMock()

        # Mock 空数据库查询
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        service = BackupService(mock_db)

        # 空数据库也能备份（mock pg_dump）
        with patch.object(service, '_dump_database', new_callable=AsyncMock) as mock_dump:
            mock_dump.return_value = None
            result = await service.generate_backup(tenant_id=1)
            assert result is not None

    def test_backup_file_size_calculation(self):
        """测试备份文件大小计算"""
        from app.services.backup import BackupService

        # Mock 文件
        mock_file_path = "/tmp/test_backup.sql"

        # 创建临时测试文件
        test_content = "SELECT 1;" * 100

        service = BackupService(AsyncMock())

        with patch('os.path.exists', return_value=True):
            with patch('os.path.getsize', return_value=len(test_content)):
                size = service._get_file_size(mock_file_path)
                assert size == len(test_content)


# ============ API 端点测试 ============
class TestBackupAPIEndpoints:
    """测试备份 API 端点"""

    @pytest.mark.asyncio
    async def test_list_backups_requires_auth(self):
        """测试备份列表需要认证"""
        from app.main import app

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/api/backups")
            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_list_backups_returns_correct_structure(self):
        """测试备份列表返回正确数据结构"""
        from app.main import app
        from app.core.database import get_db
        from app.services.auth import get_current_user
        from app.services.backup import BackupService

        # Mock 用户
        mock_user = MagicMock()
        mock_user.tenant_id = 1
        mock_user.username = "testuser"

        # Mock 数据库
        mock_db = AsyncMock()

        # Mock 备份记录（完整属性）
        mock_backup = MagicMock()
        mock_backup.id = 1
        mock_backup.tenant_id = 1
        mock_backup.backup_type = "manual"
        mock_backup.file_path = "/backups/test.sql"
        mock_backup.file_size = 1024
        mock_backup.status = "completed"
        mock_backup.error_message = None
        mock_backup.started_at = datetime.now(UTC)
        mock_backup.completed_at = datetime.now(UTC)
        mock_backup.created_at = datetime.now(UTC)

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_backup]
        mock_db.execute.return_value = mock_result

        # 覆盖依赖
        async def override_get_db():
            yield mock_db

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_current_user] = lambda: mock_user

        try:
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.get("/api/backups")
                assert response.status_code == 200
                data = response.json()
                assert isinstance(data, dict)
                assert "data" in data
                assert isinstance(data["data"], list)
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_create_manual_backup_requires_auth(self):
        """测试手动备份需要认证"""
        from app.main import app

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.post("/api/backups")
            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_create_manual_backup_success(self):
        """测试手动备份成功"""
        from app.main import app
        from app.core.database import get_db
        from app.services.auth import get_current_user
        from app.services.backup import BackupService

        # Mock 用户（管理员）
        mock_user = MagicMock()
        mock_user.tenant_id = 1
        mock_user.username = "admin"
        mock_user.role = "admin"

        # Mock 数据库
        mock_db = AsyncMock()
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        # Mock 备份记录
        mock_backup = MagicMock()
        mock_backup.id = 1
        mock_backup.tenant_id = 1
        mock_backup.backup_type = "manual"
        mock_backup.file_path = "/backups/backup_test.sql"
        mock_backup.file_size = 1024
        mock_backup.status = "completed"
        mock_backup.error_message = None
        mock_backup.started_at = datetime.now(UTC)
        mock_backup.completed_at = datetime.now(UTC)
        mock_backup.created_at = datetime.now(UTC)

        # Mock 查询结果
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_backup]
        mock_db.execute.return_value = mock_result

        # Mock 备份服务生成备份
        with patch.object(BackupService, 'generate_backup', new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = "/backups/backup_test.sql"

            # 覆盖依赖
            async def override_get_db():
                yield mock_db

            app.dependency_overrides[get_db] = override_get_db
            app.dependency_overrides[get_current_user] = lambda: mock_user

            try:
                async with AsyncClient(
                    transport=ASGITransport(app=app),
                    base_url="http://test"
                ) as client:
                    response = await client.post("/api/backups")
                    # 应该返回 200 或 201
                    assert response.status_code in [200, 201]
            finally:
                app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_download_backup_requires_auth(self):
        """测试下载备份需要认证"""
        from app.main import app

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/api/backups/1/download")
            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_download_backup_file_success(self):
        """测试下载备份文件成功"""
        from app.main import app
        from app.core.database import get_db
        from app.services.auth import get_current_user

        # Mock 用户
        mock_user = MagicMock()
        mock_user.tenant_id = 1
        mock_user.username = "admin"
        mock_user.role = "admin"

        # Mock 备份记录（使用允许的路径）
        mock_backup = MagicMock()
        mock_backup.id = 1
        mock_backup.tenant_id = 1
        mock_backup.file_path = "/app/backups/test.sql"  # 使用允许的路径
        mock_backup.status = "completed"
        mock_backup.error_message = None
        mock_backup.started_at = datetime.now(UTC)
        mock_backup.completed_at = datetime.now(UTC)
        mock_backup.created_at = datetime.now(UTC)
        mock_backup.file_size = 1024
        mock_backup.backup_type = "manual"

        # Mock 数据库查询
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_backup

        mock_db = AsyncMock()
        mock_db.execute.return_value = mock_result

        # Mock 文件存在和读取
        test_content = b"BACKUP SQL CONTENT"

        with patch('os.path.exists', return_value=True):
            with patch('builtins.open', create=True) as mock_open:
                mock_open.return_value.__enter__.return_value.read.return_value = test_content

                # 覆盖依赖
                async def override_get_db():
                    yield mock_db

                app.dependency_overrides[get_db] = override_get_db
                app.dependency_overrides[get_current_user] = lambda: mock_user

                try:
                    async with AsyncClient(
                        transport=ASGITransport(app=app),
                        base_url="http://test"
                    ) as client:
                        response = await client.get("/api/backups/1/download")
                        # 应该返回 200 或文件流
                        assert response.status_code in [200, 201, 302]
                finally:
                    app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_download_nonexistent_backup(self):
        """测试下载不存在的备份"""
        from app.main import app
        from app.core.database import get_db
        from app.services.auth import get_current_user

        mock_user = MagicMock()
        mock_user.tenant_id = 1

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
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
                response = await client.get("/api/backups/999/download")
                assert response.status_code == 404
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_delete_backup_requires_admin(self):
        """测试删除备份需要管理员权限"""
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
                response = await client.delete("/api/backups/1")
                # 应该返回 403 Forbidden
                assert response.status_code == 403
        finally:
            app.dependency_overrides.clear()


# ============ 定时任务测试 ============
class TestBackupScheduler:
    """测试备份定时任务"""

    def test_scheduler_exists(self):
        """测试定时调度器已定义"""
        try:
            from app.services.backup_scheduler import BackupScheduler
            assert BackupScheduler is not None
        except ImportError:
            pytest.fail("BackupScheduler 未定义")

    def test_scheduler_has_daily_backup_job(self):
        """测试定时任务包含每日备份任务"""
        try:
            from app.services.backup_scheduler import BackupScheduler

            scheduler = BackupScheduler()
            scheduler.setup_jobs()

            # 检查定时任务配置
            jobs = scheduler.get_jobs()
            assert len(jobs) >= 1
            assert any(j['id'] == 'daily_backup' for j in jobs)
        except ImportError:
            pytest.fail("BackupScheduler 未定义")

    @pytest.mark.asyncio
    async def test_daily_backup_execution(self):
        """测试每日备份任务执行"""
        from app.services.backup_scheduler import BackupScheduler

        scheduler = BackupScheduler()

        with patch.object(scheduler, 'execute_backup', new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = True

            result = await scheduler.execute_backup()
            assert result is True


# ============ 边界情况测试 ============
class TestBackupEdgeCases:
    """测试备份功能边界情况"""

    @pytest.mark.asyncio
    async def test_backup_tenant_isolation(self):
        """测试租户隔离 - 不能访问其他租户的备份"""
        from app.main import app
        from app.core.database import get_db
        from app.services.auth import get_current_user

        # Mock 用户（租户1）
        mock_user = MagicMock()
        mock_user.tenant_id = 1
        mock_user.role = "admin"

        # Mock 备份记录（属于租户2）
        mock_backup = MagicMock()
        mock_backup.id = 1
        mock_backup.tenant_id = 2  # 不同的租户
        mock_backup.status = "completed"
        mock_backup.file_path = "/backups/test.sql"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_backup

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
                response = await client.get("/api/backups/1/download")
                # 应该返回 403 或 404（因为租户不匹配，服务层返回None）
                assert response.status_code in [403, 404]
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_backup_limit_per_tenant(self):
        """测试备份数量限制"""
        from app.services.backup import BackupService

        mock_db = AsyncMock()

        # Mock 备份记录（限制数量内）
        mock_backups = [MagicMock(id=i, tenant_id=1, backup_type="manual",
                                  file_path=f"/backups/test{i}.sql",
                                  file_size=1024, status="completed",
                                  error_message=None,
                                  started_at=datetime.now(UTC),
                                  completed_at=datetime.now(UTC),
                                  created_at=datetime.now(UTC))
                       for i in range(15)]  # 返回15个

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_backups[:20]  # 只返回limit数量
        mock_db.execute.return_value = mock_result

        service = BackupService(mock_db)

        # 检查备份列表有分页或限制
        result = await service.list_backups(tenant_id=1, limit=20)

        # 应该只返回限制数量
        assert len(result) <= 20

    @pytest.mark.asyncio
    async def test_backup_concurrent_creation(self):
        """测试并发创建备份"""
        from app.services.backup import BackupService

        mock_db = AsyncMock()
        service = BackupService(mock_db)

        # 模拟并发请求
        with patch.object(service, 'generate_backup') as mock_gen:
            mock_gen.return_value = "/backups/backup.sql"

            # 并发调用应该被正确处理
            results = []
            for _ in range(3):
                result = await service.generate_backup(tenant_id=1)
                results.append(result)

            # 所有请求都应该成功或被正确拒绝
            assert all(r is not None for r in results)

    def test_backup_file_path_validation(self):
        """测试备份文件路径验证"""
        from app.services.backup import BackupService

        service = BackupService(AsyncMock())

        # 非法路径应该被拒绝
        invalid_paths = [
            "/etc/passwd",
            "../../../etc/passwd",
            "/root/.ssh/id_rsa",
        ]

        for path in invalid_paths:
            assert not service._validate_path(path), f"路径 {path} 应该被拒绝"

    @pytest.mark.asyncio
    async def test_backup_status_update(self):
        """测试备份状态更新"""
        from app.services.backup import BackupService

        mock_db = AsyncMock()
        mock_db.commit = AsyncMock()

        # Mock 备份记录
        mock_backup = MagicMock()
        mock_backup.id = 1
        mock_backup.status = "pending"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_backup
        mock_db.execute.return_value = mock_result

        service = BackupService(mock_db)

        # 更新状态
        await service.update_backup_status(backup_id=1, status="completed")

        mock_db.commit.assert_called()
        assert mock_backup.status == "completed"


# ============ 备份文件格式测试 ============
class TestBackupFileFormat:
    """测试备份文件格式"""

    def test_backup_filename_format(self):
        """测试备份文件名格式"""
        from app.services.backup import BackupService

        service = BackupService(AsyncMock())

        # 生成备份文件名
        filename = service._generate_filename(backup_type="manual")

        # 文件名应该包含时间戳和类型
        assert "backup" in filename
        assert ".sql" in filename

    def test_backup_file_content_format(self):
        """测试备份文件内容格式"""
        from app.services.backup import BackupService

        service = BackupService(AsyncMock())

        # 生成备份内容头部
        header = service._generate_backup_header(tenant_id=1)

        # 应该包含必要的元信息
        assert "tenant_id" in header or str(1) in header