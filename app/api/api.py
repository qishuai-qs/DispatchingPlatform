"""
API路由聚合模块
"""

from fastapi import APIRouter

from app.api.v1 import auth, system, tasks, users

# 创建v1版本路由
api_router = APIRouter(prefix="/api/v1")

# 注册各模块路由
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(tasks.router)
api_router.include_router(system.router)

