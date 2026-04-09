"""
WebSocket 端点
用于实时数据推送

安全认证：使用初始消息认证而非 URL 参数，避免 token 泄露到日志
"""

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from jose import JWTError, jwt
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.models import User
from app.services.websocket_manager import ConnectionManager, get_connection_manager

router = APIRouter()


async def get_user_from_token(token: str, db: AsyncSession) -> User | None:
    """从 JWT Token 获取用户"""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        username = payload.get("sub")
        tenant_id = payload.get("tenant_id")

        if not username or not tenant_id:
            return None

        result = await db.execute(
            select(User).where(
                User.username == username,
                User.tenant_id == tenant_id,
                User.is_active.is_(True)
            )
        )
        return result.scalar_one_or_none()

    except JWTError as e:
        logger.error(f"JWT decode error: {e}")
        return None


# 使用 websocket_manager 中的全局管理器
manager = get_connection_manager()

# 认证超时时间（秒）
AUTH_TIMEOUT = 10

# 最大消息大小限制（字节）- 防止恶意大消息
MAX_MESSAGE_SIZE = 64 * 1024  # 64KB


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    db: AsyncSession = Depends(get_db)
):
    """
    WebSocket 端点（使用消息认证）

    认证流程：
    1. 客户端连接 WebSocket
    2. 客户端发送认证消息: {"type": "auth", "token": "JWT_TOKEN"}
    3. 服务端验证 Token，返回 {"type": "connected", "user_id": xxx}
    4. 认证失败返回 {"type": "error", "message": "认证失败"} 并关闭连接

    消息格式:
    客户端 -> 服务端:
    - {"type": "auth", "token": "xxx"} - 认证（必须首先发送）
    - {"type": "ping"} - 心跳
    - {"type": "subscribe", "topic": "device", "device_id": "xxx"} - 订阅设备
    - {"type": "subscribe", "topic": "alarm"} - 订阅告警
    - {"type": "subscribe", "topic": "device_status", "device_id": "xxx"} - 订阅设备状态
    - {"type": "unsubscribe", "topic": "device", "device_id": "xxx"} - 取消订阅

    服务端 -> 客户端:
    - {"type": "connected", "user_id": xxx} - 连接成功
    - {"type": "error", "message": "xxx"} - 认证失败或错误
    - {"type": "pong"} - 心跳响应
    - {"type": "subscribed", "topic": "xxx", "device_id": "xxx"} - 订阅成功
    - {"type": "unsubscribed", "topic": "xxx", "device_id": "xxx"} - 取消订阅成功
    - {"type": "device_data", "device_id": "xxx", "data": {...}} - 设备数据推送
    - {"type": "alarm", "data": {...}} - 告警推送
    - {"type": "device_status", "device_id": "xxx", "data": {...}} - 设备状态变化

    安全措施:
    - Token 不在 URL 参数中传递（避免日志泄露）
    - 认证超时机制（10秒）
    - 消息大小限制（64KB）
    """
    manager = get_connection_manager()

    # 先接受连接（但不注册用户）
    await websocket.accept()

    user = None
    try:
        # 等待认证消息（带超时）
        import asyncio
        import json

        try:
            raw_message = await asyncio.wait_for(
                websocket.receive_text(),
                timeout=AUTH_TIMEOUT
            )
        except TimeoutError:
            await websocket.close(code=4002, reason="认证超时")
            return

        # 检查消息大小
        if len(raw_message) > MAX_MESSAGE_SIZE:
            await websocket.close(code=4003, reason="消息过大")
            return

        # 解析认证消息
        try:
            message = json.loads(raw_message)
            if message.get("type") != "auth":
                await websocket.send_json({
                    "type": "error",
                    "message": "必须首先发送认证消息"
                })
                await websocket.close(code=4001, reason="认证失败：缺少认证消息")
                return

            token = message.get("token")
            if not token:
                await websocket.send_json({
                    "type": "error",
                    "message": "缺少认证令牌"
                })
                await websocket.close(code=4001, reason="认证失败：缺少令牌")
                return

        except json.JSONDecodeError:
            await websocket.send_json({
                "type": "error",
                "message": "无效的消息格式"
            })
            await websocket.close(code=4001, reason="认证失败：无效消息格式")
            return

        # 验证 Token
        user = await get_user_from_token(token, db)
        if not user:
            await websocket.send_json({
                "type": "error",
                "message": "无效的认证令牌"
            })
            await websocket.close(code=4001, reason="认证失败：无效令牌")
            return

        # 认证成功，注册连接
        await manager.connect(websocket, user.id, user.tenant_id)

        # 发送连接成功消息
        await manager.send_personal_message(user.id, {
            "type": "connected",
            "user_id": user.id,
            "tenant_id": user.tenant_id
        })

        # 消息循环
        while True:
            try:
                raw_message = await websocket.receive_text()

                # 检查消息大小
                if len(raw_message) > MAX_MESSAGE_SIZE:
                    await manager.send_personal_message(user.id, {
                        "type": "error",
                        "message": "消息过大，最大允许 64KB"
                    })
                    continue

                await manager.handle_message(user.id, raw_message, db)

            except WebSocketDisconnect:
                logger.info(f"WebSocket 断开: user_id={user.id}")
                break

            except Exception as e:
                logger.exception(f"WebSocket 消息处理错误: {e}")
                await manager.send_personal_message(user.id, {
                    "type": "error",
                    "message": "消息处理失败"
                })

    except WebSocketDisconnect:
        pass

    finally:
        if user:
            await manager.disconnect(user.id)


def get_manager() -> ConnectionManager:
    """获取连接管理器"""
    return manager
