"""
认证 API 端点
"""
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import redis.asyncio as redis

from app.core.database import get_db
from app.core.config import settings
from app.models import User
from app.schemas import Token, LoginRequest, UserResponse
from app.services.auth import (
    verify_password,
    create_access_token,
    get_password_hash,
    get_current_user
)
from app.services.rate_limiter import RateLimiter, check_rate_limit

router = APIRouter()


# Redis 客户端依赖
async def get_redis(request: Request) -> redis.Redis:
    """获取 Redis 客户端"""
    # 从应用状态获取 Redis 客户端
    return request.app.state.redis_client


@router.post("/login", response_model=Token)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis)
):
    """用户登录（带速率限制）"""
    # 获取客户端 IP
    client_ip = request.client.host if request.client else "unknown"

    # 创建速率限制器
    rate_limiter = RateLimiter(redis_client, max_attempts=5, window_seconds=300)

    # 检查 IP 和用户名的速率限制
    ip_allowed = await rate_limiter.is_allowed(client_ip, "login")
    user_allowed = await rate_limiter.is_allowed(client_ip, "login", form_data.username)

    if not ip_allowed or not user_allowed:
        remaining_info = await rate_limiter.get_remaining_attempts(client_ip, "login", form_data.username)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"登录尝试过于频繁，请 {remaining_info['ttl']} 秒后再试",
            headers={"Retry-After": str(remaining_info['ttl'])}
        )

    # 查找用户
    result = await db.execute(
        select(User).where(User.username == form_data.username)
    )
    user = result.scalar_one_or_none()

    # 验证用户和密码
    if not user or not verify_password(form_data.password, user.password_hash):
        # 记录失败尝试
        await rate_limiter.record_failed_attempt(client_ip, "login")
        await rate_limiter.record_failed_attempt(client_ip, "login", form_data.username)

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(status_code=400, detail="用户已禁用")

    # 登录成功，清除失败记录
    await rate_limiter.clear_attempts(client_ip, "login")
    await rate_limiter.clear_attempts(client_ip, "login", form_data.username)

    # 创建令牌
    access_token = create_access_token(
        data={"sub": user.username, "tenant_id": user.tenant_id}
    )

    return Token(access_token=access_token, token_type="bearer")


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """获取当前用户信息"""
    return current_user