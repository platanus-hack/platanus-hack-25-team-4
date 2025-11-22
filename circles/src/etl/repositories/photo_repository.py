"""
Photo Repository - Specialized repository for Photo model operations.

Extends BaseRepository with photo-specific queries and batch operations.
"""

from typing import Any, List, Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Photo
from .base_repository import BaseRepository


class PhotoRepository(BaseRepository[Photo]):
    """
    Repository for Photo model operations.

    Provides photo-specific queries with automatic user_id scoping
    and optimized batch operations for parallel processing.
    """

    def __init__(self):
        """Initialize PhotoRepository."""
        super().__init__(Photo)

    async def get_by_source(
        self, source_id: int, user_id: int, session: AsyncSession
    ) -> List[Photo]:
        """
        Get all photos for a source (e.g., upload batch).

        Args:
            source_id: Source ID (RawDataSource)
            user_id: User ID for scoping
            session: Database session

        Returns:
            List of photo records
        """
        stmt = select(Photo).where(
            and_(Photo.source_id == source_id, Photo.user_id == user_id)  # type: ignore[arg-type]
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def get_recent(
        self, user_id: int, session: AsyncSession, limit: int = 50
    ) -> List[Photo]:
        """
        Get most recent photos for user.

        Args:
            user_id: User ID for scoping
            session: Database session
            limit: Maximum records to return

        Returns:
            List of photo records ordered by creation time
        """
        stmt = (
            select(Photo)
            .where(Photo.user_id == user_id)
            .order_by(Photo.created_at.desc())
            .limit(limit)
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def create_from_processor_result(
        self,
        user_id: int,
        source_id: Optional[int],
        processor_result: Any,
        session: AsyncSession,
    ) -> Photo:
        """
        Create photo record from processor result.

        Args:
            user_id: User ID
            source_id: Optional source ID
            processor_result: Processor output with content and metadata
            session: Database session

        Returns:
            Created photo record
        """
        # Extract data from processor result
        content = processor_result.content
        metadata = processor_result.metadata or {}
        exif_data = metadata.get("exif_data", {})

        photo_data = {
            "source_id": source_id,
            "file_reference": {
                "filename": content.get("image_file", ""),
                "size": metadata.get("file_size", 0),
                "type": metadata.get("file_type", ""),
            },
            "vlm_caption": content.get("caption", ""),
            "vlm_analysis": content.get("analysis", {}),
            "exif_data": exif_data,
        }

        return await self.create(user_id, photo_data, session)

    async def create_batch_from_processor_results(
        self,
        user_id: int,
        source_id: Optional[int],
        processor_results: List[Any],
        session: AsyncSession,
    ) -> List[Photo]:
        """
        Create multiple photo records efficiently from processor results.

        Optimized for batch processing with minimal database round-trips.

        Args:
            user_id: User ID
            source_id: Optional source ID (shared for batch)
            processor_results: List of processor outputs
            session: Database session

        Returns:
            List of created photo records
        """
        records = []
        for processor_result in processor_results:
            # Extract data from processor result
            content = processor_result.content
            metadata = processor_result.metadata or {}
            exif_data = metadata.get("exif_data", {})

            photo_data = {
                "source_id": source_id,
                "file_reference": {
                    "filename": content.get("image_file", ""),
                    "size": metadata.get("file_size", 0),
                    "type": metadata.get("file_type", ""),
                },
                "vlm_caption": content.get("caption", ""),
                "vlm_analysis": content.get("analysis", {}),
                "exif_data": exif_data,
            }
            records.append(photo_data)

        return await self.create_batch(user_id, records, session)

    async def search_by_caption(
        self,
        user_id: int,
        query: str,
        session: AsyncSession,
        limit: int = 50,
    ) -> List[Photo]:
        """
        Search photos by caption text.

        Args:
            user_id: User ID for scoping
            query: Search query string
            session: Database session
            limit: Maximum records to return

        Returns:
            List of matching photo records
        """
        # Simple substring search in caption
        # For production, consider full-text search or vector embeddings
        search_pattern = f"%{query}%"
        stmt = (
            select(Photo)
            .where(
                (Photo.user_id == user_id) & (Photo.vlm_caption.ilike(search_pattern))
            )
            .limit(limit)
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def count_by_source(
        self, source_id: int, user_id: int, session: AsyncSession
    ) -> int:
        """
        Count photos for a source.

        Args:
            source_id: Source ID
            user_id: User ID for scoping
            session: Database session

        Returns:
            Photo count
        """
        from sqlalchemy import func

        stmt = select(func.count(Photo.id)).where(  # type: ignore[arg-type]
            and_(Photo.source_id == source_id, Photo.user_id == user_id)  # type: ignore[arg-type]
        )
        result = await session.execute(stmt)
        count = result.scalar_one()
        return count or 0
