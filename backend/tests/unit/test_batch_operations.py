"""
测试设备批量操作
Phase 1.3 设备批量操作
"""
import pytest
from datetime import datetime, UTC
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select
from unittest.mock import patch, MagicMock

from app.models import Tenant, User, Device, Zone
from app.services.auth import create_access_token


class TestBatchDeviceControl:
    """测试批量设备控制"""

    @pytest.mark.asyncio
    async def test_batch_control_on(self, db_session):
        """测试批量开机"""
        from app.main import app
        from app.core.database import get_db

        # 创建租户、用户和设备
        tenant = Tenant(name="租户", code="test_batch_on")
        db_session.add(tenant)
        await db_session.commit()

        admin = User(
            tenant_id=tenant.id,
            username="admin_batch",
            password_hash="hash",
            role="admin"
        )
        db_session.add(admin)

        # 创建多个设备
        devices = []
        for i in range(3):
            device = Device(
                tenant_id=tenant.id,
                device_id=f"IMEI00{i}",
                name=f"空调{i}"
            )
            devices.append(device)
            db_session.add(device)

        await db_session.commit()
        await db_session.refresh(admin)

        # 生成token
        token = create_access_token(
            data={"sub": admin.username, "tenant_id": admin.tenant_id}
        )

        async def _get_db_override():
            yield db_session

        app.dependency_overrides[get_db] = _get_db_override

        # Mock MQTT客户端
        mock_mqtt = MagicMock()
        mock_mqtt.publish.return_value = True

        with patch('app.api.endpoints.devices.get_mqtt_client', return_value=mock_mqtt):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post(
                    "/api/devices/batch/control",
                    headers={"Authorization": f"Bearer {token}"},
                    json={"device_ids": [d.id for d in devices], "airstate": 1}
                )

        app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert data["success_count"] == 3
        assert data["failed_count"] == 0

    @pytest.mark.asyncio
    async def test_batch_control_off(self, db_session):
        """测试批量关机"""
        from app.main import app
        from app.core.database import get_db

        # 创建租户、用户和设备
        tenant = Tenant(name="租户", code="test_batch_off")
        db_session.add(tenant)
        await db_session.commit()

        operator = User(
            tenant_id=tenant.id,
            username="operator_batch",
            password_hash="hash",
            role="operator"
        )
        db_session.add(operator)

        devices = []
        for i in range(2):
            device = Device(
                tenant_id=tenant.id,
                device_id=f"IMEI_OFF{i}",
                name=f"空调{i}"
            )
            devices.append(device)
            db_session.add(device)

        await db_session.commit()
        await db_session.refresh(operator)

        token = create_access_token(
            data={"sub": operator.username, "tenant_id": operator.tenant_id}
        )

        async def _get_db_override():
            yield db_session

        app.dependency_overrides[get_db] = _get_db_override

        # Mock MQTT客户端
        mock_mqtt = MagicMock()
        mock_mqtt.publish.return_value = True

        with patch('app.api.endpoints.devices.get_mqtt_client', return_value=mock_mqtt):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post(
                    "/api/devices/batch/control",
                    headers={"Authorization": f"Bearer {token}"},
                    json={"device_ids": [d.id for d in devices], "airstate": 0}
                )

        app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert data["success_count"] == 2

    @pytest.mark.asyncio
    async def test_batch_control_viewer_forbidden(self, db_session):
        """测试查看者无法批量控制"""
        from app.main import app
        from app.core.database import get_db

        # 创建租户和查看者
        tenant = Tenant(name="租户", code="test_batch_viewer")
        db_session.add(tenant)
        await db_session.commit()

        viewer = User(
            tenant_id=tenant.id,
            username="viewer_batch",
            password_hash="hash",
            role="viewer"
        )
        db_session.add(viewer)
        await db_session.commit()
        await db_session.refresh(viewer)

        token = create_access_token(
            data={"sub": viewer.username, "tenant_id": viewer.tenant_id}
        )

        async def _get_db_override():
            yield db_session

        app.dependency_overrides[get_db] = _get_db_override

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/devices/batch/control",
                headers={"Authorization": f"Bearer {token}"},
                json={"device_ids": [1, 2], "airstate": 1}
            )

        app.dependency_overrides.clear()

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_batch_control_cross_tenant_forbidden(self, db_session):
        """测试不能控制其他租户设备"""
        from app.main import app
        from app.core.database import get_db

        # 创建两个租户
        tenant1 = Tenant(name="租户1", code="batch_tenant1")
        tenant2 = Tenant(name="租户2", code="batch_tenant2")
        db_session.add_all([tenant1, tenant2])
        await db_session.commit()

        # 创建用户和设备
        admin1 = User(
            tenant_id=tenant1.id,
            username="admin1_batch",
            password_hash="hash",
            role="admin"
        )
        device2 = Device(
            tenant_id=tenant2.id,
            device_id="IMEI_OTHER",
            name="其他租户设备"
        )
        db_session.add_all([admin1, device2])
        await db_session.commit()
        await db_session.refresh(admin1)
        await db_session.refresh(device2)

        token = create_access_token(
            data={"sub": admin1.username, "tenant_id": admin1.tenant_id}
        )

        async def _get_db_override():
            yield db_session

        app.dependency_overrides[get_db] = _get_db_override

        # Mock MQTT客户端
        mock_mqtt = MagicMock()
        mock_mqtt.publish.return_value = True

        with patch('app.api.endpoints.devices.get_mqtt_client', return_value=mock_mqtt):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post(
                    "/api/devices/batch/control",
                    headers={"Authorization": f"Bearer {token}"},
                    json={"device_ids": [device2.id], "airstate": 1}
                )

        app.dependency_overrides.clear()

        # 应该返回部分失败（跨租户设备）
        assert response.status_code == 200
        data = response.json()
        assert data["failed_count"] == 1
        assert data["success_count"] == 0


class TestBatchDeviceDelete:
    """测试批量设备删除"""

    @pytest.mark.asyncio
    async def test_batch_delete_success(self, db_session):
        """测试批量删除成功"""
        from app.main import app
        from app.core.database import get_db

        # 创建租户、用户和设备
        tenant = Tenant(name="租户", code="test_batch_del")
        db_session.add(tenant)
        await db_session.commit()

        admin = User(
            tenant_id=tenant.id,
            username="admin_del",
            password_hash="hash",
            role="admin"
        )
        db_session.add(admin)

        devices = []
        for i in range(3):
            device = Device(
                tenant_id=tenant.id,
                device_id=f"IMEI_DEL{i}",
                name=f"空调{i}"
            )
            devices.append(device)
            db_session.add(device)

        await db_session.commit()
        await db_session.refresh(admin)

        token = create_access_token(
            data={"sub": admin.username, "tenant_id": admin.tenant_id}
        )

        async def _get_db_override():
            yield db_session

        app.dependency_overrides[get_db] = _get_db_override

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/devices/batch/delete",
                headers={"Authorization": f"Bearer {token}"},
                json={"device_ids": [d.id for d in devices]}
            )

        app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert data["success_count"] == 3  # 使用success_count而不是deleted_count
        assert data["failed_count"] == 0

    @pytest.mark.asyncio
    async def test_batch_delete_viewer_forbidden(self, db_session):
        """测试查看者无法批量删除"""
        from app.main import app
        from app.core.database import get_db

        tenant = Tenant(name="租户", code="test_del_viewer")
        db_session.add(tenant)
        await db_session.commit()

        viewer = User(
            tenant_id=tenant.id,
            username="viewer_del",
            password_hash="hash",
            role="viewer"
        )
        db_session.add(viewer)
        await db_session.commit()
        await db_session.refresh(viewer)

        token = create_access_token(
            data={"sub": viewer.username, "tenant_id": viewer.tenant_id}
        )

        async def _get_db_override():
            yield db_session

        app.dependency_overrides[get_db] = _get_db_override

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/devices/batch/delete",
                headers={"Authorization": f"Bearer {token}"},
                json={"device_ids": [1, 2]}
            )

        app.dependency_overrides.clear()

        assert response.status_code == 403


class TestBatchDeviceMoveZone:
    """测试批量设备分区迁移"""

    @pytest.mark.asyncio
    async def test_batch_move_zone_success(self, db_session):
        """测试批量迁移分区成功"""
        from app.main import app
        from app.core.database import get_db

        # 创建租户、分区、用户和设备
        tenant = Tenant(name="租户", code="test_move_zone")
        db_session.add(tenant)
        await db_session.commit()

        zone1 = Zone(tenant_id=tenant.id, name="分区1")
        zone2 = Zone(tenant_id=tenant.id, name="分区2")
        db_session.add_all([zone1, zone2])
        await db_session.commit()

        admin = User(
            tenant_id=tenant.id,
            username="admin_zone",
            password_hash="hash",
            role="admin"
        )
        db_session.add(admin)

        devices = []
        for i in range(3):
            device = Device(
                tenant_id=tenant.id,
                device_id=f"IMEI_ZONE{i}",
                name=f"空调{i}",
                zone_id=zone1.id
            )
            devices.append(device)
            db_session.add(device)

        await db_session.commit()
        await db_session.refresh(admin)
        await db_session.refresh(zone2)

        token = create_access_token(
            data={"sub": admin.username, "tenant_id": admin.tenant_id}
        )

        async def _get_db_override():
            yield db_session

        app.dependency_overrides[get_db] = _get_db_override

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/devices/batch/move-zone",
                headers={"Authorization": f"Bearer {token}"},
                json={"device_ids": [d.id for d in devices], "zone_id": zone2.id}
            )

        app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert data["success_count"] == 3  # 使用success_count而不是moved_count

    @pytest.mark.asyncio
    async def test_batch_move_zone_operator_allowed(self, db_session):
        """测试操作员可以迁移分区"""
        from app.main import app
        from app.core.database import get_db

        tenant = Tenant(name="租户", code="test_move_op")
        db_session.add(tenant)
        await db_session.commit()

        zone1 = Zone(tenant_id=tenant.id, name="分区1")
        zone2 = Zone(tenant_id=tenant.id, name="分区2")
        db_session.add_all([zone1, zone2])
        await db_session.commit()

        operator = User(
            tenant_id=tenant.id,
            username="operator_zone",
            password_hash="hash",
            role="operator"
        )
        db_session.add(operator)

        device = Device(
            tenant_id=tenant.id,
            device_id="IMEI_OP",
            name="空调",
            zone_id=zone1.id
        )
        db_session.add(device)
        await db_session.commit()
        await db_session.refresh(operator)
        await db_session.refresh(zone2)
        await db_session.refresh(device)

        token = create_access_token(
            data={"sub": operator.username, "tenant_id": operator.tenant_id}
        )

        async def _get_db_override():
            yield db_session

        app.dependency_overrides[get_db] = _get_db_override

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/devices/batch/move-zone",
                headers={"Authorization": f"Bearer {token}"},
                json={"device_ids": [device.id], "zone_id": zone2.id}
            )

        app.dependency_overrides.clear()

        assert response.status_code == 200


class TestBatchOperationSchema:
    """测试批量操作数据结构"""

    def test_batch_control_request_schema(self):
        """测试批量控制请求schema"""
        from app.schemas import BatchControlRequest

        req = BatchControlRequest(device_ids=[1, 2, 3], airstate=1)
        assert req.device_ids == [1, 2, 3]
        assert req.airstate == 1

    def test_batch_delete_request_schema(self):
        """测试批量删除请求schema"""
        from app.schemas import BatchDeleteRequest

        req = BatchDeleteRequest(device_ids=[1, 2, 3])
        assert req.device_ids == [1, 2, 3]

    def test_batch_move_zone_request_schema(self):
        """测试批量迁移分区请求schema"""
        from app.schemas import BatchMoveZoneRequest

        req = BatchMoveZoneRequest(device_ids=[1, 2, 3], zone_id=5)
        assert req.device_ids == [1, 2, 3]
        assert req.zone_id == 5

    def test_batch_operation_response_schema(self):
        """测试批量操作响应schema"""
        from app.schemas import BatchOperationResponse

        resp = BatchOperationResponse(
            success_count=5,
            failed_count=2,
            failed_details=[{"device_id": 1, "reason": "离线"}]
        )
        assert resp.success_count == 5
        assert resp.failed_count == 2
        assert len(resp.failed_details) == 1