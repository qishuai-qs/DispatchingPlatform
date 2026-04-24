"""
Schema模块
导出所有Pydantic Schema定义
"""

from app.schemas.common import (
    ErrorDetail,
    HealthStatus,
    PaginatedResponse,
    PaginationInfo,
    PaginationParams,
    ResponseModel,
    SystemInfo,
)
from app.schemas.task import (
    TaskBase,
    TaskCreate,
    TaskExecuteRequest,
    TaskExecuteResponse,
    TaskFilter,
    TaskListResponse,
    TaskLogCreate,
    TaskLogListResponse,
    TaskLogResponse,
    TaskResponse,
    TaskStatistics,
    TaskSummary,
    TaskUpdate,
)
from app.schemas.user import (
    PasswordReset,
    Token,
    TokenPayload,
    UserBase,
    UserCreate,
    UserInDB,
    UserListResponse,
    UserLogin,
    UserResponse,
    UserUpdate,
)

__all__ = [
    # Common
    "ResponseModel",
    "PaginationParams",
    "PaginationInfo",
    "PaginatedResponse",
    "ErrorDetail",
    "HealthStatus",
    "SystemInfo",
    # User
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserInDB",
    "UserResponse",
    "UserLogin",
    "Token",
    "TokenPayload",
    "PasswordReset",
    "UserListResponse",
    # Task
    "TaskBase",
    "TaskCreate",
    "TaskUpdate",
    "TaskResponse",
    "TaskSummary",
    "TaskListResponse",
    "TaskExecuteRequest",
    "TaskExecuteResponse",
    "TaskLogCreate",
    "TaskLogResponse",
    "TaskLogListResponse",
    "TaskFilter",
    "TaskStatistics",
]
