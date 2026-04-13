"""
微信企业号通知服务

使用企业微信 Webhook 发送消息
"""
import logging
from typing import Optional

import httpx
from loguru import logger


class WeChatNotificationService:
    """
    微信企业号通知服务

    功能：
    - 发送文本消息
    - 发送 Markdown 消息
    - 异步 HTTP 发送
    """

    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    async def send(self, content: str) -> bool:
        """
        发送文本消息

        Args:
            content: 文本内容

        Returns:
            bool: 是否发送成功
        """
        payload = {
            "msgtype": "text",
            "text": {
                "content": content
            }
        }

        return await self._send_request(payload)

    async def send_markdown(self, content: str) -> bool:
        """
        发送 Markdown 消息

        Args:
            content: Markdown 格式内容

        Returns:
            bool: 是否发送成功
        """
        payload = {
            "msgtype": "markdown",
            "markdown": {
                "content": content
            }
        }

        return await self._send_request(payload)

    async def _send_request(self, payload: dict) -> bool:
        """
        发送 HTTP 请求到微信 Webhook

        Args:
            payload: 请求体

        Returns:
            bool: 是否发送成功
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    self.webhook_url,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )

                if response.status_code == 200:
                    result = response.json()
                    if result.get("errcode") == 0:
                        logger.info("微信消息发送成功")
                        return True
                    else:
                        logger.error(f"微信消息发送失败: {result.get('errmsg')}")
                        return False
                else:
                    logger.error(f"微信 Webhook 请求失败: status={response.status_code}")
                    return False

        except httpx.TimeoutException:
            logger.error("微信 Webhook 请求超时")
            return False
        except Exception as e:
            logger.error(f"微信消息发送异常: {e}")
            return False

    async def send_with_template(
        self,
        template_name: str,
        data: dict
    ) -> bool:
        """
        使用模板发送微信消息

        Args:
            template_name: 模板名称
            data: 模板数据

        Returns:
            bool: 是否发送成功
        """
        from app.services.notification.template_service import NotificationTemplateService

        template_service = NotificationTemplateService()
        content = template_service.render_wechat_markdown(template_name, data)

        return await self.send_markdown(content)