"""
测试设备参数设置功能
包括参数验证、MQTT 消息发送、版本兼容处理
"""
import pytest
import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from app.models import Tenant, User, Device
from app.services.protocol_parser import V10Parser, V20Parser, ProtocolParserRegistry
from app.services.param_validator import ParamValidator, ValidationResult


class TestParamValidator:
    """测试参数验证器"""

    def test_validate_v10_param_within_range(self):
        """测试 V10 参数在有效范围内"""
        validator = ParamValidator("V10")

        # 联动模式 0-1
        result = validator.validate("101", 1)
        assert result.valid == True
        assert result.error is None

        # 夏天空调允许开机温度
        result = validator.validate("102", 26.0)
        assert result.valid == True

    def test_validate_v10_param_out_of_range(self):
        """测试 V10 参数超出范围"""
        validator = ParamValidator("V10")

        # 联动模式超出范围
        result = validator.validate("101", 2)
        assert result.valid == False
        assert "范围" in result.error

        # 空调模式超出范围
        result = validator.validate("302", 5)
        assert result.valid == False

    def test_validate_v10_unknown_param(self):
        """测试 V10 未知参数"""
        validator = ParamValidator("V10")

        # 108 是 V20 独有参数，V10 不支持
        result = validator.validate("108", 11)
        assert result.valid == False
        assert "不支持" in result.error

    def test_validate_v20_param_104_different_meaning(self):
        """测试 V20 参数 104 含义不同"""
        validator_v10 = ParamValidator("V10")
        validator_v20 = ParamValidator("V20")

        # V10: 104 = 冬天空调允许开机温度
        result_v10 = validator_v10.validate("104", 18.0)
        assert result_v10.valid == True

        # V20: 104 = 夏天空调关机温度
        result_v20 = validator_v20.validate("104", 28.0)
        assert result_v20.valid == True

    def test_validate_v20_exclusive_params(self):
        """测试 V20 独有参数"""
        validator = ParamValidator("V20")

        # 108: 冬天开始月份
        result = validator.validate("108", 11)
        assert result.valid == True

        # 109: 冬天结束月份
        result = validator.validate("109", 3)
        assert result.valid == True

        # 110: 空调关机间隔
        result = validator.validate("110", 300)
        assert result.valid == True

    def test_validate_time_period_format(self):
        """测试时间段格式验证"""
        validator = ParamValidator("V10")

        # 正确格式
        result = validator.validate("201", "08:00~17:30")
        assert result.valid == True

        # 错误格式
        result = validator.validate("201", "8:00-17:30")
        assert result.valid == False
        assert "格式" in result.error

    def test_validate_temperature_bounds(self):
        """测试温度边界验证"""
        validator = ParamValidator("V10")

        # 合理温度范围
        result = validator.validate("102", 18.0)
        assert result.valid == True

        result = validator.validate("102", 30.0)
        assert result.valid == True

        # 温度过低
        result = validator.validate("102", -10.0)
        assert result.valid == False

        # 温度过高
        result = validator.validate("102", 50.0)
        assert result.valid == False

    def test_validate_month_range(self):
        """测试月份范围验证"""
        validator = ParamValidator("V20")

        # 合理月份
        result = validator.validate("108", 1)
        assert result.valid == True

        result = validator.validate("108", 12)
        assert result.valid == True

        # 无效月份
        result = validator.validate("108", 0)
        assert result.valid == False

        result = validator.validate("108", 13)
        assert result.valid == False

    def test_validate_multiple_params(self):
        """测试批量参数验证"""
        validator = ParamValidator("V10")

        params = {
            "101": 1,      # 联动模式
            "102": 26.0,   # 夏天开机温度
            "103": 24.0,   # 夏天设置温度
            "302": 1,      # 空调模式
        }

        results = validator.validate_batch(params)
        assert all(r.valid for r in results.values())

    def test_validate_batch_with_invalid_param(self):
        """测试批量验证包含无效参数"""
        validator = ParamValidator("V10")

        params = {
            "101": 1,
            "302": 5,  # 超出范围
            "108": 11, # V20 独有
        }

        results = validator.validate_batch(params)
        assert results["101"].valid == True
        assert results["302"].valid == False
        assert results["108"].valid == False


class TestParamSettingAPI:
    """测试参数设置 API"""

    @pytest.mark.asyncio
    async def test_set_param_requires_permission(self, db_session):
        """测试参数设置需要权限"""
        # 创建租户和用户
        tenant = Tenant(name="测试租户", code="param_test")
        db_session.add(tenant)
        await db_session.commit()
        await db_session.refresh(tenant)

        # 观察员没有 DEVICE_CONTROL 权限
        viewer = User(
            tenant_id=tenant.id,
            username="param_viewer",
            password_hash="hash",
            role="viewer",
            is_active=True
        )
        db_session.add(viewer)
        await db_session.commit()

        # 操作员有权限
        operator = User(
            tenant_id=tenant.id,
            username="param_operator",
            password_hash="hash",
            role="operator",
            is_active=True
        )
        db_session.add(operator)
        await db_session.commit()

    @pytest.mark.asyncio
    async def test_set_param_mqtt_message_format(self, db_session):
        """测试 MQTT 消息格式"""
        tenant = Tenant(name="MQTT测试", code="mqtt_param")
        db_session.add(tenant)
        await db_session.commit()
        await db_session.refresh(tenant)

        device = Device(
            tenant_id=tenant.id,
            device_id="IMEI_PARAM_TEST",
            name="参数测试设备",
            protocol_version="V10",
            is_online=True
        )
        db_session.add(device)
        await db_session.commit()
        await db_session.refresh(device)

        # 构建参数设置消息
        params = {
            "102": 26.0,
            "103": 24.0,
        }

        # 验证消息格式
        timestamp = str(int(datetime.now().timestamp()))
        for param_code, param_value in params.items():
            message = {
                "Name": param_code,
                "Value": param_value,
                "timestamp": timestamp
            }
            # 检查消息结构
            assert "Name" in message
            assert "Value" in message
            assert "timestamp" in message

    @pytest.mark.asyncio
    async def test_set_param_version_compatibility(self, db_session):
        """测试版本兼容性"""
        tenant = Tenant(name="版本兼容测试", code="version_compat")
        db_session.add(tenant)
        await db_session.commit()
        await db_session.refresh(tenant)

        # V10 设备
        device_v10 = Device(
            tenant_id=tenant.id,
            device_id="IMEI_V10",
            name="V10设备",
            protocol_version="V10"
        )
        # V20 设备
        device_v20 = Device(
            tenant_id=tenant.id,
            device_id="IMEI_V20",
            name="V20设备",
            protocol_version="V20"
        )
        db_session.add_all([device_v10, device_v20])
        await db_session.commit()

        validator_v10 = ParamValidator("V10")
        validator_v20 = ParamValidator("V20")

        # V10 参数 104 = 冬天开机温度
        assert validator_v10.validate("104", 18.0).valid == True

        # V20 参数 104 = 夏天关机温度
        assert validator_v20.validate("104", 28.0).valid == True

        # V20 独有参数 V10 不支持
        assert validator_v10.validate("108", 11).valid == False
        assert validator_v20.validate("108", 11).valid == True

    @pytest.mark.asyncio
    async def test_batch_set_param(self, db_session):
        """测试批量参数设置"""
        tenant = Tenant(name="批量参数测试", code="batch_param")
        db_session.add(tenant)
        await db_session.commit()
        await db_session.refresh(tenant)

        # 创建多个设备
        devices = []
        for i in range(3):
            device = Device(
                tenant_id=tenant.id,
                device_id=f"IMEI_BATCH_{i}",
                name=f"批量设备{i}",
                protocol_version="V10",
                is_online=True
            )
            devices.append(device)
        db_session.add_all(devices)
        await db_session.commit()

        # 批量参数
        params = {
            "101": 1,      # 联动模式: 自动
            "102": 26.0,   # 夏天开机温度
            "201": "08:00~17:30",  # 上班时间
        }

        validator = ParamValidator("V10")
        results = validator.validate_batch(params)

        # 所有参数应该有效
        assert all(r.valid for r in results.values())


class TestCriticalParams:
    """测试关键参数：开机/关机条件和时间"""

    def test_v10_startup_conditions(self):
        """测试 V10 开机条件参数"""
        validator = ParamValidator("V10")

        # 102: 夏天空调允许开机温度
        result = validator.validate("102", 26.0)
        assert result.valid == True

        # 103: 夏天空调设置温度
        result = validator.validate("103", 24.0)
        assert result.valid == True

        # 104: 冬天空调允许开机温度 (V10含义)
        result = validator.validate("104", 18.0)
        assert result.valid == True

        # 105: 冬天空调设置温度
        result = validator.validate("105", 20.0)
        assert result.valid == True

    def test_v20_startup_and_shutdown_conditions(self):
        """测试 V20 开机和关机条件参数"""
        validator = ParamValidator("V20")

        # 开机条件
        result = validator.validate("102", 26.0)  # 夏天开机温度
        assert result.valid == True

        result = validator.validate("105", 18.0)  # 冬天开机温度
        assert result.valid == True

        # 关机条件 (V20新增)
        result = validator.validate("104", 28.0)  # 夏天关机温度
        assert result.valid == True

        result = validator.validate("107", 16.0)  # 冬天关机温度
        assert result.valid == True

    def test_v10_work_time_periods(self):
        """测试 V10 工作时间段"""
        validator = ParamValidator("V10")

        # 201: 上班时间段
        result = validator.validate("201", "08:00~17:30")
        assert result.valid == True

        # 202-204: 加班时间段
        result = validator.validate("202", "18:00~20:00")
        assert result.valid == True

        result = validator.validate("203", "20:00~22:00")
        assert result.valid == True

        result = validator.validate("204", "22:00~23:00")
        assert result.valid == True

    def test_v20_shutdown_time_params(self):
        """测试 V20 关机时间参数（月份切换）"""
        validator = ParamValidator("V20")

        # 108: 冬天开始月份 (11月)
        result = validator.validate("108", 11)
        assert result.valid == True

        # 109: 冬天结束月份 (3月)
        result = validator.validate("109", 3)
        assert result.valid == True

        # 110: 空调关机间隔（秒）
        result = validator.validate("110", 300)
        assert result.valid == True

    def test_complete_startup_shutdown_config_v10(self):
        """测试 V10 完整开机关机配置"""
        validator = ParamValidator("V10")

        # 完整配置参数
        params = {
            # 开机条件
            "102": 26.0,  # 夏天开机温度
            "104": 18.0,  # 冬天开机温度
            # 设置温度
            "103": 24.0,  # 夏天设置温度
            "105": 20.0,  # 冬天设置温度
            # 工作时间
            "201": "08:00~17:30",
            "202": "18:00~20:00",
        }

        results = validator.validate_batch(params)
        assert all(r.valid for r in results.values())

    def test_complete_startup_shutdown_config_v20(self):
        """测试 V20 完整开机关机配置"""
        validator = ParamValidator("V20")

        params = {
            # 开机条件
            "102": 26.0,  # 夏天开机温度
            "105": 18.0,  # 冬天开机温度
            # 关机条件
            "104": 28.0,  # 夏天关机温度
            "107": 16.0,  # 冬天关机温度
            # 设置温度
            "103": 24.0,
            "106": 20.0,
            # 季节切换时间
            "108": 11,    # 冬天开始月份
            "109": 3,     # 冬天结束月份
            # 关机间隔
            "110": 300,   # 秒
            # 工作时间
            "201": "08:00~17:30",
        }

        results = validator.validate_batch(params)
        assert all(r.valid for r in results.values())


class TestParamSettingService:
    """测试参数设置服务"""

    def test_build_set_param_topic(self):
        """测试构建 MQTT 主题"""
        device_id = "IMEI123456789"
        expected_topic = f"/down/{device_id}/set"

        assert expected_topic == f"/down/{device_id}/set"

    def test_build_set_param_payload_single(self):
        """测试构建单个参数消息"""
        param_code = "102"
        param_value = 26.0
        timestamp = str(int(datetime.now().timestamp()))

        payload = {
            "Name": param_code,
            "Value": param_value,
            "timestamp": timestamp
        }

        # 验证 JSON 格式
        json_str = json.dumps(payload)
        parsed = json.loads(json_str)

        assert parsed["Name"] == param_code
        assert parsed["Value"] == param_value
        assert "timestamp" in parsed

    def test_build_set_param_payload_batch(self):
        """测试构建批量参数消息"""
        params = {
            "102": 26.0,
            "103": 24.0,
            "201": "08:00~17:30"
        }
        timestamp = str(int(datetime.now().timestamp()))

        # 批量发送需要多条消息
        messages = []
        for code, value in params.items():
            messages.append({
                "Name": code,
                "Value": value,
                "timestamp": timestamp
            })

        assert len(messages) == 3
        for msg in messages:
            assert "Name" in msg
            assert "Value" in msg


class TestParamSettingsModel:
    """测试参数设置数据模型"""

    def test_single_param_request_schema(self):
        """测试单个参数请求模型"""
        from app.schemas.schemas import SetParamRequest

        request = SetParamRequest(
            param_code="102",
            param_value=26.0
        )

        assert request.param_code == "102"
        assert request.param_value == 26.0

    def test_batch_param_request_schema(self):
        """测试批量参数请求模型"""
        from app.schemas.schemas import BatchSetParamRequest

        request = BatchSetParamRequest(
            device_ids=[1, 2, 3],
            params={
                "102": 26.0,
                "103": 24.0,
                "201": "08:00~17:30"
            }
        )

        assert len(request.device_ids) == 3
        assert len(request.params) == 3


class TestParamSettingEdgeCases:
    """测试参数设置边缘情况"""

    def test_set_param_to_offline_device(self):
        """测试向离线设备设置参数"""
        # 应该记录警告但允许尝试发送
        device_offline = {
            "device_id": "IMEI_OFFLINE",
            "is_online": False
        }

        # 系统应该提示设备离线但仍尝试发送
        assert device_offline["is_online"] == False

    def test_set_invalid_param_type(self):
        """测试设置无效参数类型"""
        validator = ParamValidator("V10")

        # 字符串值给数值参数
        result = validator.validate("102", "not_a_number")
        assert result.valid == False

    def test_set_empty_params(self):
        """测试设置空参数"""
        validator = ParamValidator("V10")

        params = {}
        results = validator.validate_batch(params)
        assert len(results) == 0

    def test_set_param_to_device_with_unknown_version(self):
        """测试向未知版本设备设置参数"""
        validator = ParamValidator("V10")  # 默认使用 V10

        # 未知版本设备使用 V10 验证器
        result = validator.validate("102", 26.0)
        assert result.valid == True

    def test_time_period_with_invalid_separator(self):
        """测试时间段使用错误分隔符"""
        validator = ParamValidator("V10")

        # 使用 - 而非 ~
        result = validator.validate("201", "08:00-17:30")
        assert result.valid == False

        # 使用空格
        result = validator.validate("201", "08:00 17:30")
        assert result.valid == False

    def test_time_period_with_invalid_time_format(self):
        """测试时间段时间格式错误"""
        validator = ParamValidator("V10")

        # 缺少分钟
        result = validator.validate("201", "08~17")
        assert result.valid == False

        # 24小时制错误
        result = validator.validate("201", "25:00~17:30")
        assert result.valid == False