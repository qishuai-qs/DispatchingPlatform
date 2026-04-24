"""
认证模块测试
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


@pytest.mark.asyncio
async def test_register(client: AsyncClient, db_session: AsyncSession):
    """测试用户注册"""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "Test1234!",
            "full_name": "New User",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["data"]["username"] == "newuser"
    assert data["data"]["email"] == "newuser@example.com"


@pytest.mark.asyncio
async def test_register_duplicate_username(
    client: AsyncClient, test_user: User
):
    """测试重复用户名注册"""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "username": test_user.username,
            "email": "another@example.com",
            "password": "Test1234!",
        },
    )
    assert response.status_code == 409
    data = response.json()
    assert data["success"] is False


@pytest.mark.asyncio
async def test_register_duplicate_email(
    client: AsyncClient, test_user: User
):
    """测试重复邮箱注册"""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "username": "anotheruser",
            "email": test_user.email,
            "password": "Test1234!",
        },
    )
    assert response.status_code == 409
    data = response.json()
    assert data["success"] is False


@pytest.mark.asyncio
async def test_login(client: AsyncClient, test_user: User):
    """测试用户登录"""
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "username": test_user.username,
            "password": "Test1234!",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "access_token" in data["data"]
    assert "refresh_token" in data["data"]
    assert data["data"]["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_with_email(client: AsyncClient, test_user: User):
    """测试使用邮箱登录"""
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "username": test_user.email,
            "password": "Test1234!",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient, test_user: User):
    """测试错误密码登录"""
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "username": test_user.username,
            "password": "WrongPassword123!",
        },
    )
    assert response.status_code == 401
    data = response.json()
    assert data["success"] is False


@pytest.mark.asyncio
async def test_login_nonexistent_user(client: AsyncClient):
    """测试不存在的用户登录"""
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "username": "nonexistent",
            "password": "Test1234!",
        },
    )
    assert response.status_code == 401
    data = response.json()
    assert data["success"] is False
