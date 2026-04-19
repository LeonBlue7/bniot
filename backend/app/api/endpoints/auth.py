"""
认证 API 端点
"""
import redis.asyncio as redis
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.models import User
from app.schemas import Token, UserResponse, PasswordChangeRequest
from app.services.auth import create_access_token, get_current_user, verify_password, get_password_hash
from app.services.csrf import create_csrf_token_for_user
from app.services.rate_limiter import RateLimiter

router = APIRouter()


# Redis 客户端依赖
async def get_redis(request: Request) -> redis.Redis:
    """获取 Redis 客户端"""
    # 从应用状态获取 Redis 客户端
    return request.app.state.redis_client


async def get_current_user_optional(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> User | None:
    """获取当前用户（可选，不抛出异常）"""
    from fastapi.security import OAuth2PasswordBearer

    oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)
    token = await oauth2_scheme_optional(request)

    if not token:
        return None

    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        username: str = payload.get("sub")
        tenant_id: int = payload.get("tenant_id")
        if username is None or tenant_id is None:
            return None

        result = await db.execute(
            select(User).where(
                User.username == username,
                User.tenant_id == tenant_id
            )
        )
        user = result.scalar_one_or_none()
        if user and user.is_active:
            return user
        return None
    except JWTError:
        return None


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


@router.get("/csrf-token")
async def get_csrf_token(
    request: Request,
    redis_client: redis.Redis = Depends(get_redis),
    current_user: User | None = Depends(get_current_user_optional)
):
    """
    获取 CSRF Token

    未认证用户也可以获取 CSRF Token（用于后续登录后的请求）。
    已认证用户的 Token 与用户身份绑定。
    """
    if current_user:
        # 已认证用户：Token 与用户绑定
        user_id = current_user.username
    else:
        # 未认证用户：使用会话标识（如果有的话）
        # 从请求中获取或生成会话标识
        user_id = request.headers.get("X-Session-ID", "anonymous")

    # 生成并存储 CSRF Token
    csrf_token = await create_csrf_token_for_user(user_id, redis_client)

    return {"csrf_token": csrf_token}


@router.post("/change-password")
async def change_password(
    data: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """修改密码"""
    # 验证当前密码
    if not verify_password(data.old_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="当前密码错误"
        )

    # 更新密码
    current_user.password_hash = get_password_hash(data.new_password)
    await db.commit()

    return {"message": "密码修改成功"}
