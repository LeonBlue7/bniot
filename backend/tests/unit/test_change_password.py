"""
测试修改密码 API 端点
TDD RED 阶段 - 测试编写在实现之前
"""
import pytest
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient, ASGITransport


class TestChangePasswordEndpoint:
    """测试修改密码端点"""

    @pytest.mark.asyncio
    async def test_change_password_success(self, test_app_with_redis, test_token, test_user):
        """测试修改密码成功"""
        from app.services.auth import get_password_hash, verify_password

        # 更新测试用户的密码哈希（模拟当前密码）
        test_user.password_hash = get_password_hash("oldpassword123")

        async with AsyncClient(
            transport=ASGITransport(app=test_app_with_redis),
            base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/auth/change-password",
                headers={"Authorization": f"Bearer {test_token}"},
                json={
                    "old_password": "oldpassword123",
                    "new_password": "newpassword123"
                }
            )

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "密码修改成功"

    @pytest.mark.asyncio
    async def test_change_password_wrong_old_password(self, test_app_with_redis, test_token, test_user):
        """测试当前密码错误"""
        from app.services.auth import get_password_hash

        # 设置当前密码
        test_user.password_hash = get_password_hash("correctpassword")

        async with AsyncClient(
            transport=ASGITransport(app=test_app_with_redis),
            base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/auth/change-password",
                headers={"Authorization": f"Bearer {test_token}"},
                json={
                    "old_password": "wrongpassword",
                    "new_password": "newpassword123"
                }
            )

        assert response.status_code == 400
        data = response.json()
        assert "当前密码错误" in data["detail"]

    @pytest.mark.asyncio
    async def test_change_password_unauthorized(self, test_app_with_redis):
        """测试未认证用户修改密码"""
        async with AsyncClient(
            transport=ASGITransport(app=test_app_with_redis),
            base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/auth/change-password",
                json={
                    "old_password": "oldpassword",
                    "new_password": "newpassword123"
                }
            )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_change_password_invalid_input(self, test_app_with_redis, test_token):
        """测试无效输入（密码太短）"""
        async with AsyncClient(
            transport=ASGITransport(app=test_app_with_redis),
            base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/auth/change-password",
                headers={"Authorization": f"Bearer {test_token}"},
                json={
                    "old_password": "old",
                    "new_password": "new"
                }
            )

        assert response.status_code == 422  # Validation error