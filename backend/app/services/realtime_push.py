"""
实时数据推送服务

集成 MQTT 设备数据上送和 WebSocket 实时推送
"""
from datetime import UTC, datetime
from typing import Any

from loguru import logger

from app.services.websocket_manager import get_connection_manager


class RealtimeDataPushService:
    """
    实时数据推送服务

    功能：
    - 设备数据实时推送
    - 设备状态变化推送
    - 告警实时推送
    """

    def __init__(self):
        self.manager = get_connection_manager()

    async def push_device_data(self, device_id: str, tenant_id: int, data: dict[str, Any]):
        """
        推送设备实时数据

        Args:
            device_id: 设备 ID
            tenant_id: 租户 ID
            data: 设备数据
        """
        message = {
            "type": "device_data",
            "device_id": device_id,
            "data": {
                "temp": data.get("temp"),
                "humi": data.get("humi"),
                "airstate": data.get("airstate"),
                "current": data.get("current"),
                "csq": data.get("csq"),
                "air_err": data.get("air_err"),
                "alarmtemp": data.get("alarmtemp"),
                "alarmhumi": data.get("alarmhumi"),
            },
            "timestamp": datetime.now(UTC).isoformat()
        }

        await self.manager.push_device_data(device_id, tenant_id, message)
        logger.debug(f"推送设备数据: device_id={device_id}")

    async def push_device_status(self, device_id: str, tenant_id: int, is_online: bool):
        """
        推送设备状态变化

        Args:
            device_id: 设备 ID
            tenant_id: 租户 ID
            is_online: 是否在线
        """
        message = {
            "type": "device_status",
            "device_id": device_id,
            "data": {
                "is_online": is_online,
                "timestamp": datetime.now(UTC).isoformat()
            }
        }

        await self.manager.push_device_status(device_id, tenant_id, is_online)
        logger.info(f"推送设备状态: device_id={device_id}, is_online={is_online}")

    async def push_alarm(self, tenant_id: int, alarm_data: dict[str, Any]):
        """
        推送告警通知

        Args:
            tenant_id: 租户 ID
            alarm_data: 告警数据
        """
        message = {
            "type": "alarm",
            "data": alarm_data,
            "timestamp": datetime.now(UTC).isoformat()
        }

        await self.manager.push_alarm(tenant_id, message)
        logger.info(f"推送告警: tenant_id={tenant_id}, type={alarm_data.get('type')}")


# 全局实时推送服务实例（直接创建，避免延迟初始化问题）
_realtime_push_service = RealtimeDataPushService()


def get_realtime_push_service() -> RealtimeDataPushService:
    """获取实时推送服务实例"""
    return _realtime_push_service


def reset_realtime_push_service():
    """重置实时推送服务（用于测试）"""
    global _realtime_push_service
    _realtime_push_service = RealtimeDataPushService()