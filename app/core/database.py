"""
Database connection and session management
Uses SQLAlchemy async engine for PostgreSQL
Reference: https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html
"""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


# Create async engine for PostgreSQL
# pool_pre_ping=True: Validates connections before use (prevents stale connections)
# Reference: https://docs.sqlalchemy.org/en/20/core/pooling.html#disconnect-handling-pessimistic
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,  # Set to True for SQL query logging (useful for debugging)
    pool_pre_ping=True,  # Test connections before using them
    pool_size=5,  # Number of connections to maintain in the pool
    max_overflow=10,  # Maximum number of connections beyond pool_size
)


# Create async session factory
# This is used to create database sessions throughout the application
# Reference: https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html#session-basics
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Keep objects accessible after commit
    autocommit=False,
    autoflush=False,
)


# Base class for all database models
# All models should inherit from this class
# Reference: https://docs.sqlalchemy.org/en/20/orm/declarative_styles.html
class Base(DeclarativeBase):
    """Base class for SQLAlchemy declarative models"""
    pass


# Dependency to get database session
# Used in FastAPI route handlers via dependency injection
# Reference: https://fastapi.tiangolo.com/tutorial/dependencies/
async def get_db() -> AsyncSession:
    """
    Dependency function that provides a database session
    Automatically closes the session after the request completes
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()  # Commit transaction on success
        except Exception:
            await session.rollback()  # Rollback on error
            raise
        finally:
            await session.close()  # Always close the session

