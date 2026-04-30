"""
用户管理 API 端点
使用新的权限系统进行访问控制

注意：特定路径的路由（如 /bind-wechat, /unbind-wechat）必须在参数化路由（如 /{user_id}）之前定义
"""
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models import User
from app.schemas import Message, UserCreateAPI, UserResponse, UserStatusUpdate, UserUpdate, WechatBindRequest, WechatBindResponse, WechatUnbindResponse
from app.services.auth import get_current_user, get_password_hash
from app.services.permissions import can_manage_user, Permission, require_permission
from app.services.wechat import get_wechat_openid_async

router = APIRouter()
logger = logging.getLogger(__name__)


# ============ 特定路径路由（必须在参数化路由之前） ============

@router.post("/bind-wechat", response_model=WechatBindResponse)
async def bind_wechat(
    request: WechatBindRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    绑定微信账号

    将当前用户的账号与微信 openid 绑定，绑定后可以通过微信登录
    """
    # 检查用户是否已绑定微信
    if current_user.wechat_openid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该用户已绑定微信，请先解绑后再重新绑定"
        )

    # 获取 openid
    wechat_data = await get_wechat_openid_async(request.code)

    if not wechat_data or "openid" not in wechat_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="获取微信 openid 失败，无效的 code 或网络错误"
        )

    openid = wechat_data["openid"]

    # 检查 openid 是否已被其他用户绑定
    result = await db.execute(
        select(User).where(User.wechat_openid == openid)
    )
    existing_user = result.scalar_one_or_none()

    if existing_user and existing_user.id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该微信账号已被其他用户绑定"
        )

    # 绑定 openid
    current_user.wechat_openid = openid
    await db.commit()
    await db.refresh(current_user)

    logger.info(f"User {current_user.username} bound WeChat openid: {openid}")

    return WechatBindResponse(
        success=True,
        message="微信绑定成功",
        openid=openid
    )


@router.delete("/unbind-wechat", response_model=WechatUnbindResponse)
async def unbind_wechat(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    解绑微信账号

    移除当前用户的微信 openid 绑定，解绑后无法通过微信登录
    """
    # 检查用户是否已绑定微信
    if not current_user.wechat_openid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该用户未绑定微信"
        )

    # 解绑
    old_openid = current_user.wechat_openid
    current_user.wechat_openid = None
    await db.commit()
    await db.refresh(current_user)

    logger.info(f"User {current_user.username} unbound WeChat openid: {old_openid}")

    return WechatUnbindResponse(
        success=True,
        message="微信解绑成功"
    )


# ============ 参数化路由 ============

@router.get("", response_model=list[UserResponse])
async def list_users(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.USER_READ))
):
    """获取用户列表"""
    result = await db.execute(
        select(User).where(User.tenant_id == current_user.tenant_id)
    )
    return result.scalars().all()


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_in: UserCreateAPI,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.USER_CREATE))
):
    """创建用户（仅管理员）"""
    # 检查用户名是否已存在
    result = await db.execute(
        select(User).where(User.username == user_in.username)
    )
    existing_user = result.scalar_one_or_none()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )

    # 验证角色
    valid_roles = ["admin", "operator", "viewer"]
    if user_in.role not in valid_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无效角色，有效角色为: {', '.join(valid_roles)}"
        )

    # 创建用户，tenant_id 从当前用户获取
    user = User(
        tenant_id=current_user.tenant_id,
        username=user_in.username,
        password_hash=get_password_hash(user_in.password),
        role=user_in.role,
        is_active=True
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    logger.info(
        f"用户 {user.username} 由 {current_user.username} 创建，"
        f"角色: {user.role}, 租户: {user.tenant_id}"
    )
    return user


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_in: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.USER_UPDATE))
):
    """更新用户（仅管理员）"""
    result = await db.execute(
        select(User).where(
            User.id == user_id,
            User.tenant_id == current_user.tenant_id
        )
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    # 检查是否有权限管理该用户
    if not await can_manage_user(current_user, user, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权管理该用户"
        )

    # 验证角色
    if user_in.role:
        valid_roles = ["admin", "operator", "viewer"]
        if user_in.role not in valid_roles:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"无效角色，有效角色为: {', '.join(valid_roles)}"
            )

    update_data = user_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)

    await db.commit()
    await db.refresh(user)

    logger.info(
        f"用户 {user.username} 由 {current_user.username} 更新，"
        f"修改字段: {list(update_data.keys())}"
    )
    return user


@router.patch("/{user_id}/status", response_model=UserResponse)
async def update_user_status(
    user_id: int,
    status_in: UserStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.USER_UPDATE))
):
    """启用/禁用用户（仅管理员）"""
    result = await db.execute(
        select(User).where(
            User.id == user_id,
            User.tenant_id == current_user.tenant_id
        )
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    # 检查是否有权限管理该用户
    if not await can_manage_user(current_user, user, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权管理该用户"
        )

    # 不能禁用自己
    if user.id == current_user.id and not status_in.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能禁用自己"
        )

    user.is_active = status_in.is_active
    await db.commit()
    await db.refresh(user)

    logger.info(
        f"用户 {user.username} 状态由 {current_user.username} 更改为 "
        f"{'启用' if status_in.is_active else '禁用'}"
    )
    return user


@router.delete("/{user_id}", response_model=Message)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.USER_DELETE))
):
    """删除用户（仅管理员）"""
    result = await db.execute(
        select(User).where(
            User.id == user_id,
            User.tenant_id == current_user.tenant_id
        )
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    # 检查是否有权限管理该用户
    if not await can_manage_user(current_user, user, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权管理该用户"
        )

    await db.delete(user)
    await db.commit()

    logger.info(f"用户 {user.username} 由 {current_user.username} 删除")
    return Message(message="用户已删除")