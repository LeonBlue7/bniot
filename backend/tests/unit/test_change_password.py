"""
测试修改密码 API 端点
TDD RED 阶段 - 测试编写在实现之前
"""
import pytest
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.fixture
async def setup_password_test(db_session: AsyncSession):
    """创建修改密码测试所需的用户"""
    from app.models import Tenant, User
    from app.services.auth import get_password_hash, create_access_token

    tenant = Tenant(name="密码测试租户", code="pwd_test")
    db_session.add(tenant)
    await db_session.flush()

    user = User(
        tenant_id=tenant.id,
        username="pwd_test_user",
        password_hash=get_password_hash("oldpassword123"),
        role="admin",
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()

    token = create_access_token(
        data={"sub": user.username, "tenant_id": tenant.id}
    )

    return {"user": user, "tenant": tenant, "token": token}


class TestChangePasswordEndpoint:
    """测试修改密码端点"""

    @pytest.mark.asyncio
    async def test_change_password_success(self, db_session, setup_password_test):
        """测试修改密码成功"""
        from app.main import app
        from app.core.database import get_db

        test_data = setup_password_test

        # Override dependency
        async def _get_db_override():
            yield db_session
        app.dependency_overrides[get_db] = _get_db_override

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/auth/change-password",
                headers={"Authorization": f"Bearer {test_data['token']}"},
                json={
                    "old_password": "oldpassword123",
                    "new_password": "newpassword123"
                }
            )

        app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "密码修改成功"

    @pytest.mark.asyncio
    async def test_change_password_wrong_old_password(self, db_session, setup_password_test):
        """测试当前密码错误"""
        from app.main import app
        from app.core.database import get_db

        test_data = setup_password_test

        async def _get_db_override():
            yield db_session
        app.dependency_overrides[get_db] = _get_db_override

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/auth/change-password",
                headers={"Authorization": f"Bearer {test_data['token']}"},
                json={
                    "old_password": "wrongpassword",
                    "new_password": "newpassword123"
                }
            )

        app.dependency_overrides.clear()

        assert response.status_code == 400
        data = response.json()
        assert "当前密码错误" in data["detail"]

    @pytest.mark.asyncio
    async def test_change_password_unauthorized(self, db_session):
        """测试未认证用户修改密码"""
        from app.main import app
        from app.core.database import get_db

        async def _get_db_override():
            yield db_session
        app.dependency_overrides[get_db] = _get_db_override

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/auth/change-password",
                json={
                    "old_password": "oldpassword",
                    "new_password": "newpassword123"
                }
            )

        app.dependency_overrides.clear()

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_change_password_invalid_input(self, db_session, setup_password_test):
        """测试无效输入（密码太短）"""
        from app.main import app
        from app.core.database import get_db

        test_data = setup_password_test

        async def _get_db_override():
            yield db_session
        app.dependency_overrides[get_db] = _get_db_override

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/auth/change-password",
                headers={"Authorization": f"Bearer {test_data['token']}"},
                json={
                    "old_password": "old",
                    "new_password": "new"
                }
            )

        app.dependency_overrides.clear()

        assert response.status_code == 422  # Validation error