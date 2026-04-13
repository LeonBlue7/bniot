"""
通知规则模型测试

TDD 测试用例：通知规则的 CRUD 操作
"""
import pytest
from datetime import datetime, timezone

from app.models.models import Alarm, Tenant, User
from app.services.auth import create_access_token, get_password_hash


class TestNotificationRuleModel:
    """通知规则模型测试"""

    @pytest.mark.asyncio
    async def test_create_notification_rule(self, db_session):
        """测试创建通知规则"""
        from app.models.models import NotificationRule, NotificationChannel

        # 创建租户
        tenant = Tenant(name="通知规则测试租户", code="test_notify_rule")
        db_session.add(tenant)
        await db_session.commit()
        await db_session.refresh(tenant)

        # 创建通知规则
        rule = NotificationRule(
            tenant_id=tenant.id,
            name="高优先级告警通知",
            description="当高优先级告警发生时发送邮件通知",
            alarm_types=["offline", "illegal_on", "temp_alarm"],
            severities=["high", "critical"],
            channels=[NotificationChannel.EMAIL, NotificationChannel.WECHAT],
            recipients=["admin@example.com", "user1"],
            is_enabled=True,
            cooldown_minutes=30,
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(rule)
        await db_session.commit()
        await db_session.refresh(rule)

        assert rule.id is not None
        assert rule.name == "高优先级告警通知"
        assert "offline" in rule.alarm_types
        assert NotificationChannel.EMAIL in rule.channels

    @pytest.mark.asyncio
    async def test_notification_rule_defaults(self, db_session):
        """测试通知规则默认值"""
        from app.models.models import NotificationRule

        tenant = Tenant(name="默认值测试租户", code="test_notify_default")
        db_session.add(tenant)
        await db_session.commit()
        await db_session.refresh(tenant)

        rule = NotificationRule(
            tenant_id=tenant.id,
            name="默认规则",
            alarm_types=["offline"],
            severities=["high"],
            channels=["email"],
            recipients=["admin@example.com"]
        )
        db_session.add(rule)
        await db_session.commit()
        await db_session.refresh(rule)

        assert rule.is_enabled is True  # 默认启用
        assert rule.cooldown_minutes == 30  # 默认冷却时间

    @pytest.mark.asyncio
    async def test_notification_rule_tenant_isolation(self, db_session):
        """测试通知规则租户隔离"""
        from app.models.models import NotificationRule

        # 创建两个租户
        tenant1 = Tenant(name="租户1", code="tenant1_notify")
        tenant2 = Tenant(name="租户2", code="tenant2_notify")
        db_session.add_all([tenant1, tenant2])
        await db_session.commit()
        await db_session.refresh(tenant1)
        await db_session.refresh(tenant2)

        # 创建规则
        rule1 = NotificationRule(
            tenant_id=tenant1.id,
            name="租户1规则",
            alarm_types=["offline"],
            severities=["high"],
            channels=["email"],
            recipients=["admin1@example.com"]
        )
        rule2 = NotificationRule(
            tenant_id=tenant2.id,
            name="租户2规则",
            alarm_types=["offline"],
            severities=["high"],
            channels=["email"],
            recipients=["admin2@example.com"]
        )
        db_session.add_all([rule1, rule2])
        await db_session.commit()

        # 验证租户隔离
        from sqlalchemy import select
        result = await db_session.execute(
            select(NotificationRule).where(NotificationRule.tenant_id == tenant1.id)
        )
        rules = result.scalars().all()
        assert len(rules) == 1
        assert rules[0].name == "租户1规则"


class TestNotificationRecordModel:
    """通知记录模型测试"""

    @pytest.mark.asyncio
    async def test_create_notification_record(self, db_session):
        """测试创建通知记录"""
        from app.models.models import NotificationRecord, NotificationChannel, NotificationStatus

        tenant = Tenant(name="通知记录测试租户", code="test_notify_record")
        db_session.add(tenant)
        await db_session.commit()
        await db_session.refresh(tenant)

        alarm = Alarm(
            tenant_id=tenant.id,
            device_id="device_001",
            type="offline",
            severity="high",
            message="设备离线告警",
            details={},
            is_resolved=False,
            occurred_at=datetime.now(timezone.utc)
        )
        db_session.add(alarm)
        await db_session.commit()
        await db_session.refresh(alarm)

        record = NotificationRecord(
            tenant_id=tenant.id,
            alarm_id=alarm.id,
            channel=NotificationChannel.EMAIL,
            recipient="admin@example.com",
            subject="设备离线告警",
            content="设备 device_001 已离线",
            status=NotificationStatus.SENT,
            sent_at=datetime.now(timezone.utc)
        )
        db_session.add(record)
        await db_session.commit()
        await db_session.refresh(record)

        assert record.id is not None
        assert record.status == NotificationStatus.SENT

    @pytest.mark.asyncio
    async def test_notification_record_failed_status(self, db_session):
        """测试通知记录失败状态"""
        from app.models.models import NotificationRecord, NotificationChannel, NotificationStatus

        tenant = Tenant(name="失败记录测试租户", code="test_notify_failed")
        db_session.add(tenant)
        await db_session.commit()
        await db_session.refresh(tenant)

        record = NotificationRecord(
            tenant_id=tenant.id,
            alarm_id=None,  # 可能没有关联告警
            channel=NotificationChannel.EMAIL,
            recipient="invalid@example.com",
            subject="测试通知",
            content="测试内容",
            status=NotificationStatus.FAILED,
            error_message="SMTP connection failed"
        )
        db_session.add(record)
        await db_session.commit()
        await db_session.refresh(record)

        assert record.status == NotificationStatus.FAILED
        assert "SMTP" in record.error_message