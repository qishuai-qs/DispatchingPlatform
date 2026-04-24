"""
任务调度服务模块
管理定时任务的调度和执行
"""

import asyncio
from datetime import datetime
from typing import Any, Callable, Dict, Optional

from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.config import settings
from app.models.task import Task, TaskStatus
from app.utils.logger import get_logger

logger = get_logger("scheduler")


class TaskScheduler:
    """任务调度器"""

    def __init__(self):
        self.scheduler = AsyncIOScheduler(
            timezone=settings.scheduler.timezone,
            job_defaults={"max_instances": settings.scheduler.max_workers},
        )
        self._running_tasks: Dict[int, asyncio.Task] = {}
        self._setup_listeners()

    def _setup_listeners(self):
        """设置事件监听器"""
        self.scheduler.add_listener(
            self._on_job_executed, EVENT_JOB_EXECUTED
        )
        self.scheduler.add_listener(
            self._on_job_error, EVENT_JOB_ERROR
        )

    def _on_job_executed(self, event):
        """任务执行完成回调"""
        logger.info(f"Job {event.job_id} executed successfully")

    def _on_job_error(self, event):
        """任务执行错误回调"""
        logger.error(f"Job {event.job_id} failed: {event.exception}")

    def start(self):
        """启动调度器"""
        if settings.scheduler.enabled and not self.scheduler.running:
            self.scheduler.start()
            logger.info("Task scheduler started")

    def shutdown(self):
        """关闭调度器"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Task scheduler shutdown")

    def add_scheduled_task(
        self,
        task_id: int,
        func: Callable,
        cron_expression: str,
        args: Optional[tuple] = None,
        kwargs: Optional[dict] = None,
    ) -> bool:
        """
        添加定时任务

        Args:
            task_id: 任务ID
            func: 执行函数
            cron_expression: Cron表达式
            args: 位置参数
            kwargs: 关键字参数

        Returns:
            是否添加成功
        """
        try:
            trigger = CronTrigger.from_crontab(cron_expression)
            self.scheduler.add_job(
                func=func,
                trigger=trigger,
                args=args or (),
                kwargs=kwargs or {},
                id=str(task_id),
                replace_existing=True,
            )
            logger.info(f"Scheduled task {task_id} with cron: {cron_expression}")
            return True
        except Exception as e:
            logger.error(f"Failed to add scheduled task {task_id}: {e}")
            return False

    def remove_scheduled_task(self, task_id: int) -> bool:
        """
        移除定时任务

        Args:
            task_id: 任务ID

        Returns:
            是否移除成功
        """
        try:
            self.scheduler.remove_job(str(task_id))
            logger.info(f"Removed scheduled task {task_id}")
            return True
        except Exception as e:
            logger.warning(f"Failed to remove scheduled task {task_id}: {e}")
            return False

    def pause_scheduled_task(self, task_id: int) -> bool:
        """
        暂停定时任务

        Args:
            task_id: 任务ID

        Returns:
            是否暂停成功
        """
        try:
            self.scheduler.pause_job(str(task_id))
            return True
        except Exception as e:
            logger.warning(f"Failed to pause scheduled task {task_id}: {e}")
            return False

    def resume_scheduled_task(self, task_id: int) -> bool:
        """
        恢复定时任务

        Args:
            task_id: 任务ID

        Returns:
            是否恢复成功
        """
        try:
            self.scheduler.resume_job(str(task_id))
            return True
        except Exception as e:
            logger.warning(f"Failed to resume scheduled task {task_id}: {e}")
            return False

    async def execute_task(
        self,
        task: Task,
        execute_func: Callable,
        *args,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        执行任务

        Args:
            task: 任务对象
            execute_func: 执行函数
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            执行结果
        """
        task_id = task.id

        # 检查是否已在运行
        if task_id in self._running_tasks:
            return {
                "success": False,
                "error": "Task is already running",
            }

        # 创建异步任务
        async def _run():
            try:
                result = await execute_func(*args, **kwargs)
                return {"success": True, "result": result}
            except Exception as e:
                logger.error(f"Task {task_id} execution failed: {e}")
                return {"success": False, "error": str(e)}
            finally:
                if task_id in self._running_tasks:
                    del self._running_tasks[task_id]

        # 启动任务
        task_coroutine = asyncio.create_task(_run())
        self._running_tasks[task_id] = task_coroutine

        # 等待完成（带超时）
        try:
            result = await asyncio.wait_for(
                task_coroutine, timeout=task.timeout or 3600
            )
            return result
        except asyncio.TimeoutError:
            # 取消任务
            task_coroutine.cancel()
            if task_id in self._running_tasks:
                del self._running_tasks[task_id]
            return {"success": False, "error": "Task execution timeout"}

    def cancel_task(self, task_id: int) -> bool:
        """
        取消正在执行的任务

        Args:
            task_id: 任务ID

        Returns:
            是否取消成功
        """
        if task_id in self._running_tasks:
            self._running_tasks[task_id].cancel()
            del self._running_tasks[task_id]
            logger.info(f"Cancelled task {task_id}")
            return True
        return False

    def get_running_tasks(self) -> list:
        """
        获取正在运行的任务列表

        Returns:
            正在运行的任务ID列表
        """
        return list(self._running_tasks.keys())


# 全局调度器实例
scheduler = TaskScheduler()
