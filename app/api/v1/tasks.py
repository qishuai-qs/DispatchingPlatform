"""
任务API路由
处理任务的CRUD和执行操作
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_active_user, get_db_session
from app.models.task import TaskPriority, TaskStatus, TaskType
from app.models.user import User
from app.schemas.common import PaginatedResponse, ResponseModel
from app.schemas.task import (
    TaskCreate,
    TaskExecuteRequest,
    TaskExecuteResponse,
    TaskFilter,
    TaskListResponse,
    TaskResponse,
    TaskStatistics,
    TaskSummary,
    TaskUpdate,
)
from app.services.task_service import task_service
from app.utils.response import build_paginated_data

router = APIRouter(prefix="/tasks", tags=["任务"])


@router.get(
    "",
    response_model=ResponseModel[PaginatedResponse[TaskSummary]],
    summary="获取任务列表",
)
async def list_tasks(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    status: Optional[TaskStatus] = Query(None, description="状态过滤"),
    task_type: Optional[TaskType] = Query(None, description="类型过滤"),
    priority: Optional[TaskPriority] = Query(None, description="优先级过滤"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
):
    """
    获取当前用户的任务列表
    """
    skip = (page - 1) * page_size

    tasks, total = await task_service.list_tasks(
        db=db,
        owner=current_user,
        skip=skip,
        limit=page_size,
        status=status,
        task_type=task_type,
        priority=priority,
        keyword=keyword,
    )

    task_summaries = [TaskSummary.model_validate(task) for task in tasks]

    return ResponseModel(
        data=build_paginated_data(
            items=task_summaries,
            total=total,
            page=page,
            page_size=page_size,
        ),
        message="查询成功",
    )


@router.post(
    "",
    response_model=ResponseModel[TaskResponse],
    status_code=status.HTTP_201_CREATED,
    summary="创建任务",
)
async def create_task(
    task_in: TaskCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
):
    """
    创建新任务
    - **name**: 任务名称
    - **description**: 任务描述
    - **task_type**: 任务类型 (one_time/scheduled/recurring/workflow)
    - **priority**: 优先级 (low/medium/high/critical)
    - **command**: 执行命令或脚本
    - **params**: 任务参数（JSON格式）
    - **cron_expression**: Cron表达式（定时任务需要）
    - **timeout**: 超时时间（秒）
    - **max_retries**: 最大重试次数
    - **scheduled_at**: 计划执行时间
    """
    task = await task_service.create_task(
        db=db,
        obj_in=task_in,
        owner=current_user,
    )
    return ResponseModel(
        data=TaskResponse.model_validate(task),
        message="任务创建成功",
    )


@router.get(
    "/{task_id}",
    response_model=ResponseModel[TaskResponse],
    summary="获取任务详情",
)
async def get_task(
    task_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
):
    """
    获取指定任务的详细信息
    """
    task = await task_service.get_task(
        db=db,
        task_id=task_id,
        owner=current_user,
    )
    return ResponseModel(
        data=TaskResponse.model_validate(task),
        message="查询成功",
    )


@router.put(
    "/{task_id}",
    response_model=ResponseModel[TaskResponse],
    summary="更新任务",
)
async def update_task(
    task_id: int,
    task_in: TaskUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
):
    """
    更新指定任务
    """
    task = await task_service.update_task(
        db=db,
        task_id=task_id,
        obj_in=task_in,
        owner=current_user,
    )
    return ResponseModel(
        data=TaskResponse.model_validate(task),
        message="任务更新成功",
    )


@router.delete(
    "/{task_id}",
    response_model=ResponseModel[dict],
    summary="删除任务",
)
async def delete_task(
    task_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
):
    """
    删除指定任务
    """
    await task_service.delete_task(
        db=db,
        task_id=task_id,
        owner=current_user,
    )
    return ResponseModel(
        data={},
        message="任务删除成功",
    )


@router.post(
    "/{task_id}/execute",
    response_model=ResponseModel[TaskExecuteResponse],
    summary="执行任务",
)
async def execute_task(
    task_id: int,
    execute_in: Optional[TaskExecuteRequest] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
):
    """
    立即执行指定任务
    """
    task = await task_service.execute_task(
        db=db,
        task_id=task_id,
        owner=current_user,
        params=execute_in.params if execute_in else None,
    )
    return ResponseModel(
        data=TaskExecuteResponse(
            task_id=task.id,
            status=task.status,
            message="任务已开始执行",
        ),
        message="任务执行成功",
    )


@router.get(
    "/{task_id}/logs",
    response_model=ResponseModel[PaginatedResponse[dict]],
    summary="获取任务日志",
)
async def get_task_logs(
    task_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
):
    """
    获取指定任务的执行日志（从 Elasticsearch 查询）
    """
    skip = (page - 1) * page_size

    logs, total = await task_service.get_task_logs(
        db=db,
        task_id=task_id,
        owner=current_user,
        skip=skip,
        limit=page_size,
    )

    return ResponseModel(
        data=build_paginated_data(
            items=logs,
            total=total,
            page=page,
            page_size=page_size,
        ),
        message="查询成功",
    )


@router.get(
    "/statistics",
    response_model=ResponseModel[TaskStatistics],
    summary="获取任务统计",
)
async def get_task_statistics(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
):
    """
    获取当前用户的任务统计信息
    """
    stats = await task_service.get_statistics(
        db=db,
        owner=current_user,
    )
    return ResponseModel(
        data=TaskStatistics(**stats),
        message="查询成功",
    )


# ========== 批量操作路由 ==========
from app.schemas.task import (
    BatchTaskCreate,
    BatchTaskCreateResponse,
    BatchTaskCreateResult,
    BatchTaskDeleteRequest,
    BatchTaskDeleteResponse,
    BatchTaskDeleteResult,
    BatchTaskExecuteRequest,
    BatchTaskExecuteResponse,
    BatchTaskExecuteResult,
)


@router.post(
    "/batch",
    response_model=ResponseModel[BatchTaskCreateResponse],
    status_code=status.HTTP_201_CREATED,
    summary="批量创建任务",
)
async def batch_create_tasks(
    batch_in: BatchTaskCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
):
    """
    批量创建多个任务
    - **tasks**: 任务列表，最多100个任务
    """
    results = await task_service.batch_create_tasks(
        db=db,
        tasks_in=batch_in.tasks,
        owner=current_user,
    )

    result_items = []
    success_count = 0
    failed_count = 0

    for task, error in results:
        if error:
            failed_count += 1
            result_items.append(
                BatchTaskCreateResult(
                    task=None,
                    success=False,
                    error=error,
                )
            )
        else:
            success_count += 1
            result_items.append(
                BatchTaskCreateResult(
                    task=TaskResponse.model_validate(task),
                    success=True,
                    error=None,
                )
            )

    return ResponseModel(
        data=BatchTaskCreateResponse(
            results=result_items,
            total=len(results),
            success_count=success_count,
            failed_count=failed_count,
        ),
        message=f"批量创建完成: 成功 {success_count} 个, 失败 {failed_count} 个",
    )


@router.post(
    "/batch/execute",
    response_model=ResponseModel[BatchTaskExecuteResponse],
    summary="批量执行任务",
)
async def batch_execute_tasks(
    batch_in: BatchTaskExecuteRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
):
    """
    批量执行多个任务
    - **task_ids**: 任务ID列表，最多50个
    - **params**: 可选的执行参数，将应用于所有任务
    """
    results = await task_service.batch_execute_tasks(
        db=db,
        task_ids=batch_in.task_ids,
        owner=current_user,
        params=batch_in.params,
    )

    result_items = []
    success_count = 0
    failed_count = 0

    for task_id, success, task_status, message in results:
        if success:
            success_count += 1
        else:
            failed_count += 1

        result_items.append(
            BatchTaskExecuteResult(
                task_id=task_id,
                success=success,
                status=task_status,
                message=message,
                error=None if success else message,
            )
        )

    return ResponseModel(
        data=BatchTaskExecuteResponse(
            results=result_items,
            total=len(results),
            success_count=success_count,
            failed_count=failed_count,
        ),
        message=f"批量执行完成: 成功 {success_count} 个, 失败 {failed_count} 个",
    )


@router.delete(
    "/batch",
    response_model=ResponseModel[BatchTaskDeleteResponse],
    summary="批量删除任务",
)
async def batch_delete_tasks(
    batch_in: BatchTaskDeleteRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
):
    """
    批量删除多个任务
    - **task_ids**: 任务ID列表，最多100个
    """
    results = await task_service.batch_delete_tasks(
        db=db,
        task_ids=batch_in.task_ids,
        owner=current_user,
    )

    result_items = []
    success_count = 0
    failed_count = 0

    for task_id, success, message in results:
        if success:
            success_count += 1
        else:
            failed_count += 1

        result_items.append(
            BatchTaskDeleteResult(
                task_id=task_id,
                success=success,
                message=message,
                error=None if success else message,
            )
        )

    return ResponseModel(
        data=BatchTaskDeleteResponse(
            results=result_items,
            total=len(results),
            success_count=success_count,
            failed_count=failed_count,
        ),
        message=f"批量删除完成: 成功 {success_count} 个, 失败 {failed_count} 个",
    )
