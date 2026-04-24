"""
响应工具模块
提供统一的响应格式封装
"""

from typing import Any, Dict, Generic, List, Optional, TypeVar

from fastapi import Response
from fastapi.responses import JSONResponse

T = TypeVar("T")


def success_response(
    data: Optional[T] = None,
    message: str = "操作成功",
    status_code: int = 200,
) -> Dict[str, Any]:
    """
    成功响应

    Args:
        data: 响应数据
        message: 响应消息
        status_code: HTTP状态码

    Returns:
        统一格式的响应字典
    """
    return {
        "success": True,
        "message": message,
        "data": data,
        "error": None,
    }


def error_response(
    message: str = "操作失败",
    error_code: int = 400,
    details: Optional[Dict[str, Any]] = None,
) -> JSONResponse:
    """
    错误响应

    Args:
        message: 错误消息
        error_code: 错误码
        details: 详细错误信息

    Returns:
        JSONResponse对象
    """
    return JSONResponse(
        status_code=error_code,
        content={
            "success": False,
            "message": message,
            "data": None,
            "error": {
                "code": error_code,
                "details": details,
            },
        },
    )


def paginated_response(
    items: List[T],
    total: int,
    page: int,
    page_size: int,
) -> Dict[str, Any]:
    """
    分页响应

    Args:
        items: 数据列表
        total: 总记录数
        page: 当前页码
        page_size: 每页数量

    Returns:
        统一格式的分页响应字典
    """
    total_pages = (total + page_size - 1) // page_size

    return {
        "success": True,
        "message": "查询成功",
        "data": {
            "items": items,
            "pagination": {
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1,
            },
        },
        "error": None,
    }
