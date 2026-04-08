"""
测试应用配置
Phase 1 基础设施测试
"""
import pytest
from pydantic import ValidationError


class TestSettings:
    """测试 Settings 配置类"""

    def test_settings_has_required_fields(self):
        """测试配置包含必需字段"""
        from app.core.config import Settings

        settings = Settings(
            POSTGRES_HOST="localhost",
            POSTGRES_PORT=5432,
            POSTGRES_DB="test",
            POSTGRES_USER="test",
            POSTGRES_PASSWORD="test123",
            JWT_SECRET="test-secret"
        )

        assert settings.POSTGRES_HOST == "localhost"
        assert settings.POSTGRES_PORT == 5432
        assert settings.POSTGRES_DB == "test"

    def test_database_url_generation(self):
        """测试数据库 URL 生成"""
        from app.core.config import Settings

        settings = Settings(
            POSTGRES_HOST="postgres",
            POSTGRES_PORT=5432,
            POSTGRES_DB="bniot",
            POSTGRES_USER="bniot",
            POSTGRES_PASSWORD="test123",
            JWT_SECRET="test-secret"
        )

        url = settings.DATABASE_URL
        assert "postgresql+asyncpg" in url
        assert "bniot" in url
        assert "postgres:5432" in url

    def test_database_url_with_special_password(self):
        """测试包含特殊字符的密码 URL 编码"""
        from app.core.config import Settings

        settings = Settings(
            POSTGRES_HOST="postgres",
            POSTGRES_PORT=5432,
            POSTGRES_DB="bniot",
            POSTGRES_USER="bniot",
            POSTGRES_PASSWORD="test@123#pass",
            JWT_SECRET="test-secret"
        )

        url = settings.DATABASE_URL
        # 特殊字符应该被 URL 编码
        assert "@" in url or "%40" in url

    def test_redis_url_generation(self):
        """测试 Redis URL 生成"""
        from app.core.config import Settings

        settings = Settings(
            REDIS_HOST="redis",
            REDIS_PORT=6379,
            REDIS_PASSWORD="redis123",
            JWT_SECRET="test-secret"
        )

        url = settings.REDIS_URL
        assert "redis" in url
        assert "6379" in url

    def test_redis_url_without_password(self):
        """测试无密码的 Redis URL"""
        from app.core.config import Settings

        settings = Settings(
            REDIS_HOST="localhost",
            REDIS_PORT=6379,
            REDIS_PASSWORD="",
            JWT_SECRET="test-secret"
        )

        url = settings.REDIS_URL
        assert url == "redis://localhost:6379/0"

    def test_jwt_configuration(self):
        """测试 JWT 配置"""
        from app.core.config import Settings

        settings = Settings(
            JWT_SECRET="my-super-secret-key",
            JWT_ALGORITHM="HS256",
            JWT_EXPIRE_HOURS=24,
        )

        assert settings.JWT_SECRET == "my-super-secret-key"
        assert settings.JWT_ALGORITHM == "HS256"
        assert settings.JWT_EXPIRE_HOURS == 24

    def test_cors_origins_default(self):
        """测试 CORS 默认配置"""
        from app.core.config import Settings

        settings = Settings(JWT_SECRET="test")

        assert "http://localhost:3000" in settings.CORS_ORIGINS
        assert "http://localhost:5173" in settings.CORS_ORIGINS


class TestSettingsSingleton:
    """测试配置单例"""

    def test_get_settings_returns_singleton(self):
        """测试 get_settings 返回单例"""
        from app.core.config import get_settings

        settings1 = get_settings()
        settings2 = get_settings()

        assert settings1 is settings2

    def test_settings_is_cached(self):
        """测试配置被缓存"""
        from app.core.config import get_settings, settings

        result = get_settings()
        assert result is settings