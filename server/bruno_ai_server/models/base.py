"""
Base SQLAlchemy model configuration with async support.
"""

from datetime import datetime
from sqlalchemy import Column, DateTime, Integer, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import AsyncAttrs

# Create the base class with async support
Base = declarative_base(cls=AsyncAttrs)


class TimestampMixin:
    """Mixin to add created_at and updated_at timestamps to models."""
    
    id = Column(Integer, primary_key=True, index=True)
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
