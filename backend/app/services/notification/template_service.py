"""
通知模板服务

渲染各类通知消息模板
"""
from datetime import datetime
from typing import Tuple
import re


class NotificationTemplateService:
    """
    通知模板服务

    功能：
    - 渲染告警通知模板
    - 渲染邮件模板
    - 渲染微信 Markdown 消息
    """

    # 预定义模板
    ALARM_TEMPLATES = {
        "alarm_notification": """
告警通知
设备ID: {device_id}
告警类型: {alarm_type}
严重程度: {severity}
消息: {message}
发生时间: {occurred_at}
""",
        "alarm_email": {
            "subject": "[告警通知] {alarm_type} - {device_id}",
            "body": """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
</head>
<body>
    <h2>告警通知</h2>
    <table style="width: 100%; border-collapse: collapse;">
        <tr>
            <td style="padding: 8px; border: 1px solid #ddd;">设备ID</td>
            <td style="padding: 8px; border: 1px solid #ddd;">{device_id}</td>
        </tr>
        <tr>
            <td style="padding: 8px; border: 1px solid #ddd;">告警类型</td>
            <td style="padding: 8px; border: 1px solid #ddd;">{alarm_type}</td>
        </tr>
        <tr>
            <td style="padding: 8px; border: 1px solid #ddd;">严重程度</td>
            <td style="padding: 8px; border: 1px solid #ddd;">{severity}</td>
        </tr>
        <tr>
            <td style="padding: 8px; border: 1px solid #ddd;">消息</td>
            <td style="padding: 8px; border: 1px solid #ddd;">{message}</td>
        </tr>
        <tr>
            <td style="padding: 8px; border: 1px solid #ddd;">发生时间</td>
            <td style="padding: 8px; border: 1px solid #ddd;">{occurred_at}</td>
        </tr>
    </table>
    <p>请及时处理此告警。</p>
</body>
</html>
"""
        },
        "alarm_markdown": """
## 告警通知

> **设备ID**: {device_id}
> **告警类型**: {alarm_type}
> **严重程度**: {severity}
> **发生时间**: {occurred_at}

**消息**: {message}

请及时处理此告警。
"""
    }

    def _safe_format(self, template: str, data: dict) -> str:
        """
        安全格式化模板，处理缺失字段

        Args:
            template: 模板字符串
            data: 数据字典

        Returns:
            str: 格式化后的字符串
        """
        # 创建包含所有占位符的完整数据字典
        # 找出模板中所有的占位符
        placeholders = re.findall(r'\{(\w+)\}', template)
        complete_data = {}
        for key in placeholders:
            complete_data[key] = data.get(key, '未知')
        # 添加原始数据中的其他字段
        for key, value in data.items():
            if key not in complete_data:
                complete_data[key] = value

        return template.format(**complete_data)

    def render(self, template_name: str, data: dict) -> str:
        """
        渲染通用模板

        Args:
            template_name: 模板名称
            data: 模板数据

        Returns:
            str: 渲染后的内容
        """
        template = self.ALARM_TEMPLATES.get(template_name, "")
        if not template:
            # 如果没有找到模板，返回默认格式
            return self._render_default(data)

        return self._safe_format(template, data)

    def render_email(self, template_name: str, data: dict) -> Tuple[str, str]:
        """
        渲染邮件模板

        Args:
            template_name: 模板名称
            data: 模板数据

        Returns:
            Tuple[str, str]: (主题, 正文)
        """
        template_data = self.ALARM_TEMPLATES.get(template_name, {})

        if isinstance(template_data, dict):
            subject_template = template_data.get("subject", "告警通知")
            body_template = template_data.get("body", "")

            subject = self._safe_format(subject_template, data)
            body = self._safe_format(body_template, data)
        else:
            # 如果模板不是字典格式，使用默认格式
            subject = f"[告警通知] {data.get('alarm_type', '未知')} - {data.get('device_id', '未知')}"
            body = self._safe_format(str(template_data), data)

        return subject, body

    def render_wechat_markdown(self, template_name: str, data: dict) -> str:
        """
        渲染微信 Markdown 消息

        Args:
            template_name: 模板名称
            data: 模板数据

        Returns:
            str: Markdown 格式内容
        """
        template = self.ALARM_TEMPLATES.get(template_name, "")
        if template:
            return self._safe_format(template, data)

        # 默认 Markdown 格式
        return self._render_default_markdown(data)

    def _render_default(self, data: dict) -> str:
        """渲染默认文本格式"""
        return f"""
告警通知
设备ID: {data.get('device_id', '未知')}
告警类型: {data.get('alarm_type', '未知')}
严重程度: {data.get('severity', '未知')}
消息: {data.get('message', '无')}
发生时间: {data.get('occurred_at', '未知')}
"""

    def _render_default_markdown(self, data: dict) -> str:
        """渲染默认 Markdown 格式"""
        return f"""
## 告警通知

> **设备ID**: {data.get('device_id', '未知')}
> **告警类型**: {data.get('alarm_type', '未知')}
> **严重程度**: {data.get('severity', '未知')}
> **发生时间**: {data.get('occurred_at', '未知')}

**消息**: {data.get('message', '无')}
"""