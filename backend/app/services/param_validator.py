"""
参数验证器
验证设备参数设置的有效性，区分 V10 和 V20 版本
"""
from dataclasses import dataclass
from typing import Any

from app.services.protocol_parser import ProtocolParserRegistry


@dataclass
class ValidationResult:
    """验证结果"""
    valid: bool
    error: str | None = None


class ParamValidator:
    """参数验证器"""

    # 温度范围
    TEMP_MIN = -5.0
    TEMP_MAX = 45.0

    # 时间段正则格式
    TIME_PERIOD_PATTERN = r"^\d{2}:\d{2}~\d{2}:\d{2}$"

    def __init__(self, version: str = "V10"):
        """初始化验证器"""
        self.version = version
        self.parser = ProtocolParserRegistry.get_parser(version)

    def validate(self, param_code: str, param_value: Any) -> ValidationResult:
        """验证单个参数"""
        param_code_str = str(param_code)
        param_mapping = self.parser.get_param_mapping()

        # 检查参数是否存在于映射表
        if param_code_str not in param_mapping:
            # V20 独有参数在 V10 中不支持
            v20_exclusive = ["108", "109", "110"]
            if param_code_str in v20_exclusive and self.version == "V10":
                return ValidationResult(False, f"参数 {param_code} 是 V20 独有，V10 不支持")
            return ValidationResult(False, f"未知参数编号: {param_code}")

        param_info = param_mapping[param_code_str]
        param_type = param_info.get("type", "unknown")
        param_range = param_info.get("range", "")

        # 类型验证
        if param_type == "int":
            if not isinstance(param_value, (int, float)):
                return ValidationResult(False, f"参数 {param_code} 需要整数类型")
            if isinstance(param_value, float):
                param_value = int(param_value)
        elif param_type == "float":
            if not isinstance(param_value, (int, float)):
                return ValidationResult(False, f"参数 {param_code} 需要数值类型")
        elif param_type == "string":
            if not isinstance(param_value, str):
                return ValidationResult(False, f"参数 {param_code} 需要字符串类型")

        # 范围验证
        if param_range:
            try:
                range_parts = param_range.split("-")
                min_val = int(range_parts[0])
                max_val = int(range_parts[1])
                if isinstance(param_value, (int, float)):
                    if param_value < min_val or param_value > max_val:
                        return ValidationResult(False, f"参数 {param_code} 超出范围 {param_range}")
            except (ValueError, IndexError):
                pass

        # 特殊验证：温度参数
        temp_params = ["102", "103", "104", "105", "106", "107"]
        if param_code_str in temp_params:
            if isinstance(param_value, (int, float)):
                if param_value < self.TEMP_MIN or param_value > self.TEMP_MAX:
                    return ValidationResult(False, f"温度参数 {param_code} 超出合理范围 ({self.TEMP_MIN}~{self.TEMP_MAX})")

        # 特殊验证：月份参数
        month_params = ["108", "109"]
        if param_code_str in month_params:
            if isinstance(param_value, (int, float)):
                month = int(param_value)
                if month < 1 or month > 12:
                    return ValidationResult(False, f"月份参数 {param_code} 必须在 1-12 之间")

        # 特殊验证：时间段格式
        time_params = ["201", "202", "203", "204"]
        if param_code_str in time_params:
            if isinstance(param_value, str):
                import re
                if not re.match(self.TIME_PERIOD_PATTERN, param_value):
                    return ValidationResult(False, f"时间段格式错误，应为 HH:MM~HH:MM")
                # 验证时间值是否合理
                parts = param_value.split("~")
                for part in parts:
                    hour_min = part.split(":")
                    if len(hour_min) != 2:
                        return ValidationResult(False, f"时间段格式错误，应为 HH:MM~HH:MM")
                    try:
                        hour = int(hour_min[0])
                        minute = int(hour_min[1])
                        if hour < 0 or hour > 23:
                            return ValidationResult(False, f"小时值必须在 0-23 之间")
                        if minute < 0 or minute > 59:
                            return ValidationResult(False, f"分钟值必须在 0-59 之间")
                    except ValueError:
                        return ValidationResult(False, f"时间段格式错误，应为 HH:MM~HH:MM")

        # 特殊验证：上送周期（必须为正数）
        if param_code_str == "501":
            if isinstance(param_value, (int, float)):
                if param_value <= 0:
                    return ValidationResult(False, "上送周期必须大于 0")

        return ValidationResult(True)

    def validate_batch(self, params: dict[str, Any]) -> dict[str, ValidationResult]:
        """批量验证参数"""
        results = {}
        for param_code, param_value in params.items():
            results[param_code] = self.validate(param_code, param_value)
        return results

    def get_supported_params(self) -> list[str]:
        """获取支持的参数列表"""
        return list(self.parser.get_param_mapping().keys())

    def get_param_info(self, param_code: str) -> dict[str, Any] | None:
        """获取参数信息"""
        return self.parser.get_param_mapping().get(str(param_code))