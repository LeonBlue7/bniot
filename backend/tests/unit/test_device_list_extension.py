"""
测试设备列表API扩展
Phase 1.1: 设备列表API新增字段、模糊查询扩展、协议版本筛选

测试覆盖：
1. 列表返回字段新增：temp, humi, alarmtemp, zone_name
2. 模糊查询扩展：SIM卡号、固件版本、分区名称
3. 协议版本筛选：V10/V20
"""
import pytest
from datetime import datetime, UTC
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select

from app.main import app
from app.models import Tenant, User, Zone, Device, DeviceData
from app.services.auth import create_access_token, get_password_hash


@pytest.fixture
async def setup_test_data(db_session):
    """创建测试数据"""
    # 创建租户
    tenant = Tenant(name="测试租户", code="test_devices")
    db_session.add(tenant)
    await db_session.flush()

    # 创建用户
    user = User(
        tenant_id=tenant.id,
        username="testuser_devices",
        password_hash=get_password_hash("test123"),
        role="admin"
    )
    db_session.add(user)
    await db_session.flush()

    # 创建分区
    zone1 = Zone(
        tenant_id=tenant.id,
        name="办公区",
        description="一楼办公区"
    )
    zone2 = Zone(
        tenant_id=tenant.id,
        name="会议室",
        description="二楼会议室"
    )
    db_session.add(zone1)
    db_session.add(zone2)
    await db_session.flush()

    # 创建设备
    device1 = Device(
        tenant_id=tenant.id,
        device_id="IMEI001",
        name="空调1",
        zone_id=zone1.id,
        protocol_version="V10",
        sim_card="13800138001",
        firmware_version="1.0.0",
        is_online=True,
        last_seen_at=datetime.now(UTC),
        settings={"temp_set": 26}
    )
    device2 = Device(
        tenant_id=tenant.id,
        device_id="IMEI002",
        name="空调2",
        zone_id=zone2.id,
        protocol_version="V20",
        sim_card="13800138002",
        firmware_version="2.0.0",
        is_online=False,
        settings={"temp_set": 24}
    )
    device3 = Device(
        tenant_id=tenant.id,
        device_id="IMEI003",
        name="空调3",
        zone_id=None,  # 未分配分区
        protocol_version="V10",
        sim_card="13900139003",
        firmware_version="1.0.1",
        is_online=True,
        settings={"temp_set": 25}
    )
    db_session.add(device1)
    db_session.add(device2)
    db_session.add(device3)
    await db_session.flush()

    # 创建设备数据（实时数据）
    data1 = DeviceData(
        device_id="IMEI001",
        tenant_id=tenant.id,
        temp=25.5,
        humi=60.2,
        airstate=1,
        current=5.2,
        csq=25,
        alarmtemp=0,
        alarmhumi=0,
        air_err=None
    )
    data2 = DeviceData(
        device_id="IMEI002",
        tenant_id=tenant.id,
        temp=26.8,
        humi=55.0,
        airstate=0,
        current=0.0,
        csq=20,
        alarmtemp=1,  # 温度告警
        alarmhumi=0,
        air_err=1  # 故障码
    )
    data3 = DeviceData(
        device_id="IMEI003",
        tenant_id=tenant.id,
        temp=24.0,
        humi=58.5,
        airstate=1,
        current=4.8,
        csq=22,
        alarmtemp=0,
        alarmhumi=0,
        air_err=None
    )
    db_session.add(data1)
    db_session.add(data2)
    db_session.add(data3)
    await db_session.commit()

    return {
        "tenant": tenant,
        "user": user,
        "zones": [zone1, zone2],
        "devices": [device1, device2, device3]
    }


class TestDeviceListNewFields:
    """测试设备列表新增字段"""

    @pytest.mark.asyncio
    async def test_list_returns_temp_field(self, db_session, setup_test_data):
        """测试列表返回temp字段"""
        data = setup_test_data
        token = create_access_token(
            data={"sub": data["user"].username, "tenant_id": data["tenant"].id}
        )

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            # Mock get_db dependency
            from app.core.database import get_db
            app.dependency_overrides[get_db] = lambda: db_session

            response = await client.get(
                "/api/devices",
                headers={"Authorization": f"Bearer {token}"}
            )

            assert response.status_code == 200
            devices = response.json()
            assert len(devices) >= 1

            # 查找IMEI001设备
            device1 = next((d for d in devices if d["device_id"] == "IMEI001"), None)
            assert device1 is not None
            # 应该返回temp字段
            assert "temp" in device1
            # temp应该是float或null
            if device1["temp"] is not None:
                assert isinstance(device1["temp"], (int, float))

            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_list_returns_humi_field(self, db_session, setup_test_data):
        """测试列表返回humi字段"""
        data = setup_test_data
        token = create_access_token(
            data={"sub": data["user"].username, "tenant_id": data["tenant"].id}
        )

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            from app.core.database import get_db
            app.dependency_overrides[get_db] = lambda: db_session

            response = await client.get(
                "/api/devices",
                headers={"Authorization": f"Bearer {token}"}
            )

            assert response.status_code == 200
            devices = response.json()

            device1 = next((d for d in devices if d["device_id"] == "IMEI001"), None)
            assert device1 is not None
            # 应该返回humi字段
            assert "humi" in device1
            if device1["humi"] is not None:
                assert isinstance(device1["humi"], (int, float))

            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_list_returns_alarmtemp_field(self, db_session, setup_test_data):
        """测试列表返回alarmtemp字段"""
        data = setup_test_data
        token = create_access_token(
            data={"sub": data["user"].username, "tenant_id": data["tenant"].id}
        )

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            from app.core.database import get_db
            app.dependency_overrides[get_db] = lambda: db_session

            response = await client.get(
                "/api/devices",
                headers={"Authorization": f"Bearer {token}"}
            )

            assert response.status_code == 200
            devices = response.json()

            device1 = next((d for d in devices if d["device_id"] == "IMEI001"), None)
            assert device1 is not None
            # 应该返回alarmtemp字段
            assert "alarmtemp" in device1
            if device1["alarmtemp"] is not None:
                assert isinstance(device1["alarmtemp"], int)

            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_list_returns_zone_name(self, db_session, setup_test_data):
        """测试列表返回zone_name字段"""
        data = setup_test_data
        token = create_access_token(
            data={"sub": data["user"].username, "tenant_id": data["tenant"].id}
        )

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            from app.core.database import get_db
            app.dependency_overrides[get_db] = lambda: db_session

            response = await client.get(
                "/api/devices",
                headers={"Authorization": f"Bearer {token}"}
            )

            assert response.status_code == 200
            devices = response.json()

            # 有分区的设备
            device1 = next((d for d in devices if d["device_id"] == "IMEI001"), None)
            assert device1 is not None
            assert "zone_name" in device1
            # zone_name应该关联Zone表获取
            if device1["zone_name"] is not None:
                assert device1["zone_name"] == "办公区"

            # 未分配分区的设备
            device3 = next((d for d in devices if d["device_id"] == "IMEI003"), None)
            assert device3 is not None
            assert device3.get("zone_name") is None

            app.dependency_overrides.clear()


class TestDeviceListSearchExtension:
    """测试模糊查询扩展"""

    @pytest.mark.asyncio
    async def test_search_by_sim_card(self, db_session, setup_test_data):
        """测试按SIM卡号搜索"""
        data = setup_test_data
        token = create_access_token(
            data={"sub": data["user"].username, "tenant_id": data["tenant"].id}
        )

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            from app.core.database import get_db
            app.dependency_overrides[get_db] = lambda: db_session

            # 按SIM卡号前缀搜索
            response = await client.get(
                "/api/devices?keyword=13800138001",
                headers={"Authorization": f"Bearer {token}"}
            )

            assert response.status_code == 200
            devices = response.json()
            # 应该只返回IMEI001
            assert len(devices) == 1
            assert devices[0]["device_id"] == "IMEI001"

            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_search_by_firmware_version(self, db_session, setup_test_data):
        """测试按固件版本搜索"""
        data = setup_test_data
        token = create_access_token(
            data={"sub": data["user"].username, "tenant_id": data["tenant"].id}
        )

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            from app.core.database import get_db
            app.dependency_overrides[get_db] = lambda: db_session

            # 按固件版本搜索
            response = await client.get(
                "/api/devices?keyword=2.0.0",
                headers={"Authorization": f"Bearer {token}"}
            )

            assert response.status_code == 200
            devices = response.json()
            # 应该只返回IMEI002（firmware_version=2.0.0）
            assert len(devices) == 1
            assert devices[0]["device_id"] == "IMEI002"

            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_search_by_zone_name(self, db_session, setup_test_data):
        """测试按分区名称搜索"""
        data = setup_test_data
        token = create_access_token(
            data={"sub": data["user"].username, "tenant_id": data["tenant"].id}
        )

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            from app.core.database import get_db
            app.dependency_overrides[get_db] = lambda: db_session

            # 按分区名称搜索
            response = await client.get(
                "/api/devices?keyword=办公",
                headers={"Authorization": f"Bearer {token}"}
            )

            assert response.status_code == 200
            devices = response.json()
            # 应该返回办公区的设备
            assert len(devices) >= 1
            for device in devices:
                if device.get("zone_name"):
                    assert "办公" in device["zone_name"]

            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_search_by_existing_fields(self, db_session, setup_test_data):
        """测试原有搜索字段仍可用（设备名称、设备ID）"""
        data = setup_test_data
        token = create_access_token(
            data={"sub": data["user"].username, "tenant_id": data["tenant"].id}
        )

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            from app.core.database import get_db
            app.dependency_overrides[get_db] = lambda: db_session

            # 按设备名称搜索
            response = await client.get(
                "/api/devices?keyword=空调1",
                headers={"Authorization": f"Bearer {token}"}
            )

            assert response.status_code == 200
            devices = response.json()
            assert len(devices) == 1
            assert devices[0]["name"] == "空调1"

            # 按设备ID搜索
            response = await client.get(
                "/api/devices?keyword=IMEI002",
                headers={"Authorization": f"Bearer {token}"}
            )

            assert response.status_code == 200
            devices = response.json()
            assert len(devices) == 1
            assert devices[0]["device_id"] == "IMEI002"

            app.dependency_overrides.clear()


class TestDeviceListProtocolFilter:
    """测试协议版本筛选"""

    @pytest.mark.asyncio
    async def test_filter_by_v10(self, db_session, setup_test_data):
        """测试筛选V10协议版本"""
        data = setup_test_data
        token = create_access_token(
            data={"sub": data["user"].username, "tenant_id": data["tenant"].id}
        )

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            from app.core.database import get_db
            app.dependency_overrides[get_db] = lambda: db_session

            response = await client.get(
                "/api/devices?protocol_version=V10",
                headers={"Authorization": f"Bearer {token}"}
            )

            assert response.status_code == 200
            devices = response.json()
            # 只返回V10设备
            for device in devices:
                assert device["protocol_version"] == "V10"

            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_filter_by_v20(self, db_session, setup_test_data):
        """测试筛选V20协议版本"""
        data = setup_test_data
        token = create_access_token(
            data={"sub": data["user"].username, "tenant_id": data["tenant"].id}
        )

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            from app.core.database import get_db
            app.dependency_overrides[get_db] = lambda: db_session

            response = await client.get(
                "/api/devices?protocol_version=V20",
                headers={"Authorization": f"Bearer {token}"}
            )

            assert response.status_code == 200
            devices = response.json()
            # 只返回V20设备
            for device in devices:
                assert device["protocol_version"] == "V20"

            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_filter_all_versions(self, db_session, setup_test_data):
        """测试不筛选时返回所有版本"""
        data = setup_test_data
        token = create_access_token(
            data={"sub": data["user"].username, "tenant_id": data["tenant"].id}
        )

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            from app.core.database import get_db
            app.dependency_overrides[get_db] = lambda: db_session

            response = await client.get(
                "/api/devices",
                headers={"Authorization": f"Bearer {token}"}
            )

            assert response.status_code == 200
            devices = response.json()
            # 应该返回所有3个设备
            assert len(devices) == 3
            versions = [d["protocol_version"] for d in devices]
            assert "V10" in versions
            assert "V20" in versions

            app.dependency_overrides.clear()


class TestDeviceListEdgeCases:
    """边界情况测试"""

    @pytest.mark.asyncio
    async def test_device_without_data(self, db_session, setup_test_data):
        """测试设备无实时数据时字段为null"""
        data = setup_test_data

        # 创建一个没有DeviceData的设备
        device4 = Device(
            tenant_id=data["tenant"].id,
            device_id="IMEI004",
            name="空调4",
            zone_id=None,
            protocol_version="V10",
            sim_card=None,
            firmware_version=None,
            is_online=False,
            settings={}
        )
        db_session.add(device4)
        await db_session.commit()

        token = create_access_token(
            data={"sub": data["user"].username, "tenant_id": data["tenant"].id}
        )

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            from app.core.database import get_db
            app.dependency_overrides[get_db] = lambda: db_session

            response = await client.get(
                "/api/devices",
                headers={"Authorization": f"Bearer {token}"}
            )

            assert response.status_code == 200
            devices = response.json()

            device4 = next((d for d in devices if d["device_id"] == "IMEI004"), None)
            assert device4 is not None
            # 无数据的设备，这些字段应该为null
            assert device4["temp"] is None
            assert device4["humi"] is None
            assert device4["alarmtemp"] is None
            assert device4["zone_name"] is None

            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_tenant_isolation(self, db_session, setup_test_data):
        """测试租户隔离，不能看到其他租户的设备"""
        data = setup_test_data

        # 创建另一个租户和设备
        other_tenant = Tenant(name="其他租户", code="other_tenant")
        db_session.add(other_tenant)
        await db_session.flush()

        other_user = User(
            tenant_id=other_tenant.id,
            username="otheruser",
            password_hash=get_password_hash("test123"),
            role="admin"
        )
        db_session.add(other_user)

        other_device = Device(
            tenant_id=other_tenant.id,
            device_id="IMEI999",
            name="其他设备",
            protocol_version="V10"
        )
        db_session.add(other_device)
        await db_session.commit()

        # 用原租户的token请求
        token = create_access_token(
            data={"sub": data["user"].username, "tenant_id": data["tenant"].id}
        )

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            from app.core.database import get_db
            app.dependency_overrides[get_db] = lambda: db_session

            response = await client.get(
                "/api/devices",
                headers={"Authorization": f"Bearer {token}"}
            )

            assert response.status_code == 200
            devices = response.json()
            # 不应该看到其他租户的设备
            device_ids = [d["device_id"] for d in devices]
            assert "IMEI999" not in device_ids
            # 应该看到自己的设备
            assert "IMEI001" in device_ids

            app.dependency_overrides.clear()