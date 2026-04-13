"""
通知服务测试

TDD 测试用例：邮件通知、微信推送、通知规则匹配
"""
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from app.models.models import Alarm, Tenant, User
from app.services.auth import create_access_token, get_password_hash


class TestEmailNotificationService:
    """邮件通知服务测试"""

    @pytest.mark.asyncio
    async def test_send_email_notification_success(self):
        """测试发送邮件通知成功"""
        from app.services.notification import EmailNotificationService

        service = EmailNotificationService(
            smtp_host="smtp.example.com",
            smtp_port=587,
            smtp_user="test@example.com",
            smtp_password="password",
            from_email="noreply@example.com"
        )

        # 直接 mock send 方法来验证逻辑
        with patch.object(service, '_send_via_smtp', new=AsyncMock(return_value=True)):
            result = await service.send(
                to=["admin@example.com"],
                subject="测试告警通知",
                content="设备 device_001 已离线"
            )

            assert result is True

    @pytest.mark.asyncio
    async def test_send_email_notification_with_template(self):
        """测试使用模板发送邮件通知"""
        from app.services.notification import EmailNotificationService

        service = EmailNotificationService(
            smtp_host="smtp.example.com",
            smtp_port=587,
            smtp_user="test@example.com",
            smtp_password="password",
            from_email="noreply@example.com"
        )

        template_data = {
            "device_id": "device_001",
            "alarm_type": "设备离线",
            "severity": "high",
            "message": "设备离线告警",
            "occurred_at": "2024-01-01 10:00:00"
        }

        # Mock send 方法
        with patch.object(service, 'send', new=AsyncMock(return_value=True)):
            result = await service.send_with_template(
                to=["admin@example.com"],
                template_name="alarm_email",
                data=template_data
            )

            assert result is True

    @pytest.mark.asyncio
    async def test_send_email_notification_failure(self):
        """测试发送邮件通知失败"""
        from app.services.notification import EmailNotificationService

        service = EmailNotificationService(
            smtp_host="smtp.example.com",
            smtp_port=587,
            smtp_user="test@example.com",
            smtp_password="password",
            from_email="noreply@example.com"
        )

        # Mock _send_via_smtp 方法抛出异常
        async def mock_send_failure(msg):
            raise Exception("SMTP connection failed")

        with patch.object(service, '_send_via_smtp', new=mock_send_failure):
            result = await service.send(
                to=["admin@example.com"],
                subject="测试告警通知",
                content="设备 device_001 已离线"
            )

            assert result is False

    @pytest.mark.asyncio
    async def test_send_email_empty_recipients(self):
        """测试发送邮件收件人为空"""
        from app.services.notification import EmailNotificationService

        service = EmailNotificationService(
            smtp_host="smtp.example.com",
            smtp_port=587,
            smtp_user="test@example.com",
            smtp_password="password",
            from_email="noreply@example.com"
        )

        result = await service.send(
            to=[],
            subject="测试告警通知",
            content="设备 device_001 已离线"
        )

        assert result is False


class TestWeChatNotificationService:
    """微信企业号通知服务测试"""

    @pytest.mark.asyncio
    async def test_send_wechat_webhook_success(self):
        """测试发送微信 Webhook 通知成功"""
        from app.services.notification import WeChatNotificationService

        with patch("app.services.notification.wechat_service.httpx") as mock_httpx:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"errcode": 0, "errmsg": "ok"}

            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_httpx.AsyncClient = MagicMock(return_value=mock_client)

            service = WeChatNotificationService(webhook_url="https://qyapi.weixin.qq.com/webhook/test")

            result = await service.send(
                content="设备 device_001 已离线"
            )

            assert result is True

    @pytest.mark.asyncio
    async def test_send_wechat_webhook_failure(self):
        """测试发送微信 Webhook 通知失败"""
        from app.services.notification import WeChatNotificationService

        with patch("app.services.notification.wechat_service.httpx") as mock_httpx:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"errcode": 40001, "errmsg": "invalid webhook"}

            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_httpx.AsyncClient = MagicMock(return_value=mock_client)

            service = WeChatNotificationService(webhook_url="https://qyapi.weixin.qq.com/webhook/invalid")

            result = await service.send(
                content="设备 device_001 已离线"
            )

            assert result is False

    @pytest.mark.asyncio
    async def test_send_wechat_markdown_message(self):
        """测试发送 Markdown 格式消息"""
        from app.services.notification import WeChatNotificationService

        with patch("app.services.notification.wechat_service.httpx") as mock_httpx:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"errcode": 0, "errmsg": "ok"}

            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_httpx.AsyncClient = MagicMock(return_value=mock_client)

            service = WeChatNotificationService(webhook_url="https://qyapi.weixin.qq.com/webhook/test")

            result = await service.send_markdown(
                content="## 设备告警\n> 设备ID: device_001\n> 告警类型: 离线"
            )

            assert result is True


class TestNotificationRuleService:
    """通知规则服务测试"""

    @pytest.mark.asyncio
    async def test_match_alarm_to_rule(self, db_session):
        """测试告警匹配规则"""
        from app.services.notification import NotificationRuleService
        from app.models.models import NotificationRule

        tenant = Tenant(name="规则匹配测试租户", code="test_rule_match")
        db_session.add(tenant)
        await db_session.commit()
        await db_session.refresh(tenant)

        # 创建规则
        rule = NotificationRule(
            tenant_id=tenant.id,
            name="高优先级离线告警",
            alarm_types=["offline"],
            severities=["high", "critical"],
            channels=["email", "wechat"],
            recipients=["admin@example.com"],
            is_enabled=True
        )
        db_session.add(rule)
        await db_session.commit()

        # 创建告警
        alarm = Alarm(
            tenant_id=tenant.id,
            device_id="device_001",
            type="offline",
            severity="high",
            message="设备离线",
            details={},
            is_resolved=False,
            occurred_at=datetime.now(timezone.utc)
        )
        db_session.add(alarm)
        await db_session.commit()
        await db_session.refresh(alarm)

        service = NotificationRuleService(db_session)
        matched_rules = await service.match_rules(alarm)

        assert len(matched_rules) >= 1
        assert rule.id in [r.id for r in matched_rules]

    @pytest.mark.asyncio
    async def test_match_alarm_no_matching_rule(self, db_session):
        """测试告警无匹配规则"""
        from app.services.notification import NotificationRuleService
        from app.models.models import NotificationRule

        tenant = Tenant(name="无匹配规则测试租户", code="test_no_match")
        db_session.add(tenant)
        await db_session.commit()
        await db_session.refresh(tenant)

        # 创建规则（只匹配 high 级别）
        rule = NotificationRule(
            tenant_id=tenant.id,
            name="仅高优先级",
            alarm_types=["offline"],
            severities=["high"],
            channels=["email"],
            recipients=["admin@example.com"],
            is_enabled=True
        )
        db_session.add(rule)
        await db_session.commit()

        # 创建低优先级告警
        alarm = Alarm(
            tenant_id=tenant.id,
            device_id="device_001",
            type="offline",
            severity="low",  # 低优先级，不匹配
            message="设备离线",
            details={},
            is_resolved=False,
            occurred_at=datetime.now(timezone.utc)
        )
        db_session.add(alarm)
        await db_session.commit()
        await db_session.refresh(alarm)

        service = NotificationRuleService(db_session)
        matched_rules = await service.match_rules(alarm)

        assert len(matched_rules) == 0

    @pytest.mark.asyncio
    async def test_rule_cooldown(self, db_session):
        """测试规则冷却时间"""
        from app.services.notification import NotificationRuleService
        from app.models.models import NotificationRule, NotificationRecord, NotificationChannel, NotificationStatus
        from datetime import timedelta

        tenant = Tenant(name="冷却时间测试租户", code="test_cooldown")
        db_session.add(tenant)
        await db_session.commit()
        await db_session.refresh(tenant)

        # 创建规则（冷却时间 30 分钟）
        rule = NotificationRule(
            tenant_id=tenant.id,
            name="冷却测试规则",
            alarm_types=["offline"],
            severities=["high"],
            channels=["email"],
            recipients=["admin@example.com"],
            is_enabled=True,
            cooldown_minutes=30
        )
        db_session.add(rule)
        await db_session.commit()
        await db_session.refresh(rule)

        # 创建告警
        alarm = Alarm(
            tenant_id=tenant.id,
            device_id="device_001",
            type="offline",
            severity="high",
            message="设备离线",
            details={},
            is_resolved=False,
            occurred_at=datetime.now(timezone.utc)
        )
        db_session.add(alarm)
        await db_session.commit()
        await db_session.refresh(alarm)

        service = NotificationRuleService(db_session)

        # 首次匹配，应该匹配到规则
        matched_rules = await service.match_rules(alarm)
        assert len(matched_rules) >= 1

        # 记录已发送通知
        record = NotificationRecord(
            tenant_id=tenant.id,
            alarm_id=alarm.id,
            rule_id=rule.id,
            channel=NotificationChannel.EMAIL,
            recipient="admin@example.com",
            subject="设备离线告警",
            content="设备离线",
            status=NotificationStatus.SENT,
            sent_at=datetime.now(timezone.utc)
        )
        db_session.add(record)
        await db_session.commit()

        # 检查冷却时间
        is_in_cooldown = await service.check_cooldown(rule, alarm)
        assert is_in_cooldown is True

        # 模拟冷却时间已过
        record.sent_at = datetime.now(timezone.utc) - timedelta(minutes=31)
        await db_session.commit()

        is_in_cooldown = await service.check_cooldown(rule, alarm)
        assert is_in_cooldown is False


class TestNotificationDispatchService:
    """通知分发服务测试"""

    @pytest.mark.asyncio
    async def test_dispatch_notification_email(self, db_session):
        """测试分发邮件通知"""
        from app.services.notification import NotificationDispatchService, EmailNotificationService
        from app.models.models import NotificationRule, NotificationChannel

        tenant = Tenant(name="分发测试租户", code="test_dispatch")
        db_session.add(tenant)
        await db_session.commit()
        await db_session.refresh(tenant)

        alarm = Alarm(
            tenant_id=tenant.id,
            device_id="device_001",
            type="offline",
            severity="high",
            message="设备离线",
            details={},
            is_resolved=False,
            occurred_at=datetime.now(timezone.utc)
        )
        db_session.add(alarm)
        await db_session.commit()
        await db_session.refresh(alarm)

        rule = NotificationRule(
            tenant_id=tenant.id,
            name="邮件通知规则",
            alarm_types=["offline"],
            severities=["high"],
            channels=[NotificationChannel.EMAIL],
            recipients=["admin@example.com"],
            is_enabled=True
        )
        db_session.add(rule)
        await db_session.commit()
        await db_session.refresh(rule)

        service = NotificationDispatchService(db_session)

        # 配置邮件服务并 mock send 方法
        mock_email_service = MagicMock(spec=EmailNotificationService)
        mock_email_service.send = AsyncMock(return_value=True)
        service.email_service = mock_email_service

        results = await service.dispatch(alarm, [rule])

        assert len(results) >= 1
        assert results[0]["status"] == "sent"

    @pytest.mark.asyncio
    async def test_dispatch_notification_multiple_channels(self, db_session):
        """测试多渠道通知分发"""
        from app.services.notification import NotificationDispatchService
        from app.models.models import NotificationRule, NotificationChannel

        tenant = Tenant(name="多渠道测试租户", code="test_multi_channel")
        db_session.add(tenant)
        await db_session.commit()
        await db_session.refresh(tenant)

        alarm = Alarm(
            tenant_id=tenant.id,
            device_id="device_001",
            type="offline",
            severity="high",
            message="设备离线",
            details={},
            is_resolved=False,
            occurred_at=datetime.now(timezone.utc)
        )
        db_session.add(alarm)
        await db_session.commit()
        await db_session.refresh(alarm)

        rule = NotificationRule(
            tenant_id=tenant.id,
            name="多渠道通知规则",
            alarm_types=["offline"],
            severities=["high"],
            channels=[NotificationChannel.EMAIL, NotificationChannel.WECHAT],
            recipients=["admin@example.com"],
            is_enabled=True
        )
        db_session.add(rule)
        await db_session.commit()
        await db_session.refresh(rule)

        with patch("app.services.notification.dispatch_service.EmailNotificationService") as mock_email, \
             patch("app.services.notification.dispatch_service.WeChatNotificationService") as mock_wechat:
            mock_email_instance = AsyncMock()
            mock_email_instance.send = AsyncMock(return_value=True)
            mock_email.return_value = mock_email_instance

            mock_wechat_instance = AsyncMock()
            mock_wechat_instance.send = AsyncMock(return_value=True)
            mock_wechat.return_value = mock_wechat_instance

            service = NotificationDispatchService(db_session)
            results = await service.dispatch(alarm, [rule])

            # 应该有邮件和微信两种渠道的通知
            assert len(results) >= 2

    @pytest.mark.asyncio
    async def test_dispatch_notification_disabled_rule(self, db_session):
        """测试禁用规则不分发通知"""
        from app.services.notification import NotificationDispatchService
        from app.models.models import NotificationRule, NotificationChannel

        tenant = Tenant(name="禁用规则测试租户", code="test_disabled_rule")
        db_session.add(tenant)
        await db_session.commit()
        await db_session.refresh(tenant)

        alarm = Alarm(
            tenant_id=tenant.id,
            device_id="device_001",
            type="offline",
            severity="high",
            message="设备离线",
            details={},
            is_resolved=False,
            occurred_at=datetime.now(timezone.utc)
        )
        db_session.add(alarm)
        await db_session.commit()
        await db_session.refresh(alarm)

        # 禁用的规则
        rule = NotificationRule(
            tenant_id=tenant.id,
            name="禁用的规则",
            alarm_types=["offline"],
            severities=["high"],
            channels=[NotificationChannel.EMAIL],
            recipients=["admin@example.com"],
            is_enabled=False  # 禁用
        )
        db_session.add(rule)
        await db_session.commit()
        await db_session.refresh(rule)

        service = NotificationDispatchService(db_session)
        results = await service.dispatch(alarm, [rule])

        # 禁用规则不应发送通知
        assert len(results) == 0


class TestNotificationTemplate:
    """通知模板测试"""

    @pytest.mark.asyncio
    async def test_render_alarm_template(self):
        """测试渲染告警通知模板"""
        from app.services.notification import NotificationTemplateService

        template_service = NotificationTemplateService()

        alarm_data = {
            "device_id": "device_001",
            "alarm_type": "offline",
            "severity": "high",
            "message": "设备离线告警",
            "occurred_at": "2024-01-01 10:00:00"
        }

        content = template_service.render("alarm_notification", alarm_data)

        assert "device_001" in content
        assert "离线" in content or "offline" in content.lower()

    @pytest.mark.asyncio
    async def test_render_email_template(self):
        """测试渲染邮件模板"""
        from app.services.notification import NotificationTemplateService

        template_service = NotificationTemplateService()

        data = {
            "device_id": "device_001",
            "alarm_type": "设备离线",
            "occurred_at": "2024-01-01 10:00:00",
            "tenant_name": "测试租户"
        }

        subject, body = template_service.render_email("alarm_email", data)

        assert "device_001" in body
        assert subject is not None
        assert len(subject) > 0

    @pytest.mark.asyncio
    async def test_render_wechat_markdown(self):
        """测试渲染微信 Markdown 消息"""
        from app.services.notification import NotificationTemplateService

        template_service = NotificationTemplateService()

        data = {
            "device_id": "device_001",
            "alarm_type": "设备离线",
            "severity": "high",
            "occurred_at": "2024-01-01 10:00:00"
        }

        content = template_service.render_wechat_markdown("alarm_markdown", data)

        assert "device_001" in content
        assert "离线" in content or "offline" in content.lower()