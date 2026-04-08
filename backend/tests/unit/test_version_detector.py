"""
测试版本检测器
Phase 2 核心模块测试
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
import json


class TestVersionDetector:
    """测试版本检测器"""

    @pytest.fixture
    def mock_redis(self):
        """创建 Mock Redis 客户端"""
        redis = AsyncMock()
        return redis

    @pytest.fixture
    def detector(self, mock_redis):
        """创建版本检测器实例"""
        from app.services.version_detector import VersionDetector
        return VersionDetector(mock_redis)

    @pytest.mark.asyncio
    async def test_detect_v10_by_default(self, detector, mock_redis):
        """测试默认检测为 V10"""
        mock_redis.setex = AsyncMock()

        param_data = {
            "101": 1,
            "102": 28.0,
            "103": 25.0,
            "104": 15.0,  # V10: 冬天允许开机温度
        }

        version = await detector.detect_version("device_001", param_data)

        assert version == "V10"

    @pytest.mark.asyncio
    async def test_detect_v20_by_exclusive_params(self, detector, mock_redis):
        """测试通过独有参数检测 V20"""
        mock_redis.setex = AsyncMock()

        param_data = {
            "101": 1,
            "102": 28.0,
            "104": 21.0,  # V20: 夏天关机温度
            "108": 12,     # V20 独有: 冬天开始月份
            "109": 3,      # V20 独有: 冬天结束月份
            "110": 30,     # V20 独有: 空调关机间隔
        }

        version = await detector.detect_version("device_002", param_data)

        assert version == "V20"

    @pytest.mark.asyncio
    async def test_detect_v20_by_param_108(self, detector, mock_redis):
        """测试仅通过参数 108 检测 V20"""
        mock_redis.setex = AsyncMock()

        param_data = {
            "101": 1,
            "108": 12,  # V20 独有参数
        }

        version = await detector.detect_version("device_003", param_data)

        assert version == "V20"

    @pytest.mark.asyncio
    async def test_detect_version_from_ver_field_int(self, detector, mock_redis):
        """测试通过 Ver 字段检测版本（整数）"""
        mock_redis.setex = AsyncMock()

        param_data = {
            "101": 1,
            "Ver": 20,  # Ver 字段为整数
        }

        version = await detector.detect_version("device_004", param_data)

        assert version == "V20"

    @pytest.mark.asyncio
    async def test_detect_version_from_ver_field_string(self, detector, mock_redis):
        """测试通过 Ver 字段检测版本（字符串）"""
        mock_redis.setex = AsyncMock()

        param_data = {
            "101": 1,
            "Ver": "V10",  # Ver 字段为字符串
        }

        version = await detector.detect_version("device_005", param_data)

        assert version == "V10"

    @pytest.mark.asyncio
    async def test_cache_version(self, detector, mock_redis):
        """测试版本缓存"""
        mock_redis.setex = AsyncMock()

        await detector.cache_version("device_001", "V20", method="feature_params")

        mock_redis.setex.assert_called_once()
        args = mock_redis.setex.call_args
        assert "device_version:device_001" in args[0][0]
        assert args[0][1] == 7 * 24 * 60 * 60  # 7天

    @pytest.mark.asyncio
    async def test_get_version_from_cache(self, detector, mock_redis):
        """测试从缓存获取版本"""
        cached_data = json.dumps({
            "version": "V20",
            "detected_at": "2026-04-08T10:00:00",
            "method": "feature_params"
        })
        mock_redis.get = AsyncMock(return_value=cached_data)

        version = await detector.get_version("device_001")

        assert version == "V20"

    @pytest.mark.asyncio
    async def test_get_version_not_in_cache(self, detector, mock_redis):
        """测试缓存中不存在版本"""
        mock_redis.get = AsyncMock(return_value=None)

        version = await detector.get_version("device_unknown")

        assert version is None

    @pytest.mark.asyncio
    async def test_clear_version(self, detector, mock_redis):
        """测试清除版本缓存"""
        mock_redis.delete = AsyncMock()

        await detector.clear_version("device_001")

        mock_redis.delete.assert_called_once_with("device_version:device_001")


class TestV10V20ParamDifference:
    """测试 V10/V20 参数含义差异"""

    def test_param_104_different_meaning(self):
        """测试参数 104 在 V10/V20 中含义不同"""
        from app.services.protocol_parser import V10Parser, V20Parser

        v10_parser = V10Parser()
        v20_parser = V20Parser()

        v10_mapping = v10_parser.get_param_mapping()
        v20_mapping = v20_parser.get_param_mapping()

        # V10: 104 = 冬天空调允许开机温度
        assert v10_mapping["104"]["name"] == "冬天空调允许开机温度"

        # V20: 104 = 夏天空调关机温度
        assert v20_mapping["104"]["name"] == "夏天空调关机温度"

        # 参数名称不同
        assert v10_mapping["104"]["name"] != v20_mapping["104"]["name"]

    def test_v20_exclusive_params_not_in_v10(self):
        """测试 V20 独有参数不在 V10 中"""
        from app.services.protocol_parser import V10Parser, V20Parser

        v10_parser = V10Parser()
        v20_parser = V20Parser()

        v10_mapping = v10_parser.get_param_mapping()
        v20_mapping = v20_parser.get_param_mapping()

        # V20 独有参数
        assert "108" not in v10_mapping
        assert "109" not in v10_mapping
        assert "110" not in v10_mapping

        assert "108" in v20_mapping
        assert "109" in v20_mapping
        assert "110" in v20_mapping