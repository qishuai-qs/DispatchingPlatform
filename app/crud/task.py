"""
任务CRUD模块
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.task import Task, TaskLog, TaskPriority, TaskStatus, TaskType
from app.schemas.task import TaskCreate, TaskLogCreate, TaskUpdate


class CRUDTask(CRUDBase[Task, TaskCreate, TaskUpdate]):
    """任务CRUD操作类"""

    async def get_with_owner(
        self, db: AsyncSession, *, task_id: int, owner_id: int
    ) -> Optional[Task]:
        """
        根据ID和所有者获取任务

        Args:
            db: 数据库会话
            task_id: 任务ID
            owner_id: 所有者ID

        Returns:
            任务对象或None
        """
        result = await db.execute(
            select(Task).where(Task.id == task_id, Task.owner_id == owner_id)
        )
        return result.scalar_one_or_none()

    async def get_multi_by_owner(
        self,
        db: AsyncSession,
        *,
        owner_id: int,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Task]:
        """
        获取用户的所有任务

        Args:
            db: 数据库会话
            owner_id: 所有者ID
            skip: 跳过数量
            limit: 限制数量

        Returns:
            任务列表
        """
        result = await db.execute(
            select(Task)
            .where(Task.owner_id == owner_id)
            .order_by(Task.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def create(
        self, db: AsyncSession, *, obj_in: Union[TaskCreate, Dict[str, Any]], owner_id: int
    ) -> Task:
        """
        创建任务

        Args:
            db: 数据库会话
            obj_in: 任务创建数据
            owner_id: 所有者ID

        Returns:
            创建的任务对象
        """
        if isinstance(obj_in, dict):
            obj_data = obj_in.copy()
        else:
            obj_data = obj_in.model_dump(exclude_unset=True)

        # 添加所有者ID
        obj_data["owner_id"] = owner_id
        obj_data["status"] = TaskStatus.PENDING
        obj_data["retry_count"] = 0

        db_obj = Task(**obj_data)
        db.add(db_obj)
        await db.flush()
        await db.refresh(db_obj)
        return db_obj

    async def update_status(
        self,
        db: AsyncSession,
        *,
        task: Task,
        status: TaskStatus,
        error_message: Optional[str] = None,
        result: Optional[Dict[str, Any]] = None,
        output: Optional[str] = None,
    ) -> Task:
        """
        更新任务状态

        Args:
            db: 数据库会话
            task: 任务对象
            status: 新状态
            error_message: 错误信息
            result: 执行结果
            output: 输出内容

        Returns:
            更新后的任务对象
        """
        task.status = status

        if status == TaskStatus.RUNNING and not task.started_at:
            task.started_at = datetime.now()

        if status in (TaskStatus.SUCCESS, TaskStatus.FAILED, TaskStatus.TIMEOUT, TaskStatus.CANCELLED):
            task.completed_at = datetime.now()

        if error_message:
            task.error_message = error_message

        if result:
            task.result = result

        if output:
            task.output = output

        db.add(task)
        await db.flush()
        await db.refresh(task)
        return task

    async def increment_retry(self, db: AsyncSession, *, task: Task) -> Task:
        """
        增加重试次数

        Args:
            db: 数据库会话
            task: 任务对象

        Returns:
            更新后的任务对象
        """
        task.retry_count += 1
        db.add(task)
        await db.flush()
        await db.refresh(task)
        return task

    async def get_multi_with_filters(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100,
        owner_id: Optional[int] = None,
        status: Optional[TaskStatus] = None,
        task_type: Optional[TaskType] = None,
        priority: Optional[TaskPriority] = None,
        keyword: Optional[str] = None,
    ) -> List[Task]:
        """
        带过滤条件的获取任务列表

        Args:
            db: 数据库会话
            skip: 跳过数量
            limit: 限制数量
            owner_id: 所有者ID过滤
            status: 状态过滤
            task_type: 类型过滤
            priority: 优先级过滤
            keyword: 关键词搜索

        Returns:
            任务列表
        """
        query = select(Task)

        if owner_id:
            query = query.where(Task.owner_id == owner_id)
        if status:
            query = query.where(Task.status == status)
        if task_type:
            query = query.where(Task.task_type == task_type)
        if priority:
            query = query.where(Task.priority == priority)
        if keyword:
            query = query.where(Task.name.ilike(f"%{keyword}%"))

        query = query.order_by(Task.created_at.desc()).offset(skip).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())

    async def count_with_filters(
        self,
        db: AsyncSession,
        *,
        owner_id: Optional[int] = None,
        status: Optional[TaskStatus] = None,
        task_type: Optional[TaskType] = None,
        priority: Optional[TaskPriority] = None,
        keyword: Optional[str] = None,
    ) -> int:
        """
        带过滤条件的统计任务数量

        Args:
            db: 数据库会话
            owner_id: 所有者ID过滤
            status: 状态过滤
            task_type: 类型过滤
            priority: 优先级过滤
            keyword: 关键词搜索

        Returns:
            任务数量
        """
        query = select(func.count(Task.id))

        if owner_id:
            query = query.where(Task.owner_id == owner_id)
        if status:
            query = query.where(Task.status == status)
        if task_type:
            query = query.where(Task.task_type == task_type)
        if priority:
            query = query.where(Task.priority == priority)
        if keyword:
            query = query.where(Task.name.ilike(f"%{keyword}%"))

        result = await db.execute(query)
        return result.scalar() or 0

    async def get_statistics(
        self,
        db: AsyncSession,
        *,
        owner_id: Optional[int] = None,
    ) -> Dict[str, int]:
        """
        获取任务统计信息

        Args:
            db: 数据库会话
            owner_id: 可选的所有者ID过滤

        Returns:
            各状态任务数量统计
        """
        query = select(Task.status, func.count(Task.id))

        if owner_id:
            query = query.where(Task.owner_id == owner_id)

        query = query.group_by(Task.status)
        result = await db.execute(query)

        stats = {status.value: 0 for status in TaskStatus}
        stats["total"] = 0

        for status, count in result.all():
            stats[status.value] = count
            stats["total"] += count

        return stats


class CRUDTaskLog(CRUDBase[TaskLog, TaskLogCreate, TaskLogCreate]):
    """任务日志CRUD操作类"""

    async def get_multi_by_task(
        self,
        db: AsyncSession,
        *,
        task_id: int,
        skip: int = 0,
        limit: int = 100,
    ) -> List[TaskLog]:
        """
        获取任务的所有日志

        Args:
            db: 数据库会话
            task_id: 任务ID
            skip: 跳过数量
            limit: 限制数量

        Returns:
            日志列表
        """
        result = await db.execute(
            select(TaskLog)
            .where(TaskLog.task_id == task_id)
            .order_by(TaskLog.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def create_for_task(
        self,
        db: AsyncSession,
        *,
        task_id: int,
        level: str,
        message: str,
        source: Optional[str] = None,
        meta: Optional[Dict[str, Any]] = None,
    ) -> TaskLog:
        """
        为任务创建日志

        Args:
            db: 数据库会话
            task_id: 任务ID
            level: 日志级别
            message: 日志内容
            source: 日志来源
            meta: 元数据

        Returns:
            创建的日志对象
        """
        db_obj = TaskLog(
            task_id=task_id,
            level=level,
            message=message,
            source=source,
            meta=meta,
        )
        db.add(db_obj)
        await db.flush()
        await db.refresh(db_obj)
        return db_obj


# CRUD实例
task = CRUDTask(Task)
task_log = CRUDTaskLog(TaskLog)
