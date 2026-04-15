"""
启动初始化服务
确保默认租户和管理员用户存在
"""
import asyncio
import os

from loguru import logger
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_maker
from app.models import Tenant, User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def ensure_default_tenant(db: AsyncSession) -> Tenant:
    """确保默认租户存在"""
    result = await db.execute(select(Tenant).where(Tenant.code == "default"))
    tenant = result.scalar_one_or_none()

    if tenant:
        logger.info(f"默认租户已存在: {tenant.name} (ID: {tenant.id})")
        return tenant

    # 创建默认租户
    tenant = Tenant(
        name="默认租户",
        code="default",
        settings={"timezone": "Asia/Shanghai"}
    )
    db.add(tenant)
    await db.commit()
    await db.refresh(tenant)
    logger.info(f"创建默认租户成功: {tenant.name} (ID: {tenant.id})")
    return tenant


async def ensure_admin_user(db: AsyncSession, tenant_id: int) -> User:
    """确保管理员用户存在"""
    result = await db.execute(select(User).where(User.username == "admin"))
    user = result.scalar_one_or_none()

    if user:
        logger.info(f"管理员用户已存在: {user.username} (ID: {user.id})")
        return user

    # 获取密码（优先从环境变量，否则使用默认密码）
    default_password = os.getenv("DEFAULT_ADMIN_PASSWORD", "admin123")

    # 创建管理员用户
    password_hash = pwd_context.hash(default_password)
    user = User(
        tenant_id=tenant_id,
        username="admin",
        password_hash=password_hash,
        role="admin",
        is_active=True
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    logger.info(f"创建管理员用户成功: {user.username} (密码: {default_password})")
    logger.warning("⚠️  请在生产环境修改默认密码！")
    return user


async def init_default_data():
    """初始化默认数据"""
    logger.info("检查默认数据...")

    async with async_session_maker() as db:
        # 确保默认租户
        tenant = await ensure_default_tenant(db)

        # 确保管理员用户
        await ensure_admin_user(db, tenant.id)

    logger.info("默认数据检查完成")


def run_init():
    """运行初始化（同步版本，用于 lifespan）"""
    asyncio.run(init_default_data())