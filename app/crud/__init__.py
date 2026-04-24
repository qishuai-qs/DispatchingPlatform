"""
CRUD模块
导出所有CRUD操作类
"""

from app.crud.task import task, task_log
from app.crud.user import user

__all__ = ["user", "task", "task_log"]
