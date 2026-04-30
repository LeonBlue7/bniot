"""
微信小程序登录功能测试
TDD - GREEN Phase: 测试微信登录 API

测试覆盖:
1. 微信登录 API - POST /api/wechat/login
   - 正常登录流程（已绑定用户）
   - 新用户首次登录（自动创建用户）
   - 无效 code 错误处理
   - 微信 API 调用失败处理

2. 微信绑定 API - POST /api/users/bind-wechat
   - 正常绑定流程
   - 已绑定用户再次绑定
   - openid 已被其他用户绑定

3. 微信解绑 API - DELETE /api/users/unbind-wechat
   - 正常解绑流程
   - 未绑定用户解绑

4. 边缘情况:
   - 空 code
   - 无效 code 格式
   - 网络超时
   - 微信 API 返回错误
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select

from app.main import app
from app.models import User, Tenant
from app.services.auth import get_password_hash, create_access_token
from app.schemas import WechatLoginRequest, WechatBindRequest
from app.core.database import get_db
from app.services.auth import get_current_user


@pytest.fixture
async def test_tenant(db_session):
    """创建测试租户"""
    tenant = Tenant(name="测试租户", code="test_wechat")
    db_session.add(tenant)
    await db_session.commit()
    await db_session.refresh(tenant)
    return tenant


@pytest.fixture
async def test_user_with_wechat(db_session, test_tenant):
    """创建已绑定微信的测试用户（admin 角色）"""
    user = User(
        tenant_id=test_tenant.id,
        username="wechat_user_test",
        password_hash=get_password_hash("test_password"),
        role="admin",  # 需要 admin 权限才能访问某些 API
        is_active=True,
        wechat_openid="test_openid_12345"
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def test_user_without_wechat(db_session, test_tenant):
    """创建未绑定微信的测试用户（admin 角色）"""
    user = User(
        tenant_id=test_tenant.id,
        username="normal_user_test",
        password_hash=get_password_hash("test_password"),
        role="admin",  # 需要 admin 权限
        is_active=True,
        wechat_openid=None
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
def test_token_for_user(test_user_without_wechat):
    """为测试用户生成 JWT token"""
    token = create_access_token(
        data={"sub": test_user_without_wechat.username, "tenant_id": test_user_without_wechat.tenant_id}
    )
    return token


@pytest.fixture
def test_token_for_wechat_user(test_user_with_wechat):
    """为已绑定微信用户生成 JWT token"""
    token = create_access_token(
        data={"sub": test_user_with_wechat.username, "tenant_id": test_user_with_wechat.tenant_id}
    )
    return token


@pytest.fixture
def override_get_current_user_for_wechat(test_user_with_wechat):
    """覆盖 get_current_user 依赖，返回已绑定微信的测试用户"""
    async def _get_current_user_override():
        return test_user_with_wechat
    return _get_current_user_override


@pytest.fixture
def override_get_current_user_for_normal(test_user_without_wechat):
    """覆盖 get_current_user 依赖，返回未绑定微信的测试用户"""
    async def _get_current_user_override():
        return test_user_without_wechat
    return _get_current_user_override


class TestWechatLoginAPI:
    """测试微信小程序登录 API"""

    @pytest.mark.asyncio
    async def test_wechat_login_existing_user_success(
        self, db_session, test_user_with_wechat, override_get_db
    ):
        """测试已绑定用户微信登录成功"""
        # Mock 微信 API 返回
        mock_wechat_response = {
            "openid": "test_openid_12345",
            "session_key": "test_session_key"
        }

        # Mock 异步函数
        async def mock_get_openid(code):
            return mock_wechat_response

        with patch("app.api.endpoints.wechat.get_wechat_openid_async", new=mock_get_openid):
            # 设置依赖覆盖
            app.dependency_overrides.clear()
            app.dependency_overrides[get_db] = override_get_db

            transport = ASGITransport(app=app)
            client = AsyncClient(transport=transport, base_url="http://test")

            # 发送登录请求
            response = await client.post(
                "/api/wechat/login",
                json={"code": "test_code_123"}
            )

            # 验证响应
            assert response.status_code == 200
            data = response.json()
            assert "access_token" in data
            assert data["token_type"] == "bearer"
            assert data["is_new_user"] == False
            assert data["user"]["username"] == test_user_with_wechat.username
            assert data["user"]["wechat_openid"] == "test_openid_12345"

            await client.aclose()
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_wechat_login_new_user_auto_create(
        self, db_session, test_tenant, override_get_db
    ):
        """测试新用户首次微信登录（自动创建用户）"""
        # Mock 微信 API 返回新的 openid
        new_openid = "new_openid_99999"

        async def mock_get_openid(code):
            return {
                "openid": new_openid,
                "session_key": "test_session_key"
            }

        with patch("app.api.endpoints.wechat.get_wechat_openid_async", new=mock_get_openid):
            # 设置依赖覆盖
            app.dependency_overrides.clear()
            app.dependency_overrides[get_db] = override_get_db

            transport = ASGITransport(app=app)
            client = AsyncClient(transport=transport, base_url="http://test")

            # 发送登录请求
            response = await client.post(
                "/api/wechat/login",
                json={"code": "test_new_code"}
            )

            # 验证响应
            assert response.status_code == 200
            data = response.json()
            assert "access_token" in data
            assert data["is_new_user"] == True
            assert data["user"]["wechat_openid"] == new_openid
            # 用户名应该是自动生成的
            assert "wechat_" in data["user"]["username"]

            # 验证数据库中创建了新用户
            result = await db_session.execute(
                select(User).where(User.wechat_openid == new_openid)
            )
            new_user = result.scalar_one_or_none()
            assert new_user is not None
            assert new_user.role == "viewer"
            assert new_user.is_active == True

            await client.aclose()
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_wechat_login_invalid_code(
        self, db_session, override_get_db
    ):
        """测试无效 code 登录失败"""
        # Mock 微信 API 返回 None（获取 openid 失败）
        async def mock_get_openid(code):
            return None

        with patch("app.api.endpoints.wechat.get_wechat_openid_async", new=mock_get_openid):
            # 设置依赖覆盖
            app.dependency_overrides.clear()
            app.dependency_overrides[get_db] = override_get_db

            transport = ASGITransport(app=app)
            client = AsyncClient(transport=transport, base_url="http://test")

            # 发送登录请求
            response = await client.post(
                "/api/wechat/login",
                json={"code": "invalid_code"}
            )

            # 验证响应 - 应该返回错误
            assert response.status_code == 400
            data = response.json()
            assert "detail" in data
            assert "失败" in data["detail"] or "无效" in data["detail"]

            await client.aclose()
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_wechat_login_empty_code(
        self, db_session, override_get_db
    ):
        """测试空 code 登录失败"""
        # 设置依赖覆盖
        app.dependency_overrides.clear()
        app.dependency_overrides[get_db] = override_get_db

        transport = ASGITransport(app=app)
        client = AsyncClient(transport=transport, base_url="http://test")

        # 发送空 code 请求
        response = await client.post(
            "/api/wechat/login",
            json={"code": ""}
        )

        # 验证响应 - 应该返回验证错误（Pydantic validation）
        assert response.status_code == 422

        await client.aclose()
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_wechat_login_missing_code_field(
        self, db_session, override_get_db
    ):
        """测试缺少 code 字段"""
        # 设置依赖覆盖
        app.dependency_overrides.clear()
        app.dependency_overrides[get_db] = override_get_db

        transport = ASGITransport(app=app)
        client = AsyncClient(transport=transport, base_url="http://test")

        # 发送无 code 字段的请求
        response = await client.post(
            "/api/wechat/login",
            json={}
        )

        # 验证响应 - 应该返回验证错误
        assert response.status_code == 422

        await client.aclose()
        app.dependency_overrides.clear()


class TestWechatBindAPI:
    """测试微信绑定 API"""

    @pytest.mark.asyncio
    async def test_bind_wechat_success(
        self, db_session, test_user_without_wechat, test_token_for_user, override_get_db
    ):
        """测试正常绑定微信成功"""
        new_openid = "bind_openid_88888"

        async def mock_get_openid(code):
            return {
                "openid": new_openid,
                "session_key": "test_session_key"
            }

        with patch("app.api.endpoints.users.get_wechat_openid_async", new=mock_get_openid):
            # 设置依赖覆盖
            app.dependency_overrides.clear()
            app.dependency_overrides[get_db] = override_get_db

            transport = ASGITransport(app=app)
            client = AsyncClient(transport=transport, base_url="http://test")

            # 发送绑定请求（需要认证）
            response = await client.post(
                "/api/users/bind-wechat",
                json={"code": "bind_test_code"},
                headers={"Authorization": f"Bearer {test_token_for_user}"}
            )

            # 验证响应
            assert response.status_code == 200
            data = response.json()
            assert data["success"] == True
            assert data["openid"] == new_openid

            # 验证数据库更新
            await db_session.refresh(test_user_without_wechat)
            assert test_user_without_wechat.wechat_openid == new_openid

            await client.aclose()
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_bind_wechat_already_bound(
        self, db_session, test_user_with_wechat, test_token_for_wechat_user, override_get_db
    ):
        """测试已绑定用户再次绑定失败"""
        async def mock_get_openid(code):
            return {
                "openid": "another_openid",
                "session_key": "test_session_key"
            }

        with patch("app.api.endpoints.users.get_wechat_openid_async", new=mock_get_openid):
            # 设置依赖覆盖
            app.dependency_overrides.clear()
            app.dependency_overrides[get_db] = override_get_db

            transport = ASGITransport(app=app)
            client = AsyncClient(transport=transport, base_url="http://test")

            # 发送绑定请求
            response = await client.post(
                "/api/users/bind-wechat",
                json={"code": "bind_test_code"},
                headers={"Authorization": f"Bearer {test_token_for_wechat_user}"}
            )

            # 验证响应 - 应该返回错误
            assert response.status_code == 400
            data = response.json()
            assert "已绑定" in data["detail"]

            await client.aclose()
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_bind_wechat_openid_already_used(
        self, db_session, test_user_without_wechat, test_user_with_wechat, test_token_for_user, override_get_db
    ):
        """测试 openid 已被其他用户绑定"""
        # 使用已绑定用户的 openid
        async def mock_get_openid(code):
            return {
                "openid": test_user_with_wechat.wechat_openid,
                "session_key": "test_session_key"
            }

        with patch("app.api.endpoints.users.get_wechat_openid_async", new=mock_get_openid):
            # 设置依赖覆盖
            app.dependency_overrides.clear()
            app.dependency_overrides[get_db] = override_get_db

            transport = ASGITransport(app=app)
            client = AsyncClient(transport=transport, base_url="http://test")

            # 发送绑定请求
            response = await client.post(
                "/api/users/bind-wechat",
                json={"code": "bind_test_code"},
                headers={"Authorization": f"Bearer {test_token_for_user}"}
            )

            # 验证响应 - 应该返回错误
            assert response.status_code == 400
            data = response.json()
            assert "已被绑定" in data["detail"] or "其他用户" in data["detail"]

            await client.aclose()
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_bind_wechat_without_auth(
        self, db_session, override_get_db
    ):
        """测试未认证用户绑定失败"""
        # 设置依赖覆盖
        app.dependency_overrides.clear()
        app.dependency_overrides[get_db] = override_get_db

        transport = ASGITransport(app=app)
        client = AsyncClient(transport=transport, base_url="http://test")

        # 发送绑定请求（无认证）
        response = await client.post(
            "/api/users/bind-wechat",
            json={"code": "bind_test_code"}
        )

        # 验证响应 - 应该返回认证错误
        assert response.status_code == 401

        await client.aclose()
        app.dependency_overrides.clear()


class TestWechatUnbindAPI:
    """测试微信解绑 API"""

    @pytest.mark.asyncio
    async def test_unbind_wechat_success(
        self, db_session, test_user_with_wechat, override_get_current_user_for_wechat, override_get_db
    ):
        """测试正常解绑微信成功"""
        # 设置依赖覆盖 - 必须覆盖 get_current_user 才能正确认证
        app.dependency_overrides.clear()
        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_current_user] = override_get_current_user_for_wechat

        transport = ASGITransport(app=app)
        client = AsyncClient(transport=transport, base_url="http://test")

        # 发送解绑请求
        response = await client.delete(
            "/api/users/unbind-wechat",
            headers={"Authorization": f"Bearer test_token"}
        )

        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True

        # 验证数据库更新
        await db_session.refresh(test_user_with_wechat)
        assert test_user_with_wechat.wechat_openid is None

        await client.aclose()
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_unbind_wechat_not_bound(
        self, db_session, test_user_without_wechat, override_get_current_user_for_normal, override_get_db
    ):
        """测试未绑定用户解绑失败"""
        # 设置依赖覆盖
        app.dependency_overrides.clear()
        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_current_user] = override_get_current_user_for_normal

        transport = ASGITransport(app=app)
        client = AsyncClient(transport=transport, base_url="http://test")

        # 发送解绑请求
        response = await client.delete(
            "/api/users/unbind-wechat",
            headers={"Authorization": f"Bearer test_token"}
        )

        # 验证响应 - 应该返回错误
        assert response.status_code == 400
        data = response.json()
        assert "未绑定" in data["detail"]

        await client.aclose()
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_unbind_wechat_without_auth(
        self, db_session, override_get_db
    ):
        """测试未认证用户解绑失败"""
        # 设置依赖覆盖
        app.dependency_overrides.clear()
        app.dependency_overrides[get_db] = override_get_db

        transport = ASGITransport(app=app)
        client = AsyncClient(transport=transport, base_url="http://test")

        # 发送解绑请求（无认证）
        response = await client.delete(
            "/api/users/unbind-wechat"
        )

        # 验证响应 - 应该返回认证错误
        assert response.status_code == 401

        await client.aclose()
        app.dependency_overrides.clear()


class TestWechatService:
    """测试微信服务函数"""

    def test_get_wechat_openid_success(self):
        """测试获取微信 openid 成功"""
        # Mock httpx.get 返回成功响应
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "openid": "test_openid",
            "session_key": "test_session_key"
        }

        with patch("httpx.Client.get") as mock_get:
            mock_get.return_value = mock_response

            # 设置环境变量
            from app.core.config import settings
            original_appid = settings.WECHAT_APPID
            original_secret = settings.WECHAT_SECRET

            # 使用 patch 临时设置配置
            with patch.object(settings, 'WECHAT_APPID', 'test_appid'):
                with patch.object(settings, 'WECHAT_SECRET', 'test_secret'):
                    from app.services.wechat import get_wechat_openid
                    result = get_wechat_openid("test_code")

                    assert result is not None
                    assert result["openid"] == "test_openid"

    def test_get_wechat_openid_invalid_code(self):
        """测试无效 code 获取 openid 失败"""
        # Mock 微信 API 返回错误
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "errcode": 40029,
            "errmsg": "invalid code"
        }

        with patch("httpx.Client.get") as mock_get:
            mock_get.return_value = mock_response

            from app.core.config import settings
            with patch.object(settings, 'WECHAT_APPID', 'test_appid'):
                with patch.object(settings, 'WECHAT_SECRET', 'test_secret'):
                    from app.services.wechat import get_wechat_openid
                    result = get_wechat_openid("invalid_code")

                    assert result is None

    def test_get_wechat_openid_network_error(self):
        """测试网络错误获取 openid 失败"""
        with patch("httpx.Client") as mock_client:
            mock_client_instance = MagicMock()
            mock_client_instance.get.side_effect = Exception("Network error")
            mock_client.return_value.__enter__.return_value = mock_client_instance

            from app.services.wechat import get_wechat_openid
            result = get_wechat_openid("test_code")

            assert result is None


class TestUserModelWechatField:
    """测试 User 模型的 wechat_openid 字段"""

    @pytest.mark.asyncio
    async def test_user_wechat_openid_nullable(self, db_session, test_tenant):
        """测试 wechat_openid 可为空"""
        user = User(
            tenant_id=test_tenant.id,
            username="no_wechat_user",
            password_hash=get_password_hash("password"),
            role="viewer",
            wechat_openid=None
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        assert user.wechat_openid is None

    @pytest.mark.asyncio
    async def test_user_wechat_openid_set(self, db_session, test_tenant):
        """测试 wechat_openid 可以正常设置"""
        openid = "test_openid_value"
        user = User(
            tenant_id=test_tenant.id,
            username="wechat_user_with_openid",
            password_hash=get_password_hash("password"),
            role="viewer",
            wechat_openid=openid
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        assert user.wechat_openid == openid

    @pytest.mark.asyncio
    async def test_user_response_contains_wechat_openid(
        self, test_user_with_wechat
    ):
        """测试 UserResponse schema 包含 wechat_openid"""
        from app.schemas import UserResponse

        user_response = UserResponse.model_validate(test_user_with_wechat)

        assert user_response.wechat_openid == test_user_with_wechat.wechat_openid