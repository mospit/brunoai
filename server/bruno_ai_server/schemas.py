"""
Pydantic schemas for API request/response models.
"""

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, EmailStr, validator


# Authentication schemas
class UserBase(BaseModel):
    """Base user schema."""
    email: EmailStr
    full_name: str


class UserCreate(UserBase):
    """Schema for user creation."""
    password: str

    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v


class UserLogin(BaseModel):
    """Schema for user login."""
    email: EmailStr
    password: str


class UserResponse(UserBase):
    """Schema for user response."""
    id: int
    is_active: bool
    is_verified: bool
    dietary_preferences: dict[str, Any] = {}
    voice_settings: dict[str, Any] = {}
    notification_preferences: dict[str, Any] = {}
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    """Schema for JWT token response."""
    access_token: str
    refresh_token: str | None = None
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Schema for token data."""
    user_id: int | None = None


class RefreshTokenRequest(BaseModel):
    """Schema for refresh token request."""
    refresh_token: str


# Household schemas
class HouseholdBase(BaseModel):
    """Base household schema."""
    name: str


class HouseholdCreate(HouseholdBase):
    """Schema for household creation."""
    pass


class HouseholdResponse(HouseholdBase):
    """Schema for household response."""
    id: int
    invite_code: str
    owner_id: int
    settings: dict[str, Any] = {}
    created_at: datetime

    class Config:
        from_attributes = True


class HouseholdMemberResponse(BaseModel):
    """Schema for household member response."""
    id: int
    user_id: int
    household_id: int
    role: str
    joined_at: datetime
    user: UserResponse

    class Config:
        from_attributes = True


# Pantry schemas
class PantryCategoryResponse(BaseModel):
    """Schema for pantry category response."""
    id: int
    name: str
    description: str | None = None
    icon: str | None = None
    color: str | None = None

    class Config:
        from_attributes = True


class PantryItemBase(BaseModel):
    """Base pantry item schema."""
    name: str
    quantity: float = 1.0
    unit: str = "piece"
    location: str | None = None
    notes: str | None = None


class PantryItemCreate(PantryItemBase):
    """Schema for pantry item creation."""
    barcode: str | None = None
    expiration_date: date | None = None
    category_id: int | None = None


class PantryItemUpdate(BaseModel):
    """Schema for pantry item update."""
    name: str | None = None
    quantity: float | None = None
    unit: str | None = None
    location: str | None = None
    notes: str | None = None
    expiration_date: date | None = None
    category_id: int | None = None


class PantryItemResponse(PantryItemBase):
    """Schema for pantry item response."""
    id: int
    barcode: str | None = None
    expiration_date: date | None = None
    purchase_date: date | None = None
    household_id: int
    category_id: int | None = None
    added_by_user_id: int
    item_metadata: dict[str, Any] = {}
    created_at: datetime

    # Relationships
    category: PantryCategoryResponse | None = None
    added_by_user: UserResponse

    class Config:
        from_attributes = True


# Recipe schemas
class RecipeBase(BaseModel):
    """Base recipe schema."""
    title: str
    description: str | None = None
    instructions: str


class RecipeCreate(RecipeBase):
    """Schema for recipe creation."""
    prep_time_minutes: int | None = None
    cook_time_minutes: int | None = None
    servings: int = 4
    difficulty_level: str | None = None
    tags: list = []
    cuisine_type: str | None = None


class RecipeResponse(RecipeBase):
    """Schema for recipe response."""
    id: int
    prep_time_minutes: int | None = None
    cook_time_minutes: int | None = None
    servings: int
    difficulty_level: str | None = None
    nutrition_info: dict[str, Any] = {}
    tags: list = []
    cuisine_type: str | None = None
    external_source: str | None = None
    external_id: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True
