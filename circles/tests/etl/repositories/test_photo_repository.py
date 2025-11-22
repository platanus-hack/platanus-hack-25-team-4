"""
Tests for PhotoRepository - Multi-user data isolation and batch operations.

Ensures:
- User data isolation (user A can't access user B's photos)
- Pagination and filtering work correctly
- Batch operations are efficient
- Query scoping prevents accidental data leaks
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from circles.src.etl.models import Photo
from circles.src.etl.repositories import PhotoRepository


@pytest.fixture
async def async_db():
    """Create test database session."""
    # Use in-memory SQLite for testing
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    # Create session factory
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_delete=False)

    async with async_session() as session:
        yield session

    await engine.dispose()


@pytest.mark.asyncio
async def test_user_isolation(async_db: AsyncSession):
    """Test that queries are scoped by user_id."""
    repo = PhotoRepository()

    # Create photos for user 1
    photo1_data = {
        "vlm_caption": "User 1 photo",
        "vlm_analysis": {"subject": "test"},
        "file_reference": {"filename": "photo1.jpg"},
    }
    photo1 = await repo.create(user_id=1, data=photo1_data, session=async_db)

    # Create photos for user 2
    photo2_data = {
        "vlm_caption": "User 2 photo",
        "vlm_analysis": {"subject": "test"},
        "file_reference": {"filename": "photo2.jpg"},
    }
    photo2 = await repo.create(user_id=2, data=photo2_data, session=async_db)

    # User 1 should only see their photos
    user1_photos = await repo.get_all(user_id=1, session=async_db, limit=100)
    assert len(user1_photos) == 1
    assert user1_photos[0].vlm_caption == "User 1 photo"

    # User 2 should only see their photos
    user2_photos = await repo.get_all(user_id=2, session=async_db, limit=100)
    assert len(user2_photos) == 1
    assert user2_photos[0].vlm_caption == "User 2 photo"

    # User 1 cannot access user 2's photos by ID
    user2_photo_from_user1 = await repo.get_by_id(
        model_id=photo2.id, user_id=1, session=async_db
    )
    assert user2_photo_from_user1 is None  # Data leak prevention


@pytest.mark.asyncio
async def test_create_batch(async_db: AsyncSession):
    """Test efficient batch creation."""
    repo = PhotoRepository()

    # Create batch of photos
    records = [
        {
            "vlm_caption": f"Photo {i}",
            "vlm_analysis": {"index": i},
            "file_reference": {"filename": f"photo{i}.jpg"},
        }
        for i in range(10)
    ]

    photos = await repo.create_batch(user_id=1, records=records, session=async_db)

    assert len(photos) == 10
    assert all(p.user_id == 1 for p in photos)

    # Verify all were saved
    all_photos = await repo.get_all(user_id=1, session=async_db, limit=100)
    assert len(all_photos) == 10


@pytest.mark.asyncio
async def test_get_recent(async_db: AsyncSession):
    """Test getting recent photos ordered by creation time."""
    repo = PhotoRepository()

    # Create photos for user 1
    for i in range(5):
        await repo.create(
            user_id=1,
            data={
                "vlm_caption": f"Photo {i}",
                "vlm_analysis": {},
                "file_reference": {"filename": f"photo{i}.jpg"},
            },
            session=async_db,
        )

    # Get recent (should be ordered descending by created_at)
    recent = await repo.get_recent(user_id=1, session=async_db, limit=3)

    assert len(recent) == 3
    # Most recent should be first
    assert recent[0].vlm_caption == "Photo 4"


@pytest.mark.asyncio
async def test_pagination(async_db: AsyncSession):
    """Test pagination with limit and offset."""
    repo = PhotoRepository()

    # Create 25 photos
    for i in range(25):
        await repo.create(
            user_id=1,
            data={
                "vlm_caption": f"Photo {i}",
                "vlm_analysis": {},
                "file_reference": {"filename": f"photo{i}.jpg"},
            },
            session=async_db,
        )

    # Get page 1 (10 items)
    page1 = await repo.get_all(user_id=1, session=async_db, limit=10, offset=0)
    assert len(page1) == 10

    # Get page 2 (10 items)
    page2 = await repo.get_all(user_id=1, session=async_db, limit=10, offset=10)
    assert len(page2) == 10

    # Get page 3 (5 items)
    page3 = await repo.get_all(user_id=1, session=async_db, limit=10, offset=20)
    assert len(page3) == 5

    # Verify no duplicates across pages
    ids = [p.id for p in page1 + page2 + page3]
    assert len(ids) == len(set(ids))


@pytest.mark.asyncio
async def test_count(async_db: AsyncSession):
    """Test count with user scoping."""
    repo = PhotoRepository()

    # Create photos for user 1
    for i in range(15):
        await repo.create(
            user_id=1,
            data={
                "vlm_caption": f"Photo {i}",
                "vlm_analysis": {},
                "file_reference": {"filename": f"photo{i}.jpg"},
            },
            session=async_db,
        )

    # Create photos for user 2
    for i in range(5):
        await repo.create(
            user_id=2,
            data={
                "vlm_caption": f"Photo {i}",
                "vlm_analysis": {},
                "file_reference": {"filename": f"photo{i}.jpg"},
            },
            session=async_db,
        )

    # Count should be user-specific
    count1 = await repo.count(user_id=1, session=async_db)
    count2 = await repo.count(user_id=2, session=async_db)

    assert count1 == 15
    assert count2 == 5


@pytest.mark.asyncio
async def test_update_with_user_scope(async_db: AsyncSession):
    """Test that updates are scoped by user_id."""
    repo = PhotoRepository()

    # Create photo for user 1
    photo = await repo.create(
        user_id=1,
        data={
            "vlm_caption": "Original caption",
            "vlm_analysis": {},
            "file_reference": {"filename": "test.jpg"},
        },
        session=async_db,
    )

    # User 2 should not be able to update user 1's photo
    result = await repo.update(
        model_id=photo.id,
        user_id=2,
        data={"vlm_caption": "Hacked caption"},
        session=async_db,
    )
    assert result is None  # Should not find the photo

    # User 1 should be able to update
    result = await repo.update(
        model_id=photo.id,
        user_id=1,
        data={"vlm_caption": "Updated caption"},
        session=async_db,
    )
    assert result is not None
    assert result.vlm_caption == "Updated caption"


@pytest.mark.asyncio
async def test_delete_with_user_scope(async_db: AsyncSession):
    """Test that deletes are scoped by user_id."""
    repo = PhotoRepository()

    # Create photos for both users
    photo1 = await repo.create(
        user_id=1,
        data={
            "vlm_caption": "User 1 photo",
            "vlm_analysis": {},
            "file_reference": {"filename": "test1.jpg"},
        },
        session=async_db,
    )

    photo2 = await repo.create(
        user_id=2,
        data={
            "vlm_caption": "User 2 photo",
            "vlm_analysis": {},
            "file_reference": {"filename": "test2.jpg"},
        },
        session=async_db,
    )

    # User 2 should not be able to delete user 1's photo
    deleted = await repo.delete(model_id=photo1.id, user_id=2, session=async_db)
    assert deleted is False

    # User 1 should be able to delete their own photo
    deleted = await repo.delete(model_id=photo1.id, user_id=1, session=async_db)
    assert deleted is True

    # User 1's photo should be gone
    remaining = await repo.get_all(user_id=1, session=async_db, limit=100)
    assert len(remaining) == 0

    # User 2's photo should still exist
    remaining = await repo.get_all(user_id=2, session=async_db, limit=100)
    assert len(remaining) == 1


@pytest.mark.asyncio
async def test_create_from_processor_result(async_db: AsyncSession):
    """Test creating photo from processor result."""
    repo = PhotoRepository()

    # Mock processor result
    class MockProcessorResult:
        def __init__(self):
            self.content = {
                "caption": "A beautiful sunset",
                "analysis": {"colors": ["orange", "pink"], "subject": "nature"},
                "image_file": "sunset.jpg",
            }
            self.metadata = {
                "file_size": 1024000,
                "file_type": ".jpg",
                "exif_data": {"DateTimeOriginal": "2024-01-15"},
            }

    processor_result = MockProcessorResult()

    photo = await repo.create_from_processor_result(
        user_id=1, source_id=10, processor_result=processor_result, session=async_db
    )

    assert photo.user_id == 1
    assert photo.source_id == 10
    assert photo.vlm_caption == "A beautiful sunset"
    assert photo.file_reference["size"] == 1024000
    assert photo.exif_data["DateTimeOriginal"] == "2024-01-15"


@pytest.mark.asyncio
async def test_batch_isolation(async_db: AsyncSession):
    """Test that batch operations maintain user isolation."""
    repo = PhotoRepository()

    # Create batch for user 1
    records1 = [
        {
            "vlm_caption": f"User 1 - Photo {i}",
            "vlm_analysis": {},
            "file_reference": {"filename": f"photo{i}.jpg"},
        }
        for i in range(5)
    ]
    photos1 = await repo.create_batch(user_id=1, records=records1, session=async_db)

    # Create batch for user 2
    records2 = [
        {
            "vlm_caption": f"User 2 - Photo {i}",
            "vlm_analysis": {},
            "file_reference": {"filename": f"photo{i}.jpg"},
        }
        for i in range(3)
    ]
    photos2 = await repo.create_batch(user_id=2, records=records2, session=async_db)

    # Verify isolation
    user1_photos = await repo.get_all(user_id=1, session=async_db, limit=100)
    user2_photos = await repo.get_all(user_id=2, session=async_db, limit=100)

    assert len(user1_photos) == 5
    assert len(user2_photos) == 3
    assert all("User 1" in p.vlm_caption for p in user1_photos)
    assert all("User 2" in p.vlm_caption for p in user2_photos)
