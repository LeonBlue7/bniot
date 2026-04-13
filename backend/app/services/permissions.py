"""
权限系统服务
Phase 1.1 权限系统增强

提供基于角色的访问控制（RBAC）基础能力，预留扩展接口。
"""
from enum import Enum
from typing import Callable

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User
from app.services.auth import get_current_user


class Permission(str, Enum):
    """权限枚举定义"""
    # 设备权限
    DEVICE_READ = "device:read"
    DEVICE_CREATE = "device:create"
    DEVICE_UPDATE = "device:update"
    DEVICE_DELETE = "device:delete"
    DEVICE_CONTROL = "device:control"

    # 用户权限
    USER_READ = "user:read"
    USER_CREATE = "user:create"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"

    # 分区权限
    ZONE_READ = "zone:read"
    ZONE_CREATE = "zone:create"
    ZONE_UPDATE = "zone:update"
    ZONE_DELETE = "zone:delete"

    # 告警权限
    ALARM_READ = "alarm:read"
    ALARM_HANDLE = "alarm:handle"

    # 报表权限
    REPORT_READ = "report:read"
    REPORT_EXPORT = "report:export"

    # 设置权限
    SETTING_READ = "setting:read"
    SETTING_UPDATE = "setting:update"

    # 操作日志权限（仅管理员和操作员）
    LOG_READ = "log:read"

    # 备份权限
    BACKUP_READ = "backup:read"
    BACKUP_CREATE = "backup:create"
    BACKUP_DELETE = "backup:delete"
    BACKUP_VIEW = "backup:view"


# 角色权限映射配置
# 管理员：完整权限
# 操作员：设备、分区、告警操作权限
# 查看者：只读权限
ROLE_PERMISSIONS: dict[str, set[Permission]] = {
    "admin": {
        # 设备完整权限
        Permission.DEVICE_READ,
        Permission.DEVICE_CREATE,
        Permission.DEVICE_UPDATE,
        Permission.DEVICE_DELETE,
        Permission.DEVICE_CONTROL,
        # 用户完整权限（仅管理员）
        Permission.USER_READ,
        Permission.USER_CREATE,
        Permission.USER_UPDATE,
        Permission.USER_DELETE,
        # 分区完整权限
        Permission.ZONE_READ,
        Permission.ZONE_CREATE,
        Permission.ZONE_UPDATE,
        Permission.ZONE_DELETE,
        # 告警完整权限
        Permission.ALARM_READ,
        Permission.ALARM_HANDLE,
        # 报表完整权限
        Permission.REPORT_READ,
        Permission.REPORT_EXPORT,
        # 设置完整权限
        Permission.SETTING_READ,
        Permission.SETTING_UPDATE,
        # 操作日志权限
        Permission.LOG_READ,
        # 备份完整权限（仅管理员）
        Permission.BACKUP_READ,
        Permission.BACKUP_CREATE,
        Permission.BACKUP_DELETE,
        Permission.BACKUP_VIEW,
    },
    "operator": {
        # 设备操作权限
        Permission.DEVICE_READ,
        Permission.DEVICE_CREATE,
        Permission.DEVICE_UPDATE,
        Permission.DEVICE_DELETE,
        Permission.DEVICE_CONTROL,
        # 用户：操作员不能访问用户管理
        # 分区操作权限
        Permission.ZONE_READ,
        Permission.ZONE_CREATE,
        Permission.ZONE_UPDATE,
        # 告警处理权限
        Permission.ALARM_READ,
        Permission.ALARM_HANDLE,
        # 报表查看和导出
        Permission.REPORT_READ,
        Permission.REPORT_EXPORT,
        # 设置只读
        Permission.SETTING_READ,
        # 操作日志权限
        Permission.LOG_READ,
        # 备份查看权限
        Permission.BACKUP_READ,
        Permission.BACKUP_VIEW,
    },
    "viewer": {
        # 设备只读
        Permission.DEVICE_READ,
        # 用户：查看者不能访问用户管理
        # 分区只读
        Permission.ZONE_READ,
        # 告警只读
        Permission.ALARM_READ,
        # 报表只读
        Permission.REPORT_READ,
        # 设置只读
        Permission.SETTING_READ,
        # 操作日志：查看者无权访问
        # 备份：查看者无权访问
    },
}


class PermissionChecker:
    """权限检查器"""

    def __init__(self, user: User):
        self.user = user
        self._permissions = self._get_user_permissions()

    def _get_user_permissions(self) -> set[Permission]:
        """获取用户权限集合"""
        if not self.user.is_active:
            # 禁用用户无权限
            return set()

        # 根据角色获取权限
        role_permissions = ROLE_PERMISSIONS.get(self.user.role, set())
        return role_permissions

    def has_permission(self, permission: Permission) -> bool:
        """检查是否拥有指定权限"""
        return permission in self._permissions

    def has_any_permission(self, permissions: set[Permission]) -> bool:
        """检查是否拥有任意一个指定权限"""
        return any(p in self._permissions for p in permissions)

    def has_all_permissions(self, permissions: set[Permission]) -> bool:
        """检查是否拥有所有指定权限"""
        return all(p in self._permissions for p in permissions)


def require_permission(permission: Permission) -> Callable:
    """
    权限检查依赖装饰器

    用法:
        @router.post("", dependencies=[Depends(require_permission(Permission.DEVICE_CREATE)])
        async def create_device(...):
            ...

    或者作为函数参数:
        async def create_device(
            current_user: User = Depends(require_permission(Permission.DEVICE_CREATE))
        ):
            ...
    """
    async def permission_dependency(current_user: User = Depends(get_current_user)) -> User:
        checker = PermissionChecker(current_user)

        if not checker.has_permission(permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"权限不足，需要 {permission.value} 权限"
            )

        return current_user

    return permission_dependency


async def check_tenant_access(
    user: User,
    resource_id: int,
    resource_model,
    db: AsyncSession
) -> bool:
    """
    检查用户是否有权访问指定资源（租户隔离）

    Args:
        user: 当前用户
        resource_id: 资源ID
        resource_model: 资源模型类（Device, Zone, Alarm等）
        db: 数据库会话

    Returns:
        bool: 是否有权访问
    """
    # 查询资源
    result = await db.execute(
        select(resource_model).where(resource_model.id == resource_id)
    )
    resource = result.scalar_one_or_none()

    if not resource:
        return False

    # 检查租户ID是否匹配
    if hasattr(resource, 'tenant_id'):
        return resource.tenant_id == user.tenant_id

    return False


async def can_manage_user(
    admin: User,
    target_user: User,
    db: AsyncSession
) -> bool:
    """
    检查管理员是否可以管理目标用户

    Args:
        admin: 管理员用户
        target_user: 目标用户
        db: 数据库会话

    Returns:
        bool: 是否可以管理

    管理员不能:
        1. 管理其他租户的用户
        2. 操作禁用的管理员账号

    注意: "不能删除/禁用自己"的检查应在业务逻辑层面处理，
          此函数仅检查租户隔离和权限。
    """
    # 1. 检查是否同租户
    if admin.tenant_id != target_user.tenant_id:
        return False

    # 2. 检查管理员是否活跃
    if not admin.is_active:
        return False

    return True


def get_user_permissions(user: User) -> set[Permission]:
    """
    获取用户的权限集合（便捷函数）

    Args:
        user: 用户对象

    Returns:
        set[Permission]: 用户拥有的权限集合
    """
    checker = PermissionChecker(user)
    return checker._permissions


def check_role_permission(role: str, permission: Permission) -> bool:
    """
    检查角色是否拥有指定权限（静态检查）

    Args:
        role: 角色（admin, operator, viewer）
        permission: 权限

    Returns:
        bool: 该角色是否拥有该权限
    """
    role_permissions = ROLE_PERMISSIONS.get(role, set())
    return permission in role_permissions


def check_permission(role: str, permission_str: str) -> bool:
    """
    检查角色是否拥有指定权限（字符串形式）

    Args:
        role: 角色（admin, operator, viewer）
        permission_str: 权限字符串（如 "backup:create"）

    Returns:
        bool: 该角色是否拥有该权限
    """
    # 查找对应的权限枚举
    for perm in Permission:
        if perm.value == permission_str:
            return check_role_permission(role, perm)
    return False