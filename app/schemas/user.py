"""
用户相关Schema定义
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models.user import UserRole, UserStatus


class UserBase(BaseModel):
    """用户基础Schema"""

    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: EmailStr = Field(..., description="邮箱")
    full_name: Optional[str] = Field(default=None, max_length=100, description="全名")


class UserCreate(UserBase):
    """用户创建Schema"""

    password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        description="密码",
    )
    role: Optional[UserRole] = Field(default=UserRole.USER, description="角色")

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """验证密码复杂度"""
        if not any(c.isupper() for c in v):
            raise ValueError("密码必须包含至少一个大写字母")
        if not any(c.islower() for c in v):
            raise ValueError("密码必须包含至少一个小写字母")
        if not any(c.isdigit() for c in v):
            raise ValueError("密码必须包含至少一个数字")
        return v


class UserUpdate(BaseModel):
    """用户更新Schema"""

    email: Optional[EmailStr] = Field(default=None, description="邮箱")
    full_name: Optional[str] = Field(default=None, max_length=100, description="全名")
    password: Optional[str] = Field(
        default=None,
        min_length=8,
        max_length=100,
        description="新密码",
    )


class UserInDB(UserBase):
    """数据库中的用户Schema"""

    id: int
    is_active: bool
    is_superuser: bool
    role: UserRole
    status: UserStatus
    login_count: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserResponse(UserBase):
    """用户响应Schema"""

    id: int
    role: UserRole
    status: UserStatus
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserLogin(BaseModel):
    """用户登录Schema"""

    username: str = Field(..., description="用户名或邮箱")
    password: str = Field(..., description="密码")


class Token(BaseModel):
    """Token响应Schema"""

    access_token: str = Field(..., description="访问令牌")
    refresh_token: str = Field(..., description="刷新令牌")
    token_type: str = Field(default="bearer", description="令牌类型")
    expires_in: int = Field(..., description="过期时间（秒）")


class TokenPayload(BaseModel):
    """Token载荷Schema"""

    sub: Optional[str] = Field(default=None, description="主题（用户ID）")
    exp: Optional[datetime] = Field(default=None, description="过期时间")
    type: Optional[str] = Field(default=None, description="令牌类型")


class PasswordReset(BaseModel):
    """密码重置Schema"""

    old_password: str = Field(..., description="旧密码")
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        description="新密码",
    )

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        """验证新密码复杂度"""
        if not any(c.isupper() for c in v):
            raise ValueError("密码必须包含至少一个大写字母")
        if not any(c.islower() for c in v):
            raise ValueError("密码必须包含至少一个小写字母")
        if not any(c.isdigit() for c in v):
            raise ValueError("密码必须包含至少一个数字")
        return v


class UserListResponse(BaseModel):
    """用户列表响应"""

    items: List[UserResponse]
    total: int
    page: int
    page_size: int
