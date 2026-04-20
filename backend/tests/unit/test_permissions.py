"""
测试权限系统增强
Phase 1.1 权限系统增强
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, UTC

from fastapi import HTTPException
from sqlalchemy import select


class TestRoleBasedAccessControl:
    """测试基于角色的访问控制"""

    @pytest.fixture
    def admin_user(self):
        """创建管理员用户"""
        from app.models import User
        user = User(
            id=1,
            tenant_id=1,
            username="admin",
            password_hash="hash",
            role="admin",
            is_active=True
        )
        return user

    @pytest.fixture
    def operator_user(self):
        """创建操作员用户"""
        from app.models import User
        user = User(
            id=2,
            tenant_id=1,
            username="operator",
            password_hash="hash",
            role="operator",
            is_active=True
        )
        return user

    @pytest.fixture
    def viewer_user(self):
        """创建查看者用户"""
        from app.models import User
        user = User(
            id=3,
            tenant_id=1,
            username="viewer",
            password_hash="hash",
            role="viewer",
            is_active=True
        )
        return user

    def test_admin_has_full_permissions(self, admin_user):
        """测试管理员拥有完整权限"""
        from app.services.permissions import PermissionChecker, Permission

        checker = PermissionChecker(admin_user)

        # 管理员应该拥有所有权限
        assert checker.has_permission(Permission.DEVICE_CREATE) == True
        assert checker.has_permission(Permission.DEVICE_UPDATE) == True
        assert checker.has_permission(Permission.DEVICE_DELETE) == True
        assert checker.has_permission(Permission.USER_CREATE) == True
        assert checker.has_permission(Permission.USER_UPDATE) == True
        assert checker.has_permission(Permission.USER_DELETE) == True
        assert checker.has_permission(Permission.ZONE_CREATE) == True
        assert checker.has_permission(Permission.ZONE_DELETE) == True
        assert checker.has_permission(Permission.SETTING_UPDATE) == True

    def test_operator_has_device_permissions(self, operator_user):
        """测试操作员拥有设备操作权限"""
        from app.services.permissions import PermissionChecker, Permission

        checker = PermissionChecker(operator_user)

        # 操作员可以操作设备
        assert checker.has_permission(Permission.DEVICE_CREATE) == True
        assert checker.has_permission(Permission.DEVICE_UPDATE) == True
        assert checker.has_permission(Permission.DEVICE_DELETE) == True
        assert checker.has_permission(Permission.DEVICE_CONTROL) == True

        # 操作员只能查看分区，不能增删改（只有管理员才能管理分区）
        assert checker.has_permission(Permission.ZONE_READ) == True
        assert checker.has_permission(Permission.ZONE_CREATE) == False
        assert checker.has_permission(Permission.ZONE_UPDATE) == False

        # 操作员不能访问用户管理（仅管理员）
        assert checker.has_permission(Permission.USER_READ) == False
        assert checker.has_permission(Permission.USER_CREATE) == False
        assert checker.has_permission(Permission.USER_UPDATE) == False
        assert checker.has_permission(Permission.USER_DELETE) == False

        # 操作员不能修改系统设置
        assert checker.has_permission(Permission.SETTING_UPDATE) == False

    def test_viewer_has_read_only_permissions(self, viewer_user):
        """测试查看者只有只读权限"""
        from app.services.permissions import PermissionChecker, Permission

        checker = PermissionChecker(viewer_user)

        # 查看者只能查看
        assert checker.has_permission(Permission.DEVICE_READ) == True
        assert checker.has_permission(Permission.ZONE_READ) == True
        assert checker.has_permission(Permission.ALARM_READ) == True
        assert checker.has_permission(Permission.REPORT_READ) == True

        # 查看者不能修改任何内容
        assert checker.has_permission(Permission.DEVICE_CREATE) == False
        assert checker.has_permission(Permission.DEVICE_UPDATE) == False
        assert checker.has_permission(Permission.DEVICE_DELETE) == False

        # 查看者不能访问用户管理（仅管理员）
        assert checker.has_permission(Permission.USER_READ) == False
        assert checker.has_permission(Permission.USER_CREATE) == False

        # 查看者不能创建分区
        assert checker.has_permission(Permission.ZONE_CREATE) == False

    def test_inactive_user_no_permissions(self):
        """测试禁用用户无权限"""
        from app.services.permissions import PermissionChecker, Permission
        from app.models import User

        user = User(
            id=4,
            tenant_id=1,
            username="inactive",
            password_hash="hash",
            role="admin",
            is_active=False
        )

        checker = PermissionChecker(user)

        # 禁用用户即使角色是管理员也无权限
        assert checker.has_permission(Permission.DEVICE_READ) == False
        assert checker.has_permission(Permission.DEVICE_CREATE) == False


class TestPermissionDecorator:
    """测试权限装饰器"""

    @pytest.mark.asyncio
    async def test_require_permission_allows_authorized(self):
        """测试权限装饰器允许授权用户"""
        from app.services.permissions import require_permission, Permission
        from app.models import User

        # 模拟用户
        user = User(
            id=1,
            tenant_id=1,
            username="admin",
            password_hash="hash",
            role="admin",
            is_active=True
        )

        # 应该不抛出异常
        dependency = require_permission(Permission.DEVICE_CREATE)
        result = await dependency(user)
        assert result == user

    @pytest.mark.asyncio
    async def test_require_permission_denies_unauthorized(self):
        """测试权限装饰器拒绝未授权用户"""
        from app.services.permissions import require_permission, Permission
        from app.models import User

        # 模拟查看者用户
        user = User(
            id=1,
            tenant_id=1,
            username="viewer",
            password_hash="hash",
            role="viewer",
            is_active=True
        )

        # 应该抛出403异常
        dependency = require_permission(Permission.DEVICE_CREATE)
        with pytest.raises(HTTPException) as exc_info:
            await dependency(user)

        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_require_permission_denies_inactive_user(self):
        """测试权限装饰器拒绝禁用用户"""
        from app.services.permissions import require_permission, Permission
        from app.models import User

        # 模拟禁用的管理员
        user = User(
            id=1,
            tenant_id=1,
            username="admin",
            password_hash="hash",
            role="admin",
            is_active=False
        )

        # 应该抛出403异常
        dependency = require_permission(Permission.DEVICE_READ)
        with pytest.raises(HTTPException) as exc_info:
            await dependency(user)

        assert exc_info.value.status_code == 403


class TestTenantIsolation:
    """测试租户隔离"""

    @pytest.mark.asyncio
    async def test_user_cannot_access_other_tenant_device(self, db_session):
        """测试用户不能访问其他租户的设备"""
        from app.models import Tenant, User, Device
        from app.services.permissions import check_tenant_access

        # 创建两个租户
        tenant1 = Tenant(name="租户1", code="tenant1")
        tenant2 = Tenant(name="租户2", code="tenant2")
        db_session.add_all([tenant1, tenant2])
        await db_session.commit()

        # 创建用户
        user1 = User(
            tenant_id=tenant1.id,
            username="user1",
            password_hash="hash",
            role="admin"
        )
        db_session.add(user1)
        await db_session.commit()

        # 创建属于租户2的设备
        device2 = Device(
            tenant_id=tenant2.id,
            device_id="IMEI002",
            name="设备2"
        )
        db_session.add(device2)
        await db_session.commit()

        # 用户1尝试访问设备2，应该失败
        has_access = await check_tenant_access(user1, device2.id, Device, db_session)
        assert has_access == False

    @pytest.mark.asyncio
    async def test_user_can_access_own_tenant_device(self, db_session):
        """测试用户可以访问自己租户的设备"""
        from app.models import Tenant, User, Device
        from app.services.permissions import check_tenant_access

        # 创建租户
        tenant = Tenant(name="租户", code="tenant")
        db_session.add(tenant)
        await db_session.commit()

        # 创建用户和设备
        user = User(
            tenant_id=tenant.id,
            username="user",
            password_hash="hash",
            role="operator"
        )
        device = Device(
            tenant_id=tenant.id,
            device_id="IMEI001",
            name="设备"
        )
        db_session.add_all([user, device])
        await db_session.commit()

        # 用户访问自己租户的设备，应该成功
        has_access = await check_tenant_access(user, device.id, Device, db_session)
        assert has_access == True


class TestDevicePermissionIntegration:
    """测试设备权限集成"""

    @pytest.mark.asyncio
    async def test_viewer_cannot_create_device(self, db_session):
        """测试查看者不能创建设备"""
        from app.models import Tenant, User, Device
        from app.services.permissions import require_permission, Permission

        # 创建租户和查看者用户
        tenant = Tenant(name="租户", code="test_create")
        db_session.add(tenant)
        await db_session.commit()

        viewer = User(
            tenant_id=tenant.id,
            username="viewer",
            password_hash="hash",
            role="viewer"
        )
        db_session.add(viewer)
        await db_session.commit()

        # 尝试创建设备应该失败
        dependency = require_permission(Permission.DEVICE_CREATE)
        with pytest.raises(HTTPException) as exc_info:
            await dependency(viewer)

        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_operator_can_create_device(self, db_session):
        """测试操作员可以创建设备"""
        from app.models import Tenant, User
        from app.services.permissions import require_permission, Permission

        # 创建租户和操作员用户
        tenant = Tenant(name="租户", code="test_op_create")
        db_session.add(tenant)
        await db_session.commit()

        operator = User(
            tenant_id=tenant.id,
            username="operator",
            password_hash="hash",
            role="operator"
        )
        db_session.add(operator)
        await db_session.commit()

        # 操作员应该可以创建设备
        dependency = require_permission(Permission.DEVICE_CREATE)
        result = await dependency(operator)
        assert result == operator


class TestUserManagementPermissions:
    """测试用户管理权限"""

    @pytest.mark.asyncio
    async def test_only_admin_can_create_user(self, db_session):
        """测试只有管理员可以创建用户"""
        from app.models import Tenant, User
        from app.services.permissions import require_permission, Permission

        # 创建租户
        tenant = Tenant(name="租户", code="test_user_mgmt")
        db_session.add(tenant)
        await db_session.commit()

        # 操作员尝试创建用户
        operator = User(
            tenant_id=tenant.id,
            username="operator",
            password_hash="hash",
            role="operator"
        )
        db_session.add(operator)
        await db_session.commit()

        # 操作员不应该有用户创建权限
        dependency = require_permission(Permission.USER_CREATE)
        with pytest.raises(HTTPException) as exc_info:
            await dependency(operator)

        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_admin_can_manage_any_user_in_tenant(self, db_session):
        """测试管理员可以管理同租户任何用户"""
        from app.models import Tenant, User
        from app.services.permissions import can_manage_user

        # 创建租户
        tenant = Tenant(name="租户", code="test_manage")
        db_session.add(tenant)
        await db_session.commit()

        # 创建管理员和普通用户
        admin = User(
            tenant_id=tenant.id,
            username="admin",
            password_hash="hash",
            role="admin"
        )
        viewer = User(
            tenant_id=tenant.id,
            username="viewer",
            password_hash="hash",
            role="viewer"
        )
        db_session.add_all([admin, viewer])
        await db_session.commit()

        # 管理员可以管理同租户用户
        assert await can_manage_user(admin, viewer, db_session) == True

    @pytest.mark.asyncio
    async def test_admin_cannot_manage_other_tenant_user(self, db_session):
        """测试管理员不能管理其他租户用户"""
        from app.models import Tenant, User
        from app.services.permissions import can_manage_user

        # 创建两个租户
        tenant1 = Tenant(name="租户1", code="tenant1_manage")
        tenant2 = Tenant(name="租户2", code="tenant2_manage")
        db_session.add_all([tenant1, tenant2])
        await db_session.commit()

        # 创建管理员
        admin1 = User(
            tenant_id=tenant1.id,
            username="admin1",
            password_hash="hash",
            role="admin"
        )
        viewer2 = User(
            tenant_id=tenant2.id,
            username="viewer2",
            password_hash="hash",
            role="viewer"
        )
        db_session.add_all([admin1, viewer2])
        await db_session.commit()

        # 管理员1不能管理租户2的用户
        assert await can_manage_user(admin1, viewer2, db_session) == False

    @pytest.mark.asyncio
    async def test_admin_cannot_delete_self(self, db_session):
        """测试管理员不能删除自己 - can_manage_user返回True，业务逻辑层面检查"""
        from app.models import Tenant, User
        from app.services.permissions import can_manage_user

        # 创建租户
        tenant = Tenant(name="租户", code="test_self_delete")
        db_session.add(tenant)
        await db_session.commit()

        # 创建管理员
        admin = User(
            tenant_id=tenant.id,
            username="admin",
            password_hash="hash",
            role="admin"
        )
        db_session.add(admin)
        await db_session.commit()

        # can_manage_user 只检查租户隔离，不检查"自己"
        # "不能删除自己"的检查应在业务逻辑层面（如 users.py 的 delete_user）
        assert await can_manage_user(admin, admin, db_session) == True


class TestPermissionEnum:
    """测试权限枚举定义"""

    def test_permission_enum_exists(self):
        """测试权限枚举存在"""
        from app.services.permissions import Permission

        # 设备权限
        assert hasattr(Permission, 'DEVICE_READ')
        assert hasattr(Permission, 'DEVICE_CREATE')
        assert hasattr(Permission, 'DEVICE_UPDATE')
        assert hasattr(Permission, 'DEVICE_DELETE')
        assert hasattr(Permission, 'DEVICE_CONTROL')

        # 用户权限
        assert hasattr(Permission, 'USER_READ')
        assert hasattr(Permission, 'USER_CREATE')
        assert hasattr(Permission, 'USER_UPDATE')
        assert hasattr(Permission, 'USER_DELETE')

        # 分区权限
        assert hasattr(Permission, 'ZONE_READ')
        assert hasattr(Permission, 'ZONE_CREATE')
        assert hasattr(Permission, 'ZONE_UPDATE')
        assert hasattr(Permission, 'ZONE_DELETE')

        # 告警权限
        assert hasattr(Permission, 'ALARM_READ')
        assert hasattr(Permission, 'ALARM_HANDLE')

        # 报表权限
        assert hasattr(Permission, 'REPORT_READ')
        assert hasattr(Permission, 'REPORT_EXPORT')

        # 设置权限
        assert hasattr(Permission, 'SETTING_READ')
        assert hasattr(Permission, 'SETTING_UPDATE')


class TestRolePermissionMapping:
    """测试角色权限映射"""

    def test_role_permission_mapping_exists(self):
        """测试角色权限映射配置存在"""
        from app.services.permissions import ROLE_PERMISSIONS

        # 应该有管理员权限映射
        assert 'admin' in ROLE_PERMISSIONS
        assert 'operator' in ROLE_PERMISSIONS
        assert 'viewer' in ROLE_PERMISSIONS

        # 管理员应该有最多权限
        admin_permissions = ROLE_PERMISSIONS['admin']
        from app.services.permissions import Permission
        assert Permission.USER_CREATE in admin_permissions
        assert Permission.USER_READ in admin_permissions
        assert Permission.SETTING_UPDATE in admin_permissions

        # 操作员权限：有设备操作，无用户管理，无分区增删改
        operator_permissions = ROLE_PERMISSIONS['operator']
        assert Permission.USER_CREATE not in operator_permissions
        assert Permission.USER_READ not in operator_permissions  # 用户管理仅管理员
        assert Permission.SETTING_UPDATE not in operator_permissions
        assert Permission.DEVICE_CONTROL in operator_permissions
        assert Permission.ZONE_READ in operator_permissions  # 分区查看权限
        assert Permission.ZONE_CREATE not in operator_permissions  # 分区创建仅管理员
        assert Permission.ZONE_UPDATE not in operator_permissions  # 分区更新仅管理员
        assert Permission.ZONE_DELETE not in operator_permissions  # 分区删除仅管理员

        # 查看者权限应该最少
        viewer_permissions = ROLE_PERMISSIONS['viewer']
        assert Permission.DEVICE_CREATE not in viewer_permissions
        assert Permission.USER_READ not in viewer_permissions  # 用户管理仅管理员
        assert Permission.ZONE_CREATE not in viewer_permissions