"""
用户服务模块
处理用户的业务逻辑
"""

from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthenticationError, ConflictError, NotFoundError, ValidationError
from app.core.security import create_access_token, create_refresh_token, verify_password
from app.crud.user import user as user_crud
from app.models.user import User, UserRole, UserStatus
from app.schemas.user import Token, UserCreate, UserLogin, UserUpdate
from app.utils.logger import get_logger

logger = get_logger("user_service")


class UserService:
    """用户服务类"""

    @staticmethod
    async def register(
        db: AsyncSession,
        *,
        obj_in: UserCreate,
    ) -> User:
        """
        用户注册
        Args:
            db: 数据库会话
            obj_in: 用户创建数据
        Returns:
            创建的用户对象
        Raises:
            ConflictError: 用户已存在
        """
        # 检查用户名是否已存在
        if await user_crud.get_by_username(db, username=obj_in.username):
            raise ConflictError("用户名已存在")

        # 检查邮箱是否已存在
        if await user_crud.get_by_email(db, email=obj_in.email):
            raise ConflictError("邮箱已存在")

        # 创建用户
        user = await user_crud.create(db, obj_in=obj_in)
        logger.info(f"User registered: {user.username} (ID: {user.id})")

        return user

    @staticmethod
    async def login(
        db: AsyncSession,
        *,
        obj_in: UserLogin,
    ) -> tuple[User, Token]:
        """
        用户登录
        Args:
            db: 数据库会话
            obj_in: 登录数据
        Returns:
            (用户对象, Token对象)
        Raises:
            AuthenticationError: 认证失败
        """
        # 验证用户凭据
        user = await user_crud.authenticate(
            db, login=obj_in.username, password=obj_in.password
        )

        if not user:
            raise AuthenticationError("用户名或密码错误")

        # 检查用户状态
        if user.status != UserStatus.ACTIVE:
            raise AuthenticationError("用户账户已被禁用")

        if not user.is_active:
            raise AuthenticationError("用户账户未激活")

        # 增加登录次数
        await user_crud.increment_login_count(db, user=user)

        # 生成Token
        access_token = create_access_token(subject=str(user.id))
        refresh_token = create_refresh_token(subject=str(user.id))

        token = Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=1800,  # 30分钟
        )

        logger.info(f"User logged in: {user.username} (ID: {user.id})")

        return user, token

    @staticmethod
    async def get_user(
        db: AsyncSession,
        *,
        user_id: int,
    ) -> User:
        """
        获取用户信息

        Args:
            db: 数据库会话
            user_id: 用户ID

        Returns:
            用户对象

        Raises:
            NotFoundError: 用户不存在
        """
        user = await user_crud.get(db, id=user_id)
        if not user:
            raise NotFoundError("用户不存在")
        return user

    @staticmethod
    async def update_user(
        db: AsyncSession,
        *,
        user: User,
        obj_in: UserUpdate,
    ) -> User:
        """
        更新用户信息

        Args:
            db: 数据库会话
            user: 用户对象
            obj_in: 更新数据

        Returns:
            更新后的用户对象

        Raises:
            ConflictError: 邮箱已存在
        """
        # 如果更新邮箱，检查是否已被其他用户使用
        if obj_in.email and obj_in.email != user.email:
            existing = await user_crud.get_by_email(db, email=obj_in.email)
            if existing and existing.id != user.id:
                raise ConflictError("邮箱已被其他用户使用")

        # 更新用户
        updated_user = await user_crud.update(db, db_obj=user, obj_in=obj_in)
        logger.info(f"User updated: {updated_user.username} (ID: {updated_user.id})")

        return updated_user

    @staticmethod
    async def change_password(
        db: AsyncSession,
        *,
        user: User,
        old_password: str,
        new_password: str,
    ) -> User:
        """
        修改密码

        Args:
            db: 数据库会话
            user: 用户对象
            old_password: 旧密码
            new_password: 新密码

        Returns:
            更新后的用户对象

        Raises:
            ValidationError: 旧密码错误
        """
        # 验证旧密码
        if not verify_password(old_password, user.hashed_password):
            raise ValidationError("旧密码错误")

        # 更新密码
        updated_user = await user_crud.update(
            db,
            db_obj=user,
            obj_in={"password": new_password},
        )

        logger.info(f"Password changed for user: {user.username} (ID: {user.id})")

        return updated_user

    @staticmethod
    async def refresh_token(
        db: AsyncSession,
        *,
        refresh_token: str,
    ) -> Token:
        """
        刷新访问令牌
        Args:
            db: 数据库会话
            refresh_token: 刷新令牌
        Returns:
            新的Token对象
        Raises:
            AuthenticationError: 令牌无效
        """
        from app.core.security import verify_token

        payload = verify_token(refresh_token, token_type="refresh")
        if not payload:
            raise AuthenticationError("无效的刷新令牌")

        user_id = payload.get("sub")
        if not user_id:
            raise AuthenticationError("无效的令牌载荷")

        # 验证用户是否存在
        user = await user_crud.get(db, id=int(user_id))
        if not user:
            raise AuthenticationError("用户不存在")

        # 生成新的Token
        access_token = create_access_token(subject=str(user.id))
        new_refresh_token = create_refresh_token(subject=str(user.id))

        token = Token(
            access_token=access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=1800,
        )

        logger.info(f"Token refreshed for user: {user.username} (ID: {user.id})")

        return token

    @staticmethod
    async def list_users(
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 20,
        role: Optional[UserRole] = None,
        status: Optional[UserStatus] = None,
        keyword: Optional[str] = None,
    ) -> tuple[list[User], int]:
        """
        获取用户列表

        Args:
            db: 数据库会话
            skip: 跳过数量
            limit: 限制数量
            role: 角色过滤
            status: 状态过滤
            keyword: 关键词搜索

        Returns:
            (用户列表, 总数)
        """
        users = await user_crud.get_multi_with_filters(
            db,
            skip=skip,
            limit=limit,
            role=role,
            status=status,
            keyword=keyword,
        )

        total = await user_crud.count_with_filters(
            db,
            role=role,
            status=status,
            keyword=keyword,
        )

        return users, total


# 用户服务实例
user_service = UserService()
