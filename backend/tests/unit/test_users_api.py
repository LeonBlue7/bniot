"""
用户管理 API 端点测试
TDD 测试用例：用户 CRUD 操作
"""
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Tenant, User
from app.services.auth import create_access_token, get_password_hash


class TestUserListAPI:
    """用户列表 API 测试"""

    @pytest.mark.asyncio
    async def test_list_users_as_admin(self, db_session: AsyncSession):
        """测试管理员获取用户列表"""
        from app.main import app
        from app.core.database import get_db

        # 创建租户和用户
        tenant = Tenant(name="测试列表租户", code="test_list")
        db_session.add(tenant)
        await db_session.commit()
        await db_session.refresh(tenant)

        admin = User(
            tenant_id=tenant.id,
            username="admin_list",
            password_hash=get_password_hash("admin123"),
            role="admin",
            is_active=True
        )
        viewer = User(
            tenant_id=tenant.id,
            username="viewer_list",
            password_hash=get_password_hash("viewer123"),
            role="viewer",
            is_active=True
        )
        db_session.add_all([admin, viewer])
        await db_session.commit()
        await db_session.refresh(admin)
        await db_session.refresh(viewer)

        admin_token = create_access_token(
            data={"sub": admin.username, "tenant_id": admin.tenant_id}
        )

        async def _get_db_override():
            yield db_session

        app.dependency_overrides[get_db] = _get_db_override

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/users",
                headers={"Authorization": f"Bearer {admin_token}"}
            )

        app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2  # admin + viewer

    @pytest.mark.asyncio
    async def test_list_users_as_viewer_forbidden(self, db_session: AsyncSession):
        """测试观察员无法获取用户列表（权限不足）"""
        from app.main import app
        from app.core.database import get_db

        # 创建租户和观察员用户
        tenant = Tenant(name="测试观察员租户", code="test_viewer")
        db_session.add(tenant)
        await db_session.commit()
        await db_session.refresh(tenant)

        viewer = User(
            tenant_id=tenant.id,
            username="viewer_only",
            password_hash=get_password_hash("viewer123"),
            role="viewer",
            is_active=True
        )
        db_session.add(viewer)
        await db_session.commit()
        await db_session.refresh(viewer)

        viewer_token = create_access_token(
            data={"sub": viewer.username, "tenant_id": viewer.tenant_id}
        )

        async def _get_db_override():
            yield db_session

        app.dependency_overrides[get_db] = _get_db_override

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/users",
                headers={"Authorization": f"Bearer {viewer_token}"}
            )

        app.dependency_overrides.clear()

        assert response.status_code == 403


class TestUserCreateAPI:
    """创建用户 API 测试"""

    @pytest.mark.asyncio
    async def test_create_user_as_admin(self, db_session: AsyncSession):
        """测试管理员创建用户"""
        from app.main import app
        from app.core.database import get_db

        # 创建租户和管理员用户
        tenant = Tenant(name="测试创建租户", code="test_create")
        db_session.add(tenant)
        await db_session.commit()
        await db_session.refresh(tenant)

        admin = User(
            tenant_id=tenant.id,
            username="admin_create",
            password_hash=get_password_hash("admin123"),
            role="admin",
            is_active=True
        )
        db_session.add(admin)
        await db_session.commit()
        await db_session.refresh(admin)

        admin_token = create_access_token(
            data={"sub": admin.username, "tenant_id": admin.tenant_id}
        )

        async def _get_db_override():
            yield db_session

        app.dependency_overrides[get_db] = _get_db_override

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/users",
                headers={"Authorization": f"Bearer {admin_token}"},
                json={
                    "username": "new_operator",
                    "password": "operator123",
                    "role": "operator"
                }
            )

        app.dependency_overrides.clear()

        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "new_operator"
        assert data["role"] == "operator"
        assert data["tenant_id"] == tenant.id
        assert data["is_active"] is True
        assert "password" not in data  # 不返回密码

    @pytest.mark.asyncio
    async def test_create_user_duplicate_username(self, db_session: AsyncSession):
        """测试创建重复用户名失败"""
        from app.main import app
        from app.core.database import get_db

        # 创建租户和管理员用户
        tenant = Tenant(name="测试重复租户", code="test_dup")
        db_session.add(tenant)
        await db_session.commit()
        await db_session.refresh(tenant)

        admin = User(
            tenant_id=tenant.id,
            username="existing_user",
            password_hash=get_password_hash("admin123"),
            role="admin",
            is_active=True
        )
        db_session.add(admin)
        await db_session.commit()
        await db_session.refresh(admin)

        admin_token = create_access_token(
            data={"sub": admin.username, "tenant_id": admin.tenant_id}
        )

        async def _get_db_override():
            yield db_session

        app.dependency_overrides[get_db] = _get_db_override

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/users",
                headers={"Authorization": f"Bearer {admin_token}"},
                json={
                    "username": "existing_user",  # 已存在的用户名
                    "password": "test123",
                    "role": "viewer"
                }
            )

        app.dependency_overrides.clear()

        assert response.status_code == 400
        assert "已存在" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_user_invalid_role(self, db_session: AsyncSession):
        """测试创建用户使用无效角色"""
        from app.main import app
        from app.core.database import get_db

        # 创建租户和管理员用户
        tenant = Tenant(name="测试无效租户", code="test_invalid")
        db_session.add(tenant)
        await db_session.commit()
        await db_session.refresh(tenant)

        admin = User(
            tenant_id=tenant.id,
            username="admin_invalid",
            password_hash=get_password_hash("admin123"),
            role="admin",
            is_active=True
        )
        db_session.add(admin)
        await db_session.commit()
        await db_session.refresh(admin)

        admin_token = create_access_token(
            data={"sub": admin.username, "tenant_id": admin.tenant_id}
        )

        async def _get_db_override():
            yield db_session

        app.dependency_overrides[get_db] = _get_db_override

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/users",
                headers={"Authorization": f"Bearer {admin_token}"},
                json={
                    "username": "invalid_role_user",
                    "password": "test123",
                    "role": "superadmin"  # 无效角色
                }
            )

        app.dependency_overrides.clear()

        # 应该返回验证错误或400
        assert response.status_code in [400, 422]


class TestUserUpdateAPI:
    """更新用户 API 测试"""

    @pytest.mark.asyncio
    async def test_update_user_role(self, db_session: AsyncSession):
        """测试更新用户角色"""
        from app.main import app
        from app.core.database import get_db

        # 创建租户和用户
        tenant = Tenant(name="测试更新租户", code="test_update")
        db_session.add(tenant)
        await db_session.commit()
        await db_session.refresh(tenant)

        admin = User(
            tenant_id=tenant.id,
            username="admin_update",
            password_hash=get_password_hash("admin123"),
            role="admin",
            is_active=True
        )
        viewer = User(
            tenant_id=tenant.id,
            username="viewer_update",
            password_hash=get_password_hash("viewer123"),
            role="viewer",
            is_active=True
        )
        db_session.add_all([admin, viewer])
        await db_session.commit()
        await db_session.refresh(admin)
        await db_session.refresh(viewer)

        admin_token = create_access_token(
            data={"sub": admin.username, "tenant_id": admin.tenant_id}
        )

        async def _get_db_override():
            yield db_session

        app.dependency_overrides[get_db] = _get_db_override

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.put(
                f"/api/users/{viewer.id}",
                headers={"Authorization": f"Bearer {admin_token}"},
                json={"role": "operator"}
            )

        app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "operator"

    @pytest.mark.asyncio
    async def test_update_user_not_found(self, db_session: AsyncSession):
        """测试更新不存在的用户"""
        from app.main import app
        from app.core.database import get_db

        # 创建租户和管理员用户
        tenant = Tenant(name="测试不存在租户", code="test_notfound")
        db_session.add(tenant)
        await db_session.commit()
        await db_session.refresh(tenant)

        admin = User(
            tenant_id=tenant.id,
            username="admin_notfound",
            password_hash=get_password_hash("admin123"),
            role="admin",
            is_active=True
        )
        db_session.add(admin)
        await db_session.commit()
        await db_session.refresh(admin)

        admin_token = create_access_token(
            data={"sub": admin.username, "tenant_id": admin.tenant_id}
        )

        async def _get_db_override():
            yield db_session

        app.dependency_overrides[get_db] = _get_db_override

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.put(
                "/api/users/9999",
                headers={"Authorization": f"Bearer {admin_token}"},
                json={"role": "admin"}
            )

        app.dependency_overrides.clear()

        assert response.status_code == 404


class TestUserStatusAPI:
    """用户状态管理 API 测试"""

    @pytest.mark.asyncio
    async def test_disable_user(self, db_session: AsyncSession):
        """测试禁用用户"""
        from app.main import app
        from app.core.database import get_db

        # 创建租户和用户
        tenant = Tenant(name="测试禁用租户", code="test_disable")
        db_session.add(tenant)
        await db_session.commit()
        await db_session.refresh(tenant)

        admin = User(
            tenant_id=tenant.id,
            username="admin_disable",
            password_hash=get_password_hash("admin123"),
            role="admin",
            is_active=True
        )
        viewer = User(
            tenant_id=tenant.id,
            username="viewer_disable",
            password_hash=get_password_hash("viewer123"),
            role="viewer",
            is_active=True
        )
        db_session.add_all([admin, viewer])
        await db_session.commit()
        await db_session.refresh(admin)
        await db_session.refresh(viewer)

        admin_token = create_access_token(
            data={"sub": admin.username, "tenant_id": admin.tenant_id}
        )

        async def _get_db_override():
            yield db_session

        app.dependency_overrides[get_db] = _get_db_override

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.patch(
                f"/api/users/{viewer.id}/status",
                headers={"Authorization": f"Bearer {admin_token}"},
                json={"is_active": False}
            )

        app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is False

    @pytest.mark.asyncio
    async def test_enable_user(self, db_session: AsyncSession):
        """测试启用用户"""
        from app.main import app
        from app.core.database import get_db

        # 创建租户和用户
        tenant = Tenant(name="启用测试租户", code="test_enable")
        db_session.add(tenant)
        await db_session.commit()
        await db_session.refresh(tenant)

        admin = User(
            tenant_id=tenant.id,
            username="admin_enable",
            password_hash=get_password_hash("admin123"),
            role="admin",
            is_active=True
        )
        disabled_user = User(
            tenant_id=tenant.id,
            username="disabled_user",
            password_hash=get_password_hash("test123"),
            role="viewer",
            is_active=False
        )
        db_session.add_all([admin, disabled_user])
        await db_session.commit()
        await db_session.refresh(admin)
        await db_session.refresh(disabled_user)

        admin_token = create_access_token(
            data={"sub": admin.username, "tenant_id": admin.tenant_id}
        )

        async def _get_db_override():
            yield db_session

        app.dependency_overrides[get_db] = _get_db_override

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.patch(
                f"/api/users/{disabled_user.id}/status",
                headers={"Authorization": f"Bearer {admin_token}"},
                json={"is_active": True}
            )

        app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is True

    @pytest.mark.asyncio
    async def test_cannot_disable_self(self, db_session: AsyncSession):
        """测试管理员不能禁用自己"""
        from app.main import app
        from app.core.database import get_db

        # 创建租户和管理员用户
        tenant = Tenant(name="测试自己租户", code="test_self")
        db_session.add(tenant)
        await db_session.commit()
        await db_session.refresh(tenant)

        admin = User(
            tenant_id=tenant.id,
            username="admin_self",
            password_hash=get_password_hash("admin123"),
            role="admin",
            is_active=True
        )
        db_session.add(admin)
        await db_session.commit()
        await db_session.refresh(admin)

        admin_token = create_access_token(
            data={"sub": admin.username, "tenant_id": admin.tenant_id}
        )

        async def _get_db_override():
            yield db_session

        app.dependency_overrides[get_db] = _get_db_override

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.patch(
                f"/api/users/{admin.id}/status",
                headers={"Authorization": f"Bearer {admin_token}"},
                json={"is_active": False}
            )

        app.dependency_overrides.clear()

        assert response.status_code == 400
        assert "不能禁用自己" in response.json()["detail"]


class TestUserCrossTenant:
    """跨租户访问测试"""

    @pytest.mark.asyncio
    async def test_cannot_access_other_tenant_users(self, db_session: AsyncSession):
        """测试不能访问其他租户的用户"""
        from app.main import app
        from app.core.database import get_db

        # 创建两个租户
        tenant1 = Tenant(name="租户1", code="tenant1_users")
        tenant2 = Tenant(name="租户2", code="tenant2_users")
        db_session.add_all([tenant1, tenant2])
        await db_session.commit()
        await db_session.refresh(tenant1)
        await db_session.refresh(tenant2)

        # 创建两个管理员
        admin1 = User(
            tenant_id=tenant1.id,
            username="admin1",
            password_hash=get_password_hash("admin123"),
            role="admin",
            is_active=True
        )
        admin2 = User(
            tenant_id=tenant2.id,
            username="admin2",
            password_hash=get_password_hash("admin123"),
            role="admin",
            is_active=True
        )
        db_session.add_all([admin1, admin2])
        await db_session.commit()
        await db_session.refresh(admin1)
        await db_session.refresh(admin2)

        token1 = create_access_token(
            data={"sub": admin1.username, "tenant_id": tenant1.id}
        )

        async def _get_db_override():
            yield db_session

        app.dependency_overrides[get_db] = _get_db_override

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # admin1 尝试获取用户列表（应该只能看到 tenant1 的用户）
            response = await client.get(
                "/api/users",
                headers={"Authorization": f"Bearer {token1}"}
            )

        app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        # 应该只有 tenant1 的用户，不包括 admin2
        for user in data:
            assert user["tenant_id"] == tenant1.id