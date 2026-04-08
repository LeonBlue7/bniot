"""
应用配置
"""
import os
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from functools import lru_cache
from urllib.parse import quote_plus


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
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]

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
        if os.getenv("ENV", "development") == "production":
            if self.JWT_SECRET == "dev-secret-key":
                raise ValueError("生产环境必须配置 JWT_SECRET 环境变量")


@lru_cache()
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()


settings = get_settings()