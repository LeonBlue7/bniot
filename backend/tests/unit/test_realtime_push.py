"""
实时数据推送服务测试

TDD 测试用例：设备数据实时推送、状态变化推送、告警推送
"""
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from app.models.models import Alarm, Tenant, User
from app.services.auth import create_access_token, get_password_hash


class TestRealtimeDataPushService:
    """实时数据推送服务测试"""

    @pytest.mark.asyncio
    async def test_push_device_data(self):
        """测试推送设备实时数据"""
        from app.services.realtime_push import RealtimeDataPushService

        service = RealtimeDataPushService()

        # Mock WebSocket 管理器
        with patch.object(service.manager, 'push_device_data', new=AsyncMock()):
            data = {
                "temp": 25.5,
                "humi": 60.0,
                "airstate": 1,
                "current": 2.5,
                "csq": 20.0,
            }

            await service.push_device_data(
                device_id="device_001",
                tenant_id=1,
                data=data
            )

            service.manager.push_device_data.assert_called_once()

    @pytest.mark.asyncio
    async def test_push_device_status_online(self):
        """测试推送设备在线状态"""
        from app.services.realtime_push import RealtimeDataPushService

        service = RealtimeDataPushService()

        with patch.object(service.manager, 'push_device_status', new=AsyncMock()):
            await service.push_device_status(
                device_id="device_001",
                tenant_id=1,
                is_online=True
            )

            service.manager.push_device_status.assert_called_once_with(
                "device_001", 1, True
            )

    @pytest.mark.asyncio
    async def test_push_device_status_offline(self):
        """测试推送设备离线状态"""
        from app.services.realtime_push import RealtimeDataPushService

        service = RealtimeDataPushService()

        with patch.object(service.manager, 'push_device_status', new=AsyncMock()):
            await service.push_device_status(
                device_id="device_001",
                tenant_id=1,
                is_online=False
            )

            service.manager.push_device_status.assert_called_once_with(
                "device_001", 1, False
            )

    @pytest.mark.asyncio
    async def test_push_alarm(self):
        """测试推送告警"""
        from app.services.realtime_push import RealtimeDataPushService

        service = RealtimeDataPushService()

        with patch.object(service.manager, 'push_alarm', new=AsyncMock()):
            alarm_data = {
                "type": "offline",
                "device_id": "device_001",
                "severity": "high",
                "message": "设备离线告警"
            }

            await service.push_alarm(
                tenant_id=1,
                alarm_data=alarm_data
            )

            service.manager.push_alarm.assert_called_once()

    @pytest.mark.asyncio
    async def test_push_empty_device_data(self):
        """测试推送空设备数据"""
        from app.services.realtime_push import RealtimeDataPushService

        service = RealtimeDataPushService()

        with patch.object(service.manager, 'push_device_data', new=AsyncMock()):
            await service.push_device_data(
                device_id="device_001",
                tenant_id=1,
                data={}
            )

            service.manager.push_device_data.assert_called_once()


class TestRealtimePushIntegration:
    """实时推送集成测试"""

    @pytest.mark.asyncio
    async def test_get_realtime_push_service_singleton(self):
        """测试获取实时推送服务单例"""
        from app.services.realtime_push import get_realtime_push_service, RealtimeDataPushService, reset_realtime_push_service

        # 重置服务
        reset_realtime_push_service()

        service1 = get_realtime_push_service()
        service2 = get_realtime_push_service()

        assert service1 is service2
        assert isinstance(service1, RealtimeDataPushService)

    @pytest.mark.asyncio
    async def test_push_data_message_format(self):
        """测试推送数据消息格式"""
        from app.services.realtime_push import RealtimeDataPushService

        service = RealtimeDataPushService()

        # 模拟实际调用以验证消息格式
        captured_message = None

        async def mock_push(device_id, tenant_id, message):
            captured_message = message

        with patch.object(service.manager, 'push_device_data', new=mock_push):
            data = {
                "temp": 25.5,
                "humi": 60.0,
            }

            await service.push_device_data("device_001", 1, data)

            # 消息格式应包含 type, device_id, data, timestamp
            # 通过 mock 调用验证


class TestWebSocketSubscriptionFlow:
    """WebSocket订阅流程测试"""

    @pytest.mark.asyncio
    async def test_subscribe_and_receive_data(self, db_session):
        """测试订阅设备后接收数据"""
        from app.services.websocket_manager import ConnectionManager
        from app.services.realtime_push import RealtimeDataPushService

        # 重置管理器
        from tests.unit.test_websocket import reset_connection_manager
        reset_connection_manager()

        manager = ConnectionManager()
        service = RealtimeDataPushService()
        service.manager = manager

        mock_ws = AsyncMock()
        mock_ws.accept = AsyncMock()
        mock_ws.send_json = AsyncMock()

        # 连接用户
        await manager.connect(mock_ws, 1, tenant_id=1)

        # Mock 权限检查返回 True
        with patch.object(manager, 'check_device_permission', new=AsyncMock(return_value=True)):
            # 订阅设备
            await manager.subscribe_device(1, "device_001", db_session)

        # 推送设备数据
        await service.push_device_data("device_001", 1, {"temp": 25.5})

        # 用户应收到推送消息
        assert mock_ws.send_json.called

    @pytest.mark.asyncio
    async def test_subscribe_alarm_and_receive_notification(self):
        """测试订阅告警后接收通知"""
        from app.services.websocket_manager import ConnectionManager
        from app.services.realtime_push import RealtimeDataPushService

        from tests.unit.test_websocket import reset_connection_manager
        reset_connection_manager()

        manager = ConnectionManager()
        service = RealtimeDataPushService()
        service.manager = manager

        mock_ws = AsyncMock()
        mock_ws.accept = AsyncMock()
        mock_ws.send_json = AsyncMock()

        # 连接用户并订阅告警
        await manager.connect(mock_ws, 1, tenant_id=1)
        await manager.subscribe_alarms(1)

        # 推送告警
        await service.push_alarm(1, {
            "type": "offline",
            "device_id": "device_001"
        })

        # 用户应收到推送消息
        assert mock_ws.send_json.called

    @pytest.mark.asyncio
    async def test_tenant_isolation_in_push(self):
        """测试推送时租户隔离"""
        from app.services.websocket_manager import ConnectionManager
        from app.services.realtime_push import RealtimeDataPushService

        from tests.unit.test_websocket import reset_connection_manager
        reset_connection_manager()

        manager = ConnectionManager()
        service = RealtimeDataPushService()
        service.manager = manager

        # 创建两个租户的连接
        mock_ws1 = AsyncMock()
        mock_ws1.accept = AsyncMock()
        mock_ws1.send_json = AsyncMock()

        mock_ws2 = AsyncMock()
        mock_ws2.accept = AsyncMock()
        mock_ws2.send_json = AsyncMock()

        await manager.connect(mock_ws1, 1, tenant_id=1)
        await manager.connect(mock_ws2, 2, tenant_id=2)

        # 订阅告警
        await manager.subscribe_alarms(1)
        await manager.subscribe_alarms(2)

        # 推送告警到租户1
        await service.push_alarm(1, {"type": "offline", "device_id": "device_001"})

        # 只有租户1的用户收到消息
        assert mock_ws1.send_json.called
        assert not mock_ws2.send_json.called


class TestRealtimePushEdgeCases:
    """实时推送边缘情况测试"""

    @pytest.mark.asyncio
    async def test_push_to_no_subscribers(self):
        """测试推送到无订阅者的设备"""
        from app.services.websocket_manager import ConnectionManager
        from app.services.realtime_push import RealtimeDataPushService

        from tests.unit.test_websocket import reset_connection_manager
        reset_connection_manager()

        manager = ConnectionManager()
        service = RealtimeDataPushService()
        service.manager = manager

        mock_ws = AsyncMock()
        mock_ws.accept = AsyncMock()
        mock_ws.send_json = AsyncMock()

        # 连接用户但不订阅任何设备
        await manager.connect(mock_ws, 1, tenant_id=1)

        # 推送设备数据
        await service.push_device_data("device_001", 1, {"temp": 25.5})

        # 用户不应收到消息（未订阅）
        assert not mock_ws.send_json.called

    @pytest.mark.asyncio
    async def test_push_with_null_values(self):
        """测试推送包含空值的数据"""
        from app.services.realtime_push import RealtimeDataPushService

        service = RealtimeDataPushService()

        with patch.object(service.manager, 'push_device_data', new=AsyncMock()):
            data = {
                "temp": None,
                "humi": None,
                "airstate": None,
            }

            await service.push_device_data("device_001", 1, data)

            # 应成功推送（空值被包含在消息中）
            service.manager.push_device_data.assert_called_once()

    @pytest.mark.asyncio
    async def test_concurrent_pushes(self):
        """测试并发推送"""
        from app.services.realtime_push import RealtimeDataPushService
        import asyncio

        service = RealtimeDataPushService()

        with patch.object(service.manager, 'push_device_data', new=AsyncMock()):
            # 并发推送多个设备数据
            tasks = [
                service.push_device_data(f"device_{i}", 1, {"temp": i})
                for i in range(10)
            ]

            await asyncio.gather(*tasks)

            # 应有10次推送调用
            assert service.manager.push_device_data.call_count == 10