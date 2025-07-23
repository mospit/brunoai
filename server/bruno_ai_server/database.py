"""
Database connection and session management.
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import sessionmaker

from .config import settings
from .models import Base

# Create async engine for async operations
async_engine = create_async_engine(
    settings.db_url.replace("postgresql://", "postgresql+asyncpg://"),
    echo=settings.debug,
    future=True,
)

# Create async session factory
async_session_factory = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Create sync engine for migrations
sync_engine = create_engine(
    settings.db_url,
    echo=settings.debug,
    future=True,
)

# Create sync session factory for migrations
sync_session_factory = sessionmaker(
    sync_engine,
    expire_on_commit=False,
)


async def get_async_session():
    """Dependency to get async database session."""
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()


def get_sync_session():
    """Get sync database session for migrations."""
    with sync_session_factory() as session:
        try:
            yield session
        finally:
            session.close()


async def create_tables():
    """Create all database tables."""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_tables():
    """Drop all database tables."""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
