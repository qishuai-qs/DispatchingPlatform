"""
测试配置和夹具
"""

import asyncio
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.api.api import api_router
from app.core.config import settings
from app.core.security import create_access_token
from app.db.session import get_db
from app.models import Base
from app.models.user import User, UserRole, UserStatus

# 使用内存数据库进行测试
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# 创建测试引擎
engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


# 使用 pytest-asyncio 默认的事件循环 fixture
# 不再自定义，避免与新版 pytest-asyncio 冲突


@pytest_asyncio.fixture(scope="session")
async def test_db_setup() -> None:
    """设置测试数据库"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session(test_db_setup) -> AsyncGenerator[AsyncSession, None]:
    """创建数据库会话"""
    async with TestingSessionLocal() as session:
        yield session
        await session.rollback()


@pytest.fixture
def app(db_session: AsyncSession) -> FastAPI:
    """创建测试应用"""
    from main import create_application

    test_app = create_application()

    # 重写依赖
    async def override_get_db():
        yield db_session

    test_app.dependency_overrides[get_db] = override_get_db

    return test_app


@pytest_asyncio.fixture
async def client(app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """创建测试客户端"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> User:
    """创建测试用户"""
    from app.core.security import get_password_hash

    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=get_password_hash("Test1234!"),
        full_name="Test User",
        role=UserRole.USER,
        status=UserStatus.ACTIVE,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def admin_user(db_session: AsyncSession) -> User:
    """创建管理员测试用户"""
    from app.core.security import get_password_hash

    user = User(
        username="adminuser",
        email="admin@example.com",
        hashed_password=get_password_hash("Admin1234!"),
        full_name="Admin User",
        role=UserRole.ADMIN,
        status=UserStatus.ACTIVE,
        is_active=True,
        is_superuser=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
def user_token(test_user: User) -> str:
    """生成普通用户Token"""
    return create_access_token(subject=str(test_user.id))


@pytest.fixture
def admin_token(admin_user: User) -> str:
    """生成管理员Token"""
    return create_access_token(subject=str(admin_user.id))


@pytest.fixture
def auth_headers(user_token: str) -> dict:
    """认证请求头"""
    return {"Authorization": f"Bearer {user_token}"}


@pytest.fixture
def admin_auth_headers(admin_token: str) -> dict:
    """管理员认证请求头"""
    return {"Authorization": f"Bearer {admin_token}"}
