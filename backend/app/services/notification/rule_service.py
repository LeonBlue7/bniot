"""
通知规则服务

匹配告警与通知规则，检查冷却时间
"""
from datetime import datetime, timezone, timedelta
from typing import List

from loguru import logger
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Alarm, NotificationRule, NotificationRecord


class NotificationRuleService:
    """
    通知规则服务

    功能：
    - 匹配告警与通知规则
    - 检查通知冷却时间
    - 管理通知规则 CRUD
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def match_rules(self, alarm: Alarm) -> List[NotificationRule]:
        """
        匹配告警与通知规则

        Args:
            alarm: 告警对象

        Returns:
            List[NotificationRule]: 匹配的规则列表
        """
        # 查询该租户下启用的规则
        result = await self.db.execute(
            select(NotificationRule).where(
                and_(
                    NotificationRule.tenant_id == alarm.tenant_id,
                    NotificationRule.is_enabled == True
                )
            )
        )
        all_rules = result.scalars().all()

        matched_rules = []
        for rule in all_rules:
            # 检查告警类型匹配
            if alarm.type not in rule.alarm_types:
                continue

            # 检查严重程度匹配
            if alarm.severity not in rule.severities:
                continue

            matched_rules.append(rule)

        logger.debug(
            f"告警 {alarm.id} 匹配规则: "
            f"总规则 {len(all_rules)}, 匹配 {len(matched_rules)}"
        )

        return matched_rules

    async def check_cooldown(self, rule: NotificationRule, alarm: Alarm) -> bool:
        """
        检查通知冷却时间

        Args:
            rule: 通知规则
            alarm: 告警对象

        Returns:
            bool: 是否在冷却期内（True 表示需要跳过发送）
        """
        # 查询最近发送的通知记录
        cooldown_time = datetime.now(timezone.utc) - timedelta(minutes=rule.cooldown_minutes)

        result = await self.db.execute(
            select(NotificationRecord).where(
                and_(
                    NotificationRecord.tenant_id == alarm.tenant_id,
                    NotificationRecord.rule_id == rule.id,
                    NotificationRecord.sent_at >= cooldown_time
                )
            ).order_by(NotificationRecord.sent_at.desc()).limit(1)
        )
        recent_record = result.scalar_one_or_none()

        if recent_record:
            logger.debug(
                f"规则 {rule.id} 在冷却期内，"
                f"上次发送时间: {recent_record.sent_at}"
            )
            return True

        return False

    async def create_rule(
        self,
        tenant_id: int,
        name: str,
        alarm_types: List[str],
        severities: List[str],
        channels: List[str],
        recipients: List[str],
        description: str = None,
        cooldown_minutes: int = 30,
        is_enabled: bool = True
    ) -> NotificationRule:
        """
        创建通知规则

        Args:
            tenant_id: 租户 ID
            name: 规则名称
            alarm_types: 告警类型列表
            severities: 严重程度列表
            channels: 通知渠道列表
            recipients: 接收人列表
            description: 规则描述
            cooldown_minutes: 冷却时间（分钟）
            is_enabled: 是否启用

        Returns:
            NotificationRule: 创建的规则
        """
        rule = NotificationRule(
            tenant_id=tenant_id,
            name=name,
            description=description,
            alarm_types=alarm_types,
            severities=severities,
            channels=channels,
            recipients=recipients,
            is_enabled=is_enabled,
            cooldown_minutes=cooldown_minutes
        )
        self.db.add(rule)
        await self.db.commit()
        await self.db.refresh(rule)

        logger.info(f"创建通知规则: {rule.id}, name={name}")
        return rule

    async def update_rule(
        self,
        rule_id: int,
        tenant_id: int,
        **kwargs
    ) -> NotificationRule | None:
        """
        更新通知规则

        Args:
            rule_id: 规则 ID
            tenant_id: 租户 ID（用于权限验证）
            **kwargs: 更新的字段

        Returns:
            NotificationRule | None: 更新后的规则（如果存在）
        """
        result = await self.db.execute(
            select(NotificationRule).where(
                and_(
                    NotificationRule.id == rule_id,
                    NotificationRule.tenant_id == tenant_id
                )
            )
        )
        rule = result.scalar_one_or_none()

        if not rule:
            return None

        for key, value in kwargs.items():
            if hasattr(rule, key):
                setattr(rule, key, value)

        await self.db.commit()
        await self.db.refresh(rule)

        logger.info(f"更新通知规则: {rule_id}")
        return rule

    async def delete_rule(self, rule_id: int, tenant_id: int) -> bool:
        """
        删除通知规则

        Args:
            rule_id: 规则 ID
            tenant_id: 租户 ID（用于权限验证）

        Returns:
            bool: 是否删除成功
        """
        result = await self.db.execute(
            select(NotificationRule).where(
                and_(
                    NotificationRule.id == rule_id,
                    NotificationRule.tenant_id == tenant_id
                )
            )
        )
        rule = result.scalar_one_or_none()

        if not rule:
            return False

        await self.db.delete(rule)
        await self.db.commit()

        logger.info(f"删除通知规则: {rule_id}")
        return True

    async def get_rules_by_tenant(self, tenant_id: int) -> List[NotificationRule]:
        """
        获取租户的所有通知规则

        Args:
            tenant_id: 租户 ID

        Returns:
            List[NotificationRule]: 规则列表
        """
        result = await self.db.execute(
            select(NotificationRule).where(
                NotificationRule.tenant_id == tenant_id
            ).order_by(NotificationRule.created_at.desc())
        )
        return result.scalars().all()