"""
测试安全问题修复
TDD 开发：安全漏洞修复测试
"""
import pytest
import os
from datetime import timedelta, UTC, datetime
from unittest.mock import MagicMock, patch, AsyncMock
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select


# ============================================================================
# P0-1: JWT Token 缺少 tenant_id 验证
# ============================================================================

class TestJWTTenantIdValidation:
    """测试 JWT Token 的 tenant_id 验证"""

    def test_token_data_includes_tenant_id(self):
        """测试 TokenData 包含 tenant_id 字段"""
        from app.schemas import TokenData

        # TokenData 应该包含 tenant_id 字段
        token_data = TokenData(username="testuser", tenant_id=1)
        assert token_data.username == "testuser"
        assert token_data.tenant_id == 1

    def test_create_access_token_includes_tenant_id(self):
        """测试创建的 token 包含 tenant_id"""
        from app.services.auth import create_access_token
        from jose import jwt
        from app.core.config import settings

        data = {"sub": "testuser", "tenant_id": 42}
        token = create_access_token(data)

        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        assert payload["sub"] == "testuser"
        assert payload["tenant_id"] == 42

    @pytest.mark.asyncio
    async def test_get_current_user_validates_tenant_id(self, db_session):
        """测试 get_current_user 验证 tenant_id"""
        from app.services.auth import get_current_user, create_access_token
        from app.models import User, Tenant
        from jose import jwt
        from app.core.config import settings

        # 创建租户和用户
        tenant1 = Tenant(name="租户1", code="tenant1")
        tenant2 = Tenant(name="租户2", code="tenant2")
        db_session.add(tenant1)
        db_session.add(tenant2)
        await db_session.flush()

        user = User(
            tenant_id=tenant1.id,
            username="testuser",
            password_hash="hashed",
            role="admin",
            is_active=True
        )
        db_session.add(user)
        await db_session.commit()

        # 创建正确 tenant_id 的 token
        valid_token = create_access_token({
            "sub": "testuser",
            "tenant_id": tenant1.id
        })

        # 创建错误 tenant_id 的 token（攻击者尝试访问其他租户）
        invalid_token = create_access_token({
            "sub": "testuser",
            "tenant_id": tenant2.id  # 错误的 tenant_id
        })

        # 验证正确的 token 应该成功
        result_user = await get_current_user(token=valid_token, db=db_session)
        assert result_user.username == "testuser"
        assert result_user.tenant_id == tenant1.id

        # 验证错误的 tenant_id 应该抛出异常
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token=invalid_token, db=db_session)
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user_missing_tenant_id_fails(self, db_session):
        """测试 token 中缺少 tenant_id 时验证失败"""
        from app.services.auth import get_current_user, create_access_token
        from app.models import User, Tenant
        from fastapi import HTTPException

        # 创建租户和用户
        tenant = Tenant(name="测试租户", code="test_tenant")
        db_session.add(tenant)
        await db_session.flush()

        user = User(
            tenant_id=tenant.id,
            username="testuser",
            password_hash="hashed",
            role="admin",
            is_active=True
        )
        db_session.add(user)
        await db_session.commit()

        # 创建没有 tenant_id 的 token
        token = create_access_token({"sub": "testuser"})  # 没有 tenant_id

        # 应该抛出 401 异常
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token=token, db=db_session)
        assert exc_info.value.status_code == 401


# ============================================================================
# P0-2: 设备创建缺少租户隔离验证
# ============================================================================

class TestDeviceTenantIsolation:
    """测试设备创建的租户隔离"""

    @pytest.mark.asyncio
    async def test_create_device_rejects_duplicate_device_id_other_tenant(self, db_session):
        """测试创建设备时拒绝其他租户已使用的 device_id"""
        from app.api.endpoints.devices import create_device
        from app.models import Device, User, Tenant, Zone
        from app.schemas import DeviceCreate
        from fastapi import HTTPException

        # 创建两个租户
        tenant1 = Tenant(name="租户1", code="tenant1_iso")
        tenant2 = Tenant(name="租户2", code="tenant2_iso")
        db_session.add(tenant1)
        db_session.add(tenant2)
        await db_session.flush()

        # 租户1创建设备
        device = Device(
            tenant_id=tenant1.id,
            device_id="IMEI123456789",
            name="租户1的设备"
        )
        db_session.add(device)
        await db_session.commit()

        # 租户2尝试创建相同 device_id 的设备
        user2 = User(
            tenant_id=tenant2.id,
            username="user2_iso",
            password_hash="hashed",
            role="admin",
            is_active=True
        )
        db_session.add(user2)
        await db_session.commit()

        device_in = DeviceCreate(
            device_id="IMEI123456789",  # 已被租户1使用
            name="租户2尝试创建的设备",
            tenant_id=tenant2.id
        )

        # 应该抛出 HTTPException，并提示 device_id 已被其他租户使用
        with pytest.raises(HTTPException) as exc_info:
            await create_device(device_in=device_in, db=db_session, current_user=user2)

        assert exc_info.value.status_code == 400
        # 错误信息应该明确说明是租户隔离问题
        assert "已被其他租户使用" in exc_info.value.detail or "已被其他租户使用" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_create_device_allows_same_tenant_duplicate_check(self, db_session):
        """测试同一租户重复创建 device_id 报错"""
        from app.api.endpoints.devices import create_device
        from app.models import Device, User, Tenant
        from app.schemas import DeviceCreate
        from fastapi import HTTPException

        tenant = Tenant(name="测试租户", code="test_dup")
        db_session.add(tenant)
        await db_session.flush()

        # 先创建一个设备
        device = Device(
            tenant_id=tenant.id,
            device_id="IMEI999",
            name="已存在的设备"
        )
        db_session.add(device)
        await db_session.commit()

        user = User(
            tenant_id=tenant.id,
            username="user_dup",
            password_hash="hashed",
            role="admin",
            is_active=True
        )
        db_session.add(user)
        await db_session.commit()

        device_in = DeviceCreate(
            device_id="IMEI999",
            name="重复的设备",
            tenant_id=tenant.id
        )

        # 同一租户内重复也应该报错
        with pytest.raises(HTTPException) as exc_info:
            await create_device(device_in=device_in, db=db_session, current_user=user)

        assert exc_info.value.status_code == 400


# ============================================================================
# P0-3: 默认密码安全检查
# ============================================================================

class TestDefaultPasswordSecurity:
    """测试默认密码安全检查"""

    def test_insecure_default_secrets_list(self):
        """测试不安全的默认密钥列表"""
        from app.core.config import INSECURE_DEFAULT_SECRETS

        # 应该包含常见的不安全密钥
        assert "dev-secret-key" in INSECURE_DEFAULT_SECRETS
        assert "secret" in INSECURE_DEFAULT_SECRETS
        assert "password" in INSECURE_DEFAULT_SECRETS
        assert "changeme" in INSECURE_DEFAULT_SECRETS
        assert "123456" in INSECURE_DEFAULT_SECRETS
        assert "jwt-secret" in INSECURE_DEFAULT_SECRETS

    def test_is_insecure_secret_detects_weak_secrets(self):
        """测试 is_insecure_secret 检测弱密钥"""
        from app.core.config import is_insecure_secret

        # 应该检测到不安全的密钥
        assert is_insecure_secret("dev-secret-key") == True
        assert is_insecure_secret("secret") == True
        assert is_insecure_secret("password") == True
        assert is_insecure_secret("changeme") == True
        assert is_insecure_secret("test") == True
        assert is_insecure_secret("admin") == True

        # 应该允许安全的密钥
        assert is_insecure_secret("a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6") == False
        assert is_insecure_secret("my-super-secure-random-key-2024!@#$") == False

    def test_settings_raises_error_on_insecure_secret_in_production(self):
        """测试生产环境下使用不安全密钥抛出错误"""
        from app.core.config import Settings

        with patch.dict(os.environ, {"ENV": "production"}):
            # 不安全的密钥应该抛出错误
            with pytest.raises(ValueError):
                Settings(JWT_SECRET="dev-secret-key")

            with pytest.raises(ValueError):
                Settings(JWT_SECRET="secret")

    def test_settings_allows_insecure_secret_in_development(self):
        """测试开发环境允许使用默认密钥（但发出警告）"""
        from app.core.config import Settings

        with patch.dict(os.environ, {"ENV": "development"}, clear=False):
            # 开发环境应该允许默认密钥
            settings = Settings(JWT_SECRET="dev-secret-key")
            assert settings.JWT_SECRET == "dev-secret-key"

    def test_settings_requires_secure_secret_in_production(self):
        """测试生产环境要求安全密钥"""
        from app.core.config import Settings

        with patch.dict(os.environ, {"ENV": "production"}):
            # 安全的密钥应该可以正常创建
            settings = Settings(JWT_SECRET="my-very-secure-random-key-2024!@#$%^&*()")
            assert settings.JWT_SECRET == "my-very-secure-random-key-2024!@#$%^&*()"


# ============================================================================
# P1-5: SQL 注入防护增强
# ============================================================================

class TestSQLInjectionProtection:
    """测试 SQL 注入防护"""

    @pytest.mark.asyncio
    async def test_keyword_parameter_safe_against_sql_injection(self, db_session):
        """测试 keyword 参数防止 SQL 注入"""
        from app.api.endpoints.devices import list_devices
        from app.models import Device, User, Tenant

        # 创建租户和用户
        tenant = Tenant(name="测试租户", code="test_sqli")
        db_session.add(tenant)
        await db_session.flush()

        user = User(
            tenant_id=tenant.id,
            username="user_sqli",
            password_hash="hashed",
            role="admin",
            is_active=True
        )
        db_session.add(user)
        await db_session.flush()

        # 创建一些设备
        devices = [
            Device(tenant_id=tenant.id, device_id="IMEI001", name="设备1"),
            Device(tenant_id=tenant.id, device_id="IMEI002", name="设备2"),
            Device(tenant_id=tenant.id, device_id="IMEI003", name="测试设备"),
        ]
        for d in devices:
            db_session.add(d)
        await db_session.commit()

        # 尝试 SQL 注入
        malicious_keywords = [
            "'; DROP TABLE devices; --",
            "设备' OR '1'='1",
            "设备%; DELETE FROM devices WHERE '1'='1",
            "<script>alert('xss')</script>",
        ]

        for keyword in malicious_keywords:
            # 应该安全处理，不应该抛出异常或删除数据
            result = await list_devices(
                keyword=keyword,
                skip=0,
                limit=20,
                db=db_session,
                current_user=user
            )
            # 应该返回空列表或安全过滤的结果，不应该报错
            assert hasattr(result, 'items')  # DeviceListResponse has items attribute

        # 验证数据没有被删除
        all_devices = await db_session.execute(
            select(Device).where(Device.tenant_id == tenant.id)
        )
        assert len(all_devices.scalars().all()) == 3

    @pytest.mark.asyncio
    async def test_keyword_search_uses_parameterized_query(self, db_session):
        """测试 keyword 搜索使用参数化查询"""
        from app.api.endpoints.devices import list_devices
        from app.models import Device, User, Tenant

        tenant = Tenant(name="测试租户", code="test_param")
        db_session.add(tenant)
        await db_session.flush()

        user = User(
            tenant_id=tenant.id,
            username="user_param",
            password_hash="hashed",
            role="admin",
            is_active=True
        )
        db_session.add(user)
        await db_session.flush()

        # 创建包含特殊字符名称的设备
        device = Device(
            tenant_id=tenant.id,
            device_id="IMEI_SPECIAL",
            name="测试'设备\"名称"
        )
        db_session.add(device)
        await db_session.commit()

        # 搜索包含单引号的名称
        result = await list_devices(
            keyword="测试'设备",
            skip=0,
            limit=20,
            db=db_session,
            current_user=user
        )
        # 应该安全处理特殊字符
        assert hasattr(result, 'items')


# ============================================================================
# P1-6: 操作日志模型
# ============================================================================

class TestOperationLogModel:
    """测试操作日志模型"""

    def test_operation_log_model_exists(self):
        """测试 OperationLog 模型存在"""
        from app.models import OperationLog

        assert OperationLog is not None

    def test_operation_log_model_fields(self):
        """测试 OperationLog 模型字段"""
        from app.models import OperationLog
        from datetime import datetime

        log = OperationLog(
            tenant_id=1,
            user_id=1,
            action="create_device",
            resource_type="device",
            resource_id="IMEI123",
            details={"device_name": "测试设备"},
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0"
        )

        assert log.tenant_id == 1
        assert log.user_id == 1
        assert log.action == "create_device"
        assert log.resource_type == "device"
        assert log.resource_id == "IMEI123"
        assert log.details == {"device_name": "测试设备"}
        assert log.ip_address == "192.168.1.1"
        assert log.user_agent == "Mozilla/5.0"

    def test_operation_log_table_name(self):
        """测试 OperationLog 表名"""
        from app.models import OperationLog

        assert OperationLog.__tablename__ == "operation_logs"

    def test_operation_log_has_indexes(self):
        """测试 OperationLog 有适当的索引"""
        from app.models import OperationLog

        # 检查是否有索引定义
        assert hasattr(OperationLog, '__table_args__')