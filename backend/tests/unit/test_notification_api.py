"""
通知规则 API 端点测试

TDD 测试用例：通知规则的 CRUD 操作 API
"""
import pytest
from datetime import datetime, timezone
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Alarm, NotificationRule, NotificationRecord, Tenant, User
from app.models.models import NotificationChannel, NotificationStatus
from app.services.auth import create_access_token, get_password_hash


class TestNotificationRuleAPI:
    """通知规则 API 测试"""

    @pytest.mark.asyncio
    async def test_create_notification_rule(self, db_session: AsyncSession):
        """测试创建通知规则"""
        from app.main import app
        from app.core.database import get_db

        tenant = Tenant(name="通知规则API租户", code="test_rule_api_create")
        db_session.add(tenant)
        await db_session.commit()
        await db_session.refresh(tenant)

        admin = User(
            tenant_id=tenant.id,
            username="admin_rule_api",
            password_hash=get_password_hash("admin123"),
            role="admin",
            is_active=True
        )
        db_session.add(admin)
        await db_session.commit()
        await db_session.refresh(admin)

        admin_token = create_access_token(
            data={"sub": admin.username, "tenant_id": admin.tenant_id}
        )

        async def _get_db_override():
            yield db_session

        app.dependency_overrides[get_db] = _get_db_override

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/notifications/rules",
                headers={"Authorization": f"Bearer {admin_token}"},
                json={
                    "name": "高优先级告警邮件通知",
                    "description": "发送高优先级告警邮件",
                    "alarm_types": ["offline", "illegal_on"],
                    "severities": ["high", "critical"],
                    "channels": ["email"],
                    "recipients": ["admin@example.com"],
                    "cooldown_minutes": 30,
                    "is_enabled": True
                }
            )

        app.dependency_overrides.clear()

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "高优先级告警邮件通知"
        assert "offline" in data["alarm_types"]

    @pytest.mark.asyncio
    async def test_list_notification_rules(self, db_session: AsyncSession):
        """测试获取通知规则列表"""
        from app.main import app
        from app.core.database import get_db

        tenant = Tenant(name="通知规则列表租户", code="test_rule_api_list")
        db_session.add(tenant)
        await db_session.commit()
        await db_session.refresh(tenant)

        admin = User(
            tenant_id=tenant.id,
            username="admin_rule_list",
            password_hash=get_password_hash("admin123"),
            role="admin",
            is_active=True
        )
        db_session.add(admin)
        await db_session.commit()
        await db_session.refresh(admin)

        # 创建规则
        rule = NotificationRule(
            tenant_id=tenant.id,
            name="测试规则",
            alarm_types=["offline"],
            severities=["high"],
            channels=["email"],
            recipients=["admin@example.com"],
            is_enabled=True
        )
        db_session.add(rule)
        await db_session.commit()

        admin_token = create_access_token(
            data={"sub": admin.username, "tenant_id": admin.tenant_id}
        )

        async def _get_db_override():
            yield db_session

        app.dependency_overrides[get_db] = _get_db_override

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/notifications/rules",
                headers={"Authorization": f"Bearer {admin_token}"}
            )

        app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    @pytest.mark.asyncio
    async def test_get_notification_rule(self, db_session: AsyncSession):
        """测试获取单个通知规则"""
        from app.main import app
        from app.core.database import get_db

        tenant = Tenant(name="获取规则租户", code="test_rule_api_get")
        db_session.add(tenant)
        await db_session.commit()
        await db_session.refresh(tenant)

        admin = User(
            tenant_id=tenant.id,
            username="admin_rule_get",
            password_hash=get_password_hash("admin123"),
            role="admin",
            is_active=True
        )
        db_session.add(admin)
        await db_session.commit()
        await db_session.refresh(admin)

        rule = NotificationRule(
            tenant_id=tenant.id,
            name="获取测试规则",
            alarm_types=["offline"],
            severities=["high"],
            channels=["email"],
            recipients=["admin@example.com"],
            is_enabled=True
        )
        db_session.add(rule)
        await db_session.commit()
        await db_session.refresh(rule)

        admin_token = create_access_token(
            data={"sub": admin.username, "tenant_id": admin.tenant_id}
        )

        async def _get_db_override():
            yield db_session

        app.dependency_overrides[get_db] = _get_db_override

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                f"/api/notifications/rules/{rule.id}",
                headers={"Authorization": f"Bearer {admin_token}"}
            )

        app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "获取测试规则"

    @pytest.mark.asyncio
    async def test_get_notification_rule_not_found(self, db_session: AsyncSession):
        """测试获取不存在的通知规则"""
        from app.main import app
        from app.core.database import get_db

        tenant = Tenant(name="规则不存在租户", code="test_rule_api_notfound")
        db_session.add(tenant)
        await db_session.commit()
        await db_session.refresh(tenant)

        admin = User(
            tenant_id=tenant.id,
            username="admin_rule_notfound",
            password_hash=get_password_hash("admin123"),
            role="admin",
            is_active=True
        )
        db_session.add(admin)
        await db_session.commit()
        await db_session.refresh(admin)

        admin_token = create_access_token(
            data={"sub": admin.username, "tenant_id": admin.tenant_id}
        )

        async def _get_db_override():
            yield db_session

        app.dependency_overrides[get_db] = _get_db_override

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/notifications/rules/9999",
                headers={"Authorization": f"Bearer {admin_token}"}
            )

        app.dependency_overrides.clear()

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_notification_rule(self, db_session: AsyncSession):
        """测试更新通知规则"""
        from app.main import app
        from app.core.database import get_db

        tenant = Tenant(name="更新规则租户", code="test_rule_api_update")
        db_session.add(tenant)
        await db_session.commit()
        await db_session.refresh(tenant)

        admin = User(
            tenant_id=tenant.id,
            username="admin_rule_update",
            password_hash=get_password_hash("admin123"),
            role="admin",
            is_active=True
        )
        db_session.add(admin)
        await db_session.commit()
        await db_session.refresh(admin)

        rule = NotificationRule(
            tenant_id=tenant.id,
            name="原始规则名",
            alarm_types=["offline"],
            severities=["high"],
            channels=["email"],
            recipients=["admin@example.com"],
            is_enabled=True
        )
        db_session.add(rule)
        await db_session.commit()
        await db_session.refresh(rule)

        admin_token = create_access_token(
            data={"sub": admin.username, "tenant_id": admin.tenant_id}
        )

        async def _get_db_override():
            yield db_session

        app.dependency_overrides[get_db] = _get_db_override

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.patch(
                f"/api/notifications/rules/{rule.id}",
                headers={"Authorization": f"Bearer {admin_token}"},
                json={"name": "更新后的规则名", "is_enabled": False}
            )

        app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "更新后的规则名"
        assert data["is_enabled"] is False

    @pytest.mark.asyncio
    async def test_delete_notification_rule(self, db_session: AsyncSession):
        """测试删除通知规则"""
        from app.main import app
        from app.core.database import get_db

        tenant = Tenant(name="删除规则租户", code="test_rule_api_delete")
        db_session.add(tenant)
        await db_session.commit()
        await db_session.refresh(tenant)

        admin = User(
            tenant_id=tenant.id,
            username="admin_rule_delete",
            password_hash=get_password_hash("admin123"),
            role="admin",
            is_active=True
        )
        db_session.add(admin)
        await db_session.commit()
        await db_session.refresh(admin)

        rule = NotificationRule(
            tenant_id=tenant.id,
            name="待删除规则",
            alarm_types=["offline"],
            severities=["high"],
            channels=["email"],
            recipients=["admin@example.com"],
            is_enabled=True
        )
        db_session.add(rule)
        await db_session.commit()
        await db_session.refresh(rule)

        admin_token = create_access_token(
            data={"sub": admin.username, "tenant_id": admin.tenant_id}
        )

        async def _get_db_override():
            yield db_session

        app.dependency_overrides[get_db] = _get_db_override

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.delete(
                f"/api/notifications/rules/{rule.id}",
                headers={"Authorization": f"Bearer {admin_token}"}
            )

        app.dependency_overrides.clear()

        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_cross_tenant_rule_access_denied(self, db_session: AsyncSession):
        """测试跨租户访问规则被拒绝"""
        from app.main import app
        from app.core.database import get_db

        # 创建两个租户
        tenant1 = Tenant(name="租户1", code="tenant1_cross")
        tenant2 = Tenant(name="租户2", code="tenant2_cross")
        db_session.add_all([tenant1, tenant2])
        await db_session.commit()
        await db_session.refresh(tenant1)
        await db_session.refresh(tenant2)

        admin1 = User(
            tenant_id=tenant1.id,
            username="admin1_cross",
            password_hash=get_password_hash("admin123"),
            role="admin",
            is_active=True
        )
        db_session.add(admin1)
        await db_session.commit()
        await db_session.refresh(admin1)

        # 规则在租户2
        rule2 = NotificationRule(
            tenant_id=tenant2.id,
            name="租户2的规则",
            alarm_types=["offline"],
            severities=["high"],
            channels=["email"],
            recipients=["admin2@example.com"],
            is_enabled=True
        )
        db_session.add(rule2)
        await db_session.commit()
        await db_session.refresh(rule2)

        admin1_token = create_access_token(
            data={"sub": admin1.username, "tenant_id": admin1.tenant_id}
        )

        async def _get_db_override():
            yield db_session

        app.dependency_overrides[get_db] = _get_db_override

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # 租户1的用户尝试访问租户2的规则
            response = await client.get(
                f"/api/notifications/rules/{rule2.id}",
                headers={"Authorization": f"Bearer {admin1_token}"}
            )

        app.dependency_overrides.clear()

        assert response.status_code == 404


class TestNotificationRecordAPI:
    """通知记录 API 测试"""

    @pytest.mark.asyncio
    async def test_list_notification_records(self, db_session: AsyncSession):
        """测试获取通知记录列表"""
        from app.main import app
        from app.core.database import get_db

        tenant = Tenant(name="记录列表租户", code="test_record_api_list")
        db_session.add(tenant)
        await db_session.commit()
        await db_session.refresh(tenant)

        admin = User(
            tenant_id=tenant.id,
            username="admin_record_list",
            password_hash=get_password_hash("admin123"),
            role="admin",
            is_active=True
        )
        db_session.add(admin)
        await db_session.commit()
        await db_session.refresh(admin)

        # 创建通知记录
        record = NotificationRecord(
            tenant_id=tenant.id,
            alarm_id=None,
            rule_id=None,
            channel=NotificationChannel.EMAIL,
            recipient="admin@example.com",
            subject="测试通知",
            content="测试内容",
            status=NotificationStatus.SENT,
            sent_at=datetime.now(timezone.utc)
        )
        db_session.add(record)
        await db_session.commit()

        admin_token = create_access_token(
            data={"sub": admin.username, "tenant_id": admin.tenant_id}
        )

        async def _get_db_override():
            yield db_session

        app.dependency_overrides[get_db] = _get_db_override

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/notifications/records",
                headers={"Authorization": f"Bearer {admin_token}"}
            )

        app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    @pytest.mark.asyncio
    async def test_notification_stats(self, db_session: AsyncSession):
        """测试获取通知统计"""
        from app.main import app
        from app.core.database import get_db

        tenant = Tenant(name="统计租户", code="test_record_api_stats")
        db_session.add(tenant)
        await db_session.commit()
        await db_session.refresh(tenant)

        admin = User(
            tenant_id=tenant.id,
            username="admin_record_stats",
            password_hash=get_password_hash("admin123"),
            role="admin",
            is_active=True
        )
        db_session.add(admin)
        await db_session.commit()
        await db_session.refresh(admin)

        # 创建一些通知记录
        for i in range(3):
            record = NotificationRecord(
                tenant_id=tenant.id,
                alarm_id=None,
                rule_id=None,
                channel=NotificationChannel.EMAIL,
                recipient=f"admin{i}@example.com",
                subject=f"测试通知{i}",
                content=f"测试内容{i}",
                status=NotificationStatus.SENT,
                sent_at=datetime.now(timezone.utc)
            )
            db_session.add(record)

        # 创建一条失败记录
        failed_record = NotificationRecord(
            tenant_id=tenant.id,
            alarm_id=None,
            rule_id=None,
            channel=NotificationChannel.EMAIL,
            recipient="failed@example.com",
            subject="失败通知",
            content="失败内容",
            status=NotificationStatus.FAILED,
            error_message="SMTP连接失败"
        )
        db_session.add(failed_record)
        await db_session.commit()

        admin_token = create_access_token(
            data={"sub": admin.username, "tenant_id": admin.tenant_id}
        )

        async def _get_db_override():
            yield db_session

        app.dependency_overrides[get_db] = _get_db_override

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/notifications/stats",
                headers={"Authorization": f"Bearer {admin_token}"}
            )

        app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert data["total_notifications"] == 4
        assert data["sent_count"] == 3
        assert data["failed_count"] == 1
        assert data["success_rate"] == 75.0


class TestNotificationRuleValidation:
    """通知规则验证测试"""

    @pytest.mark.asyncio
    async def test_create_rule_empty_alarm_types(self, db_session: AsyncSession):
        """测试创建规则时告警类型为空"""
        from app.main import app
        from app.core.database import get_db

        tenant = Tenant(name="验证租户", code="test_rule_validation")
        db_session.add(tenant)
        await db_session.commit()
        await db_session.refresh(tenant)

        admin = User(
            tenant_id=tenant.id,
            username="admin_validation",
            password_hash=get_password_hash("admin123"),
            role="admin",
            is_active=True
        )
        db_session.add(admin)
        await db_session.commit()
        await db_session.refresh(admin)

        admin_token = create_access_token(
            data={"sub": admin.username, "tenant_id": admin.tenant_id}
        )

        async def _get_db_override():
            yield db_session

        app.dependency_overrides[get_db] = _get_db_override

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/notifications/rules",
                headers={"Authorization": f"Bearer {admin_token}"},
                json={
                    "name": "无效规则",
                    "alarm_types": [],  # 空列表
                    "severities": ["high"],
                    "channels": ["email"],
                    "recipients": ["admin@example.com"]
                }
            )

        app.dependency_overrides.clear()

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_create_rule_invalid_cooldown(self, db_session: AsyncSession):
        """测试创建规则时冷却时间超出范围"""
        from app.main import app
        from app.core.database import get_db

        tenant = Tenant(name="冷却验证租户", code="test_rule_cooldown")
        db_session.add(tenant)
        await db_session.commit()
        await db_session.refresh(tenant)

        admin = User(
            tenant_id=tenant.id,
            username="admin_cooldown",
            password_hash=get_password_hash("admin123"),
            role="admin",
            is_active=True
        )
        db_session.add(admin)
        await db_session.commit()
        await db_session.refresh(admin)

        admin_token = create_access_token(
            data={"sub": admin.username, "tenant_id": admin.tenant_id}
        )

        async def _get_db_override():
            yield db_session

        app.dependency_overrides[get_db] = _get_db_override

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # 冷却时间超过最大值（1440分钟）
            response = await client.post(
                "/api/notifications/rules",
                headers={"Authorization": f"Bearer {admin_token}"},
                json={
                    "name": "冷却时间超限",
                    "alarm_types": ["offline"],
                    "severities": ["high"],
                    "channels": ["email"],
                    "recipients": ["admin@example.com"],
                    "cooldown_minutes": 2000  # 超出范围
                }
            )

        app.dependency_overrides.clear()

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_update_rule_empty_update(self, db_session: AsyncSession):
        """测试更新规则时没有更新字段"""
        from app.main import app
        from app.core.database import get_db

        tenant = Tenant(name="空更新租户", code="test_rule_empty_update")
        db_session.add(tenant)
        await db_session.commit()
        await db_session.refresh(tenant)

        admin = User(
            tenant_id=tenant.id,
            username="admin_empty_update",
            password_hash=get_password_hash("admin123"),
            role="admin",
            is_active=True
        )
        db_session.add(admin)
        await db_session.commit()
        await db_session.refresh(admin)

        rule = NotificationRule(
            tenant_id=tenant.id,
            name="测试规则",
            alarm_types=["offline"],
            severities=["high"],
            channels=["email"],
            recipients=["admin@example.com"],
            is_enabled=True
        )
        db_session.add(rule)
        await db_session.commit()
        await db_session.refresh(rule)

        admin_token = create_access_token(
            data={"sub": admin.username, "tenant_id": admin.tenant_id}
        )

        async def _get_db_override():
            yield db_session

        app.dependency_overrides[get_db] = _get_db_override

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.patch(
                f"/api/notifications/rules/{rule.id}",
                headers={"Authorization": f"Bearer {admin_token}"},
                json={}  # 空更新
            )

        app.dependency_overrides.clear()

        assert response.status_code == 400