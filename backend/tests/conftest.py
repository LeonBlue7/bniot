"""
测试配置
修复 JSONB 类型问题，支持 SQLite 测试数据库
"""
import asyncio
import json
from typing import Generator, AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

import pytest
import redis.asyncio as redis
from sqlalchemy import create_engine, JSON
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

# 测试数据库 URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
TEST_DATABASE_URL_SYNC = "sqlite:///:memory:"


class JSONBForSQLite(JSON):
    """JSONB 的 SQLite 替代类型"""
    pass


@pytest.fixture(scope="session", autouse=True)
def patch_jsonb():
    """在测试会话开始时替换 JSONB 类型"""
    from sqlalchemy.dialects.postgresql import JSONB
    from app.models.models import Base

    # 保存原始的 JSONB 类型
    original_types = {}

    # 遍历所有模型，将 JSONB 列替换为 JSON
    for table in Base.metadata.tables.values():
        for column in table.columns:
            if hasattr(column.type, '__class__') and column.type.__class__.__name__ == 'JSONB':
                original_types[column] = column.type
                column.type = JSON()

    yield

    # 恢复原始类型
    for column, original_type in original_types.items():
        column.type = original_type


@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def db_session() -> AsyncSession:
    """创建测试数据库会话（异步）"""
    from app.models.models import Base

    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async_session_maker = async_sessionmaker(engine, expire_on_commit=False)

    # 创建表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_maker() as session:
        yield session

    # 清理
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
def db_session_sync():
    """创建测试数据库会话（同步）"""
    from app.models.models import Base

    engine = create_engine(TEST_DATABASE_URL_SYNC, echo=False)
    SessionLocal = sessionmaker(bind=engine)

    # 创建表
    Base.metadata.create_all(bind=engine)

    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def override_get_db(db_session: AsyncSession):
    """覆盖 get_db dependency"""
    from app.core.database import get_db
    from fastapi import FastAPI

    async def _get_db_override():
        yield db_session

    return _get_db_override


@pytest.fixture
def mock_redis():
    """创建模拟 Redis 客户端"""
    mock = AsyncMock(spec=redis.Redis)
    mock.get = AsyncMock(return_value=None)
    mock.set = AsyncMock(return_value=True)
    mock.delete = AsyncMock(return_value=1)
    mock.expire = AsyncMock(return_value=True)
    mock.close = AsyncMock()
    return mock


@pytest.fixture
def test_app_with_redis(override_get_db, mock_redis):
    """创建带 Redis 的测试应用"""
    from app.main import app
    from app.core.database import get_db

    app.dependency_overrides[get_db] = override_get_db
    # 设置 Redis 客户端到应用状态
    app.state.redis_client = mock_redis

    yield app

    app.dependency_overrides.clear()
    # 清理应用状态
    if hasattr(app.state, 'redis_client'):
        delattr(app.state, 'redis_client')


@pytest.fixture
def test_app(override_get_db):
    """创建测试应用"""
    from app.main import app
    from app.core.database import get_db

    app.dependency_overrides[get_db] = override_get_db
    yield app
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db_session_sync):
    """创建测试用户"""
    from app.models import Tenant, User

    tenant = Tenant(name="测试租户", code="test_reports")
    db_session_sync.add(tenant)
    db_session_sync.commit()

    user = User(
        tenant_id=tenant.id,
        username="testuser_reports",
        password_hash="hashed_password",
        role="admin"
    )
    db_session_sync.add(user)
    db_session_sync.commit()

    return user


@pytest.fixture
def test_token(test_user):
    """生成测试 JWT token"""
    from app.services.auth import create_access_token

    token = create_access_token(
        data={"sub": test_user.username, "tenant_id": test_user.tenant_id}
    )
    return token