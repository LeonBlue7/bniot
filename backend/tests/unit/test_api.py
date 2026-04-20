"""
测试 API 端点
Phase 2 核心模块测试 - 集成测试

注意：这些测试需要后端服务运行，在 Docker 环境中测试时服务自动可用
"""
import pytest
import os


# 获取 API 基础 URL（在 Docker 内使用 localhost，外部使用环境变量）
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:5000")


class TestHealthEndpoint:
    """测试健康检查端点"""

    def test_health_check_sync(self):
        """测试健康检查返回正确响应"""
        import httpx

        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.get(f"{API_BASE_URL}/health")
                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "healthy"
                assert "version" in data
        except httpx.ConnectError:
            pytest.skip("服务未运行")


class TestAuthEndpoints:
    """测试认证端点"""

    def test_login_wrong_password(self):
        """测试登录密码错误"""
        import httpx

        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.post(
                    f"{API_BASE_URL}/api/auth/login",
                    data={"username": "admin", "password": "wrongpassword"}
                )
                assert response.status_code == 401
        except httpx.ConnectError:
            pytest.skip("服务未运行")

    def test_login_user_not_found(self):
        """测试登录用户不存在"""
        import httpx

        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.post(
                    f"{API_BASE_URL}/api/auth/login",
                    data={"username": "nonexistent", "password": "anypassword"}
                )
                assert response.status_code == 401
        except httpx.ConnectError:
            pytest.skip("服务未运行")


class TestDeviceEndpoints:
    """测试设备端点"""

    def test_list_devices_unauthorized(self):
        """测试未授权访问设备列表"""
        import httpx

        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.get(f"{API_BASE_URL}/api/devices")
                assert response.status_code == 401
        except httpx.ConnectError:
            pytest.skip("服务未运行")

    def test_list_devices_with_auth(self):
        """测试授权访问设备列表"""
        import httpx

        try:
            with httpx.Client(timeout=10.0) as client:
                # 先获取 token
                login_resp = client.post(
                    f"{API_BASE_URL}/api/auth/login",
                    data={"username": "admin", "password": "admin123"}
                )
                if login_resp.status_code != 200:
                    pytest.skip("登录失败")

                token = login_resp.json()["access_token"]

                response = client.get(
                    f"{API_BASE_URL}/api/devices",
                    headers={"Authorization": f"Bearer {token}"}
                )
                assert response.status_code == 200
                data = response.json()
                assert "items" in data
                assert "total" in data
        except httpx.ConnectError:
            pytest.skip("服务未运行")


class TestZoneEndpoints:
    """测试分区端点"""

    def test_list_zones_unauthorized(self):
        """测试未授权访问分区列表"""
        import httpx

        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.get(f"{API_BASE_URL}/api/zones")
                assert response.status_code == 401
        except httpx.ConnectError:
            pytest.skip("服务未运行")

    def test_list_zones_with_auth(self):
        """测试授权访问分区列表"""
        import httpx

        try:
            with httpx.Client(timeout=10.0) as client:
                # 先获取 token
                login_resp = client.post(
                    f"{API_BASE_URL}/api/auth/login",
                    data={"username": "admin", "password": "admin123"}
                )
                if login_resp.status_code != 200:
                    pytest.skip("登录失败")

                token = login_resp.json()["access_token"]

                response = client.get(
                    f"{API_BASE_URL}/api/zones",
                    headers={"Authorization": f"Bearer {token}"}
                )
                assert response.status_code == 200
                data = response.json()
                assert isinstance(data, list)
        except httpx.ConnectError:
            pytest.skip("服务未运行")