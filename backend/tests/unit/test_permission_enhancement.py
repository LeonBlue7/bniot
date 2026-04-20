"""
权限控制增强测试
测试仪表盘数据同步、分区管理权限、菜单权限控制
"""
import pytest
from datetime import datetime, timezone
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Alarm, Device, Tenant, User, Zone, ZoneTenant
from app.services.auth import create_access_token, get_password_hash


class TestDashboardPermissionFilter:
    """测试仪表盘统计权限过滤"""

    @pytest.mark.asyncio
    async def test_viewer_dashboard_with_no_authorized_zones(self, db_session: AsyncSession):
        """测试观察员查询仪表盘（无授权分区→返回0）"""
        from app.main import app
        from app.core.database import get_db

        # 创建租户
        tenant = Tenant(name="无授权租户", code="test_no_auth_zones")
        db_session.add(tenant)
        await db_session.commit()
        await db_session.refresh(tenant)

        # 创建分区
        zone1 = Zone(
            tenant_id=tenant.id,
            name="分区1",
            sort_order=1
        )
        zone2 = Zone(
            tenant_id=tenant.id,
            name="分区2",
            sort_order=2
        )
        db_session.add_all([zone1, zone2])
        await db_session.commit()
        await db_session.refresh(zone1)
        await db_session.refresh(zone2)

        # 在租户内创建设备（但未授权给该租户查看）
        device1 = Device(
            tenant_id=tenant.id,
            device_id="device_no_auth_1",
            name="设备1",
            zone_id=zone1.id,
            is_online=True
        )
        device2 = Device(
            tenant_id=tenant.id,
            device_id="device_no_auth_2",
            name="设备2",
            zone_id=zone2.id,
            is_online=False
        )
        db_session.add_all([device1, device2])
        await db_session.commit()

        # 创建告警
        alarm1 = Alarm(
            tenant_id=tenant.id,
            device_id="device_no_auth_1",
            type="offline",
            severity="high",
            message="告警1",
            details={},
            is_resolved=False,
            occurred_at=datetime.now(timezone.utc)
        )
        db_session.add(alarm1)
        await db_session.commit()

        # 创建观察员用户（非管理员）
        viewer = User(
            tenant_id=tenant.id,
            username="viewer_no_auth",
            password_hash=get_password_hash("viewer123"),
            role="viewer",
            is_active=True
        )
        db_session.add(viewer)
        await db_session.commit()
        await db_session.refresh(viewer)

        # 注意：没有创建 ZoneTenant 授权记录
        # 观察员没有授权分区，应该看不到任何设备

        viewer_token = create_access_token(
            data={"sub": viewer.username, "tenant_id": viewer.tenant_id}
        )

        async def _get_db_override():
            yield db_session

        app.dependency_overrides[get_db] = _get_db_override

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/devices/stats",
                headers={"Authorization": f"Bearer {viewer_token}"}
            )

        app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        # 观察员无授权分区，应该看到所有数据为0
        assert data["total_devices"] == 0
        assert data["online_devices"] == 0
        assert data["offline_devices"] == 0
        assert data["total_alarms"] == 0
        assert data["unresolved_alarms"] == 0

    @pytest.mark.asyncio
    async def test_viewer_dashboard_with_authorized_zones(self, db_session: AsyncSession):
        """测试观察员查询仪表盘（有授权分区→返回过滤后数据）"""
        from app.main import app
        from app.core.database import get_db

        # 创建租户1（设备所属租户）
        tenant1 = Tenant(name="设备租户", code="test_dev_tenant")
        db_session.add(tenant1)
        await db_session.commit()
        await db_session.refresh(tenant1)

        # 创建租户2（观察员所属租户，被授权访问租户1的分区）
        tenant2 = Tenant(name="观察员租户", code="test_viewer_tenant")
        db_session.add(tenant2)
        await db_session.commit()
        await db_session.refresh(tenant2)

        # 创建分区（属于租户1）
        zone1 = Zone(
            tenant_id=tenant1.id,
            name="授权分区",
            sort_order=1
        )
        zone2 = Zone(
            tenant_id=tenant1.id,
            name="未授权分区",
            sort_order=2
        )
        db_session.add_all([zone1, zone2])
        await db_session.commit()
        await db_session.refresh(zone1)
        await db_session.refresh(zone2)

        # 创建授权关系：租户2 被授权访问分区1
        zone_tenant_auth = ZoneTenant(
            zone_id=zone1.id,
            tenant_id=tenant2.id
        )
        db_session.add(zone_tenant_auth)
        await db_session.commit()

        # 在租户1创建设备
        # 授权分区内的设备
        device_auth1 = Device(
            tenant_id=tenant1.id,
            device_id="device_auth_1",
            name="授权设备1",
            zone_id=zone1.id,
            is_online=True
        )
        device_auth2 = Device(
            tenant_id=tenant1.id,
            device_id="device_auth_2",
            name="授权设备2",
            zone_id=zone1.id,
            is_online=False
        )
        # 未授权分区内的设备
        device_unauth = Device(
            tenant_id=tenant1.id,
            device_id="device_unauth",
            name="未授权设备",
            zone_id=zone2.id,
            is_online=True
        )
        db_session.add_all([device_auth1, device_auth2, device_unauth])
        await db_session.commit()

        # 创建告警（授权分区内的设备告警）
        alarm_auth = Alarm(
            tenant_id=tenant1.id,
            device_id="device_auth_1",
            type="offline",
            severity="high",
            message="授权分区告警",
            details={},
            is_resolved=False,
            occurred_at=datetime.now(timezone.utc)
        )
        # 创建告警（未授权分区内的设备告警）
        alarm_unauth = Alarm(
            tenant_id=tenant1.id,
            device_id="device_unauth",
            type="offline",
            severity="high",
            message="未授权分区告警",
            details={},
            is_resolved=False,
            occurred_at=datetime.now(timezone.utc)
        )
        db_session.add_all([alarm_auth, alarm_unauth])
        await db_session.commit()

        # 创建观察员用户（属于租户2）
        viewer = User(
            tenant_id=tenant2.id,
            username="viewer_with_auth",
            password_hash=get_password_hash("viewer123"),
            role="viewer",
            is_active=True
        )
        db_session.add(viewer)
        await db_session.commit()
        await db_session.refresh(viewer)

        viewer_token = create_access_token(
            data={"sub": viewer.username, "tenant_id": viewer.tenant_id}
        )

        async def _get_db_override():
            yield db_session

        app.dependency_overrides[get_db] = _get_db_override

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/devices/stats",
                headers={"Authorization": f"Bearer {viewer_token}"}
            )

        app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        # 观察员只能看到授权分区内的设备（2台：1在线1离线）
        assert data["total_devices"] == 2
        assert data["online_devices"] == 1
        assert data["offline_devices"] == 1
        # 告警也应该只统计授权分区内的
        assert data["total_alarms"] == 1
        assert data["unresolved_alarms"] == 1

    @pytest.mark.asyncio
    async def test_admin_dashboard_sees_all_tenant_devices(self, db_session: AsyncSession):
        """测试管理员查询仪表盘（返回租户全部数据）"""
        from app.main import app
        from app.core.database import get_db

        # 创建租户
        tenant = Tenant(name="管理员租户", code="test_admin_tenant")
        db_session.add(tenant)
        await db_session.commit()
        await db_session.refresh(tenant)

        # 创建分区
        zone1 = Zone(
            tenant_id=tenant.id,
            name="分区1",
            sort_order=1
        )
        zone2 = Zone(
            tenant_id=tenant.id,
            name="分区2",
            sort_order=2
        )
        db_session.add_all([zone1, zone2])
        await db_session.commit()

        # 创建设备
        device1 = Device(
            tenant_id=tenant.id,
            device_id="admin_device_1",
            name="设备1",
            zone_id=zone1.id,
            is_online=True
        )
        device2 = Device(
            tenant_id=tenant.id,
            device_id="admin_device_2",
            name="设备2",
            zone_id=zone2.id,
            is_online=True
        )
        device3 = Device(
            tenant_id=tenant.id,
            device_id="admin_device_3",
            name="设备3",
            zone_id=None,  # 未分配分区
            is_online=False
        )
        db_session.add_all([device1, device2, device3])
        await db_session.commit()

        # 创建告警
        alarm1 = Alarm(
            tenant_id=tenant.id,
            device_id="admin_device_1",
            type="offline",
            severity="high",
            message="告警1",
            details={},
            is_resolved=False,
            occurred_at=datetime.now(timezone.utc)
        )
        alarm2 = Alarm(
            tenant_id=tenant.id,
            device_id="admin_device_3",
            type="offline",
            severity="medium",
            message="告警2",
            details={},
            is_resolved=True,
            occurred_at=datetime.now(timezone.utc),
            resolved_at=datetime.now(timezone.utc)
        )
        db_session.add_all([alarm1, alarm2])
        await db_session.commit()

        # 创建管理员用户
        admin = User(
            tenant_id=tenant.id,
            username="admin_all_data",
            password_hash=get_password_hash("admin123"),
            role="admin",
            is_active=True
        )
        db_session.add(admin)
        await db_session.commit()
        await db_session.refresh(admin)

        # 注意：没有授权记录，管理员应该能看到所有设备
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
        # 管理员应该看到租户内所有设备（3台）
        assert data["total_devices"] == 3
        assert data["online_devices"] == 2
        assert data["offline_devices"] == 1
        # 所有告警
        assert data["total_alarms"] == 2
        assert data["unresolved_alarms"] == 1


class TestZoneManagementPermission:
    """测试分区管理权限控制"""

    @pytest.mark.asyncio
    async def test_operator_cannot_create_zone(self, db_session: AsyncSession):
        """测试操作员无法创建分区"""
        from app.main import app
        from app.core.database import get_db
        from app.services.permissions import Permission

        # 创建租户
        tenant = Tenant(name="分区测试租户", code="test_zone_perm")
        db_session.add(tenant)
        await db_session.commit()
        await db_session.refresh(tenant)

        # 创建操作员用户
        operator = User(
            tenant_id=tenant.id,
            username="operator_zone",
            password_hash=get_password_hash("operator123"),
            role="operator",
            is_active=True
        )
        db_session.add(operator)
        await db_session.commit()
        await db_session.refresh(operator)

        operator_token = create_access_token(
            data={"sub": operator.username, "tenant_id": operator.tenant_id}
        )

        async def _get_db_override():
            yield db_session

        app.dependency_overrides[get_db] = _get_db_override

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/zones",
                json={"name": "新分区", "tenant_id": tenant.id},
                headers={"Authorization": f"Bearer {operator_token}"}
            )

        app.dependency_overrides.clear()

        # 操作员应该被拒绝（403 Forbidden）
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_operator_cannot_update_zone(self, db_session: AsyncSession):
        """测试操作员无法更新分区"""
        from app.main import app
        from app.core.database import get_db

        # 创建租户
        tenant = Tenant(name="分区更新租户", code="test_zone_update")
        db_session.add(tenant)
        await db_session.commit()
        await db_session.refresh(tenant)

        # 创建分区
        zone = Zone(
            tenant_id=tenant.id,
            name="原分区名",
            sort_order=1
        )
        db_session.add(zone)
        await db_session.commit()
        await db_session.refresh(zone)

        # 创建操作员用户
        operator = User(
            tenant_id=tenant.id,
            username="operator_update",
            password_hash=get_password_hash("operator123"),
            role="operator",
            is_active=True
        )
        db_session.add(operator)
        await db_session.commit()
        await db_session.refresh(operator)

        operator_token = create_access_token(
            data={"sub": operator.username, "tenant_id": operator.tenant_id}
        )

        async def _get_db_override():
            yield db_session

        app.dependency_overrides[get_db] = _get_db_override

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.put(
                f"/api/zones/{zone.id}",
                json={"name": "新分区名"},
                headers={"Authorization": f"Bearer {operator_token}"}
            )

        app.dependency_overrides.clear()

        # 操作员应该被拒绝（403 Forbidden）
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_operator_cannot_delete_zone(self, db_session: AsyncSession):
        """测试操作员无法删除分区"""
        from app.main import app
        from app.core.database import get_db

        # 创建租户
        tenant = Tenant(name="分区删除租户", code="test_zone_delete")
        db_session.add(tenant)
        await db_session.commit()
        await db_session.refresh(tenant)

        # 创建分区
        zone = Zone(
            tenant_id=tenant.id,
            name="待删除分区",
            sort_order=1
        )
        db_session.add(zone)
        await db_session.commit()
        await db_session.refresh(zone)

        # 创建操作员用户
        operator = User(
            tenant_id=tenant.id,
            username="operator_delete",
            password_hash=get_password_hash("operator123"),
            role="operator",
            is_active=True
        )
        db_session.add(operator)
        await db_session.commit()
        await db_session.refresh(operator)

        operator_token = create_access_token(
            data={"sub": operator.username, "tenant_id": operator.tenant_id}
        )

        async def _get_db_override():
            yield db_session

        app.dependency_overrides[get_db] = _get_db_override

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.delete(
                f"/api/zones/{zone.id}",
                headers={"Authorization": f"Bearer {operator_token}"}
            )

        app.dependency_overrides.clear()

        # 操作员应该被拒绝（403 Forbidden）
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_viewer_cannot_create_zone(self, db_session: AsyncSession):
        """测试查看者无法创建分区"""
        from app.main import app
        from app.core.database import get_db

        # 创建租户
        tenant = Tenant(name="查看者分区租户", code="test_viewer_zone")
        db_session.add(tenant)
        await db_session.commit()
        await db_session.refresh(tenant)

        # 创建查看者用户
        viewer = User(
            tenant_id=tenant.id,
            username="viewer_zone",
            password_hash=get_password_hash("viewer123"),
            role="viewer",
            is_active=True
        )
        db_session.add(viewer)
        await db_session.commit()
        await db_session.refresh(viewer)

        viewer_token = create_access_token(
            data={"sub": viewer.username, "tenant_id": viewer.tenant_id}
        )

        async def _get_db_override():
            yield db_session

        app.dependency_overrides[get_db] = _get_db_override

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/zones",
                json={"name": "新分区", "tenant_id": tenant.id},
                headers={"Authorization": f"Bearer {viewer_token}"}
            )

        app.dependency_overrides.clear()

        # 查看者应该被拒绝（403 Forbidden）
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_viewer_can_read_zone_list(self, db_session: AsyncSession):
        """测试查看者可以查看分区列表（只读权限）"""
        from app.main import app
        from app.core.database import get_db

        # 创建租户
        tenant = Tenant(name="查看者列表租户", code="test_viewer_list")
        db_session.add(tenant)
        await db_session.commit()
        await db_session.refresh(tenant)

        # 创建分区
        zone = Zone(
            tenant_id=tenant.id,
            name="分区列表",
            sort_order=1
        )
        db_session.add(zone)
        await db_session.commit()

        # 创建查看者用户
        viewer = User(
            tenant_id=tenant.id,
            username="viewer_list",
            password_hash=get_password_hash("viewer123"),
            role="viewer",
            is_active=True
        )
        db_session.add(viewer)
        await db_session.commit()
        await db_session.refresh(viewer)

        viewer_token = create_access_token(
            data={"sub": viewer.username, "tenant_id": viewer.tenant_id}
        )

        async def _get_db_override():
            yield db_session

        app.dependency_overrides[get_db] = _get_db_override

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/zones",
                headers={"Authorization": f"Bearer {viewer_token}"}
            )

        app.dependency_overrides.clear()

        # 查看者应该可以读取分区列表
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_admin_can_create_zone(self, db_session: AsyncSession):
        """测试管理员可以创建分区"""
        from app.main import app
        from app.core.database import get_db

        # 创建租户
        tenant = Tenant(name="管理员分区租户", code="test_admin_zone")
        db_session.add(tenant)
        await db_session.commit()
        await db_session.refresh(tenant)

        # 创建管理员用户
        admin = User(
            tenant_id=tenant.id,
            username="admin_zone",
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
            response = await client.post(
                "/api/zones",
                json={"name": "管理员创建的分区", "tenant_id": tenant.id},
                headers={"Authorization": f"Bearer {admin_token}"}
            )

        app.dependency_overrides.clear()

        # 管理员应该可以创建分区
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "管理员创建的分区"


class TestZonePermissionEnumUpdate:
    """测试权限枚举更新（operator/viewer无ZONE_CREATE/UPDATE/DELETE）"""

    def test_operator_has_no_zone_create_permission(self):
        """测试操作员无分区创建权限"""
        from app.services.permissions import Permission, ROLE_PERMISSIONS

        operator_permissions = ROLE_PERMISSIONS.get('operator', set())
        # 操作员不应该有分区创建权限
        assert Permission.ZONE_CREATE not in operator_permissions

    def test_operator_has_no_zone_update_permission(self):
        """测试操作员无分区更新权限"""
        from app.services.permissions import Permission, ROLE_PERMISSIONS

        operator_permissions = ROLE_PERMISSIONS.get('operator', set())
        # 操作员不应该有分区更新权限
        assert Permission.ZONE_UPDATE not in operator_permissions

    def test_operator_has_no_zone_delete_permission(self):
        """测试操作员无分区删除权限"""
        from app.services.permissions import Permission, ROLE_PERMISSIONS

        operator_permissions = ROLE_PERMISSIONS.get('operator', set())
        # 操作员不应该有分区删除权限
        assert Permission.ZONE_DELETE not in operator_permissions

    def test_operator_has_zone_read_permission(self):
        """测试操作员有分区读取权限"""
        from app.services.permissions import Permission, ROLE_PERMISSIONS

        operator_permissions = ROLE_PERMISSIONS.get('operator', set())
        # 操作员应该有分区读取权限
        assert Permission.ZONE_READ in operator_permissions

    def test_viewer_has_zone_read_permission(self):
        """测试查看者有分区读取权限"""
        from app.services.permissions import Permission, ROLE_PERMISSIONS

        viewer_permissions = ROLE_PERMISSIONS.get('viewer', set())
        # 查看者应该有分区读取权限
        assert Permission.ZONE_READ in viewer_permissions

    def test_viewer_has_no_zone_modify_permissions(self):
        """测试查看者无分区修改权限"""
        from app.services.permissions import Permission, ROLE_PERMISSIONS

        viewer_permissions = ROLE_PERMISSIONS.get('viewer', set())
        # 查看者不应该有任何分区修改权限
        assert Permission.ZONE_CREATE not in viewer_permissions
        assert Permission.ZONE_UPDATE not in viewer_permissions
        assert Permission.ZONE_DELETE not in viewer_permissions

    def test_admin_has_all_zone_permissions(self):
        """测试管理员有完整的分区权限"""
        from app.services.permissions import Permission, ROLE_PERMISSIONS

        admin_permissions = ROLE_PERMISSIONS.get('admin', set())
        # 管理员应该有所有分区权限
        assert Permission.ZONE_READ in admin_permissions
        assert Permission.ZONE_CREATE in admin_permissions
        assert Permission.ZONE_UPDATE in admin_permissions
        assert Permission.ZONE_DELETE in admin_permissions