"""
应用配置
"""
import os
import warnings
from functools import lru_cache
from urllib.parse import quote_plus

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# 不安全的默认密钥列表
INSECURE_DEFAULT_SECRETS = [
    "dev-secret-key",
    "secret",
    "password",
    "changeme",
    "123456",
    "jwt-secret",
    "test",
    "admin",
    "default",
    "development",
    "debug",
    "example",
]


def is_insecure_secret(secret: str) -> bool:
    """检测是否使用了不安全的密钥"""
    # 检查是否在已知的不安全密钥列表中
    if secret.lower() in INSECURE_DEFAULT_SECRETS:
        return True
    # 检查是否太短（小于 16 字符）
    if len(secret) < 16:
        return True
    return False


class Settings(BaseSettings):
    """应用配置"""

    # 应用配置
    APP_NAME: str = "BNIoT"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # 数据库配置
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "bniot"
    POSTGRES_USER: str = "bniot"
    POSTGRES_PASSWORD: str = ""

    @property
    def DATABASE_URL(self) -> str:
        password = quote_plus(self.POSTGRES_PASSWORD)
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{password}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    @property
    def DATABASE_URL_SYNC(self) -> str:
        password = quote_plus(self.POSTGRES_PASSWORD)
        return f"postgresql://{self.POSTGRES_USER}:{password}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    # Redis 配置
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""
    REDIS_DB: int = 0

    @property
    def REDIS_URL(self) -> str:
        if self.REDIS_PASSWORD:
            password = quote_plus(self.REDIS_PASSWORD)
            return f"redis://:{password}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    # EMQX 配置
    EMQX_HOST: str = "localhost"
    EMQX_MQTT_PORT: int = 1883
    MQTT_USERNAME: str = "test1"
    MQTT_PASSWORD: str = "test123"

    # JWT 配置 - 生产环境必须配置
    JWT_SECRET: str = Field(default="dev-secret-key", description="JWT密钥，生产环境必须配置")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_HOURS: int = 24

    # CORS 配置
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    # 小程序配置
    WECHAT_APPID: str = ""
    WECHAT_SECRET: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 生产环境验证
        env = os.getenv("ENV", "development")
        if env == "production":
            # JWT 密钥验证
            if self.JWT_SECRET == "dev-secret-key":
                raise ValueError("生产环境必须配置 JWT_SECRET 环境变量")
            if is_insecure_secret(self.JWT_SECRET):
                raise ValueError(
                    f"生产环境使用了不安全的 JWT_SECRET: '{self.JWT_SECRET}'。"
                    "请使用至少 16 个字符的随机密钥。"
                )

            # 数据库密码验证
            if not self.POSTGRES_PASSWORD:
                raise ValueError("生产环境必须配置 POSTGRES_PASSWORD 环境变量")
            if len(self.POSTGRES_PASSWORD) < 16:
                raise ValueError(
                    "生产环境 POSTGRES_PASSWORD 至少需要 16 个字符"
                )

            # Redis 密码验证
            if not self.REDIS_PASSWORD:
                raise ValueError("生产环境必须配置 REDIS_PASSWORD 环境变量")
            if len(self.REDIS_PASSWORD) < 16:
                raise ValueError(
                    "生产环境 REDIS_PASSWORD 至少需要 16 个字符"
                )

            # MQTT 凭证验证（设备端硬编码，但平台端需要确认环境配置正确）
            if self.MQTT_USERNAME == "test1" and self.MQTT_PASSWORD == "test123":
                # 这是设备端硬编码的凭证，生产环境需要确认已配置 EMQX
                warnings.warn(
                    "生产环境使用默认 MQTT 凭证。请确认 EMQX 已正确配置设备认证。",
                    UserWarning,
                    stacklevel=2
                )


@lru_cache
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()


settings = get_settings()
