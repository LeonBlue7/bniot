"""
运行时间计算服务
基于 airstate 数据计算空调运行时间

核心功能：
1. 计算指定时间段的运行时间
2. 当天/当月累计运行时间
3. 开关机事件记录（检测状态变化）
"""
from datetime import datetime, UTC
from typing import Any

from sqlalchemy import and_, func, select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import DeviceData


class RuntimeService:
    """运行时间计算服务 - 基于 airstate 数据

    重要：所有查询必须包含 tenant_id 条件，确保租户隔离
    """

    def __init__(self, db: AsyncSession, tenant_id: int):
        self.db = db
        self.tenant_id = tenant_id

    async def calculate_runtime(
        self, device_id: str, start_time: datetime, end_time: datetime,
        last_seen_at: datetime | None = None
    ) -> float | None:
        """
        计算运行时长（小时）

        Args:
            device_id: 设备ID
            start_time: 开始时间
            end_time: 结束时间
            last_seen_at: 设备最后通信时间，用于边界条件处理

        Returns:
            运行时长（小时），如果不支持（无airstate数据）返回None
        """
        # 确保时间有时区信息
        if start_time.tzinfo is None:
            start_time = start_time.replace(tzinfo=UTC)
        if end_time.tzinfo is None:
            end_time = end_time.replace(tzinfo=UTC)

        # 获取时间段内的 airstate 数据（添加租户隔离）
        query = (
            select(DeviceData.time, DeviceData.airstate)
            .where(
                and_(
                    DeviceData.device_id == device_id,
                    DeviceData.tenant_id == self.tenant_id,  # 租户隔离
                    DeviceData.time >= start_time,
                    DeviceData.time <= end_time,
                    DeviceData.airstate.is_not(None)
                )
            )
            .order_by(DeviceData.time)
        )
        result = await self.db.execute(query)
        rows = result.all()

        if not rows:
            # 检查是否有 airstate 数据（协议版本是否支持）
            check_query = (
                select(func.count(DeviceData.id))
                .where(
                    and_(
                        DeviceData.device_id == device_id,
                        DeviceData.tenant_id == self.tenant_id,  # 租户隔离
                        DeviceData.airstate.is_not(None)
                    )
                )
            )
            check_result = await self.db.execute(check_query)
            count = check_result.scalar() or 0
            if count == 0:
                return None  # 不支持 airstate
            return 0.0  # 支持但该时间段无运行

        # 计算运行时间：累加 airstate=1 的时间段
        total_runtime_seconds = 0
        last_on_time = None
        last_data_time = None  # 记录最后一条数据的时间

        for row in rows:
            time, airstate = row.time, row.airstate
            # 确保数据时间有时区信息
            if time.tzinfo is None:
                time = time.replace(tzinfo=UTC)
            last_data_time = time  # 更新最后数据时间

            if airstate == 1:
                # 开机，记录开始时间
                if last_on_time is None:
                    last_on_time = time
            else:
                # 关机，计算运行时长
                if last_on_time is not None:
                    runtime = (time - last_on_time).total_seconds()
                    total_runtime_seconds += runtime
                    last_on_time = None

        # 如果最后一条记录是开机状态，使用设备最后通信时间作为上限
        # 避免设备离线时错误累加运行时间
        if last_on_time is not None and last_data_time is not None:
            # 使用设备最后通信时间或最后数据时间作为上限
            # 如果设备在线且最近有通信，使用 end_time（假设仍在运行）
            # 如果设备离线很久，使用 last_seen_at 或最后数据时间
            if last_seen_at is not None:
                # 确保时间有时区信息
                if last_seen_at.tzinfo is None:
                    last_seen_at = last_seen_at.replace(tzinfo=UTC)
                actual_end = min(last_seen_at, end_time)
            else:
                # 没有提供 last_seen_at，使用最后数据时间（保守估计）
                actual_end = last_data_time

            if actual_end > last_on_time:
                runtime = (actual_end - last_on_time).total_seconds()
                total_runtime_seconds += runtime

        return total_runtime_seconds / 3600  # 转换为小时

    async def get_today_runtime(
        self, device_id: str, last_seen_at: datetime | None = None
    ) -> float | None:
        """当天累计运行时间（小时）

        Args:
            device_id: 设备ID
            last_seen_at: 设备最后通信时间
        """
        now = datetime.now(UTC)
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        return await self.calculate_runtime(device_id, start_of_day, now, last_seen_at)

    async def get_month_runtime(
        self, device_id: str, last_seen_at: datetime | None = None
    ) -> float | None:
        """当月累计运行时间（小时）

        Args:
            device_id: 设备ID
            last_seen_at: 设备最后通信时间
        """
        now = datetime.now(UTC)
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        return await self.calculate_runtime(device_id, start_of_month, now, last_seen_at)

    async def get_runtime_events(
        self, device_id: str, page: int = 1, page_size: int = 20
    ) -> dict[str, Any]:
        """
        开关机事件记录（检测 airstate 状态变化）

        Args:
            device_id: 设备ID
            page: 页码
            page_size: 每页数量

        Returns:
            {
                "supported": bool,  # 是否支持 airstate
                "message": str,     # 不支持时的提示消息
                "events": [...],    # 事件列表
                "total": int,       # 总数量
                "page": int,
                "page_size": int
            }
        """
        # 检查是否支持 airstate（添加租户隔离）
        check_query = (
            select(func.count(DeviceData.id))
            .where(
                and_(
                    DeviceData.device_id == device_id,
                    DeviceData.tenant_id == self.tenant_id,  # 租户隔离
                    DeviceData.airstate.is_not(None)
                )
            )
        )
        check_result = await self.db.execute(check_query)
        count = check_result.scalar() or 0

        if count == 0:
            return {
                "supported": False,
                "message": "当前协议版本不支持空调状态监控",
                "events": [],
                "total": 0,
                "page": page,
                "page_size": page_size
            }

        # 获取 airstate 数据，检测状态变化（添加租户隔离）
        query = (
            select(DeviceData.time, DeviceData.airstate)
            .where(
                and_(
                    DeviceData.device_id == device_id,
                    DeviceData.tenant_id == self.tenant_id,  # 租户隔离
                    DeviceData.airstate.is_not(None)
                )
            )
            .order_by(desc(DeviceData.time))
            .limit(1000)  # 限制查询数量
        )
        result = await self.db.execute(query)
        rows = result.all()

        # 检测状态变化，生成事件
        events = []
        prev_airstate = None
        prev_time = None

        for row in rows:
            time, airstate = row.time, row.airstate
            if prev_airstate is not None and airstate != prev_airstate:
                # 状态变化
                if airstate == 1:
                    # 从关机变为开机
                    action = "开机"
                    duration = None
                else:
                    # 从开机变为关机
                    action = "关机"
                    if prev_time is not None:
                        duration_seconds = (prev_time - time).total_seconds()
                        duration = round(duration_seconds / 3600, 2)  # 小时

                events.append({
                    "time": time.isoformat(),
                    "action": action,
                    "duration": duration
                })

            prev_airstate = airstate
            prev_time = time

        # 反转顺序，最新的在前
        events = events[::-1]

        # 分页
        total = len(events)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        events = events[start_idx:end_idx]

        return {
            "supported": True,
            "message": "",
            "events": events,
            "total": total,
            "page": page,
            "page_size": page_size
        }

    async def supports_runtime(self, device_id: str) -> bool:
        """检查设备是否支持运行时间统计（添加租户隔离）"""
        query = (
            select(func.count(DeviceData.id))
            .where(
                and_(
                    DeviceData.device_id == device_id,
                    DeviceData.tenant_id == self.tenant_id,  # 租户隔离
                    DeviceData.airstate.is_not(None)
                )
            )
        )
        result = await self.db.execute(query)
        count = result.scalar() or 0
        return count > 0