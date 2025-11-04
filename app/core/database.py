"""
Database connection and session management
Uses SQLAlchemy async engine for PostgreSQL
Reference: https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html
"""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


# Validate DATABASE_URL is set
if not settings.DATABASE_URL:
    raise ValueError(
        "DATABASE_URL environment variable is not set. "
        "Please set it in your .env file or Vercel environment variables."
    )

# Create async engine for PostgreSQL
# Optimized for serverless (Vercel) - smaller pool, faster timeouts
# Reference: https://docs.sqlalchemy.org/en/20/core/pooling.html#disconnect-handling-pessimistic
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,  # Set to True for SQL query logging (useful for debugging)
    pool_pre_ping=True,  # Test connections before using them (important for serverless)
    pool_size=1,  # Smaller pool for serverless (Vercel functions are stateless)
    max_overflow=0,  # No overflow for serverless
    pool_recycle=300,  # Recycle connections after 5 minutes
    pool_timeout=20,  # Timeout for getting connection from pool
    connect_args={
        "server_settings": {
            "application_name": "fastapi_auth_starter",
        },
        "command_timeout": 30,  # Increased timeout for network latency
        "timeout": 30,  # Connection timeout
    },
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

