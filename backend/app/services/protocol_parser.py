"""
协议解析器
使用策略模式解析不同版本的协议数据
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from loguru import logger


class ProtocolParser(ABC):
    """协议解析器基类"""

    version: str = "unknown"

    @abstractmethod
    def parse_parameter(self, param_data: Dict[str, Any]) -> Dict[str, Any]:
        """解析参数数据"""
        pass

    @abstractmethod
    def parse_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """解析实时数据"""
        pass

    def get_param_name(self, param_code: str) -> Optional[str]:
        """获取参数名称"""
        param_mapping = self.get_param_mapping()
        if param_code in param_mapping:
            return param_mapping[param_code].get("name")
        return None

    @abstractmethod
    def get_param_mapping(self) -> Dict[str, Dict[str, Any]]:
        """获取参数映射表"""
        pass


class V10Parser(ProtocolParser):
    """V10 协议解析器"""

    version = "V10"

    # V10 参数映射
    PARAM_MAPPING = {
        "101": {"name": "联动模式", "type": "int", "range": "0-1", "desc": "0手动，1自动"},
        "102": {"name": "夏天空调允许开机温度", "type": "float", "desc": "温度阈值"},
        "103": {"name": "夏天空调设置温度", "type": "float", "desc": "目标温度"},
        "104": {"name": "冬天空调允许开机温度", "type": "float", "desc": "温度阈值"},
        "105": {"name": "冬天空调设置温度", "type": "float", "desc": "目标温度"},
        "106": {"name": "是否启用设置温度", "type": "int", "range": "0-1"},
        "201": {"name": "上班时间段", "type": "string", "desc": "如 08:00~17:30"},
        "202": {"name": "加班时间段1", "type": "string"},
        "203": {"name": "加班时间段2", "type": "string"},
        "204": {"name": "加班时间段3", "type": "string"},
        "301": {"name": "空调代码", "type": "int"},
        "302": {"name": "空调模式", "type": "int", "range": "0-4", "desc": "0自动，1制冷，2除湿，3送风，4制热"},
        "303": {"name": "风速", "type": "int", "range": "0-3", "desc": "0自动，1小风，2中风，3大风"},
        "304": {"name": "风向", "type": "int", "range": "0-1", "desc": "0手动，1自动"},
        "305": {"name": "空调灯", "type": "int", "range": "0-1", "desc": "0关闭，1开启"},
        "306": {"name": "最小电流判断", "type": "int", "desc": "mA"},
        "401": {"name": "告警判断开关", "type": "int", "range": "0-1"},
        "402": {"name": "温度上限", "type": "int", "desc": "告警阈值"},
        "403": {"name": "温度下限", "type": "int", "desc": "告警阈值"},
        "404": {"name": "湿度上限", "type": "int", "desc": "告警阈值"},
        "405": {"name": "湿度下限", "type": "int", "desc": "告警阈值"},
        "501": {"name": "上送周期", "type": "int", "desc": "秒"},
    }

    def parse_parameter(self, param_data: Dict[str, Any]) -> Dict[str, Any]:
        """解析 V10 参数数据"""
        result = {
            "version": self.version,
            "params": {}
        }

        for code, value in param_data.items():
            code_str = str(code)
            if code_str in self.PARAM_MAPPING:
                param_info = self.PARAM_MAPPING[code_str].copy()
                param_info["value"] = value
                result["params"][code_str] = param_info
            elif code_str in ["Ver", "resettimes", "Sim"]:
                # 系统字段
                result[code_str] = value
            else:
                # 未知参数
                result["params"][code_str] = {"value": value, "name": "未知参数"}

        return result

    def parse_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """解析 V10 实时数据"""
        return {
            "version": self.version,
            "temp": data.get("temp"),
            "humi": data.get("humi"),
            "airstate": data.get("airstate"),
            "current": data.get("current"),
            "csq": data.get("csq"),
            "air_err": data.get("air_err"),
            "alarmtemp": data.get("alarmtemp"),
            "alarmhumi": data.get("alarmhumi"),
        }

    def get_param_mapping(self) -> Dict[str, Dict[str, Any]]:
        return self.PARAM_MAPPING


class V20Parser(ProtocolParser):
    """V20 协议解析器"""

    version = "V20"

    # V20 参数映射（注意 104 含义不同）
    PARAM_MAPPING = {
        "101": {"name": "联动模式", "type": "int", "range": "0-1", "desc": "0手动，1自动"},
        "102": {"name": "夏天空调允许开机温度", "type": "float"},
        "103": {"name": "夏天空调设置温度", "type": "float"},
        "104": {"name": "夏天空调关机温度", "type": "float", "desc": "V20新增"},
        "105": {"name": "冬天空调允许开机温度", "type": "float"},
        "106": {"name": "冬天空调设置温度", "type": "float"},
        "107": {"name": "冬天空调关机温度", "type": "float", "desc": "V20新增"},
        "108": {"name": "冬天开始月份", "type": "int", "desc": "V20独有"},
        "109": {"name": "冬天结束月份", "type": "int", "desc": "V20独有"},
        "110": {"name": "空调关机间隔", "type": "int", "desc": "V20独有，秒"},
        "201": {"name": "上班时间段", "type": "string"},
        "202": {"name": "加班时间段1", "type": "string"},
        "203": {"name": "加班时间段2", "type": "string"},
        "204": {"name": "加班时间段3", "type": "string"},
        "301": {"name": "空调代码", "type": "int"},
        "302": {"name": "空调模式", "type": "int", "range": "0-4"},
        "303": {"name": "风速", "type": "int", "range": "0-3"},
        "304": {"name": "风向", "type": "int", "range": "0-1"},
        "305": {"name": "空调灯", "type": "int", "range": "0-1"},
        "306": {"name": "最小电流判断", "type": "int"},
        "401": {"name": "告警判断开关", "type": "int", "range": "0-1"},
        "402": {"name": "温度上限", "type": "int"},
        "403": {"name": "温度下限", "type": "int"},
        "404": {"name": "湿度上限", "type": "int"},
        "405": {"name": "湿度下限", "type": "int"},
        "501": {"name": "上送周期", "type": "int"},
    }

    def parse_parameter(self, param_data: Dict[str, Any]) -> Dict[str, Any]:
        """解析 V20 参数数据"""
        result = {
            "version": self.version,
            "params": {}
        }

        for code, value in param_data.items():
            code_str = str(code)
            if code_str in self.PARAM_MAPPING:
                param_info = self.PARAM_MAPPING[code_str].copy()
                param_info["value"] = value
                result["params"][code_str] = param_info
            elif code_str in ["Ver", "resettimes", "Sim"]:
                result[code_str] = value
            else:
                result["params"][code_str] = {"value": value, "name": "未知参数"}

        return result

    def parse_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """解析 V20 实时数据"""
        # V20 数据格式与 V10 相同
        return {
            "version": self.version,
            "temp": data.get("temp"),
            "humi": data.get("humi"),
            "airstate": data.get("airstate"),
            "current": data.get("current"),
            "csq": data.get("csq"),
            "air_err": data.get("air_err"),
            "alarmtemp": data.get("alarmtemp"),
            "alarmhumi": data.get("alarmhumi"),
        }

    def get_param_mapping(self) -> Dict[str, Dict[str, Any]]:
        return self.PARAM_MAPPING


class ProtocolParserRegistry:
    """协议解析器注册表"""

    _parsers: Dict[str, ProtocolParser] = {}

    @classmethod
    def register(cls, parser: ProtocolParser) -> None:
        """注册解析器"""
        cls._parsers[parser.version] = parser
        logger.info(f"注册协议解析器: {parser.version}")

    @classmethod
    def get_parser(cls, version: str) -> ProtocolParser:
        """获取解析器"""
        parser = cls._parsers.get(version)
        if parser is None:
            logger.warning(f"未找到版本 {version} 的解析器，使用默认解析器")
            return cls._parsers.get("V10")  # 默认返回 V10 解析器
        return parser

    @classmethod
    def list_versions(cls) -> list:
        """列出所有支持的版本"""
        return list(cls._parsers.keys())


# 初始化默认解析器
ProtocolParserRegistry.register(V10Parser())
ProtocolParserRegistry.register(V20Parser())