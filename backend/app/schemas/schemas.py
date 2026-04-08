"""
Pydantic Schemas
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


# ============ 用户认证 ============
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    username: Optional[str] = None
    tenant_id: Optional[int] = None


class LoginRequest(BaseModel):
    username: str
    password: str


# ============ 用户 ============
class UserBase(BaseModel):
    username: str
    role: str = "viewer"


class UserCreate(UserBase):
    password: str
    tenant_id: int


class UserResponse(UserBase):
    id: int
    tenant_id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ============ 租户 ============
class TenantBase(BaseModel):
    name: str
    code: str


class TenantCreate(TenantBase):
    settings: Dict[str, Any] = {}


class TenantResponse(TenantBase):
    id: int
    settings: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True


# ============ 分区 ============
class ZoneBase(BaseModel):
    name: str
    parent_id: Optional[int] = None
    description: Optional[str] = None
    sort_order: int = 0


class ZoneCreate(ZoneBase):
    tenant_id: int


class ZoneUpdate(BaseModel):
    name: Optional[str] = None
    parent_id: Optional[int] = None
    description: Optional[str] = None
    sort_order: Optional[int] = None


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
    zone_id: Optional[int] = None


class DeviceCreate(DeviceBase):
    tenant_id: int
    sim_card: Optional[str] = None


class DeviceUpdate(BaseModel):
    name: Optional[str] = None
    zone_id: Optional[int] = None
    sim_card: Optional[str] = None


class DeviceResponse(DeviceBase):
    id: int
    tenant_id: int
    protocol_version: str
    sim_card: Optional[str]
    is_online: bool
    last_seen_at: Optional[datetime]
    settings: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True


class DeviceWithDataResponse(DeviceResponse):
    """设备信息 + 最新数据"""
    temp: Optional[float] = None
    humi: Optional[float] = None
    airstate: Optional[int] = None
    current: Optional[float] = None


# ============ 设备数据 ============
class DeviceDataBase(BaseModel):
    device_id: str
    temp: Optional[float] = None
    humi: Optional[float] = None
    airstate: Optional[int] = None
    current: Optional[float] = None
    csq: Optional[float] = None
    air_err: Optional[int] = None
    alarmtemp: Optional[int] = None
    alarmhumi: Optional[int] = None


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
    message: Optional[str] = None
    details: Dict[str, Any] = {}


class AlarmCreate(AlarmBase):
    tenant_id: int
    occurred_at: datetime


class AlarmUpdate(BaseModel):
    is_resolved: Optional[bool] = None


class AlarmResponse(AlarmBase):
    id: int
    tenant_id: int
    is_resolved: bool
    occurred_at: datetime
    resolved_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


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
    data: Dict[str, Any]
    timestamp: str


class MQTTParameterMessage(BaseModel):
    """设备参数消息"""
    mid: int
    data: Dict[str, Any]
    timestamp: str


class MQTTControlMessage(BaseModel):
    """远程控制消息"""
    airstate: Optional[int] = None  # 0关机, 1开机
    reset: Optional[int] = None     # 复位
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
    items: List[Any]
    total: int
    page: int
    page_size: int
    total_pages: int