"""
API集成测试
"""

import pytest
from httpx import AsyncClient

from tests.conftest import assert_response


@pytest.mark.asyncio
async def test_root_endpoint(client: AsyncClient):
    """测试根路径"""
    response = await client.get("/")
    assert_response(response, 200)
    data = response.json()
    assert "name" in data
    assert "version" in data


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """测试健康检查端点"""
    response = await client.get("/health")
    assert_response(response, 200)
    data = response.json()
    assert data["data"]["status"] == "healthy"
    assert "version" in data["data"]


@pytest.mark.asyncio
async def test_system_info(client: AsyncClient, auth_headers: dict):
    """测试系统信息API"""
    response = await client.get(
        "/api/v1/system/info",
        headers=auth_headers,
    )
    assert_response(response, 200)
    data = response.json()
    assert data["success"] is True
    assert "app_name" in data["data"]


@pytest.mark.asyncio
async def test_system_config(client: AsyncClient, auth_headers: dict):
    """测试系统配置API"""
    response = await client.get(
        "/api/v1/system/config",
        headers=auth_headers,
    )
    assert_response(response, 200)
    data = response.json()
    assert data["success"] is True
    assert "scheduler_enabled" in data["data"]


@pytest.mark.asyncio
async def test_system_health(client: AsyncClient, auth_headers: dict):
    """测试系统健康检查API"""
    response = await client.get(
        "/api/v1/system/health",
        headers=auth_headers,
    )
    assert_response(response, 200)
    data = response.json()
    assert data["success"] is True
    assert data["data"]["status"] in ["healthy", "degraded"]


@pytest.mark.asyncio
async def test_unauthorized_access(client: AsyncClient):
    """测试未授权访问"""
    response = await client.get("/api/v1/users/me")
    assert_response(response, 401)
    data = response.json()
    assert data["success"] is False


@pytest.mark.asyncio
async def test_get_current_user(client: AsyncClient, auth_headers: dict, test_user):
    """测试获取当前用户信息"""
    response = await client.get(
        "/api/v1/users/me",
        headers=auth_headers,
    )
    assert_response(response, 200)
    data = response.json()
    assert data["success"] is True
    assert data["data"]["username"] == test_user.username
    assert data["data"]["email"] == test_user.email


@pytest.mark.asyncio
async def test_update_current_user(client: AsyncClient, auth_headers: dict, test_user):
    """测试更新当前用户信息"""
    response = await client.put(
        "/api/v1/users/me",
        headers=auth_headers,
        json={
            "full_name": "Updated Name",
            "email": "updated@example.com",
        },
    )
    assert_response(response, 200)
    data = response.json()
    assert data["success"] is True
    assert data["data"]["full_name"] == "Updated Name"
    assert data["data"]["email"] == "updated@example.com"


@pytest.mark.asyncio
async def test_create_task(client: AsyncClient, auth_headers: dict):
    """测试创建任务"""
    response = await client.post(
        "/api/v1/tasks",
        headers=auth_headers,
        json={
            "name": "Test Task",
            "description": "This is a test task",
            "task_type": "one_time",
            "priority": "medium",
            "command": "echo 'Hello World'",
            "timeout": 3600,
        },
    )
    assert_response(response, 201)
    data = response.json()
    assert data["success"] is True
    assert data["data"]["name"] == "Test Task"
    assert data["data"]["status"] == "pending"


@pytest.mark.asyncio
async def test_list_tasks(client: AsyncClient, auth_headers: dict):
    """测试获取任务列表"""
    response = await client.get(
        "/api/v1/tasks",
        headers=auth_headers,
    )
    assert_response(response, 200)
    data = response.json()
    assert data["success"] is True
    assert "items" in data["data"]
    assert "pagination" in data["data"]


@pytest.mark.asyncio
async def test_get_task_statistics(client: AsyncClient, auth_headers: dict):
    """测试获取任务统计"""
    response = await client.get(
        "/api/v1/tasks/statistics",
        headers=auth_headers,
    )
    assert_response(response, 200)
    data = response.json()
    assert data["success"] is True
    assert "total" in data["data"]
