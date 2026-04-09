"""
WebSocket 连接管理器测试

测试 WebSocket 连接管理、认证、多租户隔离、订阅机制、授权检查
"""
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from app.models import User


def reset_connection_manager():
    """重置 ConnectionManager 单例（用于测试隔离）"""
    from app.services.websocket_manager import ConnectionManager
    ConnectionManager._instance = None


class TestConnectionManager:
    """WebSocket 连接管理器测试"""

    def test_connection_manager_singleton(self):
        """测试连接管理器单例模式"""
        from app.services.websocket_manager import ConnectionManager

        reset_connection_manager()
        manager1 = ConnectionManager()
        manager2 = ConnectionManager()

        # 单例模式：两个实例应该是同一个对象
        assert manager1 is manager2

    def test_connection_manager_init(self):
        """测试连接管理器初始化"""
        from app.services.websocket_manager import ConnectionManager

        reset_connection_manager()
        manager = ConnectionManager()
        assert manager.active_connections == {}
        assert manager.user_tenants == {}
        assert manager.tenant_connections == {}
        assert manager.subscriptions == {}

    @pytest.mark.asyncio
    async def test_connect_new_user(self, db_session, test_user):
        """测试新用户连接"""
        from app.services.websocket_manager import ConnectionManager

        reset_connection_manager()
        manager = ConnectionManager()
        mock_websocket = AsyncMock()
        mock_websocket.accept = AsyncMock()

        await manager.connect(mock_websocket, test_user.id, test_user.tenant_id)

        assert str(test_user.id) in manager.active_connections
        assert mock_websocket.accept.called

    @pytest.mark.asyncio
    async def test_disconnect_user(self, db_session, test_user):
        """测试用户断开连接"""
        from app.services.websocket_manager import ConnectionManager

        reset_connection_manager()
        manager = ConnectionManager()
        mock_websocket = AsyncMock()
        mock_websocket.accept = AsyncMock()

        await manager.connect(mock_websocket, test_user.id, test_user.tenant_id)
        await manager.disconnect(test_user.id)

        assert str(test_user.id) not in manager.active_connections

    @pytest.mark.asyncio
    async def test_send_personal_message(self, db_session, test_user):
        """测试发送个人消息"""
        from app.services.websocket_manager import ConnectionManager

        reset_connection_manager()
        manager = ConnectionManager()
        mock_websocket = AsyncMock()
        mock_websocket.accept = AsyncMock()
        mock_websocket.send_json = AsyncMock()

        await manager.connect(mock_websocket, test_user.id, test_user.tenant_id)
        message = {"type": "test", "data": "hello"}
        await manager.send_personal_message(test_user.id, message)

        mock_websocket.send_json.assert_called_once_with(message)

    @pytest.mark.asyncio
    async def test_broadcast_to_tenant(self, db_session, test_user):
        """测试广播消息到租户"""
        from app.services.websocket_manager import ConnectionManager

        reset_connection_manager()
        manager = ConnectionManager()

        # 创建两个同租户用户连接
        mock_ws1 = AsyncMock()
        mock_ws1.accept = AsyncMock()
        mock_ws1.send_json = AsyncMock()

        mock_ws2 = AsyncMock()
        mock_ws2.accept = AsyncMock()
        mock_ws2.send_json = AsyncMock()

        await manager.connect(mock_ws1, test_user.id, test_user.tenant_id)
        await manager.connect(mock_ws2, test_user.id + 1, test_user.tenant_id)

        message = {"type": "broadcast", "data": "tenant message"}
        await manager.broadcast_to_tenant(test_user.tenant_id, message)

        # 两个连接都应收到消息
        mock_ws1.send_json.assert_called_once_with(message)
        mock_ws2.send_json.assert_called_once_with(message)

    @pytest.mark.asyncio
    async def test_broadcast_tenant_isolation(self):
        """测试租户隔离：消息不会发送给其他租户"""
        from app.services.websocket_manager import ConnectionManager

        reset_connection_manager()
        manager = ConnectionManager()

        mock_ws1 = AsyncMock()
        mock_ws1.accept = AsyncMock()
        mock_ws1.send_json = AsyncMock()

        mock_ws2 = AsyncMock()
        mock_ws2.accept = AsyncMock()
        mock_ws2.send_json = AsyncMock()

        await manager.connect(mock_ws1, 1, 1)  # tenant_id=1
        await manager.connect(mock_ws2, 2, 2)  # tenant_id=2

        message = {"type": "tenant1_only", "data": "secret"}
        await manager.broadcast_to_tenant(1, message)

        # 只有租户1的用户收到消息
        mock_ws1.send_json.assert_called_once_with(message)
        mock_ws2.send_json.assert_not_called()

    @pytest.mark.asyncio
    async def test_subscribe_device_with_permission(self, db_session):
        """测试订阅设备（有权限）"""
        from app.services.websocket_manager import ConnectionManager

        reset_connection_manager()
        manager = ConnectionManager()
        mock_ws = AsyncMock()
        mock_ws.accept = AsyncMock()
        mock_ws.send_json = AsyncMock()

        await manager.connect(mock_ws, 1, 1)

        # Mock check_device_permission 返回 True
        with patch.object(manager, 'check_device_permission', new=AsyncMock(return_value=True)):
            success = await manager.subscribe_device(1, "device_001", db_session)
            assert success is True
            assert "device_001" in manager.subscriptions["1"]["devices"]

    @pytest.mark.asyncio
    async def test_subscribe_device_without_permission(self, db_session):
        """测试订阅设备（无权限）"""
        from app.services.websocket_manager import ConnectionManager

        reset_connection_manager()
        manager = ConnectionManager()
        mock_ws = AsyncMock()
        mock_ws.accept = AsyncMock()
        mock_ws.send_json = AsyncMock()

        await manager.connect(mock_ws, 1, 1)

        # Mock check_device_permission 返回 False
        with patch.object(manager, 'check_device_permission', new=AsyncMock(return_value=False)):
            success = await manager.subscribe_device(1, "device_001", db_session)
            assert success is False
            assert "device_001" not in manager.subscriptions["1"]["devices"]

    @pytest.mark.asyncio
    async def test_subscribe_device_not_connected(self, db_session):
        """测试订阅设备（用户未连接）"""
        from app.services.websocket_manager import ConnectionManager

        reset_connection_manager()
        manager = ConnectionManager()

        # 用户未连接，订阅应失败
        with patch.object(manager, 'check_device_permission', new=AsyncMock(return_value=True)):
            success = await manager.subscribe_device(1, "device_001", db_session)
            assert success is False  # 用户未连接

    @pytest.mark.asyncio
    async def test_subscribe_device_status_with_permission(self, db_session):
        """测试订阅设备状态（有权限）"""
        from app.services.websocket_manager import ConnectionManager

        reset_connection_manager()
        manager = ConnectionManager()
        mock_ws = AsyncMock()
        mock_ws.accept = AsyncMock()
        mock_ws.send_json = AsyncMock()

        await manager.connect(mock_ws, 1, 1)

        with patch.object(manager, 'check_device_permission', new=AsyncMock(return_value=True)):
            success = await manager.subscribe_device_status(1, "device_001", db_session)
            assert success is True
            assert "device_001" in manager.subscriptions["1"]["device_status"]

    @pytest.mark.asyncio
    async def test_subscribe_alarms(self):
        """测试订阅告警"""
        from app.services.websocket_manager import ConnectionManager

        reset_connection_manager()
        manager = ConnectionManager()
        mock_ws = AsyncMock()
        mock_ws.accept = AsyncMock()

        await manager.connect(mock_ws, 1, 1)
        await manager.subscribe_alarms(1)

        assert manager.subscriptions["1"]["alarms"] is True

    @pytest.mark.asyncio
    async def test_handle_ping_message(self, db_session):
        """测试处理 ping 消息"""
        from app.services.websocket_manager import ConnectionManager

        reset_connection_manager()
        manager = ConnectionManager()
        mock_ws = AsyncMock()
        mock_ws.accept = AsyncMock()
        mock_ws.send_json = AsyncMock()

        await manager.connect(mock_ws, 1, 1)
        await manager.handle_message(1, '{"type": "ping"}', db_session)

        mock_ws.send_json.assert_called_once_with({"type": "pong"})

    @pytest.mark.asyncio
    async def test_handle_subscribe_message_alarm(self, db_session):
        """测试处理 subscribe 消息（告警）"""
        from app.services.websocket_manager import ConnectionManager

        reset_connection_manager()
        manager = ConnectionManager()
        mock_ws = AsyncMock()
        mock_ws.accept = AsyncMock()
        mock_ws.send_json = AsyncMock()

        await manager.connect(mock_ws, 1, 1)
        await manager.handle_message(1, '{"type": "subscribe", "topic": "alarm"}', db_session)

        assert manager.subscriptions["1"]["alarms"] is True

    @pytest.mark.asyncio
    async def test_handle_subscribe_message_device_with_permission(self, db_session):
        """测试处理 subscribe 消息（设备，有权限）"""
        from app.services.websocket_manager import ConnectionManager

        reset_connection_manager()
        manager = ConnectionManager()
        mock_ws = AsyncMock()
        mock_ws.accept = AsyncMock()
        mock_ws.send_json = AsyncMock()

        await manager.connect(mock_ws, 1, 1)

        with patch.object(manager, 'check_device_permission', new=AsyncMock(return_value=True)):
            await manager.handle_message(
                1,
                '{"type": "subscribe", "topic": "device", "device_id": "device_001"}',
                db_session
            )

        assert "device_001" in manager.subscriptions["1"]["devices"]
        # 应发送 subscribed 确认消息
        calls = mock_ws.send_json.call_args_list
        subscribed_call = [c for c in calls if c[0][0].get("type") == "subscribed"]
        assert len(subscribed_call) > 0

    @pytest.mark.asyncio
    async def test_handle_subscribe_message_device_without_permission(self, db_session):
        """测试处理 subscribe 消息（设备，无权限）"""
        from app.services.websocket_manager import ConnectionManager

        reset_connection_manager()
        manager = ConnectionManager()
        mock_ws = AsyncMock()
        mock_ws.accept = AsyncMock()
        mock_ws.send_json = AsyncMock()

        await manager.connect(mock_ws, 1, 1)

        with patch.object(manager, 'check_device_permission', new=AsyncMock(return_value=False)):
            await manager.handle_message(
                1,
                '{"type": "subscribe", "topic": "device", "device_id": "device_001"}',
                db_session
            )

        assert "device_001" not in manager.subscriptions["1"]["devices"]
        # 应发送 error 消息
        calls = mock_ws.send_json.call_args_list
        error_call = [c for c in calls if c[0][0].get("type") == "error"]
        assert len(error_call) > 0

    @pytest.mark.asyncio
    async def test_push_device_data(self, db_session):
        """测试推送设备数据"""
        from app.services.websocket_manager import ConnectionManager

        reset_connection_manager()
        manager = ConnectionManager()
        mock_ws = AsyncMock()
        mock_ws.accept = AsyncMock()
        mock_ws.send_json = AsyncMock()

        await manager.connect(mock_ws, 1, tenant_id=1)

        # 先订阅设备（mock 授权）
        with patch.object(manager, 'check_device_permission', new=AsyncMock(return_value=True)):
            await manager.subscribe_device(1, "device_001", db_session)

        await manager.push_device_data("device_001", tenant_id=1, data={"temp": 25.5})

        # 应收到推送消息
        sent_message = mock_ws.send_json.call_args[0][0]
        assert sent_message["type"] == "device_data"
        assert sent_message["device_id"] == "device_001"
        assert sent_message["data"]["temp"] == 25.5

    @pytest.mark.asyncio
    async def test_push_alarm(self):
        """测试推送告警"""
        from app.services.websocket_manager import ConnectionManager

        reset_connection_manager()
        manager = ConnectionManager()
        mock_ws = AsyncMock()
        mock_ws.accept = AsyncMock()
        mock_ws.send_json = AsyncMock()

        await manager.connect(mock_ws, 1, tenant_id=1)
        await manager.subscribe_alarms(1)
        await manager.push_alarm(
            tenant_id=1,
            alarm_data={"type": "offline", "device_id": "alarm_device_001"}
        )

        sent_message = mock_ws.send_json.call_args[0][0]
        assert sent_message["type"] == "alarm"
        assert sent_message["data"]["device_id"] == "alarm_device_001"

    @pytest.mark.asyncio
    async def test_push_device_status(self, db_session):
        """测试推送设备状态"""
        from app.services.websocket_manager import ConnectionManager

        reset_connection_manager()
        manager = ConnectionManager()
        mock_ws = AsyncMock()
        mock_ws.accept = AsyncMock()
        mock_ws.send_json = AsyncMock()

        await manager.connect(mock_ws, 1, tenant_id=1)

        with patch.object(manager, 'check_device_permission', new=AsyncMock(return_value=True)):
            await manager.subscribe_device_status(1, "device_001", db_session)

        await manager.push_device_status("device_001", tenant_id=1, is_online=True)

        sent_message = mock_ws.send_json.call_args[0][0]
        assert sent_message["type"] == "device_status"
        assert sent_message["data"]["is_online"] is True

    @pytest.mark.asyncio
    async def test_check_device_permission(self, db_session):
        """测试设备权限检查"""
        from app.services.websocket_manager import ConnectionManager

        reset_connection_manager()
        manager = ConnectionManager()
        mock_ws = AsyncMock()
        mock_ws.accept = AsyncMock()

        await manager.connect(mock_ws, 1, tenant_id=1)

        # Mock 数据库查询返回设备
        mock_device = MagicMock()
        mock_device.device_id = "device_001"
        mock_device.tenant_id = 1

        with patch.object(db_session, 'execute', new=AsyncMock(return_value=MagicMock(
            scalar_one_or_none=MagicMock(return_value=mock_device)
        ))):
            has_permission = await manager.check_device_permission(db_session, 1, "device_001")
            assert has_permission is True

        # 测试无权限（设备不存在或不同租户）
        with patch.object(db_session, 'execute', new=AsyncMock(return_value=MagicMock(
            scalar_one_or_none=MagicMock(return_value=None)
        ))):
            has_permission = await manager.check_device_permission(db_session, 1, "device_002")
            assert has_permission is False


class TestWebSocketEndpoint:
    """WebSocket 端点测试"""

    def test_websocket_endpoint_exists(self, test_app):
        """测试 WebSocket 端点存在"""
        # 检查 WebSocket 端点是否注册
        routes = [route.path for route in test_app.routes]
        assert "/api/ws" in routes

    def test_websocket_route_registered_correctly(self, test_app):
        """测试 WebSocket 路由正确注册"""
        from app.api.endpoints.websocket import router

        # 检查 WebSocket 路由配置
        ws_routes = [r for r in router.routes if hasattr(r, 'path') and r.path == "/ws"]
        assert len(ws_routes) == 1


class TestWebSocketSecurity:
    """WebSocket 安全测试"""

    @pytest.mark.asyncio
    async def test_auth_required_before_subscription(self, db_session):
        """测试认证后才能订阅"""
        from app.services.websocket_manager import ConnectionManager

        reset_connection_manager()
        manager = ConnectionManager()

        # 用户未连接，订阅应失败
        with patch.object(manager, 'check_device_permission', new=AsyncMock(return_value=True)):
            success = await manager.subscribe_device(1, "device_001", db_session)
            assert success is False  # 用户未连接


class TestWebSocketEdgeCases:
    """WebSocket 边缘情况测试"""

    @pytest.mark.asyncio
    async def test_send_to_disconnected_user(self):
        """测试向已断开连接的用户发送消息"""
        from app.services.websocket_manager import ConnectionManager

        reset_connection_manager()
        manager = ConnectionManager()
        # 用户从未连接，发送消息应静默处理
        await manager.send_personal_message(999, {"type": "test"})
        # 不应抛出异常

    @pytest.mark.asyncio
    async def test_broadcast_to_empty_tenant(self):
        """测试向没有连接的租户广播"""
        from app.services.websocket_manager import ConnectionManager

        reset_connection_manager()
        manager = ConnectionManager()
        # 租户没有连接，广播应静默处理
        await manager.broadcast_to_tenant(999, {"type": "test"})
        # 不应抛出异常

    @pytest.mark.asyncio
    async def test_concurrent_connections_same_user(self):
        """测试同一用户并发连接（应替换旧连接）"""
        from app.services.websocket_manager import ConnectionManager

        reset_connection_manager()
        manager = ConnectionManager()

        mock_ws1 = AsyncMock()
        mock_ws1.accept = AsyncMock()
        mock_ws1.close = AsyncMock()

        mock_ws2 = AsyncMock()
        mock_ws2.accept = AsyncMock()

        user_id = 1
        tenant_id = 1

        # 第一次连接
        await manager.connect(mock_ws1, user_id, tenant_id)
        # 第二次连接（同一用户）
        await manager.connect(mock_ws2, user_id, tenant_id)

        # 旧连接应被关闭
        mock_ws1.close.assert_called_once()
        # 新连接应被接受
        mock_ws2.accept.assert_called_once()

    @pytest.mark.asyncio
    async def test_invalid_message_format(self, db_session, test_user):
        """测试无效消息格式处理"""
        from app.services.websocket_manager import ConnectionManager

        reset_connection_manager()
        manager = ConnectionManager()
        mock_websocket = AsyncMock()
        mock_websocket.accept = AsyncMock()
        mock_websocket.send_json = AsyncMock()

        await manager.connect(mock_websocket, test_user.id, test_user.tenant_id)

        # 发送无效消息应被优雅处理
        await manager.handle_message(test_user.id, "invalid json string", db_session)
        # 应发送错误响应
        sent_message = mock_websocket.send_json.call_args[0][0]
        assert sent_message["type"] == "error"

    @pytest.mark.asyncio
    async def test_unknown_message_type(self, db_session):
        """测试未知消息类型处理"""
        from app.services.websocket_manager import ConnectionManager

        reset_connection_manager()
        manager = ConnectionManager()
        mock_ws = AsyncMock()
        mock_ws.accept = AsyncMock()
        mock_ws.send_json = AsyncMock()

        await manager.connect(mock_ws, 1, 1)
        await manager.handle_message(1, '{"type": "unknown_type"}', db_session)

        sent_message = mock_ws.send_json.call_args[0][0]
        assert sent_message["type"] == "error"

    @pytest.mark.asyncio
    async def test_push_to_non_subscribed_user(self):
        """测试向未订阅的用户推送消息"""
        from app.services.websocket_manager import ConnectionManager

        reset_connection_manager()
        manager = ConnectionManager()
        mock_ws = AsyncMock()
        mock_ws.accept = AsyncMock()
        mock_ws.send_json = AsyncMock()

        await manager.connect(mock_ws, 1, tenant_id=1)
        # 用户未订阅设备，推送不应发送
        await manager.push_device_data("device_001", tenant_id=1, data={"temp": 25.5})

        # send_json 只被调用一次（连接确认消息）
        # 因为用户未订阅，推送消息不会发送
        assert mock_ws.send_json.call_count == 0

    @pytest.mark.asyncio
    async def test_push_to_wrong_tenant(self, db_session):
        """测试向错误租户推送消息"""
        from app.services.websocket_manager import ConnectionManager

        reset_connection_manager()
        manager = ConnectionManager()
        mock_ws = AsyncMock()
        mock_ws.accept = AsyncMock()
        mock_ws.send_json = AsyncMock()

        await manager.connect(mock_ws, 1, tenant_id=1)

        with patch.object(manager, 'check_device_permission', new=AsyncMock(return_value=True)):
            await manager.subscribe_device(1, "device_001", db_session)

        # 推送到不同租户的消息不应发送
        await manager.push_device_data("device_001", tenant_id=2, data={"temp": 25.5})

        # 不应收到推送消息
        assert mock_ws.send_json.call_count == 0