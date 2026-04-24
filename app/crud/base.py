"""
CRUD基类模块
提供通用的数据库CRUD操作
"""

from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import Base

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=Base)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=Base)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    CRUD基类

    提供通用的增删改查操作

    Generic参数:
        ModelType: SQLAlchemy模型类型
        CreateSchemaType: 创建Schema类型
        UpdateSchemaType: 更新Schema类型
    """

    def __init__(self, model: Type[ModelType]):
        """
        初始化CRUD对象

        Args:
            model: SQLAlchemy模型类
        """
        self.model = model

    async def get(self, db: AsyncSession, id: Any) -> Optional[ModelType]:
        """
        根据ID获取单条记录

        Args:
            db: 数据库会话
            id: 记录ID

        Returns:
            模型实例或None
        """
        result = await db.execute(select(self.model).where(self.model.id == id))
        return result.scalar_one_or_none()

    async def get_or_404(self, db: AsyncSession, id: Any) -> ModelType:
        """
        根据ID获取单条记录，不存在则抛出404

        Args:
            db: 数据库会话
            id: 记录ID

        Returns:
            模型实例

        Raises:
            HTTPException: 记录不存在时抛出404
        """
        obj = await self.get(db, id)
        if obj is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{self.model.__name__} with id {id} not found",
            )
        return obj

    async def get_multi(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> List[ModelType]:
        """
        获取多条记录

        Args:
            db: 数据库会话
            skip: 跳过记录数
            limit: 返回记录数上限

        Returns:
            模型实例列表
        """
        result = await db.execute(
            select(self.model).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def get_multi_by_ids(
        self,
        db: AsyncSession,
        *,
        ids: List[Any],
    ) -> List[ModelType]:
        """
        根据ID列表获取多条记录

        Args:
            db: 数据库会话
            ids: ID列表

        Returns:
            模型实例列表
        """
        result = await db.execute(
            select(self.model).where(self.model.id.in_(ids))
        )
        return list(result.scalars().all())

    async def create(
        self,
        db: AsyncSession,
        *,
        obj_in: Union[CreateSchemaType, Dict[str, Any]],
    ) -> ModelType:
        """
        创建记录

        Args:
            db: 数据库会话
            obj_in: 创建数据（Schema对象或字典）

        Returns:
            创建的模型实例
        """
        if isinstance(obj_in, dict):
            obj_data = obj_in
        else:
            obj_data = obj_in.model_dump(exclude_unset=True)

        db_obj = self.model(**obj_data)
        db.add(db_obj)
        await db.flush()
        await db.refresh(db_obj)
        return db_obj

    async def create_multi(
        self,
        db: AsyncSession,
        *,
        objs_in: List[Union[CreateSchemaType, Dict[str, Any]]],
    ) -> List[ModelType]:
        """
        批量创建记录

        Args:
            db: 数据库会话
            objs_in: 创建数据列表

        Returns:
            创建的模型实例列表
        """
        db_objs = []
        for obj_in in objs_in:
            if isinstance(obj_in, dict):
                obj_data = obj_in
            else:
                obj_data = obj_in.model_dump(exclude_unset=True)
            db_objs.append(self.model(**obj_data))

        db.add_all(db_objs)
        await db.flush()
        for db_obj in db_objs:
            await db.refresh(db_obj)
        return db_objs

    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]],
    ) -> ModelType:
        """
        更新记录

        Args:
            db: 数据库会话
            db_obj: 数据库中的模型实例
            obj_in: 更新数据（Schema对象或字典）

        Returns:
            更新后的模型实例
        """
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)

        db.add(db_obj)
        await db.flush()
        await db.refresh(db_obj)
        return db_obj

    async def remove(self, db: AsyncSession, *, id: Any) -> Optional[ModelType]:
        """
        删除记录

        Args:
            db: 数据库会话
            id: 记录ID

        Returns:
            删除的模型实例，不存在返回None
        """
        obj = await self.get(db, id)
        if obj:
            await db.delete(obj)
            await db.flush()
        return obj

    async def count(self, db: AsyncSession) -> int:
        """
        获取记录总数

        Args:
            db: 数据库会话

        Returns:
            记录总数
        """
        result = await db.execute(select(func.count(self.model.id)))
        return result.scalar() or 0

    async def exists(self, db: AsyncSession, id: Any) -> bool:
        """
        检查记录是否存在

        Args:
            db: 数据库会话
            id: 记录ID

        Returns:
            是否存在
        """
        result = await db.execute(
            select(func.count(self.model.id)).where(self.model.id == id)
        )
        return (result.scalar() or 0) > 0
