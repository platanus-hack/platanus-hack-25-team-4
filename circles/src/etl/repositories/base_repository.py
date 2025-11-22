"""
Base Repository - Generic CRUD operations with automatic user_id scoping.

Provides a reusable base class for all repository implementations.
Ensures all queries are automatically scoped to prevent cross-user data access.
"""

from typing import Any, Dict, Generic, List, Optional, Type, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import SQLModel

ModelT = TypeVar("ModelT", bound=SQLModel)


class BaseRepository(Generic[ModelT]):
    """
    Generic repository providing CRUD operations with user_id scoping.

    All queries are automatically filtered by user_id to prevent data leaks.
    Subclasses should override methods only when custom logic is needed.
    """

    def __init__(self, model_class: Type[ModelT]):
        """
        Initialize repository for a specific model.

        Args:
            model_class: SQLModel class to operate on
        """
        self.model_class = model_class

    async def get_by_id(
        self, model_id: int, user_id: int, session: AsyncSession
    ) -> Optional[ModelT]:
        """
        Get single record by ID with user scope.

        Args:
            model_id: Record ID
            user_id: User ID for scoping
            session: Database session

        Returns:
            Model instance or None if not found
        """
        stmt = select(self.model_class).where(
            (self.model_class.id == model_id) & (self.model_class.user_id == user_id)
        )
        result = await session.exec(stmt)
        return result.first()

    async def get_all(
        self, user_id: int, session: AsyncSession, limit: int = 100, offset: int = 0
    ) -> List[ModelT]:
        """
        Get all records for user with pagination.

        Args:
            user_id: User ID for scoping
            session: Database session
            limit: Maximum records to return
            offset: Number of records to skip

        Returns:
            List of model instances
        """
        stmt = (
            select(self.model_class)
            .where(self.model_class.user_id == user_id)
            .limit(limit)
            .offset(offset)
        )
        result = await session.exec(stmt)
        return result.all()

    async def count(self, user_id: int, session: AsyncSession) -> int:
        """
        Count total records for user.

        Args:
            user_id: User ID for scoping
            session: Database session

        Returns:
            Total record count
        """
        from sqlalchemy import func

        stmt = select(func.count(self.model_class.id)).where(
            self.model_class.user_id == user_id
        )
        result = await session.exec(stmt)
        count = result.first()
        return count or 0

    async def create(
        self, user_id: int, data: Dict[str, Any], session: AsyncSession
    ) -> ModelT:
        """
        Create new record with user_id.

        Args:
            user_id: User ID (added to data)
            data: Model data dictionary
            session: Database session

        Returns:
            Created model instance
        """
        # Ensure user_id is set
        data["user_id"] = user_id

        instance = self.model_class(**data)
        session.add(instance)
        await session.flush()
        return instance

    async def create_batch(
        self, user_id: int, records: List[Dict[str, Any]], session: AsyncSession
    ) -> List[ModelT]:
        """
        Create multiple records efficiently with user_id.

        Uses batch insert for better performance with large datasets.

        Args:
            user_id: User ID (added to all records)
            records: List of model data dictionaries
            session: Database session

        Returns:
            List of created model instances
        """
        instances = []
        for data in records:
            data["user_id"] = user_id
            instance = self.model_class(**data)
            instances.append(instance)
            session.add(instance)

        await session.flush()
        return instances

    async def update(
        self, model_id: int, user_id: int, data: Dict[str, Any], session: AsyncSession
    ) -> Optional[ModelT]:
        """
        Update record (user-scoped for safety).

        Args:
            model_id: Record ID
            user_id: User ID for scope validation
            data: Fields to update
            session: Database session

        Returns:
            Updated model instance or None if not found
        """
        instance = await self.get_by_id(model_id, user_id, session)
        if not instance:
            return None

        # Update fields
        for key, value in data.items():
            if key != "user_id":  # Never allow user_id changes
                setattr(instance, key, value)

        await session.flush()
        return instance

    async def delete(self, model_id: int, user_id: int, session: AsyncSession) -> bool:
        """
        Delete record (user-scoped for safety).

        Args:
            model_id: Record ID
            user_id: User ID for scope validation
            session: Database session

        Returns:
            True if deleted, False if not found
        """
        instance = await self.get_by_id(model_id, user_id, session)
        if not instance:
            return False

        await session.delete(instance)
        await session.flush()
        return True

    async def delete_by_source(
        self, source_id: int, user_id: int, session: AsyncSession
    ) -> int:
        """
        Delete all records for a source (if model has source_id).

        Args:
            source_id: Source ID
            user_id: User ID for scope validation
            session: Database session

        Returns:
            Number of deleted records
        """
        if not hasattr(self.model_class, "source_id"):
            raise ValueError(f"{self.model_class.__name__} does not support source_id")

        stmt = select(self.model_class).where(
            (self.model_class.source_id == source_id)
            & (self.model_class.user_id == user_id)
        )
        result = await session.exec(stmt)
        instances = result.all()

        for instance in instances:
            await session.delete(instance)

        await session.flush()
        return len(instances)
