"""
微信小程序 API 端点
提供微信登录功能
"""
import logging
import random
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models import User
from app.schemas import (
    WechatBindRequest,
    WechatBindResponse,
    WechatLoginRequest,
    WechatLoginResponse,
    WechatUnbindResponse,
    UserResponse,
)
from app.services.auth import create_access_token, get_current_user, get_password_hash
from app.services.wechat import get_wechat_openid_async

router = APIRouter()
logger = logging.getLogger(__name__)


# 默认租户 ID（微信用户首次登录时使用的租户）
# 注意：实际生产环境中应该根据业务需求调整
DEFAULT_WECHAT_TENANT_ID = 1


@router.post("/login", response_model=WechatLoginResponse)
async def wechat_login(
    request: WechatLoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    微信小程序登录

    流程:
    1. 使用 code 调用微信 API 获取 openid
    2. 根据 openid 查找用户
    3. 如果用户存在，返回 token
    4. 如果用户不存在，自动创建新用户并返回 token

    Args:
        request: 包含微信 code 的请求

    Returns:
        WechatLoginResponse: 包含 token 和用户信息
    """
    # 获取 openid
    wechat_data = await get_wechat_openid_async(request.code)

    if not wechat_data or "openid" not in wechat_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="微信登录失败，无效的 code 或网络错误"
        )

    openid = wechat_data["openid"]

    # 查找已绑定该 openid 的用户
    result = await db.execute(
        select(User).where(User.wechat_openid == openid)
    )
    user = result.scalar_one_or_none()

    is_new_user = False

    if user:
        # 用户已存在，检查是否激活
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户已禁用"
            )

        # 更新最后登录时间
        user.last_login_at = datetime.now(UTC)
        await db.commit()
        await db.refresh(user)

        logger.info(f"WeChat user login: {user.username}, openid: {openid[:8]}***")
    else:
        # 新用户，自动创建
        # 生成用户名（使用 openid 前缀）
        username = f"wechat_{openid[:12]}"

        # 检查用户名是否已存在（防止冲突）
        existing = await db.execute(
            select(User).where(User.username == username)
        )
        if existing.scalar_one_or_none():
            # 如果冲突，添加随机后缀
            username = f"wechat_{openid[:8]}_{random.randint(1000, 9999)}"

        # 创建新用户
        # 微信专用用户无密码，只能通过微信登录
        user = User(
            tenant_id=DEFAULT_WECHAT_TENANT_ID,
            username=username,
            password_hash=get_password_hash(""),  # 空密码，仅支持微信登录
            role="viewer",
            is_active=True,
            wechat_openid=openid,
            last_login_at=datetime.now(UTC)
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

        is_new_user = True
        logger.info(f"New WeChat user created: {user.username}, openid: {openid[:8]}***")

    # 创建 JWT token
    access_token = create_access_token(
        data={"sub": user.username, "tenant_id": user.tenant_id}
    )

    return WechatLoginResponse(
        access_token=access_token,
        token_type="bearer",
        is_new_user=is_new_user,
        user=UserResponse.model_validate(user)
    )