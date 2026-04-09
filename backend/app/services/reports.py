"""
报表服务模块
Phase 4 报表与分析功能

提供能耗统计、温湿度趋势、告警统计、运行时长计算等核心功能
"""
from datetime import datetime
from typing import Any

# 默认数据间隔（分钟），当无法计算实际间隔时使用
DEFAULT_INTERVAL_MINUTES = 60


def calculate_energy(
    current_data: list[dict[str, Any]],
    voltage: float = 220.0,
    interval_minutes: int | None = None
) -> float:
    """
    从电流数据计算能耗

    Args:
        current_data: 电流数据列表，每个元素包含 time 和 current 字段
        voltage: 电压值（默认220V）
        interval_minutes: 数据间隔（分钟），若未提供则自动计算

    Returns:
        总能耗 (kWh)

    计算公式：
        P = U * I (功率 = 电压 * 电流)
        E = P * t (能耗 = 功率 * 时间)
        kWh = W / 1000
    """
    if not current_data:
        return 0.0

    # 计算实际数据间隔（如果没有提供）
    if interval_minutes is None:
        interval_minutes = _calculate_interval(current_data)

    interval_hours = interval_minutes / 60.0

    total_energy = 0.0

    # 累计每个数据点的能耗
    for data in current_data:
        current = data.get("current", 0) or 0
        power = voltage * current  # W
        energy = (power * interval_hours) / 1000  # kWh
        total_energy += energy

    return round(total_energy, 2)


def calculate_runtime(
    airstate_data: list[dict[str, Any]],
    interval_minutes: int | None = None
) -> float:
    """
    从 airstate 数据计算运行时长

    Args:
        airstate_data: airstate 数据列表，每个元素包含 time 和 airstate 字段
                       airstate: 1=开机, 0=关机
        interval_minutes: 数据间隔（分钟），若未提供则自动计算

    Returns:
        运行时长（小时）
    """
    if not airstate_data:
        return 0.0

    # 计算实际数据间隔（如果没有提供）
    if interval_minutes is None:
        interval_minutes = _calculate_interval(airstate_data)

    interval_hours = interval_minutes / 60.0

    runtime_hours = 0.0

    for data in airstate_data:
        airstate = data.get("airstate", 0)
        if airstate == 1:
            runtime_hours += interval_hours

    return round(runtime_hours, 2)


def _calculate_interval(data: list[dict[str, Any]]) -> int:
    """
    根据数据时间戳计算实际间隔（分钟）

    Args:
        data: 数据列表，每个元素包含 time 字段

    Returns:
        数据间隔（分钟）
    """
    if len(data) < 2:
        return DEFAULT_INTERVAL_MINUTES

    # 取前几个数据点计算平均间隔
    times = []
    for d in data[:min(5, len(data))]:
        t = d.get("time")
        if t is not None:
            # 处理字符串和 datetime 类型
            if isinstance(t, str):
                try:
                    t = datetime.fromisoformat(t.replace("Z", "+00:00"))
                except (ValueError, AttributeError):
                    continue
            elif isinstance(t, datetime):
                pass
            else:
                continue
            times.append(t)

    if len(times) < 2:
        return DEFAULT_INTERVAL_MINUTES

    # 计算平均间隔
    intervals = []
    for i in range(1, len(times)):
        delta = times[i] - times[i - 1]
        minutes = delta.total_seconds() / 60
        if minutes > 0:
            intervals.append(minutes)

    if not intervals:
        return DEFAULT_INTERVAL_MINUTES

    # 返回平均间隔（取整数）
    return round(sum(intervals) / len(intervals))


def aggregate_alarm_stats(
    alarms: list[dict[str, Any]],
    group_by: str = "type"
) -> list[dict[str, Any]]:
    """
    聚合告警统计

    Args:
        alarms: 告警数据列表
        group_by: 分组方式 (type/severity/device)

    Returns:
        聚合后的统计数据列表
    """
    if not alarms:
        return []

    stats_map: dict[str, dict[str, Any]] = {}

    for alarm in alarms:
        key = alarm.get(group_by, "unknown")

        if key not in stats_map:
            stats_map[key] = {
                group_by: key,
                "count": 0,
                "resolved_count": 0,
                "unresolved_count": 0
            }

        stats_map[key]["count"] += 1

        if alarm.get("is_resolved", False):
            stats_map[key]["resolved_count"] += 1
        else:
            stats_map[key]["unresolved_count"] += 1

    # 添加 severity 字段（如果按 type 分组）
    if group_by == "type":
        for key, stats in stats_map.items():
            # 统计每种类型的主要严重程度
            severity_counts = {}
            for alarm in alarms:
                if alarm.get("type") == key:
                    sev = alarm.get("severity", "unknown")
                    severity_counts[sev] = severity_counts.get(sev, 0) + 1
            # 取最常见的严重程度
            stats["severity"] = max(severity_counts, key=severity_counts.get) if severity_counts else "unknown"

    return list(stats_map.values())


async def get_energy_stats(
    db: Any,
    tenant_id: int,
    start_time: datetime,
    end_time: datetime,
    device_ids: list[str] | None = None,
    zone_id: int | None = None,
    granularity: str = "day"
) -> dict[str, Any]:
    """
    获取能耗统计数据

    Args:
        db: 数据库会话
        tenant_id: 租户ID
        start_time: 开始时间
        end_time: 结束时间
        device_ids: 设备ID列表（可选）
        zone_id: 分区ID（可选）
        granularity: 统计粒度 (hour/day/month)

    Returns:
        能耗统计数据
    """
    from sqlalchemy import select

    from app.models import Device, DeviceData

    # 构建设备查询
    device_query = select(Device).where(Device.tenant_id == tenant_id)

    if zone_id:
        device_query = device_query.where(Device.zone_id == zone_id)

    if device_ids:
        device_query = device_query.where(Device.device_id.in_(device_ids))

    result = await db.execute(device_query)
    devices = result.scalars().all()

    if not devices:
        return {
            "data": [],
            "total_energy": 0.0,
            "start_time": start_time,
            "end_time": end_time,
            "granularity": granularity
        }

    # 构建数据查询
    device_id_list = [d.device_id for d in devices]
    data_query = select(DeviceData).where(
        DeviceData.tenant_id == tenant_id,
        DeviceData.device_id.in_(device_id_list),
        DeviceData.time >= start_time,
        DeviceData.time <= end_time
    ).order_by(DeviceData.time)

    data_result = await db.execute(data_query)
    data_list = data_result.scalars().all()

    # 按设备分组计算能耗
    stats = []
    total_energy = 0.0

    for device in devices:
        device_data = [d for d in data_list if d.device_id == device.device_id]
        current_data = [{"time": d.time, "current": d.current} for d in device_data if d.current]

        energy = calculate_energy(current_data)

        avg_power = sum(d.current or 0 for d in device_data) / len(device_data) * 220 if device_data else 0
        max_power = max(d.current or 0 for d in device_data) * 220 if device_data else 0

        runtime_hours = len([d for d in device_data if d.airstate == 1])

        stats.append({
            "device_id": device.device_id,
            "device_name": device.name,
            "total_energy": energy,
            "avg_power": round(avg_power, 2),
            "max_power": round(max_power, 2),
            "runtime_hours": runtime_hours
        })

        total_energy += energy

    return {
        "data": stats,
        "total_energy": round(total_energy, 2),
        "start_time": start_time,
        "end_time": end_time,
        "granularity": granularity
    }


async def get_trend_data(
    db: Any,
    tenant_id: int,
    start_time: datetime,
    end_time: datetime,
    device_ids: list[str] | None = None,
    zone_id: int | None = None,
    interval: int = 60
) -> dict[str, Any]:
    """
    获取温湿度趋势数据

    Args:
        db: 数据库会话
        tenant_id: 租户ID
        start_time: 开始时间
        end_time: 结束时间
        device_ids: 设备ID列表（可选）
        zone_id: 分区ID（可选）
        interval: 采样间隔（分钟）

    Returns:
        温湿度趋势数据
    """
    from sqlalchemy import select

    from app.models import Device, DeviceData

    # 构建设备查询
    device_query = select(Device).where(Device.tenant_id == tenant_id)

    if zone_id:
        device_query = device_query.where(Device.zone_id == zone_id)

    if device_ids:
        device_query = device_query.where(Device.device_id.in_(device_ids))

    result = await db.execute(device_query)
    devices = result.scalars().all()

    if not devices:
        return {
            "data": [],
            "start_time": start_time,
            "end_time": end_time,
            "interval": interval
        }

    # 构建数据查询
    device_id_list = [d.device_id for d in devices]
    data_query = select(DeviceData).where(
        DeviceData.tenant_id == tenant_id,
        DeviceData.device_id.in_(device_id_list),
        DeviceData.time >= start_time,
        DeviceData.time <= end_time
    ).order_by(DeviceData.time)

    data_result = await db.execute(data_query)
    data_list = data_result.scalars().all()

    # 按设备分组构建趋势数据
    trends = []

    for device in devices:
        device_data = [d for d in data_list if d.device_id == device.device_id]

        temp_trend = [{"time": d.time, "value": d.temp} for d in device_data if d.temp]
        humi_trend = [{"time": d.time, "value": d.humi} for d in device_data if d.humi]

        trends.append({
            "device_id": device.device_id,
            "device_name": device.name,
            "temp_trend": temp_trend,
            "humi_trend": humi_trend
        })

    return {
        "data": trends,
        "start_time": start_time,
        "end_time": end_time,
        "interval": interval
    }


async def get_alarm_stats(
    db: Any,
    tenant_id: int,
    start_time: datetime,
    end_time: datetime,
    device_ids: list[str] | None = None,
    zone_id: int | None = None,
    group_by: str = "type"
) -> dict[str, Any]:
    """
    获取告警统计数据

    Args:
        db: 数据库会话
        tenant_id: 租户ID
        start_time: 开始时间
        end_time: 结束时间
        device_ids: 设备ID列表（可选）
        zone_id: 分区ID（可选）
        group_by: 分组方式 (type/severity/device)

    Returns:
        告警统计数据
    """
    from sqlalchemy import select

    from app.models import Alarm, Device

    # 构建设备查询（用于 zone_id 筛选）
    if zone_id:
        device_query = select(Device.device_id).where(
            Device.tenant_id == tenant_id,
            Device.zone_id == zone_id
        )
        device_result = await db.execute(device_query)
        zone_device_ids = list(device_result.scalars().all())

    # 构建告警查询
    alarm_query = select(Alarm).where(
        Alarm.tenant_id == tenant_id,
        Alarm.occurred_at >= start_time,
        Alarm.occurred_at <= end_time
    )

    if device_ids:
        alarm_query = alarm_query.where(Alarm.device_id.in_(device_ids))
    elif zone_id:
        alarm_query = alarm_query.where(Alarm.device_id.in_(zone_device_ids))

    result = await db.execute(alarm_query)
    alarms = result.scalars().all()

    # 转换为字典列表
    alarm_dicts = [
        {
            "type": a.type,
            "severity": a.severity,
            "device_id": a.device_id,
            "is_resolved": a.is_resolved
        }
        for a in alarms
    ]

    # 聚合统计
    stats = aggregate_alarm_stats(alarm_dicts, group_by)

    # 计算总数
    total_alarms = len(alarms)
    resolved_alarms = sum(1 for a in alarms if a.is_resolved)
    unresolved_alarms = total_alarms - resolved_alarms

    return {
        "data": stats,
        "total_alarms": total_alarms,
        "resolved_alarms": resolved_alarms,
        "unresolved_alarms": unresolved_alarms,
        "start_time": start_time,
        "end_time": end_time
    }


async def get_runtime_stats(
    db: Any,
    tenant_id: int,
    start_time: datetime,
    end_time: datetime,
    device_ids: list[str] | None = None,
    zone_id: int | None = None
) -> dict[str, Any]:
    """
    获取设备运行时长统计

    Args:
        db: 数据库会话
        tenant_id: 租户ID
        start_time: 开始时间
        end_time: 结束时间
        device_ids: 设备ID列表（可选）
        zone_id: 分区ID（可选）

    Returns:
        运行时长统计数据
    """
    from sqlalchemy import select

    from app.models import Device, DeviceData, Zone

    # 构建设备查询
    device_query = select(Device).where(Device.tenant_id == tenant_id)

    if zone_id:
        device_query = device_query.where(Device.zone_id == zone_id)

    if device_ids:
        device_query = device_query.where(Device.device_id.in_(device_ids))

    result = await db.execute(device_query)
    devices = result.scalars().all()

    if not devices:
        return {
            "data": [],
            "total_devices": 0,
            "avg_runtime_hours": 0.0,
            "start_time": start_time,
            "end_time": end_time
        }

    # 构建数据查询
    device_id_list = [d.device_id for d in devices]
    data_query = select(DeviceData).where(
        DeviceData.tenant_id == tenant_id,
        DeviceData.device_id.in_(device_id_list),
        DeviceData.time >= start_time,
        DeviceData.time <= end_time
    ).order_by(DeviceData.time)

    data_result = await db.execute(data_query)
    data_list = data_result.scalars().all()

    # 获取分区名称映射
    zone_query = select(Zone).where(Zone.tenant_id == tenant_id)
    zone_result = await db.execute(zone_query)
    zones = {z.id: z.name for z in zone_result.scalars().all()}

    # 按设备计算运行时长
    stats = []
    total_runtime = 0.0

    for device in devices:
        device_data = [d for d in data_list if d.device_id == device.device_id]

        airstate_data = [{"time": d.time, "airstate": d.airstate} for d in device_data]
        runtime_hours = calculate_runtime(airstate_data)

        # 计算开机占比
        total_hours = len(device_data)
        on_time_percentage = (runtime_hours / total_hours * 100) if total_hours > 0 else 0

        # 计算开关机次数
        on_count = 0
        off_count = 0
        prev_airstate = None

        for d in device_data:
            airstate = d.airstate
            if prev_airstate is not None:
                if airstate == 1 and prev_airstate == 0:
                    on_count += 1
                elif airstate == 0 and prev_airstate == 1:
                    off_count += 1
            prev_airstate = airstate

        zone_name = zones.get(device.zone_id) if device.zone_id else None

        stats.append({
            "device_id": device.device_id,
            "device_name": device.name,
            "zone_name": zone_name,
            "total_runtime_hours": runtime_hours,
            "on_time_percentage": round(on_time_percentage, 2),
            "on_count": on_count,
            "off_count": off_count
        })

        total_runtime += runtime_hours

    avg_runtime = total_runtime / len(devices) if devices else 0

    return {
        "data": stats,
        "total_devices": len(devices),
        "avg_runtime_hours": round(avg_runtime, 2),
        "start_time": start_time,
        "end_time": end_time
    }
