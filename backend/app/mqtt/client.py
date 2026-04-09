"""
MQTT 客户端管理
"""
import asyncio
import threading
from collections.abc import Awaitable, Callable
from typing import Any

import paho.mqtt.client as mqtt
from loguru import logger
from paho.mqtt.enums import CallbackAPIVersion

from app.core.config import settings

# 消息处理器类型
HandlerType = Callable[[str, str, str], Awaitable[None]]


class MQTTClient:
    """MQTT 客户端管理器"""

    def __init__(self):
        self.client: mqtt.Client | None = None
        self.connected = False
        self._message_handlers: dict[str, HandlerType] = {}
        self._loop: asyncio.AbstractEventLoop | None = None

    def connect(self):
        """连接到 MQTT Broker"""
        if self.client is not None:
            return

        # 获取当前事件循环
        try:
            self._loop = asyncio.get_running_loop()
        except RuntimeError:
            # 如果没有运行的事件循环，稍后获取
            self._loop = None

        self.client = mqtt.Client(callback_api_version=CallbackAPIVersion.VERSION2)
        self.client.username_pw_set(settings.MQTT_USERNAME, settings.MQTT_PASSWORD)

        # 设置回调
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message

        try:
            logger.info(f"连接 MQTT Broker: {settings.EMQX_HOST}:{settings.EMQX_MQTT_PORT}")
            self.client.connect(
                settings.EMQX_HOST,
                settings.EMQX_MQTT_PORT,
                keepalive=60
            )
            # 启动网络循环
            self.client.loop_start()
        except Exception as e:
            logger.error(f"MQTT 连接失败: {e}")
            raise

    def disconnect(self):
        """断开 MQTT 连接"""
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
            self.client = None
            self.connected = False
            logger.info("MQTT 已断开连接")

    def _on_connect(self, client: mqtt.Client, userdata: Any, flags: dict, rc: int, properties: Any):
        """连接回调"""
        if rc == 0:
            self.connected = True
            logger.info("MQTT 连接成功")

            # 获取事件循环（如果之前未获取）
            if self._loop is None:
                try:
                    self._loop = asyncio.get_running_loop()
                except RuntimeError:
                    pass

            # 订阅所有设备上行主题
            client.subscribe("/up/+/+")
            logger.info("订阅主题: /up/+/+")
        else:
            logger.error(f"MQTT 连接失败，返回码: {rc}")

    def _on_disconnect(self, client: mqtt.Client, userdata: Any, rc: int, properties: Any):
        """断开连接回调"""
        self.connected = False
        logger.warning(f"MQTT 断开连接，返回码: {rc}")

    def _on_message(self, client: mqtt.Client, userdata: Any, msg: mqtt.MQTTMessage):
        """消息回调 - 安全地在事件循环中调度异步任务"""
        try:
            topic = msg.topic
            payload = msg.payload.decode('utf-8')

            # 解析主题: /up/{device_id}/{action}
            parts = topic.split('/')
            if len(parts) >= 4 and parts[1] == 'up':
                device_id = parts[2]
                action = parts[3]

                # 调用对应的消息处理器
                handler = self._message_handlers.get(action)
                if handler:
                    # 安全地在事件循环中调度异步任务
                    if self._loop is not None:
                        asyncio.run_coroutine_threadsafe(
                            handler(device_id, payload, action),
                            self._loop
                        )
                    else:
                        logger.warning(f"无法调度异步任务，事件循环未就绪: {topic}")
                else:
                    logger.debug(f"未处理的消息: {topic}")

        except Exception as e:
            logger.exception(f"处理 MQTT 消息失败: {e}")

    def register_handler(self, action: str, handler: HandlerType) -> None:
        """注册消息处理器"""
        self._message_handlers[action] = handler
        logger.info(f"注册 MQTT 消息处理器: {action}")

    def publish(self, topic: str, payload: str) -> bool:
        """发布消息"""
        if not self.connected or not self.client:
            logger.warning("MQTT 未连接，无法发布消息")
            return False

        try:
            result = self.client.publish(topic, payload)
            logger.debug(f"发布消息: {topic}")
            return result.rc == mqtt.MQTT_ERR_SUCCESS
        except Exception as e:
            logger.error(f"发布 MQTT 消息失败: {e}")
            return False


class MQTTClientSingleton:
    """
    线程安全的 MQTT 客户端单例

    使用双重检查锁定模式确保线程安全
    """
    _instance: MQTTClient | None = None
    _lock = threading.Lock()

    @classmethod
    def get_instance(cls) -> MQTTClient:
        """
        获取 MQTT 客户端单例实例

        Returns:
            MQTTClient 实例
        """
        # 第一次检查（无锁）
        if cls._instance is None:
            # 加锁
            with cls._lock:
                # 第二次检查（有锁）
                if cls._instance is None:
                    cls._instance = MQTTClient()
                    logger.info("MQTT 客户端单例已创建")

        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """重置单例（用于测试）"""
        with cls._lock:
            if cls._instance is not None:
                cls._instance.disconnect()
            cls._instance = None


# 向后兼容的全局访问函数
def get_mqtt_client() -> MQTTClient:
    """获取 MQTT 客户端实例"""
    return MQTTClientSingleton.get_instance()


def init_mqtt_client() -> MQTTClient:
    """初始化 MQTT 客户端"""
    client = get_mqtt_client()
    client.connect()
    return client
