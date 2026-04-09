"""
用户管理 API 端点
仅管理员可访问
"""
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models import User
from app.schemas import Message, UserCreateAPI, UserResponse, UserStatusUpdate, UserUpdate
from app.services.auth import check_admin_role, get_current_user, get_password_hash

router = APIRouter()
logger = logging.getLogger(__name__)


def require_admin(user: User = Depends(get_current_user)) -> User:
    """要求管理员权限"""
    if not check_admin_role(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    return user


@router.get("", response_model=list[UserResponse])
async def list_users(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """获取用户列表（仅管理员）"""
    result = await db.execute(
        select(User).where(User.tenant_id == current_user.tenant_id)
    )
    return result.scalars().all()


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_in: UserCreateAPI,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
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
    current_user: User = Depends(require_admin)
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
    current_user: User = Depends(require_admin)
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
    current_user: User = Depends(require_admin)
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

    # 不能删除自己
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能删除自己"
        )

    await db.delete(user)
    await db.commit()

    logger.info(f"用户 {user.username} 由 {current_user.username} 删除")
    return Message(message="用户已删除")