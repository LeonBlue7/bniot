"""
报表 API 端点
Phase 4 报表与分析功能

提供能耗统计、温湿度趋势、告警统计、运行时长统计等报表接口
"""
import csv
import io
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models import User
from app.schemas.reports import (
    AlarmStats,
    AlarmStatsResponse,
    EnergyStats,
    EnergyStatsResponse,
    RuntimeResponse,
    RuntimeStats,
    TrendData,
    TrendPoint,
    TrendResponse,
)
from app.services.auth import get_current_user
from app.services.reports import (
    get_alarm_stats,
    get_energy_stats,
    get_runtime_stats,
    get_trend_data,
)

# 查询时间范围上限（防止大数据量查询）
MAX_QUERY_DAYS = 31

router = APIRouter()


def _validate_time_range(start_time: datetime, end_time: datetime) -> None:
    """
    验证时间范围

    Args:
        start_time: 开始时间
        end_time: 结束时间

    Raises:
        HTTPException: 时间范围无效
    """
    if start_time > end_time:
        raise HTTPException(status_code=400, detail="开始时间不能大于结束时间")

    # 确保时间是 UTC
    if start_time.tzinfo is None:
        start_time = start_time.replace(tzinfo=UTC)
    if end_time.tzinfo is None:
        end_time = end_time.replace(tzinfo=UTC)

    days = (end_time - start_time).days
    if days > MAX_QUERY_DAYS:
        raise HTTPException(
            status_code=400,
            detail=f"查询时间范围不能超过{MAX_QUERY_DAYS}天"
        )


def _parse_device_ids(device_ids: str | None) -> list[str] | None:
    """
    解析设备ID列表

    Args:
        device_ids: 逗号分隔的设备ID字符串

    Returns:
        设备ID列表或 None
    """
    if not device_ids:
        return None
    return [id.strip() for id in device_ids.split(",")]


@router.get("/energy", response_model=EnergyStatsResponse)
async def energy_stats(
    start_time: datetime = Query(..., description="开始时间"),
    end_time: datetime = Query(..., description="结束时间"),
    device_ids: str | None = Query(None, description="设备ID列表，逗号分隔"),
    zone_id: int | None = Query(None, description="分区ID"),
    granularity: str = Query("day", description="统计粒度: hour/day/month"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取能耗统计数据

    - 按时间范围查询
    - 支持按设备或分区筛选
    - 支持不同统计粒度
    """
    # 验证时间范围
    _validate_time_range(start_time, end_time)

    # 解析设备ID列表
    device_id_list = _parse_device_ids(device_ids)

    # 调用服务获取数据
    result = await get_energy_stats(
        db=db,
        tenant_id=current_user.tenant_id,
        start_time=start_time,
        end_time=end_time,
        device_ids=device_id_list,
        zone_id=zone_id,
        granularity=granularity
    )

    return EnergyStatsResponse(
        data=[EnergyStats(**item) for item in result["data"]],
        total_energy=result["total_energy"],
        start_time=result["start_time"],
        end_time=result["end_time"],
        granularity=result["granularity"]
    )


@router.get("/trend", response_model=TrendResponse)
async def trend_data(
    start_time: datetime = Query(..., description="开始时间"),
    end_time: datetime = Query(..., description="结束时间"),
    device_ids: str | None = Query(None, description="设备ID列表，逗号分隔"),
    zone_id: int | None = Query(None, description="分区ID"),
    interval: int = Query(60, ge=5, le=1440, description="采样间隔(分钟)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取温湿度趋势数据

    - 按时间范围查询
    - 支持按设备或分区筛选
    - 支持自定义采样间隔
    """
    # 验证时间范围
    _validate_time_range(start_time, end_time)

    # 解析设备ID列表
    device_id_list = _parse_device_ids(device_ids)

    # 调用服务获取数据
    result = await get_trend_data(
        db=db,
        tenant_id=current_user.tenant_id,
        start_time=start_time,
        end_time=end_time,
        device_ids=device_id_list,
        zone_id=zone_id,
        interval=interval
    )

    return TrendResponse(
        data=[
            TrendData(
                device_id=item["device_id"],
                device_name=item["device_name"],
                temp_trend=[TrendPoint(**p) for p in item["temp_trend"]],
                humi_trend=[TrendPoint(**p) for p in item["humi_trend"]]
            )
            for item in result["data"]
        ],
        start_time=result["start_time"],
        end_time=result["end_time"],
        interval=result["interval"]
    )


@router.get("/alarms", response_model=AlarmStatsResponse)
async def alarm_stats(
    start_time: datetime = Query(..., description="开始时间"),
    end_time: datetime = Query(..., description="结束时间"),
    device_ids: str | None = Query(None, description="设备ID列表，逗号分隔"),
    zone_id: int | None = Query(None, description="分区ID"),
    group_by: str = Query("type", description="分组方式: type/severity/device"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取告警统计数据

    - 按时间范围查询
    - 支持按设备或分区筛选
    - 支持按类型、严重程度或设备分组
    """
    # 验证时间范围
    _validate_time_range(start_time, end_time)

    # 验证分组方式
    if group_by not in ["type", "severity", "device"]:
        raise HTTPException(status_code=400, detail="无效的分组方式")

    # 解析设备ID列表
    device_id_list = _parse_device_ids(device_ids)

    # 调用服务获取数据
    result = await get_alarm_stats(
        db=db,
        tenant_id=current_user.tenant_id,
        start_time=start_time,
        end_time=end_time,
        device_ids=device_id_list,
        zone_id=zone_id,
        group_by=group_by
    )

    return AlarmStatsResponse(
        data=[AlarmStats(**item) for item in result["data"]],
        total_alarms=result["total_alarms"],
        resolved_alarms=result["resolved_alarms"],
        unresolved_alarms=result["unresolved_alarms"],
        start_time=result["start_time"],
        end_time=result["end_time"]
    )


@router.get("/runtime", response_model=RuntimeResponse)
async def runtime_stats(
    start_time: datetime = Query(..., description="开始时间"),
    end_time: datetime = Query(..., description="结束时间"),
    device_ids: str | None = Query(None, description="设备ID列表，逗号分隔"),
    zone_id: int | None = Query(None, description="分区ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取设备运行时长统计

    - 按时间范围查询
    - 支持按设备或分区筛选
    - 显示运行时长、开机占比、开关机次数
    """
    # 验证时间范围
    _validate_time_range(start_time, end_time)

    # 解析设备ID列表
    device_id_list = _parse_device_ids(device_ids)

    # 调用服务获取数据
    result = await get_runtime_stats(
        db=db,
        tenant_id=current_user.tenant_id,
        start_time=start_time,
        end_time=end_time,
        device_ids=device_id_list,
        zone_id=zone_id
    )

    return RuntimeResponse(
        data=[RuntimeStats(**item) for item in result["data"]],
        total_devices=result["total_devices"],
        avg_runtime_hours=result["avg_runtime_hours"],
        start_time=result["start_time"],
        end_time=result["end_time"]
    )


@router.get("/export")
async def export_report(
    report_type: str = Query(..., description="报表类型: energy/trend/alarm/runtime"),
    start_time: datetime = Query(..., description="开始时间"),
    end_time: datetime = Query(..., description="结束时间"),
    device_ids: str | None = Query(None, description="设备ID列表，逗号分隔"),
    zone_id: int | None = Query(None, description="分区ID"),
    format: str = Query("csv", description="导出格式: csv"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    导出报表数据

    - 支持能耗、温湿度趋势、告警统计、运行时长报表
    - 支持 CSV 格式导出
    """
    # 验证报表类型
    valid_report_types = ["energy", "trend", "alarm", "runtime"]
    if report_type not in valid_report_types:
        raise HTTPException(status_code=400, detail=f"无效的报表类型，支持: {valid_report_types}")

    # 验证时间范围
    _validate_time_range(start_time, end_time)

    # 验证导出格式（目前只支持 CSV）
    if format != "csv":
        raise HTTPException(status_code=400, detail="目前只支持 CSV 格式导出")

    # 解析设备ID列表
    device_id_list = _parse_device_ids(device_ids)

    # 根据报表类型获取数据
    if report_type == "energy":
        result = await get_energy_stats(
            db=db,
            tenant_id=current_user.tenant_id,
            start_time=start_time,
            end_time=end_time,
            device_ids=device_id_list,
            zone_id=zone_id
        )
        headers = ["设备ID", "设备名称", "总能耗(kWh)", "平均功率(W)", "最大功率(W)", "运行时长(小时)"]
        rows = [
            [
                item["device_id"],
                item["device_name"],
                item["total_energy"],
                item["avg_power"],
                item["max_power"],
                item["runtime_hours"]
            ]
            for item in result["data"]
        ]
    elif report_type == "trend":
        result = await get_trend_data(
            db=db,
            tenant_id=current_user.tenant_id,
            start_time=start_time,
            end_time=end_time,
            device_ids=device_id_list,
            zone_id=zone_id
        )
        headers = ["设备ID", "设备名称", "时间", "温度", "湿度"]
        rows = []
        for item in result["data"]:
            # 使用 zip 处理温度和湿度数据（数据点可能不完全对应）
            for temp_point, humi_point in zip(item["temp_trend"], item["humi_trend"], strict=False):
                rows.append([
                    item["device_id"],
                    item["device_name"],
                    temp_point["time"],
                    temp_point["value"],
                    humi_point["value"]
                ])
    elif report_type == "alarm":
        result = await get_alarm_stats(
            db=db,
            tenant_id=current_user.tenant_id,
            start_time=start_time,
            end_time=end_time,
            device_ids=device_id_list,
            zone_id=zone_id
        )
        headers = ["告警类型", "严重程度", "数量", "已解决", "未解决"]
        rows = [
            [
                item["type"],
                item["severity"],
                item["count"],
                item["resolved_count"],
                item["unresolved_count"]
            ]
            for item in result["data"]
        ]
    elif report_type == "runtime":
        result = await get_runtime_stats(
            db=db,
            tenant_id=current_user.tenant_id,
            start_time=start_time,
            end_time=end_time,
            device_ids=device_id_list,
            zone_id=zone_id
        )
        headers = ["设备ID", "设备名称", "分区", "运行时长(小时)", "开机占比(%)", "开机次数", "关机次数"]
        rows = [
            [
                item["device_id"],
                item["device_name"],
                item["zone_name"] or "",
                item["total_runtime_hours"],
                item["on_time_percentage"],
                item["on_count"],
                item["off_count"]
            ]
            for item in result["data"]
        ]

    # 生成 CSV 文件
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    writer.writerows(rows)

    # 生成文件名
    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    file_name = f"{report_type}_report_{timestamp}.csv"

    # 返回 StreamingResponse
    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8-sig")),  # utf-8-sig 支持 Excel 正确显示中文
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={file_name}"
        }
    )
