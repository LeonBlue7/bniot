"""测试配置"""
import pytest
import asyncio
from typing import Generator
from sqlalchemy import create_engine, JSON
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

# 测试数据库 URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
TEST_DATABASE_URL_SYNC = "sqlite:///:memory:"


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
    from sqlalchemy.dialects.postgresql import JSONB

    # 将 JSONB 替换为 JSON 以支持 SQLite
    JSONB.__visit_name__ = "JSON"

    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    # 创建表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        yield session


@pytest.fixture
def db_session_sync():
    """创建测试数据库会话（同步）"""
    from app.models.models import Base
    from sqlalchemy.dialects.postgresql import JSONB

    # 将 JSONB 替换为 JSON 以支持 SQLite
    # 通过临时替换类型编译器的方式
    original_process = JSONB._compiler_dispatch

    def json_dispatch(self, compiler, **kw):
        return compiler.process(JSON(), **kw)

    JSONB._compiler_dispatch = json_dispatch

    engine = create_engine(TEST_DATABASE_URL_SYNC, echo=False)
    SessionLocal = sessionmaker(bind=engine)

    # 创建表
    Base.metadata.create_all(bind=engine)

    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        # 恢复原方法
        JSONB._compiler_dispatch = original_process