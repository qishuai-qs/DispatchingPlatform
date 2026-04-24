"""
通用Schema定义
"""

from typing import Any, Dict, Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ResponseModel(BaseModel, Generic[T]):
    """统一响应模型"""

    success: bool = Field(default=True, description="是否成功")
    message: str = Field(default="操作成功", description="响应消息")
    data: Optional[T] = Field(default=None, description="响应数据")
    error: Optional[Dict[str, Any]] = Field(default=None, description="错误信息")


class PaginationParams(BaseModel):
    """分页参数"""

    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=20, ge=1, le=100, description="每页数量")


class PaginationInfo(BaseModel):
    """分页信息"""

    total: int = Field(description="总记录数")
    page: int = Field(description="当前页码")
    page_size: int = Field(description="每页数量")
    total_pages: int = Field(description="总页数")
    has_next: bool = Field(description="是否有下一页")
    has_prev: bool = Field(description="是否有上一页")


class PaginatedResponse(BaseModel, Generic[T]):
    """分页响应模型"""

    items: List[T] = Field(description="数据列表")
    pagination: PaginationInfo = Field(description="分页信息")


class ErrorDetail(BaseModel):
    """错误详情"""

    code: int = Field(description="错误码")
    message: str = Field(description="错误消息")
    details: Optional[Dict[str, Any]] = Field(default=None, description="详细错误信息")


class HealthStatus(BaseModel):
    """健康状态"""

    status: str = Field(description="状态: healthy/degraded/unhealthy")
    version: str = Field(description="应用版本")
    timestamp: str = Field(description="检查时间")
    checks: Dict[str, Any] = Field(default_factory=dict, description="各项检查详情")


class SystemInfo(BaseModel):
    """系统信息"""

    app_name: str = Field(description="应用名称")
    version: str = Field(description="应用版本")
    environment: str = Field(description="运行环境")
    python_version: str = Field(description="Python版本")
    uptime: str = Field(description="运行时间")
