"""
测试设备API的分区权限过滤集成

验证设备列表API是否正确应用分区权限过滤：
- 管理员可以看到租户内所有设备
- 操作员/观察员只能看到已授权分区内的设备
"""
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select

from app.main import app
from app.models import Tenant, User, Device, Zone
from app.models.models import ZoneTenant
from app.services.auth import create_access_token


class TestDeviceAPIZonePermission:
    """测试设备API的分区权限过滤"""

    async def _create_test_data(self, db_session):
        """创建测试数据"""
        # 创建租户
        tenant1 = Tenant(name="租户API", code="tenant_api_test")
        tenant2 = Tenant(name="租户API2", code="tenant_api_test2")
        db_session.add_all([tenant1, tenant2])
        await db_session.commit()
        await db_session.refresh(tenant1)
        await db_session.refresh(tenant2)

        # 创建用户
        admin1 = User(
            tenant_id=tenant1.id,
            username="admin_api_test",
            password_hash="hash",
            role="admin",
            is_active=True
        )
        operator1 = User(
            tenant_id=tenant1.id,
            username="operator_api_test",
            password_hash="hash",
            role="operator",
            is_active=True
        )
        viewer1 = User(
            tenant_id=tenant1.id,
            username="viewer_api_test",
            password_hash="hash",
            role="viewer",
            is_active=True
        )
        db_session.add_all([admin1, operator1, viewer1])
        await db_session.commit()
        await db_session.refresh(admin1)
        await db_session.refresh(operator1)
        await db_session.refresh(viewer1)

        # 创建分区
        zone1 = Zone(
            tenant_id=tenant1.id,
            name="授权分区API"
        )
        zone2 = Zone(
            tenant_id=tenant1.id,
            name="未授权分区API"
        )
        db_session.add_all([zone1, zone2])
        await db_session.commit()
        await db_session.refresh(zone1)
        await db_session.refresh(zone2)

        # 创建设备
        device1 = Device(
            tenant_id=tenant1.id,
            device_id="IMEI_API_001",
            name="授权分区设备",
            zone_id=zone1.id
        )
        device2 = Device(
            tenant_id=tenant1.id,
            device_id="IMEI_API_002",
            name="未授权分区设备",
            zone_id=zone2.id
        )
        device3 = Device(
            tenant_id=tenant1.id,
            device_id="IMEI_API_003",
            name="未分区设备",
            zone_id=None
        )
        db_session.add_all([device1, device2, device3])
        await db_session.commit()

        # 授权zone1给tenant1
        zt = ZoneTenant(zone_id=zone1.id, tenant_id=tenant1.id)
        db_session.add(zt)
        await db_session.commit()

        return {
            "tenant1": tenant1,
            "tenant2": tenant2,
            "admin1": admin1,
            "operator1": operator1,
            "viewer1": viewer1,
            "zone1": zone1,
            "zone2": zone2,
            "device1": device1,
            "device2": device2,
            "device3": device3,
        }

    def _get_token(self, user: User) -> str:
        """生成JWT token"""
        return create_access_token(
            data={"sub": user.username, "tenant_id": user.tenant_id}
        )

    @pytest.mark.asyncio
    async def test_admin_can_see_all_devices_via_api(self, db_session, test_app):
        """测试管理员通过API可以看到所有设备"""
        data = await self._create_test_data(db_session)
        token = self._get_token(data["admin1"])

        async with AsyncClient(
            transport=ASGITransport(app=test_app),
            base_url="http://test"
        ) as client:
            response = await client.get(
                "/api/devices",
                headers={"Authorization": f"Bearer {token}"}
            )

        assert response.status_code == 200
        result = response.json()
        # 管理员应该能看到3个设备
        assert result["total"] == 3
        device_ids = [d["device_id"] for d in result["items"]]
        assert "IMEI_API_001" in device_ids
        assert "IMEI_API_002" in device_ids
        assert "IMEI_API_003" in device_ids

    @pytest.mark.asyncio
    async def test_operator_can_only_see_authorized_devices_via_api(self, db_session, test_app):
        """测试操作员通过API只能看到已授权分区设备"""
        data = await self._create_test_data(db_session)
        token = self._get_token(data["operator1"])

        async with AsyncClient(
            transport=ASGITransport(app=test_app),
            base_url="http://test"
        ) as client:
            response = await client.get(
                "/api/devices",
                headers={"Authorization": f"Bearer {token}"}
            )

        assert response.status_code == 200
        result = response.json()
        # 操作员应该只能看到1个设备（授权分区内的）
        assert result["total"] == 1
        device_ids = [d["device_id"] for d in result["items"]]
        assert "IMEI_API_001" in device_ids
        # 不应该看到未授权分区和未分区的设备
        assert "IMEI_API_002" not in device_ids
        assert "IMEI_API_003" not in device_ids

    @pytest.mark.asyncio
    async def test_viewer_can_only_see_authorized_devices_via_api(self, db_session, test_app):
        """测试观察员通过API只能看到已授权分区设备"""
        data = await self._create_test_data(db_session)
        token = self._get_token(data["viewer1"])

        async with AsyncClient(
            transport=ASGITransport(app=test_app),
            base_url="http://test"
        ) as client:
            response = await client.get(
                "/api/devices",
                headers={"Authorization": f"Bearer {token}"}
            )

        assert response.status_code == 200
        result = response.json()
        # 观察员应该只能看到1个设备
        assert result["total"] == 1
        device_ids = [d["device_id"] for d in result["items"]]
        assert "IMEI_API_001" in device_ids

    @pytest.mark.asyncio
    async def test_no_authorization_returns_empty_list(self, db_session, test_app):
        """测试没有分区授权时返回空列表"""
        # 创建租户和用户，但不创建分区授权
        tenant = Tenant(name="无授权租户", code="no_auth_tenant")
        db_session.add(tenant)
        await db_session.commit()
        await db_session.refresh(tenant)

        operator = User(
            tenant_id=tenant.id,
            username="no_auth_operator",
            password_hash="hash",
            role="operator",
            is_active=True
        )
        db_session.add(operator)
        await db_session.commit()

        zone = Zone(
            tenant_id=tenant.id,
            name="无授权分区"
        )
        db_session.add(zone)
        await db_session.commit()
        await db_session.refresh(zone)

        device = Device(
            tenant_id=tenant.id,
            device_id="IMEI_NO_AUTH",
            name="无授权设备",
            zone_id=zone.id
        )
        db_session.add(device)
        await db_session.commit()

        token = self._get_token(operator)

        async with AsyncClient(
            transport=ASGITransport(app=test_app),
            base_url="http://test"
        ) as client:
            response = await client.get(
                "/api/devices",
                headers={"Authorization": f"Bearer {token}"}
            )

        assert response.status_code == 200
        result = response.json()
        # 没有分区授权，应该返回空列表
        assert result["total"] == 0
        assert len(result["items"]) == 0