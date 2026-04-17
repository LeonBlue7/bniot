"""
设备在线状态监控服务

定期检测设备在线状态，将长时间未通信的设备标记为离线
"""
import asyncio
from datetime import UTC, datetime, timedelta

from loguru import logger
from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_maker
from app.models import Device
from app.services.realtime_push import get_realtime_push_service


# 离线阈值：设备超过此时间未通信则标记为离线
# EMQX心跳120秒，设备可能3个心跳周期（6分钟）才发送数据
# 设置为15分钟，确保设备有足够时间发送数据
OFFLINE_THRESHOLD_MINUTES = 15


class DeviceMonitorService:
    """
    设备在线状态监控服务

    功能：
    - 定期检测设备在线状态
    - 将超时未通信的设备标记为离线
    - 推送状态变化到 WebSocket
    """

    def __init__(self):
        self.realtime_push = get_realtime_push_service()
        self._running = False
        self._task: asyncio.Task | None = None
        # 离线阈值（秒）
        self.offline_threshold_seconds = OFFLINE_THRESHOLD_MINUTES * 60

    async def start(self):
        """启动监控服务"""
        if self._running:
            logger.warning("设备监控服务已在运行")
            return

        self._running = True
        self._task = asyncio.create_task(self._monitor_loop())
        logger.info(f"设备监控服务已启动，离线阈值: {OFFLINE_THRESHOLD_MINUTES} 分钟")

    async def stop(self):
        """停止监控服务"""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("设备监控服务已停止")

    async def _monitor_loop(self):
        """监控循环"""
        while self._running:
            try:
                await self._check_offline_devices()
            except Exception as e:
                logger.exception(f"设备离线检测失败: {e}")

            # 每 60 秒检测一次
            await asyncio.sleep(60)

    async def _check_offline_devices(self):
        """
        检测离线设备

        将 last_seen_at 超过阈值的设备标记为离线
        """
        now = datetime.now(UTC)
        threshold_time = now - timedelta(seconds=self.offline_threshold_seconds)

        async with async_session_maker() as db:
            # 查询需要标记为离线的设备
            # 条件：is_online=True 且 last_seen_at < threshold_time 或 last_seen_at 为 None
            result = await db.execute(
                select(Device.id, Device.device_id, Device.tenant_id, Device.last_seen_at)
                .where(
                    and_(
                        Device.is_online == True,
                        (Device.last_seen_at < threshold_time) | (Device.last_seen_at.is_(None))
                    )
                )
            )
            offline_devices = result.all()

            if not offline_devices:
                logger.debug("没有设备需要标记为离线")
                return

            # 批量更新设备状态
            device_ids_to_update = [d.id for d in offline_devices]
            await db.execute(
                update(Device)
                .where(Device.id.in_(device_ids_to_update))
                .values(is_online=False)
            )
            await db.commit()

            # 推送状态变化
            for device in offline_devices:
                await self.realtime_push.push_device_status(
                    device.device_id, device.tenant_id, is_online=False
                )
                logger.info(
                    f"设备离线: device_id={device.device_id}, "
                    f"last_seen_at={device.last_seen_at}"
                )

            logger.info(f"已标记 {len(offline_devices)} 台设备为离线")


# 全局监控服务实例
_device_monitor_service: DeviceMonitorService | None = None


def get_device_monitor_service() -> DeviceMonitorService:
    """获取设备监控服务实例"""
    global _device_monitor_service
    if _device_monitor_service is None:
        _device_monitor_service = DeviceMonitorService()
    return _device_monitor_service


async def start_device_monitor():
    """启动设备监控服务"""
    service = get_device_monitor_service()
    await service.start()


async def stop_device_monitor():
    """停止设备监控服务"""
    service = get_device_monitor_service()
    await service.stop()