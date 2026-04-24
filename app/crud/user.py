"""
用户CRUD模块
"""

from typing import Any, Dict, List, Optional, Union

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash, verify_password
from app.crud.base import CRUDBase
from app.models.user import User, UserRole, UserStatus
from app.schemas.user import UserCreate, UserUpdate


class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    """用户CRUD操作类"""

    async def get_by_email(self, db: AsyncSession, *, email: str) -> Optional[User]:
        """
        根据邮箱获取用户

        Args:
            db: 数据库会话
            email: 邮箱地址

        Returns:
            用户对象或None
        """
        result = await db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_by_username(self, db: AsyncSession, *, username: str) -> Optional[User]:
        """
        根据用户名获取用户

        Args:
            db: 数据库会话
            username: 用户名

        Returns:
            用户对象或None
        """
        result = await db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()

    async def get_by_email_or_username(
        self, db: AsyncSession, *, login: str
    ) -> Optional[User]:
        """
        根据邮箱或用户名获取用户

        Args:
            db: 数据库会话
            login: 邮箱或用户名

        Returns:
            用户对象或None
        """
        result = await db.execute(
            select(User).where(
                or_(User.email == login, User.username == login)
            )
        )
        return result.scalar_one_or_none()

    async def create(self, db: AsyncSession, *, obj_in: Union[UserCreate, Dict[str, Any]]) -> User:
        """
        创建用户

        Args:
            db: 数据库会话
            obj_in: 用户创建数据

        Returns:
            创建的用户对象
        """
        if isinstance(obj_in, dict):
            obj_data = obj_in.copy()
        else:
            obj_data = obj_in.model_dump(exclude_unset=True)

        # 提取并加密密码
        password = obj_data.pop("password", None)
        if password:
            obj_data["hashed_password"] = get_password_hash(password)

        # 创建用户对象
        db_obj = User(**obj_data)
        db.add(db_obj)
        await db.flush()
        await db.refresh(db_obj)
        return db_obj

    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: User,
        obj_in: Union[UserUpdate, Dict[str, Any]],
    ) -> User:
        """
        更新用户

        Args:
            db: 数据库会话
            db_obj: 数据库中的用户对象
            obj_in: 更新数据

        Returns:
            更新后的用户对象
        """
        if isinstance(obj_in, dict):
            update_data = obj_in.copy()
        else:
            update_data = obj_in.model_dump(exclude_unset=True)

        # 处理密码更新
        if "password" in update_data and update_data["password"]:
            hashed_password = get_password_hash(update_data.pop("password"))
            update_data["hashed_password"] = hashed_password

        return await super().update(db, db_obj=db_obj, obj_in=update_data)

    async def authenticate(
        self, db: AsyncSession, *, login: str, password: str
    ) -> Optional[User]:
        """
        验证用户凭据

        Args:
            db: 数据库会话
            login: 用户名或邮箱
            password: 密码

        Returns:
            验证通过的用户对象，失败返回None
        """
        user = await self.get_by_email_or_username(db, login=login)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    async def increment_login_count(self, db: AsyncSession, *, user: User) -> User:
        """
        增加登录次数

        Args:
            db: 数据库会话
            user: 用户对象

        Returns:
            更新后的用户对象
        """
        user.login_count += 1
        db.add(user)
        await db.flush()
        await db.refresh(user)
        return user

    async def is_active(self, user: User) -> bool:
        """
        检查用户是否激活

        Args:
            user: 用户对象

        Returns:
            是否激活
        """
        return user.is_active and user.status == UserStatus.ACTIVE

    async def is_superuser(self, user: User) -> bool:
        """
        检查是否为超级用户

        Args:
            user: 用户对象

        Returns:
            是否为超级用户
        """
        return user.is_superuser

    async def get_multi_with_filters(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100,
        role: Optional[UserRole] = None,
        status: Optional[UserStatus] = None,
        is_active: Optional[bool] = None,
        keyword: Optional[str] = None,
    ) -> List[User]:
        """
        带过滤条件的获取用户列表

        Args:
            db: 数据库会话
            skip: 跳过数量
            limit: 限制数量
            role: 角色过滤
            status: 状态过滤
            is_active: 是否激活过滤
            keyword: 关键词搜索

        Returns:
            用户列表
        """
        query = select(User)

        if role:
            query = query.where(User.role == role)
        if status:
            query = query.where(User.status == status)
        if is_active is not None:
            query = query.where(User.is_active == is_active)
        if keyword:
            query = query.where(
                or_(
                    User.username.ilike(f"%{keyword}%"),
                    User.email.ilike(f"%{keyword}%"),
                    User.full_name.ilike(f"%{keyword}%"),
                )
            )

        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())

    async def count_with_filters(
        self,
        db: AsyncSession,
        *,
        role: Optional[UserRole] = None,
        status: Optional[UserStatus] = None,
        is_active: Optional[bool] = None,
        keyword: Optional[str] = None,
    ) -> int:
        """
        带过滤条件的统计用户数量

        Args:
            db: 数据库会话
            role: 角色过滤
            status: 状态过滤
            is_active: 是否激活过滤
            keyword: 关键词搜索

        Returns:
            用户数量
        """
        query = select(func.count(User.id))

        if role:
            query = query.where(User.role == role)
        if status:
            query = query.where(User.status == status)
        if is_active is not None:
            query = query.where(User.is_active == is_active)
        if keyword:
            query = query.where(
                or_(
                    User.username.ilike(f"%{keyword}%"),
                    User.email.ilike(f"%{keyword}%"),
                    User.full_name.ilike(f"%{keyword}%"),
                )
            )

        result = await db.execute(query)
        return result.scalar() or 0


# 用户CRUD实例
user = CRUDUser(User)
