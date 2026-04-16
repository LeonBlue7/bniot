"""
版本检测模块
检测设备协议版本并缓存到 Redis
"""
import json
import threading
from datetime import UTC, datetime
from typing import Any, ClassVar

import redis.asyncio as redis
from loguru import logger


class VersionDetector:
    """
    设备协议版本检测器

    版本识别策略（仅通过特征参数检测）：
    - V20 独有参数：108（冬天开始月份）、109（冬天结束月份）、110（空调关机间隔）
    - 若参数数据包含 108、109 或 110 任一参数，则为 V20
    - 否则为 V10

    注意：Ver 字段是固件版本号，不能用于判断协议版本
    """

    # V20 独有参数（V10 不存在）
    V20_EXCLUSIVE_PARAMS: ClassVar[set[str]] = {"108", "109", "110"}

    # Redis 键前缀
    REDIS_KEY_PREFIX: ClassVar[str] = "device_version:"

    # 缓存过期时间（7天）
    CACHE_EXPIRE_SECONDS: ClassVar[int] = 7 * 24 * 60 * 60

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client

    def _get_cache_key(self, device_id: str) -> str:
        """获取 Redis 缓存键"""
        return f"{self.REDIS_KEY_PREFIX}{device_id}"

    async def get_version(self, device_id: str) -> str | None:
        """
        从缓存获取设备版本

        Args:
            device_id: 设备ID (IMEI)

        Returns:
            版本号 (V10/V20) 或 None
        """
        try:
            key = self._get_cache_key(device_id)
            data = await self.redis.get(key)
            if data:
                cached = json.loads(data)
                logger.debug(f"从缓存获取设备版本: {device_id} -> {cached.get('version')}")
                return cached.get("version")
        except Exception as e:
            logger.error(f"获取设备版本缓存失败: {e}")
        return None

    async def detect_version(self, device_id: str, param_data: dict[str, Any]) -> str:
        """
        检测设备协议版本（仅通过特征参数检测）

        V20 独有参数：108、109、110（V10 协议不存在这些参数）

        Args:
            device_id: 设备ID (IMEI)
            param_data: 参数数据 (/getparam_reply 返回的 data 字段)

        Returns:
            版本号 (V10/V20)
        """
        # 通过特征参数检测
        # 若参数数据包含 108、109 或 110 任一参数，则为 V20，否则为 V10
        param_keys = {str(k) for k in param_data.keys()}

        if param_keys & self.V20_EXCLUSIVE_PARAMS:
            # 存在 V20 独有参数
            version = "V20"
            found_params = param_keys & self.V20_EXCLUSIVE_PARAMS
            logger.info(f"通过特征参数检测版本: {device_id} -> V20 (发现参数: {found_params})")
        else:
            version = "V10"
            logger.info(f"通过特征参数检测版本: {device_id} -> V10 (无V20独有参数)")

        await self.cache_version(device_id, version, method="feature_params")
        return version

    async def cache_version(
        self,
        device_id: str,
        version: str,
        method: str = "unknown",
        extra: dict[str, Any] | None = None
    ) -> None:
        """
        缓存设备版本信息

        Args:
            device_id: 设备ID
            version: 版本号
            method: 检测方法 (ver_field, feature_params, default)
            extra: 额外信息
        """
        try:
            key = self._get_cache_key(device_id)
            data = {
                "version": version,
                "detected_at": datetime.now(UTC).isoformat(),
                "method": method,
                **(extra or {})
            }
            await self.redis.setex(
                key,
                self.CACHE_EXPIRE_SECONDS,
                json.dumps(data)
            )
            logger.debug(f"缓存设备版本: {device_id} -> {version}")
        except Exception as e:
            logger.error(f"缓存设备版本失败: {e}")

    async def clear_version(self, device_id: str) -> None:
        """清除设备版本缓存"""
        try:
            key = self._get_cache_key(device_id)
            await self.redis.delete(key)
            logger.debug(f"清除设备版本缓存: {device_id}")
        except Exception as e:
            logger.error(f"清除设备版本缓存失败: {e}")


class VersionDetectorSingleton:
    """
    线程安全的版本检测器单例

    使用双重检查锁定模式确保线程安全
    """
    _instance: VersionDetector | None = None
    _lock = threading.Lock()
    _initialized = False

    @classmethod
    def get_instance(cls, redis_client: redis.Redis) -> VersionDetector:
        """
        获取版本检测器单例实例

        Args:
            redis_client: Redis 客户端

        Returns:
            VersionDetector 实例
        """
        # 第一次检查（无锁）
        if cls._instance is None:
            # 加锁
            with cls._lock:
                # 第二次检查（有锁）
                if cls._instance is None:
                    cls._instance = VersionDetector(redis_client)
                    cls._initialized = True
                    logger.info("版本检测器单例已创建")

        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """重置单例（用于测试）"""
        with cls._lock:
            cls._instance = None
            cls._initialized = False


# 向后兼容的全局访问函数
async def init_version_detector(redis_client: redis.Redis) -> VersionDetector:
    """初始化版本检测器"""
    return VersionDetectorSingleton.get_instance(redis_client)


def get_version_detector() -> VersionDetector:
    """获取版本检测器实例"""
    instance = VersionDetectorSingleton._instance
    if instance is None:
        raise RuntimeError("版本检测器未初始化")
    return instance
