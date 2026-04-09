"""
仪表盘统计 API 测试
TDD 测试用例：设备统计和告警统计
"""
import pytest
from datetime import datetime, timezone
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Alarm, Device, Tenant, User
from app.services.auth import create_access_token, get_password_hash


class TestDashboardStatsAPI:
    """仪表盘统计 API 测试"""

    @pytest.mark.asyncio
    async def test_dashboard_stats_empty(self, db_session: AsyncSession):
        """测试空数据的仪表盘统计"""
        from app.main import app
        from app.core.database import get_db

        # 创建租户和用户
        tenant = Tenant(name="空统计租户", code="test_stats_empty")
        db_session.add(tenant)
        await db_session.commit()
        await db_session.refresh(tenant)

        admin = User(
            tenant_id=tenant.id,
            username="admin_stats_empty",
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
            response = await client.get(
                "/api/devices/stats",
                headers={"Authorization": f"Bearer {admin_token}"}
            )

        app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert data["total_devices"] == 0
        assert data["online_devices"] == 0
        assert data["offline_devices"] == 0
        assert data["total_alarms"] == 0
        assert data["unresolved_alarms"] == 0

    @pytest.mark.asyncio
    async def test_dashboard_stats_with_devices(self, db_session: AsyncSession):
        """测试带设备的仪表盘统计"""
        from app.main import app
        from app.core.database import get_db

        # 创建租户和用户
        tenant = Tenant(name="设备统计租户", code="test_stats_devices")
        db_session.add(tenant)
        await db_session.commit()
        await db_session.refresh(tenant)

        admin = User(
            tenant_id=tenant.id,
            username="admin_stats_dev",
            password_hash=get_password_hash("admin123"),
            role="admin",
            is_active=True
        )
        db_session.add(admin)
        await db_session.commit()
        await db_session.refresh(admin)

        # 创建设备
        device1 = Device(
            tenant_id=tenant.id,
            device_id="device_online_1",
            name="在线设备1",
            is_online=True
        )
        device2 = Device(
            tenant_id=tenant.id,
            device_id="device_online_2",
            name="在线设备2",
            is_online=True
        )
        device3 = Device(
            tenant_id=tenant.id,
            device_id="device_offline_1",
            name="离线设备",
            is_online=False
        )
        db_session.add_all([device1, device2, device3])
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
                "/api/devices/stats",
                headers={"Authorization": f"Bearer {admin_token}"}
            )

        app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert data["total_devices"] == 3
        assert data["online_devices"] == 2
        assert data["offline_devices"] == 1

    @pytest.mark.asyncio
    async def test_dashboard_stats_with_alarms(self, db_session: AsyncSession):
        """测试带告警的仪表盘统计"""
        from app.main import app
        from app.core.database import get_db

        # 创建租户和用户
        tenant = Tenant(name="告警统计租户", code="test_stats_alarms")
        db_session.add(tenant)
        await db_session.commit()
        await db_session.refresh(tenant)

        admin = User(
            tenant_id=tenant.id,
            username="admin_stats_alarm",
            password_hash=get_password_hash("admin123"),
            role="admin",
            is_active=True
        )
        db_session.add(admin)
        await db_session.commit()
        await db_session.refresh(admin)

        # 创建告警
        alarm1 = Alarm(
            tenant_id=tenant.id,
            device_id="device_1",
            type="offline",
            severity="high",
            message="未处理告警1",
            details={},
            is_resolved=False,
            occurred_at=datetime.now(timezone.utc)
        )
        alarm2 = Alarm(
            tenant_id=tenant.id,
            device_id="device_2",
            type="offline",
            severity="medium",
            message="未处理告警2",
            details={},
            is_resolved=False,
            occurred_at=datetime.now(timezone.utc)
        )
        alarm3 = Alarm(
            tenant_id=tenant.id,
            device_id="device_3",
            type="offline",
            severity="low",
            message="已处理告警",
            details={},
            is_resolved=True,
            occurred_at=datetime.now(timezone.utc),
            resolved_at=datetime.now(timezone.utc)
        )
        db_session.add_all([alarm1, alarm2, alarm3])
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
                "/api/devices/stats",
                headers={"Authorization": f"Bearer {admin_token}"}
            )

        app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert data["total_alarms"] == 3
        assert data["unresolved_alarms"] == 2

    @pytest.mark.asyncio
    async def test_dashboard_stats_cross_tenant_isolation(self, db_session: AsyncSession):
        """测试仪表盘统计跨租户隔离"""
        from app.main import app
        from app.core.database import get_db

        # 创建两个租户
        tenant1 = Tenant(name="租户1", code="tenant1_stats")
        tenant2 = Tenant(name="租户2", code="tenant2_stats")
        db_session.add_all([tenant1, tenant2])
        await db_session.commit()
        await db_session.refresh(tenant1)
        await db_session.refresh(tenant2)

        # 创建用户
        admin1 = User(
            tenant_id=tenant1.id,
            username="admin1_stats",
            password_hash=get_password_hash("admin123"),
            role="admin",
            is_active=True
        )
        db_session.add(admin1)
        await db_session.commit()
        await db_session.refresh(admin1)

        # 在租户2创建设备
        device_t2 = Device(
            tenant_id=tenant2.id,
            device_id="device_t2",
            name="租户2设备",
            is_online=True
        )
        alarm_t2 = Alarm(
            tenant_id=tenant2.id,
            device_id="device_t2",
            type="offline",
            severity="high",
            message="租户2告警",
            details={},
            is_resolved=False,
            occurred_at=datetime.now(timezone.utc)
        )
        db_session.add_all([device_t2, alarm_t2])
        await db_session.commit()

        admin_token = create_access_token(
            data={"sub": admin1.username, "tenant_id": admin1.tenant_id}
        )

        async def _get_db_override():
            yield db_session

        app.dependency_overrides[get_db] = _get_db_override

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/devices/stats",
                headers={"Authorization": f"Bearer {admin_token}"}
            )

        app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        # admin1 应该看不到租户2的数据
        assert data["total_devices"] == 0
        assert data["total_alarms"] == 0
        assert data["unresolved_alarms"] == 0