"""
任务相关Schema定义
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.task import TaskPriority, TaskStatus, TaskType


class TaskBase(BaseModel):
    """任务基础Schema"""

    name: str = Field(..., min_length=1, max_length=200, description="任务名称")
    description: Optional[str] = Field(default=None, description="任务描述")
    task_type: TaskType = Field(default=TaskType.ONE_TIME, description="任务类型")
    priority: TaskPriority = Field(default=TaskPriority.MEDIUM, description="优先级")
    command: Optional[str] = Field(default=None, description="执行命令或脚本")
    params: Optional[Dict[str, Any]] = Field(default=None, description="任务参数")
    cron_expression: Optional[str] = Field(default=None, max_length=100, description="Cron表达式")
    timeout: int = Field(default=3600, ge=0, description="超时时间(秒)")
    max_retries: int = Field(default=0, ge=0, le=10, description="最大重试次数")
    scheduled_at: Optional[datetime] = Field(default=None, description="计划执行时间")


class TaskCreate(TaskBase):
    """任务创建Schema"""

    @field_validator("cron_expression")
    @classmethod
    def validate_cron(cls, v: Optional[str], info) -> Optional[str]:
        """验证Cron表达式（简单验证格式）"""
        if v is not None:
            # 如果是定时任务类型，必须有cron表达式
            data = info.data
            if data.get("task_type") == TaskType.SCHEDULED and not v:
                raise ValueError("定时任务必须提供Cron表达式")
        return v


class TaskUpdate(BaseModel):
    """任务更新Schema"""

    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = Field(default=None)
    priority: Optional[TaskPriority] = Field(default=None)
    command: Optional[str] = Field(default=None)
    params: Optional[Dict[str, Any]] = Field(default=None)
    cron_expression: Optional[str] = Field(default=None, max_length=100)
    timeout: Optional[int] = Field(default=None, ge=0)
    max_retries: Optional[int] = Field(default=None, ge=0, le=10)
    scheduled_at: Optional[datetime] = Field(default=None)


class TaskResponse(BaseModel):
    """任务响应Schema"""

    id: int
    name: str
    description: Optional[str]
    task_type: TaskType
    status: TaskStatus
    priority: TaskPriority
    command: Optional[str]
    params: Optional[Dict[str, Any]]
    cron_expression: Optional[str]
    timeout: int
    max_retries: int
    retry_count: int
    scheduled_at: Optional[datetime]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    result: Optional[Dict[str, Any]]
    error_message: Optional[str]
    output: Optional[str]
    owner_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TaskSummary(BaseModel):
    """任务摘要Schema（用于列表）"""

    id: int
    name: str
    status: TaskStatus
    priority: TaskPriority
    task_type: TaskType
    scheduled_at: Optional[datetime]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    owner_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TaskListResponse(BaseModel):
    """任务列表响应"""

    items: List[TaskSummary]
    total: int
    page: int
    page_size: int


class TaskExecuteRequest(BaseModel):
    """任务执行请求"""

    params: Optional[Dict[str, Any]] = Field(
        default=None, description="执行时的额外参数"
    )


class TaskExecuteResponse(BaseModel):
    """任务执行响应"""

    task_id: int
    status: TaskStatus
    message: str


class TaskLogBase(BaseModel):
    """任务日志基础Schema"""

    level: str = Field(..., description="日志级别")
    message: str = Field(..., description="日志内容")
    source: Optional[str] = Field(default=None, description="日志来源")
    meta: Optional[Dict[str, Any]] = Field(default=None, description="元数据")


class TaskLogCreate(TaskLogBase):
    """任务日志创建Schema"""

    task_id: int = Field(..., description="任务ID")


class TaskLogResponse(TaskLogBase):
    """任务日志响应Schema"""

    id: int
    task_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TaskLogListResponse(BaseModel):
    """任务日志列表响应"""

    items: List[TaskLogResponse]
    total: int
    page: int
    page_size: int


class TaskFilter(BaseModel):
    """任务筛选条件"""

    status: Optional[TaskStatus] = Field(default=None, description="任务状态")
    task_type: Optional[TaskType] = Field(default=None, description="任务类型")
    priority: Optional[TaskPriority] = Field(default=None, description="优先级")
    keyword: Optional[str] = Field(default=None, description="关键词搜索")


class TaskStatistics(BaseModel):
    """任务统计信息"""

    total: int = Field(description="总任务数")
    pending: int = Field(description="待执行")
    running: int = Field(description="执行中")
    success: int = Field(description="成功")
    failed: int = Field(description="失败")
    cancelled: int = Field(description="已取消")
    timeout: int = Field(description="超时")
