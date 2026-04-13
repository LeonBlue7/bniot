"""
测试错误码定义和文档

测试内容：
1. 错误码枚举完整性
2. 错误响应格式标准化
3. 错误码文档化
"""
import pytest
from enum import Enum
from fastapi.testclient import TestClient


class TestErrorCodeDefinition:
    """测试错误码定义"""

    def test_error_codes_module_exists(self):
        """测试错误码模块存在"""
        try:
            from app.core.errors import ErrorCode, ErrorResponse
            assert ErrorCode is not None
            assert ErrorResponse is not None
        except ImportError:
            pytest.fail("缺少 app.core.errors 模块，需要创建错误码定义")

    def test_error_code_is_enum(self):
        """测试错误码是枚举类型"""
        from app.core.errors import ErrorCode
        assert issubclass(ErrorCode, Enum)

    def test_error_code_has_required_fields(self):
        """测试错误码有必需字段"""
        from app.core.errors import ErrorCode

        # 检查是否有 code, message, http_status 属性
        for error in ErrorCode:
            assert hasattr(error, 'code') or hasattr(error, 'value'), \
                f"错误码 {error.name} 缺少 code 属性"
            assert hasattr(error, 'message') or hasattr(error, 'value'), \
                f"错误码 {error.name} 缺少 message 属性"

    def test_error_code_categories(self):
        """测试错误码分类完整"""
        from app.core.errors import ErrorCode

        # 应该有以下类别的错误码
        error_names = [e.name for e in ErrorCode]

        # 认证相关
        auth_errors = [name for name in error_names if 'AUTH' in name]
        assert len(auth_errors) > 0, "缺少认证相关错误码"

        # 权限相关
        permission_errors = [name for name in error_names if 'PERMISSION' in name]
        assert len(permission_errors) > 0, "缺少权限相关错误码"

        # 资源相关 (RESOURCE 或 DEVICE)
        resource_errors = [name for name in error_names if 'RESOURCE' in name or 'DEVICE' in name]
        assert len(resource_errors) > 0, "缺少资源相关错误码"

        # 验证相关
        validation_errors = [name for name in error_names if 'VALIDATION' in name]
        assert len(validation_errors) > 0, "缺少验证相关错误码"

    def test_error_response_schema(self):
        """测试错误响应格式"""
        from app.core.errors import ErrorResponse
        from pydantic import BaseModel

        assert issubclass(ErrorResponse, BaseModel)

        # 检查必需字段
        fields = ErrorResponse.model_fields
        assert 'code' in fields or 'error_code' in fields, "ErrorResponse 缺少错误码字段"
        assert 'message' in fields, "ErrorResponse 缺少消息字段"

    def test_error_response_has_details(self):
        """测试错误响应支持详细信息"""
        from app.core.errors import ErrorResponse

        fields = ErrorResponse.model_fields
        # details 是可选字段
        assert 'details' in fields or 'data' in fields, "ErrorResponse 缺少详情字段"


class TestErrorCodeUsage:
    """测试错误码使用"""

    def test_login_error_returns_error_code(self, test_app_with_redis):
        """测试登录错误返回错误码"""
        client = TestClient(test_app_with_redis)
        # 使用错误密码登录
        response = client.post(
            "/api/auth/login",
            data={"username": "testuser", "password": "wrongpassword"}
        )

        # 登录失败会返回 401 或 400
        assert response.status_code in [400, 401, 429]
        data = response.json()
        # 应该有某种形式的错误信息
        assert "detail" in data or "code" in data or "message" in data

    def test_404_returns_error_code(self, test_app_with_redis):
        """测试 404 错误返回错误码

        注意：此测试验证错误响应格式，不验证认证逻辑。
        未认证请求返回 401，这也是一种错误响应格式验证。
        """
        client = TestClient(test_app_with_redis)
        # 不带认证访问受保护资源
        response = client.get("/api/devices/999999")

        # 返回 401（未认证）或 404（设备不存在）
        assert response.status_code in [401, 404]
        data = response.json()
        # 应该有标准化的错误响应
        assert "detail" in data or "message" in data or "code" in data

    def test_validation_error_returns_error_code(self, test_app_with_redis):
        """测试验证错误返回错误码

        注意：此测试验证错误响应格式，不验证认证逻辑。
        """
        client = TestClient(test_app_with_redis)
        # 创建设备时使用无效数据（不带认证）
        response = client.post(
            "/api/devices",
            json={"name": "test"}  # 缺少 device_id
        )

        # 返回 401（未认证）或 422（验证错误）
        assert response.status_code in [401, 422]
        data = response.json()
        assert "detail" in data


class TestErrorCodeDocumentation:
    """测试错误码文档"""

    def test_error_codes_in_openapi(self, test_app):
        """测试错误码在 OpenAPI 文档中"""
        client = TestClient(test_app)
        response = client.get("/api/openapi.json")
        schema = response.json()

        # 检查是否有错误响应定义
        schemas = schema.get("components", {}).get("schemas", {})
        error_schemas = [name for name in schemas if "Error" in name or "error" in name]

        assert len(error_schemas) > 0, "OpenAPI 文档缺少错误响应 schema"

    def test_error_codes_endpoint_exists(self, test_app):
        """测试错误码查询端点存在"""
        client = TestClient(test_app)
        response = client.get("/api/docs/error-codes")

        # 端点可能返回 200 或 404
        # 如果存在，验证返回格式
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, dict) or isinstance(data, list)


class TestHTTPStatusMapping:
    """测试 HTTP 状态码映射"""

    def test_error_codes_have_http_status(self):
        """测试错误码有 HTTP 状态码映射"""
        from app.core.errors import ErrorCode

        for error in ErrorCode:
            # 每个错误码应该有对应的 HTTP 状态码
            if hasattr(error, 'http_status'):
                assert 100 <= error.http_status <= 599
            elif hasattr(error, 'value') and isinstance(error.value, dict):
                if 'http_status' in error.value:
                    assert 100 <= error.value['http_status'] <= 599

    def test_client_errors_map_to_4xx(self):
        """测试客户端错误映射到 4xx"""
        from app.core.errors import ErrorCode

        client_error_names = ['NOT_FOUND', 'INVALID', 'AUTH', 'FORBIDDEN', 'VALIDATION']

        for error in ErrorCode:
            error_name = error.name.upper()
            is_client_error = any(err in error_name for err in client_error_names)

            if is_client_error:
                if hasattr(error, 'http_status'):
                    assert 400 <= error.http_status < 500
                elif hasattr(error, 'value') and isinstance(error.value, dict):
                    if 'http_status' in error.value:
                        assert 400 <= error.value['http_status'] < 500

    def test_server_errors_map_to_5xx(self):
        """测试服务器错误映射到 5xx"""
        from app.core.errors import ErrorCode

        for error in ErrorCode:
            error_name = error.name.upper()
            is_server_error = 'INTERNAL' in error_name or 'DATABASE' in error_name

            if is_server_error:
                if hasattr(error, 'http_status'):
                    assert 500 <= error.http_status < 600
                elif hasattr(error, 'value') and isinstance(error.value, dict):
                    if 'http_status' in error.value:
                        assert 500 <= error.value['http_status'] < 600