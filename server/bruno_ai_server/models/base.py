"""
Base SQLAlchemy model configuration with async support.
"""

from sqlalchemy import Column, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.ext.declarative import declarative_base

# Create the base class with async support
Base = declarative_base(cls=AsyncAttrs)


class TimestampMixin:
    """Mixin to add created_at and updated_at timestamps to models."""

    id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
