"""
数据库模型
"""
from datetime import UTC, datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class NotificationChannel:
    """通知渠道枚举"""
    EMAIL = "email"
    WECHAT = "wechat"
    SMS = "sms"


class NotificationStatus:
    """通知状态枚举"""
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    RATE_LIMITED = "rate_limited"


class BackupStatus:
    """备份状态枚举"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


def utc_now() -> datetime:
    """获取 UTC 时间（timezone-aware）"""
    return datetime.now(UTC)


class Tenant(Base):
    """租户表"""
    __tablename__ = "tenants"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    code: Mapped[str] = mapped_column(String(20), unique=True)
    settings: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    # 关系
    users: Mapped[list["User"]] = relationship(back_populates="tenant", cascade="all, delete-orphan")
    zones: Mapped[list["Zone"]] = relationship(back_populates="tenant", cascade="all, delete-orphan")
    devices: Mapped[list["Device"]] = relationship(back_populates="tenant", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Tenant(id={self.id}, name={self.name}, code={self.code})>"


class User(Base):
    """用户表"""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"))
    username: Mapped[str] = mapped_column(String(50), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default="viewer")  # admin, operator, viewer
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    # 关系
    tenant: Mapped["Tenant"] = relationship(back_populates="users")

    # 索引
    __table_args__ = (
        Index('idx_users_tenant_id', 'tenant_id'),
    )

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, role={self.role})>"


class Zone(Base):
    """分区表"""
    __tablename__ = "zones"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(100))
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("zones.id", ondelete="SET NULL"), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    # 关系
    tenant: Mapped["Tenant"] = relationship(back_populates="zones")
    devices: Mapped[list["Device"]] = relationship(back_populates="zone")

    # 索引
    __table_args__ = (
        Index('idx_zones_tenant_id', 'tenant_id'),
    )

    def __repr__(self):
        return f"<Zone(id={self.id}, name={self.name})>"


class Device(Base):
    """设备表"""
    __tablename__ = "devices"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"))
    zone_id: Mapped[int | None] = mapped_column(ForeignKey("zones.id", ondelete="SET NULL"), nullable=True)
    device_id: Mapped[str] = mapped_column(String(20), unique=True)  # IMEI号
    name: Mapped[str] = mapped_column(String(100))
    protocol_version: Mapped[str] = mapped_column(String(10), default="V10")
    sim_card: Mapped[str | None] = mapped_column(String(30), nullable=True)
    firmware_version: Mapped[str | None] = mapped_column(String(20), nullable=True)
    is_online: Mapped[bool] = mapped_column(Boolean, default=False)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    settings: Mapped[dict] = mapped_column(JSONB, default=dict)
    extra_data: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    # 关系
    tenant: Mapped["Tenant"] = relationship(back_populates="devices")
    zone: Mapped[Optional["Zone"]] = relationship(back_populates="devices")

    # 索引
    __table_args__ = (
        Index('idx_devices_tenant_id', 'tenant_id'),
        Index('idx_devices_zone_id', 'zone_id'),  # Zone 关联索引
        Index('idx_devices_is_online', 'is_online'),
        Index('idx_devices_last_seen', 'last_seen_at'),
        Index('idx_devices_protocol_version', 'protocol_version'),  # 协议版本筛选索引
    )

    def __repr__(self):
        return f"<Device(id={self.id}, device_id={self.device_id}, name={self.name})>"


class DeviceData(Base):
    """设备时序数据表"""
    __tablename__ = "device_data"

    id: Mapped[int] = mapped_column(primary_key=True)
    time: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    device_id: Mapped[str] = mapped_column(String(20))
    tenant_id: Mapped[int] = mapped_column(Integer)
    temp: Mapped[float | None] = mapped_column(Float, nullable=True)
    humi: Mapped[float | None] = mapped_column(Float, nullable=True)
    airstate: Mapped[int | None] = mapped_column(Integer, nullable=True)
    current: Mapped[float | None] = mapped_column(Float, nullable=True)
    csq: Mapped[float | None] = mapped_column(Float, nullable=True)
    air_err: Mapped[int | None] = mapped_column(Integer, nullable=True)
    alarmtemp: Mapped[int | None] = mapped_column(Integer, nullable=True)
    alarmhumi: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # 索引
    __table_args__ = (
        Index('idx_device_data_time', 'time'),
        Index('idx_device_data_device_id', 'device_id', 'time'),
        Index('idx_device_data_airstate', 'device_id', 'tenant_id', 'airstate'),  # 运行时间查询优化
    )

    def __repr__(self):
        return f"<DeviceData(time={self.time}, device_id={self.device_id})>"


class Alarm(Base):
    """告警表"""
    __tablename__ = "alarms"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"))
    device_id: Mapped[str] = mapped_column(String(20))
    type: Mapped[str] = mapped_column(String(20))  # offline, illegal_on, temp_alarm
    severity: Mapped[str] = mapped_column(String(10))  # high, medium, low
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    details: Mapped[dict] = mapped_column(JSONB, default=dict)
    is_resolved: Mapped[bool] = mapped_column(Boolean, default=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    # 索引
    __table_args__ = (
        Index('idx_alarms_tenant_id', 'tenant_id'),
        Index('idx_alarms_device_id', 'device_id'),
        Index('idx_alarms_occurred_at', 'occurred_at'),
    )

    def __repr__(self):
        return f"<Alarm(id={self.id}, type={self.type}, device_id={self.device_id})>"


class ProtocolVersion(Base):
    """协议版本注册表"""
    __tablename__ = "protocol_versions"

    id: Mapped[int] = mapped_column(primary_key=True)
    version_code: Mapped[str] = mapped_column(String(10), unique=True)  # V10, V20
    version_number: Mapped[int] = mapped_column(Integer)
    feature_params: Mapped[dict] = mapped_column(JSONB, default=dict)
    param_mappings: Mapped[dict] = mapped_column(JSONB, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    def __repr__(self):
        return f"<ProtocolVersion(code={self.version_code}, number={self.version_number})>"


class OperationLog(Base):
    """操作日志表"""
    __tablename__ = "operation_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"))
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action: Mapped[str] = mapped_column(String(50))  # create_device, update_device, delete_device, etc.
    resource_type: Mapped[str] = mapped_column(String(50))  # device, zone, user, etc.
    resource_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    details: Mapped[dict] = mapped_column(JSONB, default=dict)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    # 索引
    __table_args__ = (
        Index('idx_operation_logs_tenant_id', 'tenant_id'),
        Index('idx_operation_logs_user_id', 'user_id'),
        Index('idx_operation_logs_action', 'action'),
        Index('idx_operation_logs_resource', 'resource_type', 'resource_id'),
        Index('idx_operation_logs_created_at', 'created_at'),
    )

    def __repr__(self):
        return f"<OperationLog(action={self.action}, resource_type={self.resource_type})>"


class NotificationRule(Base):
    """通知规则表"""
    __tablename__ = "notification_rules"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    alarm_types: Mapped[list] = mapped_column(JSONB, default=list)  # ["offline", "illegal_on", ...]
    severities: Mapped[list] = mapped_column(JSONB, default=list)  # ["high", "medium", "low"]
    channels: Mapped[list] = mapped_column(JSONB, default=list)  # ["email", "wechat"]
    recipients: Mapped[list] = mapped_column(JSONB, default=list)  # 邮箱列表或用户ID列表
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    cooldown_minutes: Mapped[int] = mapped_column(Integer, default=30)  # 冷却时间（分钟）
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    # 索引
    __table_args__ = (
        Index('idx_notification_rules_tenant_id', 'tenant_id'),
        Index('idx_notification_rules_enabled', 'is_enabled'),
    )

    def __repr__(self):
        return f"<NotificationRule(id={self.id}, name={self.name})>"


class NotificationRecord(Base):
    """通知记录表"""
    __tablename__ = "notification_records"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"))
    alarm_id: Mapped[int | None] = mapped_column(ForeignKey("alarms.id", ondelete="SET NULL"), nullable=True)
    rule_id: Mapped[int | None] = mapped_column(ForeignKey("notification_rules.id", ondelete="SET NULL"), nullable=True)
    channel: Mapped[str] = mapped_column(String(20))  # email, wechat, sms
    recipient: Mapped[str] = mapped_column(String(255))
    subject: Mapped[str | None] = mapped_column(String(255), nullable=True)
    content: Mapped[Text] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending, sent, failed, rate_limited
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    # 索引
    __table_args__ = (
        Index('idx_notification_records_tenant_id', 'tenant_id'),
        Index('idx_notification_records_alarm_id', 'alarm_id'),
        Index('idx_notification_records_status', 'status'),
        Index('idx_notification_records_created_at', 'created_at'),
    )

    def __repr__(self):
        return f"<NotificationRecord(id={self.id}, channel={self.channel}, status={self.status})>"


class BackupRecord(Base):
    """备份记录表"""
    __tablename__ = "backup_records"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int | None] = mapped_column(ForeignKey("tenants.id", ondelete="SET NULL"), nullable=True)
    backup_type: Mapped[str] = mapped_column(String(20))  # manual, scheduled, auto
    file_path: Mapped[str] = mapped_column(String(255))
    file_size: Mapped[int | None] = mapped_column(Integer, nullable=True)  # bytes
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending, in_progress, completed, failed
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    # 索引
    __table_args__ = (
        Index('idx_backup_records_tenant_id', 'tenant_id'),
        Index('idx_backup_records_status', 'status'),
        Index('idx_backup_records_backup_type', 'backup_type'),
        Index('idx_backup_records_created_at', 'created_at'),
    )

    def __repr__(self):
        return f"<BackupRecord(id={self.id}, backup_type={self.backup_type}, status={self.status})>"


class RestoreRecord(Base):
    """恢复记录表"""
    __tablename__ = "restore_records"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"))
    backup_id: Mapped[int] = mapped_column(ForeignKey("backup_records.id", ondelete="SET NULL"), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending, in_progress, completed, failed, rolled_back
    progress: Mapped[int] = mapped_column(Integer, default=0)  # 0-100
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    safety_backup_id: Mapped[int | None] = mapped_column(ForeignKey("backup_records.id"), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    # 索引
    __table_args__ = (
        Index('idx_restore_records_tenant_id', 'tenant_id'),
        Index('idx_restore_records_status', 'status'),
        Index('idx_restore_records_backup_id', 'backup_id'),
        Index('idx_restore_records_created_at', 'created_at'),
    )

    def __repr__(self):
        return f"<RestoreRecord(id={self.id}, status={self.status}, progress={self.progress})>"
