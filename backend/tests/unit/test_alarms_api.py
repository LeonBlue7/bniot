"""
告警处理 API 端点测试
TDD 测试用例：告警处理和批量处理
"""
import pytest
from datetime import datetime, timezone
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Alarm, Tenant, User
from app.services.auth import create_access_token, get_password_hash


class TestAlarmHandleAPI:
    """单个告警处理 API 测试"""

    @pytest.mark.asyncio
    async def test_handle_single_alarm(self, db_session: AsyncSession):
        """测试处理单个告警"""
        from app.main import app
        from app.core.database import get_db

        # 创建租户和用户
        tenant = Tenant(name="告警测试租户", code="test_alarm_handle")
        db_session.add(tenant)
        await db_session.commit()
        await db_session.refresh(tenant)

        admin = User(
            tenant_id=tenant.id,
            username="admin_alarm",
            password_hash=get_password_hash("admin123"),
            role="admin",
            is_active=True
        )
        db_session.add(admin)
        await db_session.commit()
        await db_session.refresh(admin)

        # 创建未处理的告警
        alarm = Alarm(
            tenant_id=tenant.id,
            device_id="test_device_001",
            type="offline",
            severity="high",
            message="设备离线告警",
            details={},
            is_resolved=False,
            occurred_at=datetime.now(timezone.utc)
        )
        db_session.add(alarm)
        await db_session.commit()
        await db_session.refresh(alarm)

        admin_token = create_access_token(
            data={"sub": admin.username, "tenant_id": admin.tenant_id}
        )

        async def _get_db_override():
            yield db_session

        app.dependency_overrides[get_db] = _get_db_override

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.patch(
                f"/api/alarms/{alarm.id}/handle",
                headers={"Authorization": f"Bearer {admin_token}"}
            )

        app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert data["is_resolved"] is True
        assert data["resolved_at"] is not None

    @pytest.mark.asyncio
    async def test_handle_alarm_not_found(self, db_session: AsyncSession):
        """测试处理不存在的告警"""
        from app.main import app
        from app.core.database import get_db

        # 创建租户和用户
        tenant = Tenant(name="告警不存在租户", code="test_alarm_notfound")
        db_session.add(tenant)
        await db_session.commit()
        await db_session.refresh(tenant)

        admin = User(
            tenant_id=tenant.id,
            username="admin_notfound",
            password_hash=get_password_hash("admin123"),
            role="admin",
            is_active=True
        )
        db_session.add(admin)
        await db_session.commit()
        await db_session.refresh(admin)

        admin_token = create_access_token(
            data={"sub": admin.username, "tenant_id": admin.tenant_id}
        )

        async def _get_db_override():
            yield db_session

        app.dependency_overrides[get_db] = _get_db_override

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.patch(
                "/api/alarms/9999/handle",
                headers={"Authorization": f"Bearer {admin_token}"}
            )

        app.dependency_overrides.clear()

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_handle_already_resolved_alarm(self, db_session: AsyncSession):
        """测试处理已处理的告警"""
        from app.main import app
        from app.core.database import get_db

        # 创建租户和用户
        tenant = Tenant(name="已处理告警租户", code="test_alarm_resolved")
        db_session.add(tenant)
        await db_session.commit()
        await db_session.refresh(tenant)

        admin = User(
            tenant_id=tenant.id,
            username="admin_resolved",
            password_hash=get_password_hash("admin123"),
            role="admin",
            is_active=True
        )
        db_session.add(admin)
        await db_session.commit()
        await db_session.refresh(admin)

        # 创建已处理的告警
        alarm = Alarm(
            tenant_id=tenant.id,
            device_id="test_device_002",
            type="offline",
            severity="high",
            message="设备离线告警",
            details={},
            is_resolved=True,
            occurred_at=datetime.now(timezone.utc),
            resolved_at=datetime.now(timezone.utc)
        )
        db_session.add(alarm)
        await db_session.commit()
        await db_session.refresh(alarm)

        admin_token = create_access_token(
            data={"sub": admin.username, "tenant_id": admin.tenant_id}
        )

        async def _get_db_override():
            yield db_session

        app.dependency_overrides[get_db] = _get_db_override

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.patch(
                f"/api/alarms/{alarm.id}/handle",
                headers={"Authorization": f"Bearer {admin_token}"}
            )

        app.dependency_overrides.clear()

        # 可以再次处理，返回200
        assert response.status_code == 200
        data = response.json()
        assert data["is_resolved"] is True


class TestAlarmBatchHandleAPI:
    """批量告警处理 API 测试"""

    @pytest.mark.asyncio
    async def test_batch_handle_alarms(self, db_session: AsyncSession):
        """测试批量处理告警"""
        from app.main import app
        from app.core.database import get_db

        # 创建租户和用户
        tenant = Tenant(name="批量告警租户", code="test_alarm_batch")
        db_session.add(tenant)
        await db_session.commit()
        await db_session.refresh(tenant)

        admin = User(
            tenant_id=tenant.id,
            username="admin_batch",
            password_hash=get_password_hash("admin123"),
            role="admin",
            is_active=True
        )
        db_session.add(admin)
        await db_session.commit()
        await db_session.refresh(admin)

        # 创建多个未处理的告警
        alarms = []
        for i in range(3):
            alarm = Alarm(
                tenant_id=tenant.id,
                device_id=f"test_device_{i}",
                type="offline",
                severity="high",
                message=f"设备离线告警{i}",
                details={},
                is_resolved=False,
                occurred_at=datetime.now(timezone.utc)
            )
            alarms.append(alarm)
        db_session.add_all(alarms)
        await db_session.commit()
        for alarm in alarms:
            await db_session.refresh(alarm)

        alarm_ids = [a.id for a in alarms]

        admin_token = create_access_token(
            data={"sub": admin.username, "tenant_id": admin.tenant_id}
        )

        async def _get_db_override():
            yield db_session

        app.dependency_overrides[get_db] = _get_db_override

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.patch(
                "/api/alarms/batch-handle",
                headers={"Authorization": f"Bearer {admin_token}"},
                json={"alarm_ids": alarm_ids}
            )

        app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert "handled_count" in data
        assert data["handled_count"] == 3

    @pytest.mark.asyncio
    async def test_batch_handle_empty_list(self, db_session: AsyncSession):
        """测试批量处理空列表"""
        from app.main import app
        from app.core.database import get_db

        # 创建租户和用户
        tenant = Tenant(name="空批量租户", code="test_alarm_empty")
        db_session.add(tenant)
        await db_session.commit()
        await db_session.refresh(tenant)

        admin = User(
            tenant_id=tenant.id,
            username="admin_empty",
            password_hash=get_password_hash("admin123"),
            role="admin",
            is_active=True
        )
        db_session.add(admin)
        await db_session.commit()
        await db_session.refresh(admin)

        admin_token = create_access_token(
            data={"sub": admin.username, "tenant_id": admin.tenant_id}
        )

        async def _get_db_override():
            yield db_session

        app.dependency_overrides[get_db] = _get_db_override

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.patch(
                "/api/alarms/batch-handle",
                headers={"Authorization": f"Bearer {admin_token}"},
                json={"alarm_ids": []}
            )

        app.dependency_overrides.clear()

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_batch_handle_cross_tenant_forbidden(self, db_session: AsyncSession):
        """测试批量处理其他租户告警失败"""
        from app.main import app
        from app.core.database import get_db

        # 创建两个租户
        tenant1 = Tenant(name="租户1", code="tenant1_batch")
        tenant2 = Tenant(name="租户2", code="tenant2_batch")
        db_session.add_all([tenant1, tenant2])
        await db_session.commit()
        await db_session.refresh(tenant1)
        await db_session.refresh(tenant2)

        # 创建管理员在租户1
        admin = User(
            tenant_id=tenant1.id,
            username="admin_t1",
            password_hash=get_password_hash("admin123"),
            role="admin",
            is_active=True
        )
        db_session.add(admin)
        await db_session.commit()
        await db_session.refresh(admin)

        # 创建告警在租户2
        alarm = Alarm(
            tenant_id=tenant2.id,
            device_id="other_device",
            type="offline",
            severity="high",
            message="其他租户告警",
            details={},
            is_resolved=False,
            occurred_at=datetime.now(timezone.utc)
        )
        db_session.add(alarm)
        await db_session.commit()
        await db_session.refresh(alarm)

        admin_token = create_access_token(
            data={"sub": admin.username, "tenant_id": admin.tenant_id}
        )

        async def _get_db_override():
            yield db_session

        app.dependency_overrides[get_db] = _get_db_override

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.patch(
                "/api/alarms/batch-handle",
                headers={"Authorization": f"Bearer {admin_token}"},
                json={"alarm_ids": [alarm.id]}
            )

        app.dependency_overrides.clear()

        # 应该处理成功但只处理属于自己租户的告警
        assert response.status_code == 200
        data = response.json()
        assert data["handled_count"] == 0


class TestAlarmListAPI:
    """告警列表 API 测试"""

    @pytest.mark.asyncio
    async def test_list_alarms(self, db_session: AsyncSession):
        """测试获取告警列表"""
        from app.main import app
        from app.core.database import get_db

        # 创建租户和用户
        tenant = Tenant(name="告警列表租户", code="test_alarm_list")
        db_session.add(tenant)
        await db_session.commit()
        await db_session.refresh(tenant)

        admin = User(
            tenant_id=tenant.id,
            username="admin_list",
            password_hash=get_password_hash("admin123"),
            role="admin",
            is_active=True
        )
        db_session.add(admin)
        await db_session.commit()
        await db_session.refresh(admin)

        # 创建告警
        alarm = Alarm(
            tenant_id=tenant.id,
            device_id="test_device_list",
            type="offline",
            severity="high",
            message="设备离线",
            details={},
            is_resolved=False,
            occurred_at=datetime.now(timezone.utc)
        )
        db_session.add(alarm)
        await db_session.commit()

        admin_token = create_access_token(
            data={"sub": admin.username, "tenant_id": admin.tenant_id}
        )

        async def _get_db_override():
            yield db_session

        app.dependency_overrides[get_db] = _get_db_override

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/alarms",
                headers={"Authorization": f"Bearer {admin_token}"}
            )

        app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    @pytest.mark.asyncio
    async def test_list_alarms_with_filter(self, db_session: AsyncSession):
        """测试带过滤条件获取告警列表"""
        from app.main import app
        from app.core.database import get_db

        # 创建租户和用户
        tenant = Tenant(name="告警过滤租户", code="test_alarm_filter")
        db_session.add(tenant)
        await db_session.commit()
        await db_session.refresh(tenant)

        admin = User(
            tenant_id=tenant.id,
            username="admin_filter",
            password_hash=get_password_hash("admin123"),
            role="admin",
            is_active=True
        )
        db_session.add(admin)
        await db_session.commit()
        await db_session.refresh(admin)

        # 创建不同状态的告警
        alarm_unresolved = Alarm(
            tenant_id=tenant.id,
            device_id="device_unresolved",
            type="offline",
            severity="high",
            message="未处理告警",
            details={},
            is_resolved=False,
            occurred_at=datetime.now(timezone.utc)
        )
        alarm_resolved = Alarm(
            tenant_id=tenant.id,
            device_id="device_resolved",
            type="offline",
            severity="low",
            message="已处理告警",
            details={},
            is_resolved=True,
            occurred_at=datetime.now(timezone.utc),
            resolved_at=datetime.now(timezone.utc)
        )
        db_session.add_all([alarm_unresolved, alarm_resolved])
        await db_session.commit()

        admin_token = create_access_token(
            data={"sub": admin.username, "tenant_id": admin.tenant_id}
        )

        async def _get_db_override():
            yield db_session

        app.dependency_overrides[get_db] = _get_db_override

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # 过滤未处理告警
            response = await client.get(
                "/api/alarms",
                headers={"Authorization": f"Bearer {admin_token}"},
                params={"is_resolved": "false"}
            )

        app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        for alarm in data:
            assert alarm["is_resolved"] is False