"""
速率限制服务
用于防止暴力破解攻击
"""

import redis.asyncio as redis
from fastapi import HTTPException, Request, status
from loguru import logger


class RateLimiter:
    """
    基于 Redis 的速率限制器

    使用滑动窗口算法限制请求频率
    """

    def __init__(
        self,
        redis_client: redis.Redis,
        max_attempts: int = 5,
        window_seconds: int = 300,  # 5分钟
    ):
        """
        初始化速率限制器

        Args:
            redis_client: Redis 客户端
            max_attempts: 最大尝试次数
            window_seconds: 时间窗口（秒）
        """
        self.redis = redis_client
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds

    def _get_key(self, ip: str, action: str, identifier: str | None = None) -> str:
        """
        生成 Redis 键

        Args:
            ip: 客户端IP
            action: 操作类型（如 login）
            identifier: 可选标识符（如用户名）

        Returns:
            Redis 键
        """
        if identifier:
            return f"rate_limit:{action}:{identifier}:{ip}"
        return f"rate_limit:{action}:{ip}"

    async def is_allowed(self, ip: str, action: str, identifier: str | None = None) -> bool:
        """
        检查是否允许请求

        Args:
            ip: 客户端IP
            action: 操作类型
            identifier: 可选标识符

        Returns:
            是否允许请求
        """
        try:
            key = self._get_key(ip, action, identifier)
            current = await self.redis.get(key)

            if current is None:
                return True

            attempts = int(current)
            return attempts < self.max_attempts

        except Exception as e:
            logger.error(f"检查速率限制失败: {e}")
            # 出错时允许请求，避免影响正常用户
            return True

    async def record_failed_attempt(
        self, ip: str, action: str, identifier: str | None = None
    ) -> int:
        """
        记录失败尝试

        Args:
            ip: 客户端IP
            action: 操作类型
            identifier: 可选标识符

        Returns:
            当前失败次数
        """
        try:
            key = self._get_key(ip, action, identifier)

            # 增加计数
            attempts = await self.redis.incr(key)

            # 如果是第一次设置，设置过期时间
            if attempts == 1:
                await self.redis.expire(key, self.window_seconds)

            logger.warning(f"记录失败尝试: {key}, 次数: {attempts}")
            return attempts

        except Exception as e:
            logger.error(f"记录失败尝试失败: {e}")
            return 0

    async def clear_attempts(self, ip: str, action: str, identifier: str | None = None) -> None:
        """
        清除失败记录（登录成功后调用）

        Args:
            ip: 客户端IP
            action: 操作类型
            identifier: 可选标识符
        """
        try:
            key = self._get_key(ip, action, identifier)
            await self.redis.delete(key)
            logger.debug(f"清除失败记录: {key}")

        except Exception as e:
            logger.error(f"清除失败记录失败: {e}")

    async def get_remaining_attempts(
        self, ip: str, action: str, identifier: str | None = None
    ) -> dict:
        """
        获取剩余尝试次数

        Args:
            ip: 客户端IP
            action: 操作类型
            identifier: 可选标识符

        Returns:
            包含尝试次数、剩余次数和TTL的字典
        """
        try:
            key = self._get_key(ip, action, identifier)

            current = await self.redis.get(key)
            ttl = await self.redis.ttl(key)

            attempts = int(current) if current else 0
            remaining = max(0, self.max_attempts - attempts)

            return {
                "attempts": attempts,
                "remaining": remaining,
                "ttl": ttl if ttl > 0 else 0,
            }

        except Exception as e:
            logger.error(f"获取剩余尝试次数失败: {e}")
            return {
                "attempts": 0,
                "remaining": self.max_attempts,
                "ttl": 0,
            }


async def check_rate_limit(
    request: Request,
    action: str,
    redis_client: redis.Redis,
    identifier: str | None = None,
    max_attempts: int = 5,
) -> None:
    """
    检查速率限制的 FastAPI 依赖

    Args:
        request: FastAPI 请求对象
        action: 操作类型
        redis_client: Redis 客户端
        identifier: 可选标识符
        max_attempts: 最大尝试次数

    Raises:
        HTTPException: 超过速率限制时抛出 429 错误
    """
    # 获取客户端 IP
    ip = request.client.host if request.client else "unknown"

    limiter = RateLimiter(redis_client, max_attempts=max_attempts)

    # 检查是否允许
    allowed = await limiter.is_allowed(ip, action, identifier)

    if not allowed:
        # 获取剩余时间
        remaining_info = await limiter.get_remaining_attempts(ip, action, identifier)
        ttl = remaining_info["ttl"]

        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"操作过于频繁，请 {ttl} 秒后再试",
            headers={"Retry-After": str(ttl)},
        )
