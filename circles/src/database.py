"""
Database connection and initialization utilities.

Provides SQLAlchemy engine setup and session management for the Circles application.
Supports both sync and async operations.
"""

import os
from typing import AsyncGenerator, Generator

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlmodel import SQLModel

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./circles.db",  # Default to SQLite for development
)

# Create SQLAlchemy engine (sync)
engine = create_engine(
    DATABASE_URL,
    echo=os.getenv("SQL_ECHO", "False").lower() == "true",
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
)

# Create session factory (sync)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create async engine
async_database_url = DATABASE_URL.replace("sqlite://", "sqlite+aiosqlite://")
async_engine = create_async_engine(
    async_database_url,
    echo=os.getenv("SQL_ECHO", "False").lower() == "true",
)

# Create async session factory
AsyncSessionLocal = sessionmaker(
    async_engine, class_=AsyncSession, expire_on_commit=False
)


def create_db_and_tables():
    """Create all database tables.

    This should be called once on application startup.
    """
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    """Get a database session for dependency injection.

    Usage in FastAPI:
        @app.get("/profiles/{user_id}")
        def get_profile(user_id: str, session: Session = Depends(get_session)):
            return session.query(UserProfile).filter(...).first()

    Yields:
        Database session
    """
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Get an async database session for dependency injection.

    Usage in FastAPI:
        @app.get("/profiles/{user_id}")
        async def get_profile(user_id: int, session: AsyncSession = Depends(get_async_session)):
            result = await session.execute(select(UserProfile).where(...))
            return result.scalars().first()

    Yields:
        Async database session
    """
    async with AsyncSessionLocal() as session:
        yield session
