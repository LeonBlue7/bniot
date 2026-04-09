"""
Alembic 环境配置
支持异步 SQLAlchemy 和多租户模型
"""
import asyncio
import os
from logging.config import fileConfig
from urllib.parse import quote_plus

from sqlalchemy import pool, create_engine
from sqlalchemy.engine import Connection

from alembic import context

# 导入项目配置和模型
import sys
sys.path.insert(0, '/app')

from app.core.config import settings
from app.models.models import Base

# this is the Alembic Config object
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 添加模型的 MetaData 对象以支持 autogenerate
target_metadata = Base.metadata

# 构建数据库 URL
DB_URL = f"postgresql://{settings.POSTGRES_USER}:{quote_plus(settings.POSTGRES_PASSWORD)}@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    context.configure(
        url=DB_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    # 使用同步引擎进行迁移
    connectable = create_engine(DB_URL, poolclass=pool.NullPool)
    
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
