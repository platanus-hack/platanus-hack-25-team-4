"""
Database connection and initialization utilities.

Provides SQLAlchemy engine setup and session management for the Circles application.
"""

import os
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlmodel import SQLModel

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./circles.db",  # Default to SQLite for development
)

# Create SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    echo=os.getenv("SQL_ECHO", "False").lower() == "true",
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


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
