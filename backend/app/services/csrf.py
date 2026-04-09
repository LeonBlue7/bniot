"""
CSRF 保护服务
实现 CSRF Token 的生成、存储和验证
"""
import secrets

import redis.asyncio as redis
from fastapi import Depends, HTTPException, Request, status

from app.models import User

# CSRF Token 过期时间（秒）
CSRF_EXPIRE_SECONDS = 3600  # 1 小时

# 豁免 CSRF 检查的路径
CSRF_EXEMPT_PATHS = {
    "/api/auth/login",
    "/api/auth/csrf-token",
    "/health",
    "/api/docs",
    "/api/redoc",
    "/api/openapi.json",
}

# 不需要 CSRF 检查的 HTTP 方法
CSRF_SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}

# CSRF Token 请求头名称
CSRF_HEADER_NAME = "X-CSRF-Token"


def generate_csrf_token() -> str:
    """
    生成安全的 CSRF Token

    使用 secrets 模块生成密码学安全的随机 Token。
    返回 URL 安全的 base64 编码字符串。

    Returns:
        str: 32 字节的随机 Token（base64 编码后约 43 字符）
    """
    # 生成 32 字节的随机数据，转换为 URL 安全的 base64 字符串
    return secrets.token_urlsafe(32)


def requires_csrf(method: str) -> bool:
    """
    判断请求方法是否需要 CSRF 保护

    Args:
        method: HTTP 方法

    Returns:
        bool: 是否需要 CSRF 保护
    """
    return method.upper() not in CSRF_SAFE_METHODS


def is_csrf_exempt(method: str, path: str) -> bool:
    """
    判断请求是否豁免 CSRF 检查

    Args:
        method: HTTP 方法
        path: 请求路径

    Returns:
        bool: 是否豁免 CSRF 检查
    """
    # 安全方法豁免
    if method.upper() in CSRF_SAFE_METHODS:
        return True

    # 豁免路径
    if path in CSRF_EXEMPT_PATHS:
        return True

    # 静态文件豁免
    if path.startswith("/static") or path.startswith("/api/static"):
        return True

    return False


async def store_csrf_token(
    token: str,
    user_id: str,
    redis_client: redis.Redis,
    expire_seconds: int = CSRF_EXPIRE_SECONDS
) -> bool:
    """
    存储 CSRF Token 到 Redis

    Args:
        token: CSRF Token
        user_id: 用户标识（用户名或用户 ID）
        redis_client: Redis 客户端
        expire_seconds: 过期时间（秒）

    Returns:
        bool: 存储是否成功
    """
    key = f"csrf:{user_id}:{token}"
    await redis_client.set(key, "1", ex=expire_seconds)
    return True


async def verify_csrf_token(
    token: str,
    user_id: str,
    redis_client: redis.Redis
) -> bool:
    """
    验证 CSRF Token

    验证成功后删除 Token（一次性使用）。

    Args:
        token: 待验证的 CSRF Token
        user_id: 用户标识
        redis_client: Redis 客户端

    Returns:
        bool: 验证是否成功
    """
    # 空值检查
    if not token or not user_id:
        return False

    key = f"csrf:{user_id}:{token}"

    # 检查 Token 是否存在
    stored = await redis_client.get(key)
    if not stored:
        return False

    # 验证成功后删除 Token（一次性使用）
    await redis_client.delete(key)

    return True


async def create_csrf_token_for_user(
    user_id: str,
    redis_client: redis.Redis
) -> str:
    """
    为用户创建新的 CSRF Token

    生成 Token 并存储到 Redis。

    Args:
        user_id: 用户标识
        redis_client: Redis 客户端

    Returns:
        str: 生成的 CSRF Token
    """
    token = generate_csrf_token()
    await store_csrf_token(token, user_id, redis_client)
    return token


async def get_redis_client(request: Request) -> redis.Redis:
    """
    获取 Redis 客户端依赖

    Args:
        request: FastAPI Request 对象

    Returns:
        redis.Redis: Redis 客户端
    """
    return request.app.state.redis_client


async def verify_csrf_dependency(
    request: Request,
    current_user: User | None = None
) -> None:
    """
    CSRF 验证依赖

    用于验证 POST/PUT/DELETE/PATCH 请求中的 CSRF Token。
    如果请求不需要 CSRF 保护或已豁免，则跳过验证。

    Args:
        request: FastAPI Request 对象
        current_user: 当前用户（可选）

    Raises:
        HTTPException: CSRF Token 无效或缺失
    """
    method = request.method
    path = request.url.path

    # 检查是否豁免 CSRF
    if is_csrf_exempt(method, path):
        return

    # 获取用户标识
    user_id = current_user.username if current_user else "anonymous"

    # 从请求头获取 CSRF Token
    csrf_token = request.headers.get(CSRF_HEADER_NAME)

    if not csrf_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="缺少 CSRF Token"
        )

    # 获取 Redis 客户端
    redis_client = await get_redis_client(request)

    # 验证 Token
    is_valid = await verify_csrf_token(csrf_token, user_id, redis_client)

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF Token 无效或已过期"
        )


def get_csrf_dependency():
    """
    获取 CSRF 验证依赖函数

    用于在路由中作为 Depends 参数使用。

    Returns:
        Callable: CSRF 验证依赖函数
    """
    return Depends(verify_csrf_dependency)
