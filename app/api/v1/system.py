"""
系统API路由
处理健康检查、系统信息等
"""

from datetime import datetime

from fastapi import APIRouter

from app.core.config import settings
from app.schemas.common import HealthStatus, ResponseModel, SystemInfo

router = APIRouter(prefix="/system", tags=["系统"])

# 启动时间
_start_time: datetime = datetime.now()


@router.get(
    "/info",
    response_model=ResponseModel[SystemInfo],
    summary="获取系统信息",
)
async def get_system_info():
    """
    获取系统运行信息
    """
    import platform
    import sys

    uptime = datetime.now() - _start_time
    uptime_str = str(uptime).split(".")[0]  # 去掉微秒

    info = SystemInfo(
        app_name=settings.app_name,
        version=settings.app_version,
        environment=settings.env,
        python_version=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        uptime=uptime_str,
    )

    return ResponseModel(
        data=info,
        message="查询成功",
    )


@router.get(
    "/health",
    response_model=ResponseModel[HealthStatus],
    summary="健康检查",
)
async def health_check():
    """
    系统健康状态检查
    """
    checks = {
        "database": "ok",
        "scheduler": "ok" if settings.scheduler.enabled else "disabled",
    }

    all_ok = all(v in ("ok", "disabled") for v in checks.values())
    status = "healthy" if all_ok else "degraded"

    health = HealthStatus(
        status=status,
        version=settings.app_version,
        timestamp=datetime.now().isoformat(),
        checks=checks,
    )

    return ResponseModel(
        data=health,
        message="服务运行正常" if status == "healthy" else "服务状态异常",
    )


@router.get(
    "/config",
    response_model=ResponseModel[dict],
    summary="获取配置信息",
)
async def get_config():
    """
    获取应用配置（仅返回非敏感信息）
    """
    safe_config = {
        "app_name": settings.app_name,
        "app_version": settings.app_version,
        "debug": settings.debug,
        "env": settings.env,
        "scheduler_enabled": settings.scheduler.enabled,
        "scheduler_timezone": settings.scheduler.timezone,
    }

    return ResponseModel(
        data=safe_config,
        message="查询成功",
    )
