"""
测试设备详情API扩展
Phase 1.4: 设备详情API新增字段测试

测试覆盖：
1. zone_name 分区名称
2. firmware_version 固件版本
3. csq 信号强度
4. alarmhumi 湿度告警
5. air_err 空调故障码
6. temp/humi/airstate/current/alarmtemp 实时数据
7. supports_runtime/today_runtime/month_runtime 运行统计
"""
import pytest
from datetime import datetime, UTC, timedelta
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.models import Tenant, User, Zone, Device, DeviceData
from app.services.auth import create_access_token, get_password_hash
from app.core.database import get_db


@pytest.fixture
async def setup_detail_data(db_session):
    """创建测试数据用于详情API"""
    # 创建租户
    tenant = Tenant(name="详情API测试租户", code="test_detail_api")
    db_session.add(tenant)
    await db_session.flush()

    # 创建用户
    user = User(
        tenant_id=tenant.id,
        username="testuser_detail",
        password_hash=get_password_hash("test123"),
        role="admin"
    )
    db_session.add(user)
    await db_session.flush()

    # 创建分区
    zone = Zone(
        tenant_id=tenant.id,
        name="测试分区",
        description="测试分区描述"
    )
    db_session.add(zone)
    await db_session.flush()

    # 创建V10设备（支持airstate）
    device_v10 = Device(
        tenant_id=tenant.id,
        device_id="IMEI_DETAIL_V10",
        name="V10详情测试空调",
        zone_id=zone.id,
        protocol_version="V10",
        sim_card="13800138001",
        firmware_version="1.0.0",
        is_online=True,
        settings={"temp_set": 26}
    )
    db_session.add(device_v10)
    await db_session.flush()

    # 创建V20设备（不支持airstate）
    device_v20 = Device(
        tenant_id=tenant.id,
        device_id="IMEI_DETAIL_V20",
        name="V20详情测试空调",
        zone_id=None,
        protocol_version="V20",
        sim_card="13800138002",
        firmware_version="2.0.0",
        is_online=True,
        settings={"temp_set": 24}
    )
    db_session.add(device_v20)
    await db_session.flush()

    # 创建V10设备的时序数据（含airstate）
    now = datetime.now(UTC)
    base_time = now - timedelta(hours=24)

    airstate_data = [
        (base_time + timedelta(hours=8), 1, 25.5, 60.2, 5.2, 25, 0, 0, None),
        (base_time + timedelta(hours=12), 0, 27.0, 55.0, 0.0, 20, 1, 0, 1),  # 告警+故障
        (base_time + timedelta(hours=14), 1, 26.0, 58.0, 4.8, 22, 0, 1, None),  # 湿度告警
        (base_time + timedelta(hours=18), 0, 28.0, 52.0, 0.0, 18, 0, 0, None),
    ]

    for time_data in airstate_data:
        data = DeviceData(
            device_id="IMEI_DETAIL_V10",
            tenant_id=tenant.id,
            time=time_data[0],
            airstate=time_data[1],
            temp=time_data[2],
            humi=time_data[3],
            current=time_data[4],
            csq=time_data[5],
            alarmtemp=time_data[6],
            alarmhumi=time_data[7],
            air_err=time_data[8]
        )
        db_session.add(data)

    # 创建V20设备的时序数据（无airstate）
    data_v20 = DeviceData(
        device_id="IMEI_DETAIL_V20",
        tenant_id=tenant.id,
        time=now - timedelta(hours=2),
        temp=24.0,
        humi=58.0,
        airstate=None,  # V20不支持airstate
        current=None,
        csq=23,
        alarmtemp=0,
        alarmhumi=0,
        air_err=None
    )
    db_session.add(data_v20)

    await db_session.commit()

    return {
        "tenant": tenant,
        "user": user,
        "zone": zone,
        "device_v10": device_v10,
        "device_v20": device_v20
    }


class TestDeviceDetailNewFields:
    """测试详情API新增字段"""

    @pytest.mark.asyncio
    async def test_detail_returns_zone_name(self, db_session, setup_detail_data):
        """测试详情返回zone_name"""
        data = setup_detail_data
        token = create_access_token(
            data={"sub": data["user"].username, "tenant_id": data["tenant"].id}
        )

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            app.dependency_overrides[get_db] = lambda: db_session

            response = await client.get(
                f"/api/devices/{data['device_v10'].id}",
                headers={"Authorization": f"Bearer {token}"}
            )

            assert response.status_code == 200
            result = response.json()

            assert "zone_name" in result
            assert result["zone_name"] == "测试分区"

            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_detail_returns_firmware_version(self, db_session, setup_detail_data):
        """测试详情返回firmware_version"""
        data = setup_detail_data
        token = create_access_token(
            data={"sub": data["user"].username, "tenant_id": data["tenant"].id}
        )

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            app.dependency_overrides[get_db] = lambda: db_session

            response = await client.get(
                f"/api/devices/{data['device_v10'].id}",
                headers={"Authorization": f"Bearer {token}"}
            )

            assert response.status_code == 200
            result = response.json()

            assert "firmware_version" in result
            assert result["firmware_version"] == "1.0.0"

            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_detail_returns_realtime_data(self, db_session, setup_detail_data):
        """测试详情返回实时数据（temp/humi/csq/alarmtemp/alarmhumi/air_err）"""
        data = setup_detail_data
        token = create_access_token(
            data={"sub": data["user"].username, "tenant_id": data["tenant"].id}
        )

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            app.dependency_overrides[get_db] = lambda: db_session

            response = await client.get(
                f"/api/devices/{data['device_v10'].id}",
                headers={"Authorization": f"Bearer {token}"}
            )

            assert response.status_code == 200
            result = response.json()

            # 验证实时数据字段存在
            assert "temp" in result
            assert "humi" in result
            assert "csq" in result
            assert "alarmtemp" in result
            assert "alarmhumi" in result
            assert "air_err" in result
            assert "airstate" in result
            assert "current" in result

            # 验证最新数据值
            assert result["temp"] == 28.0  # 最新记录的值
            assert result["humi"] == 52.0
            assert result["csq"] == 18

            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_detail_device_without_zone(self, db_session, setup_detail_data):
        """测试未分配分区的设备zone_name为null"""
        data = setup_detail_data
        token = create_access_token(
            data={"sub": data["user"].username, "tenant_id": data["tenant"].id}
        )

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            app.dependency_overrides[get_db] = lambda: db_session

            response = await client.get(
                f"/api/devices/{data['device_v20'].id}",
                headers={"Authorization": f"Bearer {token}"}
            )

            assert response.status_code == 200
            result = response.json()

            assert "zone_name" in result
            assert result["zone_name"] is None

            app.dependency_overrides.clear()


class TestDeviceDetailRuntimeStats:
    """测试运行时间统计"""

    @pytest.mark.asyncio
    async def test_detail_runtime_supported(self, db_session, setup_detail_data):
        """测试支持airstate的设备返回运行统计"""
        data = setup_detail_data
        token = create_access_token(
            data={"sub": data["user"].username, "tenant_id": data["tenant"].id}
        )

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            app.dependency_overrides[get_db] = lambda: db_session

            response = await client.get(
                f"/api/devices/{data['device_v10'].id}",
                headers={"Authorization": f"Bearer {token}"}
            )

            assert response.status_code == 200
            result = response.json()

            # 验证运行时间字段存在
            assert "supports_runtime" in result
            assert "today_runtime" in result
            assert "month_runtime" in result

            assert result["supports_runtime"] is True

            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_detail_runtime_not_supported(self, db_session, setup_detail_data):
        """测试不支持airstate的设备不返回运行统计"""
        data = setup_detail_data
        token = create_access_token(
            data={"sub": data["user"].username, "tenant_id": data["tenant"].id}
        )

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            app.dependency_overrides[get_db] = lambda: db_session

            response = await client.get(
                f"/api/devices/{data['device_v20'].id}",
                headers={"Authorization": f"Bearer {token}"}
            )

            assert response.status_code == 200
            result = response.json()

            assert result["supports_runtime"] is False
            assert result["today_runtime"] is None
            assert result["month_runtime"] is None

            app.dependency_overrides.clear()


class TestDeviceDetailEdgeCases:
    """边界情况测试"""

    @pytest.mark.asyncio
    async def test_detail_device_without_data(self, db_session):
        """测试设备无实时数据时字段为null"""
        tenant = Tenant(name="无数据详情测试", code="test_detail_no_data")
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
            device_id="IMEI_DETAIL_NODATA",
            name="无数据详情空调",
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
                f"/api/devices/{device.id}",
                headers={"Authorization": f"Bearer {token}"}
            )

            assert response.status_code == 200
            result = response.json()

            # 无数据时，实时数据字段应该为null
            assert result["temp"] is None
            assert result["humi"] is None
            assert result["csq"] is None
            assert result["zone_name"] is None

            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_detail_device_not_found(self, db_session, setup_detail_data):
        """测试设备不存在返回404"""
        data = setup_detail_data
        token = create_access_token(
            data={"sub": data["user"].username, "tenant_id": data["tenant"].id}
        )

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            app.dependency_overrides[get_db] = lambda: db_session

            response = await client.get(
                "/api/devices/99999",
                headers={"Authorization": f"Bearer {token}"}
            )

            assert response.status_code == 404

            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_detail_unauthorized(self, db_session, setup_detail_data):
        """测试未授权返回401"""
        data = setup_detail_data

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            app.dependency_overrides[get_db] = lambda: db_session

            response = await client.get(
                f"/api/devices/{data['device_v10'].id}"
            )

            assert response.status_code == 401

            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_detail_tenant_isolation(self, db_session, setup_detail_data):
        """测试租户隔离"""
        data = setup_detail_data

        # 创建另一个租户
        other_tenant = Tenant(name="其他租户详情", code="other_detail")
        db_session.add(other_tenant)
        await db_session.flush()

        other_user = User(
            tenant_id=other_tenant.id,
            username="otheruser_detail",
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
                f"/api/devices/{data['device_v10'].id}",
                headers={"Authorization": f"Bearer {other_token}"}
            )

            assert response.status_code == 404

            app.dependency_overrides.clear()