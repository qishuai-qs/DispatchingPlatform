"""
数据库模型基类
提供SQLAlchemy基础配置和通用功能
"""

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Integer, func
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(AsyncAttrs, DeclarativeBase):
    """SQLAlchemy声明式基类"""

    # 类型注解映射
    type_annotation_map = {
        datetime: DateTime(timezone=True),
    }

    # 通用字段
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def to_dict(self, exclude: set[str] | None = None) -> dict[str, Any]:
        """
        将模型转换为字典

        Args:
            exclude: 要排除的字段集合

        Returns:
            模型数据的字典表示
        """
        exclude = exclude or set()
        result = {}
        for column in self.__table__.columns:
            if column.name not in exclude:
                value = getattr(self, column.name)
                if isinstance(value, datetime):
                    value = value.isoformat()
                result[column.name] = value
        return result

    def __repr__(self) -> str:
        """字符串表示"""
        return f"<{self.__class__.__name__}(id={self.id})>"
