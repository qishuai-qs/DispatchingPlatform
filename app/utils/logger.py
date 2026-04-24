"""
日志工具模块
使用loguru进行日志管理
"""

import sys
from pathlib import Path

from loguru import logger

from app.core.config import settings

# 移除默认的日志处理器
logger.remove()

# 添加控制台日志
logger.add(
    sys.stdout,
    level=settings.log.level,
    format=settings.log.format,
    colorize=True,
    backtrace=True,
    diagnose=True,
)

# 添加文件日志
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

logger.add(
    log_dir / "app.log",
    level=settings.log.level,
    format=settings.log.format,
    rotation=settings.log.rotation,
    retention=settings.log.retention,
    encoding="utf-8",
    backtrace=True,
    diagnose=True,
)

logger.add(
    log_dir / "error.log",
    level="ERROR",
    format=settings.log.format,
    rotation=settings.log.rotation,
    retention=settings.log.retention,
    encoding="utf-8",
    backtrace=True,
    diagnose=True,
)


class LoggerMixin:
    """日志混入类，为类提供日志功能"""

    @property
    def logger(self):
        """获取logger实例"""
        return logger.bind(name=self.__class__.__name__)


def get_logger(name: str = None):
    """
    获取带名称绑定的logger

    Args:
        name: 日志名称

    Returns:
        logger实例
    """
    if name:
        return logger.bind(name=name)
    return logger
