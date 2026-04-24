"""
认证API路由
处理用户注册、登录、Token刷新等
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session
from app.schemas.common import ResponseModel
from app.schemas.user import Token, UserCreate, UserLogin, UserResponse
from app.services.user_service import user_service

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post(
    "/register",
    response_model=ResponseModel[UserResponse],
    status_code=status.HTTP_201_CREATED,
    summary="用户注册",
)
async def register(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db_session),
):
    """
    用户注册

    - **username**: 用户名（3-50字符）
    - **email**: 邮箱地址
    - **password**: 密码（至少8位，包含大小写字母和数字）
    - **full_name**: 全名（可选）
    """
    user = await user_service.register(db=db, obj_in=user_in)
    return ResponseModel(
        data=UserResponse.model_validate(user),
        message="注册成功",
    )


@router.post(
    "/login",
    response_model=ResponseModel[Token],
    summary="用户登录",
)
async def login(
    user_in: UserLogin,
    db: AsyncSession = Depends(get_db_session),
):
    """
    用户登录

    - **username**: 用户名或邮箱
    - **password**: 密码

    返回JWT访问令牌和刷新令牌
    """
    _, token = await user_service.login(db=db, obj_in=user_in)
    return ResponseModel(
        data=token,
        message="登录成功",
    )


@router.post(
    "/refresh",
    response_model=ResponseModel[Token],
    summary="刷新Token",
)
async def refresh_token(
    refresh_token: str,
    db: AsyncSession = Depends(get_db_session),
):
    """
    刷新访问令牌

    - **refresh_token**: 刷新令牌

    使用刷新令牌获取新的访问令牌
    """
    token = await user_service.refresh_token(db=db, refresh_token=refresh_token)
    return ResponseModel(
        data=token,
        message="Token刷新成功",
    )
