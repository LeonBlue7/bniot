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
    wechat_openid: str | None = None
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
                "wechat_openid": None,
                "created_at": "2024-01-01T00:00:00Z"
            }
        }


class UserStatusUpdate(BaseModel):
    """用户状态更新"""
    is_active: bool


class PasswordChangeRequest(BaseModel):
    """修改密码请求"""
    old_password: str = Field(..., min_length=6, description="当前密码")
    new_password: str = Field(..., min_length=6, description="新密码")


# ============ 微信小程序登录 ============
class WechatLoginRequest(BaseModel):
    """微信小程序登录请求"""
    code: str = Field(..., min_length=1, description="wx.login() 获取的 code")


class WechatLoginResponse(BaseModel):
    """微信小程序登录响应"""
    access_token: str
    token_type: str = "bearer"
    is_new_user: bool = Field(..., description="是否为新用户（首次微信登录）")
    user: "UserResponse"

    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "is_new_user": False,
                "user": {
                    "id": 1,
                    "username": "wechat_user_abc123",
                    "role": "viewer",
                    "tenant_id": 1,
                    "is_active": True,
                    "created_at": "2024-01-01T00:00:00Z"
                }
            }
        }


class WechatBindRequest(BaseModel):
    """微信绑定请求"""
    code: str = Field(..., min_length=1, description="wx.login() 获取的 code")


class WechatBindResponse(BaseModel):
    """微信绑定响应"""
    success: bool
    message: str
    openid: str | None = Field(None, description="绑定成功的 openid")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "微信绑定成功",
                "openid": "oABC123xyz456"
            }
        }


class WechatUnbindResponse(BaseModel):
    """微信解绑响应"""
    success: bool
    message: str

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "微信解绑成功"
            }
        }


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


class DeviceListItemResponse(DeviceBase):
    """设备列表项响应 - 包含实时数据和分区信息"""
    id: int
    tenant_id: int
    protocol_version: str | None = None
    temp: float | None = None
    humi: float | None = None
    alarmtemp: int | None = None
    zone_name: str | None = None
    is_online: bool
    last_seen_at: datetime | None
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
                "temp": 25.5,
                "humi": 60.2,
                "alarmtemp": 0,
                "zone_name": "办公区",
                "is_online": True,
                "last_seen_at": "2024-04-13T10:30:00Z",
                "created_at": "2024-01-01T00:00:00Z"
            }
        }


class DeviceListResponse(BaseModel):
    """设备列表分页响应"""
    items: list[DeviceListItemResponse]
    total: int
    skip: int
    limit: int


class DeviceWithDataResponse(DeviceResponse):
    """设备信息 + 最新数据"""
    temp: float | None = None
    humi: float | None = None
    airstate: int | None = None
    current: float | None = None


class DeviceDetailResponse(DeviceResponse):
    """设备详情响应 - 包含完整信息"""
    zone_name: str | None = None
    firmware_version: str | None = None
    csq: float | None = None
    alarmhumi: int | None = None
    air_err: int | None = None
    temp: float | None = None
    humi: float | None = None
    airstate: int | None = None
    current: float | None = None
    alarmtemp: int | None = None
    # 运行时间统计（仅支持airstate的协议版本）
    supports_runtime: bool = False
    today_runtime: float | None = None  # 当天运行时间（小时）
    month_runtime: float | None = None  # 当月运行时间（小时）

    class Config:
        from_attributes = True


class DeviceEventItem(BaseModel):
    """开关机事件项"""
    time: str = Field(..., description="事件时间（ISO格式）")
    action: str = Field(..., description="动作：开机/关机")
    duration: float | None = Field(None, description="运行时长（小时），仅关机事件有")

    class Config:
        json_schema_extra = {
            "example": {
                "time": "2024-04-13T10:30:00",
                "action": "关机",
                "duration": 2.5
            }
        }


class DeviceEventsResponse(BaseModel):
    """开关机事件记录响应"""
    supported: bool = Field(..., description="是否支持空调状态监控")
    message: str = Field(default="", description="不支持时的提示消息")
    events: list[DeviceEventItem] = Field(default_factory=list, description="事件列表")
    total: int = Field(default=0, description="总数量")
    page: int = Field(default=1, description="当前页")
    page_size: int = Field(default=20, description="每页数量")

    class Config:
        json_schema_extra = {
            "example": {
                "supported": True,
                "message": "",
                "events": [
                    {"time": "2024-04-13T10:30:00", "action": "关机", "duration": 2.5},
                    {"time": "2024-04-13T08:00:00", "action": "开机", "duration": None}
                ],
                "total": 50,
                "page": 1,
                "page_size": 20
            }
        }


class DeviceRuntimeResponse(BaseModel):
    """运行时间统计响应"""
    supported: bool = Field(..., description="是否支持运行时间统计")
    message: str = Field(default="", description="不支持时的提示消息")
    today_runtime: float | None = Field(None, description="当天运行时间（小时）")
    month_runtime: float | None = Field(None, description="当月运行时间（小时）")

    class Config:
        json_schema_extra = {
            "example": {
                "supported": True,
                "message": "",
                "today_runtime": 5.5,
                "month_runtime": 120.0
            }
        }


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


class SetParamRequest(BaseModel):
    """单个参数设置请求"""
    param_code: str = Field(..., description="参数编号")
    param_value: Any = Field(..., description="参数值")


class SetParamResponse(BaseModel):
    """参数设置响应"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="响应消息")
    param_code: str | None = Field(None, description="参数编号")
    validation_errors: list[str] | None = Field(None, description="验证错误列表")


class ParamInfoResponse(BaseModel):
    """参数信息响应"""
    code: str = Field(..., description="参数编号")
    name: str = Field(..., description="参数名称")
    type: str = Field(..., description="参数类型")
    range: str | None = Field(None, description="参数范围")
    desc: str | None = Field(None, description="参数描述")
    current_value: Any | None = Field(None, description="当前值")


class DeviceParamsResponse(BaseModel):
    """设备参数响应"""
    version: str = Field(..., description="协议版本")
    params: list[ParamInfoResponse] = Field(..., description="参数列表")
    supported_codes: list[str] = Field(..., description="支持的参数编号列表")


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
