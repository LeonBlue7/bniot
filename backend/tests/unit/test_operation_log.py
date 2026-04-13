"""
测试操作日志系统
Phase 1.2 操作日志系统
"""
import pytest
from datetime import datetime, UTC, timedelta
from unittest.mock import MagicMock, patch

from fastapi import HTTPException
from sqlalchemy import select


class TestOperationLogService:
    """测试操作日志服务"""

    @pytest.mark.asyncio
    async def test_log_device_create(self, db_session):
        """测试记录设备创建操作"""
        from app.services.operation_log import OperationLogService
        from app.models import Tenant, User, Device, OperationLog

        # 创建租户和用户
        tenant = Tenant(name="租户", code="test_log")
        db_session.add(tenant)
        await db_session.commit()

        user = User(
            tenant_id=tenant.id,
            username="operator",
            password_hash="hash",
            role="operator"
        )
        db_session.add(user)
        await db_session.commit()

        # 记录操作日志
        log_service = OperationLogService()
        await log_service.log(
            db_session,
            user=user,
            action="create_device",
            resource_type="device",
            resource_id="IMEI001",
            details={"name": "空调1", "zone_id": None},
            ip_address="192.168.1.1"
        )
        await db_session.commit()

        # 查询日志
        result = await db_session.execute(
            select(OperationLog).where(
                OperationLog.tenant_id == tenant.id,
                OperationLog.action == "create_device"
            )
        )
        log = result.scalar_one_or_none()

        assert log is not None
        assert log.user_id == user.id
        assert log.action == "create_device"
        assert log.resource_type == "device"
        assert log.resource_id == "IMEI001"
        assert log.details["name"] == "空调1"
        assert log.ip_address == "192.168.1.1"

    @pytest.mark.asyncio
    async def test_log_device_update(self, db_session):
        """测试记录设备更新操作"""
        from app.services.operation_log import OperationLogService
        from app.models import Tenant, User

        # 创建租户和用户
        tenant = Tenant(name="租户", code="test_update_log")
        db_session.add(tenant)
        await db_session.commit()

        user = User(
            tenant_id=tenant.id,
            username="admin",
            password_hash="hash",
            role="admin"
        )
        db_session.add(user)
        await db_session.commit()

        # 记录更新操作日志（包含变更前后对比）
        log_service = OperationLogService()
        await log_service.log(
            db_session,
            user=user,
            action="update_device",
            resource_type="device",
            resource_id="1",
            details={
                "before": {"name": "空调旧名"},
                "after": {"name": "空调新名"},
                "changed_fields": ["name"]
            },
            ip_address="192.168.1.2"
        )
        await db_session.commit()

        # 查询日志
        from app.models import OperationLog
        result = await db_session.execute(
            select(OperationLog).where(
                OperationLog.tenant_id == tenant.id,
                OperationLog.action == "update_device"
            )
        )
        log = result.scalar_one_or_none()

        assert log is not None
        assert log.details["before"]["name"] == "空调旧名"
        assert log.details["after"]["name"] == "空调新名"
        assert "name" in log.details["changed_fields"]

    @pytest.mark.asyncio
    async def test_log_device_delete(self, db_session):
        """测试记录设备删除操作"""
        from app.services.operation_log import OperationLogService
        from app.models import Tenant, User, OperationLog

        # 创建租户和用户
        tenant = Tenant(name="租户", code="test_delete_log")
        db_session.add(tenant)
        await db_session.commit()

        user = User(
            tenant_id=tenant.id,
            username="admin",
            password_hash="hash",
            role="admin"
        )
        db_session.add(user)
        await db_session.commit()

        # 记录删除操作日志
        log_service = OperationLogService()
        await log_service.log(
            db_session,
            user=user,
            action="delete_device",
            resource_type="device",
            resource_id="1",
            details={"name": "已删除的空调", "device_id": "IMEI001"},
            ip_address="192.168.1.3"
        )
        await db_session.commit()

        # 查询日志
        result = await db_session.execute(
            select(OperationLog).where(
                OperationLog.tenant_id == tenant.id,
                OperationLog.action == "delete_device"
            )
        )
        log = result.scalar_one_or_none()

        assert log is not None
        assert log.action == "delete_device"
        assert log.details["name"] == "已删除的空调"

    @pytest.mark.asyncio
    async def test_log_user_create(self, db_session):
        """测试记录用户创建操作"""
        from app.services.operation_log import OperationLogService
        from app.models import Tenant, User, OperationLog

        # 创建租户和用户
        tenant = Tenant(name="租户", code="test_user_log")
        db_session.add(tenant)
        await db_session.commit()

        admin = User(
            tenant_id=tenant.id,
            username="admin",
            password_hash="hash",
            role="admin"
        )
        db_session.add(admin)
        await db_session.commit()

        # 记录用户创建日志
        log_service = OperationLogService()
        await log_service.log(
            db_session,
            user=admin,
            action="create_user",
            resource_type="user",
            resource_id="2",
            details={"username": "new_operator", "role": "operator"},
            ip_address="192.168.1.4"
        )
        await db_session.commit()

        # 查询日志
        result = await db_session.execute(
            select(OperationLog).where(
                OperationLog.tenant_id == tenant.id,
                OperationLog.action == "create_user"
            )
        )
        log = result.scalar_one_or_none()

        assert log is not None
        assert log.details["username"] == "new_operator"

    @pytest.mark.asyncio
    async def test_log_with_null_user(self, db_session):
        """测试记录操作日志时用户为空（如系统自动操作）"""
        from app.services.operation_log import OperationLogService
        from app.models import Tenant, OperationLog

        # 创建租户
        tenant = Tenant(name="租户", code="test_null_user")
        db_session.add(tenant)
        await db_session.commit()

        # 系统自动操作（用户为空）
        log_service = OperationLogService()
        await log_service.log(
            db_session,
            user=None,
            tenant_id=tenant.id,
            action="auto_offline_detection",
            resource_type="device",
            resource_id="IMEI001",
            details={"reason": "heartbeat_timeout"},
            ip_address=None
        )
        await db_session.commit()

        # 查询日志
        result = await db_session.execute(
            select(OperationLog).where(
                OperationLog.tenant_id == tenant.id,
                OperationLog.action == "auto_offline_detection"
            )
        )
        log = result.scalar_one_or_none()

        assert log is not None
        assert log.user_id is None
        assert log.ip_address is None


class TestOperationLogQuery:
    """测试操作日志查询"""

    @pytest.mark.asyncio
    async def test_query_logs_by_action(self, db_session):
        """测试按操作类型查询日志"""
        from app.services.operation_log import OperationLogService
        from app.models import Tenant, User

        # 创建租户和用户
        tenant = Tenant(name="租户", code="test_query")
        db_session.add(tenant)
        await db_session.commit()

        user = User(
            tenant_id=tenant.id,
            username="user",
            password_hash="hash",
            role="admin"
        )
        db_session.add(user)
        await db_session.commit()

        # 记录多条日志
        log_service = OperationLogService()
        await log_service.log(db_session, user=user, action="create_device", resource_type="device", resource_id="1", details={})
        await log_service.log(db_session, user=user, action="update_device", resource_type="device", resource_id="2", details={})
        await log_service.log(db_session, user=user, action="delete_device", resource_type="device", resource_id="3", details={})
        await db_session.commit()

        # 查询 create_device 操作
        logs = await log_service.query(
            db_session,
            tenant_id=tenant.id,
            action="create_device"
        )

        assert len(logs) == 1
        assert logs[0].action == "create_device"

    @pytest.mark.asyncio
    async def test_query_logs_by_resource_type(self, db_session):
        """测试按资源类型查询日志"""
        from app.services.operation_log import OperationLogService
        from app.models import Tenant, User

        # 创建租户和用户
        tenant = Tenant(name="租户", code="test_resource_query")
        db_session.add(tenant)
        await db_session.commit()

        user = User(
            tenant_id=tenant.id,
            username="user",
            password_hash="hash",
            role="admin"
        )
        db_session.add(user)
        await db_session.commit()

        # 记录不同资源类型的日志
        log_service = OperationLogService()
        await log_service.log(db_session, user=user, action="create", resource_type="device", resource_id="1", details={})
        await log_service.log(db_session, user=user, action="create", resource_type="zone", resource_id="1", details={})
        await log_service.log(db_session, user=user, action="create", resource_type="user", resource_id="2", details={})
        await db_session.commit()

        # 查询设备类型日志
        logs = await log_service.query(
            db_session,
            tenant_id=tenant.id,
            resource_type="device"
        )

        assert len(logs) == 1
        assert logs[0].resource_type == "device"

    @pytest.mark.asyncio
    async def test_query_logs_with_pagination(self, db_session):
        """测试分页查询日志"""
        from app.services.operation_log import OperationLogService
        from app.models import Tenant, User

        # 创建租户和用户
        tenant = Tenant(name="租户", code="test_pagination")
        db_session.add(tenant)
        await db_session.commit()

        user = User(
            tenant_id=tenant.id,
            username="user",
            password_hash="hash",
            role="admin"
        )
        db_session.add(user)
        await db_session.commit()

        # 记录多条日志
        log_service = OperationLogService()
        for i in range(25):
            await log_service.log(db_session, user=user, action="create_device", resource_type="device", resource_id=str(i), details={})
        await db_session.commit()

        # 分页查询
        page1 = await log_service.query(
            db_session,
            tenant_id=tenant.id,
            skip=0,
            limit=10
        )
        page2 = await log_service.query(
            db_session,
            tenant_id=tenant.id,
            skip=10,
            limit=10
        )
        page3 = await log_service.query(
            db_session,
            tenant_id=tenant.id,
            skip=20,
            limit=10
        )

        assert len(page1) == 10
        assert len(page2) == 10
        assert len(page3) == 5

    @pytest.mark.asyncio
    async def test_query_logs_by_date_range(self, db_session):
        """测试按日期范围查询日志"""
        from app.services.operation_log import OperationLogService
        from app.models import Tenant, User, OperationLog

        # 创建租户和用户
        tenant = Tenant(name="租户", code="test_date_range")
        db_session.add(tenant)
        await db_session.commit()

        user = User(
            tenant_id=tenant.id,
            username="user",
            password_hash="hash",
            role="admin"
        )
        db_session.add(user)
        await db_session.commit()

        # 记录日志（使用不同时间）
        log_service = OperationLogService()

        # 创建一些日志（时间会自动设置为当前）
        await log_service.log(db_session, user=user, action="action1", resource_type="device", resource_id="1", details={})
        await log_service.log(db_session, user=user, action="action2", resource_type="device", resource_id="2", details={})
        await db_session.commit()

        # 查询今天的日志
        now = datetime.now(UTC)
        start_date = now - timedelta(hours=1)
        end_date = now + timedelta(hours=1)

        logs = await log_service.query(
            db_session,
            tenant_id=tenant.id,
            start_date=start_date,
            end_date=end_date
        )

        assert len(logs) >= 2


class TestOperationLogAPI:
    """测试操作日志API"""

    @pytest.mark.asyncio
    async def test_get_logs_api_as_admin(self, db_session):
        """测试管理员获取操作日志"""
        from app.main import app
        from app.core.database import get_db
        from app.services.operation_log import OperationLogService
        from app.models import Tenant, User
        from app.services.auth import create_access_token

        # 创建租户和用户
        tenant = Tenant(name="租户", code="test_api_logs")
        db_session.add(tenant)
        await db_session.commit()

        admin = User(
            tenant_id=tenant.id,
            username="admin_logs",
            password_hash="hash",
            role="admin"
        )
        db_session.add(admin)
        await db_session.commit()

        # 记录一些日志
        log_service = OperationLogService()
        await log_service.log(db_session, user=admin, action="create_device", resource_type="device", resource_id="1", details={})
        await db_session.commit()

        # 生成token
        token = create_access_token(
            data={"sub": admin.username, "tenant_id": admin.tenant_id}
        )

        async def _get_db_override():
            yield db_session

        app.dependency_overrides[get_db] = _get_db_override

        from httpx import AsyncClient, ASGITransport
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/logs",
                headers={"Authorization": f"Bearer {token}"}
            )

        app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert "items" in data  # PaginatedResponse格式
        assert "total" in data
        assert isinstance(data["items"], list)

    @pytest.mark.asyncio
    async def test_get_logs_api_as_viewer_forbidden(self, db_session):
        """测试查看者无法获取操作日志"""
        from app.main import app
        from app.core.database import get_db
        from app.models import Tenant, User
        from app.services.auth import create_access_token

        # 创建租户和查看者
        tenant = Tenant(name="租户", code="test_logs_viewer")
        db_session.add(tenant)
        await db_session.commit()

        viewer = User(
            tenant_id=tenant.id,
            username="viewer_logs",
            password_hash="hash",
            role="viewer"
        )
        db_session.add(viewer)
        await db_session.commit()

        # 生成token
        token = create_access_token(
            data={"sub": viewer.username, "tenant_id": viewer.tenant_id}
        )

        async def _get_db_override():
            yield db_session

        app.dependency_overrides[get_db] = _get_db_override

        from httpx import AsyncClient, ASGITransport
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/logs",
                headers={"Authorization": f"Bearer {token}"}
            )

        app.dependency_overrides.clear()

        # 查看者无权访问日志（仅管理员和操作员）
        assert response.status_code == 403


class TestOperationLogConstants:
    """测试操作日志常量定义"""

    def test_action_types_defined(self):
        """测试操作类型常量定义"""
        from app.services.operation_log import ActionType

        # 设备操作
        assert hasattr(ActionType, 'DEVICE_CREATE')
        assert hasattr(ActionType, 'DEVICE_UPDATE')
        assert hasattr(ActionType, 'DEVICE_DELETE')
        assert hasattr(ActionType, 'DEVICE_CONTROL')

        # 用户操作
        assert hasattr(ActionType, 'USER_CREATE')
        assert hasattr(ActionType, 'USER_UPDATE')
        assert hasattr(ActionType, 'USER_DELETE')

        # 分区操作
        assert hasattr(ActionType, 'ZONE_CREATE')
        assert hasattr(ActionType, 'ZONE_DELETE')

        # 告警操作
        assert hasattr(ActionType, 'ALARM_HANDLE')

    def test_resource_types_defined(self):
        """测试资源类型常量定义"""
        from app.services.operation_log import ResourceType

        assert hasattr(ResourceType, 'DEVICE')
        assert hasattr(ResourceType, 'USER')
        assert hasattr(ResourceType, 'ZONE')
        assert hasattr(ResourceType, 'ALARM')
        assert hasattr(ResourceType, 'SETTING')