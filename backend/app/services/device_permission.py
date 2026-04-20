"""
设备权限服务
实现基于分区授权的设备访问控制

权限规则：
- 系统管理员（admin）：可以看到租户内所有设备
- 观察员/操作员：只能看到所属租户关联分区内的设备
- 未分区的设备：仅管理员可见
"""
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Device, User


class DevicePermissionService:
    """设备权限服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_visible_devices(self, user: User) -> list[Device]:
        """
        获取用户可见的设备列表

        Args:
            user: 当前用户

        Returns:
            list[Device]: 用户可见的设备列表
        """
        from app.models.models import ZoneTenant

        # 禁用用户无权限
        if not user.is_active:
            return []

        # 管理员可以看到租户内所有设备
        if user.role == "admin":
            result = await self.db.execute(
                select(Device).where(Device.tenant_id == user.tenant_id)
            )
            return list(result.scalars().all())

        # 操作员和观察员：只能看到已授权分区内的设备
        # 查询用户租户被授权的分区ID列表
        authorized_zones_result = await self.db.execute(
            select(ZoneTenant.zone_id).where(
                ZoneTenant.tenant_id == user.tenant_id
            )
        )
        authorized_zone_ids = [row[0] for row in authorized_zones_result.all()]

        if not authorized_zone_ids:
            # 没有任何授权分区，返回空列表
            return []

        # 查询这些分区内的设备
        result = await self.db.execute(
            select(Device).where(
                and_(
                    Device.tenant_id == user.tenant_id,
                    Device.zone_id.in_(authorized_zone_ids)
                )
            )
        )
        return list(result.scalars().all())

    async def can_access_device(self, user: User, device_id: int) -> bool:
        """
        检查用户是否有权访问指定设备

        Args:
            user: 当前用户
            device_id: 设备ID（数据库主键）

        Returns:
            bool: 是否有权访问
        """
        from app.models.models import ZoneTenant

        # 禁用用户无权限
        if not user.is_active:
            return False

        # 查询设备
        result = await self.db.execute(
            select(Device).where(Device.id == device_id)
        )
        device = result.scalar_one_or_none()

        if not device:
            return False

        # 租户隔离：设备必须属于用户所在租户
        if device.tenant_id != user.tenant_id:
            return False

        # 管理员可以访问租户内任何设备
        if user.role == "admin":
            return True

        # 操作员和观察员：只能访问已授权分区内的设备
        if device.zone_id is None:
            # 未分区设备，非管理员无法访问
            return False

        # 检查分区是否授权给用户租户
        authorized_result = await self.db.execute(
            select(ZoneTenant).where(
                and_(
                    ZoneTenant.zone_id == device.zone_id,
                    ZoneTenant.tenant_id == user.tenant_id
                )
            )
        )
        return authorized_result.scalar_one_or_none() is not None