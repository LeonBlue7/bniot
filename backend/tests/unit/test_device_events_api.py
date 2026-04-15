"""
测试设备开关机记录API
Phase 1.3: 设备事件API测试

测试覆盖：
1. GET /devices/{id}/events - 开关机事件记录
2. GET /devices/{id}/runtime - 运行时间统计
"""
import pytest
from datetime import datetime, UTC, timedelta
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.models import Tenant, User, Device, DeviceData
from app.services.auth import create_access_token, get_password_hash
from app.core.database import get_db


@pytest.fixture
async def setup_events_data(db_session):
    """创建测试数据用于事件API"""
    # 创建租户
    tenant = Tenant(name="事件API测试租户", code="test_events_api")
    db_session.add(tenant)
    await db_session.flush()

    # 创建用户
    user = User(
        tenant_id=tenant.id,
        username="testuser_events",
        password_hash=get_password_hash("test123"),
        role="admin"
    )
    db_session.add(user)
    await db_session.flush()

    # 创建支持 airstate 的设备
    device_v10 = Device(
        tenant_id=tenant.id,
        device_id="IMEI_EVENTS_V10",
        name="V10空调",
        protocol_version="V10",
        is_online=True,
        settings={}
    )
    db_session.add(device_v10)
    await db_session.flush()

    # 创建不支持 airstate 的设备
    device_v20 = Device(
        tenant_id=tenant.id,
        device_id="IMEI_EVENTS_V20",
        name="V20空调",
        protocol_version="V20",
        is_online=True,
        settings={}
    )
    db_session.add(device_v20)
    await db_session.flush()

    # 为V10设备创建 airstate 数据
    now = datetime.now(UTC)
    base_time = now - timedelta(hours=24)

    airstate_data = [
        (base_time + timedelta(hours=8), 1),   # 08:00 开机
        (base_time + timedelta(hours=12), 0),  # 12:00 关机
        (base_time + timedelta(hours=14), 1),  # 14:00 开机
        (base_time + timedelta(hours=18), 0),  # 18:00 关机
    ]

    for time_data in airstate_data:
        data = DeviceData(
            device_id="IMEI_EVENTS_V10",
            tenant_id=tenant.id,
            time=time_data[0],
            airstate=time_data[1],
            temp=25.0,
            humi=60.0,
            csq=25
        )
        db_session.add(data)

    # 为V20设备创建无 airstate 的数据
    data_no_airstate = DeviceData(
        device_id="IMEI_EVENTS_V20",
        tenant_id=tenant.id,
        time=base_time + timedelta(hours=10),
        temp=25.0,
        humi=60.0,
        airstate=None,
        csq=25
    )
    db_session.add(data_no_airstate)

    await db_session.commit()

    return {
        "tenant": tenant,
        "user": user,
        "device_v10": device_v10,
        "device_v20": device_v20
    }


class TestDeviceEventsAPI:
    """测试开关机事件API"""

    @pytest.mark.asyncio
    async def test_events_supported_device(self, db_session, setup_events_data):
        """测试支持 airstate 的设备返回事件列表"""
        data = setup_events_data
        token = create_access_token(
            data={"sub": data["user"].username, "tenant_id": data["tenant"].id}
        )

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            app.dependency_overrides[get_db] = lambda: db_session

            response = await client.get(
                f"/api/devices/{data['device_v10'].id}/events",
                headers={"Authorization": f"Bearer {token}"}
            )

            assert response.status_code == 200
            result = response.json()

            assert result["supported"] is True
            assert result["message"] == ""
            assert isinstance(result["events"], list)
            assert result["page"] == 1
            assert result["page_size"] == 20

            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_events_not_supported_device(self, db_session, setup_events_data):
        """测试不支持 airstate 的设备返回提示消息"""
        data = setup_events_data
        token = create_access_token(
            data={"sub": data["user"].username, "tenant_id": data["tenant"].id}
        )

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            app.dependency_overrides[get_db] = lambda: db_session

            response = await client.get(
                f"/api/devices/{data['device_v20'].id}/events",
                headers={"Authorization": f"Bearer {token}"}
            )

            assert response.status_code == 200
            result = response.json()

            assert result["supported"] is False
            assert result["message"] == "当前协议版本不支持空调状态监控"
            assert result["events"] == []
            assert result["total"] == 0

            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_events_pagination(self, db_session, setup_events_data):
        """测试事件分页"""
        data = setup_events_data
        token = create_access_token(
            data={"sub": data["user"].username, "tenant_id": data["tenant"].id}
        )

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            app.dependency_overrides[get_db] = lambda: db_session

            # 第一页
            response = await client.get(
                f"/api/devices/{data['device_v10'].id}/events?page=1&page_size=1",
                headers={"Authorization": f"Bearer {token}"}
            )

            assert response.status_code == 200
            result = response.json()
            assert result["page"] == 1
            assert result["page_size"] == 1
            assert len(result["events"]) <= 1

            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_events_device_not_found(self, db_session, setup_events_data):
        """测试设备不存在返回404"""
        data = setup_events_data
        token = create_access_token(
            data={"sub": data["user"].username, "tenant_id": data["tenant"].id}
        )

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            app.dependency_overrides[get_db] = lambda: db_session

            response = await client.get(
                "/api/devices/99999/events",
                headers={"Authorization": f"Bearer {token}"}
            )

            assert response.status_code == 404

            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_events_unauthorized(self, db_session, setup_events_data):
        """测试未授权返回401"""
        data = setup_events_data

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            app.dependency_overrides[get_db] = lambda: db_session

            response = await client.get(
                f"/api/devices/{data['device_v10'].id}/events"
            )

            assert response.status_code == 401

            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_events_tenant_isolation(self, db_session, setup_events_data):
        """测试租户隔离，不能访问其他租户设备"""
        data = setup_events_data

        # 创建另一个租户
        other_tenant = Tenant(name="其他租户", code="other_events")
        db_session.add(other_tenant)
        await db_session.flush()

        other_user = User(
            tenant_id=other_tenant.id,
            username="otheruser_events",
            password_hash=get_password_hash("test123"),
            role="admin"
        )
        db_session.add(other_user)
        await db_session.commit()

        # 用其他租户的token访问
        other_token = create_access_token(
            data={"sub": other_user.username, "tenant_id": other_tenant.id}
        )

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            app.dependency_overrides[get_db] = lambda: db_session

            response = await client.get(
                f"/api/devices/{data['device_v10'].id}/events",
                headers={"Authorization": f"Bearer {other_token}"}
            )

            assert response.status_code == 404

            app.dependency_overrides.clear()


class TestDeviceRuntimeAPI:
    """测试运行时间API"""

    @pytest.mark.asyncio
    async def test_runtime_supported_device(self, db_session, setup_events_data):
        """测试支持 airstate 的设备返回运行时间"""
        data = setup_events_data
        token = create_access_token(
            data={"sub": data["user"].username, "tenant_id": data["tenant"].id}
        )

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            app.dependency_overrides[get_db] = lambda: db_session

            response = await client.get(
                f"/api/devices/{data['device_v10'].id}/runtime",
                headers={"Authorization": f"Bearer {token}"}
            )

            assert response.status_code == 200
            result = response.json()

            assert result["supported"] is True
            assert result["message"] == ""
            assert "today_runtime" in result
            assert "month_runtime" in result

            # 运行时间应该是数字或null
            if result["today_runtime"] is not None:
                assert isinstance(result["today_runtime"], (int, float))

            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_runtime_not_supported_device(self, db_session, setup_events_data):
        """测试不支持 airstate 的设备返回提示消息"""
        data = setup_events_data
        token = create_access_token(
            data={"sub": data["user"].username, "tenant_id": data["tenant"].id}
        )

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            app.dependency_overrides[get_db] = lambda: db_session

            response = await client.get(
                f"/api/devices/{data['device_v20'].id}/runtime",
                headers={"Authorization": f"Bearer {token}"}
            )

            assert response.status_code == 200
            result = response.json()

            assert result["supported"] is False
            assert result["message"] == "当前协议版本不支持空调状态监控"
            assert result["today_runtime"] is None
            assert result["month_runtime"] is None

            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_runtime_device_not_found(self, db_session, setup_events_data):
        """测试设备不存在返回404"""
        data = setup_events_data
        token = create_access_token(
            data={"sub": data["user"].username, "tenant_id": data["tenant"].id}
        )

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            app.dependency_overrides[get_db] = lambda: db_session

            response = await client.get(
                "/api/devices/99999/runtime",
                headers={"Authorization": f"Bearer {token}"}
            )

            assert response.status_code == 404

            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_runtime_unauthorized(self, db_session, setup_events_data):
        """测试未授权返回401"""
        data = setup_events_data

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            app.dependency_overrides[get_db] = lambda: db_session

            response = await client.get(
                f"/api/devices/{data['device_v10'].id}/runtime"
            )

            assert response.status_code == 401

            app.dependency_overrides.clear()


class TestEventsEdgeCases:
    """边界情况测试"""

    @pytest.mark.asyncio
    async def test_events_device_no_data(self, db_session):
        """测试设备没有任何数据"""
        tenant = Tenant(name="无数据测试", code="test_no_data")
        db_session.add(tenant)
        await db_session.flush()

        user = User(
            tenant_id=tenant.id,
            username="testuser_nodata",
            password_hash=get_password_hash("test123"),
            role="admin"
        )
        db_session.add(user)

        device = Device(
            tenant_id=tenant.id,
            device_id="IMEI_NO_DATA",
            name="无数据空调",
            protocol_version="V10"
        )
        db_session.add(device)
        await db_session.commit()

        token = create_access_token(
            data={"sub": user.username, "tenant_id": tenant.id}
        )

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            app.dependency_overrides[get_db] = lambda: db_session

            response = await client.get(
                f"/api/devices/{device.id}/events",
                headers={"Authorization": f"Bearer {token}"}
            )

            assert response.status_code == 200
            result = response.json()
            # 无数据，不支持
            assert result["supported"] is False

            app.dependency_overrides.clear()