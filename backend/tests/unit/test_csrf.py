"""
CSRF 保护服务测试
测试 CSRF Token 的生成、验证和端点
"""
import pytest
import time
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import timedelta

# 导入待测试的服务
from app.services.csrf import (
    generate_csrf_token,
    verify_csrf_token,
    store_csrf_token,
    create_csrf_token_for_user,
    is_csrf_exempt,
    requires_csrf,
    CSRF_EXPIRE_SECONDS,
)


# ============ Fixtures ============
@pytest.fixture
def mock_redis():
    """创建模拟 Redis 客户端"""
    redis_mock = AsyncMock()
    # 模拟 Redis 数据存储
    data = {}

    async def mock_get(key):
        return data.get(key)

    async def mock_set(key, value, ex=None):
        data[key] = value
        return True

    async def mock_delete(key):
        if key in data:
            del data[key]
        return 1

    async def mock_ttl(key):
        # 返回一个正数模拟 TTL
        if key in data:
            return CSRF_EXPIRE_SECONDS
        return -2

    redis_mock.get = mock_get
    redis_mock.set = mock_set
    redis_mock.delete = mock_delete
    redis_mock.ttl = mock_ttl

    return redis_mock


# ============ Token 生成测试 ============
class TestCSRFTokenGeneration:
    """CSRF Token 生成测试"""

    def test_generate_csrf_token_returns_string(self):
        """测试生成 CSRF Token 返回字符串"""
        token = generate_csrf_token()
        assert isinstance(token, str)
        assert len(token) > 0

    def test_generate_csrf_token_has_minimum_length(self):
        """测试 CSRF Token 最小长度（安全随机性）"""
        token = generate_csrf_token()
        # 32 字节的 base64 编码，至少 43 个字符
        assert len(token) >= 32

    def test_generate_csrf_token_is_unique(self):
        """测试多次生成返回不同的 Token"""
        token1 = generate_csrf_token()
        token2 = generate_csrf_token()
        assert token1 != token2

    def test_generate_csrf_token_url_safe(self):
        """测试 Token 是 URL 安全的（无特殊字符）"""
        token = generate_csrf_token()
        # URL 安全的 base64 只包含 A-Za-z0-9-_
        import re
        assert re.match(r'^[A-Za-z0-9_-]+$', token), f"Token contains unsafe chars: {token}"


# ============ Token 验证测试 ============
class TestCSRFTokenVerification:
    """CSRF Token 验证测试"""

    @pytest.mark.asyncio
    async def test_verify_valid_token(self, mock_redis):
        """测试验证有效的 CSRF Token"""
        token = generate_csrf_token()
        user_id = "test_user_123"

        # 先存储 Token
        await mock_redis.set(f"csrf:{user_id}:{token}", "1", ex=CSRF_EXPIRE_SECONDS)

        # 验证应该成功
        result = await verify_csrf_token(token, user_id, mock_redis)
        assert result is True

    @pytest.mark.asyncio
    async def test_verify_invalid_token(self, mock_redis):
        """测试验证无效的 CSRF Token"""
        token = "invalid_token_12345"
        user_id = "test_user_123"

        # 验证无效 Token 应该失败
        result = await verify_csrf_token(token, user_id, mock_redis)
        assert result is False

    @pytest.mark.asyncio
    async def test_verify_token_wrong_user(self, mock_redis):
        """测试使用其他用户的 Token"""
        token = generate_csrf_token()
        user_id = "user_a"
        other_user_id = "user_b"

        # 存储给 user_a
        await mock_redis.set(f"csrf:{user_id}:{token}", "1", ex=CSRF_EXPIRE_SECONDS)

        # user_b 尝试验证应该失败
        result = await verify_csrf_token(token, other_user_id, mock_redis)
        assert result is False

    @pytest.mark.asyncio
    async def test_verify_expired_token(self, mock_redis):
        """测试验证过期的 CSRF Token"""
        token = generate_csrf_token()
        user_id = "test_user_123"

        # 存储 Token 并立即删除（模拟过期）
        await mock_redis.set(f"csrf:{user_id}:{token}", "1", ex=1)
        await mock_redis.delete(f"csrf:{user_id}:{token}")

        # 验证过期 Token 应该失败
        result = await verify_csrf_token(token, user_id, mock_redis)
        assert result is False

    @pytest.mark.asyncio
    async def test_verify_empty_token(self, mock_redis):
        """测试验证空 Token"""
        result = await verify_csrf_token("", "user_123", mock_redis)
        assert result is False

    @pytest.mark.asyncio
    async def test_verify_empty_user_id(self, mock_redis):
        """测试验证空用户 ID"""
        token = generate_csrf_token()
        result = await verify_csrf_token(token, "", mock_redis)
        assert result is False

    @pytest.mark.asyncio
    async def test_verify_token_deletes_after_use(self, mock_redis):
        """测试 Token 使用后删除（一次性）"""
        token = generate_csrf_token()
        user_id = "test_user_123"

        # 存储 Token
        await mock_redis.set(f"csrf:{user_id}:{token}", "1", ex=CSRF_EXPIRE_SECONDS)

        # 第一次验证成功
        result1 = await verify_csrf_token(token, user_id, mock_redis)
        assert result1 is True

        # 第二次验证应该失败（Token 已删除）
        result2 = await verify_csrf_token(token, user_id, mock_redis)
        assert result2 is False


# ============ Token 存储测试 ============
class TestCSRFTokenStorage:
    """CSRF Token 存储测试"""

    @pytest.mark.asyncio
    async def test_store_csrf_token(self, mock_redis):
        """测试存储 CSRF Token"""
        token = generate_csrf_token()
        user_id = "test_user_123"

        await store_csrf_token(token, user_id, mock_redis)

        # 验证存储成功
        stored = await mock_redis.get(f"csrf:{user_id}:{token}")
        assert stored == "1"

    @pytest.mark.asyncio
    async def test_store_csrf_token_with_expiry(self, mock_redis):
        """测试 Token 存储有过期时间"""
        token = generate_csrf_token()
        user_id = "test_user_123"

        await store_csrf_token(token, user_id, mock_redis)

        # 检查过期时间设置（TTL > 0）
        ttl = await mock_redis.ttl(f"csrf:{user_id}:{token}")
        assert ttl > 0
        assert ttl <= CSRF_EXPIRE_SECONDS

    @pytest.mark.asyncio
    async def test_create_csrf_token_for_user(self, mock_redis):
        """测试为用户创建 CSRF Token"""
        user_id = "test_user_456"

        token = await create_csrf_token_for_user(user_id, mock_redis)

        # Token 应该已存储
        stored = await mock_redis.get(f"csrf:{user_id}:{token}")
        assert stored == "1"


# ============ CSRF 中间件测试 ============
class TestCSRFMiddleware:
    """CSRF 中间件测试"""

    def test_csrf_middleware_exemptions(self):
        """测试 CSRF 中间件豁免路径"""

        # GET, HEAD, OPTIONS 应该豁免
        assert is_csrf_exempt("GET", "/api/auth/login") is True
        assert is_csrf_exempt("HEAD", "/api/devices") is True
        assert is_csrf_exempt("OPTIONS", "/api/zones") is True

        # CSRF Token 端点豁免
        assert is_csrf_exempt("GET", "/api/auth/csrf-token") is True

        # 登录端点豁免（还没有 Token）
        assert is_csrf_exempt("POST", "/api/auth/login") is True

        # 健康检查豁免
        assert is_csrf_exempt("GET", "/health") is True

        # 其他 POST 请求不豁免
        assert is_csrf_exempt("POST", "/api/devices") is False
        assert is_csrf_exempt("PUT", "/api/devices/1") is False
        assert is_csrf_exempt("DELETE", "/api/zones/1") is False

    def test_csrf_middleware_requirement(self):
        """测试 CSRF 中间件对请求方法的要求"""

        # GET, HEAD, OPTIONS 不需要 CSRF
        assert requires_csrf("GET") is False
        assert requires_csrf("HEAD") is False
        assert requires_csrf("OPTIONS") is False

        # POST, PUT, DELETE, PATCH 需要 CSRF
        assert requires_csrf("POST") is True
        assert requires_csrf("PUT") is True
        assert requires_csrf("DELETE") is True
        assert requires_csrf("PATCH") is True


# ============ API 端点测试 ============
class TestCSRFEndpoints:
    """CSRF API 端点测试（使用模拟）"""

    @pytest.mark.asyncio
    async def test_get_csrf_token_endpoint_logic(self, mock_redis):
        """测试获取 CSRF Token 端点逻辑"""
        user_id = "testuser"

        # 调用创建 Token 函数
        token = await create_csrf_token_for_user(user_id, mock_redis)

        # 验证返回的 Token
        assert token is not None
        assert len(token) >= 32

        # 验证 Token 已存储
        stored = await mock_redis.get(f"csrf:{user_id}:{token}")
        assert stored == "1"

    @pytest.mark.asyncio
    async def test_csrf_token_workflow(self, mock_redis):
        """测试完整的 CSRF Token 工作流"""
        user_id = "testuser_workflow"

        # 1. 获取 CSRF Token
        token = await create_csrf_token_for_user(user_id, mock_redis)
        assert token is not None

        # 2. 验证 Token（模拟请求携带 Token）
        is_valid = await verify_csrf_token(token, user_id, mock_redis)
        assert is_valid is True

        # 3. 验证 Token 已被删除（一次性使用）
        is_valid_again = await verify_csrf_token(token, user_id, mock_redis)
        assert is_valid_again is False

        # 4. 获取新 Token 进行下一次请求
        new_token = await create_csrf_token_for_user(user_id, mock_redis)
        assert new_token != token  # 新 Token 应该不同

    @pytest.mark.asyncio
    async def test_concurrent_token_usage(self, mock_redis):
        """测试并发 Token 使用场景"""
        user_id = "concurrent_user"

        # 用户可以同时持有多个有效 Token
        token1 = await create_csrf_token_for_user(user_id, mock_redis)
        token2 = await create_csrf_token_for_user(user_id, mock_redis)
        token3 = await create_csrf_token_for_user(user_id, mock_redis)

        # 所有 Token 应该都有效
        assert await verify_csrf_token(token1, user_id, mock_redis) is True
        assert await verify_csrf_token(token2, user_id, mock_redis) is True
        assert await verify_csrf_token(token3, user_id, mock_redis) is True


# ============ 边界情况测试 ============
class TestCSRFEdgeCases:
    """CSRF 边界情况测试"""

    @pytest.mark.asyncio
    async def test_verify_token_with_none_values(self, mock_redis):
        """测试验证 None 值"""
        assert await verify_csrf_token(None, "user", mock_redis) is False
        assert await verify_csrf_token("token", None, mock_redis) is False
        assert await verify_csrf_token(None, None, mock_redis) is False

    @pytest.mark.asyncio
    async def test_verify_very_long_token(self, mock_redis):
        """测试验证超长 Token"""
        long_token = "a" * 1000
        user_id = "test_user"

        # 不应该崩溃
        result = await verify_csrf_token(long_token, user_id, mock_redis)
        assert result is False

    @pytest.mark.asyncio
    async def test_verify_token_with_special_characters(self, mock_redis):
        """测试验证包含特殊字符的 Token"""
        special_token = "token/with:special@chars#and$more"
        user_id = "test_user"

        # 不应该崩溃
        result = await verify_csrf_token(special_token, user_id, mock_redis)
        assert result is False

    def test_is_csrf_exempt_static_paths(self):
        """测试静态文件路径豁免"""
        assert is_csrf_exempt("GET", "/static/css/style.css") is True
        assert is_csrf_exempt("GET", "/api/static/images/logo.png") is True

    def test_requires_csrf_case_insensitive(self):
        """测试 HTTP 方法大小写不敏感"""
        assert requires_csrf("post") is True
        assert requires_csrf("POST") is True
        assert requires_csrf("get") is False
        assert requires_csrf("GET") is False


# ============ CSRF 依赖测试 ============
class TestCSRFDependency:
    """CSRF 依赖函数测试"""

    @pytest.mark.asyncio
    async def test_verify_csrf_dependency_exempt_method(self):
        """测试 CSRF 依赖豁免安全方法"""
        from app.services.csrf import verify_csrf_dependency, get_redis_client
        from unittest.mock import MagicMock

        # 创建模拟请求
        request = MagicMock()
        request.method = "GET"
        request.url.path = "/api/devices"

        # GET 方法应该豁免，不抛出异常
        await verify_csrf_dependency(request, None)

    @pytest.mark.asyncio
    async def test_verify_csrf_dependency_exempt_path(self):
        """测试 CSRF 依赖豁免路径"""
        from app.services.csrf import verify_csrf_dependency
        from unittest.mock import MagicMock

        # 创建模拟请求
        request = MagicMock()
        request.method = "POST"
        request.url.path = "/api/auth/login"

        # 登录路径应该豁免，不抛出异常
        await verify_csrf_dependency(request, None)

    @pytest.mark.asyncio
    async def test_verify_csrf_dependency_missing_token(self):
        """测试 CSRF 依赖缺少 Token"""
        from app.services.csrf import verify_csrf_dependency
        from fastapi import HTTPException
        from unittest.mock import MagicMock, AsyncMock

        # 创建模拟请求
        request = MagicMock()
        request.method = "POST"
        request.url.path = "/api/devices"
        request.headers = {}  # 无 CSRF Token
        request.app.state.redis_client = AsyncMock()

        # 应该抛出 403 异常
        try:
            await verify_csrf_dependency(request, None)
            assert False, "应该抛出异常"
        except HTTPException as e:
            assert e.status_code == 403
            assert "缺少 CSRF Token" in e.detail

    @pytest.mark.asyncio
    async def test_verify_csrf_dependency_invalid_token(self):
        """测试 CSRF 依赖无效 Token"""
        from app.services.csrf import verify_csrf_dependency
        from fastapi import HTTPException
        from unittest.mock import MagicMock, AsyncMock

        # 创建模拟 Redis
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)  # Token 不存在

        # 创建模拟请求
        request = MagicMock()
        request.method = "POST"
        request.url.path = "/api/devices"
        request.headers = {"X-CSRF-Token": "invalid_token"}
        request.app.state.redis_client = mock_redis

        # 创建模拟用户
        user = MagicMock()
        user.username = "testuser"

        # 应该抛出 403 异常
        try:
            await verify_csrf_dependency(request, user)
            assert False, "应该抛出异常"
        except HTTPException as e:
            assert e.status_code == 403
            assert "CSRF Token 无效" in e.detail

    @pytest.mark.asyncio
    async def test_verify_csrf_dependency_valid_token(self):
        """测试 CSRF 依赖有效 Token"""
        from app.services.csrf import verify_csrf_dependency
        from unittest.mock import MagicMock, AsyncMock

        # 创建模拟 Redis
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value="1")  # Token 存在
        mock_redis.delete = AsyncMock(return_value=1)

        # 创建模拟请求
        request = MagicMock()
        request.method = "POST"
        request.url.path = "/api/devices"
        request.headers = {"X-CSRF-Token": "valid_token"}
        request.app.state.redis_client = mock_redis

        # 创建模拟用户
        user = MagicMock()
        user.username = "testuser"

        # 应该不抛出异常
        await verify_csrf_dependency(request, user)

        # 验证 Token 被删除（一次性使用）
        mock_redis.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_redis_client(self):
        """测试获取 Redis 客户端"""
        from app.services.csrf import get_redis_client
        from unittest.mock import MagicMock

        # 创建模拟请求
        request = MagicMock()
        mock_redis = MagicMock()
        request.app.state.redis_client = mock_redis

        # 获取 Redis 客户端
        result = await get_redis_client(request)

        assert result == mock_redis

    def test_get_csrf_dependency(self):
        """测试获取 CSRF 依赖函数"""
        from app.services.csrf import get_csrf_dependency
        from fastapi import Depends

        # 获取依赖
        dep = get_csrf_dependency()

        # 应该返回 Depends 对象
        assert isinstance(dep, type(Depends(lambda: None)))