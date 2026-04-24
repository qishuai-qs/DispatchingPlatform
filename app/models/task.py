"""
任务模型模块
定义任务相关的数据库模型
"""

from datetime import datetime
from enum import Enum as PyEnum
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class TaskStatus(str, PyEnum):
    """任务状态枚举"""

    PENDING = "pending"           # 待执行
    RUNNING = "running"           # 执行中
    SUCCESS = "success"           # 成功
    FAILED = "failed"             # 失败
    CANCELLED = "cancelled"       # 已取消
    TIMEOUT = "timeout"           # 超时


class TaskPriority(str, PyEnum):
    """任务优先级枚举"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TaskType(str, PyEnum):
    """任务类型枚举"""

    SCHEDULED = "scheduled"       # 定时任务
    ONE_TIME = "one_time"         # 一次性任务
    RECURRING = "recurring"       # 周期性任务
    WORKFLOW = "workflow"         # 工作流任务


class Task(Base):
    """任务模型"""

    __tablename__ = "tasks"

    # 基本信息
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # 任务类型和状态
    task_type: Mapped[TaskType] = mapped_column(
        Enum(TaskType), default=TaskType.ONE_TIME, nullable=False
    )
    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus), default=TaskStatus.PENDING, nullable=False, index=True
    )
    priority: Mapped[TaskPriority] = mapped_column(
        Enum(TaskPriority), default=TaskPriority.MEDIUM, nullable=False
    )

    # 任务配置
    command: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # 执行命令/脚本
    params: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)  # 参数
    cron_expression: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # Cron表达式

    # 执行控制
    timeout: Mapped[int] = mapped_column(Integer, default=3600, nullable=False)  # 超时时间(秒)
    max_retries: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # 最大重试次数
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # 已重试次数

    # 调度信息
    scheduled_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )  # 计划执行时间
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )  # 实际开始时间
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )  # 完成时间

    # 执行结果
    result: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)  # 执行结果
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # 错误信息
    output: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # 输出内容

    # 关联用户
    owner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    owner: Mapped["User"] = relationship("User", back_populates="tasks")

    def __repr__(self) -> str:
        return f"<Task(id={self.id}, name={self.name}, status={self.status})>"

    @property
    def duration(self) -> Optional[float]:
        """计算任务执行时长（秒）"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    @property
    def is_running(self) -> bool:
        """检查任务是否正在运行"""
        return self.status == TaskStatus.RUNNING

    @property
    def is_completed(self) -> bool:
        """检查任务是否已完成（成功或失败）"""
        return self.status in (TaskStatus.SUCCESS, TaskStatus.FAILED, TaskStatus.TIMEOUT)

    @property
    def can_retry(self) -> bool:
        """检查任务是否可以重试"""
        return self.retry_count < self.max_retries and self.status in (
            TaskStatus.FAILED,
            TaskStatus.TIMEOUT,
        )

    def to_summary(self) -> Dict[str, Any]:
        """获取任务摘要"""
        return {
            "id": self.id,
            "name": self.name,
            "status": self.status.value,
            "priority": self.priority.value,
            "task_type": self.task_type.value,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "scheduled_at": self.scheduled_at.isoformat() if self.scheduled_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration": self.duration,
        }


class TaskLog(Base):
    """任务日志模型"""

    __tablename__ = "task_logs"

    # 关联任务
    task_id: Mapped[int] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # 日志内容
    level: Mapped[str] = mapped_column(String(20), nullable=False)  # DEBUG/INFO/WARNING/ERROR
    message: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # 日志来源

    # 额外信息
    meta: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    def __repr__(self) -> str:
        return f"<TaskLog(id={self.id}, task_id={self.task_id}, level={self.level})>"
