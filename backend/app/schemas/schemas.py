"""
Pydantic Schemas
"""
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


# ============ 用户认证 ============
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer"
            }
        }


class TokenData(BaseModel):
    username: str | None = None
    tenant_id: int | None = None


class LoginRequest(BaseModel):
    username: str
    password: str


# ============ 用户 ============
class UserBase(BaseModel):
    username: str
    role: str = "viewer"


class UserCreate(UserBase):
    """用于内部创建用户（包含tenant_id）"""
    password: str
    tenant_id: int


class UserCreateAPI(UserBase):
    """用于API创建用户（不包含tenant_id，从当前用户获取）"""
    password: str


class UserUpdate(BaseModel):
    """用户更新"""
    role: str | None = None


class UserResponse(UserBase):
    id: int
    tenant_id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "username": "admin",
                "role": "admin",
                "tenant_id": 1,
                "is_active": True,
                "created_at": "2024-01-01T00:00:00Z"
            }
        }


class UserStatusUpdate(BaseModel):
    """用户状态更新"""
    is_active: bool


# ============ 租户 ============
class TenantBase(BaseModel):
    name: str
    code: str


class TenantCreate(TenantBase):
    settings: dict[str, Any] = {}


class TenantResponse(TenantBase):
    id: int
    settings: dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True


# ============ 分区 ============
class ZoneBase(BaseModel):
    name: str
    parent_id: int | None = None
    description: str | None = None
    sort_order: int = 0


class ZoneCreate(ZoneBase):
    tenant_id: int


class ZoneUpdate(BaseModel):
    name: str | None = None
    parent_id: int | None = None
    description: str | None = None
    sort_order: int | None = None


class ZoneResponse(ZoneBase):
    id: int
    tenant_id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ============ 设备 ============
class DeviceBase(BaseModel):
    device_id: str = Field(..., description="4G模组IMEI号")
    name: str
    zone_id: int | None = None


class DeviceCreate(DeviceBase):
    tenant_id: int
    sim_card: str | None = None


class DeviceUpdate(BaseModel):
    name: str | None = None
    zone_id: int | None = None
    sim_card: str | None = None


class DeviceResponse(DeviceBase):
    id: int
    tenant_id: int
    protocol_version: str
    sim_card: str | None
    is_online: bool
    last_seen_at: datetime | None
    settings: dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "device_id": "IMEI12345678",
                "name": "会议室空调",
                "zone_id": 1,
                "tenant_id": 1,
                "protocol_version": "V20",
                "sim_card": "13800138000",
                "is_online": True,
                "last_seen_at": "2024-04-13T10:30:00Z",
                "settings": {"temp_set": 26},
                "created_at": "2024-01-01T00:00:00Z"
            }
        }


class DeviceWithDataResponse(DeviceResponse):
    """设备信息 + 最新数据"""
    temp: float | None = None
    humi: float | None = None
    airstate: int | None = None
    current: float | None = None


# ============ 设备数据 ============
class DeviceDataBase(BaseModel):
    device_id: str
    temp: float | None = None
    humi: float | None = None
    airstate: int | None = None
    current: float | None = None
    csq: float | None = None
    air_err: int | None = None
    alarmtemp: int | None = None
    alarmhumi: int | None = None


class DeviceDataCreate(DeviceDataBase):
    tenant_id: int


class DeviceDataResponse(DeviceDataBase):
    id: int
    time: datetime
    tenant_id: int

    class Config:
        from_attributes = True


# ============ 告警 ============
class AlarmBase(BaseModel):
    device_id: str
    type: str
    severity: str
    message: str | None = None
    details: dict[str, Any] = {}


class AlarmCreate(AlarmBase):
    tenant_id: int
    occurred_at: datetime


class AlarmUpdate(BaseModel):
    is_resolved: bool | None = None


class AlarmResponse(AlarmBase):
    id: int
    tenant_id: int
    is_resolved: bool
    occurred_at: datetime
    resolved_at: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "device_id": "IMEI12345678",
                "type": "temperature_high",
                "severity": "warning",
                "message": "温度超过设定值",
                "details": {"temp": 30, "threshold": 28},
                "tenant_id": 1,
                "is_resolved": False,
                "occurred_at": "2024-04-13T10:30:00Z",
                "resolved_at": None,
                "created_at": "2024-04-13T10:30:00Z"
            }
        }


# ============ MQTT 消息 ============
class MQTTLoginMessage(BaseModel):
    """设备上线消息"""
    mid: int
    deviceId: str
    productId: str
    timestamp: str


class MQTTDataMessage(BaseModel):
    """设备数据上送消息"""
    mid: int
    data: dict[str, Any]
    timestamp: str


class MQTTParameterMessage(BaseModel):
    """设备参数消息"""
    mid: int
    data: dict[str, Any]
    timestamp: str


class MQTTControlMessage(BaseModel):
    """远程控制消息"""
    airstate: int | None = None  # 0关机, 1开机
    reset: int | None = None     # 复位
    timestamp: str


class MQTTSetParamMessage(BaseModel):
    """设置参数消息"""
    Name: str
    Value: Any
    timestamp: str


# ============ 仪表盘统计 ============
class DashboardStats(BaseModel):
    """仪表盘统计"""
    total_devices: int
    online_devices: int
    offline_devices: int
    total_alarms: int
    unresolved_alarms: int


# ============ 通用响应 ============
class Message(BaseModel):
    message: str


class PaginatedResponse(BaseModel):
    """分页响应"""
    items: list[Any]
    total: int
    page: int
    page_size: int
    total_pages: int


# ============ 批量操作 ============
class BatchControlRequest(BaseModel):
    """批量控制请求"""
    device_ids: list[int] = Field(..., min_length=1, max_length=100, description="设备ID列表")
    airstate: int = Field(..., ge=0, le=1, description="0关机，1开机")


class BatchDeleteRequest(BaseModel):
    """批量删除请求"""
    device_ids: list[int] = Field(..., min_length=1, max_length=100, description="设备ID列表")


class BatchMoveZoneRequest(BaseModel):
    """批量迁移分区请求"""
    device_ids: list[int] = Field(..., min_length=1, max_length=100, description="设备ID列表")
    zone_id: int | None = Field(None, description="目标分区ID（null表示移出分区）")


class BatchOperationResponse(BaseModel):
    """批量操作响应"""
    success_count: int = Field(..., description="成功数量")
    failed_count: int = Field(..., description="失败数量")
    failed_details: list[dict[str, Any]] = Field(default_factory=list, description="失败详情")


class BatchSetParamRequest(BaseModel):
    """批量设置参数请求"""
    device_ids: list[int] = Field(..., min_length=1, max_length=100, description="设备ID列表")
    params: dict[str, Any] = Field(..., description="参数键值对")


# ============ 通知规则 ============
class NotificationRuleBase(BaseModel):
    """通知规则基础"""
    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = None
    alarm_types: list[str] = Field(..., min_length=1)
    severities: list[str] = Field(..., min_length=1)
    channels: list[str] = Field(..., min_length=1)
    recipients: list[str] = Field(..., min_length=1)
    cooldown_minutes: int = Field(default=30, ge=1, le=1440)


class NotificationRuleResponse(NotificationRuleBase):
    """通知规则响应"""
    id: int
    tenant_id: int
    is_enabled: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============ 通知记录 ============
class NotificationRecordResponse(BaseModel):
    """通知记录响应"""
    id: int
    tenant_id: int
    alarm_id: int | None
    rule_id: int | None
    channel: str
    recipient: str
    subject: str | None
    content: str
    status: str
    error_message: str | None
    sent_at: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True
