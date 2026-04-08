"""
测试线程安全单例模式
"""
import pytest
import threading
import asyncio


class TestThreadSafeSingleton:
    """测试线程安全单例"""

    def test_version_detector_singleton_thread_safe(self):
        """测试版本检测器单例线程安全"""
        from app.services.version_detector import VersionDetectorSingleton
        from unittest.mock import MagicMock

        # 模拟 Redis 客户端
        mock_redis = MagicMock()

        instances = []

        def create_instance():
            instance = VersionDetectorSingleton.get_instance(mock_redis)
            instances.append(instance)

        # 创建多个线程同时获取实例
        threads = [threading.Thread(target=create_instance) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # 所有实例应该是同一个对象
        assert len(set(id(i) for i in instances)) == 1

    def test_mqtt_client_singleton_thread_safe(self):
        """测试 MQTT 客户端单例线程安全"""
        from app.mqtt.client import MQTTClientSingleton

        instances = []

        def create_instance():
            instance = MQTTClientSingleton.get_instance()
            instances.append(instance)

        # 创建多个线程同时获取实例
        threads = [threading.Thread(target=create_instance) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # 所有实例应该是同一个对象
        assert len(set(id(i) for i in instances)) == 1

    @pytest.mark.asyncio
    async def test_concurrent_access_to_singleton(self):
        """测试并发访问单例"""
        from app.services.version_detector import VersionDetectorSingleton
        from unittest.mock import AsyncMock

        mock_redis = AsyncMock()

        # 并发获取实例
        async def get_instance_task():
            return VersionDetectorSingleton.get_instance(mock_redis)

        instances = await asyncio.gather(*[get_instance_task() for _ in range(5)])

        # 所有实例应该是同一个对象
        assert len(set(id(i) for i in instances)) == 1