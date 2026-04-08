"""
MQTT 消息处理器
处理设备上报的各类消息
"""
import json
from datetime import datetime
from typing import Optional, Dict, Any, Callable
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.models import Device, DeviceData, Alarm, Tenant
from app.services import get_version_detector, ProtocolParserRegistry
from app.mqtt.client import get_mqtt_client


class MQTTMessageHandler:
    """MQTT 消息处理器"""

    def __init__(self, db_session_factory: Callable):
        self.db_session_factory = db_session_factory

    async def handle_login(self, device_id: str, payload: str, action: str):
        """
        处理设备上线消息

        收到 login 后主动发送 getparam 探测版本
        """
        try:
            data = json.loads(payload)
            logger.info(f"设备上线: {device_id}, data: {data}")

            async with self.db_session_factory() as db:
                # 查找或创建设备
                device = await self._get_or_create_device(db, device_id)

                # 更新设备在线状态
                device.is_online = True
                device.last_seen_at = datetime.utcnow()
                await db.commit()

            # 主动发送 getparam 探测版本
            await self._send_getparam(device_id)
            logger.info(f"已发送 getparam 命令到设备: {device_id}")

        except Exception as e:
            logger.exception(f"处理设备上线消息失败: {e}")

    async def handle_datas(self, device_id: str, payload: str, action: str):
        """处理设备数据上送"""
        try:
            data = json.loads(payload)
            mid = data.get("mid")
            msg_data = data.get("data", {})
            timestamp = data.get("timestamp")

            logger.debug(f"设备数据上送: {device_id}, temp: {msg_data.get('temp')}")

            async with self.db_session_factory() as db:
                device = await self._get_device(db, device_id)
                if not device:
                    logger.warning(f"设备不存在: {device_id}")
                    return

                # 保存数据到时序表
                device_data = DeviceData(
                    device_id=device_id,
                    tenant_id=device.tenant_id,
                    temp=msg_data.get("temp"),
                    humi=msg_data.get("humi"),
                    airstate=msg_data.get("airstate"),
                    current=msg_data.get("current"),
                    csq=msg_data.get("csq"),
                    air_err=msg_data.get("air_err"),
                    alarmtemp=msg_data.get("alarmtemp"),
                    alarmhumi=msg_data.get("alarmhumi"),
                )
                db.add(device_data)

                # 更新设备状态
                device.last_seen_at = datetime.utcnow()
                await db.commit()

            # 发送回复
            await self._send_reply(device_id, "datas_reply", mid, 200)

        except Exception as e:
            logger.exception(f"处理数据上送消息失败: {e}")

    async def handle_getparam_reply(self, device_id: str, payload: str, action: str):
        """
        处理参数查询回复

        这是版本探测的关键消息
        """
        try:
            data = json.loads(payload)
            param_data = data.get("data", {})

            logger.info(f"收到参数回复: {device_id}")

            # 检测版本
            version_detector = get_version_detector()
            version = await version_detector.detect_version(device_id, param_data)

            # 使用对应版本的解析器解析参数
            parser = ProtocolParserRegistry.get_parser(version)
            parsed = parser.parse_parameter(param_data)

            # 更新数据库
            async with self.db_session_factory() as db:
                device = await self._get_device(db, device_id)
                if device:
                    device.protocol_version = version
                    device.settings = param_data
                    device.sim_card = param_data.get("Sim")
                    device.firmware_version = str(param_data.get("Ver", ""))
                    await db.commit()

            logger.info(f"设备 {device_id} 版本: {version}, 参数已更新")

        except Exception as e:
            logger.exception(f"处理参数回复消息失败: {e}")

    async def handle_parameter(self, device_id: str, payload: str, action: str):
        """处理设备主动上报参数"""
        try:
            data = json.loads(payload)
            mid = data.get("mid")
            param_data = data.get("data", {})

            logger.info(f"设备上报参数: {device_id}")

            # 检测版本（如果缓存中没有）
            version_detector = get_version_detector()
            version = await version_detector.get_version(device_id)
            if not version:
                version = await version_detector.detect_version(device_id, param_data)

            # 更新数据库
            async with self.db_session_factory() as db:
                device = await self._get_device(db, device_id)
                if device:
                    device.protocol_version = version
                    device.settings = param_data
                    await db.commit()

            # 发送回复
            await self._send_reply(device_id, "parameter_reply", mid, 200)

        except Exception as e:
            logger.exception(f"处理参数上报消息失败: {e}")

    async def handle_ctr_reply(self, device_id: str, payload: str, action: str):
        """处理远程控制回复"""
        try:
            data = json.loads(payload)
            code = data.get("code")

            logger.info(f"远程控制回复: {device_id}, code: {code}")

        except Exception as e:
            logger.exception(f"处理控制回复消息失败: {e}")

    async def handle_set_reply(self, device_id: str, payload: str, action: str):
        """处理设置参数回复"""
        try:
            data = json.loads(payload)
            code = data.get("code")

            logger.info(f"设置参数回复: {device_id}, code: {code}")

        except Exception as e:
            logger.exception(f"处理设置回复消息失败: {e}")

    # ============ 辅助方法 ============

    async def _get_device(self, db: AsyncSession, device_id: str) -> Optional[Device]:
        """获取设备"""
        result = await db.execute(
            select(Device).where(Device.device_id == device_id)
        )
        return result.scalar_one_or_none()

    async def _get_or_create_device(self, db: AsyncSession, device_id: str) -> Device:
        """获取或创建设备"""
        device = await self._get_device(db, device_id)
        if device:
            return device

        # 创建新设备（使用默认租户）
        result = await db.execute(select(Tenant).limit(1))
        tenant = result.scalar_one_or_none()

        device = Device(
            tenant_id=tenant.id if tenant else 1,
            device_id=device_id,
            name=f"设备_{device_id[-6:]}",
            protocol_version="V10",
        )
        db.add(device)
        await db.commit()
        await db.refresh(device)
        logger.info(f"创建新设备: {device_id}")
        return device

    async def _send_getparam(self, device_id: str):
        """发送参数查询命令"""
        topic = f"/down/{device_id}/getparam"
        payload = json.dumps({"timestamp": str(int(datetime.now().timestamp()))})
        get_mqtt_client().publish(topic, payload)

    async def _send_reply(self, device_id: str, action: str, mid: Optional[int], code: int):
        """发送回复消息"""
        topic = f"/down/{device_id}/{action}"
        payload = json.dumps({
            "mid": mid,
            "code": code,
            "timestamp": str(int(datetime.now().timestamp()))
        })
        get_mqtt_client().publish(topic, payload)


def init_message_handlers(db_session_factory: Callable):
    """初始化消息处理器"""
    handler = MQTTMessageHandler(db_session_factory)
    mqtt = get_mqtt_client()

    # 注册消息处理器
    mqtt.register_handler("login", handler.handle_login)
    mqtt.register_handler("datas", handler.handle_datas)
    mqtt.register_handler("getparam_reply", handler.handle_getparam_reply)
    mqtt.register_handler("parameter", handler.handle_parameter)
    mqtt.register_handler("ctr_reply", handler.handle_ctr_reply)
    mqtt.register_handler("set_reply", handler.handle_set_reply)

    logger.info("MQTT 消息处理器已初始化")
    return handler