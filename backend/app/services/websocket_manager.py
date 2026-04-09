"""
WebSocket 连接管理器
管理 WebSocket 连接、订阅、消息推送

安全特性:
- 多租户隔离
- 设备订阅授权检查（用户只能订阅自己租户的设备）
- 消息大小限制
"""
import json
from datetime import UTC, datetime

from fastapi import WebSocket
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Device


class ConnectionManager:
    """
    WebSocket 连接管理器

    功能：
    - 管理用户 WebSocket 连接
    - 支持多租户隔离
    - 支持设备订阅（带授权检查）
    - 支持告警订阅
    - 心跳保活
    """

    _instance = None  # 类级别的单例

    def __new__(cls):
        """单例模式：确保只有一个 ConnectionManager 实例"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            # 初始化实例属性
            cls._instance.active_connections = {}
            cls._instance.user_tenants = {}
            cls._instance.tenant_connections = {}
            cls._instance.subscriptions = {}
        return cls._instance

    async def connect(self, websocket: WebSocket, user_id: int, tenant_id: int):
        """
        接受新的 WebSocket 连接

        如果同一用户已有连接，则关闭旧连接
        """
        user_id_str = str(user_id)

        # 如果用户已有连接，先关闭旧连接
        if user_id_str in self.active_connections:
            old_ws = self.active_connections[user_id_str]
            try:
                await old_ws.close()
            except Exception as e:
                logger.warning(f"关闭旧连接失败: {e}")

        # 接受新连接
        await websocket.accept()
        self.active_connections[user_id_str] = websocket
        self.user_tenants[user_id_str] = tenant_id

        # 添加到租户连接集合
        if tenant_id not in self.tenant_connections:
            self.tenant_connections[tenant_id] = set()
        self.tenant_connections[tenant_id].add(user_id_str)

        # 初始化订阅
        self.subscriptions[user_id_str] = {
            "devices": set(),
            "alarms": False,
            "device_status": set(),
        }

        logger.info(f"WebSocket 连接成功: user_id={user_id}, tenant_id={tenant_id}")

    async def disconnect(self, user_id: int):
        """断开用户连接"""
        user_id_str = str(user_id)

        if user_id_str in self.active_connections:
            del self.active_connections[user_id_str]

        if user_id_str in self.user_tenants:
            tenant_id = self.user_tenants[user_id_str]
            if tenant_id in self.tenant_connections:
                self.tenant_connections[tenant_id].discard(user_id_str)
            del self.user_tenants[user_id_str]

        if user_id_str in self.subscriptions:
            del self.subscriptions[user_id_str]

        logger.info(f"WebSocket 断开连接: user_id={user_id}")

    async def send_personal_message(self, user_id: int, message: dict):
        """发送个人消息"""
        user_id_str = str(user_id)
        if user_id_str in self.active_connections:
            try:
                await self.active_connections[user_id_str].send_json(message)
            except Exception as e:
                logger.warning(f"发送消息失败: user_id={user_id}, error={e}")

    async def broadcast_to_tenant(self, tenant_id: int, message: dict):
        """广播消息到租户内的所有用户"""
        if tenant_id not in self.tenant_connections:
            return

        disconnected = []
        for user_id_str in self.tenant_connections[tenant_id]:
            if user_id_str in self.active_connections:
                try:
                    await self.active_connections[user_id_str].send_json(message)
                except Exception as e:
                    logger.warning(f"广播消息失败: user_id={user_id_str}, error={e}")
                    disconnected.append(user_id_str)

        # 清理断开的连接
        for user_id_str in disconnected:
            if user_id_str in self.active_connections:
                del self.active_connections[user_id_str]

    async def subscribe_device(self, user_id: int, device_id: str, db: AsyncSession) -> bool:
        """
        订阅设备（带授权检查）

        Args:
            user_id: 用户 ID
            device_id: 设备 ID
            db: 数据库会话

        Returns:
            bool: 是否订阅成功（失败表示无权限或未连接）
        """
        user_id_str = str(user_id)

        # 检查用户是否已连接
        if user_id_str not in self.subscriptions:
            logger.warning(f"用户未连接，无法订阅: user_id={user_id}")
            return False

        # 授权检查：用户只能订阅自己租户的设备
        has_permission = await self.check_device_permission(db, user_id, device_id)
        if not has_permission:
            logger.warning(f"用户无权订阅设备: user_id={user_id}, device_id={device_id}")
            return False

        self.subscriptions[user_id_str]["devices"].add(device_id)
        logger.debug(f"用户订阅设备: user_id={user_id}, device_id={device_id}")
        return True

    async def unsubscribe_device(self, user_id: int, device_id: str):
        """取消订阅设备"""
        user_id_str = str(user_id)
        if user_id_str in self.subscriptions:
            self.subscriptions[user_id_str]["devices"].discard(device_id)

    async def subscribe_alarms(self, user_id: int):
        """订阅告警"""
        user_id_str = str(user_id)
        if user_id_str in self.subscriptions:
            self.subscriptions[user_id_str]["alarms"] = True
            logger.debug(f"用户订阅告警: user_id={user_id}")

    async def subscribe_device_status(self, user_id: int, device_id: str, db: AsyncSession) -> bool:
        """订阅设备状态变化（带授权检查）"""
        has_permission = await self.check_device_permission(db, user_id, device_id)
        if not has_permission:
            logger.warning(f"用户无权订阅设备状态: user_id={user_id}, device_id={device_id}")
            return False

        user_id_str = str(user_id)
        if user_id_str in self.subscriptions:
            self.subscriptions[user_id_str]["device_status"].add(device_id)
        return True

    async def unsubscribe_device_status(self, user_id: int, device_id: str):
        """取消订阅设备状态变化"""
        user_id_str = str(user_id)
        if user_id_str in self.subscriptions:
            self.subscriptions[user_id_str]["device_status"].discard(device_id)

    async def handle_message(self, user_id: int, raw_message: str, db: AsyncSession):
        """处理客户端消息"""
        try:
            message = json.loads(raw_message)
            message_type = message.get("type")

            if message_type == "ping":
                await self.send_personal_message(user_id, {"type": "pong"})

            elif message_type == "subscribe":
                await self._handle_subscribe(user_id, message, db)

            elif message_type == "unsubscribe":
                await self._handle_unsubscribe(user_id, message)

            else:
                await self.send_personal_message(user_id, {
                    "type": "error",
                    "message": f"未知的消息类型: {message_type}"
                })

        except json.JSONDecodeError:
            await self.send_personal_message(user_id, {
                "type": "error",
                "message": "无效的消息格式"
            })
        except Exception as e:
            logger.exception(f"处理消息失败: {e}")
            await self.send_personal_message(user_id, {
                "type": "error",
                "message": "处理消息失败"
            })

    async def _handle_subscribe(self, user_id: int, message: dict, db: AsyncSession):
        """处理订阅请求（带授权检查）"""
        topic = message.get("topic")
        device_id = message.get("device_id")

        if topic == "device" and device_id:
            success = await self.subscribe_device(user_id, device_id, db)
            if success:
                await self.send_personal_message(user_id, {
                    "type": "subscribed",
                    "topic": topic,
                    "device_id": device_id
                })
            else:
                await self.send_personal_message(user_id, {
                    "type": "error",
                    "message": "无权订阅该设备"
                })

        elif topic == "alarm":
            await self.subscribe_alarms(user_id)
            await self.send_personal_message(user_id, {
                "type": "subscribed",
                "topic": topic
            })

        elif topic == "device_status" and device_id:
            success = await self.subscribe_device_status(user_id, device_id, db)
            if success:
                await self.send_personal_message(user_id, {
                    "type": "subscribed",
                    "topic": topic,
                    "device_id": device_id
                })
            else:
                await self.send_personal_message(user_id, {
                    "type": "error",
                    "message": "无权订阅该设备状态"
                })

        else:
            await self.send_personal_message(user_id, {
                "type": "error",
                "message": "无效的订阅请求"
            })

    async def _handle_unsubscribe(self, user_id: int, message: dict):
        """处理取消订阅请求"""
        topic = message.get("topic")
        device_id = message.get("device_id")

        if topic == "device" and device_id:
            await self.unsubscribe_device(user_id, device_id)
            await self.send_personal_message(user_id, {
                "type": "unsubscribed",
                "topic": topic,
                "device_id": device_id
            })

        elif topic == "device_status" and device_id:
            await self.unsubscribe_device_status(user_id, device_id)
            await self.send_personal_message(user_id, {
                "type": "unsubscribed",
                "topic": topic,
                "device_id": device_id
            })

        else:
            await self.send_personal_message(user_id, {
                "type": "error",
                "message": "无效的取消订阅请求"
            })

    # ============ 消息推送方法 ============

    async def push_device_data(self, device_id: str, tenant_id: int, data: dict):
        """推送设备数据到订阅了该设备的用户"""
        message = {
            "type": "device_data",
            "device_id": device_id,
            "data": data,
            "timestamp": datetime.now(UTC).isoformat()
        }

        # 查找订阅了该设备的用户
        for user_id_str, subs in self.subscriptions.items():
            if device_id in subs.get("devices", set()):
                user_tenant = self.user_tenants.get(user_id_str)
                if user_tenant == tenant_id:
                    await self.send_personal_message(int(user_id_str), message)

    async def push_alarm(self, tenant_id: int, alarm_data: dict):
        """推送告警到订阅了告警的租户用户"""
        message = {
            "type": "alarm",
            "data": alarm_data,
            "timestamp": datetime.now(UTC).isoformat()
        }

        for user_id_str, subs in self.subscriptions.items():
            if subs.get("alarms"):
                user_tenant = self.user_tenants.get(user_id_str)
                if user_tenant == tenant_id:
                    await self.send_personal_message(int(user_id_str), message)

    async def push_device_status(self, device_id: str, tenant_id: int, is_online: bool):
        """推送设备状态变化"""
        message = {
            "type": "device_status",
            "device_id": device_id,
            "data": {
                "is_online": is_online
            },
            "timestamp": datetime.now(UTC).isoformat()
        }

        for user_id_str, subs in self.subscriptions.items():
            if device_id in subs.get("device_status", set()):
                user_tenant = self.user_tenants.get(user_id_str)
                if user_tenant == tenant_id:
                    await self.send_personal_message(int(user_id_str), message)

    async def check_device_permission(
        self, db: AsyncSession, user_id: int, device_id: str
    ) -> bool:
        """检查用户是否有权限访问设备"""
        user_id_str = str(user_id)
        tenant_id = self.user_tenants.get(user_id_str)
        if not tenant_id:
            return False

        result = await db.execute(
            select(Device).where(
                Device.device_id == device_id,
                Device.tenant_id == tenant_id
            )
        )
        device = result.scalar_one_or_none()
        return device is not None


# 全局连接管理器单例
manager = ConnectionManager()


def get_connection_manager() -> ConnectionManager:
    """获取连接管理器单例"""
    return manager
