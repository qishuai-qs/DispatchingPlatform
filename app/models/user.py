"""
用户模型模块
定义用户相关的数据库模型
"""

from enum import Enum as PyEnum
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, Enum, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.task import Task


class UserRole(str, PyEnum):
    """用户角色枚举"""

    USER = "user"
    ADMIN = "admin"
    OPERATOR = "operator"


class UserStatus(str, PyEnum):
    """用户状态枚举"""

    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


class User(Base):
    """用户模型"""

    __tablename__ = "users"

    # 基本信息
    username: Mapped[str] = mapped_column(
        String(50), unique=True, index=True, nullable=False
    )
    email: Mapped[str] = mapped_column(
        String(100), unique=True, index=True, nullable=False
    )
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # 状态信息
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole), default=UserRole.USER, nullable=False
    )
    status: Mapped[UserStatus] = mapped_column(
        Enum(UserStatus), default=UserStatus.ACTIVE, nullable=False
    )

    # 统计信息
    login_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # 关系
    tasks: Mapped[List["Task"]] = relationship(
        "Task", back_populates="owner", lazy="selectin", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username}, email={self.email})>"

    @property
    def role_display(self) -> str:
        """获取角色显示名称"""
        role_map = {
            UserRole.USER: "普通用户",
            UserRole.ADMIN: "管理员",
            UserRole.OPERATOR: "操作员",
        }
        return role_map.get(self.role, "未知")

    @property
    def status_display(self) -> str:
        """获取状态显示名称"""
        status_map = {
            UserStatus.ACTIVE: "正常",
            UserStatus.INACTIVE: "未激活",
            UserStatus.SUSPENDED: "已停用",
        }
        return status_map.get(self.status, "未知")

    def has_role(self, role: UserRole) -> bool:
        """检查用户是否具有指定角色"""
        return self.role == role

    def is_admin(self) -> bool:
        """检查是否为管理员"""
        return self.role == UserRole.ADMIN or self.is_superuser
