"""
任务服务模块
处理任务的业务逻辑
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, TaskExecutionError, ValidationError
from app.crud.task import task as task_crud
from app.crud.task import task_log as task_log_crud
from app.db.session import AsyncSessionLocal
from app.models.task import Task, TaskLog, TaskStatus, TaskType
from app.models.user import User
from app.schemas.task import TaskCreate, TaskLogCreate, TaskUpdate
from app.services.scheduler import scheduler
from app.utils.logger import get_logger

logger = get_logger("task_service")


class TaskService:
    """任务服务类"""

    @staticmethod
    async def create_task(
        db: AsyncSession,
        *,
        obj_in: TaskCreate,
        owner: User,
    ) -> Task:
        """
        创建任务

        Args:
            db: 数据库会话
            obj_in: 任务创建数据
            owner: 任务所有者

        Returns:
            创建的任务对象
        """
        # 验证定时任务的cron表达式
        if obj_in.task_type == TaskType.SCHEDULED and not obj_in.cron_expression:
            raise ValidationError("定时任务必须提供Cron表达式")

        # 创建任务
        task = await task_crud.create(db, obj_in=obj_in, owner_id=owner.id)

        # 如果是定时任务，添加到调度器
        if task.task_type == TaskType.SCHEDULED:
            scheduler.add_scheduled_task(
                task_id=task.id,
                func=TaskService._execute_scheduled_task,
                cron_expression=task.cron_expression,
                args=(task.id,),
            )

        logger.info(f"Task {task.id} created by user {owner.id}")
        return task

    @staticmethod
    async def get_task(
        db: AsyncSession,
        *,
        task_id: int,
        owner: Optional[User] = None,
    ) -> Task:
        """
        获取任务

        Args:
            db: 数据库会话
            task_id: 任务ID
            owner: 可选的所有者（用于权限检查）

        Returns:
            任务对象

        Raises:
            NotFoundError: 任务不存在
        """
        if owner:
            task = await task_crud.get_with_owner(
                db, task_id=task_id, owner_id=owner.id
            )
        else:
            task = await task_crud.get(db, id=task_id)

        if not task:
            raise NotFoundError(f"任务不存在: {task_id}")

        return task

    @staticmethod
    async def update_task(
        db: AsyncSession,
        *,
        task_id: int,
        obj_in: TaskUpdate,
        owner: User,
    ) -> Task:
        """
        更新任务

        Args:
            db: 数据库会话
            task_id: 任务ID
            obj_in: 更新数据
            owner: 任务所有者

        Returns:
            更新后的任务对象
        """
        task = await TaskService.get_task(db, task_id=task_id, owner=owner)

        # 如果任务正在运行，不允许更新
        if task.status == TaskStatus.RUNNING:
            raise ValidationError("任务正在执行中，无法更新")

        # 更新任务
        task = await task_crud.update(db, db_obj=task, obj_in=obj_in)

        # 如果更新了cron表达式，重新添加到调度器
        if obj_in.cron_expression and task.task_type == TaskType.SCHEDULED:
            scheduler.remove_scheduled_task(task.id)
            scheduler.add_scheduled_task(
                task_id=task.id,
                func=TaskService._execute_scheduled_task,
                cron_expression=task.cron_expression,
                args=(task.id,),
            )

        logger.info(f"Task {task_id} updated by user {owner.id}")
        return task

    @staticmethod
    async def delete_task(
        db: AsyncSession,
        *,
        task_id: int,
        owner: User,
    ) -> Task:
        """
        删除任务

        Args:
            db: 数据库会话
            task_id: 任务ID
            owner: 任务所有者

        Returns:
            删除的任务对象
        """
        task = await TaskService.get_task(db, task_id=task_id, owner=owner)

        # 如果任务正在运行，先取消
        if task.status == TaskStatus.RUNNING:
            scheduler.cancel_task(task.id)

        # 从调度器中移除
        if task.task_type == TaskType.SCHEDULED:
            scheduler.remove_scheduled_task(task.id)

        # 删除任务
        task = await task_crud.remove(db, id=task_id)

        logger.info(f"Task {task_id} deleted by user {owner.id}")
        return task

    @staticmethod
    async def list_tasks(
        db: AsyncSession,
        *,
        owner: Optional[User] = None,
        skip: int = 0,
        limit: int = 20,
        status: Optional[TaskStatus] = None,
        task_type: Optional[TaskType] = None,
        priority: Optional[Any] = None,
        keyword: Optional[str] = None,
    ) -> tuple[List[Task], int]:
        """
        获取任务列表

        Args:
            db: 数据库会话
            owner: 可选的所有者过滤
            skip: 跳过数量
            limit: 限制数量
            status: 状态过滤
            task_type: 类型过滤
            priority: 优先级过滤
            keyword: 关键词搜索

        Returns:
            (任务列表, 总数)
        """
        owner_id = owner.id if owner else None

        tasks = await task_crud.get_multi_with_filters(
            db,
            skip=skip,
            limit=limit,
            owner_id=owner_id,
            status=status,
            task_type=task_type,
            priority=priority,
            keyword=keyword,
        )

        total = await task_crud.count_with_filters(
            db,
            owner_id=owner_id,
            status=status,
            task_type=task_type,
            priority=priority,
            keyword=keyword,
        )

        return tasks, total

    @staticmethod
    async def execute_task(
        db: AsyncSession,
        *,
        task_id: int,
        owner: User,
        params: Optional[Dict[str, Any]] = None,
    ) -> Task:
        """
        执行任务

        Args:
            db: 数据库会话
            task_id: 任务ID
            owner: 任务所有者
            params: 执行参数

        Returns:
            执行后的任务对象
        """
        task = await TaskService.get_task(db, task_id=task_id, owner=owner)

        # 检查任务状态
        if task.status == TaskStatus.RUNNING:
            raise ValidationError("任务正在执行中")

        # 更新状态为运行中
        task = await task_crud.update_status(db, task=task, status=TaskStatus.RUNNING)

        # 记录开始日志
        await task_log_crud.create_for_task(
            db,
            task_id=task.id,
            level="INFO",
            message=f"任务开始执行",
            source="task_service",
        )

        try:
            # 执行实际的命令
            result = await TaskService._run_command(
                task=task,
                params=params or task.params,
            )

            # 更新任务状态为成功
            task = await task_crud.update_status(
                db,
                task=task,
                status=TaskStatus.SUCCESS,
                result=result,
                output=result.get("output"),
            )

            # 记录成功日志
            await task_log_crud.create_for_task(
                db,
                task_id=task.id,
                level="INFO",
                message="任务执行成功",
                source="task_service",
                meta=result,
            )

        except Exception as e:
            logger.error(f"Task {task_id} execution failed: {e}")

            # 检查是否可以重试
            if task.can_retry:
                await task_crud.increment_retry(db, task=task)
                task = await task_crud.update_status(
                    db,
                    task=task,
                    status=TaskStatus.PENDING,
                    error_message=str(e),
                )
                raise TaskExecutionError(
                    f"任务执行失败，将在重试后再次执行: {e}",
                    details={"retry_count": task.retry_count},
                )
            else:
                task = await task_crud.update_status(
                    db,
                    task=task,
                    status=TaskStatus.FAILED,
                    error_message=str(e),
                )

                # 记录失败日志
                await task_log_crud.create_for_task(
                    db,
                    task_id=task.id,
                    level="ERROR",
                    message=f"任务执行失败: {e}",
                    source="task_service",
                )

                raise TaskExecutionError(f"任务执行失败: {e}")

        return task

    @staticmethod
    async def _run_command(
        task: Task,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        运行任务命令

        Args:
            task: 任务对象
            params: 执行参数

        Returns:
            执行结果
        """
        import asyncio

        command = task.command or "echo 'No command specified'"

        # 简单的命令执行（实际项目中可能需要更复杂的实现）
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=task.timeout,
            )

            return {
                "returncode": process.returncode,
                "output": stdout.decode() if stdout else "",
                "error": stderr.decode() if stderr else "",
                "params": params,
            }
        except asyncio.TimeoutError:
            raise TaskExecutionError("任务执行超时")
        except Exception as e:
            raise TaskExecutionError(f"命令执行失败: {e}")

    @staticmethod
    async def _execute_scheduled_task(task_id: int):
        """
        执行定时任务（供调度器调用）

        Args:
            task_id: 任务ID
        """
        async with AsyncSessionLocal() as db:
            try:
                task = await task_crud.get(db, id=task_id)
                if not task or not task.owner:
                    logger.error(f"Scheduled task {task_id} not found")
                    return

                await TaskService.execute_task(
                    db, task_id=task_id, owner=task.owner
                )
            except Exception as e:
                logger.error(f"Failed to execute scheduled task {task_id}: {e}")

    @staticmethod
    async def cancel_task(
        db: AsyncSession,
        *,
        task_id: int,
        owner: User,
    ) -> Task:
        """
        取消任务

        Args:
            db: 数据库会话
            task_id: 任务ID
            owner: 任务所有者

        Returns:
            取消后的任务对象
        """
        task = await TaskService.get_task(db, task_id=task_id, owner=owner)

        if task.status != TaskStatus.RUNNING:
            raise ValidationError("任务未在执行中")

        # 取消正在执行的任务
        scheduler.cancel_task(task.id)

        # 更新状态为取消
        task = await task_crud.update_status(
            db, task=task, status=TaskStatus.CANCELLED
        )

        # 记录日志
        await task_log_crud.create_for_task(
            db,
            task_id=task.id,
            level="WARNING",
            message="任务被取消",
            source="task_service",
        )

        logger.info(f"Task {task_id} cancelled by user {owner.id}")
        return task

    @staticmethod
    async def get_task_logs(
        db: AsyncSession,
        *,
        task_id: int,
        owner: User,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[List[TaskLog], int]:
        """
        获取任务日志

        Args:
            db: 数据库会话
            task_id: 任务ID
            owner: 任务所有者
            skip: 跳过数量
            limit: 限制数量

        Returns:
            (日志列表, 总数)
        """
        # 先检查任务是否存在
        await TaskService.get_task(db, task_id=task_id, owner=owner)

        logs = await task_log_crud.get_multi_by_task(
            db, task_id=task_id, skip=skip, limit=limit
        )

        # 统计总数（简化实现）
        total = len(logs)  # 实际应该查询总数

        return logs, total

    @staticmethod
    async def get_statistics(
        db: AsyncSession,
        *,
        owner: Optional[User] = None,
    ) -> Dict[str, int]:
        """
        获取任务统计

        Args:
            db: 数据库会话
            owner: 可选的所有者过滤

        Returns:
            统计信息
        """
        return await task_crud.get_statistics(
            db, owner_id=owner.id if owner else None
        )


# 任务服务实例
task_service = TaskService()
