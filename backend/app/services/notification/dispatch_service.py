"""
通知分发服务

根据匹配的规则分发通知到各渠道
"""
from datetime import datetime, timezone
from typing import List, Dict, Any

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Alarm, NotificationRule, NotificationRecord, NotificationChannel, NotificationStatus
from app.services.notification.email_service import EmailNotificationService
from app.services.notification.wechat_service import WeChatNotificationService
from app.services.notification.rule_service import NotificationRuleService
from app.services.notification.template_service import NotificationTemplateService


class NotificationDispatchService:
    """
    通知分发服务

    功能：
    - 根据规则分发通知到多个渠道
    - 记录通知发送结果
    - 处理发送失败情况
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.rule_service = NotificationRuleService(db)
        self.template_service = NotificationTemplateService()

        # 邮件服务（需要配置）
        self.email_service = None
        # 微信服务（需要配置）
        self.wechat_service = None

    def configure_email(
        self,
        smtp_host: str,
        smtp_port: int,
        smtp_user: str,
        smtp_password: str,
        from_email: str
    ):
        """配置邮件服务"""
        self.email_service = EmailNotificationService(
            smtp_host=smtp_host,
            smtp_port=smtp_port,
            smtp_user=smtp_user,
            smtp_password=smtp_password,
            from_email=from_email
        )

    def configure_wechat(self, webhook_url: str):
        """配置微信服务"""
        self.wechat_service = WeChatNotificationService(webhook_url=webhook_url)

    async def dispatch(
        self,
        alarm: Alarm,
        rules: List[NotificationRule]
    ) -> List[Dict[str, Any]]:
        """
        分发通知

        Args:
            alarm: 告警对象
            rules: 匹配的规则列表

        Returns:
            List[Dict[str, Any]]: 发送结果列表
        """
        results = []

        for rule in rules:
            # 检查规则是否启用
            if not rule.is_enabled:
                logger.debug(f"规则 {rule.id} 已禁用，跳过")
                continue

            # 检查冷却时间
            if await self.rule_service.check_cooldown(rule, alarm):
                logger.debug(f"规则 {rule.id} 在冷却期内，跳过")
                results.append({
                    "rule_id": rule.id,
                    "status": "rate_limited",
                    "message": "通知在冷却期内"
                })
                continue

            # 准备模板数据
            template_data = {
                "device_id": alarm.device_id,
                "alarm_type": alarm.type,
                "severity": alarm.severity,
                "message": alarm.message or "",
                "occurred_at": alarm.occurred_at.isoformat() if alarm.occurred_at else ""
            }

            # 按渠道分发
            for channel in rule.channels:
                result = await self._dispatch_to_channel(
                    alarm=alarm,
                    rule=rule,
                    channel=channel,
                    recipients=rule.recipients,
                    template_data=template_data
                )
                results.append(result)

        return results

    async def _dispatch_to_channel(
        self,
        alarm: Alarm,
        rule: NotificationRule,
        channel: str,
        recipients: List[str],
        template_data: dict
    ) -> Dict[str, Any]:
        """
        分发到单个渠道

        Args:
            alarm: 告警对象
            rule: 通知规则
            channel: 渠道类型
            recipients: 接收人列表
            template_data: 模板数据

        Returns:
            Dict[str, Any]: 发送结果
        """
        result = {
            "rule_id": rule.id,
            "channel": channel,
            "status": "pending"
        }

        try:
            if channel == NotificationChannel.EMAIL:
                success = await self._send_email(recipients, template_data)
            elif channel == NotificationChannel.WECHAT:
                success = await self._send_wechat(template_data)
            else:
                logger.warning(f"未知的通知渠道: {channel}")
                success = False

            result["status"] = "sent" if success else "failed"

            # 记录通知发送
            await self._record_notification(
                alarm=alarm,
                rule=rule,
                channel=channel,
                recipients=recipients,
                success=success,
                template_data=template_data
            )

        except Exception as e:
            logger.error(f"通知发送异常: {e}")
            result["status"] = "failed"
            result["error"] = str(e)

            # 记录失败通知
            await self._record_notification(
                alarm=alarm,
                rule=rule,
                channel=channel,
                recipients=recipients,
                success=False,
                template_data=template_data,
                error_message=str(e)
            )

        return result

    async def _send_email(self, recipients: List[str], template_data: dict) -> bool:
        """
        发送邮件通知

        Args:
            recipients: 邮件接收人列表
            template_data: 模板数据

        Returns:
            bool: 是否发送成功
        """
        if not self.email_service:
            logger.warning("邮件服务未配置")
            return False

        # 邮件接收人（筛选出邮箱格式的）
        email_recipients = [r for r in recipients if "@" in r]
        if not email_recipients:
            logger.warning("没有有效的邮件接收人")
            return False

        subject, body = self.template_service.render_email("alarm_email", template_data)
        return await self.email_service.send(
            to=email_recipients,
            subject=subject,
            content=body,
            html_content=body
        )

    async def _send_wechat(self, template_data: dict) -> bool:
        """
        发送微信通知

        Args:
            template_data: 模板数据

        Returns:
            bool: 是否发送成功
        """
        if not self.wechat_service:
            logger.warning("微信服务未配置")
            return False

        content = self.template_service.render_wechat_markdown("alarm_markdown", template_data)
        return await self.wechat_service.send_markdown(content)

    async def _record_notification(
        self,
        alarm: Alarm,
        rule: NotificationRule,
        channel: str,
        recipients: List[str],
        success: bool,
        template_data: dict,
        error_message: str = None
    ):
        """
        记录通知发送

        Args:
            alarm: 告警对象
            rule: 通知规则
            channel: 渠道
            recipients: 接收人
            success: 是否成功
            template_data: 模板数据
            error_message: 错误信息
        """
        record = NotificationRecord(
            tenant_id=alarm.tenant_id,
            alarm_id=alarm.id,
            rule_id=rule.id,
            channel=channel,
            recipient=", ".join(recipients),
            subject=f"[告警通知] {template_data.get('alarm_type')} - {template_data.get('device_id')}",
            content=self.template_service.render("alarm_notification", template_data),
            status=NotificationStatus.SENT if success else NotificationStatus.FAILED,
            error_message=error_message,
            sent_at=datetime.now(timezone.utc) if success else None
        )
        self.db.add(record)
        await self.db.commit()

        logger.debug(f"记录通知: {record.id}, status={record.status}")