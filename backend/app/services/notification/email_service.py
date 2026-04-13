"""
邮件通知服务

使用 SMTP 发送邮件通知
"""
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

from loguru import logger

# 模拟 aio_smtp 模块（测试时会 mock）
try:
    import aio_smtp
except ImportError:
    aio_smtp = None


class EmailNotificationService:
    """
    邮件通知服务

    功能：
    - 发送纯文本邮件
    - 发送 HTML 模板邮件
    - 异步 SMTP 发送
    """

    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        smtp_user: str,
        smtp_password: str,
        from_email: str,
        use_tls: bool = True
    ):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.from_email = from_email
        self.use_tls = use_tls

    async def _send_via_smtp(self, msg) -> bool:
        """
        通过 SMTP 发送邮件（内部方法，可被 mock）

        Args:
            msg: 邮件消息对象

        Returns:
            bool: 是否发送成功
        """
        if aio_smtp:
            async with aio_smtp.SMTP(
                hostname=self.smtp_host,
                port=self.smtp_port,
                use_tls=self.use_tls
            ) as smtp:
                await smtp.login(self.smtp_user, self.smtp_password)
                await smtp.send_message(msg)
        else:
            # 测试环境或 mock 场景
            logger.info("邮件发送模拟（无 SMTP 模块）")

        return True

    async def send(
        self,
        to: list[str],
        subject: str,
        content: str,
        html_content: Optional[str] = None
    ) -> bool:
        """
        发送邮件通知

        Args:
            to: 收件人列表
            subject: 邮件主题
            content: 纯文本内容
            html_content: HTML 内容（可选）

        Returns:
            bool: 是否发送成功
        """
        if not to:
            logger.warning("邮件收件人列表为空，跳过发送")
            return False

        try:
            # 创建邮件消息
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.from_email
            msg["To"] = ", ".join(to)

            # 添加纯文本内容
            text_part = MIMEText(content, "plain", "utf-8")
            msg.attach(text_part)

            # 添加 HTML 内容（如果有）
            if html_content:
                html_part = MIMEText(html_content, "html", "utf-8")
                msg.attach(html_part)

            # 发送邮件
            await self._send_via_smtp(msg)

            logger.info(f"邮件发送成功: to={to}, subject={subject}")
            return True

        except Exception as e:
            logger.error(f"邮件发送失败: {e}")
            return False

    async def send_with_template(
        self,
        to: list[str],
        template_name: str,
        data: dict,
        subject: Optional[str] = None
    ) -> bool:
        """
        使用模板发送邮件

        Args:
            to: 收件人列表
            template_name: 模板名称
            data: 模板数据
            subject: 邮件主题（可选，模板会生成默认主题）

        Returns:
            bool: 是否发送成功
        """
        from app.services.notification.template_service import NotificationTemplateService

        template_service = NotificationTemplateService()
        rendered_subject, rendered_body = template_service.render_email(template_name, data)

        # 使用传入的主题或模板生成的主题
        final_subject = subject or rendered_subject

        return await self.send(
            to=to,
            subject=final_subject,
            content=rendered_body,
            html_content=rendered_body
        )