"""
测试数据库模型
Phase 1 基础设施测试
"""
import pytest
from datetime import datetime
from sqlalchemy.exc import IntegrityError


class TestTenantModel:
    """测试租户模型"""

    def test_tenant_creation(self, db_session_sync):
        """测试创建租户"""
        from app.models import Tenant

        tenant = Tenant(
            name="测试租户",
            code="test_tenant",
            settings={"timezone": "Asia/Shanghai"}
        )

        db_session_sync.add(tenant)
        db_session_sync.commit()

        assert tenant.id is not None
        assert tenant.name == "测试租户"
        assert tenant.code == "test_tenant"
        assert tenant.created_at is not None

    def test_tenant_unique_code(self, db_session_sync):
        """测试租户编码唯一性"""
        from app.models import Tenant

        tenant1 = Tenant(name="租户1", code="unique_code")
        tenant2 = Tenant(name="租户2", code="unique_code")

        db_session_sync.add(tenant1)
        db_session_sync.commit()

        db_session_sync.add(tenant2)
        with pytest.raises(IntegrityError):
            db_session_sync.commit()


class TestUserModel:
    """测试用户模型"""

    def test_user_creation(self, db_session_sync):
        """测试创建用户"""
        from app.models import Tenant, User

        tenant = Tenant(name="租户", code="test")
        db_session_sync.add(tenant)
        db_session_sync.commit()

        user = User(
            tenant_id=tenant.id,
            username="testuser",
            password_hash="hashed_password",
            role="admin"
        )

        db_session_sync.add(user)
        db_session_sync.commit()

        assert user.id is not None
        assert user.username == "testuser"
        assert user.role == "admin"
        assert user.is_active == True

    def test_user_unique_username(self, db_session_sync):
        """测试用户名唯一性"""
        from app.models import Tenant, User

        tenant = Tenant(name="租户", code="test")
        db_session_sync.add(tenant)
        db_session_sync.commit()

        user1 = User(tenant_id=tenant.id, username="unique", password_hash="hash1")
        user2 = User(tenant_id=tenant.id, username="unique", password_hash="hash2")

        db_session_sync.add(user1)
        db_session_sync.commit()

        db_session_sync.add(user2)
        with pytest.raises(IntegrityError):
            db_session_sync.commit()

    def test_user_default_role(self, db_session_sync):
        """测试用户默认角色"""
        from app.models import Tenant, User

        tenant = Tenant(name="租户", code="test")
        db_session_sync.add(tenant)
        db_session_sync.commit()

        user = User(
            tenant_id=tenant.id,
            username="viewer",
            password_hash="hash"
        )

        db_session_sync.add(user)
        db_session_sync.commit()

        assert user.role == "viewer"


class TestDeviceModel:
    """测试设备模型"""

    def test_device_creation(self, db_session_sync):
        """测试创建设备"""
        from app.models import Tenant, Device

        tenant = Tenant(name="租户", code="test")
        db_session_sync.add(tenant)
        db_session_sync.commit()

        device = Device(
            tenant_id=tenant.id,
            device_id="123456789012345",
            name="测试空调",
            protocol_version="V10"
        )

        db_session_sync.add(device)
        db_session_sync.commit()

        assert device.id is not None
        assert device.device_id == "123456789012345"
        assert device.is_online == False
        assert device.protocol_version == "V10"

    def test_device_unique_device_id(self, db_session_sync):
        """测试设备 ID 唯一性"""
        from app.models import Tenant, Device

        tenant = Tenant(name="租户", code="test")
        db_session_sync.add(tenant)
        db_session_sync.commit()

        device1 = Device(tenant_id=tenant.id, device_id="unique_imei", name="设备1")
        device2 = Device(tenant_id=tenant.id, device_id="unique_imei", name="设备2")

        db_session_sync.add(device1)
        db_session_sync.commit()

        db_session_sync.add(device2)
        with pytest.raises(IntegrityError):
            db_session_sync.commit()


class TestZoneModel:
    """测试分区模型"""

    def test_zone_creation(self, db_session_sync):
        """测试创建分区"""
        from app.models import Tenant, Zone

        tenant = Tenant(name="租户", code="test")
        db_session_sync.add(tenant)
        db_session_sync.commit()

        zone = Zone(
            tenant_id=tenant.id,
            name="一楼办公区",
            description="一楼办公室空调分区"
        )

        db_session_sync.add(zone)
        db_session_sync.commit()

        assert zone.id is not None
        assert zone.name == "一楼办公区"

    def test_zone_parent_child_relationship(self, db_session_sync):
        """测试分区父子关系"""
        from app.models import Tenant, Zone

        tenant = Tenant(name="租户", code="test")
        db_session_sync.add(tenant)
        db_session_sync.commit()

        parent = Zone(tenant_id=tenant.id, name="总公司")
        db_session_sync.add(parent)
        db_session_sync.commit()

        child = Zone(
            tenant_id=tenant.id,
            name="分公司",
            parent_id=parent.id
        )
        db_session_sync.add(child)
        db_session_sync.commit()

        assert child.parent_id == parent.id


class TestProtocolVersionModel:
    """测试协议版本模型"""

    def test_protocol_version_creation(self, db_session_sync):
        """测试创建协议版本"""
        from app.models import ProtocolVersion

        version = ProtocolVersion(
            version_code="V30",
            version_number=30,
            feature_params={"exclusive": ["111", "112"]},
            param_mappings={"111": {"name": "新参数"}},
            description="V30 新增参数"
        )

        db_session_sync.add(version)
        db_session_sync.commit()

        assert version.id is not None
        assert version.version_code == "V30"
        assert version.version_number == 30
        assert version.is_active == True

    def test_protocol_version_unique_code(self, db_session_sync):
        """测试协议版本编码唯一性"""
        from app.models import ProtocolVersion

        version1 = ProtocolVersion(version_code="V_UNIQUE", version_number=99)
        version2 = ProtocolVersion(version_code="V_UNIQUE", version_number=100)

        db_session_sync.add(version1)
        db_session_sync.commit()

        db_session_sync.add(version2)
        with pytest.raises(IntegrityError):
            db_session_sync.commit()