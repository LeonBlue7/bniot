"""
测试登录速率限制
Phase 2 安全修复测试
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient


class TestLoginRateLimit:
    """测试登录速率限制"""

    @pytest.fixture
    def mock_redis(self):
        """创建 Mock Redis 客户端"""
        redis = AsyncMock()
        return redis

    @pytest.fixture
    def rate_limiter(self, mock_redis):
        """创建速率限制器实例"""
        from app.services.rate_limiter import RateLimiter
        return RateLimiter(mock_redis)

    @pytest.mark.asyncio
    async def test_rate_limiter_allows_first_attempt(self, rate_limiter, mock_redis):
        """测试第一次尝试应该允许"""
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.setex = AsyncMock()

        allowed = await rate_limiter.is_allowed("192.168.1.1", "login")

        assert allowed == True

    @pytest.mark.asyncio
    async def test_rate_limiter_blocks_after_max_attempts(self, rate_limiter, mock_redis):
        """测试超过最大尝试次数后应该阻止"""
        # 模拟已有 5 次失败记录
        mock_redis.get = AsyncMock(return_value=b"5")
        mock_redis.incr = AsyncMock(return_value=6)
        mock_redis.expire = AsyncMock()

        allowed = await rate_limiter.is_allowed("192.168.1.1", "login")

        assert allowed == False

    @pytest.mark.asyncio
    async def test_rate_limiter_resets_after_window(self, rate_limiter, mock_redis):
        """测试时间窗口过后应该重置"""
        # 模拟过期键（返回 None）
        mock_redis.get = AsyncMock(return_value=None)

        allowed = await rate_limiter.is_allowed("192.168.1.1", "login")

        assert allowed == True

    @pytest.mark.asyncio
    async def test_rate_limiter_records_failed_attempt(self, rate_limiter, mock_redis):
        """测试记录失败尝试"""
        mock_redis.incr = AsyncMock(return_value=1)
        mock_redis.expire = AsyncMock()

        await rate_limiter.record_failed_attempt("192.168.1.1", "login")

        mock_redis.incr.assert_called_once()
        mock_redis.expire.assert_called_once()

    @pytest.mark.asyncio
    async def test_rate_limiter_clears_on_success(self, rate_limiter, mock_redis):
        """测试成功后清除记录"""
        mock_redis.delete = AsyncMock()

        await rate_limiter.clear_attempts("192.168.1.1", "login")

        mock_redis.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_rate_limiter_with_username_identifier(self, rate_limiter, mock_redis):
        """测试使用用户名作为标识符"""
        mock_redis.incr = AsyncMock(return_value=1)
        mock_redis.expire = AsyncMock()

        # 应该同时限制 IP 和用户名
        await rate_limiter.record_failed_attempt("192.168.1.1", "login", identifier="admin")

        # 验证调用了 incr（记录失败）
        mock_redis.incr.assert_called_once()

    @pytest.mark.asyncio
    async def test_rate_limiter_get_remaining_attempts(self, rate_limiter, mock_redis):
        """测试获取剩余尝试次数"""
        mock_redis.get = AsyncMock(return_value=b"3")
        mock_redis.ttl = AsyncMock(return_value=60)

        remaining = await rate_limiter.get_remaining_attempts("192.168.1.1", "login")

        # 假设最大 5 次，已有 3 次，剩余 2 次
        assert remaining["attempts"] == 3
        assert remaining["remaining"] == 2
        assert remaining["ttl"] == 60


class TestRateLimitDependency:
    """测试速率限制 FastAPI 依赖"""

    @pytest.fixture
    def app(self):
        """创建测试应用"""
        from fastapi import FastAPI
        app = FastAPI()
        return app

    @pytest.mark.asyncio
    async def test_rate_limit_dependency_blocks_excessive_requests(self):
        """测试依赖阻止过多请求"""
        from app.services.rate_limiter import check_rate_limit
        from unittest.mock import AsyncMock

        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=b"5")  # 已达限制

        # 模拟请求上下文
        from fastapi import Request
        request = MagicMock(spec=Request)
        request.client = MagicMock()
        request.client.host = "192.168.1.1"

        with pytest.raises(HTTPException) as exc_info:
            await check_rate_limit(request, "login", mock_redis)

        assert exc_info.value.status_code == 429
        assert "频繁" in exc_info.value.detail or "limit" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_rate_limit_dependency_allows_normal_requests(self):
        """测试依赖允许正常请求"""
        from app.services.rate_limiter import check_rate_limit
        from unittest.mock import AsyncMock

        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)  # 没有记录

        from fastapi import Request
        request = MagicMock(spec=Request)
        request.client = MagicMock()
        request.client.host = "192.168.1.1"

        # 应该不抛出异常
        result = await check_rate_limit(request, "login", mock_redis)
        assert result is None or result is True