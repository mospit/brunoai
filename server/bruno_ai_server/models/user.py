"""
User and household-related database models.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid

from .base import Base, TimestampMixin


class User(Base, TimestampMixin):
    """User model for authentication and profile management."""
    
    __tablename__ = "users"

    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    
    # User preferences stored as JSON
    dietary_preferences = Column(JSONB, default=dict)
    voice_settings = Column(JSONB, default=dict)
    notification_preferences = Column(JSONB, default=dict)
    
    # Relationships
    household_memberships = relationship("HouseholdMember", back_populates="user")
    owned_households = relationship("Household", back_populates="owner")
    pantry_items = relationship("PantryItem", back_populates="added_by_user")
    favorite_recipes = relationship("UserFavorite", back_populates="user")

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', full_name='{self.full_name}')>"


class Household(Base, TimestampMixin):
    """Household model for shared pantry and collaboration."""
    
    __tablename__ = "households"

    name = Column(String(255), nullable=False)
    invite_code = Column(String(6), unique=True, index=True, nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Household settings stored as JSON
    settings = Column(JSONB, default=dict)
    
    # Relationships
    owner = relationship("User", back_populates="owned_households")
    members = relationship("HouseholdMember", back_populates="household")
    pantry_items = relationship("PantryItem", back_populates="household")

    def __repr__(self):
        return f"<Household(id={self.id}, name='{self.name}', invite_code='{self.invite_code}')>"


class HouseholdMember(Base, TimestampMixin):
    """Junction table for household membership with roles."""
    
    __tablename__ = "household_members"

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    household_id = Column(Integer, ForeignKey("households.id"), nullable=False)
    role = Column(String(50), default="member", nullable=False)  # admin, member
    joined_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="household_memberships")
    household = relationship("Household", back_populates="members")
    
    # Ensure unique user-household combinations
    __table_args__ = (UniqueConstraint('user_id', 'household_id', name='unique_user_household'),)

    def __repr__(self):
        return f"<HouseholdMember(user_id={self.user_id}, household_id={self.household_id}, role='{self.role}')>"
