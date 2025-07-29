"""
Pantry-related database models.
"""

from datetime import date

from sqlalchemy import Column, Date, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin
from .types import CompatibleJSONB


class PantryCategory(Base, TimestampMixin):
    """Categories for organizing pantry items."""

    __tablename__ = "pantry_categories"

    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text)
    icon = Column(String(50))  # Icon identifier for UI
    color = Column(String(7))  # Hex color code

    # Relationships
    pantry_items = relationship("PantryItem", back_populates="category")

    def __repr__(self):
        return f"<PantryCategory(id={self.id}, name='{self.name}')>"


class PantryItem(Base, TimestampMixin):
    """Individual pantry items with expiration tracking."""

    __tablename__ = "pantry_items"

    name = Column(String(255), nullable=False)
    barcode = Column(String(50), index=True)  # For barcode scanning
    quantity = Column(Float, default=1.0, nullable=False)
    unit = Column(String(50), default="piece")  # piece, gram, liter, etc.

    # Expiration management
    expiration_date = Column(Date)
    purchase_date = Column(Date, default=date.today)

    # Location and organization
    location = Column(String(100))  # Fridge, pantry, freezer, etc.
    notes = Column(Text)

    # Relationships
    household_id = Column(UUID(as_uuid=True), ForeignKey("households.id"), nullable=False)
    category_id = Column(UUID(as_uuid=True), ForeignKey("pantry_categories.id"))
    added_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    household = relationship("Household", back_populates="pantry_items")
    category = relationship("PantryCategory", back_populates="pantry_items")
    added_by_user = relationship("User", back_populates="pantry_items")

    # Additional item data stored as JSON
    item_metadata = Column(CompatibleJSONB, default=dict)  # For nutrition info, brand, etc.

    @property
    def is_expiring_soon(self) -> bool:
        """Check if item is expiring within 3 days."""
        if not self.expiration_date:
            return False
        days_until_expiration = (self.expiration_date - date.today()).days
        return 0 <= days_until_expiration <= 3

    @property
    def is_expired(self) -> bool:
        """Check if item has expired."""
        if not self.expiration_date:
            return False
        return self.expiration_date < date.today()

    def __repr__(self):
        return f"<PantryItem(id={self.id}, name='{self.name}', quantity={self.quantity}, expiration='{self.expiration_date}')>"
