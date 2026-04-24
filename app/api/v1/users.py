"""
用户API路由
处理用户信息查询、更新等
"""

from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, get_db_session
from app.models.user import User
from app.schemas.common import ResponseModel
from app.schemas.user import UserResponse, UserUpdate
from app.services.user_service import user_service

router = APIRouter(prefix="/users", tags=["用户"])


@router.get(
    "/me",
    response_model=ResponseModel[UserResponse],
    summary="获取当前用户信息",
)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user),
):
    """
    获取当前登录用户的详细信息
    """
    return ResponseModel(
        data=UserResponse.model_validate(current_user),
        message="查询成功",
    )


@router.put(
    "/me",
    response_model=ResponseModel[UserResponse],
    summary="更新当前用户信息",
)
async def update_current_user(
    user_in: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
):
    """
    更新当前登录用户的信息

    - **email**: 新邮箱（可选）
    - **full_name**: 新全名（可选）
    - **password**: 新密码（可选）
    """
    user = await user_service.update_user(
        db=db,
        user=current_user,
        obj_in=user_in,
    )
    return ResponseModel(
        data=UserResponse.model_validate(user),
        message="更新成功",
    )


@router.post(
    "/me/password",
    response_model=ResponseModel[dict],
    summary="修改密码",
)
async def change_password(
    old_password: str,
    new_password: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
):
    """
    修改当前用户密码

    - **old_password**: 旧密码
    - **new_password**: 新密码
    """
    await user_service.change_password(
        db=db,
        user=current_user,
        old_password=old_password,
        new_password=new_password,
    )
    return ResponseModel(
        data={},
        message="密码修改成功",
    )
