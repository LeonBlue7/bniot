"""
报表相关 Pydantic Schemas
Phase 4 报表与分析功能
"""
from datetime import datetime

from pydantic import BaseModel, Field


# ============ 能耗统计 ============
class EnergyStats(BaseModel):
    """能耗统计数据"""
    device_id: str
    device_name: str
    total_energy: float = Field(..., description="总能耗(kWh)")
    avg_power: float = Field(..., description="平均功率(W)")
    max_power: float = Field(..., description="最大功率(W)")
    runtime_hours: float = Field(..., description="运行时长(小时)")


class EnergyStatsQuery(BaseModel):
    """能耗统计查询参数"""
    start_time: datetime
    end_time: datetime
    device_ids: list[str] | None = None
    zone_id: int | None = None
    granularity: str = Field(default="day", description="统计粒度: hour/day/month")


class EnergyStatsResponse(BaseModel):
    """能耗统计响应"""
    data: list[EnergyStats]
    total_energy: float = Field(..., description="总能耗(kWh)")
    start_time: datetime
    end_time: datetime
    granularity: str


# ============ 温湿度趋势 ============
class TrendPoint(BaseModel):
    """趋势数据点"""
    time: datetime
    value: float | None


class TrendData(BaseModel):
    """温湿度趋势数据"""
    device_id: str
    device_name: str
    temp_trend: list[TrendPoint] = Field(default_factory=list, description="温度趋势")
    humi_trend: list[TrendPoint] = Field(default_factory=list, description="湿度趋势")


class TrendQuery(BaseModel):
    """趋势数据查询参数"""
    start_time: datetime
    end_time: datetime
    device_ids: list[str] | None = None
    zone_id: int | None = None
    interval: int = Field(default=60, description="采样间隔(分钟)")


class TrendResponse(BaseModel):
    """趋势数据响应"""
    data: list[TrendData]
    start_time: datetime
    end_time: datetime
    interval: int


# ============ 告警统计 ============
class AlarmStats(BaseModel):
    """告警统计数据"""
    type: str = Field(..., description="告警类型")
    severity: str = Field(..., description="告警级别")
    count: int = Field(..., description="告警数量")
    resolved_count: int = Field(default=0, description="已解决数量")
    unresolved_count: int = Field(default=0, description="未解决数量")


class AlarmStatsQuery(BaseModel):
    """告警统计查询参数"""
    start_time: datetime
    end_time: datetime
    device_ids: list[str] | None = None
    zone_id: int | None = None
    group_by: str = Field(default="type", description="分组方式: type/severity/device")


class AlarmStatsResponse(BaseModel):
    """告警统计响应"""
    data: list[AlarmStats]
    total_alarms: int
    resolved_alarms: int
    unresolved_alarms: int
    start_time: datetime
    end_time: datetime


# ============ 设备运行时长 ============
class RuntimeStats(BaseModel):
    """设备运行时长统计"""
    device_id: str
    device_name: str
    zone_name: str | None = None
    total_runtime_hours: float = Field(..., description="总运行时长(小时)")
    on_time_percentage: float = Field(..., description="开机时间占比(%)")
    on_count: int = Field(default=0, description="开机次数")
    off_count: int = Field(default=0, description="关机次数")


class RuntimeQuery(BaseModel):
    """运行时长查询参数"""
    start_time: datetime
    end_time: datetime
    device_ids: list[str] | None = None
    zone_id: int | None = None


class RuntimeResponse(BaseModel):
    """运行时长响应"""
    data: list[RuntimeStats]
    total_devices: int
    avg_runtime_hours: float
    start_time: datetime
    end_time: datetime


# ============ 报表导出 ============
class ExportQuery(BaseModel):
    """导出查询参数"""
    report_type: str = Field(..., description="报表类型: energy/trend/alarm/runtime")
    start_time: datetime
    end_time: datetime
    device_ids: list[str] | None = None
    zone_id: int | None = None
    format: str = Field(default="csv", description="导出格式: csv/excel")


class ExportResponse(BaseModel):
    """导出响应"""
    download_url: str
    file_name: str
    expires_at: datetime
