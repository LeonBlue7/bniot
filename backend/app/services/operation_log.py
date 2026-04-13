"""
操作日志服务
Phase 1.2 操作日志系统

提供操作日志记录和查询功能，支持审计追踪。
"""
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import OperationLog, User


class ActionType(str, Enum):
    """操作类型常量"""
    # 设备操作
    DEVICE_CREATE = "create_device"
    DEVICE_UPDATE = "update_device"
    DEVICE_DELETE = "delete_device"
    DEVICE_CONTROL = "control_device"
    DEVICE_BATCH_CONTROL = "batch_control_device"
    DEVICE_BATCH_DELETE = "batch_delete_device"

    # 用户操作
    USER_CREATE = "create_user"
    USER_UPDATE = "update_user"
    USER_DELETE = "delete_user"
    USER_STATUS_CHANGE = "change_user_status"

    # 分区操作
    ZONE_CREATE = "create_zone"
    ZONE_UPDATE = "update_zone"
    ZONE_DELETE = "delete_zone"

    # 告警操作
    ALARM_HANDLE = "handle_alarm"
    ALARM_BATCH_HANDLE = "batch_handle_alarm"

    # 参数设置
    PARAM_SET = "set_parameter"
    PARAM_BATCH_SET = "batch_set_parameter"

    # 登录相关
    LOGIN = "login"
    LOGIN_FAILED = "login_failed"
    LOGOUT = "logout"

    # 系统自动操作
    AUTO_OFFLINE = "auto_offline_detection"
    AUTO_ALARM = "auto_alarm_create"


class ResourceType(str, Enum):
    """资源类型常量"""
    DEVICE = "device"
    USER = "user"
    ZONE = "zone"
    ALARM = "alarm"
    SETTING = "setting"
    PARAMETER = "parameter"
    SESSION = "session"


class OperationLogService:
    """操作日志服务"""

    async def log(
        self,
        db: AsyncSession,
        user: User | None = None,
        tenant_id: int | None = None,
        action: str = "",
        resource_type: str = "",
        resource_id: str | None = None,
        details: dict[str, Any] | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None
    ) -> OperationLog:
        """
        记录操作日志

        Args:
            db: 数据库会话
            user: 操作用户（可为None，如系统自动操作）
            tenant_id: 租户ID（从用户获取或单独提供）
            action: 操作类型
            resource_type: 资源类型
            resource_id: 资源ID
            details: 操作详情（JSON）
            ip_address: IP地址
            user_agent: User Agent

        Returns:
            OperationLog: 创建的日志记录
        """
        # 如果提供了用户，从用户获取tenant_id
        if user:
            tenant_id = user.tenant_id
            user_id = user.id
        else:
            user_id = None

        # 创建日志记录
        log_entry = OperationLog(
            tenant_id=tenant_id,
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details or {},
            ip_address=ip_address,
            user_agent=user_agent,
            created_at=datetime.now(UTC)
        )

        db.add(log_entry)
        # 注意：不在这里commit，让调用者决定是否commit
        # 这样可以在同一个事务中记录日志和执行操作

        return log_entry

    async def query(
        self,
        db: AsyncSession,
        tenant_id: int,
        action: str | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        user_id: int | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        skip: int = 0,
        limit: int = 20
    ) -> list[OperationLog]:
        """
        查询操作日志

        Args:
            db: 数据库会话
            tenant_id: 租户ID（必须）
            action: 操作类型过滤
            resource_type: 资源类型过滤
            resource_id: 资源ID过滤
            user_id: 用户ID过滤
            start_date: 开始日期
            end_date: 结束日期
            skip: 跳过条数
            limit: 返回条数

        Returns:
            list[OperationLog]: 日志列表
        """
        query = select(OperationLog).where(
            OperationLog.tenant_id == tenant_id
        )

        # 添加过滤条件
        if action:
            query = query.where(OperationLog.action == action)
        if resource_type:
            query = query.where(OperationLog.resource_type == resource_type)
        if resource_id:
            query = query.where(OperationLog.resource_id == resource_id)
        if user_id:
            query = query.where(OperationLog.user_id == user_id)
        if start_date:
            query = query.where(OperationLog.created_at >= start_date)
        if end_date:
            query = query.where(OperationLog.created_at <= end_date)

        # 排序和分页
        query = query.order_by(OperationLog.created_at.desc())
        query = query.offset(skip).limit(limit)

        result = await db.execute(query)
        return result.scalars().all()

    async def count(
        self,
        db: AsyncSession,
        tenant_id: int,
        action: str | None = None,
        resource_type: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None
    ) -> int:
        """
        统计日志数量

        Args:
            db: 数据库会话
            tenant_id: 租户ID
            action: 操作类型过滤
            resource_type: 资源类型过滤
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            int: 日志数量
        """
        from sqlalchemy import func

        query = select(func.count(OperationLog.id)).where(
            OperationLog.tenant_id == tenant_id
        )

        if action:
            query = query.where(OperationLog.action == action)
        if resource_type:
            query = query.where(OperationLog.resource_type == resource_type)
        if start_date:
            query = query.where(OperationLog.created_at >= start_date)
        if end_date:
            query = query.where(OperationLog.created_at <= end_date)

        result = await db.execute(query)
        return result.scalar() or 0


# 便捷函数：记录操作日志
async def log_operation(
    db: AsyncSession,
    user: User | None = None,
    action: str = "",
    resource_type: str = "",
    resource_id: str | None = None,
    details: dict[str, Any] | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None
) -> OperationLog:
    """
    便捷函数：记录操作日志

    Usage:
        await log_operation(
            db,
            current_user,
            ActionType.DEVICE_CREATE,
            ResourceType.DEVICE,
            device.device_id,
            {"name": device.name}
        )
    """
    service = OperationLogService()
    return await service.log(
        db,
        user=user,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
        ip_address=ip_address,
        user_agent=user_agent
    )