"""
测试运行时间服务
Phase 1.2: RuntimeService 功能测试

测试覆盖：
1. calculate_runtime - 计算指定时间段的运行时长
2. get_today_runtime - 当天累计运行时间
3. get_month_runtime - 当月累计运行时间
4. get_runtime_events - 开关机事件记录
5. supports_runtime - 检查是否支持运行时间统计
"""
import pytest
from datetime import datetime, UTC, timedelta
from unittest.mock import AsyncMock

from sqlalchemy import select

from app.models import Tenant, User, Device, DeviceData
from app.services.runtime import RuntimeService
from app.services.auth import get_password_hash


@pytest.fixture
async def setup_runtime_data(db_session):
    """创建测试数据用于运行时间计算"""
    # 创建租户
    tenant = Tenant(name="运行时间测试租户", code="test_runtime")
    db_session.add(tenant)
    await db_session.flush()

    # 创建设备
    device = Device(
        tenant_id=tenant.id,
        device_id="IMEI_RUNTIME",
        name="运行测试空调",
        protocol_version="V10",
        is_online=True,
        settings={}
    )
    db_session.add(device)

    # 创建无 airstate 的设备（模拟不支持）
    device_no_airstate = Device(
        tenant_id=tenant.id,
        device_id="IMEI_NO_AIRSTATE",
        name="无运行数据空调",
        protocol_version="V20",
        is_online=True,
        settings={}
    )
    db_session.add(device_no_airstate)
    await db_session.flush()

    # 创建时序数据（模拟一天的运行）
    now = datetime.now(UTC)
    base_time = now - timedelta(hours=24)

    # 模拟运行数据：
    # - 08:00 开机
    # - 12:00 关机（运行4小时）
    # - 14:00 开机
    # - 18:00 关机（运行4小时）
    # 总计：8小时

    airstate_data = [
        # 08:00 开机
        (base_time + timedelta(hours=8), 1, 25.0, 60.0),
        # 12:00 关机
        (base_time + timedelta(hours=12), 0, 27.0, 55.0),
        # 14:00 开机
        (base_time + timedelta(hours=14), 1, 26.0, 58.0),
        # 18:00 关机
        (base_time + timedelta(hours=18), 0, 28.0, 52.0),
    ]

    for time_data in airstate_data:
        data = DeviceData(
            device_id="IMEI_RUNTIME",
            tenant_id=tenant.id,
            time=time_data[0],
            airstate=time_data[1],
            temp=time_data[2],
            humi=time_data[3],
            csq=25
        )
        db_session.add(data)

    # 为无 airstate 的设备创建数据（无 airstate 字段）
    data_no_airstate = DeviceData(
        device_id="IMEI_NO_AIRSTATE",
        tenant_id=tenant.id,
        time=base_time + timedelta(hours=10),
        temp=25.0,
        humi=60.0,
        airstate=None,  # 无 airstate 数据
        csq=25
    )
    db_session.add(data_no_airstate)

    await db_session.commit()

    return {
        "tenant": tenant,
        "device": device,
        "device_no_airstate": device_no_airstate,
        "base_time": base_time,
        "now": now
    }


class TestCalculateRuntime:
    """测试 calculate_runtime 方法"""

    @pytest.mark.asyncio
    async def test_calculate_runtime_with_data(self, db_session, setup_runtime_data):
        """测试有 airstate 数据时的运行时间计算"""
        data = setup_runtime_data
        service = RuntimeService(db_session, tenant_id=data["tenant"].id)

        # 计算一天内的运行时间
        start_time = data["base_time"]
        end_time = data["now"]

        runtime = await service.calculate_runtime(
            "IMEI_RUNTIME",
            start_time,
            end_time
        )

        # 应该返回约8小时
        assert runtime is not None
        assert isinstance(runtime, float)
        # 允许一定误差（因为时间计算可能有精度问题）
        assert 7.9 <= runtime <= 8.1

    @pytest.mark.asyncio
    async def test_calculate_runtime_no_airstate(self, db_session, setup_runtime_data):
        """测试不支持 airstate 的设备返回 None"""
        data = setup_runtime_data
        service = RuntimeService(db_session, tenant_id=data["tenant"].id)

        runtime = await service.calculate_runtime(
            "IMEI_NO_AIRSTATE",
            data["base_time"],
            data["now"]
        )

        # 不支持 airstate，应该返回 None
        assert runtime is None

    @pytest.mark.asyncio
    async def test_calculate_runtime_empty_period(self, db_session, setup_runtime_data):
        """测试时间段内无数据时返回 0"""
        data = setup_runtime_data
        service = RuntimeService(db_session, tenant_id=data["tenant"].id)

        # 使用一个没有任何数据的时间段（很久以前）
        start_time = datetime(2020, 1, 1, tzinfo=UTC)
        end_time = datetime(2020, 1, 2, tzinfo=UTC)

        runtime = await service.calculate_runtime(
            "IMEI_RUNTIME",
            start_time,
            end_time
        )

        # 该时间段无运行，返回 0
        assert runtime == 0.0

    @pytest.mark.asyncio
    async def test_calculate_runtime_still_running(self, db_session):
        """测试设备仍在运行时的计算（最后一条记录是开机状态，设备在线）"""
        # 创建独立测试数据
        tenant = Tenant(name="仍在运行测试", code="test_still_running")
        db_session.add(tenant)
        await db_session.flush()

        device = Device(
            tenant_id=tenant.id,
            device_id="IMEI_RUNNING",
            name="仍在运行空调",
            protocol_version="V10",
            is_online=True,
            last_seen_at=datetime.now(UTC)  # 设备在线
        )
        db_session.add(device)

        now = datetime.now(UTC)
        # 创建数据：10:00开机，没有关机记录
        runtime_data = DeviceData(
            device_id="IMEI_RUNNING",
            tenant_id=tenant.id,
            time=now - timedelta(hours=10),
            airstate=1,
            temp=25.0,
            humi=60.0
        )
        db_session.add(runtime_data)
        await db_session.commit()

        service = RuntimeService(db_session, tenant_id=tenant.id)

        # 传入 last_seen_at 参数，设备在线时假设仍在运行
        runtime = await service.calculate_runtime(
            "IMEI_RUNNING",
            now - timedelta(hours=12),
            now,
            last_seen_at=device.last_seen_at
        )

        # 设备在线，应该假设仍在运行，从开机时间到现在
        assert runtime is not None
        # 约10小时
        assert 9.9 <= runtime <= 10.1


class TestTodayMonthRuntime:
    """测试当天/当月运行时间"""

    @pytest.mark.asyncio
    async def test_get_today_runtime(self, db_session, setup_runtime_data):
        """测试当天运行时间"""
        data = setup_runtime_data
        service = RuntimeService(db_session, tenant_id=data["tenant"].id)

        runtime = await service.get_today_runtime("IMEI_RUNTIME")

        assert runtime is not None
        assert isinstance(runtime, float)

    @pytest.mark.asyncio
    async def test_get_today_runtime_no_airstate(self, db_session, setup_runtime_data):
        """测试不支持的设备当天运行时间返回 None"""
        data = setup_runtime_data
        service = RuntimeService(db_session, tenant_id=data["tenant"].id)

        runtime = await service.get_today_runtime("IMEI_NO_AIRSTATE")

        assert runtime is None

    @pytest.mark.asyncio
    async def test_get_month_runtime(self, db_session, setup_runtime_data):
        """测试当月运行时间"""
        data = setup_runtime_data
        service = RuntimeService(db_session, tenant_id=data["tenant"].id)

        runtime = await service.get_month_runtime("IMEI_RUNTIME")

        assert runtime is not None
        assert isinstance(runtime, float)

    @pytest.mark.asyncio
    async def test_get_month_runtime_no_airstate(self, db_session, setup_runtime_data):
        """测试不支持的设备当月运行时间返回 None"""
        data = setup_runtime_data
        service = RuntimeService(db_session, tenant_id=data["tenant"].id)

        runtime = await service.get_month_runtime("IMEI_NO_AIRSTATE")

        assert runtime is None


class TestRuntimeEvents:
    """测试开关机事件记录"""

    @pytest.mark.asyncio
    async def test_get_runtime_events_supported(self, db_session, setup_runtime_data):
        """测试支持的设备返回事件列表"""
        data = setup_runtime_data
        service = RuntimeService(db_session, tenant_id=data["tenant"].id)

        result = await service.get_runtime_events("IMEI_RUNTIME")

        assert result["supported"] is True
        assert result["message"] == ""
        assert isinstance(result["events"], list)
        assert result["total"] >= 0
        assert result["page"] == 1
        assert result["page_size"] == 20

    @pytest.mark.asyncio
    async def test_get_runtime_events_not_supported(self, db_session, setup_runtime_data):
        """测试不支持的设备返回提示消息"""
        data = setup_runtime_data
        service = RuntimeService(db_session, tenant_id=data["tenant"].id)

        result = await service.get_runtime_events("IMEI_NO_AIRSTATE")

        assert result["supported"] is False
        assert result["message"] == "当前协议版本不支持空调状态监控"
        assert result["events"] == []
        assert result["total"] == 0

    @pytest.mark.asyncio
    async def test_get_runtime_events_pagination(self, db_session, setup_runtime_data):
        """测试分页功能"""
        data = setup_runtime_data
        service = RuntimeService(db_session, tenant_id=data["tenant"].id)

        # 第一页
        result = await service.get_runtime_events("IMEI_RUNTIME", page=1, page_size=2)
        assert result["page"] == 1
        assert result["page_size"] == 2
        assert len(result["events"]) <= 2

        # 第二页
        result2 = await service.get_runtime_events("IMEI_RUNTIME", page=2, page_size=2)
        assert result2["page"] == 2

    @pytest.mark.asyncio
    async def test_events_have_correct_structure(self, db_session, setup_runtime_data):
        """测试事件记录的数据结构"""
        data = setup_runtime_data
        service = RuntimeService(db_session, tenant_id=data["tenant"].id)

        result = await service.get_runtime_events("IMEI_RUNTIME")

        if result["events"]:
            event = result["events"][0]
            assert "time" in event
            assert "action" in event
            assert "duration" in event
            # action 应该是 "开机" 或 "关机"
            assert event["action"] in ["开机", "关机"]
            # time 应该是 ISO 格式字符串
            assert isinstance(event["time"], str)


class TestSupportsRuntime:
    """测试 supports_runtime 方法"""

    @pytest.mark.asyncio
    async def test_supports_runtime_true(self, db_session, setup_runtime_data):
        """测试支持 airstate 的设备返回 True"""
        data = setup_runtime_data
        service = RuntimeService(db_session, tenant_id=data["tenant"].id)

        supported = await service.supports_runtime("IMEI_RUNTIME")

        assert supported is True

    @pytest.mark.asyncio
    async def test_supports_runtime_false(self, db_session, setup_runtime_data):
        """测试不支持 airstate 的设备返回 False"""
        data = setup_runtime_data
        service = RuntimeService(db_session, tenant_id=data["tenant"].id)

        supported = await service.supports_runtime("IMEI_NO_AIRSTATE")

        assert supported is False

    @pytest.mark.asyncio
    async def test_supports_runtime_nonexistent_device(self, db_session):
        """测试不存在设备返回 False"""
        # 创建独立租户用于此测试
        tenant = Tenant(name="不存在设备测试", code="test_nonexist")
        db_session.add(tenant)
        await db_session.commit()

        service = RuntimeService(db_session, tenant_id=tenant.id)

        supported = await service.supports_runtime("IMEI_NOTEXIST")

        assert supported is False


class TestRuntimeEdgeCases:
    """边界情况测试"""

    @pytest.mark.asyncio
    async def test_runtime_with_only_off_states(self, db_session):
        """测试仅有关机状态的数据"""
        tenant = Tenant(name="仅关机测试", code="test_only_off")
        db_session.add(tenant)
        await db_session.flush()

        device = Device(
            tenant_id=tenant.id,
            device_id="IMEI_ONLY_OFF",
            name="仅关机空调",
            protocol_version="V10"
        )
        db_session.add(device)

        now = datetime.now(UTC)
        for i in range(5):
            runtime_data = DeviceData(
                device_id="IMEI_ONLY_OFF",
                tenant_id=tenant.id,
                time=now - timedelta(hours=i),
                airstate=0,
                temp=25.0,
                humi=60.0
            )
            db_session.add(runtime_data)
        await db_session.commit()

        service = RuntimeService(db_session, tenant_id=tenant.id)

        runtime = await service.calculate_runtime(
            "IMEI_ONLY_OFF",
            now - timedelta(hours=10),
            now
        )

        # 全是关机状态，运行时间为0
        assert runtime == 0.0

    @pytest.mark.asyncio
    async def test_runtime_with_only_on_states(self, db_session):
        """测试仅有开机状态的数据（设备在线）"""
        tenant = Tenant(name="仅开机测试", code="test_only_on")
        db_session.add(tenant)
        await db_session.flush()

        device = Device(
            tenant_id=tenant.id,
            device_id="IMEI_ONLY_ON",
            name="仅开机空调",
            protocol_version="V10",
            is_online=True,
            last_seen_at=datetime.now(UTC)  # 设备在线
        )
        db_session.add(device)

        now = datetime.now(UTC)
        start_time = now - timedelta(hours=5)
        for i in range(5):
            runtime_data = DeviceData(
                device_id="IMEI_ONLY_ON",
                tenant_id=tenant.id,
                time=start_time + timedelta(hours=i),
                airstate=1,
                temp=25.0,
                humi=60.0
            )
            db_session.add(runtime_data)
        await db_session.commit()

        service = RuntimeService(db_session, tenant_id=tenant.id)

        # 传入 last_seen_at 参数，设备在线时假设仍在运行
        runtime = await service.calculate_runtime(
            "IMEI_ONLY_ON",
            now - timedelta(hours=10),
            now,
            last_seen_at=device.last_seen_at
        )

        # 设备在线，全是开机状态，应该假设仍在运行
        assert runtime is not None
        # 大约5小时（从第一条开机记录到现在）
        assert runtime >= 4.0