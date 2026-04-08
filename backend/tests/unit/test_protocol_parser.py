"""
测试协议解析器
Phase 2 核心模块测试
"""
import pytest


class TestProtocolParserRegistry:
    """测试协议解析器注册表"""

    def test_registry_has_v10_parser(self):
        """测试注册表包含 V10 解析器"""
        from app.services.protocol_parser import ProtocolParserRegistry

        assert "V10" in ProtocolParserRegistry.list_versions()

    def test_registry_has_v20_parser(self):
        """测试注册表包含 V20 解析器"""
        from app.services.protocol_parser import ProtocolParserRegistry

        assert "V20" in ProtocolParserRegistry.list_versions()

    def test_get_v10_parser(self):
        """测试获取 V10 解析器"""
        from app.services.protocol_parser import ProtocolParserRegistry

        parser = ProtocolParserRegistry.get_parser("V10")

        assert parser.version == "V10"

    def test_get_v20_parser(self):
        """测试获取 V20 解析器"""
        from app.services.protocol_parser import ProtocolParserRegistry

        parser = ProtocolParserRegistry.get_parser("V20")

        assert parser.version == "V20"

    def test_get_unknown_parser_returns_v10(self):
        """测试获取未知版本解析器返回 V10"""
        from app.services.protocol_parser import ProtocolParserRegistry

        parser = ProtocolParserRegistry.get_parser("V99")

        assert parser.version == "V10"  # 默认返回 V10


class TestV10Parser:
    """测试 V10 协议解析器"""

    @pytest.fixture
    def parser(self):
        from app.services.protocol_parser import V10Parser
        return V10Parser()

    def test_parse_parameter_basic(self, parser):
        """测试解析基本参数"""
        param_data = {
            "101": 1,
            "102": 28.0,
            "103": 25.0,
        }

        result = parser.parse_parameter(param_data)

        assert result["version"] == "V10"
        assert "101" in result["params"]
        assert result["params"]["101"]["value"] == 1
        assert result["params"]["101"]["name"] == "联动模式"

    def test_parse_parameter_with_system_fields(self, parser):
        """测试解析包含系统字段的参数"""
        param_data = {
            "101": 1,
            "Ver": 10,
            "resettimes": 2,
            "Sim": "898600B11823FA130187"
        }

        result = parser.parse_parameter(param_data)

        assert result["Ver"] == 10
        assert result["resettimes"] == 2
        assert result["Sim"] == "898600B11823FA130187"

    def test_parse_data(self, parser):
        """测试解析实时数据"""
        data = {
            "temp": 28.5,
            "humi": 33.4,
            "airstate": 1,
            "current": 568,
            "csq": 60.5,
        }

        result = parser.parse_data(data)

        assert result["version"] == "V10"
        assert result["temp"] == 28.5
        assert result["humi"] == 33.4
        assert result["airstate"] == 1

    def test_get_param_name(self, parser):
        """测试获取参数名称"""
        assert parser.get_param_name("101") == "联动模式"
        assert parser.get_param_name("102") == "夏天空调允许开机温度"
        assert parser.get_param_name("201") == "上班时间段"

    def test_param_mapping_completeness(self, parser):
        """测试参数映射完整性"""
        mapping = parser.get_param_mapping()

        # V10 应包含 101-106, 201-204, 301-306, 401-405, 501
        expected_params = [
            "101", "102", "103", "104", "105", "106",
            "201", "202", "203", "204",
            "301", "302", "303", "304", "305", "306",
            "401", "402", "403", "404", "405",
            "501"
        ]

        for param in expected_params:
            assert param in mapping, f"缺少参数 {param}"


class TestV20Parser:
    """测试 V20 协议解析器"""

    @pytest.fixture
    def parser(self):
        from app.services.protocol_parser import V20Parser
        return V20Parser()

    def test_parse_parameter_basic(self, parser):
        """测试解析基本参数"""
        param_data = {
            "101": 1,
            "102": 28.0,
            "104": 21.0,  # V20: 夏天关机温度
            "108": 12,    # V20 独有
        }

        result = parser.parse_parameter(param_data)

        assert result["version"] == "V20"
        assert "108" in result["params"]
        assert result["params"]["108"]["value"] == 12
        assert result["params"]["108"]["name"] == "冬天开始月份"

    def test_parse_parameter_with_all_exclusive_params(self, parser):
        """测试解析包含所有独有参数的数据"""
        param_data = {
            "108": 12,
            "109": 3,
            "110": 30,
        }

        result = parser.parse_parameter(param_data)

        assert result["params"]["108"]["name"] == "冬天开始月份"
        assert result["params"]["109"]["name"] == "冬天结束月份"
        assert result["params"]["110"]["name"] == "空调关机间隔"

    def test_parse_data_same_format_as_v10(self, parser):
        """测试 V20 数据格式与 V10 相同"""
        data = {
            "temp": 25.0,
            "humi": 45.0,
            "airstate": 0,
        }

        result = parser.parse_data(data)

        assert result["version"] == "V20"
        assert result["temp"] == 25.0
        assert result["humi"] == 45.0

    def test_param_104_meaning_in_v20(self, parser):
        """测试 V20 中参数 104 的含义"""
        mapping = parser.get_param_mapping()

        # V20: 104 = 夏天空调关机温度
        assert mapping["104"]["name"] == "夏天空调关机温度"

    def test_param_107_exists_in_v20(self, parser):
        """测试 V20 包含参数 107"""
        mapping = parser.get_param_mapping()

        assert "107" in mapping
        assert mapping["107"]["name"] == "冬天空调关机温度"


class TestParserComparison:
    """测试 V10/V20 解析器对比"""

    def test_same_param_different_meaning(self):
        """测试相同参数编号不同含义"""
        from app.services.protocol_parser import V10Parser, V20Parser

        v10 = V10Parser()
        v20 = V20Parser()

        # 参数 104 在两个版本中含义不同
        v10_104 = v10.get_param_name("104")
        v20_104 = v20.get_param_name("104")

        assert v10_104 != v20_104

    def test_v20_has_more_params(self):
        """测试 V20 比 V10 有更多参数"""
        from app.services.protocol_parser import V10Parser, V20Parser

        v10 = V10Parser()
        v20 = V20Parser()

        v10_params = v10.get_param_mapping()
        v20_params = v20.get_param_mapping()

        # V20 应该包含 V10 所有参数 + 新参数
        v20_exclusive = ["107", "108", "109", "110"]
        for param in v20_exclusive:
            assert param not in v10_params
            assert param in v20_params