"""
测试报表 API 端点
Phase 4 报表与分析功能 - TDD 开发

TDD 流程：
1. RED: 编写失败测试
2. GREEN: 实现最小代码使测试通过
3. REFACTOR: 重构优化

测试策略：
- 使用 TestClient 和 dependency_override
- 测试 API 端点存在性
- 测试返回数据结构
- 测试边界情况
"""
import pytest
from datetime import datetime, timedelta, UTC
from unittest.mock import AsyncMock, MagicMock
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select


class MockDBResult:
    """Mock 数据库查询结果"""
    def __init__(self, items=None):
        self._items = items or []

    def scalars(self):
        return self

    def all(self):
        return self._items


def create_mock_db_session(devices=None, data=None, alarms=None, zones=None):
    """创建 Mock 数据库会话"""
    mock_db = AsyncMock()

    async def mock_execute(query):
        # 根据查询类型返回不同的 Mock 结果
        if hasattr(query, 'column_descriptions'):
            # 判断是哪种查询
            table_name = str(query.column_descriptions[0]['type'])
            if 'Device' in table_name:
                return MockDBResult(devices)
            elif 'DeviceData' in table_name:
                return MockDBResult(data)
            elif 'Alarm' in table_name:
                return MockDBResult(alarms)
            elif 'Zone' in table_name:
                return MockDBResult(zones)
        return MockDBResult()

    mock_db.execute = mock_execute
    return mock_db


class TestEnergyStatsEndpoint:
    """测试能耗统计端点"""

    @pytest.mark.asyncio
    async def test_get_energy_stats_requires_auth(self):
        """测试能耗统计需要认证"""
        from app.main import app

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/api/reports/energy")
            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_energy_stats_returns_correct_structure(self):
        """测试能耗统计返回正确数据结构"""
        from app.main import app
        from app.core.database import get_db
        from app.services.auth import get_current_user

        # 创建 Mock 设备
        mock_device = MagicMock()
        mock_device.device_id = "test_device_001"
        mock_device.name = "测试设备"

        # 创建 Mock 数据库会话
        mock_db = create_mock_db_session(devices=[mock_device], data=[])

        # 创建 Mock 用户
        mock_user = MagicMock()
        mock_user.tenant_id = 1
        mock_user.username = "testuser"

        # 覆盖依赖
        async def override_get_db():
            yield mock_db

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_current_user] = lambda: mock_user

        try:
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                now = datetime.now(UTC)
                response = await client.get(
                    "/api/reports/energy",
                    params={
                        "start_time": (now - timedelta(days=1)).isoformat(),
                        "end_time": now.isoformat()
                    }
                )
                assert response.status_code == 200
                data = response.json()
                assert "data" in data
                assert "total_energy" in data
                assert "start_time" in data
                assert "end_time" in data
                assert "granularity" in data
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_get_energy_stats_invalid_time_range(self):
        """测试无效时间范围返回错误"""
        from app.main import app
        from app.core.database import get_db
        from app.services.auth import get_current_user

        mock_db = create_mock_db_session()
        mock_user = MagicMock()
        mock_user.tenant_id = 1

        async def override_get_db():
            yield mock_db

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_current_user] = lambda: mock_user

        try:
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                now = datetime.now(UTC)
                response = await client.get(
                    "/api/reports/energy",
                    params={
                        "start_time": now.isoformat(),
                        "end_time": (now - timedelta(days=1)).isoformat()
                    }
                )
                assert response.status_code == 400
        finally:
            app.dependency_overrides.clear()


class TestTrendEndpoint:
    """测试温湿度趋势端点"""

    @pytest.mark.asyncio
    async def test_get_trend_requires_auth(self):
        """测试趋势数据需要认证"""
        from app.main import app

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/api/reports/trend")
            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_trend_returns_correct_structure(self):
        """测试温湿度趋势返回正确数据结构"""
        from app.main import app
        from app.core.database import get_db
        from app.services.auth import get_current_user

        mock_device = MagicMock()
        mock_device.device_id = "test_device_001"
        mock_device.name = "测试设备"

        mock_db = create_mock_db_session(devices=[mock_device], data=[])

        mock_user = MagicMock()
        mock_user.tenant_id = 1

        async def override_get_db():
            yield mock_db

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_current_user] = lambda: mock_user

        try:
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                now = datetime.now(UTC)
                response = await client.get(
                    "/api/reports/trend",
                    params={
                        "start_time": (now - timedelta(hours=24)).isoformat(),
                        "end_time": now.isoformat()
                    }
                )
                assert response.status_code == 200
                data = response.json()
                assert "data" in data
                assert "start_time" in data
                assert "end_time" in data
                assert "interval" in data
        finally:
            app.dependency_overrides.clear()


class TestAlarmStatsEndpoint:
    """测试告警统计端点"""

    @pytest.mark.asyncio
    async def test_get_alarm_stats_requires_auth(self):
        """测试告警统计需要认证"""
        from app.main import app

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/api/reports/alarms")
            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_alarm_stats_returns_correct_structure(self):
        """测试告警统计返回正确数据结构"""
        from app.main import app
        from app.core.database import get_db
        from app.services.auth import get_current_user

        mock_alarm = MagicMock()
        mock_alarm.type = "offline"
        mock_alarm.severity = "high"
        mock_alarm.device_id = "test_device"
        mock_alarm.is_resolved = False

        mock_db = create_mock_db_session(alarms=[mock_alarm])

        mock_user = MagicMock()
        mock_user.tenant_id = 1

        async def override_get_db():
            yield mock_db

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_current_user] = lambda: mock_user

        try:
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                now = datetime.now(UTC)
                response = await client.get(
                    "/api/reports/alarms",
                    params={
                        "start_time": (now - timedelta(days=7)).isoformat(),
                        "end_time": now.isoformat()
                    }
                )
                assert response.status_code == 200
                data = response.json()
                assert "data" in data
                assert "total_alarms" in data
                assert "resolved_alarms" in data
                assert "unresolved_alarms" in data
                assert "start_time" in data
                assert "end_time" in data
        finally:
            app.dependency_overrides.clear()


class TestRuntimeStatsEndpoint:
    """测试设备运行时长统计端点"""

    @pytest.mark.asyncio
    async def test_get_runtime_stats_requires_auth(self):
        """测试运行时长统计需要认证"""
        from app.main import app

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/api/reports/runtime")
            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_runtime_stats_returns_correct_structure(self):
        """测试运行时长统计返回正确数据结构"""
        from app.main import app
        from app.core.database import get_db
        from app.services.auth import get_current_user

        mock_device = MagicMock()
        mock_device.device_id = "test_device_001"
        mock_device.name = "测试设备"
        mock_device.zone_id = None

        mock_db = create_mock_db_session(devices=[mock_device], data=[], zones=[])

        mock_user = MagicMock()
        mock_user.tenant_id = 1

        async def override_get_db():
            yield mock_db

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_current_user] = lambda: mock_user

        try:
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                now = datetime.now(UTC)
                response = await client.get(
                    "/api/reports/runtime",
                    params={
                        "start_time": (now - timedelta(days=30)).isoformat(),
                        "end_time": now.isoformat()
                    }
                )
                assert response.status_code == 200
                data = response.json()
                assert "data" in data
                assert "total_devices" in data
                assert "avg_runtime_hours" in data
                assert "start_time" in data
                assert "end_time" in data
        finally:
            app.dependency_overrides.clear()


class TestExportEndpoint:
    """测试报表导出端点"""

    @pytest.mark.asyncio
    async def test_export_requires_auth(self):
        """测试报表导出需要认证"""
        from app.main import app

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/api/reports/export")
            # export 需要必填参数，未认证时返回 401 或 422
            assert response.status_code in [401, 422]

    @pytest.mark.asyncio
    async def test_export_csv_format(self):
        """测试导出 CSV 格式"""
        from app.main import app
        from app.core.database import get_db
        from app.services.auth import get_current_user

        mock_device = MagicMock()
        mock_device.device_id = "test_device_001"
        mock_device.name = "测试设备"

        mock_db = create_mock_db_session(devices=[mock_device], data=[])

        mock_user = MagicMock()
        mock_user.tenant_id = 1

        async def override_get_db():
            yield mock_db

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_current_user] = lambda: mock_user

        try:
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                now = datetime.now(UTC)
                response = await client.get(
                    "/api/reports/export",
                    params={
                        "report_type": "energy",
                        "start_time": (now - timedelta(days=1)).isoformat(),
                        "end_time": now.isoformat(),
                        "format": "csv"
                    }
                )
                assert response.status_code == 200
                # 检查返回 CSV 文件
                content_type = response.headers.get("content-type")
                assert content_type and content_type.startswith("text/csv")
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_export_invalid_report_type_returns_error(self):
        """测试无效报表类型返回错误"""
        from app.main import app
        from app.core.database import get_db
        from app.services.auth import get_current_user

        mock_db = create_mock_db_session()
        mock_user = MagicMock()
        mock_user.tenant_id = 1

        async def override_get_db():
            yield mock_db

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_current_user] = lambda: mock_user

        try:
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                now = datetime.now(UTC)
                response = await client.get(
                    "/api/reports/export",
                    params={
                        "report_type": "invalid_type",
                        "start_time": (now - timedelta(days=1)).isoformat(),
                        "end_time": now.isoformat()
                    }
                )
                assert response.status_code == 400
        finally:
            app.dependency_overrides.clear()


class TestReportServiceUnit:
    """测试报表服务层（单元测试）"""

    def test_calculate_energy_from_current_data(self):
        """测试计算能耗"""
        from app.services.reports import calculate_energy

        # 模拟电流数据
        current_data = [
            {"time": "2024-01-01T00:00:00", "current": 5.0},  # 5A
            {"time": "2024-01-01T01:00:00", "current": 5.5},  # 5.5A
            {"time": "2024-01-01T02:00:00", "current": 4.8},  # 4.8A
        ]

        # 计算能耗
        result = calculate_energy(current_data, voltage=220)

        # 平均电流 = (5.0 + 5.5 + 4.8) / 3 = 5.1A
        # 平均功率 = 220V * 5.1A = 1122W
        # 能耗 = 1122W * 3小时 / 1000 = 3.366 kWh
        assert result > 0
        assert isinstance(result, float)
        assert result == 3.37  # 四舍五入到两位小数

    def test_calculate_energy_empty_data(self):
        """测试空数据返回0"""
        from app.services.reports import calculate_energy

        result = calculate_energy([])
        assert result == 0.0

    def test_calculate_runtime_from_airstate_data(self):
        """测试计算运行时长"""
        from app.services.reports import calculate_runtime

        # 模拟 airstate 数据 (1=开机, 0=关机)
        airstate_data = [
            {"time": "2024-01-01T00:00:00", "airstate": 1},
            {"time": "2024-01-01T01:00:00", "airstate": 1},
            {"time": "2024-01-01T02:00:00", "airstate": 0},
            {"time": "2024-01-01T03:00:00", "airstate": 0},
            {"time": "2024-01-01T04:00:00", "airstate": 1},
        ]

        # 计算运行时长
        result = calculate_runtime(airstate_data)

        # 开机时长 = 3小时
        assert result == 3.0

    def test_calculate_runtime_empty_data(self):
        """测试空数据返回0"""
        from app.services.reports import calculate_runtime

        result = calculate_runtime([])
        assert result == 0.0

    def test_aggregate_alarm_stats_by_type(self):
        """测试按类型聚合告警统计"""
        from app.services.reports import aggregate_alarm_stats

        alarms = [
            {"type": "offline", "severity": "high", "is_resolved": True},
            {"type": "offline", "severity": "high", "is_resolved": False},
            {"type": "temp_alarm", "severity": "medium", "is_resolved": False},
        ]

        result = aggregate_alarm_stats(alarms, group_by="type")

        assert len(result) == 2  # 两种类型
        # 验证 offline 类型的统计
        offline_stat = next(s for s in result if s["type"] == "offline")
        assert offline_stat["count"] == 2
        assert offline_stat["resolved_count"] == 1
        assert offline_stat["unresolved_count"] == 1
        assert offline_stat["severity"] == "high"

    def test_aggregate_alarm_stats_by_severity(self):
        """测试按严重程度聚合告警统计"""
        from app.services.reports import aggregate_alarm_stats

        alarms = [
            {"type": "offline", "severity": "high", "is_resolved": True},
            {"type": "offline", "severity": "high", "is_resolved": False},
            {"type": "temp_alarm", "severity": "medium", "is_resolved": False},
        ]

        result = aggregate_alarm_stats(alarms, group_by="severity")

        assert len(result) == 2  # 两种严重程度
        # 验证 high 严重程度的统计
        high_stat = next(s for s in result if s["severity"] == "high")
        assert high_stat["count"] == 2

    def test_aggregate_alarm_stats_empty_data(self):
        """测试空数据返回空列表"""
        from app.services.reports import aggregate_alarm_stats

        result = aggregate_alarm_stats([], group_by="type")
        assert result == []