"""
测试 Excel 导出增强功能
Phase 3.3 数据管理 - TDD 开发

TDD 流程：
1. RED: 编写失败测试
2. GREEN: 实现最小代码使测试通过
3. REFACTOR: 重构优化

测试策略：
- 测试Excel导出格式
- 测试多工作表导出
- 测试数据样式和格式化
- 测试大数据量导出
- 测试边界情况
"""
import pytest
from datetime import datetime, timedelta, UTC
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient, ASGITransport
import io


# ============ Excel导出服务测试 ============
class TestExcelExportService:
    """测试Excel导出服务"""

    def test_excel_export_service_exists(self):
        """测试Excel导出服务已定义"""
        try:
            from app.services.excel_export import ExcelExportService
            assert ExcelExportService is not None
        except ImportError:
            pytest.fail("ExcelExportService 服务未定义")

    def test_export_to_excel_returns_bytes(self):
        """测试导出返回字节数据"""
        from app.services.excel_export import ExcelExportService

        service = ExcelExportService()

        # 模拟数据
        data = [
            {"device_id": "test001", "name": "设备1", "value": 25.5},
            {"device_id": "test002", "name": "设备2", "value": 30.0},
        ]

        headers = ["设备ID", "名称", "数值"]

        result = service.export_data(data, headers)

        assert result is not None
        assert isinstance(result, bytes)

    def test_export_empty_data(self):
        """测试导出空数据"""
        from app.services.excel_export import ExcelExportService

        service = ExcelExportService()

        result = service.export_data([], ["列1", "列2"])

        # 空数据也应该能导出（只有标题行）
        assert result is not None
        assert isinstance(result, bytes)

    def test_export_with_header_style(self):
        """测试导出带表头样式"""
        from app.services.excel_export import ExcelExportService

        service = ExcelExportService()

        data = [{"col1": "val1"}]
        headers = ["列1"]

        result = service.export_data(data, headers, style_header=True)

        assert result is not None

    def test_export_multiple_sheets(self):
        """测试多工作表导出"""
        from app.services.excel_export import ExcelExportService

        service = ExcelExportService()

        sheets_data = [
            {"name": "Sheet1", "data": [{"a": 1}], "headers": ["A"]},
            {"name": "Sheet2", "data": [{"b": 2}], "headers": ["B"]},
        ]

        result = service.export_multi_sheet(sheets_data)

        assert result is not None
        assert isinstance(result, bytes)

    def test_export_with_datetime_format(self):
        """测试日期时间格式化"""
        from app.services.excel_export import ExcelExportService

        service = ExcelExportService()

        now = datetime.now(UTC)
        data = [{"time": now, "value": 10}]
        headers = ["时间", "数值"]

        result = service.export_data(data, headers)

        assert result is not None

    def test_export_with_number_format(self):
        """测试数值格式化"""
        from app.services.excel_export import ExcelExportService

        service = ExcelExportService()

        data = [
            {"energy": 123.456789, "power": 1000.5},
        ]
        headers = ["能耗(kWh)", "功率(W)"]

        result = service.export_data(data, headers, number_format="#,##0.00")

        assert result is not None


# ============ 报表Excel导出API测试 ============
class TestReportExcelExportAPI:
    """测试报表Excel导出API"""

    @pytest.mark.asyncio
    async def test_export_energy_excel_requires_auth(self):
        """测试能耗报表Excel导出需要认证"""
        from app.main import app

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/api/reports/export", params={
                "report_type": "energy",
                "start_time": datetime.now(UTC).isoformat(),
                "end_time": datetime.now(UTC).isoformat(),
                "format": "excel"
            })
            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_export_energy_excel_format(self):
        """测试能耗报表Excel导出格式"""
        from app.main import app
        from app.core.database import get_db
        from app.services.auth import get_current_user

        mock_user = MagicMock()
        mock_user.tenant_id = 1
        mock_user.role = "admin"

        # 创建带有实际值的mock设备
        mock_device = MagicMock()
        mock_device.device_id = "test001"
        mock_device.name = "测试设备"
        mock_device.zone_id = None

        # Mock 数据库查询
        mock_db = AsyncMock()

        mock_device_result = MagicMock()
        mock_device_result.scalars.return_value.all.return_value = [mock_device]

        mock_data_result = MagicMock()
        mock_data_result.scalars.return_value.all.return_value = []

        # 先返回设备查询，然后返回数据查询
        mock_db.execute.side_effect = [mock_device_result, mock_data_result, mock_data_result]

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
                response = await client.get("/api/reports/export", params={
                    "report_type": "energy",
                    "start_time": (now - timedelta(days=1)).isoformat(),
                    "end_time": now.isoformat(),
                    "format": "excel"
                })
                # 应该返回 200 或 201
                assert response.status_code in [200, 201]
                # 检查返回 Excel 文件
                content_type = response.headers.get("content-type")
                # Excel 的 MIME 类型
                assert content_type and (
                    content_type.startswith("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet") or
                    content_type.startswith("application/octet-stream")
                )
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_export_alarm_excel_format(self):
        """测试告警报表Excel导出格式"""
        from app.main import app
        from app.core.database import get_db
        from app.services.auth import get_current_user

        mock_user = MagicMock()
        mock_user.tenant_id = 1
        mock_user.role = "admin"

        mock_alarm = MagicMock()
        mock_alarm.type = "offline"
        mock_alarm.severity = "high"
        mock_alarm.device_id = "test001"

        mock_db = AsyncMock()

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_alarm]
        mock_db.execute.return_value = mock_result

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
                response = await client.get("/api/reports/export", params={
                    "report_type": "alarm",
                    "start_time": (now - timedelta(days=7)).isoformat(),
                    "end_time": now.isoformat(),
                    "format": "excel"
                })
                assert response.status_code in [200, 201]
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_export_runtime_excel_format(self):
        """测试运行时长报表Excel导出格式"""
        from app.main import app
        from app.core.database import get_db
        from app.services.auth import get_current_user

        mock_user = MagicMock()
        mock_user.tenant_id = 1
        mock_user.role = "admin"

        mock_device = MagicMock()
        mock_device.device_id = "test001"
        mock_device.name = "测试设备"
        mock_device.zone_id = None

        mock_db = AsyncMock()

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_device]
        mock_db.execute.return_value = mock_result

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
                response = await client.get("/api/reports/export", params={
                    "report_type": "runtime",
                    "start_time": (now - timedelta(days=30)).isoformat(),
                    "end_time": now.isoformat(),
                    "format": "excel"
                })
                assert response.status_code in [200, 201]
        finally:
            app.dependency_overrides.clear()


# ============ 边界情况测试 ============
class TestExcelExportEdgeCases:
    """测试Excel导出边界情况"""

    def test_export_large_dataset(self):
        """测试大数据量导出"""
        from app.services.excel_export import ExcelExportService

        service = ExcelExportService()

        # 模拟大量数据
        large_data = [{"id": i, "value": i * 1.5} for i in range(1000)]
        headers = ["ID", "数值"]

        result = service.export_data(large_data, headers)

        assert result is not None
        # 大数据导出应该成功

    def test_export_unicode_characters(self):
        """测试Unicode字符导出"""
        from app.services.excel_export import ExcelExportService

        service = ExcelExportService()

        data = [
            {"name": "测试设备", "location": "北京市"},
            {"name": "空调-1号", "location": "上海浦东"},
        ]
        headers = ["名称", "位置"]

        result = service.export_data(data, headers)

        assert result is not None
        # Unicode字符应该正确处理

    def test_export_special_characters(self):
        """测试特殊字符导出"""
        from app.services.excel_export import ExcelExportService

        service = ExcelExportService()

        data = [
            {"text": "包含,逗号", "formula": "=SUM(A1:A10)"},
            {"text": "包含\"引号", "formula": "=1+2"},
        ]
        headers = ["文本", "公式"]

        result = service.export_data(data, headers)

        assert result is not None

    def test_export_null_values(self):
        """测试空值导出"""
        from app.services.excel_export import ExcelExportService

        service = ExcelExportService()

        data = [
            {"col1": "value", "col2": None},
            {"col1": None, "col2": "value2"},
        ]
        headers = ["列1", "列2"]

        result = service.export_data(data, headers)

        assert result is not None

    def test_export_mixed_types(self):
        """测试混合类型数据导出"""
        from app.services.excel_export import ExcelExportService

        service = ExcelExportService()

        now = datetime.now(UTC)
        data = [
            {"str": "文本", "num": 123.45, "bool": True, "time": now},
            {"str": "文本2", "num": 200, "bool": False, "time": now},
        ]
        headers = ["字符串", "数值", "布尔", "时间"]

        result = service.export_data(data, headers)

        assert result is not None

    @pytest.mark.asyncio
    async def test_export_unsupported_format(self):
        """测试不支持的导出格式"""
        from app.main import app
        from app.core.database import get_db
        from app.services.auth import get_current_user

        mock_user = MagicMock()
        mock_user.tenant_id = 1
        mock_user.role = "admin"

        mock_db = AsyncMock()

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
                response = await client.get("/api/reports/export", params={
                    "report_type": "energy",
                    "start_time": (now - timedelta(days=1)).isoformat(),
                    "end_time": now.isoformat(),
                    "format": "pdf"  # 不支持的格式
                })
                # 应该返回 400 错误
                assert response.status_code == 400
        finally:
            app.dependency_overrides.clear()


# ============ Excel文件格式验证测试 ============
class TestExcelFileFormat:
    """测试Excel文件格式"""

    def test_excel_filename_format(self):
        """测试Excel文件名格式"""
        from app.services.excel_export import ExcelExportService

        service = ExcelExportService()

        filename = service.generate_filename("energy")

        assert ".xlsx" in filename
        assert "energy" in filename

    def test_excel_mime_type(self):
        """测试Excel MIME类型"""
        from app.services.excel_export import ExcelExportService

        service = ExcelExportService()

        mime_type = service.get_mime_type()

        assert mime_type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    def test_excel_file_extension(self):
        """测试Excel文件扩展名"""
        from app.services.excel_export import ExcelExportService

        service = ExcelExportService()

        extension = service.get_file_extension()

        assert extension == ".xlsx"