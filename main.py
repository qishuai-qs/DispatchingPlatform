"""
应用入口文件
启动FastAPI应用
"""

from contextlib import asynccontextmanager
from datetime import datetime

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.api import api_router
from app.core.config import settings
from app.core.exceptions import (
    AppException,
    app_exception_handler,
    general_exception_handler,
    http_exception_handler,
)
from app.db.session import close_db, init_db
from app.services.scheduler import scheduler
from app.utils.logger import get_logger

logger = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理

    启动时初始化数据库和调度器
    关闭时清理资源
    """
    # 启动
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Environment: {settings.env}")

    # 初始化数据库
    await init_db()
    logger.info("Database initialized")

    # 启动调度器
    scheduler.start()
    logger.info("Scheduler started")

    yield

    # 关闭
    logger.info("Shutting down application")

    # 关闭调度器
    scheduler.shutdown()
    logger.info("Scheduler stopped")

    # 关闭数据库
    await close_db()
    logger.info("Database connection closed")


def create_application() -> FastAPI:
    """
    创建FastAPI应用实例

    Returns:
        FastAPI应用实例
    """
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="全自动平台服务 - 任务调度、用户管理、配置中心",
        docs_url="/docs" if settings.is_development else None,
        redoc_url="/redoc" if settings.is_development else None,
        openapi_url="/openapi.json" if settings.is_development else None,
        lifespan=lifespan,
    )

    # 配置CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 注册异常处理器
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)

    # 注册路由
    app.include_router(api_router)

    return app


# 创建应用实例
app = create_application()


@app.get("/", tags=["根路径"])
async def root():
    """
    根路径 - 返回应用基本信息
    """
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "environment": settings.env,
        "docs_url": "/docs",
        "api_prefix": "/api/v1",
    }


@app.get("/health", tags=["健康检查"])
async def health():
    """
    健康检查端点
    """
    from app.schemas.common import HealthStatus

    return HealthStatus(
        status="healthy",
        version=settings.app_version,
        timestamp=datetime.now().isoformat(),
        checks={
            "app": "ok",
            "timestamp": datetime.now().isoformat(),
        },
    )


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log.level.lower(),
    )
